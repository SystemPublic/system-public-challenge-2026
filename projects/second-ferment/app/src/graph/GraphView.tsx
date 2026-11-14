// "The graph": the evidence network behind the atlas. Nodes are drug classes, body effects and heat; edges are
// the evidence from the System Public Graph (drug → effect, heat → effect, and studies of a drug during heat).
// Focusing a drug and an effect opens the edge into the papers behind it; each paper opens to its graph rows.
import { motion } from 'motion/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Abstract } from '../components/evidence'
import { Term } from '../components/Glossary'
import type { Index } from '../data/derive'
import type { Finding, Link } from '../data/types'
import { useGraphFocus } from './focus'

const W = 1200, H = 900, CX = 600, CY = 450
// Fixed triangle for a focused path: drug top left, effect top right, heat at the bottom, direct studies in the middle.
const TD: [number, number] = [190, 150], TE: [number, number] = [810, 150], TH: [number, number] = [500, 540], TC: [number, number] = [500, 285]
const SKIP_EFFECTS = new Set(['storage', 'overdose'])
const TIER_COL: Record<string, string> = { direct: 'var(--color-heat)', shared: 'var(--color-s2)', guidance_only: 'var(--color-faint)' }

interface PaperNode { id: string; pmid: string; side: 'drug' | 'heat' | 'direct'; x: number; y: number; findings: Finding[]; directText?: string }

