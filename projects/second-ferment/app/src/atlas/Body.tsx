// A clear anatomical figure with eight body-system markers and side labels.
// No drug selected: markers show what heat itself does (heat-side studies).
// Drug selected: markers show where that drug and heat meet, coloured by evidence tier, sized by studies.
import { motion } from 'motion/react'
import type { Index } from '../data/derive'
import type { Link } from '../data/types'

export const SYSTEMS: { id: string; label: string; sub: string; at: [number, number]; label_at: [number, number]; side: 'l' | 'r' }[] = [
  { id: 'heat', label: 'Heat illness', sub: 'heat stroke, overheating', at: [232, 70], label_at: [330, 52], side: 'r' },
  { id: 'brain', label: 'Brain', sub: 'confusion, delirium', at: [192, 58], label_at: [70, 52], side: 'l' },
  { id: 'heart', label: 'Heart and blood pressure', sub: 'fainting, rhythm', at: [214, 178], label_at: [330, 165], side: 'r' },
  { id: 'salts', label: 'Sodium and potassium', sub: 'low sodium, potassium', at: [98, 238], label_at: [70, 205], side: 'l' },
  { id: 'sugar', label: 'Blood sugar', sub: 'lows, ketoacidosis', at: [188, 226], label_at: [70, 285], side: 'l' },
  { id: 'kidney', label: 'Kidneys', sub: 'acute kidney injury', at: [224, 266], label_at: [330, 265], side: 'r' },
  { id: 'fluid', label: 'Fluid loss', sub: 'dehydration, sweating', at: [306, 222], label_at: [330, 340], side: 'r' },
  { id: 'falls', label: 'Falls', sub: 'fractures', at: [200, 450], label_at: [70, 440], side: 'l' },
]
const TIER_COL: Record<string, string> = { direct: 'var(--color-heat)', shared: 'var(--color-s2)', guidance_only: 'var(--color-faint)' }

export function Body({ ix, links, system, onSystem, drugLabel }: {
  ix: Index; links: Record<string, Link> | null; system: string | null; onSystem: (id: string | null) => void; drugLabel: string | null
}) {
  const BODY = 'var(--color-soft)', LINE = 'var(--color-line-2)'
  return (
    <svg viewBox="-150 0 700 560" className="block h-full w-full" role="img" aria-label="Body systems heat strains">
      {/* figure */}
      <g>
        {[['M114,150 Q92,240 86,345', 32], ['M286,150 Q308,240 314,345', 32], ['M172,330 L164,532', 44], ['M228,330 L236,532', 44]].map(([d, w]) => (
          <g key={d as string}>
            <path d={d as string} stroke={LINE} strokeWidth={(w as number) + 2} strokeLinecap="round" fill="none" />
            <path d={d as string} stroke={BODY} strokeWidth={w as number} strokeLinecap="round" fill="none" />
          </g>
        ))}
        <path d="M150,122 Q200,110 250,122 L284,140 Q298,150 296,172 L290,300 Q287,336 260,346 L140,346 Q113,336 110,300 L104,172 Q102,150 116,140 Z" fill={BODY} stroke={LINE} />
        <rect x={185} y={96} width={30} height={30} rx={8} fill={BODY} stroke={LINE} />
        <ellipse cx={200} cy={62} rx={40} ry={46} fill={BODY} stroke={LINE} />
        <rect x={184} y={110} width={32} height={18} fill={BODY} />
        {/* faint organ shapes for orientation */}
        <path d="M172,58 q8,-26 28,-24 q22,-2 28,24 q-6,16 -28,14 q-22,2 -28,-14z" fill="none" stroke={LINE} strokeDasharray="2 3" />
        <path d="M214,168 q12,-14 20,0 q-2,16 -20,24 q-18,-8 -20,-24 q8,-14 20,0z" fill="none" stroke={LINE} strokeDasharray="2 3" />
        <ellipse cx={176} cy={266} rx={10} ry={16} fill="none" stroke={LINE} strokeDasharray="2 3" />
        <ellipse cx={224} cy={266} rx={10} ry={16} fill="none" stroke={LINE} strokeDasharray="2 3" />
      </g>

      {SYSTEMS.map(s => {
        const l = links?.[s.id]
        const heatN = ix.heatStudiesByHub[s.id] ?? 0
        const n = l ? l.drug_arm.raised + l.direct_ids.length * 12 : 0
        const r = links ? (l ? Math.min(26, 8 + Math.sqrt(n) * 2.4) : 4) : Math.min(22, 6 + Math.sqrt(heatN) * 2.2)
        const fill = links ? (l ? TIER_COL[l.tier] ?? 'var(--color-faint)' : 'var(--color-line-2)') : 'var(--color-heat-soft)'
        const stroke = links ? 'none' : 'var(--color-heat)'
        const on = system === s.id
        const [lx, ly] = s.label_at
        const tx = s.side === 'r' ? lx : lx
        return (
          <g key={s.id} className="cursor-pointer" role="button" tabIndex={0} aria-label={s.label}
            onClick={() => onSystem(on ? null : s.id)} onKeyDown={e => { if (e.key === 'Enter') onSystem(on ? null : s.id) }}>
            <line x1={s.at[0]} y1={s.at[1]} x2={s.side === 'r' ? lx - 6 : lx + 6} y2={ly - 4} stroke={on ? 'var(--color-ink)' : 'var(--color-line-2)'} strokeWidth={on ? 1.4 : 0.8} />
            {l?.tier === 'direct' && <motion.circle cx={s.at[0]} cy={s.at[1]} fill="none" stroke="var(--color-heat)" strokeWidth={1.5}
              initial={{ r, opacity: 0.6 }} animate={{ r: r + 10, opacity: 0 }} transition={{ duration: 1.6, repeat: Infinity }} />}
            <motion.circle cx={s.at[0]} cy={s.at[1]} initial={false} animate={{ r }} transition={{ type: 'spring', stiffness: 160, damping: 18 }}
              fill={fill} fillOpacity={links ? 0.95 : 1} stroke={on ? 'var(--color-ink)' : stroke} strokeWidth={on ? 2.5 : 1}
              strokeDasharray={l?.tier === 'guidance_only' ? '3 3' : undefined} />
            <text x={tx} y={ly} textAnchor={s.side === 'r' ? 'start' : 'end'} fontSize={13} fontWeight={700} fill="var(--color-ink)">{s.label}</text>
            <text x={tx} y={ly + 14} textAnchor={s.side === 'r' ? 'start' : 'end'} fontSize={11} fill="var(--color-ink-3)">
              {links ? (l ? (l.tier === 'direct' ? 'direct evidence' : l.tier === 'shared' ? `${l.drug_arm.raised} drug studies, ${l.heat_arm_studies} heat studies` : 'guidance only, no studies') : '—') : `${s.sub} · ${heatN} heat studies`}
            </text>
          </g>
        )
      })}
      {drugLabel === null && <text x={200} y={552} textAnchor="middle" fontSize={11} fill="var(--color-ink-3)">Circle size: how many studies link heat to each part of the body. Choose a medicine to see where it adds risk.</text>}
    </svg>
  )
}
