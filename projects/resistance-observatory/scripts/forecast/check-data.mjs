// Invariant checks and spot checks for the pinned Forecast data. Run: node scripts/forecast/check-data.mjs
import { readFileSync } from "node:fs";

const load = (p) => JSON.parse(readFileSync(new URL(`../../${p}`, import.meta.url), "utf8"));
const genome = load("data/forecast/genome-k540e.json");
const graph = load("data/forecast/graph-findings.json");
const alerts = load("data/forecast/alerts.placeholder.json");

let failures = 0;
const fail = (msg) => {
  failures += 1;
  console.error("FAIL", msg);
};
const ISO = /^[A-Z]{3}$/;

for (const c of genome.countries) {
  if (!ISO.test(c.iso3)) fail(`bad iso3 ${c.iso3}`);
  let prev = -Infinity;
  for (const y of c.years) {
    if (y.year <= prev) fail(`${c.iso3} years not ascending/unique at ${y.year}`);
    prev = y.year;
    if (y.tested !== y.kOnly + y.eOnly + y.mixedWithE + y.other) fail(`${c.iso3} ${y.year} tested sum`);
    if (y.withE !== y.eOnly + y.mixedWithE) fail(`${c.iso3} ${y.year} withE sum`);
    if (y.tested + y.missing === 0) fail(`${c.iso3} ${y.year} empty year row`);
  }
}
const allYears = genome.countries.flatMap((c) => c.years.map((y) => y.year));
if (Math.min(...allYears) !== genome.minYear || Math.max(...allYears) !== genome.maxYear) fail("min/max year");

for (const f of graph.findings) {
  if (!f.systemId) fail("finding without systemId");
  if (!f.pubmedId && !f.doi) fail(`${f.systemId} has neither pubmedId nor doi`);
  if (f.kind !== "haplotype" && !f.countries?.length) fail(`${f.systemId} has no countries`);
  if (f.kind === "haplotype" && f.countries?.length) fail(`${f.systemId} haplotype finding unexpectedly names a country`);
  for (const c of f.countries ?? []) if (!ISO.test(c.iso3)) fail(`${f.systemId} bad iso3 ${c.iso3}`);
  if (!["sp", "codon540", "haplotype"].includes(f.kind)) fail(`${f.systemId} bad kind`);
}
if (!Array.isArray(alerts) || alerts.length !== 2) fail("placeholder alerts must be an array of 2");

const row = (iso, year) => {
  const y = genome.countries.find((c) => c.iso3 === iso)?.years.find((r) => r.year === year);
  return y ? `${y.withE}/${y.tested}` : "not sampled";
};
console.log("Spot checks (withE/tested):");
console.log("  NGA 2020", row("NGA", 2020), "(expected 3/204)");
console.log(
  "  NGA 2008-2019",
  [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019].map((y) => `${y}:${row("NGA", y)}`).join(" "),
  "(expected withE 0; tested 10,1,4,24,96,20,29 in sampled years)",
);
console.log("  GMB 2014", row("GMB", 2014), "(expected 3/302); GMB 2013", row("GMB", 2013), "(expected 0/49)");
console.log("  KEN 1994", row("KEN", 1994), "(expected 16/53); KEN 2019", row("KEN", 2019), "(expected 236/243)");
console.log("  countries", genome.countries.length, "years", genome.minYear, "-", genome.maxYear);
const sum = genome.countries.reduce((s, c) => s + c.years.reduce((t, y) => t + y.tested + y.missing, 0), 0);
console.log("  sum(tested+missing)", sum, "(expected 24409)");
if (sum !== 24409) fail("tested+missing sum");
console.log("Graph totals", JSON.stringify(graph.totals));
console.log(
  "  findings",
  graph.findings.length,
  "| sp",
  graph.findings.filter((f) => f.kind === "sp").length,
  "| codon540",
  graph.findings.filter((f) => f.kind === "codon540").length,
  "| with OpenAlex date",
  graph.findings.filter((f) => f.paper.publishedDate).length,
);
// Paper spot-check join
const STATUSES = ["supported", "partly_supported", "contradicted", "not_verifiable"];
const verification = load("data/forecast/graph-verification.json");

// (a) Shape guard: graph-verification.json is imported read-only by other tabs (lib/findings.ts).
if (typeof verification.checkedBy !== "string" || !verification.checkedBy.trim()) fail("graph-verification.json: checkedBy must be a non-empty string");
if (!Array.isArray(verification.records)) fail("graph-verification.json: records must be an array");
for (const [i, r] of (Array.isArray(verification.records) ? verification.records : []).entries()) {
  if (typeof r?.systemId !== "string" || !r.systemId) fail(`graph-verification.json records[${i}]: systemId must be a string`);
  if (!STATUSES.includes(r?.status)) fail(`graph-verification.json records[${i}] (${r?.systemId}): status ${JSON.stringify(r?.status)} not allowed`);
  for (const k of ["where", "note"]) {
    if (!(r?.[k] === null || typeof r?.[k] === "string")) fail(`graph-verification.json records[${i}] (${r?.systemId}): ${k} must be a string or null`);
  }
}

