/**
 * Types for the K540E data pack (k540e-data-pack/ at the repo root) and the
 * adapter from the pack's shapes to the derivation's inputs.
 *
 * Marker keys: the DATA layer uses the pack's key (`dhps_K540E`); the URL uses
 * the shell's id (`pfdhps-K540E`). MARKERS maps one to the other. Adding a
 * second marker is one more entry here plus its data files.
 */
import type {
  AlertData,
  Cell,
  MarkerKey,
  WhoBasis,
} from "./derive";
import type { StudyContextFile } from "./context";

/* -------------------------------------------------------------- registry --- */

export type MarkerDef = {
  key: MarkerKey;
  /** Shared URL id used by every tab (`?marker=`). */
  urlId: string;
  label: string;
  gene: string;
  mutation: string;
  drug: string;
  drugShort: string;
  /** Companion series in the genomes file. */
  companions: { a581g: string; a437g: string; quintuple: string };
  /** Text the live probe searches graph variable names for. */
  probes: string[];
};

export const MARKERS: Record<MarkerKey, MarkerDef> = {
  dhps_K540E: {
    key: "dhps_K540E",
    urlId: "pfdhps-K540E",
    label: "PfDHPS K540E",
    gene: "dhps",
    mutation: "K540E",
    drug: "sulfadoxine-pyrimethamine (SP)",
    drugShort: "SP",
    companions: { a581g: "dhps_A581G", a437g: "dhps_A437G", quintuple: "dhfr_dhps_quintuple" },
    probes: ["K540E", "540E"],
  },
};

export const DEFAULT_MARKER: MarkerKey = "dhps_K540E";

export function markerFromUrlId(urlId: string | null | undefined): MarkerDef {
  return Object.values(MARKERS).find((m) => m.urlId === urlId) ?? MARKERS[DEFAULT_MARKER];
}

/* ----------------------------------------------------------------- files --- */

export type Meta = Record<string, unknown>;

export type CountryInfo = {
  country: string;
  region?: string;
  region_label?: string;
  samples?: number;
  year_min?: number;
  year_max?: number;
  who_basis: WhoBasis;
};

/** [iso3, collection_year, numerator, denominator] */
export type ObservationRow = [string, number, number, number];

export type GenomesFile = {
  _meta?: Meta;
  countries: Record<string, CountryInfo>;
  observations: Record<string, ObservationRow[]>;
};

export type Paper = {
  pmid: string | number | null;
  title: string;
  journal?: string | null;
  pub_year: number;
  pub_month?: number | null;
  doi?: string | null;
  url?: string | null;
  countries_iso3?: string[] | null;
  in_graph?: boolean;
  first_report_claim?: unknown;
};

export type AbstractPrevalence = {
  pmid: string | number;
  pub_year: number;
  iso3: string | null;
  country?: string | null;
  site?: string | null;
  year_start?: number | null;
  year_end?: number | null;
  prevalence_pct: number | null;
  numerator?: number | null;
  denominator?: number | null;
  population?: string | null;
  quote: string;
};

export type AbstractAssociation = {
  pmid: string | number;
  pub_year: number;
  countries_iso3?: string[] | null;
  exposure?: string | null;
  outcome?: string | null;
  quote: string;
};

export type LiteratureFile = {
  _meta?: Meta;
  papers: Paper[];
  abstract_prevalence: AbstractPrevalence[];
  abstract_associations: AbstractAssociation[];
};

/** A System graph finding as stored in the pack. Sections carry slightly different extras. */
export type GraphFinding = {
  system_id: string;
  study_id?: string;
  pubmed_id?: string | number | null;
  pubmed_url?: string | null;
  doi?: string | null;
  paper_title?: string | null;
  journal?: string | null;
  pub_year?: number;
  variable_1?: string;
  variable_2?: string;
  variable_1_concept_id?: string | null;
  variable_2_concept_id?: string | null;
  statistic_type?: string | null;
  statistic_label?: string | null;
  statistic_value?: number | null;
  ci_level?: number | null;
  ci_lower?: number | null;
  ci_upper?: number | null;
  p_value?: number | null;
  population?: string | null;
  study_type?: string | null;
  /** stakes_sp only: which use of SP the finding concerns. */
  use?: string;
  country_iso3?: string | null;
  countries_iso3?: string[] | null;
  source_checked?: boolean;
  in_vetted_csv?: boolean;
  /** Present on hand-checked findings. */
  checked?: Record<string, string | null> | null;
  [k: string]: unknown;
};

export type Concept = { label: string; system_id: string; wikidata_id?: string };

