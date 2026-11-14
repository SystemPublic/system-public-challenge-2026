// Usage: node scripts/forecast/build-geo.mjs <countries.geojson> <places.geojson> <outDir> [threshold=0.3]
import fs from "node:fs";
import path from "node:path";

const [countriesPath, placesPath, outDir, thr] = process.argv.slice(2);
if (!countriesPath || !placesPath || !outDir) {
  console.error("usage: build-geo.mjs <countries.geojson> <places.geojson> <outDir> [threshold]");
  process.exit(1);
}
const THRESH = thr ? Number(thr) : 0.3;

const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, M = Math.sqrt(3) / 2;
const rad = Math.PI / 180;
function eq(lon, lat) {
  const p = lat * rad, l = Math.asin(M * Math.sin(p)), l2 = l * l, l6 = l2 * l2 * l2;
  return [
    (lon * rad * Math.cos(l)) / (M * (A1 + 3 * A2 * l2 + l6 * (7 * A3 + 9 * A4 * l2))),
    l * (A1 + A2 * l2 + l6 * (A3 + A4 * l2)),
  ];
}
const S = 500 / eq(180, 0)[0];
const yTop = eq(0, 84)[1];
const project = (lon, lat) => {
  const [x, y] = eq(lon, lat);
  return [500 + x * S, (yTop - y) * S];
};
const HEIGHT = Math.ceil((yTop - eq(0, -58)[1]) * S);

const OVERRIDE = { LAO: "Laos", PRK: "North Korea", KOR: "South Korea", RUS: "Russia", BRN: "Brunei",
  COD: "Democratic Republic of the Congo", COG: "Republic of the Congo", GMB: "The Gambia",
  CIV: "Côte d'Ivoire", TZA: "Tanzania" };
const EXTRA = { COD: ["DRC", "DR Congo", "Congo-Kinshasa", "Zaire"], COG: ["Congo-Brazzaville"],
  CIV: ["Ivory Coast", "Cote d'Ivoire"], GMB: ["Gambia"], LAO: ["Lao PDR"], MMR: ["Burma"],
  VNM: ["Viet Nam"], PNG: ["PNG"], USA: ["USA", "America"], GBR: ["UK", "Britain"], SWZ: ["Swaziland"],
  CPV: ["Cape Verde", "Cabo Verde"], TLS: ["East Timor"], TZA: ["United Republic of Tanzania"] };
const REQUIRED = "BGD BEN BFA KHM CMR COL CIV COD ETH GAB GMB GHA GIN IND IDN KEN LAO MDG MWI MLI MRT MOZ MMR NGA PNG PER SEN SDN TZA THA UGA VEN VNM SLE TCD ZMB SOM RWA NAM TGO".split(" ");

const f2 = (n) => Math.round(n * 100) / 100;
const fmt = (n) => String(f2(n)).replace(/^(-?)0\./, "$1.");

function ringArea(r) {
  let a = 0;
  for (let i = 0; i < r.length - 1; i++) a += r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1];
  return a / 2;
}
function simplify(ring) {
  const pts = ring.map(([lo, la]) => project(lo, la).map(f2));
  const run = (th) => {
    const kept = [pts[0]];
    for (let i = 1; i < pts.length; i++) {
      const p = pts[i], q = kept[kept.length - 1];
      if (Math.hypot(p[0] - q[0], p[1] - q[1]) >= th) kept.push(p);
    }
    // drop closing duplicate if present
    while (kept.length > 1 && Math.hypot(kept[0][0] - kept.at(-1)[0], kept[0][1] - kept.at(-1)[1]) < th) kept.pop();
    return kept;
  };
  // tiny rings (islands) fall back to finer thresholds so small countries survive
  for (const th of [THRESH, THRESH / 3, 0.01]) {
    const k = run(th);
    if (k.length >= 4) return k;
  }
  return null;
}
function ringPath(pts) {
  let s = `M${fmt(pts[0][0])} ${fmt(pts[0][1])}l`;
  const out = [];
  for (let i = 1; i < pts.length; i++) {
    out.push(fmt(pts[i][0] - pts[i - 1][0]) + " " + fmt(pts[i][1] - pts[i - 1][1]));
  }
  return s + out.join(" ").replace(/ -/g, "-") + "Z";
}
function centroid(pts) {
  let a = 0, cx = 0, cy = 0;
  for (let i = 0; i < pts.length; i++) {
    const [x0, y0] = pts[i], [x1, y1] = pts[(i + 1) % pts.length];
    const c = x0 * y1 - x1 * y0; a += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c;
  }
  a /= 2;
  return a ? [cx / (6 * a), cy / (6 * a)] : pts[0];
}

