// Priority tiers with human-readable reason tags, gated on the forecast HeatRisk so urgent
// actions fire only on high-risk days (spec §4.4 safety rules; §10.4 alert fatigue).
// Rules come from the health-system config (alert_rules), not code.

import type { AlertRules, HeatRiskLevel, ReadinessLevel } from "../types/health-system.ts";
import type { ExposureResult, MedRiskStack, PriorityTier, QuestionnaireAnswers, TierResult } from "../types/patient.ts";

export const HEATRISK_LABELS = ["Green (little to no risk)", "Yellow (minor)", "Orange (moderate)", "Red (major)", "Magenta (extreme)"];
export const TIER_ORDER: PriorityTier[] = ["call_today", "call_before_heat_wave", "send_heat_card", "routine"];
export const TIER_LABELS: Record<PriorityTier, string> = {
  call_today: "Call today",
  call_before_heat_wave: "Call before the heat wave",
  send_heat_card: "Send heat card",
  routine: "Routine",
};
const R_IDX: Record<ReadinessLevel, number> = { low: 0, medium: 1, high: 2, very_high: 3 };

export const TIER_RULES = [
  "call_today: today's HeatRisk in the patient's ZIP ≥ alert_rules.call_today_min_heatrisk[readiness] (SBH: very high ≥ 2 orange)",
  "call_today (uncovered): readiness ≥ call_today_if_uncovered.min_readiness, HeatRisk ≥ its min_heatrisk (SBH: high at ≥ 3 red), no trusted contact close enough AND (lives alone OR not opted in)",
  "call_before_heat_wave: not call_today, today's HeatRisk still below min_heatrisk (wave not started), max HeatRisk in the next lookahead_days ≥ min_heatrisk, and readiness ≥ min_readiness",
  "send_heat_card: otherwise, medication stack level ≥ heat_card_min_med_level, or a heat-sensitive medicine to store (non-urgent education, not gated on forecast)",
  "routine: everyone else",
  "auto safety alert (push + SMS): today's HeatRisk ≥ auto_safety_alert_min_heatrisk, readiness high/very high, opted in",
  "morning cooling-place text: today's HeatRisk ≥ cooling_text_min_heatrisk and (no reliable AC, or readiness high/very high)",
];

export interface TierInput {
  readiness: ReadinessLevel;
  readinessDrivers: string[];
  med: MedRiskStack;
  exposure: ExposureResult;
  q: QuestionnaireAnswers | null;
  zip: string;
  heatriskToday: HeatRiskLevel;
  heatriskMaxNext: HeatRiskLevel;
  noQualifyingContact: boolean;
}

export function priorityTier(inp: TierInput, rules: AlertRules): TierResult {
  const { readiness, med, q } = inp;
  const reasons: string[] = [];
  const minToday = rules.call_today_min_heatrisk[readiness];
  const today = inp.heatriskToday;
  const cb = rules.call_before_heat_wave;
  let tier: PriorityTier;
  let gate: string;

  const unc = rules.call_today_if_uncovered;
  const uncovered = inp.noQualifyingContact && (q?.livesAlone === true || q?.alertOptIn === false);
  if (minToday !== undefined && today >= minToday) {
    tier = "call_today";
    gate = `HeatRisk ${today} today ≥ ${minToday} for ${readiness.replace("_", " ")} readiness`;
    reasons.push(`HeatRisk ${today} ${HEATRISK_LABELS[today].split(" ")[0]} today in ${inp.zip}`);
  } else if (unc && uncovered && today >= unc.min_heatrisk && R_IDX[readiness] >= R_IDX[unc.min_readiness]) {
    tier = "call_today";
    gate = `HeatRisk ${today} today ≥ ${unc.min_heatrisk} and automation can't reach anyone in time`;
    reasons.push(`HeatRisk ${today} ${HEATRISK_LABELS[today].split(" ")[0]} today in ${inp.zip}`);
    reasons.push(q?.alertOptIn === false ? "not opted in to safety alerts" : "lives alone");
  } else if (today < cb.min_heatrisk && inp.heatriskMaxNext >= cb.min_heatrisk && R_IDX[readiness] >= R_IDX[cb.min_readiness]) {
    tier = "call_before_heat_wave";
    gate = `HeatRisk ${inp.heatriskMaxNext} forecast within ${cb.lookahead_days} days ≥ ${cb.min_heatrisk}`;
    reasons.push(`HeatRisk ${inp.heatriskMaxNext} ${HEATRISK_LABELS[inp.heatriskMaxNext].split(" ")[0]} forecast within ${cb.lookahead_days} days`);
  } else if (med.level >= rules.heat_card_min_med_level || (rules.heat_card_if_storage_sensitive && med.defenses.some((d) => d.defense === "medicine_storage"))) {
    tier = "send_heat_card";
    gate = today === 0 && inp.heatriskMaxNext === 0 ? "No heat forecast: no calls or alerts (drill only)" : `HeatRisk ${today} today below call threshold for ${readiness.replace("_", " ")} readiness`;
    if (today >= rules.auto_safety_alert_min_heatrisk && R_IDX[readiness] >= 2) reasons.push("covered by automated safety alert, check-ins and contact escalation today");
  } else {
    tier = "routine";
    gate = "Below all thresholds";
  }

  if (tier !== "routine") {
    reasons.push(`${readiness.replace("_", " ")} readiness`);
    reasons.push(...inp.readinessDrivers.slice(0, 4));
    if (med.combinations.some((c) => c.raisesLevel)) reasons.push(...med.combinations.filter((c) => c.raisesLevel).map((c) => c.label));
    else if (med.reasons.length) reasons.push(med.reasons[0]);
    if (inp.noQualifyingContact && (tier === "call_today" || tier === "call_before_heat_wave")) reasons.push("no trusted contact close enough");
    if (q?.alertOptIn === false && tier === "call_today") reasons.push("not opted in to safety alerts: phone call is the only route");
  }

  const reliableAc = q?.workingAc === "yes";
  return {
    tier,
    reasons: [...new Set(reasons)],
    gate,
    autoSafetyAlert: today >= rules.auto_safety_alert_min_heatrisk && R_IDX[readiness] >= 2 && q?.alertOptIn !== false,
    coolingText: today >= rules.cooling_text_min_heatrisk && (!reliableAc || R_IDX[readiness] >= 2),
  };
}

/** Sort key: tier, then readiness, then medication level, then exposure points. */
export function compareForCallList(
  a: { tier: TierResult; readiness: { level: ReadinessLevel }; meds: MedRiskStack; exposure: ExposureResult; patientId: string },
  b: typeof a,
): number {
  return (
    TIER_ORDER.indexOf(a.tier.tier) - TIER_ORDER.indexOf(b.tier.tier) ||
    R_IDX[b.readiness.level] - R_IDX[a.readiness.level] ||
    b.meds.level - a.meds.level ||
    b.exposure.points - a.exposure.points ||
    b.meds.plotY - a.meds.plotY ||
    a.patientId.localeCompare(b.patientId)
  );
}
