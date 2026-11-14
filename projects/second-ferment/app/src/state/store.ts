// Shared state for the home views: both maps read and write the same selection, heat level, filters and role,
// so a drug selected in one view stays selected in the other.
import { create } from 'zustand'
import type { Bucket, Tier } from '../data/types'

export type Role = 'pharmacist' | 'prescriber' | 'public_health'
export type View = 'systems' | 'ribbons'
export type Arrange = 'system' | 'action' | 'prescriber'
export type Heat = 0 | 1 | 2

export const ROLE_DEFAULTS: Record<Role, { tiers: Tier[]; view: View; note: string }> = {
  pharmacist: { tiers: ['direct', 'shared'], view: 'systems', note: 'All drug classes, evidence-backed links.' },
  prescriber: { tiers: ['direct', 'shared'], view: 'systems', note: 'Filter by your specialty to see the classes you prescribe.' },
  public_health: { tiers: ['direct', 'shared', 'guidance_only'], view: 'ribbons', note: 'Guidance-only links shown, to compare guidance with evidence.' },
}

interface State {
  role: Role
  view: View
  arrange: Arrange
  heat: Heat
  selectedClass: string | null
  selectedHub: string | null
  selectedFinding: string | null
  tiers: Tier[]
  bucket: Bucket | null
  specialty: string | null
  topOnly: boolean
  tourStep: number
  replay: { scenario: string; day: number; playing: boolean } | null
  setRole: (r: Role) => void
  setView: (v: View) => void
  setArrange: (a: Arrange) => void
  setHeat: (h: Heat) => void
  selectClass: (id: string | null) => void
  selectHub: (id: string | null) => void
  selectFinding: (id: string | null) => void
  toggleTier: (t: Tier) => void
  setBucket: (b: Bucket | null) => void
  setSpecialty: (s: string | null) => void
  setTopOnly: (v: boolean) => void
  setTourStep: (n: number) => void
  setReplay: (r: State['replay']) => void
}

export const useStore = create<State>(set => ({
  role: 'pharmacist',
  view: 'systems',
  arrange: 'system',
  heat: 0,
  selectedClass: null,
  selectedHub: null,
  selectedFinding: null,
  tiers: ROLE_DEFAULTS.pharmacist.tiers,
  bucket: null,
  specialty: null,
  topOnly: false,
  tourStep: -1,
  replay: null,
  setRole: role => set({ role, tiers: ROLE_DEFAULTS[role].tiers, view: ROLE_DEFAULTS[role].view, specialty: null, bucket: null }),
  setView: view => set({ view, tourStep: -1 }),
  setArrange: arrange => set({ arrange, selectedHub: null, tourStep: -1 }),
  setHeat: heat => set({ heat }),
  selectClass: selectedClass => set({ selectedClass, selectedFinding: null, tourStep: -1 }),
  selectHub: selectedHub => set({ selectedHub, selectedFinding: null, tourStep: -1, arrange: 'system' }),
  selectFinding: selectedFinding => set({ selectedFinding }),
  toggleTier: t => set(s => ({ tiers: s.tiers.includes(t) ? s.tiers.filter(x => x !== t) : [...s.tiers, t] })),
  setBucket: bucket => set({ bucket }),
  setSpecialty: specialty => set({ specialty }),
  setTopOnly: topOnly => set({ topOnly }),
  setTourStep: tourStep => set({ tourStep }),
  setReplay: replay => set({ replay }),
}))
