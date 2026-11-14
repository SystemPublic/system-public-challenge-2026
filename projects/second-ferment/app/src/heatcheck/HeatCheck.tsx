import { AnimatePresence, motion } from 'motion/react'
import { useMemo, useState } from 'react'
import { DirectList, GuidanceTable, LabelNote, RiskFactorList, Section, SharedPathway, SourceChips, directFor } from '../components/evidence'
import type { Index } from '../data/derive'
import { BASIS_LABEL, COLOUR_LABEL, allMedNames, buildPlan, type Card, type Colour, type Plan } from './engine'
import { CONDITIONS, DEMO_PATIENTS, HEAT_QUESTIONS, blankPatient, type Patient, type YN } from './patients'

const COL: Record<Colour, { chip: string; ring: string; soft: string; dot: string }> = {
  red: { chip: 'bg-red text-white', ring: 'ring-red', soft: 'bg-red-soft', dot: 'bg-red' },
  amber: { chip: 'bg-amber text-white', ring: 'ring-amber', soft: 'bg-amber-soft', dot: 'bg-amber' },
  green: { chip: 'bg-green text-white', ring: 'ring-green', soft: 'bg-green-soft', dot: 'bg-green' },
  blue: { chip: 'bg-blue text-white', ring: 'ring-blue', soft: 'bg-blue-soft', dot: 'bg-blue' },
}
const BAND: Record<Plan['band'], string> = { Low: 'bg-green-soft text-green', Elevated: 'bg-amber-soft text-amber', High: 'bg-red-soft text-red', 'Very high': 'bg-red text-white' }
const HEAT_LEVELS = ['Normal day', 'Heat advisory', 'Extreme heat warning']

export function HeatCheck({ ix }: { ix: Index }) {
  const [p, setP] = useState<Patient>(DEMO_PATIENTS[0].patient)
  const [heat, setHeat] = useState(2)
  const [sel, setSel] = useState<string | null>(null)
  const [modal, setModal] = useState<'note' | 'plan' | null>(null)
  const plan = useMemo(() => buildPlan(ix.b, p, heat), [ix, p, heat])
  const card = plan.cards.find(c => c.id === sel) ?? null

  return (
    <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 xl:grid-cols-[340px_minmax(0,1fr)_420px]">
      <Intake ix={ix} p={p} setP={x => { setP(x); setSel(null) }} plan={plan} />
      <PlanView plan={plan} p={p} heat={heat} setHeat={setHeat} sel={sel} setSel={setSel} onModal={setModal} />
      <Detail ix={ix} card={card} plan={plan} />
      <AnimatePresence>{modal && <Modal kind={modal} plan={plan} p={p} heat={heat} close={() => setModal(null)} />}</AnimatePresence>
    </div>
  )
}

