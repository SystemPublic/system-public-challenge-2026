// FHIR R4 Bundle → PatientRecord[] (Patient, Condition, MedicationRequest, RelatedPerson,
// QuestionnaireResponse). Pure; works on any bundle that follows the same profiles, so a
// health system plugs in through FHIR rather than custom integration (spec §3.7).

import type {
  ConditionEntry,
  LatLon,
  MedicationOrder,
  PatientRecord,
  QuestionnaireAnswers,
  TrustedContact,
} from "../types/patient.ts";

const SYNTHETIC_EXT = "https://example.org/fhir/StructureDefinition/synthetic";
const STORY_EXT = "https://example.org/fhir/StructureDefinition/story-patient";
const MAIL_EXT = "https://example.org/fhir/StructureDefinition/mail-order";
const GEO_EXT = "http://hl7.org/fhir/StructureDefinition/geolocation";

type Json = any; // FHIR resources are loosely typed here on purpose (no dependency on a FHIR lib).

function ext(r: Json, url: string): Json | undefined {
  return (r?.extension ?? []).find((e: Json) => e.url === url);
}

function geo(holder: Json): LatLon | null {
  const g = ext(holder, GEO_EXT);
  if (!g) return null;
  const lat = g.extension?.find((e: Json) => e.url === "latitude")?.valueDecimal;
  const lon = g.extension?.find((e: Json) => e.url === "longitude")?.valueDecimal;
  return typeof lat === "number" && typeof lon === "number" ? { lat, lon } : null;
}

function refId(ref: string | undefined): string {
  return (ref ?? "").split("/").pop() ?? "";
}

/** ICD-10-CM prefixes for conditions the patient logic needs (fluid limits, kidney, etc.). */
const ICD_KEYS: [RegExp, string][] = [
  [/^I50/, "heart_failure"],
  [/^N18/, "ckd"],
  [/^E10/, "type1_diabetes"],
  [/^E11/, "type2_diabetes"],
  [/^F20/, "schizophrenia"],
  [/^F31/, "bipolar"],
  [/^(F0[1-3]|G30)/, "dementia"],
  [/^G40/, "epilepsy"],
  [/^J45/, "asthma"],
  [/^I10/, "hypertension"],
  [/^O/, "pregnancy"],
];

export function conditionKey(text: string, code?: string): string {
  if (code) for (const [re, k] of ICD_KEYS) if (re.test(code)) return k;
  return text.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
}

function answer(item: Json): string | number | boolean | null {
  const a = item?.answer?.[0];
  if (!a) return null;
  for (const k of ["valueString", "valueInteger", "valueBoolean", "valueDecimal", "valueDate"]) if (k in a) return a[k];
  if (a.valueCoding) return a.valueCoding.code ?? null;
  return null;
}

const str = (v: unknown): string | null => (v === null || v === undefined || v === "" ? null : String(v));
const bool = (v: unknown): boolean | null =>
  v === null || v === undefined || v === "" ? null : v === true || v === "true" || v === "True";
const num = (v: unknown): number | null => {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
};
const list = (v: unknown): string[] =>
  v === null || v === undefined ? [] : String(v).split(";").map((s) => s.trim()).filter(Boolean);

/** Build answers from a flat key → value map (FHIR QuestionnaireResponse items or a CSV row). */
export function questionnaireFromMap(m: Record<string, unknown>): QuestionnaireAnswers {
  return {
    respondent: (str(m.respondent) as QuestionnaireAnswers["respondent"]) ?? null,
    workingAc: (str(m.q1_working_ac) as QuestionnaireAnswers["workingAc"]) ?? null,
    dayLocation: (str(m.q2_day_location) as QuestionnaireAnswers["dayLocation"]) ?? null,
    floor: num(m.q3_floor),
    buildingType: str(m.building_type),
    hasElevator: bool(m.building_has_elevator),
    livesAlone: bool(m.q4_lives_alone),
    canReachCoolPlace: (str(m.q5_can_reach_cool_place) as QuestionnaireAnswers["canReachCoolPlace"]) ?? null,
    stepFreeNeeded: bool(m.mobility_step_free_needed),
    fluidRestricted: bool(m.fluid_restricted),
    fluidRestrictionSetBy: str(m.fluid_restriction_set_by),
    preferredLanguage: str(m.preferred_language),
    alertOptIn: bool(m.alert_opt_in),
    alertChannel: (str(m.alert_channel) as QuestionnaireAnswers["alertChannel"]) ?? null,
    hasSmartphone: bool(m.has_smartphone),
    checkinTimes: list(m.checkin_times),
    powerDependentEquipment: list(m.power_dependent_equipment),
    fridgeMedicines: list(m.fridge_medicines),
    mailOrderDropLocation: str(m.mail_order_drop_location),
    outdoorWorkOrSports: bool(m.outdoor_work_or_sports),
    windowsOpen: bool(m.windows_open),
    homeGetsHot: (str(m.home_gets_hot) as QuestionnaireAnswers["homeGetsHot"]) ?? null,
    someoneChecksOn: bool(m.someone_checks_on_them),
    leavesHomeMostDays: bool(m.leaves_home_most_days),
    knowsHeatIllnessSigns: bool(m.knows_heat_illness_signs),
    stableHousing: bool(m.stable_housing),
    answeredOn: str(m.answered_on),
  };
}

