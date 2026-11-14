// Server-only loader for <PatientPlanMap>. Sources (nothing invented):
//   home            data/processed/synthetic/patients.csv (home_lat, home_lon)
//   nearest help    data/processed/synthetic/cooling_match.csv (rank 1: place, walk_min)
//   leave by        panel_scores_replay.json cooling.best.leaveBy (same as the text), else cooling_match.csv leave_by
//   can reach alone data/processed/synthetic/questionnaire.csv (q5_can_reach_cool_place)
//   subway          data/processed/subway_stations_nyc.geojson (nearest by straight line)
//   hottest hours   data/processed/replay_heatwave_hourly.csv (demo day, LaGuardia, feels-like >= 95°F)
//   risk group      data/processed/panel_scores_replay.json (readiness.level)
import fs from "node:fs";
import path from "node:path";
import { REPO_ROOT } from "@/lib/kb";
import { getPanelPatient, loadPanel } from "@/lib/panel";
import type { RiskGroup } from "./colors";
import { readCsv } from "./csv";
import { riskGroup } from "./data";
import { clock } from "./format";

export const PLAN_FILES = {
  patients: "data/processed/synthetic/patients.csv",
  cooling: "data/processed/synthetic/cooling_match.csv",
  questionnaire: "data/processed/synthetic/questionnaire.csv",
  subway: "data/processed/subway_stations_nyc.geojson",
  hourly: "data/processed/replay_heatwave_hourly.csv",
};

/** Rules used to show "Ask for a delivery instead". */
export const LONG_WALK_MIN = 15;
export const HOT_FEELS_LIKE_F = 95;
const HOURLY_STATION = "LaGuardia";

export interface PlanPlace {
  name: string; type: string; address: string; phone: string | null; hours: string | null;
  lat: number; lon: number; walkMin: number | null; walkKm: number | null;
  leaveBy: string | null; arriveBefore: string | null; officialCoolingCenter: boolean; notes: string[];
  /** Opening time on the demo day, "HH:MM" (cooling_match.csv opens_ref_day / closes_ref_day). */
  opens: string | null; closes: string | null;
}

export interface PatientPlanMapData {
  patientId: string;
  name: string;
  group: RiskGroup | null;
  home: { lat: number; lon: number } | null;
  place: PlanPlace | null;
  subway: { name: string; routes: string; lat: number; lon: number; meters: number } | null;
  hottest: { date: string; station: string; startHour: number; endHour: number; peakF: number } | null;
  canReachAlone: "yes" | "with_help" | "no" | null;
  delivery: { show: boolean; reasons: string[] };
  sources: string[];
}

const p = (rel: string) => path.join(REPO_ROOT, rel);

function haversineM(a: { lat: number; lon: number }, b: { lat: number; lon: number }) {
  const R = 6371000, toR = Math.PI / 180;
  const dLat = (b.lat - a.lat) * toR, dLon = (b.lon - a.lon) * toR;
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * toR) * Math.cos(b.lat * toR) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

const cache = globalThis as unknown as {
  __planCsv?: Map<string, { mtime: number; rows: Record<string, string>[] }>;
  __planSubway?: { name: string; routes: string; lat: number; lon: number }[];
};

function rows(rel: string) {
  cache.__planCsv ??= new Map();
  const f = p(rel);
  if (!fs.existsSync(f)) return [];
  const mtime = fs.statSync(f).mtimeMs;
  const hit = cache.__planCsv.get(rel);
  if (hit && hit.mtime === mtime) return hit.rows;
  const r = readCsv(f);
  cache.__planCsv.set(rel, { mtime, rows: r });
  return r;
}

function subwayStations() {
  if (cache.__planSubway) return cache.__planSubway;
  const f = p(PLAN_FILES.subway);
  if (!fs.existsSync(f)) return [];
  const gj = JSON.parse(fs.readFileSync(f, "utf8")) as {
    features: { geometry: { coordinates: [number, number] }; properties: { stop_name: string; routes: string } }[];
  };
  cache.__planSubway = gj.features.map((ft) => ({
    name: ft.properties.stop_name, routes: ft.properties.routes ?? "",
    lon: ft.geometry.coordinates[0], lat: ft.geometry.coordinates[1],
  }));
  return cache.__planSubway;
}

