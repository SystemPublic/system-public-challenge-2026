/**
 * Alert derivation: one pure function from a watch and the data to a list of
 * dated events. The live counter, the feed and the replay all read from it.
 *
 * This file is deliberately self-contained (no local imports) so the unit
 * tests can run it directly with `node --test`, no test library needed.
 *
 * Three kinds of evidence stay separate end to end:
 *   - genomes: country x collection-year counts, dated by COLLECTION year
 *   - papers:  machine-read abstract items, dated by PUBLICATION year
 *   - graph:   System Public Graph findings and in-graph papers, PUBLICATION year
 * Nothing here pools one with another.
 *
 * Percentages are on a 0-100 scale throughout.
 */

/* ------------------------------------------------------------- inputs --- */

export type MarkerKey = string;

export type WhoBasis =
  | "east_southern_africa"
  | "central_west_africa"
  | "outside_africa";

/** One country x collection-year cell: `x` of `n` sampled parasites carried it. */
export type Cell = { iso3: string; year: number; x: number; n: number };

export type Trigger =
  | "who_band"
  | "rise"
  | "fall"
  | "change"
  | "first_detection"
  | "very_high_combo";

export type Watch = {
  marker: MarkerKey;
  /** ISO3 country code. */
  area: string;
  trigger: Trigger;
  /** Percent level for `rise` / `fall`. */
  level: number;
  /** Percentage points for `change`. */
  points: number;
  /** Minimum samples in a cell for it to count. */
  minN: number;
};

export type AbstractFigure = {
  pmid: string;
  pubYear: number;
  iso3: string;
  /** Percent as stated in the abstract; null when the quote has no single figure. */
  pct: number | null;
  quote: string;
};

export type AbstractAssociation = {
  pmid: string;
  pubYear: number;
  /** Countries of the paper; empty when none is given. */
  iso3s: string[];
  quote: string;
};

export type FirstReportClaim = {
  pmid: string;
  pubYear: number;
  iso3: string;
  quote: string;
};

export type GraphFindingRef = {
  id: string;
  pubYear: number;
  iso3: string | null;
  sourceChecked: boolean;
};

export type GraphPaperRef = {
  pmid: string;
  pubYear: number;
  iso3s: string[];
};

export type AlertData = {
  /** Marker cells, any order, any country. */
  cells: Cell[];
  /** Companion A581G cells, read alongside for the WHO "very high" band. */
  a581g: Cell[];
  figures?: AbstractFigure[];
  associations?: AbstractAssociation[];
  firstReports?: FirstReportClaim[];
  graphFindings?: GraphFindingRef[];
  graphPapers?: GraphPaperRef[];
};

/* ------------------------------------------------------------ outputs --- */

/** The three kinds of change the challenge brief names. */
export type ChangeKind = "prevalence_shift" | "new_signal" | "association";

export type Band = "low" | "medium" | "high" | "very_high";

export type Rule =
  | "baseline"
  | "band_change"
  | "level_crossed"
  | "still_beyond"
  | "level_returned"
  | "change"
  | "first_detection"
  | "combo_reached"
  | "combo_holds"
  | "combo_lapsed"
  | "first_report_claim"
  | "abstract_figure"
  | "abstract_association"
  | "graph_finding"
  | "graph_paper";

export type Interval = { lo: number; hi: number };

export type CellStat = Cell & { pct: number; ci: Interval };

export type AlertEvent = {
  id: string;
  kind: ChangeKind;
  rule: Rule;
  source: "genomes" | "papers" | "graph";
  year: number;
  dateBasis: "collection" | "publication";
  /** True when this counts as the watch firing; false for quiet context entries. */
  fired: boolean;
  strength: "strong" | "signal" | "weak" | null;
  iso3: string | null;
  /** Genome events: the cell and the cell it was compared with. */
  cell?: CellStat;
  prev?: CellStat;
  yearsApart?: number;
  band?: Band;
  prevBand?: Band;
  /** A581G in the same cell, when it was tested. */
  a581g?: CellStat;
  /** True when A581G was missing or under the minimum, so "very high" could not be judged. */
  a581gUnjudged?: boolean;
  direction?: "up" | "down";
  /** Percentage-point difference from `prev`. */
  delta?: number;
  /** The level or point threshold this event was judged against. */
  threshold?: number;
  /** First detection: cells that tested and found none before this one. */
  priorNegative?: { cells: number; tested: number; lastYear: number; lastTested: number };
  belowMinN?: boolean;
  /** Paper and graph events. */
  pmid?: string;
  quote?: string;
  statedPct?: number | null;
  graphFindingId?: string;
  sourceChecked?: boolean;
  /** Paper/graph item with no country given: shown as context, never as a match. */
  noCountryGiven?: boolean;
};