export function GraphView({ ix }: { ix: Index }) {
  const focus = useGraphFocus()
  const [paper, setPaper] = useState<PaperNode | null>(null)
  const [hover, setHover] = useState<string | null>(null)
  const effects = useMemo(() => ix.b.effects.filter(e => !SKIP_EFFECTS.has(e.id)), [ix])
  const classes = ix.b.classes

  // ---- layout: heat in the centre, effects on an inner ring, drug classes on an outer ring near their effects ----
  const pos = useMemo(() => {
    const p: Record<string, [number, number]> = { heat: [CX, CY] }
    const angE: Record<string, number> = {}
    effects.forEach((e, i) => {
      const a = -Math.PI / 2 + (i * 2 * Math.PI) / effects.length
      angE[e.id] = a; p['e:' + e.id] = [CX + Math.cos(a) * 250, CY + Math.sin(a) * 215]
    })
    const want = classes.map(c => {
      const ls = (ix.linksByClass[c.id] ?? []).filter(l => (l.tier === 'direct' || l.tier === 'shared') && angE[l.effect] !== undefined)
      let sx = 0, sy = 0
      for (const l of ls) { const w = 1 + l.drug_arm.raised + l.direct_ids.length * 10; sx += Math.cos(angE[l.effect]) * w; sy += Math.sin(angE[l.effect]) * w }
      return { id: c.id, a: ls.length ? Math.atan2(sy, sx) : 0 }
    }).sort((a, z) => a.a - z.a)
    const gap = (2 * Math.PI) / classes.length
    want.forEach((w, i) => { const a = want[0].a + i * gap; p['d:' + w.id] = [CX + Math.cos(a) * 410, CY + Math.sin(a) * 380] })
    return p
  }, [effects, classes, ix])

  const drugEdges = useMemo(() => ix.b.links.filter(l => (l.tier === 'direct' || l.tier === 'shared') && pos['e:' + l.effect]), [ix, pos])
  const heatEdges = useMemo(() => ix.b.heat_arms.filter(h => pos['e:' + h.effect]), [ix, pos])

  // ---- focus: papers behind the selected drug → effect ← heat path ----
  const fl: Link | undefined = focus.cls && focus.effect ? (ix.linksByClass[focus.cls] ?? []).find(l => l.effect === focus.effect) : undefined
  const papers = useMemo<PaperNode[]>(() => {
    if (!fl) return []
    const out: PaperNode[] = []
    const group = (ids: string[], side: 'drug' | 'heat', a: [number, number], b: [number, number], limit: number) => {
      const by = new Map<string, Finding[]>()
      for (const id of ids) { const f = ix.b.findings[id]; if (!f || (side === 'drug' && f.dir !== 'raised')) continue; const k = f.pmid || f.study; by.set(k, [...(by.get(k) ?? []), f]) }
      const list = [...by.entries()].slice(0, limit)
      const dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy) || 1, px = -dy / len, py = dx / len
      const perRow = 12
      list.forEach(([k, fs], i) => {
        const row = Math.floor(i / perRow), col = i % perRow, n = Math.min(perRow, list.length - row * perRow)
        const t = 0.5 + (col - (n - 1) / 2) * (0.6 / perRow), off = (row % 2 ? 1 : -1) * Math.ceil((row + 1) / 2) * 17
        out.push({ id: side + k, pmid: fs[0].pmid, side, findings: fs, x: a[0] + dx * t + px * off, y: a[1] + dy * t + py * off })
      })
    }
    group(fl.drug_arm_ids, 'drug', TD, TE, 36)
    group(ix.b.heat_arms.find(h => h.effect === fl.effect)?.ids ?? [], 'heat', TH, TE, 24)
    const ds = ix.b.direct.filter(d => fl.direct_ids.includes(d.id))
    ds.forEach((d, i) => {
      out.push({ id: 'direct' + d.id, pmid: d.pmid, side: 'direct', findings: d.finding_ids.map(id => ix.b.findings[id]).filter(Boolean), directText: `${d.finding} ${d.statistic.replace(/_/g, ' ')} ${d.value}${d.ci_lower ? ` (${d.ci_lower}–${d.ci_upper})` : ''}`,
        x: TD[0] + (TH[0] - TD[0]) * (0.5 + (i - (ds.length - 1) / 2) * 0.1), y: TD[1] + (TH[1] - TD[1]) * (0.5 + (i - (ds.length - 1) / 2) * 0.1) })
    })
    return out
  }, [fl, ix])

  // ---- view box: whole graph, or zoomed to the focused path ----
  const target = useMemo(() => [0, 0, W, H], [])
  const [vb, setVb] = useState(target)
  const tkey = target.join(',')
  useEffect(() => { setVb(tkey.split(',').map(Number)) }, [tkey])
  const drag = useRef<{ x: number; y: number; vb: number[] } | null>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const onWheel = (e: React.WheelEvent) => {
    const k = e.deltaY > 0 ? 1.12 : 1 / 1.12
    const r = svgRef.current!.getBoundingClientRect()
    const mx = vb[0] + ((e.clientX - r.left) / r.width) * vb[2], my = vb[1] + ((e.clientY - r.top) / r.height) * vb[3]
    setVb([mx - (mx - vb[0]) * k, my - (my - vb[1]) * k, vb[2] * k, vb[3] * k])
  }

  const dim = (key: string) => hover ? !(key.includes(hover)) : false
  const clsLabel = (id: string) => ix.cls[id]?.label ?? id
  const findingsTotal = drugEdges.reduce((s, l) => s + l.drug_arm_ids.length, 0) + heatEdges.reduce((s, h) => s + h.ids.length, 0)

  return (
    <main className="grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 xl:grid-cols-[minmax(0,1fr)_420px]">
      <section className="relative min-h-[600px] overflow-hidden rounded-lg border border-line bg-hero">
        <div className="absolute top-4 left-5 z-10 max-w-[560px]">
          <div className="eyebrow">The graph behind the atlas</div>
          <h1 className="font-display text-[22px] font-bold leading-tight">{fl ? `${clsLabel(fl.class)} → ${ix.effect[fl.effect]?.label} ← heat` : 'Medicines, body effects and heat'}</h1>
          <p className="mt-1 text-[12.5px] text-ink-2">{fl ? 'Three kinds of study can connect a medicine to heat. Each dot is one paper in the System Public Graph; select it to see its findings.'
            : `Built from ${findingsTotal.toLocaleString()} findings in the System Public Graph. Lines show evidence between a medicine, an effect in the body and heat; thicker means more studies. Select a medicine and an effect, or open one from the atlas.`}</p>
        </div>
        <div className="absolute top-4 right-4 z-10 flex gap-2">
          {fl && <button onClick={() => { focus.set(null, null); setPaper(null) }} className="rounded-md border border-line bg-panel px-3 py-1.5 text-[12.5px] font-semibold hover:bg-hov">Show the whole graph</button>}
          {!fl && <button onClick={() => setVb(target)} className="rounded-md border border-line bg-panel px-3 py-1.5 text-[12.5px] hover:bg-hov">Reset view</button>}
        </div>
        {fl ? <FocusTriangle ix={ix} l={fl} papers={papers} paper={paper} pick={setPaper} /> : <>
        <div className="absolute bottom-3 left-5 z-10 flex flex-wrap gap-4 text-[11.5px] text-ink-2">
          <span><i className="mr-1 inline-block h-1 w-5 rounded bg-heat align-middle" />Direct evidence</span>
          <span><i className="mr-1 inline-block h-1 w-5 rounded bg-s2 align-middle" />Drug and effect (indirect)</span>
          <span><i className="mr-1 inline-block h-1 w-5 rounded align-middle" style={{ background: 'var(--color-heat-soft)', outline: '1px solid var(--color-heat)' }} />Heat and effect</span>
          <span>Scroll to zoom, drag to move</span>
        </div>
        <motion.svg ref={svgRef} className="h-full w-full cursor-grab active:cursor-grabbing" viewBox={vb.join(' ')} animate={{ viewBox: vb.join(' ') }}
          transition={{ duration: drag.current ? 0 : 0.6, ease: [0.22, 1, 0.36, 1] }} onWheel={onWheel}
          onPointerDown={e => { drag.current = { x: e.clientX, y: e.clientY, vb } }}
          onPointerMove={e => { if (!drag.current) return; const r = svgRef.current!.getBoundingClientRect(); const s = drag.current.vb[2] / r.width
            setVb([drag.current.vb[0] - (e.clientX - drag.current.x) * s, drag.current.vb[1] - (e.clientY - drag.current.y) * s, drag.current.vb[2], drag.current.vb[3]]) }}
          onPointerUp={() => { drag.current = null }} onPointerLeave={() => { drag.current = null }} role="img" aria-label="Evidence graph">
          {/* heat → effect */}
          {heatEdges.map(h => { const [x, y] = pos['e:' + h.effect]; const k = 'heat|e:' + h.effect; const off = dim('e:' + h.effect) && dim('heat')
            return <line key={k} x1={CX} y1={CY} x2={x} y2={y} stroke="var(--color-heat)" strokeOpacity={off ? 0.06 : 0.35} strokeWidth={Math.min(10, 1 + Math.sqrt(h.studies) * 1.3)} /> })}
          {/* drug → effect */}
          {drugEdges.map(l => { const [x1, y1] = pos['d:' + l.class], [x2, y2] = pos['e:' + l.effect]; const off = hover ? !(hover === 'd:' + l.class || hover === 'e:' + l.effect) : false
            return <line key={l.class + l.effect} x1={x1} y1={y1} x2={x2} y2={y2} stroke={TIER_COL[l.tier]} strokeOpacity={off ? 0.05 : 0.4}
              strokeWidth={Math.min(9, 1 + Math.sqrt(l.drug_arm.raised + l.direct_ids.length * 8))} className="cursor-pointer"
              onClick={() => { focus.set(l.class, l.effect); setPaper(null) }}><title>{clsLabel(l.class)} → {ix.effect[l.effect]?.label}: {l.drug_arm.raised} of {l.drug_arm.studies} studies raised risk</title></line> })}
          {/* effect nodes */}
          {effects.map(e => { const [x, y] = pos['e:' + e.id]; const k = 'e:' + e.id
            return <g key={k} opacity={dim(k) ? 0.25 : 1} onMouseEnter={() => setHover(k)} onMouseLeave={() => setHover(null)}>
              <rect x={x - 62} y={y - 15} width={124} height={30} rx={15} fill="var(--color-panel)" stroke="var(--color-ink-3)" />
              <text x={x} y={y + 4} textAnchor="middle" fontSize={11.5} fontWeight={600} fill="var(--color-ink)">{e.label.length > 20 ? e.label.split(' and ')[0] : e.label}</text>
            </g> })}
          {/* heat node */}
          <g opacity={dim('heat') ? 0.3 : 1}><circle cx={CX} cy={CY} r={36} fill="var(--color-heat)" /><text x={CX} y={CY + 5} textAnchor="middle" fontSize={15} fontWeight={700} fill="#fff">Heat</text></g>
          {/* drug nodes */}
          {classes.map(c => { const [x, y] = pos['d:' + c.id]; const k = 'd:' + c.id
            return <g key={k} opacity={dim(k) ? 0.25 : 1} onMouseEnter={() => setHover(k)} onMouseLeave={() => setHover(null)}>
              <circle cx={x} cy={y} r={7} fill="var(--color-ink)" />
              <text x={x} y={y - 12} textAnchor="middle" fontSize={12} fontWeight={700} fill="var(--color-ink)">{c.label}</text>
            </g> })}
        </motion.svg></>}
      </section>
      <aside className="min-h-0 overflow-y-auto rounded-lg border border-line bg-panel p-5">
        {paper ? <PaperPanel ix={ix} p={paper} back={() => setPaper(null)} /> : fl ? <PathPanel ix={ix} l={fl} papers={papers} pick={setPaper} /> : <GraphIntro ix={ix} pick={(c, e) => focus.set(c, e)} />}
      </aside>
    </main>
  )
}

