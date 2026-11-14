// Shared shapes for the CHILL'D-Out-style sign-up (/phone/signup). Safe for client code.
import type { RiskGroup } from "@/lib/risk";

export type WorkingAc = "yes" | "yes_but_cost_limits_use" | "no";
export type DayLocation = "home" | "indoors_ac" | "outdoors_or_physical_work";
export type CanReach = "yes" | "with_help" | "no";
export type HomeHot = "rarely" | "sometimes" | "often";

/** The answers the intake collects. Keys mirror data/processed/synthetic/questionnaire.csv. */
export interface IntakeAnswers {
  workingAc: WorkingAc | null; // q1_working_ac
  homeGetsHot: HomeHot | null; // home_gets_hot
  stableHousing: boolean | null; // stable_housing
  floor: number | null; // q3_floor
  hasElevator: boolean | null; // building_has_elevator
  livesAlone: boolean | null; // q4_lives_alone
  someoneChecksOn: boolean | null; // someone_checks_on_them
  canReachCoolPlace: CanReach | null; // q5_can_reach_cool_place
  powerEquipment: boolean | null; // power_dependent_equipment (non-empty)
  fridgeMedicines: boolean | null; // fridge_medicines (non-empty)
  checksForecast: boolean | null; // not in questionnaire.csv (new CHILL'D-Out question; not scored)
  knowsHeatIllnessSigns: boolean | null; // knows_heat_illness_signs
  dayLocation: DayLocation | null; // q2_day_location
  outdoorWorkOrSports: boolean | null; // outdoor_work_or_sports
  alertOptIn: boolean | null; // alert_opt_in
}

export interface IntakeMed {
  /** med_id in medications.csv = MedicationRequest id in patients_fhir.json */
  id: string;
  generic: string;
  plainClass: string;
  /** One plain line from data/kb/knowledge_base.json (label_line), when the medicine is in it. */
  heatLine: string | null;
  taking: boolean;
}

export interface IntakeContact {
  name: string;
  relationship: string;
  phone: string;
}

export interface IntakeResult {
  group: RiskGroup;
  why: string;
  /** Same group as the precomputed panel_scores_replay.json record? */
  sameAsRecord: boolean;
  recordGroup: RiskGroup | null;
  method: string;
}
