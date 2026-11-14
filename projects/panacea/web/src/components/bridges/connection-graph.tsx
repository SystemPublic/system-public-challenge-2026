"use client";

// The research-graph connection view for one bridge pair: every shipped
// connection between the A and B concept sets as a deterministic layered
// node-link diagram. No force simulation — positions come from column order
// once, so the layout never wobbles. Nodes wear their dominant effect
// direction (risk-increasing vs protective); hovering a node or selecting a
// hypothesis chip highlights that connection and prints effect sizes on the
// edges.

import { useEffect, useMemo, useRef, useState } from "react";
import type { Bridge, ConceptDict } from "@/lib/bundle";
import { effectDirection, fmtEffect, fmtInt } from "@/lib/format";

const W = 780;
const COL_X = [85, 255, 425, 595, W - 85]; // A | one-step | corr X | corr Y | B
const ROW_H = 24;
const MIN_H = 430;
const MAX_H = 1020;
const TOP = 40;

type Role = "endpoint" | "one" | "corrX" | "corrY";

type GNode = {
  id: string;
  role: Role;
  x: number;
  y: number;
  r: number;
  deg: number; // connections shown in this view
  dir: "up" | "down" | null; // dominant effect direction
};
type GEdge = {
  from: number; // node index
  to: number;
  f: number;
  st: number;
  na: number | null;
  med: number | null;
  et: string | null;
  conn: string; // "one:{id}" or "two:{x}|{y}" — which hypothesis this edge serves
};

const trunc = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

const edgeStrength = (f: number, st: number) =>
  Math.log10(1 + f) + 0.5 * Math.log10(1 + st);