/** A focused path drawn as a triangle: medicine, body effect and heat, with each side's papers as dots on it. */
function FocusTriangle({ ix, l, papers, paper, pick }: { ix: Index; l: Link; papers: PaperNode[]; paper: PaperNode | null; pick: (p: PaperNode) => void }) {
  const drugName = ix.cls[l.class].label, effName = ix.effect[l.effect]?.label ?? l.effect
  const n = (s: PaperNode['side']) => papers.filter(p => p.side === s).length
  const uniq = (ids: string[], raisedOnly: boolean) => new Set(ids.map(id => ix.b.findings[id]).filter(f => f && (!raisedOnly || f.dir === 'raised')).map(f => f.pmid || f.study)).size
  const nd = uniq(l.drug_arm_ids, true), nh = uniq(ix.b.heat_arms.find(h => h.effect === l.effect)?.ids ?? [], false), nx = n('direct')
  const shown = (k: number, side: PaperNode['side']) => n(side) < k ? ` (${n(side)} shown)` : ''
  const plural = (k: number) => `${k} paper${k === 1 ? '' : 's'}`
  // label placed beside the middle of a side, pushed outward from the triangle's centre
  const Side = ({ a, b, on, color, title, sub, push }: { a: number[]; b: number[]; on: boolean; color: string; title: string; sub: string; push: number }) => {
    const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, dx = mx - TC[0], dy = my - TC[1], k = Math.hypot(dx, dy) || 1
    const lx = mx + (dx / k) * push, ly = my + (dy / k) * push
    const anchor = Math.abs(dx / k) < 0.3 ? 'middle' : dx > 0 ? 'start' : 'end'
    return <g>
      <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={on ? color : 'var(--color-faint)'} strokeWidth={on ? 3 : 2} strokeDasharray={on ? undefined : '6 6'} strokeOpacity={on ? 0.55 : 1} />
      <text x={lx} y={ly} textAnchor={anchor} fontSize={14} fontWeight={700} fill={on ? 'var(--color-ink)' : 'var(--color-ink-3)'}>{title}</text>
      <text x={lx} y={ly + 18} textAnchor={anchor} fontSize={12.5} fill="var(--color-ink-2)">{sub}</text>
    </g>
  }
  const Node = ({ at, label, kind }: { at: number[]; label: string; kind: 'drug' | 'effect' | 'heat' }) => kind === 'heat'
    ? <g><circle cx={at[0]} cy={at[1]} r={34} fill="var(--color-heat)" /><text x={at[0]} y={at[1] + 5} textAnchor="middle" fontSize={15} fontWeight={700} fill="#fff">Heat</text></g>
    : <g><rect x={at[0] - 95} y={at[1] - 20} width={190} height={40} rx={20} fill={kind === 'drug' ? 'var(--color-ink)' : 'var(--color-panel)'} stroke="var(--color-ink)" strokeWidth={1.5} />
      <text x={at[0]} y={at[1] + 5} textAnchor="middle" fontSize={14} fontWeight={700} fill={kind === 'drug' ? 'var(--color-panel)' : 'var(--color-ink)'}>{label.length > 24 ? label.split(' and ')[0] : label}</text>
      <text x={at[0]} y={at[1] - 28} textAnchor="middle" fontSize={11} fontWeight={600} letterSpacing={1} fill="var(--color-ink-3)">{kind === 'drug' ? 'MEDICINE' : 'EFFECT IN THE BODY'}</text></g>
  return (
    <svg className="h-full w-full pt-24" viewBox="0 20 1000 600" role="img" aria-label={`${drugName}, ${effName} and heat`}>
      <Side a={TD} b={TE} on={nd > 0} color="var(--color-s2)" push={88}
        title={nd > 0 ? 'Medicine linked to this effect' : l.drug_arm.studies > 0 ? 'Medicine studied for this effect' : 'No study links the medicine to this effect'}
        sub={nd > 0 ? `${plural(nd)} showing raised risk, in any weather${shown(nd, 'drug')}` : l.drug_arm.studies > 0 ? `${l.drug_arm.studies} studies, none showing raised risk` : 'outside heat, in the graph'} />
      <Side a={TH} b={TE} on={nh > 0} color="var(--color-heat)" push={64}
        title={nh > 0 ? 'Heat linked to this effect' : 'No study links heat to this effect'} sub={nh > 0 ? `${plural(nh)}, any population${shown(nh, 'heat')}` : 'in the graph'} />
      <Side a={TD} b={TH} on={nx > 0} color="var(--color-heat)" push={70}
        title={nx > 0 ? 'Studied together' : 'Never studied together'}
        sub={nx > 0 ? `${plural(nx)}: people on it, during heat, ${effName.toLowerCase()} measured` : 'no study in heat measured this effect'} />
      {nx === 0 && <g>
        <text x={TC[0] - 20} y={TC[1] + 10} textAnchor="middle" fontSize={12.5} fill="var(--color-ink-3)">The two solid sides are separate studies</text>
        <text x={TC[0] - 20} y={TC[1] + 27} textAnchor="middle" fontSize={12.5} fill="var(--color-ink-3)">of different people: a possible pathway,</text>
        <text x={TC[0] - 20} y={TC[1] + 44} textAnchor="middle" fontSize={12.5} fill="var(--color-ink-3)">not a measured interaction.</text>
      </g>}
      {papers.map(p => (
        <g key={p.id} className="cursor-pointer" onClick={() => pick(p)}>
          <motion.circle cx={p.x} cy={p.y} initial={{ r: 0 }} animate={{ r: paper?.id === p.id ? 10 : p.side === 'direct' ? 9 : 6 }}
            fill={p.side === 'direct' ? 'var(--color-heat)' : p.side === 'drug' ? 'var(--color-s2)' : 'var(--color-panel)'}
            stroke={p.side === 'heat' ? 'var(--color-heat)' : 'var(--color-panel)'} strokeWidth={2} />
          <title>{ix.b.papers[p.pmid] ? `${ix.b.papers[p.pmid].authors} ${ix.b.papers[p.pmid].year}: ${ix.b.papers[p.pmid].title}` : `PMID ${p.pmid}`}</title>
        </g>
      ))}
      <Node at={TD} label={drugName} kind="drug" />
      <Node at={TE} label={effName} kind="effect" />
      <Node at={TH} label="Heat" kind="heat" />
    </svg>
  )
}

