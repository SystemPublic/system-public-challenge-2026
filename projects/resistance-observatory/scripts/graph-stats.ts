/**
 * Pulls the pinned figures for the demo marker (pfdhps K540E / sulfadoxine)
 * from the System Public Graph API and writes data/graph-stats.json.
 *
 * Server-side only. Never import this from app code.
 *
 *   node --env-file=.env.local scripts/graph-stats.ts
 *
 * (Node >= 22.18 runs .ts directly; `npx tsx --env-file=.env.local ...` also
 * works.) The key is read from SYSTEM_API_KEY and is never logged or written.
 *
 * API: https://public-api.system.com/v1, header x-api-key. `limit` is always
 * set explicitly (the default is 10). Pipes in relationship_id are sent as %7C.
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const BASE = "https://public-api.system.com/v1";
const KEY = process.env.SYSTEM_API_KEY;
if (!KEY && process.env.VERIFY_ONLY !== "1") {
  console.error("SYSTEM_API_KEY is not set. Run with --env-file=.env.local");
  process.exit(1);
}

const SEARCH_TERMS = [
  "dhps",
  "pfdhps",
  "dihydropteroate",
  "K540E",
  "540E",
  "sulfadoxine",
  "sulfadoxine-pyrimethamine",
];
const PAGE = 50;
/** Cap on search hits kept per term (each hit costs one count request). */
const MAX_HITS_PER_TERM = 200;
const MAX_ASSOCIATIONS = 200;
const MAX_RELATIONSHIPS = 200;
/**
 * The demo marker is codon 540 of pfdhps. `search=name:K540E` returns nothing
 * (names are written "A437G/K540E", "K540 E:", "540K/E", "Glu-540"), so the
 * marker's variables are picked from all search hits by variable NAME TEXT,
 * as docs/SCIENCE.md instructs ("match on variable name text as well as
 * concept ID").
 */
const MARKER_NAME_PATTERN = /540\s*E|540\s*K\/E|Glu-540/i;
/**
 * Wider context set: variables whose NAME explicitly identifies the
 * P. falciparum dhps gene. Either it says "pfdhps", or it says dhps /
 * dihydropteroate together with "falciparum" or a pfdhps codon (437, 540,
 * 581). This deliberately drops everything the name does not tie to malaria:
 * the 16-DHPS steroid, dihydropyridines ("DHPs"), dental health professionals,
 * Pneumocystis / P. carinii DHPS, and bare "DHPS mutations" variables.
 */
const isPfdhpsName = (name: string) =>
  /pfdhps/i.test(name) ||
  (/dhps|dihydropteroate/i.test(name) && /falciparum|437|540|581/i.test(name) && !/carinii|pneumocystis/i.test(name));
/**
 * The graph has no per-finding publication date, so the marker findings' dates
 * are resolved through OpenAlex from each finding's pubmed_id (batched, one
 * request per 50 ids). Set OPENALEX_MAILTO in .env.local to join OpenAlex's
 * polite pool; the address is sent to OpenAlex only and is never written to
 * the output file.
 */
const OPENALEX = "https://api.openalex.org";
const OPENALEX_MAILTO = process.env.OPENALEX_MAILTO;
/**
 * Verification layer: System's vetted release of the graph on Harvard
 * Dataverse (doi:10.7910/DVN/7V6JDO). The live API serves more associations
 * than the vetted associations CSV holds, so every finding this script pins is
 * looked up in that CSV by system_id and gets `in_vetted_csv: true | false`.
 * The file is ~440 MB and is streamed, not saved. Set SKIP_VETTED_CSV=1 to
 * skip the download (the field is then null).
 */
const VETTED_CSV = {
  doi: "10.7910/DVN/7V6JDO",
  filename: "system-public-graph-v1-associations.csv",
  url: "https://dataverse.harvard.edu/api/access/datafile/14061020",
};

