// Core loop (spec §4.0): clinician sends alert → simulated push + SMS on the phone →
// escalation on the demo clock → clinic board. Server-only.
//
// All wording and timings come from panel_scores_<scenario>.json:
//   alert text  = the patient's `safety_alert` message
//   steps       = escalation.steps (atMin, action, to)
//   contact SMS = the `contact_check` message
// If a piece is missing, the message body says so in [brackets] instead of inventing text.

import { db, demoNow } from "@/lib/db";
import { contactMessage, englishFor, getPanelPatient, patientMessage, type Scenario } from "@/lib/panel";
import { riskGroup } from "@/lib/risk";

export type AlertStatus = "sent" | "acknowledged" | "escalated_contact" | "escalated_clinic" | "resolved";

export interface AlertRow {
  id: number;
  patient_id: string;
  message: string;
  language: string;
  status: AlertStatus;
  wait_minutes: number | null;
  contact_id: string | null;
  scenario: Scenario;
  steps_done: number;
  sent_at: string;
  ack_at: string | null;
  escalated_at: string | null;
}

export interface MessageRow {
  id: number;
  patient_id: string | null;
  alert_id: number | null;
  recipient: string;
  channel: string;
  body: string;
  note: string | null;
  simulated: number;
  read_at: string | null;
  created_at: string;
}

const OPEN: AlertStatus[] = ["sent", "escalated_contact", "escalated_clinic"];

function logMessage(m: Omit<MessageRow, "id" | "simulated" | "read_at" | "created_at">, at: Date) {
  db()
    .prepare(
      `INSERT INTO messages (patient_id, alert_id, recipient, channel, body, note, simulated, created_at)
       VALUES (?, ?, ?, ?, ?, ?, 1, ?)`,
    )
    .run(m.patient_id, m.alert_id, m.recipient, m.channel, m.body, m.note, at.toISOString());
}

export type SendMode = "text" | "call";

/**
 * Send a patient their risk group's message (P2 "Text this group").
 *   Low    → heads-up (heat_card), no escalation
 *   Medium → nearest cool place + safe hours (cooling_place), no escalation
 *   High   → safety_alert + cooling_place, with the full escalation (check-ins, contact, clinic)
 *   mode "call" (alert_opt_in = false) → no text; put on the clinic call list instead.
 */
export function sendAlert(
  patientId: string,
  scenario: Scenario = "replay",
  mode: SendMode = "text",
): { ok: true; alertId: number } | { ok: false; error: string } {
  const p = getPanelPatient(patientId, scenario);
  if (!p) return { ok: false, error: `${patientId} not in panel_scores_${scenario}.json` };
  const group = riskGroup(p.readiness?.level);
  const kind = group === "high" ? "safety_alert" : group === "medium" ? "cooling_place" : "heat_card";
  const msg = patientMessage(p, kind);
  const body = msg?.text ?? `[no ${kind} message for ${patientId} in panel_scores_${scenario}.json]`;
  const steps = p.escalation?.steps ?? [];
  const firstStep = steps[0];
  const now = demoNow();

  if (mode === "call") {
    const res = db()
      .prepare(
        `INSERT INTO alerts (patient_id, kind, message, language, channel, status, wait_minutes, scenario, steps_done, sent_at, escalated_at)
         VALUES (?, 'heat_safety', ?, ?, 'call', 'escalated_clinic', NULL, ?, ?, ?, ?)`,
      )
      .run(patientId, body, msg?.language ?? p.language, scenario, steps.length, now.toISOString(), now.toISOString());
    const alertId = Number(res.lastInsertRowid);
    logMessage({
      patient_id: patientId, alert_id: alertId, recipient: "clinic", channel: "call_list",
      body: `Call this patient (they asked not to get texts). Read them: ${body}`,
      note: "alert_opt_in = false (questionnaire.csv)",
    }, now);
    return { ok: true, alertId };
  }

  // Only the High group gets the check-in / contact / clinic escalation.
  const stepsDone = group === "high" ? (firstStep ? 1 : 0) : steps.length;
  const res = db()
    .prepare(
      `INSERT INTO alerts (patient_id, kind, message, language, channel, status, wait_minutes, scenario, steps_done, sent_at)
       VALUES (?, 'heat_safety', ?, ?, 'push+sms', 'sent', ?, ?, ?, ?)`,
    )
    .run(patientId, body, msg?.language ?? p.language, p.escalation?.tWaitMin ?? null, scenario, stepsDone, now.toISOString());
  const alertId = Number(res.lastInsertRowid);

  const note = group === "high" ? firstStep?.action ?? null : `${group === "medium" ? "Medium" : "Low"} group message`;
  for (const channel of ["push", "sms"]) {
    logMessage({ patient_id: patientId, alert_id: alertId, recipient: "patient", channel, body, note }, now);
  }
  if (group === "high") {
    const cool = patientMessage(p, "cooling_place");
    if (cool) logMessage({ patient_id: patientId, alert_id: alertId, recipient: "patient", channel: "sms", body: cool.text, note: "Where to go" }, now);
  }
  return { ok: true, alertId };
}

