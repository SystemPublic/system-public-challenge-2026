// Data for the heat-day time-lapse (/replay). Server-only (reads files). Nothing invented:
//   data/processed/replay_hrrr_grid.json       hourly "feels like" °F on a 0.03° grid (NOAA HRRR 3 km via Open-Meteo)
//   data/processed/heatrisk_zip_replay.csv     NWS/WPC HeatRisk by ZIP and day
//   data/processed/synthetic/patients.csv      synthetic patients' home locations
//   data/processed/synthetic/medications.csv   their medicines (heat class)
//   data/processed/panel_scores_replay.json    risk level, reasons, nearest cool place + leave-by (2025-06-24)
//   data/processed/system_api_pathways.csv     System Public Graph: medicine → body effect and heat → body effect study counts
import fs from "node:fs";
import path from "node:path";
import { REPO_ROOT } from "@/lib/kb";
import { plainWhy } from "@/lib/plainWhy";
import { parseCsv } from "@lib/patient/csv.ts";

const P = (...p: string[]) => path.join(REPO_ROOT, "data", "processed", ...p);

export type RiskGroup = "High" | "Medium" | "Low";

export interface HeatGrid {
  lats: number[];
  lons: number[];
  times: string[]; // local ISO hours
  f: (number | null)[][][]; // [t][lat][lon]
  source: string;
}

export interface SystemLink {
  effect: string; // plain words
  drugStudies: number; // studies in System linking this medicine class to the effect
  heatStudies: number; // studies in System linking heat to the same effect
}

export interface PatientMed {
  name: string;
  heatClass: string;
  links: SystemLink[];
}

export interface ReplayPatient {
  id: string;
  name: string;
  age: number;
  group: RiskGroup;
  lon: number;
  lat: number;
  why: string[];
  meds: PatientMed[];
  shared: { effect: string; meds: string[] }[]; // effects hit by 2+ of their medicines (stacking)
  place: {
    name: string;
    address: string | null;
    lon: number;
    lat: number;
    walkMin: number | null;
    leaveBy: string | null;
    arriveBy: string | null;
    hours: string | null;
    needsHelp: boolean;
  } | null;
}

export interface ReplayData {
  grid: HeatGrid;
  eventDate: string;
  heatriskByDate: Record<string, number>;
  patients: ReplayPatient[];
  sources: string[];
}

const START = "2025-06-22T00:00";
const END = "2025-06-26T12:00";

// Medication heat class (synthetic/medications.csv) → System pathway drug group (system_api_pathways.csv).
const CLASS_TO_GROUP: Record<string, string> = {
  "ACE inhibitors/ARBs": "acei_arb",
  metformin: "metformin",
  SSRIs: "ssris",
  "beta blockers": "beta_blockers",
  insulin: "insulin",
  anticholinergics: "anticholinergics",
  thiazides: "thiazides",
  antipsychotics: "antipsychotics",
  "SGLT2 inhibitors": "sglt2",
  "loop diuretics": "loop_diuretics",
  "epinephrine auto-injectors": "epinephrine_ai",
  "ADHD stimulants": "adhd_stimulants",
  "topiramate/zonisamide": "topiramate_zonisamide",
  lithium: "lithium",
  "fentanyl/opioid patches": "opioids_fentanyl",
};
const EFFECT_WORDS: Record<string, string> = {
  dehydration: "dehydration",
  hyponatremia: "low salt (sodium) in the blood",
  aki: "kidney strain",
  bp_hypotension: "low blood pressure",
  sweating: "trouble sweating",
  body_temp: "body overheating",
};