/**
 * Findings checked against the source paper and found to be mis-extracted,
 * with the method that found each one. They stay in the output, flagged `vetted: false`, and the app
 * excludes them from every count and list presented as evidence.
 */
type Flag = {
  note: string;
  /** How the mis-extraction was found. */
  method: "source_abstract_check_and_vetted_csv" | "ai_assisted_spot_check";
};
const TAYLOR_NOTE =
  "Mis-extraction (PMID 25564249). Checked against the source abstract: the prevalence ratio recorded here belongs to the A581G sextuple mutant, not to K540E; K540E appears in that sentence only as a proxy definition. Not in System's vetted Dataverse CSV.";
const MIS_EXTRACTED: Record<string, Flag> = {
  paFNq6MPX5: { note: TAYLOR_NOTE, method: "source_abstract_check_and_vetted_csv" },
  "AeI-laBxXr": { note: TAYLOR_NOTE, method: "source_abstract_check_and_vetted_csv" },
  iD_4aq3uIs: {
    note: "Mis-extraction (PMID 29854394). Found by an AI-assisted spot-check against the PubMed abstract (data/forecast/graph-verification.json), not reviewed by a human; the abstract was re-read when this flag was set. The abstract reports no difference in the antifolate SNPs 51I, 59R, 108N or 540E (P > 0.05). The -41.3 recorded here equals the drop the abstract gives for a different, non-antifolate marker (97.3% to 56.0%).",
    method: "ai_assisted_spot_check",
  },
  QIrkddNp_j: {
    note: "Mis-extraction (PMID 16023986). Found by an AI-assisted spot-check against the PubMed abstract (data/forecast/graph-verification.json), not reviewed by a human; the abstract was re-read when this flag was set. The abstract gives OR 24.72 (95% CI 8.24-74.15) for the dhfr+dhps quintuple mutant in both younger and older children, not for the triple-or-double mutants in children under 5 that this finding names.",
    method: "ai_assisted_spot_check",
  },
};

/** Streams the vetted CSV and returns which of `ids` appear as a row's system_id. */
async function idsInVettedCsv(ids: Set<string>): Promise<Set<string>> {
  const found = new Set<string>();
  const res = await fetch(VETTED_CSV.url);
  if (!res.ok || !res.body) throw new Error(`Dataverse ${res.status}`);
  const decoder = new TextDecoder();
  let tail = "";
  for await (const chunk of res.body as unknown as AsyncIterable<Uint8Array>) {
    const lines = (tail + decoder.decode(chunk, { stream: true })).split("\n");
    tail = lines.pop() ?? "";
    for (const line of lines) {
      const comma = line.indexOf(",");
      if (comma === 10 && ids.has(line.slice(0, 10))) found.add(line.slice(0, 10));
    }
  }
  return found;
}

const OUT = resolve(import.meta.dirname, "..", "data", "graph-stats.json");

type Json = Record<string, unknown>;
let requests = 0;

async function get(path: string): Promise<Json> {
  for (let attempt = 0; ; attempt++) {
    requests++;
    const res = await fetch(BASE + path, { headers: { "x-api-key": KEY as string } });
    if (res.ok) return (await res.json()) as Json;
    if ((res.status === 429 || res.status >= 500) && attempt < 4) {
      await new Promise((r) => setTimeout(r, 1000 * 2 ** attempt));
      continue;
    }
    throw new Error(`GET ${path} -> ${res.status} ${(await res.text()).slice(0, 200)}`);
  }
}

/** Offset pagination; stops at `max`, on a short page, or if a page repeats. */
async function paged(path: string, max: number): Promise<{ rows: Json[]; total: number | null; truncated: boolean }> {
  const rows: Json[] = [];
  const seen = new Set<string>();
  let total: number | null = null;
  const sep = path.includes("?") ? "&" : "?";
  for (let offset = 0; offset < max; offset += PAGE) {
    const page = await get(`${path}${sep}limit=${PAGE}&offset=${offset}&include_total=true`);
    const data = (page.data as Json[]) ?? [];
    if (typeof page.total === "number") total = page.total;
    const fresh = data.filter((d) => {
      const id = String(d.system_id ?? d.relationship_id ?? d.study_id ?? JSON.stringify(d));
      if (seen.has(id)) return false;
      seen.add(id);
      return true;
    });
    rows.push(...fresh);
    if (data.length < PAGE || fresh.length === 0) return { rows, total, truncated: false };
  }
  return { rows: rows.slice(0, max), total, truncated: true };
}

