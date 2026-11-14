/**
 * Every sentence a user reads about an alert, as templates filled from the
 * data. No language model at runtime: each statement traces to a count or a
 * verbatim quote.
 *
 * Wording rules (project brief + CLAUDE.md):
 *  - "among N samples collected in <country> in <year>", never "<country>'s prevalence"
 *  - WHO bands describe a level; they are not an instruction about SP
 *  - presets are ours and are labelled as such
 *  - abstract items are quoted, never paraphrased or given a direction
 */
import type { AlertEvent, Band, CellStat, ChangeKind, Trigger, Watch, WhoBasis } from "./derive";
import { WHO_BAND_LINES } from "./derive";

export const pct = (v: number) => `${v.toFixed(1)}%`;
export const ci = (c: CellStat) => `95% CI ${c.ci.lo.toFixed(1)} to ${c.ci.hi.toFixed(1)}`;
export const frac = (c: CellStat) => `${c.x} of ${c.n}`;
const pts = (v: number) => `${Math.abs(v).toFixed(1)} points`;
const years = (n: number) => (n === 1 ? "1 year" : `${n} years`);

export const BAND_LABEL: Record<Band, string> = {
  low: "low",
  medium: "medium",
  high: "high",
  very_high: "very high",
};

export const BAND_RULE: Record<Band, string> = {
  low: `K540E below ${WHO_BAND_LINES.medium}%`,
  medium: `K540E ${WHO_BAND_LINES.medium}% to under ${WHO_BAND_LINES.high}%`,
  high: `K540E ${WHO_BAND_LINES.high}% or more`,
  very_high: `K540E ${WHO_BAND_LINES.high}% or more with A581G ${WHO_BAND_LINES.a581g}% or more`,
};

export const KIND_LABEL: Record<ChangeKind, string> = {
  prevalence_shift: "Prevalence shift",
  new_signal: "New signal in a place or time",
  association: "Association",
};

export const SOURCE_LABEL = {
  genomes: "Genome counts",
  papers: "Papers",
  graph: "System graph",
} as const;

export const TRIGGER_LABEL: Record<Trigger, string> = {
  who_band: "moves into a new WHO resistance band",
  rise: "rises to or above",
  fall: "falls below",
  change: "changes by at least",
  first_detection: "is first detected",
  very_high_combo: "reaches the WHO “very high” combination with A581G",
};

export function watchSentence(w: Watch, marker: string, country: string): string {
  const tail =
    w.trigger === "rise" || w.trigger === "fall"
      ? ` ${w.level}%`
      : w.trigger === "change"
        ? ` ${w.points} percentage points`
        : "";
  return `Tell me when ${marker} in ${country} ${TRIGGER_LABEL[w.trigger]}${tail}, counting samples of at least ${w.minN}.`;
}

/** Whether the watch's line is WHO's or ours. */
export function thresholdBasis(w: Watch, basis: WhoBasis): { published: boolean; text: string } {
  const esa = basis === "east_southern_africa";
  if (w.trigger === "who_band" || w.trigger === "very_high_combo") {
    return esa
      ? { published: true, text: "WHO resistance categories for SP (East and Southern Africa)" }
      : {
          published: false,
          text: "preset, no published threshold: WHO applies K540E bands to East and Southern Africa only",
        };
  }
  if (w.trigger === "rise" || w.trigger === "fall") {
    const onLine = esa && (w.level === WHO_BAND_LINES.medium || w.level === WHO_BAND_LINES.high);
    return onLine
      ? { published: true, text: `WHO category line at ${w.level}% (East and Southern Africa)` }
      : { published: false, text: "preset, no published threshold" };
  }
  if (w.trigger === "change") return { published: false, text: "preset, no published threshold" };
  return { published: false, text: "no threshold: any positive sample after cells that found none" };
}

const cellPhrase = (c: CellStat, marker: string, country: string) =>
  `among ${c.n} samples collected in ${country} in ${c.year}, ${c.x} carried ${marker} (${pct(c.pct)}, ${ci(c)})`;

const prevPhrase = (c: CellStat, minN: number) =>
  `The previous sampled year with at least ${minN} samples, collected in ${c.year}, had ${frac(c)} (${pct(c.pct)}, ${ci(c)})`;

export type EventCopy = {
  /** Short headline for the card. */
  title: string;
  /** One sentence: what changed, before and after. */
  statement: string;
  /** What was compared with what. Printed on every card. */
  basis: string;
};

