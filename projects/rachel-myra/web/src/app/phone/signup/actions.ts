"use server";

// Scores the sign-up answers with the SAME rules the panel uses (lib/patient):
//   medRiskStack → personalExposure → readinessLevel (+ lifestyleSusceptibility),
// then maps readiness.level → Low / Medium / High with web/src/lib/risk.ts.
// The patient's record (conditions, ZIP, age) comes from data/processed/synthetic/patients_fhir.json;
// only the questionnaire answers and the medicine list are replaced by what was entered.

import fs from "node:fs";
import path from "node:path";
// Imported file by file (not via lib/patient/index.ts or load-node.ts) so the web type-check
// does not pull in lib/patient/stacking.ts, which has a strict-mode error outside this task.
import { parseCsv } from "@lib/patient/csv.ts";
import { overlayKnowledgeBase, provisionalIndex } from "@lib/patient/drug-profiles.ts";
import type { DrugProfileIndex } from "@lib/patient/drug-profiles.ts";
import { personalExposure, readinessLevel } from "@lib/patient/exposure.ts";
import type { NeighborhoodData } from "@lib/patient/exposure.ts";
import { patientsFromFhirBundle } from "@lib/patient/fhir.ts";
import { lifestyleSusceptibility } from "@lib/patient/lifestyle.ts";
import { medRiskStack } from "@lib/patient/med-risk.ts";
import type { HealthSystemConfig } from "@lib/types/health-system.ts";
import type { PatientRecord } from "@lib/types/patient.ts";
import type { QuestionnaireAnswers } from "@lib/types/patient.ts";
import type { IntakeAnswers, IntakeResult } from "@/components/intake/types";
import { REPO_ROOT } from "@/lib/kb";
import { getPanelPatient } from "@/lib/panel";
import { patientWhy, patientWhyEs, riskGroup } from "@/lib/risk";

// Second-person wording for readiness.drivers (lower-cased EXPOSURE_POINTS labels + age modifiers).
const YOU: Record<string, string> = {
  "no working ac at home": "You have no working AC at home.",
  "has ac but cost limits use": "Running your AC costs a lot.",
  "spends the day outdoors or doing physical work": "You spend the day outdoors or doing physical work.",
  "outdoor work or sports": "You work or play sports outdoors.",
  "home all day without reliable ac": "You are home all day without reliable AC.",
  "lives alone": "You live alone.",
  "lives alone and no one checks on them": "You live alone and no one checks on you.",
  "cannot get to a cool place": "You can't get to a cool place.",
  "can reach a cool place only with help": "You need help to get to a cool place.",
  "lives on floor 7 or higher": "You live on a high floor.",
  "floor 4+ with no elevator": "You live up several flights of stairs.",
  "home often gets hot": "Your home often gets hot.",
  "uses power-dependent equipment": "You use medical equipment that needs power.",
  "neighborhood heat vulnerability index 5 (highest)": "You live in one of the most heat-exposed neighborhoods.",
  "neighborhood heat vulnerability index 4": "You live in a heat-exposed neighborhood.",
  "age 75+": "You are 75 or older.",
  "child under 5": "Young children get sick from heat faster.",
};

// Spanish (usted form) for the same drivers. Machine-style translation, flagged "por revisar" in the UI.
const YOU_ES: Record<string, string> = {
  "no working ac at home": "No tiene aire acondicionado que funcione en casa.",
  "has ac but cost limits use": "Usar el aire acondicionado le cuesta mucho.",
  "spends the day outdoors or doing physical work": "Pasa el día afuera o haciendo trabajo físico.",
  "outdoor work or sports": "Trabaja o hace deporte al aire libre.",
  "home all day without reliable ac": "Pasa el día en casa sin aire acondicionado confiable.",
  "lives alone": "Vive solo/a.",
  "lives alone and no one checks on them": "Vive solo/a y nadie viene a verle.",
  "cannot get to a cool place": "No puede llegar a un lugar fresco.",
  "can reach a cool place only with help": "Necesita ayuda para llegar a un lugar fresco.",
  "lives on floor 7 or higher": "Vive en un piso alto.",
  "floor 4+ with no elevator": "Tiene que subir varios pisos por escalera.",
  "home often gets hot": "Su casa se calienta mucho a menudo.",
  "uses power-dependent equipment": "Usa equipo médico que necesita electricidad.",
  "neighborhood heat vulnerability index 5 (highest)": "Vive en uno de los barrios más expuestos al calor.",
  "neighborhood heat vulnerability index 4": "Vive en un barrio expuesto al calor.",
  "age 75+": "Tiene 75 años o más.",
  "child under 5": "Los niños pequeños se enferman por el calor más rápido.",
};

type Ctx = { drugIndex: DrugProfileIndex; neighborhood: NeighborhoodData; patients: PatientRecord[] };

const g = globalThis as unknown as { __intakeCtx?: Ctx };
const read = (rel: string) => fs.readFileSync(path.join(REPO_ROOT, rel), "utf8");
const exists = (rel: string) => fs.existsSync(path.join(REPO_ROOT, rel));

