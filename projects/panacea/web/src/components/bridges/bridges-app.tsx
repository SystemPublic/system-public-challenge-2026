"use client";

// Bridges: start from a theme. A search box suggests overall categories
// (themes and concepts across the bridge pairs); picking one offers candidate
// pairs as chips; clicking a chip opens the full connection view below:
// district maps whose correlation is ρ, then every research-graph connection
// between the two concept sets. Deep links (?x=…&y=…) land directly on the
// full view.

import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type {
  Bridge,
  ConceptDict,
  District,
  DistrictValue,
  MeasureDict,
} from "@/lib/bundle";
import { fmtRho } from "@/lib/format";
import { DistrictMaps } from "@/components/bridges/district-maps";
import { ConnectionGraph } from "@/components/bridges/connection-graph";
import { CitationSidebar } from "@/components/bridges/citation-sidebar";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type PairOption = { measure: string; rho: number };

type Conn = {
  key: string;
  head: string;
  story: string;
  pms: string[];
  strength: number; // weakest-link evidence score across the connection
};

/** story text → segments; [n] markers become citation buttons */
function StoryBody({
  story,
  pms,
  onCite,
}: {
  story: string;
  pms: string[];
  onCite: (pmid: string) => void;
}) {
  const parts = story.split(/(\[\d+\])/g);
  return (
    <p className="max-w-[62rem] text-[1.02rem] leading-[1.75]">
      {parts.map((seg, i) => {
        const m = seg.match(/^\[(\d+)\]$/);
        if (m) {
          const idx = Number(m[1]) - 1;
          const pmid = pms[idx];
          if (!pmid) return <Fragment key={i}>{seg}</Fragment>;
          return (
            <button
              key={i}
              className="cite-link font-sans text-[0.8em] font-medium"
              onClick={() => onCite(pmid)}
              title={`PMID ${pmid} — open the study`}
            >
              [{m[1]}]
            </button>
          );
        }
        return <Fragment key={i}>{seg}</Fragment>;
      })}
    </p>
  );
}

// dark-surface blue ramp, dark (faint evidence) → bright (strong evidence)
const STRENGTH_RAMP = [
  "#0d366b", "#104281", "#184f95", "#1c5cab", "#256abf", "#2a78d6",
  "#3987e5", "#5598e7", "#6da7ec", "#86b6ef", "#9ec5f4",
];

const TOP_CHIPS = 8;

type SearchHit = { term: string; kind: "theme" | "concept"; idxs: number[] };

/** Theme/concept index over the bridge entries for the search box. */
function buildSearchIndex(bridges: Bridge[], concepts: ConceptDict) {
  const themes = new Map<string, number[]>();
  const conceptHits = new Map<string, number[]>();
  bridges.forEach((e, idx) => {
    for (const cid of [...e.A, ...e.B]) {
      const dm = concepts[cid]?.dm || "";
      for (const seg of dm.split("; ")) {
        const t = seg.trim();
        if (!t || t === "beyond-473") continue;
        const arr = themes.get(t) ?? [];
        if (!arr.includes(idx)) arr.push(idx);
        themes.set(t, arr);
      }
      const l = (concepts[cid]?.l || cid).trim();
      if (!l) continue;
      const arr = conceptHits.get(l) ?? [];
      if (!arr.includes(idx)) arr.push(idx);
      conceptHits.set(l, arr);
    }
  });
  const toHits = (
    m: Map<string, number[]>,
    kind: SearchHit["kind"],
  ): SearchHit[] =>
    [...m]
      .map(([term, idxs]) => ({ term, kind, idxs }))
      .sort((a, b) => a.term.localeCompare(b.term));
  return {
    themes: toHits(themes, "theme"),
    concepts: toHits(conceptHits, "concept"),
  };
}

