// Run: node --test lib/alert/
// Fixture counts are the check figures from the project brief (MalariaGEN
// genome counts); zero-positive "earlier" cells are the ones the brief names.
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  bandOf,
  deriveAlerts,
  firedCount,
  visibleAt,
  wilson,
  type AlertData,
  type Cell,
  type Watch,
} from "./derive.ts";

const c = (iso3: string, year: number, x: number, n: number): Cell => ({ iso3, year, x, n });

const data: AlertData = {
  cells: [
    c("KEN", 1998, 24, 64),
    c("KEN", 2001, 9, 12), // under the minimum: must be skipped, not compared
    c("KEN", 2003, 44, 56),
    c("KEN", 2014, 118, 123),
    c("TZA", 2010, 80, 100),
    c("TZA", 2019, 388, 432),
    c("COD", 2012, 17, 173),
    c("COD", 2022, 195, 662),
    c("VNM", 2012, 93, 130),
    c("VNM", 2019, 14, 525),
    c("GMB", 2013, 0, 49),
    c("GMB", 2014, 3, 302),
    c("NGA", 2019, 0, 29),
    c("NGA", 2020, 3, 204),
    c("XXA", 2000, 5, 50), // first record already positive
    c("XXB", 2000, 0, 40),
    c("XXB", 2001, 1, 8), // single positive, tiny sample
  ],
  a581g: [c("TZA", 2010, 13, 100), c("TZA", 2019, 5, 431)],
};

const watch = (over: Partial<Watch>): Watch => ({
  marker: "pfdhps-K540E",
  area: "KEN",
  trigger: "who_band",
  level: 60,
  points: 20,
  minN: 20,
  ...over,
});

test("wilson interval matches a known value", () => {
  const w = wilson(7, 93); // 7.5%, published interval about 3.1 to 14.9 (exact); Wilson is close
  assert.ok(w.lo > 3 && w.lo < 4.2, String(w.lo));
  assert.ok(w.hi > 14 && w.hi < 15.5, String(w.hi));
  assert.deepEqual(wilson(0, 0), { lo: 0, hi: 100 });
  assert.equal(wilson(0, 49).lo, 0);
});

test("WHO bands", () => {
  assert.equal(bandOf(37.5, null), "low");
  assert.equal(bandOf(40, null), "medium");
  assert.equal(bandOf(59.9, 50), "medium");
  assert.equal(bandOf(60, null), "high");
  assert.equal(bandOf(89.8, 1.2), "high");
  assert.equal(bandOf(80, 5), "very_high");
});

test("Kenya: low in 1998 straight to high in 2003, skipping the under-minimum cell", () => {
  const ev = deriveAlerts(watch({}), data);
  assert.deepEqual(ev.map((e) => [e.year, e.rule]), [
    [1998, "baseline"],
    [2003, "band_change"],
  ]);
  const change = ev[1];
  assert.equal(change.prevBand, "low");
  assert.equal(change.band, "high");
  assert.equal(change.prev?.year, 1998);
  assert.equal(change.yearsApart, 5);
  assert.equal(change.cell?.pct.toFixed(1), "78.6");
  assert.equal(change.prev?.pct.toFixed(1), "37.5");
  assert.equal(change.a581gUnjudged, true); // A581G untested: cannot be called very high
  assert.equal(firedCount(ev), 1);
});

test("Tanzania: very high in 2010, high (not very high) in 2019 when A581G is 1.2%", () => {
  const ev = deriveAlerts(watch({ area: "TZA", trigger: "very_high_combo" }), data);
  assert.deepEqual(ev.map((e) => [e.year, e.rule, e.band]), [
    [2010, "baseline", "very_high"],
    [2019, "combo_lapsed", "high"],
  ]);
  assert.equal(ev[1].cell?.pct.toFixed(1), "89.8");
  assert.equal(ev[1].a581g?.pct.toFixed(1), "1.2");
  const bands = deriveAlerts(watch({ area: "TZA" }), data);
  assert.equal(bands[1].rule, "band_change");
  assert.equal(bands[1].direction, "down");
});

test("DRC: change of 19.6 points fires at 15 but not at 20", () => {
  const at15 = deriveAlerts(watch({ area: "COD", trigger: "change", points: 15 }), data);
  assert.equal(firedCount(at15), 1);
  const e = at15.find((x) => x.fired)!;
  assert.equal(e.delta?.toFixed(1), "19.6");
  assert.equal(e.yearsApart, 10);
  assert.equal(e.strength, "strong");
  assert.equal(firedCount(deriveAlerts(watch({ area: "COD", trigger: "change", points: 20 }), data)), 0);
});

test("DRC: rising to 25% is a strong signal; to 29% only a signal", () => {
  const strong = deriveAlerts(watch({ area: "COD", trigger: "rise", level: 25 }), data).find((e) => e.fired)!;
  assert.equal(strong.rule, "level_crossed");
  assert.equal(strong.strength, "strong");
  const weak = deriveAlerts(watch({ area: "COD", trigger: "rise", level: 29 }), data).find((e) => e.fired)!;
  assert.equal(weak.strength, "signal");
});

