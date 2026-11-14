// Evidence building blocks shared by the atlas drawer and the heat check's evidence panel.
import { useState } from 'react'
import type { Index } from '../data/derive'
import type { RiskFactor, V2Class, V2Direct } from '../data/types'

const EFFECT: Record<string, { t: string; c: string }> = {
  risk: { t: 'Raises risk', c: 'bg-heat-soft text-heat-ink' },
  null: { t: 'No clear effect', c: 'bg-soft text-ink-2 ring-1 ring-line-2' },
  lower: { t: 'Lower risk', c: 'bg-accent-soft text-accent' },
  unclear: { t: 'Unclear', c: 'bg-soft text-ink-3' },
}

export function Section({ title, children, note }: { title: string; children: React.ReactNode; note?: string }) {
  return (
    <section className="border-t border-line pt-3">
      <h4 className="eyebrow mb-2">{title}</h4>
      {children}
      {note && <p className="mt-1.5 text-[11.5px] text-ink-3">{note}</p>}
    </section>
  )
}

export function Abstract({ pmid }: { pmid: string }) {
  const [state, setState] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [text, setText] = useState('')
  const load = () => {
    setState('loading')
    fetch(`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=${pmid}&rettype=abstract&retmode=text`)
      .then(r => (r.ok ? r.text() : Promise.reject(r.status)))
      .then(t => { setText(t.trim()); setState('done') })
      .catch(() => setState('error'))
  }
  return (
    <span className="ml-1">
      <a className="text-accent underline-offset-2 hover:underline" href={`https://pubmed.ncbi.nlm.nih.gov/${pmid}/`} target="_blank" rel="noreferrer">PMID {pmid}</a>
      {state === 'idle' && <button className="ml-2 text-[11.5px] text-ink-3 hover:text-ink" onClick={load}>Read abstract</button>}
      {state === 'loading' && <span className="ml-2 text-[11.5px] text-ink-3">Loading from PubMed…</span>}
      {state === 'error' && <span className="ml-2 text-[11.5px] text-ink-3">Couldn't load; open the link.</span>}
      {state === 'done' && <span className="mt-1.5 block max-h-56 overflow-y-auto whitespace-pre-wrap rounded-md bg-soft p-2 text-[11.5px] leading-relaxed text-ink-2">{text}</span>}
    </span>
  )
}

export function DirectList({ items }: { items: V2Direct[] }) {
  if (!items.length) return <p className="text-[13px] text-ink-3">No study in the graph measured this drug class and heat together.</p>
  return (
    <ul className="flex flex-col gap-2.5">
      {items.map(d => {
        const e = EFFECT[d.effect] ?? EFFECT.unclear
        return (
          <li key={d.pmid + d.summary} className="text-[13px] leading-snug">
            <div className="mb-0.5 flex flex-wrap items-center gap-1.5">
              <span className={`rounded px-1.5 py-0.5 text-[10.5px] font-bold uppercase tracking-wide ${e.c}`}>{e.t}</span>
              <span className={`rounded px-1.5 py-0.5 text-[10.5px] font-semibold ${d.vetted ? 'bg-soft text-ink-2' : 'bg-amber-soft text-amber'}`}>{d.vetted ? 'Vetted graph row' : 'Unvetted (API only)'}</span>
            </div>
            {d.summary}
            <Abstract pmid={d.pmid} />
            {d.correction && <p className="mt-1 rounded bg-heat-soft p-1.5 text-[11.5px] text-heat-ink">Corrected by us: {d.correction}</p>}
          </li>
        )
      })}
    </ul>
  )
}

/** All direct studies for a v2 class, deduplicated across action buckets. */
export function directFor(c: V2Class): V2Direct[] {
  const seen = new Set<string>(); const out: V2Direct[] = []
  for (const cell of Object.values(c.cells)) for (const d of cell.direct) {
    const k = d.pmid + d.summary
    if (!seen.has(k)) { seen.add(k); out.push(d) }
  }
  const rank = (e: string) => ({ risk: 0, null: 1, lower: 2 } as Record<string, number>)[e] ?? 3
  return out.sort((a, z) => Number(z.vetted) - Number(a.vetted) || rank(a.effect) - rank(z.effect))
}

export function SharedPathway({ ix, ourId }: { ix: Index; ourId: string | null }) {
  if (!ourId) return <p className="text-[13px] text-ink-3">No shared-pathway analysis for this group.</p>
  const ls = (ix.linksByClass[ourId] ?? []).filter(l => l.tier === 'shared' || l.tier === 'direct').filter(l => l.drug_arm.studies > 0)
    .sort((a, z) => z.drug_arm.raised - a.drug_arm.raised).slice(0, 4)
  if (!ls.length) return <p className="text-[13px] text-ink-3">No body effect passes the shared-pathway test for this class.</p>
  return (
    <ul className="flex flex-col gap-1.5">
      {ls.map(l => (
        <li key={l.effect} className="grid grid-cols-[1fr_auto] gap-x-3 text-[13px]">
          <span className="font-medium">{ix.effect[l.effect]?.label}</span>
          <span className="num text-ink-3">{l.drug_arm.raised} of {l.drug_arm.studies} drug studies ↑ · {l.heat_arm_studies} heat studies</span>
        </li>
      ))}
    </ul>
  )
}

export function GuidanceTable({ ix, c }: { ix: Index; c: V2Class }) {
  const src = ix.b.v2.guidance_sources
  const lv: Record<string, string> = { action: 'Gives an action', mention: 'Names it', storage: 'Storage only', absent: 'Silent' }
  return (
    <ul className="flex flex-col gap-1">
      {src.map(s => {
        const g = c.guidance[s.id]
        const level = g?.level ?? 'absent'
        return (
          <li key={s.id} className="grid grid-cols-[84px_92px_1fr] items-baseline gap-2 text-[12.5px]">
            <a href={s.url} target="_blank" rel="noreferrer" className="font-semibold hover:underline">{s.short}</a>
            <span className={level === 'action' ? 'font-semibold text-ink' : level === 'absent' ? 'text-ink-3' : 'text-ink-2'}>{lv[level] ?? level}</span>
            <span className="text-ink-2">{g?.action || g?.mech || ''}</span>
          </li>
        )
      })}
    </ul>
  )
}

export function LabelNote({ c }: { c: V2Class }) {
  const ls = c.label?.label ?? []
  const l = ls.find(x => x.snippet) ?? ls[0]
  if (!l) return <p className="text-[13px] text-ink-3">No label data pulled for this class.</p>
  return (
    <p className="text-[13px] leading-snug text-ink-2">
      <b className="text-ink">{l.generic}</b>{l.brand ? ` (${l.brand})` : ''}: “{l.snippet.trim()}”
      {l.storage?.max_c ? ` Storage limit ${l.storage.max_c} °C.` : ''}
      {l.dailymed && <a className="ml-1 text-accent hover:underline" href={l.dailymed} target="_blank" rel="noreferrer">DailyMed</a>}
    </p>
  )
}

export function RiskFactorList({ items }: { items: RiskFactor[] }) {
  return (
    <ul className="flex flex-col gap-2.5">
      {items.map(r => (
        <li key={r.id} className="text-[13px] leading-snug">
          <div className="mb-0.5 flex flex-wrap items-center gap-1.5">
            <span className={`rounded px-1.5 py-0.5 text-[10.5px] font-bold uppercase tracking-wide ${r.direction === 'protective' ? 'bg-green-soft text-green' : 'bg-heat-soft text-heat-ink'}`}>{r.direction === 'protective' ? 'Protective' : 'Raises risk'}</span>
            <span className="rounded bg-soft px-1.5 py-0.5 text-[10.5px] font-semibold text-ink-2">Abstract-checked</span>
          </div>
          <b>{r.factor}</b>: {r.outcome.toLowerCase()}, {r.statistic.replace(/_/g, ' ')} {r.value}{r.ci_lower ? ` (${r.ci_lower}–${r.ci_upper})` : ''}. {r.population}.
          <Abstract pmid={r.pmid} />
          {r.note && <span className="block text-[11.5px] text-ink-3">{r.note}</span>}
        </li>
      ))}
    </ul>
  )
}

export function SourceChips({ sources, pmids, ix }: { sources: string[]; pmids: string[]; ix: Index }) {
  const short = (id: string) => ix.b.v2.guidance_sources.find(s => s.id === id)?.short ?? id.toUpperCase()
  if (!sources.length && !pmids.length) return <span className="text-[11px] text-ink-3">HeatRx rule</span>
  return (
    <span className="inline-flex flex-wrap gap-1">
      {sources.map(s => <span key={s} className="rounded bg-soft px-1.5 py-0.5 text-[10.5px] font-semibold text-ink-2">{short(s)}</span>)}
      {pmids.map(p => <a key={p} href={`https://pubmed.ncbi.nlm.nih.gov/${p}/`} target="_blank" rel="noreferrer" className="rounded bg-accent-soft px-1.5 py-0.5 text-[10.5px] font-semibold text-accent hover:underline">PMID {p}</a>)}
    </span>
  )
}