async function pool<T, R>(items: T[], size: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(items.length);
  let next = 0;
  await Promise.all(
    Array.from({ length: Math.min(size, items.length) }, async () => {
      while (next < items.length) {
        const i = next++;
        out[i] = await fn(items[i]);
      }
    }),
  );
  return out;
}

/** Step 9. Annotates each pinned finding in place and returns the summary block. */
async function verify(pinned: Json[]) {
  const skipCsv = process.env.SKIP_VETTED_CSV === "1";
  const ids = new Set(pinned.map((a) => String(a.system_id)));
  const inCsv = skipCsv ? null : await idsInVettedCsv(ids);
  for (const a of pinned) {
    const id = String(a.system_id);
    a.in_vetted_csv = inCsv ? inCsv.has(id) : null;
    if (MIS_EXTRACTED[id]) {
      a.vetted = false;
      a.vetting_note = MIS_EXTRACTED[id].note;
      a.vetting_method = MIS_EXTRACTED[id].method;
    }
  }
  if (inCsv) console.log(`vetted CSV: ${inCsv.size} of ${ids.size} pinned findings present`);
  return {
    vetted_csv: VETTED_CSV,
    vetted_csv_checked: !skipCsv,
    verified_at: new Date().toISOString(),
    note: "in_vetted_csv says whether a finding's system_id is a row in the vetted associations CSV. That CSV holds only associations whose two variables are both grounded to a concept, so false is conclusive only for those. vetted: false marks a finding compared with its source paper and found mis-extracted; vetting_method says how it was found, and vetting_note says what was wrong.",
  };
}

