"use client";

import type { AlertEvent, CellStat } from "@/lib/alert/derive";
import { KindMark } from "./glyphs";
import { radiusFor } from "./EvidenceChart";
import css from "./alert.module.css";

const W = 1000;
const GUT = 132;
const RPAD = 22;
const LANES = { genomes: 44, papers: 104, graph: 160 } as const;
const H = 208;

export type PaperTick = { year: number; total: number; inCountry: number };
export type GraphTick = { year: number; key: string; inCountry: boolean; label: string };
export type WhoYear = { year: number; label: string };

type Props = {
  domain: [number, number];
  replayYear: number;
  onReplayYear: (y: number) => void;
  playing: boolean;
  onTogglePlay: () => void;
  country: string;
  minN: number;
  cells: CellStat[];
  /** Study behind a genome cell (partner studies, site scope, DNA preparation), for the hover text. */
  cellNote?: (year: number) => string;
  /** One line on an alert and the study behind it, for the hover text. */
  eventNote?: (e: AlertEvent) => string;
  papers: PaperTick[];
  graph: GraphTick[];
  events: AlertEvent[];
  whoYears: WhoYear[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  freshYear: number | null;
};

export function Timeline(p: Props) {
  const [y0, y1] = p.domain;
  const x = (yr: number) => GUT + ((yr - y0) / Math.max(1, y1 - y0)) * (W - GUT - RPAD);
  const span = y1 - y0;
  const step = span > 45 ? 10 : span > 18 ? 5 : 2;
  const ticks: number[] = [];
  for (let t = Math.ceil(y0 / step) * step; t <= y1; t += step) ticks.push(t);
  const maxPapers = Math.max(1, ...p.papers.map((d) => d.total));
  const barH = (n: number) => (n / maxPapers) * 34;
  const vis = (yr: number) => yr <= p.replayYear;

  // fired events, offset sideways when several share a lane and year
  const fired = p.events.filter((e) => e.fired);
  const slot = new Map<string, number>();
  const placed = fired.map((e) => {
    const k = `${e.source}:${e.year}`;
    const i = slot.get(k) ?? 0;
    slot.set(k, i + 1);
    return { e, i };
  });

  // graph squares stack upward within a year
  const gSlot = new Map<number, number>();

  return (
    <div>
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full min-w-[640px]" role="group" aria-label="Evidence timeline in three lanes: genome counts by collection year, papers and graph findings by publication year">
          {/* lane rules + labels */}
          {(
            [
              ["genomes", "Genome counts", "by collection year", "var(--fg)"],
              ["papers", "Papers", "by publication year", "var(--gap)"],
              ["graph", "System graph", "by publication year", "var(--drug)"],
            ] as const
          ).map(([k, label, sub, color]) => (
            <g key={k}>
              <line x1={GUT} x2={W - RPAD} y1={LANES[k]} y2={LANES[k]} stroke="var(--line)" />
              <g transform={`translate(8 ${LANES[k] - 12})`} style={{ color }}>
                {k === "genomes" && <circle cx={5} cy={5} r={4.2} fill="none" stroke="currentColor" strokeWidth={1.8} />}
                {k === "papers" && <rect x={3.4} y={0} width={3.2} height={10.5} rx={1} fill="currentColor" />}
                {k === "graph" && <rect x={0.8} y={0.8} width={8.8} height={8.8} rx={1.5} fill="currentColor" />}
              </g>
              <text x={24} y={LANES[k] - 3} fontSize={12.5} fontWeight={600} fill="var(--fg)">
                {label}
              </text>
              <text x={24} y={LANES[k] + 11} fontSize={10} fill="var(--muted)" fontFamily="var(--font-mono)">
                {sub}
              </text>
            </g>
          ))}

          {/* year axis */}
          {ticks.map((t) => (
            <g key={t} aria-hidden>
              <line x1={x(t)} x2={x(t)} y1={14} y2={H - 22} stroke="var(--line)" strokeWidth={0.6} />
              <text x={x(t)} y={H - 6} textAnchor="middle" fontSize={10.5} fill="var(--muted)" fontFamily="var(--font-mono)">
                {t}
              </text>
            </g>
          ))}

          {/* years WHO's position changed: context, not alerts */}
          {p.whoYears
            .filter((w) => w.year >= y0 && w.year <= y1)
            .map((w, i) => (
              <g key={`${w.year}-${i}`} opacity={vis(w.year) ? 1 : 0.3} className={css.mark}>
                <line x1={x(w.year)} x2={x(w.year)} y1={14} y2={H - 22} stroke="var(--muted)" strokeWidth={1} strokeDasharray="1 3" />
                <text x={x(w.year)} y={10} textAnchor="middle" fontSize={9.5} fill="var(--muted)" fontFamily="var(--font-mono)">
                  WHO {w.year}
                </text>
                <title>{`${w.year}: ${w.label} (context, not an alert)`}</title>
              </g>
            ))}

          {/* genome lane: one circle per sampled year, radius = samples */}
          {p.cells.map((c) => {
            const ok = c.n >= p.minN;
            return (
              <circle
                key={c.year}
                cx={x(c.year)}
                cy={LANES.genomes}
                r={radiusFor(c.n) * 0.62}
                fill={ok ? "var(--fg)" : "var(--surface)"}
                fillOpacity={ok ? 0.8 : 1}
                stroke={ok ? "var(--surface)" : "var(--muted)"}
                strokeWidth={1.2}
                strokeDasharray={ok ? undefined : "2 1.6"}
                className={`${css.mark} ${vis(c.year) ? "" : css.markHidden}`}
              >
                <title>{`${p.country}, collected ${c.year}: ${c.x} of ${c.n}${ok ? "" : ` (under ${p.minN} samples)`}${p.cellNote?.(c.year) ? `. ${p.cellNote(c.year)}` : ""}`}</title>
              </circle>
            );
          })}

          {/* papers lane: all papers on the marker per year; darker part mentions this country */}
          {p.papers.map((d) => (
            <g key={d.year} className={`${css.mark} ${vis(d.year) ? "" : css.markHidden}`} style={{ transformOrigin: "bottom" }}>
              <rect x={x(d.year) - 3} y={LANES.papers - barH(d.total)} width={6} height={barH(d.total)} rx={1.5} fill="var(--gap)" opacity={0.28} />
              {d.inCountry > 0 ? (
                <rect x={x(d.year) - 3} y={LANES.papers - barH(d.inCountry)} width={6} height={barH(d.inCountry)} rx={1.5} fill="var(--gap)" />
              ) : null}
              <title>{`Published ${d.year}: ${d.total} paper${d.total === 1 ? "" : "s"} on the marker, ${d.inCountry} naming ${p.country}. Published molecular / clinical papers, each with its own design; not pooled.`}</title>
            </g>
          ))}

          {/* graph lane: one square per paper the graph has read / finding it holds */}
          {p.graph.map((g) => {
            const i = gSlot.get(g.year) ?? 0;
            gSlot.set(g.year, i + 1);
            return (
              <rect
                key={g.key}
                x={x(g.year) - 4}
                y={LANES.graph - 9 - i * 10}
                width={8}
                height={8}
                rx={1.5}
                fill={g.inCountry ? "var(--drug)" : "var(--surface)"}
                stroke="var(--drug)"
                strokeWidth={1.3}
                className={`${css.mark} ${vis(g.year) ? "" : css.markHidden}`}
              >
                <title>{g.label}</title>
              </rect>
            );
          })}

          {/* not-yet-published veil */}
          <rect
            x={x(p.replayYear) + 7}
            y={14}
            width={Math.max(0, W - RPAD - x(p.replayYear) - 7 + RPAD)}
            height={H - 36}
            fill="var(--bg)"
            opacity={0.55}
            pointerEvents="none"
          />

          {/* fired alerts, shaped by kind */}
          {placed.map(({ e, i }) => {
            const cy = LANES[e.source] - (e.source === "genomes" ? 20 : e.source === "papers" ? 44 : 0) + (e.source === "graph" ? 15 : 0);
            const cx = x(e.year) + i * 11;
            const sel = e.id === p.selectedId;
            return (
              <g
                key={e.id}
                transform={`translate(${cx} ${cy})`}
                className={`${css.mark} ${vis(e.year) ? "" : css.markHidden}`}
                style={{ color: "var(--signal)", cursor: "pointer", outline: "none" }}
                tabIndex={vis(e.year) ? 0 : -1}
                role="button"
                aria-label={`Alert, ${e.dateBasis === "collection" ? "collected" : "published"} ${e.year}. Press Enter to open.`}
                onClick={() => p.onSelect(e.id)}
                onKeyDown={(k) => {
                  if (k.key === "Enter" || k.key === " ") {
                    k.preventDefault();
                    p.onSelect(e.id);
                  }
                }}
              >
                {p.eventNote ? <title>{p.eventNote(e)}</title> : null}
                <circle r={11} fill="transparent" />
                {p.freshYear === e.year ? <circle className={css.pulse} r={6} /> : null}
                {sel ? <circle r={10} fill="none" stroke="var(--signal)" strokeWidth={1.4} /> : null}
                <KindMark kind={e.kind} direction={e.direction} r={5.5} />
              </g>
            );
          })}

          {/* playhead */}
          <g className={css.playhead} style={{ transform: `translateX(${x(p.replayYear) + 7}px)` }} pointerEvents="none">
            <line x1={0} x2={0} y1={12} y2={H - 22} stroke="var(--fg)" strokeWidth={1.4} />
            <path d="M-5 12 L5 12 L0 19 Z" fill="var(--fg)" />
          </g>
        </svg>
      </div>

      <div className="mt-1 flex items-center gap-3">
        <button
          type="button"
          onClick={p.onTogglePlay}
          className="inline-flex h-10 shrink-0 items-center gap-2 rounded-full bg-fg px-4 text-sm font-medium text-bg transition-transform active:scale-95"
          aria-pressed={p.playing}
        >
          <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden>
            {p.playing ? <path d="M2 1h3v10H2zM7 1h3v10H7z" fill="currentColor" /> : <path d="M2 1l9 5-9 5z" fill="currentColor" />}
          </svg>
          {p.playing ? "Pause" : p.replayYear >= y1 ? "Replay" : "Play"}
        </button>
        <label className="flex min-w-0 flex-1 items-center gap-3">
          <span className="sr-only">Replay year</span>
          <input
            type="range"
            className={css.scrub}
            min={y0}
            max={y1}
            step={1}
            value={p.replayYear}
            onChange={(e) => p.onReplayYear(Number(e.target.value))}
            aria-valuetext={`Showing what existed by ${p.replayYear}`}
          />
        </label>
        <output className="shrink-0 font-mono text-2xl font-semibold tabular-nums" aria-live="off">
          {p.replayYear}
        </output>
      </div>
    </div>
  );
}
