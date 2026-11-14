// Medication heat-risk stack: the call-first scatter's y-axis (spec §4.3, §6.1).
// Categories and reasons first; the ordinal `level` is a transparent rule lookup
// (MED_LEVEL_RULES, first match wins) for plotting. No multiplied risk score.

import type { CombinationFlag, DrugHeatProfile, HeatDefense, MedRiskStack, MedicationOrder } from "../types/patient.ts";
import { BODY_DEFENSES, DEFENSE_LABELS, lookupProfile } from "./drug-profiles.ts";
import type { DrugProfileIndex } from "./drug-profiles.ts";

// ---------------------------------------------------------------- class detection

const NAME_SETS: Record<string, string[]> = {
  nsaid: ["ibuprofen", "naproxen", "diclofenac", "meloxicam", "celecoxib", "indomethacin", "ketorolac"],
  acei_arb: ["lisinopril", "enalapril", "ramipril", "benazepril", "losartan", "valsartan", "irbesartan", "olmesartan", "candesartan", "telmisartan", "sacubitril/valsartan"],
  thiazide: ["hydrochlorothiazide", "chlorthalidone", "indapamide", "metolazone"],
  loop: ["furosemide", "bumetanide", "torsemide"],
  diuretic_other: ["spironolactone", "eplerenone", "triamterene", "amiloride"],
  ssri: ["sertraline", "citalopram", "escitalopram", "fluoxetine", "paroxetine", "fluvoxamine"],
  antipsychotic: ["clozapine", "olanzapine", "quetiapine", "risperidone", "haloperidol", "aripiprazole", "ziprasidone", "chlorpromazine", "lurasidone", "paliperidone"],
};

function is(p: DrugHeatProfile, cls: keyof typeof NAME_SETS | "diuretic"): boolean {
  const txt = `${p.plainClass} ${p.heatClass}`.toLowerCase();
  switch (cls) {
    case "nsaid":
      return /nsaid/.test(txt) || NAME_SETS.nsaid.includes(p.generic);
    case "acei_arb":
      return /ace inhibitor|acei|\barb\b|\barni\b|angiotensin/.test(txt) || NAME_SETS.acei_arb.includes(p.generic);
    case "thiazide":
      return /thiazide/.test(txt) || NAME_SETS.thiazide.includes(p.generic);
    case "loop":
      return /loop diuretic/.test(txt) || NAME_SETS.loop.includes(p.generic);
    case "diuretic":
      return /diuretic|thiazide/.test(txt) || [...NAME_SETS.thiazide, ...NAME_SETS.loop, ...NAME_SETS.diuretic_other].includes(p.generic);
    case "ssri":
      return /\bssri/.test(txt) || NAME_SETS.ssri.includes(p.generic);
    case "antipsychotic":
      return /antipsychotic/.test(txt) || NAME_SETS.antipsychotic.includes(p.generic);
    default:
      return false;
  }
}

const isSglt2 = (p: DrugHeatProfile) => /sglt2/i.test(`${p.plainClass} ${p.heatClass}`) || /gliflozin$/.test(p.generic);

// ---------------------------------------------------------------- combination flags (spec §6.1)

/**
 * Combination rules (spec §6.1). Evidence wording follows the knowledge base's
 * combination_rules (kb_rule ids, data/kb/knowledge_base.json); null findings shown, not hidden.
 */
