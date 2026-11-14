// Right-hand panel: what is selected, with its evidence in plain words. The full evidence drawer is phase 4;
// this panel already shows real findings, papers, trust tags and corrections.
import { BUCKET_LABEL, DRAWN, TIER_LABEL, hubLabel, hubLinks, score, type Index } from '../data/derive'
import type { Link } from '../data/types'
import { useStore } from '../state/store'
import { TOUR } from './tour'

const tierChip: Record<string, string> = {
  direct: 'bg-direct/12 text-direct', shared: 'bg-shared/15 text-shared', guidance_only: 'bg-guidance/15 text-ink-2',
  direct_misuse: 'bg-guidance/15 text-ink-2', weak: 'bg-guidance/15 text-ink-2',
}
const srcLabel: Record<string, string> = {
  in_csv: 'Quality-filtered graph', api_only_ungrounded: 'Live API only', api_only_grounded_suspect: 'Live API only (removed from snapshot)',
}

export function DetailPanel({ ix }: { ix: Index }) {
  const s = useStore()
  return (
    <aside className="flex min-h-0 flex-col gap-4 overflow-y-auto rounded-xl border border-line bg-panel p-5" aria-live="polite">
      {s.tourStep >= 0 && <TourCard />}
      {s.selectedFinding ? <FindingCard ix={ix} id={s.selectedFinding} />
        : s.selectedClass ? <ClassCard ix={ix} id={s.selectedClass} />
        : s.selectedHub ? <HubCard ix={ix} id={s.selectedHub} />
        : <Overview ix={ix} />}
    </aside>
  )
}

function TourCard() {
  const step = useStore(s => s.tourStep)
  const t = TOUR[step]
  return (
    <div className="rounded-lg bg-heat-soft p-3 text-[13px] leading-relaxed">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-heat-ink">Finding {step + 1} of {TOUR.length}</div>
      {t.caption}
    </div>
  )
}

function Overview({ ix }: { ix: Index }) {
  const c = ix.b.meta.counts
  const drawn = ix.b.links.filter(l => l.tier === 'direct' || l.tier === 'shared').length
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="font-display text-[20px] font-semibold leading-tight">Which medicines make heat more dangerous</h2>
        <p className="mt-2 text-[14px] leading-relaxed text-ink-2">
          Each dot is a drug class; each hub is a body system heat strains. Select one to see the studies linking them, or take the guided tour.
        </p>
      </div>
      <dl className="grid grid-cols-2 gap-3">
        <Stat n="1,999,877" l="graph findings scanned" />
        <Stat n={String(drawn)} l="evidence-backed links" />
        <Stat n={String(c.direct)} l="direct studies, abstract-checked" />
        <Stat n={String(c.guidance_documents ?? 0)} l="guidance documents compared" />
      </dl>
      <p className="text-[12px] leading-relaxed text-ink-3">
        Sources: System Public Graph ({ix.b.meta.source.split(';')[0]}), PubMed, 8 heat-health guidance documents, Medicare Part D 2024, NWS. Shared pathways link a drug and heat to the same body effect in different studies; they are not proof of an interaction in one person.
      </p>
    </div>
  )
}

function Stat({ n, l }: { n: string; l: string }) {
  return <div className="rounded-lg bg-canvas p-3"><dt className="num font-display text-[22px] font-semibold">{n}</dt><dd className="text-[12px] text-ink-2">{l}</dd></div>
}

