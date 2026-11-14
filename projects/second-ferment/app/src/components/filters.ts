import { useMemo } from 'react'
import type { Index } from '../data/derive'
import { useStore } from '../state/store'

/** Classes that pass the specialty and action filters (shared by both home views). */
export function useVisibleClasses(ix: Index) {
  const specialty = useStore(s => s.specialty)
  const bucket = useStore(s => s.bucket)
  return useMemo(() => {
    const out = new Set<string>()
    for (const c of ix.b.classes) {
      if (specialty && !(c.specialties ?? []).some(([t, v]) => t === specialty && v >= 0.08)) continue
      if (bucket && !(c.buckets ?? []).includes(bucket)) continue
      out.add(c.id)
    }
    return out
  }, [ix, specialty, bucket])
}

/** Prescriber types that hold at least 8% of claims for some class, for the specialty filter. */
export function specialtyOptions(ix: Index) {
  const s = new Set<string>()
  for (const c of ix.b.classes) for (const [t, v] of c.specialties ?? []) if (v >= 0.08) s.add(t)
  return [...s].sort()
}
