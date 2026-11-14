import { test } from "node:test";
import assert from "node:assert/strict";
import type { MedicationOrder } from "../../types/patient.ts";
import { provisionalIndex } from "../drug-profiles.ts";
import type { NeighborhoodData } from "../exposure.ts";
import { EXPOSURE_MAX_POINTS, personalExposure, readinessLevel } from "../exposure.ts";
import { medRiskStack } from "../med-risk.ts";
import { priorityTier } from "../tiers.ts";
import { config, q } from "./helpers.ts";

const nb: NeighborhoodData = {
  hviByZip: new Map([["10457", 5], ["10468", 4], ["10001", 2]]),
  pctNoAcByZip: new Map([["10457", { pct: 16, area: "x", approximate: true }]]),
};
const idx = provisionalIndex();
const meds = (...names: string[]): MedicationOrder[] => names.map((g, i) => ({ id: `m${i}`, generic: g, status: "active" }));

test("reference home scores 0 in a low-HVI ZIP", () => {
  const e = personalExposure(q(), "10001", nb);
  assert.equal(e.points, 0);
  assert.equal(e.band, "low");
});

test("documented points add up (no AC + home all day + lives alone + HVI 5)", () => {
  const e = personalExposure(q({ workingAc: "no", dayLocation: "home", livesAlone: true, someoneChecksOn: false }), "10457", nb);
  const ids = e.factors.map((f) => f.id).sort();
  assert.deepEqual(ids, ["home_all_day_no_ac", "hvi_5", "lives_alone", "no_ac", "no_one_checks"]);
  assert.equal(e.points, 3 + 1 + 2 + 1 + 2);
  assert.equal(e.band, "very_high");
  assert.ok(e.points <= EXPOSURE_MAX_POINTS);
});

test("neighborhood AC rate is used only when the patient's own AC answer is missing", () => {
  assert.ok(!personalExposure(q({ workingAc: "yes" }), "10457", nb).factors.some((f) => f.id === "nbhd_low_ac"));
  const e = personalExposure(q({ workingAc: null }), "10457", nb);
  assert.ok(e.factors.some((f) => f.id === "nbhd_low_ac"));
  assert.ok(e.missingAnswers.includes("Q1 working AC"));
});

test("walk-up and high floor are separate factors", () => {
  const e = personalExposure(q({ floor: 9, hasElevator: false }), "10001", nb);
  assert.deepEqual(e.factors.map((f) => f.id).sort(), ["high_floor", "walkup"]);
});

test("readiness matrix + one-step modifiers", () => {
  const m4 = medRiskStack(meds("lithium", "hydrochlorothiazide"), idx);
  const low = personalExposure(q(), "10001", nb);
  assert.equal(readinessLevel(m4, low, 50, []).level, "high");
  assert.equal(readinessLevel(m4, low, 80, []).level, "very_high"); // age 75+ bumps one step
  const none = medRiskStack([], idx);
  assert.equal(readinessLevel(none, low, 80, ["dementia"]).level, "medium"); // two modifiers still one step
});

const tierBase = (over: Partial<Parameters<typeof priorityTier>[0]> = {}) => {
  const med = medRiskStack(meds("lithium", "hydrochlorothiazide"), idx);
  const exposure = personalExposure(q(), "10457", nb);
  return { readiness: "very_high" as const, readinessDrivers: ["lives alone"], med, exposure, q: q(), zip: "10457", heatriskToday: 0 as const, heatriskMaxNext: 0 as const, noQualifyingContact: false, ...over };
};

test("HeatRisk 0 (drill day): nobody is called, heat cards only", () => {
  const t = priorityTier(tierBase(), config().alert_rules);
  assert.equal(t.tier, "send_heat_card");
  assert.equal(t.autoSafetyAlert, false);
  assert.equal(t.coolingText, false);
  assert.match(t.gate, /drill/);
});

test("very high readiness is called at orange (2)", () => {
  const t = priorityTier(tierBase({ heatriskToday: 2 }), config().alert_rules);
  assert.equal(t.tier, "call_today");
  assert.ok(t.reasons[0].includes("HeatRisk 2"));
  assert.equal(t.autoSafetyAlert, false); // auto alert only from red (3)
});

test("high readiness at red: called only if automation can't reach anyone", () => {
  const rules = config().alert_rules;
  const covered = priorityTier(tierBase({ readiness: "high", heatriskToday: 3 }), rules);
  assert.equal(covered.tier, "send_heat_card");
  assert.equal(covered.autoSafetyAlert, true);
  const uncovered = priorityTier(tierBase({ readiness: "high", heatriskToday: 3, noQualifyingContact: true, q: q({ livesAlone: true }) }), rules);
  assert.equal(uncovered.tier, "call_today");
  assert.ok(uncovered.reasons.includes("no trusted contact close enough"));
});

test("call before the heat wave when it is forecast but hasn't started", () => {
  const t = priorityTier(tierBase({ readiness: "high", heatriskToday: 1, heatriskMaxNext: 3 }), config().alert_rules);
  assert.equal(t.tier, "call_before_heat_wave");
  const during = priorityTier(tierBase({ readiness: "high", heatriskToday: 3, heatriskMaxNext: 3 }), config().alert_rules);
  assert.notEqual(during.tier, "call_before_heat_wave");
});

test("no heat meds and good home → routine", () => {
  const t = priorityTier(tierBase({ readiness: "low", med: medRiskStack(meds("atorvastatin"), idx), heatriskToday: 4 }), config().alert_rules);
  assert.equal(t.tier, "routine");
});
