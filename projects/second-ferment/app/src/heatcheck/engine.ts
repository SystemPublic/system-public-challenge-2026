// The heat check rules engine. Transparent rules, not a model: every point and every card says where it comes from.
// Principles (docs/PROPOSAL_v2.md): mitigation before modification; intensity = medicine signal x patient exposure;
// stop only as-needed or low-benefit drugs, or under sick-day rules; every card states its basis.
import type { Bundle, RiskFactor, V2Action, V2Class } from '../data/types'
import type { Patient } from './patients'

export type Colour = 'red' | 'amber' | 'green' | 'blue'
export const COLOUR_LABEL: Record<Colour, string> = {
  red: 'Do before the heat', amber: 'Adjust or monitor', green: 'Continue and counsel', blue: 'Storage and supplies',
}
export type Basis = 'graph' | 'guidance' | 'label' | 'rule'
export const BASIS_LABEL: Record<Basis, string> = {
  graph: 'Research evidence', guidance: 'Heat-health guidance', label: 'Drug label', rule: 'HeatRx rule',
}

export interface Factor {
  id: string; label: string; points: number; group: 'Medicines' | 'Conditions' | 'Situation' | 'Place' | 'Protective'
  evidence?: RiskFactor; basis: Basis; note?: string
}
export interface Card {
  id: string; colour: Colour; title: string; why: string; who: string; when: string
  steps: { text: string; sources: string[]; pmids: string[] }[]
  tell: string
  basis: Basis[]
  className?: string // v2 class name, for the evidence panel
  meds?: string[]
  riskFactors?: string[] // risk factor ids, for mitigation cards
  certainty: string
  bottomLine: string
  priority: number
}
export interface Plan {
  meds: { name: string; cls: V2Class | null }[]
  factors: Factor[]
  score: number
  band: 'Low' | 'Elevated' | 'High' | 'Very high'
  unknowns: string[]
  cards: Card[]
  hvi: { hvi: number; neighbourhood: string; borough: string } | null
  alerts: { text: string; pmid?: string }[]
}

const has = (p: Patient, c: string) => p.conditions.includes(c)
const yes = (v: string) => v === 'yes'
const no = (v: string) => v === 'no'

export function resolveMed(b: Bundle, name: string): V2Class | null {
  const n = name.trim().toLowerCase()
  if (!n) return null
  for (const c of b.v2.classes) if (c.names.some(x => x.toLowerCase() === n)) return c
  for (const c of b.v2.classes) if (c.names.some(x => x.toLowerCase().startsWith(n) || n.startsWith(x.toLowerCase().split(' ')[0]))) return c
  return null
}

export function allMedNames(b: Bundle) {
  const out: { name: string; cls: string }[] = []
  for (const c of b.v2.classes) for (const n of c.names) out.push({ name: n, cls: c.name })
  return out
}

function rf(b: Bundle, id: string) { return b.v2.risk_factors.find(r => r.id === id) }

function actionsFor(b: Bundle, cls: string, when: string[]): V2Action[] {
  return b.v2.actions.filter(a => a.class === cls && when.includes(a.when))
}

function strongestSignal(c: V2Class): 'direct_risk' | 'direct_null' | 'bridged' | 'gap' | 'none' {
  const cells = Object.values(c.cells)
  if (cells.some(x => x.tier === 'direct' && x.signal === 'risk' && x.vetted)) return 'direct_risk'
  if (cells.some(x => x.tier === 'direct' && x.signal === 'risk')) return 'direct_risk'
  if (cells.some(x => x.tier === 'direct')) return 'direct_null'
  if (cells.some(x => x.tier === 'bridged' && (x.strength ?? 0) >= 2)) return 'bridged'
  if (cells.some(x => x.tier === 'bridged' || x.tier === 'partial')) return 'bridged'
  if (cells.some(x => x.tier === 'gap')) return 'gap'
  return 'none'
}

export function certaintyOf(c: V2Class): string {
  const s = strongestSignal(c)
  return s === 'direct_risk' ? (c.research?.vetted ? 'Direct evidence' : 'Direct evidence (unvetted)')
    : s === 'direct_null' ? 'Studied in heat, no clear effect'
    : s === 'bridged' ? 'Indirect evidence'
    : s === 'gap' ? 'No studies' : 'Little evidence'
}

