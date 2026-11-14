// Panel orchestrator (pure): score every patient for one day and rank the call list.
// The app calls scorePatient / scorePanel with data it already has; the Node loaders in
// load-node.ts only exist for scripts and tests.

import type { HealthSystemConfig, HeatRiskLevel } from "../types/health-system.ts";
import type { CoolingMatch, PatientMessage, PatientRecord, PatientScore, PriorityTier } from "../types/patient.ts";
import type { CoolingPlace } from "./cooling.ts";
import { coolingFromRoutedRows, matchCoolingPlace } from "./cooling.ts";
import type { DrugProfileIndex } from "./drug-profiles.ts";
import type { TravelLookup } from "./escalation.ts";
import { escalationPlan } from "./escalation.ts";
import type { NeighborhoodData } from "./exposure.ts";
import { personalExposure, readinessLevel } from "./exposure.ts";
import { ageOn } from "./fhir.ts";
import type { ForecastInputs } from "./forecast.ts";
import { daysBetween, heatRiskOn } from "./forecast.ts";
import { medRiskStack } from "./med-risk.ts";
import { lifestyleSusceptibility } from "./lifestyle.ts";
import { stackingView } from "./stacking.ts";
import type { SystemPathwayIndex } from "./stacking.ts";
import type { MessageContext } from "./messages.ts";
import { checkMessageSafety, checkinText, contactCheckText, coolingPlaceText, heatCard, safetyAlert } from "./messages.ts";
import { TIER_ORDER, compareForCallList, priorityTier } from "./tiers.ts";

export interface PanelContext {
  config: HealthSystemConfig;
  asOf: string;
  forecast: ForecastInputs;
  neighborhood: NeighborhoodData;
  drugIndex: DrugProfileIndex;
  travel: TravelLookup;
  places: CoolingPlace[];
  /** Routing agent's cooling_match.csv rows grouped by patient_id, when present. */
  routedCooling?: Map<string, Record<string, string>[]>;
  /** Date ages are computed on (default asOf). A replayed past heat wave hits today's patients, so pass today. */
  ageAsOf?: string;
  placeById?: Map<string, CoolingPlace>;
  /** System graph drug → mediator ← heat study counts (system_pathways.csv), when loaded. */
  systemPathways?: SystemPathwayIndex | null;
}

/** HeatRisk for a ZIP; ZIPs without a forecast use the max over forecast ZIPs that day (labeled). */
export function zipHeatRisk(ctx: PanelContext, zip: string, date: string): { level: HeatRiskLevel; source: string } {
  const own = heatRiskOn(ctx.forecast, zip, date);
  if (own !== null) return { level: own, source: "zip" };
  let m = -1;
  for (const days of ctx.forecast.heatrisk.values()) for (const d of days) if (d.date === date) m = Math.max(m, d.level);
  if (m >= 0) return { level: m as HeatRiskLevel, source: "proxy: max HeatRisk of forecast ZIPs in catchment (ZIP not sampled)" };
  return { level: 0, source: "no forecast for this date (treated as 0)" };
}

function maxAhead(ctx: PanelContext, zip: string, days: number): HeatRiskLevel {
  let m = 0;
  const dates = new Set<string>();
  for (const arr of ctx.forecast.heatrisk.values()) for (const d of arr) dates.add(d.date);
  for (const date of dates) {
    const k = daysBetween(ctx.asOf, date);
    if (k >= 1 && k <= days) m = Math.max(m, zipHeatRisk(ctx, zip, date).level);
  }
  return m as HeatRiskLevel;
}

