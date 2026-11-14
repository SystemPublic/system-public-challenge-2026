"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { RISK, RISK_ORDER, type RiskGroup } from "@/lib/risk";
import { BUCKETS } from "@/lib/ui";
import type { Bucket } from "@lib/types/knowledge-base.ts";

// The group's risk color stays on hover (the Button default hovers to the app teal).
const GROUP_HOVER: Record<string, string> = { high: "hover:bg-risk-high", medium: "hover:bg-risk-medium", low: "hover:bg-risk-low" };

// Medicine boxes take the Evidence Map's action-bucket color (left accent + chip).
const BUCKET_ACCENT: Record<Bucket, string> = {
  hold_or_substitute: "border-l-hold-solid",
  adjust_dose: "border-l-adjust-solid",
  monitor: "border-l-monitor-solid",
  storage: "border-l-store-solid",
};

/** Same paper can appear twice in a drug's claims; show each link once. */
const uniqueSources = (s: { label: string; url: string }[]) =>
  s.filter((x, i) => s.findIndex((y) => y.url === x.url && y.label === x.label) === i);

function StudyChip({ label, n }: { label: string; n: number | null }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-page px-2 py-0.5 text-xs">
      <span>{label}</span>
      <span className={`rounded-full px-1.5 font-semibold tabular-nums ${n ? "bg-layer-graph-bg text-layer-graph-fg" : "bg-surface text-ink-muted"}`}>
        {n ?? 0}
      </span>
    </span>
  );
}

export interface BoardRow {
  id: string;
  name: string;
  age: number;
  zip: string;
  group: RiskGroup;
  why: string;
  callInstead: boolean;
  detail: {
    bullets: string[];
    meds: { name: string; kbId: string | null; kbName: string | null; bucket: Bucket | null; line: string | null; sources: { label: string; url: string }[] }[];
    pathways: {
      label: string;
      drugs: string[];
      stacked: boolean;
      system: { mediator: string; heatStudies: number | null; drugLegs: { drug: string; systemGroup: string | null; studies: number | null }[] }[];
      note: string;
    }[];
    systemSource: string | null;
    caveat: string | null;
  };
}

type Alert = {
  id: number; patient_id: string; status: string; channel: string; steps_done: number; total_steps: number;
  elapsed_min: number; sent_at: string; next_step: { atMin: number; action: string; to: string } | null;
};
type Message = { id: number; patient_id: string | null; recipient: string; channel: string; body: string; note: string | null; created_at: string };
type State = { demo_time: string; alerts: Alert[]; messages: Message[] };

const POLL_MS = 2500;

const STATUS: Record<string, { label: string; cls: string }> = {
  sent: { label: "Waiting for reply", cls: "text-adjust-ink" },
  sent_done: { label: "Text sent", cls: "text-ink-muted" },
  acknowledged: { label: "Replied OK", cls: "text-verify-double-fg" },
  escalated_contact: { label: "Contact asked to check", cls: "text-monitor-ink" },
  escalated_clinic: { label: "Call this patient", cls: "text-hold-ink" },
  resolved: { label: "Resolved", cls: "text-ink-muted" },
};

const t = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

async function post(url: string, body: unknown) {
  await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
}

