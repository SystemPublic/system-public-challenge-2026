// Integration test on the real synthetic panel + repo data (KB / routed files used if present).
import { test } from "node:test";
import assert from "node:assert/strict";
import { panelSummary, scorePanel } from "../panel.ts";
import type { PanelContext } from "../panel.ts";
import { loadConfig, loadDrugIndex, loadForecast, loadNeighborhood, loadPatients, loadPlaces, loadRoutedCooling, loadTravel } from "../load-node.ts";
import { ROOT } from "./helpers.ts";

const cfg = loadConfig(ROOT, "sbh");
const patients = loadPatients(ROOT);
const places = loadPlaces(ROOT, cfg);
const base = {
  config: cfg,
  neighborhood: loadNeighborhood(ROOT, cfg),
  drugIndex: loadDrugIndex(ROOT, cfg).value,
  travel: loadTravel(ROOT, cfg).value,
  places,
  routedCooling: loadRoutedCooling(ROOT, cfg).value,
  placeById: new Map(places.map((p) => [p.id, p])),
  ageAsOf: "2026-11-14",
};
const replay = scorePanel(patients, { ...base, asOf: "2025-06-24", forecast: loadForecast(ROOT, cfg, "replay") } as PanelContext);
const today = scorePanel(patients, { ...base, asOf: "2026-11-14", forecast: loadForecast(ROOT, cfg, "current") } as PanelContext);

test("config loads and covers the catchment", () => {
  assert.equal(cfg.id, "sbh");
  assert.ok(cfg.catchment_zips.includes("10457"));
  assert.deepEqual(cfg.languages, ["en", "es"]);
});

test("November (HeatRisk 0): no calls, no alerts; heat cards only", () => {
  const s = panelSummary(today);
  assert.equal(s.tiers.call_today, 0);
  assert.equal(s.tiers.call_before_heat_wave, 0);
  assert.equal(s.auto_safety_alerts, 0);
  assert.equal(s.cooling_place_texts, 0);
  assert.ok(s.drill_tiers.call_today > 0);
});

test("replay day (HeatRisk 4): story patients S01, S04, S06, S08, S10 are on the call-today list", () => {
  const byId = new Map(replay.map((s) => [s.patientId, s]));
  for (const id of ["S01", "S04", "S06", "S08", "S10"]) assert.equal(byId.get(id)!.tier.tier, "call_today", id);
  assert.equal(byId.get("S01")!.heatriskToday, 4);
  assert.equal(byId.get("S01")!.escalation.noQualifyingContact, true); // only contact is out of area
  const s = panelSummary(replay);
  assert.ok(s.tiers.call_today > 0 && s.tiers.call_today < patients.length / 2, "call list is a minority of the panel");
});

test("ranks are 1..N and call-today patients come first", () => {
  assert.deepEqual(replay.map((s) => s.rank), replay.map((_, i) => i + 1));
  const firstNonCall = replay.findIndex((s) => s.tier.tier !== "call_today");
  assert.ok(replay.slice(firstNonCall).every((s) => s.tier.tier !== "call_today"));
});

test("every generated message passes the guardrails", () => {
  for (const s of [...replay, ...today]) for (const m of s.messages) assert.deepEqual(m.safetyIssues, [], `${s.patientId} ${m.kind}: ${m.text}`);
});

test("scatter coordinates are within documented ranges", () => {
  for (const s of replay) {
    assert.ok(s.exposure.points >= 0 && s.exposure.points <= s.exposure.maxPoints);
    assert.ok(s.meds.level >= 0 && s.meds.level <= 4);
    assert.ok(s.meds.plotY >= s.meds.level && s.meds.plotY < s.meds.level + 1);
  }
});

test("scoring is deterministic", () => {
  const again = scorePanel(patients, { ...base, asOf: "2025-06-24", forecast: loadForecast(ROOT, cfg, "replay") } as PanelContext);
  assert.equal(JSON.stringify(again), JSON.stringify(replay));
});