/** Hottest stretch on the demo day: hours whose feels-like temperature is >= HOT_FEELS_LIKE_F. */
function hottestHours(date: string) {
  const hrs = rows(PLAN_FILES.hourly).filter((r) => r.station_name === HOURLY_STATION && r.date_local === date);
  const hot = hrs.filter((r) => Number(r.heat_index_f) >= HOT_FEELS_LIKE_F).map((r) => Number(r.hour_local));
  if (!hot.length) return null;
  const peak = Math.max(...hrs.map((r) => Number(r.heat_index_f)).filter(Number.isFinite));
  return { date, station: HOURLY_STATION, startHour: Math.min(...hot), endHour: Math.max(...hot) + 1, peakF: Math.round(peak) };
}

const num = (s: string | undefined) => (s === undefined || s === "" || !Number.isFinite(Number(s)) ? null : Number(s));
const hhmmToMin = (s: string | null) => {
  if (!s) return null;
  const m = /^(\d{1,2}):(\d{2})/.exec(s);
  return m ? Number(m[1]) * 60 + Number(m[2]) : null;
};

export function getPatientPlanMapData(patientId: string): PatientPlanMapData {
  const panel = loadPanel("replay");
  const pp = getPanelPatient(patientId, "replay") as (ReturnType<typeof getPanelPatient> & { readiness?: { level?: string } }) | null;
  const prow = rows(PLAN_FILES.patients).find((r) => r.patient_id === patientId);
  const crow = rows(PLAN_FILES.cooling).find((r) => r.patient_id === patientId && r.rank === "1");
  const qrow = rows(PLAN_FILES.questionnaire).find((r) => r.patient_id === patientId);

  const lat = num(prow?.home_lat), lon = num(prow?.home_lon);
  const home = lat !== null && lon !== null ? { lat, lon } : null;

  let place: PlanPlace | null = null;
  if (crow && num(crow.place_lat) !== null && num(crow.place_lon) !== null) {
    const best = pp?.cooling?.best as (Record<string, unknown> | null | undefined);
    const arrive = /before ([^.]+)\./.exec(crow.text_line ?? "");
    place = {
      name: crow.place_name, type: crow.place_type, address: [crow.address, crow.borough, crow.zip].filter(Boolean).join(", "),
      phone: crow.phone || null, hours: crow.hours_ref_day_raw || null,
      lat: Number(crow.place_lat), lon: Number(crow.place_lon),
      walkMin: num(crow.walk_min), walkKm: num(crow.walk_dist_km),
      // Same leave-by the patient's text uses: panel cooling.best first, then cooling_match.csv.
      leaveBy: (best?.leaveBy as string | undefined) || crow.leave_by || null,
      arriveBefore: (best?.arriveBy ? clock(best.arriveBy as string) : null) ?? (arrive ? arrive[1] : null),
      officialCoolingCenter: crow.official_cooling_center === "true",
      opens: crow.opens_ref_day || null, closes: crow.closes_ref_day || null,
      notes: (crow.notes ?? "").split(";").map((s) => s.trim()).filter(Boolean),
    };
  }

  let subway: PatientPlanMapData["subway"] = null;
  if (home) {
    for (const s of subwayStations()) {
      const m = haversineM(home, s);
      if (!subway || m < subway.meters) subway = { ...s, meters: Math.round(m) };
    }
  }

  const date = panel?.data.meta.as_of ?? "2025-06-24";
  const hottest = hottestHours(date);
  const q5 = (qrow?.q5_can_reach_cool_place ?? "") as PatientPlanMapData["canReachAlone"] | "";

  const reasons: string[] = [];
  if (place?.walkMin !== null && place?.walkMin !== undefined && place.walkMin > LONG_WALK_MIN) reasons.push(`The walk is long (about ${Math.round(place.walkMin)} minutes).`);
  if (q5 === "no") reasons.push("You told us you can't get to a cool place.");
  if (q5 === "with_help") reasons.push("You told us you need help to get to a cool place.");
  const leave = hhmmToMin(place?.leaveBy ?? null);
  if (hottest && leave !== null && leave >= hottest.startHour * 60 && leave < hottest.endHour * 60) reasons.push("You would be walking in the hottest hours.");

  return {
    patientId,
    name: pp?.displayName ?? (prow ? `${prow.given_name} ${prow.family_name}` : patientId),
    group: pp ? riskGroup(pp.readiness?.level) : null,
    home, place, subway, hottest,
    canReachAlone: q5 === "" ? null : q5,
    delivery: { show: reasons.length > 0, reasons },
    sources: Object.values(PLAN_FILES),
  };
}
