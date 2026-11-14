// Plain-language explanation of how one drug class and heat meet in the body, one card per effect,
// with the evidence for that effect inside its own card. Sources: our graph analysis (counts, rows),
// guidance documents (what the drug does), and general heat physiology as stated in CDC/NYC/UKHSA guidance.
import { useState } from 'react'
import { Abstract } from '../components/evidence'
import type { Index } from '../data/derive'
import type { Link } from '../data/types'
import type { Headline } from './headlines'
import { useGraphFocus } from '../graph/focus'

// What heat does to each effect, and why heat + drug together matter. General physiology, as described in
// the guidance documents we read (CDC 2025, NYC Health, UKHSA 2024, Health Canada 2011); not from the graph.
const EFFECT_TEXT: Record<string, { heat: string; why: string }> = {
  heat_illness: { heat: 'Heat pushes body temperature up; the body copes by sweating and widening skin blood vessels.', why: 'If a medicine blunts sweating or the brain\'s temperature control, the body cannot shed heat and heat exhaustion or heat stroke comes on faster.' },
  confusion: { heat: 'Heat itself can bring on confusion, especially in older people.', why: 'A confused or sedated person is less likely to notice overheating, drink enough or move somewhere cool.' },
  low_bp: { heat: 'Heat widens blood vessels and drains fluid through sweat, which lowers blood pressure.', why: 'A medicine that lowers blood pressure further raises the chance of dizziness, fainting and falls on hot days.' },
  heart_rhythm: { heat: 'Heat makes the heart work harder and shifts the body\'s salts.', why: 'Medicines that affect heart rhythm add to that strain.' },
  kidney: { heat: 'Dehydration in heat cuts blood flow to the kidneys.', why: 'A medicine that also stresses the kidneys can tip them into acute injury.' },
  sodium: { heat: 'Heavy sweating, and drinking plain water to replace it, lowers blood sodium.', why: 'Medicines that already lower sodium make it worse; low sodium causes confusion, falls and seizures.' },
  potassium: { heat: 'Fluid shifts in heat change potassium levels.', why: 'Medicines that raise or lower potassium add to the imbalance.' },
  low_sugar: { heat: 'Heat speeds insulin absorption from the skin and often changes eating.', why: 'Low blood sugar becomes more likely, and its symptoms are easy to mistake for heat exhaustion.' },
  ketoacidosis: { heat: 'Dehydration in heat raises blood sugar and ketones.', why: 'Medicines that already push toward ketoacidosis make a dangerous crisis more likely.' },
  fluid_loss: { heat: 'Heat drains fluid through sweat.', why: 'Medicines that increase urine, blunt thirst or cause diarrhoea add to the loss.' },
  falls: { heat: 'Dizziness, low blood pressure and weakness in heat make falls more likely.', why: 'Sedating medicines and those that lower blood pressure add to the risk.' },
  drug_level: { heat: 'Dehydration concentrates medicines that the kidneys clear.', why: 'For medicines with a narrow safe range, such as lithium, levels can rise toward toxicity.' },
}

export const DOC_SHORT: Record<string, string> = {
  cdc_2025: 'CDC', nyc_page: 'NYC Health', nyc_han_2026: 'NYC Health alert 2026', hc_2011: 'Health Canada 2011',
  hc_2024: 'Health Canada 2024', ukhsa_2024: 'UK Health Security Agency', ansm_2023: 'France (ANSM)', vic_2024: 'Victoria, Australia',
}

function DocLinks({ ix, ids }: { ix: Index; ids: string[] }) {
  return <>{ids.map((id, i) => {
    const d = ix.b.guidance.documents.find(x => x.id === id)
    return <span key={id}>{i > 0 ? ', ' : ''}<a href={d?.url} target="_blank" rel="noreferrer" title={d ? `${d.publisher} (${d.year}): ${d.title}` : id} className="text-accent hover:underline">{DOC_SHORT[id] ?? id}</a></span>
  })}</>
}

const TIER_WORDS: Record<string, { t: string; c: string }> = {
  direct: { t: 'Direct evidence', c: 'bg-heat text-white' },
  shared: { t: 'Indirect evidence', c: 'bg-s2 text-white' },
  guidance_only: { t: 'No studies', c: 'border border-dashed border-faint text-ink-3' },
}

