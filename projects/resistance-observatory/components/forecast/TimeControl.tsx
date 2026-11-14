"use client";

import { useEffect, useRef, useState } from "react";
import { GENOME_MAX_YEAR } from "@/lib/forecast/data";

const BTN =
  "inline-flex h-8 min-w-8 px-2.5 text-sm tabular-nums whitespace-nowrap gap-1 items-center justify-center rounded-[5px] border border-line-strong bg-surface-2 text-fg hover:border-drug focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-drug disabled:cursor-not-allowed disabled:opacity-40";

export function TimeControl(props: {
  year: number;
  minYear: number;
  maxYear: number;
  onChange: (year: number) => void;
  markedYears?: number[];
  className?: string;
}): React.JSX.Element {
  const { year, minYear, maxYear, onChange, markedYears, className } = props;
  const [playing, setPlaying] = useState(false);
  const [reduced, setReduced] = useState(false);
  const yearRef = useRef(year);
  yearRef.current = year;
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const h = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener("change", h);
    return () => mq.removeEventListener("change", h);
  }, []);

  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => {
      const next = yearRef.current + 1;
      if (next >= maxYear) setPlaying(false);
      if (next <= maxYear) onChangeRef.current(next);
    }, reduced ? 1200 : 700);
    return () => window.clearInterval(id);
  }, [playing, reduced, maxYear]);

  const manual = (y: number) => {
    setPlaying(false);
    onChange(Math.min(maxYear, Math.max(minYear, y)));
  };

  const togglePlay = () => {
    if (playing) {
      setPlaying(false);
      return;
    }
    if (year >= maxYear) onChange(minYear);
    setPlaying(true);
  };

  const span = Math.max(1, maxYear - minYear);
  const ticks = (markedYears ?? []).filter((y) => y >= minYear && y <= maxYear);

  return (
    <div className={`fc-card w-full max-w-[520px] px-4 py-2 ${className ?? ""}`}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-baseline gap-2">
          <span className="text-xs uppercase tracking-[0.18em] text-muted">As of</span>
          <span className="text-4xl font-semibold leading-none tabular-nums text-fg">{year}</span>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" className={BTN} aria-label="Previous year" disabled={year <= minYear} onClick={() => manual(year - 1)}>
            <span aria-hidden>{year > minYear ? `‹ ${year - 1}` : "‹"}</span>
          </button>
          <button type="button" className={BTN} aria-label={playing ? "Pause" : "Play through the years"} onClick={togglePlay}>
            <span aria-hidden>{playing ? "❚❚ Pause" : "▶ Play"}</span>
          </button>
          <button type="button" className={BTN} aria-label="Next year" disabled={year >= maxYear} onClick={() => manual(year + 1)}>
            <span aria-hidden>{year < maxYear ? `${year + 1} ›` : "›"}</span>
          </button>
        </div>
      </div>

      <div className="mt-1">
        <div className="relative">
          <input
            id="fc-asof-year"
            type="range"
            min={minYear}
            max={maxYear}
            step={1}
            value={year}
            aria-valuetext={`As of ${year}`}
            onChange={(e) => manual(Number(e.target.value))}
            className="block h-5 w-full cursor-pointer accent-drug focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-drug"
          />
          <div aria-hidden className="pointer-events-none relative mx-[8px] h-2">
            {ticks.map((y) => (
              <span
                key={y}
                className="absolute top-0 h-2 w-px bg-signal"
                style={{ left: `${((y - minYear) / span) * 100}%` }}
              />
            ))}
          </div>
        </div>
        <div className="flex justify-between text-xs tabular-nums text-muted">
          <label htmlFor="fc-asof-year" className="sr-only">           As-of year         </label>
          <span>{minYear}</span>
          <span>{maxYear}</span>
        </div>
      </div>

      <p className="mt-0.5 text-xs leading-snug text-muted">
        {year <= GENOME_MAX_YEAR
          ? `Genomes: collected through ${year} · Papers, Graph findings: published through ${year}`
          : `Genomes: collected through ${GENOME_MAX_YEAR}, where this dataset ends · Papers, Graph findings: published through ${year}`}
      </p>
    </div>
  );
}