function GraphIntro({ ix, pick }: { ix: Index; pick: (c: string, e: string) => void }) {
  const top = ix.b.links.filter(l => l.tier === 'direct' || l.tier === 'shared').sort((a, z) => z.drug_arm.raised + z.direct_ids.length * 20 - (a.drug_arm.raised + a.direct_ids.length * 20)).slice(0, 8)
  return (
    <div className="flex flex-col gap-4 text-[13px] leading-relaxed">
      <div><div className="eyebrow">How to read it</div>
        <p className="mt-1">The System Public Graph stores findings from papers: each finding links two things a study measured, such as "use of furosemide" and "acute kidney injury". We grouped those findings into medicines, body effects and heat.</p>
        <ul className="mt-2 list-disc pl-5 text-ink-2">
          <li><b>Heat → effect</b>: studies linking hot weather to an effect.</li>
          <li><b>Medicine → effect</b>: studies linking the medicine to the same effect (<Term id="shared">indirect evidence</Term>).</li>
          <li><b>Medicine ↔ heat</b>: studies of people on the medicine during heat (<Term id="measured">direct evidence</Term>).</li>
        </ul></div>
      <div><div className="eyebrow">Strongest paths</div>
        <ul className="mt-2 flex flex-col gap-1">{top.map(l => (
          <li key={l.class + l.effect}><button onClick={() => pick(l.class, l.effect)} className="w-full rounded px-2 py-1.5 text-left hover:bg-hov">
            <b>{ix.cls[l.class].label}</b> → {ix.effect[l.effect]?.label.toLowerCase()} <span className="text-ink-3">· {l.direct_ids.length ? 'direct evidence' : `${l.drug_arm.raised} studies`}</span></button></li>))}</ul></div>
    </div>
  )
}

