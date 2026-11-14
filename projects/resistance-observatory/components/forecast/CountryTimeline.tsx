"use client";

import { useState } from "react";
import { GENOME_MAX_YEAR, MAX_YEAR, POLICY_MILESTONES, alertsFor, genomeSnapshot, papersFor } from "@/lib/forecast/data";
import { countryName } from "@/lib/forecast/geo";
import type { AlertFeed } from "@/lib/forecast/types";

const W = 388;
const L = 34;
const R = 12;
const FS = 12;
const CAP = 6;
const SQ = 6; // square height incl. 1px gap

export function CountryTimeline(props: { iso3: string; asOfYear: number; alertFeed: AlertFeed; className?: string }): React.JSX.Element {
  const { iso3, asOfYear, alertFeed, className } = props;
  const [active, setActive] = useState<{ key: string; text: string } | null>(null);

  const genomes = genomeSnapshot(iso3, MAX_YEAR).years.filter((g) => g.tested > 0);
  const papers = papersFor(iso3).papers;
  const alerts = alertsFor(alertFeed, iso3);
  const who = POLICY_MILESTONES.items;

  const y0 = Math.min(1990, genomes[0]?.year ?? 1990, papers[0]?.year ?? 1990);
  const y1 = MAX_YEAR;
  const span = Math.max(1, y1 - y0);
  const x = (yr: number) => L + ((yr - y0) / span) * (W - L - R);
  const step = (W - L - R) / span;
  const sqW = Math.max(2, Math.min(6, step - 1.5));
  const bw = Math.max(2, Math.min(10, step * 0.7));
  const tickEvery = span > 40 ? 10 : 5;
  const firstTick = Math.ceil(y0 / tickEvery) * tickEvery;
  const ticks: number[] = [];
  for (let t = firstTick; t <= y1; t += tickEvery) ticks.push(t);

  const papersByYear = new Map<number, { n: number; read: number }>();
  for (const p of papers) {
    const e = papersByYear.get(p.year) ?? { n: 0, read: 0 };
    e.n += 1;
    if (p.readByGraph) e.read += 1;
    papersByYear.set(p.year, e);
  }

  // vertical layout: label above each track
  let yy = 16;
  const gLabelY = (yy += 14);
  const gTop = yy + 4;
  const gH = 32;
  const gBase = gTop + gH;
  yy = gBase + 8;
  const pLabelY = (yy += 14);
  const pTop = yy + 4;
  const pH = CAP * SQ + 2;
  const pBase = pTop + pH;
  yy = pBase + 6;
  const aLabelY = (yy += 14);
  const aTop = yy + 4;
  const aH = 16;
  yy = aTop + aH + 6;
  let wLabelY = 0;
  let wMid = 0;
  if (who.length > 0) {
    wLabelY = yy += 14;
    wMid = yy + 10;
    yy = wMid + 8;
  }
  const axisY = yy + 6;
  const H = axisY + 22;

  const dim = (yr: number) => (yr > asOfYear ? 0.4 : 1);
  const ring = (key: string, cx: number, cy: number, w: number, h: number) =>
    active?.key === key ? <rect x={cx - w / 2} y={cy - h / 2} width={w} height={h} rx={3} fill="none" className="stroke-fg" strokeWidth={1.5} /> : null;
  const markProps = (key: string, text: string) => ({
    role: "img" as const,
    "aria-label": text,
    onMouseEnter: () => setActive({ key, text }),
    onMouseLeave: () => setActive((a) => (a?.key === key ? null : a)),
    style: { cursor: "default" },
  });
  // One tab stop per track; arrow keys move between its marks.
  const trackProps = (name: string, marks: { key: string; text: string }[]) => ({
    tabIndex: 0,
    role: "group" as const,
    "aria-label": `${name} track, ${marks.length} mark${marks.length === 1 ? "" : "s"}. Use left and right arrow keys to move between marks.`,
    style: { outline: "none" },
    onFocus: () => {
      if (!marks.some((m) => m.key === active?.key)) setActive(marks[0] ?? null);
    },
    onBlur: () => setActive(null),
    onKeyDown: (e: React.KeyboardEvent) => {
      if (marks.length === 0) return;
      const i = Math.max(0, marks.findIndex((m) => m.key === active?.key));
      let n = i;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") n = Math.min(marks.length - 1, i + 1);
      else if (e.key === "ArrowLeft" || e.key === "ArrowUp") n = Math.max(0, i - 1);
      else if (e.key === "Home") n = 0;
      else if (e.key === "End") n = marks.length - 1;
      else return;
      e.preventDefault();
      setActive(marks[n]);
    },
  });
  const gMarks = genomes.map((g) => ({ key: `g${g.year}`, text: `${g.year} · genomes: ${g.withE} of ${g.tested} samples carry K540E` }));
  const pMarks = Array.from(papersByYear.entries()).map(([yr, e]) => ({ key: `p${yr}`, text: `${yr} · ${e.n} paper${e.n === 1 ? "" : "s"} (${e.read} read by the Graph)` }));
  const aMarks = alerts.map((a) => ({ key: `a${a.id}`, text: `${a.year} · alert: ${a.headline}` }));
  const wMarks = who.map((m, i) => ({ key: `w${i}`, text: `${m.year} · WHO document: ${m.text}` }));

  const cursorX = x(Math.min(y1, Math.max(y0, asOfYear))) + step / 2; // end of the as-of year
  const labelRight = cursorX > W - 70;

  return (
    <div className={className}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" className="block h-auto w-full" style={{ fontSize: FS }}>
        <title>{`Evidence timeline for ${countryName(iso3)}: marker K540E in pfdhps (sulfadoxine-pyrimethamine)`}</title>
        <desc>{`Tracks on one year axis from ${y0} to ${y1}: genome samples by collection year, papers by publication year, alerts by collection year${who.length > 0 ? ", and WHO documents" : ""}. Things recorded for the same years, each on its own clock. Coincidence in time, not cause.`}</desc>

        {/* Track 1: genomes */}
        <text x={0} y={gLabelY} className="fill-muted" fontSize={FS}>Genomes · collection year</text>
        <g {...trackProps("Genomes", gMarks)}>
        {genomes.length === 0 ? (
          <text x={L} y={gTop + gH / 2 + 4} className="fill-muted" fontSize={FS}>not sampled in this dataset</text>
        ) : (
          <>
            <text x={0} y={gTop + 9} className="fill-muted" fontSize={FS}>100%</text>
            <text x={0} y={gBase} className="fill-muted" fontSize={FS}>0%</text>
            <line x1={L} x2={W - R} y1={gBase + 0.5} y2={gBase + 0.5} className="stroke-line-strong" strokeWidth={1} />
            {genomes.map((g) => {
              const key = `g${g.year}`;
              const text = `${g.year} · genomes: ${g.withE} of ${g.tested} samples carry K540E`;
              const h = (g.withE / g.tested) * gH;
              const cx = x(g.year);
              return (
                <g key={key} opacity={dim(g.year)} {...markProps(key, text)}>
                  <rect x={cx - bw / 2 - 1} y={gTop - 2} width={bw + 2} height={gH + 4} fill="transparent" />
                  {g.withE > 0 ? (
                    <rect x={cx - bw / 2} y={gBase - Math.max(6, h)} width={bw} height={Math.max(6, h)} className="fill-drug" />
                  ) : (
                    <rect x={cx - bw / 2} y={gBase - 5} width={bw} height={4.5} fill="none" className="stroke-drug" strokeWidth={1.3} />
                  )}
                  {ring(key, cx, gTop + gH / 2, bw + 4, gH + 4)}
                </g>
              );
            })}
          </>
        )}
        </g>

        {/* Track 2: papers */}
        <text x={0} y={pLabelY} className="fill-muted" fontSize={FS}>Papers · publication year</text>
        <g {...trackProps("Papers", pMarks)}>
        {papersByYear.size === 0 ? (
          <text x={L} y={pTop + 14} className="fill-muted" fontSize={FS}>no paper in this list</text>
        ) : (
          Array.from(papersByYear.entries()).map(([yr, e]) => {
            const key = `p${yr}`;
            const text = `${yr} · ${e.n} paper${e.n === 1 ? "" : "s"} (${e.read} read by the Graph)`;
            const cx = x(yr);
            const shown = Math.min(CAP, e.n);
            return (
              <g key={key} opacity={dim(yr)} {...markProps(key, text)}>
                <rect x={cx - sqW / 2 - 1} y={pBase - (CAP + 1) * SQ - 4} width={sqW + 2} height={(CAP + 1) * SQ + 6} fill="transparent" />
                {Array.from({ length: shown }).map((_, i) => (
                  <rect
                    key={i}
                    x={cx - sqW / 2}
                    y={pBase - (i + 1) * SQ}
                    width={sqW}
                    height={SQ - 1}
                    className={i < e.read ? "fill-muted" : "stroke-muted"}
                    fill={i < e.read ? undefined : "none"}
                    strokeWidth={1}
                  />
                ))}
                {e.n > CAP ? (
                  <text x={cx} y={pBase - CAP * SQ - 2} textAnchor="middle" className="fill-muted" fontSize={FS}>+{e.n - CAP}</text>
                ) : null}
                {ring(key, cx, pBase - (shown * SQ) / 2, sqW + 4, shown * SQ + 2)}
              </g>
            );
          })
        )}
        </g>

        {/* Track 3: alerts */}
        <text x={0} y={aLabelY} className="fill-muted" fontSize={FS}>Alerts · collection year</text>
        <g {...trackProps("Alerts", aMarks)}>
        {alerts.length === 0 ? (
          <text x={L} y={aTop + 14} className="fill-muted" fontSize={FS}>no alert</text>
        ) : (
          alerts.map((a) => {
            const key = `a${a.id}`;
            const text = `${a.year} · alert: ${a.headline}`;
            const cx = x(a.year);
            return (
              <g key={key} opacity={dim(a.year)} {...markProps(key, text)} className="text-signal">
                <rect x={cx - 4} y={aTop - 2} width={16} height={aH + 4} fill="transparent" />
                <line x1={cx} x2={cx} y1={aTop} y2={aTop + aH} stroke="currentColor" strokeWidth={1.6} />
                <path d={`M${cx} ${aTop} L${cx + 10} ${aTop + 5} L${cx} ${aTop + 10} Z`} fill="currentColor" />
                {ring(key, cx + 4, aTop + aH / 2, 18, aH + 4)}
              </g>
            );
          })
        )}
        </g>

        {/* Track 4: WHO documents */}
        {who.length > 0 ? (
          <>
            <text x={0} y={wLabelY} className="fill-muted" fontSize={FS}>WHO documents</text>
            <g {...trackProps("WHO documents", wMarks)}>
            {who.map((m, i) => {
              const key = `w${i}`;
              const text = `${m.year} · WHO document: ${m.text}`;
              const cx = x(m.year);
              return (
                <g key={key} opacity={dim(m.year)} {...markProps(key, text)}>
                  <rect x={cx - 8} y={wMid - 8} width={16} height={16} fill="transparent" />
                  <path d={`M${cx} ${wMid - 6} L${cx + 6} ${wMid} L${cx} ${wMid + 6} L${cx - 6} ${wMid} Z`} className="fill-fg" />
                  {ring(key, cx, wMid, 18, 18)}
                </g>
              );
            })}
            </g>
          </>
        ) : null}

        {/* axis */}
        <line x1={L} x2={W - R} y1={axisY} y2={axisY} className="stroke-line-strong" strokeWidth={1} />
        {ticks.map((t) => (
          <g key={t}>
            <line x1={x(t)} x2={x(t)} y1={axisY} y2={axisY + 4} className="stroke-line-strong" strokeWidth={1} />
            <text x={x(t)} y={axisY + 16} textAnchor="middle" className="fill-muted tabular-nums" fontSize={FS}>{t}</text>
          </g>
        ))}

        {/* as-of cursor */}
        <line x1={cursorX} x2={cursorX} y1={14} y2={axisY} className="stroke-fg" strokeWidth={1.2} strokeDasharray="3 3" />
        <text x={cursorX + (labelRight ? -4 : 4)} y={11} textAnchor={labelRight ? "end" : "start"} className="fill-fg tabular-nums" fontSize={FS}>
          as of {asOfYear}
        </text>
      </svg>

      <p className="mt-1 min-h-[1.5rem] text-xs leading-snug text-fg" aria-live="polite">
        {active ? active.text : <span className="text-muted">Hover or focus a mark for its exact values.</span>}
      </p>
      <p className="mt-1 text-xs leading-snug text-muted">
        <span aria-hidden>■</span> year with K540E carriers (height = share of samples, minimum height shown) · <span aria-hidden>□</span> year tested, none found · blank = not sampled
        <br />
        Papers: <span aria-hidden>■</span> read by the Graph · <span aria-hidden>□</span> not read
      </p>
      <p className="mt-1 text-xs leading-snug text-muted">
        Things recorded for the same years, each on its own clock. Coincidence in time, not cause.
        {asOfYear > GENOME_MAX_YEAR ? ` Genome data end in ${GENOME_MAX_YEAR}.` : ""}
        {asOfYear < y1 ? ` Marks after ${asOfYear} are dimmed.` : ""}
      </p>

      {who.length > 0 ? (
        <details className="mt-1 text-xs leading-snug text-muted">
          <summary className="cursor-pointer text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-drug">WHO documents ({who.length})</summary>
          <p className="mt-1">WHO documents, as summarised in the Alert tab&apos;s data pack. They are not specific to this country.</p>
          <ul className="mt-1 space-y-1">
            {who.map((m, i) => (
              <li key={i} className="tabular-nums">
                {m.year}: {m.text}{" "}
                <a href={m.url} target="_blank" rel="noopener noreferrer" className="text-drug underline underline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-drug">
                  source ↗<span className="sr-only"> (opens in a new tab)</span>
                </a>
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  );
}
