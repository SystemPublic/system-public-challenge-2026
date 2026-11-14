// Score the synthetic panel for (a) today and (b) the replayed heat-wave day.
//
//   node --experimental-strip-types scripts/compute_panel.ts [--today YYYY-MM-DD] [--system sbh]
//
// Writes data/processed/panel_scores_today.json, panel_scores_replay.json and
// panel_scores_summary.json. SYNTHETIC data only. Deterministic for a given --today.

import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  COMBINATION_RULES,
  EXPOSURE_BANDS,
  EXPOSURE_MAX_POINTS,
  EXPOSURE_POINTS,
  FLUID_RULES,
  FORECAST_METHOD,
  MED_LEVEL_RULES,
  READINESS_MATRIX,
  READINESS_MODIFIERS,
  TIER_LABELS,
  TIER_RULES,
  addDays,
  heatWaveOutlook,
  panelSummary,
  scorePanel,
} from "../lib/patient/index.ts";
import type { PanelContext } from "../lib/patient/index.ts";
import {
  loadConfig,
  loadDrugIndex,
  loadForecast,
  loadNeighborhood,
  loadPatients,
  loadPlaces,
  loadRoutedCooling,
  loadSystemPathways,
  loadTravel,
} from "../lib/patient/load-node.ts";
import type { PatientScore } from "../lib/types/patient.ts";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const arg = (k: string, d: string) => {
  const i = process.argv.indexOf(k);
  return i > 0 ? process.argv[i + 1] : d;
};
const TODAY = arg("--today", new Date().toISOString().slice(0, 10));
const SYSTEM = arg("--system", "sbh");
const REPLAY_DAY = "2025-06-24";

const cfg = loadConfig(ROOT, SYSTEM);
const patients = loadPatients(ROOT);
const drugs = loadDrugIndex(ROOT, cfg);
const travel = loadTravel(ROOT, cfg);
const routedCooling = loadRoutedCooling(ROOT, cfg);
const places = loadPlaces(ROOT, cfg);
const placeById = new Map(places.map((p) => [p.id, p]));
const neighborhood = loadNeighborhood(ROOT, cfg);
const systemPathways = loadSystemPathways(ROOT);
const dataNotes = [...drugs.notes, ...travel.notes, ...routedCooling.notes, ...systemPathways.notes];

const RULES = {
  med_level_rules: MED_LEVEL_RULES,
  combination_rules: COMBINATION_RULES,
  exposure_points: EXPOSURE_POINTS,
  exposure_bands: EXPOSURE_BANDS,
  exposure_max_points: EXPOSURE_MAX_POINTS,
  readiness_matrix: { rows: "medication level 0-4", cols: ["low", "medium", "high", "very_high"], matrix: READINESS_MATRIX },
  readiness_modifiers: READINESS_MODIFIERS,
  tier_rules: TIER_RULES,
  fluid_rules: FLUID_RULES,
  forecast_method: FORECAST_METHOD,
  alert_rules: cfg.alert_rules,
  escalation: cfg.escalation,
};

function compact(s: PatientScore) {
  const send = s.messages.filter((m) => m.sendToday);
  return {
    rank: s.rank,
    patient_id: s.patientId,
    story: s.storyLabel,
    age: s.age,
    zip: s.zip,
    heatrisk_today: s.heatriskToday,
    tier: s.tier.tier,
    tier_label: TIER_LABELS[s.tier.tier],
    drill_tier: s.drillTier.tier,
    why: s.tier.reasons,
    readiness: s.readiness.level,
    readiness_drivers: s.readiness.drivers,
    x_exposure_points: s.exposure.points,
    exposure_factors: s.exposure.factors.map((f) => `${f.label} (+${f.points})`),
    y_med_level: s.meds.level,
    y_plot: s.meds.plotY,
    med_rule: s.meds.ruleId,
    med_reasons: s.meds.reasons,
    escalation: {
      t_max_min: s.escalation.tMaxMin,
      t_wait_min: s.escalation.tWaitMin,
      t_contact_min: s.escalation.tContactMin,
      allowed_travel_min: s.escalation.allowedTravelMin,
      resend_at_min: s.escalation.resendAtMin,
      contacts: s.escalation.contacts.map((c) => `${c.relationship}: ${c.travelMin ?? "?"} min ${c.travelMode ?? ""} (${c.travelSource}) → ${c.eligible ? "eligible" : "too far"}`),
      fallback: s.escalation.fallback,
      checkins: s.escalation.checkinTimes,
      worst_case_unnoticed_min: s.escalation.worstCaseUnnoticedMin,
    },
    cooling: s.cooling.best
      ? `${s.cooling.best.name} (${s.cooling.best.category}), ${s.cooling.best.travelMin} min ${s.cooling.best.travelMode}, leave by ${s.cooling.best.leaveBy}${s.cooling.best.caveats.length ? `; ${s.cooling.best.caveats.join("; ")}` : ""}`
      : s.cooling.note,
    messages_sent_today: send.map((m) => m.kind),
    message_preview: Object.fromEntries(s.messages.map((m) => [m.kind, m.text])),
  };
}

