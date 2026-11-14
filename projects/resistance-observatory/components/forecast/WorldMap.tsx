"use client";

import {
  memo,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { WORLD, COUNTRY_BY_ISO3, type GeoCountry } from "@/lib/forecast/geo";
import {
  GENOME,
  alertsFor,
  allGenomeSnapshots,
  genomeChangesInYear,
  genomeSnapshot,
  graphCountsByCountry,
  papersCountsByCountry,
} from "@/lib/forecast/data";
import type { AlertFeed, AlertRecord, GenomeSnapshot } from "@/lib/forecast/types";
import {
  AMBER,
  DETECTED_DOT,
  alertCountText,
  mapLabel,
  PAPER_READ_FILL,
  PAPER_SOURCE_LINE,
  paperLabelSuffix,
  paperRampColor,
  type MapLayer,
  HATCH_BG,
  HATCH_LINE,
  HATCH_PATTERN_ID,
  LAND_NOT_SAMPLED,
  STATE_LABEL,
  fillFor,
  stateOf,
} from "@/lib/forecast/encoding";

/** View in projected units: centre and width; height follows the container aspect. */
type View = { cx: number; cy: number; w: number };
type Size = { cw: number; ch: number };

const MAX_ZOOM = 40;
const MIN_FLY_WIDTH = 45;
const FLY_MS = 1100;

const GENOME_ISO3 = new Set(GENOME.countries.map((c) => c.iso3));
const INTERACTIVE_ISO3 = (() => {
  const s = new Set(GENOME_ISO3);
  const g = graphCountsByCountry();
  for (const [iso3, c] of Object.entries(g)) if (c && (c.sp > 0 || c.codon540 > 0)) s.add(iso3);
  for (const iso3 of Object.keys(papersCountsByCountry())) s.add(iso3);
  return s;
})();

function reducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function worldWidth({ cw, ch }: Size): number {
  return Math.max(WORLD.width, (WORLD.height * cw) / ch) * 1.02;
}

function clampView(v: View, size: Size, loose = false): View {
  const ww = worldWidth(size);
  const w = Math.min(ww, Math.max(WORLD.width / MAX_ZOOM, v.w));
  const h = (w * size.ch) / size.cw;
  const slackX = loose ? w * 0.45 : 0;
  const slackY = loose ? h * 0.45 : 0;
  const clampAxis = (c: number, span: number, total: number, slack: number) => {
    if (span >= total) return total / 2 + Math.max(-slack, Math.min(slack, c - total / 2));
    return Math.min(total - span / 2 + slack, Math.max(span / 2 - slack, c));
  };
  return {
    w,
    cx: clampAxis(v.cx, w, WORLD.width, slackX),
    cy: clampAxis(v.cy, h, WORLD.height, slackY),
  };
}

function worldView(size: Size): View {
  return { cx: WORLD.width / 2, cy: WORLD.height / 2, w: worldWidth(size) };
}

/** Fit a country's bbox into the part of the map not covered by the panel. */
function targetView(
  c: GeoCountry,
  size: Size,
  panelPx: number,
  leftPx = 0,
  topPx = 0,
  bottomPx = 0,
): View {
  const [x0, y0, x1, y1] = c.bbox;
  if (size.cw - panelPx - leftPx < 320) leftPx = 0;
  if (size.ch - topPx - bottomPx < 220) topPx = bottomPx = 0;
  const usableV = (size.ch - topPx - bottomPx) / size.ch;
  const usable = Math.max(0.35, (size.cw - panelPx - leftPx) / size.cw);
  const pad = 2.4;
  const bw = Math.max(1, x1 - x0) * pad;
  const bh = Math.max(1, y1 - y0) * pad;
  let w = Math.max(bw / usable, (bh * size.cw) / (size.ch * usableV), MIN_FLY_WIDTH);
  w = Math.min(w, worldWidth(size));
  const bcx = (x0 + x1) / 2;
  const bcy = (y0 + y1) / 2;
  const visibleCentrePx = leftPx + (size.cw - panelPx - leftPx) / 2;
  const left = bcx - visibleCentrePx * (w / size.cw);
  const h = (w * size.ch) / size.cw;
  const visibleMiddlePx = topPx + (size.ch - topPx - bottomPx) / 2;
  const top = bcy - visibleMiddlePx * (h / size.ch);
  return clampView({ cx: left + w / 2, cy: top + h / 2, w }, size, true);
}

const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

// ---------------------------------------------------------------------------

const CountryPaths = memo(function CountryPaths({
  fills,
  states,
  selected,
}: {
  fills: Record<string, string>;
  states: Record<string, string>;
  selected: string | null;
}) {
  return (
    <g>
      {WORLD.countries.map((c) => {
        const focusable = INTERACTIVE_ISO3.has(c.iso3);
        return (
          <path
            key={c.iso3}
            d={c.d}
            data-iso3={c.iso3}
            fill={fills[c.iso3] ?? LAND_NOT_SAMPLED}
            className={`fc-country is-interactive${selected === c.iso3 ? " is-selected" : ""}`}
            tabIndex={focusable ? 0 : undefined}
            role={focusable ? "button" : undefined}
            aria-label={focusable ? `${c.name}: ${states[c.iso3]}` : undefined}
            aria-pressed={focusable ? selected === c.iso3 : undefined}
          />
        );
      })}
    </g>
  );
});

export function WorldMap({
  asOfYear,
  selected,
  flyKey,
  panelPx,
  leftPx,
  alertFeed,
  layer = "genome",
  topPx = 0,
  bottomPx = 0,
  onSelect,
}: {
  /** Screen px at the top (time control) and bottom (legend strip) that the fly-to keeps clear. */
  topPx?: number;
  bottomPx?: number;
  asOfYear: number;
  layer?: MapLayer;
  /** Width in px of the left column of cards (the map centres countries right of it). */
  leftPx: number;
  alertFeed: AlertFeed;
  selected: string | null;
  /** Bump to re-fly to the same country (e.g. a repeated search). */
  flyKey: number;
  /** Width in px of the panel covering the right side of the map (0 when closed). */
  panelPx: number;
  onSelect: (iso3: string) => void;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [size, setSize] = useState<Size | null>(null);
  const [view, setView] = useState<View | null>(null);
  const viewRef = useRef<View | null>(null);
  viewRef.current = view;
  const sizeRef = useRef<Size | null>(null);
  sizeRef.current = size;
  const animRef = useRef<number | null>(null);
  const positionedRef = useRef(false);
  const lastFlyRef = useRef<string>("");

  const [hover, setHover] = useState<{ iso3: string; x: number; y: number } | null>(null);
  const [dragging, setDragging] = useState(false);
  const dragRef = useRef<{ x: number; y: number; view: View; moved: boolean; id: number } | null>(null);
  const suppressClickRef = useRef(false);

  const snapshots = useMemo(() => allGenomeSnapshots(asOfYear), [asOfYear]);
  const isPapers = layer === "papers";
  const paperCounts = useMemo(() => papersCountsByCountry(asOfYear), [asOfYear]);
  const paperMax = useMemo(
    () => Object.values(paperCounts).reduce((m, r) => Math.max(m, r.total), 0),
    [paperCounts],
  );
  // One fill and one state phrase per country for the active layer only.
  const { fills, states } = useMemo(() => {
    const fills: Record<string, string> = {};
    const states: Record<string, string> = {};
    for (const c of WORLD.countries) {
      if (isPapers) {
        const r = paperCounts[c.iso3];
        fills[c.iso3] = r && r.total > 0 ? paperRampColor(r.total, paperMax) : LAND_NOT_SAMPLED;
        states[c.iso3] = r && r.total > 0
          ? `${r.total} K540E papers through ${asOfYear}, the Graph has read ${r.readByGraph}`
          : `no K540E paper in the list through ${asOfYear}`;
      } else {
        const sn = snapshots[c.iso3];
        fills[c.iso3] = fillFor(sn);
        states[c.iso3] = STATE_LABEL[stateOf(sn)];
      }
    }
    return { fills, states };
  }, [isPapers, paperCounts, paperMax, snapshots, asOfYear]);
  const changed = useMemo(
    () => new Set(genomeChangesInYear(asOfYear).map((c) => c.iso3)),
    [asOfYear],
  );
  const alertsByIso3 = useMemo(() => {
    const out: Record<string, AlertRecord[]> = {};
    for (const iso3 of new Set(alertFeed.alerts.map((a) => a.country_iso3))) {
      const list = alertsFor(alertFeed, iso3, asOfYear);
      if (list.length) out[iso3] = list;
    }
    return out;
  }, [alertFeed, asOfYear]);

  // Screen rectangles (relative to the map) that labels must not fall under:
  // the left column, the time control, the zoom buttons and the panel.
  const [avoid, setAvoid] = useState<{ l: number; t: number; r: number; b: number }[]>([]);
  useEffect(() => {
    const measure = () => {
      const wrap = wrapRef.current;
      const stage = wrap?.parentElement;
      if (!wrap || !stage) return;
      const w = wrap.getBoundingClientRect();
      setAvoid(
        [...stage.querySelectorAll("[data-fc-avoid]")].map((el) => {
          const r = el.getBoundingClientRect();
          return { l: r.left - w.left, t: r.top - w.top, r: r.right - w.left, b: r.bottom - w.top };
        }),
      );
    };
    measure();
    const t = setTimeout(measure, 450);
    return () => clearTimeout(t);
  }, [size, panelPx, selected]);

  // Measure the container.
  useLayoutEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const measure = () => {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) setSize({ cw: r.width, ch: r.height });
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const stopAnim = () => {
    if (animRef.current !== null) cancelAnimationFrame(animRef.current);
    animRef.current = null;
  };

  const flyTo = useCallback((target: View, ms = FLY_MS) => {
    stopAnim();
    const from = viewRef.current;
    if (!from || reducedMotion() || ms <= 0) {
      setView(target);
      return;
    }
    const lw0 = Math.log(from.w);
    const lw1 = Math.log(target.w);
    const dist = Math.hypot(target.cx - from.cx, target.cy - from.cy);
    const span = Math.max(from.w, target.w);
    // Zoom out a little mid-flight when the hop is long relative to the view.
    const bump = dist > span * 0.6 ? Math.log(1 + Math.min(1.2, dist / span) * 0.6) : 0;
    const t0 = performance.now();
    const step = (now: number) => {
      const t = Math.min(1, (now - t0) / ms);
      const e = ease(t);
      setView({
        cx: from.cx + (target.cx - from.cx) * e,
        cy: from.cy + (target.cy - from.cy) * e,
        w: Math.exp(lw0 + (lw1 - lw0) * e + bump * Math.sin(Math.PI * t)),
      });
      animRef.current = t < 1 ? requestAnimationFrame(step) : null;
    };
    animRef.current = requestAnimationFrame(step);
  }, []);

  // First positioning and fly-to on selection change.
  useEffect(() => {
    if (!size) return;
    const c = selected ? COUNTRY_BY_ISO3[selected] : undefined;
    if (!positionedRef.current || !viewRef.current) {
      positionedRef.current = true;
      lastFlyRef.current = `${selected}|${flyKey}`;
      setView(c ? targetView(c, size, panelPx, leftPx, topPx, bottomPx) : worldView(size));
      return;
    }
    const key = `${selected}|${flyKey}`;
    if (key === lastFlyRef.current) return;
    lastFlyRef.current = key;
    if (c) flyTo(targetView(c, size, panelPx, leftPx, topPx, bottomPx));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, flyKey, size !== null]);

  // Keep the view valid when the container resizes.
  useEffect(() => {
    if (!size || !viewRef.current || animRef.current !== null) return;
    setView((v) => (v ? clampView(v, size, true) : v));
  }, [size]);

  useEffect(() => () => stopAnim(), []);

  // Wheel zoom about the cursor (non-passive so the page does not scroll).
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const onWheel = (e: WheelEvent) => {
      const v = viewRef.current;
      const s = sizeRef.current;
      if (!v || !s) return;
      e.preventDefault();
      stopAnim();
      const r = svg.getBoundingClientRect();
      const px = e.clientX - r.left;
      const py = e.clientY - r.top;
      const h = (v.w * s.ch) / s.cw;
      const ptx = v.cx - v.w / 2 + (px / s.cw) * v.w;
      const pty = v.cy - h / 2 + (py / s.ch) * h;
      const factor = Math.exp(Math.max(-1, Math.min(1, e.deltaY * 0.0022)));
      const nw = Math.min(worldWidth(s), Math.max(WORLD.width / MAX_ZOOM, v.w * factor));
      const nh = (nw * s.ch) / s.cw;
      const left = ptx - (px / s.cw) * nw;
      const top = pty - (py / s.ch) * nh;
      setView(clampView({ cx: left + nw / 2, cy: top + nh / 2, w: nw }, s, true));
    };
    svg.addEventListener("wheel", onWheel, { passive: false });
    return () => svg.removeEventListener("wheel", onWheel);
  }, [view !== null]); // eslint-disable-line react-hooks/exhaustive-deps

  const onPointerDown = (e: ReactPointerEvent<SVGSVGElement>) => {
    if (e.button !== 0 || !viewRef.current) return;
    dragRef.current = { x: e.clientX, y: e.clientY, view: viewRef.current, moved: false, id: e.pointerId };
  };
  const onPointerMove = (e: ReactPointerEvent<SVGSVGElement>) => {
    const d = dragRef.current;
    const s = sizeRef.current;
    if (d && s) {
      const dx = e.clientX - d.x;
      const dy = e.clientY - d.y;
      if (!d.moved && Math.hypot(dx, dy) > 4) {
        d.moved = true;
        stopAnim();
        setDragging(true);
        setHover(null);
        try {
          svgRef.current?.setPointerCapture(d.id);
        } catch {}
      }
      if (d.moved) {
        const k = d.view.w / s.cw;
        setView(clampView({ cx: d.view.cx - dx * k, cy: d.view.cy - dy * k, w: d.view.w }, s, true));
        return;
      }
    }
    const target = (e.target as Element).closest?.("[data-iso3]") as Element | null;
    const wrap = wrapRef.current?.getBoundingClientRect();
    if (target && wrap) {
      setHover({ iso3: target.getAttribute("data-iso3")!, x: e.clientX - wrap.left, y: e.clientY - wrap.top });
    } else if (hover) setHover(null);
  };
  const endDrag = () => {
    const d = dragRef.current;
    dragRef.current = null;
    if (d?.moved) {
      suppressClickRef.current = true;
      setDragging(false);
      setTimeout(() => (suppressClickRef.current = false), 0);
    }
  };
  const onClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (suppressClickRef.current) return;
    const target = (e.target as Element).closest?.("[data-iso3]");
    const iso3 = target?.getAttribute("data-iso3");
    if (iso3) onSelect(iso3);
  };
  const onKeyDown = (e: ReactKeyboardEvent<SVGSVGElement>) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const iso3 = (e.target as Element).getAttribute?.("data-iso3");
    if (iso3) {
      e.preventDefault();
      onSelect(iso3);
    }
  };
  const projToPx = (x: number, y: number) => {
    const v = viewRef.current;
    const s = sizeRef.current;
    if (!v || !s) return { x: 0, y: 0 };
    const h = (v.w * s.ch) / s.cw;
    return { x: ((x - (v.cx - v.w / 2)) / v.w) * s.cw, y: ((y - (v.cy - h / 2)) / h) * s.ch };
  };
  const onFocus = (e: React.FocusEvent<SVGSVGElement>) => {
    const iso3 = (e.target as Element).getAttribute?.("data-iso3");
    const c = iso3 ? COUNTRY_BY_ISO3[iso3] : undefined;
    if (c) setHover({ iso3: c.iso3, ...projToPx(c.center[0], c.center[1]) });
  };

  const zoomBy = (factor: number) => {
    const v = viewRef.current;
    const s = sizeRef.current;
    if (!v || !s) return;
    flyTo(clampView({ ...v, w: v.w / factor }, s, true), 350);
  };
  const resetWorld = () => {
    const s = sizeRef.current;
    if (s) flyTo(worldView(s), 700);
  };

  const zoom = view && size ? worldWidth(size) / view.w : 1;
  const unit = view && size ? view.w / size.cw : 1; // projected units per screen px
  const vb =
    view && size
      ? `${view.cx - view.w / 2} ${view.cy - (view.w * size.ch) / size.cw / 2} ${view.w} ${(view.w * size.ch) / size.cw}`
      : `0 0 ${WORLD.width} ${WORLD.height}`;
  const sel = selected ? COUNTRY_BY_ISO3[selected] : undefined;

  // Markers (constant on-screen size) for sampled states and tiny countries.
  const markers = WORLD.countries.map((c) => {
    if (isPapers) {
      const r = paperCounts[c.iso3];
      const [x, y] = c.center;
      if (!r || r.total <= 0) {
        return c.tiny ? (
          <circle key={c.iso3} data-iso3={c.iso3} className="fc-marker is-interactive" cx={x} cy={y} r={2.2 * unit} fill={LAND_NOT_SAMPLED} stroke="#1d3f58" strokeWidth={1} />
        ) : null;
      }
      const read = r.readByGraph > 0;
      const half = (read ? 6 : 4.5) * unit;
      return (
        <rect
          key={c.iso3}
          data-iso3={c.iso3}
          className="fc-marker is-interactive"
          x={x - half}
          y={y - half}
          width={half * 2}
          height={half * 2}
          fill={read ? PAPER_READ_FILL : "#050d17"}
          stroke={read ? "#050d17" : "#f5f4ef"}
          strokeWidth={read ? 1.25 : 1.6}
        />
      );
    }
    const s = snapshots[c.iso3];
    const st = stateOf(s);
    const [x, y] = c.center;
    if (st === "detected") {
      return (
        <circle
          key={c.iso3}
          data-iso3={c.iso3}
          className="fc-marker is-interactive"
          cx={x}
          cy={y}
          r={5 * unit}
          fill={DETECTED_DOT}
          stroke="#050d17"
          strokeWidth={1.75}
        />
      );
    }
    if (st === "tested_not_detected") {
      return (
        <circle
          key={c.iso3}
          data-iso3={c.iso3}
          className="fc-marker is-interactive"
          cx={x}
          cy={y}
          r={4.5 * unit}
          fill="#050d17"
          stroke="#f5f4ef"
          strokeWidth={1.6}
        />
      );
    }
    if (c.tiny) {
      return (
        <circle
          key={c.iso3}
          data-iso3={c.iso3}
          className="fc-marker is-interactive"
          cx={x}
          cy={y}
          r={2.2 * unit}
          fill={LAND_NOT_SAMPLED}
          stroke="#1d3f58"
          strokeWidth={1}
        />
      );
    }
    return null;
  });

  // Amber rings: "changed this year" around the state marker (first genomes
  // sampled, or first detection in our data). Keyed by year so the pulse
  // replays on each step and then stays.
  const changedRings = (isPapers ? [] : [...changed]).map((iso3) => {
    const c = COUNTRY_BY_ISO3[iso3];
    if (!c) return null;
    return (
      <g key={`${iso3}-${asOfYear}`} transform={`translate(${c.center[0]} ${c.center[1]}) scale(${unit})`} pointerEvents="none">
        <circle className="fc-pulse" r={9.5} fill="none" stroke={AMBER} strokeWidth={1.9} />
      </g>
    );
  });

  // Alert flags: a pennant on a pole, offset up-right of the state marker.
  const placeholderFeed = alertFeed.placeholder;
  // Spread flags whose screen boxes overlap: try offsets on a short arc
  // around the country's own marker; a leader line ties a moved flag to it.
  const FLAG_OFFSETS: [number, number][] = [
    [8, -3], [-22, -8], [10, -26], [-22, -30], [32, -16], [10, -48], [-24, -52],
  ];
  const flagOffset: Record<string, [number, number]> = {};
  if (!isPapers && view && size) {
    const placedFlags: { l: number; t: number; r: number; b: number }[] = [];
    const entries = Object.entries(alertsByIso3)
      .map(([iso3, list]) => ({ iso3, n: list.length, c: COUNTRY_BY_ISO3[iso3] }))
      .filter((e) => e.c)
      .sort((a, b) => a.c!.center[1] - b.c!.center[1] || a.c!.center[0] - b.c!.center[0]);
    for (const e of entries) {
      const p = projToPx(e.c!.center[0], e.c!.center[1]);
      let chosen = FLAG_OFFSETS[0];
      for (const off of FLAG_OFFSETS) {
        const box = { l: p.x + off[0] - 5, r: p.x + off[0] + (e.n > 1 ? 25 : 17), t: p.y + off[1] - 24, b: p.y + off[1] + 3 };
        if (!placedFlags.some((a) => box.l < a.r && box.r > a.l && box.t < a.b && box.b > a.t)) {
          chosen = off;
          placedFlags.push(box);
          break;
        }
      }
      flagOffset[e.iso3] = chosen;
    }
  }
  const flags = (isPapers ? [] : Object.entries(alertsByIso3)).map(([iso3, list]) => {
    const c = COUNTRY_BY_ISO3[iso3];
    if (!c) return null;
    const [ox, oy] = flagOffset[iso3] ?? FLAG_OFFSETS[0];
    const moved = ox !== FLAG_OFFSETS[0][0] || oy !== FLAG_OFFSETS[0][1];
    const n = list.length;
    const isNew = list.some((a) => a.year === asOfYear);
    const name = c.name;
    return (
      <g
        key={iso3}
        data-iso3={iso3}
        className="fc-flag"
        role="button"
        tabIndex={0}
        aria-label={`${name}: ${n} ${n === 1 ? "alert" : "alerts"} as of ${asOfYear}. Open country view`}
        transform={`translate(${c.center[0]} ${c.center[1]}) scale(${unit})`}
      >
        {moved ? (
          <line x1={0} y1={0} x2={ox} y2={oy + 1} stroke={AMBER} strokeWidth={1} strokeOpacity={0.8} pointerEvents="none" />
        ) : null}
        <g transform={`translate(${ox} ${oy})`}>
        <rect x={-5} y={-24} width={n > 1 ? 30 : 22} height={27} fill="transparent" />
        {isNew ? (
          <circle key={`new-${asOfYear}`} className="fc-pulse" cx={5} cy={-12} r={12.5} fill="none" stroke={AMBER} strokeWidth={1.7} pointerEvents="none" />
        ) : null}
        <line x1={0} y1={1} x2={0} y2={-19} stroke="#050d17" strokeWidth={3.5} strokeLinecap="round" />
        <line x1={0} y1={1} x2={0} y2={-19} stroke={AMBER} strokeWidth={1.6} strokeLinecap="round" />
        <path
          className="fc-flag-focus"
          d="M0.8 -19 L13 -15 L0.8 -11 Z"
          fill={placeholderFeed ? "rgba(242,189,118,0.3)" : AMBER}
          stroke={placeholderFeed ? AMBER : "#050d17"}
          strokeWidth={1.2}
          strokeDasharray={placeholderFeed ? "2 1.6" : undefined}
          strokeLinejoin="round"
        />
        {n > 1 ? (
          <text className="fc-label-text" x={15} y={-10} fontSize={12} strokeWidth={3} style={{ fill: AMBER }}>
            {n}
          </text>
        ) : null}
        </g>
      </g>
    );
  });

  // Labels below the marker, at least 13px on screen, never under an overlay.
  // Labels below the marker, at least 13px on screen, never under an overlay
  // or another label. Selected first; in the papers layer then by paper count.
  const labels = (() => {
    if (!view || !size) return null;
    const cands = WORLD.countries.filter(
      (c) =>
        c.iso3 === selected ||
        (zoom > 2.5 && (isPapers ? (paperCounts[c.iso3]?.total ?? 0) > 0 : GENOME_ISO3.has(c.iso3))),
    );
    cands.sort((a, b) => {
      if (a.iso3 === selected) return -1;
      if (b.iso3 === selected) return 1;
      return isPapers ? (paperCounts[b.iso3]?.total ?? 0) - (paperCounts[a.iso3]?.total ?? 0) : 0;
    });
    const placed: { l: number; t: number; r: number; b: number }[] = [];
    const out: React.JSX.Element[] = [];
    for (const c of cands) {
      const pr = paperCounts[c.iso3];
      const name = mapLabel(c.iso3, c.name);
      const second = isPapers && pr && pr.total > 0 ? paperLabelSuffix(pr.readByGraph, pr.total) : null;
      const fs = c.iso3 === selected ? 15 : 13;
      const p = projToPx(c.center[0], c.center[1]);
      const longest = Math.max(name.length, second?.length ?? 0);
      const half = (longest * fs * 0.58) / 2;
      const lines = second ? 2 : 1;
      const box = { l: p.x - half, r: p.x + half, t: p.y + 8, b: p.y + 12 + fs * lines * 1.15 };
      if (box.l < 0 || box.r > size.cw - panelPx || box.t < 0 || box.b > size.ch) continue;
      const hit = (a: { l: number; t: number; r: number; b: number }) =>
        box.l < a.r && box.r > a.l && box.t < a.b && box.b > a.t;
      if (avoid.some(hit) || placed.some(hit)) continue;
      placed.push(box);
      const x = c.center[0];
      const y = c.center[1] + (10 + fs) * unit;
      out.push(
        <text
          key={c.iso3}
          className="fc-label-text"
          x={x}
          y={y}
          textAnchor="middle"
          fontSize={fs * unit}
          strokeWidth={3.5 * unit}
        >
          {name}
          {second ? (
            <tspan x={x} dy={fs * 1.15 * unit} fontWeight={500}>
              {second}
            </tspan>
          ) : null}
        </text>,
      );
    }
    return out;
  })();

  const hoverSnap = hover ? genomeSnapshot(hover.iso3, asOfYear) : null;
  const hoverGeo = hover ? COUNTRY_BY_ISO3[hover.iso3] : undefined;
  const hoverAlerts = hover ? (alertsByIso3[hover.iso3] ?? []) : [];

  return (
    <div ref={wrapRef} className="absolute inset-0">
      <svg
        ref={svgRef}
        className={`fc-map${dragging ? " is-dragging" : ""}${selected ? " fc-dim" : ""}`}
        viewBox={vb}
        preserveAspectRatio="xMidYMid meet"
        role="group"
        aria-label={`World map of K540E (pfdhps, sulfadoxine-pyrimethamine) in genome data as of ${asOfYear}. Countries with data are focusable.`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        onPointerLeave={() => setHover(null)}
        onClick={onClick}
        onKeyDown={onKeyDown}
        onFocus={onFocus}
        onBlur={() => setHover(null)}
      >
        <defs>
          <pattern
            id={HATCH_PATTERN_ID}
            width={5 * unit}
            height={5 * unit}
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(45)"
          >
            <rect width={5 * unit} height={5 * unit} fill={HATCH_BG} />
            <line x1="0" y1="0" x2="0" y2={5 * unit} stroke={HATCH_LINE} strokeWidth={1.4 * unit} />
          </pattern>
        </defs>
        <CountryPaths fills={fills} states={states} selected={selected} />
        {sel ? (
          <g>
            <path d={sel.d} className="fc-sel-halo" />
            <path d={sel.d} className="fc-sel-outline" />
          </g>
        ) : null}
        <g>{markers}</g>
        <g aria-hidden>{changedRings}</g>
        <g aria-hidden>{labels}</g>
        <g>{flags}</g>
      </svg>

      {isPapers && hover && hoverGeo ? (
        <div
          className="fc-card fc-tooltip"
          style={{
            left: Math.min(hover.x + 14, (size?.cw ?? 1000) - 300 - panelPx),
            top: Math.max(8, hover.y + 14),
          }}
          role="status"
        >
          <div className="font-semibold text-[13px]">{hoverGeo.name}</div>
          <div className="tabular-nums">
            {paperCounts[hover.iso3]?.total ?? 0} K540E papers published through {asOfYear}
          </div>
          {(paperCounts[hover.iso3]?.total ?? 0) > 0 ? (
            <div className="tabular-nums">The Graph has read {paperCounts[hover.iso3]?.readByGraph ?? 0} of them</div>
          ) : null}
          <div className="mt-1 text-[12px] text-muted">{PAPER_SOURCE_LINE}</div>
        </div>
      ) : null}
      {!isPapers && hover && hoverGeo && hoverSnap ? (
        <div
          className="fc-card fc-tooltip"
          style={{
            left: Math.min(hover.x + 14, (size?.cw ?? 1000) - 300 - panelPx),
            top: Math.max(8, hover.y + 14),
          }}
          role="status"
        >
          <div className="font-semibold text-[13px]">{hoverGeo.name}</div>
          <div>{STATE_LABEL[hoverSnap.state]}</div>
          {hoverSnap.latest ? (
            <div className="tabular-nums">
              {hoverSnap.latest.year}: {hoverSnap.latest.withE} of {hoverSnap.latest.tested} samples carry
              K540E
            </div>
          ) : null}
          {hoverSnap.firstDetectionYear !== null ? (
            <div>First detection in our data: {hoverSnap.firstDetectionYear}</div>
          ) : null}
          {hoverAlerts.length ? (
            <div className="mt-1 border-t border-line pt-1" style={{ color: AMBER }}>
              <div>
                {alertCountText(hoverAlerts.length, asOfYear)}
                {placeholderFeed ? " (placeholder, not a real alert)" : ""}
              </div>
              <div className="text-fg">{hoverAlerts[hoverAlerts.length - 1].headline}</div>
            </div>
          ) : null}
          <div className="mt-1 text-[12px] text-muted">Genome data · MalariaGEN Pf8 · by collection year</div>
        </div>
      ) : null}

      <div
        data-fc-avoid
        className="absolute bottom-4 z-20 flex flex-col gap-1.5"
        style={{ right: panelPx + 16, transition: "right 300ms ease" }}
      >
        <button type="button" className="fc-btn" aria-label="Zoom in" onClick={() => zoomBy(1.8)}>
          +
        </button>
        <button type="button" className="fc-btn" aria-label="Zoom out" onClick={() => zoomBy(1 / 1.8)}>
          −
        </button>
        <button type="button" className="fc-btn text-[12px] uppercase tracking-[0.1em]" aria-label="Reset to world view" onClick={resetWorld}>
          World
        </button>
      </div>
    </div>
  );
}
