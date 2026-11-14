import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import { isPublicClaim } from "@lib/types/knowledge-base.ts";
import {
  BucketChip,
  CompassArrowMark,
  Dash,
  EvidenceMeter,
  GapBadge,
  LayerTag,
  LevelMeter,
  VerificationBadge,
} from "@/components/badges";
import { KbSourceBanner } from "@/components/KbSourceBanner";
import { GuidanceQuote } from "@/components/medicines/GuidanceQuote";
import {
  ACTOR_LABEL,
  guidanceSaysWhatToDo,
  labelWarnsAboutHeat,
  PHASE_LABEL,
  PHASE_ORDER,
  prescriberText,
} from "@/components/medicines/plain";
import { getDrug, getDrugs, loadKb, primaryBucket } from "@/lib/kb";
import { BUCKETS } from "@/lib/ui";

export function generateStaticParams() {
  return getDrugs().map((d) => ({ id: d.id }));
}

export async function generateMetadata({ params }: PageProps<"/drug/[id]">): Promise<Metadata> {
  const { id } = await params;
  const d = getDrug(decodeURIComponent(id));
  return { title: `${d?.names?.display ?? "Drug"} · Cool-Aid` };
}

function Section({ title, plain, children }: { title: string; plain?: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-line pt-4">
      <h3 className="font-semibold">{title}</h3>
      {plain && <p className="mb-2 text-sm text-ink-muted">{plain}</p>}
      <div className="space-y-2">{children}</div>
    </section>
  );
}

function List({ items }: { items: string[] | undefined }) {
  if (!items || items.length === 0) return <Dash />;
  return <span>{items.join(", ")}</span>;
}

export default function DrugPage({ params }: PageProps<"/drug/[id]">) {
  return (
    <Suspense fallback={<p className="mx-auto max-w-3xl text-ink-muted">Loading medicine…</p>}>
      <DrugBody params={params} />
    </Suspense>
  );
}

