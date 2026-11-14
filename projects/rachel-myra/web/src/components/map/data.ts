// Server-only loaders for the clinician heat + help map (/map).
// Every value comes from a file in data/ (nothing invented):
//   risk group   data/processed/panel_scores_replay.json → patients[].readiness.level
//   home         data/processed/synthetic/patients.csv (home_lat, home_lon)
//   heat         data/processed/hvi_nta2020.geojson (NYC heat vulnerability index, 1–5)
//   help places  data/processed/community_resources_nyc.geojson
import fs from "node:fs";
import path from "node:path";
import { REPO_ROOT } from "@/lib/kb";
import { loadPanel } from "@/lib/panel";
import type { RiskGroup } from "./colors";
import { readCsv } from "./csv";

export const PROCESSED = path.join(REPO_ROOT, "data", "processed");
export const FILES = {
  panel: "data/processed/panel_scores_replay.json",
  patients: "data/processed/synthetic/patients.csv",
  questionnaire: "data/processed/synthetic/questionnaire.csv",
  heat: "data/processed/hvi_nta2020.geojson",
  help: "data/processed/community_resources_nyc.geojson",
};

export function riskGroup(level: string | undefined | null): RiskGroup {
  if (level === "high" || level === "very_high") return "High";
  if (level === "medium") return "Medium";
  return "Low";
}

/** Rewrite readiness.drivers into plain words. */
export function plainDriver(d: string): string {
  const s = d.trim();
  if (s.startsWith("neighborhood heat vulnerability index 5")) return "lives in one of the neighborhoods hit hardest by heat";
  if (s.startsWith("neighborhood heat vulnerability index")) return "lives in a neighborhood hit hard by heat";
  if (s.startsWith("on ")) {
    const meds = s.slice(3).split(/\s*(?:\+|,)\s*/).filter(Boolean);
    const list = meds.length > 1 ? `${meds.slice(0, -1).join(", ")} and ${meds[meds.length - 1]}` : meds[0];
    return `takes ${list}`;
  }
  const map: Record<string, string> = {
    "no working ac at home": "has no working AC",
    "has ac but cost limits use": "can't afford to run the AC much",
    "home all day without reliable ac": "is home all day without reliable AC",
    "lives on floor 7 or higher": "lives on a high floor",
    "floor 4+ with no elevator": "lives up several flights of stairs with no elevator",
    "age 75+": "is 75 or older",
    "child under 5": "is a child under 5",
    "can reach a cool place only with help": "needs help to get to a cool place",
    "cannot get to a cool place": "can't get to a cool place",
    "uses power-dependent equipment": "uses medical equipment that needs power",
    "spends the day outdoors or doing physical work": "spends the day outdoors or doing physical work",
    "outdoor work or sports": "works or plays sports outdoors",
    "home often gets hot": "says the home often gets hot",
    "lives alone and no one checks on them": "lives alone with no one checking in",
  };
  return map[s] ?? s;
}

export function plainWhy(drivers: string[] | undefined, group: RiskGroup): string {
  const ds = (drivers ?? []).filter(Boolean);
  if (!ds.length) return group === "Low" ? "No strong heat risks found in their medicines or home." : "Several heat risks add up for this person.";
  // Keep the medicine reason if there is one: that is what the product is about.
  const med = ds.find((d) => d.startsWith("on "));
  const others = ds.filter((d) => d !== med);
  const picked = (med ? [med, ...others.slice(0, 2)] : others.slice(0, 3)).map(plainDriver);
  const list = picked.length > 1 ? `${picked.slice(0, -1).join(", ")} and ${picked[picked.length - 1]}` : picked[0];
  const s = `This person ${list}.`;
  return s;
}

type Ring = number[][];
type Poly = Ring[];
interface HeatFeature {
  type: "Feature";
  geometry: { type: "Polygon" | "MultiPolygon"; coordinates: Poly | Poly[] };
  properties: { nta2020: string; ntaname: string; borough: string; hvi: number };
}

function inRing(x: number, y: number, ring: Ring): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
function inFeature(x: number, y: number, f: HeatFeature): boolean {
  const polys = (f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates) as Poly[];
  return polys.some((p) => inRing(x, y, p[0]) && !p.slice(1).some((h) => inRing(x, y, h)));
}
const r5 = (n: number) => Math.round(n * 1e5) / 1e5;

export interface HeatArea {
  type: "Feature";
  geometry: HeatFeature["geometry"];
  properties: { nta: string; name: string; borough: string; hvi: number };
}

export interface MapPatient {
  id: string;
  name: string;
  age: number;
  zip: string;
  lat: number;
  lon: number;
  group: RiskGroup;
  why: string;
  nta: string | null;
  ntaName: string | null;
  /** questionnaire.csv alert_opt_in; false → "Call instead". */
  textOk: boolean;
  /** Every reason, in plain words (for the "Why?" panel). */
  reasons: string[];
}

