/** Data contract for the Forecast tab. One owner: the data agent. */

/** ISO 3166-1 alpha-3, upper case, e.g. "NGA". */
export type Iso3 = string;

export interface SourceInfo {
  id: string; // "malariagen-pf8" | "system-public-graph"
  label: string; // short on-screen label
  licence: string;
  citation: string; // verbatim where the source prescribes one
  url: string;
  retrievedAt: string; // ISO datetime
  notes: string[]; // caveats shown on screen, plain sentences
}

/* ===== GENOME DATA — MalariaGEN Pf8. Clock: sample COLLECTION year. ===== */
export interface GenomeYear {
  year: number; // collection year
  tested: number; // samples with a usable call at pfdhps codon 540 (= kOnly + eOnly + mixedWithE + other)
  kOnly: number; // K only: no mutation at codon 540
  eOnly: number; // E only: K540E
  mixedWithE: number; // mixed call that includes E (e.g. "K,E"): sample carries K540E alongside another allele
  withE: number; // eOnly + mixedWithE = samples carrying K540E
  other: number; // usable call with no E and not K-only (e.g. N, Y, "K,N"): NOT K540E
  missing: number; // no usable call. Not part of `tested`.
}
export interface GenomeCountry {
  iso3: Iso3;
  name: string; // country name as written in the Pf8 metadata
  years: GenomeYear[]; // ascending; only years with at least one sample
}
export interface GenomeDataset {
  source: SourceInfo;
  minYear: number;
  maxYear: number;
  countries: GenomeCountry[];
}

/* ===== PUBLIC GRAPH — System Public Graph findings. ===== */
export type GraphKind = "sp" | "codon540" | "haplotype"; // "haplotype": the Alert tab pack's K540E-containing haplotype findings
export interface GraphCountryMatch {
  iso3: Iso3;
  matchedText: string; // the exact text that matched
  field: "study.population" | "variable_name";
}
export interface GraphPaperMeta {
  /** Resolved OUTSIDE the Graph (OpenAlex, by PMID or DOI). The Graph has no per-finding date or title. */
  title: string | null;
  publishedDate: string | null; // YYYY-MM-DD
  year: number | null;
  source: "openalex" | null;
}
export interface GraphFinding {
  systemId: string; // Graph association id, verbatim
  kind: GraphKind; // "sp": a variable name refers to SP. "codon540": a variable name explicitly includes 540E
  spLooksLikeUptake: boolean; // name-based hint only: the SP variable looks like an uptake/coverage measure
  variable1: string; // verbatim
  variable2: string; // verbatim
  statisticType: string; // verbatim, e.g. "odds_ratio"
  statisticValue: number | null;
  ciLower: number | null;
  ciUpper: number | null;
  pValue: number | null;
  studyId: string | null;
  pubmedId: string | null;
  doi: string | null;
  population: string | null; // verbatim Graph study population text
  countries: GraphCountryMatch[];
  paper: GraphPaperMeta;
  verification?: GraphVerification | null; // null or absent = not checked against the paper
  inVettedCsv?: boolean | null; // true = in System's vetted associations CSV; false = served by the API only; null = not determined
}

/* ===== PAPER SPOT-CHECK — data/forecast/graph-verification.json (AI-assisted, not human-reviewed). ===== */
export type VerificationStatus = "supported" | "partly_supported" | "contradicted" | "not_verifiable";
export interface GraphVerification {
  status: VerificationStatus;
  where: "abstract" | "full_text" | null;
  quote: string | null; // <= 30 words, copied from the paper
  note: string | null; // what differs, one plain sentence
  countryAgrees: boolean | null;
}
export interface VerificationCounts {
  supported: number;
  partly_supported: number;
  contradicted: number;
  not_verifiable: number;
  unchecked: number;
}
export interface GraphVerificationMeta {
  method: string;
  checkedBy: string;
  checkedAt: string;
  scope: string;
  counts: VerificationCounts;
}
export interface GraphDataset {
  source: SourceInfo;
  version: string; // "2.1"
  snapshot: string; // "2026-07-01"
  selectionRule: string;
  totals: {
    sp: number; // all findings where a variable name refers to SP
    spNamingCountry: number;
    spWithoutStudyRecord: number; // no study record, so the country is unknown
    codon540: number;
    codon540NamingCountry: number;
    papersBehindCodon540: number;
    haplotype: number; // the Alert tab pack's haplotype findings (3)
    haplotypeNamingCountry: number;
  };
  findings: GraphFinding[]; // only findings that name at least one country
}

/* ===== PAPERS — K540E papers from PubMed, via the Alert tab's data pack. Clock: PUBLICATION date. ===== */
export interface PaperRecord {
  pmid: string;
  doi: string | null;
  title: string;
  journal: string | null;
  year: number; // publication year
  month: number | null; // publication month 1-12 when the pack has it
  countries: Iso3[]; // countries the paper concerns, as given in the pack (machine-read from abstracts)
  readByGraph: boolean; // the System Public Graph holds findings from this paper (pack field `in_graph`)
  url: string;
}
export interface PapersDataset {
  source: SourceInfo;
  total: number;
  readByGraph: number;
  papers: PaperRecord[];
}

/* ===== ALERTS — produced by the Alert tab (David). Field names are the team contract: do not rename. ===== */
export interface AlertRecord {
  id: string;
  marker_id: string; // "pfdhps-K540E"
  country_iso3: Iso3;
  year: number; // the year the alert fires on
  rule: string;
  headline: string;
}
export interface AlertFeed {
  alerts: AlertRecord[];
  placeholder: boolean; // true = the badged placeholder, not the Alert tab's real output
}

/* ===== Derived as-of views (computed in lib/forecast/data.ts) ===== */
export type GenomeState = "not_sampled" | "tested_not_detected" | "detected";
export interface GenomeSnapshot {
  iso3: Iso3;
  asOfYear: number;
  state: GenomeState; // from all collection years <= asOfYear
  years: GenomeYear[]; // years <= asOfYear, ascending
  latest: GenomeYear | null; // most recent year <= asOfYear with tested > 0
  firstTestedYear: number | null;
  firstDetectionYear: number | null; // first year <= asOfYear with withE > 0 ("first detection in our data")
  totalTested: number;
  totalWithE: number;
  totalOther: number;
}
export interface GenomeChange {
  iso3: Iso3;
  year: number;
  kind: "first_tested" | "first_detection";
  counts: GenomeYear;
}

/* ===== POLICY MILESTONES — WHO documents as listed in the Alert tab's data pack (verbatim). ===== */
export interface PolicyMilestone {
  year: number;
  text: string;
  url: string;
}
