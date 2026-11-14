/**
 * Live window onto the System Public Graph API (v1, beta). Server-side only:
 * the key is read from the environment and never reaches the browser. This is
 * not an open proxy: only the fixed questions below are allowed.
 *
 *   ?op=status                 is a key configured?
 *   ?op=finding&id=<id>        one finding by System id, live values
 *   ?op=paper&pmid=<pmid>      has the graph read this paper, and what did it extract?
 *   ?op=coverage               the in-graph papers of the data pack, confirmed live, with a quarantine count
 *   ?op=studies&pmids=a,b,c    which of these papers the live graph holds now
 *   ?op=probe&q=<text>         does any graph variable name this text?
 *   ?op=concept&id=<id>        a concept's relationships, most findings first
 *
 * Every response carries { live }. live:false means "use the snapshot": no
 * key, or the call failed. Roughly a fifth of API associations are known-bad
 * extractions (System's own documentation), so every association returned is
 * tagged `vetted` against the data pack's vetted id list; the UI hides the
 * unvetted ones and counts them.
 *
 * Responses are cached in memory (the graph is a periodic snapshot; the daily
 * request allowance is finite).
 */
import { NextResponse } from "next/server";
import { loadPack, vettedIds } from "@/lib/alert/loadPack";
import { EXCLUDED_AFTER_CHECK } from "@/lib/alert/receipt";

export const dynamic = "force-dynamic";

const BASE = "https://public-api.system.com";
const TTL_MS = 6 * 60 * 60 * 1000;
const ID = /^[A-Za-z0-9_-]{4,40}$/;

const key = () =>
  (process.env.SYSTEM_API_KEY || process.env.system_public_API_key || process.env.SYSTEM_PUBLIC_API_KEY || "").trim();

type Cached = { at: number; value: unknown };
const cache = new Map<string, Cached>();

async function call(pathAndQuery: string): Promise<unknown> {
  const hit = cache.get(pathAndQuery);
  if (hit && Date.now() - hit.at < TTL_MS) return hit.value;
  // The API is a beta and has transient 5xx spells: try twice, then fall back
  // to an older answer if we have one. Failures are never cached.
  let lastError: unknown;
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const res = await fetch(BASE + pathAndQuery, {
        headers: { "x-api-key": key() },
        signal: AbortSignal.timeout(12000),
        cache: "no-store",
      });
      if (res.status === 404) {
        cache.set(pathAndQuery, { at: Date.now(), value: null });
        return null;
      }
      if (!res.ok) throw new Error(`System API returned HTTP ${res.status}`);
      const value: unknown = await res.json();
      cache.set(pathAndQuery, { at: Date.now(), value });
      return value;
    } catch (e) {
      lastError = e;
      if (attempt === 0) await new Promise((r) => setTimeout(r, 400));
    }
  }
  if (hit) return hit.value;
  throw lastError;
}

type Assoc = Record<string, unknown> & { system_id?: string };
type List<T> = { data?: T[]; total?: number };

type Study = { study_id?: string; doi?: string; population?: string };

/**
 * Has the graph read this paper, and what did it extract? Only associations
 * whose id is in the vetted list are returned; the rest are counted as
 * quarantined and never sent to the browser.
 */
async function paperLive(pmid: string) {
  const studies = (await call(`/v1/studies?filter=pubmed_id:${pmid}&limit=5`)) as List<Study> | null;
  const study = studies?.data?.[0];
  if (!study?.study_id) return { inGraph: false, study: null as Study | null, findings: [] as Assoc[], total: 0, quarantined: 0 };
  // Never pass `fields` to an associations endpoint: the beta API answers 500.
  const assoc = (await call(
    `/v1/studies/${encodeURIComponent(study.study_id)}/associations?limit=50&include_total=true`,
  )) as List<Assoc> | null;
  const tagged = await tag(assoc?.data ?? []);
  const findings = tagged.filter((a) => a.vetted === true);
  return { inGraph: true, study, findings, total: assoc?.total ?? tagged.length, quarantined: tagged.length - findings.length };
}

async function tag(list: Assoc[]) {
  const vetted = await vettedIds();
  return list.map((a) => ({ ...a, vetted: vetted ? vetted.has(String(a.system_id)) && !(String(a.system_id) in EXCLUDED_AFTER_CHECK) : null }));
}

type Concept = { system_id?: string; wikidata_label?: string };
type Relationship = {
  relationship_id?: string;
  num_findings?: number;
  num_studies?: number;
  last_published_date?: string | null;
  source_concept?: Concept;
  target_concept?: Concept;
};