export function Board({ rows, source, questionnaireFile, asOf }: { rows: BoardRow[]; source: string; questionnaireFile: string; asOf: string }) {
  const [state, setState] = useState<State | null>(null);
  const [group, setGroup] = useState<RiskGroup>("high");
  const [open, setOpen] = useState<BoardRow | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const names = useMemo(() => new Map(rows.map((r) => [r.id, r.name])), [rows]);

  const refresh = useCallback(async () => {
    try {
      const r = await fetch("/api/loop/board", { cache: "no-store" });
      setState(await r.json());
      setError(null);
    } catch {
      setError("Can't reach the server");
    }
  }, []);

  useEffect(() => {
    const first = setTimeout(refresh, 0);
    const id = setInterval(refresh, POLL_MS);
    return () => { clearTimeout(first); clearInterval(id); };
  }, [refresh]);

  const latest = new Map<string, Alert>();
  for (const a of state?.alerts ?? []) if (!latest.has(a.patient_id)) latest.set(a.patient_id, a);

  const counts = Object.fromEntries(RISK_ORDER.map((g) => [g, rows.filter((r) => r.group === g).length])) as Record<RiskGroup, number>;
  const shown = rows.filter((r) => r.group === group);
  const texts = shown.filter((r) => !r.callInstead);
  const calls = shown.filter((r) => r.callInstead);

  const send = async (ids: string[], mode: "text" | "call" = "text") => {
    if (!ids.length) return;
    setBusy(true);
    await post("/api/loop/alerts", { patientIds: ids, scenario: "replay", mode });
    setBusy(false);
    refresh();
  };
  const ff = async (minutes: number) => { await post("/api/loop/clock", { minutes }); refresh(); };
  const reset = async () => { await post("/api/loop/clock", { reset: true }); refresh(); };

  const statusOf = (id: string) => {
    const a = latest.get(id);
    if (!a) return null;
    const key = a.status === "sent" && !a.next_step ? "sent_done" : a.status;
    return { ...(STATUS[key] ?? STATUS.sent), a };
  };

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold tracking-tight">Who needs help today</h1>
          <p className="text-ink-muted">
            Heat wave day {asOf}. {rows.length} synthetic patients, grouped by their medicines and their home.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-ink-muted" aria-label="Demo clock">
          <span>
            Demo clock <span className="font-semibold tabular-nums text-ink">{state ? t(state.demo_time) : "—"}</span>
          </span>
          {[5, 15, 45].map((m) => (
            <button key={m} onClick={() => ff(m)} className="text-sm text-ink-muted underline underline-offset-[3px] hover:text-ink">+{m} min</button>
          ))}
          <button onClick={reset} className="text-sm text-ink-muted underline underline-offset-[3px] hover:text-ink">Reset</button>
        </div>
      </header>
      {error && <p className="text-hold-ink">{error}</p>}

      <div role="tablist" aria-label="Risk group" className="grid grid-cols-3 gap-2 sm:max-w-lg">
        {RISK_ORDER.map((g) => (
          <button
            key={g}
            role="tab"
            aria-selected={group === g}
            onClick={() => setGroup(g)}
            className={`rounded-lg border px-4 py-2.5 text-left shadow-sm transition ${
              group === g ? RISK[g].chip : "border-line bg-page text-ink-muted hover:border-line-strong hover:text-ink"
            }`}
          >
            <span className="flex items-center gap-2 text-sm font-semibold">
              <span aria-hidden className={`inline-block h-2.5 w-2.5 rounded-full ${RISK[g].dot}`} />
              {RISK[g].label}
            </span>
            <span className="block text-2xl font-semibold tabular-nums">{counts[g]}</span>
          </button>
        ))}
      </div>

      <div className="grid gap-10 lg:grid-cols-[3fr_2fr]">
        <section aria-label={`${RISK[group].label} risk patients`} className="min-w-0 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
            <div className="min-w-0 max-w-prose space-y-1">
              <h2 className="text-xl font-semibold">{RISK[group].label} risk: {RISK[group].action.toLowerCase()}</h2>
              <p className="text-sm text-ink-muted">
                {group === "high" && "Heat warning, where to go and how to get there, then check-ins. No reply: their contact, then the clinic."}
                {group === "medium" && "The nearest cool place and the safest hours to go."}
                {group === "low" && "A short heat heads-up about their medicines."}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <Button size="lg" className={`px-6 text-base hover:brightness-95 ${RISK[group].solid} ${GROUP_HOVER[group]}`} onClick={() => send(texts.map((r) => r.id))} disabled={busy || !texts.length}>
                Text this group ({texts.length})
              </Button>
              {calls.length > 0 && (
                <button onClick={() => send(calls.map((r) => r.id), "call")} disabled={busy} className="text-sm text-ink-muted underline underline-offset-[3px] hover:text-ink disabled:opacity-40">
                  Add {calls.length} who asked for calls to the call list
                </button>
              )}
            </div>
          </div>

          <Card className="overflow-hidden border-line"><ul className="max-h-[70vh] divide-y divide-line overflow-auto">
            {shown.map((r) => {
              const st = statusOf(r.id);
              return (
                <li key={r.id} className="flex flex-col gap-1 border-l-[6px] px-4 py-2.5 sm:flex-row sm:items-center sm:gap-4" style={{ borderLeftColor: `var(--risk-${r.group})` }}>
                  <div className="min-w-0 flex-1">
                    <p>
                      <span className="font-semibold">{r.name}</span>{" "}
                      <span className="text-sm text-ink-muted">· {r.age} · {r.zip}{r.callInstead ? " · call, don’t text" : ""}</span>
                    </p>
                    <p className="text-sm text-ink-muted">{r.why}</p>
                  </div>
                  <div className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-1">
                    {st && <span className={`whitespace-nowrap text-sm font-semibold ${st.cls}`}>{st.label}</span>}
                    <button onClick={() => setOpen(r)} className="text-sm text-ink-muted underline underline-offset-[3px] hover:text-ink">Why?</button>
                    <button onClick={() => send([r.id], r.callInstead ? "call" : "text")} className="text-sm text-ink-muted underline underline-offset-[3px] hover:text-ink">
                      {r.callInstead ? "Call" : "Text"}
                    </button>
                    <Link href={`/phone/${r.id}`} className="text-sm text-ink-muted underline underline-offset-[3px] hover:text-ink">Plan</Link>
                  </div>
                </li>
              );
            })}
          </ul></Card>
          <details className="text-xs text-ink-muted">
            <summary className="cursor-pointer">Sources</summary>
            <p className="mt-1">
              Groups from <code>{source}</code>. &ldquo;Call, don&rsquo;t text&rdquo; = alert_opt_in false in <code>{questionnaireFile}</code>. Texts are simulated.
            </p>
          </details>
        </section>

        <section aria-label="Messages" className="min-w-0 space-y-3">
          <h2 className="text-xl font-semibold">Messages <span className="text-sm font-normal text-ink-muted">simulated</span></h2>
          <Card className="overflow-hidden border-line"><ol className="max-h-[70vh] divide-y divide-line overflow-auto">
            {!state?.messages.length && <li className="px-4 py-3 text-sm text-ink-muted">Nothing sent yet. Pick a group and press &ldquo;Text this group.&rdquo;</li>}
            {state?.messages.map((m) => (
              <li key={m.id} className="px-4 py-2.5 text-sm">
                <div className="flex justify-between gap-2 text-xs text-ink-muted">
                  <span>
                    <b className="text-ink">{(m.patient_id && names.get(m.patient_id)) ?? m.patient_id}</b> →{" "}
                    {m.recipient.startsWith("contact") ? "their contact" : m.recipient === "clinic" ? "clinic call list" : "patient"}
                  </span>
                  <span className="tabular-nums">{t(m.created_at)}</span>
                </div>
                <p className="mt-1 line-clamp-3">{m.body}</p>
              </li>
            ))}
          </ol></Card>
        </section>
      </div>

      {open && <WhyPanel row={open} onClose={() => setOpen(null)} />}
    </div>
  );
}