export const COMBINATION_RULES: { id: string; kb_rule: string | null; label: string; evidence: string; raisesLevel: boolean; tier: "danger_combo" | "evidence" | "mechanism" | "shown_only" }[] = [
  { id: "antipsychotic_polypharmacy", kb_rule: "cr_two_antipsychotics", label: "2+ antipsychotics", evidence: "BC 2021 heat dome: two or more antipsychotics OR 4.05 for death among people with schizophrenia (any antipsychotic OR 2.43; Chen et al., Sci Rep 2025).", raisesLevel: true, tier: "danger_combo" },
  { id: "narrow_margin_plus_fluid_or_kidney", kb_rule: "cr_lithium_fluid", label: "Lithium (or another kidney-cleared, narrow-margin drug) + a fluid-losing or kidney-flow drug", evidence: "Cross-mechanism: dehydration lowers lithium clearance. Known interaction; not studied in heat (mechanism only).", raisesLevel: true, tier: "danger_combo" },
  { id: "thiazide_plus_ssri", kb_rule: "cr_thiazide_ssri_sodium", label: "Thiazide water pill + SSRI (low-sodium risk)", evidence: "Both lower sodium; drug-induced hyponatremia rises in hot periods (IJERPH 2017; JCEM 2022). The '~30% of admissions' figure is not machine-verified and is not shown.", raisesLevel: true, tier: "danger_combo" },
  { id: "acei_arb_plus_diuretic", kb_rule: "cr_diuretic_raas", label: "ACE inhibitor/ARB + water pill", evidence: "Kalisch Ellett 2016: starting an ACE inhibitor + diuretic had the highest dehydration/heat-illness admission ratio (2.79).", raisesLevel: true, tier: "evidence" },
  { id: "anticholinergic_stack", kb_rule: "cr_anticholinergic_stack", label: "Anticholinergic stack (2+ drugs, ACB total ≥3)", evidence: "Sweat blockers add up: ACB 2012 total ≥3 is the scale's clinically relevant threshold; anticholinergic burden linked to heat-wave admission, not death.", raisesLevel: true, tier: "evidence" },
  { id: "sglt2_plus_diuretic", kb_rule: "cr_sglt2_diuretic", label: "SGLT2 inhibitor + water pill", evidence: "Both remove water and salt through the urine. Mechanism only; not studied in heat.", raisesLevel: true, tier: "mechanism" },
  { id: "sweat_blocker_stack", kb_rule: null, label: "2+ sweat-blocking drugs", evidence: "Same-mechanism stacking (spec §6.1); mechanism-based, untested as a combination in heat.", raisesLevel: true, tier: "mechanism" },
  { id: "triple_whammy", kb_rule: "cr_diuretic_raas", label: "Triple whammy (water pill + NSAID + ACEi/ARB)", evidence: "Mangoni 2017: NULL for in-hospital AKI in heat waves (OR 1.02). Shown honestly; does not raise the level by itself.", raisesLevel: false, tier: "shown_only" },
  { id: "polypharmacy_5plus", kb_rule: null, label: "5 or more medicines", evidence: "Polypharmacy linked to heat-wave admission, not death. Shown; does not raise the level by itself.", raisesLevel: false, tier: "shown_only" },
];

function rule(id: string) {
  return COMBINATION_RULES.find((r) => r.id === id)!;
}

export function combinationFlags(profiles: DrugHeatProfile[], medCount: number): CombinationFlag[] {
  const flags: CombinationFlag[] = [];
  const add = (id: string, drugs: DrugHeatProfile[]) => {
    const r = rule(id);
    flags.push({ id, label: r.label, drugs: [...new Set(drugs.map((d) => d.generic))], evidence: r.evidence, raisesLevel: r.raisesLevel });
  };
  const of = (pred: (p: DrugHeatProfile) => boolean) => profiles.filter(pred);

  const aps = of((p) => is(p, "antipsychotic"));
  if (aps.length >= 2) add("antipsychotic_polypharmacy", aps);

  const nm = of((p) => p.narrowMarginKidneyCleared);
  if (nm.length) {
    const partners = of(
      (p) => !p.narrowMarginKidneyCleared && (is(p, "diuretic") || is(p, "nsaid") || is(p, "acei_arb") || isSglt2(p)),
    );
    if (partners.length) add("narrow_margin_plus_fluid_or_kidney", [...nm, ...partners]);
  }

  const thz = of((p) => is(p, "thiazide"));
  const ssri = of((p) => is(p, "ssri"));
  if (thz.length && ssri.length) add("thiazide_plus_ssri", [...thz, ...ssri]);

  const ace = of((p) => is(p, "acei_arb"));
  const diu = of((p) => is(p, "diuretic"));
  if (ace.length && diu.length) add("acei_arb_plus_diuretic", [...ace, ...diu]);

  const sglt2 = of(isSglt2);
  const waterPill = of((p) => is(p, "diuretic"));
  if (sglt2.length && waterPill.length) add("sglt2_plus_diuretic", [...sglt2, ...waterPill]);

  const acbDrugs = of((p) => p.acb >= 1);
  const acbTotal = profiles.reduce((s, p) => s + p.acb, 0);
  if (acbDrugs.length >= 2 && acbTotal >= 3) add("anticholinergic_stack", acbDrugs);

  const sweat = of((p) => p.defenses.includes("sweating"));
  if (sweat.length >= 2 && !flags.some((f) => f.id === "anticholinergic_stack")) add("sweat_blocker_stack", sweat);

  const nsaid = of((p) => is(p, "nsaid"));
  if (ace.length && diu.length && nsaid.length) add("triple_whammy", [...diu, ...nsaid, ...ace]);

  if (medCount >= 5) flags.push({ id: "polypharmacy_5plus", label: rule("polypharmacy_5plus").label, drugs: [], evidence: rule("polypharmacy_5plus").evidence, raisesLevel: false });
  return flags;
}

// ---------------------------------------------------------------- level rule table

export const MED_LEVEL_LABELS = ["none", "low", "moderate", "high", "very high"];

