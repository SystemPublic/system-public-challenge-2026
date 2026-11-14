// Patient model for the heat check and three synthetic demo patients (not real people).
export type YN = 'yes' | 'no' | 'ask'

export interface Patient {
  name: string
  age: number | null
  sex: 'female' | 'male' | 'other' | ''
  conditions: string[]
  meds: string[] // generic names as entered
  zip: string
  // CDC HEAT questionnaire (Housing, Emergency preparedness, Awareness, Temperature/outdoors)
  heat: {
    stableHousing: YN; cooling: YN; controlTemp: YN; upperFloor: YN
    checkIn: YN; mobility: YN; outagePlan: YN
    usesHeatRisk: YN; knowsMeds: YN
    outdoors: YN; outdoorWork: YN
    livesAlone: YN
  }
}

export const CONDITIONS = [
  { id: 'heart', label: 'Heart failure or heart disease' },
  { id: 'ckd', label: 'Kidney disease' },
  { id: 'diabetes', label: 'Diabetes' },
  { id: 'dementia', label: 'Dementia or cognitive impairment' },
  { id: 'smi', label: 'Serious mental illness' },
  { id: 'substance', label: 'Substance use' },
  { id: 'prior_heat', label: 'Prior heat illness' },
  { id: 'pregnancy', label: 'Pregnancy' },
]

export const HEAT_QUESTIONS: { section: string; items: { key: keyof Patient['heat']; q: string; risky: YN }[] }[] = [
  { section: 'Housing and indoor environment', items: [
    { key: 'stableHousing', q: 'Has stable housing?', risky: 'no' },
    { key: 'cooling', q: 'Has working air conditioning at home?', risky: 'no' },
    { key: 'controlTemp', q: 'Can check and control the indoor temperature?', risky: 'no' },
    { key: 'upperFloor', q: 'Lives in heat-prone housing (upper or top floor)?', risky: 'yes' },
  ] },
  { section: 'Emergency preparedness', items: [
    { key: 'livesAlone', q: 'Lives alone?', risky: 'yes' },
    { key: 'checkIn', q: 'Has someone to check on them on hot days?', risky: 'no' },
    { key: 'mobility', q: 'Does mobility limit getting to a cool place?', risky: 'yes' },
    { key: 'outagePlan', q: 'Has a power-outage plan for refrigerated medicines or devices?', risky: 'no' },
  ] },
  { section: 'Awareness of health risks', items: [
    { key: 'usesHeatRisk', q: 'Uses the forecast or HeatRisk to decide what to do?', risky: 'no' },
    { key: 'knowsMeds', q: 'Knows their medicines can cause problems in heat?', risky: 'no' },
  ] },
  { section: 'Temperature and outdoor environment', items: [
    { key: 'outdoors', q: 'Spends 2+ hours outdoors on hot days?', risky: 'yes' },
    { key: 'outdoorWork', q: 'Works outdoors or in a hot workplace?', risky: 'yes' },
  ] },
]

const ask = (): Patient['heat'] => ({
  stableHousing: 'ask', cooling: 'ask', controlTemp: 'ask', upperFloor: 'ask', checkIn: 'ask', mobility: 'ask',
  outagePlan: 'ask', usesHeatRisk: 'ask', knowsMeds: 'ask', outdoors: 'ask', outdoorWork: 'ask', livesAlone: 'ask',
})

export const blankPatient = (): Patient => ({ name: '', age: null, sex: '', conditions: [], meds: [], zip: '', heat: ask() })

export const DEMO_PATIENTS: { id: string; blurb: string; patient: Patient }[] = [
  {
    id: 'rosa', blurb: '78, Bronx, no AC, lives alone',
    patient: {
      name: 'Rosa R. (synthetic)', age: 78, sex: 'female', conditions: ['heart', 'ckd', 'diabetes'],
      meds: ['insulin glargine', 'furosemide', 'lisinopril', 'sertraline', 'ibuprofen'], zip: '10454',
      heat: { stableHousing: 'yes', cooling: 'no', controlTemp: 'no', upperFloor: 'yes', livesAlone: 'yes', checkIn: 'no',
        mobility: 'yes', outagePlan: 'no', usesHeatRisk: 'no', knowsMeds: 'no', outdoors: 'no', outdoorWork: 'no' },
    },
  },
  {
    id: 'marcus', blurb: '34, Queens, works outdoors',
    patient: {
      name: 'Marcus T. (synthetic)', age: 34, sex: 'male', conditions: ['smi'],
      meds: ['lithium carbonate', 'quetiapine', 'ibuprofen'], zip: '11368',
      heat: { stableHousing: 'yes', cooling: 'yes', controlTemp: 'yes', upperFloor: 'no', livesAlone: 'no', checkIn: 'yes',
        mobility: 'no', outagePlan: 'ask', usesHeatRisk: 'no', knowsMeds: 'no', outdoors: 'yes', outdoorWork: 'yes' },
    },
  },
  {
    id: 'helen', blurb: '71, Upper West Side, has AC',
    patient: {
      name: 'Helen K. (synthetic)', age: 71, sex: 'female', conditions: ['heart'],
      meds: ['furosemide', 'metoprolol', 'lisinopril'], zip: '10025',
      heat: { stableHousing: 'yes', cooling: 'yes', controlTemp: 'yes', upperFloor: 'no', livesAlone: 'no', checkIn: 'yes',
        mobility: 'no', outagePlan: 'yes', usesHeatRisk: 'yes', knowsMeds: 'yes', outdoors: 'no', outdoorWork: 'no' },
    },
  },
]
