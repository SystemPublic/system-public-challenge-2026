// English copies of every patient message, for team members and judges who don't read Spanish.
//
// Runs the SAME lib/patient scoring as scripts/compute_panel.ts on the replay day, with each
// patient's (and contact's) language forced to "en", and keeps only the messages. Nothing is
// hand-translated: the English text comes from the same message blocks and rules.
// panel_scores_replay.json is not touched.
//
//   node --experimental-strip-types scripts/compute_messages_en.ts --today 2026-11-14
//   → data/processed/panel_messages_en_replay.json  { meta, messages: { [patientId]: PatientMessage[] } }

import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { scorePanel } from "../lib/patient/index.ts";
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

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const arg = (k: string, d: string) => {
  const i = process.argv.indexOf(k);
  return i > 0 ? process.argv[i + 1] : d;
};
const TODAY = arg("--today", new Date().toISOString().slice(0, 10));
const REPLAY_DAY = "2025-06-24"; // same as compute_panel.ts

const cfg = loadConfig(ROOT, arg("--system", "sbh"));
const drugs = loadDrugIndex(ROOT, cfg);
const travel = loadTravel(ROOT, cfg);
const routedCooling = loadRoutedCooling(ROOT, cfg);
const places = loadPlaces(ROOT, cfg);
const placeById = new Map(places.map((p) => [p.id, p]));
const neighborhood = loadNeighborhood(ROOT, cfg);
const systemPathways = loadSystemPathways(ROOT);

// Force English everywhere the message builders look for a language.
const patients = loadPatients(ROOT).map((p) => ({
  ...p,
  language: "en",
  questionnaire: p.questionnaire ? { ...p.questionnaire, preferredLanguage: "en" } : null,
  contacts: p.contacts.map((c) => ({ ...c, language: "en" })),
}));

const forecast = loadForecast(ROOT, cfg, "replay");
const ctx: PanelContext = {
  config: cfg, asOf: REPLAY_DAY, forecast, neighborhood, drugIndex: drugs.value, travel: travel.value,
  places, routedCooling: routedCooling.value, placeById, ageAsOf: TODAY, systemPathways: systemPathways.value,
};
const scores = scorePanel(patients, ctx);

const out = {
  meta: {
    synthetic: true,
    scenario: "replay",
    as_of: REPLAY_DAY,
    note: "English versions of panel_scores_replay.json messages, built by the same lib/patient rules with language forced to en. For reading only; patients are sent their own language.",
    generated_by: "scripts/compute_messages_en.ts (lib/patient)",
  },
  messages: Object.fromEntries(scores.map((s) => [s.patientId, s.messages])),
};
const file = join(ROOT, "data", "processed", "panel_messages_en_replay.json");
writeFileSync(file, JSON.stringify(out));
const n = scores.reduce((a, s) => a + s.messages.length, 0);
console.log(`wrote ${file}: ${scores.length} patients, ${n} messages`);