function ClassCard({ ix, id }: { ix: Index; id: string }) {
  const c = ix.cls[id]
  const tiers = useStore(s => s.tiers)
  const links = (ix.linksByClass[id] ?? []).filter(l => DRAWN.includes(l.tier) || l.tier === 'direct_misuse').sort((a, z) => score(z) - score(a))
  const buckets = c.buckets ?? []
  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-3">Drug class{c.named_in_brief ? ' · named in the brief' : ''}</div>
        <h2 className="font-display text-[22px] font-semibold">{c.label}</h2>
        <p className="text-[12px] text-ink-3">{c.members.slice(0, 6).join(', ')}</p>
      </div>
      <section>
        <h3 className="mb-2 text-[12px] font-semibold uppercase tracking-wider text-ink-3">Evidence by body effect</h3>
        <ul className="flex flex-col gap-2">
          {links.map(l => <LinkRow key={l.effect} ix={ix} l={l} muted={!tiers.includes(l.tier)} />)}
          {!links.length && <li className="text-[13px] text-ink-2">Nothing in the graph links this class to heat beyond drug use.</li>}
        </ul>
      </section>
      {buckets.length > 0 && (
        <section>
          <h3 className="mb-2 text-[12px] font-semibold uppercase tracking-wider text-ink-3">What guidance says to do</h3>
          <div className="flex flex-wrap gap-1.5">
            {buckets.map(b => <span key={b} className="rounded-full bg-accent-soft px-2.5 py-1 text-[12px] font-medium text-accent">{BUCKET_LABEL[b]}</span>)}
          </div>
          <p className="mt-2 text-[12px] text-ink-3">Named in {c.guidance_docs?.length ?? 0} of {ix.b.guidance.documents.length} guidance documents.</p>
        </section>
      )}
      {c.specialties && (
        <section>
          <h3 className="mb-2 text-[12px] font-semibold uppercase tracking-wider text-ink-3">Who prescribes it</h3>
          <ul className="flex flex-col gap-1">
            {c.specialties.slice(0, 5).map(([t, v]) => (
              <li key={t} className="grid grid-cols-[120px_1fr_36px] items-center gap-2 text-[12px]">
                <span className="truncate text-ink-2">{t}</span>
                <span className="h-2 rounded-full bg-canvas"><span className="block h-2 rounded-full bg-accent" style={{ width: `${Math.round(v * 100)}%` }} /></span>
                <span className="num text-right text-ink-2">{Math.round(v * 100)}%</span>
              </li>
            ))}
          </ul>
          <p className="mt-1 text-[11px] text-ink-3">Share of Medicare Part D claims, 2024 (older adults).</p>
        </section>
      )}
    </div>
  )
}