async function main() {
  /* VERIFY_ONLY=1: re-run only the verification step on the pinned file,
   * without calling the System API. */
  if (process.env.VERIFY_ONLY === "1") {
    const pinnedFile = JSON.parse(readFileSync(OUT, "utf8"));
    pinnedFile.verification = await verify([
      ...pinnedFile.marker.associations,
      ...pinnedFile.pfdhps_context.associations,
    ]);
    writeFileSync(OUT, JSON.stringify(pinnedFile, null, 2) + "\n");
    console.log(`verified ${OUT}`);
    return;
  }

  /* 1 — variable search, one term at a time (only `name` is searchable). */
  const searches: Json[] = [];
  const variables = new Map<string, { system_id: string; name: string; concept_id: string | null; matched_terms: string[] }>();
  for (const term of SEARCH_TERMS) {
    const path = `/variables?search=name:${encodeURIComponent(term)}`;
    const { rows, truncated } = await paged(path, MAX_HITS_PER_TERM);
    searches.push({
      term,
      query: `GET ${path}&limit=${PAGE}&offset=<n>&include_total=true`,
      hits: rows.length,
      truncated_at_cap: truncated,
    });
    for (const r of rows) {
      const id = String(r.system_id);
      const v = variables.get(id) ?? {
        system_id: id,
        name: String(r.name),
        concept_id: (r.concept_id as string | undefined) ?? null,
        matched_terms: [],
      };
      v.matched_terms.push(term);
      variables.set(id, v);
    }
    console.log(`search ${term}: ${rows.length} hits${truncated ? " (capped)" : ""}`);
  }

  /* 2 — association count per hit. */
  const counted = await pool([...variables.values()], 6, async (v) => {
    const r = await get(`/variables/${encodeURIComponent(v.system_id)}/associations?limit=1&include_total=true`);
    return { ...v, association_count: typeof r.total === "number" ? r.total : 0 };
  });
  counted.sort((a, b) => b.association_count - a.association_count || a.system_id.localeCompare(b.system_id));

  /* 3 — highest-count pfdhps variable, and its associations. */
  const pfdhps = counted.filter((v) => /pfdhps/i.test(v.name));
  const top = pfdhps[0];
  if (!top) throw new Error("No variable with 'pfdhps' in its name was returned.");
  console.log(`top pfdhps variable: ${top.system_id} "${top.name}" (${top.association_count} associations)`);

  const assocPath = `/variables/${encodeURIComponent(top.system_id)}/associations`;
  const assoc = await paged(assocPath, MAX_ASSOCIATIONS);

  /* 4 — concept relationships (num_findings, num_studies, last_published_date). */
  let concept: Json | null = null;
  let relationships: Json[] = [];
  let relationshipsTruncated = false;
  let relationshipsTotal: number | null = null;
  if (top.concept_id) {
    const cid = encodeURIComponent(top.concept_id);
    concept = await get(`/concepts/${cid}`);
    const rel = await paged(`/concepts/${cid}/relationships`, MAX_RELATIONSHIPS);
    relationshipsTruncated = rel.truncated;
    relationshipsTotal = rel.total;
    relationships = rel.rows.map((r) => ({
      relationship_id: r.relationship_id,
      // Path-safe form: pipes must be sent as %7C.
      relationship_path: `/relationships/${String(r.relationship_id).replaceAll("|", "%7C")}`,
      num_findings: r.num_findings,
      num_studies: r.num_studies,
      last_published_date: r.last_published_date,
      last_updated: r.last_updated,
      source_concept: pickConcept(r.source_concept as Json),
      target_concept: pickConcept(r.target_concept as Json),
    }));
  }

  /* 5 — linked studies: doi, pubmed_id, study_type. */
  const studyIds = [...new Set(assoc.rows.map((a) => a.study_id).filter(Boolean).map(String))];
  const studies = await pool(studyIds, 6, async (id) => {
    const s = await get(`/studies/${encodeURIComponent(id)}`);
    return {
      study_id: String(s.study_id ?? id),
      doi: (s.doi as string | null) ?? null,
      pubmed_id: s.pubmed_id ?? null,
      study_type: (s.study_type as string | null) ?? null,
      population: (s.population as string | null) ?? null,
    };
  });

  /* 6 — the marker itself: every hit whose name text names codon 540. */
  const markerVars = counted.filter((v) => MARKER_NAME_PATTERN.test(v.name));
  const markerAssoc: Json[] = [];
  for (const v of markerVars) {
    const a = await paged(`/variables/${encodeURIComponent(v.system_id)}/associations`, MAX_ASSOCIATIONS);
    for (const row of a.rows) {
      if (!markerAssoc.some((m) => m.system_id === row.system_id)) {
        markerAssoc.push({ ...row, marker_variable_id: v.system_id });
      }
    }
  }
  // The graph dates findings only at relationship level (last_published_date).
  // A relationship exists when both variables of an association are grounded.
  const relCache = new Map<string, Json | null>();
  for (const a of markerAssoc) {
    const c1 = a.variable_1_concept_id as string | undefined;
    const c2 = a.variable_2_concept_id as string | undefined;
    a.relationship = null;
    if (!c1 || !c2) continue;
    for (const id of [`${c1}|${c2}`, `${c2}|${c1}`]) {
      if (!relCache.has(id)) {
        try {
          const r = await get(`/relationships/${id.replaceAll("|", "%7C")}`);
          relCache.set(id, {
            relationship_id: r.relationship_id,
            query: `GET /relationships/${id.replaceAll("|", "%7C")}`,
            num_findings: r.num_findings,
            num_studies: r.num_studies,
            last_published_date: r.last_published_date,
            source_concept: pickConcept(r.source_concept as Json),
            target_concept: pickConcept(r.target_concept as Json),
          });
        } catch {
          relCache.set(id, null);
        }
      }
      if (relCache.get(id)) {
        a.relationship = relCache.get(id);
        break;
      }
    }
  }
  const markerStudyIds = [...new Set(markerAssoc.map((a) => a.study_id).filter(Boolean).map(String))];
  const markerStudies = await pool(markerStudyIds, 6, async (id) => {
    const s = await get(`/studies/${encodeURIComponent(id)}`);
    return {
      study_id: String(s.study_id ?? id),
      doi: (s.doi as string | null) ?? null,
      pubmed_id: s.pubmed_id ?? null,
      study_type: (s.study_type as string | null) ?? null,
      population: (s.population as string | null) ?? null,
    };
  });
  // Concept-level rollup for the marker variable with the most associations
  // that is grounded to a concept.
  const groundedMarker = markerVars.find((v) => v.concept_id);
  let markerConcept: Json | null = null;
  let markerConceptRels: Json[] = [];
  if (groundedMarker?.concept_id) {
    const cid = encodeURIComponent(groundedMarker.concept_id);
    markerConcept = await get(`/concepts/${cid}`);
    const rel = await paged(`/concepts/${cid}/relationships`, MAX_RELATIONSHIPS);
    markerConceptRels = rel.rows.map((r) => ({
      relationship_id: r.relationship_id,
      num_findings: r.num_findings,
      num_studies: r.num_studies,
      last_published_date: r.last_published_date,
      source_concept: pickConcept(r.source_concept as Json),
      target_concept: pickConcept(r.target_concept as Json),
    }));
  }
  /* 7 — wider pfdhps context set (includes the marker set). */
  const contextVars = counted.filter((v) => isPfdhpsName(v.name) || MARKER_NAME_PATTERN.test(v.name));
  const contextAssoc = new Map<string, Json>();
  for (const v of contextVars) {
    const a = await paged(`/variables/${encodeURIComponent(v.system_id)}/associations`, MAX_ASSOCIATIONS);
    for (const row of a.rows) {
      contextAssoc.set(String(row.system_id), {
        system_id: row.system_id,
        variable_1_name: row.variable_1_name,
        variable_2_name: row.variable_2_name,
        study_id: row.study_id,
        pubmed_id: row.pubmed_id ?? null,
        statistic_type: row.statistic_type,
      });
    }
  }
  const contextStudyIds = [...new Set([...contextAssoc.values()].map((a) => a.study_id).filter(Boolean).map(String))];
  /* 8 — publication dates for the marker findings, from OpenAlex. */
  const markerPmids = [...new Set(markerAssoc.map((a) => a.pubmed_id).filter(Boolean).map(String))];
  const publicationDates: Json[] = [];
  for (let i = 0; i < markerPmids.length; i += 50) {
    const batch = markerPmids.slice(i, i + 50);
    const qs = `filter=pmid:${batch.join("|")}&select=id,doi,ids,publication_date&per-page=50`;
    const res = await fetch(`${OPENALEX}/works?${qs}${OPENALEX_MAILTO ? `&mailto=${encodeURIComponent(OPENALEX_MAILTO)}` : ""}`);
    if (!res.ok) throw new Error(`OpenAlex ${res.status} ${(await res.text()).slice(0, 200)}`);
    const works = ((await res.json()) as { results: Json[] }).results;
    for (const pmid of batch) {
      const w = works.find((x) => String((x.ids as Json | undefined)?.pmid ?? "").endsWith(`/${pmid}`));
      publicationDates.push({
        pubmed_id: Number(pmid),
        publication_date: (w?.publication_date as string | undefined) ?? null,
        openalex_id: (w?.id as string | undefined) ?? null,
        openalex_doi: (w?.doi as string | undefined) ?? null,
      });
    }
  }
  console.log(`openalex: ${publicationDates.filter((d) => d.publication_date).length}/${markerPmids.length} marker PubMed IDs dated`);

  console.log(`pfdhps context: ${contextVars.length} variables, ${contextAssoc.size} associations, ${contextStudyIds.length} studies`);
  console.log(`marker: ${markerVars.length} variables, ${markerAssoc.length} associations, ${markerStudies.length} studies`);

  /* 9 — verification: vetted-CSV membership and human review flags. */
  const verification = await verify([...markerAssoc, ...contextAssoc.values()]);

  const out = {
    source: {
      name: "System Public Graph",
      version: "2.1",
      snapshot: "2026-07-01",
      license: "CC BY-NC 4.0",
      doi: "10.7910/DVN/7V6JDO",
      api_base: BASE,
      // From System's API documentation, not from an API response.
      documented_known_bad_extraction_share_percent: 20,
    },
    verification,
    generated_at: new Date().toISOString(),
    generated_by: "scripts/graph-stats.ts",
    requests_made: 0,
    searches,
    variables: counted,
    top_pfdhps_variable: {
      ...top,
      selection_rule: "highest association_count among search hits whose name contains 'pfdhps' (case-insensitive); ties broken by system_id",
      associations_query: `GET ${assocPath}?limit=${PAGE}&offset=<n>&include_total=true`,
      associations_total: assoc.total,
      associations_truncated: assoc.truncated,
    },
    associations: assoc.rows,
    concept,
    concept_relationships_query: top.concept_id
      ? `GET /concepts/${top.concept_id}/relationships?limit=${PAGE}&offset=<n>&include_total=true`
      : null,
    concept_relationships_total: relationshipsTotal,
    concept_relationships_truncated: relationshipsTruncated,
    concept_relationships: relationships,
    studies_query: "GET /studies/{study_id}",
    studies,
    marker: {
      id: "pfdhps-K540E",
      drug: "sulfadoxine (with pyrimethamine, as SP)",
      name_pattern: MARKER_NAME_PATTERN.source,
      selection_rule:
        "every variable returned by the searches above whose name matches name_pattern (case-insensitive); associations fetched per variable with GET /variables/{id}/associations?limit=50&offset=<n>&include_total=true and de-duplicated by system_id",
      variables: markerVars,
      associations: markerAssoc,
      studies: markerStudies,
      publication_dates_source: {
        name: "OpenAlex",
        license: "CC0",
        query: `GET ${OPENALEX}/works?filter=pmid:<id>|<id>|...&select=id,doi,ids,publication_date&per-page=50`,
        note: "One date per paper, matched on pubmed_id. A null publication_date means OpenAlex returned no work for that PubMed ID.",
      },
      publication_dates: publicationDates,
      grounded_variable_id: groundedMarker?.system_id ?? null,
      concept: markerConcept,
      concept_relationships_query: groundedMarker?.concept_id
        ? `GET /concepts/${groundedMarker.concept_id}/relationships?limit=${PAGE}&offset=<n>&include_total=true`
        : null,
      concept_relationships: markerConceptRels,
    },
    pfdhps_context: {
      selection_rule:
        "every variable returned by the searches above whose name contains 'pfdhps', or contains dhps/dihydropteroate together with 'falciparum' or a pfdhps codon (437, 540, 581) and not carinii/pneumocystis; plus the marker variables. Associations fetched per variable with GET /variables/{id}/associations?limit=50&offset=<n>&include_total=true and de-duplicated by system_id; studies are distinct study_id values.",
      variables: contextVars,
      associations: [...contextAssoc.values()],
      study_ids: contextStudyIds,
    },
  };
  out.requests_made = requests;

  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, JSON.stringify(out, null, 2) + "\n");
  console.log(`wrote ${OUT} (${requests} requests)`);
}

function pickConcept(c: Json | undefined) {
  return c ? { system_id: c.system_id, wikidata_label: c.wikidata_label, wikidata_id: c.wikidata_id } : null;
}

main().catch((e) => {
  console.error(e instanceof Error ? e.message : e);
  process.exit(1);
});
