"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { WhoBasis } from "@/lib/alert/derive";
import css from "./alert.module.css";

export type CountryRow = {
  iso3: string;
  name: string;
  basis: WhoBasis;
  /** Sampled years (cells with any data). */
  cells: number;
  /** Cells meeting the minimum sample size. */
  qualifying: number;
  /** PubMed papers on the marker that name this country. */
  papers: number;
};

const GROUPS: { basis: WhoBasis; title: string; sub: string }[] = [
  { basis: "east_southern_africa", title: "East & Southern Africa", sub: "WHO K540E bands" },
  { basis: "central_west_africa", title: "Central & West Africa", sub: "emergence presets" },
  { basis: "outside_africa", title: "Outside Africa", sub: "presets" },
];

/** The [Country] token in the watch sentence: a structured picker, grouped by how WHO grades the region. */
export function CountryPicker({ rows, value, minN, onChange }: { rows: CountryRow[]; value: string; minN: number; onChange: (iso3: string) => void }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const wrap = useRef<HTMLSpanElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const id = useId();
  const current = rows.find((r) => r.iso3 === value);

  useEffect(() => {
    if (!open) return;
    input.current?.focus();
    const onDown = (e: MouseEvent) => {
      if (wrap.current && !wrap.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  const needle = q.trim().toLowerCase();
  const match = (r: CountryRow) => !needle || r.name.toLowerCase().includes(needle) || r.iso3.toLowerCase().includes(needle);
  const flat = GROUPS.flatMap((g) => rows.filter((r) => r.basis === g.basis && match(r)));

  const pick = (iso3: string) => {
    onChange(iso3);
    setOpen(false);
    setQ("");
  };

  return (
    <span
      ref={wrap}
      className="relative inline"
      onKeyDown={(e) => {
        if (e.key === "Escape" && open) {
          e.stopPropagation();
          setOpen(false);
        }
      }}
    >
      <button type="button" className={css.tokenButton} aria-haspopup="dialog" aria-expanded={open} aria-controls={id} onClick={() => setOpen((o) => !o)}>
        {current?.name ?? value}
        {" "}
        <span className={css.tokenCaret} aria-hidden>
          ▼
        </span>
      </button>
      {open ? (
        <div
          id={id}
          role="dialog"
          aria-label="Choose a country"
          className="absolute left-0 top-full z-30 mt-2 w-[min(30rem,calc(100vw-3rem))] rounded-[var(--radius)] border border-line-strong bg-surface p-3 font-sans text-sm font-normal leading-normal tracking-normal shadow-[var(--shadow)]"
        >
          <input
            ref={input}
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && flat[0]) pick(flat[0].iso3);
            }}
            placeholder="Filter countries…"
            aria-label="Filter countries"
            className="h-9 w-full rounded-full border border-line-strong bg-bg px-3.5 text-sm"
          />
          <div className="mt-2 max-h-[22rem] overflow-y-auto pr-1">
            {GROUPS.map((g) => {
              const list = rows.filter((r) => r.basis === g.basis && match(r));
              if (list.length === 0) return null;
              return (
                <div key={g.basis} className="mb-2">
                  <p className="sticky top-0 flex items-baseline justify-between gap-2 bg-surface py-1.5 font-mono text-[0.66rem] uppercase tracking-[0.14em] text-muted">
                    <span>
                      <span className="text-fg">{g.title}</span> · {g.sub}
                    </span>
                    <span className="normal-case tracking-normal">cells n≥{minN} · papers</span>
                  </p>
                  <ul>
                    {list.map((r) => (
                      <li key={r.iso3}>
                        <button
                          type="button"
                          onClick={() => pick(r.iso3)}
                          aria-current={r.iso3 === value}
                          className={`grid w-full grid-cols-[1fr_auto_auto] items-center gap-3 rounded-md px-2 py-1.5 text-left hover:bg-surface-2 ${r.iso3 === value ? "bg-surface-2 font-semibold" : ""}`}
                        >
                          <span className="truncate">
                            {r.name} <span className="font-mono text-[0.66rem] font-normal text-muted">{r.iso3}</span>
                          </span>
                          <span className="font-mono text-[0.72rem] tabular-nums text-muted" title={`${r.qualifying} of ${r.cells} sampled years have at least ${minN} samples`}>
                            <span className={r.qualifying > 0 ? "text-fg" : ""}>{r.qualifying}</span>/{r.cells} yrs
                          </span>
                          <span className="w-16 text-right font-mono text-[0.72rem] tabular-nums text-muted" title={`${r.papers} PubMed papers on the marker name ${r.name}`}>
                            <span className={r.papers > 0 ? "text-gap" : ""}>{r.papers}</span> paper{r.papers === 1 ? "" : "s"}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
            {flat.length === 0 ? <p className="px-2 py-4 text-muted">No country with genome counts matches “{q}”. Countries without data are not listed: not sampled is not zero.</p> : null}
          </div>
        </div>
      ) : null}
    </span>
  );
}
