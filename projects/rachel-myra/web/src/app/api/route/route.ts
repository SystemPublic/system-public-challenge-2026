// GET ?from=lon,lat&to=lon,lat → a walking route (GeoJSON LineString) from the free FOSSGIS OSRM foot
// router (routing.openstreetmap.de, no key). Used to draw ONE selected patient's way to a cool place.
// Coordinates are synthetic patients' homes and public places. Cached in memory.
import { connection } from "next/server";

const cache = new Map<string, unknown>();

function parse(s: string | null): [number, number] | null {
  if (!s) return null;
  const [lon, lat] = s.split(",").map(Number);
  return Number.isFinite(lon) && Number.isFinite(lat) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180 ? [lon, lat] : null;
}

export async function GET(req: Request) {
  await connection();
  const u = new URL(req.url);
  const from = parse(u.searchParams.get("from"));
  const to = parse(u.searchParams.get("to"));
  if (!from || !to) return Response.json({ ok: false, error: "from and to required as lon,lat" }, { status: 400 });
  const key = `${from.join(",")};${to.join(",")}`;
  if (cache.has(key)) return Response.json(cache.get(key));
  try {
    const url = `https://routing.openstreetmap.de/routed-foot/route/v1/foot/${from.join(",")};${to.join(",")}?overview=full&geometries=geojson`;
    const r = await fetch(url, { headers: { "User-Agent": "heat-med-hackathon-prototype" }, signal: AbortSignal.timeout(10000) });
    const d = await r.json();
    const route = d?.routes?.[0];
    if (!route) throw new Error("no route");
    const out = { ok: true, source: "OSRM foot routing (routing.openstreetmap.de), © OpenStreetMap", distanceM: route.distance, geometry: route.geometry };
    cache.set(key, out);
    return Response.json(out);
  } catch {
    return Response.json({ ok: false, error: "Routing service unavailable; showing a straight line." });
  }
}