/* ------------------------------------------------------------ helpers --- */

/** Wilson score interval, 95%, in percent. */
export function wilson(x: number, n: number): Interval {
  if (n <= 0) return { lo: 0, hi: 100 };
  const z = 1.959963984540054;
  const p = x / n;
  const z2 = z * z;
  const denom = 1 + z2 / n;
  const centre = (p + z2 / (2 * n)) / denom;
  const half = (z * Math.sqrt((p * (1 - p)) / n + z2 / (4 * n * n))) / denom;
  return {
    lo: x === 0 ? 0 : Math.max(0, (centre - half) * 100),
    hi: x === n ? 100 : Math.min(100, (centre + half) * 100),
  };
}

export function stat(c: Cell): CellStat {
  return { ...c, pct: c.n > 0 ? (c.x / c.n) * 100 : 0, ci: wilson(c.x, c.n) };
}

export const WHO_BAND_LINES = { medium: 40, high: 60, a581g: 5 } as const;

/**
 * WHO band for a marker cell. `a581gPct` is the A581G percentage in the same
 * country-year, or null when it was not tested (or not tested enough): the
 * band then stops at "high", because untested is not zero and not five.
 */
export function bandOf(pct: number, a581gPct: number | null): Band {
  if (pct < WHO_BAND_LINES.medium) return "low";
  if (pct < WHO_BAND_LINES.high) return "medium";
  if (a581gPct !== null && a581gPct >= WHO_BAND_LINES.a581g) return "very_high";
  return "high";
}

const BAND_RANK: Record<Band, number> = { low: 0, medium: 1, high: 2, very_high: 3 };

function byYear<T extends { year: number }>(a: T, b: T) {
  return a.year - b.year;
}

/** Cells for one country, with data only (n > 0), in collection-year order. */
export function countryCells(cells: Cell[], iso3: string): CellStat[] {
  return cells
    .filter((c) => c.iso3 === iso3 && c.n > 0)
    .sort(byYear)
    .map(stat);
}

type Banded = { cell: CellStat; band: Band; a581g?: CellStat; a581gUnjudged: boolean };

function banded(cell: CellStat, a581g: Cell[], minN: number): Banded {
  const raw = a581g.find((c) => c.iso3 === cell.iso3 && c.year === cell.year && c.n > 0);
  const companion = raw ? stat(raw) : undefined;
  const judged = companion && companion.n >= minN ? companion.pct : null;
  const band = bandOf(cell.pct, judged);
  return {
    cell,
    band,
    a581g: companion,
    a581gUnjudged: cell.pct >= WHO_BAND_LINES.high && judged === null,
  };
}

/** Band of every qualifying cell, any country. Used for the summary counters. */
export function bandCells(data: Pick<AlertData, "cells" | "a581g">, minN: number): Banded[] {
  return data.cells
    .filter((c) => c.n >= minN)
    .map((c) => banded(stat(c), data.a581g, minN));
}

/* --------------------------------------------------------- derivation --- */

