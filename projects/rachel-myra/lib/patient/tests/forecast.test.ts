import { test } from "node:test";
import assert from "node:assert/strict";
import type { ForecastInputs } from "../forecast.ts";
import { addDays, daysBetween, heatWaveOutlook, maxHeatRiskAhead, seasonCovers } from "../forecast.ts";

const inp: ForecastInputs = {
  heatrisk: new Map([["10457", [{ date: "2026-07-10", level: 1 }, { date: "2026-07-11", level: 3 }, { date: "2026-07-12", level: 2 }]]]),
  heatriskLabel: "test HeatRisk",
  cpc: [
    { outlook: "6-10 day temperature", issued: "2026-07-09", valid_start: "2026-07-15", valid_end: "2026-07-19", valid_season: null, favored_category: "Above", p_above_normal_est_pct: 60 },
    { outlook: "Week 3-4 temperature", issued: "2026-07-09", valid_start: "2026-07-25", valid_end: "2026-08-07", valid_season: null, favored_category: "EC", p_above_normal_est_pct: 33.33 },
    { outlook: "Seasonal temperature lead 1", issued: "2026-07-01", valid_start: null, valid_end: null, valid_season: "ASO 2026", favored_category: "Above", p_above_normal_est_pct: 50 },
    { outlook: "Seasonal temperature lead 9", issued: "2027-01-01", valid_start: null, valid_end: null, valid_season: "SON 2026", favored_category: "Above", p_above_normal_est_pct: 90 },
  ],
  history: { pInHeatwave: new Map([["07-10", 0.2], ["07-11", 0.2], ["07-16", 0.25], ["07-30", 0.2], ["09-20", 0.02], ["11-14", 0]]), pWithin14d: new Map(), column: "test" },
};

test("date helpers", () => {
  assert.equal(addDays("2026-12-31", 1), "2027-01-01");
  assert.equal(daysBetween("2026-11-14", "2026-11-21"), 7);
});

test("0-7 days: HeatRisk level, not a probability", () => {
  const o = heatWaveOutlook("2026-07-11", "2026-07-10", "10457", inp);
  assert.equal(o.window, "0-7d forecast");
  assert.equal(o.heatrisk, 3);
  assert.equal(o.probability, null);
  assert.equal(o.barFraction, 0.75);
});

test("6-14 days: CPC tilt of historical odds", () => {
  const o = heatWaveOutlook("2026-07-16", "2026-07-10", "10457", inp);
  assert.equal(o.window, "6-14d outlook");
  assert.ok(Math.abs(o.probability! - 0.25 * (60 / (100 / 3))) < 1e-9);
});

test("equal chances leaves history unchanged; week 3-4 window", () => {
  const o = heatWaveOutlook("2026-07-30", "2026-07-10", "10457", inp);
  assert.equal(o.window, "week 3-4 outlook");
  assert.ok(Math.abs(o.probability! - 0.2) < 1e-3);
});

test("seasonal outlook; outlooks issued after the as-of date are ignored", () => {
  const o = heatWaveOutlook("2026-09-20", "2026-07-10", "10457", inp);
  assert.equal(o.window, "monthly/seasonal outlook");
  assert.match(o.source, /ASO 2026/);
});

test("history-only fallback; November reads 0 (the drill talking point)", () => {
  const o = heatWaveOutlook("2026-11-14", "2026-07-10", "10457", inp);
  assert.equal(o.window, "history only");
  assert.equal(o.probability, 0);
});

test("seasonCovers handles year-spanning seasons", () => {
  assert.equal(seasonCovers("DJF 2026-2027", "2026-12-15"), true);
  assert.equal(seasonCovers("DJF 2026-2027", "2027-02-15"), true);
  assert.equal(seasonCovers("DJF 2026-2027", "2026-02-15"), false);
  assert.equal(seasonCovers("NDJ 2026-2027", "2027-01-13"), true);
  assert.equal(seasonCovers("JJA 2027", "2027-07-01"), true);
  assert.equal(seasonCovers("Nov 2026", "2026-11-30"), true);
  assert.equal(seasonCovers("Nov 2026", "2025-11-30"), false);
});

test("max HeatRisk ahead excludes today", () => {
  assert.equal(maxHeatRiskAhead(inp, "10457", "2026-07-10", 7), 3);
  assert.equal(maxHeatRiskAhead(inp, "10457", "2026-07-11", 7), 2);
});
