/**
 * EVERY user-facing number in the app lives here. Nowhere else.
 *
 * Every figure is read from data/graph-stats.json, the pinned output of
 * scripts/graph-stats.ts. Counts come from the System Public Graph API
 * (https://public-api.system.com/v1, header x-api-key) and are GRAPH_*.
 * Publication dates come from OpenAlex, matched on pubmed_id, and are
 * OPENALEX_*. Nothing is typed in by hand. Each constant carries the exact
 * query it derives from, and its label says which question it answers. To refresh: re-run the script, commit the
 * JSON.
 *
 * "Finding" = one association in the graph (two variables linked by a
 * statistic). Per System's own documentation roughly 20% of API associations
 * are known-bad extractions. Findings found to be mis-extracted are flagged
 * in the pinned file and left out of every count here.
 */
import graph from "@/data/graph-stats.json";

export type Stat = {
  value: number | string;
  /** What the figure is, in plain words. Used as its label. */
  label: string;
  /** Rendered after the value, e.g. "%". */
  unit?: string;
  /** Shown on screen under the figure. */
  source: string;
  /** The exact API query (or queries) the value derives from. */
  query: string;
};

const SOURCE = `System Public Graph v${graph.source.version}`;

/* A finding compared with its paper and found mis-extracted is
 * flagged `vetted: false` in graph-stats.json. It stays in the file but is not
 * evidence: every count and list below leaves it out. */
type Pinned = {
  system_id: string;
  study_id: string;
  pubmed_id?: number | null;
  variable_1_id?: string;
  variable_2_id?: string;
  variable_1_name: string;
  variable_2_name: string;
  vetted?: boolean;
};
const ALL_MARKER = graph.marker.associations as Pinned[];
const MARKER = ALL_MARKER.filter((a) => a.vetted !== false);
const CONTEXT = (graph.pfdhps_context.associations as Pinned[]).filter((a) => a.vetted !== false);
const distinct = (xs: (string | undefined)[]) => new Set(xs.filter(Boolean)).size;
const SEARCHES = graph.searches.map((s) => s.term).join(", ");

/** "2015-06-15" -> "June 15, 2015", without timezone drift. */
export function formatGraphDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const month = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][m - 1];
  return `${month} ${d}, ${y}`;
}

/** Publication dates for the marker's papers, resolved through OpenAlex on
 *  pubmed_id by scripts/graph-stats.ts. The graph itself has no per-finding date. */
const DATES_BY_PMID = new Map(
  graph.marker.publication_dates.map((d) => [String(d.pubmed_id), d.publication_date as string | null]),
);

/** ISO date (YYYY-MM-DD) for a PubMed ID, or null when OpenAlex did not resolve it. */
export function publishedDate(pubmedId: string | number | null | undefined): string | null {
  return pubmedId == null ? null : (DATES_BY_PMID.get(String(pubmedId)) ?? null);
}

const markerDates = MARKER
  .map((a) => publishedDate(a.pubmed_id))
  .filter((d): d is string => d !== null)
  .sort();

/* --------------------------------------- The marker: codon 540 of pfdhps --- */
/* The graph indexes K540E only lightly. The marker's evidence is every
 * variable whose NAME mentions codon 540 (graph.marker.name_pattern): a few
 * name K540E on its own, most name it inside a combination or a list. */

// GET /variables?search=name:<term>&limit=50&offset=<n>&include_total=true
//   for <term> in dhps, pfdhps, dihydropteroate, K540E, 540E, sulfadoxine,
//   sulfadoxine-pyrimethamine; keep hits whose name matches /540\s*E|540\s*K\/E|Glu-540/i
export const GRAPH_MARKER_VARIABLES = {
  value: graph.marker.variables.filter((v) =>
    MARKER.some((a) => a.variable_1_id === v.system_id || a.variable_2_id === v.system_id),
  ).length,
  label: "Graph variables that name codon 540 of pfdhps directly",
  source: SOURCE,
  query: `GET /variables?search=name:<term>&limit=50&offset=<n>&include_total=true (terms: ${SEARCHES}), name-filtered`,
} satisfies Stat;

// For each marker variable:
// GET /variables/{id}/associations?limit=50&offset=<n>&include_total=true
//   de-duplicated by association system_id
export const GRAPH_MARKER_FINDINGS = {
  value: MARKER.length,
  label: "Findings that name codon 540 of pfdhps directly",
  source: SOURCE,
  query: "GET /variables/{id}/associations?limit=50&offset=<n>&include_total=true, per marker variable",
} satisfies Stat;

// Subset of the marker associations (same query) in which a variable names
// K540E on its own: the name matches /K540\s*E/ and names no other codon,
// gene or combination.
const NAMES_K540E_ALONE = (name: string) =>
  /K540\s*E/i.test(name) && !/437|581|51I|59R|108|dhfr|reductase|mutant/i.test(name);
export const GRAPH_MARKER_K540E_ALONE_FINDINGS = {
  value: MARKER.filter(
    (a) => NAMES_K540E_ALONE(a.variable_1_name) || NAMES_K540E_ALONE(a.variable_2_name),
  ).length,
  label: "Findings that name K540E on its own, with no other codon",
  source: SOURCE,
  query: "subset of GET /variables/{id}/associations?limit=50&offset=<n>&include_total=true, per marker variable",
} satisfies Stat;

