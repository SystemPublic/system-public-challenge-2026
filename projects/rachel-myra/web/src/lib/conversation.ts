// Clinician ↔ patient conversation view (server-only). Reads the same SQLite log as the core loop
// (lib/loop.ts): every simulated push/SMS to the patient, texts to their contacts, clinic call-list
// events, and the patient's check-in taps. Clinician-typed texts are added to the same `messages`
// table (recipient 'patient', channel 'sms'), so they also appear on the demo phone.
// Patient details come from panel_scores_replay.json and synthetic/questionnaire.csv. Nothing invented.
import fs from "node:fs";
import path from "node:path";
import { db, demoNow } from "@/lib/db";
import { REPO_ROOT } from "@/lib/kb";
import { getPanelPatient, loadPanel } from "@/lib/panel";
import { parseCsv } from "@lib/patient/csv.ts";
import { plainWhy } from "@/lib/plainWhy";

export type RiskGroup = "High" | "Medium" | "Low";

export interface ThreadItem {
  id: string;
  at: string; // ISO demo time
  kind: "out" | "in" | "contact" | "clinic";
  channel: string;
  body: string;
  note: string | null;
  who: string; // display label
}

export interface PatientHeader {
  id: string;
  name: string;
  age: number;
  zip: string;
  language: string;
  group: RiskGroup;
  why: string[];
  optIn: boolean | null;
  phone: string | null;
  contacts: { id: string; name: string; relationship: string }[];
  templates: { kind: string; label: string; text: string }[];
}

const groupOf = (lvl?: string): RiskGroup => (lvl === "high" || lvl === "very_high" ? "High" : lvl === "medium" ? "Medium" : "Low");

let qCache: Map<string, Record<string, string>> | null = null;
function questionnaire(id: string) {
  if (!qCache) {
    qCache = new Map();
    try {
      const rows = parseCsv(fs.readFileSync(path.join(REPO_ROOT, "data", "processed", "synthetic", "questionnaire.csv"), "utf8"));
      for (const r of rows) qCache.set(r.patient_id, r);
    } catch {
      /* file missing → optIn null */
    }
  }
  return qCache.get(id);
}

let phoneCache: Map<string, string> | null = null;
function phoneOf(id: string) {
  if (!phoneCache) {
    phoneCache = new Map();
    try {
      for (const r of parseCsv(fs.readFileSync(path.join(REPO_ROOT, "data", "processed", "synthetic", "patients.csv"), "utf8"))) {
        if (r.phone) phoneCache.set(r.patient_id, r.phone);
      }
    } catch {
      /* ignore */
    }
  }
  return phoneCache.get(id) ?? null;
}

const TEMPLATE_LABELS: Record<string, string> = {
  cooling_place: "Nearest cool place",
  checkin: "Check-in",
  heat_card: "Heat tips for your medicines",
};

export function patientHeader(id: string): PatientHeader | null {
  const p = getPanelPatient(id, "replay");
  if (!p) return null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const raw = p as any;
  const q = questionnaire(id);
  const optRaw = q?.alert_opt_in?.toLowerCase();
  return {
    id,
    name: p.displayName,
    age: p.age,
    zip: p.zip,
    language: p.language,
    group: groupOf(raw.readiness?.level),
    why: ((raw.readiness?.drivers as string[] | undefined) ?? []).map(plainWhy),
    optIn: optRaw === "true" ? true : optRaw === "false" ? false : null,
    phone: phoneOf(id),
    contacts: (p.escalation?.contacts ?? []).map((c) => ({ id: c.contactId, name: c.name, relationship: c.relationship })),
    templates: (p.messages ?? [])
      .filter((m) => m.audience === "patient" && TEMPLATE_LABELS[m.kind])
      .map((m) => ({ kind: m.kind, label: TEMPLATE_LABELS[m.kind], text: m.text })),
  };
}

