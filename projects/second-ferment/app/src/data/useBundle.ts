import { useEffect, useState } from 'react'
import type { Bundle } from './types'
import { buildIndex, type Index } from './derive'

export function useBundle() {
  const [ix, setIx] = useState<Index | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    fetch('/data/evidence.json')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<Bundle>
      })
      .then(b => setIx(buildIndex(b)))
      .catch(e => setError(`Couldn't load the evidence bundle (${e.message}). Rebuild it with the scripts in scripts/.`))
  }, [])
  return { ix, error }
}
