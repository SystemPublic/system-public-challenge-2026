import fs from "node:fs";
import path from "node:path";
import type { Metadata } from "next";
import { Suspense } from "react";
import { Intake } from "@/components/intake/Intake";
import type { IntakeAnswers, IntakeContact, IntakeMed } from "@/components/intake/types";
import { Placeholder } from "@/components/Placeholder";
import { REPO_ROOT } from "@/lib/kb";
import { getPanelPatient, loadPanel } from "@/lib/panel";
import { plainName } from "@/lib/risk";
import { kbDrugFor, parseCsv, questionnaire, QUESTIONNAIRE_FILE } from "@/lib/synthetic";

export const metadata: Metadata = { title: "Sign up · Cool-Aid" };

// CHILL'D-Out-style sign-up (CDC 2024; areas listed in research-notes/advisor-models.md).
// Pre-filled from the chosen synthetic patient's files:
//   data/processed/synthetic/questionnaire.csv, medications.csv, contacts.csv
const MEDS_FILE = "data/processed/synthetic/medications.csv";
const CONTACTS_FILE = "data/processed/synthetic/contacts.csv";
const DEFAULT_PATIENT = "S01";

function csv(rel: string): Record<string, string>[] {
  const f = path.join(REPO_ROOT, rel);
  return fs.existsSync(f) ? parseCsv(fs.readFileSync(f, "utf8")) : [];
}

const yn = (v: string | undefined): boolean | null => (v === "true" ? true : v === "false" ? false : null);
function oneOf<T extends string>(v: string | undefined, xs: readonly T[]): T | null {
  return xs.includes(v as T) ? (v as T) : null;
}

export default function SignupPage({ searchParams }: { searchParams: Promise<{ patient?: string; lang?: string }> }) {
  return (
    <Suspense fallback={<p className="text-ink-muted">Loading…</p>}>
      <Signup searchParams={searchParams} />
    </Suspense>
  );
}

async function Signup({ searchParams }: { searchParams: Promise<{ patient?: string; lang?: string }> }) {
  const { patient, lang: langParam } = await searchParams;
  const id = patient ?? DEFAULT_PATIENT;
  const panel = loadPanel("replay");
  const p = getPanelPatient(id, "replay");
  if (!panel || !p) {
    return (
      <Placeholder title="Sign up">
        Patient {id} not found. Data goes here: data/processed/panel_scores_replay.json and {QUESTIONNAIRE_FILE}
      </Placeholder>
    );
  }
  // Same rule as the plan page (/phone/[id]): panel patients[].language; ?lang=en|es overrides.
  const lang: "en" | "es" = langParam === "es" || langParam === "en" ? langParam : p.language === "es" ? "es" : "en";
  const q = questionnaire().get(id);
  const num = q?.q3_floor ? Number(q.q3_floor) : NaN;
  const answers: IntakeAnswers = {
    workingAc: oneOf(q?.q1_working_ac, ["yes", "yes_but_cost_limits_use", "no"] as const),
    homeGetsHot: oneOf(q?.home_gets_hot, ["rarely", "sometimes", "often"] as const),
    stableHousing: yn(q?.stable_housing),
    floor: Number.isFinite(num) ? num : null,
    hasElevator: yn(q?.building_has_elevator),
    livesAlone: yn(q?.q4_lives_alone),
    someoneChecksOn: yn(q?.someone_checks_on_them),
    canReachCoolPlace: oneOf(q?.q5_can_reach_cool_place, ["yes", "with_help", "no"] as const),
    powerEquipment: q ? q.power_dependent_equipment !== "" : null,
    fridgeMedicines: q ? q.fridge_medicines !== "" : null,
    checksForecast: null,
    knowsHeatIllnessSigns: yn(q?.knows_heat_illness_signs),
    dayLocation: oneOf(q?.q2_day_location, ["home", "indoors_ac", "outdoors_or_physical_work"] as const),
    outdoorWorkOrSports: yn(q?.outdoor_work_or_sports),
    alertOptIn: yn(q?.alert_opt_in),
  };

  const meds: IntakeMed[] = csv(MEDS_FILE)
    .filter((r) => r.patient_id === id && r.status === "active")
    .map((r) => ({
      id: r.med_id,
      generic: r.generic_name,
      plainClass: r.drug_class,
      heatLine: kbDrugFor(r.generic_name)?.label_line ?? null,
      taking: true,
    }));

  const c = csv(CONTACTS_FILE)
    .filter((r) => r.patient_id === id)
    .sort((a, b) => Number(a.priority) - Number(b.priority))[0];
  const contact: IntakeContact = c
    ? { name: plainName(`${c.given_name} ${c.family_name}`), relationship: c.relationship.replace(/_/g, " "), phone: c.phone }
    : { name: "", relationship: "", phone: "" };

  const story = panel.data.patients
    .filter((x) => x.storyLabel)
    .sort((a, b) => a.patientId.localeCompare(b.patientId))
    .map((x) => ({ id: x.patientId, name: plainName(x.displayName) }));

  return (
    <Intake
      key={`${id}-${lang}`}
      patientId={id}
      lang={lang}
      firstName={plainName(p.displayName).split(" ")[0]}
      initial={answers}
      meds={meds}
      contact={contact}
      story={story}
      files={{ questionnaire: QUESTIONNAIRE_FILE, meds: MEDS_FILE, contacts: CONTACTS_FILE }}
    />
  );
}