// Distinct study_id over those associations; each resolved with
// GET /studies/{study_id}
export const GRAPH_MARKER_STUDIES = {
  value: distinct(MARKER.map((a) => a.study_id)),
  label: "Studies that name codon 540 of pfdhps directly",
  source: SOURCE,
  query: "distinct study_id over the marker associations; GET /studies/{study_id}",
} satisfies Stat;

// OpenAlex, not the graph:
// GET https://api.openalex.org/works?filter=pmid:<id>|<id>|...&select=id,doi,ids,publication_date&per-page=50
//   over the pubmed_id of every marker association
export const OPENALEX_MARKER_DATED_FINDINGS = {
  value: markerDates.length,
  label: "Findings that name codon 540 directly and have a resolved publication date",
  source: "OpenAlex",
  query: "GET https://api.openalex.org/works?filter=pmid:<ids>&select=id,doi,ids,publication_date&per-page=50",
} satisfies Stat;

// Latest publication_date over the same OpenAlex response.
export const OPENALEX_MARKER_LAST_PUBLISHED = {
  value: markerDates.length ? formatGraphDate(markerDates[markerDates.length - 1]) : "Date unknown",
  label: "Most recent publication among the findings that name codon 540 directly",
  source: "OpenAlex",
  query: "max publication_date over GET https://api.openalex.org/works?filter=pmid:<ids>&select=id,doi,ids,publication_date&per-page=50",
} satisfies Stat;

// GET /studies/{study_id} for each marker association's study -> study_type.
// Counts the findings whose study has a non-empty study_type.
const STUDY_TYPES = new Map(
  graph.marker.studies.map((s) => [s.study_id, (s.study_type as string | null) || null]),
);
export const GRAPH_MARKER_TYPED_FINDINGS = {
  value: MARKER.filter((a) => STUDY_TYPES.get(a.study_id)).length,
  label: "Findings that name codon 540 directly and whose study type the graph records",
  source: SOURCE,
  query: "GET /studies/{study_id} per marker association; study_type present",
} satisfies Stat;

// Marker associations flagged `vetted: false` in graph-stats.json
// (same query as GRAPH_MARKER_FINDINGS; flagged after a check against the paper).
export const GRAPH_MARKER_EXCLUDED_FINDINGS = {
  value: ALL_MARKER.length - MARKER.length,
  label: "Findings the live API returned for codon 540 that were found mis-extracted and are excluded",
  source: SOURCE,
  query: "GET /variables/{id}/associations?limit=50&offset=<n>&include_total=true, per marker variable; vetted = false",
} satisfies Stat;

/* ------------------------------------------------- Context: pfdhps overall --- */
/* Variables whose name explicitly identifies the P. falciparum dhps gene
 * (graph.pfdhps_context.selection_rule). Includes the marker set. */

// Same searches as above, name-filtered to P. falciparum dhps; then
// GET /variables/{id}/associations?limit=50&offset=<n>&include_total=true
//   per variable, de-duplicated by association system_id
export const GRAPH_PFDHPS_FINDINGS = {
  value: CONTEXT.length,
  label: "Findings that cover pfdhps overall, any alteration",
  source: SOURCE,
  query: "GET /variables/{id}/associations?limit=50&offset=<n>&include_total=true, per pfdhps variable",
} satisfies Stat;

// Distinct study_id over those associations.
export const GRAPH_PFDHPS_STUDIES = {
  value: distinct(CONTEXT.map((a) => a.study_id)),
  label: "Studies that cover pfdhps overall, any alteration",
  source: SOURCE,
  query: "distinct study_id over the pfdhps associations",
} satisfies Stat;

/* ------------------------------------------------------- The graph itself --- */
/* Release metadata recorded in graph-stats.json `source`. These describe the
 * dataset (DOI 10.7910/DVN/7V6JDO); the API does not return them. */

export const GRAPH_VERSION = {
  value: graph.source.version,
  label: "System Public Graph version",
  source: `System Public Graph, doi:${graph.source.doi}`,
  query: "release metadata (graph-stats.json source.version); not an API field",
} satisfies Stat;

export const GRAPH_SNAPSHOT_DATE = {
  value: formatGraphDate(graph.source.snapshot),
  label: "System Public Graph snapshot date",
  source: `System Public Graph, doi:${graph.source.doi}`,
  query: "release metadata (graph-stats.json source.snapshot); not an API field",
} satisfies Stat;

export const GRAPH_KNOWN_BAD_SHARE = {
  value: graph.source.documented_known_bad_extraction_share_percent,
  unit: "%",
  label: "Approximate share of API associations that are known-bad extractions",
  source: "System API documentation",
  query: "documented by System (graph-stats.json source.documented_known_bad_extraction_share_percent); not an API field",
} satisfies Stat;

export const GRAPH_LICENSE = graph.source.license;
export const GRAPH_DOI = graph.source.doi;

/** Full registry, for the Data tab and any audit view. */
export const ALL_STATS = {
  GRAPH_MARKER_VARIABLES,
  GRAPH_MARKER_FINDINGS,
  GRAPH_MARKER_K540E_ALONE_FINDINGS,
  GRAPH_MARKER_EXCLUDED_FINDINGS,
  GRAPH_MARKER_TYPED_FINDINGS,
  GRAPH_MARKER_STUDIES,
  OPENALEX_MARKER_DATED_FINDINGS,
  OPENALEX_MARKER_LAST_PUBLISHED,
  GRAPH_PFDHPS_FINDINGS,
  GRAPH_PFDHPS_STUDIES,
  GRAPH_VERSION,
  GRAPH_SNAPSHOT_DATE,
  GRAPH_KNOWN_BAD_SHARE,
} as const;
