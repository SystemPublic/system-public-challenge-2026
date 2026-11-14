/**
 * Triggering-study context: for every alert, which study it rests on, where
 * the samples came from, how the genomes were measured, what else sits at
 * codon 540, and how much local history there was before it.
 *
 * Early-warning alerts still fire on thin signals. This module does not
 * suppress anything; it attaches what a reader needs to weigh the signal.
 *
 * Pure and self-contained (type-only imports), so `node --test` can run it
 * directly. Every sentence is a template filled from counts in
 * k540e-data-pack/k540e-study-context.json (MalariaGEN Pf8 sample metadata).
 */
import type { AlertEvent, Cell, CellStat, Watch, WhoBasis } from "./derive";

/* ------------------------------------------------------------------ file --- */

export type Admin1 = { name: string; k: number; n: number };

export type StudyRef = {
  study_id: string;
  k: number;
  n: number;
  pct: number;
  admin1: Admin1[];
  dna_method: Record<string, number>;
  median_callable_pct: number | null;
};

export type MutantIsolate = {
  sample: string;
  study_id: string;
  admin1: string;
  dna_method: string;
  callable_pct: number | null;
  call540: string;
  ena: string | null;
};

export type StudyCell = {
  iso3: string;
  year: number;
  k: number;
  n: number;
  qc_total_in_cell: number;
  study_count: number;
  admin1_count: number;
  single_site_warning: boolean;
  studies: StudyRef[];
  admin1: Admin1[];
  dna_method_all: Record<string, number>;
  dna_method_mutants: Record<string, number>;
  codon540_breakdown: { monoclonal_E: number; polyclonal_mixed_E: number; alt_mutant_540N: number; wildtype_only_K: number };
  median_callable_pct: number | null;
  mutant_min_callable_pct: number | null;
  sample_mutant_isolates: MutantIsolate[];
};

export type StudyContextFile = {
  _meta?: {
    source?: string;
    url?: string;
    doi?: string;
    license?: string;
    dna_method_glossary?: Record<string, string>;
    note?: string;
  };
  cells: Record<string, StudyCell>;
};

export const cellKey = (iso3: string, year: number) => `${iso3}:${year}`;

export function studyCellFor(file: StudyContextFile | null | undefined, iso3: string | null | undefined, year: number): StudyCell | undefined {
  return file && iso3 ? file.cells[cellKey(iso3, year)] : undefined;
}

/* ----------------------------------------------------------- tier labels --- */

/** The three lanes are different kinds of study. They are badged everywhere and never blurred. */
export const EVIDENCE_TIER = {
  genomes: "Curated WGS Surveillance (MalariaGEN Pf8)",
  papers: "Published Molecular / Clinical Paper",
  graph: "System Graph extraction",
} as const;

export const NO_STUDY_TYPE = "study type not given by the graph";

export const enaUrl = (run: string) => `https://www.ebi.ac.uk/ena/browser/view/${encodeURIComponent(run)}`;

const ASSAY_WORDS: [RegExp, string][] = [
  [/whole[- ]genome/i, "whole-genome"],
  [/amplicon/i, "amplicon"],
  [/\bPCR\b|polymerase chain reaction/i, "PCR"],
  [/sanger/i, "Sanger"],
  [/deep sequencing|next[- ]generation sequencing|\bNGS\b/i, "deep sequencing"],
  [/efficacy/i, "efficacy study"],
  [/\btrial\b/i, "trial"],
];

/** Assay or design words that appear in a paper's title. Read from the title only; nothing is inferred. */
export function assayKeywords(title: string | null | undefined): string[] {
  if (!title) return [];
  return ASSAY_WORDS.filter(([re]) => re.test(title)).map(([, label]) => label);
}

/** Abstract figures whose stated collection window covers a genome cell's country and year. */
export function matchingFigures<T extends { iso3: string | null; year_start?: number | null; year_end?: number | null }>(figures: T[], iso3: string, year: number): T[] {
  return figures.filter((f) => f.iso3 === iso3 && f.year_start != null && f.year_start <= year && year <= (f.year_end ?? f.year_start));
}

