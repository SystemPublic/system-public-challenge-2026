"use client";

// Side-by-side UHF42 choropleths for the selected bridge pair: the X measure
// on a blue sequential ramp, the Y measure on an orange one. Quantile bins
// (the EHDP distributions are skewed); hollow = no district value (typically
// a suppressed observation). Hover any district for value + vintage; the
// table view repeats every value without hover.

import { useMemo, useRef, useState } from "react";
import type { District, DistrictValue, MeasureDict } from "@/lib/bundle";

const PAD = 10;
const VW = 470;
const VH = 430;
const NBINS = 7;

// dark surface: the anchor flips — low values recede toward the dark paper
const BLUE_RAMP = [
  "#0d366b", "#104281", "#184f95", "#1c5cab", "#256abf", "#2a78d6",
  "#3987e5", "#5598e7", "#6da7ec", "#86b6ef", "#9ec5f4", "#b7d3f6", "#cde2fb",
];
const ORANGE_RAMP = [
  "#5f2005", "#722a0b", "#853311", "#983d18", "#ac481f", "#c15226",
  "#d55d2d", "#eb6834", "#f77b4c", "#ff8d62", "#ffa078", "#ffb28c", "#ffc4a1",
];

const rampAt = (ramp: string[], t: number) =>
  ramp[Math.round(t * (ramp.length - 1))];

export function fmtVal(v: number, mt: string): string {
  const s =
    Math.abs(v) >= 1000
      ? Math.round(v).toLocaleString("en-US")
      : String(Math.round(v * 10) / 10);
  return mt === "Percent" ? `${s}%` : s;
}

type Bin = { lo: number; hi: number; color: string; count: number };

function binValues(recs: DistrictValue[], ramp: string[]): Bin[] {
  const vs = recs.map((r) => r.v).sort((a, b) => a - b);
  const edges: number[] = [];
  for (let i = 1; i < NBINS; i++) {
    const q = vs[Math.floor((i / NBINS) * vs.length)];
    if (q !== edges[edges.length - 1]) edges.push(q);
  }
  const cuts = [vs[0], ...edges, vs[vs.length - 1]];
  const bins: Bin[] = [];
  const n = cuts.length - 1;
  for (let i = 0; i < n; i++) {
    bins.push({
      lo: cuts[i],
      hi: cuts[i + 1],
      color: rampAt(ramp, n === 1 ? 1 : (i + 0.5) / n),
      count: 0,
    });
  }
  for (const r of recs) {
    let i = bins.findIndex((b) => r.v <= b.hi);
    if (i === -1) i = bins.length - 1;
    bins[i].count++;
  }
  return bins;
}

