import { test } from "node:test";
import assert from "node:assert/strict";
import type { MedicationOrder } from "../../types/patient.ts";
import { normalizeDefense, normalizeDrugName, overlayKnowledgeBase, provisionalIndex } from "../drug-profiles.ts";
import { MED_LEVEL_RULES, medRiskStack } from "../med-risk.ts";

const idx = provisionalIndex();
const meds = (...names: string[]): MedicationOrder[] => names.map((g, i) => ({ id: `m${i}`, generic: g, status: "active" }));

test("no meds → level 0, no reasons", () => {
  const r = medRiskStack([], idx);
  assert.equal(r.level, 0);
  assert.equal(r.ruleId, "L0");
  assert.deepEqual(r.reasons, []);
});

test("lithium + thiazide is a danger combination (level 4)", () => {
  const r = medRiskStack(meds("lithium", "hydrochlorothiazide"), idx);
  assert.equal(r.level, 4);
  assert.equal(r.ruleId, "L4-combo");
  assert.ok(r.combinations.some((c) => c.id === "narrow_margin_plus_fluid_or_kidney"));
});

test("lithium + SSRI is NOT a fluid/kidney combo", () => {
  const r = medRiskStack(meds("lithium", "sertraline"), idx);
  assert.ok(!r.combinations.some((c) => c.id === "narrow_margin_plus_fluid_or_kidney"));
});

test("two antipsychotics flag and level 4", () => {
  const r = medRiskStack(meds("clozapine", "haloperidol"), idx);
  assert.ok(r.combinations.some((c) => c.id === "antipsychotic_polypharmacy"));
  assert.equal(r.level, 4);
});

test("triple whammy is shown but does not raise the level by itself (null evidence)", () => {
  const r = medRiskStack(meds("lisinopril", "hydrochlorothiazide", "ibuprofen"), idx);
  const tw = r.combinations.find((c) => c.id === "triple_whammy");
  assert.ok(tw);
  assert.equal(tw!.raisesLevel, false);
  assert.match(tw!.evidence, /NULL/);
  // the ACEi + diuretic part does raise it
  assert.ok(r.combinations.some((c) => c.id === "acei_arb_plus_diuretic" && c.raisesLevel));
});

test("anticholinergic stack needs 2+ drugs and ACB ≥3", () => {
  assert.ok(medRiskStack(meds("oxybutynin", "diphenhydramine"), idx).combinations.some((c) => c.id === "anticholinergic_stack"));
  assert.ok(!medRiskStack(meds("oxybutynin"), idx).combinations.some((c) => c.id === "anticholinergic_stack"));
});

test("single storage-only drug is level 1; unknown drugs are reported, not guessed", () => {
  const r = medRiskStack(meds("epinephrine", "madeupazole"), idx);
  assert.equal(r.level, 1);
  assert.deepEqual(r.unmappedDrugs, ["madeupazole"]);
});

test("plotY stays inside its level band", () => {
  const r = medRiskStack(meds("furosemide", "lisinopril", "metoprolol", "oxybutynin"), idx);
  assert.ok(r.plotY >= r.level && r.plotY < r.level + 1);
});

test("every rule id used is documented", () => {
  const ids = new Set(MED_LEVEL_RULES.map((r) => r.id));
  for (const set of [["lithium", "hydrochlorothiazide"], ["metformin"], ["amlodipine"], ["topiramate"], ["sertraline", "metoprolol"]])
    assert.ok(ids.has(medRiskStack(meds(...set), idx).ruleId));
});

test("drug names and defenses normalize", () => {
  assert.equal(normalizeDrugName("Lithium Carbonate"), "lithium");
  assert.equal(normalizeDrugName("sacubitril / valsartan"), "sacubitril/valsartan");
  assert.equal(normalizeDrugName("amphetamine aspartate / amphetamine sulfate / dextroamphetamine saccharate"), "amphetamine mixed salts");
  assert.equal(normalizeDefense("sweat_blocked"), "sweating");
  assert.equal(normalizeDefense("thermostat"), "brain_thermostat");
  assert.equal(normalizeDefense({ id: "water_salt" }), "fluid_salt_balance");
});

test("knowledge-base DrugRecord overlay replaces provisional rows and keeps the rest", () => {
  const kb = {
    drugs: [
      {
        id: "loop_diuretics",
        names: { class_label: "Diuretic", ingredients: [{ name: "furosemide", rxcui: "4603", acb_score: 1 }, { name: "bumetanide", rxcui: "1808", acb_score: null }] },
        mechanism_groups: ["fluid_salt_loss", "bp_drop"],
        heat_stack: { sweating: { affected: "no" }, water_salt: { affected: "yes" }, kidney_clearance: { affected: "yes" }, blood_pressure: { affected: "yes" }, other: [] },
        patient_messages: [{ situation: "heat_forecast", en: "Heat warning for your water pill. Talk to your doctor or pharmacist.", es: "Aviso. Hable con su médico o farmacéutico." }],
      },
    ],
  };
  const { index, matched } = overlayKnowledgeBase(idx, kb, "knowledge_base");
  assert.equal(matched, 2);
  const f = index.byName.get("furosemide")!;
  assert.equal(f.source, "knowledge_base");
  assert.deepEqual([...f.defenses].sort(), ["blood_pressure", "fluid_salt_balance", "kidney_clearance"]);
  assert.equal(f.plainClass, "loop diuretic"); // drug-specific class kept
  assert.equal(index.byName.get("lithium")!.source, "provisional");
  assert.ok(index.kbMessages.get("furosemide")?.en);
  assert.equal(index.byRxcui.get("4603")!.source, "knowledge_base");
});

test("ACB table overlay: sourced scale wins over recalled provisional scores", () => {
  const { index } = overlayKnowledgeBase(idx, [], "knowledge_base", [{ drug_generic: "oxybutynin", acb_score: "3" }]);
  assert.equal(index.byName.get("oxybutynin")!.acb, 3);
  assert.equal(index.byName.get("metoprolol")!.acb, 0); // not on the provided scale
});