export function loadReplay(): ReplayData | null {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const g = JSON.parse(fs.readFileSync(P("replay_hrrr_grid.json"), "utf8")) as any;
    const keep = (g.times as string[]).map((t, i) => [t, i] as const).filter(([t]) => t >= START && t <= END);
    const grid: HeatGrid = {
      lats: g.lats,
      lons: g.lons,
      times: keep.map(([t]) => t),
      f: keep.map(([, i]) => g.apparent_f[i]),
      source: g.source,
    };

    const heatriskByDate: Record<string, number> = {};
    for (const r of parseCsv(fs.readFileSync(P("heatrisk_zip_replay.csv"), "utf8"))) {
      if (r.zip === "10457") heatriskByDate[r.date] = Number(r.heatrisk_day1);
    }

    // System pathways by drug group
    const paths = new Map<string, SystemLink[]>();
    for (const r of parseCsv(fs.readFileSync(P("system_api_pathways.csv"), "utf8"))) {
      const ds = Number(r.drug_leg_studies) || 0;
      if (ds <= 0) continue;
      const list = paths.get(r.drug_group) ?? [];
      list.push({ effect: EFFECT_WORDS[r.mediator] ?? r.mediator, drugStudies: ds, heatStudies: Number(r.heat_leg_studies) || 0 });
      paths.set(r.drug_group, list);
    }
    for (const l of paths.values()) l.sort((a, b) => b.drugStudies - a.drugStudies);

    const medsBy = new Map<string, PatientMed[]>();
    for (const r of parseCsv(fs.readFileSync(P("synthetic", "medications.csv"), "utf8"))) {
      if (r.status && r.status !== "active") continue;
      const grp = CLASS_TO_GROUP[r.heat_class_spec_8_7];
      if (!grp) continue;
      const list = medsBy.get(r.patient_id) ?? [];
      if (!list.some((m) => m.name === r.generic_name)) {
        list.push({ name: r.generic_name, heatClass: r.heat_class_spec_8_7, links: paths.get(grp) ?? [] });
      }
      medsBy.set(r.patient_id, list);
    }

    const homes = new Map<string, { lat: number; lon: number }>();
    for (const r of parseCsv(fs.readFileSync(P("synthetic", "patients.csv"), "utf8"))) {
      const lat = Number(r.home_lat), lon = Number(r.home_lon);
      if (Number.isFinite(lat) && Number.isFinite(lon)) homes.set(r.patient_id, { lat, lon });
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const panel = JSON.parse(fs.readFileSync(P("panel_scores_replay.json"), "utf8")) as any;
    const groupOf = (lvl: string): RiskGroup => (lvl === "high" || lvl === "very_high" ? "High" : lvl === "medium" ? "Medium" : "Low");
    const patients: ReplayPatient[] = [];
    for (const p of panel.patients) {
      const home = homes.get(p.patientId);
      if (!home) continue;
      const meds = medsBy.get(p.patientId) ?? [];
      const byEffect = new Map<string, string[]>();
      for (const m of meds) for (const l of m.links) byEffect.set(l.effect, [...(byEffect.get(l.effect) ?? []), m.name]);
      const shared = [...byEffect.entries()].filter(([, ms]) => ms.length > 1).map(([effect, ms]) => ({ effect, meds: ms }));
      const b = p.cooling?.best;
      patients.push({
        id: p.patientId,
        name: p.displayName,
        age: p.age,
        group: groupOf(p.readiness?.level),
        lon: home.lon,
        lat: home.lat,
        why: ((p.readiness?.drivers as string[]) ?? []).map(plainWhy),
        meds,
        shared,
        place:
          b && Number.isFinite(b.lat)
            ? {
                name: b.name,
                address: b.address ?? null,
                lon: b.lon,
                lat: b.lat,
                walkMin: b.travelMin ?? null,
                leaveBy: b.leaveBy ?? null,
                arriveBy: b.arriveBy ?? null,
                hours: b.hoursToday ?? null,
                needsHelp: (b.caveats as string[] | undefined)?.some((c) => /help/i.test(c)) ?? false,
              }
            : null,
      });
    }

    return {
      grid,
      eventDate: panel.meta?.as_of ?? "2025-06-24",
      heatriskByDate,
      patients,
      sources: [
        "Heat: NOAA HRRR 3 km model, hourly “feels like” temperature, via Open-Meteo (data/processed/replay_hrrr_grid.json)",
        "Heat warning: NWS/WPC HeatRisk archive (data/processed/heatrisk_zip_replay.csv)",
        "Medicine → body effect ← heat: System Public Graph API (data/processed/system_api_pathways.csv)",
        "Patients: synthetic (data/processed/synthetic/, panel_scores_replay.json)",
        "Walking routes: OSRM foot routing on OpenStreetMap (fetched when you click “Show the way”)",
      ],
    };
  } catch {
    return null;
  }
}