function genomeEvents(watch: Watch, data: AlertData): AlertEvent[] {
  const all = countryCells(data.cells, watch.area);
  const qual = all.filter((c) => c.n >= watch.minN);
  const out: AlertEvent[] = [];
  const base = (c: CellStat, rule: Rule) => ({
    id: `g:${watch.area}:${c.year}:${rule}`,
    source: "genomes" as const,
    year: c.year,
    dateBasis: "collection" as const,
    iso3: watch.area,
    cell: c,
    rule,
  });

  if (watch.trigger === "first_detection") {
    // May use cells below the minimum sample size, labelled as such.
    let negCells = 0;
    let negTested = 0;
    let last: CellStat | undefined;
    for (const c of all) {
      if (c.x === 0) {
        negCells++;
        negTested += c.n;
        last = c;
        continue;
      }
      if (!last) {
        out.push({
          ...base(c, "baseline"),
          kind: "new_signal",
          fired: false,
          strength: null,
          belowMinN: c.n < watch.minN,
        });
      } else {
        out.push({
          ...base(c, "first_detection"),
          kind: "new_signal",
          fired: true,
          strength: c.x === 1 ? "weak" : "signal",
          prev: last,
          yearsApart: c.year - last.year,
          priorNegative: {
            cells: negCells,
            tested: negTested,
            lastYear: last.year,
            lastTested: last.n,
          },
          belowMinN: c.n < watch.minN,
        });
      }
      break;
    }
    return out;
  }

  if (watch.trigger === "who_band" || watch.trigger === "very_high_combo") {
    let prev: Banded | undefined;
    for (const c of qual) {
      const b = banded(c, data.a581g, watch.minN);
      const common = {
        band: b.band,
        a581g: b.a581g,
        a581gUnjudged: b.a581gUnjudged,
        prev: prev?.cell,
        prevBand: prev?.band,
        yearsApart: prev ? c.year - prev.cell.year : undefined,
        delta: prev ? c.pct - prev.cell.pct : undefined,
      };
      if (watch.trigger === "who_band") {
        if (!prev) {
          out.push({ ...base(c, "baseline"), ...common, kind: "prevalence_shift", fired: false, strength: null });
        } else if (b.band !== prev.band) {
          out.push({
            ...base(c, "band_change"),
            ...common,
            kind: "prevalence_shift",
            fired: true,
            strength: "signal",
            direction: BAND_RANK[b.band] > BAND_RANK[prev.band] ? "up" : "down",
          });
        }
      } else {
        const now = b.band === "very_high";
        const was = prev?.band === "very_high";
        if (!prev) {
          // The record opens here: nothing earlier to compare with.
          out.push({ ...base(c, "baseline"), ...common, kind: "prevalence_shift", fired: false, strength: null });
        } else if (now && !was) {
          out.push({ ...base(c, "combo_reached"), ...common, kind: "prevalence_shift", fired: true, strength: "signal", direction: "up" });
        } else if (now && was) {
          out.push({ ...base(c, "combo_holds"), ...common, kind: "prevalence_shift", fired: false, strength: null });
        } else if (!now && was) {
          out.push({ ...base(c, "combo_lapsed"), ...common, kind: "prevalence_shift", fired: true, strength: "signal", direction: "down" });
        }
      }
      prev = b;
    }
    return out;
  }

  if (watch.trigger === "rise" || watch.trigger === "fall") {
    const rise = watch.trigger === "rise";
    const beyond = (c: CellStat) => (rise ? c.pct >= watch.level : c.pct < watch.level);
    const strong = (c: CellStat) => (rise ? c.ci.lo >= watch.level : c.ci.hi < watch.level);
    let prev: CellStat | undefined;
    for (const c of qual) {
      const common = {
        prev,
        yearsApart: prev ? c.year - prev.year : undefined,
        delta: prev ? c.pct - prev.pct : undefined,
        threshold: watch.level,
        direction: (rise ? "up" : "down") as "up" | "down",
      };
      if (!prev) {
        out.push({ ...base(c, "baseline"), ...common, kind: "prevalence_shift", fired: false, strength: null });
      } else if (beyond(c) && !beyond(prev)) {
        out.push({
          ...base(c, "level_crossed"),
          ...common,
          kind: "prevalence_shift",
          fired: true,
          strength: strong(c) ? "strong" : "signal",
        });
      } else if (beyond(c)) {
        out.push({ ...base(c, "still_beyond"), ...common, kind: "prevalence_shift", fired: false, strength: null });
      } else if (beyond(prev)) {
        out.push({
          ...base(c, "level_returned"),
          ...common,
          kind: "prevalence_shift",
          fired: false,
          strength: null,
          direction: rise ? "down" : "up",
        });
      }
      prev = c;
    }
    return out;
  }

  // change
  let prev: CellStat | undefined;
  for (const c of qual) {
    if (!prev) {
      out.push({ ...base(c, "baseline"), kind: "prevalence_shift", fired: false, strength: null, threshold: watch.points });
    } else {
      const delta = c.pct - prev.pct;
      if (Math.abs(delta) >= watch.points) {
        // Strong when the two intervals do not overlap.
        const apart = delta > 0 ? c.ci.lo > prev.ci.hi : c.ci.hi < prev.ci.lo;
        out.push({
          ...base(c, "change"),
          kind: "prevalence_shift",
          fired: true,
          strength: apart ? "strong" : "signal",
          prev,
          yearsApart: c.year - prev.year,
          delta,
          direction: delta > 0 ? "up" : "down",
          threshold: watch.points,
        });
      }
    }
    prev = c;
  }
  return out;
}

