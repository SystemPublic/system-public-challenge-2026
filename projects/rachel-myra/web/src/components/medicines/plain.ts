// Plain-language helpers for the Medicines screens. Client-safe (no fs).

import type { Actor, Bucket, DrugRecord, TimelinePhase } from "@lib/types/knowledge-base.ts";

/** Group headers on /medicines, in plain words. Colors stay the bucket colors. */
export const GROUP_HEADER: Record<Bucket, string> = {
  hold_or_substitute: "Think about pausing or switching",
  adjust_dose: "The dose may need a look",
  monitor: "Check on these patients",
  storage: "Store it cool",
};

export const PHASE_LABEL: Record<TimelinePhase, string> = {
  before_summer: "Before summer",
  "72h_before": "3 days before the heat",
  during: "During the heat",
  after: "After the heat",
};

export const PHASE_ORDER: TimelinePhase[] = ["before_summer", "72h_before", "during", "after"];

export const ACTOR_LABEL: Record<Actor, string> = {
  prescriber: "Prescriber",
  pharmacist: "Pharmacist",
  care_coordinator: "Care team",
  patient: "Patient",
  caregiver: "Caregiver",
  health_system: "Clinic",
};

/** ✓ when the FDA label audit found a heat warning (data/processed/fda_label_heat_audit_summary_v2.csv via KB). */
export function labelWarnsAboutHeat(d: DrugRecord): boolean | null {
  const s = d.fda_label?.class_status;
  if (!s || s === "not audited") return null;
  return s === "heat warning";
}

/** ✓ when at least one guidance document gives a drug-specific action (data/processed/guidance_matrix.csv via KB). */
export function guidanceSaysWhatToDo(d: DrugRecord): boolean | null {
  const g = d.guidance;
  if (!g || !g.n_jurisdictions) return null;
  return g.jurisdictions_specific_action > 0;
}

/** Capitalise the first letter of each prescriber specialty, joined. */
export function prescriberText(d: DrugRecord): string {
  return (d.prescribers ?? []).map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(", ");
}
