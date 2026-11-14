/**
 * Pure data access for the Forecast tab. No React; safe in client components.
 * Every value comes from the pinned JSON files in data/forecast/.
 * Two clocks: genome counts use sample COLLECTION year; papers and Graph findings use PUBLICATION year.
 */
import genomeJson from "@/data/forecast/genome-k540e.json";
import graphJson from "@/data/forecast/graph-findings.json";
import verificationJson from "@/data/forecast/graph-verification.json";
import papersJson from "@/data/forecast/papers.json";
import vettedJson from "@/data/forecast/graph-vetted.json";
import policyJson from "@/data/forecast/policy-milestones.json";
import type {
  AlertFeed,
  AlertRecord,
  GenomeChange,
  GenomeDataset,
  GenomeSnapshot,
  GenomeYear,
  GraphDataset,
  GraphFinding,
  GraphVerification,
  GraphVerificationMeta,
  Iso3,
  PaperRecord,
  PapersDataset,
  PolicyMilestone,
  SourceInfo,
  VerificationCounts,
  VerificationStatus,
} from "./types";

export const GENOME: GenomeDataset = genomeJson as GenomeDataset;

/* ----- Paper spot-check join (by systemId). Unknown statuses are ignored, never guessed. ----- */
const STATUSES: readonly VerificationStatus[] = [
  "supported",
  "partly_supported",
  "contradicted",
  "not_verifiable",
];
interface RawVerificationFile {
  method?: unknown;
  checkedBy?: unknown;
  checkedAt?: unknown;
  scope?: unknown;
  records?: unknown;
}
const rawVerification = verificationJson as RawVerificationFile;
const strOrNull = (x: unknown): string | null => (typeof x === "string" ? x : null);
const VERIFICATION_BY_ID = new Map<string, GraphVerification>();
for (const r of Array.isArray(rawVerification.records) ? rawVerification.records : []) {
  const rec = r as Record<string, unknown>;
  const status = rec.status as VerificationStatus;
  if (typeof rec.systemId !== "string" || !STATUSES.includes(status)) continue;
  VERIFICATION_BY_ID.set(rec.systemId, {
    status,
    where: rec.where === "abstract" || rec.where === "full_text" ? rec.where : null,
    quote: strOrNull(rec.quote),
    note: strOrNull(rec.note),
    countryAgrees: typeof rec.countryAgrees === "boolean" ? rec.countryAgrees : null,
  });
}

/* ----- Vetted-release membership (graph-vetted.json). Absent id = not determined (null). ----- */
interface RawVettedFile {
  source?: unknown;
  file?: unknown;
  method?: unknown;
  checkedAt?: unknown;
  ids?: unknown;
}
const rawVetted = vettedJson as RawVettedFile;
const VETTED_IDS: Record<string, unknown> =
  rawVetted.ids && typeof rawVetted.ids === "object" ? (rawVetted.ids as Record<string, unknown>) : {};
const vettedFlag = (id: string): boolean | null =>
  typeof VETTED_IDS[id] === "boolean" ? (VETTED_IDS[id] as boolean) : null;

const graphBase = graphJson as GraphDataset;
/** Codon-540 findings checked against their source paper and found mis-extracted (two by a human check
 *  of the abstract plus the vetted CSV, two by the AI-assisted spot-check). Same exclusion as the Data tab
 *  (data/graph-stats.json, marker.associations with vetted: false). Hidden on the map; they stay in
 *  graph-findings.json and in graph-verification.json. Hardcoded on purpose (graph-stats.json is not imported);
 *  scripts/forecast/check-data.mjs fails if this list drifts from that file. Keep the ids on one line. */
export const MIS_EXTRACTED_IDS: ReadonlySet<string> = new Set(["paFNq6MPX5", "AeI-laBxXr", "iD_4aq3uIs", "QIrkddNp_j"]);
export const GRAPH: GraphDataset = {
  ...graphBase,
  findings: graphBase.findings.filter((f) => !MIS_EXTRACTED_IDS.has(f.systemId)).map((f) => ({
    ...f,
    verification: VERIFICATION_BY_ID.get(f.systemId) ?? null,
    inVettedCsv: vettedFlag(f.systemId),
  })),
};

/** Findings that name at least one country (sp, codon540). All per-country and headline counts use these. */
const COUNTRY_FINDINGS: GraphFinding[] = GRAPH.findings.filter((f) => f.countries.length > 0);
/** The Alert tab pack's haplotype findings: they name no country, so they are shown in every panel as not country-specific. */
const GLOBAL_HAPLOTYPE: GraphFinding[] = GRAPH.findings.filter(
  (f) => f.kind === "haplotype" && f.countries.length === 0,
);

const vettedCounts = (fs: GraphFinding[]) => ({
  vetted: fs.filter((f) => f.inVettedCsv === true).length,
  apiOnly: fs.filter((f) => f.inVettedCsv === false).length,
  unknown: fs.filter((f) => f.inVettedCsv == null).length,
});

