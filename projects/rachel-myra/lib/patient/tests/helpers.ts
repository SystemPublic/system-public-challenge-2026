// Shared fixtures for the patient-logic tests. SYNTHETIC only.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { HealthSystemConfig } from "../../types/health-system.ts";
import type { QuestionnaireAnswers } from "../../types/patient.ts";
import { questionnaireFromMap } from "../fhir.ts";

export const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
export const config = (): HealthSystemConfig => JSON.parse(readFileSync(join(ROOT, "config/health-systems/sbh.json"), "utf8"));

export function q(over: Partial<QuestionnaireAnswers> = {}): QuestionnaireAnswers {
  return {
    ...questionnaireFromMap({
      respondent: "self",
      q1_working_ac: "yes",
      q2_day_location: "indoors_ac",
      q3_floor: 2,
      building_has_elevator: true,
      q4_lives_alone: false,
      q5_can_reach_cool_place: "yes",
      mobility_step_free_needed: false,
      fluid_restricted: false,
      preferred_language: "en",
      alert_opt_in: true,
      alert_channel: "app_and_sms",
      has_smartphone: true,
      checkin_times: "10:00;16:00",
      home_gets_hot: "rarely",
      someone_checks_on_them: true,
    }),
    ...over,
  };
}