export function scorePatient(p: PatientRecord, ctx: PanelContext): Omit<PatientScore, "rank"> {
  const cfg = ctx.config;
  const age = ageOn(p.birthDate, ctx.ageAsOf ?? ctx.asOf);
  const q = p.questionnaire;
  const hr = zipHeatRisk(ctx, p.zip, ctx.asOf);
  const hrNext = maxAhead(ctx, p.zip, cfg.alert_rules.call_before_heat_wave.lookahead_days);

  const meds = medRiskStack(p.medications, ctx.drugIndex);
  const exposure = personalExposure(q, p.zip, ctx.neighborhood);
  const condKeys = p.conditions.map((c) => c.key);
  const readiness = readinessLevel(meds, exposure, age, condKeys);
  const lifestyle = lifestyleSusceptibility(q);
  const stacking = stackingView(meds, ctx.systemPathways ?? null);

  const escalation = escalationPlan({
    age,
    q,
    contacts: p.contacts,
    readiness: readiness.level,
    heatriskToday: hr.level,
    travel: ctx.travel,
    rules: cfg.escalation,
    finalStep: cfg.contacts.final_step,
    buddyProgram: cfg.contacts.buddy_program,
  });

  const tierIn = {
    readiness: readiness.level,
    readinessDrivers: readiness.drivers,
    med: meds,
    exposure,
    q,
    zip: p.zip,
    noQualifyingContact: escalation.noQualifyingContact,
  };
  const tier = priorityTier({ ...tierIn, heatriskToday: hr.level, heatriskMaxNext: hrNext }, cfg.alert_rules);
  const drill = cfg.alert_rules.drill_heatrisk;
  const drillTier = priorityTier({ ...tierIn, heatriskToday: drill, heatriskMaxNext: drill }, cfg.alert_rules);

  let cooling: CoolingMatch | null = null;
  const routed = ctx.routedCooling?.get(p.id);
  if (routed?.length) cooling = coolingFromRoutedRows(routed, ctx.placeById ?? new Map(), cfg.data_sources.cooling_places, ctx.asOf);
  if (!cooling)
    cooling = matchCoolingPlace(
      { home: p.home, age, stepFreeNeeded: q?.stepFreeNeeded === true, canReach: q?.canReachCoolPlace ?? null },
      ctx.places,
      ctx.asOf,
      cfg.data_sources.cooling_places,
    );

  const mctx: MessageContext = {
    patientName: p.givenName,
    age,
    language: p.language,
    supportedLanguages: cfg.languages,
    fallbackLanguage: cfg.fallback_language,
    q,
    med: meds,
    meds: p.medications,
    conditionKeys: condKeys,
    idx: ctx.drugIndex,
    heatriskToday: Math.max(hr.level, 1) as HeatRiskLevel,
    cooling: cooling.best,
  };
  const sendsAlert = tier.autoSafetyAlert || tier.tier === "call_today";
  const messages: PatientMessage[] = [];
  const push = (m: PatientMessage | null, send: boolean) => {
    if (!m) return;
    messages.push({ ...m, sendToday: send, safetyIssues: checkMessageSafety(m) });
  };
  push(heatCard(mctx), tier.tier !== "routine");
  push(safetyAlert({ ...mctx, heatriskToday: hr.level >= 1 ? hr.level : drill }), sendsAlert);
  push(coolingPlaceText(mctx), tier.coolingText);
  push(checkinText(mctx), escalation.enrolled && hr.level >= cfg.alert_rules.cooling_text_min_heatrisk);
  const first = p.contacts.find((c) => c.id === escalation.firstContactId);
  if (first) push(contactCheckText(p.givenName, first.language ?? p.language, cfg.languages, q?.fluidRestricted === true), false);

  return {
    patientId: p.id,
    synthetic: true,
    storyLabel: p.storyLabel ?? null,
    displayName: `${p.givenName} ${p.familyName}`,
    age,
    zip: p.zip,
    language: q?.preferredLanguage ?? p.language,
    heatriskToday: hr.level,
    heatriskMaxNext: hrNext,
    heatriskSource: hr.source,
    meds,
    exposure,
    readiness,
    lifestyle,
    stacking,
    tier,
    drillTier,
    escalation,
    cooling,
    messages,
  };
}

export function scorePanel(patients: PatientRecord[], ctx: PanelContext): PatientScore[] {
  const scored = patients.map((p) => scorePatient(p, ctx));
  scored.sort(compareForCallList);
  return scored.map((s, i) => ({ ...s, rank: i + 1 }));
}

