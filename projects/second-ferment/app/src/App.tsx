import { useEffect, useState } from 'react'
import { DrugAtlas } from './atlas/DrugAtlas'
import { useBundle } from './data/useBundle'
import { GraphView } from './graph/GraphView'
import { GlossaryPanel, useGlossary } from './components/Glossary'

type Route = 'atlas' | 'graph' | 'patient' | 'panel' | 'appendix'
const ROUTES: Route[] = ['atlas', 'graph', 'patient', 'panel', 'appendix']
// Stella's heat-med-story-guide page, embedded tab by tab (her own header hidden with ?embed)
const STELLA: Partial<Record<Route, string>> = { patient: 'map&lens=pt', panel: 'pop', appendix: 'ev' }
const read = (): Route => { const h = location.hash.slice(1) as Route; return ROUTES.includes(h) ? h : 'atlas' }

export default function App() {
  const { ix, error } = useBundle()
  const showGloss = useGlossary(g => g.show)
  const [route, setRoute] = useState<Route>(read)
  useEffect(() => { const f = () => setRoute(read()); addEventListener('hashchange', f); return () => removeEventListener('hashchange', f) }, [])
  if (error) return <div className="p-8 text-heat-ink">{error}</div>
  if (!ix) return <div className="grid h-full place-items-center text-ink-3">Loading the evidence…</div>
  const go = (r: Route) => { location.hash = r }
  const tab = (r: Route, n: string, t: string) => (
    <button onClick={() => go(r)} className={`flex items-baseline gap-1.5 border-b-2 px-1 py-3 text-[13.5px] font-semibold ${route === r ? 'border-heat text-ink' : 'border-transparent text-ink-3 hover:text-ink'}`}>
      <span className="text-[11px] text-ink-3">{n}</span>{t}
    </button>
  )
  return (
    <div className="flex h-full flex-col">
      <header className="no-print flex flex-wrap items-center gap-x-6 border-b border-line bg-panel px-5">
        <div className="py-3 text-[17px] font-extrabold tracking-tight">Heat<span className="text-heat">Rx</span></div>
        <nav aria-label="Sections" className="flex items-center gap-6">
          <div className="flex items-center gap-4"><span className="eyebrow">The evidence</span>{tab('atlas', '1', 'Evidence atlas')}{tab('graph', '2', 'The graph')}</div>
          <span className="h-6 w-px bg-line" />
          <div className="flex items-center gap-4"><span className="eyebrow">In the clinic</span>{tab('patient', '3', 'Patient plan')}{tab('panel', '4', 'Patient panel')}</div>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          {tab('appendix', '', 'Evidence appendix')}
        <button onClick={() => showGloss()} className="rounded-md border border-line px-3 py-1.5 text-[12.5px] font-semibold hover:bg-hov">Glossary</button>
        </div>
      </header>
      {route === 'atlas' && <DrugAtlas ix={ix} goHeatCheck={() => go('patient')} />}
      {route === 'graph' && <GraphView ix={ix} />}
      {STELLA[route] && <iframe key={route} title="Heat and medicines guide" src={`/stella/guide.html?embed#t=${STELLA[route]}`} className="min-h-0 w-full flex-1 border-0" />}
      <GlossaryPanel />
    </div>
  )
}
