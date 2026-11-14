import type { Metadata } from "next";
import { Suspense } from "react";
import Link from "next/link";
import { Placeholder } from "@/components/Placeholder";
import { buildEhrPlan, KB_FILE, PANEL_FILE } from "@/components/ehr/ehrPlan";
import { RISK } from "@/lib/risk";
import { HOURLY_FILE } from "@/lib/synthetic";

export const metadata: Metadata = { title: "EHR side panel · Cool-Aid" };

// P6: the patient's heat plan in a narrow EHR side-panel layout (~400 px).
// Same sources as the patient plan (/phone/[id]); see components/ehr/ehrPlan.ts.
export default function EhrPanelPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<p className="text-ink-muted">Loading…</p>}>
      <EhrPanel params={params} />
    </Suspense>
  );
}

async function EhrPanel({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const plan = buildEhrPlan(id);

  return (
    <div className="flex justify-center md:justify-end">
      <aside
        aria-label="Heat plan side panel"
        className="w-full max-w-[400px] overflow-hidden rounded-tile border border-line-strong bg-white shadow-sm"
      >
        <header className="border-b border-line bg-surface px-4 py-2">
          <p className="text-sm font-semibold text-ink">Heat plan · Cool-Aid</p>
          <p className="text-xs text-ink-muted">Prototype, designed to embed via SMART on FHIR / CDS Hooks.</p>
        </header>

        {!plan ? (
          <div className="p-4">
            <Placeholder title={`Patient ${id}`}>Patient not found in {PANEL_FILE}</Placeholder>
          </div>
        ) : (
          <div className="space-y-5 p-4 text-sm">
            {/* Who + group */}
            <section className="space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-base font-semibold text-ink">{plan.name}</p>
                  <p className="text-xs text-ink-muted">
                    {plan.age} y · ZIP {plan.zip} · Synthetic patient
                  </p>
                </div>
                <span className={`shrink-0 rounded-full border px-3 py-0.5 text-sm font-semibold ${RISK[plan.group].chip}`}>
                  {RISK[plan.group].label} risk
                </span>
              </div>
              <p className="text-ink">{plan.why}</p>
            </section>

            {/* What to do */}
            <section className="space-y-1.5">
              <h2 className="font-semibold text-ink">What to do during this heat wave</h2>
              <ul className="list-disc space-y-1 pl-5 text-ink">
                {plan.todo.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </section>

            {/* Nearest cool place */}
            <section className={`space-y-1 rounded-tile p-3 ${RISK.low.tint}`}>
              <h2 className="font-semibold text-ink">Nearest cool place</h2>
              {plan.cool ? (
                <>
                  <p className="text-ink">
                    <b>{plan.cool.name}</b>
                    <br />
                    {plan.cool.address}
                    {plan.cool.note && (
                      <>
                        <br />
                        <span className="text-sm text-ink-muted">{plan.cool.note}</span>
                      </>
                    )}
                  </p>
                  <p className="text-ink">
                    {plan.cool.walkMin != null && <>About {plan.cool.walkMin} min walk</>}
                    {plan.cool.leaveBy && <> · leave by {plan.cool.leaveBy}</>}
                    {plan.cool.hours && <> · open {plan.cool.hours}</>}
                  </p>
                  {plan.cool.notes.length > 0 && (
                    <p className="text-xs text-ink-muted">{plan.cool.notes.join(" · ")}. Call ahead.</p>
                  )}
                </>
              ) : (
                <Placeholder title="Nearest cool place">Data goes here: {PANEL_FILE} (cooling.best)</Placeholder>
              )}
            </section>

            {/* Medicines in heat */}
            <section className="space-y-1.5">
              <h2 className="font-semibold text-ink">Medicines in heat</h2>
              {plan.meds.length ? (
                <ul className="space-y-2">
                  {plan.meds.map((m) => (
                    <li key={m.name} className="border-l-2 border-line-strong pl-2">
                      <p className="font-medium capitalize text-ink">
                        {m.name}
                        {m.kbName && m.kbName.toLowerCase() !== m.name && (
                          <span className="font-normal normal-case text-ink-muted"> ({m.kbName})</span>
                        )}
                      </p>
                      <p className="text-ink">{m.line ?? <span className="text-ink-muted">No heat line in {KB_FILE} yet.</span>}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-ink-muted">No heat-risk medicines on file.</p>
              )}
            </section>

            <div className="flex flex-wrap gap-2">
              <Link href={`/phone/${plan.id}`} className="rounded-full border border-line-strong px-3 py-1 text-sm hover:bg-surface">
                Patient&apos;s own plan
              </Link>
              <Link href="/board" className="rounded-full border border-line-strong px-3 py-1 text-sm hover:bg-surface">
                All patients
              </Link>
            </div>

            {/* Evidence, collapsed */}
            <details className="rounded-tile border border-line">
              <summary className="cursor-pointer px-3 py-2 font-semibold text-ink">See the evidence</summary>
              <div className="space-y-3 border-t border-line px-3 py-2 text-xs text-ink">
                {plan.evidence.bullets.length > 0 && (
                  <div>
                    <p className="font-semibold">Why this group</p>
                    <ul className="list-disc pl-4">
                      {plan.evidence.bullets.map((b) => (
                        <li key={b}>{b}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {plan.evidence.combos.length > 0 && (
                  <div>
                    <p className="font-semibold">Medicine combinations</p>
                    <ul className="list-disc pl-4">
                      {plan.evidence.combos.map((c) => (
                        <li key={c.label}>
                          <b>{c.label}.</b> {c.evidence}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {plan.evidence.sources.length > 0 && (
                  <div>
                    <p className="font-semibold">Sources</p>
                    <ul className="list-disc pl-4">
                      {plan.evidence.sources.map((s) => (
                        <li key={s.url}>
                          <a href={s.url} target="_blank" rel="noreferrer" className="underline">
                            {s.label}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div>
                  <p className="font-semibold">Cool place and timing</p>
                  {plan.evidence.coolNote && <p>{plan.evidence.coolNote}</p>}
                  {plan.evidence.coolTechnical.map((c) => (
                    <p key={c}>{c}</p>
                  ))}
                </div>
                <p className="text-ink-muted">
                  Data: {PANEL_FILE} (as of {plan.asOf}, heat wave replay), {HOURLY_FILE}, {KB_FILE}. Synthetic patients
                  only. Not clinical advice.
                </p>
              </div>
            </details>
          </div>
        )}
      </aside>
    </div>
  );
}
