"use client";

import { useState } from "react";
import { useSystem, type LiveConcept, type LiveCoverage, type LiveProbe } from "./useSystem";
import css from "./alert.module.css";

export type ConceptRef = { key: string; id: string; label: string };

type Props = {
  marker: string;
  mutation: string;
  probes: string[];
  concepts: ConceptRef[];
  replayYear: number;
  lastYear: number;
  papersTotal: number;
  papersByNow: number;
  inGraphTotal: number;
  inGraphByNow: number;
  haplotypeFindings: number;
  checkedFindings: number;
  vettedCount: number;
  snapshotLabel: string;
};

export function LiveStatus({ live, snapshotLabel }: { live: "loading" | "live" | "snapshot"; snapshotLabel: string }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-line px-2.5 py-1 font-mono text-[0.7rem] text-muted"
      title={live === "live" ? "Connected to the System API: answers below were fetched from it just now" : "The System API is not answering; showing the data pack"}
    >
      {live === "live" ? (
        <>
          <span aria-hidden className={`inline-block h-2 w-2 rounded-full bg-drug ${css.liveDot}`} />
          System API · connected
        </>
      ) : live === "loading" ? (
        <>
          <span aria-hidden className="inline-block h-2 w-2 rounded-full border border-muted" />
          System API · checking
        </>
      ) : (
        <>
          <span aria-hidden className="inline-block h-2 w-2 rounded-sm border border-gap bg-gap-soft" />
          {snapshotLabel}
        </>
      )}
    </span>
  );
}

