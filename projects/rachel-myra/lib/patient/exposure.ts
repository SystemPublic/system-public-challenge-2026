// Personal heat exposure: the call-first scatter's x-axis (spec §4.3, §4.5a), and the
// personal heat readiness level (spec §9) that combines it with the medication stack.
// Fixed, documented points per factor (EXPOSURE_POINTS), weighted by the evidence in §4.5a.

import type { ExposureFactor, ExposureResult, MedRiskStack, QuestionnaireAnswers, ReadinessLevel } from "../types/patient.ts";

export interface NeighborhoodData {
  hviByZip: Map<string, number>;
  pctNoAcByZip: Map<string, { pct: number; area: string; approximate: boolean }>;
}

/** Points table, shown verbatim in nerd stats. "basis" = why this factor and weight. */
export const EXPOSURE_POINTS = {
  no_ac: { points: 3, label: "No working AC at home", basis: "Strongest home factor: working AC OR 0.03 (Cincinnati 1999); AC protective (Chicago 1995, Semenza NEJM 1996, verify); NYC heat deaths mostly at home without AC" },
  ac_cost_limited: { points: 2, label: "Has AC but cost limits use", basis: "NYC heat-mortality reports: AC present but not used counts as no cooling; slightly below no AC" },
  outdoors_day: { points: 2, label: "Spends the day outdoors or doing physical work", basis: "Direct heat load and exertion (occupational heat illness)" },
  outdoor_sport: { points: 1, label: "Outdoor work or sports", basis: "Exertion in heat; counted only if not already 'outdoors' for Q2" },
  home_all_day_no_ac: { points: 1, label: "Home all day without reliable AC", basis: "Not leaving home raised risk (Chicago 1995)" },
  lives_alone: { points: 2, label: "Lives alone", basis: "Chicago 1995 and BC 2021: most who died were alone at home" },
  no_one_checks: { points: 1, label: "Lives alone and no one checks on them", basis: "Social contact protective (Chicago 1995)" },
  cannot_reach_cool: { points: 2, label: "Cannot get to a cool place", basis: "Access to cooled places protective (Chicago 1995); mobility limits" },
  reach_cool_with_help: { points: 1, label: "Can reach a cool place only with help", basis: "Half weight of 'cannot'" },
  high_floor: { points: 1, label: "Lives on floor 7 or higher", basis: "ASSUMPTION: upper floors run hotter (heat rises, roof gain); mechanism, not a measured effect" },
  walkup: { points: 1, label: "Floor 4+ with no elevator", basis: "ASSUMPTION: harder to leave and to reach; egress/mobility" },
  home_gets_hot: { points: 1, label: "Home often gets hot", basis: "Self-reported indoor heat (optional question)" },
  power_dependent: { points: 1, label: "Uses power-dependent equipment", basis: "Power outages during heat waves (spec §4.3 playbook reminders)" },
  hvi_5: { points: 2, label: "Neighborhood Heat Vulnerability Index 5 (highest)", basis: "NYC HVI is built from heat-mortality predictors (surface temp, green space, AC, income, race)" },
  hvi_4: { points: 1, label: "Neighborhood Heat Vulnerability Index 4", basis: "As above, one step lower" },
  nbhd_low_ac: { points: 1, label: "Neighborhood: 15%+ of homes lack AC (own AC unknown)", basis: "NYC HVS; used only when the patient's own AC answer is missing (personal answer wins)" },
} as const;

export type ExposureFactorId = keyof typeof EXPOSURE_POINTS;

/** Highest achievable total (mutually exclusive factors counted once). */
export const EXPOSURE_MAX_POINTS = 3 + 2 + 1 + 2 + 1 + 2 + 1 + 1 + 1 + 1 + 2; // = 17

export const EXPOSURE_BANDS: { band: ExposureResult["band"]; min: number }[] = [
  { band: "very_high", min: 9 },
  { band: "high", min: 6 },
  { band: "medium", min: 3 },
  { band: "low", min: 0 },
];

