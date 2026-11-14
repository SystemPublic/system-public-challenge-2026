// Deep-dive pieces for the atlas panel: study cards, graph rows behind a body-system link, and potential actions.
import { useState } from 'react'
import { Abstract, SourceChips } from '../components/evidence'
import type { Index } from '../data/derive'
import type { Link, V2Action, V2Direct } from '../data/types'

const EFFECT: Record<string, { t: string; c: string }> = {
  risk: { t: 'Raises risk', c: 'bg-heat-soft text-heat-ink' },
  null: { t: 'No clear effect', c: 'bg-soft text-ink-2 ring-1 ring-line-2' },
  lower: { t: 'Lower risk', c: 'bg-green-soft text-green' },
  unclear: { t: 'Unclear', c: 'bg-soft text-ink-3' },
}
const TYPE: Record<string, string> = { H: 'Heat-wave epidemiology', S: 'Seasonal comparison', X: 'Experimental local heat', C: 'Class-wide (as a group)' }

function Paper({ ix, pmid }: { ix: Index; pmid: string }) {
  const p = ix.b.papers[pmid]
  return p ? <span className="block text-[11.5px] text-ink-3">{p.authors} {p.year}. <i>{p.title}</i> {p.journal}.</span> : null
}

export function StudyCards({ ix, items }: { ix: Index; items: V2Direct[] }) {
  const [open, setOpen] = useState<string | null>(null)
  if (!items.length) return null
  return (
    <ul className="flex flex-col divide-y divide-line rounded-md border border-line">
      {items.map(d => {
        const k = d.pmid + d.summary, on = open === k, e = EFFECT[d.effect] ?? EFFECT.unclear
        return (
          <li key={k}>
            <button onClick={() => setOpen(on ? null : k)} className="flex w-full items-start gap-2 px-3 py-2 text-left hover:bg-hov">
              <span className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${e.c}`}>{e.t}</span>
              <span className="text-[12.5px] leading-snug">{d.summary.split(':')[0]}</span>
              <span className="ml-auto shrink-0 text-[11px] text-ink-3">{on ? '−' : '+'}</span>
            </button>
            {on && (
              <div className="flex flex-col gap-1.5 px-3 pb-3 text-[12.5px] leading-snug">
                <span>{d.summary}</span>
                <span className="flex flex-wrap gap-1.5">
                  <span className={`rounded px-1.5 py-0.5 text-[10.5px] font-semibold ${d.vetted ? 'bg-soft text-ink-2' : 'bg-amber-soft text-amber'}`}>{d.vetted ? 'Vetted graph row (quality-filtered snapshot)' : 'Unvetted: live graph only'}</span>
                  {d.type && TYPE[d.type] && <span className="rounded bg-soft px-1.5 py-0.5 text-[10.5px] font-semibold text-ink-2">{TYPE[d.type]}</span>}
                </span>
                <Paper ix={ix} pmid={d.pmid} />
                {d.correction && <span className="rounded bg-heat-soft p-1.5 text-[11.5px] text-heat-ink">Corrected by us: {d.correction}</span>}
                <Abstract pmid={d.pmid} />
              </div>
            )}
          </li>
        )
      })}
    </ul>
  )
}

/** The graph rows behind one body-system link: drug-side findings showing raised risk, and heat-side findings. */
export function LinkStudies({ ix, l }: { ix: Index; l: Link }) {
  const drug = l.drug_arm_ids.map(id => ix.b.findings[id]).filter(f => f && f.dir === 'raised').slice(0, 6)
  const heat = (ix.b.heat_arms.find(h => h.effect === l.effect)?.ids ?? []).map(id => ix.b.findings[id]).filter(Boolean).slice(0, 4)
  const dirs = ix.b.direct.filter(d => l.direct_ids.includes(d.id))
  const Row = ({ f }: { f: (typeof drug)[number] }) => (
    <li className="text-[12px] leading-snug">
      <b>{f.v1}</b> ↔ <b>{f.v2}</b>: {f.stat.replace(/_/g, ' ')} {f.value}{f.lo ? ` (${f.lo}–${f.hi})` : ''}
      <Paper ix={ix} pmid={f.pmid} />
      {f.correction && <span className="block text-[11px] text-heat-ink">Corrected by us: {f.correction.text}</span>}
      {f.pmid && <Abstract pmid={f.pmid} />}
    </li>
  )
  return (
    <div className="mt-2 flex flex-col gap-2 rounded-md bg-soft p-2.5">
      {dirs.length > 0 && <div><div className="text-[11px] font-semibold text-ink-2">Measured together with heat</div>
        <ul className="mt-1 flex flex-col gap-1.5">{dirs.map(d => <li key={d.id} className="text-[12px]">{d.finding} <Abstract pmid={d.pmid} /></li>)}</ul></div>}
      {drug.length > 0 && <div><div className="text-[11px] font-semibold text-ink-2">Drug side: studies showing raised risk (first {drug.length} of {l.drug_arm.raised})</div>
        <ul className="mt-1 flex flex-col gap-1.5">{drug.map(f => <Row key={f.id} f={f} />)}</ul></div>}
      {heat.length > 0 && <div><div className="text-[11px] font-semibold text-ink-2">Heat side: heat and the same effect (first {heat.length})</div>
        <ul className="mt-1 flex flex-col gap-1.5">{heat.map(f => <Row key={f.id} f={f} />)}</ul></div>}
      <p className="text-[10.5px] text-ink-3">Rows as extracted by the System Public Graph; not checked against abstracts unless marked.</p>
    </div>
  )
}

const BASIS: Record<string, { t: string; c: string }> = {
  study: { t: 'Study', c: 'bg-heat-soft text-heat-ink' },
  guidance: { t: 'Guidance', c: 'bg-accent-soft text-accent' },
  label: { t: 'Drug label', c: 'bg-soft text-ink-2' },
  mechanism: { t: 'Mechanism', c: 'bg-soft text-ink-2' },
  draft: { t: 'Draft: no source yet', c: 'bg-amber-soft text-amber' },
}
const BUCKETS = ['Continue, don\'t stop', 'Substitute or hold', 'Dose adjustment', 'Closer monitoring', 'Storage and stability', 'Counsel and plan']
const BUCKET_LABEL: Record<string, string> = {
  "Continue, don't stop": 'Keep taking', 'Substitute or hold': 'Hold or switch', 'Dose adjustment': 'Adjust the dose',
  'Closer monitoring': 'Monitor', 'Storage and stability': 'Storage', 'Counsel and plan': 'Counsel and plan',
}

export function PotentialActions({ ix, actions }: { ix: Index; actions: V2Action[] }) {
  const seen = new Set<string>()
  const uniq = actions.filter(a => (seen.has(a.text) ? false : (seen.add(a.text), true)))
  const groups = [...BUCKETS, ...new Set(uniq.map(a => a.bucket).filter(b => !BUCKETS.includes(b)))]
  return (
    <div className="flex flex-col gap-3">
      {groups.map(g => {
        const as = uniq.filter(a => a.bucket === g)
        if (!as.length) return null
        return (
          <div key={g}>
            <div className="mb-1 text-[11.5px] font-bold uppercase tracking-wide text-ink-3">{BUCKET_LABEL[g] ?? g}</div>
            <ul className="flex flex-col gap-2">
              {as.map(a => {
                const bs = BASIS[a.basis] ?? BASIS.draft
                return (
                  <li key={a.text} className="rounded-md border border-line p-2.5">
                    <div className="text-[13px] font-semibold leading-snug">{a.text}</div>
                    <div className="mt-1 text-[12px] leading-snug text-ink-2">
                      {a.note && a.note !== 'Label' && <span className="block">Why: {a.note}</span>}
                      {a.trigger && <span className="block">Applies when: {a.trigger.charAt(0).toLowerCase() + a.trigger.slice(1)}</span>}
                      {a.who && <span className="block text-ink-3">Who: {a.who}</span>}
                    </div>
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                      <span className={`rounded px-1.5 py-0.5 text-[10.5px] font-semibold ${bs.c}`}>{bs.t}</span>
                      {(a.sources.length > 0 || a.pmids.length > 0) && <SourceChips sources={a.sources} pmids={a.pmids} ix={ix} />}
                    </div>
                  </li>
                )
              })}
            </ul>
          </div>
        )
      })}
    </div>
  )
}

/** Forest plot as clickable rows: each row is a study; click it to open the paper, badges and abstract inline. */
export function StudyForest({ ix, items, parse }: { ix: Index; items: V2Direct[]; parse: (t: string) => { est: number; lo?: number; hi?: number } | null }) {
  const [open, setOpen] = useState<string | null>(null)
  const parsed = items.map(d => ({ d, r: parse(d.summary) }))
  const vals = parsed.flatMap(({ r }) => (r ? [r.est, r.lo ?? r.est, r.hi ?? r.est] : [])).filter(v => v > 0)
  const min = Math.min(0.3, ...vals) * 0.85, max = Math.max(5, ...vals) * 1.15
  const W = 130
  const x = (v: number) => ((Math.log(Math.min(Math.max(v, min), max)) - Math.log(min)) / (Math.log(max) - Math.log(min))) * W
  const ticks = [0.1, 0.5, 1, 2, 5, 10, 20].filter(t => t >= min && t <= max)
  if (!items.length) return null
  return (
    <div className="rounded-md border border-line">
      <div className="grid grid-cols-[minmax(0,1fr)_130px_44px] items-end gap-2 border-b border-line px-3 py-1.5 text-[10.5px] text-ink-3">
        <span>Study (click to open)</span>
        <svg viewBox={`0 0 ${W} 14`} className="h-3.5 w-[130px]" aria-hidden>
          {ticks.map(t => <text key={t} x={x(t)} y={10} fontSize={9} textAnchor="middle" fill="var(--color-ink-3)">{t}</text>)}
        </svg>
        <span className="text-right">Result</span>
      </div>
      <ul className="divide-y divide-line">
        {parsed.map(({ d, r }) => {
          const k = d.pmid + d.summary, on = open === k
          const col = d.effect === 'risk' ? 'var(--color-heat)' : d.effect === 'lower' ? 'var(--color-green)' : 'var(--color-faint)'
          const e = EFFECT[d.effect] ?? EFFECT.unclear
          return (
            <li key={k}>
              <button onClick={() => setOpen(on ? null : k)} className={`grid w-full grid-cols-[minmax(0,1fr)_130px_44px] items-center gap-2 px-3 py-2 text-left ${on ? 'bg-soft' : 'hover:bg-hov'}`}>
                <span className="min-w-0">
                  <span className="block truncate text-[12.5px] font-semibold">{d.summary.split(':')[0]}</span>
                  <span className={`mt-0.5 inline-block rounded px-1 text-[9.5px] font-bold uppercase ${e.c}`}>{e.t}</span>
                  {!d.vetted && <span className="ml-1 inline-block rounded bg-amber-soft px-1 text-[9.5px] font-bold uppercase text-amber">unvetted</span>}
                </span>
                <svg viewBox={`0 0 ${W} 16`} className="h-4 w-[130px]" aria-hidden>
                  <line x1={x(1)} x2={x(1)} y1={0} y2={16} stroke="var(--color-line-2)" strokeDasharray="2 2" />
                  {r && r.lo !== undefined && r.hi !== undefined && <line x1={x(r.lo)} x2={x(r.hi)} y1={8} y2={8} stroke={col} strokeWidth={2} strokeDasharray={d.vetted ? undefined : '3 2'} />}
                  {r && <rect x={x(r.est) - 4} y={4} width={8} height={8} fill={col} />}
                  {!r && <text x={W / 2} y={11} fontSize={9} textAnchor="middle" fill="var(--color-ink-3)">no ratio reported</text>}
                </svg>
                <span className="num text-right text-[12.5px] font-bold">{r ? r.est : '—'}</span>
              </button>
              {on && (
                <div className="flex flex-col gap-1.5 bg-soft px-3 pb-3 text-[12.5px] leading-snug">
                  <span>{d.summary}</span>
                  <span className="flex flex-wrap gap-1.5">
                    <span className={`rounded px-1.5 py-0.5 text-[10.5px] font-semibold ${d.vetted ? 'bg-panel text-ink-2' : 'bg-amber-soft text-amber'}`}>{d.vetted ? 'Vetted graph row (quality-filtered snapshot)' : 'Unvetted: live graph only'}</span>
                    {d.type && TYPE[d.type] && <span className="rounded bg-panel px-1.5 py-0.5 text-[10.5px] font-semibold text-ink-2">{TYPE[d.type]}</span>}
                  </span>
                  <Paper ix={ix} pmid={d.pmid} />
                  {d.correction && <span className="rounded bg-heat-soft p-1.5 text-[11.5px] text-heat-ink">Corrected by us: {d.correction}</span>}
                  <Abstract pmid={d.pmid} />
                </div>
              )}
            </li>
          )
        })}
      </ul>
      <p className="border-t border-line px-3 py-1.5 text-[10.5px] text-ink-3">Square = result; bar = 95% interval; dashed line = 1 (no difference); right of the line = higher risk.</p>
    </div>
  )
}
