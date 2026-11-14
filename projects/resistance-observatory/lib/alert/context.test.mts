// Run: node --test lib/alert/*.test.mts
// Triggering-study context (k540e-study-context.json) against the genome counts,
// the local-prior classification and the email subject line.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { deriveAlerts, type AlertData, type Cell, type Watch } from "./derive.ts";
import { codon540, cutoffFor, enaRuns, genomeContext, genomeSubject, geoScope, localPrior, measurement, type StudyContextFile } from "./context.ts";

const read = (f: string) => JSON.parse(readFileSync(new URL(`../../k540e-data-pack/${f}`, import.meta.url), "utf8"));
const genomes = read("k540e-genomes.json");
const study: StudyContextFile = read("k540e-study-context.json");
const rows: [string, number, number, number][] = genomes.observations.dhps_K540E;
const cells: Cell[] = rows.map(([iso3, year, x, n]) => ({ iso3, year, x, n }));
const data: AlertData = { cells, a581g: genomes.observations.dhps_A581G.map(([iso3, year, x, n]: [string, number, number, number]) => ({ iso3, year, x, n })) };
const watch = (over: Partial<Watch>): Watch => ({ marker: "dhps_K540E", area: "KEN", trigger: "who_band", level: 60, points: 20, minN: 20, ...over });
const cell = (k: string) => study.cells[k];

test("all 222 study-context cells match the genome counts exactly (k and n)", () => {
  assert.equal(Object.keys(study.cells).length, 222);
  assert.equal(rows.length, 222);
  for (const [iso3, year, x, n] of rows) {
    const c = study.cells[`${iso3}:${year}`];
    assert.ok(c, `${iso3}:${year} missing`);
    assert.deepEqual([c.iso3, c.year, c.k, c.n], [iso3, year, x, n], `${iso3}:${year}`);
  }
});

test("KEN:2003 is a single-site sample (Kilifi 44/56); COD:2015 is single-site Kinshasa 8/39", () => {
  const k = cell("KEN:2003");
  assert.equal(k.single_site_warning, true);
  const g = geoScope(k);
  assert.deepEqual([g.kind, g.flag, g.site], ["single_site", "Single-site sample", "Kilifi"]);
  assert.deepEqual(k.admin1, [{ name: "Kilifi", k: 44, n: 56 }]);
  assert.equal(k.studies[0].study_id, "1132-PF-K1000G-DBS-KE-BEJON");
  const c = geoScope(cell("COD:2015"));
  assert.deepEqual([c.kind, c.site, cell("COD:2015").k, cell("COD:2015").n], ["single_site", "Kinshasa", 8, 39]);
});

test("NGA:2020: 10 states sampled, all 3 mutants in Ogun (3/37), 0/167 elsewhere, sWGA-only", () => {
  const n = cell("NGA:2020");
  assert.equal(n.admin1_count, 10);
  assert.deepEqual(n.admin1.filter((a) => a.k > 0), [{ name: "Ogun", k: 3, n: 37 }]);
  const g = geoScope(n);
  assert.deepEqual([g.kind, g.flag, g.site], ["clustered", "Subnational clustering", "Ogun"]);
  assert.match(g.text, /all 3 of 3 .* Ogun \(3\/37\), with 0\/167 across the other 9/);
  assert.equal(n.studies[0].study_id, "1306-PF-NG-NGWA-SM");
  const m = measurement(n);
  assert.equal(m.replicated, false);
  assert.match(m.note!, /sWGA-only/);
});

test("GMB:2014: positives in 2 of 4 studies, replicated across gDNA and sWGA, all in Upper River", () => {
  const g = cell("GMB:2014");
  assert.equal(g.study_count, 4);
  assert.deepEqual(g.studies.filter((s) => s.k > 0).map((s) => s.study_id).sort(), ["1137-PF-GM-DALESSANDRO", "1182-PF-GM-DALESSANDRO-SM"]);
  assert.deepEqual(g.dna_method_mutants, { gDNA: 2, sWGA: 1 });
  const m = measurement(g);
  assert.equal(m.replicated, true);
  assert.match(m.note!, /replicate across gDNA and sWGA/);
  assert.deepEqual([geoScope(g).kind, geoScope(g).site], ["clustered", "Upper River"]);
  // the raw-read links cover both preparations
  assert.deepEqual([...new Set(enaRuns(g).map((r) => r.dna_method))].sort(), ["gDNA", "sWGA"]);
});

