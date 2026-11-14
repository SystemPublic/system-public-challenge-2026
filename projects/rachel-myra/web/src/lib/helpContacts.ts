import fs from "node:fs";
import path from "node:path";
import { REPO_ROOT } from "@/lib/kb";
import { parseCsv } from "@/lib/synthetic";

export const HELP_FILE = "data/processed/community_resources_nyc.geojson";
const PATIENTS_FILE = "data/processed/synthetic/patients.csv";

export interface HelpContact { id: string; name: string; offers: string; phone: string | null; address: string | null; website: string | null; distanceMi: number }

interface Place { id: string; name: string; type: string; phone: string | null; services: string | null; languages: string | null; address: string | null; website: string | null; lat: number; lon: number }

const TYPES = new Set(["Food pantry / soup kitchen", "Senior center", "Community organization", "Community center"]);
const SERVICE_RE = /deliver|grocer|meal|pantry|food|errand/i;

let places: Place[] | null = null;
let homes: Map<string, { lat: number; lon: number; age: number; lang: string }> | null = null;

function loadPlaces(): Place[] {
  if (places) return places;
  try {
    const d = JSON.parse(fs.readFileSync(path.join(REPO_ROOT, HELP_FILE), "utf8"));
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    places = (d.features ?? []).flatMap((f: any) => {
      const p = f.properties ?? {};
      const [lon, lat] = f.geometry?.coordinates ?? [];
      if (!TYPES.has(p.type) || !SERVICE_RE.test(`${p.services ?? ""} ${p.type === "Food pantry / soup kitchen" ? "food" : ""}`) || typeof lat !== "number") return [];
      return [{ id: p.id, name: p.name, type: p.type, phone: p.phone, services: p.services, languages: p.languages, address: p.address ? `${p.address}${p.borough ? ", " + p.borough : ""}` : null, website: p.website, lat, lon }];
    });
  } catch {
    places = [];
  }
  return places!;
}

function loadHomes() {
  if (homes) return homes;
  homes = new Map();
  try {
    for (const r of parseCsv(fs.readFileSync(path.join(REPO_ROOT, PATIENTS_FILE), "utf8"))) {
      const lat = Number(r.home_lat), lon = Number(r.home_lon);
      if (Number.isFinite(lat) && Number.isFinite(lon) && r.home_lat) homes.set(r.patient_id, { lat, lon, age: Number(r.age), lang: r.preferred_language });
    }
  } catch {}
  return homes;
}

function miles(aLat: number, aLon: number, bLat: number, bLon: number) {
  const R = 3958.8, toR = Math.PI / 180;
  const dLat = (bLat - aLat) * toR, dLon = (bLon - aLon) * toR;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(aLat * toR) * Math.cos(bLat * toR) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

/** 2–3 nearest places that help with food, meals or errands, by straight-line distance from home. */
export function helpContactsFor(patientId: string, n = 3): HelpContact[] {
  const home = loadHomes().get(patientId);
  if (!home) return [];
  const es = home.lang === "es";
  return loadPlaces()
    .filter((p) => p.type !== "Senior center" || home.age >= 60)
    .map((p) => ({ p, d: miles(home.lat, home.lon, p.lat, p.lon) }))
    .filter((x) => x.d <= 5)
    .sort((a, b) => {
      const sa = es && /spanish/i.test(a.p.languages ?? "") ? 0 : 1;
      const sb = es && /spanish/i.test(b.p.languages ?? "") ? 0 : 1;
      const pa = a.p.phone ? 0 : 0.5, pb = b.p.phone ? 0 : 0.5; // prefer ones with a phone (worth ~0.5 mi)
      return sa - sb || a.d + pa - (b.d + pb);
    })
    .slice(0, n)
    .map(({ p, d }) => {
      const s = (p.services ?? "").replace(/\s+/g, " ").trim();
      return { id: p.id, name: p.name, offers: s.length > 80 ? s.slice(0, 77).trimEnd() + "…" : s, phone: p.phone, address: p.address, website: p.website, distanceMi: Math.round(d * 10) / 10 };
    });
}