function paperEvents(watch: Watch, data: AlertData): AlertEvent[] {
  const out: AlertEvent[] = [];
  const pub = { source: "papers" as const, dateBasis: "publication" as const };

  for (const [i, r] of (data.firstReports ?? []).entries()) {
    if (r.iso3 !== watch.area) continue;
    out.push({
      ...pub,
      id: `p:first:${r.pmid}:${i}`,
      kind: "new_signal",
      rule: "first_report_claim",
      year: r.pubYear,
      fired: true,
      strength: null,
      iso3: r.iso3,
      pmid: r.pmid,
      quote: r.quote,
    });
  }

  // Abstract figures: the first for the country, or one beyond the watch's
  // level. Each stands alone; they are never pooled with each other or with
  // the genome series.
  const figs = (data.figures ?? [])
    .map((f, i) => ({ f, i }))
    .filter(({ f }) => f.iso3 === watch.area)
    .sort((a, b) => a.f.pubYear - b.f.pubYear || a.i - b.i);
  const hasLevel = watch.trigger === "rise" || watch.trigger === "fall";
  figs.forEach(({ f, i }, order) => {
    const beyond =
      hasLevel && f.pct !== null
        ? watch.trigger === "rise"
          ? f.pct >= watch.level
          : f.pct < watch.level
        : false;
    const first = order === 0;
    out.push({
      ...pub,
      id: `p:fig:${f.pmid}:${i}`,
      kind: first ? "new_signal" : "prevalence_shift",
      rule: "abstract_figure",
      year: f.pubYear,
      fired: first || beyond,
      strength: null,
      iso3: f.iso3,
      pmid: f.pmid,
      quote: f.quote,
      statedPct: f.pct,
      threshold: beyond ? watch.level : undefined,
    });
  });

  for (const [i, a] of (data.associations ?? []).entries()) {
    const match = a.iso3s.includes(watch.area);
    if (!match && a.iso3s.length > 0) continue;
    out.push({
      ...pub,
      id: `p:assoc:${a.pmid}:${i}`,
      kind: "association",
      rule: "abstract_association",
      year: a.pubYear,
      fired: match,
      strength: null,
      iso3: match ? watch.area : null,
      pmid: a.pmid,
      quote: a.quote,
      noCountryGiven: !match,
    });
  }
  return out;
}

function graphEvents(watch: Watch, data: AlertData): AlertEvent[] {
  const out: AlertEvent[] = [];
  const g = { source: "graph" as const, dateBasis: "publication" as const, strength: null };
  for (const f of data.graphFindings ?? []) {
    if (f.iso3 !== null && f.iso3 !== watch.area) continue;
    out.push({
      ...g,
      id: `s:finding:${f.id}`,
      kind: "association",
      rule: "graph_finding",
      year: f.pubYear,
      fired: f.iso3 === watch.area,
      iso3: f.iso3,
      graphFindingId: f.id,
      sourceChecked: f.sourceChecked,
      noCountryGiven: f.iso3 === null,
    });
  }
  for (const p of data.graphPapers ?? []) {
    const match = p.iso3s.includes(watch.area);
    if (!match && p.iso3s.length > 0) continue;
    out.push({
      ...g,
      id: `s:paper:${p.pmid}`,
      kind: "association",
      rule: "graph_paper",
      year: p.pubYear,
      fired: false,
      iso3: match ? watch.area : null,
      pmid: p.pmid,
      noCountryGiven: !match,
    });
  }
  return out;
}

const SOURCE_ORDER = { genomes: 0, papers: 1, graph: 2 } as const;

/** Watch + data -> every event, in year order. Pure. */
export function deriveAlerts(watch: Watch, data: AlertData): AlertEvent[] {
  return [...genomeEvents(watch, data), ...paperEvents(watch, data), ...graphEvents(watch, data)].sort(
    (a, b) => a.year - b.year || SOURCE_ORDER[a.source] - SOURCE_ORDER[b.source] || a.id.localeCompare(b.id),
  );
}

/** Replay: only what existed by `year` (collection year for genomes, publication year otherwise). */
export function visibleAt<T extends { year: number }>(items: T[], year: number): T[] {
  return items.filter((e) => e.year <= year);
}

export function firedCount(events: AlertEvent[]): number {
  return events.filter((e) => e.fired).length;
}