/** First match wins. This table is shown verbatim in nerd stats. */
export const MED_LEVEL_RULES: { id: string; level: number; rule: string }[] = [
  { id: "L4-combo", level: 4, rule: "A danger combination: 2+ antipsychotics (direct evidence), lithium/narrow-margin drug + fluid-losing/kidney-flow partner (known interaction), or thiazide + SSRI (low sodium)" },
  { id: "L4-acb", level: 4, rule: "Anticholinergic stack (ACB total ≥3 across 2+ drugs) AND 3+ body heat defenses weakened" },
  { id: "L4-stack", level: 4, rule: "Another level-raising combination AND 5+ distinct body heat defenses weakened" },
  { id: "L3-combo", level: 3, rule: "Any other level-raising combination (ACEi/ARB + water pill, anticholinergic stack, SGLT2 + water pill, 2+ sweat blockers)" },
  { id: "L3-defenses", level: 3, rule: "4 or more distinct body heat defenses weakened" },
  { id: "L3-drug", level: 3, rule: "On lithium (or another narrow-margin kidney-cleared drug) or an antipsychotic" },
  { id: "L2-defenses", level: 2, rule: "2-3 distinct body heat defenses weakened" },
  { id: "L2-core", level: 2, rule: "1 core defense weakened: sweating, brain thermostat/heat production, fluid & salt balance, or drug delivery (patch/insulin)" },
  { id: "L1", level: 1, rule: "1 other body defense weakened (blood pressure, kidneys, alertness, blood sugar, skin blood flow), or a heat-sensitive medicine to store" },
  { id: "L0", level: 0, rule: "No heat-relevant medicine in the record" },
];

const CORE: HeatDefense[] = ["sweating", "brain_thermostat", "fluid_salt_balance", "drug_delivery"];

export function medRiskStack(meds: MedicationOrder[], idx: DrugProfileIndex): MedRiskStack {
  const profiles: DrugHeatProfile[] = [];
  const unmapped: string[] = [];
  for (const m of meds) {
    const p = lookupProfile(idx, m.generic, m.rxcui);
    if (p) profiles.push(p);
    else unmapped.push(m.generic);
  }
  const byDef = new Map<HeatDefense, string[]>();
  for (const p of profiles) for (const d of p.defenses) byDef.set(d, [...(byDef.get(d) ?? []), p.generic]);
  const defenses = [...byDef.entries()]
    .sort((a, b) => b[1].length - a[1].length || BODY_DEFENSES.indexOf(a[0]) - BODY_DEFENSES.indexOf(b[0]))
    .map(([defense, drugs]) => ({ defense, label: DEFENSE_LABELS[defense].plain, drugs }));
  const body = defenses.filter((d) => d.defense !== "medicine_storage");
  const nBody = body.length;
  const flags = combinationFlags(profiles, meds.length);
  const acbTotal = profiles.reduce((s, p) => s + p.acb, 0);
  const has = (id: string) => flags.some((f) => f.id === id);

  let ruleId = "L0";
  const raising = flags.some((f) => f.raisesLevel);
  if (has("antipsychotic_polypharmacy") || has("narrow_margin_plus_fluid_or_kidney") || has("thiazide_plus_ssri")) ruleId = "L4-combo";
  else if (has("anticholinergic_stack") && nBody >= 3) ruleId = "L4-acb";
  else if (raising && nBody >= 5) ruleId = "L4-stack";
  else if (raising) ruleId = "L3-combo";
  else if (nBody >= 4) ruleId = "L3-defenses";
  else if (profiles.some((p) => p.narrowMarginKidneyCleared || is(p, "antipsychotic"))) ruleId = "L3-drug";
  else if (nBody >= 2) ruleId = "L2-defenses";
  else if (body.some((d) => CORE.includes(d.defense))) ruleId = "L2-core";
  else if (defenses.length) ruleId = "L1";
  const level = MED_LEVEL_RULES.find((r) => r.id === ruleId)!.level;

  const heatRelevant = profiles.filter((p) => p.defenses.length).map((p) => p.generic);
  const reasons: string[] = [];
  for (const f of flags.filter((f) => f.raisesLevel)) reasons.push(`${f.label}: ${f.drugs.join(" + ")}`);
  if (nBody) reasons.push(`${nBody} heat defense${nBody > 1 ? "s" : ""} weakened: ${body.map((d) => DEFENSE_LABELS[d.defense].en).join(", ")}`);
  if (acbTotal >= 3) reasons.push(`Anticholinergic burden ${acbTotal} (ACB ≥3 is clinically relevant)`);
  if (byDef.has("medicine_storage")) reasons.push(`Heat-sensitive to store: ${byDef.get("medicine_storage")!.join(", ")}`);
  for (const f of flags.filter((f) => !f.raisesLevel)) reasons.push(`${f.label} (shown; ${f.id === "triple_whammy" ? "null evidence in heat" : "context only"})`);

  return {
    level,
    levelLabel: MED_LEVEL_LABELS[level],
    plotY: +(level + Math.min(nBody, 9) / 10).toFixed(2),
    ruleId,
    defenses,
    combinations: flags,
    acbTotal,
    heatRelevantDrugs: heatRelevant,
    reasons,
    profileSources: [...new Set(profiles.map((p) => p.source))],
    unmappedDrugs: unmapped,
  };
}
