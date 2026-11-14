// Atlas screen 2: the brief's grid. Drug classes x the four actions, one mark per cell (size = evidence,
// fill = tier), plus guidance coverage per class. Words only in the drawer.
import { useState } from 'react'
import { DirectList, GuidanceTable, LabelNote, Section } from '../components/evidence'
import type { Index } from '../data/derive'
import type { V2Bucket, V2Cell, V2Class } from '../data/types'

const GROUPS: { title: string; classes: string[] }[] = [
  { title: 'Volume and kidney', classes: ['Diuretics', 'ACE inhibitors / ARBs', 'NSAIDs', 'SGLT2 inhibitors', 'Lithium'] },
  { title: 'Blood pressure', classes: ['Beta blockers', 'Calcium channel blockers'] },
  { title: 'Thermoregulation and the brain', classes: ['Antipsychotics', 'Antidepressants', 'Benzodiazepines / sedatives', 'Anticholinergics', 'Topiramate / zonisamide', 'Parkinson / dopaminergic', 'Cholinesterase inhibitors'] },
  { title: 'Blood sugar', classes: ['Insulin', 'Metformin and sulfonylureas', 'GLP-1 agonists'] },
  { title: 'Overdose', classes: ['Opioids', 'Stimulants'] },
  { title: 'Combinations and storage', classes: ['Combination: diuretic + ACEi/ARB (± NSAID)', 'Polypharmacy (several heat-sensitising drugs)', 'Heat-labile emergency products'] },
]
const SHORT: Record<V2Bucket, string> = { 'Dose adjustment': 'Adjust dose', 'Substitute or hold': 'Hold or switch', 'Closer monitoring': 'Monitor', 'Storage and stability': 'Storage' }
const PATTERN: Record<string, { t: string; c: string }> = {
  missed: { t: 'Under-warned', c: 'bg-heat text-white' },
  label_silent: { t: 'Labels silent', c: 'bg-heat-soft text-heat-ink' },
  overwarned: { t: 'Over-warned', c: 'border border-ink text-ink' },
  agree: { t: 'Aligned', c: 'bg-soft text-ink-2' },
  thin: { t: 'Thin', c: 'bg-soft text-ink-3' },
  storage: { t: 'Storage', c: 'bg-accent-soft text-accent' },
}

function Mark({ c }: { c: V2Cell }) {
  const n = c.direct.length
  if (c.tier === 'none') return <circle r={2} fill="var(--color-line-2)" />
  if (c.tier === 'gap') return <circle r={8} fill="none" stroke="var(--color-faint)" strokeWidth={1.4} strokeDasharray="3 2.5" />
  if (c.tier === 'partial') return <circle r={7} fill="none" stroke="var(--color-s2)" strokeWidth={1.6} />
  if (c.tier === 'bridged') {
    const f = ['var(--color-s1)', 'var(--color-s1)', 'var(--color-s2)', 'var(--color-s3)'][c.strength ?? 1]
    return <circle r={6 + (c.strength ?? 1) * 2} fill={f} stroke={c.vetted ? 'none' : 'var(--color-ink-3)'} strokeDasharray={c.vetted ? undefined : '2 2'} />
  }
  const r = Math.min(15, 8 + n * 1.6)
  if (c.signal === 'risk') return <circle r={r} fill="var(--color-heat)" stroke={c.vetted ? 'none' : 'var(--color-ink)'} strokeWidth={1.2} strokeDasharray={c.vetted ? undefined : '2 2'} />
  return <circle r={r} fill="var(--color-panel)" stroke="var(--color-heat)" strokeWidth={2} />
}

