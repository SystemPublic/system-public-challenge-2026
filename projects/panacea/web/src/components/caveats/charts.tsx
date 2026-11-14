// Contested-tab charts: diverging spot-check bars, the modeled-vs-observed
// segmented bar, and the measurement-vintage timeline. Pure server components
// — the only interaction is SVG <title> tooltips.

import type { Contested } from "@/lib/bundle";
import { deEmdash } from "@/lib/format";

const SANS = "var(--font-sans)";

/** Diverging ρ bars for the flagship spot checks. */
export function SpotChart({ spot }: { spot: Contested["spot"] }) {
  const W = 660;
  const rowH = 64;
  const H = spot.length * rowH + 30;
  const LO = -0.5;
  const HI = 0.42;
  const X0 = 268; // label gutter — 44-char check names must fit left of the axis
  const x = (v: number) => X0 + ((v - LO) / (HI - LO)) * (W - X0 - 20);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 w-full h-auto" role="img"
      aria-label="Spot-check direction tests across 42 districts">
      {/* baseline + grid */}
      <line x1={x(0)} x2={x(0)} y1={8} y2={H - 18} stroke="var(--chart-baseline)" strokeWidth={1.5} />
      {[-0.4, -0.2, 0, 0.2, 0.4].map((g) => (
        <g key={g}>
          <line x1={x(g)} x2={x(g)} y1={8} y2={H - 18} stroke="var(--chart-grid)" strokeWidth={1} />
          <text x={x(g)} y={H - 4} textAnchor="middle" fontSize={10.5}
            fill="var(--chart-muted)" fontFamily={SANS}>{g}</text>
        </g>
      ))}
      {spot.map((r, i) => {
        const y = 24 + i * rowH;
        const v = r.spearman_uhf42;
        const col = Math.abs(v) < 0.1 ? "var(--div-mid)" : v >= 0 ? "var(--div-pos)" : "var(--div-neg)";
        const x0 = Math.min(x(0), x(v));
        const w = Math.max(Math.abs(x(v) - x(0)), 2);
        const name = r.check.length > 44 ? r.check.slice(0, 43) + "…" : r.check;
        return (
          <g key={r.check}>
            <rect x={x0} y={y} width={w} height={16} rx={4} fill={col}>
              <title>{`${r.check}: ρ=${v} over ${r.n_districts} districts\nExpectation: ${deEmdash(r.expectation)}`}</title>
            </rect>
            <text x={X0 - 12} y={y + 12} textAnchor="end" fontSize={11.5}
              fill="var(--ink)" fontFamily={SANS}>{name}</text>
            <text x={x0 + w + (v >= 0 ? 6 : -6)} y={y + 12}
              textAnchor={v >= 0 ? "start" : "end"} fontSize={11.5} fontWeight={600}
              fill="var(--ink)" fontFamily={SANS}>{v.toFixed(3)}</text>
            <text x={X0 - 12} y={y + 30} textAnchor="end" fontSize={10}
              fill="var(--chart-muted)" fontFamily={SANS}>
              {`${r.measure1} vs ${r.measure2}`}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/** Modeled-vs-observed split of the computed city checks (segmented bar). */
export function ModeledBar({ modeled }: { modeled: Contested["modeled"] }) {
  const total = modeled.conf_observed + modeled.conf_modeled;
  const W = 560;
  const H = 28;
  const gap = 2;
  const parts = [
    { v: modeled.conf_observed, label: "observed", color: "var(--s-blue)", text: "var(--paper)" },
    { v: modeled.conf_modeled, label: "modeled ρ⚠", color: "var(--status-warn)", text: "var(--paper)" },
  ];
  let x0 = 0;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 w-full h-auto" role="img"
      aria-label={`City correlation checks: ${modeled.conf_observed} observed, ${modeled.conf_modeled} modeled`}>
      {parts.map((p, i) => {
        const w = (p.v / total) * (W - 8);
        const el = (
          <g key={p.label}>
            <rect x={x0 + (i ? gap : 0)} y={0} width={Math.max(w - gap, 4)} height={H}
              rx={4} fill={p.color}>
              <title>{`${p.v} ${p.label} of ${total} computed checks`}</title>
            </rect>
            {w > 80 && (
              <text
                x={x0 + (i ? gap : 0) + 10}
                y={H / 2 + 4}
                fontSize={11.5}
                fontWeight={600}
                fill={p.text}
                fontFamily={SANS}
              >
                {`${p.v} ${p.label}`}
              </text>
            )}
          </g>
        );
        x0 += w;
        return el;
      })}
    </svg>
  );
}

const COLL_COLORS: Record<string, string> = {
  "environment-health": "var(--s-blue)",
  "heat-complaints": "#d95926",
  "leading-causes-of-death": "var(--s-aqua)",
  "street-trees": "#c98500",
};

/** Measurement vintages: year-range bars grouped by NYC collection. */
export function VintageChart({ vintage }: { vintage: Contested["vintage"] }) {
  const rows = vintage
    .filter((r) => r.yr)
    .map((r) => ({ ...r, y0: +r.yr.split("-")[0], y1: +r.yr.split("-")[1] }))
    .sort((a, b) => (a.coll + a.l).localeCompare(b.coll + b.l));
  const W = 900;
  const rowH = 17;
  const H = rows.length * rowH + 40;
  const X0 = 250;
  const LO = 1996;
  const HI = 2026;
  const x = (v: number) => X0 + ((v - LO) / (HI - LO)) * (W - X0 - 20);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 w-full h-auto" role="img"
      aria-label="Measurement vintages by NYC collection">
      {[1996, 2000, 2005, 2010, 2015, 2020, 2026].map((g) => (
        <g key={g}>
          <line x1={x(g)} x2={x(g)} y1={6} y2={H - 22} stroke="var(--chart-grid)" strokeWidth={1} />
          <text x={x(g)} y={H - 8} textAnchor="middle" fontSize={10.5}
            fill="var(--chart-muted)" fontFamily={SANS}>{g}</text>
        </g>
      ))}
      {rows.map((r, i) => {
        const y = 10 + i * rowH;
        const w = Math.max(x(r.y1) - x(r.y0), 3);
        const col = COLL_COLORS[r.coll] ?? "var(--s-deemph)";
        return (
          <g key={r.id}>
            <rect
              x={x(r.y0)} y={y} width={w} height={11} rx={3}
              fill={col} opacity={r.mod ? 0.55 : 0.92}
              stroke="var(--paper)" strokeWidth={1}
            >
              <title>{`${r.l}: ${r.coll}, ${r.yr}${r.mod ? " (modeled attribution)" : ""}`}</title>
            </rect>
            {r.mod && (
              <text x={x(r.y1) + 5} y={y + 9} fontSize={9.5}
                fill="var(--chart-muted)" fontFamily={SANS}>modeled</text>
            )}
            <text x={X0 - 8} y={y + 9.5} textAnchor="end" fontSize={10.5}
              fill="var(--ink)" fontFamily={SANS}>
              {r.l.length > 44 ? r.l.slice(0, 43) + "…" : r.l}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export function VintageLegend() {
  return (
    <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 font-sans text-[0.72rem] text-[color:var(--chart-ink-2)]">
      {Object.entries(COLL_COLORS).map(([coll, col]) => (
        <span key={coll} className="inline-flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-[3px]" style={{ background: col }} />
          {coll}
        </span>
      ))}
    </div>
  );
}
