// Shape of bundle/evidence.json (built by scripts/evidence.py, merge_papers.py, merge_outside.py).

export type Tier = 'direct' | 'shared' | 'guidance_only' | 'direct_misuse' | 'weak'
export type Bucket = 'hold_swap' | 'adjust_dose' | 'monitor' | 'storage' | 'counsel'
export type Dir = 'raised' | 'lowered' | 'unclear' | 'not_ratio'

export interface DrugClass {
  id: string
  label: string
  named_in_brief: boolean
  members: string[]
  links_shown: number
  raised_studies: number
  direct_findings: number
  guidance_docs?: string[]
  actions?: { bucket: Bucket; text: string; docs: string[]; basis: string; timing?: string; inferred?: boolean }[]
  buckets?: Bucket[]
  specialties?: [string, number][]
}

export interface Arm { studies: number; raised: number; lowered: number; unclear: number; not_ratio: number }

export interface Link {
  class: string
  effect: string
  tier: Tier
  direct_scope: string[]
  direct_ids: string[]
  drug_arm: Arm
  drug_arm_ids: string[]
  heat_arm_studies: number
  guidance_docs: string[]
  weak_evidence?: boolean
}

export interface Effect { id: string; label: string; hub: string | null }
export interface Hub { id: string; label: string }
export interface HeatArm extends Arm { effect: string; explicit_high: number; ids: string[] }

export interface Direct {
  id: string
  pmid: string
  classes: string[]
  scope: 'class' | 'group' | 'any'
  effect: string
  context: 'prescribed' | 'misuse' | 'storage'
  statistic: string
  value: string
  ci_lower: string
  ci_upper: string
  finding: string
  graph_label: string
  source: string
  checked: string
  note: string
  finding_ids: string[]
  levels: { measure: string; source: string; levels: { band: string; value: number; ci_lower: number; ci_upper: number }[] } | null
}

export interface Finding {
  id: string
  pmid: string
  study: string
  stat: string
  value: string
  lo: string | null
  hi: string | null
  p: string | null
  v1: string
  v2: string
  src: string
  dir: Dir
  doi: string
  pop: string
  correction?: { text: string; caveat: string }
}

export interface Paper { title: string; journal: string; year: string; authors: string }

export interface GuidanceDoc {
  id: string; title: string; publisher: string; country: string; year: string; url: string; audience: string
  read: string; evidence_statement: string; timing: string; note: string
}
export interface Mention { doc: string; class: string; effect: string; named_as: string; mechanism: string }
export interface GuidanceAction { doc: string; bucket: Bucket; scope: string; classes: string[]; text: string; timing: string; section: string }

export interface ScenarioDay {
  date: string; max_temp_f: number; min_temp_f: number; max_heat_index_f: number
  level: 'normal' | 'heat_advisory' | 'extreme_heat_warning'; level_rank: number; nws_product: string
}
export interface Scenario { id: string; title: string; place: string; note: string; days: ScenarioDay[] }

export interface Bundle {
  meta: { generated: string; source: string; rules: Record<string, unknown>; counts: Record<string, number> }
  classes: DrugClass[]
  hubs: Hub[]
  effects: Effect[]
  links: Link[]
  heat_arms: HeatArm[]
  direct: Direct[]
  findings: Record<string, Finding>
  papers: Record<string, Paper>
  guidance: {
    documents: GuidanceDoc[]; mentions: Mention[]; actions: GuidanceAction[]
    not_included: { title: string; reason: string }[]; buckets: Record<Bucket, string>
  }
  effect_actions: { effect: string; bucket: Bucket | ''; basis: string[]; note: string }[]
  specialties: { source: string; measure: string; sample: string }
  scenarios: { source: string; levels: { id: string; rank: number; label: string }[]; scenarios: Scenario[] }
  gaps: {
    rule: string
    classes: { class: string; evidence: string; guidance_docs: number; quadrant: string; effects_backed_not_in_guidance: string[]; effects_in_guidance_not_backed: string[] }[]
    missing_studies: { topic: string; detail: string }[]
  }
  v2: V2
}

// ---- v2: teammate's grid, guidance, timed actions; risk factors; NYC heat vulnerability (scripts/merge_v2.py) ----
export type V2Bucket = 'Dose adjustment' | 'Substitute or hold' | 'Closer monitoring' | 'Storage and stability'
export interface V2Direct {
  pmid: string; summary: string; vetted: boolean; type?: string; effect: 'risk' | 'null' | 'lower' | 'unclear' | string
  correction?: string
}
export interface V2Cell {
  tier: 'direct' | 'bridged' | 'partial' | 'gap' | 'none'; strength: number | null; vetted: boolean; signal: string | null
  action: string; note: string; direct: V2Direct[]
  mechanisms: { mechanism: string; primary: boolean; drug_studies: number; drug_unvetted: number; heat_studies: number; heat_unvetted: number }[]
}
export interface V2GuidanceEntry { level: 'action' | 'mention' | 'storage' | 'absent' | string; mech?: string; action?: string }
export interface V2Label {
  generic: string; status: string; snippet: string; brand?: string; dailymed?: string
  storage?: { max_c?: number; refrigerate?: boolean } | null
}
export interface V2Class {
  name: string; our_id: string | null; examples: string; specialties: string[]; names: string[]
  cells: Record<V2Bucket, V2Cell>; guidance: Record<string, V2GuidanceEntry>
  pattern: string | null; finding: string | null; label: { label?: V2Label[] } | null
  research: { tier: string; signal: string | null; strength: number | null; vetted: boolean; label: string; lead?: V2Direct | null; n_direct_studies?: number } | null
}
export interface V2Action {
  class: string; bucket: string; when: 'before' | 'alert' | 'unwell' | 'after' | string; text: string; who: string
  trigger?: string; sources: string[]; pmids: string[]; basis: string; note?: string
}
export interface RiskFactor {
  id: string; factor: string; direction: 'risk' | 'protective'; statistic: string; value: string; ci_lower: string; ci_upper: string
  outcome: string; population: string; pmid: string; checked: string; note: string
}
export interface V2 {
  source_note: string
  buckets: V2Bucket[]
  classes: V2Class[]
  general_direct: V2Direct[]
  guidance_sources: { id: string; name: string; short: string; url: string; date: string; status: string; note: string }[]
  patterns: { id: string; title: string; blurb: string }[]
  timing: Record<string, string>
  actions: V2Action[]
  actions_all_classes: V2Action[]
  risk_factors: RiskFactor[]
  hvi: Record<string, { hvi: number; neighbourhood: string; borough: string }>
  hvi_source: string
}
