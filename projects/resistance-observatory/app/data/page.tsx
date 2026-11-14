import type { Metadata } from "next";
import type { ReactNode } from "react";
import {
  ANTIFOLATE,
  CANDIDATE_MARKERS,
  GLOSSARY,
  ONE_PARAGRAPH,
} from "@/content/data";
import { ALL_STATS } from "@/lib/stats";
import { StatFigure } from "@/components/StatFigure";
import { PullQuote } from "@/components/PullQuote";
import { FindingsTimeline } from "@/components/data/FindingsTimeline";
import { StudyTypeChip } from "@/components/data/StudyTypeChip";
import { EXCLUDED_FINDINGS, MARKER_FINDINGS, SPOT_CHECK_COUNTS } from "@/lib/findings";
import { Reveal } from "@/components/Reveal";

export const metadata: Metadata = {
  title: "Data",
  description: "A long-form guide to antimalarial resistance evidence: the marker's findings in publication order, key numbers and glossary.",
};

const TOC = [
  ["why", "Why markers are tracked"],
  ["timeline", "The findings, by publication date"],
  ["review", "Caught in review"],
  ["markers", "Five markers"],
  ["antifolate", "How antifolate resistance stacks"],
  ["method", "How we read the evidence"],
  ["limits", "What evidence can’t tell you"],
  ["numbers", "Key numbers"],
  ["glossary", "Glossary"],
] as const;

/** The two ways mis-extracted findings were found. */
const REVIEW_GROUPS = [
  {
    method: "source_abstract_check_and_vetted_csv",
    title: "Found by checking the abstract and the vetted release",
    how: "Checked against the abstract of the paper they cite, and absent from System\u2019s vetted release of the graph.",
  },
  {
    method: "ai_assisted_spot_check",
    title: "Found by an AI-assisted spot-check against the source papers",
    how: "An AI model compared each finding with its paper\u2019s abstract. No person has reviewed this check. Both abstracts were read again, also with AI assistance, before these were excluded.",
  },
] as const;

