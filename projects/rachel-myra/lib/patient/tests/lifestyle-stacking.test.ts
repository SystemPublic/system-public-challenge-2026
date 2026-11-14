import { test } from "node:test";
import assert from "node:assert/strict";
import type { MedicationOrder } from "../../types/patient.ts";
import { provisionalIndex } from "../drug-profiles.ts";
import { lifestyleSusceptibility } from "../lifestyle.ts";
import { medRiskStack } from "../med-risk.ts";
import { stackingView, systemGroupFor } from "../stacking.ts";
import type { SystemPathwayIndex } from "../stacking.ts";
import { q } from "./helpers.ts";

const idx = provisionalIndex();
const meds = (...names: string[]): MedicationOrder[] => names.map((g, i) => ({ id: `m${i}`, generic: g, status: "active" }));

// ---------------------------------------------------------------- lifestyle

test("indoors somewhere cool with AC is least susceptible", () => {
  const l = lifestyleSusceptibility(q({ workingAc: "yes", dayLocation: "indoors_ac", outdoorWorkOrSports: false, homeGetsHot: "rarely", floor: 2 }));
  assert.equal(l.category, "least");
  assert.equal(l.profile, "indoors_cool_place");
  assert.equal(l.points, 0);
});

test("outdoor worker is at least medium, and most with a hot home", () => {
  const work = lifestyleSusceptibility(q({ workingAc: "yes", dayLocation: "outdoors_or_physical_work", homeGetsHot: "rarely", floor: 2 }));
  assert.equal(work.profile, "outdoor_worker");
  assert.equal(work.category, "medium");
  const hot = lifestyleSusceptibility(q({ workingAc: "yes_but_cost_limits_use", dayLocation: "outdoors_or_physical_work", homeGetsHot: "often", floor: 2 }));
  assert.equal(hot.points, 3 + 2 + 2);
  assert.equal(hot.category, "most");
});

test("home all day without AC is medium; add a hot, high-floor home and it's most", () => {
  const l = lifestyleSusceptibility(q({ workingAc: "no", dayLocation: "home", floor: 2, homeGetsHot: "rarely" }));
  assert.deepEqual(l.factors.map((f) => f.id).sort(), ["home_all_day_hot", "no_ac"]);
  assert.equal(l.points, 4);
  assert.equal(l.category, "medium");
  const top = lifestyleSusceptibility(q({ workingAc: "no", dayLocation: "home", floor: 9, homeGetsHot: "often" }));
  assert.equal(top.category, "most");
  assert.equal(top.profile, "home_without_reliable_ac");
});

test("outdoor sport counts only when the day isn't already outdoors", () => {
  const a = lifestyleSusceptibility(q({ workingAc: "yes", dayLocation: "outdoors_or_physical_work", outdoorWorkOrSports: true, floor: 1, homeGetsHot: "rarely" }));
  assert.ok(!a.factors.some((f) => f.id === "outdoor_sport"));
  const b = lifestyleSusceptibility(q({ workingAc: "yes", dayLocation: "indoors_ac", outdoorWorkOrSports: true, floor: 1, homeGetsHot: "rarely" }));
  assert.ok(b.factors.some((f) => f.id === "outdoor_sport"));
  assert.equal(b.profile, "indoors_with_outdoor_activity");
});

test("missing answers are flagged, not guessed", () => {
  const l = lifestyleSusceptibility(null);
  assert.equal(l.profile, "unknown");
  assert.equal(l.incomplete, true);
  assert.equal(l.category, "least");
  assert.ok(l.missingAnswers.length >= 2);
});

// ---------------------------------------------------------------- stacking

const sys: SystemPathwayIndex = new Map([
  ["loop_diuretics", new Map([
    ["dehydration", { drugGroup: "loop_diuretics", mediator: "dehydration", mediatorLabel: "Dehydration / volume depletion", drugLegStudies: 1, heatLegStudies: 4 }],
    ["aki", { drugGroup: "loop_diuretics", mediator: "aki", mediatorLabel: "Acute kidney injury", drugLegStudies: 35, heatLegStudies: 12 }],
  ])],
  ["acei_arb", new Map([
    ["aki", { drugGroup: "acei_arb", mediator: "aki", mediatorLabel: "Acute kidney injury", drugLegStudies: 59, heatLegStudies: 12 }],
  ])],
]);

test("system groups map common generics", () => {
  assert.equal(systemGroupFor("furosemide"), "loop_diuretics");
  assert.equal(systemGroupFor("lisinopril"), "acei_arb");
  assert.equal(systemGroupFor("sacubitril/valsartan"), "acei_arb");
  assert.equal(systemGroupFor("empagliflozin"), "sglt2");
  assert.equal(systemGroupFor("metoprolol"), "beta_blockers");
  assert.equal(systemGroupFor("oxybutynin"), "anticholinergics");
  assert.equal(systemGroupFor("amoxicillin"), null);
});

test("drugs sharing a defense are marked stacked, with System study counts per leg", () => {
  const stack = medRiskStack(meds("furosemide", "lisinopril"), idx);
  const s = stackingView(stack, sys);
  const kidney = s.mechanisms.find((m) => m.defense === "kidney_clearance");
  if (kidney && kidney.drugs.length >= 2) {
    assert.equal(kidney.stacked, true);
    const aki = kidney.system.find((x) => x.mediator === "aki")!;
    assert.equal(aki.heatLegStudies, 12);
    const legs = Object.fromEntries(aki.drugLegs.map((l) => [l.drug, l.studies]));
    assert.equal(legs.furosemide, 35);
    assert.equal(legs.lisinopril, 59);
  }
  assert.equal(s.systemSource !== null, true);
  assert.ok(s.caveat.includes("Not a diagnosis"));
});

test("sweat blockers mask the heavy-sweating warning sign", () => {
  const s = stackingView(medRiskStack(meds("oxybutynin"), idx), null);
  if (s.mechanisms.some((m) => m.defense === "sweating")) assert.ok(s.maskedSigns.some((m) => m.sign === "heavy_sweating"));
  assert.equal(s.systemSource, null);
});

test("symptom sources count medicines plus heat; stacked needs 2+ medicines", () => {
  const s = stackingView(medRiskStack(meds("furosemide", "hydrochlorothiazide", "lisinopril"), idx), sys);
  for (const sym of s.symptoms) {
    assert.equal(sym.sources, sym.drugs.length + 1);
    assert.equal(sym.stacked, sym.drugs.length >= 2);
  }
  assert.ok(s.symptoms.some((x) => x.stacked), "two water pills + ACE inhibitor should stack at least one symptom");
});

test("no medicines → nothing stacked", () => {
  const s = stackingView(medRiskStack([], idx), sys);
  assert.equal(s.stackedMechanismCount, 0);
  assert.equal(s.symptoms.length, 0);
  assert.equal(s.maskedSigns.length, 0);
});
