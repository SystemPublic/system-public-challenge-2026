"use client";

// The 1-hop research-graph view for one confirmation/contested pair, drawn in
// the bridges connection-graph's visual language: deterministic layered
// layout, bezier edges colored by effect direction, effect-size chips on
// hover, dot size ∝ findings, stroke width ∝ evidence. Columns: its other
// neighbors | concept 1 | shared connectors | concept 2 | its other
// neighbors — the two endpoints flank the shared links, each concept's other
// neighbors pushed to the outside. No force simulation: positions come from
// column order once.

import { useEffect, useMemo, useRef, useState } from "react";
import type { ConceptDict, ConfirmationRow, Ego } from "@/lib/bundle";
import { effectDirection, fmtEffect, fmtInt, fmtRho, deEmdash } from "@/lib/format";

const ROW_H = 30;
const MIN_H = 300;
const MAX_H = 760;
const TOP = 34;
const BOTTOM = 66; // room for the pair-edge annotation

const edgeStrength = (f: number, st: number) =>
  Math.log10(1 + f) + 0.5 * Math.log10(1 + st);

type Item = {
  id: string;
  f?: number;
  st?: number;
  nyc?: boolean;
  na?: number | null;
  med?: number | null;
  et?: string | null;
};

type Role = "only1" | "endpoint1" | "shared" | "endpoint2" | "only2";

type GNode = {
  id: string;
  role: Role;
  x: number;
  y: number;
  r: number;
  /** findings on the edge to this node's owning endpoint (null for shared/endpoints) */
  f: number | null;
  st: number | null;
  nyc: boolean;
  deg: number; // edges drawn in this view
};
type GEdge = {
  from: number;
  to: number;
  kind: "pair" | "nbr" | "shared";
  f: number | null;
  st: number | null;
  na: number | null;
  med: number | null;
  et: string | null;
  nyc: boolean;
};

const trunc = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

const NULL_STATS = { f: null, st: null, na: null, med: null, et: null, nyc: false };