function MapPanel({
  side,
  label,
  measureId,
  districts,
  recs,
  ramp,
  measures,
}: {
  side: "x" | "y";
  label: string;
  measureId: string;
  districts: District[];
  recs: Record<string, DistrictValue>;
  ramp: string[];
  measures: MeasureDict;
}) {
  const meta = measures[measureId];
  const bins = useMemo(
    () => binValues(Object.values(recs), ramp),
    [recs, ramp],
  );
  const [hover, setHover] = useState<{
    x: number;
    y: number;
    lines: { v?: string; sub?: string }[];
  } | null>(null);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  const { paths } = useMemo(() => {
    let minLon = 1e9, maxLon = -1e9, minLat = 1e9, maxLat = -1e9;
    for (const d of districts) {
      for (const poly of d.polys) {
        for (const ring of poly) {
          for (const pt of ring) {
            minLon = Math.min(minLon, pt[0]);
            maxLon = Math.max(maxLon, pt[0]);
            minLat = Math.min(minLat, pt[1]);
            maxLat = Math.max(maxLat, pt[1]);
          }
        }
      }
    }
    const latMid = (minLat + maxLat) / 2;
    const kx = Math.cos((latMid * Math.PI) / 180);
    const sx = (VW - 2 * PAD) / ((maxLon - minLon) * kx);
    const sy = (VH - 2 * PAD) / (maxLat - minLat);
    const s = Math.min(sx, sy);
    const ox = (VW - (maxLon - minLon) * kx * s) / 2;
    const oy = (VH - (maxLat - minLat) * s) / 2;
    const proj = (pt: [number, number]) =>
      [ox + (pt[0] - minLon) * kx * s, oy + (maxLat - pt[1]) * s] as const;

    const ringPath = (ring: number[][]) => {
      const pts = ring.map((p) => proj([p[0], p[1]]));
      return (
        `M ${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)} ` +
        pts.slice(1).map((p) => `L ${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ") +
        " Z"
      );
    };
    const paths = districts.map((d) => ({
      d,
      path: d.polys
        .map((poly) => poly.map((ring) => ringPath(ring)).join(" "))
        .join(" "),
    }));
    return { paths };
  }, [districts]);

  const colorFor = (v: number) => {
    const i = bins.findIndex((b) => v <= b.hi);
    return bins[i === -1 ? bins.length - 1 : i].color;
  };

  const showTip = (ev: React.PointerEvent, lines: { v?: string; sub?: string }[]) => {
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect) return;
    setHover({
      x: ev.clientX - rect.left,
      y: ev.clientY - rect.top,
      lines,
    });
  };

  return (
    <div>
      <h3 className="font-sans text-[0.8rem] font-semibold">
        {side === "x" ? "X" : "Y"}: {label}
      </h3>
      <p className="font-sans text-[0.7rem] text-muted">
        {meta?.coll ? `${meta.coll} · ` : ""}
        {meta?.mt ? `${meta.mt} · ` : ""}
        {meta?.yr || "vintage n/a"}
        {meta?.mod ? " · modeled attribution" : ""}
      </p>
      <div ref={wrapRef} className="relative mt-2">
        <svg
          viewBox={`0 0 ${VW} ${VH}`}
          className="w-full h-auto touch-none"
          role="img"
          aria-label={`Choropleth of ${label} across 42 NYC UHF districts`}
        >
          {paths.map(({ d, path }) => {
            const rec = recs[d.id];
            const fill = rec ? colorFor(rec.v) : "var(--div-mid)";
            const isHover = hoverId === d.id;
            return (
              <path
                key={d.id}
                d={path}
                fill={fill}
                fillRule="evenodd"
                stroke={isHover ? "var(--ink)" : "var(--paper)"}
                strokeWidth={isHover ? 1.6 : 1.1}
                onPointerMove={(ev) => {
                  setHoverId(d.id);
                  showTip(ev, [
                    { v: `${d.name} · ${d.id.replace("UHF42:", "")}` },
                    ...(rec
                      ? [
                          {
                            v: `${fmtVal(rec.v, meta?.mt ?? "")}`,
                          },
                          { sub: `vintage ${rec.tp || "n/a"}` },
                          ...(rec.rel && rec.rel !== "ok"
                            ? [{ sub: `reliability: ${rec.rel}` }]
                            : []),
                        ]
                      : [{ sub: "no district value (typically suppressed)" }]),
                  ]);
                }}
                onPointerLeave={() => {
                  setHoverId(null);
                  setHover(null);
                }}
              />
            );
          })}
        </svg>
        {hover && (
          <div className="viz-tip" style={{ left: hover.x, top: hover.y }} role="status">
            {hover.lines.map((l, i) =>
              l.v !== undefined ? (
                <div key={i} className="v">
                  {l.v}
                </div>
              ) : (
                <div key={i} className="sub">
                  {l.sub}
                </div>
              ),
            )}
          </div>
        )}
      </div>

      {/* legend */}
      <div className="mt-2">
        <div className="flex h-3 overflow-hidden rounded-[3px]">
          {bins.map((b, i) => (
            <span
              key={i}
              className="flex-1"
              style={{ background: b.color }}
              title={`${fmtVal(b.lo, meta?.mt ?? "")} – ${fmtVal(b.hi, meta?.mt ?? "")}`}
            />
          ))}
        </div>
        <div className="mt-1 flex justify-between font-sans text-[0.65rem] text-muted">
          <span>{bins.length ? fmtVal(bins[0].lo, meta?.mt ?? "") : ""}</span>
          <span>quantile bins, n = {Object.keys(recs).length}</span>
          <span>
            {bins.length ? fmtVal(bins[bins.length - 1].hi, meta?.mt ?? "") : ""}
          </span>
        </div>
      </div>
    </div>
  );
}

export function DistrictMaps({
  districts,
  values,
  xMeasure,
  yMeasure,
  measures,
  rho,
}: {
  districts: District[];
  values: Record<string, Record<string, DistrictValue>>;
  xMeasure: string;
  yMeasure: string;
  measures: MeasureDict;
  /** the Spearman ρ the two maps summarize (shown under the maps) */
  rho: number;
}) {
  // bundle ids carry the ehdp: prefix; districts.json uses Underlay ids
  const bare = (mid: string) => mid.replace(/^ehdp:/, "");
  const xRecs = values[bare(xMeasure)] ?? {};
  const yRecs = values[bare(yMeasure)] ?? {};
  const xLabel = measures[xMeasure]?.l ?? xMeasure;
  const yLabel = measures[yMeasure]?.l ?? yMeasure;

  return (
    <div className="mt-4">
      <div className="grid grid-cols-1 gap-10 md:grid-cols-2 md:gap-8">
        <MapPanel
          side="x"
          label={xLabel}
          measureId={xMeasure}
          districts={districts}
          recs={xRecs}
          ramp={BLUE_RAMP}
          measures={measures}
        />
        <MapPanel
          side="y"
          label={yLabel}
          measureId={yMeasure}
          districts={districts}
          recs={yRecs}
          ramp={ORANGE_RAMP}
          measures={measures}
        />
      </div>
      <p className="mt-3 font-sans text-[0.7rem] text-muted">
        The two maps use their own scales (blue = X, orange = Y). Spearman ρ ={" "}
        <span className={rho >= 0 ? "text-[#2a78d6]" : "text-[#e34948]"}>
          {(rho > 0 ? "+" : "") + rho.toFixed(3)}
        </span>{" "}
        across the 42 districts: computed on these same values (first observation
        per district), cross-sectional and unadjusted.
      </p>

      {/* table view — every value reachable without hover */}
      <details className="mt-4">
        <summary className="cursor-pointer font-sans text-[0.75rem] text-muted hover:text-ink">
          district values (table view)
        </summary>
        <div className="mt-3 overflow-x-auto">
          <table className="dash-table">
            <thead>
              <tr>
                <th>district</th>
                <th className="num">{xLabel}</th>
                <th className="num">{yLabel}</th>
              </tr>
            </thead>
            <tbody>
              {districts.map((d) => {
                const xr = xRecs[d.id];
                const yr = yRecs[d.id];
                return (
                  <tr key={d.id}>
                    <td>{d.name}</td>
                    <td className="num">
                      {xr ? (
                        <>
                          {fmtVal(xr.v, measures[xMeasure]?.mt ?? "")}
                          <span className="dom-note">{xr.tp}</span>
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="num">
                      {yr ? (
                        <>
                          {fmtVal(yr.v, measures[yMeasure]?.mt ?? "")}
                          <span className="dom-note">{yr.tp}</span>
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
