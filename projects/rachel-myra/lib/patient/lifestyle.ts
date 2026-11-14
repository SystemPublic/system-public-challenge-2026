// Lifestyle heat susceptibility: least / medium / most susceptible, from daily habits only
// (where the day is spent, work and sport outdoors, indoor heat at home). Neighborhood,
// social and medication factors are deliberately left out here: they live in exposure.ts
// (x-axis) and med-risk.ts (y-axis). This is a plain-language grouping shown next to the
// patient, not a score that changes call tiers.

import type { LifestyleResult, QuestionnaireAnswers } from "../types/patient.ts";

/** Points table, shown verbatim in nerd stats. Weights follow exposure.ts bases. */
export const LIFESTYLE_POINTS = {
  outdoor_work_day: { points: 3, label: "Spends the day outdoors or doing physical work", basis: "Direct sun and exertion; occupational heat illness" },
  outdoor_sport: { points: 2, label: "Outdoor work or sports on top of the day's routine", basis: "Exertion in heat (counted only if the day isn't already outdoors)" },
  no_ac: { points: 3, label: "No working AC at home", basis: "Strongest home factor: working AC OR 0.03 (Cincinnati 1999)" },
  ac_cost_limited: { points: 2, label: "Has AC but cost limits use", basis: "AC present but unused counts as no cooling (NYC heat-mortality reports)" },
  home_all_day_hot: { points: 1, label: "Home all day without reliable AC", basis: "No break from indoor heat (Chicago 1995: not leaving home raised risk)" },
  rarely_leaves_home: { points: 1, label: "Doesn't leave home most days (no reliable AC)", basis: "As above; counted only if not already 'home all day'" },
  home_gets_hot_often: { points: 2, label: "Home often gets hot", basis: "Self-reported indoor heat" },
  home_gets_hot_sometimes: { points: 1, label: "Home sometimes gets hot", basis: "Half weight of 'often'" },
  high_floor: { points: 1, label: "Lives on floor 7 or higher", basis: "ASSUMPTION: upper floors run hotter; mechanism, not a measured effect" },
} as const;

export type LifestyleFactorId = keyof typeof LIFESTYLE_POINTS;

/** Category cut-offs (points). least: 0-2, medium: 3-5, most: 6+. */
export const LIFESTYLE_BANDS: { category: LifestyleResult["category"]; min: number }[] = [
  { category: "most", min: 6 },
  { category: "medium", min: 3 },
  { category: "least", min: 0 },
];

export const LIFESTYLE_CATEGORY_LABELS: Record<LifestyleResult["category"], string> = {
  least: "Least susceptible",
  medium: "Medium susceptibility",
  most: "Most susceptible",
};

function profileOf(a: Partial<QuestionnaireAnswers>): LifestyleResult["profile"] {
  const coolAtHome = a.workingAc === "yes";
  if (a.dayLocation === "outdoors_or_physical_work") return "outdoor_worker";
  if (a.dayLocation === "indoors_ac") return a.outdoorWorkOrSports ? "indoors_with_outdoor_activity" : "indoors_cool_place";
  if (a.dayLocation === "home") {
    if (a.workingAc == null) return "unknown";
    return coolAtHome ? (a.outdoorWorkOrSports ? "indoors_with_outdoor_activity" : "home_with_ac") : "home_without_reliable_ac";
  }
  return "unknown";
}

export const LIFESTYLE_PROFILE_LABELS: Record<LifestyleResult["profile"], string> = {
  outdoor_worker: "Outdoor worker / physical work",
  indoors_with_outdoor_activity: "Mostly indoors, with outdoor work or sports",
  indoors_cool_place: "Spends the day indoors somewhere cool",
  home_with_ac: "Home most of the day, with working AC",
  home_without_reliable_ac: "Home most of the day without reliable AC",
  unknown: "Not enough answers yet",
};

export function lifestyleSusceptibility(q: QuestionnaireAnswers | null): LifestyleResult {
  const a = q ?? ({} as Partial<QuestionnaireAnswers>);
  const factors: LifestyleResult["factors"] = [];
  const add = (id: LifestyleFactorId) => factors.push({ id, label: LIFESTYLE_POINTS[id].label, points: LIFESTYLE_POINTS[id].points, basis: LIFESTYLE_POINTS[id].basis });
  const missing: string[] = [];
  const reliableAc = a.workingAc === "yes";

  if (a.dayLocation === "outdoors_or_physical_work") add("outdoor_work_day");
  else if (a.dayLocation == null) missing.push("Where you spend the day");
  if (a.outdoorWorkOrSports && a.dayLocation !== "outdoors_or_physical_work") add("outdoor_sport");

  if (a.workingAc === "no") add("no_ac");
  else if (a.workingAc === "yes_but_cost_limits_use") add("ac_cost_limited");
  else if (a.workingAc == null) missing.push("Working AC at home");

  if (a.workingAc != null && !reliableAc) {
    if (a.dayLocation === "home") add("home_all_day_hot");
    else if (a.leavesHomeMostDays === false) add("rarely_leaves_home");
  }

  if (a.homeGetsHot === "often") add("home_gets_hot_often");
  else if (a.homeGetsHot === "sometimes") add("home_gets_hot_sometimes");

  if (a.floor != null && a.floor >= 7) add("high_floor");

  const points = factors.reduce((s, f) => s + f.points, 0);
  const category = LIFESTYLE_BANDS.find((b) => points >= b.min)!.category;
  const profile = profileOf(a);
  return {
    category,
    categoryLabel: LIFESTYLE_CATEGORY_LABELS[category],
    profile,
    profileLabel: LIFESTYLE_PROFILE_LABELS[profile],
    points,
    factors,
    missingAnswers: missing,
    // With 2+ core answers missing the category is a floor, not a judgment.
    incomplete: missing.length >= 2,
  };
}