const gj = JSON.parse(fs.readFileSync(countriesPath, "utf8"));
const byIso = new Map();
const a3ToIso = new Map();
for (const ft of gj.features) {
  const p = ft.properties;
  if (p.ADM0_A3 === "ATA") continue;
  let iso3 = p.ISO_A3_EH;
  if (!iso3 || iso3 === "-99") iso3 = p.ADM0_A3;
  a3ToIso.set(p.ADM0_A3, iso3);
  const polys = ft.geometry.type === "Polygon" ? [ft.geometry.coordinates] : ft.geometry.coordinates;
  let rec = byIso.get(iso3);
  if (!rec) { rec = { iso3, props: p, polys: [] }; byIso.set(iso3, rec); }
  for (const poly of polys) rec.polys.push(poly);
  if (!rec.props) rec.props = p;
}

const countries = [];
for (const rec of byIso.values()) {
  const p = rec.props, iso3 = rec.iso3;
  const name = OVERRIDE[iso3] || p.NAME_LONG || p.NAME;
  const al = new Set();
  for (const k of ["NAME", "NAME_LONG", "NAME_EN", "FORMAL_EN", "ADMIN", "BRK_NAME", "ABBREV", "NAME_SORT"]) {
    const v = p[k]; if (v && v !== name) al.add(v);
  }
  for (const v of EXTRA[iso3] || []) if (v !== name) al.add(v);
  const polyInfo = [];
  const ds = [];
  for (const poly of rec.polys) {
    const rings = poly.map(simplify);
    if (!rings[0]) continue;
    const outer = rings[0];
    polyInfo.push({ outer, area: Math.abs(ringArea([...outer, outer[0]])) });
    for (const r of rings) if (r) ds.push(ringPath(r));
  }
  if (!polyInfo.length) continue;
  const maxA = Math.max(...polyInfo.map((x) => x.area));
  const main = polyInfo.filter((x) => x.area >= 0.2 * maxA);
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const m of main) for (const [x, y] of m.outer) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  const big = polyInfo.find((x) => x.area === maxA);
  const c = centroid(big.outer);
  countries.push({
    iso3, name, aliases: [...al], continent: p.CONTINENT || "",
    d: ds.join(""),
    bbox: [f2(x0), f2(y0), f2(x1), f2(y1)],
    center: [f2(c[0]), f2(c[1])],
    tiny: x1 - x0 < 3 && y1 - y0 < 3,
  });
}
countries.sort((a, b) => a.iso3.localeCompare(b.iso3));
const have = new Set(countries.map((c) => c.iso3));
const missing = REQUIRED.filter((c) => !have.has(c));
if (missing.length) { console.error("MISSING required ISO3:", missing.join(" ")); process.exit(2); }

const source = { id: "natural-earth", label: "Natural Earth", licence: "Public domain", url: "https://www.naturalearthdata.com/",
  files: ["ne_50m_admin_0_countries", "ne_10m_populated_places_simple"], retrievedAt: new Date().toISOString() };
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, "world.json"), JSON.stringify({ source, projection: "Equal Earth", width: 1000, height: HEIGHT, countries }));

const pj = JSON.parse(fs.readFileSync(placesPath, "utf8"));
const places = [];
for (const ft of pj.features) {
  const p = ft.properties;
  const iso3 = a3ToIso.get(p.adm0_a3);
  if (!iso3 || !have.has(iso3)) continue;
  places.push([p.name, p.nameascii, iso3, Math.round(p.pop_max || 0), String(p.featurecla || "").includes("Admin-0 capital") ? 1 : 0]);
}
places.sort((a, b) => b[3] - a[3]);
fs.writeFileSync(path.join(outDir, "places.json"), JSON.stringify({ source, fields: ["name", "ascii", "iso3", "pop", "capital"], places }));
console.log(`threshold=${THRESH} height=${HEIGHT} countries=${countries.length} places=${places.length}`);
console.log("tiny:", countries.filter((c) => c.tiny).map((c) => c.iso3).join(" "));