export function countBy<T>(xs: T[], key: (x: T) => string): Record<string, number> {
  const o: Record<string, number> = {};
  for (const x of xs) {
    const k = key(x);
    o[k] = (o[k] ?? 0) + 1;
  }
  return o;
}

export function panelSummary(scores: PatientScore[]) {
  const tiers = Object.fromEntries(TIER_ORDER.map((t) => [t, 0])) as Record<PriorityTier, number>;
  const drill = Object.fromEntries(TIER_ORDER.map((t) => [t, 0])) as Record<PriorityTier, number>;
  for (const s of scores) {
    tiers[s.tier.tier]++;
    drill[s.drillTier.tier]++;
  }
  const callToday = scores.filter((s) => s.tier.tier === "call_today");
  const msgs = scores.flatMap((s) => s.messages);
  return {
    n_patients: scores.length,
    tiers,
    headline: `${tiers.call_today} patients to call today, ${tiers.call_before_heat_wave} before the heat wave, ${tiers.send_heat_card} heat cards`,
    drill_tiers: drill,
    auto_safety_alerts: scores.filter((s) => s.tier.autoSafetyAlert).length,
    cooling_place_texts: scores.filter((s) => s.tier.coolingText).length,
    heatrisk_today_by_zip: Object.fromEntries([...new Set(scores.map((s) => s.zip))].sort().map((z) => [z, scores.find((s) => s.zip === z)!.heatriskToday])),
    readiness: countBy(scores, (s) => s.readiness.level),
    med_level: countBy(scores, (s) => `${s.meds.level} ${s.meds.levelLabel}`),
    exposure_band: countBy(scores, (s) => s.exposure.band),
    lifestyle: {
      category: countBy(scores, (s) => s.lifestyle.category),
      profile: countBy(scores, (s) => s.lifestyle.profile),
      incomplete: scores.filter((s) => s.lifestyle.incomplete).length,
    },
    stacking: {
      patients_with_stacked_mechanism: scores.filter((s) => s.stacking.stackedMechanismCount > 0).length,
      patients_with_stacked_symptoms: scores.filter((s) => s.stacking.stackedSymptomCount > 0).length,
      patients_with_masked_signs: scores.filter((s) => s.stacking.maskedSigns.length > 0).length,
      stacked_mechanisms: countBy(scores.flatMap((s) => s.stacking.mechanisms.filter((m) => m.stacked)), (m) => m.defense),
      masked_signs: countBy(scores.flatMap((s) => s.stacking.maskedSigns), (m) => m.sign),
    },
    escalation: {
      enrolled: scores.filter((s) => s.escalation.enrolled).length,
      t_max_min: countBy(scores.filter((s) => s.escalation.enrolled), (s) => String(s.escalation.tMaxMin)),
      enrolled_without_qualifying_contact: scores.filter((s) => s.escalation.enrolled && s.escalation.noQualifyingContact).length,
      call_today_without_qualifying_contact: callToday.filter((s) => s.escalation.noQualifyingContact).length,
      travel_source: countBy(scores.flatMap((s) => s.escalation.contacts), (c) => c.travelSource),
      median_worst_case_unnoticed_min: median(scores.filter((s) => s.escalation.enrolled).map((s) => s.escalation.worstCaseUnnoticedMin)),
    },
    cooling: {
      source: countBy(scores, (s) => s.cooling.source),
      matched: scores.filter((s) => s.cooling.best).length,
      median_travel_min: median(scores.filter((s) => s.cooling.best).map((s) => s.cooling.best!.travelMin)),
      no_match: scores.filter((s) => !s.cooling.best).map((s) => s.patientId),
    },
    messages: {
      total: msgs.length,
      sent_today: countBy(msgs.filter((m) => m.sendToday), (m) => m.kind),
      needs_translation: msgs.filter((m) => m.needsTranslation && m.sendToday).length,
      safety_issues: msgs.filter((m) => m.safetyIssues?.length).length,
    },
    drug_profile_sources: countBy(scores.flatMap((s) => s.meds.profileSources), (x) => x),
    unmapped_drugs: [...new Set(scores.flatMap((s) => s.meds.unmappedDrugs))],
  };
}

function median(xs: number[]): number | null {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}
