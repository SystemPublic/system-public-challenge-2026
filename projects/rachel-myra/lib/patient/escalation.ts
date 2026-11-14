// Escalation algorithm (spec §4.4a): a time budget T_max set by medical evidence, split as
//   T_max = T_wait (patient acknowledges) + T_contact (contact responds) + T_travel (contact arrives).
// A contact is eligible when T_travel ≤ T_max − p90(patient) − p90(contact), using the routed
// travel time when the routing agent has produced it (contacts_routed.csv), else the naive
// straight-line placeholder (labeled as such). Ends at a human: never auto-calls 911.

import type { EscalationRules, HeatRiskLevel, ReadinessLevel } from "../types/health-system.ts";
import type { ContactEligibility, EscalationPlan, EscalationStep, QuestionnaireAnswers, TrustedContact } from "../types/patient.ts";

export interface TravelEstimate {
  minutes: number;
  mode: string;
  source: "routed" | "naive_placeholder";
}

export type TravelLookup = Map<string, TravelEstimate>;

const R_IDX: Record<ReadinessLevel, number> = { low: 0, medium: 1, high: 2, very_high: 3 };

export function toMin(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + (m || 0);
}
export function fmtMin(min: number): string {
  const m = ((Math.round(min) % 1440) + 1440) % 1440;
  return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
}

export function timeBudget(
  readiness: ReadinessLevel,
  heatriskToday: HeatRiskLevel,
  q: QuestionnaireAnswers | null,
  rules: EscalationRules,
): { tMax: number; reason: string } {
  let tMax = rules.t_max_min[readiness];
  let reason = `${readiness.replace("_", " ")} readiness → ${tMax} min`;
  const hotHome = q?.workingAc === "no" && q?.homeGetsHot === "often";
  if (heatriskToday >= rules.tighten_to_very_high_if_heatrisk_gte && tMax > rules.t_max_min.very_high) {
    tMax = rules.t_max_min.very_high;
    reason += `; tightened to ${tMax} min because HeatRisk ${heatriskToday} ≥ ${rules.tighten_to_very_high_if_heatrisk_gte}`;
  } else if (hotHome && tMax > rules.t_max_min.very_high) {
    tMax = rules.t_max_min.very_high;
    reason += `; tightened to ${tMax} min because the home is hot with no AC`;
  }
  return { tMax, reason };
}

export function checkinSchedule(
  q: QuestionnaireAnswers | null,
  readiness: ReadinessLevel,
  heatriskToday: HeatRiskLevel,
  rules: EscalationRules,
): { times: string[]; longestGapMin: number } {
  const base = q?.checkinTimes?.length ? q.checkinTimes : ["10:00", "16:00"];
  const d = rules.checkin_densify;
  const set = new Set(base);
  if (heatriskToday >= d.min_heatrisk && R_IDX[readiness] >= R_IDX[d.min_readiness]) for (const t of d.add_times) set.add(t);
  const times = [...set].sort((a, b) => toMin(a) - toMin(b));
  const [ws, we] = rules.waking_window.map(toMin);
  const pts = [ws, ...times.map(toMin).filter((m) => m >= ws && m <= we), we];
  let gap = 0;
  for (let i = 1; i < pts.length; i++) gap = Math.max(gap, pts[i] - pts[i - 1]);
  return { times, longestGapMin: gap };
}

export function escalationPlan(args: {
  age: number;
  q: QuestionnaireAnswers | null;
  contacts: TrustedContact[];
  readiness: ReadinessLevel;
  heatriskToday: HeatRiskLevel;
  travel: TravelLookup;
  rules: EscalationRules;
  finalStep: string;
  buddyProgram: string;
}): EscalationPlan {
  const { age, q, rules } = args;
  const { tMax, reason } = timeBudget(args.readiness, args.heatriskToday, q, rules);
  const p = rules.response_p90_min;
  const voice = q?.alertChannel === "voice_call";
  const tWait = (voice ? p.patient_voice_call.value : p.patient_app_or_sms.value) + (age >= 65 ? p.older_adult_extra.value : 0);
  const tContact = p.contact.value;
  const allowed = tMax - tWait - tContact;

  const contacts: ContactEligibility[] = args.contacts.map((c) => {
    const t = args.travel.get(c.id);
    return {
      contactId: c.id,
      name: `${c.givenName} ${c.familyName}`.trim(),
      relationship: c.relationship,
      travelMin: t ? +t.minutes.toFixed(1) : null,
      travelMode: t?.mode ?? null,
      travelSource: t?.source ?? "none",
      allowedTravelMin: allowed,
      eligible: !!t && t.minutes <= allowed,
    };
  });
  const eligible = contacts.filter((c) => c.eligible).sort((a, b) => (a.travelMin ?? 1e9) - (b.travelMin ?? 1e9));
  const none = eligible.length === 0;
  const enrolled = q?.alertOptIn !== false && args.readiness !== "low";
  const resendAt = Math.round(tWait * rules.resend_fraction_of_wait);
  const channel = voice ? "voice call" : q?.alertChannel === "sms_only" ? "SMS" : "app push + SMS";

  const steps: EscalationStep[] = [
    { atMin: 0, action: `Send safety alert (${channel}); ask for "OK"`, to: "patient" },
    { atMin: resendAt, action: "No reply: re-send the alert once (halfway point)", to: "patient" },
  ];
  if (!none) {
    steps.push({ atMin: tWait, action: `No reply: ask ${eligible[0].relationship} to check in person or by phone, with the what-to-look-for checklist`, to: eligible[0].contactId });
    const next = eligible[1];
    steps.push({
      atMin: tWait + tContact,
      action: next
        ? `Contact hasn't confirmed: alert next contact (${next.relationship}) and add to clinic call list`
        : "Contact hasn't confirmed: add to clinic call list",
      to: next ? `${next.contactId} + clinic` : "clinic",
    });
  } else {
    steps.push({ atMin: tWait, action: "No reply and no contact close enough: put on clinic call list now (and buddy, if matched)", to: "clinic" });
  }
  steps.push({ atMin: tMax, action: `Budget reached: ${args.finalStep}`, to: "clinic (human decides)" });

  const sched = checkinSchedule(q, args.readiness, args.heatriskToday, rules);
  const anyNaive = contacts.some((c) => c.travelSource === "naive_placeholder");
  return {
    enrolled,
    tMaxMin: tMax,
    tMaxReason: reason,
    tWaitMin: tWait,
    tContactMin: tContact,
    allowedTravelMin: allowed,
    resendAtMin: resendAt,
    contacts,
    firstContactId: none ? null : eligible[0].contactId,
    noQualifyingContact: none,
    fallback: none
      ? `${contacts.length ? "Ask for a closer contact" : "Ask for a trusted contact"}, or offer a buddy (${args.buddyProgram}); priority call list`
      : null,
    checkinTimes: sched.times,
    longestGapMin: sched.longestGapMin,
    worstCaseUnnoticedMin: sched.longestGapMin + tMax,
    steps,
    assumptions: [
      `T_max: ${rules.t_max_source}`,
      `T_wait p90 ${tWait} min: ${voice ? p.patient_voice_call.source : p.patient_app_or_sms.source}${age >= 65 ? ` + ${p.older_adult_extra.source}` : ""}`,
      `T_contact p90 ${tContact} min: ${p.contact.source}`,
      anyNaive
        ? "Travel time: NAIVE straight-line placeholder (contacts.csv naive_travel_min); routed times not yet available"
        : contacts.length
          ? "Travel time: routed (contacts_routed.csv)"
          : "No trusted contacts on file",
    ],
  };
}