function Panel({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return <div className={`min-h-0 overflow-y-auto rounded-lg border border-line bg-panel ${className}`}>{children}</div>
}

function Intake({ ix, p, setP, plan }: { ix: Index; p: Patient; setP: (p: Patient) => void; plan: Plan }) {
  const [q, setQ] = useState('')
  const names = useMemo(() => allMedNames(ix.b), [ix])
  const sugg = q.length >= 2 ? names.filter(n => n.name.toLowerCase().includes(q.toLowerCase()) && !p.meds.includes(n.name)).slice(0, 6) : []
  const addMed = (m: string) => { if (m && !p.meds.includes(m)) setP({ ...p, meds: [...p.meds, m] }); setQ('') }
  const setH = (k: keyof Patient['heat'], v: YN) => setP({ ...p, heat: { ...p.heat, [k]: v } })
  return (
    <Panel className="p-4">
      <div className="eyebrow">Demo patients (synthetic)</div>
      <div className="mt-2 flex flex-col gap-1.5">
        {DEMO_PATIENTS.map(d => (
          <button key={d.id} onClick={() => setP(structuredClone(d.patient))}
            className={`rounded-md border px-3 py-2 text-left text-[13px] ${p.name === d.patient.name ? 'border-ink bg-soft' : 'border-line hover:bg-hov'}`}>
            <b>{d.patient.name.split(' (')[0]}</b> <span className="text-ink-3">· {d.blurb}</span>
          </button>
        ))}
        <button onClick={() => setP(blankPatient())} className="text-left text-[12px] text-ink-3 hover:text-ink">Start a blank patient</button>
      </div>

      <h3 className="eyebrow mt-5">Patient</h3>
      <div className="mt-2 grid grid-cols-[1fr_72px_96px] gap-2">
        <input aria-label="Name" value={p.name} onChange={e => setP({ ...p, name: e.target.value })} placeholder="Name" className="rounded border border-line px-2 py-1.5 text-[13px]" />
        <input aria-label="Age" type="number" value={p.age ?? ''} onChange={e => setP({ ...p, age: e.target.value ? +e.target.value : null })} placeholder="Age" className="num rounded border border-line px-2 py-1.5 text-[13px]" />
        <select aria-label="Sex" value={p.sex} onChange={e => setP({ ...p, sex: e.target.value as Patient['sex'] })} className="rounded border border-line px-1.5 py-1.5 text-[13px]">
          <option value="">Sex</option><option value="female">Female</option><option value="male">Male</option><option value="other">Other</option>
        </select>
      </div>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {CONDITIONS.map(c => {
          const on = p.conditions.includes(c.id)
          return <button key={c.id} onClick={() => setP({ ...p, conditions: on ? p.conditions.filter(x => x !== c.id) : [...p.conditions, c.id] })}
            className={`rounded-full border px-2.5 py-1 text-[12px] ${on ? 'border-ink bg-ink text-white' : 'border-line text-ink-2 hover:bg-hov'}`}>{c.label}</button>
        })}
      </div>

      <h3 className="eyebrow mt-5">Medicines</h3>
      <div className="relative mt-2">
        <input aria-label="Add a medicine" value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && sugg[0]) addMed(sugg[0].name) }}
          placeholder="Type a generic name, e.g. furosemide" className="w-full rounded border border-line px-2 py-1.5 text-[13px]" />
        {sugg.length > 0 && (
          <ul className="absolute z-10 mt-1 w-full rounded-md border border-line bg-panel py-1 shadow-lg">
            {sugg.map(s => <li key={s.name}><button onClick={() => addMed(s.name)} className="flex w-full justify-between px-2.5 py-1 text-left text-[13px] hover:bg-hov"><span>{s.name}</span><span className="text-[11px] text-ink-3">{s.cls}</span></button></li>)}
          </ul>
        )}
      </div>
      <ul className="mt-2 flex flex-col gap-1">
        {plan.meds.map(m => (
          <li key={m.name} className="flex items-center justify-between rounded bg-soft px-2.5 py-1.5 text-[13px]">
            <span><b>{m.name}</b> <span className="text-ink-3">· {m.cls?.name ?? 'not in the heat list'}</span></span>
            <button aria-label={`Remove ${m.name}`} onClick={() => setP({ ...p, meds: p.meds.filter(x => x !== m.name) })} className="text-ink-3 hover:text-ink">×</button>
          </li>
        ))}
      </ul>

      <h3 className="eyebrow mt-5">Place</h3>
      <div className="mt-2 flex items-center gap-2">
        <input aria-label="NYC ZIP code" value={p.zip} onChange={e => setP({ ...p, zip: e.target.value.replace(/\D/g, '').slice(0, 5) })} placeholder="NYC ZIP" className="num w-24 rounded border border-line px-2 py-1.5 text-[13px]" />
        {plan.hvi ? (
          <span className="flex items-center gap-2 text-[12px] text-ink-2">
            <span className="flex gap-0.5" aria-hidden>{[1, 2, 3, 4, 5].map(i => <i key={i} className={`h-3 w-2.5 rounded-sm ${i <= plan.hvi!.hvi ? 'bg-heat' : 'bg-line'}`} />)}</span>
            {plan.hvi.neighbourhood}, heat vulnerability {plan.hvi.hvi}/5
          </span>
        ) : p.zip.length === 5 ? <span className="text-[12px] text-ink-3">No NYC score for this ZIP</span> : null}
      </div>

      <h3 className="eyebrow mt-5">CDC HEAT questionnaire</h3>
      {HEAT_QUESTIONS.map(s => (
        <div key={s.section} className="mt-2.5">
          <div className="text-[12px] font-semibold text-ink-2">{s.section}</div>
          {s.items.map(it => (
            <div key={it.key} className="mt-1 flex items-center justify-between gap-2 text-[12.5px]">
              <span className={p.heat[it.key] === it.risky ? 'font-semibold text-heat-ink' : 'text-ink-2'}>{it.q}</span>
              <div className="flex shrink-0 overflow-hidden rounded border border-line text-[11.5px]">
                {(['yes', 'no', 'ask'] as YN[]).map(v => (
                  <button key={v} onClick={() => setH(it.key, v)} className={`px-1.5 py-0.5 ${p.heat[it.key] === v ? 'bg-ink text-white' : 'text-ink-3 hover:bg-hov'}`}>{v === 'ask' ? 'Ask' : v === 'yes' ? 'Yes' : 'No'}</button>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
      <p className="mt-3 text-[11px] text-ink-3">Questions follow CDC's HEAT risk screening questionnaire (2024). "Ask" means not yet known.</p>
    </Panel>
  )
}

function PlanView({ plan, p, heat, setHeat, sel, setSel, onModal }: {
  plan: Plan; p: Patient; heat: number; setHeat: (n: number) => void; sel: string | null; setSel: (s: string) => void; onModal: (m: 'note' | 'plan') => void
}) {
  const groups = ['Medicines', 'Conditions', 'Situation', 'Place'] as const
  const pos = plan.factors.filter(f => f.points > 0)
  const shown = plan.factors.filter(f => f.points > 0 || (f.group === 'Medicines' && f.points === 0))
  const total = pos.reduce((s, f) => s + f.points, 0) || 1
  const gcol: Record<string, string> = { Medicines: 'bg-s3', Conditions: 'bg-s2', Situation: 'bg-heat', Place: 'bg-s1' }
  return (
    <Panel className="flex flex-col">
      <div className="border-b border-line p-5">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <div>
            <div className="eyebrow">Heat plan · planning for 1–4 July 2026 (NWS Extreme Heat Warning, Central Park 100 °F)</div>
            <h2 className="font-display text-[26px] font-bold leading-tight">{p.name || 'New patient'}{p.age ? `, ${p.age}` : ''}</h2>
          </div>
          <div className="flex-1" />
          <div className="no-print flex gap-2">
            <button onClick={() => onModal('note')} className="rounded-md border border-line-2 px-3 py-1.5 text-[13px] font-semibold hover:bg-hov">Note for the EHR</button>
            <button onClick={() => onModal('plan')} className="rounded-md bg-ink px-3 py-1.5 text-[13px] font-semibold text-white">Patient heat plan</button>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <span className={`rounded-md px-3 py-1.5 font-display text-[18px] font-bold ${BAND[plan.band]}`}>{plan.band} heat risk</span>
          <div className="flex rounded-md border border-line p-0.5 text-[12px]" role="radiogroup" aria-label="Heat level">
            {HEAT_LEVELS.map((l, i) => <button key={l} role="radio" aria-checked={heat === i} onClick={() => setHeat(i)} className={`rounded px-2.5 py-1 ${heat === i ? 'bg-heat text-white' : 'text-ink-3 hover:text-ink'}`}>{l}</button>)}
          </div>
          {plan.unknowns.length > 0 && <span className="text-[12px] text-amber">{plan.unknowns.length} questions still to ask</span>}
        </div>
        <div className="mt-4">
          <div className="flex h-3 overflow-hidden rounded-full bg-soft" aria-hidden>
            {groups.map(g => {
              const w = pos.filter(f => f.group === g).reduce((s, f) => s + f.points, 0)
              return w ? <motion.span key={g} className={gcol[g]} initial={false} animate={{ width: `${(w / total) * 100}%` }} /> : null
            })}
          </div>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-ink-2">
            {groups.map(g => {
              const fs = shown.filter(f => f.group === g)
              return fs.length ? <span key={g}><i className={`mr-1.5 inline-block h-2 w-2 rounded-full ${gcol[g]}`} /><b>{g}:</b> {fs.map(f => f.label).join(', ')}</span> : null
            })}
            {plan.factors.filter(f => f.group === 'Protective').map(f => <span key={f.id} className="text-green"><b>Protective:</b> {f.label}</span>)}
          </div>
        </div>
        {plan.alerts.map(a => (
          <p key={a.text} className="mt-3 rounded-md bg-heat-soft px-3 py-2 text-[12.5px] text-heat-ink">{a.text}{a.pmid && <a className="ml-1 font-semibold underline" href={`https://pubmed.ncbi.nlm.nih.gov/${a.pmid}/`} target="_blank" rel="noreferrer">PMID {a.pmid}</a>}</p>
        ))}
      </div>
      <div className="flex flex-col gap-2.5 p-5">
        <div className="flex flex-wrap gap-3 text-[11.5px] text-ink-3">
          {(Object.keys(COLOUR_LABEL) as Colour[]).map(c => <span key={c}><i className={`mr-1.5 inline-block h-2.5 w-2.5 rounded-sm ${COL[c].dot}`} />{COLOUR_LABEL[c]}</span>)}
        </div>
        {plan.cards.length === 0 && <p className="text-[14px] text-ink-3">Add medicines or answer the HEAT questions to build a plan.</p>}
        {plan.cards.map((c, i) => <CardRow key={c.id} c={c} i={i} on={sel === c.id} onClick={() => setSel(c.id)} />)}
        <p className="mt-2 text-[11px] text-ink-3">Recommendations are drafts for clinician review, built from transparent rules over the evidence and guidance shown. Not a substitute for clinical judgement.</p>
      </div>
    </Panel>
  )
}

function CardRow({ c, i, on, onClick }: { c: Card; i: number; on: boolean; onClick: () => void }) {
  return (
    <motion.button layout initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}
      onClick={onClick} className={`grid grid-cols-[6px_1fr] overflow-hidden rounded-md border text-left transition ${on ? `border-transparent ring-2 ${COL[c.colour].ring}` : 'border-line hover:border-line-2'}`}>
      <span className={COL[c.colour].dot} />
      <span className="flex flex-col gap-1 px-4 py-3">
        <span className="flex flex-wrap items-center gap-2">
          <span className={`rounded px-1.5 py-0.5 text-[10.5px] font-bold uppercase tracking-wide ${COL[c.colour].chip}`}>{COLOUR_LABEL[c.colour]}</span>
          <span className="text-[11.5px] text-ink-3">{c.when} · {c.who}</span>
        </span>
        <span className="font-display text-[17px] font-bold leading-snug">{c.title}</span>
        <span className="text-[13px] text-ink-2">{c.why}</span>
        <span className="flex flex-wrap gap-1.5 pt-0.5">
          {c.basis.map(bs => <span key={bs} className="rounded bg-soft px-1.5 py-0.5 text-[10.5px] font-semibold text-ink-2">{BASIS_LABEL[bs]}</span>)}
          <span className="rounded bg-accent-soft px-1.5 py-0.5 text-[10.5px] font-semibold text-accent">{c.certainty}</span>
        </span>
      </span>
    </motion.button>
  )
}

function Detail({ ix, card, plan }: { ix: Index; card: Card | null; plan: Plan }) {
  if (!card) {
    return (
      <Panel className="p-5">
        <div className="eyebrow">How this plan was made</div>
        <ul className="mt-3 flex flex-col gap-2.5 text-[13px] leading-relaxed text-ink-2">
          <li><b className="text-ink">Mitigation before modification.</b> Fix heat exposure first; keep long-term medicines unless they are as-needed or a sick-day rule applies.</li>
          <li><b className="text-ink">Intensity depends on the patient.</b> The same medicine is a red card for a hot, isolated patient and a green one for a cool, supervised patient.</li>
          <li><b className="text-ink">Every card shows its basis:</b> research evidence, guidance, drug label, or a HeatRx rule.</li>
        </ul>
        <div className="eyebrow mt-5">What drives {plan.band.toLowerCase()} risk</div>
        <ul className="mt-2 flex flex-col gap-1.5">
          {plan.factors.map(f => (
            <li key={f.id} className="grid grid-cols-[1fr_auto] gap-2 text-[12.5px]">
              <span>{f.label}{f.evidence && <span className="text-ink-3"> · {f.evidence.statistic.replace(/_/g, ' ')} {f.evidence.value}, PMID {f.evidence.pmid}</span>}</span>
              <span className={`num font-semibold ${f.points < 0 ? 'text-green' : 'text-ink'}`}>{f.points > 0 ? '+' : ''}{f.points}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-[13px] text-ink-3">Select a recommendation to see the detail and the evidence behind it.</p>
      </Panel>
    )
  }
  const cls = card.className ? ix.b.v2.classes.find(c => c.name === card.className) ?? null : null
  const rfs = (card.riskFactors ?? []).map(id => ix.b.v2.risk_factors.find(r => r.id === id)!).filter(Boolean)
  return (
    <Panel className="p-5">
      <span className={`rounded px-1.5 py-0.5 text-[10.5px] font-bold uppercase tracking-wide ${COL[card.colour].chip}`}>{COLOUR_LABEL[card.colour]}</span>
      <h3 className="mt-2 font-display text-[21px] font-bold leading-snug">{card.title}</h3>
      <p className="mt-1 text-[12.5px] text-ink-3">{card.who} · {card.when}</p>
      <ol className="mt-3 flex list-decimal flex-col gap-2 pl-5 text-[13.5px] leading-snug">
        {card.steps.map(s => <li key={s.text}>{s.text} <SourceChips sources={s.sources} pmids={s.pmids} ix={ix} /></li>)}
      </ol>
      <div className={`mt-3 rounded-md p-3 text-[13px] ${COL[card.colour].soft}`}><b>Tell the patient:</b> {card.tell}</div>

      <div className="mt-5 flex flex-col gap-4">
        <div>
          <div className="eyebrow">Evidence summary</div>
          <p className="mt-1.5 font-display text-[16px] leading-snug">{card.bottomLine}</p>
          <span className="mt-2 inline-block rounded bg-accent-soft px-2 py-0.5 text-[11px] font-semibold text-accent">{card.certainty}</span>
        </div>
        {rfs.length > 0 && <Section title="Heat-wave studies"><RiskFactorList items={rfs} /></Section>}
        {cls && <>
          <Section title="Studies in heat"><DirectList items={directFor(cls)} /></Section>
          <Section title="Indirect evidence" note="The drug and heat were each studied separately for the same effect.">
            <SharedPathway ix={ix} ourId={cls.our_id} />
          </Section>
          <Section title="Who was studied">
            <p className="text-[13px] text-ink-2">Most heat-and-medicine studies come from people 65 and older during heat waves. {cls.finding}</p>
          </Section>
          <Section title="What heat-health guidance says"><GuidanceTable ix={ix} c={cls} /></Section>
          <Section title="Drug label"><LabelNote c={cls} /></Section>
        </>}
      </div>
    </Panel>
  )
}

function Modal({ kind, plan, p, heat, close }: { kind: 'note' | 'plan'; plan: Plan; p: Patient; heat: number; close: () => void }) {
  const [copied, setCopied] = useState(false)
  const note = [
    `Heat risk assessment (HeatRx draft) — ${p.name}, ${p.age ?? ''}`,
    `Planning for: 1–4 July 2026 NWS Extreme Heat Warning. Heat level shown: ${HEAT_LEVELS[heat]}.`,
    `Overall heat risk: ${plan.band}. Drivers: ${plan.factors.filter(f => f.points > 0 || f.group === 'Medicines').map(f => f.label).join('; ')}.`,
    plan.factors.some(f => f.points < 0) ? `Protective: ${plan.factors.filter(f => f.points < 0).map(f => f.label).join('; ')}.` : '',
    `Medicines reviewed: ${plan.meds.map(m => m.name).join(', ') || 'none'}.`,
    '', 'Plan:',
    ...plan.cards.map((c, i) => `${i + 1}. [${COLOUR_LABEL[c.colour]}] ${c.title}. ${c.why}`),
    '', 'Patient counselled: do not stop medicines abruptly; signs of heat illness; when to call 911. Heat action plan given.',
    plan.unknowns.length ? `Still to ask: ${plan.unknowns.length} HEAT questionnaire items.` : '',
  ].filter(Boolean).join('\n')
  return (
    <motion.div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={close}>
      <motion.div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-panel p-6 shadow-2xl" initial={{ y: 12 }} animate={{ y: 0 }} onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h3 className="font-display text-[22px] font-bold">{kind === 'note' ? 'Note for the EHR' : `Heat action plan for ${p.name.split(' (')[0]}`}</h3>
          <button onClick={close} className="text-[13px] text-ink-3 hover:text-ink">Close</button>
        </div>
        {kind === 'note' ? (
          <>
            <pre className="mt-3 whitespace-pre-wrap rounded-md bg-soft p-3 font-sans text-[12.5px] leading-relaxed">{note}</pre>
            <button className="mt-3 rounded-md bg-ink px-3 py-1.5 text-[13px] font-semibold text-white"
              onClick={() => navigator.clipboard.writeText(note).then(() => setCopied(true)).catch(() => setCopied(false))}>{copied ? 'Copied' : 'Copy note'}</button>
          </>
        ) : (
          <div className="mt-3 flex flex-col gap-3 text-[14px] leading-relaxed">
            <p className="text-ink-3 text-[12px]">Follows CDC's five-step heat action plan for patients.</p>
            <PlanStep n={1} t="Your heat risk">Your heat risk is <b>{plan.band.toLowerCase()}</b> because of: {plan.factors.filter(f => f.points > 0).map(f => f.label.toLowerCase()).join(', ')}.</PlanStep>
            <PlanStep n={2} t="Stay cool">{plan.cards.find(c => c.id === 'cooling')?.tell ?? 'Use your air conditioning on hot days. Even a few hours somewhere cool helps.'} Cooling centres: call 311.</PlanStep>
            <PlanStep n={3} t="Stay hydrated">Drink water through the day, before you feel thirsty. Limit alcohol and very sugary or caffeinated drinks.</PlanStep>
            <PlanStep n={4} t="Your medicines on hot days">
              <ul className="list-disc pl-5">{plan.cards.filter(c => c.meds?.length).map(c => <li key={c.id}>{c.tell}</li>)}</ul>
              Don't stop any medicine on your own.
            </PlanStep>
            <PlanStep n={5} t="Who checks on you, and when to get help">{plan.cards.find(c => c.id === 'checkin')?.tell ?? 'Tell family or a friend to check on you on hot days.'} Call 911 for confusion, fainting, a very high temperature, or hot, dry skin.</PlanStep>
          </div>
        )}
      </motion.div>
    </motion.div>
  )
}

function PlanStep({ n, t, children }: { n: number; t: string; children: React.ReactNode }) {
  return <div><div className="font-display text-[16px] font-bold">{n}. {t}</div><div className="text-ink-2">{children}</div></div>
}