function WhyPanel({ row, onClose }: { row: BoardRow; onClose: () => void }) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  const d = row.detail;
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-ink/30" onClick={onClose}>
      <aside
        role="dialog"
        aria-label={`Why ${row.name} is ${RISK[row.group].label} risk`}
        className="h-full w-full max-w-md overflow-auto bg-page p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <span className={`inline-flex items-center whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-semibold ${RISK[row.group].chip}`}>{RISK[row.group].label} risk</span>
            <h2 className="text-xl font-semibold mt-2">{row.name}</h2>
            <p className="text-sm text-ink-muted">{row.age} · {row.zip} · synthetic patient</p>
          </div>
          <button onClick={onClose} className="text-sm text-ink-muted underline underline-offset-[3px] hover:text-ink">Close</button>
        </div>

        <h3 className="mt-5 font-semibold">In plain words</h3>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">
          {d.bullets.map((b) => <li key={b}>{b}</li>)}
        </ul>

        <h3 className="mt-5 font-semibold">Their medicines in heat</h3>
        <ul className="mt-2 space-y-3 text-sm">
          {d.meds.length === 0 && <li className="text-ink-muted">No heat-relevant medicines on file.</li>}
          {d.meds.map((m) => {
            const b = m.bucket ? BUCKETS[m.bucket] : null;
            return (
              <li
                key={m.name}
                className={`rounded-tile border border-line border-l-4 bg-surface p-3 ${m.bucket ? BUCKET_ACCENT[m.bucket] : "border-l-line-strong"}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="font-semibold capitalize">{m.name}</div>
                  {b && (
                    <span className={`shrink-0 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-semibold ${b.solid}`}>
                      {b.letter} · {b.label}
                    </span>
                  )}
                </div>
                {m.line ? <p className="mt-1">{m.line}</p> : <p className="mt-1 text-ink-muted">Not in data/kb/knowledge_base.json yet.</p>}
                {(m.kbId || m.sources.length > 0) && (
                  <div className="mt-2 space-y-1 border-t border-line pt-2 text-xs">
                    {m.kbId && (
                      <Link href={`/drug/${m.kbId}`} className="font-semibold underline">
                        {m.kbName} evidence card →
                      </Link>
                    )}
                    {uniqueSources(m.sources).map((s) => (
                      <a key={s.url + s.label} href={s.url} target="_blank" rel="noreferrer" className="block text-ink-muted underline hover:text-ink">
                        {s.label}
                      </a>
                    ))}
                  </div>
                )}
              </li>
            );
          })}
        </ul>

        {d.pathways.length > 0 && (
          <>
            <h3 className="mt-5 font-semibold">How it adds up</h3>
            <ul className="mt-2 space-y-3 text-sm">
              {d.pathways.map((p) => (
                <li
                  key={p.label}
                  className={`rounded-tile border border-l-4 p-3 ${p.stacked ? "border-line border-l-hold-solid bg-hold-tint/40" : "border-line border-l-layer-graph-fg bg-layer-graph-bg/50"}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-semibold">{p.label}</div>
                    {p.stacked && (
                      <span className="shrink-0 rounded-full bg-hold-solid px-2 py-0.5 text-xs font-semibold text-hold-on">2+ medicines</span>
                    )}
                  </div>
                  {p.system.map((s) => (
                    <div key={s.mediator} className="mt-2">
                      <div className="text-xs font-semibold text-ink-muted">{s.mediator} · studies in System</div>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        <StudyChip label="Heat" n={s.heatStudies} />
                        {s.drugLegs.map((l) => (
                          <StudyChip key={l.drug} label={l.drug} n={l.studies} />
                        ))}
                      </div>
                    </div>
                  ))}
                  <p className="mt-2 text-xs text-ink-muted">{p.note}</p>
                </li>
              ))}
            </ul>
          </>
        )}
        {d.caveat && <p className="mt-4 text-xs text-ink-muted">{d.caveat}</p>}
        {d.systemSource && <p className="mt-1 text-xs text-ink-muted">Source: {d.systemSource}</p>}
      </aside>
    </div>
  );
}