function run(scenario: "today" | "replay", asOf: string) {
  const forecast = loadForecast(ROOT, cfg, scenario === "today" ? "current" : "replay");
  const ctx: PanelContext = { config: cfg, asOf, forecast, neighborhood, drugIndex: drugs.value, travel: travel.value, places, routedCooling: routedCooling.value, placeById, ageAsOf: TODAY, systemPathways: systemPathways.value };
  const scores = scorePanel(patients, ctx);
  const summary = panelSummary(scores);
  const defaultZip = cfg.demo_zips.includes("10457") ? "10457" : cfg.demo_zips[0];
  const leads = [0, 1, 2, 3, 6, 7, 10, 14, 21, 30, 60, 120, 180, 240];
  const outlook = { zip: defaultZip, series: leads.map((d) => heatWaveOutlook(addDays(asOf, d), asOf, defaultZip, forecast)) };
  const story = scores.filter((s) => s.storyLabel).sort((a, b) => a.patientId.localeCompare(b.patientId));
  const out = {
    meta: {
      synthetic: true,
      note: "SYNTHETIC patients only. No real people. Not clinical advice.",
      health_system: { id: cfg.id, name: cfg.name },
      scenario,
      as_of: asOf,
      forecast_source: forecast.heatriskLabel,
      data_notes: dataNotes,
      generated_by: "scripts/compute_panel.ts (lib/patient)",
    },
    summary,
    outlook,
    scatter: scores.map((s) => ({
      patient_id: s.patientId,
      rank: s.rank,
      story: !!s.storyLabel,
      x: s.exposure.points,
      y: s.meds.plotY,
      med_level: s.meds.level,
      exposure_band: s.exposure.band,
      readiness: s.readiness.level,
      tier: s.tier.tier,
      drill_tier: s.drillTier.tier,
    })),
    call_list: scores.filter((s) => s.tier.tier === "call_today" || s.tier.tier === "call_before_heat_wave").map(compact),
    drill_call_list_top25: [...scores]
      .filter((s) => s.drillTier.tier === "call_today")
      .slice(0, 25)
      .map((s) => ({ rank: s.rank, patient_id: s.patientId, why: s.drillTier.reasons })),
    story_patients: story.map(compact),
    rules: RULES,
    patients: scores,
  };
  const file = join(ROOT, `data/processed/panel_scores_${scenario}.json`);
  writeFileSync(file, JSON.stringify(out, null, 1));
  return { file, summary, story: story.map(compact), outlook, asOf };
}

const today = run("today", TODAY);
const replay = run("replay", REPLAY_DAY);

const summaryOut = {
  meta: { synthetic: true, health_system: cfg.id, data_notes: dataNotes },
  today: { as_of: today.asOf, ...today.summary, outlook_today: today.outlook.series[0] },
  replay: { as_of: replay.asOf, ...replay.summary, outlook_today: replay.outlook.series[0] },
  story_patients_replay: replay.story.map((s) => ({
    patient_id: s.patient_id,
    story: s.story,
    rank: s.rank,
    tier: s.tier,
    readiness: s.readiness,
    x: s.x_exposure_points,
    y_level: s.y_med_level,
    why: s.why,
    escalation: s.escalation,
    cooling: s.cooling,
    sent: s.messages_sent_today,
  })),
  story_patients_today: today.story.map((s) => ({ patient_id: s.patient_id, tier: s.tier, drill_tier: s.drill_tier, readiness: s.readiness, x: s.x_exposure_points, y_level: s.y_med_level })),
};
writeFileSync(join(ROOT, "data/processed/panel_scores_summary.json"), JSON.stringify(summaryOut, null, 1));

for (const r of [today, replay]) {
  console.log(`\n== ${r.asOf} → ${r.file.replace(ROOT + "/", "")}`);
  console.log(`   ${r.summary.headline}`);
  console.log(`   tiers ${JSON.stringify(r.summary.tiers)}  drill ${JSON.stringify(r.summary.drill_tiers)}`);
  console.log(`   auto safety alerts ${r.summary.auto_safety_alerts}, cooling texts ${r.summary.cooling_place_texts}, msg safety issues ${r.summary.messages.safety_issues}`);
  console.log(`   outlook today: ${r.outlook.series[0].window} ${r.outlook.series[0].heatrisk ?? r.outlook.series[0].probability} (${r.outlook.series[0].source})`);
  for (const s of r.story) console.log(`   ${s.patient_id} #${s.rank} ${s.tier} (drill ${s.drill_tier}) readiness=${s.readiness} x=${s.x_exposure_points} y=${s.y_med_level}`);
}
console.log("\nnotes:\n  " + dataNotes.join("\n  "));
