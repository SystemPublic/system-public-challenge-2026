// Derived views of the bundle that both home views share.
import type { Bucket, Bundle, DrugClass, Link, Tier } from './types'

export const TIER_RANK: Record<Tier, number> = { direct: 4, shared: 3, guidance_only: 2, direct_misuse: 1, weak: 0 }
export const DRAWN: Tier[] = ['direct', 'shared', 'guidance_only']
export const BUCKET_ORDER: Bucket[] = ['hold_swap', 'adjust_dose', 'monitor', 'storage', 'counsel']
export const BUCKET_LABEL: Record<Bucket, string> = {
  hold_swap: 'Hold or swap', adjust_dose: 'Adjust dose', monitor: 'Monitor closely', storage: 'Storage', counsel: 'Counsel',
}

export interface Index {
  b: Bundle
  cls: Record<string, DrugClass>
  effect: Record<string, Bundle['effects'][number]>
  hubOf: Record<string, string | null>
  linksByClass: Record<string, Link[]>
  linksByEffect: Record<string, Link[]>
  heatStudiesByHub: Record<string, number>
  primaryHub: Record<string, string>
  searchIndex: { label: string; kind: 'class' | 'drug' | 'hub' | 'effect'; target: string; hint?: string }[]
}

export function buildIndex(b: Bundle): Index {
  const cls = Object.fromEntries(b.classes.map(c => [c.id, c]))
  const effect = Object.fromEntries(b.effects.map(e => [e.id, e]))
  const hubOf = Object.fromEntries(b.effects.map(e => [e.id, e.hub]))
  const linksByClass: Record<string, Link[]> = {}
  const linksByEffect: Record<string, Link[]> = {}
  for (const l of b.links) {
    ;(linksByClass[l.class] ??= []).push(l)
    ;(linksByEffect[l.effect] ??= []).push(l)
  }
  const heatStudiesByHub: Record<string, number> = {}
  for (const h of b.heat_arms) {
    const hub = hubOf[h.effect]
    if (hub) heatStudiesByHub[hub] = (heatStudiesByHub[hub] ?? 0) + h.studies
  }
  // A class sits next to the hub where its strongest drawn evidence is.
  const primaryHub: Record<string, string> = {}
  for (const c of b.classes) {
    const ls = (linksByClass[c.id] ?? []).filter(l => DRAWN.includes(l.tier) && hubOf[l.effect])
    ls.sort((a, z) => score(z) - score(a))
    primaryHub[c.id] = ls.length ? (hubOf[ls[0].effect] as string) : 'heat'
  }
  const searchIndex: Index['searchIndex'] = []
  for (const c of b.classes) {
    searchIndex.push({ label: c.label, kind: 'class', target: c.id })
    for (const m of c.members) searchIndex.push({ label: m, kind: 'drug', target: c.id, hint: c.label })
  }
  for (const h of b.hubs) searchIndex.push({ label: h.label, kind: 'hub', target: h.id })
  for (const e of b.effects) if (e.hub) searchIndex.push({ label: e.label, kind: 'effect', target: e.hub, hint: hubLabel(b, e.hub) })
  return { b, cls, effect, hubOf, linksByClass, linksByEffect, heatStudiesByHub, primaryHub, searchIndex }
}

export function score(l: Link): number {
  return TIER_RANK[l.tier] * 1000 + l.drug_arm.raised + (l.direct_ids.length ? 50 : 0)
}

export function hubLabel(b: Bundle, id: string) {
  return b.hubs.find(h => h.id === id)?.label ?? id
}

/** Evidence weight of a class: harmful-direction studies on drawn links, with direct findings counted heavily. */
export function classWeight(ix: Index, id: string) {
  const ls = (ix.linksByClass[id] ?? []).filter(l => l.tier === 'direct' || l.tier === 'shared')
  return ls.reduce((s, l) => s + l.drug_arm.raised + l.direct_ids.length * 15, 0)
}

/** Best link per class x hub (several effects can share a hub). */
export function hubLinks(ix: Index, classId: string) {
  const out: Record<string, Link> = {}
  for (const l of ix.linksByClass[classId] ?? []) {
    const hub = ix.hubOf[l.effect]
    if (!hub || !DRAWN.includes(l.tier)) continue
    if (!out[hub] || score(l) > score(out[hub])) out[hub] = l
  }
  return out
}

/** The action bucket a class is grouped under in "arrange by action": the most specific one it has. */
export function primaryBucket(c: DrugClass): Bucket | 'none' {
  const bs = c.buckets ?? []
  for (const b of BUCKET_ORDER) if (bs.includes(b)) return b
  return 'none'
}

export function topSpecialty(c: DrugClass) {
  return c.specialties?.[0]?.[0] ?? 'Unknown'
}

export const TIER_LABEL: Record<Tier, string> = {
  direct: 'Direct', shared: 'Shared pathway', guidance_only: 'Guidance only', direct_misuse: 'Drug use only', weak: 'Weak',
}