export function thread(id: string): { demo_time: string; items: ThreadItem[] } {
  const header = patientHeader(id);
  const contactName = new Map(header?.contacts.map((c) => [c.id, `${c.name} (${c.relationship})`]) ?? []);
  const msgs = db()
    .prepare(`SELECT * FROM messages WHERE patient_id = ? ORDER BY created_at ASC, id ASC`)
    .all(id) as unknown as { id: number; recipient: string; channel: string; body: string; note: string | null; created_at: string }[];
  const checkins = db()
    .prepare(`SELECT * FROM checkins WHERE patient_id = ? ORDER BY created_at ASC, id ASC`)
    .all(id) as unknown as { id: number; status: string; created_at: string }[];

  const items: ThreadItem[] = [];
  // The loop logs each alert twice (push + sms). Show it once, as "push + text".
  const seen = new Set<string>();
  for (const m of msgs) {
    if (m.recipient === "patient") {
      const key = `${m.created_at}|${m.body}`;
      if (seen.has(key)) continue;
      seen.add(key);
      const twin = msgs.some((o) => o !== m && o.recipient === "patient" && o.created_at === m.created_at && o.body === m.body);
      items.push({ id: `m${m.id}`, at: m.created_at, kind: "out", channel: twin ? "push + text" : m.channel === "sms" ? "text" : m.channel, body: m.body, note: m.note, who: "Clinic" });
    } else if (m.recipient.startsWith("contact:")) {
      const cid = m.recipient.slice("contact:".length);
      items.push({ id: `m${m.id}`, at: m.created_at, kind: "contact", channel: "text", body: m.body, note: m.note, who: `To ${contactName.get(cid) ?? "contact"}` });
    } else {
      items.push({ id: `m${m.id}`, at: m.created_at, kind: "clinic", channel: m.channel, body: m.body, note: m.note, who: "Clinic call list" });
    }
  }
  const CHECKIN_TEXT: Record<string, string> = { ok: "I'm OK", unwell: "I feel unwell", no_ac: "I have no AC" };
  for (const c of checkins) {
    items.push({ id: `c${c.id}`, at: c.created_at, kind: "in", channel: "tap", body: CHECKIN_TEXT[c.status] ?? c.status, note: null, who: header?.name ?? id });
  }
  items.sort((a, b) => a.at.localeCompare(b.at) || a.id.localeCompare(b.id));
  return { demo_time: demoNow().toISOString(), items };
}

export function sendText(id: string, body: string): { ok: true } | { ok: false; error: string } {
  const text = body.trim();
  if (!text) return { ok: false, error: "Message is empty" };
  if (text.length > 1000) return { ok: false, error: "Message is too long" };
  if (!getPanelPatient(id, "replay")) return { ok: false, error: `${id} not in panel_scores_replay.json` };
  db()
    .prepare(
      `INSERT INTO messages (patient_id, alert_id, recipient, channel, body, note, simulated, created_at)
       VALUES (?, NULL, 'patient', 'sms', ?, 'clinician message', 1, ?)`,
    )
    .run(id, text, demoNow().toISOString());
  return { ok: true };
}

export interface ConversationSummary {
  id: string;
  name: string;
  group: RiskGroup;
  zip: string;
  last: string | null; // last activity (ISO)
  lastText: string | null;
  needsAttention: boolean; // latest event is "unwell"/"no AC" or a clinic call-list entry
}

export function conversations(): ConversationSummary[] {
  const panel = loadPanel("replay");
  if (!panel) return [];
  const lastMsg = new Map<string, { at: string; body: string; recipient: string }>();
  for (const r of db()
    .prepare(`SELECT patient_id, created_at, body, recipient FROM messages WHERE patient_id IS NOT NULL ORDER BY created_at ASC, id ASC`)
    .all() as unknown as { patient_id: string; created_at: string; body: string; recipient: string }[]) {
    lastMsg.set(r.patient_id, { at: r.created_at, body: r.body, recipient: r.recipient });
  }
  const lastCheck = new Map<string, { at: string; status: string }>();
  for (const r of db().prepare(`SELECT patient_id, created_at, status FROM checkins ORDER BY created_at ASC, id ASC`).all() as unknown as {
    patient_id: string;
    created_at: string;
    status: string;
  }[]) {
    lastCheck.set(r.patient_id, { at: r.created_at, status: r.status });
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (panel.data.patients as any[]).map((p) => {
    const m = lastMsg.get(p.patientId);
    const c = lastCheck.get(p.patientId);
    const checkLatest = c && (!m || c.at >= m.at);
    const last = checkLatest ? c!.at : m?.at ?? null;
    const lastText = checkLatest
      ? c!.status === "ok"
        ? "Patient: I'm OK"
        : c!.status === "unwell"
          ? "Patient: I feel unwell"
          : "Patient: I have no AC"
      : m?.body ?? null;
    const needsAttention = checkLatest ? c!.status !== "ok" : m?.recipient === "clinic";
    return { id: p.patientId, name: p.displayName, group: groupOf(p.readiness?.level), zip: p.zip, last, lastText, needsAttention };
  });
}