// (b) Drift guard: the ids hidden in the app (parsed from the MIS_EXTRACTED_IDS line in lib/forecast/data.ts)
// must equal the team list (data/graph-stats.json, marker.associations with vetted === false).
const dataTs = readFileSync(new URL("../../lib/forecast/data.ts", import.meta.url), "utf8");
const misLine = dataTs.split("\n").find((l) => /export const MIS_EXTRACTED_IDS\b/.test(l)) ?? "";
const hiddenIds = new Set([...misLine.matchAll(/"([^"]+)"/g)].map((m) => m[1]));
if (!misLine) fail("could not find the MIS_EXTRACTED_IDS line in lib/forecast/data.ts");
const teamStats = load("data/graph-stats.json");
const teamIds = new Set((teamStats?.marker?.associations ?? []).filter((a) => a.vetted === false).map((a) => a.system_id));
const onlyApp = [...hiddenIds].filter((x) => !teamIds.has(x));
const onlyTeam = [...teamIds].filter((x) => !hiddenIds.has(x));
if (onlyApp.length || onlyTeam.length)
  fail(`MIS_EXTRACTED_IDS drifted from data/graph-stats.json (vetted: false). Only in data.ts: [${onlyApp}]. Only in graph-stats.json: [${onlyTeam}]`);
console.log("Hidden in the app (MIS_EXTRACTED_IDS)", [...hiddenIds].join(", "), "| matches data/graph-stats.json vetted:false:", !(onlyApp.length || onlyTeam.length));
const shown = graph.findings.filter((f) => !hiddenIds.has(f.systemId)); // what lib/forecast/data.ts exposes as GRAPH.findings
const recon = load("data/forecast/raw/graph/sp_findings.json");
const reconIds = new Set(recon.map((r) => r.system_id));
const pinnedIds = new Set(graph.findings.map((f) => f.systemId));
const byId = new Map();
for (const r of verification.records ?? []) {
  if (!STATUSES.includes(r.status)) fail(`verification ${r.systemId} bad status ${r.status}`);
  if (!reconIds.has(r.systemId) && !pinnedIds.has(r.systemId)) fail(`verification ${r.systemId} matches no recon record or finding`);
  if (byId.has(r.systemId)) fail(`verification ${r.systemId} duplicated`);
  byId.set(r.systemId, r);
}
const notDisplayed = (verification.records ?? []).filter((r) => !pinnedIds.has(r.systemId)).map((r) => r.systemId);
const vc = { supported: 0, partly_supported: 0, contradicted: 0, not_verifiable: 0, unchecked: 0 };
const countryFindings = shown.filter((f) => f.countries.length > 0);
for (const f of countryFindings) vc[byId.get(f.systemId)?.status ?? "unchecked"] += 1;
console.log("Verification records", (verification.records ?? []).length, "| not among displayed findings:", notDisplayed.length ? notDisplayed.join(", ") : "none");
console.log(
  "Displayed country-naming findings", countryFindings.length,
  "| sp", countryFindings.filter((f) => f.kind === "sp").length,
  "| codon540", countryFindings.filter((f) => f.kind === "codon540").length,
  "| vetted", countryFindings.filter((f) => f.inVettedCsv === true).length,
  "| API only", countryFindings.filter((f) => f.inVettedCsv === false).length,
);
console.log("Verification over displayed country-naming findings", JSON.stringify(vc));
console.log("Global haplotype findings (shown in every panel as not country-specific):");
for (const f of shown.filter((x) => x.kind === "haplotype"))
  console.log(`  ${f.systemId} | paper ${f.paper.year} | PMID ${f.pubmedId} | vetted ${f.inVettedCsv} | status ${byId.get(f.systemId)?.status ?? "unchecked"} | ${f.paper.title}`);

// Papers layer
const papers = load("data/forecast/papers.json");
if (papers.papers.length !== 372) fail(`papers: expected 372, got ${papers.papers.length}`);
if (papers.total !== papers.papers.length) fail("papers.total mismatch");
if (papers.readByGraph !== papers.papers.filter((p) => p.readByGraph).length) fail("papers.readByGraph mismatch");
const pmids = new Set();
for (const p of papers.papers) {
  if (!/^\d+$/.test(p.pmid)) fail(`paper bad pmid ${p.pmid}`);
  if (pmids.has(p.pmid)) fail(`paper duplicate pmid ${p.pmid}`);
  pmids.add(p.pmid);
  if (!Number.isInteger(p.year)) fail(`paper ${p.pmid} without year`);
  if (p.month !== null && !(Number.isInteger(p.month) && p.month >= 1 && p.month <= 12)) fail(`paper ${p.pmid} bad month`);
  if (!p.title || !p.url) fail(`paper ${p.pmid} without title or url`);
  for (const c of p.countries) if (!ISO.test(c)) fail(`paper ${p.pmid} bad iso3 ${c}`);
}
const pc = {};
for (const p of papers.papers) for (const c of new Set(p.countries)) {
  pc[c] ??= { n: 0, first: Infinity };
  pc[c].n += 1;
  pc[c].first = Math.min(pc[c].first, p.year);
}
const yrs = papers.papers.map((p) => p.year);
console.log(
  "Papers",
  papers.total,
  "| readByGraph",
  papers.readByGraph,
  "| with >=1 country",
  papers.papers.filter((p) => p.countries.length).length,
  "| years",
  Math.min(...yrs),
  "-",
  Math.max(...yrs),
  "| month missing",
  papers.papers.filter((p) => p.month === null).length,
);
console.log(
  "  top countries",
  Object.entries(pc)
    .sort((a, b) => b[1].n - a[1].n || a[0].localeCompare(b[0]))
    .slice(0, 8)
    .map(([c, v]) => `${c}:${v.n}`)
    .join(" "),
);
for (const c of ["NGA", "KEN", "GMB"]) console.log(`  ${c}`, pc[c] ? `${pc[c].n} papers, earliest ${pc[c].first}` : "no papers");

// Vetted-release membership
const vetted = load("data/forecast/graph-vetted.json");
console.log("Vetted source:", vetted.source, "| file", vetted.file, "| checksum", vetted.checksum, "| checkedAt", vetted.checkedAt);
for (const [id, v] of Object.entries(vetted.ids)) {
  if (typeof v !== "boolean") fail(`vetted ${id} not boolean`);
  if (!reconIds.has(id)) fail(`vetted ${id} not among the pulled records`);
}
for (const f of graph.findings) {
  if (f.inVettedCsv !== (vetted.ids[f.systemId] ?? null)) fail(`${f.systemId} inVettedCsv disagrees with graph-vetted.json`);
}
const label = (v) => (v === true ? "vetted" : v === false ? "apiOnly" : "unknown");
const xt = {};
for (const f of countryFindings) {
  const k = `${f.kind} ${label(f.inVettedCsv)}`;
  xt[k] ??= { supported: 0, partly_supported: 0, contradicted: 0, not_verifiable: 0, unchecked: 0, total: 0 };
  xt[k][byId.get(f.systemId)?.status ?? "unchecked"] += 1;
  xt[k].total += 1;
}
console.log("Vetted x spot-check over displayed country-naming findings:");
for (const k of Object.keys(xt).sort()) console.log(`  ${k.padEnd(18)}`, JSON.stringify(xt[k]));
for (const c of ["NGA", "KEN", "GMB"]) {
  const sp = shown.filter((f) => f.kind === "sp" && f.countries.some((x) => x.iso3 === c));
  console.log(`  ${c} SP findings`, sp.length, "| vetted", sp.filter((f) => f.inVettedCsv === true).length, "| API only", sp.filter((f) => f.inVettedCsv === false).length);
}

// Policy milestones (verbatim from the Alert tab pack)
const policy = load("data/forecast/policy-milestones.json");
for (const m of policy.items) {
  if (!Number.isInteger(m.year) || !m.text || !/^https:\/\//.test(m.url)) fail(`policy milestone bad item ${JSON.stringify(m)}`);
}
console.log("Policy milestones", policy.items.map((m) => m.year).join(", "));

// Year ranges (two clocks)
const gpy = graph.findings.map((f) => f.paper.year).filter((y) => y !== null);
const all = [genome.minYear, genome.maxYear, ...papers.papers.map((p) => p.year), ...gpy];
console.log(
  "Year ranges: genome (collection)", genome.minYear, "-", genome.maxYear,
  "| papers (publication)", Math.min(...yrs), "-", Math.max(...yrs),
  "| Graph papers (publication)", Math.min(...gpy), "-", Math.max(...gpy),
  "| MIN_YEAR/MAX_YEAR", Math.min(...all), "-", Math.max(...all),
  "| papers after genome max", papers.papers.filter((p) => p.year > genome.maxYear).length,
);

console.log(failures ? `${failures} FAILURE(S)` : "All invariants hold.");
process.exit(failures ? 1 : 0);