export default function DataPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6">
      {/* Masthead */}
      <header className="border-b border-line pb-14 pt-16 sm:pt-24">
        <p className="mb-5 font-mono text-xs uppercase tracking-[0.2em] text-muted">Data · the long view</p>
        <h1 className="max-w-4xl font-display text-[clamp(2.6rem,6.5vw,5.4rem)] font-semibold leading-[0.98] tracking-tight text-balance">
          Drugs, mutations, and the slow arithmetic of evidence.
        </h1>
        <p className="mt-8 max-w-2xl text-xl leading-relaxed text-muted text-pretty">
          A field guide to how antimalarial resistance is tracked, what the evidence can and cannot say, and
          the vocabulary this project uses. Every count on this page comes from the System Public Graph; publication dates come from OpenAlex.
        </p>
      </header>

      <div className="grid gap-12 py-14 lg:grid-cols-[13rem_1fr]">
        {/* Table of contents */}
        <nav aria-label="On this page" className="hidden lg:block">
          <ol className="sticky top-24 space-y-2 border-l border-line pl-4 text-sm">
            {TOC.map(([id, label], i) => (
              <li key={id}>
                <a href={`#${id}`} className="group flex gap-2 text-muted hover:text-fg">
                  <span className="font-mono text-xs tabular-nums text-line-strong group-hover:text-drug">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  {label}
                </a>
              </li>
            ))}
          </ol>
        </nav>

        <article className="min-w-0 text-lg leading-[1.75] [&_p]:text-pretty">
          <Section id="why" n={1} title="Why markers are tracked">
            {(
              <>
                {ONE_PARAGRAPH.value.map((p, i) => (
                  <p
                    key={i}
                    className={
                      i === 0
                        ? "mt-4 first-letter:float-left first-letter:mr-3 first-letter:font-display first-letter:text-7xl first-letter:font-semibold first-letter:leading-[0.8] first-letter:text-drug"
                        : "mt-4"
                    }
                  >
                    {p}
                  </p>
                ))}
              </>
            )}
            <p className="mt-6">
              A researcher tracking a marker has no simple way to know when the evidence has shifted enough to
              matter. That gap is what this project addresses.
            </p>
          </Section>

          <Section id="timeline" n={2} title="pfdhps K540E and sulfadoxine: the findings, by publication date" wide>
            <p>
              These are the {ALL_STATS.GRAPH_MARKER_FINDINGS.value} findings in the graph that name codon 540 of
              pfdhps directly, the marker associated with reduced efficacy of sulfadoxine, from{" "}
              {ALL_STATS.GRAPH_MARKER_STUDIES.value} studies. These are the findings the live API returns when a
              variable&rsquo;s name mentions codon 540. None of them is in System&rsquo;s vetted release. The Map
              and Alert tabs also draw on the vetted findings from the K540E papers the graph has read, so their
              counts differ. The graph indexes K540E only lightly: these findings
              sit at the pfdhps level, naming codon 540 inside a combination or a list, or comparing how common it
              is between two groups. No graph finding gives a prevalence figure for K540E. Each one links to its paper.
            </p>
            <p className="mt-4">
              The graph has no per-finding publication date, so each date here is the paper&rsquo;s publication
              date from OpenAlex, matched on the finding&rsquo;s PubMed ID. It resolved for{" "}
              {ALL_STATS.OPENALEX_MARKER_DATED_FINDINGS.value} of these {ALL_STATS.GRAPH_MARKER_FINDINGS.value}.
              Other tabs ask the graph different questions about this marker and show different counts; that is
              expected. By
              System&rsquo;s own documentation roughly {ALL_STATS.GRAPH_KNOWN_BAD_SHARE.value}
              {ALL_STATS.GRAPH_KNOWN_BAD_SHARE.unit} of API extractions are known-bad.
            </p>
            <p className="mt-4">
              What was checked, and how: every finding here was compared with its paper&rsquo;s PubMed abstract,
              and with open-access full text where there was any, in an AI-assisted spot-check. No person has
              reviewed that check. Of the {SPOT_CHECK_COUNTS.shown} findings shown, it marked{" "}
              {SPOT_CHECK_COUNTS.supported} supported and {SPOT_CHECK_COUNTS.partlySupported} partly supported,
              meaning the value matches the paper but the graph&rsquo;s label or population does not fully. Each
              entry carries its result. Findings the check contradicted are listed under &ldquo;Caught in
              review&rdquo;, not here.
            </p>
            <p className="mt-4">
              Evidence carries different weight depending on how it was produced: a therapeutic efficacy study
              and a general surveillance report are not the same thing. Each entry shows its study type as the
              graph recorded it, not as our judgement. The graph records a study type for{" "}
              {ALL_STATS.GRAPH_MARKER_TYPED_FINDINGS.value} of these {ALL_STATS.GRAPH_MARKER_FINDINGS.value}{" "}
              findings; where it records none, the entry says &ldquo;type not recorded&rdquo;.
            </p>
            <FindingsTimeline findings={MARKER_FINDINGS} />
            <p className="font-mono text-xs text-muted">
              Source: System Public Graph v{ALL_STATS.GRAPH_VERSION.value}, {ALL_STATS.GRAPH_SNAPSHOT_DATE.value}{" "}
              snapshot, CC BY-NC 4.0. Publication dates: OpenAlex.
            </p>
          </Section>

          <Section id="review" n={3} title="Caught in review">
            <p>
              Domain experts warn that automated extraction can place a large clinical trial and a small
              observational report side by side as if they carried equal weight. That is why every finding
              here shows its study type and links to its source, and why the findings below were checked against
              their paper.
            </p>
            <p className="mt-4">
              The live API returned {ALL_STATS.GRAPH_MARKER_EXCLUDED_FINDINGS.value} more findings for this
              marker. They are not on the timeline above, and they are in none of the counts on this site.
            </p>
            <p className="mt-4">They were found by two different methods.</p>
            {REVIEW_GROUPS.map((g) => {
              const group = EXCLUDED_FINDINGS.filter((f) => f.vettingMethod === g.method);
              if (!group.length) return null;
              return (
                <div key={g.method} className="mt-8">
                  <h3 className="font-display text-xl font-semibold">
                    {g.title} <span className="font-mono text-sm font-normal text-muted">({group.length})</span>
                  </h3>
                  <p className="mt-1 text-base text-muted">{g.how}</p>
                  <ul className="mt-5 space-y-6 border-l-2 border-dashed border-line-strong pl-6">
                    {group.map((f) => (
                      <li key={f.systemId}>
                        <p className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-sm font-semibold">
                          Excluded · mis-extracted
                          <StudyTypeChip studyType={f.studyType} />
                        </p>
                        <p className="mt-1 text-base leading-snug">
                          <span className="font-semibold">{f.variable1}</span>
                          <span className="text-muted"> — recorded against — </span>
                          <span className="font-semibold">{f.variable2}</span>
                        </p>
                        {f.vettingNote ? <p className="mt-2 text-base">{f.vettingNote}</p> : null}
                        <p className="mt-1 font-mono text-[0.72rem] text-muted">
                          system_id {f.systemId} · statistic recorded: {f.statisticType}
                        </p>
                        {f.pubmedId ? (
                          <a
                            href={`https://pubmed.ncbi.nlm.nih.gov/${f.pubmedId}/`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-1 inline-flex items-center gap-1 text-base font-medium text-drug underline decoration-drug/40 underline-offset-4 hover:decoration-drug"
                          >
                            PubMed record, PMID {f.pubmedId} <span aria-hidden>↗</span>
                            <span className="sr-only">(opens in a new tab)</span>
                          </a>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
            <p className="mt-8">
              This is not a criticism of the graph. System&rsquo;s API documentation says roughly{" "}
              {ALL_STATS.GRAPH_KNOWN_BAD_SHARE.value}
              {ALL_STATS.GRAPH_KNOWN_BAD_SHARE.unit} of the associations it serves are known-bad extractions.
              This is that rate, found in our own data, and it is why every finding here links to its paper.
              All of them stay in our pinned data file, flagged with the reason and the method.
            </p>
            <p className="mt-4 text-base text-muted">
              The vetted release holds only findings whose two variables are both matched to a concept, so it
              cannot confirm most of the findings on the timeline. Those were compared with their papers in
              the AI-assisted spot-check instead, which no person has reviewed.
            </p>
          </Section>

          <Section id="markers" n={4} title="Five markers worth knowing">
            <p>A marker means nothing without its drug, so they are always listed together.</p>
            {(
              <div className="mt-6 overflow-x-auto rounded-xl border border-line">
                <table className="w-full text-left text-base">
                  <thead className="bg-surface-2 font-mono text-xs uppercase tracking-wider text-muted">
                    <tr>
                      <th scope="col" className="px-4 py-3">Gene</th>
                      <th scope="col" className="px-4 py-3">Key alteration(s)</th>
                      <th scope="col" className="px-4 py-3">Drug</th>
                    </tr>
                  </thead>
                  <tbody>
                    {CANDIDATE_MARKERS.value.map((m) => (
                      <tr key={m.gene} className="border-t border-line">
                        <th scope="row" className="px-4 py-3 font-mono font-semibold">{m.gene}</th>
                        <td className="px-4 py-3 font-mono text-signal">{m.alterations}</td>
                        <td className="px-4 py-3">{m.drug}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Section>

          <Section id="antifolate" n={5} title="How antifolate resistance stacks">
            {(
              <>
                <p className="mt-4">{ANTIFOLATE.value.body}</p>
                <PullQuote cite="The hard constraint">{ANTIFOLATE.value.constraint}</PullQuote>
              </>
            )}
          </Section>

          <Section id="method" n={6} title="How this project reads the evidence">
            <p>
              The evidence comes from the System Public Graph, version {String(ALL_STATS.GRAPH_VERSION.value)},
              a snapshot frozen on {String(ALL_STATS.GRAPH_SNAPSHOT_DATE.value)}. Its atomic unit is
              an <em>association</em>: two variables linked by a statistic. It holds statistical associations, not
              prevalence measurements, so this site shows no prevalence figures.
            </p>
            <p className="mt-4">
              The graph has no geography field and no per-finding publication date. Publication dates are
              resolved through OpenAlex from each finding&rsquo;s PubMed ID. Locations on the Map tab come from a separate source and are attributed to it, never to the
              graph.
            </p>
            <p className="mt-4">
              By System&rsquo;s own documentation, roughly{" "}
              {String(ALL_STATS.GRAPH_KNOWN_BAD_SHARE.value)}
              {ALL_STATS.GRAPH_KNOWN_BAD_SHARE.unit} of associations served by its API are known-bad
              extractions, and variables that failed to ground to a Wikidata concept were removed from the public
              release. A codon-level mutation may be missing or only lightly indexed, as K540E is. {ALL_STATS.GRAPH_MARKER_EXCLUDED_FINDINGS.value}{" "}
              findings were found to be mis-extracted and excluded. The rest were compared with their papers in
              an AI-assisted spot-check that no person has reviewed. The project README records what was checked.
            </p>
            <PullQuote cite="How the alert demo works">
              The logic is tested on real history; the feed is a snapshot.
            </PullQuote>
            <p>
              Because the graph is frozen, the Alert demo replays real publication history: findings are played
              forward in the order they were actually published, and the matcher reacts as if they were new. It is
              not live surveillance. Every finding keeps its system ID, PubMed ID and DOI, so you can always click
              through to the paper.
            </p>
          </Section>

          <Section id="limits" n={7} title="What the evidence can’t tell you">
            <ul className="space-y-3">
              {[
                "That a marker’s presence means a patient’s treatment will fail.",
                "That a divergent finding is wrong, refuted, or an error. Studies differ for good reasons.",
                "Any prevalence figure. The graph holds associations, not prevalence.",
                "Where a marker is, from the graph alone. The graph has no geography.",
                "Any numerical forecast. No forecasting model has been evaluated.",
                "A comparison of effect sizes across different statistic types.",
                "That absence of evidence is evidence of absence. A missing relationship may reflect extraction gaps, grounding failures, or no published study.",
                "Any treatment recommendation, for anyone. Nor any WHO endorsement, integration or operational readiness.",
              ].map((t) => (
                <li key={t} className="flex gap-3">
                  <span aria-hidden className="mt-1 font-mono text-sm font-bold text-signal">✕</span>
                  <span>{t}</span>
                </li>
              ))}
            </ul>
            <PullQuote cite="Our rule for disagreement">We flag disagreement; we do not adjudicate.</PullQuote>
          </Section>

          <Section id="numbers" n={8} title="Key numbers" wide>
            <p>
              Every number in this app lives in one file, <code className="font-mono text-base">lib/stats.ts</code>,
              and every one is read from a pinned data pull: counts from the System Public Graph API, dates from
              OpenAlex. Nothing is typed in by hand. Each count is labelled with the question it answers.
            </p>
            <div className="mt-10 grid gap-x-10 gap-y-12 sm:grid-cols-2">
              {(
                [
                  "GRAPH_MARKER_FINDINGS",
                  "GRAPH_MARKER_STUDIES",
                  "GRAPH_PFDHPS_FINDINGS",
                  "GRAPH_PFDHPS_STUDIES",
                  "GRAPH_MARKER_EXCLUDED_FINDINGS",
                  "OPENALEX_MARKER_LAST_PUBLISHED",
                ] as const
              ).map((k, i) => (
                <Reveal key={k} delay={(i % 2) * 100}>
                  <StatFigure stat={ALL_STATS[k]} size="md" />
                </Reveal>
              ))}
            </div>
          </Section>

          <Section id="glossary" n={9} title="Glossary">
            <dl className="divide-y divide-line border-y border-line">
              {GLOSSARY.map((g) => (
                <div key={g.term} className="grid gap-1 py-5 sm:grid-cols-[11rem_1fr] sm:gap-6">
                  <dt className="font-display text-xl font-semibold">{g.term}</dt>
                  <dd className="text-muted">
                    {(
                      <>
                        {g.definition}
                      </>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          </Section>
        </article>
      </div>
    </div>
  );
}

function Section({
  id,
  n,
  title,
  children,
  wide = false,
}: {
  id: string;
  n: number;
  title: string;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className={`scroll-mt-24 pb-16 ${wide ? "" : "max-w-[44rem]"}`}>
      <p className="font-mono text-xs tabular-nums text-drug">{String(n).padStart(2, "0")}</p>
      <h2 id={`${id}-h`} className="mb-5 mt-1 font-display text-3xl font-semibold tracking-tight sm:text-4xl text-balance">
        {title}
      </h2>
      {children}
    </section>
  );
}
