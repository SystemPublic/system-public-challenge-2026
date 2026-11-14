// Evidence atlas, drug-first: medicines listed vertically (circle size = strength of heat evidence), a clear body
// on the right showing where the selected medicine and heat meet, and a panel to explore effects and risk factors.
import { motion } from 'motion/react'
import { useMemo, useState } from 'react'
import { Abstract, Section, directFor } from '../components/evidence'
import { PotentialActions, StudyForest } from './Deep'
import { BodyStory, shortVersion } from './Explain'
import { Term, useGlossary } from '../components/Glossary'
import { hubLinks, type Index } from '../data/derive'
import type { V2Class } from '../data/types'
import { Body, SYSTEMS } from './Body'
import { Forest, parseRatio, type ForestRow } from './Forest'
import { HEADLINES, KIND_LABEL, type Headline, type Kind } from './headlines'

const KIND_STYLE: Record<Kind, { fill: string; stroke: string; dash?: string }> = {
  risk: { fill: 'var(--color-heat)', stroke: 'var(--color-heat)' },
  group: { fill: 'var(--color-heat-soft)', stroke: 'var(--color-heat)' },
  null: { fill: 'var(--color-panel)', stroke: 'var(--color-ink-3)' },
  mechanism: { fill: 'var(--color-s2)', stroke: 'var(--color-s2)' },
  guidance: { fill: 'none', stroke: 'var(--color-faint)', dash: '3 3' },
}

function Dot({ h, max = 20 }: { h: Headline; max?: number }) {
  const r = Math.min(max / 2 - 1, 3 + h.strength * 1.7)
  const st = KIND_STYLE[h.kind]
  return (
    <svg width={max} height={max} viewBox={`${-max / 2} ${-max / 2} ${max} ${max}`} aria-hidden className="shrink-0">
      <circle r={r} fill={st.fill} stroke={st.stroke} strokeWidth={1.5} strokeDasharray={st.dash} />
    </svg>
  )
}