function PathPanel({ ix, l, papers, pick }: { ix: Index; l: Link; papers: PaperNode[]; pick: (p: PaperNode) => void }) {
  const a = l.drug_arm, h = ix.b.heat_arms.find(x => x.effect === l.effect)
  const by = (s: PaperNode['side']) => papers.filter(p => p.side === s)
  const List = ({ side, title, note }: { side: PaperNode['side']; title: string; note: string }) => by(side).length ? (
    <section><h3 className="eyebrow">{title} ({by(side).length})</h3><p className="text-[11.5px] text-ink-3">{note}</p>
      <ul className="mt-1.5 flex flex-col">{by(side).map(p => { const pp = ix.b.papers[p.pmid]; return (
        <li key={p.id}><button onClick={() => pick(p)} className="w-full rounded px-2 py-1.5 text-left text-[12.5px] hover:bg-hov">
          <b>{pp ? `${pp.authors} ${pp.year}` : `PMID ${p.pmid}`}</b> <span className="text-ink-2">{pp?.title ?? p.directText}</span>
          <span className="block text-[11px] text-ink-3">{p.findings.length} finding{p.findings.length === 1 ? '' : 's'} in the graph</span></button></li>) })}</ul></section>
  ) : null
  return (
    <div className="flex flex-col gap-4">
      <div><div className="eyebrow">Path</div><h2 className="font-display text-[20px] font-bold leading-snug">{ix.cls[l.class].label} → {ix.effect[l.effect]?.label} ← heat</h2>
        <p className="mt-1 text-[13px] text-ink-2">{a.studies > 0 ? `${a.raised} of ${a.studies} studies linked the medicine to more ${ix.effect[l.effect]?.label.toLowerCase()} (${a.lowered} to less). ` : ''}{h?.studies ?? 0} studies linked heat to it.{l.direct_ids.length ? ' It has also been studied directly in people taking the medicine during heat.' : ' No study has looked at both together.'}</p></div>
      <List side="direct" title="Studied together with heat" note="The strongest link: people on the medicine, measured during heat." />
      <List side="drug" title="Medicine and this effect" note="Papers with at least one finding showing raised risk." />
      <List side="heat" title="Heat and this effect" note="Papers linking hot weather to this effect." />
    </div>
  )
}