export type GraphFile = {
  _meta?: Meta;
  haplotype_findings: GraphFinding[];
  stakes_sp: GraphFinding[];
  findings_from_k540e_papers: GraphFinding[];
  concepts: Concept[];
  vetted_association_ids: string[];
};

export type WhoVerbatim = {
  quote?: string;
  where?: string;
  continue_quote?: string;
  continue_where?: string;
  programme_quote?: string;
  programme_where?: string;
  note?: string;
};

export type ThresholdsFile = {
  _meta?: Meta;
  marker?: {
    who_classification_alone?: string;
    who_classification_haplotype?: string;
    who_compendium?: { source?: string; url?: string };
    [k: string]: unknown;
  };
  who_categories?: {
    label?: string;
    statement?: string;
    limits?: string;
    sources?: { name: string; url: string }[];
    verbatim?: WhoVerbatim;
    [k: string]: unknown;
  };
  presets?: {
    min_samples?: number;
    change_points?: number;
    central_west_africa?: { threshold_pct?: number; why?: string };
    outside_africa?: { threshold_pct?: number; why?: string };
    [k: string]: unknown;
  };
  context?: { id: string; text: string; source?: string; url?: string }[];
  history?: { year: number; text: string; url?: string }[];
};

export type Pack = {
  genomes: GenomesFile;
  literature: LiteratureFile;
  graph: GraphFile;
  thresholds: ThresholdsFile;
  /** Sample-level study context per genome cell; null when the file is not installed. */
  studyContext: StudyContextFile | null;
};

/** What the browser receives: the pack minus the long vetted-id list. */
export type ClientPack = Omit<Pack, "graph"> & {
  graph: Omit<GraphFile, "vetted_association_ids"> & { vetted_count: number };
};

/* --------------------------------------------------------------- adapter --- */

export const pmidStr = (p: string | number | null | undefined): string => (p == null ? "" : String(p));

function rowsToCells(rows: ObservationRow[] | undefined): Cell[] {
  return (rows ?? []).map(([iso3, year, x, n]) => ({ iso3, year, x, n }));
}

/** A paper's first-report claim: a verbatim quote from its abstract, tied to the paper's countries. */
export function firstReportOf(p: Paper): { iso3s: string[]; quote: string } | null {
  const c = p.first_report_claim;
  return typeof c === "string" && c.trim() ? { iso3s: p.countries_iso3 ?? [], quote: c } : null;
}

export function toAlertData(marker: MarkerDef, pack: Pick<Pack, "genomes" | "literature" | "graph"> | ClientPack): AlertData {
  const papers = new Map(pack.literature.papers.map((p) => [pmidStr(p.pmid), p]));
  const yearOf = (pmid: string, fallback?: number) => papers.get(pmid)?.pub_year ?? fallback ?? 0;

  return {
    cells: rowsToCells(pack.genomes.observations[marker.key]),
    a581g: rowsToCells(pack.genomes.observations[marker.companions.a581g]),
    figures: pack.literature.abstract_prevalence
      .filter((f) => f.iso3)
      .map((f) => ({
        pmid: pmidStr(f.pmid),
        pubYear: f.pub_year ?? yearOf(pmidStr(f.pmid)),
        iso3: f.iso3 as string,
        pct: typeof f.prevalence_pct === "number" ? f.prevalence_pct : null,
        quote: f.quote,
      })),
    associations: pack.literature.abstract_associations.map((a) => ({
      pmid: pmidStr(a.pmid),
      pubYear: a.pub_year ?? yearOf(pmidStr(a.pmid)),
      iso3s: a.countries_iso3 ?? papers.get(pmidStr(a.pmid))?.countries_iso3 ?? [],
      quote: a.quote,
    })),
    firstReports: pack.literature.papers.flatMap((p) => {
      const fr = firstReportOf(p);
      if (!fr) return [];
      return fr.iso3s.map((iso3) => ({ pmid: pmidStr(p.pmid), pubYear: p.pub_year, iso3, quote: fr.quote }));
    }),
    graphFindings: pack.graph.haplotype_findings.map((f) => ({
      id: f.system_id,
      pubYear: f.pub_year ?? yearOf(pmidStr(f.pubmed_id)),
      iso3: f.country_iso3 ?? null,
      sourceChecked: f.source_checked === true,
    })),
    graphPapers: pack.literature.papers
      .filter((p) => p.in_graph)
      .map((p) => ({ pmid: pmidStr(p.pmid), pubYear: p.pub_year, iso3s: p.countries_iso3 ?? [] })),
  };
}
