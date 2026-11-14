/**
 * The demo marker's findings, straight from data/graph-stats.json (pinned
 * output of scripts/graph-stats.ts). Every finding keeps its system_id,
 * pubmed_id and doi so a reader can always click through to the paper.
 */
import graph from "@/data/graph-stats.json";
// Read-only: the AI-assisted spot-check of graph findings against their papers
// (owned by the Map tab). We read statuses from it; we never write to it.
import verification from "@/data/forecast/graph-verification.json";
import { publishedDate } from "@/lib/stats";

export type MarkerFinding = {
  systemId: string;
  studyId: string;
  pubmedId: string | null;
  doi: string | null;
  variable1: string;
  variable2: string;
  variable1Id: string;
  variable2Id: string;
  statisticType: string;
  /** The statistic's value exactly as the graph records it; null if absent. */
  statisticValue: number | null;
  population: string | null;
  /** study_type exactly as the graph's Studies table records it; null = not recorded. */
  studyType: string | null;
  /** Why a `vetted: false` finding was excluded, and how that was found. */
  vettingNote: string | null;
  vettingMethod: "source_abstract_check_and_vetted_csv" | "ai_assisted_spot_check" | null;
  /** Result of the AI-assisted spot-check against the paper, if it covered this finding. */
  spotCheck: { status: string; where: string; note: string } | null;
  /** ISO publication date (YYYY-MM-DD) of the paper, from OpenAlex; null = unknown. */
  published: string | null;
};

type RawAssociation = {
  system_id: string;
  study_id: string;
  pubmed_id?: number | null;
  variable_1_name: string;
  variable_2_name: string;
  variable_1_id: string;
  variable_2_id: string;
  statistic_type: string;
  statistic_value?: number | null;
  vetted?: boolean;
  vetting_note?: string;
  vetting_method?: string;
};

type SpotRecord = { systemId: string; status: string; where?: string; note?: string };
const SPOT = new Map(((verification as { records?: SpotRecord[] }).records ?? []).map((r) => [r.systemId, r]));

/** How the spot-check describes itself, in its own words. */
export const SPOT_CHECK = {
  checkedBy: String((verification as { checkedBy?: string }).checkedBy ?? "AI-assisted spot-check; not reviewed by a human"),
};

/** "partly_supported" -> "partly supported" */
export const spotStatusLabel = (status: string) => status.replaceAll("_", " ");

const studies = new Map(graph.marker.studies.map((s) => [s.study_id, s]));

const toFinding = (a: RawAssociation): MarkerFinding => {
    const study = studies.get(a.study_id);
    const pmid = a.pubmed_id ?? study?.pubmed_id ?? null;
    return {
      systemId: a.system_id,
      studyId: a.study_id,
      pubmedId: pmid === null ? null : String(pmid),
      doi: study?.doi ?? null,
      variable1: a.variable_1_name,
      variable2: a.variable_2_name,
      variable1Id: a.variable_1_id,
      variable2Id: a.variable_2_id,
      statisticValue: typeof a.statistic_value === "number" ? a.statistic_value : null,
      statisticType: a.statistic_type.replaceAll("_", " "),
      population: study?.population ?? null,
      studyType: (study?.study_type as string | null | undefined)?.trim() || null,
      vettingNote: a.vetting_note ?? null,
      vettingMethod: (a.vetting_method as MarkerFinding["vettingMethod"]) ?? null,
      spotCheck: SPOT.has(a.system_id)
        ? {
            status: SPOT.get(a.system_id)!.status,
            where: SPOT.get(a.system_id)!.where ?? "",
            note: SPOT.get(a.system_id)!.note ?? "",
          }
        : null,
      published: publishedDate(pmid),
    };
};

const RAW = graph.marker.associations as RawAssociation[];

/** Findings flagged `vetted: false`: compared with the paper and found
 *  mis-extracted. Kept in the pinned file, never shown as evidence. */
export const EXCLUDED_FINDINGS: MarkerFinding[] = RAW.filter((a) => a.vetted === false).map(toFinding);

/** The marker's evidence. Dated findings first, oldest to newest; then any
 *  with no resolved date. Excludes anything flagged `vetted: false`. */
export const MARKER_FINDINGS: MarkerFinding[] = RAW.filter((a) => a.vetted !== false)
  .map(toFinding)
  .sort((a, b) => {
    if (a.published && b.published) return a.published.localeCompare(b.published);
    if (a.published) return -1;
    if (b.published) return 1;
    return Number(a.pubmedId ?? 0) - Number(b.pubmedId ?? 0) || a.systemId.localeCompare(b.systemId);
  });

/** How many of the findings shown carry each spot-check status. */
export const SPOT_CHECK_COUNTS = {
  shown: MARKER_FINDINGS.length,
  covered: MARKER_FINDINGS.filter((f) => f.spotCheck).length,
  supported: MARKER_FINDINGS.filter((f) => f.spotCheck?.status === "supported").length,
  partlySupported: MARKER_FINDINGS.filter((f) => f.spotCheck?.status === "partly_supported").length,
};
