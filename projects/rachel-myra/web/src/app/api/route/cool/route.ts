// GET ?from=lon,lat&to=lon,lat → up to 3 OSRM foot alternatives (routing.openstreetmap.de, © OpenStreetMap);
// picks the one with the lowest heat exposure = Σ segment length × NYC Heat Vulnerability Index of the
// neighborhood (NTA2020) the segment midpoint falls in. HVI is a neighborhood index, not shade measurements.
import { readFileSync } from "node:fs";
import path from "node:path";
import { connection } from "next/server";

type Ring = number[][];
type Poly = { hvi: number; rings: Ring[][] };
let polys: Poly[] | null = null;
const cache = new Map<string, unknown>();

function loadPolys(): Poly[] {
  if (polys) return polys;
  const d = JSON.parse(readFileSync(path.join(process.cwd(), "..", "data", "processed", "hvi_nta2020.geojson"), "utf8"));
  polys = [];
  for (const f of d.features ?? []) {
    const hvi = Number(f.properties?.hvi);
    if (!Number.isFinite(hvi) || !f.geometry) continue;
    const g = f.geometry;
    polys.push({ hvi, rings: g.type === "Polygon" ? [g.coordinates] : g.coordinates });
  }
  return polys;
}
function inRing(x: number, y: number, r: Ring) {
  let c = false;
  for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
    const [xi, yi] = r[i], [xj, yj] = r[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}
function hviAt(x: number, y: number): number {
  for (const p of loadPolys()) for (const poly of p.rings) if (inRing(x, y, poly[0]) && !poly.slice(1).some((h) => inRing(x, y, h))) return p.hvi;
  return 3; // outside any NTA (parks/water): middle of the 1–5 scale
}
function meters(a: number[], b: number[]) {
  const R = 6371000, toR = Math.PI / 180;
  const dLat = (b[1] - a[1]) * toR, dLon = (b[0] - a[0]) * toR;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * toR) * Math.cos(b[1] * toR) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
function exposure(coords: number[][]) {
  let s = 0;
  for (let i = 1; i < coords.length; i++) {
    const a = coords[i - 1], b = coords[i];
    s += meters(a, b) * hviAt((a[0] + b[0]) / 2, (a[1] + b[1]) / 2);
  }
  return Math.round(s);
}
type Step = { maneuver?: { type?: string; modifier?: string }; name?: string; distance?: number };
function instruction(s: Step): string {
  const type = s.maneuver?.type ?? "", mod = s.maneuver?.modifier ?? "", name = s.name?.trim();
  const d = Math.round((s.distance ?? 0) / 10) * 10;
  if (type === "arrive") return "Arrive at your destination";
  if (type === "depart") return name ? `Start on ${name}${d ? ` for ${d} m` : ""}` : `Start walking${d ? ` for ${d} m` : ""}`;
  const onto = name ? ` onto ${name}` : "";
  if (mod === "straight" || type === "continue" || type === "new name") return name ? `Continue on ${name}${d ? ` for ${d} m` : ""}` : `Continue straight${d ? ` for ${d} m` : ""}`;
  if (mod === "uturn") return `Turn around${onto}`;
  if (mod) return `${mod.startsWith("slight") ? "Bear" : mod.startsWith("sharp") ? "Turn sharp" : "Turn"} ${mod.replace(/^(slight|sharp) /, "")}${onto}`;
  return `Continue${onto}`;
}
function parse(s: string | null): [number, number] | null {
  if (!s) return null;
  const [lon, lat] = s.split(",").map(Number);
  return Number.isFinite(lon) && Number.isFinite(lat) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180 ? [lon, lat] : null;
}

export async function GET(req: Request) {
  await connection();
  const u = new URL(req.url);
  const from = parse(u.searchParams.get("from")), to = parse(u.searchParams.get("to"));
  if (!from || !to) return Response.json({ ok: false, error: "from and to required as lon,lat" }, { status: 400 });
  const key = `${from.join(",")};${to.join(",")}`;
  if (cache.has(key)) return Response.json(cache.get(key));
  try {
    const url = `https://routing.openstreetmap.de/routed-foot/route/v1/foot/${key}?overview=full&geometries=geojson&steps=true&alternatives=3`;
    const r = await fetch(url, { headers: { "User-Agent": "heat-med-hackathon-prototype" }, signal: AbortSignal.timeout(10000) });
    const d = await r.json();
    const routes: { distance: number; geometry: { coordinates: number[][] }; legs?: { steps?: Step[] }[] }[] = d?.routes ?? [];
    if (!routes.length) throw new Error("no route");
    const scored = routes.map((rt) => ({ rt, exp: exposure(rt.geometry.coordinates) }));
    scored.sort((a, b) => a.exp - b.exp || a.rt.distance - b.rt.distance);
    const { rt, exp } = scored[0];
    const steps = (rt.legs ?? []).flatMap((l) => l.steps ?? []).map((s) => ({ instruction: instruction(s), distanceM: Math.round(s.distance ?? 0) }));
    const out = {
      ok: true,
      source: "OSRM foot routing (routing.openstreetmap.de), © OpenStreetMap; heat score = NYC DOHMH Heat Vulnerability Index by neighborhood",
      chosen: { geometry: rt.geometry, distanceM: Math.round(rt.distance), walkMin: Math.round(rt.distance / 0.8 / 60), exposureScore: exp },
      alternatives: routes.length,
      steps,
    };
    cache.set(key, out);
    return Response.json(out);
  } catch {
    return Response.json({ ok: false, error: "Routing service unavailable; showing a straight line." });
  }
}
