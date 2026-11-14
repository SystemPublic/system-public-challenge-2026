"use client";

import { useMemo, useState } from "react";
import { pmidStr, type ClientPack, type MarkerDef } from "@/lib/alert/pack";
import { TIER } from "@/lib/alert/receipt";
import { EVIDENCE_TIER, NO_STUDY_TYPE, assayKeywords } from "@/lib/alert/context";
import { useSystem, type LiveCoverage, type LiveStudies } from "./useSystem";

/**
 * The extraction gap, made useful to the people who maintain the graph:
 *  - what the graph extracted from the K540E papers it has read (clinical
 *    endpoints, no stand-alone K540E prevalence), confirmed live with a
 *    count of associations quarantined for not being in the vetted set;
 *  - the K540E papers naming this country that it has not read, as a
 *    ready-to-ingest PubMed id queue.
 * Both follow the replay year.
 */
export function CurationQueue({ pack, marker, area, country, replayYear }: { pack: ClientPack; marker: MarkerDef; area: string; country: string; replayYear: number }) {
  const [copied, setCopied] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const coverage = useSystem<LiveCoverage>("op=coverage");

  const read = useMemo(
    () =>
      pack.literature.papers
        .filter((p) => p.in_graph && p.pub_year <= replayYear)
        .sort((a, b) => Number((b.countries_iso3 ?? []).includes(area)) - Number((a.countries_iso3 ?? []).includes(area)) || b.pub_year - a.pub_year),
    [pack.literature.papers, replayYear, area],
  );
  const figures = useMemo(() => new Set(pack.literature.abstract_prevalence.map((f) => pmidStr(f.pmid))), [pack.literature.abstract_prevalence]);
  const assoc = useMemo(() => new Set(pack.literature.abstract_associations.map((f) => pmidStr(f.pmid))), [pack.literature.abstract_associations]);
  const queue = useMemo(
    () =>
      pack.literature.papers
        .filter((p) => !p.in_graph && p.pub_year <= replayYear && (p.countries_iso3 ?? []).includes(area))
        .map((p) => {
          const id = pmidStr(p.pmid);
          return { p, id, figure: figures.has(id), assoc: assoc.has(id), claim: Boolean(p.first_report_claim) };
        })
        .sort((a, b) => Number(b.figure) + Number(b.claim) + Number(b.assoc) - (Number(a.figure) + Number(a.claim) + Number(a.assoc)) || b.p.pub_year - a.p.pub_year),
    [pack.literature.papers, replayYear, area, figures, assoc],
  );
  const queueIds = queue.map((x) => x.id).filter((id) => /^\d+$/.test(id));
  const liveQueue = useSystem<LiveStudies>(queueIds.length ? `op=studies&pmids=${queueIds.slice(0, 45).join(",")}` : null);
  const nowHeld = liveQueue?.state === "live" ? new Set(liveQueue.data.held.map((h) => h.pmid)) : null;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(queueIds.join("\n"));
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard unavailable: the ids are on screen */
    }
  };

  const livePaper = (pmid: string) => (coverage?.state === "live" ? coverage.data.papers.find((x) => x.pmid === pmid) : undefined);

  return (
    <section aria-labelledby="cur-h" className="mt-6 rounded-[var(--radius)] border border-drug/40 bg-drug-soft/30 p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <h2 id="cur-h" className="font-mono text-xs uppercase tracking-[0.18em] text-drug">
          Extraction gap and curation queue · for the graph’s maintainers
        </h2>
        <p className="font-mono text-[0.7rem] text-muted" aria-live="polite">
          {coverage?.state === "live" ? (
            <>
              System API connected: {coverage.data.confirmed} of {coverage.data.papers.length} in-graph papers confirmed · API returns {coverage.data.total} associations ·{" "}
              <strong className="text-fg">{coverage.data.shown} vetted</strong> ·{" "}
              <strong className={coverage.data.quarantined > 0 ? "text-gap" : "text-fg"}>{coverage.data.quarantined} quarantined</strong> (not in the vetted set, never shown)
            </>
          ) : coverage?.state === "snapshot" ? (
            "System API not connected; showing the data pack"
          ) : (
            "Checking the System API…"
          )}
        </p>
      </div>

      <p className="mt-3 max-w-4xl rounded-lg border border-gap/50 bg-gap-soft/40 p-3 text-xs leading-relaxed">
        <strong>Why unvetted extractions are quarantined: one concrete case.</strong> From Gutman et al. 2015, Malawi (
        <a href="https://pubmed.ncbi.nlm.nih.gov/25564249/" target="_blank" rel="noopener noreferrer" className="text-drug underline underline-offset-2">
          PMID 25564249 ↗
        </a>
        ), the System API returns two associations on variable <span className="font-mono">w1ktrLk4Wc</span>: <span className="font-mono">paFNq6MPX5</span> (adjusted prevalence ratio 2.76) and{" "}
        <span className="font-mono">AeI-laBxXr</span> (adjusted prevalence ratio 3.28). The extractor attached risks reported for the A581G-bearing sextuple haplotype onto {marker.mutation}. Neither id is in
        the vetted set, so this tab counts them and never shows them as evidence about {marker.mutation}. This is what happens when machine extraction drops a study’s
        meta-context: which haplotype was measured, in whom, by what kind of study. Being in the vetted set is not proof either: <span className="font-mono">PEyo2A8Ol0</span> (
        <a href="https://pubmed.ncbi.nlm.nih.gov/26429700/" target="_blank" rel="noopener noreferrer" className="text-drug underline underline-offset-2">
          PMID 26429700 ↗
        </a>
        , a Kenya trial) is a vetted id, but its relative risk of 0.32 is dihydroartemisinin-piperaquine compared against {marker.drugShort}, presented by the graph as an effect of {marker.drugShort}. We caught the
        reversed arms against the paper and excluded it from the {marker.drugShort} findings shown here. Every item shown on this page therefore carries its evidence tier, study type and population.
      </p>

      <div className="mt-4 grid gap-6 xl:grid-cols-2">
        {/* read */}
        <div>
          <h3 className="text-sm font-semibold">
            Read by the graph by {replayYear}: {read.length} paper{read.length === 1 ? "" : "s"} <span className="font-normal text-muted">· what it extracted</span>
          </h3>
          <p className="mt-1 text-xs text-muted">
            Clinical endpoints, mostly. No finding gives {marker.mutation} prevalence on its own; the one variable that mentions it (5bJrK_wJcx) bundles 540E with three other SNPs.
          </p>
          {read.length === 0 ? (
            <p className="mt-3 rounded-lg border border-dashed border-line-strong p-4 text-sm text-muted">By {replayYear} the graph had read none of the {marker.mutation} papers.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {(showAll ? read : read.slice(0, 4)).map((p) => {
                const id = pmidStr(p.pmid);
                const fs = pack.graph.findings_from_k540e_papers.filter((f) => pmidStr(f.pubmed_id) === id);
                const lp = livePaper(id);
                const here = (p.countries_iso3 ?? []).includes(area);
                return (
                  <li key={id} className={`rounded-lg border bg-surface p-3 text-sm ${here ? "border-drug/60" : "border-line"}`}>
                    <p className="font-medium leading-snug">{p.title}</p>
                    <p className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 font-mono text-[0.68rem] text-muted">
                      <span>published {p.pub_year}</span>
                      <span>{(p.countries_iso3 ?? []).join(", ") || "no country stated"}</span>
                      <a href={p.url ?? `https://pubmed.ncbi.nlm.nih.gov/${id}/`} target="_blank" rel="noopener noreferrer" className="text-drug underline underline-offset-2">
                        PMID {id} ↗
                      </a>
                      {fs[0]?.study_id ? <span>study_id {fs[0].study_id}</span> : lp?.studyId ? <span>study_id {lp.studyId}</span> : null}
                      {lp ? (
                        <span className="text-drug">
                          API ✓ {lp.total} returned, {lp.shown} vetted{lp.quarantined ? `, ${lp.quarantined} quarantined` : ""}
                        </span>
                      ) : null}
                    </p>
                    {fs.length ? (
                      <ul className="mt-2 space-y-1 border-t border-line pt-2 text-[0.8rem]">
                        {fs.slice(0, 3).map((f) => (
                          <li key={f.system_id} className="leading-snug">
                            {f.variable_1} <span className="font-mono text-xs text-muted">↔</span> {f.variable_2}{" "}
                            <span className="font-mono text-[0.66rem] text-muted">
                              {f.system_id} · {f.source_checked ? TIER.checked : TIER.unverified} · {f.study_type ? <strong className="text-fg">{f.study_type}</strong> : NO_STUDY_TYPE} · population:{" "}
                              {f.population ?? "not given"}
                            </span>
                          </li>
                        ))}
                        {fs.length > 3 ? <li className="font-mono text-[0.68rem] text-muted">+ {fs.length - 3} more from this paper</li> : null}
                      </ul>
                    ) : (
                      <p className="mt-2 border-t border-line pt-2 text-xs text-muted">The data pack lists no vetted finding from this paper.</p>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
          {read.length > 4 ? (
            <button type="button" onClick={() => setShowAll((s) => !s)} className="mt-2 text-xs text-muted underline underline-offset-2 hover:text-fg" aria-expanded={showAll}>
              {showAll ? "Show fewer" : `Show all ${read.length}`}
            </button>
          ) : null}
        </div>

        {/* queue */}
        <div>
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="text-sm font-semibold">
              Ready to ingest for {country}: {queue.length} unread paper{queue.length === 1 ? "" : "s"}
            </h3>
            {queue.length ? (
              <button type="button" onClick={copy} className="rounded-full border border-line-strong px-3 py-1 text-xs font-medium hover:bg-surface">
                {copied ? "Copied" : `Copy ${queueIds.length} PMIDs`}
              </button>
            ) : null}
          </div>
          <p className="mt-1 text-xs text-muted">
            {marker.mutation} papers naming {country}, published by {replayYear}, that the graph has not read. Papers whose abstract states a {marker.mutation} figure come first.
            {nowHeld ? ` API check: ${nowHeld.size} of ${Math.min(queueIds.length, 45)} have been ingested since the snapshot.` : ""}
          </p>
          {queue.length === 0 ? (
            <p className="mt-3 rounded-lg border border-dashed border-line-strong p-4 text-sm text-muted">
              No unread {marker.mutation} paper names {country} by {replayYear}.
            </p>
          ) : (
            <ol className="mt-3 max-h-[26rem] space-y-1 overflow-y-auto pr-1">
              {queue.map(({ p, id, figure, assoc: a, claim }) => (
                <li key={id} className="grid grid-cols-[3rem_1fr] gap-x-2 rounded-md border border-line bg-surface px-2.5 py-2 text-[0.82rem]">
                  <span className="font-mono text-xs font-semibold tabular-nums">{p.pub_year}</span>
                  <span className="min-w-0">
                    <span className="block leading-snug">{p.title}</span>
                    <span className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 font-mono text-[0.66rem] text-muted">
                      <a href={p.url ?? `https://pubmed.ncbi.nlm.nih.gov/${id}/`} target="_blank" rel="noopener noreferrer" className="text-drug underline underline-offset-2">
                        PMID {id} ↗
                      </a>
                      <span className="rounded-full border border-gap/60 px-1.5 text-gap">{EVIDENCE_TIER.papers}</span>
                      {assayKeywords(p.title).length ? <span>title mentions {assayKeywords(p.title).join(", ")}</span> : null}
                      {figure ? <span className="rounded-full border border-gap/60 px-1.5 text-gap">states a K540E figure</span> : null}
                      {claim ? <span className="rounded-full border border-gap/60 px-1.5 text-gap">first-report claim</span> : null}
                      {a ? <span className="rounded-full border border-line-strong px-1.5">association sentence</span> : null}
                      {nowHeld?.has(id) ? <span className="text-drug">now in the graph, per the API</span> : null}
                    </span>
                  </span>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </section>
  );
}