export function ActionGrid({ ix }: { ix: Index }) {
  const v = ix.b.v2
  const [sel, setSel] = useState<{ cls: string; bucket: V2Bucket | 'guidance' } | null>({ cls: 'Antipsychotics', bucket: 'Closer monitoring' })
  const [spec, setSpec] = useState<string | null>(null)
  const specs = [...new Set(v.classes.flatMap(c => c.specialties))].sort()
  const byName = Object.fromEntries(v.classes.map(c => [c.name, c]))
  const nSources = v.guidance_sources.length
  const named = (c: V2Class) => v.guidance_sources.filter(s => ['action', 'mention'].includes(c.guidance[s.id]?.level ?? '')).length
  const selCls = sel ? byName[sel.cls] : null

  return (
    <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[minmax(0,1fr)_400px]">
      <section className="min-h-0 overflow-y-auto rounded-lg border border-line bg-panel p-5">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="eyebrow">Evidence atlas · 2 of 2</div>
            <h1 className="font-display text-[26px] font-bold leading-tight">What to do, and where guidance falls short</h1>
            <p className="mt-1 max-w-[70ch] text-[13.5px] text-ink-2">Each drug class against the brief's four actions. The mark shows how strong the heat evidence is for that action, not how dangerous the drug is. Select any cell.</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-[12px] text-ink-2">
          <Legend r={9} el={<circle r={9} fill="var(--color-heat)" />} t="Measured in heat: raises risk" />
          <Legend r={9} el={<circle r={8} fill="var(--color-panel)" stroke="var(--color-heat)" strokeWidth={2} />} t="Measured: no clear effect" />
          <Legend r={9} el={<g><circle r={9} cx={-6} fill="var(--color-s3)" /></g>} t="Mechanism (strong → weak)" />
          <Legend r={9} el={<circle r={8} fill="none" stroke="var(--color-faint)" strokeDasharray="3 2.5" strokeWidth={1.4} />} t="Guidance or label only" />
          <Legend r={9} el={<circle r={8} fill="var(--color-heat)" stroke="var(--color-ink)" strokeDasharray="2 2" strokeWidth={1.2} />} t="Dashed edge: unvetted rows" />
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-1.5 text-[12px]">
          <span className="eyebrow mr-1">Prescriber</span>
          <button onClick={() => setSpec(null)} className={`rounded-full px-2.5 py-1 ${!spec ? 'bg-ink text-white' : 'border border-line hover:bg-hov'}`}>All</button>
          {specs.map(s => <button key={s} onClick={() => setSpec(spec === s ? null : s)} className={`rounded-full px-2.5 py-1 ${spec === s ? 'bg-ink text-white' : 'border border-line hover:bg-hov'}`}>{s}</button>)}
        </div>
        <table className="mt-4 w-full border-collapse text-[13px]">
          <thead>
            <tr className="text-left">
              <th className="w-[34%] pb-2 font-semibold text-ink-3">Drug class</th>
              {v.buckets.map(bk => <th key={bk} className="pb-2 text-center font-semibold">{SHORT[bk]}</th>)}
              <th className="pb-2 pl-3 font-semibold">Guidance <span className="font-normal text-ink-3">(of {nSources})</span></th>
            </tr>
          </thead>
          <tbody>
            {GROUPS.map(g => {
              const rows = g.classes.map(n => byName[n]).filter(Boolean).filter(c => !spec || c.specialties.includes(spec))
              if (!rows.length) return null
              return [
                <tr key={g.title}><td colSpan={6} className="eyebrow pt-4 pb-1 text-heat-ink">{g.title}</td></tr>,
                ...rows.map(c => (
                  <tr key={c.name} className="border-t border-line hover:bg-soft">
                    <td className="py-1.5 pr-2">
                      <div className="font-semibold">{c.name}</div>
                      <div className="text-[11.5px] text-ink-3">{c.examples}</div>
                    </td>
                    {v.buckets.map(bk => {
                      const cell = c.cells[bk]
                      const on = sel?.cls === c.name && sel.bucket === bk
                      return (
                        <td key={bk} className="text-center">
                          <button aria-label={`${c.name}, ${SHORT[bk]}: ${cell.tier}`} onClick={() => setSel({ cls: c.name, bucket: bk })}
                            className={`rounded-md p-1 ${on ? 'bg-accent-soft ring-1 ring-accent' : 'hover:bg-hov'}`}>
                            <svg width={34} height={34} viewBox="-17 -17 34 34" aria-hidden><Mark c={cell} /></svg>
                          </button>
                        </td>
                      )
                    })}
                    <td className="pl-3">
                      <button onClick={() => setSel({ cls: c.name, bucket: 'guidance' })} className="flex items-center gap-2 text-left">
                        <span className="flex gap-0.5" aria-hidden>{v.guidance_sources.map(s => <i key={s.id} className={`h-3.5 w-1.5 rounded-sm ${c.guidance[s.id]?.level === 'action' ? 'bg-ink' : c.guidance[s.id]?.level === 'mention' ? 'bg-ink-3' : 'bg-line'}`} />)}</span>
                        <span className="num text-[12px]">{named(c)}</span>
                        {c.pattern && PATTERN[c.pattern] && <span className={`rounded px-1.5 py-0.5 text-[10.5px] font-bold uppercase tracking-wide ${PATTERN[c.pattern].c}`}>{PATTERN[c.pattern].t}</span>}
                      </button>
                    </td>
                  </tr>
                )),
              ]
            })}
          </tbody>
        </table>
        <p className="mt-4 text-[11.5px] text-ink-3">{v.source_note} Guidance bars: dark = gives an action, grey = names the class. Sources: {v.guidance_sources.map(s => s.short).join(', ')}.</p>
      </section>
      <aside className="min-h-0 overflow-y-auto rounded-lg border border-line bg-panel p-5">
        {selCls && sel ? <CellDrawer ix={ix} c={selCls} bucket={sel.bucket} /> : <p className="text-ink-3">Select a cell.</p>}
      </aside>
    </div>
  )
}

