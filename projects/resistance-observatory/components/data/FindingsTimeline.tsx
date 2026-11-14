import { EvidenceLink } from "@/components/EvidenceLink";
import { StudyTypeChip } from "@/components/data/StudyTypeChip";
import { formatGraphDate } from "@/lib/stats";
import { spotStatusLabel, type MarkerFinding } from "@/lib/findings";

/**
 * Publication-date timeline of the demo marker's findings, oldest to newest.
 * Dates come from OpenAlex, matched on PubMed ID. A finding whose date did not
 * resolve sits outside the timeline under "Date unknown" — position, shape and
 * label, never colour alone.
 */
export function FindingsTimeline({ findings }: { findings: MarkerFinding[] }) {
  const dated = findings.filter((f) => f.published);
  const undated = findings.filter((f) => !f.published);
  return (
    <div className="my-10 space-y-12">
      <Group title="Timeline" note="Oldest first. Findings from the same paper share its date." findings={dated} />
      {undated.length ? (
        <Group
          title="Date unknown"
          note="OpenAlex returned no publication date for these. They sit outside the timeline. Follow the link for the paper's own date."
          findings={undated}
        />
      ) : null}
    </div>
  );
}

function Group({ title, note, findings }: { title: string; note: string; findings: MarkerFinding[] }) {
  return (
    <section>
      <h3 className="font-display text-xl font-semibold">
        {title} <span className="font-mono text-sm font-normal text-muted">({findings.length})</span>
      </h3>
      <p className="mt-1 max-w-2xl text-sm text-muted">{note}</p>
      <ol className="mt-6 border-l-2 border-line-strong">
        {findings.map((f) => (
          <li key={f.systemId} className="relative pb-8 pl-6 last:pb-0">
            <span
              aria-hidden
              className={`absolute -left-[7px] top-1.5 h-3 w-3 border-2 border-fg ${f.published ? "rounded-full bg-fg" : "rotate-45 bg-bg"}`}
            />
            <p className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-sm font-semibold tabular-nums">
              {f.published ? <time dateTime={f.published}>{formatGraphDate(f.published)}</time> : "Date unknown"}
              <StudyTypeChip studyType={f.studyType} />
            </p>
            <p className="mt-1 text-base leading-snug">
              <span className="font-semibold">{f.variable1}</span>
              <span className="text-muted"> — associated with — </span>
              <span className="font-semibold">{f.variable2}</span>
            </p>
            <p className="mt-1 text-sm text-muted">
              Statistic reported: {f.statisticType}.
            </p>
            {f.spotCheck ? (
              <p className="mt-1 text-sm text-muted">
                AI-assisted spot-check, not human-reviewed:{" "}
                <span className="font-semibold text-fg">{spotStatusLabel(f.spotCheck.status)}</span>.{" "}
                {f.spotCheck.note}
              </p>
            ) : (
              <p className="mt-1 text-sm text-muted">Not covered by the spot-check.</p>
            )}
            <EvidenceLink systemId={f.systemId} pubmedId={f.pubmedId} doi={f.doi} className="mt-2" />
          </li>
        ))}
      </ol>
    </section>
  );
}