export function personalExposure(q: QuestionnaireAnswers | null, zip: string, nb: NeighborhoodData): ExposureResult {
  const factors: ExposureFactor[] = [];
  const add = (id: ExposureFactorId) => factors.push({ id, label: EXPOSURE_POINTS[id].label, points: EXPOSURE_POINTS[id].points, basis: EXPOSURE_POINTS[id].basis });
  const missing: string[] = [];
  const a = q ?? ({} as Partial<QuestionnaireAnswers>);

  if (a.workingAc === "no") add("no_ac");
  else if (a.workingAc === "yes_but_cost_limits_use") add("ac_cost_limited");
  else if (a.workingAc == null) missing.push("Q1 working AC");

  if (a.dayLocation === "outdoors_or_physical_work") add("outdoors_day");
  else if (a.dayLocation === "home" && a.workingAc && a.workingAc !== "yes") add("home_all_day_no_ac");
  else if (a.dayLocation == null) missing.push("Q2 where you spend the day");
  if (a.outdoorWorkOrSports && a.dayLocation !== "outdoors_or_physical_work") add("outdoor_sport");

  if (a.floor == null) missing.push("Q3 floor");
  else {
    if (a.floor >= 7) add("high_floor");
    if (a.floor >= 4 && a.hasElevator === false) add("walkup");
  }

  if (a.livesAlone === true) {
    add("lives_alone");
    if (a.someoneChecksOn === false) add("no_one_checks");
  } else if (a.livesAlone == null) missing.push("Q4 lives alone");

  if (a.canReachCoolPlace === "no") add("cannot_reach_cool");
  else if (a.canReachCoolPlace === "with_help") add("reach_cool_with_help");
  else if (a.canReachCoolPlace == null) missing.push("Q5 can reach a cool place");

  if (a.homeGetsHot === "often") add("home_gets_hot");
  if (a.powerDependentEquipment && a.powerDependentEquipment.length) add("power_dependent");

  const hvi = nb.hviByZip.get(zip) ?? null;
  if (hvi === 5) add("hvi_5");
  else if (hvi === 4) add("hvi_4");
  const ac = nb.pctNoAcByZip.get(zip) ?? null;
  if (a.workingAc == null && ac && ac.pct >= 15) add("nbhd_low_ac");

  const points = factors.reduce((s, f) => s + f.points, 0);
  const band = EXPOSURE_BANDS.find((b) => points >= b.min)!.band;
  return {
    points,
    maxPoints: EXPOSURE_MAX_POINTS,
    band,
    factors,
    neighborhood: { hvi, pctNoAc: ac?.pct ?? null, acArea: ac?.area ?? null, acAreaApproximate: ac?.approximate ?? false },
    missingAnswers: missing,
  };
}

// ---------------------------------------------------------------- readiness level (spec §9)

const LEVELS: ReadinessLevel[] = ["low", "medium", "high", "very_high"];
const BAND_IDX = { low: 0, medium: 1, high: 2, very_high: 3 } as const;

/** Rows = medication level 0-4, columns = exposure band low → very high. Shown in nerd stats. */
export const READINESS_MATRIX: ReadinessLevel[][] = [
  ["low", "low", "low", "medium"],
  ["low", "low", "medium", "medium"],
  ["low", "medium", "high", "high"],
  ["medium", "high", "high", "very_high"],
  ["high", "high", "very_high", "very_high"],
];

export const READINESS_MODIFIERS = [
  { id: "age_75_plus", rule: "Age 75+ → one step up (older adults are most likely to die in heat; spec §4.5)" },
  { id: "cognition", rule: "Dementia or schizophrenia in the record → one step up (may not notice heat or thirst)" },
  { id: "young_child", rule: "Child under 5 → one step up (depends on others to cool them)" },
];

export function readinessLevel(
  med: MedRiskStack,
  exp: ExposureResult,
  age: number,
  conditionKeys: string[],
): { level: ReadinessLevel; drivers: string[]; modifiers: string[] } {
  let i = LEVELS.indexOf(READINESS_MATRIX[Math.min(med.level, 4)][BAND_IDX[exp.band]]);
  const modifiers: string[] = [];
  if (age >= 75) modifiers.push("age 75+");
  else if (age < 5) modifiers.push("child under 5");
  if (conditionKeys.some((k) => k === "dementia" || k === "schizophrenia")) modifiers.push(conditionKeys.includes("dementia") ? "dementia" : "schizophrenia");
  if (modifiers.length && i < 3) i++; // at most one step, whatever the number of modifiers
  const topFactors = [...exp.factors].sort((a, b) => b.points - a.points).slice(0, 3).map((f) => f.label.toLowerCase());
  const medBits = med.combinations.filter((c) => c.raisesLevel).map((c) => c.drugs.join(" + "));
  const drugs = medBits.length ? [`on ${medBits[0]}`] : med.heatRelevantDrugs.length ? [`on ${med.heatRelevantDrugs.slice(0, 3).join(", ")}`] : [];
  return { level: LEVELS[i], drivers: [...topFactors, ...drugs, ...modifiers], modifiers };
}