/** counts: over country-naming findings only. globalHaplotype: the global haplotype findings, counted separately. */
export const GRAPH_VETTED: {
  source: string;
  file: string;
  method: string;
  checkedAt: string;
  counts: { vetted: number; apiOnly: number; unknown: number };
  globalHaplotype: { vetted: number; apiOnly: number; unknown: number };
  note: string;
} = {
  source: strOrNull(rawVetted.source) ?? "",
  file: strOrNull(rawVetted.file) ?? "",
  method: strOrNull(rawVetted.method) ?? "",
  checkedAt: strOrNull(rawVetted.checkedAt) ?? "",
  counts: vettedCounts(COUNTRY_FINDINGS),
  globalHaplotype: vettedCounts(GLOBAL_HAPLOTYPE),
  note: "counts cover findings that name a country. The global haplotype findings name no country and are counted separately.",
};

export function verificationCounts(findings: GraphFinding[]): VerificationCounts {
  const c: VerificationCounts = {
    supported: 0,
    partly_supported: 0,
    contradicted: 0,
    not_verifiable: 0,
    unchecked: 0,
  };
  for (const f of findings) c[f.verification ? f.verification.status : "unchecked"] += 1;
  return c;
}

export const GRAPH_VERIFICATION: GraphVerificationMeta = {
  method: strOrNull(rawVerification.method) ?? "",
  checkedBy: strOrNull(rawVerification.checkedBy) ?? "",
  checkedAt: strOrNull(rawVerification.checkedAt) ?? "",
  scope: strOrNull(rawVerification.scope) ?? "",
  counts: verificationCounts(COUNTRY_FINDINGS), // country-naming findings only; global haplotype findings excluded
};
export const PAPERS: PapersDataset = papersJson as PapersDataset;

/** Genome clock (sample collection year). */
export const GENOME_MIN_YEAR: number = GENOME.minYear;
export const GENOME_MAX_YEAR: number = GENOME.maxYear;
const ALL_CLOCK_YEARS: number[] = [
  GENOME.minYear,
  GENOME.maxYear,
  ...PAPERS.papers.map((p) => p.year),
  ...GRAPH.findings.map((f) => f.paper.year).filter((y): y is number => y !== null),
];
/** Earliest year on any clock (genome collection, paper publication, Graph paper publication). */
export const MIN_YEAR: number = Math.min(...ALL_CLOCK_YEARS);
/** Latest year on any clock. Years after GENOME_MAX_YEAR carry no new genome data. */
export const MAX_YEAR: number = Math.max(...ALL_CLOCK_YEARS);
export const MARKER_ID = "pfdhps-K540E";

const GENOME_BY_ISO: Record<Iso3, GenomeYear[]> = Object.fromEntries(
  GENOME.countries.map((c) => [c.iso3, c.years]),
);

export function clampYear(y: number): number {
  if (!Number.isFinite(y)) return MAX_YEAR;
  return Math.min(MAX_YEAR, Math.max(MIN_YEAR, Math.round(y)));
}

export function genomeSnapshot(iso3: Iso3, asOfYear: number): GenomeSnapshot {
  const all = GENOME_BY_ISO[iso3] ?? [];
  const years = all.filter((y) => y.year <= asOfYear);
  let latest: GenomeYear | null = null;
  let firstTestedYear: number | null = null;
  let firstDetectionYear: number | null = null;
  let totalTested = 0;
  let totalWithE = 0;
  let totalOther = 0;
  for (const y of years) {
    totalTested += y.tested;
    totalWithE += y.withE;
    totalOther += y.other;
    if (y.tested > 0) {
      latest = y;
      if (firstTestedYear === null) firstTestedYear = y.year;
    }
    if (y.withE > 0 && firstDetectionYear === null) firstDetectionYear = y.year;
  }
  const state =
    totalWithE > 0 ? "detected" : totalTested > 0 ? "tested_not_detected" : "not_sampled";
  return {
    iso3,
    asOfYear,
    state,
    years,
    latest,
    firstTestedYear,
    firstDetectionYear,
    totalTested,
    totalWithE,
    totalOther,
  };
}

export function allGenomeSnapshots(asOfYear: number): Record<Iso3, GenomeSnapshot> {
  const out: Record<Iso3, GenomeSnapshot> = {};
  for (const c of GENOME.countries) out[c.iso3] = genomeSnapshot(c.iso3, asOfYear);
  return out;
}

export function genomeChangesInYear(year: number): GenomeChange[] {
  const out: GenomeChange[] = [];
  for (const c of GENOME.countries) {
    const counts = c.years.find((y) => y.year === year);
    if (!counts) continue;
    const before = genomeSnapshot(c.iso3, year - 1);
    if (counts.tested > 0 && before.firstTestedYear === null) {
      out.push({ iso3: c.iso3, year, kind: "first_tested", counts });
    }
    if (counts.withE > 0 && before.firstDetectionYear === null) {
      out.push({ iso3: c.iso3, year, kind: "first_detection", counts });
    }
  }
  return out;
}

