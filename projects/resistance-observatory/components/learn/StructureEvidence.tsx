"use client";

/**
 * The structure viewer and the marker's graph findings, side by side in
 * meaning but NOT joined in the data. The structure comes from RCSB PDB; the
 * findings come from the System Public Graph; neither references the other.
 * The only link is our own marker definition in content/markers.ts
 * (`sources.pdbResidue` and `sources.graphVariableIds`). The page says so.
 *
 * Wiring, both ways:
 *  - choosing the marker's residue in either viewer highlights this panel and
 *    scrolls it into view;
 *  - hovering or focusing a finding pulses that residue in both viewers.
 */
import { useCallback, useMemo, useRef, useState } from "react";
import type { Marker } from "@/content/markers";
import { MARKER_FINDINGS, spotStatusLabel } from "@/lib/findings";
import { formatGraphDate } from "@/lib/stats";
import { EvidenceLink } from "@/components/EvidenceLink";
import { StudyTypeChip } from "@/components/data/StudyTypeChip";
import { StructureViewer } from "@/components/learn/StructureViewer";

export function StructureEvidence({ marker }: { marker: Marker }) {
  const sources = marker.sources;
  /** The panel's opening lines: scrolled just into view, so the structures stay on screen. */
  const headRef = useRef<HTMLDivElement | null>(null);
  const [fromStructure, setFromStructure] = useState(false);
  const [pulse, setPulse] = useState<number | null>(null);

  // MARKER_FINDINGS already leaves out anything flagged `vetted: false`.
  const findings = useMemo(() => {
    const ids = new Set(sources?.graphVariableIds ?? []);
    return MARKER_FINDINGS.filter((f) => ids.has(f.variable1Id) || ids.has(f.variable2Id));
  }, [sources]);

  const onPick = useCallback(
    (resi: number) => {
      if (!sources || resi !== sources.pdbResidue) {
        setFromStructure(false);
        return;
      }
      setFromStructure(true);
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      headRef.current?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "nearest" });
    },
    [sources],
  );

  const pulseOn = () => sources && setPulse(sources.pdbResidue);
  const pulseOff = () => setPulse(null);

  return (
    <div className="space-y-6">
      <StructureViewer onPick={onPick} pulseResi={pulse} />

      {/* DOI cross-check, done when this was built: see README. */}
      <p className="max-w-3xl text-sm text-muted text-pretty">
        A coverage observation: both structures come from one paper,{" "}
        <a
          href="https://doi.org/10.1111/febs.15196"
          target="_blank"
          rel="noopener noreferrer"
          className="font-mono text-drug underline decoration-drug/40 underline-offset-4"
        >
          doi:10.1111/febs.15196
        </a>
        , and we found no findings from it in the System Public Graph: none in its vetted release and none among the
        findings we pulled. The graph&rsquo;s API cannot be searched by DOI, so this is as far as we could check. The
        structural literature on this marker is not represented in the graph.
      </p>

      <section
        aria-labelledby="struct-findings-h"
        className={`scroll-mt-24 rounded-[calc(var(--radius)+6px)] border bg-surface p-4 transition-colors sm:p-8 ${
          fromStructure ? "border-2 border-drug" : "border-line"
        }`}
      >
        <div ref={headRef} className="scroll-mb-6">
        <p className="max-w-3xl text-base text-muted text-pretty">
          The structure comes from RCSB PDB; the findings come from the System Public Graph. We connect them through
          our own definition of this marker &mdash; neither source links to the other.
        </p>

        <div className="mt-5 flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <h2 id="struct-findings-h" className="font-display text-2xl font-semibold">
            Graph findings for {marker.gene} {marker.alteration} and {marker.drug}
          </h2>
          <p aria-live="polite" className="font-mono text-sm text-drug">
            {fromStructure && sources ? `▶ Selected from the structure: residue ${sources.pdbResidue}` : ""}
          </p>
        </div>
        </div>

        {findings.length === 0 ? (
          <p className="mt-5 text-base">
            No findings in the pinned graph data pass review for this marker, so there is nothing to list here.
          </p>
        ) : (
          <>
            <p className="mt-2 text-sm text-muted">
              Statistics are shown as the graph records them. Each finding was compared with its paper in an
              AI-assisted spot-check that no person has reviewed; its result is shown beside the statistic. Point at
              or focus a finding to mark the residue in both structures.
            </p>
            <ol className="mt-5 divide-y divide-line border-y border-line">
              {findings.map((f) => (
                <li
                  key={f.systemId}
                  onMouseEnter={pulseOn}
                  onMouseLeave={pulseOff}
                  onFocus={pulseOn}
                  onBlur={pulseOff}
                  className="grid gap-x-8 gap-y-2 py-4 hover:bg-bg/40 focus-within:bg-bg/40 md:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]"
                >
                  <div className="min-w-0">
                    <p className="text-base leading-snug">
                      <span className="font-semibold">{f.variable1}</span>
                      <span className="text-muted"> — associated with — </span>
                      <span className="font-semibold">{f.variable2}</span>
                    </p>
                    <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-sm">
                      <span>
                        {f.statisticType}
                        {f.statisticValue !== null ? `: ${f.statisticValue}` : ": value not recorded"}
                      </span>
                      <StudyTypeChip studyType={f.studyType} />
                      <span className="text-muted">
                        spot-check: {f.spotCheck ? spotStatusLabel(f.spotCheck.status) : "not covered"}
                      </span>
                    </p>
                  </div>
                  <div className="min-w-0">
                    <p className="font-mono text-sm">
                      {f.published ? (
                        <>
                          Published <time dateTime={f.published}>{formatGraphDate(f.published)}</time>
                        </>
                      ) : (
                        "Publication date unknown"
                      )}
                    </p>
                    <EvidenceLink systemId={f.systemId} pubmedId={f.pubmedId} doi={f.doi} className="mt-1" />
                  </div>
                </li>
              ))}
            </ol>
          </>
        )}
      </section>
    </div>
  );
}