export function eventCopy(e: AlertEvent, w: Watch, marker: string, country: string): EventCopy {
  const c = e.cell;
  const p = e.prev;
  const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

  switch (e.rule) {
    case "baseline": {
      if (!c) break;
      const where =
        e.band && (w.trigger === "who_band" || w.trigger === "very_high_combo")
          ? ` That is the ${BAND_LABEL[e.band]} band.`
          : "";
      return {
        title: `Record opens in ${c.year} at ${pct(c.pct)}`,
        statement: `${cap(cellPhrase(c, marker, country))}.${where} This is the first cell in the record${
          w.trigger === "first_detection" ? "" : ` with at least ${w.minN} samples`
        }, so it is a baseline, not a change.`,
        basis: "No earlier cell to compare with. An earlier year without data was not sampled; it is not a zero.",
      };
    }
    case "band_change": {
      if (!c || !p || !e.band || !e.prevBand) break;
      return {
        title: `${cap(BAND_LABEL[e.prevBand])} band to ${BAND_LABEL[e.band]} band`,
        statement: `${cap(cellPhrase(c, marker, country))}: the ${BAND_LABEL[e.band]} band. ${prevPhrase(p, w.minN)}: the ${BAND_LABEL[e.prevBand]} band.`,
        basis: `Compared with the previous sampled year of at least ${w.minN} samples, ${years(e.yearsApart ?? 0)} earlier (${p.year}). Years in between were not sampled or fell under the minimum.`,
      };
    }
    case "combo_reached":
    case "combo_holds":
    case "combo_lapsed": {
      if (!c || !e.band) break;
      const a = e.a581g;
      const aPhrase = a
        ? `A581G was found in ${frac(a)} (${pct(a.pct)}, ${ci(a)}) of the same collection`
        : "A581G was not tested in this cell, so the “very high” band cannot be judged";
      const title =
        e.rule === "combo_reached"
          ? "Reaches the “very high” combination"
          : e.rule === "combo_holds"
            ? "“Very high” combination still holds"
            : "“Very high” combination lapses";
      return {
        title,
        statement: `${cap(cellPhrase(c, marker, country))}; ${aPhrase}. That is the ${BAND_LABEL[e.band]} band${
          p && e.prevBand ? `; the previous sampled year (${p.year}) was in the ${BAND_LABEL[e.prevBand]} band` : ""
        }.`,
        basis: p
          ? `Compared with the previous sampled year of at least ${w.minN} samples, ${years(e.yearsApart ?? 0)} earlier (${p.year}). “Very high” needs ${BAND_RULE.very_high} in the same cell.`
          : `“Very high” needs ${BAND_RULE.very_high} in the same cell.`,
      };
    }
    case "level_crossed":
    case "still_beyond":
    case "level_returned": {
      if (!c || !p) break;
      const rise = w.trigger === "rise";
      const side = rise ? "at or above" : "below";
      const other = rise ? "below" : "at or above";
      const title =
        e.rule === "level_crossed"
          ? `${rise ? "Rises to" : "Falls below"} ${w.level}%`
          : e.rule === "still_beyond"
            ? `Still ${side} ${w.level}%`
            : `Back ${other} ${w.level}%`;
      const now = e.rule === "level_returned" ? other : side;
      const strength =
        e.rule !== "level_crossed"
          ? ""
          : e.strength === "strong"
            ? ` The whole interval is ${side} ${w.level}%: a strong signal.`
            : ` The interval spans ${w.level}%: a signal, not a strong one.`;
      return {
        title,
        statement: `${cap(cellPhrase(c, marker, country))}: ${now} ${w.level}%. ${prevPhrase(p, w.minN)}.${strength}`,
        basis: `Compared with the previous sampled year of at least ${w.minN} samples, ${years(e.yearsApart ?? 0)} earlier (${p.year}).`,
      };
    }
    case "change": {
      if (!c || !p || e.delta === undefined) break;
      const dir = e.delta > 0 ? "up" : "down";
      return {
        title: `${cap(dir)} ${pts(e.delta)} in ${years(e.yearsApart ?? 0)}`,
        statement: `${cap(cellPhrase(c, marker, country))}, ${dir} ${pts(e.delta)} from ${frac(p)} (${pct(p.pct)}, ${ci(p)}) in ${p.year}.${
          e.strength === "strong" ? " The two intervals do not overlap." : " The two intervals overlap."
        }`,
        basis: `Compared with the previous sampled year of at least ${w.minN} samples, ${years(e.yearsApart ?? 0)} earlier (${p.year}). The two collections may come from different sites.`,
      };
    }
    case "first_detection": {
      if (!c || !e.priorNegative) break;
      const n = e.priorNegative;
      return {
        title: `First detected in ${c.year}${e.strength === "weak" ? " (single sample)" : ""}`,
        statement: `${cap(cellPhrase(c, marker, country))}, after none in ${n.lastTested} samples collected in ${n.lastYear}${
          n.cells > 1 ? ` (none in ${n.tested} samples across ${n.cells} earlier cells)` : ""
        }.${e.strength === "weak" ? " A single positive sample: a weak signal." : ""}${
          e.belowMinN ? ` This cell has fewer than ${w.minN} samples.` : ""
        }`,
        basis: `Compared with every earlier cell for ${country}, of any size. Earlier cells tested for ${marker} and found none; years without a cell were not sampled.`,
      };
    }
    case "first_report_claim":
      return {
        title: `First-report claim, published ${e.year}`,
        statement: `A paper published in ${e.year} makes a first-report claim involving ${country}. Its abstract says: “${e.quote}”`,
        basis: "Machine-read from the abstract; the quote appears word for word in it. Not checked by hand.",
      };
    case "abstract_figure":
      return {
        title: `Stated in the abstract${e.statedPct != null ? `: ${e.statedPct}%` : ""}`,
        statement: `A paper published in ${e.year} states a ${marker} figure for ${country}. Its abstract says: “${e.quote}”`,
        basis:
          "Stated in the abstract, machine-read, not checked by hand. Shown on its own: never pooled with the genome counts or with other papers.",
      };
    case "abstract_association":
      return {
        title: `Association sentence, published ${e.year}`,
        statement: `A paper published in ${e.year} links ${marker} or a haplotype containing it to an outcome. Its abstract says: “${e.quote}”`,
        basis:
          "Machine-read from the abstract and quoted as written. No direction or strength is assigned here; read the paper.",
      };
    case "graph_finding":
      return {
        title: `System graph finding, published ${e.year}`,
        statement: `The System graph holds a finding on a haplotype that contains ${marker}, from a paper published in ${e.year}.`,
        basis: e.sourceChecked
          ? "Checked against the source paper."
          : "Reported by the graph, unverified.",
      };
    case "graph_paper":
      return {
        title: `Graph has read a paper published ${e.year}`,
        statement: `The System graph contains a ${marker} paper published in ${e.year}.`,
        basis: "In-graph flag from the data pack; what the graph extracted is listed with the alert.",
      };
  }
  return { title: e.rule, statement: "", basis: "" };
}

