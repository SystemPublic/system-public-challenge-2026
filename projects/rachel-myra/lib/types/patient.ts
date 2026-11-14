// Patient-side formats (spec §4.4, §4.5a, §6.1, §9). FHIR-derived: PatientRecord is what
// lib/patient/fhir.ts builds from a FHIR R4 Bundle (Patient, Condition, MedicationRequest,
// RelatedPerson, QuestionnaireResponse). All demo data is SYNTHETIC.

import type { HeatRiskLevel, ReadinessLevel } from "./health-system.ts";
export type { HeatRiskLevel, ReadinessLevel } from "./health-system.ts";

export interface LatLon {
  lat: number;
  lon: number;
}

export interface ConditionEntry {
  /** ICD-10-CM code when present. */
  code?: string;
  text: string;
  /** Normalized key, e.g. "heart_failure", "ckd". */
  key: string;
}

export interface MedicationOrder {
  id: string;
  rxcui?: string;
  /** Lower-case generic (ingredient) name, e.g. "hydrochlorothiazide". */
  generic: string;
  text?: string;
  route?: string;
  status: string;
  authoredOn?: string;
  mailOrder?: boolean;
}

export interface TrustedContact {
  id: string;
  patientId: string;
  priority: number;
  givenName: string;
  familyName: string;
  relationship: string;
  phone?: string;
  language?: string;
  home: LatLon | null;
}

export type WorkingAc = "yes" | "yes_but_cost_limits_use" | "no";
export type DayLocation = "home" | "indoors_ac" | "outdoors_or_physical_work";
export type CanReach = "yes" | "with_help" | "no";
export type AlertChannel = "app_and_sms" | "sms_only" | "voice_call";

/** Spec §4.5a: core 5 + action-item fields + optional "asked over time" fields. Every answer is optional. */
export interface QuestionnaireAnswers {
  respondent: "self" | "parent_or_caregiver" | null;
  workingAc: WorkingAc | null; // Q1
  dayLocation: DayLocation | null; // Q2
  floor: number | null; // Q3
  buildingType: string | null;
  hasElevator: boolean | null;
  livesAlone: boolean | null; // Q4
  canReachCoolPlace: CanReach | null; // Q5
  stepFreeNeeded: boolean | null;
  fluidRestricted: boolean | null;
  fluidRestrictionSetBy: string | null;
  preferredLanguage: string | null;
  alertOptIn: boolean | null;
  alertChannel: AlertChannel | null;
  hasSmartphone: boolean | null;
  checkinTimes: string[];
  powerDependentEquipment: string[];
  fridgeMedicines: string[];
  mailOrderDropLocation: string | null;
  outdoorWorkOrSports: boolean | null;
  windowsOpen: boolean | null;
  homeGetsHot: "rarely" | "sometimes" | "often" | null;
  someoneChecksOn: boolean | null;
  leavesHomeMostDays: boolean | null;
  knowsHeatIllnessSigns: boolean | null;
  stableHousing: boolean | null;
  answeredOn: string | null;
}

export interface PatientRecord {
  id: string;
  synthetic: boolean;
  storyLabel?: string;
  givenName: string;
  familyName: string;
  sex: string;
  birthDate: string;
  zip: string;
  home: LatLon | null;
  language: string;
  phone?: string;
  conditions: ConditionEntry[];
  medications: MedicationOrder[];
  contacts: TrustedContact[];
  questionnaire: QuestionnaireAnswers | null;
}

// ---------------------------------------------------------------- outputs

/** Body heat defenses a drug can weaken (plus the medicine's own storage). */
export type HeatDefense =
  | "sweating"
  | "skin_blood_flow"
  | "fluid_salt_balance"
  | "blood_pressure"
  | "kidney_clearance"
  | "brain_thermostat"
  | "alertness"
  | "blood_sugar"
  | "drug_delivery"
  | "medicine_storage";

export interface DrugHeatProfile {
  generic: string;
  /** Human label for the class, e.g. "water pill (thiazide)". */
  plainClass: string;
  heatClass: string;
  defenses: HeatDefense[];
  acb: number;
  /** Narrow-margin, kidney-cleared drug (lithium, digoxin, dabigatran). */
  narrowMarginKidneyCleared: boolean;
  /** Which source supplied this row. */
  source: "knowledge_base" | "mock_knowledge_base" | "provisional";
}

export interface CombinationFlag {
  id: string;
  label: string;
  drugs: string[];
  /** Evidence note shown verbatim; null findings are shown, not hidden (spec §6.1). */
  evidence: string;
  /** Does this flag raise the plotted level? (Null-evidence flags are shown but do not.) */
  raisesLevel: boolean;
}

export interface MedRiskStack {
  /** 0-4 transparent ordinal for the y-axis; see MED_LEVEL_RULES. */
  level: number;
  levelLabel: string;
  /** level + small within-band offset for plotting (defenses count / 10, capped at 0.9). */
  plotY: number;
  /** Which rule produced the level (id from MED_LEVEL_RULES). */
  ruleId: string;
  defenses: { defense: HeatDefense; label: string; drugs: string[] }[];
  combinations: CombinationFlag[];
  acbTotal: number;
  heatRelevantDrugs: string[];
  reasons: string[];
  profileSources: string[];
  unmappedDrugs: string[];
}

export interface ExposureFactor {
  id: string;
  label: string;
  points: number;
  basis: string;
}

export interface ExposureResult {
  points: number;
  maxPoints: number;
  band: "low" | "medium" | "high" | "very_high";
  factors: ExposureFactor[];
  neighborhood: { hvi: number | null; pctNoAc: number | null; acArea: string | null; acAreaApproximate: boolean };
  missingAnswers: string[];
}