/** Fire every escalation step whose time has come (called on each poll; fast-forward aware). */
export function tick(): void {
  const now = demoNow();
  const open = db()
    .prepare(`SELECT * FROM alerts WHERE status IN (${OPEN.map(() => "?").join(",")})`)
    .all(...OPEN) as unknown as AlertRow[];

  for (const a of open) {
    const p = getPanelPatient(a.patient_id, a.scenario);
    const steps = p?.escalation?.steps ?? [];
    const elapsed = (now.getTime() - new Date(a.sent_at).getTime()) / 60_000;
    let done = a.steps_done;
    let status: AlertStatus = a.status;
    let contactId = a.contact_id;

    while (done < steps.length && steps[done].atMin <= elapsed) {
      const s = steps[done];
      const at = new Date(new Date(a.sent_at).getTime() + s.atMin * 60_000);
      if (s.to === "patient") {
        for (const channel of ["push", "sms"]) {
          logMessage({ patient_id: a.patient_id, alert_id: a.id, recipient: "patient", channel, body: a.message, note: s.action }, at);
        }
      } else if (s.to.startsWith("clinic")) {
        logMessage({ patient_id: a.patient_id, alert_id: a.id, recipient: "clinic", channel: "call_list", body: s.action, note: s.action }, at);
        status = "escalated_clinic";
      } else {
        // Any other `to` is a contact id (e.g. "P0149-C2").
        const cm = p ? contactMessage(p) : null;
        logMessage({
          patient_id: a.patient_id, alert_id: a.id, recipient: `contact:${s.to}`, channel: "sms",
          body: cm?.text ?? `[no contact_check message for ${a.patient_id} in panel_scores_${a.scenario}.json]`,
          note: s.action,
        }, at);
        contactId = s.to;
        if (status === "sent") status = "escalated_contact";
      }
      done++;
    }

    if (done !== a.steps_done) {
      db()
        .prepare(`UPDATE alerts SET steps_done = ?, status = ?, contact_id = ?, escalated_at = COALESCE(escalated_at, ?) WHERE id = ?`)
        .run(done, status, contactId, status === "sent" ? null : now.toISOString(), a.id);
    }
  }
}

export type CheckinStatus = "ok" | "unwell" | "no_ac";

/** Patient tap on the phone. "ok" acknowledges open alerts and stops escalation. */
export function checkin(patientId: string, status: CheckinStatus) {
  const now = demoNow().toISOString();
  const open = db()
    .prepare(`SELECT id FROM alerts WHERE patient_id = ? AND status IN (${OPEN.map(() => "?").join(",")}) ORDER BY id DESC`)
    .all(patientId, ...OPEN) as { id: number }[];
  const alertId = open[0]?.id ?? null;

  db().prepare(`INSERT INTO checkins (patient_id, alert_id, status, created_at) VALUES (?, ?, ?, ?)`).run(patientId, alertId, status, now);

  if (status === "ok") {
    for (const a of open) db().prepare(`UPDATE alerts SET status = 'acknowledged', ack_at = ? WHERE id = ?`).run(now, a.id);
  } else {
    // "I feel unwell" / "No AC" → straight to the clinic call list; a human decides.
    logMessage({
      patient_id: patientId, alert_id: alertId, recipient: "clinic", channel: "call_list",
      body: status === "unwell" ? "Patient tapped “I feel unwell”" : "Patient tapped “No AC”",
      note: "patient check-in",
    }, new Date(now));
    for (const a of open) db().prepare(`UPDATE alerts SET status = 'escalated_clinic', escalated_at = COALESCE(escalated_at, ?) WHERE id = ?`).run(now, a.id);
  }
  return { ok: true, alertId };
}

export function boardState() {
  tick();
  const alerts = db().prepare(`SELECT * FROM alerts ORDER BY id DESC`).all() as unknown as AlertRow[];
  const messages = db().prepare(`SELECT * FROM messages ORDER BY created_at DESC, id DESC LIMIT 200`).all() as unknown as MessageRow[];
  const checkins = db().prepare(`SELECT * FROM checkins ORDER BY id DESC LIMIT 100`).all();
  const now = demoNow();
  const withNext = alerts.map((a) => {
    const steps = getPanelPatient(a.patient_id, a.scenario)?.escalation?.steps ?? [];
    const next = OPEN.includes(a.status) ? steps[a.steps_done] ?? null : null;
    return {
      ...a,
      elapsed_min: (now.getTime() - new Date(a.sent_at).getTime()) / 60_000,
      next_step: next,
      total_steps: steps.length,
    };
  });
  return { demo_time: now.toISOString(), alerts: withNext, messages, checkins };
}

/** What the demo phone shows: messages to this patient + its latest alert status. */
export function inbox(patientId: string, lang?: "en" | "es") {
  tick();
  const rows = db()
    .prepare(`SELECT * FROM messages WHERE patient_id = ? AND recipient = 'patient' ORDER BY created_at ASC, id ASC`)
    .all(patientId) as unknown as MessageRow[];
  // ?lang=en: show the English build of the same message (reading copy; the patient was sent their own language).
  const messages = lang === "en"
    ? rows.map((m) => {
        const en = englishFor(patientId, m.body);
        return en ? { ...m, body: en } : m;
      })
    : rows;
  const latest = db().prepare(`SELECT * FROM alerts WHERE patient_id = ? ORDER BY id DESC LIMIT 1`).get(patientId) as unknown as AlertRow | undefined;
  return { demo_time: demoNow().toISOString(), messages, alert: latest ?? null };
}