function strengthWords(l: Link) {
  const a = l.drug_arm
  if (l.tier === 'direct') return 'Studied in people taking the drug during heat.'
  if (l.tier === 'guidance_only') return 'Mentioned in guidance; no studies found.'
  const share = a.studies ? a.raised / a.studies : 0
  const drug = share >= 0.6 ? 'mostly raised risk' : share >= 0.4 ? 'about half raised risk' : 'mixed'
  const heat = l.heat_arm_studies >= 20 ? `${l.heat_arm_studies}, plenty` : l.heat_arm_studies >= 8 ? `${l.heat_arm_studies}, some` : `${l.heat_arm_studies}, few`
  return `Drug studies: ${drug}. Heat studies: ${heat}.`
}

export function linksForStory(ix: Index, ourId: string | null) {
  if (!ourId) return []
  const rank = (t: string) => ({ direct: 3, shared: 2, guidance_only: 1 } as Record<string, number>)[t] ?? 0
  return (ix.linksByClass[ourId] ?? []).filter(l => ['direct', 'shared', 'guidance_only'].includes(l.tier) && EFFECT_TEXT[l.effect])
    .sort((a, z) => rank(z.tier) - rank(a.tier) || z.drug_arm.raised - a.drug_arm.raised)
}

/** A short narrative for the top of the drug panel, built from the headline and the strongest links. */
export function shortVersion(ix: Index, _name: string, h: Headline, ourId: string | null) {
  const ls = linksForStory(ix, ourId)
  const routes = ls.filter(l => l.tier !== 'guidance_only').slice(0, 3).map(l => ix.effect[l.effect]?.label.toLowerCase())
  const gl = ls.filter(l => l.tier === 'guidance_only').slice(0, 2)
  const guided = gl.map(l => ix.effect[l.effect]?.label.toLowerCase())
  const gdocs = [...new Set(gl.flatMap(l => l.guidance_docs))].map(d => DOC_SHORT[d] ?? d).slice(0, 3)
  const lead = h.kind === 'risk' || h.kind === 'group'
    ? `${h.plain} (${h.outcome.charAt(0).toLowerCase() + h.outcome.slice(1)}).`
    : h.kind === 'null' ? `Studied in heat, with no clear effect so far.` : `Not yet studied in people taking it during heat.`
  const how = routes.length ? ` Main effects in the body: ${routes.join(', ')}.` : ''
  const g = guided.length ? ` Heat-health guidance (${gdocs.join(', ')}) also mentions ${guided.join(' and ')}, with no studies behind it.` : ''
  return lead + how + g
}

export function BodyStory({ ix, cls, ourId }: { ix: Index; cls: string; ourId: string | null }) {
  const ls = linksForStory(ix, ourId)
  const [open, setOpen] = useState<string | null>(null)
  const setFocus = useGraphFocus(g => g.set)
  if (!ls.length) return <p className="text-[13px] text-ink-3">Our analysis found no body-system link for this group.</p>
  const mentions = ix.b.guidance.mentions
  return (
    <ol className="flex flex-col gap-3">
      {ls.map(l => {
        const t = EFFECT_TEXT[l.effect], tw = TIER_WORDS[l.tier], a = l.drug_arm
        const mech = [...new Set(mentions.filter(m => m.class === ourId && m.effect === l.effect).map(m => m.mechanism))].filter(m => !/^named|^listed/i.test(m)).slice(0, 2)
        const docs = [...new Set(mentions.filter(m => m.class === ourId && m.effect === l.effect).map(m => m.doc))]
        const k = l.effect, on = open === k
        return (
          <li key={k} className="rounded-lg border border-line">
            <div className="p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h4 className="font-display text-[16px] font-bold">{ix.effect[l.effect]?.label}</h4>
                <span className={`rounded px-1.5 py-0.5 text-[10.5px] font-bold uppercase tracking-wide ${tw.c}`}>{tw.t}</span>
              </div>
              <dl className="mt-2 grid grid-cols-[92px_1fr] gap-x-3 gap-y-1.5 text-[13px] leading-snug">
                <dt className="font-semibold text-ink-3">The drug</dt>
                <dd>
                  {mech.length ? <>{mech.join('; ')}. </> : null}
                  {a.studies > 0 && <><b>{a.raised} of {a.studies}</b> studies linked {cls.toLowerCase()} to more {ix.effect[l.effect]?.label.toLowerCase()}{a.lowered ? <> ({a.lowered} to less)</> : null}.</>}
                  {!mech.length && !a.studies && l.direct_ids.length > 0 && <>Measured directly together with heat (below).</>}
                </dd>
                {docs.length > 0 && <><dt className="font-semibold text-ink-3">Named by</dt>
                <dd className="text-[12.5px]"><DocLinks ix={ix} ids={docs} /> <span className="text-ink-3">(heat-health guidance)</span></dd></>}
                <dt className="font-semibold text-ink-3">Heat</dt>
                <dd>{t.heat}{l.heat_arm_studies ? <> <b>{l.heat_arm_studies}</b> studies link heat to this.</> : null}</dd>
                <dt className="font-semibold text-heat-ink">Why it matters</dt>
                <dd className="font-semibold">{t.why}</dd>
              </dl>
              <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[11.5px] text-ink-3">
                <span>{strengthWords(l)}</span>
                <span className="flex gap-3">
                  <button onClick={() => setOpen(on ? null : k)} className="font-semibold text-accent hover:underline">{on ? 'Hide studies' : 'Show studies'}</button>
                  {l.tier !== 'guidance_only' && <button onClick={() => { setFocus(ourId, l.effect); location.hash = 'graph' }} className="font-semibold text-accent hover:underline">Show in the graph →</button>}
                </span>
              </div>
            </div>
            {on && <Evidence ix={ix} l={l} />}
          </li>
        )
      })}
    </ol>
  )
}