export function DrugAtlas({ ix, goHeatCheck }: { ix: Index; goHeatCheck: () => void }) {
  const v2 = ix.b.v2
  const byName = useMemo(() => Object.fromEntries(v2.classes.map(c => [c.name, c])), [v2])
  const list = useMemo(() => [...HEADLINES].filter(h => byName[h.cls]).sort((a, z) => z.strength - a.strength), [byName])
  const [sel, setSel] = useState<string | null>('Antipsychotics')
  const [system, setSystem] = useState<string | null>(null)
  const [bodyOpen, setBodyOpen] = useState(true)
  const cls = sel ? byName[sel] : null
  const head = sel ? HEADLINES.find(h => h.cls === sel)! : null
  const links = cls?.our_id ? hubLinks(ix, cls.our_id) : null
  const actsOn = (h: Headline) => {
    if (!system) return true
    const c = byName[h.cls]
    return !!(c?.our_id && hubLinks(ix, c.our_id)[system])
  }

  return (
    <main className={`grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 ${bodyOpen ? 'xl:grid-cols-[360px_minmax(0,1fr)_440px]' : 'xl:grid-cols-[360px_44px_minmax(0,1fr)]'}`}>
      {/* medicines */}
      <section className="min-h-0 overflow-y-auto rounded-lg border border-line bg-panel">
        <div className="sticky top-0 z-10 border-b border-line bg-panel px-4 pt-4 pb-3">
          <div className="eyebrow">Evidence atlas</div>
          <h1 className="font-display text-[22px] font-bold leading-tight">Which medicines make heat more dangerous</h1>
          <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-ink-3">
            <span><Term id="strength">Larger circle = more evidence</Term></span>
            {(['risk', 'group', 'null', 'mechanism'] as Kind[]).map(k => (
              <span key={k} className="flex items-center gap-1"><Dot h={{ cls: '', kind: k, plain: '', outcome: '', strength: 1.5 }} max={12} />{KIND_LABEL[k]}</span>
            ))}
          </div>
          {system && <button onClick={() => setSystem(null)} className="mt-2 rounded bg-soft px-2 py-1 text-[11.5px]">Showing medicines that act on {SYSTEMS.find(s => s.id === system)?.label.toLowerCase()} · clear</button>}
        </div>
        <ul>
          {list.map(h => {
            const on = sel === h.cls, hit = actsOn(h)
            return (
              <li key={h.cls}>
                <button onClick={() => setSel(on ? null : h.cls)}
                  className={`grid w-full grid-cols-[34px_1fr_auto] items-center gap-2 border-b border-line px-4 py-2.5 text-left transition ${on ? 'bg-heat-soft' : 'hover:bg-hov'} ${hit ? '' : 'opacity-30'}`}>
                  <span className="grid place-items-center"><Dot h={h} max={30} /></span>
                  <span className="min-w-0">
                    <span className="block text-[14px] font-semibold leading-tight">{h.cls}</span>
                    <span className="block truncate text-[11.5px] text-ink-3">{byName[h.cls]?.examples}</span>
                    <span className="mt-0.5 block text-[12px] leading-snug text-ink-2">{h.plain}</span>
                  </span>
                  <span className={`num text-right text-[13px] font-bold ${h.kind === 'risk' || h.kind === 'group' ? 'text-heat-ink' : 'text-ink-3'}`}>{h.value ?? ''}</span>
                </button>
              </li>
            )
          })}
        </ul>
      </section>

      {/* body */}
      {!bodyOpen ? (
        <button onClick={() => setBodyOpen(true)} aria-label="Show the body" title="Show the body"
          className="flex flex-col items-center gap-3 rounded-lg border border-line bg-hero py-4 text-[12px] font-semibold text-ink-2 hover:bg-hov">
          <span aria-hidden>›</span><span style={{ writingMode: 'vertical-rl' }}>Show the body</span>
        </button>
      ) : (
      <section className="flex min-h-[560px] min-w-0 flex-col rounded-lg border border-line bg-hero p-4">
        <div className="flex items-baseline justify-between gap-3">
          <div>
            <div className="eyebrow">{cls ? 'Effects in the body during heat' : 'Effects of heat on the body'}</div>
            <h2 className="font-display text-[20px] font-bold">{cls ? cls.name : 'Choose a medicine'}</h2>
          </div>
          <div className="flex flex-wrap gap-3 text-[11.5px] text-ink-2">
            <span><i className="mr-1 inline-block h-2.5 w-2.5 rounded-full bg-heat" />Direct evidence</span>
            <span><i className="mr-1 inline-block h-2.5 w-2.5 rounded-full bg-s2" />Indirect evidence</span>
            <span><i className="mr-1 inline-block h-2.5 w-2.5 rounded-full border border-dashed border-faint" />No studies</span>
            <button onClick={() => setBodyOpen(false)} className="rounded border border-line px-2 py-0.5 font-semibold hover:bg-hov" title="Hide the body to give the panels more room">Hide ‹</button>
          </div>
        </div>
        <div className="min-h-0 flex-1"><Body ix={ix} links={links} system={system} onSystem={setSystem} drugLabel={cls?.name ?? null} /></div>
      </section>
      )}

      {/* explore */}
      <aside className="min-h-0 overflow-y-auto rounded-lg border border-line bg-panel p-5">
        {cls && head ? <DrugPanel ix={ix} c={cls} h={head} goHeatCheck={goHeatCheck} />
          : system ? <SystemPanel ix={ix} system={system} pick={setSel} list={list} />
          : <Overview ix={ix} pick={setSel} />}
      </aside>
    </main>
  )
}

function riskFactorRows(ix: Index): ForestRow[] {
  return ix.b.v2.risk_factors.filter(r => r.ci_lower).map(r => ({
    label: r.factor, est: +r.value, lo: +r.ci_lower, hi: r.ci_upper ? +r.ci_upper : undefined,
    tone: r.direction === 'protective' ? 'protective' : 'risk', sub: r.outcome.toLowerCase(), pmid: r.pmid,
  }))
}