async function DrugBody({ params }: { params: PageProps<"/drug/[id]">["params"] }) {
  const { id } = await params;
  const d = getDrug(decodeURIComponent(id));
  if (!d) notFound();
  const { source, file } = loadKb();
  const bucket = primaryBucket(d);
  const b = bucket ? BUCKETS[bucket] : null;
  const claims = (d.claims ?? []).filter(isPublicClaim);
  const g = d.guidance;
  const patientMsgs = d.patient_messages ?? [];
  const steps = [...(d.timeline ?? [])].sort((x, y) => PHASE_ORDER.indexOf(x.phase) - PHASE_ORDER.indexOf(y.phase));
  const label = labelWarnsAboutHeat(d);
  const guide = guidanceSaysWhatToDo(d);

  return (
    <article className="max-w-3xl space-y-8">
      <Link href="/medicines" className="text-sm text-ink-muted underline underline-offset-[3px] hover:text-ink">
        ← All medicines
      </Link>
      <KbSourceBanner source={source} file={file} />

      {/* Outcome first: the plain message and what to do. */}
      <section className={`border-l-4 pl-5 ${b ? b.ink : "border-line-strong"}`}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-ink">{d.names?.display ?? d.id}</h1>
            {d.names?.class_label && <p className="text-ink-muted">{d.names.class_label}</p>}
          </div>
          {bucket && <BucketChip bucket={bucket} size="md" />}
        </div>
        <p className="mt-4 text-xl leading-snug text-ink">
          {d.label_line || <Dash what="No plain message yet" />}
        </p>
      </section>

      <section aria-labelledby="todo-h" className="space-y-3">
        <h2 id="todo-h" className="text-xl font-semibold">
          What to do
        </h2>
        {steps.length === 0 ? (
          <p className="text-sm text-ink-muted">
            No steps yet <Dash what="No timeline in data/kb/knowledge_base.json" />
          </p>
        ) : (
          <ol className="space-y-3">
            {steps.map((s, i) => (
              <li key={`${s.phase}-${i}`} className="flex gap-3">
                <span
                  aria-hidden
                  className={`mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-sm font-bold ${
                    b ? b.tint : "border-line-strong"
                  }`}
                >
                  {i + 1}
                </span>
                <div>
                  <p className="text-sm font-semibold text-ink-muted">
                    {PHASE_LABEL[s.phase] ?? s.phase}
                    {s.who?.length ? ` · ${s.who.map((w) => ACTOR_LABEL[w] ?? w).join(", ")}` : ""}
                  </p>
                  <p className="text-ink">{s.action}</p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>

      {/* Everything else: one click away. */}
      <details className="group rounded-lg border border-line bg-card px-4 shadow-sm">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 py-3 font-semibold [&::-webkit-details-marker]:hidden">
          <span>See the evidence</span>
          <span aria-hidden className="text-ink-muted transition-transform group-open:rotate-180">
            ▾
          </span>
        </summary>
        <div className="space-y-6 pb-6">
          <Section title="In short">
            <p className="text-sm">{d.evidence?.plain_summary || <Dash />}</p>
            <dl className="grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <dt className="font-semibold">How strong is the evidence</dt>
                <dd>
                  <EvidenceMeter meter={d.evidence?.meter} />
                </dd>
              </div>
              <div>
                <dt className="font-semibold">Who prescribes it</dt>
                <dd>{prescriberText(d) || <Dash />}</dd>
              </div>
              <div>
                <dt className="font-semibold">Label warns about heat</dt>
                <dd>
                  {label === null ? <Dash /> : label ? "Yes" : "No"} · <span className="text-ink-muted">{d.fda_label?.plain}</span>
                </dd>
              </div>
              <div>
                <dt className="font-semibold">Guidance says what to do</dt>
                <dd>{guide === null ? <Dash /> : guide ? "Yes" : "No"}</dd>
              </div>
              <div>
                <dt className="font-semibold">Higher-risk groups</dt>
                <dd>
                  <List items={d.higher_risk_groups} />
                </dd>
              </div>
              {d.pediatric_note && (
                <div>
                  <dt className="font-semibold">Children</dt>
                  <dd>{d.pediatric_note}</dd>
                </div>
              )}
            </dl>
          </Section>

          <div className="grid gap-4 md:grid-cols-2">
            <Section title="Check on this person (FLAG)" plain="How strongly this prescription marks someone to contact.">
              <LevelMeter level={d.flag?.level} />
              <p className="text-sm">{d.flag?.rationale || <Dash />}</p>
            </Section>
            <Section title="Rethink the medicine (CHANGE)" plain="How strongly the evidence supports changing the drug itself.">
              <LevelMeter level={d.change?.level} />
              <p className="text-sm">{d.change?.rationale || <Dash />}</p>
            </Section>
          </div>

          <Section title="Heat Dose Compass" plain="Direction only, not doses. There isn't enough data for numbers.">
            <CompassArrowMark arrow={d.compass?.arrow} large />
            <dl className="grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <dt className="font-semibold">Why</dt>
                <dd>{d.compass?.mechanism || <Dash />}</dd>
              </div>
              <div>
                <dt className="font-semibold">Triggers</dt>
                <dd>
                  <List items={d.compass?.triggers} />
                </dd>
              </div>
              <div>
                <dt className="font-semibold">What to monitor</dt>
                <dd>
                  <List items={d.compass?.monitor} />
                </dd>
              </div>
              <div>
                <dt className="font-semibold">Evidence</dt>
                <dd>
                  <EvidenceMeter meter={d.compass?.evidence_meter} />
                </dd>
              </div>
            </dl>
          </Section>

          <Section title="Studies and reports" plain="System graph, published studies and FDA reports are kept separate.">
            {claims.length === 0 ? (
              <p className="text-sm text-ink-muted">
                No verified claims yet <Dash />
              </p>
            ) : (
              <ul className="divide-y divide-line">
                {claims.map((c) => (
                  <li key={c.id} className="flex flex-wrap items-start gap-2 py-2 text-sm">
                    <LayerTag layer={c.layer} />
                    <VerificationBadge code={c.badge_code} />
                    <div className="min-w-0 flex-1">
                      <p>{c.plain || c.text}</p>
                      <p className="text-xs text-ink-muted" title={c.text}>
                        {c.number?.display ? `${c.number.display} · ` : ""}
                        {c.source?.url ? (
                          <a href={c.source.url} className="underline" target="_blank" rel="noreferrer">
                            {c.source.label}
                          </a>
                        ) : (
                          c.source?.label
                        )}
                        {c.population ? ` · ${c.population}` : ""}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="What heat guidance says" plain="Which official heat guides mention this medicine, and their words.">
            <p className="flex flex-wrap items-center gap-2 text-sm">
              {g?.n_jurisdictions ? (
                <>
                  {g.jurisdictions_mentioning} of {g.n_jurisdictions} guides mention it; {g.jurisdictions_specific_action} say
                  what to do for this medicine.
                </>
              ) : (
                <Dash what="Guidance not coded yet" />
              )}
              {g?.gap && <GapBadge />}
            </p>
            {g?.gap_reason && <p className="text-sm text-ink-muted">{g.gap_reason}</p>}
            {(g?.by_source ?? []).filter((s) => s.mention_level !== "none").length > 0 && (
              <ul className="space-y-2 text-sm">
                {g!.by_source
                  .filter((s) => s.mention_level !== "none")
                  .map((s) => (
                    <li key={s.source_id}>
                      <span className="font-semibold">{s.source_id}</span>{" "}
                      <span className="text-xs text-ink-muted">({s.jurisdiction})</span>:{" "}
                      <GuidanceQuote sourceId={s.source_id} quote={s.quote} />
                    </li>
                  ))}
              </ul>
            )}
          </Section>

          <div className="grid gap-4 md:grid-cols-2">
            <Section title="Risky combinations" plain="Common partners that stack the same heat risk.">
              {(d.combinations ?? []).length === 0 ? (
                <Dash />
              ) : (
                <ul className="space-y-1 text-sm">
                  {d.combinations.map((c) => (
                    <li key={c.id}>
                      <span className="font-semibold">{c.label}</span>: {c.plain}
                    </li>
                  ))}
                </ul>
              )}
            </Section>
            <Section
              title="Lower heat-risk options to consider"
              plain="For a spring review, never an automatic switch. Never stop abruptly."
            >
              {(d.alternatives ?? []).length === 0 ? (
                <Dash />
              ) : (
                <ul className="space-y-2 text-sm">
                  {d.alternatives.map((a) => (
                    <li key={a.name}>
                      <span className="font-semibold">{a.name}</span>: {a.why}
                      <br />
                      <span className="text-ink-muted">
                        What you lose: {a.what_is_lost || "—"} · {a.heat_evidence_label} · {a.caution}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Section>
          </div>

          <Section title="What the patient app says" plain="Exactly what patients on this medicine are told.">
            {patientMsgs.length === 0 ? (
              <Dash what="No patient message yet" />
            ) : (
              patientMsgs.map((m) => (
                <blockquote key={m.situation} className="rounded border-l-4 border-line-strong bg-surface p-3 text-sm">
                  <span className="block text-xs font-semibold text-ink-muted">{m.situation.replace(/_/g, " ")}</span>
                  {m.en}
                </blockquote>
              ))
            )}
          </Section>

          {(d.gaps ?? []).length > 0 && (
            <Section title="What we don't know" plain="Gaps are shown, not hidden.">
              <ul className="list-disc pl-5 text-sm">
                {d.gaps.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </Section>
          )}
          <p className="text-xs text-ink-muted">Sources: {file ?? "inline fallback"}</p>
        </div>
      </details>
    </article>
  );
}
