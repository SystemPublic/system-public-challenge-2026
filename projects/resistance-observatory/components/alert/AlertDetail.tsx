"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { AlertEvent, Cell, Watch, WhoBasis } from "@/lib/alert/derive";
import { EVIDENCE_TIER, NEXT_STEPS_NOTE, NO_STUDY_TYPE, genomeContext, genomeSubject, itemSubject, matchingFigures, methodText } from "@/lib/alert/context";
import { composeAlert, composeEmail } from "@/lib/alert/compose";
import { ItemTier, StudyContextPanel, TierBadge as EvidenceTierBadge } from "./StudyContext";
import { BAND_LABEL, BAND_RULE, KIND_LABEL, SOURCE_LABEL, ci, eventCopy, frac, limits, pct, thresholdBasis, watchSentence } from "@/lib/alert/copy";
import { pmidStr, type AbstractPrevalence, type ClientPack, type GraphFinding, type MarkerDef, type Paper } from "@/lib/alert/pack";
import { PRESET_BADGE, SOURCES, TIER, buildEmail, buildReceipt, graphTierDetail, paperTierDetail, pickStakes, pubmedUrl, statText, type ReceiptSection } from "@/lib/alert/receipt";
import { KindGlyph, SourceGlyph, SOURCE_TONE } from "./glyphs";
import { useSystem, type LiveFinding, type LivePaper } from "./useSystem";
import { DEMO_EMAIL } from "./SendTestAlert";
import css from "./alert.module.css";

/* ------------------------------------------------------ graph finding --- */

