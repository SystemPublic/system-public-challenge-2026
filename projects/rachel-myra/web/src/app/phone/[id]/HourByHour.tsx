"use client";

import { useState } from "react";
import { heatColor } from "@/components/replay/colors";

type Hour = { hour: number; f: number };

// Compact hour-by-hour heat for the patient plan: same hourly "feels like" data as Rachel's
// time-lapse (replay_heatwave_hourly.csv, June 24), one big line per hour. Drag the slider;
// the hour scale underneath shows where you are in the day.
const L = {
  en: {
    feels: "feels like",
    ok: "OK to go out", careful: "Be careful", stay: "Stay inside",
    drag: "Drag to see each hour",
    hour: (h: number) => (h === 0 ? "12 AM" : h < 12 ? `${h} AM` : h === 12 ? "12 PM" : `${h - 12} PM`),
  },
  es: {
    feels: "se siente como",
    ok: "Puede salir", careful: "Tenga cuidado", stay: "Quédese adentro",
    drag: "Deslice para ver cada hora",
    hour: (h: number) => (h === 0 ? "12 a.m." : h < 12 ? `${h} a.m.` : h === 12 ? "12 p.m." : `${h - 12} p.m.`),
  },
};

// The range thumb's center travels from THUMB_R to (100% - THUMB_R); the scale uses the same inset
// so each tick sits under the thumb position for its hour.
const THUMB_R = 12; // px

export function HourByHour({ hours, hotF, lang, startHour }: { hours: Hour[]; hotF: number; lang: "en" | "es"; startHour?: number }) {
  const l = L[lang];
  const first = Math.max(0, hours.findIndex((h) => h.hour === (startHour ?? 14)));
  const [i, setI] = useState(first);

  if (!hours.length) return null;
  const h = hours[Math.min(i, hours.length - 1)];
  const f = Math.round(h.f);
  const level = f >= hotF ? "high" : f >= hotF - 6 ? "medium" : "low";
  const word = level === "high" ? l.stay : level === "medium" ? l.careful : l.ok;
  const tone = {
    high: "bg-risk-high-tint text-risk-high-ink",
    medium: "bg-risk-medium-tint text-risk-medium-ink",
    low: "bg-risk-low-tint text-risk-low-ink",
  }[level];
  const last = hours.length - 1;
  const at = (k: number) => `calc(${THUMB_R}px + (100% - ${2 * THUMB_R}px) * ${last ? k / last : 0})`;

  return (
    <div className="space-y-3">
      <div className={`rounded-lg p-4 text-center ${tone}`} aria-live="polite">
        <p className="text-patient-xl font-bold leading-tight">{l.hour(h.hour)}</p>
        <p className="text-patient-lg font-semibold">{l.feels} {f}°F</p>
        <p className="text-patient-lg font-bold">{word}</p>
      </div>

      <div>
        {/* Heat strip: one cell per hour, centered under each slider stop. */}
        <div className="relative h-3" aria-hidden>
          {hours.map((x, k) => {
            const half = last ? `((100% - ${2 * THUMB_R}px) / ${last} / 2)` : "0px";
            return (
              <span
                key={x.hour}
                className={`absolute inset-y-0 ${k === 0 ? "rounded-l-full" : ""} ${k === last ? "rounded-r-full" : ""}`}
                style={{
                  left: k === 0 ? 0 : `calc(${at(k)} - ${half})`,
                  right: k === last ? 0 : `calc(100% - (${at(k)} + ${half}))`,
                  background: heatColor(x.f),
                  outline: k === i ? "2px solid currentColor" : undefined,
                  zIndex: k === i ? 1 : 0,
                }}
              />
            );
          })}
        </div>

        <input
          type="range"
          min={0}
          max={last}
          step={1}
          value={i}
          onChange={(e) => setI(Number(e.target.value))}
          aria-label={l.drag}
          aria-valuetext={`${l.hour(h.hour)}, ${l.feels} ${f}°F, ${word}`}
          className="mt-1 block h-tap w-full cursor-pointer accent-primary"
        />

        {/* Hour scale: a tick for every hour, a label every 3 hours. */}
        <div className="relative h-8 text-base text-muted-foreground" aria-hidden>
          {hours.map((x, k) => {
            const labelled = x.hour % 3 === 0;
            return (
              <span key={x.hour} className="absolute top-0 flex -translate-x-1/2 flex-col items-center" style={{ left: at(k) }}>
                <span className={`w-px bg-current ${labelled ? "h-2" : "h-1 opacity-50"}`} />
                {labelled && <span className={`whitespace-nowrap leading-tight ${k === i ? "font-semibold text-ink" : ""}`}>{l.hour(x.hour)}</span>}
              </span>
            );
          })}
        </div>
        <p className="mt-1 text-center text-base text-muted-foreground">{l.drag}</p>
      </div>
    </div>
  );
}