function DrugPanel({ ix, c, h, goHeatCheck }: { ix: Index; c: V2Class; h: Headline; goHeatCheck: () => void }) {
  const studies = directFor(c)
  const actions = ix.b.v2.actions.filter(a => a.class === c.name)
  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="eyebrow">{KIND_LABEL[h.kind]}{h.vetted === false ? ' · unvetted rows' : ''}</div>
        <h2 className="font-display text-[24px] font-bold leading-tight">{c.name}</h2>
        <p className="text-[12px] text-ink-3">{c.examples}</p>
      </div>

      <motion.section key={c.name} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="rounded-lg bg-soft p-4">
        <h3 className="eyebrow">Summary</h3>
        <p className="mt-1.5 text-[14.5px] leading-relaxed">{shortVersion(ix, c.name, h, c.our_id)}</p>
        {h.value && (
          <div className="mt-3 flex flex-wrap items-baseline gap-x-3 gap-y-1 border-t border-line pt-3">
            <span className="num font-display text-[30px] font-bold leading-none text-heat-ink"><Term id={h.value.split(' ')[0]}>{h.value.split(' ')[0]}</Term> {h.value.split(' ')[1]}</span>
            <span className="text-[13px] text-ink-3"><Term id="CI">95% CI {h.ci}</Term></span>
            <span className="basis-full text-[12.5px] text-ink-2">{h.outcome}.{h.pmid && <Abstract pmid={h.pmid} />}</span>
          </div>
        )}
        {h.note && <p className="mt-2 text-[12.5px] text-ink-2">{h.note}</p>}
        <GlossLink />
      </motion.section>

      <Section title="Effects in the body" note="Direct evidence: studied in people taking the drug during heat. Indirect evidence: the drug and heat were each studied separately for the same effect. No studies: mentioned in guidance only.">
        <BodyStory ix={ix} cls={c.name} ourId={c.our_id} />
      </Section>

      <Section title="Studies in heat" note="Studies of people taking this drug during hot weather or heat waves. Select a row for details.">
        {studies.length ? <StudyForest ix={ix} items={studies} parse={parseRatio} /> : <p className="text-[13px] text-ink-3">No study in the graph has measured this drug class in heat yet.</p>}
      </Section>

      <Section title="Other risk factors" note="From heat-wave studies in Chicago (1995, 1999), Adelaide (2009), France (2003), Michigan and Italy; each abstract checked. These apply to anyone, whatever their medicines.">
        <RiskFactors ix={ix} />
      </Section>

      {actions.length > 0 && (
        <Section title="Possible actions" note="Which ones apply depends on the patient; see the heat check.">
          <PotentialActions ix={ix} actions={actions} />
        </Section>
      )}
      <button onClick={goHeatCheck} className="self-start rounded-md bg-ink px-3.5 py-2 text-[13px] font-semibold text-white">Check a patient on this medicine →</button>
    </div>
  )
}

function SystemPanel({ ix, system, pick, list }: { ix: Index; system: string; pick: (c: string) => void; list: Headline[] }) {
  const s = SYSTEMS.find(x => x.id === system)!
  const heat = ix.heatStudiesByHub[system] ?? 0
  const rows = list.map(h => ({ h, c: ix.b.v2.classes.find(c => c.name === h.cls)! })).filter(({ c }) => c.our_id && hubLinks(ix, c.our_id)[system])
  return (
    <div className="flex flex-col gap-4">
      <div><div className="eyebrow">Body system</div><h2 className="font-display text-[24px] font-bold">{s.label}</h2>
        <p className="text-[13px] text-ink-2">{heat} studies link heat to {s.sub}.</p></div>
      <Section title="Medicines that act here">
        <ul className="flex flex-col gap-1.5">
          {rows.map(({ h, c }) => { const l = hubLinks(ix, c.our_id!)[system]; return (
            <li key={h.cls}><button onClick={() => pick(h.cls)} className="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-[13px] hover:bg-hov">
              <span className="flex items-center gap-2"><Dot h={h} max={16} /><b>{h.cls}</b></span>
              <span className="num text-[11.5px] text-ink-3">{l.tier === 'guidance_only' ? 'guidance only' : l.tier === 'direct' ? (h.kind === 'null' ? 'studied: no clear effect' : 'measured in heat') : `${l.drug_arm.raised} studies`}</span></button></li>) })}
        </ul>
      </Section>
    </div>
  )
}