function byPaperYear(a: GraphFinding, b: GraphFinding): number {
  const ya = a.paper.year;
  const yb = b.paper.year;
  if (ya === null && yb === null) return a.systemId.localeCompare(b.systemId);
  if (ya === null) return 1;
  if (yb === null) return -1;
  return ya - yb || a.systemId.localeCompare(b.systemId);
}

function visible(f: GraphFinding, asOfYear?: number): boolean {
  return asOfYear === undefined || f.paper.year === null || f.paper.year <= asOfYear;
}

/** The global haplotype findings (no country named), as-of filtered by paper year, sorted like the rest. */
export function globalHaplotypeFindings(asOfYear?: number): GraphFinding[] {
  return GLOBAL_HAPLOTYPE.filter((f) => visible(f, asOfYear)).sort(byPaperYear);
}

/** sp / codon540: findings naming the country. haplotype: the global, not-country-specific findings (same for every country). */
export function graphFindingsFor(
  iso3: Iso3,
  asOfYear?: number,
): { sp: GraphFinding[]; codon540: GraphFinding[]; haplotype: GraphFinding[] } {
  const hits = COUNTRY_FINDINGS.filter(
    (f) => f.countries.some((c) => c.iso3 === iso3) && visible(f, asOfYear),
  ).sort(byPaperYear);
  return {
    sp: hits.filter((f) => f.kind === "sp"),
    codon540: hits.filter((f) => f.kind === "codon540"),
    haplotype: globalHaplotypeFindings(asOfYear),
  };
}

export type GraphCountryCounts = {
  sp: number;
  codon540: number;
  haplotype: number;
  vetted: number; // findings of any kind in System's vetted associations CSV
} & VerificationCounts;

/** Country-naming findings only (global haplotype findings are never counted per country, so haplotype stays 0). */
export function graphCountsByCountry(asOfYear?: number): Record<Iso3, GraphCountryCounts> {
  const out: Record<Iso3, GraphCountryCounts> = {};
  for (const f of COUNTRY_FINDINGS) {
    if (!visible(f, asOfYear)) continue;
    const isos = new Set(f.countries.map((c) => c.iso3));
    for (const iso of isos) {
      const row = (out[iso] ??= {
        sp: 0,
        codon540: 0,
        haplotype: 0,
        vetted: 0,
        supported: 0,
        partly_supported: 0,
        contradicted: 0,
        not_verifiable: 0,
        unchecked: 0,
      });
      row[f.kind] += 1;
      if (f.inVettedCsv === true) row.vetted += 1;
      row[f.verification ? f.verification.status : "unchecked"] += 1;
    }
  }
  return out;
}

export function alertsFor(feed: AlertFeed, iso3: Iso3, asOfYear?: number): AlertRecord[] {
  return feed.alerts
    .filter((a) => a.country_iso3 === iso3 && (asOfYear === undefined || a.year <= asOfYear))
    .sort((a, b) => a.year - b.year || a.id.localeCompare(b.id));
}

/* ===== PAPERS (publication clock) ===== */

function byPublication(a: PaperRecord, b: PaperRecord): number {
  return a.year - b.year || (a.month ?? 0) - (b.month ?? 0) || a.pmid.localeCompare(b.pmid);
}
const papersUpTo = (asOfYear?: number): PaperRecord[] =>
  asOfYear === undefined ? PAPERS.papers : PAPERS.papers.filter((p) => p.year <= asOfYear);

/** Papers that concern the country, published up to asOfYear when given. Sorted by (year, month) ascending. */
export function papersFor(
  iso3: Iso3,
  asOfYear?: number,
): { papers: PaperRecord[]; earliest: PaperRecord | null; readByGraph: number } {
  const papers = papersUpTo(asOfYear)
    .filter((p) => p.countries.includes(iso3))
    .sort(byPublication);
  return {
    papers,
    earliest: papers[0] ?? null,
    readByGraph: papers.filter((p) => p.readByGraph).length,
  };
}

export function papersCountsByCountry(
  asOfYear?: number,
): Record<Iso3, { total: number; readByGraph: number }> {
  const out: Record<Iso3, { total: number; readByGraph: number }> = {};
  for (const p of papersUpTo(asOfYear)) {
    for (const iso of new Set(p.countries)) {
      const row = (out[iso] ??= { total: 0, readByGraph: 0 });
      row.total += 1;
      if (p.readByGraph) row.readByGraph += 1;
    }
  }
  return out;
}

export function papersTotals(asOfYear?: number): { total: number; readByGraph: number } {
  const ps = papersUpTo(asOfYear);
  return { total: ps.length, readByGraph: ps.filter((p) => p.readByGraph).length };
}

/* ===== POLICY MILESTONES (verbatim from the Alert tab's pack; no thresholds or bands defined here) ===== */
export const POLICY_MILESTONES: { source: SourceInfo; items: PolicyMilestone[] } = {
  source: (policyJson as { source: SourceInfo }).source,
  items: [...(policyJson as { items: PolicyMilestone[] }).items].sort((a, b) => a.year - b.year),
};