/** What an alert of this kind cannot tell you. Fixed text per source. */
export function limits(e: AlertEvent, basis: WhoBasis, marker: string, drugShort: string): string[] {
  const out: string[] = [];
  if (e.source === "genomes") {
    out.push(
      "These are convenience samples, often from a few sites. This is not the country’s prevalence.",
      "Years without a cell were not sampled. No data is not the same as no resistance.",
      `A molecular marker is associated with reduced drug susceptibility. This alert does not establish that ${drugShort} has stopped working for anyone.`,
    );
    if (basis === "east_southern_africa") {
      out.push(
        `The WHO bands describe a level of resistance. They are not an instruction to stop using ${drugShort}, and this is not a WHO determination.`,
      );
    } else {
      out.push(
        `WHO applies ${marker} bands to East and Southern Africa only. Any line drawn here is this tool’s preset, not a published threshold.`,
      );
    }
    out.push("Genome counts are dated by collection year. They became public later, with the data release.");
  } else if (e.source === "papers") {
    out.push(
      "A language model read the abstract; a program kept only quotes that appear word for word. Nobody checked it by hand.",
      "An abstract is not the full paper: sample sizes, sites and caveats may be missing from the quote.",
      "Figures from different papers were sampled differently and are never pooled here.",
    );
  } else {
    out.push(
      "A graph finding is an association between a pair of variables. It is not cause and effect, and it does not say which variable is the exposure.",
      `No graph finding names ${marker} on its own; these concern haplotypes that contain it.`,
      "About a fifth of associations returned by the System API are known-bad extractions; only vetted ids are shown.",
      "A vetted id can still be wrong. One SP finding (PEyo2A8Ol0, PMID 26429700) presented a trial’s comparison in the reverse direction; it was caught against the paper and excluded.",
    );
  }
  out.push("Nothing here is live surveillance or clinical guidance.");
  return out;
}
