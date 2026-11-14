// Health-system configuration (spec §3.7: "per-health-system configuration, not code").
// One JSON file per health system in config/health-systems/<id>.json. Switching the
// app to another health system means loading another config; no code changes.
// Every number here is either sourced (see `source` fields) or marked as an assumption.

export type ReadinessLevel = "low" | "medium" | "high" | "very_high";

/** NWS HeatRisk is a 0-4 scale: 0 green, 1 yellow, 2 orange, 3 red, 4 magenta. */
export type HeatRiskLevel = 0 | 1 | 2 | 3 | 4;

export interface SourcedValue<T> {
  value: T;
  /** Citation, or "ASSUMPTION: ..." when no source has been extracted yet. */
  source: string;
}

export interface CoolingPlaceRules {
  /** GeoJSON FeatureCollection path, relative to repo root. */
  file: string;
  source_label: string;
  /** Only places whose `category` is in this list are offered (indoor, air-conditioned). */
  include_categories: string[];
  /** Arrive-by time on a heat day ("get there before 11 AM"). Local time HH:MM. */
  arrive_before: string;
  /** Minutes of slack before arrive_before when computing the leave-by time. */
  arrival_buffer_min: number;
  /** Maximum straight-line search radius in km. */
  max_radius_km: number;
  /** Detour factor: network distance ≈ straight-line × factor (ASSUMPTION unless routed). */
  detour_factor: SourcedValue<number>;
  /** Walking speeds in m/s. */
  walk_speed_mps: { adult: SourcedValue<number>; older_or_mobility: SourcedValue<number> };
  /** Above this walking time we propose transit (naive estimate) instead. */
  max_walk_min: number;
  /** Naive transit model when no routed time exists: wait + in-vehicle at this speed. */
  naive_transit: { wait_min: number; speed_kmh: number; source: string };
  /** Facility types restricted to older adults, and the minimum age. */
  older_adult_only_facility_types: string[];
  older_adult_min_age: number;
}

export interface EscalationRules {
  /** T_max: minutes from a missed acknowledgement to a person physically present (spec §4.4a). */
  t_max_min: Record<Exclude<ReadinessLevel, "low">, number> & { low: number };
  t_max_source: string;
  /** Use the tightest budget when HeatRisk ≥ this or the home is hot with no AC. */
  tighten_to_very_high_if_heatrisk_gte: HeatRiskLevel;
  /** p90 response times (minutes) used until a person's own p90 is learned from check-ins. */
  response_p90_min: {
    patient_app_or_sms: SourcedValue<number>;
    patient_voice_call: SourcedValue<number>;
    older_adult_extra: SourcedValue<number>;
    contact: SourcedValue<number>;
  };
  /** Re-send the alert once at this fraction of T_wait (spec: halfway). */
  resend_fraction_of_wait: number;
  /** Extra check-ins for very-high readiness on HeatRisk ≥ min (spec: more at 2-6 PM). */
  checkin_densify: { min_heatrisk: HeatRiskLevel; min_readiness: ReadinessLevel; add_times: string[] };
  /** Waking-hours window over which the longest unobserved gap is measured. */
  waking_window: [string, string];
}

export interface AlertRules {
  heatrisk_scale: string;
  /** Minimum HeatRisk *today* (patient's ZIP) to put a patient in "call today", by readiness level. */
  call_today_min_heatrisk: Partial<Record<ReadinessLevel, HeatRiskLevel>>;
  /** Also call today when automation can't reach anyone in time (see definition). */
  call_today_if_uncovered?: { min_readiness: ReadinessLevel; min_heatrisk: HeatRiskLevel; definition: string };
  /** "Call before the heat wave": max HeatRisk in the next N days ≥ min, for readiness ≥ min. */
  call_before_heat_wave: { lookahead_days: number; min_heatrisk: HeatRiskLevel; min_readiness: ReadinessLevel };
  /** Mandatory safety alert (push + SMS) is auto-sent only on days at/above this level. */
  auto_safety_alert_min_heatrisk: HeatRiskLevel;
  /** Morning cooling-place text is sent on days at/above this level. */
  cooling_text_min_heatrisk: HeatRiskLevel;
  /** Heat card (non-urgent education; not an alert): medication stack level ≥ this. */
  heat_card_min_med_level: number;
  /** Also send a heat card when any medicine is heat-sensitive to store (insulin, epinephrine...). */
  heat_card_if_storage_sensitive?: boolean;
  /** Hypothetical HeatRisk used for the drill column ("what if a heat wave hit now"). */
  drill_heatrisk: HeatRiskLevel;
  notes: string;
}

export interface HealthSystemConfig {
  id: string;
  name: string;
  short_name: string;
  region: { city: string; county: string; state: string; county_fips: string };
  timezone: string;
  catchment_zips: string[];
  catchment_source: string;
  demo_zips: string[];
  /** Languages with pre-reviewed message text. Others fall back to English + interpreter flag. */
  languages: string[];
  fallback_language: string;
  data_sources: {
    heatrisk_current: string;
    heatrisk_replay: string;
    cpc_outlook: string;
    historical_odds: string;
    historical_odds_column: string;
    historical_within_14d_column: string;
    hvi_by_zip: string;
    hvi_source: string;
    ac_households: string;
    ac_source: string;
    /** ZIP → neighborhood geography used by the AC file (approximate crosswalks are flagged). */
    zip_to_ac_area: Record<string, { geotype: string; geoid: string; name: string; approximate: boolean }>;
    ac_year: number;
    cooling_places: CoolingPlaceRules;
    routing: {
      contacts_routed: string;
      cooling_match: string;
      fallback: string;
      /** Routed-time columns to use, in order of preference (first non-empty wins). */
      contact_travel_columns?: { minutes: string; mode: string; why: string }[];
    };
    knowledge_base: string[];
  };
  alert_rules: AlertRules;
  escalation: EscalationRules;
  contacts: {
    /** Where an unanswered escalation ends: always a human (spec §4.4 safety rules). */
    final_step: string;
    buddy_program: string;
    clinic_call_list_label: string;
  };
  help_programs: { ac_assistance: string };
}