test("Vietnam: falls below 10% in 2019, strong", () => {
  const ev = deriveAlerts(watch({ area: "VNM", trigger: "fall", level: 10 }), data);
  assert.deepEqual(ev.map((e) => [e.year, e.rule, e.fired]), [
    [2012, "baseline", false],
    [2019, "level_crossed", true],
  ]);
  assert.equal(ev[1].strength, "strong");
  assert.equal(ev[1].cell?.pct.toFixed(1), "2.7");
});

test("a record that opens already beyond the level is a baseline, later cells are quiet", () => {
  const ev = deriveAlerts(watch({ area: "KEN", trigger: "rise", level: 30 }), data);
  assert.deepEqual(ev.map((e) => e.rule), ["baseline", "still_beyond", "still_beyond"]);
  assert.equal(firedCount(ev), 0);
});

test("first detection: Gambia 2014 and Nigeria 2020", () => {
  const gmb = deriveAlerts(watch({ area: "GMB", trigger: "first_detection" }), data);
  assert.equal(gmb.length, 1);
  assert.equal(gmb[0].rule, "first_detection");
  assert.equal(gmb[0].strength, "signal");
  assert.deepEqual(gmb[0].priorNegative, { cells: 1, tested: 49, lastYear: 2013, lastTested: 49 });
  const nga = deriveAlerts(watch({ area: "NGA", trigger: "first_detection" }), data);
  assert.equal(nga[0].year, 2020);
  assert.equal(nga[0].priorNegative?.lastTested, 29);
});

test("first detection: positive first record is a baseline; single positive is weak and labelled under-minimum", () => {
  const a = deriveAlerts(watch({ area: "XXA", trigger: "first_detection" }), data);
  assert.equal(a[0].rule, "baseline");
  assert.equal(a[0].fired, false);
  const b = deriveAlerts(watch({ area: "XXB", trigger: "first_detection" }), data);
  assert.equal(b[0].rule, "first_detection");
  assert.equal(b[0].strength, "weak");
  assert.equal(b[0].belowMinN, true);
});

test("a country with no cells yields no genome events: missing is not zero", () => {
  assert.deepEqual(deriveAlerts(watch({ area: "ZZZ", trigger: "first_detection" }), data), []);
  assert.deepEqual(deriveAlerts(watch({ area: "ZZZ" }), data), []);
});

test("papers and graph join by publication year, matched to the country, never pooled", () => {
  const d: AlertData = {
    ...data,
    firstReports: [{ pmid: "1", pubYear: 2015, iso3: "COD", quote: "q1" }],
    figures: [
      { pmid: "2", pubYear: 2009, iso3: "COD", pct: 4, quote: "q2" },
      { pmid: "3", pubYear: 2018, iso3: "COD", pct: 30, quote: "q3" },
      { pmid: "4", pubYear: 2019, iso3: "COD", pct: 3, quote: "q4" },
      { pmid: "5", pubYear: 2019, iso3: "KEN", pct: 90, quote: "q5" },
    ],
    associations: [
      { pmid: "6", pubYear: 2011, iso3s: ["COD", "UGA"], quote: "q6" },
      { pmid: "7", pubYear: 2012, iso3s: ["KEN"], quote: "q7" },
    ],
    graphFindings: [
      { id: "A", pubYear: 2013, iso3: "TZA", sourceChecked: true },
      { id: "B", pubYear: 2016, iso3: null, sourceChecked: false },
    ],
    graphPapers: [{ pmid: "1", pubYear: 2015, iso3s: ["COD"] }],
  };
  const ev = deriveAlerts(watch({ area: "COD", trigger: "rise", level: 25 }), d);
  const papers = ev.filter((e) => e.source === "papers");
  assert.deepEqual(
    papers.map((e) => [e.year, e.rule, e.fired, e.quote]),
    [
      [2009, "abstract_figure", true, "q2"], // first figure for the country
      [2011, "abstract_association", true, "q6"],
      [2015, "first_report_claim", true, "q1"],
      [2018, "abstract_figure", true, "q3"], // beyond the level
      [2019, "abstract_figure", false, "q4"],
    ],
  );
  const graph = ev.filter((e) => e.source === "graph");
  assert.deepEqual(graph.map((e) => [e.rule, e.graphFindingId ?? e.pmid, e.noCountryGiven]), [
    ["graph_paper", "1", false],
    ["graph_finding", "B", true],
  ]);
  // genome cells carry counts; paper figures never alter them
  assert.equal(ev.find((e) => e.source === "genomes" && e.fired)?.cell?.x, 195);
  // replay
  assert.ok(visibleAt(ev, 2012).every((e) => e.year <= 2012));
  assert.equal(visibleAt(ev, 2008).length, 0);
});
