// The headline number shown for each drug class in the atlas, and how strong its heat evidence is.
// Every value is from a study checked against its abstract or from the vetted graph, except where `vetted: false`.
// "strength" drives the circle size: bigger = stronger heat evidence (not "more dangerous").

export type Kind = 'risk' | 'group' | 'null' | 'mechanism' | 'guidance'
export interface Headline {
  cls: string // teammate's class name (bundle.v2.classes[].name)
  kind: Kind
  value?: string // e.g. "aOR 2.09"
  ci?: string
  plain: string // what it means, in plain words
  outcome: string
  pmid?: string
  vetted?: boolean
  strength: number // 0..5
  note?: string
}

export const HEADLINES: Headline[] = [
  { cls: 'Antipsychotics', kind: 'risk', value: 'aOR 2.09', ci: '1.89–2.35', plain: 'About 2× the odds of dying in a heat wave', outcome: 'Death, 2003 French heat wave, ages 70–100', pmid: '20104062', vetted: true, strength: 5 },
  { cls: 'Antidepressants', kind: 'risk', value: 'aOR 1.71', ci: '1.57–1.86', plain: 'About 70% higher odds of dying in a heat wave', outcome: 'Death, 2003 French heat wave, ages 70–100', pmid: '20104062', vetted: true, strength: 4.6 },
  { cls: 'Insulin', kind: 'risk', value: 'OR 1.38', ci: '1.28–1.48', plain: 'About 40% higher odds of a serious low on the hottest days', outcome: 'Serious hypoglycaemia, insulin users 65+, US and Taiwan', pmid: '38060348', vetted: true, strength: 4.6 },
  { cls: 'Anticholinergics', kind: 'risk', value: 'OR 6.0', ci: '1.8–19.6', plain: 'About 6× the odds of hospital admission for heat illness', outcome: 'Admission for heat illness, 2003 French heat wave', pmid: '17513091', vetted: false, strength: 3.2, note: 'Mixed: a second study found no clear effect on death (OR 1.21, p = 0.31).' },
  { cls: 'Diuretics', kind: 'group', value: 'HR 2.17', ci: '1.17–4.05', plain: 'About 2× the risk of dying once in hospital with heatstroke', outcome: 'Death in heatstroke patients, antihypertensives as a group', pmid: '17698677', vetted: true, strength: 3.6, note: 'Studied as "antihypertensives" as a group; kidney and sodium evidence on the drug side is strong.' },
  { cls: 'ACE inhibitors / ARBs', kind: 'group', value: 'HR 2.17', ci: '1.17–4.05', plain: 'About 2× the risk of dying once in hospital with heatstroke', outcome: 'Death in heatstroke patients, antihypertensives as a group', pmid: '17698677', vetted: true, strength: 3.4, note: 'Studied as a group; no study of this class alone in heat.' },
  { cls: 'Beta blockers', kind: 'group', value: 'HR 2.17', ci: '1.17–4.05', plain: 'About 2× the risk of dying once in hospital with heatstroke', outcome: 'Death in heatstroke patients, antihypertensives as a group', pmid: '17698677', vetted: true, strength: 2.6, note: 'Studied as a group; no study of this class alone in heat.' },
  { cls: 'Calcium channel blockers', kind: 'group', value: 'HR 2.17', ci: '1.17–4.05', plain: 'About 2× the risk of dying once in hospital with heatstroke', outcome: 'Death in heatstroke patients, antihypertensives as a group', pmid: '17698677', vetted: true, strength: 2.6, note: 'Studied as a group; no study of this class alone in heat.' },
  { cls: 'Benzodiazepines / sedatives', kind: 'risk', value: 'OR 2.4', ci: '1.3–4.4', plain: 'About 2.4× the odds of hospital admission for heat illness', outcome: 'Admission for heat illness, 2003 (anxiolytics)', pmid: '17513091', vetted: false, strength: 2.4, note: 'Conflicting: the larger 2003 study found lower odds of death (aOR 0.85).' },
  { cls: 'Opioids', kind: 'risk', value: 'OR 1.08', ci: '1.05–1.11', plain: 'About 8% more overdoses on very hot days', outcome: 'Overdose ED visits, California 2005–2019', pmid: '37897873', vetted: true, strength: 3, note: 'About drug use and overdose, not prescribed use.' },
  { cls: 'Stimulants', kind: 'risk', value: 'OR 1.15', ci: '1.09–1.22', plain: 'About 15% more amphetamine overdoses on very hot days', outcome: 'Overdose ED visits, California 2005–2019', pmid: '37897873', vetted: false, strength: 2, note: 'About drug use and overdose.' },
  { cls: 'Lithium', kind: 'null', plain: 'Studied in heat: no clear effect on blood levels', outcome: 'Lithium level vs temperature (p = 0.08; r = −0.008)', pmid: '25163443', vetted: true, strength: 1.6, note: 'Every guidance source warns about lithium; the two studies found no clear effect.' },
  { cls: 'NSAIDs', kind: 'null', plain: 'Studied in heat: no clear effect on kidney injury', outcome: 'Kidney injury in heat waves, with a diuretic and ACE inhibitor (OR 1.02)', pmid: '29116624', vetted: true, strength: 1.8, note: 'Strong kidney-injury evidence on the drug side (50 studies).' },
  { cls: 'SGLT2 inhibitors', kind: 'mechanism', plain: 'Not studied in heat; linked to fluid loss and ketoacidosis', outcome: 'No study in heat', strength: 1.6 },
  { cls: 'Metformin and sulfonylureas', kind: 'mechanism', plain: 'Not studied in heat; linked to low blood sugar', outcome: 'No study in heat', strength: 1.4 },
  { cls: 'GLP-1 agonists', kind: 'mechanism', plain: 'Not studied in heat; linked to fluid loss', outcome: 'No study in heat', strength: 0.8 },
  { cls: 'Topiramate / zonisamide', kind: 'mechanism', plain: 'Not studied in heat; linked to less sweating', outcome: 'No study in heat', strength: 0.8 },
  { cls: 'Parkinson / dopaminergic', kind: 'mechanism', plain: 'Not studied in heat', outcome: 'No study in heat', strength: 0.6 },
  { cls: 'Cholinesterase inhibitors', kind: 'guidance', plain: 'Not studied; named in guidance only', outcome: 'No study in heat', strength: 0.4 },
]

export const KIND_LABEL: Record<Kind, string> = {
  risk: 'Direct evidence', group: 'Direct evidence, drug group', null: 'Studied in heat, no clear effect', mechanism: 'Indirect evidence', guidance: 'No studies',
}