async function answer(op: string, q: URLSearchParams): Promise<unknown> {
  switch (op) {
    case "finding": {
      const id = q.get("id") ?? "";
      if (!ID.test(id)) throw new BadRequest("id");
      const a = (await call(`/v1/associations/${encodeURIComponent(id)}`)) as Assoc | null;
      const t = a ? (await tag([a]))[0] : null;
      // An id outside the vetted set is reported as such, without its values.
      return { found: Boolean(a), vetted: t?.vetted ?? null, finding: t && t.vetted === true ? t : null };
    }
    case "paper": {
      const pmid = q.get("pmid") ?? "";
      if (!/^\d{1,9}$/.test(pmid)) throw new BadRequest("pmid");
      return { pmid, ...(await paperLive(pmid)) };
    }
    case "coverage": {
      // The papers the data pack flags as in the graph: confirm each live and split
      // what the API returns into vetted (shown) and quarantined (counted only).
      const pack = await loadPack();
      const pmids = (pack?.literature.papers ?? []).filter((p) => p.in_graph).map((p) => String(p.pmid));
      const papers = [];
      for (const pmid of pmids) {
        const r = await paperLive(pmid);
        papers.push({ pmid, inGraph: r.inGraph, studyId: r.study?.study_id ?? null, total: r.total, shown: r.findings.length, quarantined: r.quarantined });
      }
      return {
        papers,
        confirmed: papers.filter((p) => p.inGraph).length,
        total: papers.reduce((n, p) => n + p.total, 0),
        shown: papers.reduce((n, p) => n + p.shown, 0),
        quarantined: papers.reduce((n, p) => n + p.quarantined, 0),
      };
    }
    case "studies": {
      // Which of these PubMed ids does the live graph hold now? One OR-filtered call.
      const pmids = (q.get("pmids") ?? "").split(",").filter((x) => /^\d{1,9}$/.test(x)).slice(0, 45);
      if (pmids.length === 0) throw new BadRequest("pmids");
      const res = (await call(
        `/v1/studies?filter=pubmed_id:${pmids.join("%7C%7C")}&limit=50`,
      )) as List<{ study_id?: string; pubmed_id?: number | string }> | null;
      const held = (res?.data ?? []).map((st) => ({ pmid: String(st.pubmed_id), studyId: st.study_id ?? null }));
      return { asked: pmids.length, held };
    }
    case "probe": {
      const text = (q.get("q") ?? "").trim();
      if (!/^[A-Za-z0-9 _-]{2,40}$/.test(text)) throw new BadRequest("q");
      // `total` on a search is the size of the whole table, so count the rows.
      const vars = (await call(
        `/v1/variables?search=name:${encodeURIComponent(text)}&limit=50&fields=system_id,name`,
      )) as List<{ system_id?: string; name?: string }> | null;
      const data = vars?.data ?? [];
      return { q: text, count: data.length, capped: data.length >= 50, variables: data };
    }
    case "concept": {
      const id = q.get("id") ?? "";
      if (!ID.test(id)) throw new BadRequest("id");
      const rel = (await call(
        `/v1/concepts/${encodeURIComponent(id)}/relationships?sort=num_findings:desc&include_total=true&limit=8`,
      )) as List<Relationship> | null;
      const rows = rel?.data ?? [];
      const self = rows.map((r) => (r.source_concept?.system_id === id ? r.source_concept : r.target_concept))[0];
      const lastPublished = rows
        .map((r) => r.last_published_date)
        .filter((d): d is string => Boolean(d))
        .sort()
        .at(-1);
      return {
        id,
        label: self?.wikidata_label ?? null,
        totalRelationships: rel?.total ?? rows.length,
        shown: rows.length,
        /** Latest publication date among the relationships shown, not the whole graph. */
        lastPublishedAmongShown: lastPublished ? lastPublished.slice(0, 10) : null,
        neighbours: rows.map((r) => {
          const other = r.source_concept?.system_id === id ? r.target_concept : r.source_concept;
          return {
            id: other?.system_id ?? null,
            label: other?.wikidata_label ?? null,
            numFindings: r.num_findings ?? 0,
            numStudies: r.num_studies ?? 0,
            lastPublished: r.last_published_date ? r.last_published_date.slice(0, 10) : null,
          };
        }),
      };
    }
    default:
      throw new BadRequest("op");
  }
}

class BadRequest extends Error {}

export async function GET(req: Request) {
  const q = new URL(req.url).searchParams;
  const op = q.get("op") ?? "status";
  const configured = Boolean(key());
  const fetchedAt = new Date().toISOString();

  if (op === "status") return NextResponse.json({ live: configured, configured });
  if (!configured) return NextResponse.json({ live: false, reason: "no_key" });

  try {
    return NextResponse.json({ live: true, fetchedAt, ...(await answer(op, q) as object) });
  } catch (e) {
    if (e instanceof BadRequest) {
      return NextResponse.json({ live: false, reason: "bad_request", field: e.message }, { status: 400 });
    }
    return NextResponse.json({
      live: false,
      reason: "call_failed",
      error: e instanceof Error ? e.message : String(e),
    });
  }
}
