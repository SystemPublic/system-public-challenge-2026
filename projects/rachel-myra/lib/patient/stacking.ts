// Systems view of a patient's medicines in heat (spec §6.1):
//  1. Mechanism stacking: which body heat defenses 2+ medicines weaken at once, with the
//     System Public Graph evidence behind each leg (drug → mediator, heat → mediator).
//  2. Symptom stacking: which heat-illness warning signs (CDC list) are also produced by
//     the patient's medicines, and which warning signs a medicine can hide.
// Mechanism-based and descriptive: no risk number, no diagnosis, no dose advice.

import type { HeatDefense, MedRiskStack, StackingResult } from "../types/patient.ts";
import { DEFENSE_LABELS } from "./drug-profiles.ts";

// ---------------------------------------------------------------- System graph evidence

/** One row of data/processed/system_pathways.csv (drug group × mediator). */
export interface SystemPathwayRow {
  drugGroup: string;
  mediator: string;
  mediatorLabel: string;
  drugLegStudies: number;
  heatLegStudies: number;
}

/** drugGroup → mediator → row. Built in load-node.ts from system_pathways.csv. */
export type SystemPathwayIndex = Map<string, Map<string, SystemPathwayRow>>;

export const SYSTEM_SOURCE =
  "System Public Graph, Dataverse v2.1 bulk release (data/processed/system_pathways.csv; variable-name matching, ~20% extraction error per System)";

/** Body defense → System mediator concepts used in the pathway scan. */
export const DEFENSE_TO_MEDIATORS: Partial<Record<HeatDefense, string[]>> = {
  fluid_salt_balance: ["dehydration", "hyponatremia"],
  kidney_clearance: ["aki"],
  blood_pressure: ["bp_hypotension"],
  sweating: ["sweating"],
  brain_thermostat: ["body_temp"],
};

/** Generic name → System drug group (ids in data/processed/system_pathways.csv). */
const GROUP_RULES: { group: string; test: (g: string) => boolean }[] = [
  { group: "lithium", test: (g) => g.startsWith("lithium") },
  { group: "loop_diuretics", test: (g) => ["furosemide", "bumetanide", "torsemide"].includes(g) },
  { group: "thiazides", test: (g) => ["hydrochlorothiazide", "chlorthalidone", "indapamide", "metolazone"].includes(g) },
  { group: "acei_arb", test: (g) => /pril$|sartan$/.test(g) || g.includes("valsartan") },
  { group: "sglt2", test: (g) => /gliflozin$/.test(g) },
  { group: "insulin", test: (g) => g.includes("insulin") },
  { group: "metformin", test: (g) => g === "metformin" },
  { group: "sulfonylureas", test: (g) => ["glipizide", "glyburide", "glimepiride", "gliclazide"].includes(g) },
  { group: "anticholinergics", test: (g) => ["oxybutynin", "tolterodine", "solifenacin", "trospium", "darifenacin", "fesoterodine", "benztropine", "trihexyphenidyl", "diphenhydramine", "hydroxyzine", "glycopyrrolate"].includes(g) },
  { group: "antipsychotics", test: (g) => ["clozapine", "olanzapine", "quetiapine", "risperidone", "haloperidol", "aripiprazole", "ziprasidone", "chlorpromazine", "lurasidone", "paliperidone"].includes(g) },
  { group: "ssris", test: (g) => ["sertraline", "citalopram", "escitalopram", "fluoxetine", "paroxetine", "fluvoxamine"].includes(g) },
  { group: "topiramate_zonisamide", test: (g) => g === "topiramate" || g === "zonisamide" },
  { group: "adhd_stimulants", test: (g) => /amphetamine|methylphenidate/.test(g) },
  { group: "beta_blockers", test: (g) => /olol$|olol /.test(g) || g === "carvedilol" || g === "labetalol" },
  { group: "opioids_fentanyl", test: (g) => ["fentanyl", "buprenorphine", "morphine", "oxycodone", "hydromorphone", "methadone", "tramadol"].includes(g) },
  { group: "nsaids", test: (g) => ["ibuprofen", "naproxen", "diclofenac", "meloxicam", "celecoxib", "indomethacin", "ketorolac"].includes(g) },
  { group: "benzodiazepines", test: (g) => /azepam$|azolam$/.test(g) },
  { group: "epinephrine_ai", test: (g) => g === "epinephrine" },
];

export function systemGroupFor(generic: string): string | null {
  const g = generic.toLowerCase().trim();
  return GROUP_RULES.find((r) => r.test(g))?.group ?? null;
}

// ---------------------------------------------------------------- symptoms

/** Heat-illness warning signs (CDC "Heat-Related Illnesses" list: heat exhaustion and heat stroke). */
export const HEAT_ILLNESS_SIGNS = {
  dizziness: "Dizziness",
  fainting: "Fainting",
  confusion: "Confusion",
  nausea: "Nausea or vomiting",
  headache: "Headache",
  muscle_cramps: "Muscle cramps",
  tiredness: "Tiredness or weakness",
  fast_pulse: "Fast pulse",
  heavy_sweating: "Heavy sweating",
  hot_dry_skin: "Hot, red, dry skin",
  high_body_temp: "High body temperature",
} as const;
export type HeatSign = keyof typeof HEAT_ILLNESS_SIGNS;

/**
 * Defense weakened by a medicine → heat-illness signs the medicine's own effects can also
 * produce (so they pile up with heat). Mechanism-based, from the defense definitions in
 * drug-profiles.ts; shown with that caveat. Not patient-specific predictions.
 */