export interface HelpPoint { id: string; name: string; type: string; lon: number; lat: number }
export interface HelpPlace {
  id: string; name: string; type: string; address: string | null; borough: string | null; zip: string | null;
  phone: string | null; website: string | null; hours: string | null; services: string | null;
  languages: string | null; operator: string | null; source: string | null; accessed: string | null;
  lon: number; lat: number;
}

const cache = globalThis as unknown as {
  __mapHeat?: { mtime: number; areas: HeatArea[]; raw: HeatFeature[] };
  __mapHelp?: { mtime: number; points: HelpPoint[]; byId: Map<string, HelpPlace> };
  __mapPatients?: { key: string; patients: MapPatient[] };
};

export function loadHeatAreas() {
  const f = path.join(REPO_ROOT, FILES.heat);
  if (!fs.existsSync(f)) return null;
  const mtime = fs.statSync(f).mtimeMs;
  if (cache.__mapHeat?.mtime === mtime) return cache.__mapHeat;
  const gj = JSON.parse(fs.readFileSync(f, "utf8")) as { features: HeatFeature[] };
  const roundPoly = (p: Poly): Poly => p.map((ring) => ring.map(([x, y]) => [r5(x), r5(y)]));
  const areas: HeatArea[] = gj.features
    .filter((ft) => ft.geometry && Number.isFinite(Number(ft.properties.hvi)))
    .map((ft) => ({
      type: "Feature",
      geometry: {
        type: ft.geometry.type,
        coordinates: ft.geometry.type === "Polygon"
          ? roundPoly(ft.geometry.coordinates as Poly)
          : (ft.geometry.coordinates as Poly[]).map(roundPoly),
      },
      properties: { nta: ft.properties.nta2020, name: ft.properties.ntaname, borough: ft.properties.borough, hvi: Number(ft.properties.hvi) },
    }));
  cache.__mapHeat = { mtime, areas, raw: gj.features.filter((ft) => ft.geometry) };
  return cache.__mapHeat;
}

export function loadHelp() {
  const f = path.join(REPO_ROOT, FILES.help);
  if (!fs.existsSync(f)) return null;
  const mtime = fs.statSync(f).mtimeMs;
  if (cache.__mapHelp?.mtime === mtime) return cache.__mapHelp;
  const gj = JSON.parse(fs.readFileSync(f, "utf8")) as {
    features: { geometry: { coordinates: [number, number] } | null; properties: Record<string, string | null> }[];
  };
  const byId = new Map<string, HelpPlace>();
  const points: HelpPoint[] = [];
  for (const ft of gj.features) {
    if (!ft.geometry) continue;
    const p = ft.properties;
    const [lon, lat] = ft.geometry.coordinates;
    const id = String(p.id);
    const place: HelpPlace = {
      id, name: p.name ?? "Unnamed place", type: p.type ?? "Other", address: p.address, borough: p.borough, zip: p.zip,
      phone: p.phone, website: p.website, hours: p.hours, services: p.services, languages: p.languages,
      operator: p.operator, source: p.source, accessed: p.accessed, lon, lat,
    };
    byId.set(id, place);
    points.push({ id, name: place.name, type: place.type, lon: r5(lon), lat: r5(lat) });
  }
  cache.__mapHelp = { mtime, points, byId };
  return cache.__mapHelp;
}

export function loadMapPatients(): MapPatient[] {
  const panel = loadPanel("replay");
  const pf = path.join(REPO_ROOT, FILES.patients);
  if (!panel || !fs.existsSync(pf)) return [];
  const key = `${panel.mtime}:${fs.statSync(pf).mtimeMs}`;
  if (cache.__mapPatients?.key === key) return cache.__mapPatients.patients;
  const rows = readCsv(pf);
  const home = new Map(rows.map((r) => [r.patient_id, r]));
  const optIn = new Map(readCsv(path.join(REPO_ROOT, FILES.questionnaire)).map((r) => [r.patient_id, r.alert_opt_in !== "false"]));
  const heat = loadHeatAreas();
  const out: MapPatient[] = [];
  for (const p of panel.data.patients as unknown as {
    patientId: string; displayName: string; age: number; zip: string; readiness?: { level?: string; drivers?: string[] };
  }[]) {
    const h = home.get(p.patientId);
    const lat = Number(h?.home_lat);
    const lon = Number(h?.home_lon);
    if (!h || !Number.isFinite(lat) || !Number.isFinite(lon)) continue;
    const group = riskGroup(p.readiness?.level);
    const area = heat?.raw.find((f) => inFeature(lon, lat, f)) ?? null;
    out.push({
      id: p.patientId, name: p.displayName, age: p.age, zip: p.zip, lat, lon, group,
      why: plainWhy(p.readiness?.drivers, group),
      nta: area?.properties.nta2020 ?? null, ntaName: area?.properties.ntaname ?? null,
      textOk: optIn.get(p.patientId) ?? true,
      reasons: (p.readiness?.drivers ?? []).map((d) => { const t = plainDriver(d); return t.charAt(0).toUpperCase() + t.slice(1); }),
    });
  }
  cache.__mapPatients = { key, patients: out };
  return out;
}
