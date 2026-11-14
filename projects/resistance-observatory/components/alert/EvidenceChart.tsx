"use client";

import { useState } from "react";
import type { AlertEvent, CellStat, Watch, WhoBasis } from "@/lib/alert/derive";
import { WHO_BAND_LINES } from "@/lib/alert/derive";
import { ci, frac, pct } from "@/lib/alert/copy";
import { KindMark } from "./glyphs";
import css from "./alert.module.css";

const W = 760;
const H = 330;
const M = { l: 46, r: 78, t: 18, b: 36 };

/** Mark radius carries sample size (area roughly proportional to n). */
export const radiusFor = (n: number) => Math.max(3.5, Math.min(13, 2.6 + Math.sqrt(n) / 2.1));

type Props = {
  country: string;
  marker: string;
  cells: CellStat[];
  companion: CellStat[];
  watch: Watch;
  basis: WhoBasis;
  /** Genome events for this watch (all years). */
  events: AlertEvent[];
  replayYear: number;
  freshYear: number | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export function EvidenceChart(props: Props) {
  const { cells, companion, watch, basis, events, replayYear, country, marker } = props;
  const [hover, setHover] = useState<CellStat | null>(null);

  if (cells.length === 0) {
    return (
      <div className="grid h-56 place-items-center rounded-[var(--radius)] border border-dashed border-line-strong text-sm text-muted">
        No genome counts for {country}. That means not sampled, not absent.
      </div>
    );
  }

  const y0 = cells[0].year;
  const y1 = cells[cells.length - 1].year;
  const pad = y1 - y0 < 4 ? 2 : 1;
  const xMin = y0 - pad;
  const xMax = y1 + pad;
  const x = (yr: number) => M.l + ((yr - xMin) / (xMax - xMin)) * (W - M.l - M.r);
  const y = (v: number) => M.t + (1 - v / 100) * (H - M.t - M.b);
  const span = xMax - xMin;
  const step = span > 40 ? 10 : span > 16 ? 5 : span > 8 ? 2 : 1;
  const xTicks: number[] = [];
  for (let t = Math.ceil(xMin / step) * step; t <= xMax; t += step) xTicks.push(t);

  const esa = basis === "east_southern_africa";
  const bandMode = watch.trigger === "who_band" || watch.trigger === "very_high_combo";
  const showBands = esa;
  const showCompanion = bandMode && companion.length > 0;
  const levelLine =
    watch.trigger === "rise" || watch.trigger === "fall" ? watch.level : null;
  const levelIsWho = esa && (levelLine === WHO_BAND_LINES.medium || levelLine === WHO_BAND_LINES.high);

  const qual = cells.filter((c) => c.n >= watch.minN);
  const visible = (yr: number) => yr <= replayYear;
  const eventByYear = new Map(events.filter((e) => e.cell).map((e) => [e.year, e]));

  const shown = hover ?? null;

  return (
    <figure className="m-0">
      <div className="overflow-x-auto">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="block h-auto w-full min-w-[560px]"
          role="group"
          aria-label={`${marker} among genome samples collected in ${country}, by collection year, with 95% intervals`}
        >
          {/* WHO bands as a quiet backdrop (East and Southern Africa only) */}
          {showBands ? (
            <g aria-hidden>
              <rect x={M.l} y={y(100)} width={W - M.l - M.r} height={y(60) - y(100)} fill="var(--surface-2)" opacity={0.95} />
              <rect x={M.l} y={y(60)} width={W - M.l - M.r} height={y(40) - y(60)} fill="var(--surface-2)" opacity={0.5} />
              {[
                ["high", 80],
                ["medium", 50],
                ["low", 24],
              ].map(([label, at]) => (
                <text key={label} x={W - M.r + 8} y={y(at as number) + 4} fontSize={11} fill="var(--muted)" fontFamily="var(--font-mono)">
                  {label}
                </text>
              ))}
              <text x={W - M.r + 8} y={y(100) + 4} fontSize={9.5} fill="var(--muted)" fontFamily="var(--font-mono)">
                WHO band
              </text>
            </g>
          ) : null}

          {/* grid */}
          {[0, 20, 40, 60, 80, 100].map((t) => (
            <g key={t} aria-hidden>
              <line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} stroke="var(--line)" strokeWidth={t === 0 ? 1.2 : 0.7} />
              <text x={M.l - 8} y={y(t) + 4} textAnchor="end" fontSize={11} fill="var(--muted)" fontFamily="var(--font-mono)">
                {t}
                {t === 100 ? "%" : ""}
              </text>
            </g>
          ))}
          {xTicks.map((t) => (
            <g key={t} aria-hidden>
              <line x1={x(t)} x2={x(t)} y1={H - M.b} y2={H - M.b + 5} stroke="var(--line-strong)" />
              <text x={x(t)} y={H - M.b + 18} textAnchor="middle" fontSize={11} fill="var(--muted)" fontFamily="var(--font-mono)">
                {t}
              </text>
            </g>
          ))}
          <text x={M.l} y={H - 3} fontSize={10.5} fill="var(--muted)">
            collection year
          </text>

          {/* threshold lines */}
          {showBands
            ? [WHO_BAND_LINES.medium, WHO_BAND_LINES.high].map((t) => (
                <g key={t}>
                  <line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} stroke="var(--line-strong)" strokeWidth={1.2} strokeDasharray="5 4" />
                  <text x={W - M.r + 8} y={y(t) + 4} fontSize={10.5} fontWeight={600} fill="var(--fg)" fontFamily="var(--font-mono)">
                    WHO {t}%
                  </text>
                </g>
              ))
            : null}
          {levelLine !== null && !(showBands && levelIsWho) ? (
            <g>
              <line x1={M.l} x2={W - M.r} y1={y(levelLine)} y2={y(levelLine)} stroke="var(--signal)" strokeWidth={1.4} strokeDasharray="2 4" />
              <text x={W - M.r - 6} y={y(levelLine) - 5} textAnchor="end" fontSize={10.5} fill="var(--signal)" fontFamily="var(--font-mono)">
                {levelIsWho ? `WHO ${levelLine}%` : `preset ${levelLine}%`}
              </text>
            </g>
          ) : null}
          {levelLine !== null && showBands && levelIsWho ? (
            <line x1={M.l} x2={W - M.r} y1={y(levelLine)} y2={y(levelLine)} stroke="var(--signal)" strokeWidth={1.6} strokeDasharray="5 4" />
          ) : null}
          {showCompanion ? (
            <g>
              <line x1={M.l} x2={W - M.r} y1={y(WHO_BAND_LINES.a581g)} y2={y(WHO_BAND_LINES.a581g)} stroke="var(--drug)" strokeWidth={1} strokeDasharray="2 4" />
              <text x={W - M.r + 8} y={y(WHO_BAND_LINES.a581g) + 4} fontSize={10.5} fill="var(--drug)" fontFamily="var(--font-mono)">
                ◇ A581G 5%
              </text>
            </g>
          ) : null}

          {/* trend between qualifying cells; dashed across unsampled years */}
          {qual.slice(1).map((c, i) => {
            const p = qual[i];
            const gap = c.year - p.year > 1;
            return (
              <line
                key={c.year}
                x1={x(p.year)}
                y1={y(p.pct)}
                x2={x(c.year)}
                y2={y(c.pct)}
                stroke="var(--fg)"
                strokeOpacity={gap ? 0.35 : 0.6}
                strokeWidth={1.5}
                strokeDasharray={gap ? "3 4" : undefined}
                className={`${css.mark} ${visible(c.year) ? "" : css.markHidden}`}
              />
            );
          })}

          {/* companion A581G: small hollow diamonds, same axis (also a percentage) */}
          {showCompanion
            ? companion.map((c) => (
                <g
                  key={c.year}
                  transform={`translate(${x(c.year)} ${y(c.pct)})`}
                  className={`${css.mark} ${visible(c.year) ? "" : css.markHidden}`}
                  style={{ color: "var(--drug)" }}
                  opacity={c.n >= watch.minN ? 1 : 0.45}
                >
                  <line x1={0} x2={0} y1={y(c.ci.hi) - y(c.pct)} y2={y(c.ci.lo) - y(c.pct)} stroke="currentColor" strokeWidth={1} />
                  <path d="M0 -4.5 L4.5 0 L0 4.5 L-4.5 0 Z" fill="var(--surface)" stroke="currentColor" strokeWidth={1.5} />
                  <title>{`A581G, collected ${c.year}: ${frac(c)} (${pct(c.pct)}, ${ci(c)})`}</title>
                </g>
              ))
            : null}

          {/* cells: interval drawn, radius = sample size, hollow when under the minimum */}
          {cells.map((c) => {
            const ok = c.n >= watch.minN;
            const r = radiusFor(c.n);
            const ev = eventByYear.get(c.year);
            const fired = ev?.fired;
            const selected = ev && ev.id === props.selectedId;
            return (
              <g
                key={c.year}
                className={`${css.mark} ${visible(c.year) ? "" : css.markHidden}`}
                tabIndex={visible(c.year) ? 0 : -1}
                role={ev ? "button" : "img"}
                aria-label={`Collected ${c.year}: ${frac(c)} carried ${marker}, ${pct(c.pct)}, ${ci(c)}${ok ? "" : `, under the minimum of ${watch.minN} samples`}${fired ? ". Alert fired; press Enter to open." : ""}`}
                onMouseEnter={() => setHover(c)}
                onMouseLeave={() => setHover(null)}
                onFocus={() => setHover(c)}
                onBlur={() => setHover(null)}
                onClick={() => ev && props.onSelect(ev.id)}
                onKeyDown={(k) => {
                  if (ev && (k.key === "Enter" || k.key === " ")) {
                    k.preventDefault();
                    props.onSelect(ev.id);
                  }
                }}
                style={{ cursor: ev ? "pointer" : "default", outline: "none" }}
              >
                {/* generous hit area */}
                <rect x={x(c.year) - 11} y={M.t} width={22} height={H - M.t - M.b} fill="transparent" />
                <line
                  x1={x(c.year)}
                  x2={x(c.year)}
                  y1={y(c.ci.hi)}
                  y2={y(c.ci.lo)}
                  stroke={ok ? "var(--fg)" : "var(--muted)"}
                  strokeWidth={ok ? 1.6 : 1}
                  strokeOpacity={ok ? 0.75 : 0.6}
                />
                {[c.ci.hi, c.ci.lo].map((v, i) => (
                  <line key={i} x1={x(c.year) - 3} x2={x(c.year) + 3} y1={y(v)} y2={y(v)} stroke={ok ? "var(--fg)" : "var(--muted)"} strokeWidth={1} strokeOpacity={0.7} />
                ))}
                <circle
                  cx={x(c.year)}
                  cy={y(c.pct)}
                  r={r}
                  fill={ok ? (fired ? "var(--signal)" : "var(--fg)") : "var(--surface)"}
                  stroke={ok ? "var(--surface)" : "var(--muted)"}
                  strokeWidth={ok ? 2 : 1.3}
                  strokeDasharray={ok ? undefined : "2.5 2"}
                />
                {hover === c || selected ? (
                  <circle cx={x(c.year)} cy={y(c.pct)} r={r + 4} fill="none" stroke={selected ? "var(--signal)" : "var(--focus)"} strokeWidth={1.6} />
                ) : null}
                {fired && ev ? (
                  <g transform={`translate(${x(c.year)} ${Math.max(M.t + 9, y(c.ci.hi) - 13)})`} style={{ color: "var(--signal)" }}>
                    {props.freshYear === c.year ? <circle className={css.pulse} r={6} /> : null}
                    <KindMark kind={ev.kind} direction={ev.direction} r={6.5} />
                  </g>
                ) : null}
              </g>
            );
          })}
        </svg>
      </div>

      <figcaption className="mt-2 flex min-h-[2.6rem] flex-wrap items-start justify-between gap-x-6 gap-y-1 text-xs text-muted">
        <p aria-live="polite" className="font-mono text-[0.72rem] text-fg">
          {shown ? (
            <>
              {country}, collected {shown.year}: <strong>{frac(shown)}</strong> carried {marker} · {pct(shown.pct)} · {ci(shown)}
              {shown.n < watch.minN ? ` · under the minimum of ${watch.minN}` : ""}
            </>
          ) : (
            <span className="text-muted">Hover or tab to a mark for its counts.</span>
          )}
        </p>
        <ul className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <li className="flex items-center gap-1.5">
            <svg width="34" height="14" aria-hidden>
              <circle cx="6" cy="7" r="3.5" fill="var(--fg)" />
              <circle cx="24" cy="7" r="6.5" fill="var(--fg)" />
            </svg>
            mark size = samples
          </li>
          <li className="flex items-center gap-1.5">
            <svg width="14" height="14" aria-hidden>
              <circle cx="7" cy="7" r="5" fill="none" stroke="var(--muted)" strokeDasharray="2.5 2" strokeWidth="1.3" />
            </svg>
            under {watch.minN} samples (not counted)
          </li>
          <li className="flex items-center gap-1.5">
            <svg width="10" height="16" aria-hidden>
              <path d="M5 1v14M2 1h6M2 15h6" stroke="var(--fg)" strokeWidth="1.2" fill="none" />
            </svg>
            95% Wilson interval
          </li>
          <li className="flex items-center gap-1.5">
            <svg width="26" height="8" aria-hidden>
              <line x1="0" x2="26" y1="4" y2="4" stroke="var(--fg)" strokeOpacity="0.4" strokeDasharray="3 4" strokeWidth="1.5" />
            </svg>
            years between not sampled
          </li>
        </ul>
      </figcaption>

      <details className="mt-2 text-xs">
        <summary className="cursor-pointer text-muted hover:text-fg">Counts as a table</summary>
        <div className="mt-2 max-h-64 overflow-auto rounded border border-line">
          <table className="w-full border-collapse font-mono text-[0.72rem]">
            <thead className="sticky top-0 bg-surface-2 text-left">
              <tr>
                <th className="px-2 py-1 font-medium">Collected</th>
                <th className="px-2 py-1 font-medium">Carrying / tested</th>
                <th className="px-2 py-1 font-medium">%</th>
                <th className="px-2 py-1 font-medium">95% CI</th>
                <th className="px-2 py-1 font-medium">Counted</th>
              </tr>
            </thead>
            <tbody>
              {cells.map((c) => (
                <tr key={c.year} className="border-t border-line">
                  <td className="px-2 py-1">{c.year}</td>
                  <td className="px-2 py-1">
                    {c.x} / {c.n}
                  </td>
                  <td className="px-2 py-1">{c.pct.toFixed(1)}</td>
                  <td className="px-2 py-1">
                    {c.ci.lo.toFixed(1)} to {c.ci.hi.toFixed(1)}
                  </td>
                  <td className="px-2 py-1">{c.n >= watch.minN ? "yes" : `no (under ${watch.minN})`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}
