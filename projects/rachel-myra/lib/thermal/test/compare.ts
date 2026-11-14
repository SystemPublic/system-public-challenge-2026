// Parity harness: recompute every precomputed scenario with the TypeScript port
// and compare with the Python reference (data/processed/thermal_scenarios.json).
//
// Run from the repo root:
//   node --experimental-strip-types lib/thermal/test/compare.ts
// Exit code 0 = all checks passed.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { makeWeather, simulateLegs } from "../model.ts";
import type { Leg } from "../model.ts";
import { summarize, mktC } from "../metrics.ts";
import { assess } from "../advice.ts";
import type { DrugProfile } from "../advice.ts";
import { preshipCheck } from "../preship.ts";
import { PARAMS } from "../params.ts";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const scen = JSON.parse(readFileSync(join(ROOT, "data/processed/thermal_scenarios.json"), "utf8"));
const prof = JSON.parse(readFileSync(join(ROOT, "data/processed/drug_storage_profiles.json"), "utf8"));
const profiles: Record<string, DrugProfile> = Object.fromEntries(prof.profiles.map((p: DrugProfile) => [p.id, p]));

const TOL_TEMP_C = 0.05; // max |TS - Python| on any downsampled trace point
const TOL_METRIC_C = 0.05;
const TOL_MINUTES = 1.0;

let checks = 0;
let failures = 0;
let worstTrace = 0;
const fail = (msg: string) => { failures++; if (failures <= 25) console.error("FAIL:", msg); };
const check = (ok: boolean, msg: string) => { checks++; if (!ok) fail(msg); };

// --- parameters used by Python must equal the generated TS parameters
for (const [sec, vals] of Object.entries(scen.params as Record<string, Record<string, unknown>>)) {
  for (const [k, v] of Object.entries(vals)) {
    const tsv = (PARAMS as Record<string, Record<string, unknown>>)[sec]?.[k];
    check(JSON.stringify(tsv) === JSON.stringify(v), `param ${sec}.${k}: python=${JSON.stringify(v)} ts=${JSON.stringify(tsv)}`);
  }
}

const w = makeWeather(scen.weather);
const step = Math.round(scen.grid[0].trace.step_min * 60 / PARAMS.num.dt_s);

function compareScenario(s: any, label: string) {
  const env = PARAMS.env as Record<string, number>;
  const saved: Record<string, number> = {};
  for (const [k, v] of Object.entries((s.inputs.params_override?.env ?? {}) as Record<string, number>)) { saved[k] = env[k]; env[k] = v; }
  try { compareInner(s, label); } finally { Object.assign(env, saved); }
}

function compareInner(s: any, label: string) {
  const r = simulateLegs(w, s.inputs.legs as Leg[], s.inputs.packaging, s.inputs.T0_c);
  const py: number[] = s.trace.temp_c;
  let maxd = 0;
  for (let i = 0; i < py.length; i++) {
    const ts = r.temp[i * step];
    maxd = Math.max(maxd, Math.abs(ts - py[i]));
  }
  worstTrace = Math.max(worstTrace, maxd);
  check(maxd <= TOL_TEMP_C, `${label}: trace differs by ${maxd.toFixed(4)} C`);
  const p = profiles[s.drug];
  const m = summarize(r.temp, undefined, p.mkt_delta_h_kj_mol);
  check(Math.abs(m.peak_c - s.metrics.peak_c) <= TOL_METRIC_C, `${label}: peak ${m.peak_c} vs ${s.metrics.peak_c}`);
  check(Math.abs(m.mkt_c - s.metrics.mkt_c) <= TOL_METRIC_C, `${label}: MKT ${m.mkt_c} vs ${s.metrics.mkt_c}`);
  for (const th of Object.keys(s.metrics.minutes_above)) {
    check(Math.abs(m.minutes_above[th] - s.metrics.minutes_above[th]) <= TOL_MINUTES, `${label}: minutes>${th} ${m.minutes_above[th]} vs ${s.metrics.minutes_above[th]}`);
  }
  const a = assess(r.temp, p);
  check(a.tier === s.advice.tier, `${label}: tier ${a.tier} vs ${s.advice.tier}`);
  check(a.matched_evidence === s.advice.matched_evidence, `${label}: evidence ${a.matched_evidence} vs ${s.advice.matched_evidence}`);
}

let nScen = 0;
for (const s of scen.hero.scenarios) { compareScenario(s, `hero ${s.id}`); nScen++; }
for (const s of scen.hero.sensitivity_hot_truck.scenarios) { compareScenario(s, `hero ${s.id}`); nScen++; }
for (const s of scen.grid) { compareScenario(s, `grid ${s.id}`); nScen++; }
for (const s of scen.home) { compareScenario(s, `home ${s.id}`); nScen++; }

let nPre = 0;
for (const pc of scen.preship) {
  const i = pc.inputs;
  const r = preshipCheck({ profile: profiles[pc.drug], weather: w, shipDay: pc.ship_day, speed: i.speed, packaging: i.packaging,
    deliveryWindow: i.delivery_window, doorstep: i.doorstep, expectedDwellH: i.expected_dwell_h, daysOfSupply: i.days_of_supply });
  check(r.risk_tier === pc.result.risk_tier, `preship ${pc.id}: risk ${r.risk_tier} vs ${pc.result.risk_tier}`);
  check(r.recommended_action === pc.result.recommended_action, `preship ${pc.id}: action ${r.recommended_action} vs ${pc.result.recommended_action}`);
  check(r.options.length === pc.result.options.length, `preship ${pc.id}: #options`);
  r.options.forEach((o, k) => {
    const q = pc.result.options[k];
    check(o.action === q.action && o.tier === q.tier, `preship ${pc.id}: option ${k} ${o.action}/${o.tier} vs ${q.action}/${q.tier}`);
    check(Math.abs(o.peak_c - q.peak_c) <= TOL_METRIC_C, `preship ${pc.id}: option ${o.action} peak ${o.peak_c} vs ${q.peak_c}`);
  });
  nPre++;
}

// --- small analytic checks on the TS side
check(Math.abs(mktC([25, 25, 25, 25]) - 25) < 1e-9, "MKT of a constant equals the constant");
const fl = [20, 30, 20, 30, 40, 15];
check(mktC(fl) >= fl.reduce((a, b) => a + b, 0) / fl.length, "MKT >= arithmetic mean");

console.log(`TS vs Python: ${nScen} scenarios, ${nPre} pre-ship checks, ${checks} checks, ${failures} failures; worst trace difference ${worstTrace.toExponential(2)} C (tolerance ${TOL_TEMP_C} C)`);
process.exit(failures ? 1 : 0);