export function buildPlan(b: Bundle, p: Patient, heatLevel: number): Plan {
  const meds = p.meds.map(name => ({ name, cls: resolveMed(b, name) }))
  const byClass = new Map<string, { cls: V2Class; names: string[] }>()
  for (const m of meds) if (m.cls) {
    const e = byClass.get(m.cls.name) ?? { cls: m.cls, names: [] }
    e.names.push(m.name); byClass.set(m.cls.name, e)
  }
  const cn = (n: string) => byClass.has(n)
  const hvi = p.zip ? b.v2.hvi[p.zip] ?? null : null
  const factors: Factor[] = []
  const add = (f: Factor) => factors.push(f)
  const H = p.heat

  // ---- patient and situation (evidence-weighted points) ----
  if ((p.age ?? 0) >= 75) add({ id: 'age75', label: `Age ${p.age}`, points: 2, group: 'Conditions', basis: 'guidance', note: 'Most heat deaths and most heat-and-medicine studies are in older adults.' })
  else if ((p.age ?? 0) >= 65) add({ id: 'age65', label: `Age ${p.age}`, points: 1, group: 'Conditions', basis: 'guidance' })
  if (has(p, 'heart')) add({ id: 'heart', label: 'Heart disease', points: 2, group: 'Conditions', evidence: rf(b, 'rf_heart'), basis: 'graph' })
  if (has(p, 'dementia')) add({ id: 'dementia', label: 'Dementia', points: 2, group: 'Conditions', evidence: rf(b, 'rf_dementia'), basis: 'graph' })
  for (const [id, label] of [['ckd', 'Kidney disease'], ['diabetes', 'Diabetes'], ['smi', 'Serious mental illness'], ['substance', 'Substance use'], ['prior_heat', 'Prior heat illness'], ['pregnancy', 'Pregnancy']] as const)
    if (has(p, id)) add({ id, label, points: 1, group: 'Conditions', basis: 'guidance' })
  if (no(H.cooling)) add({ id: 'no_ac', label: 'No working air conditioning', points: 3, group: 'Situation', evidence: rf(b, 'rf_ac'), basis: 'graph', note: 'A working air conditioner cut the odds of heat death to 0.2.' })
  else if (no(H.controlTemp)) add({ id: 'no_control', label: "Can't control indoor temperature", points: 1, group: 'Situation', basis: 'guidance' })
  if (yes(H.livesAlone) && !yes(H.checkIn)) add({ id: 'alone', label: 'Lives alone, no one checking in', points: 3, group: 'Situation', evidence: rf(b, 'rf_alone'), basis: 'graph' })
  else if (yes(H.livesAlone)) add({ id: 'alone_ci', label: 'Lives alone (has a check-in)', points: 1, group: 'Situation', evidence: rf(b, 'rf_alone'), basis: 'graph' })
  else if (no(H.checkIn)) add({ id: 'no_checkin', label: 'No one to check in on hot days', points: 1, group: 'Situation', basis: 'guidance' })
  if (yes(H.mobility)) add({ id: 'mobility', label: 'Limited mobility, housebound', points: 2, group: 'Situation', evidence: rf(b, 'rf_home'), basis: 'graph' })
  if (yes(H.upperFloor)) add({ id: 'top', label: 'Top-floor home', points: 2, group: 'Situation', evidence: rf(b, 'rf_top'), basis: 'graph' })
  if (no(H.stableHousing)) add({ id: 'housing', label: 'Unstable housing', points: 3, group: 'Situation', basis: 'guidance' })
  if (yes(H.outdoorWork)) add({ id: 'work', label: 'Works outdoors', points: 2, group: 'Situation', basis: 'guidance', note: 'CDC HEAT questionnaire; NYC Health Alert #23.' })
  else if (yes(H.outdoors)) add({ id: 'outdoors', label: '2+ hours outdoors on hot days', points: 1, group: 'Situation', basis: 'guidance' })
  if (hvi && hvi.hvi >= 4) add({ id: 'hvi', label: `${hvi.neighbourhood}: heat vulnerability ${hvi.hvi}/5`, points: hvi.hvi === 5 ? 2 : 1, group: 'Place', evidence: rf(b, 'rf_green'), basis: 'graph', note: b.v2.hvi_source })
  if (yes(H.cooling)) add({ id: 'ac', label: 'Has working air conditioning', points: -2, group: 'Protective', evidence: rf(b, 'rf_ac'), basis: 'graph' })
  if (yes(H.checkIn)) add({ id: 'checkin', label: 'Someone checks in on hot days', points: -1, group: 'Protective', evidence: rf(b, 'rf_social'), basis: 'graph' })

  // ---- medicines ----
  const psych = ['Antipsychotics', 'Antidepressants', 'Lithium', 'Benzodiazepines / sedatives'].filter(cn)
  let medBudget = 4 // the medicine list alone can add at most 4 points; exposure decides the rest
  for (const { cls, names } of byClass.values()) {
    const s = strongestSignal(cls)
    const raw = s === 'direct_risk' ? 2 : s === 'bridged' ? 1 : 0
    const pts = Math.min(medBudget, raw)
    medBudget -= pts
    if (raw) add({ id: 'med_' + cls.name, label: `${names.join(', ')} (${cls.name.toLowerCase()})`, points: pts, group: 'Medicines', basis: 'graph', note: certaintyOf(cls) })
  }
  if (psych.length >= 2) add({ id: 'psych2', label: `${psych.length} psychotropic classes`, points: 1, group: 'Medicines', evidence: rf(b, 'rf_psych_count'), basis: 'graph' })

  const score = Math.max(0, factors.reduce((s, f) => s + f.points, 0))
  const band: Plan['band'] = score >= 12 ? 'Very high' : score >= 8 ? 'High' : score >= 4 ? 'Elevated' : 'Low'
  const high = band === 'High' || band === 'Very high'
  const unknowns = Object.entries(H).filter(([, v]) => v === 'ask').map(([k]) => k)
  const isOld = (p.age ?? 0) >= 65

  // ---- alerts (combinations) ----
  const alerts: Plan['alerts'] = []
  const triple = cn('Diuretics') && cn('ACE inhibitors / ARBs') && cn('NSAIDs')
  if (triple) alerts.push({ text: 'Diuretic + ACE inhibitor/ARB + NSAID ("triple whammy"): kidney-injury risk if dehydrated. The one heat-wave study found no added kidney injury in hospital (OR 1.02); guidance still advises against NSAIDs in heat.', pmid: '29116624' })
  if (psych.length >= 2) alerts.push({ text: `${psych.length} psychotropic classes: in the 2003 heat wave each additional psychotropic raised the odds of death by about 25%.`, pmid: '20104062' })

  // ---- cards ----
  const cards: Card[] = []
  const steps = (cls: string, when: string[], buckets?: string[]) =>
    actionsFor(b, cls, when).filter(a => !buckets || buckets.includes(a.bucket)).map(a => ({ text: a.text, sources: a.sources, pmids: a.pmids }))

  // mitigation first
  if (no(H.cooling) || no(H.controlTemp) || no(H.stableHousing)) {
    cards.push({
      id: 'cooling', colour: high ? 'red' : 'amber', priority: 1,
      title: 'Arrange cooling before the heat arrives',
      why: no(H.cooling) ? 'No working air conditioning at home, the strongest modifiable risk for heat death.' : "Can't keep the home cool.",
      who: 'Clinician or social worker', when: 'This visit',
      steps: [
        { text: 'Refer to NYC HEAP Cooling Assistance for a free air conditioner (medical documentation may be needed).', sources: ['nyc'], pmids: [] },
        { text: 'Give the nearest cooling centre: call 311 or maps.nyc.gov/oem/cc. Even a few hours in a cool place lowers risk.', sources: ['nyc', 'cdc'], pmids: [] },
        ...(yes(H.upperFloor) ? [{ text: 'Top-floor home: spend the hottest hours somewhere cooler (family, library, cooling centre).', sources: [], pmids: ['8649494'] }] : []),
        { text: 'Fans only while indoor temperature is below 90 °F; above that a fan can raise body temperature.', sources: ['cdc'], pmids: [] },
      ],
      tell: 'Air conditioning is the best protection. If home is hot, go somewhere cool for the hottest hours, even for a few hours.',
      basis: ['graph', 'guidance'], riskFactors: ['rf_ac', 'rf_ac_bed', 'rf_top'],
      certainty: 'Direct evidence', bottomLine: 'In two heat waves a working air conditioner was the strongest protection against heat death and admission (OR 0.2; bedroom AC aOR 0.12). No medicine change does as much.',
    })
  }
  if ((yes(H.livesAlone) && !yes(H.checkIn)) || yes(H.mobility)) {
    cards.push({
      id: 'checkin', colour: high ? 'red' : 'amber', priority: 2,
      title: 'Set up a daily check-in for the heat wave',
      why: [yes(H.livesAlone) && 'Lives alone', no(H.checkIn) && 'no one checks in', yes(H.mobility) && 'limited mobility'].filter(Boolean).join(', ') + '.',
      who: 'Clinician, care manager or family', when: 'Before the heat; daily during it',
      steps: [
        { text: 'Name a contact who will call or visit every day of the heat advisory; record it in the chart.', sources: ['cdc', 'nyc'], pmids: [] },
        { text: 'Enrol in the city heat-advisory calls or a community check-in programme.', sources: ['nyc'], pmids: ['34770101'] },
        { text: 'Arrange grocery and medicine delivery so the patient does not go out in peak heat.', sources: [], pmids: [] },
      ],
      tell: 'Someone will check on you every day while it is hot. Call them, or 911, if you feel dizzy, confused or very weak.',
      basis: ['graph', 'guidance'], riskFactors: ['rf_alone', 'rf_home', 'rf_bed', 'rf_isolation_prog'],
      certainty: 'Direct evidence', bottomLine: 'Living alone (OR 8.1) and not leaving home daily (OR 5.8) were the strongest risks for heat death in Chicago; a programme reducing isolation cut heat-wave deaths in people over 80 (IRR 0.76).',
    })
  }
  if (yes(H.outdoorWork) || yes(H.outdoors)) {
    cards.push({
      id: 'work', colour: 'amber', priority: 4,
      title: 'Plan outdoor work around the heat',
      why: yes(H.outdoorWork) ? 'Works outdoors on hot days.' : 'Spends hours outdoors on hot days.',
      who: 'Clinician; employer', when: 'Before the heat; each hot day',
      steps: [
        { text: 'Ask the employer about heat safety: water, rest breaks in shade or cool spaces, lighter work in peak hours.', sources: ['nyc'], pmids: [] },
        { text: 'Schedule heavy work for the coolest part of the day; wear light, loose clothing and a brimmed hat.', sources: ['cdc'], pmids: [] },
        { text: 'Know the signs of heat exhaustion and heat stroke, and stop work at the first ones.', sources: ['cdc'], pmids: [] },
      ],
      tell: 'Drink water regularly, rest in the shade or a cool place, and stop if you feel dizzy, sick or confused.',
      basis: ['guidance'], certainty: 'Guidance',
      bottomLine: 'Outdoor workers are named by CDC and NYC Health as a high-risk group; the medicine cards below say what changes with heat for their drugs.',
    })
  }

  // medicines
  for (const { cls, names } of byClass.values()) {
    const nm = names.join(', ')
    const cert = certaintyOf(cls)
    const base = { className: cls.name, meds: names, certainty: cert }
    switch (cls.name) {
      case 'NSAIDs': {
        const red = triple || has(p, 'ckd') || cn('Diuretics') || cn('ACE inhibitors / ARBs')
        cards.push({ ...base, id: 'nsaid', colour: red ? 'red' : 'amber', priority: red ? 3 : 6,
          title: `Pause ${nm} during the heat`,
          why: triple ? 'Combined with a diuretic and an ACE inhibitor/ARB.' : has(p, 'ckd') ? 'Kidney disease.' : 'Kidney injury risk when dehydrated.',
          who: 'Prescriber or pharmacist', when: 'Before the heat; resume after',
          steps: [...steps('NSAIDs', ['before', 'alert'], ['Substitute or hold']), { text: 'Discuss another option for pain while it is hot, and when to restart.', sources: [], pmids: [] }],
          tell: `Don't take ${nm} while it is very hot. Ask us what to use for pain instead.`,
          basis: ['graph', 'guidance', 'rule'],
          bottomLine: 'NSAIDs are among the drugs most often linked to kidney injury (50 studies), and heat raises kidney injury too; the only direct heat-wave studies were null. As-needed use is easy to pause, so the benefit of pausing outweighs the cost.',
        })
        break
      }
      case 'Insulin':
        cards.push({ ...base, id: 'insulin', colour: 'amber', priority: 5,
          title: 'Check glucose more often; lower insulin if lows occur',
          why: `On ${nm}; heat raises serious hypoglycaemia in older insulin users.`,
          who: 'Prescriber; patient', when: 'During the heat',
          steps: steps('Insulin', ['alert', 'before'], ['Dose adjustment', 'Closer monitoring']),
          tell: 'Check your sugar more often when it is hot, and carry fast sugar. Call us if you have lows.',
          basis: ['graph', 'guidance'],
          bottomLine: `In about 2 million insulin users over 65, serious hypoglycaemia rose on hot days (OR 1.38 on the hottest).${isOld ? '' : ' Most evidence is in older adults.'} Heat also speeds insulin absorption from the injection site.`,
        })
        cards.push({ ...base, id: 'insulin_store', colour: 'blue', priority: 9,
          title: 'Keep insulin cool; plan for power cuts',
          why: 'Insulin degrades in heat; labels say keep below 30 °C.',
          who: 'Pharmacist; patient', when: 'Before the heat',
          steps: [...steps('Insulin', ['before'], ['Storage and stability']), { text: 'Plan where to keep insulin cool if the power goes out.', sources: ['cdc'], pmids: [] }],
          tell: 'Keep insulin out of the sun and never in a hot car. Keep spare pens in the fridge.',
          basis: ['label', 'guidance'], certainty: 'Drug label',
          bottomLine: 'Insulin labels set a 30 °C storage limit; CDC asks clinicians to plan refrigerated medicines for outages.',
        })
        break
      case 'Diuretics':
      case 'ACE inhibitors / ARBs': {
        if (cards.some(c => c.id === 'bp')) { const c = cards.find(c => c.id === 'bp')!; c.meds = [...(c.meds ?? []), ...names]; c.title = `Review ${c.meds.join(' and ')} before the heat`; break }
        cards.push({ ...base, id: 'bp', colour: 'amber', priority: 6,
          title: `Review ${nm} before the heat`,
          why: 'Volume loss, low sodium, low blood pressure and kidney injury rise with heat.',
          who: 'Prescriber', when: 'Before the heat; check if it lasts',
          steps: [...steps(cls.name, ['before', 'alert'], ['Dose adjustment', 'Closer monitoring']), ...steps(cls.name, ['unwell'])].slice(0, 4),
          tell: 'Keep taking your water and blood-pressure pills unless we tell you. If you are vomiting or not drinking, call us; you may need to pause them for a day.',
          basis: ['graph', 'guidance'],
          bottomLine: 'Long-term antihypertensives were linked to death in heatstroke patients (HR 2.17); diuretics and ACE inhibitors/ARBs are among the drugs most linked to kidney injury and low sodium. Keep, review the dose, and use sick-day rules.',
        })
        break
      }
      case 'Antipsychotics':
      case 'Antidepressants':
      case 'Benzodiazepines / sedatives': {
        const supervise = high || (yes(H.livesAlone) && !yes(H.checkIn))
        cards.push({ ...base, id: 'psych_' + cls.name, colour: supervise ? 'amber' : 'green', priority: supervise ? 7 : 10,
          title: `Continue ${nm}; ${supervise ? 'add supervision in the heat' : 'counsel on heat'}`,
          why: cls.name === 'Antipsychotics' ? 'Antipsychotics doubled the odds of death in the 2003 heat wave.' : cls.name === 'Antidepressants' ? 'Antidepressants raised the odds of death in the 2003 heat wave.' : 'Sedatives dull thirst and awareness of heat.',
          who: 'Prescriber; family or care team', when: 'Before and during the heat',
          steps: [{ text: "Don't stop abruptly; the medicine treats a condition that heat also worsens.", sources: ['cdc', 'nyc'], pmids: [] }, ...steps(cls.name, ['alert', 'before'], ['Closer monitoring'])].slice(0, 3),
          tell: 'Keep taking your medicine. On hot days stay cool, drink water, and have someone check on you.',
          basis: ['graph', 'guidance'],
          bottomLine: cls.name === 'Antipsychotics' ? 'In the 2003 French heat wave, people over 70 on antipsychotics had about twice the odds of dying (aOR 2.09). The response is closer watching and cooling, not stopping.'
            : cls.name === 'Antidepressants' ? 'In the 2003 French heat wave, antidepressants were linked to death (aOR 1.71); SSRIs also cause low sodium. Keep, watch, and check sodium in older adults.'
            : 'The evidence conflicts (one study higher risk, one lower). Taper rather than stop; review long-term need.',
        })
        break
      }
      case 'Lithium':
        cards.push({ ...base, id: 'lithium', colour: 'amber', priority: 6,
          title: 'Keep lithium; plan a level if unwell or the heat lasts',
          why: 'Narrow therapeutic index; dehydration can raise levels.',
          who: 'Prescriber (psychiatry or primary care)', when: 'During prolonged heat or illness',
          steps: [...steps('Lithium', ['alert', 'unwell'], ['Closer monitoring', 'Substitute or hold', 'Dose adjustment']), { text: 'Hydrate with water rather than electrolyte drinks.', sources: ['canada'], pmids: [] }].slice(0, 4),
          tell: 'Keep taking lithium and drink water through the day. If you get shaky, confused or have diarrhoea, call us for a blood test.',
          basis: ['graph', 'guidance', 'label'],
          bottomLine: 'Every guidance source flags lithium, but the two heat studies found no clear effect on levels (p = 0.08; r = -0.008). Monitor on symptoms rather than changing the dose.',
        })
        break
      case 'Beta blockers':
      case 'Calcium channel blockers':
        cards.push({ ...base, id: 'cv_' + cls.name, colour: 'green', priority: 10,
          title: `Continue ${nm}; watch for dizziness and falls`,
          why: cls.name === 'Beta blockers' ? 'May blunt sweating and the heart-rate response to heat.' : 'Can add to low blood pressure in heat.',
          who: 'Prescriber', when: 'Before and during the heat',
          steps: [{ text: "Don't stop abruptly (rebound risk); reassess only if blood pressure runs low.", sources: ['cdc', 'nyc'], pmids: [] }, ...steps(cls.name, ['alert', 'before'], ['Closer monitoring', 'Dose adjustment'])].slice(0, 3),
          tell: 'Keep taking it. Stand up slowly on hot days and sit down if you feel dizzy.',
          basis: ['graph', 'guidance'],
          bottomLine: 'Evidence is class-wide: long-term antihypertensives were linked to death in heatstroke patients (HR 2.17), with no study of this class alone. Continue and monitor.',
        })
        break
      default: {
        const st = steps(cls.name, ['before', 'alert'])
        if (!st.length) break
        const s = strongestSignal(cls)
        cards.push({ ...base, id: 'cls_' + cls.name, colour: s === 'direct_risk' && high ? 'amber' : 'green', priority: 8,
          title: `${nm}: ${st[0].text.split('.')[0]}`, why: cls.finding?.split('.')[0] ?? '', who: 'Prescriber', when: 'Before and during the heat',
          steps: st.slice(0, 3), tell: "Keep taking your medicines as prescribed unless we change them.", basis: ['graph', 'guidance'],
          bottomLine: cls.finding ?? '',
        })
      }
    }
  }
  if (!byClass.size && p.meds.length === 0) { /* no medicines: plan is exposure only */ }
  if (heatLevel < 1) for (const c of cards) if (c.colour === 'red') c.colour = 'amber'
  cards.sort((a, z) => a.priority - z.priority)
  return { meds, factors, score, band, unknowns, cards, hvi, alerts }
}