/* -------------------------------------------------------------- geography --- */

export type GeoScope = {
  kind: "single_site" | "clustered" | "multi_site" | "unknown";
  /** Short flag for badges, or null when there is nothing to flag. */
  flag: string | null;
  /** The one site (single-site) or the one positive site (clustered). */
  site: string | null;
  /** One sentence, counts only. */
  text: string;
  /** Scope as it appears in an email subject. */
  short: string;
};

const methodList = (m: Record<string, number>) =>
  Object.entries(m)
    .filter(([, n]) => n > 0)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));

export const methodNames = (m: Record<string, number>) => methodList(m).map(([k]) => k);
export const methodText = (m: Record<string, number>) =>
  methodList(m)
    .map(([k, n]) => `${k} ${n}`)
    .join(", ") || "not recorded";

export function geoScope(c: StudyCell, mutation = "K540E"): GeoScope {
  const all = methodNames(c.dna_method_all).join("/");
  if (c.single_site_warning) {
    const site = c.admin1[0]?.name ?? "one Admin-1 area";
    return {
      kind: "single_site",
      flag: "Single-site sample",
      site,
      text: `Single-site sample: all ${c.n} samples (${c.k} carrying ${mutation}) were collected in ${site}. Reading this as a national figure needs multi-site confirmation.`,
      short: `single-site ${site}${all ? ` (${all})` : ""}`,
    };
  }
  const positive = c.admin1.filter((a) => a.k > 0);
  if (c.admin1_count > 1 && c.k > 0 && positive.length === 1) {
    const a = positive[0];
    const others = c.admin1_count - 1;
    return {
      kind: "clustered",
      flag: "Subnational clustering",
      site: a.name,
      text: `Subnational clustering: ${c.admin1_count} Admin-1 areas were sampled (n=${c.n}); all ${c.k} of ${c.k} samples carrying ${mutation} were in ${a.name} (${a.k}/${a.n}), with 0/${c.n - a.n} ${others === 1 ? "in the other one" : `across the other ${others}`}.`,
      short: `${c.admin1_count} Admin-1 areas (${c.k}/${c.k} in ${a.name}, ${methodNames(c.dna_method_mutants).join("/")})`,
    };
  }
  if (c.admin1_count > 1) {
    return {
      kind: "multi_site",
      flag: null,
      site: null,
      text: `${c.admin1_count} Admin-1 areas were sampled (n=${c.n})${c.k > 0 ? `; samples carrying ${mutation} came from ${positive.length} of them` : ""}.`,
      short: `${c.admin1_count} Admin-1 areas${all ? ` (${all})` : ""}`,
    };
  }
  return { kind: "unknown", flag: null, site: null, text: "No Admin-1 site is recorded for this cell.", short: `site not recorded${all ? ` (${all})` : ""}` };
}

/* ------------------------------------------------------------ measurement --- */

export type Measurement = {
  all: [string, number][];
  mutants: [string, number][];
  /** Positives seen under two or more DNA preparations. */
  replicated: boolean;
  /** One sentence on whether the positives replicate across preparations. */
  note: string | null;
  callable: string;
};

export function measurement(c: StudyCell, mutation = "K540E"): Measurement {
  const all = methodList(c.dna_method_all);
  const mutants = methodList(c.dna_method_mutants);
  const replicated = mutants.length >= 2;
  let note: string | null = null;
  if (c.k > 0 && replicated) {
    note = `Samples carrying ${mutation} replicate across ${mutants.map(([m]) => m).join(" and ")} preparations.`;
  } else if (c.k > 0 && mutants.length === 1) {
    const m = mutants[0][0];
    note =
      all.length > 1
        ? `Samples carrying ${mutation} are ${m}-only; the ${all.filter(([k]) => k !== m).map(([k]) => k).join(" and ")} samples in this cell found none.`
        : `${m}-only: every sample in this cell used one preparation, so the calls are not replicated across methods.`;
  }
  const callable = [
    c.median_callable_pct != null ? `median ${c.median_callable_pct}% of the genome callable` : null,
    c.k > 0 && c.mutant_min_callable_pct != null ? `lowest among samples carrying ${mutation}: ${c.mutant_min_callable_pct}%` : null,
  ]
    .filter(Boolean)
    .join("; ");
  return { all, mutants, replicated, note, callable: callable || "callable genome not recorded" };
}

