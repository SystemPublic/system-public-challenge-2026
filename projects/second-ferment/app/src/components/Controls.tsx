import { useEffect, useMemo, useRef, useState } from 'react'
import { BUCKET_LABEL, BUCKET_ORDER, TIER_LABEL, type Index } from '../data/derive'
import type { Tier } from '../data/types'
import { ROLE_DEFAULTS, useStore, type Heat, type Role } from '../state/store'
import { specialtyOptions } from './filters'

const seg = 'rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors'

export function Segmented<T extends string | number>({ value, options, onChange, dark, label }: {
  value: T; options: { v: T; label: string; tone?: string }[]; onChange: (v: T) => void; dark?: boolean; label: string
}) {
  return (
    <div role="radiogroup" aria-label={label}
      className={`flex rounded-lg p-0.5 ${dark ? 'bg-hero-2 ring-1 ring-hero-line' : 'bg-panel ring-1 ring-line'}`}>
      {options.map(o => {
        const on = o.v === value
        return (
          <button key={String(o.v)} role="radio" aria-checked={on} onClick={() => onChange(o.v)}
            className={`${seg} ${on ? (o.tone ?? (dark ? 'bg-hero-line text-hero-ink' : 'bg-accent-soft text-accent'))
              : dark ? 'text-hero-ink-2 hover:text-hero-ink' : 'text-ink-2 hover:text-ink'}`}>
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

export function TopBar({ ix }: { ix: Index }) {
  const role = useStore(s => s.role), setRole = useStore(s => s.setRole)
  return (
    <header className="flex flex-wrap items-center gap-x-6 gap-y-3 border-b border-line bg-panel px-5 py-3">
      <div className="font-display text-[22px] font-semibold tracking-tight">Heat<span className="text-direct">Rx</span></div>
      <nav aria-label="Pages" className="flex gap-1 text-[13px] font-medium">
        <span className="rounded-md bg-accent-soft px-3 py-1.5 text-accent">Evidence map</span>
        <span className="rounded-md px-3 py-1.5 text-ink-3" title="Phase 5">Medication review</span>
        <span className="rounded-md px-3 py-1.5 text-ink-3" title="Phase 6">Gaps</span>
      </nav>
      <div className="flex-1" />
      <Search ix={ix} />
      <label className="flex items-center gap-2 text-[13px] text-ink-2">
        View as
        <select value={role} onChange={e => setRole(e.target.value as Role)}
          className="rounded-md border border-line bg-panel px-2 py-1.5 text-[13px] text-ink">
          <option value="pharmacist">Pharmacist</option>
          <option value="prescriber">Prescriber</option>
          <option value="public_health">Public health</option>
        </select>
      </label>
    </header>
  )
}

function Search({ ix }: { ix: Index }) {
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const { selectClass, selectHub, setView, setArrange } = useStore()
  const results = useMemo(() => {
    const t = q.trim().toLowerCase()
    if (t.length < 2) return []
    return ix.searchIndex.filter(r => r.label.toLowerCase().includes(t))
      .sort((a, z) => Number(z.label.toLowerCase().startsWith(t)) - Number(a.label.toLowerCase().startsWith(t))).slice(0, 8)
  }, [q, ix])
  const go = (r: Index['searchIndex'][number]) => {
    if (r.kind === 'hub' || r.kind === 'effect') { setView('systems'); setArrange('system'); selectHub(r.target); selectClass(null) }
    else { selectHub(null); selectClass(r.target) }
    setQ(r.label); setOpen(false)
  }
  return (
    <div className="relative w-72">
      <input id="search" value={q} placeholder="Search a drug, class or body system" aria-label="Search"
        onChange={e => { setQ(e.target.value); setOpen(true); setActive(0) }}
        onFocus={() => setOpen(true)} onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={e => {
          if (e.key === 'ArrowDown') { e.preventDefault(); setActive(a => Math.min(a + 1, results.length - 1)) }
          if (e.key === 'ArrowUp') { e.preventDefault(); setActive(a => Math.max(a - 1, 0)) }
          if (e.key === 'Enter' && results[active]) go(results[active])
        }}
        className="w-full rounded-md border border-line bg-panel px-3 py-1.5 text-[13px] placeholder:text-ink-3" />
      {open && results.length > 0 && (
        <ul role="listbox" className="absolute z-20 mt-1 w-full overflow-hidden rounded-lg border border-line bg-panel py-1 shadow-lg">
          {results.map((r, i) => (
            <li key={r.kind + r.label} role="option" aria-selected={i === active}>
              <button onMouseDown={() => go(r)}
                className={`flex w-full items-baseline justify-between gap-3 px-3 py-1.5 text-left text-[13px] ${i === active ? 'bg-accent-soft' : ''}`}>
                <span>{r.label}</span>
                <span className="text-[11px] text-ink-3">{r.kind === 'drug' ? r.hint : r.kind === 'effect' ? r.hint : r.kind === 'hub' ? 'Body system' : 'Drug class'}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function HeatControl({ ix }: { ix: Index }) {
  const { heat, setHeat, replay, setReplay } = useStore()
  const scen = ix.b.scenarios.scenarios
  const timer = useRef<number | null>(null)
  useEffect(() => {
    if (!replay?.playing) return
    const sc = scen.find(x => x.id === replay.scenario)!
    setHeat(sc.days[replay.day].level_rank as Heat)
    timer.current = window.setTimeout(() => {
      if (replay.day + 1 < sc.days.length) setReplay({ ...replay, day: replay.day + 1 })
      else setReplay({ ...replay, playing: false })
    }, 1400)
    return () => { if (timer.current) clearTimeout(timer.current) }
  }, [replay, scen, setHeat, setReplay])
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-[11px] font-semibold uppercase tracking-wider text-hero-ink-2">Heat level</span>
      <Segmented dark label="Heat level" value={heat} onChange={v => { setReplay(null); setHeat(v) }} options={[
        { v: 0 as Heat, label: 'Normal' },
        { v: 1 as Heat, label: 'Heat advisory', tone: 'bg-shared text-[#241800]' },
        { v: 2 as Heat, label: 'Extreme heat warning', tone: 'bg-direct text-white' },
      ]} />
      <select aria-label="Replay a real heat wave" value={replay?.scenario ?? ''}
        onChange={e => e.target.value ? setReplay({ scenario: e.target.value, day: 0, playing: true }) : setReplay(null)}
        className="rounded-md border border-hero-line bg-hero-2 px-2 py-1.5 text-[13px] text-hero-ink">
        <option value="">Replay a real NYC heat wave…</option>
        {scen.map(x => <option key={x.id} value={x.id}>{x.title}</option>)}
      </select>
    </div>
  )
}

export function ReplayBanner({ ix }: { ix: Index }) {
  const replay = useStore(s => s.replay), setReplay = useStore(s => s.setReplay)
  if (!replay) return null
  const sc = ix.b.scenarios.scenarios.find(x => x.id === replay.scenario)!
  const d = sc.days[replay.day]
  const date = new Date(d.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 rounded-lg bg-hero-2 px-4 py-2 text-[13px] text-hero-ink ring-1 ring-hero-line">
      <span className="font-display text-[15px] font-semibold">{date}</span>
      <span className="num">High {d.max_temp_f} °F · heat index {Math.round(d.max_heat_index_f)} °F</span>
      <span className={d.level_rank === 2 ? 'font-semibold text-direct' : d.level_rank === 1 ? 'font-semibold text-shared' : 'text-hero-ink-2'}>{d.nws_product}</span>
      <div className="flex gap-1" aria-hidden>
        {sc.days.map((x, i) => (
          <button key={x.date} onClick={() => setReplay({ ...replay, day: i, playing: false })} title={x.date}
            className={`h-2.5 w-4 rounded-sm ${x.level_rank === 2 ? 'bg-direct' : x.level_rank === 1 ? 'bg-shared' : 'bg-hero-line'} ${i === replay.day ? 'ring-2 ring-hero-ink' : ''}`} />
        ))}
      </div>
      <span className="flex-1" />
      <button className="text-hero-ink-2 hover:text-hero-ink" onClick={() => setReplay({ ...replay, playing: !replay.playing })}>
        {replay.playing ? 'Pause' : 'Play'}
      </button>
      <button className="text-hero-ink-2 hover:text-hero-ink" onClick={() => setReplay(null)}>Close</button>
      <span className="basis-full text-[11px] text-hero-ink-2">{sc.note} Source: NWS alerts and Central Park observations (Iowa Environmental Mesonet).</span>
    </div>
  )
}

export function Filters({ ix }: { ix: Index }) {
  const { tiers, toggleTier, bucket, setBucket, specialty, setSpecialty, role, view, topOnly, setTopOnly } = useStore()
  const tierOpts: Tier[] = ['direct', 'shared', 'guidance_only']
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[12px] text-hero-ink-2">
      {tierOpts.map(t => (
        <label key={t} className="flex cursor-pointer items-center gap-1.5">
          <input type="checkbox" checked={tiers.includes(t)} onChange={() => toggleTier(t)} className="accent-[var(--color-shared)]" />
          <i className={`inline-block h-1 w-5 rounded ${t === 'direct' ? 'bg-direct' : t === 'shared' ? 'bg-shared' : 'border-t-2 border-dashed border-guidance'}`} />
          {TIER_LABEL[t]}
        </label>
      ))}
      <select aria-label="Filter by action" value={bucket ?? ''} onChange={e => setBucket((e.target.value || null) as never)}
        className="rounded-md border border-hero-line bg-hero-2 px-2 py-1 text-hero-ink">
        <option value="">All actions</option>
        {BUCKET_ORDER.map(b => <option key={b} value={b}>{BUCKET_LABEL[b]}</option>)}
      </select>
      <select aria-label="Filter by prescriber" value={specialty ?? ''} onChange={e => setSpecialty(e.target.value || null)}
        className="rounded-md border border-hero-line bg-hero-2 px-2 py-1 text-hero-ink">
        <option value="">All prescribers</option>
        {specialtyOptions(ix).map(sp => <option key={sp} value={sp}>{sp}</option>)}
      </select>
      {view === 'ribbons' && (
        <label className="flex cursor-pointer items-center gap-1.5">
          <input type="checkbox" checked={topOnly} onChange={e => setTopOnly(e.target.checked)} /> Top pathways only
        </label>
      )}
      <span className="text-hero-ink-2/80">{ROLE_DEFAULTS[role].note}</span>
    </div>
  )
}