function Evidence({ ix, l }: { ix: Index; l: Link }) {
  const dirs = ix.b.direct.filter(d => l.direct_ids.includes(d.id))
  const drug = l.drug_arm_ids.map(id => ix.b.findings[id]).filter(f => f && f.dir === 'raised').slice(0, 5)
  const heat = (ix.b.heat_arms.find(h => h.effect === l.effect)?.ids ?? []).map(id => ix.b.findings[id]).filter(f => f && f.dir !== 'lowered').slice(0, 3)
  const paper = (p: string) => ix.b.papers[p] ? `${ix.b.papers[p].authors} ${ix.b.papers[p].year}, ${ix.b.papers[p].journal}` : ''
  const Row = ({ f }: { f: (typeof drug)[number] }) => (
    <li className="text-[12px] leading-snug">
      <span className="text-ink-2">{f.v1} → {f.v2}</span>: <b className="num">{f.stat.replace(/_/g, ' ')} {f.value}{f.lo ? ` (${f.lo}–${f.hi})` : ''}</b>
      <span className="block text-[11px] text-ink-3">{paper(f.pmid)}{f.src !== 'in_csv' ? ' · unvetted' : ''}</span>
      {f.correction && <span className="block text-[11px] text-heat-ink">Corrected by us: {f.correction.text}</span>}
      {f.pmid && <Abstract pmid={f.pmid} />}
    </li>
  )
  return (
    <div className="flex flex-col gap-3 border-t border-line bg-soft p-3">
      {dirs.length > 0 && <section><h5 className="text-[11.5px] font-bold text-ink-2">Studies of this drug in heat</h5>
        <ul className="mt-1 flex flex-col gap-1.5">{dirs.map(d => <li key={d.id} className="text-[12px] leading-snug">{d.finding} <b className="num">{d.statistic.replace(/_/g, ' ')} {d.value}{d.ci_lower ? ` (${d.ci_lower}–${d.ci_upper})` : ''}</b> <Abstract pmid={d.pmid} /></li>)}</ul></section>}
      {drug.length > 0 && <section><h5 className="text-[11.5px] font-bold text-ink-2">The drug and this effect (examples, {drug.length} of {l.drug_arm.raised} showing raised risk)</h5>
        <ul className="mt-1 flex flex-col gap-2">{drug.map(f => <Row key={f.id} f={f} />)}</ul></section>}
      {heat.length > 0 && <section><h5 className="text-[11.5px] font-bold text-ink-2">Heat and this effect (examples, {heat.length} of {l.heat_arm_studies})</h5>
        <ul className="mt-1 flex flex-col gap-2">{heat.map(f => <Row key={f.id} f={f} />)}</ul></section>}
      <p className="text-[10.5px] text-ink-3">Rows from the System Public Graph as extracted ("→" reads as "linked to"); checked against abstracts only where marked.</p>
    </div>
  )
}