/** Up to `max` mutant isolates with an ENA run, spread across DNA preparations so each can be checked. */
export function enaRuns(c: StudyCell, max = 3): MutantIsolate[] {
  const withRun = c.sample_mutant_isolates.filter((s) => s.ena);
  const out: MutantIsolate[] = [];
  for (const s of withRun) if (!out.some((o) => o.dna_method === s.dna_method)) out.push(s);
  for (const s of withRun) if (!out.includes(s)) out.push(s);
  return out.slice(0, max);
}

/* --------------------------------------------------------------- codon 540 --- */

export type Codon540 = {
  text: string;
  /** Set whenever another codon-540 mutant was called in the cell. */
  altWarning: string | null;
};

const pct1 = (x: number, n: number) => (n > 0 ? `${((x / n) * 100).toFixed(1)}%` : "n/a");

export function codon540(c: StudyCell, mutation = "K540E"): Codon540 {
  const b = c.codon540_breakdown;
  const text = `${b.monoclonal_E} single-genotype E, ${b.polyclonal_mixed_E} mixed K,E (counted as carrying ${mutation}), ${b.alt_mutant_540N} with K540N, ${b.wildtype_only_K} wild-type K only, of ${c.n} samples.`;
  const altWarning =
    b.alt_mutant_540N > 0
      ? `Alternative codon-540 allele: K540N was called in ${b.alt_mutant_540N} of ${c.n} samples in this cell (${pct1(b.alt_mutant_540N, c.n)}), against ${c.k} carrying ${mutation} (${pct1(c.k, c.n)}). A low or falling ${mutation} count here is not a return to wild-type: ${b.wildtype_only_K} of ${c.n} samples were wild-type K only.`
      : null;
  return { text, altWarning };
}

/* ------------------------------------------------------------ local prior --- */

export type LocalPrior = {
  kind: "zero" | "established";
  /** Classification name, as tested. */
  name: "Zero local prior" | "Established local prior";
  /** The line shown on the alert. */
  label: string;
  detail: string;
  /** What a reader would look for next. Surveillance follow-up, not treatment advice. */
  steps: string[];
};

export const NEXT_STEPS_NOTE =
  "What a reviewer would look for before this signal bears on a decision. A genetic signal is an early-warning trigger for follow-up, never on its own a declaration of a clinical emergency. Not clinical guidance.";

/**
 * Local prior: genome cells for the same country collected strictly before
 * `year`. Zero when none of them carried the mutation (or there are none).
 */
export function localPrior(cells: Cell[], iso3: string, year: number, opts: { country?: string; mutation?: string; site?: string | null } = {}): LocalPrior {
  const mutation = opts.mutation ?? "K540E";
  const where = opts.country ?? iso3;
  const earlier = cells.filter((c) => c.iso3 === iso3 && c.n > 0 && c.year < year).sort((a, b) => a.year - b.year);
  const positive = earlier.filter((c) => c.x > 0);
  if (positive.length === 0) {
    const tested = earlier.reduce((s, c) => s + c.n, 0);
    return {
      kind: "zero",
      name: "Zero local prior",
      label: "Zero local prior — higher verification bar",
      detail:
        earlier.length === 0
          ? `No genome cell for ${where} was collected before ${year}, so there is no local history of ${mutation} to weigh this against.`
          : `None of ${tested} samples in ${earlier.length} earlier cell${earlier.length === 1 ? "" : "s"} for ${where} (${earlier[0].year}${earlier.length > 1 ? ` to ${earlier[earlier.length - 1].year}` : ""}) carried ${mutation}.`,
      steps: [
        "Verify the assay and the raw sequencing reads (ENA runs listed with this alert).",
        `Expand sentinel sampling around the positive Admin-1 site${opts.site ? ` (${opts.site})` : ""}.`,
        "Monitor clinical clearance through efficacy studies.",
      ],
    };
  }
  const first = positive[0];
  const last = positive[positive.length - 1];
  return {
    kind: "established",
    name: "Established local prior",
    label: "Established resistance prior — evaluate against cutoff",
    detail: `${positive.length} earlier cell${positive.length === 1 ? "" : "s"} for ${where} already carried ${mutation}, from ${first.x}/${first.n} collected in ${first.year}${
      last !== first ? ` to ${last.x}/${last.n} in ${last.year}` : ""
    }.`,
    steps: [
      "Read the observed proportion and its interval against the cutoff, side by side.",
      "Genetics is the early-warning trigger; clinical follow-up runs through WHO therapeutic efficacy studies (TES) or chemoprevention efficacy studies (CES).",
      "A marker proportion alone does not establish that the drug has failed for anyone.",
    ],
  };
}

