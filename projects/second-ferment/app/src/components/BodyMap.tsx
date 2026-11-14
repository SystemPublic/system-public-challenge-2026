// Home view A (default): body systems as hubs on a faint body outline, drug classes as dots. Calm at rest;
// detail on demand: select a class to see its links, select a hub to zoom in and see one dot per study.
import { motion } from 'motion/react'
import { useMemo } from 'react'
import { BUCKET_LABEL, BUCKET_ORDER, classWeight, hubLinks, primaryBucket, topSpecialty, type Index } from '../data/derive'
import type { Link, Tier } from '../data/types'
import { useStore } from '../state/store'
import { useVisibleClasses } from './filters'

const W = 1000, H = 620
const HUB_POS: Record<string, [number, number]> = {
  heat: [215, 150], brain: [500, 92], heart: [785, 170], kidney: [500, 318],
  salts: [790, 370], sugar: [215, 370], fluid: [355, 492], falls: [645, 492],
}
const TIER_COLOR: Record<Tier, string> = {
  direct: 'var(--color-direct)', shared: 'var(--color-shared)', guidance_only: 'var(--color-guidance)',
  direct_misuse: 'var(--color-guidance)', weak: 'var(--color-guidance)',
}
const SPRING = { type: 'spring', stiffness: 120, damping: 20 } as const

function radius(w: number) { return Math.min(26, 7 + Math.sqrt(w) * 1.25) }

