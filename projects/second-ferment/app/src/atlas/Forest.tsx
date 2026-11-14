// Forest plot on a log scale: one row per study (or risk factor), point = estimate, bar = 95% CI when reported.
export interface ForestRow { label: string; est: number; lo?: number; hi?: number; tone: 'risk' | 'null' | 'protective'; sub?: string; pmid?: string; vetted?: boolean }

const STAT = /\b(aOR|OR|HR|RR|IRR|aHR)\s*=?\s*([\d.]+)\s*\(([\d.]+)\s*(?:to|–|-)\s*([\d.]+)\)/i
const STAT_NOCI = /\b(aOR|OR|HR|RR|IRR|aHR)\s*=?\s*([\d.]+)/i

/** Pull the first ratio with its CI out of a study summary; null if the summary has no ratio. */
export function parseRatio(text: string): { est: number; lo?: number; hi?: number; kind: string } | null {
  const m = text.match(STAT)
  if (m) return { kind: m[1], est: +m[2], lo: +m[3], hi: +m[4] }
  const n = text.match(STAT_NOCI)
  if (n) return { kind: n[1], est: +n[2] }
  return null
}

export function Forest({ rows, height = 26 }: { rows: ForestRow[]; height?: number }) {
  if (!rows.length) return null
  const vals = rows.flatMap(r => [r.est, r.lo ?? r.est, r.hi ?? r.est]).filter(v => v > 0)
  const min = Math.min(0.1, ...vals) * 0.9, max = Math.max(10, ...vals) * 1.1
  const L = 210, R = 392, W = R - L
  const x = (v: number) => L + ((Math.log(v) - Math.log(min)) / (Math.log(max) - Math.log(min))) * W
  const ticks = [0.1, 0.5, 1, 2, 5, 10, 50].filter(t => t >= min && t <= max)
  const H = rows.length * height + 30
  const col = { risk: 'var(--color-heat)', null: 'var(--color-faint)', protective: 'var(--color-green)' }
  return (
    <svg viewBox={`0 0 448 ${H}`} className="w-full max-w-[560px]" role="img" aria-label="Forest plot of study results">
      <line x1={x(1)} x2={x(1)} y1={4} y2={H - 22} stroke="var(--color-line-2)" strokeDasharray="3 3" />
      {ticks.map(t => (
        <g key={t}>
          <line x1={x(t)} x2={x(t)} y1={H - 22} y2={H - 18} stroke="var(--color-line-2)" />
          <text x={x(t)} y={H - 6} fontSize={9.5} textAnchor="middle" fill="var(--color-ink-3)">{t}</text>
        </g>
      ))}
      {rows.map((r, i) => {
        const y = 14 + i * height
        return (
          <g key={r.label + i}>
            <text x={0} y={y + 1} fontSize={11} fill="var(--color-ink)">{r.label.length > 38 ? r.label.slice(0, 37) + '…' : r.label}<title>{r.label}</title></text>
            {r.sub && <text x={0} y={y + 12} fontSize={9.5} fill="var(--color-ink-3)">{r.sub}</text>}
            {r.lo !== undefined && r.hi !== undefined && (
              <line x1={x(Math.max(r.lo, min))} x2={x(Math.min(r.hi, max))} y1={y} y2={y} stroke={col[r.tone]} strokeWidth={2}
                strokeDasharray={r.vetted === false ? '3 2' : undefined} />
            )}
            <rect x={x(r.est) - 4} y={y - 4} width={8} height={8} fill={col[r.tone]} />
            <text x={Math.min(x(Math.min(r.hi ?? r.est, max)) + 6, 416)} y={y + 4} fontSize={10.5} fontWeight={600} fill="var(--color-ink)">{r.est}</text>
          </g>
        )
      })}
      <text x={x(1)} y={H - 26} fontSize={9} textAnchor="middle" fill="var(--color-ink-3)" dy={-H + 34}>no effect</text>
    </svg>
  )
}