/* ----------------------------------------------------------------- cutoff --- */

export type Cutoff = {
  /** Line in percent, or null when the rule has no level (first detection, change in points). */
  value: number | null;
  published: boolean;
  /** Short form for badges and the email subject. */
  short: string;
  text: string;
};

/** The line this alert was judged against, and whether WHO or this project drew it. */
export function cutoffFor(e: Pick<AlertEvent, "band" | "rule">, watch: Pick<Watch, "trigger" | "level" | "points">, basis: WhoBasis): Cutoff {
  const esa = basis === "east_southern_africa";
  if (watch.trigger === "first_detection") {
    return { value: null, published: false, short: "no cutoff: any positive sample", text: "No cutoff applies: this rule fires on any positive sample after cells that found none." };
  }
  if (watch.trigger === "change") {
    return {
      value: null,
      published: false,
      short: `project preset ${watch.points}-point change`,
      text: `Project preset: a change of at least ${watch.points} percentage points between two cells. No published threshold.`,
    };
  }
  if (watch.trigger === "rise" || watch.trigger === "fall") {
    const who = esa && (watch.level === 40 || watch.level === 60);
    return {
      value: watch.level,
      published: who,
      short: who ? `WHO ${watch.level}% line` : `project preset ${watch.level}%`,
      text: who ? `WHO SP-resistance category line at ${watch.level}% (East and Southern Africa).` : `Project preset at ${watch.level}%. No published threshold.`,
    };
  }
  // who_band / very_high_combo: the line that bounds the band this cell sits in
  const value = e.band === "high" || e.band === "very_high" ? 60 : 40;
  return esa
    ? {
        value,
        published: true,
        short: `WHO ${value}% line`,
        text: `WHO SP-resistance category lines for East and Southern Africa: 40% and 60% (with A581G at 5% for “very high”). The nearest line to this cell's band is ${value}%.`,
      }
    : {
        value,
        published: false,
        short: `project preset ${value}% line`,
        text: `Project preset: WHO applies K540E bands to East and Southern Africa only, so the 40% and 60% lines here are not a published threshold for this country.`,
      };
}

export const observedText = (c: CellStat) => `${c.pct.toFixed(1)}% (${c.x}/${c.n}), 95% Wilson CI ${c.ci.lo.toFixed(1)} to ${c.ci.hi.toFixed(1)}`;

/** Where the interval sits relative to the cutoff. Null when the rule has no level. */
export function cutoffRelation(c: CellStat, cutoff: Cutoff): string | null {
  if (cutoff.value == null) return null;
  const v = cutoff.value;
  if (c.ci.lo >= v) return `The whole interval is at or above ${v}%.`;
  if (c.ci.hi < v) return `The whole interval is below ${v}%.`;
  return `The interval spans ${v}%: the data do not settle which side of the line this cell is on.`;
}

/* --------------------------------------------------------------- assembled --- */

export type ContextFlag = { tone: "warn" | "info"; label: string; text: string };

export type GenomeContext = {
  cell: StudyCell | undefined;
  tier: string;
  /** "1 study · sWGA 54, gDNA 2" */
  tierDetail: string;
  geo: GeoScope | null;
  measure: Measurement | null;
  codon: Codon540 | null;
  runs: MutantIsolate[];
  prior: LocalPrior;
  cutoff: Cutoff;
  observed: string;
  relation: string | null;
  flags: ContextFlag[];
};