export const DEFENSE_SYMPTOMS: Partial<Record<HeatDefense, HeatSign[]>> = {
  blood_pressure: ["dizziness", "fainting"],
  fluid_salt_balance: ["dizziness", "confusion", "nausea", "headache", "muscle_cramps", "tiredness"],
  kidney_clearance: ["confusion", "nausea", "tiredness"],
  alertness: ["confusion", "tiredness"],
  blood_sugar: ["confusion", "dizziness", "heavy_sweating", "headache"],
  drug_delivery: ["confusion", "dizziness", "tiredness"],
  brain_thermostat: ["high_body_temp"],
  sweating: ["hot_dry_skin", "high_body_temp"],
};

/** Defense weakened → warning signs that may NOT appear, so heat illness is easier to miss. */
export const DEFENSE_MASKS: Partial<Record<HeatDefense, { sign: HeatSign; why: string }[]>> = {
  sweating: [{ sign: "heavy_sweating", why: "the medicine reduces sweating, so the usual 'sweating a lot' warning may be missing" }],
  skin_blood_flow: [{ sign: "fast_pulse", why: "the medicine slows the heart, so a racing pulse may not show up" }],
  alertness: [{ sign: "confusion", why: "drowsiness or slower thinking can hide early confusion, and thirst may not be felt" }],
};

// ---------------------------------------------------------------- main

export function stackingView(med: MedRiskStack, sys: SystemPathwayIndex | null): StackingResult {
  const body = med.defenses.filter((d) => d.defense !== "medicine_storage");

  const mechanisms: StackingResult["mechanisms"] = body.map((d) => {
    const mediators = DEFENSE_TO_MEDIATORS[d.defense] ?? [];
    const system = mediators.map((m) => {
      let heatLeg: number | null = null;
      let label = m;
      const drugLegs = d.drugs.map((generic) => {
        const group = systemGroupFor(generic);
        const row = group && sys ? sys.get(group)?.get(m) ?? null : null;
        if (row) {
          heatLeg = row.heatLegStudies;
          label = row.mediatorLabel;
        }
        return { drug: generic, systemGroup: group, studies: row ? row.drugLegStudies : null };
      });
      if (heatLeg == null && sys) {
        for (const g of sys.values()) {
          const r = g.get(m);
          if (r) {
            heatLeg = r.heatLegStudies;
            label = r.mediatorLabel;
            break;
          }
        }
      }
      return { mediator: m, mediatorLabel: label, heatLegStudies: heatLeg, drugLegs };
    });
    const studied = system.some((s) => s.drugLegs.some((l) => (l.studies ?? 0) > 0) && (s.heatLegStudies ?? 0) > 0);
    return {
      defense: d.defense,
      label: DEFENSE_LABELS[d.defense].plain,
      drugs: d.drugs,
      stacked: d.drugs.length >= 2,
      system,
      graphNote: !mediators.length
        ? "No matching concept in the System graph scan for this defense"
        : !sys
          ? "System pathway data not loaded"
          : studied
            ? "Both legs (medicine → this effect, heat → this effect) have System findings; the combination itself is untested in heat"
            : "At least one leg has no System findings: a gap in the graph",
    };
  });

  const signSources = new Map<HeatSign, Set<string>>();
  for (const d of body) for (const s of DEFENSE_SYMPTOMS[d.defense] ?? []) {
    const set = signSources.get(s) ?? new Set<string>();
    d.drugs.forEach((g) => set.add(g));
    signSources.set(s, set);
  }
  const symptoms: StackingResult["symptoms"] = [...signSources.entries()]
    .map(([sign, drugs]) => ({ sign, label: HEAT_ILLNESS_SIGNS[sign], drugs: [...drugs], sources: drugs.size + 1, stacked: drugs.size >= 2 }))
    .sort((a, b) => b.sources - a.sources || a.label.localeCompare(b.label));

  const masked: StackingResult["maskedSigns"] = [];
  for (const d of body)
    for (const m of DEFENSE_MASKS[d.defense] ?? [])
      if (!masked.some((x) => x.sign === m.sign)) masked.push({ sign: m.sign, label: HEAT_ILLNESS_SIGNS[m.sign], drugs: d.drugs, why: m.why });

  const stackedMechanisms = mechanisms.filter((m) => m.stacked);
  const stackedSymptoms = symptoms.filter((s) => s.stacked);
  const summary: string[] = [];
  for (const m of stackedMechanisms)
    summary.push(`${m.drugs.join(" + ")} ${m.drugs.length === 2 ? "both" : "all"} weaken ${DEFENSE_LABELS[m.defense].en}, and heat strains it too`);
  if (stackedSymptoms.length) summary.push(`Heat and ${stackedSymptoms.length > 1 ? "several medicines" : "two medicines"} can each cause ${stackedSymptoms.slice(0, 3).map((s) => s.label.toLowerCase()).join(", ")}`);
  for (const m of masked) summary.push(`${m.label} may not appear: ${m.why}`);

  return {
    mechanisms,
    stackedMechanismCount: stackedMechanisms.length,
    symptoms,
    stackedSymptomCount: stackedSymptoms.length,
    maskedSigns: masked,
    summary,
    caveat:
      "Mechanism-based. Heat-illness signs from the CDC list; medicine overlaps follow each medicine's weakened heat defenses. Combinations are untested in heat unless a combination rule says otherwise. Not a diagnosis.",
    systemSource: sys ? SYSTEM_SOURCE : null,
  };
}
