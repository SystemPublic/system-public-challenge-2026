// Home view B: the full picture on one screen. Drug classes → body effects → actions, ribbons coloured by evidence
// tier and sized by harmful-direction studies. Faint at rest; the hovered or selected path is drawn at full strength.
import { motion } from 'motion/react'
import { useMemo, useState } from 'react'
import { BUCKET_LABEL, BUCKET_ORDER, type Index } from '../data/derive'
import type { Bucket, Link, Tier } from '../data/types'
import { useStore } from '../state/store'
import { useVisibleClasses } from './filters'

const W = 1000, H = 640
const X_CLASS = 200, X_EFF = 455, W_EFF = 190, X_ACT = 830, W_ACT = 150
const TIER_COLOR: Record<Tier, string> = {
  direct: 'var(--color-direct)', shared: 'var(--color-shared)', guidance_only: 'var(--color-guidance)',
  direct_misuse: 'var(--color-guidance)', weak: 'var(--color-guidance)',
}

function curve(x1: number, y1: number, x2: number, y2: number) {
  const m = (x1 + x2) / 2
  return `M${x1},${y1} C${m},${y1} ${m},${y2} ${x2},${y2}`
}

export function RibbonMap({ ix }: { ix: Index }) {
  const s = useStore()
  const visible = useVisibleClasses(ix)
  const [hover, setHover] = useState<{ kind: 'class' | 'effect' | 'action'; id: string } | null>(null)

  const effects = ix.b.effects.filter(e => e.id !== 'overdose')
  const yClass = (i: number) => 30 + i * ((H - 50) / ix.b.classes.length)
  const yEff = (i: number) => 34 + i * ((H - 60) / effects.length)
  const yAct = (i: number) => 90 + i * 112

  const links = useMemo(() => ix.b.links.filter(l =>
    s.tiers.includes(l.tier) && visible.has(l.class) && effects.some(e => e.id === l.effect) &&
    (!s.topOnly || l.tier === 'direct' || l.drug_arm.raised >= 10)), [ix, s.tiers, s.topOnly, visible, effects])

  const effActs = ix.b.effect_actions.filter(e => e.bucket) as { effect: string; bucket: Bucket; basis: string[]; note: string }[]

  // what is "lit": the hovered thing, else the selected class / hub
  const focus = hover ?? (s.selectedClass ? { kind: 'class' as const, id: s.selectedClass } : null)
  const litLink = (l: Link) => !focus ? null
    : focus.kind === 'class' ? l.class === focus.id
    : focus.kind === 'effect' ? l.effect === focus.id
    : effActs.some(e => e.effect === l.effect && e.bucket === focus.id)
  const litEffects = new Set(focus ? (focus.kind === 'effect' ? [focus.id] : links.filter(l => litLink(l)).map(l => l.effect)) : [])
  const base = s.heat === 0 ? 0.16 : s.heat === 1 ? 0.26 : 0.38

  const width = (l: Link) => l.tier === 'guidance_only' ? 1.6 : Math.min(16, 2 + Math.sqrt(l.drug_arm.raised) * 1.5 + (l.direct_ids.length ? 4 : 0))

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="block h-full w-full select-none" role="img"
      aria-label="Ribbons from drug classes to body effects to actions" onMouseLeave={() => setHover(null)}>
      {/* effect → action */}
      {effActs.map(ea => {
        const i = effects.findIndex(e => e.id === ea.effect), j = BUCKET_ORDER.indexOf(ea.bucket)
        if (i < 0 || j < 0) return null
        const lit = focus ? (focus.kind === 'action' ? focus.id === ea.bucket : litEffects.has(ea.effect)) : false
        return <motion.path key={ea.effect + ea.bucket} d={curve(X_EFF + W_EFF, yEff(i), X_ACT, yAct(j))} fill="none"
          stroke="var(--color-hero-ink-2)" strokeWidth={1.4} strokeDasharray={ea.basis.length ? undefined : '3 4'}
          animate={{ opacity: lit ? 0.9 : focus ? 0.06 : 0.3 }} transition={{ duration: 0.25 }} />
      })}

      {/* class → effect ribbons */}
      {links.map(l => {
        const i = ix.b.classes.findIndex(c => c.id === l.class), k = effects.findIndex(e => e.id === l.effect)
        const lit = litLink(l)
        return <motion.path key={l.class + l.effect} d={curve(X_CLASS + 8, yClass(i), X_EFF, yEff(k))} fill="none"
          stroke={TIER_COLOR[l.tier]} strokeLinecap="round" strokeDasharray={l.tier === 'guidance_only' ? '6 5' : undefined}
          initial={false} animate={{ opacity: lit ? 0.95 : focus ? 0.05 : base, strokeWidth: width(l) }}
          transition={{ duration: 0.3 }} className="cursor-pointer"
          onMouseEnter={() => setHover({ kind: 'class', id: l.class })} onClick={() => s.selectClass(l.class)}>
          <title>{ix.cls[l.class].label} → {ix.effect[l.effect].label}: {l.tier.replace('_', ' ')}, {l.drug_arm.raised} of {l.drug_arm.studies} studies raised</title>
        </motion.path>
      })}

      {/* classes */}
      {ix.b.classes.map((c, i) => {
        const on = s.selectedClass === c.id || (hover?.kind === 'class' && hover.id === c.id)
        const dim = !visible.has(c.id) || (focus && focus.kind === 'class' && !on) ||
          (focus && focus.kind !== 'class' && !links.some(l => l.class === c.id && litLink(l)))
        return (
          <g key={c.id} className="cursor-pointer" opacity={dim ? 0.3 : 1} role="button" tabIndex={0}
            onMouseEnter={() => setHover({ kind: 'class', id: c.id })}
            onClick={() => s.selectClass(s.selectedClass === c.id ? null : c.id)}
            onKeyDown={e => { if (e.key === 'Enter') s.selectClass(s.selectedClass === c.id ? null : c.id) }}>
            <text x={X_CLASS} y={yClass(i) + 4} textAnchor="end" fontSize={13} fontWeight={on ? 650 : 500}
              fill={on ? 'var(--color-shared)' : 'var(--color-hero-ink)'}>{c.label}</text>
            <circle cx={X_CLASS + 8} cy={yClass(i)} r={3} fill="var(--color-hero-ink-2)" />
          </g>
        )
      })}

      {/* effects */}
      {effects.map((e, k) => {
        const on = litEffects.has(e.id)
        return (
          <g key={e.id} className="cursor-pointer" onMouseEnter={() => setHover({ kind: 'effect', id: e.id })}
            onClick={() => e.hub && s.selectHub(e.hub)} opacity={focus && !on ? 0.35 : 1}>
            <rect x={X_EFF} y={yEff(k) - 14} width={W_EFF} height={28} rx={6} fill="var(--color-hero-2)"
              stroke={on ? 'var(--color-shared)' : 'var(--color-hero-line)'} />
            <text x={X_EFF + W_EFF / 2} y={yEff(k) + 4} textAnchor="middle" fontSize={11.5} fill="var(--color-hero-ink)">{e.label}</text>
          </g>
        )
      })}

      {/* actions */}
      {BUCKET_ORDER.map((b, j) => {
        const on = focus?.kind === 'action' ? focus.id === b : effActs.some(ea => ea.bucket === b && litEffects.has(ea.effect))
        return (
          <g key={b} className="cursor-pointer" onMouseEnter={() => setHover({ kind: 'action', id: b })}
            onClick={() => s.setBucket(s.bucket === b ? null : b)} opacity={focus && !on ? 0.4 : 1}>
            <rect x={X_ACT} y={yAct(j) - 20} width={W_ACT} height={40} rx={8} fill="none"
              stroke={s.bucket === b ? 'var(--color-shared)' : 'var(--color-hero-ink-2)'} strokeWidth={s.bucket === b ? 2 : 1} />
            <text x={X_ACT + W_ACT / 2} y={yAct(j) + 5} textAnchor="middle" fontSize={13} fontWeight={600}
              fill="var(--color-hero-ink)" style={{ fontFamily: 'var(--font-display)' }}>{BUCKET_LABEL[b]}</text>
          </g>
        )
      })}
    </svg>
  )
}