function TierBadge({ checked }: { checked: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 ${checked ? "border-drug/60 text-drug" : "border-gap/60 text-gap"}`}>
      {checked ? `✓ ${TIER.checked}` : TIER.unverified}
    </span>
  );
}

/** One graph finding: the pair of variables, the statistic, its provenance. Never worded as cause and effect. */
export function FindingRow({ f, confirm = true, conceptLabel }: { f: GraphFinding; confirm?: boolean; conceptLabel?: (id: string) => string | null }) {
  const live = useSystem<LiveFinding>(confirm ? `op=finding&id=${encodeURIComponent(f.system_id)}` : null);
  const pmid = f.pubmed_id ? pmidStr(f.pubmed_id) : null;
  const checked = f.source_checked === true;
  const c = f.checked ?? null;
  const liveValue = live?.state === "live" && live.data.finding ? live.data.finding.statistic_value : undefined;
  const concepts = [f.variable_1_concept_id, f.variable_2_concept_id].filter((x): x is string => Boolean(x));
  return (
    <li className="rounded-lg border border-line bg-surface p-3 text-sm">
      <p className="leading-snug">
        <span className="font-medium">{f.variable_1}</span>
        <span className="mx-1.5 font-mono text-xs text-muted" title="An association between two variables; no direction is implied">
          ↔
        </span>
        <span className="font-medium">{f.variable_2}</span>
      </p>
      <p className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1">
        <span
          className={`rounded-full border px-2 py-px font-mono text-[0.66rem] ${f.study_type ? "border-fg/50 font-semibold text-fg" : "border-dashed border-line-strong text-muted"}`}
          title="Study type, as the System graph gives it"
        >
          {f.study_type ?? NO_STUDY_TYPE}
        </span>
        {statText(f) ? <span className="font-mono text-[0.8rem] font-semibold">{statText(f)}</span> : null}
      </p>
      <p className="mt-1 text-xs">
        <span className="text-muted">Population, per the graph: </span>
        {f.population ?? <span className="text-muted">not given</span>}
      </p>
      {c?.comparison ? (
        <p className="mt-1 text-xs">
          <span className="text-muted">Comparison, from the paper: </span>
          {c.comparison}
          {c.units ? ` (${c.units})` : ""}
        </p>
      ) : null}
      {c?.abstract_quote ? (
        <p className="mt-1.5 border-l-2 border-drug/50 pl-2 text-xs italic">
          “{c.abstract_quote}”{c.site ? <span className="not-italic text-muted"> · {c.site}</span> : null}
          {c.sample_size ? <span className="not-italic text-muted"> · {c.sample_size}</span> : null}
        </p>
      ) : null}
      {c?.review_notes ? <p className="mt-1 text-xs text-gap">Reviewer note: {c.review_notes}</p> : null}
      <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[0.68rem] text-muted">
        <TierBadge checked={checked} />
        {f.pub_year ? <span>published {f.pub_year}</span> : null}
        <span>system_id {f.system_id}</span>
        {f.study_id ? <span>study_id {f.study_id}</span> : null}
        {concepts.length ? <span>concepts {concepts.map((id) => (conceptLabel?.(id) ? `${conceptLabel(id)} ${id}` : id)).join(" | ")}</span> : null}
        {pmid ? (
          <a href={f.pubmed_url ?? pubmedUrl(pmid)} target="_blank" rel="noopener noreferrer" className="text-drug underline underline-offset-2">
            PMID {pmid} ↗
          </a>
        ) : null}
        {live?.state === "live" ? (
          live.data.vetted === false ? (
            <span className="text-gap">API: id not in the vetted set</span>
          ) : live.data.finding ? (
            <span title="Fetched from the System API just now" className="text-drug">
              API ✓ {String(liveValue)}
              {typeof liveValue === "number" && typeof f.statistic_value === "number" ? (liveValue === f.statistic_value ? " (matches snapshot)" : " (differs from snapshot)") : ""}
            </span>
          ) : (
            <span>API: id not returned</span>
          )
        ) : live?.state === "loading" ? (
          <span>API: checking…</span>
        ) : null}
      </p>
    </li>
  );
}

/* -------------------------------------------------------------- receipt --- */

const BADGE_TONE = {
  who: "border-drug/60 text-drug",
  checked: "border-drug/60 text-drug",
  preset: "border-gap/60 text-gap",
  unverified: "border-gap/60 text-gap",
} as const;

export function Receipt({ sections }: { sections: ReceiptSection[] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-line-strong bg-bg">
      <p className="flex items-center justify-between gap-2 border-b border-dashed border-line-strong px-3 py-2 font-mono text-[0.7rem] uppercase tracking-[0.16em]">
        <span className="font-semibold">Decision receipt</span>
        <span className="normal-case tracking-normal text-muted">every number, threshold and id this alert rests on</span>
      </p>
      {sections.map((s) => (
        <div key={s.title} className="border-b border-dashed border-line-strong px-3 py-2.5 last:border-b-0">
          <p className="mb-1.5 font-mono text-[0.66rem] uppercase tracking-[0.14em] text-muted">{s.title}</p>
          <dl className="grid grid-cols-[7.5rem_minmax(0,1fr)] gap-x-3 gap-y-1.5 text-[0.8rem]">
            {s.rows.map((r, i) => (
              <div key={i} className="contents">
                <dt className="font-mono text-[0.7rem] text-muted">{r.label}</dt>
                <dd className="min-w-0 break-words">
                  {r.text}{" "}
                  {r.badge ? <span className={`mr-1 inline-block rounded-full border px-2 py-px font-mono text-[0.66rem] ${BADGE_TONE[r.badge.tone]}`}>{r.badge.text}</span> : null}
                  {r.links?.map((l) => (
                    <a key={l.url} href={l.url} target="_blank" rel="noopener noreferrer" className="mr-2 whitespace-nowrap font-mono text-[0.7rem] text-drug underline underline-offset-2">
                      {l.label} ↗
                    </a>
                  ))}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      ))}
    </div>
  );
}

/* --------------------------------------------------------------- detail --- */

type Props = {
  event: AlertEvent;
  watch: Watch;
  marker: MarkerDef;
  country: string;
  basis: WhoBasis;
  pack: ClientPack;
  /** Every genome cell for the marker, any country: the local prior reads the earlier ones. */
  cells: Cell[];
  papers: Map<string, Paper>;
  asOfLine: string;
  emailConfigured: boolean | null;
  emailFrom: string | null;
  links: { forecast: string; learn: string };
  onClose: () => void;
};

function Section({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-line py-4 first:border-t-0 first:pt-0">
      <h3 className="mb-2 flex items-baseline gap-2 font-mono text-[0.7rem] uppercase tracking-[0.16em] text-muted">
        <span className="tabular-nums text-fg">{n}</span>
        {title}
      </h3>
      {children}
    </section>
  );
}

function Node({ tone, kicker, children }: { tone: "signal" | "drug" | "fg"; kicker: string; children: React.ReactNode }) {
  const t = tone === "signal" ? "border-signal/50 bg-signal-soft/40" : tone === "drug" ? "border-drug/50 bg-drug-soft/50" : "border-line-strong bg-surface-2/60";
  return (
    <div className={`min-w-0 flex-1 rounded-lg border p-2.5 ${t}`}>
      <p className="font-mono text-[0.62rem] uppercase tracking-[0.14em] text-muted">{kicker}</p>
      <div className="mt-1 text-[0.82rem] leading-snug">{children}</div>
    </div>
  );
}

export function AlertDetail(p: Props) {
  const { event: e, watch, marker, country, basis, pack } = p;
  const composed = useMemo(() => composeAlert({ e, watch, marker, country, basis, pack, cells: p.cells, papers: p.papers }), [e, watch, marker, country, basis, pack, p.cells, p.papers]);
  const { copy, tb, lim, paper, figure, stakes, extracted, graphFinding, graphLine, whoStatus, ctx, matched, itemDetail, receipt, stakesCaveat } = composed;
  const conceptLabel = (id: string) => pack.graph.concepts.find((c) => c.system_id === id)?.label ?? null;
  const [openUse, setOpenUse] = useState<string | null>(null);
  const outcomeIds = [...new Set(stakes.lead.map((f) => f.variable_2_concept_id).filter((x): x is string => Boolean(x)))];
  const drugConcepts = pack.graph.concepts.filter((c) => /^(sulfadoxine|pyrimethamine)$/i.test(c.label));
  const livePaper = useSystem<LivePaper>(e.pmid && /^\d+$/.test(e.pmid) ? `op=paper&pmid=${e.pmid}` : null);
  const th = pack.thresholds;
  const v = th.who_categories?.verbatim;
  const whoSource = th.who_categories?.sources?.[0] ?? { name: SOURCES.whoFallback.label, url: SOURCES.whoFallback.url };
  const esa = basis === "east_southern_africa";

  const [link, setLink] = useState("");
  useEffect(() => setLink(window.location.href), [e.id]);
  const email = composeEmail(composed, {
    e,
    watch,
    marker,
    country,
    link,
    asOf: p.asOfLine,
    extras: link ? { links: [{ label: "See this country on the Forecast map", url: new URL(p.links.forecast, link).toString() }] } : undefined,
  });

  return (
    <article aria-label={`Alert: ${copy.title}`} className="rounded-[var(--radius)] border border-line bg-surface p-5 shadow-[var(--shadow)]">
      <header className="mb-4 flex items-start gap-3">
        <span className={e.fired ? "mt-1 text-signal" : "mt-1 text-muted"}>
          <KindGlyph event={e} size={24} quiet={!e.fired} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[0.7rem] uppercase tracking-[0.14em] text-muted">
            <span>{KIND_LABEL[e.kind]}</span>
            <span aria-hidden>·</span>
            <span className={`inline-flex items-center gap-1 ${SOURCE_TONE[e.source]}`}>
              <SourceGlyph source={e.source} /> {SOURCE_LABEL[e.source]}
            </span>
            <span aria-hidden>·</span>
            <span>
              {e.dateBasis === "collection" ? "collected" : "published"} {e.year}
            </span>
            {e.strength ? (
              <span className={`rounded-full border px-2 py-0.5 normal-case tracking-normal ${e.strength === "strong" ? "border-signal/60 text-signal" : "border-line-strong"}`}>
                {e.strength === "strong" ? "strong signal" : e.strength === "weak" ? "weak signal" : "signal"}
              </span>
            ) : null}
            {!e.fired ? <span className="rounded-full border border-line-strong px-2 py-0.5 normal-case tracking-normal">context, not an alert</span> : null}
          </p>
          <h2 className="mt-1 font-display text-2xl font-semibold tracking-tight text-balance">
            {marker.label}, {country}: {copy.title}
          </h2>
        </div>
        <button type="button" onClick={p.onClose} className="rounded-full border border-line px-2.5 py-1 text-xs text-muted hover:text-fg" aria-label="Close alert">
          Close
        </button>
      </header>

      <Section n={1} title="Why it matters: the graph’s bridge from molecule to patient">
        <div className="flex flex-col items-stretch gap-1.5 sm:flex-row sm:items-center">
          <Node tone="signal" kicker="Molecular marker · genomes and PubMed">
            <strong>{marker.label}</strong>
            <span className="block text-xs text-muted">no graph finding names it alone</span>
          </Node>
          <span aria-hidden className="self-center font-mono text-muted">
            →
          </span>
          <Node tone="drug" kicker="Drug concepts in the graph">
            {drugConcepts.map((c) => (
              <span key={c.system_id} className="block">
                <strong>{c.label}</strong> <span className="font-mono text-[0.68rem] text-muted">{c.system_id}</span>
              </span>
            ))}
          </Node>
          <span aria-hidden className="self-center font-mono text-muted">
            →
          </span>
          <Node tone="fg" kicker="Patient outcomes in the graph">
            {outcomeIds.length ? (
              outcomeIds.slice(0, 3).map((id) => (
                <span key={id} className="block">
                  <strong>{conceptLabel(id) ?? stakes.lead.find((f) => f.variable_2_concept_id === id)?.variable_2 ?? "concept"}</strong> <span className="font-mono text-[0.68rem] text-muted">{id}</span>
                </span>
              ))
            ) : (
              <span className="text-muted">see findings below</span>
            )}
          </Node>
        </div>
        <p className="mt-2 text-xs text-muted">
          The surveillance data say where {marker.mutation} is; the graph says what {marker.drugShort} does for patients. Hand-checked findings from {country} come first where they exist.
        </p>

        {stakes.local.length > 0 ? (
          <div className="mt-3">
            <p className="mb-1.5 text-xs font-medium">
              From {country}: what a haplotype containing {marker.mutation} has been associated with
            </p>
            <ul className="space-y-2">
              {stakes.local.map((f) => (
                <FindingRow key={f.system_id} f={f} conceptLabel={conceptLabel} />
              ))}
            </ul>
          </div>
        ) : null}

        {stakes.groups.map((g, gi) => {
          const open = openUse === g.use;
          const shown = open ? g.findings : gi < 2 ? g.findings.slice(0, 1) : [];
          return (
            <div key={g.use} className="mt-3">
              <p className="mb-1.5 flex items-center justify-between gap-2 text-xs">
                <span className="font-medium">
                  What {marker.drugShort} does: {g.use}
                  {gi === 0 ? <span className="font-normal text-muted"> · the use most relevant to this region</span> : null}
                </span>
                {g.findings.length > shown.length || open ? (
                  <button type="button" className="shrink-0 text-muted underline underline-offset-2 hover:text-fg" onClick={() => setOpenUse(open ? null : g.use)} aria-expanded={open}>
                    {open ? "show fewer" : `show all ${g.findings.length}`}
                  </button>
                ) : null}
              </p>
              {shown.length ? (
                <ul className="space-y-2">
                  {shown.map((f) => (
                    <FindingRow key={f.system_id} f={f} confirm={gi === 0 || open} conceptLabel={conceptLabel} />
                  ))}
                </ul>
              ) : null}
            </div>
          );
        })}
        <p className="mt-3 text-xs text-muted">
          {stakesCaveat} The {pack.graph.stakes_sp.length} {marker.drugShort} findings were hand-selected for readability; they are a sample, not a systematic review.
        </p>
      </Section>

      <Section n={2} title="What changed">
        <p className="text-[0.95rem] leading-relaxed text-pretty">{e.quote ? copy.statement.split(" Its abstract says:")[0] : copy.statement}</p>
        {e.quote ? <blockquote className={`mt-3 ${css.quote}`}>“{e.quote}”</blockquote> : null}
        <p className="mt-2 text-xs text-muted">
          <span className="font-medium text-fg">Comparison basis.</span> {copy.basis}
        </p>
      </Section>

      <Section n={3} title="How much weight to give this: the triggering study">
        {ctx ? (
          <StudyContextPanel ctx={ctx} mutation={marker.mutation} study={pack.studyContext} matched={matched} papers={p.papers} />
        ) : e.source !== "genomes" ? (
          <ItemTier source={e.source} detail={itemDetail} />
        ) : null}
      </Section>

      <Section n={4} title="The evidence">
        {e.cell ? (
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 font-mono text-[0.8rem]">
            <dt className="text-muted">this cell</dt>
            <dd>
              <strong>{frac(e.cell)}</strong> · {pct(e.cell.pct)} · {ci(e.cell)} · {country} · collected {e.cell.year}
            </dd>
            {e.prev ? (
              <>
                <dt className="text-muted">compared with</dt>
                <dd>
                  {frac(e.prev)} · {pct(e.prev.pct)} · {ci(e.prev)} · collected {e.prev.year}
                </dd>
              </>
            ) : null}
            {e.a581g ? (
              <>
                <dt className="text-muted">A581G, same cell</dt>
                <dd>
                  {frac(e.a581g)} · {pct(e.a581g.pct)} · {ci(e.a581g)}
                </dd>
              </>
            ) : e.a581gUnjudged ? (
              <>
                <dt className="text-muted">A581G, same cell</dt>
                <dd>not tested (or under the minimum): “very high” cannot be judged</dd>
              </>
            ) : null}
            <dt className="text-muted">source</dt>
            <dd className="font-sans text-sm">
              <a href={SOURCES.pf8.url} target="_blank" rel="noopener noreferrer" className="text-drug underline underline-offset-2">
                {SOURCES.pf8.label} ↗
              </a>
              , dated by collection year. Intervals are Wilson 95%, computed here.
            </dd>
          </dl>
        ) : (
          <div className="space-y-1.5 text-sm">
            {paper ? (
              <>
                <p className="font-medium leading-snug">{paper.title}</p>
                <p className="text-muted">
                  {paper.journal ? <em>{paper.journal}</em> : null}
                  {paper.journal ? ", " : ""}published {paper.pub_month ? `${paper.pub_month} ` : ""}
                  {paper.pub_year}
                </p>
              </>
            ) : null}
            {figure ? (
              <p className="font-mono text-[0.78rem] text-muted">
                {[
                  figure.prevalence_pct != null ? `${figure.prevalence_pct}% as stated` : null,
                  figure.numerator != null && figure.denominator != null ? `${figure.numerator} of ${figure.denominator}` : null,
                  figure.site ? `site: ${figure.site}` : null,
                  figure.year_start ? `collected ${figure.year_start}${figure.year_end && figure.year_end !== figure.year_start ? ` to ${figure.year_end}` : ""}` : null,
                  figure.population ? `population: ${figure.population}` : null,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            ) : null}
            {e.source === "papers" ? (
              <p>
                <EvidenceTierBadge source="papers" small />
              </p>
            ) : null}
            {graphFinding ? (
              <ul>
                <FindingRow f={graphFinding} conceptLabel={conceptLabel} />
              </ul>
            ) : null}
            {e.pmid ? (
              <p>
                <a href={paper?.url ?? pubmedUrl(e.pmid)} target="_blank" rel="noopener noreferrer" className="font-medium text-drug underline decoration-drug/40 underline-offset-4 hover:decoration-drug">
                  Read the paper on PubMed ↗
                </a>{" "}
                <span className="font-mono text-[0.7rem] text-muted">PMID {e.pmid}</span>
              </p>
            ) : null}
            {e.source === "papers" ? <p className="text-xs text-gap">Machine-read from the abstract; quoted word for word; not checked by hand.</p> : null}
          </div>
        )}
      </Section>

      <Section n={5} title="What the graph has on it">
        <p className="text-sm">{graphLine}</p>
        {extracted.length > 0 ? (
          <>
            <p className="mb-1.5 mt-2 text-xs text-muted">What it did extract from this paper:</p>
            <ul className="space-y-2">
              {extracted.slice(0, 4).map((f) => (
                <FindingRow key={f.system_id} f={f} confirm={false} conceptLabel={conceptLabel} />
              ))}
            </ul>
            {extracted.length > 4 ? <p className="mt-1.5 font-mono text-[0.7rem] text-muted">{extracted.length - 4} more in the curation panel below.</p> : null}
          </>
        ) : null}
        {livePaper?.state === "live" ? (
          <p className="mt-2 font-mono text-[0.7rem] text-muted">
            API check:{" "}
            {livePaper.data.inGraph
              ? `the API holds this paper (study_id ${livePaper.data.study?.study_id}) with ${livePaper.data.total} association${livePaper.data.total === 1 ? "" : "s"}; ${livePaper.data.findings.length} in the vetted set`
              : "the API does not hold this paper"}
            {livePaper.data.quarantined > 0 ? `; ${livePaper.data.quarantined} more returned by the API are not in the vetted set and are not shown` : ""}.
          </p>
        ) : livePaper?.state === "snapshot" ? (
          <p className="mt-2 font-mono text-[0.7rem] text-muted">API check unavailable; the in-graph flag is from the data pack.</p>
        ) : null}
      </Section>

      <Section n={6} title="WHO status of the marker">
        {whoStatus.map((s) => (
          <p key={s} className="mb-1.5 text-sm">
            {s}
          </p>
        ))}
        {th.marker?.who_compendium?.url ? (
          <p className="font-mono text-[0.7rem] text-muted">
            <a href={th.marker.who_compendium.url} target="_blank" rel="noopener noreferrer" className="text-drug underline underline-offset-2">
              {th.marker.who_compendium.source ?? "WHO compendium"} ↗
            </a>
          </p>
        ) : null}
        {esa && v?.continue_quote ? (
          <div className="mt-3 rounded-lg border border-drug/40 bg-drug-soft/40 p-3 text-sm">
            <p className="mb-1 font-medium">WHO says SP in pregnancy should continue even where resistance is high.</p>
            <p className="italic">“{v.continue_quote}”</p>
            <p className="mt-1 font-mono text-[0.68rem] text-muted">{v.continue_where}</p>
          </div>
        ) : null}
      </Section>

      <Section n={7} title="Threshold and its basis">
        <p className="text-sm">
          <span className={`mr-2 inline-block rounded-full border px-2 py-0.5 font-mono text-[0.7rem] ${tb.published ? "border-drug/60 text-drug" : "border-gap/60 text-gap"}`}>
            {tb.published ? "Published by WHO" : watch.trigger === "first_detection" ? "Project rule" : PRESET_BADGE}
          </span>
          {tb.text}.
        </p>
        {e.band ? (
          <p className="mt-2 font-mono text-[0.78rem] text-muted">
            {BAND_LABEL[e.band]} band = {BAND_RULE[e.band]}
          </p>
        ) : null}
        {v?.quote ? (
          <details className="mt-2 text-sm">
            <summary className="cursor-pointer text-muted hover:text-fg">WHO wording</summary>
            <div className="mt-2 space-y-2.5 rounded-lg border border-line bg-bg p-3 text-[0.85rem] leading-relaxed">
              <p className="italic">“{v.quote}”</p>
              <p className="font-mono text-[0.68rem] text-muted">{v.where}</p>
              {v.programme_quote ? (
                <>
                  <p className="italic">“{v.programme_quote}”</p>
                  <p className="font-mono text-[0.68rem] text-muted">{v.programme_where}</p>
                </>
              ) : null}
              {v.note ? <p className="text-xs text-muted">{v.note}</p> : null}
              {th.who_categories?.limits ? <p className="text-xs text-muted">{th.who_categories.limits}</p> : null}
              <p>
                <a href={whoSource.url} target="_blank" rel="noopener noreferrer" className="font-mono text-[0.72rem] text-drug underline underline-offset-2">
                  {whoSource.name} ↗
                </a>
              </p>
            </div>
          </details>
        ) : null}
      </Section>

      <Section n={8} title="What this alert cannot tell you">
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          {lim.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </Section>

      <div className="border-t border-line pt-4">
        <Receipt sections={receipt} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Link href={p.links.forecast} className="rounded-full border border-line-strong px-3.5 py-1.5 text-sm font-medium hover:bg-surface-2">
          See on map →
        </Link>
        <Link href={p.links.learn} className="rounded-full border border-line-strong px-3.5 py-1.5 text-sm font-medium hover:bg-surface-2">
          What is {marker.mutation}? →
        </Link>
      </div>

      <EmailPanel key={e.id} subject={email.subject} text={email.text} html={email.html} configured={p.emailConfigured} from={p.emailFrom} />
    </article>
  );
}

/* --------------------------------------------------------------- email --- */

type SendState = { s: "idle" } | { s: "sending" } | { s: "sent"; id: string; to: string } | { s: "error"; message: string };

function EmailPanel({ subject, text, html, configured, from }: { subject: string; text: string; html: string; configured: boolean | null; from: string | null }) {
  const [to, setTo] = useState(DEMO_EMAIL);
  const [state, setState] = useState<SendState>({ s: "idle" });
  const [view, setView] = useState<"none" | "html" | "text">("none");

  async function send(ev: React.FormEvent) {
    ev.preventDefault();
    if (!configured) return;
    setState({ s: "sending" });
    try {
      const res = await fetch("/api/alert/email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to: to.trim(), subject, text, html }),
      });
      const json = (await res.json()) as { ok?: boolean; id?: string; error?: string; to?: string };
      if (json.ok && json.id) setState({ s: "sent", id: json.id, to: json.to ?? to });
      else setState({ s: "error", message: json.error ?? `HTTP ${res.status}` });
    } catch (err) {
      setState({ s: "error", message: err instanceof Error ? err.message : String(err) });
    }
  }

  return (
    <section className="mt-4 rounded-lg border border-line bg-bg p-4" aria-label="Email this alert">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-mono text-[0.7rem] uppercase tracking-[0.16em] text-muted">The email a subscriber would receive</h3>
        <div className="flex gap-1 text-xs" role="group" aria-label="Email preview">
          {(["html", "text", "none"] as const).map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => setView(k)}
              aria-pressed={view === k}
              className={`rounded-full px-2.5 py-1 ${view === k ? "bg-fg text-bg" : "border border-line text-muted hover:text-fg"}`}
            >
              {k === "html" ? "Preview" : k === "text" ? "Plain text" : "Hide"}
            </button>
          ))}
        </div>
      </div>
      <p className="mt-2 text-sm">
        <span className="font-mono text-[0.7rem] text-muted">Subject: </span>
        {subject}
      </p>
      {view === "html" ? (
        <iframe title="Email preview" sandbox="" srcDoc={`<body style="margin:0;background:#050d17">${html}</body>`} className="mt-2 h-[26rem] w-full rounded border border-line bg-bg" />
      ) : view === "text" ? (
        <pre className="mt-2 max-h-[26rem] overflow-auto whitespace-pre-wrap rounded border border-line bg-surface p-3 font-mono text-[0.72rem] leading-relaxed">{text}</pre>
      ) : null}

      <form onSubmit={send} className="mt-3 flex flex-wrap items-center gap-2">
        <label className="sr-only" htmlFor="alert-email-to">
          Recipient email address
        </label>
        <input
          id="alert-email-to"
          type="email"
          required
          value={to}
          onChange={(e) => setTo(e.target.value)}
          placeholder="you@institute.org"
          disabled={!configured}
          className="h-9 min-w-0 flex-1 rounded-full border border-line-strong bg-surface px-3.5 text-sm disabled:opacity-50"
        />
        <button type="submit" disabled={!configured || state.s === "sending"} className="h-9 rounded-full bg-fg px-4 text-sm font-medium text-bg disabled:opacity-40">
          {configured === null ? "Checking…" : !configured ? "Preview only" : state.s === "sending" ? "Sending…" : "Send this alert"}
        </button>
      </form>
      <p className="mt-2 text-xs text-muted" aria-live="polite">
        {configured === false ? (
          "No email key is configured on this server, so nothing can be sent. The preview is exactly what would go out, receipt included."
        ) : state.s === "sent" ? (
          <span className="text-drug">
            ✓ Sent · Resend ID <span className="font-mono">{state.id}</span> · to {state.to}
          </span>
        ) : state.s === "error" ? (
          <span className="text-signal">Not sent. The provider said: “{state.message}”</span>
        ) : configured ? (
          `Sent through Resend from ${from ?? "the configured sender"}. The test sender only delivers to the account owner’s own address.`
        ) : null}
      </p>
    </section>
  );
}
