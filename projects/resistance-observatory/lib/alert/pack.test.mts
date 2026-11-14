// Run: node --test lib/alert/
// Checks the derivation against the real data pack (k540e-data-pack/).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildMapAlerts } from "./generate-map-alerts.mts";
import { bandCells, deriveAlerts, type AlertData, type Cell, type Watch } from "./derive.ts";

const read = (f: string) => JSON.parse(readFileSync(new URL(`../../k540e-data-pack/${f}`, import.meta.url), "utf8"));
const genomes = read("k540e-genomes.json");
const lit = read("k540e-literature.json");
const graph = read("k540e-graph.json");

const cells = (key: string): Cell[] => genomes.observations[key].map(([iso3, year, x, n]: [string, number, number, number]) => ({ iso3, year, x, n }));
const data: AlertData = { cells: cells("dhps_K540E"), a581g: cells("dhps_A581G") };
const watch = (over: Partial<Watch>): Watch => ({ marker: "dhps_K540E", area: "KEN", trigger: "who_band", level: 60, points: 20, minN: 20, ...over });
const basis = (iso: string) => genomes.countries[iso].who_basis;

test("222 country-year cells in 33 countries; 149 with at least 20 samples, in 29 countries", () => {
  assert.equal(data.cells.length, 222);
  assert.equal(new Set(data.cells.map((c) => c.iso3)).size, 33);
  const q = data.cells.filter((c) => c.n >= 20);
  assert.equal(q.length, 149);
  assert.equal(new Set(q.map((c) => c.iso3)).size, 29);
});

test("East and Southern Africa, n>=20: 33 cells = 5 low, 1 medium, 24 high, 3 very high (TZA 2010, 2013, 2014)", () => {
  const esa = bandCells(data, 20).filter((b) => basis(b.cell.iso3) === "east_southern_africa");
  assert.equal(esa.length, 33);
  const count = (band: string) => esa.filter((b) => b.band === band).length;
  assert.deepEqual([count("low"), count("medium"), count("high"), count("very_high")], [5, 1, 24, 3]);
  assert.deepEqual(
    esa.filter((b) => b.band === "very_high").map((b) => `${b.cell.iso3} ${b.cell.year}`).sort(),
    ["TZA 2010", "TZA 2013", "TZA 2014"],
  );
  const tz19 = esa.find((b) => b.cell.iso3 === "TZA" && b.cell.year === 2019)!;
  assert.equal(tz19.band, "high");
  assert.deepEqual([tz19.cell.x, tz19.cell.n, tz19.a581g?.x, tz19.a581g?.n], [388, 432, 5, 431]);
});

test("Kenya: 24/64 in 1998 then 44/56 in 2003, low straight to high; 118/123 in 2014", () => {
  const ev = deriveAlerts(watch({}), data);
  const change = ev.find((e) => e.rule === "band_change")!;
  assert.deepEqual([change.year, change.prevBand, change.band], [2003, "low", "high"]);
  assert.deepEqual([change.prev?.year, change.prev?.x, change.prev?.n, change.cell?.x, change.cell?.n], [1998, 24, 64, 44, 56]);
  const k14 = data.cells.find((c) => c.iso3 === "KEN" && c.year === 2014)!;
  assert.deepEqual([k14.x, k14.n], [118, 123]);
});

test("Tanzania: the very-high combination lapses in 2019", () => {
  const ev = deriveAlerts(watch({ area: "TZA", trigger: "very_high_combo" }), data);
  assert.equal(ev.find((e) => e.rule === "combo_lapsed")?.year, 2019);
  assert.deepEqual(ev.filter((e) => e.band === "very_high").map((e) => e.year), [2010, 2013, 2014]);
});

test("DRC 2012 and 2022; Vietnam 2012 and 2019", () => {
  const at = (iso: string, y: number) => {
    const c = data.cells.find((k) => k.iso3 === iso && k.year === y)!;
    return [c.x, c.n];
  };
  assert.deepEqual(at("COD", 2012), [17, 173]);
  assert.deepEqual(at("COD", 2022), [195, 662]);
  assert.deepEqual(at("VNM", 2012), [93, 130]);
  assert.deepEqual(at("VNM", 2019), [14, 525]);
});

test("first detections: Gambia 2014 (3/302 after 0/49), Nigeria 2020 (3/204 after 0/29)", () => {
  const g = deriveAlerts(watch({ area: "GMB", trigger: "first_detection" }), data).find((e) => e.rule === "first_detection")!;
  assert.deepEqual([g.year, g.cell?.x, g.cell?.n, g.priorNegative?.lastTested], [2014, 3, 302, 49]);
  const n = deriveAlerts(watch({ area: "NGA", trigger: "first_detection" }), data).find((e) => e.rule === "first_detection")!;
  assert.deepEqual([n.year, n.cell?.x, n.cell?.n, n.priorNegative?.lastTested], [2020, 3, 204, 29]);
});

test("papers: 372, 10 in the graph; 55 abstract figures from 49 papers in 25 countries", () => {
  assert.equal(lit.papers.length, 372);
  assert.equal(lit.papers.filter((p: { in_graph: boolean }) => p.in_graph).length, 10);
  assert.equal(lit.abstract_prevalence.length, 55);
  assert.equal(new Set(lit.abstract_prevalence.map((f: { pmid: string }) => f.pmid)).size, 49);
  assert.equal(new Set(lit.abstract_prevalence.map((f: { iso3: string }) => f.iso3)).size, 25);
});

test("graph: 3 haplotype findings, 22 SP findings, 21 paper findings all vetted, 4,912 vetted ids", () => {
  assert.equal(graph.haplotype_findings.length, 3);
  assert.equal(graph.stakes_sp.length, 22);
  // PEyo2A8Ol0 reversed its trial arms (DP vs SP): vetted id, excluded after checking the paper
  assert.equal(graph.stakes_sp.some((f: { system_id: string }) => f.system_id === "PEyo2A8Ol0"), false);
  assert.deepEqual(graph.stakes_sp.filter((f: { source_checked?: boolean }) => f.source_checked).map((f: { system_id: string }) => f.system_id).sort(), ["6gHNBtEMhm", "FeOFp8SnEy", "Q9e3_2VwzW"]);
  assert.equal(graph.findings_from_k540e_papers.length, 21);
  const vetted = new Set(graph.vetted_association_ids);
  assert.equal(vetted.size, 4912);
  for (const f of [...graph.haplotype_findings, ...graph.stakes_sp, ...graph.findings_from_k540e_papers]) assert.ok(vetted.has(f.system_id), f.system_id);
});

test("data/alerts.json (Forecast map contract) matches a fresh derivation from the pack", () => {
  const onDisk = JSON.parse(readFileSync(new URL("../../data/alerts.json", import.meta.url), "utf8"));
  const fresh = buildMapAlerts();
  assert.deepEqual(onDisk, fresh);
  assert.ok(fresh.length > 0);
  for (const a of fresh) {
    assert.deepEqual(Object.keys(a), ["id", "marker_id", "country_iso3", "year", "rule", "headline"]);
    assert.equal(a.marker_id, "pfdhps-K540E");
  }
  assert.ok(fresh.some((a) => a.id === "k540e-KEN-2003-band_change"));
  assert.equal(new Set(fresh.map((a) => a.id)).size, fresh.length);
});

test("the quarantine example ids are not in the vetted set", () => {
  const vetted = new Set(graph.vetted_association_ids);
  assert.equal(vetted.has("paFNq6MPX5"), false);
  assert.equal(vetted.has("AeI-laBxXr"), false);
});