export function genomeContext(args: {
  e: AlertEvent;
  watch: Watch;
  basis: WhoBasis;
  cells: Cell[];
  study: StudyContextFile | null | undefined;
  country: string;
  mutation: string;
}): GenomeContext | null {
  const { e, mutation } = args;
  if (!e.cell || !e.iso3) return null;
  const cell = studyCellFor(args.study, e.iso3, e.cell.year);
  const geo = cell ? geoScope(cell, mutation) : null;
  const measure = cell ? measurement(cell, mutation) : null;
  const codon = cell ? codon540(cell, mutation) : null;
  const prior = localPrior(args.cells, e.iso3, e.cell.year, { country: args.country, mutation, site: geo?.site ?? cell?.admin1.find((a) => a.k > 0)?.name });
  const cutoff = cutoffFor(e, args.watch, args.basis);
  const flags: ContextFlag[] = [];
  // the label is shown beside the text, so drop the sentence's own lead-in
  const body = (s: string) => {
    const t = s.replace(/^[^:]{1,40}: /, "");
    return t.charAt(0).toUpperCase() + t.slice(1);
  };
  if (codon?.altWarning) flags.push({ tone: "warn", label: "Alternative codon-540 allele", text: body(codon.altWarning) });
  if (geo?.flag) flags.push({ tone: "warn", label: geo.flag, text: body(geo.text) });
  flags.push({ tone: prior.kind === "zero" ? "warn" : "info", label: prior.label, text: prior.detail });
  return {
    cell,
    tier: EVIDENCE_TIER.genomes,
    tierDetail: cell ? `${cell.study_count} partner stud${cell.study_count === 1 ? "y" : "ies"} · ${methodText(cell.dna_method_all)}` : "study context not recorded for this cell",
    geo,
    measure,
    codon,
    runs: cell ? enaRuns(cell) : [],
    prior,
    cutoff,
    observed: observedText(e.cell),
    relation: cutoffRelation(e.cell, cutoff),
    flags,
  };
}

/* ----------------------------------------------------------------- subject --- */

const clip = (s: string, n: number) => (s.length > n ? `${s.slice(0, n - 1).trimEnd()}…` : s);

/** `[<evidence source and assay> · <study and site scope>]` for a genome cell. */
export function genomeSourceTag(c: StudyCell | undefined, mutation = "K540E"): string {
  if (!c) return "MalariaGEN Pf8 WGS · study context not recorded";
  return `MalariaGEN Pf8 WGS · ${c.study_count} stud${c.study_count === 1 ? "y" : "ies"}, ${geoScope(c, mutation).short}`;
}

/**
 * Email subject for a genome alert: where the evidence comes from and its
 * scope first, then the country, the marker with its drug, the headline
 * count, and the prior or rule it should be read against.
 */
export function genomeSubject(args: { e: AlertEvent; ctx: GenomeContext; country: string; mutation: string; drugShort: string }): string {
  const { e, ctx } = args;
  const c = e.cell!;
  const first = e.rule === "first_detection" ? "first " : "";
  const tail = ctx.prior.kind === "zero" ? "Zero-prior early warning" : `${ctx.cutoff.short}; confirm via TES/CES`;
  return `[${genomeSourceTag(ctx.cell, args.mutation)}] ${args.country} ${first}${args.mutation} (${args.drugShort} marker) ${c.pct.toFixed(1)}% (${c.x}/${c.n}) — ${tail}${e.fired ? "" : " · context, not an alert"}`;
}

/** Email subject for a paper or graph item: tier and study scope first. */
export function itemSubject(args: { tier: string; scope: (string | null | undefined)[]; country: string; mutation: string; drugShort: string; title: string; fired: boolean }): string {
  const scope = args.scope.filter(Boolean).map((s) => clip(String(s), 60));
  return clip(`[${[args.tier, ...scope].join(" · ")}] ${args.country} ${args.mutation} (${args.drugShort} marker): ${args.title}${args.fired ? "" : " · context, not an alert"}`, 290);
}