export function patientsFromFhirBundle(bundle: Json): PatientRecord[] {
  const byId = new Map<string, PatientRecord>();
  const resources: Json[] = (bundle?.entry ?? []).map((e: Json) => e.resource).filter(Boolean);

  for (const r of resources) {
    if (r.resourceType !== "Patient") continue;
    const name = r.name?.[0] ?? {};
    const addr = r.address?.find((a: Json) => a.use === "home") ?? r.address?.[0] ?? {};
    const lang =
      r.communication?.find((c: Json) => c.preferred)?.language?.coding?.[0]?.code ??
      r.communication?.[0]?.language?.coding?.[0]?.code ??
      "en";
    byId.set(r.id, {
      id: r.id,
      synthetic: ext(r, SYNTHETIC_EXT)?.valueBoolean === true,
      storyLabel: ext(r, STORY_EXT)?.valueString,
      givenName: name.given?.[0] ?? "",
      familyName: name.family ?? "",
      sex: r.gender ?? "unknown",
      birthDate: r.birthDate ?? "",
      zip: String(addr.postalCode ?? ""),
      home: geo(addr),
      language: lang,
      phone: r.telecom?.find((t: Json) => t.system === "phone")?.value,
      conditions: [],
      medications: [],
      contacts: [],
      questionnaire: null,
    });
  }

  for (const r of resources) {
    switch (r.resourceType) {
      case "Condition": {
        const p = byId.get(refId(r.subject?.reference));
        if (!p) break;
        const status = r.clinicalStatus?.coding?.[0]?.code;
        if (status && status !== "active") break;
        const coding = r.code?.coding?.[0] ?? {};
        const text = r.code?.text ?? coding.display ?? "";
        const c: ConditionEntry = { code: coding.code, text, key: conditionKey(text, coding.code) };
        p.conditions.push(c);
        break;
      }
      case "MedicationRequest": {
        const p = byId.get(refId(r.subject?.reference));
        if (!p) break;
        if (r.status && r.status !== "active") break;
        const coding =
          r.medicationCodeableConcept?.coding?.find((c: Json) => /rxnorm/i.test(c.system ?? "")) ??
          r.medicationCodeableConcept?.coding?.[0] ??
          {};
        const m: MedicationOrder = {
          id: r.id,
          rxcui: coding.code,
          generic: String(coding.display ?? r.medicationCodeableConcept?.text ?? "").toLowerCase(),
          text: r.medicationCodeableConcept?.text,
          route: r.dosageInstruction?.[0]?.route?.text,
          status: r.status ?? "active",
          authoredOn: r.authoredOn,
          mailOrder: ext(r, MAIL_EXT)?.valueBoolean === true,
        };
        p.medications.push(m);
        break;
      }
      case "RelatedPerson": {
        const p = byId.get(refId(r.patient?.reference));
        if (!p) break;
        const tel = r.telecom?.find((t: Json) => t.system === "phone");
        const c: TrustedContact = {
          id: r.id,
          patientId: p.id,
          priority: tel?.rank ?? p.contacts.length + 1,
          givenName: r.name?.[0]?.given?.[0] ?? "",
          familyName: r.name?.[0]?.family ?? "",
          relationship: r.relationship?.find((x: Json) => x.text)?.text ?? "contact",
          phone: tel?.value,
          language: r.communication?.[0]?.language?.coding?.[0]?.code,
          home: geo(r),
        };
        p.contacts.push(c);
        break;
      }
      case "QuestionnaireResponse": {
        const p = byId.get(refId(r.subject?.reference));
        if (!p) break;
        const m: Record<string, unknown> = { answered_on: r.authored };
        for (const it of r.item ?? []) m[it.linkId] = answer(it);
        p.questionnaire = questionnaireFromMap(m);
        break;
      }
    }
  }
  for (const p of byId.values()) p.contacts.sort((a, b) => a.priority - b.priority);
  return [...byId.values()];
}

export function ageOn(birthDate: string, isoDate: string): number {
  const [by, bm, bd] = birthDate.split("-").map(Number);
  const [y, m, d] = isoDate.slice(0, 10).split("-").map(Number);
  let a = y - by;
  if (m < bm || (m === bm && d < bd)) a--;
  return a;
}