export type PriorityTier = "call_today" | "call_before_heat_wave" | "send_heat_card" | "routine";

export interface TierResult {
  tier: PriorityTier;
  reasons: string[];
  /** Gate actually applied (so the UI can say "no alerts today: HeatRisk 0"). */
  gate: string;
  autoSafetyAlert: boolean;
  coolingText: boolean;
}

export interface ContactEligibility {
  contactId: string;
  name: string;
  relationship: string;
  travelMin: number | null;
  travelMode: string | null;
  travelSource: "routed" | "naive_placeholder" | "none";
  allowedTravelMin: number;
  eligible: boolean;
}

export interface EscalationStep {
  atMin: number;
  action: string;
  to: string;
}

export interface EscalationPlan {
  enrolled: boolean;
  tMaxMin: number;
  tMaxReason: string;
  tWaitMin: number;
  tContactMin: number;
  allowedTravelMin: number;
  resendAtMin: number;
  contacts: ContactEligibility[];
  firstContactId: string | null;
  noQualifyingContact: boolean;
  fallback: string | null;
  checkinTimes: string[];
  longestGapMin: number;
  worstCaseUnnoticedMin: number;
  steps: EscalationStep[];
  assumptions: string[];
}

export interface CoolingPlaceOption {
  id: string;
  name: string;
  category: string;
  address: string | null;
  lat: number;
  lon: number;
  officialCoolingCenter: boolean;
  stepFree: "yes" | "no" | "unknown";
  hoursToday: string | null;
  opensMin: number | null;
  closesMin: number | null;
  distanceKm: number;
  travelMin: number;
  travelMode: "walk" | "transit_naive" | "routed";
  leaveBy: string | null;
  arriveBy: string;
  caveats: string[];
}

export interface CoolingMatch {
  source: "routing_agent" | "fallback_nearest";
  best: CoolingPlaceOption | null;
  alternatives: CoolingPlaceOption[];
  note: string;
}

export interface PatientMessage {
  kind: "safety_alert" | "heat_card" | "cooling_place" | "contact_check" | "checkin";
  language: string;
  needsTranslation: boolean;
  audience: "patient" | "caregiver" | "trusted_contact";
  channel: string;
  text: string;
  blocks: string[];
  /** Customization rules that fired (shown in nerd stats). */
  rulesApplied: string[];
  /** Would this message go out on the scored day (false = preview only)? */
  sendToday?: boolean;
  /** Guardrail check result (empty = passed). */
  safetyIssues?: string[];
}

export interface HeatWaveOutlook {
  targetDate: string;
  leadDays: number;
  window: "0-7d forecast" | "6-14d outlook" | "week 3-4 outlook" | "monthly/seasonal outlook" | "history only";
  source: string;
  /** Probability of the date being inside a heat wave, when a probability is defined. */
  probability: number | null;
  /** HeatRisk level when the window is a deterministic forecast. */
  heatrisk: HeatRiskLevel | null;
  /** 0-1 for the probability bar; for forecasts it is the HeatRisk level / 4 (labeled). */
  barFraction: number;
  historical: number;
  method: string;
}

export interface LifestyleResult {
  category: "least" | "medium" | "most";
  categoryLabel: string;
  profile:
    | "outdoor_worker"
    | "indoors_with_outdoor_activity"
    | "indoors_cool_place"
    | "home_with_ac"
    | "home_without_reliable_ac"
    | "unknown";
  profileLabel: string;
  points: number;
  factors: { id: string; label: string; points: number; basis: string }[];
  missingAnswers: string[];
  /** True when 2+ core answers are missing: the category is a floor, not a judgment. */
  incomplete: boolean;
}

export interface StackingResult {
  mechanisms: {
    defense: HeatDefense;
    label: string;
    drugs: string[];
    /** 2+ medicines weaken this defense. */
    stacked: boolean;
    system: {
      mediator: string;
      mediatorLabel: string;
      heatLegStudies: number | null;
      drugLegs: { drug: string; systemGroup: string | null; studies: number | null }[];
    }[];
    graphNote: string;
  }[];
  stackedMechanismCount: number;
  symptoms: { sign: string; label: string; drugs: string[]; /** medicines + heat */ sources: number; stacked: boolean }[];
  stackedSymptomCount: number;
  maskedSigns: { sign: string; label: string; drugs: string[]; why: string }[];
  summary: string[];
  caveat: string;
  systemSource: string | null;
}

export interface PatientScore {
  patientId: string;
  synthetic: true;
  storyLabel: string | null;
  displayName: string;
  age: number;
  zip: string;
  language: string;
  heatriskToday: HeatRiskLevel;
  heatriskMaxNext: HeatRiskLevel;
  /** "zip" = the patient's own ZIP; otherwise how the level was proxied. */
  heatriskSource: string;
  meds: MedRiskStack;
  exposure: ExposureResult;
  readiness: { level: ReadinessLevel; drivers: string[]; modifiers: string[] };
  /** Least / medium / most susceptible from daily habits only (lib/patient/lifestyle.ts). */
  lifestyle: LifestyleResult;
  /** Mechanism and symptom stacking across the patient's medicines (lib/patient/stacking.ts). */
  stacking: StackingResult;
  tier: TierResult;
  /** Tier if HeatRisk were alert_rules.drill_heatrisk today (the drill / simulator column). */
  drillTier: TierResult;
  escalation: EscalationPlan;
  cooling: CoolingMatch;
  messages: PatientMessage[];
  rank: number;
}