export function PairGraph({
  pair,
  concepts,
  egos,
}: {
  pair: ConfirmationRow;
  concepts: ConceptDict;
  egos: Record<string, Ego>;
}) {
  const e1 = egos[pair.c1];
  const e2 = egos[pair.c2];

  const wrapRef = useRef<HTMLDivElement>(null);
  const [cw, setCw] = useState(860);
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width ?? 0;
      if (w > 0) setCw(w);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const [hoverNode, setHoverNode] = useState<number | null>(null);
  const [hoverEdge, setHoverEdge] = useState<number | null>(null);
  const [tip, setTip] = useState<{
    x: number;
    y: number;
    lines: { v?: string; sub?: string }[];
  } | null>(null);

  const { nodes, edges, H, colX } = useMemo(() => {
    if (!e1 || !e2) return { nodes: [], edges: [], H: MIN_H, colX: [] as number[] };
    const sharedSet = new Set(pair.sh);
    const only1 = e1.nbrs.filter((n) => !sharedSet.has(n.id) && n.id !== pair.c2);
    const only2 = e2.nbrs.filter((n) => !sharedSet.has(n.id) && n.id !== pair.c1);
    const stats1 = new Map(e1.nbrs.map((n) => [n.id, n]));
    const stats2 = new Map(e2.nbrs.map((n) => [n.id, n]));
    const statsOf = (s: Item | undefined) =>
      s
        ? { f: s.f ?? null, st: s.st ?? null, na: s.na ?? null, med: s.med ?? null, et: s.et ?? null, nyc: Boolean(s.nyc) }
        : NULL_STATS;

    const W = Math.max(cw, 640);
    const colX = [0.09, 0.3, 0.5, 0.7, 0.91].map((t) => t * W);
    const cols: { role: Role; ids: Item[] }[] = [
      { role: "only1", ids: only1 },
      { role: "endpoint1", ids: [{ id: pair.c1 }] },
      { role: "shared", ids: pair.sh.map((id) => ({ id })) },
      { role: "endpoint2", ids: [{ id: pair.c2 }] },
      { role: "only2", ids: only2 },
    ];
    const maxLen = Math.max(...cols.map((c) => c.ids.length), 4);
    const H = Math.min(MAX_H, Math.max(MIN_H, maxLen * ROW_H + TOP + BOTTOM));

    const nodes: GNode[] = [];
    const idx = new Map<string, number>();
    cols.forEach((col, ci) => {
      const n = col.ids.length;
      col.ids.forEach((item, i) => {
        const y =
          n === 1
            ? TOP + (H - TOP - BOTTOM) / 2
            : TOP + ((H - TOP - BOTTOM) * (i + 0.5)) / n;
        idx.set(item.id, nodes.length);
        const neighbor = col.role === "only1" || col.role === "only2";
        const f = neighbor ? (item.f ?? 0) : null;
        const st = neighbor ? (item.st ?? 0) : null;
        const nyc = neighbor ? Boolean(item.nyc) : false;
        nodes.push({
          id: item.id,
          role: col.role,
          x: colX[ci],
          y,
          r:
            col.role === "endpoint1" || col.role === "endpoint2"
              ? 11
              : col.role === "shared"
                ? 6.5
                : 5 + 3.5 * Math.log10(1 + (f ?? 0)),
          f,
          st,
          nyc,
          deg: 0,
        });
      });
    });

    const edges: GEdge[] = [];
    const bump = (id: string) => {
      const i = idx.get(id);
      if (i !== undefined) nodes[i].deg += 1;
    };
    const link = (a: string, b: string, kind: GEdge["kind"], s: ReturnType<typeof statsOf>) => {
      const i = idx.get(a);
      const j = idx.get(b);
      if (i === undefined || j === undefined) return;
      edges.push({ from: i, to: j, kind, ...s });
      bump(a);
      bump(b);
    };
    // the pair edge itself, colored by the pair's own effect direction
    link(pair.c1, pair.c2, "pair", {
      f: pair.rel ? pair.rel.f : 0,
      st: pair.rel ? pair.rel.st : 0,
      na: pair.na,
      med: pair.med,
      et: pair.et[0] ?? null,
      nyc: false,
    });
    // only-neighbors: edge to their owning endpoint
    for (const n of only1) {
      link(pair.c1, n.id, "nbr", statsOf(n));
    }
    for (const n of only2) {
      link(pair.c2, n.id, "nbr", statsOf(n));
    }
    // shared connectors: one edge per side, each with that side's evidence
    for (const id of pair.sh) {
      link(pair.c1, id, "shared", statsOf(stats1.get(id)));
      link(pair.c2, id, "shared", statsOf(stats2.get(id)));
    }
    return { nodes, edges, H, colX };
  }, [pair, e1, e2, cw]);

  // lit edges: everything touching the hovered node, or the hovered edge
  const litEdges = useMemo(() => {
    if (hoverNode !== null) {
      return new Set(
        edges
          .map((e, i) => (e.from === hoverNode || e.to === hoverNode ? i : -1))
          .filter((i) => i >= 0),
      );
    }
    if (hoverEdge !== null) return new Set([hoverEdge]);
    return null;
  }, [hoverNode, hoverEdge, edges]);

  const COL_HEADS = ["its other neighbors", "concept 1", "shared connectors", "concept 2", "its other neighbors"];

  // label budget per column: the gap this column's label runs into, alone
  // (shared connectors stay unlabeled inline; hover names them)
  const labelChars = (colIdx: number) => {
    const gap =
      colIdx === 0
        ? colX[1] - colX[0]
        : colIdx === 1
          ? colX[2] - colX[1]
          : colIdx === 3
            ? colX[3] - colX[2]
            : colX[4] - colX[3];
    const px = colIdx === 1 || colIdx === 3 ? gap - 44 : gap - 30;
    return Math.max(8, Math.min(30, Math.round(px / 6.2)));
  };

  const edgeLit = (i: number) => hoverEdge === i || (litEdges?.has(i) ?? false);

  // effect chips for lit edges, greedily deconflicted vertically (23px-tall
  // chips need ~26px of clearance; edges converging on adjacent dots would
  // otherwise overprint)
  const chips = useMemo(() => {
    const all: { x: number; y: number; text: string; i: number }[] = [];
    edges.forEach((e, i) => {
      if (!edgeLit(i)) return;
      const eff = fmtEffect(e.med, e.et);
      if (!eff) return;
      const a = nodes[e.from];
      const b = nodes[e.to];
      all.push({
        x: (a.x + b.x) / 2,
        y: e.kind === "pair" ? (a.y + b.y) / 2 + 40 : (a.y + b.y) / 2,
        text: eff,
        i,
      });
    });
    const placed: typeof all = [];
    for (const c of [...all].sort((p, q) => p.y - q.y)) {
      if (placed.every((p) => Math.abs(p.y - c.y) >= 26)) placed.push(c);
    }
    return new Map(placed.map((p) => [p.i, p]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [edges, hoverNode, hoverEdge]);

  if (!e1 || !e2) return null;

  const showTip = (ev: React.PointerEvent, lines: { v?: string; sub?: string }[]) => {
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect) return;
    setTip({ x: ev.clientX - rect.left, y: ev.clientY - rect.top, lines });
  };

  const nodeTipLines = (i: number) => {
    const nd = nodes[i];
    const c = concepts[nd.id];
    const lines: { v?: string; sub?: string }[] = [
      { v: c?.l || nd.id },
      { sub: c?.dm || "beyond the mapped concepts" },
      ...(c?.d ? [{ sub: deEmdash(c.d) }] : []),
    ];
    if (nd.role === "only1" || nd.role === "only2") {
      lines.push({ sub: `edge: ${nd.f} findings · ${nd.st} studies` });
    }
    if (nd.role === "shared") {
      lines.push({ sub: `shared connector: links both concepts` });
    }
    if (nd.nyc) {
      lines.push({ sub: "mapped to NYC measures" });
    }
    lines.push({ sub: `${fmtInt(nd.deg)} connections shown: bigger dot, more findings` });
    return lines;
  };

  const edgeTipLines = (e: GEdge) => {
    const a = concepts[nodes[e.from].id]?.l || nodes[e.from].id;
    const b = concepts[nodes[e.to].id]?.l || nodes[e.to].id;
    const eff = fmtEffect(e.med, e.et);
    return [
      { v: e.kind === "pair" ? `${a} × ${b}` : `${a} → ${b}` },
      { sub: `${fmtInt(e.f ?? 0)} findings · ${fmtInt(e.st ?? 0)} studies` },
      ...(e.na !== null
        ? [
            {
              sub: `${fmtInt(e.na)} associations · median effect ${eff}: direction only`,
            },
          ]
        : [{ sub: "no associations in the deposit" }]),
    ];
  };

  return (
    <div ref={wrapRef} className="relative">
      <svg
        viewBox={`0 0 ${Math.max(cw, 640)} ${H}`}
        width="100%"
        height={H}
        className="touch-none"
        role="img"
        aria-label={`One-hop research graph around ${concepts[pair.c1]?.l ?? pair.c1} and ${concepts[pair.c2]?.l ?? pair.c2}`}
      >
        {/* column heads */}
        {colX.map((x, i) => (
          <text
            key={i}
            x={x}
            y={16}
            textAnchor="middle"
            fontSize={11}
            fontWeight={600}
            fill="var(--color-muted)"
            fontFamily="var(--font-sans)"
          >
            {COL_HEADS[i]}
          </text>
        ))}

        {/* edges */}
        {edges.map((e, i) => {
          const a = nodes[e.from];
          const b = nodes[e.to];
          const lit = edgeLit(i);
          const dim = litEdges !== null && !litEdges.has(i);
          const isPair = e.kind === "pair";
          const w = isPair
            ? 2.5
            : 0.5 + Math.min(2.2, edgeStrength(e.f ?? 0, e.st ?? 0) * 0.45);
          const dir = effectDirection(e.med, e.et);
          const dirColor =
            dir === "up" ? "var(--dir-up)" : dir === "down" ? "var(--dir-down)" : null;
          const stroke = lit
            ? dirColor ?? "var(--ink)"
            : dirColor
              ? `color-mix(in srgb, ${dirColor} 45%, transparent)`
              : "var(--chart-grid)";
          // the pair edge arcs under everything; other edges are bridges beziers
          const mx = (a.x + b.x) / 2;
          const d = isPair
            ? `M ${a.x + 14} ${a.y + 24} C ${mx} ${a.y + 74}, ${mx} ${b.y + 74}, ${b.x - 14} ${b.y + 24}`
            : `M ${a.x} ${a.y} C ${mx} ${a.y}, ${mx} ${b.y}, ${b.x} ${b.y}`;
          const chip = chips.get(i);
          return (
            <g key={i} opacity={dim ? 0.15 : 1}>
              <path
                d={d}
                fill="none"
                stroke={stroke}
                strokeWidth={lit ? Math.max(w, 1.8) : w}
                opacity={isPair ? 0.85 : 1}
              />
              {chip && (
                <>
                  <rect
                    x={chip.x - 64}
                    y={chip.y - 12}
                    width={128}
                    height={23}
                    rx={5}
                    fill="var(--paper)"
                    stroke="var(--color-rule)"
                    strokeWidth={1.2}
                  />
                  <text
                    x={chip.x}
                    y={chip.y + 4.5}
                    textAnchor="middle"
                    fontSize={13}
                    fontWeight={600}
                    fill="var(--ink)"
                    fontFamily="var(--font-sans)"
                  >
                    {chip.text}
                  </text>
                </>
              )}
              {!isPair && (
                <path
                  d={d}
                  fill="none"
                  stroke="transparent"
                  strokeWidth={12}
                  style={{ pointerEvents: "stroke" }}
                  onPointerMove={(ev) => {
                    setHoverEdge(i);
                    showTip(ev, edgeTipLines(e));
                  }}
                  onPointerLeave={() => setHoverEdge(null)}
                />
              )}
            </g>
          );
        })}

        {/* pair-edge annotation */}
        <text
          x={Math.max(cw, 640) / 2}
          y={H - 14}
          textAnchor="middle"
          fontSize={12}
          fill="var(--chart-ink-2)"
          fontFamily="var(--font-sans)"
        >
          {`pair edge: ${fmtInt(pair.na)} associations · ${fmtInt(pair.np)} studies` +
            (pair.rho !== null ? ` · city ρ ${fmtRho(pair.rho)}` : " · no district-level check")}
        </text>

        {/* nodes */}
        {nodes.map((nd, i) => {
          const fill =
            nd.role === "endpoint1" || nd.role === "endpoint2" || nd.nyc
              ? "var(--s-blue)"
              : nd.role === "shared"
                ? "var(--s-aqua)"
                : "var(--s-deemph)";
          const colIdx =
            nd.role === "only1" ? 0 : nd.role === "endpoint1" ? 1 : nd.role === "shared" ? 2 : nd.role === "endpoint2" ? 3 : 4;
          const labelLeft = colIdx >= 3;
          const dim =
            hoverNode !== null &&
            !edges.some((e, ei) => litEdges?.has(ei) && (e.from === i || e.to === i));
          return (
            <g key={nd.id} opacity={dim ? 0.25 : 1}>
              <circle
                cx={nd.x}
                cy={nd.y}
                r={nd.r}
                fill={fill}
                stroke={nd.role === "shared" ? "var(--s-aqua)" : "var(--paper)"}
                strokeWidth={nd.role === "shared" ? 1.6 : 1.5}
              />
              {/* shared connectors stay unlabeled inline: their gap would
                  collide with the endpoint labels; hover names them */}
              {colIdx !== 2 && (
                <text
                  x={labelLeft ? nd.x - nd.r - 6 : nd.x + nd.r + 6}
                  y={nd.y + 4}
                  textAnchor={labelLeft ? "end" : "start"}
                  fontSize={12}
                  fontWeight={colIdx === 1 || colIdx === 3 ? 600 : 400}
                  fill="var(--ink)"
                  fontFamily="var(--font-sans)"
                >
                  {trunc(concepts[nd.id]?.l || nd.id, labelChars(colIdx))}
                </text>
              )}
              <circle
                cx={nd.x}
                cy={nd.y}
                r={Math.max(nd.r + 8, 14)}
                fill="transparent"
                onPointerMove={(ev) => {
                  setHoverNode(i);
                  showTip(ev, nodeTipLines(i));
                }}
                onPointerLeave={() => setHoverNode(null)}
              />
            </g>
          );
        })}
      </svg>

      {tip && (
        <div className="viz-tip" style={{ left: tip.x, top: tip.y }} role="status">
          {tip.lines.map((l, i) =>
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
  );
}
