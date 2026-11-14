// Patient-side logic (build plan Step 4). Dependency-free; runs in Node 24
// (`node --experimental-strip-types`) and in the browser / Next.js (pure modules only;
// load-node.ts is the one Node-specific file and is NOT re-exported here).
//
// Typical use:
//   const idx = provisionalIndex();                       // or overlayKnowledgeBase(idx, kbJson, "knowledge_base")
//   const patients = patientsFromFhirBundle(bundle);      // FHIR R4 → PatientRecord[]
//   const scores = scorePanel(patients, { config, asOf, forecast, neighborhood, drugIndex: idx, travel, places });
//   scores[0].tier.tier === "call_today"; scores[0].meds.plotY; scores[0].exposure.points
//
// Rule tables for nerd stats: MED_LEVEL_RULES, COMBINATION_RULES, EXPOSURE_POINTS,
// EXPOSURE_BANDS, READINESS_MATRIX, READINESS_MODIFIERS, TIER_RULES, FLUID_RULES, FORECAST_METHOD.

export { parseCsv } from "./csv.ts";
export { patientsFromFhirBundle, questionnaireFromMap, ageOn, conditionKey } from "./fhir.ts";
export {
  DEFENSE_LABELS,
  BODY_DEFENSES,
  TAG_TO_DEFENSE,
  normalizeDefense,
  normalizeDrugName,
  provisionalIndex,
  overlayKnowledgeBase,
  lookupProfile,
} from "./drug-profiles.ts";
export type { DrugProfileIndex } from "./drug-profiles.ts";
export { PROVISIONAL_DRUG_MAP } from "./provisional-drug-map.ts";
export { medRiskStack, combinationFlags, MED_LEVEL_RULES, MED_LEVEL_LABELS, COMBINATION_RULES } from "./med-risk.ts";
export { personalExposure, readinessLevel, EXPOSURE_POINTS, EXPOSURE_BANDS, EXPOSURE_MAX_POINTS, READINESS_MATRIX, READINESS_MODIFIERS } from "./exposure.ts";
export type { NeighborhoodData } from "./exposure.ts";
export { priorityTier, compareForCallList, TIER_ORDER, TIER_LABELS, TIER_RULES, HEATRISK_LABELS } from "./tiers.ts";
export { escalationPlan, timeBudget, checkinSchedule, toMin, fmtMin } from "./escalation.ts";
export type { TravelLookup, TravelEstimate } from "./escalation.ts";
export { matchCoolingPlace, coolingFromRoutedRows, placesFromGeoJson, hoursOn, parseClock, haversineKm, weekdayOf } from "./cooling.ts";
export type { CoolingPlace, CoolingNeeds } from "./cooling.ts";
export {
  safetyAlert,
  heatCard,
  coolingPlaceText,
  contactCheckText,
  checkinText,
  checkMessageSafety,
  fluidRule,
  isCaregiverAudience,
  plainDrugName,
  DEFENSE_BLOCKS,
  FLUID_RULES,
  CLOSING,
} from "./messages.ts";
export type { MessageContext } from "./messages.ts";
export {
  heatWaveOutlook,
  heatRiskFromCurrentJson,
  heatRiskFromReplayCsv,
  cpcFromJson,
  historyFromCsv,
  heatRiskOn,
  maxHeatRiskAhead,
  seasonCovers,
  addDays,
  daysBetween,
  FORECAST_METHOD,
} from "./forecast.ts";
export type { ForecastInputs, HeatRiskByZip, CpcOutlook, HistoricalOdds } from "./forecast.ts";
export { lifestyleSusceptibility, LIFESTYLE_POINTS, LIFESTYLE_BANDS, LIFESTYLE_CATEGORY_LABELS, LIFESTYLE_PROFILE_LABELS } from "./lifestyle.ts";
export { stackingView, systemGroupFor, DEFENSE_TO_MEDIATORS, DEFENSE_SYMPTOMS, DEFENSE_MASKS, HEAT_ILLNESS_SIGNS, SYSTEM_SOURCE } from "./stacking.ts";
export type { SystemPathwayIndex, SystemPathwayRow } from "./stacking.ts";
export { scorePatient, scorePanel, panelSummary, zipHeatRisk, countBy } from "./panel.ts";
export type { PanelContext } from "./panel.ts";