function Legend({ el, t }: { r: number; el: React.ReactNode; t: string }) {
  return <span className="flex items-center gap-1.5"><svg width={20} height={20} viewBox="-10 -10 20 20" aria-hidden>{el}</svg>{t}</span>
}

function CellDrawer({ ix, c, bucket }: { ix: Index; c: V2Class; bucket: V2Bucket | 'guidance' }) {
  const pat = c.pattern ? ix.b.v2.patterns.find(p => p.id === c.pattern) : null
  if (bucket === 'guidance') {
    return (
      <div className="flex flex-col gap-4">
        <div><div className="eyebrow">Guidance vs evidence</div><h2 className="font-display text-[22px] font-bold">{c.name}</h2>
          {pat && <p className="mt-1 text-[13px]"><b>{pat.title}.</b> {pat.blurb}</p>}
          {c.finding && <p className="mt-2 text-[13px] text-ink-2">{c.finding}</p>}</div>
        <Section title="Guidance, source by source"><GuidanceTable ix={ix} c={c} /></Section>
        <Section title="Drug label"><LabelNote c={c} /></Section>
      </div>
    )
  }
  const cell = c.cells[bucket]
  const tierText: Record<string, string> = { direct: cell.signal === 'risk' ? 'Measured in heat: raises risk' : 'Measured in heat: no clear effect', bridged: 'Mechanism support (shared pathway)', partial: 'Partial: the drug side only', gap: 'Guidance or label only', none: 'No heat-specific action expected' }
  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="eyebrow">{c.name} · {SHORT[bucket]}</div>
        <h2 className="mt-1 font-display text-[20px] font-bold leading-snug">{cell.action || 'No heat-specific action'}</h2>
        <span className="mt-2 inline-block rounded bg-accent-soft px-2 py-0.5 text-[11px] font-semibold text-accent">{tierText[cell.tier]}{cell.vetted ? '' : ' · relies on unvetted rows'}</span>
        {cell.note && <p className="mt-2 text-[12.5px] text-ink-2">Outside the graph: {cell.note}</p>}
        <p className="mt-2 text-[11.5px] text-ink-3">Action wording is a draft for clinician review. Prescribers: {c.specialties.join(', ')}.</p>
      </div>
      <Section title="Studies of this medicine and heat together"><DirectList items={cell.direct} /></Section>
      {cell.mechanisms.length > 0 && (
        <Section title="Mechanism: drug studies / heat studies" note="Two halves from different studies; '+' counts are unvetted rows.">
          <ul className="flex flex-col gap-1">
            {cell.mechanisms.map(m => (
              <li key={m.mechanism} className="grid grid-cols-[1fr_auto] text-[13px]">
                <span className={m.primary ? 'font-semibold' : 'text-ink-2'}>{m.mechanism}{m.primary ? ' (main)' : ''}</span>
                <span className="num text-ink-3">{m.drug_studies}{m.drug_unvetted ? `+${m.drug_unvetted}` : ''} / {m.heat_studies}{m.heat_unvetted ? `+${m.heat_unvetted}` : ''}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}
      <Section title="Guidance"><GuidanceTable ix={ix} c={c} /></Section>
    </div>
  )
}
