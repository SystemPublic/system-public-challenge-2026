import { StatFigure } from "@/components/StatFigure";
import { Reveal } from "@/components/Reveal";
import {
  GRAPH_DOI,
  GRAPH_KNOWN_BAD_SHARE,
  GRAPH_LICENSE,
  GRAPH_MARKER_EXCLUDED_FINDINGS,
  GRAPH_MARKER_FINDINGS,
  GRAPH_MARKER_K540E_ALONE_FINDINGS,
  GRAPH_MARKER_STUDIES,
  GRAPH_PFDHPS_FINDINGS,
  GRAPH_PFDHPS_STUDIES,
  GRAPH_SNAPSHOT_DATE,
  GRAPH_VERSION,
  OPENALEX_MARKER_LAST_PUBLISHED,
} from "@/lib/stats";

/**
 * The scale of the evidence — framed as scarcity. Every figure comes from
 * lib/stats.ts, which reads the pinned System Public Graph pull.
 */
export function Scale() {
  return (
    <section id="scale" aria-labelledby="scale-h" className="border-y border-line bg-surface py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal>
          <p className="mb-3 font-mono text-xs uppercase tracking-[0.18em] text-muted">
            The evidence · pfdhps K540E and sulfadoxine
          </p>
          <h2 id="scale-h" className="sr-only">
            How much evidence the graph holds for pfdhps K540E and sulfadoxine
          </h2>
        </Reveal>

        {/* The marker itself: codon 540 */}
        <div className="mt-10 grid gap-x-12 gap-y-12 md:grid-cols-2">
          <Reveal>
            <StatFigure
              stat={{ ...GRAPH_MARKER_FINDINGS, unit: " findings." }}
              showLabel={false}
              showSource={false}
            />
          </Reveal>
          <Reveal delay={120}>
            <StatFigure
              stat={{ ...GRAPH_MARKER_STUDIES, unit: " studies." }}
              showLabel={false}
              showSource={false}
            />
          </Reveal>
        </div>
        <Reveal className="mt-6">
          <p className="font-mono text-sm uppercase tracking-[0.14em] text-muted">
            in the graph that name codon 540 of pfdhps directly
          </p>
        </Reveal>
        <Reveal className="mt-8">
          <p className="max-w-3xl text-base text-muted text-pretty">
            These are the findings the live API returns when a variable&rsquo;s name mentions codon 540. None
            of them is in System&rsquo;s vetted release. The Map and Alert tabs also draw on the vetted findings
            from the K540E papers the graph has read, so their counts differ.
          </p>
          <p className="mt-4 max-w-3xl text-base text-muted text-pretty">
            <strong className="text-fg">A coverage limitation, stated plainly:</strong> the graph indexes
            K540E only lightly.{" "}
            {GRAPH_MARKER_K540E_ALONE_FINDINGS.value === 0
              ? "No finding that survived review names K540E on its own."
              : `${GRAPH_MARKER_K540E_ALONE_FINDINGS.value} findings name K540E on its own.`}{" "}
            The {GRAPH_MARKER_FINDINGS.value - GRAPH_MARKER_K540E_ALONE_FINDINGS.value} codon-540 findings counted
            here sit at the pfdhps level: they name codon 540 inside a combination or a list, such as the
            A437G/K540E double mutant, or compare how common it is between two groups. No graph finding gives a
            prevalence figure for K540E.
            {GRAPH_MARKER_EXCLUDED_FINDINGS.value > 0
              ? ` ${GRAPH_MARKER_EXCLUDED_FINDINGS.value} more findings the live API returned were checked against their paper, found to be mis-extracted, and left out. The Data tab shows them.`
              : ""}
          </p>
        </Reveal>

        {/* Context: pfdhps overall */}
        <Reveal className="mt-20">
          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-muted">
            For context · a wider question
          </h3>
        </Reveal>
        <div className="mt-6 grid gap-x-12 gap-y-10 md:grid-cols-3">
          <Reveal>
            <StatFigure stat={GRAPH_PFDHPS_FINDINGS} size="md" showSource={false} />
          </Reveal>
          <Reveal delay={100}>
            <StatFigure stat={GRAPH_PFDHPS_STUDIES} size="md" showSource={false} />
          </Reveal>
          <Reveal delay={200}>
            <StatFigure stat={OPENALEX_MARKER_LAST_PUBLISHED} size="md" showSource={false} />
            <p className="mt-2 max-w-xs text-sm text-muted">
              The graph has no per-finding date; this one is resolved through OpenAlex from the
              finding&rsquo;s PubMed ID.
            </p>
          </Reveal>
        </div>

        {/* The turn */}
        <Reveal className="mt-20">
          <p className="max-w-4xl font-display text-4xl font-semibold tracking-tight sm:text-5xl text-balance">
            When the total is this small, <span className="text-drug">one new finding changes the picture.</span>
          </p>
        </Reveal>

        <Reveal className="mt-12">
          <p className="max-w-3xl border-t border-line pt-4 font-mono text-xs leading-relaxed text-muted">
            Source: System Public Graph v{GRAPH_VERSION.value}, {GRAPH_SNAPSHOT_DATE.value} snapshot, {GRAPH_LICENSE},
            doi:{GRAPH_DOI}. A finding is one association in the graph: two variables linked by a statistic. By
            System&rsquo;s own documentation roughly {GRAPH_KNOWN_BAD_SHARE.value}
            {GRAPH_KNOWN_BAD_SHARE.unit} of API associations are known-bad extractions; the findings counted
            here were compared with their papers in an AI-assisted spot-check that no person has reviewed.
            Publication dates: OpenAlex.
          </p>
          <p className="mt-4 max-w-3xl text-sm text-muted text-pretty">
            Each count answers the question written beside it. Other tabs ask the graph different questions
            about this marker, so they show different counts. That is expected, not a discrepancy.
          </p>
        </Reveal>
      </div>
    </section>
  );
}