// Same steps as lib/patient/load-node.ts (loadDrugIndex, loadNeighborhood, loadPatients).
function ctx(): Ctx {
  if (g.__intakeCtx) return g.__intakeCtx;
  const cfg = JSON.parse(read("config/health-systems/sbh.json")) as HealthSystemConfig;
  const ds = cfg.data_sources;

  let idx = provisionalIndex();
  const acbPath = ds.knowledge_base.find((p) => /anticholinergic/i.test(p));
  const acbRows = acbPath && exists(acbPath) ? parseCsv(read(acbPath)) : [];
  let matchedKb = false;
  for (const p of ds.knowledge_base.filter((x) => x.endsWith(".json"))) {
    if (!exists(p)) continue;
    try {
      const { index, matched } = overlayKnowledgeBase(idx, JSON.parse(read(p)), /mock/.test(p) ? "mock_knowledge_base" : "knowledge_base", acbRows);
      if (matched > 0) {
        idx = index;
        matchedKb = true;
        break;
      }
    } catch {
      /* keep provisional mapping, as load-node.ts does */
    }
  }
  if (!matchedKb && acbRows.length) idx = overlayKnowledgeBase(idx, [], "knowledge_base", acbRows).index;

  const hviByZip = new Map<string, number>();
  for (const r of parseCsv(read(ds.hvi_by_zip))) {
    const z = r.zcta20 ?? r.modzcta ?? r.zip;
    const v = Number(r.hvi);
    if (z && Number.isFinite(v)) hviByZip.set(z, v);
  }
  const ac = parseCsv(read(ds.ac_households));
  const pctNoAcByZip: NeighborhoodData["pctNoAcByZip"] = new Map();
  for (const [zip, area] of Object.entries(ds.zip_to_ac_area)) {
    const row = ac.find((r) => r.geotype === area.geotype && r.geoid === area.geoid && Number(r.year) === ds.ac_year && r.measure === "pct_households_with_ac");
    if (row) pctNoAcByZip.set(zip, { pct: +(100 - Number(row.value)).toFixed(1), area: `${area.name} (${area.geotype} ${ds.ac_year})`, approximate: area.approximate });
  }

  g.__intakeCtx = {
    drugIndex: idx,
    neighborhood: { hviByZip, pctNoAcByZip },
    patients: patientsFromFhirBundle(JSON.parse(read("data/processed/synthetic/patients_fhir.json"))),
  };
  return g.__intakeCtx;
}

export async function scoreIntake(patientId: string, a: IntakeAnswers, takingMedIds: string[], lang: "en" | "es" = "en"): Promise<IntakeResult | { error: string }> {
  const c = ctx();
  const rec = c.patients.find((p) => p.id === patientId);
  const panel = getPanelPatient(patientId, "replay");
  if (!rec || !panel) return { error: `Patient ${patientId} not found in patients_fhir.json / panel_scores_replay.json` };

  const base = rec.questionnaire ?? ({} as QuestionnaireAnswers);
  const q: QuestionnaireAnswers = {
    ...base,
    workingAc: a.workingAc,
    homeGetsHot: a.homeGetsHot,
    stableHousing: a.stableHousing,
    floor: a.floor,
    hasElevator: a.hasElevator,
    livesAlone: a.livesAlone,
    someoneChecksOn: a.someoneChecksOn,
    canReachCoolPlace: a.canReachCoolPlace,
    // Yes/no on the phone; keep the record's list when it already says yes.
    powerDependentEquipment: a.powerEquipment ? (base.powerDependentEquipment?.length ? base.powerDependentEquipment : ["reported at sign-up"]) : [],
    fridgeMedicines: a.fridgeMedicines ? (base.fridgeMedicines?.length ? base.fridgeMedicines : ["reported at sign-up"]) : [],
    knowsHeatIllnessSigns: a.knowsHeatIllnessSigns,
    dayLocation: a.dayLocation,
    outdoorWorkOrSports: a.outdoorWorkOrSports,
    alertOptIn: a.alertOptIn,
  };
  const keep = new Set(takingMedIds);
  const meds = rec.medications.filter((m) => keep.has(m.id));

  const med = medRiskStack(meds, c.drugIndex);
  const exp = personalExposure(q, rec.zip, c.neighborhood);
  // Age as shown in the panel file (computed by scripts/compute_panel.ts).
  const readiness = readinessLevel(med, exp, panel.age, rec.conditions.map((x) => x.key));
  const lifestyle = lifestyleSusceptibility(q);
  // Same "stacked" rule as lib/patient/stacking.ts (2+ medicines weaken the same body defense).
  const stacking = {
    mechanisms: med.defenses
      .filter((d) => d.defense !== "medicine_storage")
      .map((d) => ({ defense: d.defense, label: d.label, drugs: d.drugs, stacked: d.drugs.length >= 2 })),
  };

  const group = riskGroup(readiness.level);
  const es = lang === "es";
  let why = es ? patientWhyEs({ readiness, stacking, lifestyle }) : patientWhy({ readiness, stacking, lifestyle });
  const hotOnly = es ? "Hoy hace mucho calor." : "Today is very hot.";
  if (why === hotOnly) {
    // No medicine or AC reason: say which home answers drove the group (readiness.drivers).
    const home = readiness.drivers.map((d) => (es ? YOU_ES : YOU)[d]).filter(Boolean).slice(0, 2);
    if (home.length) why = `${home.join(" ")} ${hotOnly}`;
  }
  const recordGroup = panel.readiness ? riskGroup(panel.readiness.level) : null;
  return {
    group,
    why,
    sameAsRecord: recordGroup === group,
    recordGroup,
    method: es
      ? "Su grupo sale de sus medicinas y de su casa, igual que en la lista de su clínica."
      : "Your group comes from your medicines and your home, the same way your clinic's list does.",
  };
}
