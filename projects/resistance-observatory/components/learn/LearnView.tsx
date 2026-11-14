"use client";

/**
 * Learn — docs/LEARN.md. Five blocks, in order, nothing else:
 *   1. identity strip  2. one-sentence answer  3. diagram
 *   4. plain-language mechanism  5. limits + actions
 *
 * Content comes from content/markers.ts, transcribed from
 * docs/MARKER-CONTENT.md.
 */
import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { useSelection } from "@/lib/selection";
import { getMarker, MARKERS } from "@/content/markers";
import { Chip } from "@/components/Chip";
import { ActionButtons } from "@/components/learn/ActionButtons";
import { MarkerDiagram } from "@/components/learn/MarkerDiagram";
import { StructureEvidence } from "@/components/learn/StructureEvidence";

/** Same side gutters as the nav and the story page, so left edges line up. */
const WRAP = "mx-auto max-w-[1340px] px-[clamp(16px,5.4vw,100px)]";

export function LearnView({ structureFigure }: { structureFigure?: ReactNode }) {
  const { markerId, setMarkerId, hrefWithSelection } = useSelection();
  // A marker id from the URL that we have no content for. Kept so the notice
  // stays visible after the URL is corrected.
  const [uncovered, setUncovered] = useState<string | null>(null);
  const marker = getMarker(markerId);

  // Learn sets markerId (LEARN.md). If the URL carries none, or an unknown id,
  // write the shown marker into shared state so every other tab inherits it.
  useEffect(() => {
    if (markerId && !MARKERS[markerId]) setUncovered(markerId);
    if (!markerId || !MARKERS[markerId]) setMarkerId(marker.id);
  }, [markerId, marker.id, setMarkerId]);

  const sentence = marker.oneSentence;
  const diagram = marker.diagram;
  const mechanism = marker.mechanism;

  return (
    <article className="pb-16">
      <h1 className="sr-only">
        Learn: {marker.gene} {marker.alteration} and {marker.drug}
      </h1>

      {/* First screen: identity, answer and diagram composed as one unit, on
          the story's dark gradient field. Blocks 1-3 keep their order. */}
      <div className="learn-top border-b border-line">
        <div className={`${WRAP} pb-12 pt-8 xl:pb-14 xl:pt-12`}>
          {uncovered ? (
            <p
              role="status"
              className="mb-6 flex items-start gap-3 rounded-[var(--radius)] border-2 border-fg bg-surface px-4 py-3 text-base"
            >
              <span aria-hidden className="font-mono font-bold">
                i
              </span>
              <span>
                <span className="font-mono font-semibold break-all">{uncovered.slice(0, 80)}</span> isn&rsquo;t covered
                yet &mdash; showing {marker.gene} {marker.alteration}.
              </span>
            </p>
          ) : null}

          {/* 1 — Identity strip */}
          <section aria-label="Marker identity" className="border-b border-line pb-5">
            {/* The story's eyebrow hairline, carried over. */}
            <span aria-hidden className="mb-4 block h-px w-[34px] bg-drug" />
            <p className="flex flex-wrap items-center gap-x-3 gap-y-2 font-mono text-sm sm:text-base">
              <span className="italic">{marker.organism}</span>
              <Dot />
              <span>
                <span className="font-semibold">{marker.gene}</span>
                {marker.geneFullName ? <span className="text-muted"> ({marker.geneFullName})</span> : null}
              </span>
              <Dot />
              <span>
                <span className="font-semibold text-signal">{marker.alteration}</span>
                {marker.alterationPlain ? <span className="text-muted"> ({marker.alterationPlain})</span> : null}
              </span>
              <Dot />
              <span>
                affects <span className="font-semibold text-drug">{marker.drug}</span>
                {marker.drugNote ? <span className="text-muted"> ({marker.drugNote})</span> : null}
              </span>
              {marker.classification ? (
                <Chip tone="neutral" title={`Source: ${marker.classification.source}`}>
                  {marker.classification.label} · {marker.classification.source}
                </Chip>
              ) : null}
            </p>
          </section>

          <div className="mt-8 grid gap-8 xl:grid-cols-[minmax(0,5fr)_minmax(0,8fr)] xl:items-center xl:gap-10">
            <div className="min-w-0">
              {/* Left-hand anchor: the marker name, large and quiet. Decorative;
                  the name is already in the identity strip and the heading. */}
              <p
                aria-hidden
                className="select-none font-display text-[clamp(3.5rem,7vw,6.5rem)] leading-none text-fg/15"
              >
                {marker.alteration}
              </p>

              {/* 2 — The one-sentence answer */}
              <section aria-label="The answer in one sentence" className="mt-5">
                <p className="font-display text-[clamp(1.6rem,2.8vw,2.6rem)] leading-[1.12] text-balance">
                  {sentence.value}
                </p>
              </section>
            </div>

            {/* 3 — The diagram */}
            <section
              aria-label="Diagram"
              className="min-w-0 rounded-[calc(var(--radius)+6px)] border border-line bg-surface p-4 sm:p-6 xl:p-5"
            >
              <h2 className="mb-4 font-display text-2xl font-semibold">{diagram.value.title}</h2>
              <MarkerDiagram diagram={diagram.value} />
            </section>
          </div>
        </div>
      </div>

      <div className={`${WRAP} pt-10`}>
      {/* 3b — Published crystal structures: live 3D viewer, then the static
          figure (rendered on the server; absent if its images are). */}
      <StructureEvidence marker={marker} />
      {structureFigure}

      {/* 4 — Plain-language mechanism */}
      <section aria-labelledby="mech-h" className="py-14">
        <h2 id="mech-h" className="mb-6 font-mono text-xs uppercase tracking-[0.18em] text-muted">
          How it works, plainly
        </h2>
        {marker.keyPoint ? (
          <div className="mb-10 border-l-4 border-signal bg-surface px-5 py-5 sm:px-7">
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-signal">Keep this in mind</p>
            <h3 className="mt-2 font-display text-2xl font-semibold sm:text-3xl">{marker.keyPoint.heading}</h3>
            <p className="mt-3 max-w-3xl text-lg leading-relaxed text-pretty">{marker.keyPoint.body}</p>
          </div>
        ) : null}
        <div className="grid gap-8 md:grid-cols-3">
          {mechanism.value.map((para, i) => (
            <div key={i}>
              <h3 className="mb-2 font-mono text-xs text-muted">{para.heading}</h3>
              <p className="text-lg leading-relaxed text-pretty">{para.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Why this matters — points to Alert's stakes chain; no figures restated here. */}
      <section aria-labelledby="why-h" className="mb-14 rounded-[calc(var(--radius)+6px)] border border-line bg-surface p-6 sm:p-8">
        <h2 id="why-h" className="font-display text-2xl font-semibold sm:text-3xl">Why this matters</h2>
        <p className="mt-4 max-w-3xl text-lg leading-relaxed text-pretty">
          {marker.gene} {marker.alteration} is associated with reduced efficacy of {marker.drug}, one half of SP.
          The evidence graph also holds findings that connect SP failure with outcomes for patients: birth weight,
          placental parasitemia, and malaria at delivery.
        </p>
        <p className="mt-3 max-w-3xl text-base text-muted text-pretty">
          Alert follows that chain of evidence one finding at a time, each linked to its paper. These are
          associations reported in published studies. They are not a prediction for any patient, and not
          clinical guidance.
        </p>
        <Link
          href={hrefWithSelection("/alert", { markerId: marker.id })}
          className="mt-5 inline-flex items-center gap-2 font-semibold text-drug underline decoration-drug/40 underline-offset-4 hover:decoration-drug"
        >
          Follow the stakes chain on Alert <span aria-hidden>→</span>
        </Link>
      </section>

      {/* 5 — Limits and actions */}
      <section aria-label="Limits and next steps" className="grid gap-8 border-t border-line pt-12 md:grid-cols-2">
        <div>
          <h2 className="font-display text-2xl font-semibold">What this doesn&rsquo;t tell you</h2>
          <ul className="mt-5 space-y-4">
            {(marker.limits ?? [
              <>
                Finding this marker in a parasite does <strong>not</strong> mean any individual
                patient&rsquo;s treatment will fail.
              </>,
              <>
                <strong>Absence of evidence is not evidence of absence.</strong> A missing
                relationship may reflect extraction gaps, grounding failures, or no published study.
              </>,
              <>
                <strong>This is not clinical guidance</strong> and is never a treatment
                recommendation.
              </>,
            ]).map((item, i) => (
              <li key={i} className="flex gap-3 text-pretty">
                <span aria-hidden className="mt-1 font-mono text-sm font-bold text-signal">
                  ✕
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h2 className="font-display text-2xl font-semibold">Next</h2>
          <p className="mb-5 mt-2 text-sm text-muted">
            Both carry this marker &mdash; {marker.gene} {marker.alteration}, {marker.drug} &mdash; with you.
          </p>
          <ActionButtons marker={marker} />
        </div>
      </section>
      </div>
    </article>
  );
}

function Dot() {
  return (
    <span aria-hidden className="hidden text-muted sm:inline">
      ·
    </span>
  );
}