test("VNM:2015 surfaces the alternative codon-540 allele (K540N in 28 of 81); none in Kenya", () => {
  const v = cell("VNM:2015");
  assert.equal(v.codon540_breakdown.alt_mutant_540N, 28);
  assert.match(codon540(v).altWarning!, /K540N was called in 28 of 81/);
  assert.match(codon540(cell("VNM:2019")).altWarning!, /K540N was called in 485 of 525 .*92\.4%/);
  assert.equal(codon540(cell("KEN:2003")).altWarning, null);
});

test("local prior: zero for GMB 2014 and NGA 2020; established for KEN 2003 and TZA 2019", () => {
  for (const [iso, y] of [["GMB", 2014], ["NGA", 2020]] as const) {
    const p = localPrior(cells, iso, y);
    assert.equal(p.name, "Zero local prior", iso);
    assert.equal(p.label, "Zero local prior — higher verification bar");
    assert.match(p.steps.join(" "), /raw sequencing reads.*sentinel sampling.*clinical clearance/);
  }
  for (const [iso, y] of [["KEN", 2003], ["TZA", 2019]] as const) {
    const p = localPrior(cells, iso, y);
    assert.equal(p.name, "Established local prior", iso);
    assert.equal(p.label, "Established resistance prior — evaluate against cutoff");
    assert.match(p.steps.join(" "), /TES.*CES/);
  }
});

test("zero-prior first detections still fire: the context never suppresses an early warning", () => {
  for (const area of ["GMB", "NGA"]) {
    const e = deriveAlerts(watch({ area, trigger: "first_detection" }), data).find((x) => x.rule === "first_detection")!;
    assert.equal(e.fired, true);
    const ctx = genomeContext({ e, watch: watch({ area, trigger: "first_detection" }), basis: genomes.countries[area].who_basis, cells, study, country: area, mutation: "K540E" })!;
    assert.equal(ctx.prior.kind, "zero");
    assert.equal(ctx.cutoff.value, null);
  }
});

test("email subject leads with evidence source, study scope and assay", () => {
  const subject = (area: string, over: Partial<Watch>, rule: string) => {
    const w = watch({ area, ...over });
    const e = deriveAlerts(w, data).find((x) => x.rule === rule)!;
    const country = genomes.countries[area].country;
    const ctx = genomeContext({ e, watch: w, basis: genomes.countries[area].who_basis, cells, study, country, mutation: "K540E" })!;
    return genomeSubject({ e, ctx, country, mutation: "K540E", drugShort: "SP" });
  };
  assert.equal(
    subject("KEN", {}, "band_change"),
    "[MalariaGEN Pf8 WGS · 1 study, single-site Kilifi (sWGA/gDNA)] Kenya K540E (SP marker) 78.6% (44/56) — WHO 60% line; confirm via TES/CES",
  );
  assert.equal(
    subject("NGA", { trigger: "first_detection" }, "first_detection"),
    "[MalariaGEN Pf8 WGS · 1 study, 10 Admin-1 areas (3/3 in Ogun, sWGA)] Nigeria first K540E (SP marker) 1.5% (3/204) — Zero-prior early warning",
  );
  assert.match(subject("GMB", { trigger: "first_detection" }, "first_detection"), /^\[MalariaGEN Pf8 WGS · 4 studies, 2 Admin-1 areas \(3\/3 in Upper River, gDNA\/sWGA\)\] Gambia first K540E/);
});

test("cutoff: WHO lines only in East and Southern Africa; elsewhere a labelled project preset", () => {
  assert.deepEqual([cutoffFor({ band: "high", rule: "band_change" }, watch({}), "east_southern_africa").published, cutoffFor({ band: "high", rule: "band_change" }, watch({}), "east_southern_africa").value], [true, 60]);
  assert.equal(cutoffFor({ band: "high", rule: "band_change" }, watch({}), "central_west_africa").published, false);
  assert.equal(cutoffFor({ rule: "level_crossed" }, watch({ trigger: "fall", level: 50 }), "outside_africa").short, "project preset 50%");
});