function PaperPanel({ ix, p, back }: { ix: Index; p: PaperNode; back: () => void }) {
  const pp = ix.b.papers[p.pmid]
  return (
    <div className="flex flex-col gap-3">
      <button onClick={back} className="self-start text-[12px] font-semibold text-accent">← Back to the path</button>
      <div className="eyebrow">{p.side === 'direct' ? 'Studied together with heat' : p.side === 'drug' ? 'Medicine and this effect' : 'Heat and this effect'}</div>
      <h2 className="font-display text-[18px] font-bold leading-snug">{pp?.title ?? `PMID ${p.pmid}`}</h2>
      {pp && <p className="text-[12px] text-ink-3">{pp.authors} {pp.year} · {pp.journal}</p>}
      {p.directText && <p className="rounded-md bg-heat-soft p-2 text-[13px]">{p.directText}</p>}
      <section><h3 className="eyebrow">Findings in the graph from this paper</h3>
        <p className="text-[11.5px] text-ink-3">Each finding is an edge in the System Public Graph between two measured variables.</p>
        <ul className="mt-2 flex flex-col gap-2">{p.findings.map(f => (
          <li key={f.id} className="rounded-md border border-line p-2 text-[12.5px] leading-snug">
            <span className="block"><b>{f.v1}</b></span><span className="block text-ink-3">linked to</span><span className="block"><b>{f.v2}</b></span>
            <span className="num mt-1 block">{f.stat.replace(/_/g, ' ')} <b>{f.value}</b>{f.lo ? ` (95% CI ${f.lo}–${f.hi})` : ''}{f.p ? `, p ${f.p}` : ''}</span>
            {f.pop && <span className="block text-[11.5px] text-ink-3">Population: {f.pop}</span>}
            <span className="block text-[11px] text-ink-3">Graph row {f.id} · {f.src === 'in_csv' ? 'vetted snapshot' : 'live graph only (unvetted)'}</span>
            {f.correction && <span className="block text-[11px] text-heat-ink">Corrected by us: {f.correction.text}</span>}
          </li>))}</ul></section>
      <Abstract pmid={p.pmid} />
    </div>
  )
}