function LinkRow({ ix, l, muted, byClass }: { ix: Index; l: Link; muted: boolean; byClass?: boolean }) {
  const a = l.drug_arm
  const dir = l.direct_ids.map(d => ix.b.direct.find(x => x.id === d)!).filter(Boolean)
  const selectClass = useStore(s => s.selectClass)
  return (
    <li className={`rounded-lg border border-line p-2.5 ${muted ? 'opacity-50' : ''}`}>
      <div className="flex items-center justify-between gap-2">
        {byClass
          ? <button className="text-left text-[13px] font-medium text-accent hover:underline" onClick={() => selectClass(l.class)}>
              {ix.cls[l.class].label} <span className="font-normal text-ink-3">· {ix.effect[l.effect]?.label}</span></button>
          : <span className="text-[13px] font-medium">{ix.effect[l.effect]?.label ?? l.effect}</span>}
        <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${tierChip[l.tier]}`}>{TIER_LABEL[l.tier]}{l.direct_scope.includes('group') && !l.direct_scope.includes('class') ? ' (as a group)' : ''}</span>
      </div>
      {dir.map(d => (
        <p key={d.id} className="mt-1 text-[12px] leading-snug text-ink-2">
          {d.statistic.replace(/_/g, ' ')} {d.value}{d.ci_lower ? ` (${d.ci_lower}–${d.ci_upper})` : ''}: {d.finding}
        </p>
      ))}
      {a.studies > 0 && (
        <p className="num mt-1 text-[12px] text-ink-2">
          Drug side: {a.raised} of {a.studies} studies show raised risk, {a.lowered} lowered. Heat side: {l.heat_arm_studies} studies.
        </p>
      )}
      {l.guidance_docs.length > 0 && <p className="mt-1 text-[11px] text-ink-3">Named in guidance: {l.guidance_docs.join(', ')}</p>}
    </li>
  )
}

function HubCard({ ix, id }: { ix: Index; id: string }) {
  const rows = ix.b.classes.map(c => ({ c, l: hubLinks(ix, c.id)[id] })).filter(r => r.l).sort((a, z) => score(z.l) - score(a.l))
  const effects = ix.b.effects.filter(e => e.hub === id)
  const heat = ix.b.heat_arms.filter(h => effects.some(e => e.id === h.effect))
  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-3">Body system</div>
        <h2 className="font-display text-[22px] font-semibold">{hubLabel(ix.b, id)}</h2>
        <p className="num text-[13px] text-ink-2">Heat side: {heat.reduce((s, h) => s + h.studies, 0)} studies link heat to {effects.map(e => e.label.toLowerCase()).join(' or ')}.</p>
      </div>
      <p className="text-[12px] text-ink-3">Each small dot on the map is one study showing raised risk. Select a dot to read it.</p>
      <ul className="flex flex-col gap-2">{rows.map(r => <LinkRow key={r.c.id} ix={ix} l={r.l} muted={false} byClass />)}</ul>
    </div>
  )
}

function FindingCard({ ix, id }: { ix: Index; id: string }) {
  const selectFinding = useStore(s => s.selectFinding)
  if (id.startsWith('direct:')) {
    const d = ix.b.direct.find(x => x.id === id.slice(7))!
    const p = ix.b.papers[d.pmid]
    return (
      <div className="flex flex-col gap-3">
        <button className="self-start text-[12px] text-accent" onClick={() => selectFinding(null)}>← Back</button>
        <span className="self-start rounded-full bg-direct/12 px-2 py-0.5 text-[11px] font-semibold text-direct">Direct study · checked against abstract</span>
        <p className="text-[15px] leading-relaxed">{d.finding}</p>
        <p className="num font-display text-[20px] font-semibold">{d.statistic.replace(/_/g, ' ')} {d.value}{d.ci_lower ? ` (${d.ci_lower}–${d.ci_upper})` : ''}</p>
        {d.levels && (
          <table className="num text-[12px]"><tbody>{d.levels.levels.map(lv => (
            <tr key={lv.band}><td className="pr-3 text-ink-2">{lv.band} percentile</td><td>{lv.value} ({lv.ci_lower}–{lv.ci_upper})</td></tr>))}</tbody></table>
        )}
        {p && <p className="text-[12px] text-ink-2">{p.authors} {p.year}. <i>{p.title}</i> {p.journal}. PMID {d.pmid}</p>}
        {d.note && <p className="rounded-md bg-canvas p-2 text-[12px] text-ink-2">{d.note}</p>}
      </div>
    )
  }
  const f = ix.b.findings[id]
  const p = ix.b.papers[f.pmid]
  return (
    <div className="flex flex-col gap-3">
      <button className="self-start text-[12px] text-accent" onClick={() => selectFinding(null)}>← Back</button>
      <div className="flex flex-wrap gap-1.5 text-[11px] font-semibold">
        <span className="rounded-full bg-canvas px-2 py-0.5 text-ink-2">{srcLabel[f.src] ?? f.src}</span>
        <span className="rounded-full bg-canvas px-2 py-0.5 text-ink-2">{f.dir === 'raised' ? 'Raised risk' : f.dir}</span>
      </div>
      <p className="text-[15px] leading-relaxed"><b>{f.v1}</b> ↔ <b>{f.v2}</b></p>
      <p className="num font-display text-[20px] font-semibold">{f.stat.replace(/_/g, ' ')} {f.value}{f.lo ? ` (${f.lo}–${f.hi})` : ''}</p>
      {f.pop && <p className="text-[12px] text-ink-2">Population: {f.pop}</p>}
      {p && <p className="text-[12px] text-ink-2">{p.authors} {p.year}. <i>{p.title}</i> {p.journal}. PMID {f.pmid}</p>}
      {f.correction && <p className="rounded-md bg-direct/10 p-2 text-[12px] text-ink">Corrected by us: {f.correction.text}</p>}
      <p className="text-[11px] text-ink-3">Values as extracted by the graph; not checked against the abstract unless marked.</p>
    </div>
  )
}