export function GraphPanel(p: Props) {
  const [concept, setConcept] = useState(0);
  const exact = useSystem<LiveProbe>(`op=probe&q=${encodeURIComponent(p.probes[0])}`);
  const loose = useSystem<LiveProbe>(p.probes[1] ? `op=probe&q=${encodeURIComponent(p.probes[1])}` : null);
  const active = p.concepts[concept];
  const cov = useSystem<LiveCoverage>("op=coverage");
  const rel = useSystem<LiveConcept>(active ? `op=concept&id=${encodeURIComponent(active.id)}` : null);

  const live: "loading" | "live" | "snapshot" =
    exact?.state === "live" ? "live" : exact?.state === "loading" || !exact ? "loading" : "snapshot";
  const replaying = p.replayYear < p.lastYear;
  const share = p.papersByNow > 0 ? p.inGraphByNow / p.papersByNow : 0;
  const maxF = rel?.state === "live" ? Math.max(1, ...rel.data.neighbours.map((n) => n.numFindings)) : 1;

  return (
    <section aria-labelledby="graph-h" className="rounded-[var(--radius)] border border-drug/40 bg-drug-soft/40 p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="graph-h" className="font-mono text-xs uppercase tracking-[0.18em] text-drug">
          What the System graph knows about {p.mutation}
        </h2>
        <LiveStatus live={live} snapshotLabel={p.snapshotLabel} />
      </div>

      <div className="mt-3 grid gap-5 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)_minmax(0,1.25fr)]">
        {/* coverage readout: follows the replay */}
        <div>
          <p className="font-display text-3xl font-semibold leading-none tracking-tight tabular-nums sm:text-4xl">
            {p.inGraphByNow} <span className="text-muted">of</span> {p.papersByNow}
          </p>
          <p className="mt-1.5 text-sm">
            papers on {p.mutation} {replaying ? `published by ${p.replayYear}` : "published to date"} have been read by the graph.
          </p>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface" role="img" aria-label={`${p.inGraphByNow} of ${p.papersByNow} papers`}>
            <div className="h-full rounded-full bg-drug transition-[width] duration-500" style={{ width: `${Math.max(share * 100, p.inGraphByNow ? 1.5 : 0)}%` }} />
          </div>
          {replaying ? (
            <p className="mt-1.5 font-mono text-[0.7rem] text-muted">
              Whole record: {p.inGraphTotal} of {p.papersTotal}.
            </p>
          ) : null}
        </div>

        {/* what it holds, and the live variable probe */}
        <ul className="space-y-2 text-sm">
          <li>
            <strong>No finding names {p.mutation} on its own.</strong> It holds {p.haplotypeFindings} finding{p.haplotypeFindings === 1 ? "" : "s"} on
            haplotypes that contain it; {p.checkedFindings} {p.checkedFindings === 1 ? "was" : "were"} checked against the paper.
          </li>
          <li className="text-muted">
            {exact?.state === "live" ? (
              <>
                API probe: {exact.data.count === 0 ? "no" : exact.data.count} graph variable{exact.data.count === 1 ? "" : "s"} named “{exact.data.q}”
                {loose?.state === "live" && loose.data.count > 0 ? (
                  <>
                    ; {loose.data.count} mention{loose.data.count === 1 ? "s" : ""} “{loose.data.q}”:{" "}
                    <span className="text-fg">“{loose.data.variables[0]?.name}”</span>{" "}
                    <span className="font-mono text-[0.7rem]">({loose.data.variables[0]?.system_id})</span>. A variable, not a finding.
                  </>
                ) : (
                  "."
                )}
              </>
            ) : exact?.state === "snapshot" ? (
              <>API probe unavailable; the data pack records no finding naming {p.mutation} alone.</>
            ) : (
              <span className={`inline-block h-4 w-48 align-middle ${css.skeleton}`} />
            )}
          </li>
          <li className="font-mono text-[0.7rem] text-muted">
            Accuracy quarantine: only the {p.vettedCount.toLocaleString("en-US")} vetted association ids are ever shown.{" "}
            {cov?.state === "live" ? (
              <>
                From the API, for the {cov.data.papers.length} papers it has read: {cov.data.total} associations returned, {cov.data.shown} vetted,{" "}
                <strong className={cov.data.quarantined > 0 ? "text-gap" : "text-fg"}>{cov.data.quarantined} quarantined</strong>.
              </>
            ) : (
              "The API’s other returns are counted, not displayed."
            )}
          </li>
        </ul>

        {/* where the drug sits in the graph, live */}
        <div>
          <div className="flex flex-wrap items-center gap-1" role="tablist" aria-label="Concept">
            {p.concepts.map((c, i) => (
              <button
                key={c.id}
                role="tab"
                type="button"
                aria-selected={i === concept}
                onClick={() => setConcept(i)}
                className={`rounded-full px-2.5 py-1 text-xs transition-colors ${
                  i === concept ? "bg-drug font-medium text-bg" : "border border-line text-muted hover:text-fg"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
          <div className="mt-2 min-h-[7.5rem]">
            {rel?.state === "live" ? (
              rel.data.neighbours.length === 0 ? (
                <p className="text-sm text-muted">The graph returns no relationships for this concept.</p>
              ) : (
                <>
                  <ul className="space-y-1">
                    {rel.data.neighbours.slice(0, 5).map((n) => (
                      <li key={n.id} className="grid grid-cols-[minmax(0,9.5rem)_1fr_auto] items-center gap-2 text-xs">
                        <span className="truncate" title={n.label ?? ""}>
                          {n.label}
                        </span>
                        <span className="h-1.5 rounded-full bg-surface">
                          <span className="block h-full rounded-full bg-drug" style={{ width: `${(n.numFindings / maxF) * 100}%` }} />
                        </span>
                        <span className="font-mono text-[0.68rem] tabular-nums text-muted">
                          {n.numFindings} finding{n.numFindings === 1 ? "" : "s"} · {n.numStudies} stud{n.numStudies === 1 ? "y" : "ies"}
                        </span>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-1.5 font-mono text-[0.68rem] text-muted">
                    {rel.data.totalRelationships} relationships in all · most recent publication among these: {rel.data.lastPublishedAmongShown ?? "not given"}
                  </p>
                </>
              )
            ) : rel?.state === "snapshot" ? (
              <p className="text-sm text-muted">API relationships unavailable ({p.snapshotLabel}).</p>
            ) : (
              <div className="space-y-2" aria-label="Loading">
                {[70, 55, 40, 32].map((w) => (
                  <div key={w} className={`h-3 ${css.skeleton}`} style={{ width: `${w}%` }} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