export function BodyMap({ ix }: { ix: Index }) {
  const s = useStore()
  const visible = useVisibleClasses(ix)
  const classes = ix.b.classes

  // positions for the current arrangement
  const pos = useMemo(() => {
    const out: Record<string, [number, number]> = {}
    if (s.arrange === 'system') {
      const byHub: Record<string, string[]> = {}
      for (const c of classes) (byHub[ix.primaryHub[c.id]] ??= []).push(c.id)
      for (const [hub, ids] of Object.entries(byHub)) {
        const [hx, hy] = HUB_POS[hub]
        ids.forEach((id, k) => {
          const a = -Math.PI / 2 + 0.75 + (k * 2 * Math.PI) / Math.max(ids.length, 3)
          out[id] = [hx + Math.cos(a) * 122, hy + Math.sin(a) * 76]
        })
      }
      if (s.selectedHub) {
        const [hx, hy] = HUB_POS[s.selectedHub]
        const linked = classes.filter(c => hubLinks(ix, c.id)[s.selectedHub!] && s.tiers.includes(hubLinks(ix, c.id)[s.selectedHub!].tier))
        linked.forEach((c, k) => {
          const a = -Math.PI / 2 + (k * 2 * Math.PI) / linked.length
          out[c.id] = [hx + Math.cos(a) * 190, hy + Math.sin(a) * 118]
        })
      }
    } else {
      const groups: string[] = s.arrange === 'action'
        ? [...BUCKET_ORDER, 'none']
        : (() => {
            const counts: Record<string, number> = {}
            for (const c of classes) counts[topSpecialty(c)] = (counts[topSpecialty(c)] ?? 0) + 1
            return Object.keys(counts).sort((a, z) => counts[z] - counts[a])
          })()
      const key = (id: string) => (s.arrange === 'action' ? primaryBucket(ix.cls[id]) : topSpecialty(ix.cls[id]))
      const used = groups.filter(g => classes.some(c => key(c.id) === g))
      const size: Record<string, number> = {}
      for (const c of classes) size[key(c.id)] = (size[key(c.id)] ?? 0) + 1
      const rowOf: Record<string, number> = {}
      const colW = W / used.length
      for (const c of classes) {
        const g = key(c.id)
        const k = (rowOf[g] = (rowOf[g] ?? -1) + 1)
        const split = size[g] > 6 // long groups wrap into two sub-columns
        const row = split ? Math.floor(k / 2) : k
        const dx = split ? (k % 2 === 0 ? -colW * 0.27 : colW * 0.27) : 0
        out[c.id] = [colW * (used.indexOf(g) + 0.5) + dx, 160 + row * 76 + (split && k % 2 ? 26 : 0)]
      }
    }
    return out
  }, [s.arrange, s.selectedHub, s.tiers, classes, ix])

  const groupsHeader = useMemo(() => {
    if (s.arrange === 'system') return []
    const xs: Record<string, number> = {}
    for (const c of classes) {
      const g = s.arrange === 'action' ? primaryBucket(c) : topSpecialty(c)
      xs[g] = pos[c.id][0]
    }
    return Object.entries(xs).map(([g, x]) => ({
      x, label: s.arrange === 'action' ? (g === 'none' ? 'No guidance action' : BUCKET_LABEL[g as keyof typeof BUCKET_LABEL]) : g,
    }))
  }, [s.arrange, pos, classes])

  const zoom = s.arrange === 'system' && s.selectedHub
  const viewBox = zoom ? (() => { const [x, y] = HUB_POS[s.selectedHub!]; return [x - 300, y - 180, 600, 360] })() : [0, 0, W, H]
  const sel = s.selectedClass
  const selLinks: Link[] = sel ? Object.values(hubLinks(ix, sel)).filter(l => s.tiers.includes(l.tier)) : []

  return (
    <motion.svg
      viewBox={viewBox.join(' ')}
      animate={{ viewBox: viewBox.join(' ') }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      className="block h-full w-full select-none"
      role="img"
      aria-label="Body systems as hubs, with drug classes around them"
      onClick={e => { if (e.target === e.currentTarget) { s.selectClass(null); s.selectHub(null) } }}
    >
      <defs>
        <radialGradient id="heatGlow">
          <stop offset="0%" stopColor="var(--color-direct)" stopOpacity="0.55" />
          <stop offset="100%" stopColor="var(--color-direct)" stopOpacity="0" />
        </radialGradient>
      </defs>

      {s.arrange === 'system' && (
        <g stroke="var(--color-hero-line)" strokeWidth={1.5} fill="none" pointerEvents="none">
          <circle cx={500} cy={92} r={52} />
          <rect x={410} y={150} width={180} height={300} rx={70} />
          <rect x={424} y={442} width={66} height={168} rx={32} />
          <rect x={510} y={442} width={66} height={168} rx={32} />
          <rect x={352} y={162} width={50} height={210} rx={25} />
          <rect x={598} y={162} width={50} height={210} rx={25} />
        </g>
      )}

      {groupsHeader.map(g => (
        <text key={g.label} x={g.x} y={92} textAnchor="middle" fontSize={15} fontWeight={600} fill="var(--color-hero-ink)"
          style={{ fontFamily: 'var(--font-display)' }}>{g.label}</text>
      ))}

      {/* heat glow on hubs */}
      {s.arrange === 'system' && ix.b.hubs.map(h => {
        const hs = ix.heatStudiesByHub[h.id] ?? 0
        const r = 34 + (s.heat === 0 ? 0 : (h.id === 'heat' ? 30 : 8 + Math.sqrt(hs) * 4) * (s.heat === 1 ? 0.65 : 1))
        return <motion.circle key={'g' + h.id} cx={HUB_POS[h.id][0]} cy={HUB_POS[h.id][1]} fill="url(#heatGlow)"
          animate={{ r, opacity: s.heat === 0 ? 0 : 1 }} transition={{ duration: 0.8 }} pointerEvents="none" />
      })}

      {/* links for the selected class */}
      {s.arrange === 'system' && !zoom && selLinks.map(l => {
        const hub = ix.hubOf[l.effect]!
        const [x1, y1] = pos[sel!], [x2, y2] = HUB_POS[hub]
        return <motion.line key={hub} x1={x1} y1={y1} x2={x2} y2={y2} stroke={TIER_COLOR[l.tier]}
          strokeWidth={l.tier === 'guidance_only' ? 1.6 : Math.min(9, 2 + Math.sqrt(l.drug_arm.raised + l.direct_ids.length * 10))}
          strokeDasharray={l.tier === 'guidance_only' ? '6 5' : undefined} strokeLinecap="round"
          initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 0.9 }} transition={{ duration: 0.5 }} />
      })}

      {/* zoomed hub: one line per class, one dot per study showing raised risk */}
      {zoom && classes.map(c => {
        const l = hubLinks(ix, c.id)[s.selectedHub!]
        if (!l || !s.tiers.includes(l.tier) || !visible.has(c.id)) return null
        const [x1, y1] = pos[c.id], [x2, y2] = HUB_POS[s.selectedHub!]
        const raised = l.drug_arm_ids.filter(id => ix.b.findings[id]?.dir === 'raised').slice(0, 40)
        const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1, px = -dy / len, py = dx / len
        return (
          <g key={c.id}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={TIER_COLOR[l.tier]} strokeOpacity={0.5} strokeWidth={1.4}
              strokeDasharray={l.tier === 'guidance_only' ? '5 4' : undefined} />
            {l.direct_ids.map((d, k) => (
              <circle key={d} cx={x1 + dx * (0.12 + k * 0.05)} cy={y1 + dy * (0.12 + k * 0.05)} r={6} fill="var(--color-direct)"
                stroke="var(--color-hero)" strokeWidth={1.5} className="cursor-pointer"
                onClick={() => s.selectFinding('direct:' + d)}><title>Direct study {d}</title></circle>
            ))}
            {raised.map((id, j) => {
              const t = 0.22 + 0.62 * ((j + 0.5) / raised.length), o = ((j % 5) - 2) * 3.4
              return (
                <motion.circle key={id} cx={x1 + dx * t + px * o} cy={y1 + dy * t + py * o} r={2.6}
                  fill={TIER_COLOR[l.tier]} className="cursor-pointer" initial={{ opacity: 0, r: 0 }}
                  animate={{ opacity: s.selectedFinding === id ? 1 : 0.85, r: s.selectedFinding === id ? 4.5 : 2.6 }}
                  transition={{ delay: j * 0.01 }} onClick={() => s.selectFinding(id)}>
                  <title>{ix.b.findings[id]?.v1} ↔ {ix.b.findings[id]?.v2}</title>
                </motion.circle>
              )
            })}
          </g>
        )
      })}

      {/* hubs */}
      {s.arrange === 'system' && ix.b.hubs.map(h => {
        const [x, y] = HUB_POS[h.id]
        const on = s.selectedHub === h.id, dim = zoom && !on
        const hs = ix.heatStudiesByHub[h.id] ?? 0
        const words = h.label.split(' ')
        return (
          <g key={h.id} className="cursor-pointer" opacity={dim ? 0.2 : 1} role="button" tabIndex={0}
            aria-label={`${h.label}: ${hs} heat studies`}
            onClick={() => s.selectHub(on ? null : h.id)}
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); s.selectHub(on ? null : h.id) } }}>
            <circle cx={x} cy={y} r={34} fill="var(--color-hero-2)" stroke={on ? 'var(--color-shared)' : 'var(--color-hero-ink-2)'} strokeWidth={on ? 2.5 : 1.2} />
            <text x={x} y={words.length > 1 ? y - 3 : y + 4} textAnchor="middle" fontSize={11.5} fontWeight={600} fill="var(--color-hero-ink)">{words[0]}</text>
            {words.length > 1 && <text x={x} y={y + 11} textAnchor="middle" fontSize={9.5} fill="var(--color-hero-ink-2)">{words.slice(1).join(' ')}</text>}
            {s.heat > 0 && hs > 0 && <text x={x} y={y + 50} textAnchor="middle" fontSize={10} fill="var(--color-direct)">heat: {hs} studies</text>}
          </g>
        )
      })}

      {/* drug class dots */}
      {classes.map(c => {
        const [x, y] = pos[c.id]
        const show = visible.has(c.id)
        const linked = zoom ? !!hubLinks(ix, c.id)[s.selectedHub!] && s.tiers.includes(hubLinks(ix, c.id)[s.selectedHub!].tier) : true
        const dim = !show || (sel && sel !== c.id) || (zoom && !linked)
        const best = zoom && linked ? hubLinks(ix, c.id)[s.selectedHub!]
          : (ix.linksByClass[c.id] ?? []).filter(l => s.tiers.includes(l.tier)).sort((a, z) => rank(z.tier) - rank(a.tier))[0]
        const colored = sel === c.id || (zoom && linked) || s.arrange !== 'system'
        const r = zoom ? Math.min(radius(classWeight(ix, c.id)), 13) : radius(classWeight(ix, c.id))
        return (
          <motion.g key={c.id} initial={false} animate={{ x, y, opacity: dim ? 0.18 : 1 }} transition={SPRING}
            className="cursor-pointer" role="button" tabIndex={show ? 0 : -1} aria-label={c.label}
            onClick={() => s.selectClass(sel === c.id ? null : c.id)}
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); s.selectClass(sel === c.id ? null : c.id) } }}>
            <circle r={r} fill={colored && best ? TIER_COLOR[best.tier] : 'var(--color-hero-ink-2)'}
              stroke={sel === c.id ? 'var(--color-hero-ink)' : 'none'} strokeWidth={2.5} />
            <text y={r + 14} textAnchor="middle" fontSize={zoom ? 9 : 11.5} fill="var(--color-hero-ink)" pointerEvents="none">{c.label}</text>
          </motion.g>
        )
      })}
    </motion.svg>
  )
}

function rank(t: Tier) { return { direct: 4, shared: 3, guidance_only: 2, direct_misuse: 1, weak: 0 }[t] }