/** Every shipped connection, scored by its weakest link. */
function connsFor(bridge: Bridge | null): Conn[] {
  const edgeStrength = (f: number, st: number) =>
    Math.log10(1 + f) + 0.5 * Math.log10(1 + st);
  const one: Conn[] = (bridge?.one ?? []).map((c) => {
    const strengths = [...c.ea, ...c.eb].map((d) => edgeStrength(d.f, d.st));
    return {
      key: `one:${c.id}`,
      head: c.head,
      story: c.story,
      pms: c.pms,
      strength: Math.min(...strengths),
    };
  });
  const two: Conn[] = (bridge?.two ?? []).map((c) => ({
    key: `two:${c.x}|${c.y}`,
    head: c.head,
    story: c.story,
    pms: c.pms,
    strength: c.s,
  }));
  return [...one, ...two].sort((a, b) => b.strength - a.strength);
}

/** The theme/concept autocomplete: type, pick a category, get pair chips. */
function BridgeSearch({
  index,
  bridges,
  activeEntryIdx,
  onPickPair,
}: {
  index: { themes: SearchHit[]; concepts: SearchHit[] };
  bridges: Bridge[];
  activeEntryIdx: number;
  onPickPair: (entryIdx: number) => void;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [hi, setHi] = useState(0);
  const [cat, setCat] = useState<SearchHit | null>(null);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = (ev: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(ev.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const ql = q.trim().toLowerCase();
  const themeHits = index.themes.filter((t) => !ql || t.term.toLowerCase().includes(ql));
  const conceptHits = index.concepts.filter((t) => !ql || t.term.toLowerCase().includes(ql));
  const list: SearchHit[] = [...themeHits, ...conceptHits];

  const choose = (hit: SearchHit) => {
    setCat(hit);
    setQ(hit.term);
    setOpen(false);
    setHi(0);
  };

  return (
    <div>
      <div ref={boxRef} className="relative max-w-[520px]">
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
            setHi(0);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setOpen(true);
              setHi((h) => Math.min(h + 1, list.length - 1));
            } else if (e.key === "ArrowUp") {
              e.preventDefault();
              setHi((h) => Math.max(h - 1, 0));
            } else if (e.key === "Enter" && open && list[hi]) {
              choose(list[hi]!);
            } else if (e.key === "Escape") {
              setOpen(false);
            }
          }}
          placeholder="Search a theme, e.g. air pollution"
          className="dash-select w-full py-2 pl-3 pr-3"
          role="combobox"
          aria-expanded={open}
          aria-controls="bridge-theme-list"
          aria-autocomplete="list"
          aria-label="Search a theme"
        />
        {open && (
          <ul
            id="bridge-theme-list"
            role="listbox"
            className="absolute z-20 mt-1 max-h-72 w-full overflow-auto border border-rule bg-[color:var(--paper)] py-1"
          >
            {list.length === 0 && (
              <li className="px-3 py-2 font-sans text-[0.78rem] text-muted">
                no theme matches “{q.trim()}”
              </li>
            )}
            {themeHits.map((t, i) => (
              <li key={`t:${t.term}`}>
                <button
                  type="button"
                  role="option"
                  aria-selected={hi === i}
                  className={`flex w-full items-baseline justify-between px-3 py-1.5 text-left font-sans text-[0.82rem]`}
                  style={
                    hi === i
                      ? { background: "color-mix(in srgb, var(--ink) 6%, var(--paper))" }
                      : undefined
                  }
                  onMouseEnter={() => setHi(i)}
                  onClick={() => choose(t)}
                >
                  <span>{t.term}</span>
                  <span className="dom-note">
                    theme · {t.idxs.length} pair{t.idxs.length === 1 ? "" : "s"}
                  </span>
                </button>
              </li>
            ))}
            {conceptHits.map((t, j) => {
              const i = themeHits.length + j;
              return (
                <li key={`c:${t.term}`}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={hi === i}
                    className="flex w-full items-baseline justify-between px-3 py-1.5 text-left font-sans text-[0.82rem]"
                    style={
                      hi === i
                        ? { background: "color-mix(in srgb, var(--ink) 6%, var(--paper))" }
                        : undefined
                    }
                    onMouseEnter={() => setHi(i)}
                    onClick={() => choose(t)}
                  >
                    <span>{t.term}</span>
                    <span className="dom-note">
                      concept · {t.idxs.length} pair{t.idxs.length === 1 ? "" : "s"}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {cat && (
        <div className="mt-5">
          <span className="label">candidate pairs</span>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {cat.idxs.map((idx) => {
              const e = bridges[idx]!;
              const r = e.rows[0]!;
              const isOn = activeEntryIdx === idx;
              return (
                <Badge
                  key={idx}
                  variant="outline"
                  asChild
                  className={`max-w-full cursor-pointer px-3 py-1.5 font-sans text-[0.72rem] leading-tight ${
                    isOn ? "border-[color:var(--ink)] ring-2 ring-[color:var(--ring)]" : ""
                  }`}
                >
                  <button
                    onClick={() => onPickPair(idx)}
                    aria-pressed={isOn}
                    title={`${r.l1} × ${r.l2}: ρ ${fmtRho(r.rho)}`}
                  >
                    {r.l1} × {r.l2} · ρ {fmtRho(r.rho)}
                  </button>
                </Badge>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default function BridgesApp({
  bridges,
  concepts,
  measures,
  districts,
  values,
}: {
  bridges: Bridge[];
  concepts: ConceptDict;
  measures: MeasureDict;
  districts: District[];
  values: Record<string, Record<string, DistrictValue>>;
}) {
  const search = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const [pickedKey, setPickedKey] = useState<string | null>(null);
  const [citePmid, setCitePmid] = useState<string | null>(null);
  const fullRef = useRef<HTMLDivElement>(null);

  // directed pair index over the shipped bridge rows; both directions of a
  // row are selectable and resolve to the same bridge entry
  const { xOptions, pairsByX, pairKeys } = useMemo(() => {
    const pairsByX = new Map<string, Map<string, PairOption>>();
    const labels = new Map<string, string>();
    const pairKeys = new Map<string, { bridge: Bridge; m1: string; m2: string }>();
    for (const e of bridges) {
      for (const r of e.rows) {
        labels.set(r.m1, r.l1);
        labels.set(r.m2, r.l2);
        pairKeys.set(`${r.m1}|${r.m2}`, { bridge: e, m1: r.m1, m2: r.m2 });
        pairKeys.set(`${r.m2}|${r.m1}`, { bridge: e, m1: r.m1, m2: r.m2 });
        for (const [a, b] of [
          [r.m1, r.m2],
          [r.m2, r.m1],
        ]) {
          if (!pairsByX.has(a)) pairsByX.set(a, new Map());
          pairsByX.get(a)!.set(b, { measure: b, rho: r.rho });
        }
      }
    }
    const xOptions = [...pairsByX.keys()].sort((a, b) =>
      (labels.get(a) ?? a).localeCompare(labels.get(b) ?? b),
    );
    return { xOptions, pairsByX, pairKeys };
  }, [bridges]);

  // the theme/concept search index: domain segments are the overall themes,
  // endpoint concept names the more specific entries
  const searchIndex = buildSearchIndex(bridges, concepts);

  const mlabel = (mid: string) => measures[mid]?.l ?? mid;

  const x = search.get("x");
  const y = search.get("y");
  const sel = x !== null && y !== null ? pairKeys.get(`${x}|${y}`) : undefined;
  const bridge = sel ? sel.bridge : null;
  const activeEntryIdx = bridge ? bridges.indexOf(bridge) : -1;

  const xId = sel ? (x === sel.m1 ? sel.m1 : sel.m2) : "";
  const yId = sel ? (x === sel.m1 ? sel.m2 : sel.m1) : "";
  const row = bridge
    ? bridge.rows.find(
        (r) => (r.m1 === xId && r.m2 === yId) || (r.m2 === xId && r.m1 === yId),
      ) ?? bridge.rows[0]
    : null;
  const rho = row ? row.rho : 0;

  const yOptions = pairsByX.get(xId) ?? new Map<string, PairOption>();

  const setPair = (nx: string, ny: string) => {
    setPickedKey(null); // new pair — fall back to its strongest hypothesis
    router.replace(`${pathname}?x=${encodeURIComponent(nx)}&y=${encodeURIComponent(ny)}`, {
      scroll: false,
    });
  };

  // chip click: select the pair and bring the full view (mounting below) into view
  const pickEntry = (entryIdx: number) => {
    const e = bridges[entryIdx]!;
    const r = e.rows[0]!;
    setPair(r.m1, r.m2);
    window.setTimeout(
      () => fullRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
      150,
    );
  };

  // every shipped connection, scored by its weakest link so chips and
  // corridors grade on one scale
  const conns = connsFor(bridge);

  // null pick = no hypothesis selected: the whole graph shows, unhighlighted
  const active = conns.find((c) => c.key === pickedKey) ?? null;

  const [topChips, restChips] = [
    conns.slice(0, TOP_CHIPS),
    conns.slice(TOP_CHIPS),
  ];
  const sMin = conns.length ? conns[conns.length - 1].strength : 0;
  const sMax = conns.length ? conns[0].strength : 1;
  const chipColor = (strength: number) => {
    const t =
      sMax === sMin ? 1 : (strength - sMin) / (sMax - sMin);
    return STRENGTH_RAMP[Math.round(t * (STRENGTH_RAMP.length - 1))];
  };

  const cite = (pmid: string) => setCitePmid(pmid);

  const chipEl = (c: Conn) => {
    const bg = chipColor(c.strength);
    const onBright = STRENGTH_RAMP.indexOf(bg) >= 8; // light fill → dark text
    const isOn = active?.key === c.key;
    return (
      <Badge
        key={c.key}
        variant="outline"
        asChild
        className={`max-w-full cursor-pointer px-3 py-1.5 font-sans text-[0.72rem] leading-tight ${
          isOn ? "border-[color:var(--ink)] ring-2 ring-[color:var(--ring)]" : "border-transparent"
        }`}
      >
        <button
          style={{ background: bg, color: onBright ? "var(--paper)" : "var(--ink)" }}
          onClick={() => setPickedKey((k) => (k === c.key ? null : c.key))}
          aria-pressed={isOn}
          title={`strength ${c.strength.toFixed(2)} — ${c.head}`}
        >
          {c.head}
        </button>
      </Badge>
    );
  };

  return (
    <div className="mt-8">
      {/* the search landing: theme box, category pick, candidate pair chips */}
      <div className="mx-auto w-full max-w-[72rem] px-6 sm:px-10">
        {!bridge && (
          <div className="mt-12 max-w-[62rem]">
            <h1 className="text-[clamp(1.8rem,4vw,2.6rem)] leading-tight font-normal">
              Which two measures should we <em>connect</em>?
            </h1>
            <p className="mt-3 text-[1.05rem] leading-relaxed text-[color:var(--chart-ink-2)]">
              Search an overall theme, pick a candidate pair, and the full
              connection view opens below.
            </p>
          </div>
        )}
        <div className={bridge ? "mt-8" : "mt-10"}>
          <span className="label">start from a theme</span>
          <div className="mt-2">
            <BridgeSearch
              index={searchIndex}
              bridges={bridges}
              activeEntryIdx={activeEntryIdx}
              onPickPair={pickEntry}
            />
          </div>
        </div>
      </div>

      {/* the full view: selectors, district maps, connection graph */}
      {bridge && row && (
        <div ref={fullRef}>
          <div className="mx-auto w-full max-w-[72rem] px-6 sm:px-10">
            <h1 className="mt-12 max-w-[62rem] text-[1.55rem] leading-relaxed sm:text-[1.85rem] sm:leading-[1.7]">
              How does{" "}
              <Select
                value={xId}
                onValueChange={(v) => {
                  const opts = pairsByX.get(v)!;
                  const keep = opts.has(yId) ? yId : [...opts.keys()][0];
                  setPair(v, keep);
                }}
              >
                <SelectTrigger
                  className="inline-flex h-[2.4rem] w-[280px] max-w-full align-baseline sm:w-[340px]"
                  aria-label="X — the first measure"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="max-w-[340px]">
                  {xOptions.map((m) => (
                    <SelectItem key={m} value={m}>
                      <span className="truncate">{mlabel(m)}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>{" "}
              connect to{" "}
              <Select value={yId} onValueChange={(v) => setPair(xId, v)}>
                <SelectTrigger
                  className="inline-flex h-[2.4rem] w-[280px] max-w-full align-baseline sm:w-[340px]"
                  aria-label="Y — the second measure"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="max-w-[360px]">
                  {[...yOptions.entries()].map(([m, opt]) => (
                    <SelectItem key={m} value={m}>
                      <span className="truncate">
                        {mlabel(m)} — ρ {fmtRho(opt.rho)}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              ?
            </h1>
            <p className="mt-2 max-w-[62rem] font-sans text-[0.75rem] text-muted">
              X and Y are measurements from the environment-health collection
              (Underlay); the network below is the SPG v1 research graph. ρ ={" "}
              <span className={rho >= 0 ? "text-[#3987e5]" : "text-[#e66767]"}>
                {fmtRho(rho)}
              </span>{" "}
              (Spearman across the 42 districts).
            </p>

            {/* district maps — the correlation, district by district */}
            <section className="mt-10">
              <h2 className="label">the city, district by district</h2>
              <DistrictMaps
                districts={districts}
                values={values}
                xMeasure={xId}
                yMeasure={yId}
                measures={measures}
                rho={rho}
              />
            </section>
          </div>

          {/* the connection graph in the main column, the findings as a Tufte
              sidenote in the reserved margin column */}
          <section className="mt-14">
            <div className="mx-auto w-full max-w-[72rem] px-6 sm:px-10">
              <h2 className="label">what the studies connect through</h2>

              <div
                className={`mt-4 grid gap-y-8 transition-[grid-template-columns,gap] duration-500 ease-in-out lg:items-start ${
                  active
                    ? "lg:grid-cols-[1fr_17rem] lg:gap-x-10"
                    : "lg:grid-cols-[1fr_0rem]"
                }`}
              >
                <div>
                  <ConnectionGraph
                    bridge={bridge}
                    concepts={concepts}
                    selected={active?.key ?? null}
                  />
                </div>

                <aside
                  aria-label="Hypothesis findings"
                  className="overflow-hidden text-[0.85rem] leading-[1.6] lg:sticky lg:top-6"
                >
                  {active && (
                    <div
                      key={active.key}
                      className="animate-[fade-up_0.45s_ease-out]"
                    >
                      <span className="label">findings</span>
                      <h3 className="mt-2 text-[1.05rem] font-medium leading-snug">
                        {active.head}
                      </h3>
                      <div className="mt-3 text-ink">
                        <StoryBody story={active.story} pms={active.pms} onCite={cite} />
                      </div>
                    </div>
                  )}
                </aside>
              </div>

              {/* hypothesis chips, strongest first, graded by evidence */}
              <div className="mt-8 flex flex-wrap gap-1.5">{topChips.map(chipEl)}</div>
              {restChips.length > 0 && (
                <details className="mt-3">
                  <summary className="cursor-pointer font-sans text-[0.75rem] text-muted hover:text-ink">
                    show {restChips.length} more hypotheses, graded by strength
                  </summary>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {restChips.map(chipEl)}
                  </div>
                </details>
              )}
            </div>
          </section>
        </div>
      )}

      {citePmid && <CitationSidebar key={citePmid} pmid={citePmid} onClose={() => setCitePmid(null)} />}
    </div>
  );
}