export function ConnectionGraph({
  bridge,
  concepts,
  selected,
}: {
  bridge: Bridge;
  concepts: ConceptDict;
  /** active hypothesis chip: "one:{id}" or "two:{x}|{y}", null = none */
  selected: string | null;
}) {
  // rendered width drives the layout; height stays fixed, so selecting a
  // hypothesis (which narrows the column) keeps the graph's short height
  const wrapRef = useRef<HTMLDivElement>(null);
  const [cw, setCw] = useState(780);
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

  const { nodes, edges, H } = useMemo(() => {
    const aSet = new Set(bridge.A);
    const bSet = new Set(bridge.B);
    const oneIds = bridge.one.map((c) => c.id);

    const corrX: string[] = [];
    const corrY: string[] = [];
    const seen = new Set([...oneIds, ...bridge.A, ...bridge.B]);
    for (const c of bridge.two) {
      if (!seen.has(c.x) && !bSet.has(c.x)) {
        seen.add(c.x);
        corrX.push(c.x);
      }
      if (!seen.has(c.y) && !aSet.has(c.y)) {
        seen.add(c.y);
        corrY.push(c.y);
      }
    }

    const cols: { role: Role; ids: string[] }[] = [
      { role: "endpoint", ids: bridge.A },
      { role: "one", ids: oneIds },
      { role: "corrX", ids: corrX },
      { role: "corrY", ids: corrY },
      { role: "endpoint", ids: bridge.B },
    ];
    const maxCount = Math.max(...cols.map((c) => c.ids.length), 5);
    const H = Math.min(MAX_H, Math.max(MIN_H, maxCount * ROW_H + TOP + 40));

    const idx = new Map<string, number>();
    const nodes: GNode[] = [];
    cols.forEach((col, ci) => {
      col.ids.forEach((id, i) => {
        const y =
          TOP + ((H - TOP - 40) * (i + 0.5)) / Math.max(col.ids.length, 1);
        idx.set(id, nodes.length);
        nodes.push({ id, role: col.role, x: COL_X[ci], y, r: 7, deg: 0, dir: null });
      });
    });

    const edges: GEdge[] = [];
    const drawn = new Set<string>(); // corridor edges can duplicate 1-step edges
    const bump = (id: string) => {
      const i = idx.get(id);
      if (i !== undefined) nodes[i].deg += 1;
    };
    const push = (
      fromId: string,
      toId: string,
      f: number,
      st: number,
      na: number | null,
      med: number | null,
      et: string | null,
      conn: string,
    ) => {
      const a = idx.get(fromId);
      const b = idx.get(toId);
      if (a === undefined || b === undefined) return;
      const key = a < b ? `${a}-${b}` : `${b}-${a}`;
      if (drawn.has(key)) return;
      drawn.add(key);
      edges.push({ from: a, to: b, f, st, na, med, et, conn });
      bump(fromId);
      bump(toId);
    };

    for (const c of bridge.one) {
      const conn = `one:${c.id}`;
      for (const d of c.ea) push(d.a, c.id, d.f, d.st, d.na, d.med, d.et, conn);
      for (const d of c.eb) push(c.id, d.b, d.f, d.st, d.na, d.med, d.et, conn);
    }
    for (const c of bridge.two) {
      const conn = `two:${c.x}|${c.y}`;
      push(c.ea.a, c.x, c.ea.f, c.ea.st, c.ea.na, c.ea.med, c.ea.et, conn);
      push(c.x, c.y, c.xy.f, c.xy.st, c.xy.na, c.xy.med, c.xy.et, conn);
      push(c.y, c.eb.b, c.eb.f, c.eb.st, c.eb.na, c.eb.med, c.eb.et, conn);
    }

    // radii; nodes stay neutral — direction lives on the edges
    for (const nd of nodes) {
      nd.dir = null;
      if (nd.role === "one") {
        const c = bridge.one.find((c) => c.id === nd.id)!;
        const fmax = Math.max(...c.ea.map((d) => d.f), ...c.eb.map((d) => d.f));
        nd.r = 5 + 3.5 * Math.log10(1 + fmax);
      } else if (nd.role === "endpoint") {
        nd.r = 11;
      } else {
        nd.r = 6.5;
      }
    }
    return { nodes, edges, H };
  }, [bridge]);

  const showTip = (
    ev: React.PointerEvent,
    lines: { v?: string; sub?: string }[],
  ) => {
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect) return;
    setTip({ x: ev.clientX - rect.left, y: ev.clientY - rect.top, lines });
  };

  const nodeTipLines = (i: number) => {
    const nd = nodes[i];
    const c = concepts[nd.id];
    return [
      { v: c?.l || nd.id },
      { sub: c?.dm || "not in the mapped concept set" },
      ...(c?.d ? [{ sub: c.d }] : []),
      { sub: `${fmtInt(nd.deg)} connections shown — bigger dot, more findings` },
    ];
  };

  const edgeTipLines = (e: GEdge) => {
    const a = concepts[nodes[e.from].id]?.l || nodes[e.from].id;
    const b = concepts[nodes[e.to].id]?.l || nodes[e.to].id;
    const eff = fmtEffect(e.med, e.et);
    return [
      { v: `${a} — ${b}` },
      { sub: `${e.f} findings · ${e.st} studies` },
      ...(e.na !== null
        ? [
            {
              sub: `${fmtInt(e.na)} associations · median effect ${eff} — direction only`,
            },
          ]
        : [{ sub: "no associations in the deposit" }]),
    ];
  };

  // which edges are lit: hover (all edges of the hovered node) or the
  // selected hypothesis chip
  const litEdges = useMemo(() => {
    if (hoverNode !== null) {
      return new Set(
        edges
          .map((e, i) => (e.from === hoverNode || e.to === hoverNode ? i : -1))
          .filter((i) => i >= 0),
      );
    }
    if (selected !== null) {
      const lit = new Set(
        edges.map((e, i) => (e.conn === selected ? i : -1)).filter((i) => i >= 0),
      );
      // corridor first legs can be deduped into a 1-step edge — recover them
      // by matching the corridor's node chain
      if (selected.startsWith("two:")) {
        const [, xy] = selected.split(":");
        const [x, y] = xy!.split("|");
        const c = bridge.two.find((t) => t.x === x && t.y === y);
        if (c) {
          const chain = [c.ea.a, c.x, c.y, c.eb.b];
          edges.forEach((e, i) => {
            const a = nodes[e.from].id;
            const b = nodes[e.to].id;
            for (let k = 0; k < chain.length - 1; k++) {
              if (
                (a === chain[k] && b === chain[k + 1]) ||
                (b === chain[k] && a === chain[k + 1])
              ) {
                lit.add(i);
              }
            }
          });
        }
      }
      return lit;
    }
    return null;
  }, [hoverNode, selected, edges, bridge.two, nodes]);

  const edgeLit = (i: number) =>
    (hoverEdge === i) || (litEdges?.has(i) ?? false);

  return (
    <div ref={wrapRef} className="relative mt-2">
      <svg
        viewBox={`0 0 ${cw} ${H}`}
        width="100%"
        height={H}
        className="touch-none"
        role="img"
        aria-label={`Research-graph connections between ${bridge.A.join(", ")} and ${bridge.B.join(", ")}`}
      >
        {/* edges */}
        {edges.map((e, i) => {
          const a = nodes[e.from];
          const b = nodes[e.to];
          const lit = edgeLit(i);
          const dim = litEdges !== null && !litEdges.has(i);
          const w = 0.5 + Math.min(2.2, edgeStrength(e.f, e.st) * 0.45);
          const mx = (a.x + b.x) / 2;
          const my = (a.y + b.y) / 2;
          const d = `M ${a.x} ${a.y} C ${mx} ${a.y}, ${mx} ${b.y}, ${b.x} ${b.y}`;
          const eff = fmtEffect(e.med, e.et);
          const showLabel = lit && eff !== null;
          const dir = effectDirection(e.med, e.et);
          const edgeColor = lit
            ? dir === "up"
              ? "var(--dir-up)"
              : dir === "down"
                ? "var(--dir-down)"
                : "var(--ink)"
            : dir === "up"
              ? "color-mix(in srgb, var(--dir-up) 45%, transparent)"
              : dir === "down"
                ? "color-mix(in srgb, var(--dir-down) 45%, transparent)"
                : "var(--chart-grid)";
          return (
            <g key={i} opacity={dim ? 0.15 : 1}>
              <path
                d={d}
                fill="none"
                stroke={edgeColor}
                strokeWidth={lit ? Math.max(1.8, w) : w}
              />
              {showLabel && (
                <>
                  <rect
                    x={mx - 64}
                    y={my - 12}
                    width={128}
                    height={23}
                    rx={5}
                    fill="var(--paper)"
                    stroke="var(--color-rule)"
                    strokeWidth={1.2}
                  />
                  <text
                    x={mx}
                    y={my + 4.5}
                    textAnchor="middle"
                    fontSize={13}
                    fontWeight={600}
                    fill="var(--ink)"
                    fontFamily="var(--font-sans)"
                  >
                    {eff}
                  </text>
                </>
              )}
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
            </g>
          );
        })}

        {/* nodes */}
        {nodes.map((nd, i) => {
          const fill =
            nd.role === "endpoint" ? "var(--s-blue)" : "var(--s-deemph)";
          const labelLeft = nd.x > cw / 2;
          const dim =
            (hoverNode !== null || selected !== null) &&
            !edges.some((e, ei) => edgeLit(ei) && (e.from === i || e.to === i));
          return (
            <g key={nd.id} opacity={dim ? 0.25 : 1}>
              <circle
                cx={nd.x}
                cy={nd.y}
                r={nd.r}
                fill={fill}
                stroke="var(--paper)"
                strokeWidth={2}
              />
              <text
                x={labelLeft ? nd.x - nd.r - 6 : nd.x + nd.r + 6}
                y={nd.y + 4}
                textAnchor={labelLeft ? "end" : "start"}
                fontSize={12.5}
                fontWeight={nd.role === "endpoint" ? 600 : 400}
                fill="var(--ink)"
                fontFamily="var(--font-sans)"
              >
                {trunc(concepts[nd.id]?.l || nd.id, cw > 900 ? 26 : 17)}
              </text>
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

      {/* legend */}
      <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 font-sans text-[0.72rem] text-[color:var(--chart-ink-2)]">
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-[color:var(--s-blue)]" />
          Underlay concepts
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-[3px] w-5 rounded-full bg-[color:var(--dir-up)]" />
          studies find them rise together
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-[3px] w-5 rounded-full bg-[color:var(--dir-down)]" />
          studies find one goes up as the other goes down
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-[3px] w-5 rounded-full bg-[color:var(--chart-grid)]" />
          studies name the pair but give no number
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-[color:var(--s-deemph)]" />
          <span className="inline-block h-3 w-3 rounded-full bg-[color:var(--s-deemph)]" />
          dot size = how many findings back it
        </span>
      </div>


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