function Overview({ ix, pick }: { ix: Index; pick: (c: string) => void }) {
  const findings: [string, string][] = [
    ['Antipsychotics', 'Psychiatric medicines carry the strongest signal: about 2× the odds of dying in the 2003 heat wave.'],
    ['NSAIDs', 'The measured evidence runs through the kidneys and sodium, not sweating.'],
    ['Insulin', 'Under-recognised: more serious lows on the hottest days.'],
    ['Lithium', 'Over-warned: every guidance source flags it; the heat studies found no clear effect.'],
    ['Opioids', 'Overdoses rise with temperature; guidance rarely says so.'],
  ]
  return (
    <div className="flex flex-col gap-4">
      <div><div className="eyebrow">Five findings</div>
        <ul className="mt-2 flex flex-col gap-2">{findings.map(([c, t]) => <li key={c}><button onClick={() => pick(c)} className="text-left text-[13.5px] leading-snug hover:underline"><b>{c}.</b> {t}</button></li>)}</ul></div>
      <Section title="Other risk factors" note="From heat-wave studies; each abstract checked."><RiskFactors ix={ix} /></Section>
      <p className="text-[11.5px] text-ink-3">{ix.b.meta.counts.findings?.toLocaleString()} graph findings, {ix.b.meta.counts.direct} direct studies checked against abstracts, {ix.b.v2.guidance_sources.length} guidance sources. System Public Graph, CC BY-NC 4.0.</p>
    </div>
  )
}

const PLAIN: Record<string, string> = {
  rf_ac: 'People with a working air conditioner had about one-fifth the odds of dying in the heat wave.',
  rf_ac_bed: 'An air conditioner in the bedroom cut the odds of hospital admission for heat illness to about one-eighth.',
  rf_alone: 'People living alone had about 8 times the odds of dying in the heat wave (wide range: small study).',
  rf_home: 'People who did not leave home each day had about 6 times the odds of dying.',
  rf_bed: 'People confined to bed had about 8 times the odds of dying.',
  rf_top: 'Living on the top floor of a building: about 5 times the odds of dying.',
  rf_social: 'Regular social contacts or activities: about one-tenth the odds of hospital admission for heat illness.',
  rf_isolation_prog: 'Areas with a programme to reduce social isolation had about a quarter fewer heat-wave deaths in people over 80.',
  rf_green: 'Older adults in ZIP codes with little green space had 17% higher odds of cardiovascular death on extreme-heat days.',
  rf_heart: 'People with heart disease had much higher odds of heat-illness admission (13.6×; very wide range).',
  rf_dementia: 'People with dementia had much higher odds of heat-illness admission (26×; very wide range).',
  rf_psych_count: 'Each additional psychotropic medicine raised the odds of dying in the 2003 heat wave by about 25%.',
}

function RiskFactors({ ix }: { ix: Index }) {
  const [open, setOpen] = useState<string | null>(null)
  return (
    <div>
      <Forest rows={riskFactorRows(ix)} />
      <ul className="mt-2 flex flex-col divide-y divide-line rounded-md border border-line">
        {ix.b.v2.risk_factors.map(r => (
          <li key={r.id}>
            <button onClick={() => setOpen(open === r.id ? null : r.id)} className="flex w-full items-start gap-2 px-3 py-2 text-left hover:bg-hov">
              <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${r.direction === 'protective' ? 'bg-green' : 'bg-heat'}`} />
              <span className="text-[12.5px] leading-snug">{PLAIN[r.id] ?? r.factor}</span>
              <span className="ml-auto shrink-0 text-[11px] text-ink-3">{open === r.id ? '−' : '+'}</span>
            </button>
            {open === r.id && (
              <div className="px-3 pb-3 text-[12px] leading-snug text-ink-2">
                <b>{r.factor}</b> → {r.outcome.toLowerCase()}: {r.statistic.replace(/_/g, ' ')} {r.value}{r.ci_lower ? ` (95% CI ${r.ci_lower}${r.ci_upper ? `–${r.ci_upper}` : ', upper bound not given in the abstract'})` : ''}.
                <span className="block">Study: {r.population}.</span>
                {r.note && <span className="block text-ink-3">{r.note}</span>}
                {ix.b.papers[r.pmid] && <span className="block text-ink-3">{ix.b.papers[r.pmid].authors} {ix.b.papers[r.pmid].year}. <i>{ix.b.papers[r.pmid].title}</i></span>}
                <Abstract pmid={r.pmid} />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

function GlossLink() {
  const show = useGlossary(g => g.show)
  return <button onClick={() => show('ratio')} className="mt-1 text-[12px] font-semibold text-accent hover:underline">How to read these numbers</button>
}
