"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import type { HeatGrid, ReplayData, ReplayPatient } from "@/lib/replay";
import { GROUP_COLORS, HEAT_STOPS, heatColor } from "./colors";
import { inArea, type Area } from "./area";

const GROUP_ORDER = { High: 0, Medium: 1, Low: 2 } as const;

const TimelapseMap = dynamic(() => import("./TimelapseMap"), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse bg-surface" />,
});

const STEPS_PER_HOUR = 6; // smooth morphing between hourly frames
const SPEEDS = [
  { label: "Slow", ms: 120 },
  { label: "Normal", ms: 50 },
  { label: "Fast", ms: 20 },
];
const HEATRISK_WORDS = ["Little or no risk", "Minor risk", "Moderate risk", "Major risk", "Extreme risk"];

const DAY = new Intl.DateTimeFormat("en-US", { weekday: "short", month: "short", day: "numeric", timeZone: "UTC" });
const fmtDate = (d: string) => DAY.format(new Date(d.slice(0, 10) + "T12:00:00Z"));
function fmtHour(h: number) {
  const hh = Math.floor(h) % 24;
  const mm = Math.round((h - Math.floor(h)) * 60) % 60;
  const h12 = hh % 12 === 0 ? 12 : hh % 12;
  return `${h12}${mm ? ":" + String(mm).padStart(2, "0") : ""} ${hh < 12 ? "AM" : "PM"}`;
}

/** "Feels like" at a point, bilinear from the grid. */
function heatAt(grid: HeatGrid, t: number, lat: number, lon: number): number | null {
  const { lats, lons } = grid;
  const gy = (lat - lats[0]) / (lats[1] - lats[0]);
  const gx = (lon - lons[0]) / (lons[1] - lons[0]);
  const i = Math.max(0, Math.min(lats.length - 2, Math.floor(gy)));
  const j = Math.max(0, Math.min(lons.length - 2, Math.floor(gx)));
  const fy = Math.min(1, Math.max(0, gy - i)), fx = Math.min(1, Math.max(0, gx - j));
  const f = grid.f[t];
  const v = [f[i][j], f[i][j + 1], f[i + 1][j], f[i + 1][j + 1]];
  if (v.some((x) => x == null)) return null;
  const [a, b, c, d] = v as number[];
  return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy;
}

export function Timelapse({ data, embedded = false }: { data: ReplayData; embedded?: boolean }) {
  const { grid } = data;
  const nHours = grid.times.length;
  const total = (nHours - 1) * STEPS_PER_HOUR;
  // Start on the worst day's morning, so the first frame already shows something.
  const startStep = Math.max(0, grid.times.findIndex((t) => t.startsWith(data.eventDate) && t.endsWith("06:00"))) * STEPS_PER_HOUR;
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [selected, setSelected] = useState<ReplayPatient | null>(null);
  const [route, setRoute] = useState<[number, number][] | null>(null);
  const [routeNote, setRouteNote] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!playing) return;
    timer.current = setInterval(() => {
      setStep((s) => {
        if (s >= total) {
          setPlaying(false);
          return s;
        }
        return s + 1;
      });
    }, SPEEDS[speed].ms);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [playing, speed, total]);

  const tf = step / STEPS_PER_HOUR;
  const idx = Math.min(Math.floor(tf), nHours - 1);
  const time = grid.times[idx];
  const date = time.slice(0, 10);
  const clock = Number(time.slice(11, 13)) + (tf - idx);

  // Heat where the patients live (their average location), for the clock card and the strip.
  const center = useMemo(() => {
    const n = Math.max(1, data.patients.length);
    return { lat: data.patients.reduce((s, p) => s + p.lat, 0) / n, lon: data.patients.reduce((s, p) => s + p.lon, 0) / n };
  }, [data.patients]);
  const strip = useMemo(() => grid.times.map((_, t) => heatAt(grid, t, center.lat, center.lon)), [grid, center]);
  // Horizontal position of hour t on the scrubber, matching the range thumb's center
  // (it travels from THUMB_R to 100% - THUMB_R).
  const THUMB_R = 8;
  const at = (t: number) => `(${THUMB_R}px + (100% - ${2 * THUMB_R}px) * ${nHours > 1 ? t / (nHours - 1) : 0})`;
  const halfHour = `((100% - ${2 * THUMB_R}px) / ${Math.max(1, nHours - 1)} / 2)`;
  const hereNow = (() => {
    const a = strip[idx], b = strip[Math.min(idx + 1, nHours - 1)];
    return a != null && b != null ? a + (b - a) * (tf - idx) : a;
  })();
  const heatrisk = data.heatriskByDate[date];
  const counts = useMemo(() => {
    const c = { High: 0, Medium: 0, Low: 0 };
    for (const p of data.patients) c[p.group]++;
    return c;
  }, [data.patients]);

  // Area select: drag a box on the map → everyone inside is listed in the sidebar.
  const [selecting, setSelecting] = useState(false);
  const [area, setArea] = useState<Area | null>(null);
  const areaPeople = useMemo(
    () =>
      area
        ? data.patients
            .filter((p) => inArea(area, p))
            .sort((a, b) => GROUP_ORDER[a.group] - GROUP_ORDER[b.group] || a.name.localeCompare(b.name))
        : [],
    [area, data.patients],
  );
  useEffect(() => {
    if (!selecting) return;
    const k = (e: KeyboardEvent) => e.key === "Escape" && setSelecting(false);
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [selecting]);
  function pickArea(a: Area | null) {
    setSelecting(false);
    setArea(a);
    select(null);
  }

  function select(p: ReplayPatient | null) {
    setSelected(p);
    setRoute(null);
    setRouteNote(null);
  }

  async function showWay() {
    if (!selected?.place) return;
    setRouteNote("Finding the way…");
    const from = `${selected.lon},${selected.lat}`;
    const to = `${selected.place.lon},${selected.place.lat}`;
    const d = await fetch(`/api/route?from=${from}&to=${to}`).then((r) => r.json()).catch(() => null);
    if (d?.ok && d.geometry?.coordinates) {
      setRoute(d.geometry.coordinates);
      setRouteNote(null);
    } else {
      setRoute([
        [selected.lon, selected.lat],
        [selected.place.lon, selected.place.lat],
      ]);
      setRouteNote("Street route unavailable right now; showing a straight line.");
    }
  }

  return (
    <div className={embedded ? "flex flex-col gap-4" : "mx-auto flex max-w-7xl flex-col gap-4 px-4 py-6"}>
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          {embedded ? (
            <h2 className="text-xl font-bold tracking-tight">The June 2025 heat wave, hour by hour</h2>
          ) : (
            <h1 className="text-2xl font-bold tracking-tight md:text-3xl">The June 2025 heat wave, hour by hour</h1>
          )}
          <p className="mt-1 text-ink-muted">Watch the heat roll over the city. Click any patient to see their plan, or select an area to list everyone in it.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => {
              if (step >= total) setStep(0);
              setPlaying((p) => !p);
            }}
            className="rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90"
          >
            {playing ? "Pause" : step >= total ? "Replay" : "Play"}
          </button>
          <button
            type="button"
            onClick={() => {
              setPlaying(false);
              setStep(startStep);
            }}
            className="rounded-full border border-line-strong px-4 py-2 text-sm hover:bg-surface"
          >
            Jump to the worst day
          </button>
          <div className="flex overflow-hidden rounded-full border border-line-strong text-sm" role="group" aria-label="Speed">
            {SPEEDS.map((s, i) => (
              <button
                key={s.label}
                type="button"
                onClick={() => setSpeed(i)}
                aria-pressed={i === speed}
                className={`px-3 py-2 ${i === speed ? "bg-surface font-semibold" : "hover:bg-surface"}`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
        <div className="relative h-[64vh] min-h-[440px] overflow-hidden rounded-tile border border-line">
          <TimelapseMap
            grid={grid}
            tf={tf}
            patients={data.patients}
            selected={selected}
            route={route}
            onSelect={select}
            selecting={selecting}
            area={area}
            onArea={pickArea}
          />
          {/* Top-right corner of the map */}
          <button
            type="button"
            onClick={() => setSelecting((s) => !s)}
            aria-pressed={selecting}
            className={`absolute right-3 top-3 z-20 rounded-full border-2 border-layer-graph-fg px-3.5 py-1.5 text-sm font-semibold shadow-sm ${
              selecting ? "bg-layer-graph-fg text-white" : "bg-page text-layer-graph-fg hover:bg-layer-graph-bg"
            }`}
          >
            {selecting ? "Cancel selecting" : "Select an area"}
          </button>
          {selecting && (
            <div className="pointer-events-none absolute bottom-10 left-1/2 z-20 -translate-x-1/2 whitespace-nowrap rounded-full bg-layer-graph-fg px-4 py-1.5 text-sm font-semibold text-white shadow">
              Drag a box around the people you want to see · Esc to cancel
            </div>
          )}
          <div className="pointer-events-none absolute left-3 top-3 rounded-tile bg-page/95 px-4 py-3 shadow-sm">
            <div className="text-sm text-ink-muted">{fmtDate(date)}</div>
            <div className="text-3xl font-bold tabular-nums">{fmtHour(clock)}</div>
            <div className="mt-1 flex items-center gap-2">
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: heatColor(hereNow) }} />
              <span className="text-lg font-semibold tabular-nums">Feels like {hereNow != null ? Math.round(hereNow) : "—"}°F</span>
            </div>
            <div className="text-xs text-ink-muted">where the patients live</div>
          </div>
          <div className="absolute bottom-8 left-3 rounded-tile bg-page/95 px-3 py-2 text-xs shadow-sm">
            <div className="font-semibold">Feels like</div>
            <div
              className="mt-1 h-2.5 w-44 rounded"
              style={{
                background: `linear-gradient(90deg, ${HEAT_STOPS.slice(1)
                  .map(([, r, g, b]) => `rgb(${r},${g},${b})`)
                  .join(",")})`,
              }}
            />
            <div className="mt-0.5 flex w-44 justify-between text-ink-muted">
              <span>88°</span>
              <span>100°</span>
              <span>116°+</span>
            </div>
          </div>
        </div>

        <aside className="flex flex-col gap-3">
          {selected ? (
            <PatientCard
              p={selected}
              onClose={() => select(null)}
              onShowWay={showWay}
              routeShown={!!route}
              routeNote={routeNote}
              backLabel={area ? `Back to the ${areaPeople.length} ${areaPeople.length === 1 ? "person" : "people"} in this area` : null}
            />
          ) : area ? (
            <AreaList people={areaPeople} onPick={select} onClear={() => pickArea(null)} onRedo={() => setSelecting(true)} />
          ) : (
            <>
              <section className="rounded-tile border border-line bg-page p-4">
                <h2 className="text-sm font-semibold text-ink-muted">Bronx heat warning that day</h2>
                <p className="mt-1 text-xl font-bold">{heatrisk != null ? HEATRISK_WORDS[heatrisk] ?? `Level ${heatrisk}` : "No forecast on file"}</p>
                {heatrisk != null && <p className="text-sm text-ink-muted">Level {heatrisk} of 4, National Weather Service HeatRisk</p>}
              </section>
              <section className="rounded-tile border border-line bg-page p-4">
                <h2 className="text-sm font-semibold text-ink-muted">Patients by risk (synthetic)</h2>
                <ul className="mt-2 space-y-1.5">
                  {(["High", "Medium", "Low"] as const).map((g) => (
                    <li key={g} className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <span className="inline-block h-3.5 w-3.5 rounded-full" style={{ background: GROUP_COLORS[g].css, outline: g === "Medium" ? `1px solid ${GROUP_COLORS.Medium.ink}` : undefined }} />
                        {g}
                      </span>
                      <span className="font-semibold tabular-nums">{counts[g]}</span>
                    </li>
                  ))}
                </ul>
              </section>
              <section className="rounded-tile border border-dashed border-line-strong bg-surface p-4 text-sm">
                <p className="font-semibold">Click a patient on the map</p>
                <p className="mt-1 text-ink-muted">See why they&apos;re at risk, how their medicines and the heat add up, where their nearest cool place is, and the way there. Then message them.</p>
                <p className="mt-2 font-semibold">Or select an area</p>
                <p className="mt-1 text-ink-muted">Press &ldquo;Select an area&rdquo; and drag a box on the map to list everyone inside it.</p>
              </section>
            </>
          )}
        </aside>
      </div>

      {/* Scrubber over the heat strip */}
      <div>
        {/* Strip, slider and time scale share one horizontal scale: hour t sits at at(t), the same
            spot as the slider thumb for that hour (the thumb's center is inset by its radius). */}
        <div className="relative h-7 overflow-hidden rounded" aria-hidden>
          {strip.map((v, i) => (
            <div
              key={i}
              className="absolute inset-y-0"
              style={{
                left: i === 0 ? 0 : `calc(${at(i)} - ${halfHour})`,
                right: i === nHours - 1 ? 0 : `calc(100% - ${at(i)} - ${halfHour})`,
                background: heatColor(v),
              }}
              title={`${fmtDate(grid.times[i])} ${fmtHour(Number(grid.times[i].slice(11, 13)))}: feels like ${v != null ? Math.round(v) : "—"}°F`}
            />
          ))}
        </div>
        <input
          type="range"
          min={0}
          max={total}
          value={step}
          onChange={(e) => {
            setPlaying(false);
            setStep(Number(e.target.value));
          }}
          aria-label="Time"
          aria-valuetext={`${fmtDate(date)}, ${fmtHour(clock)}${hereNow != null ? `, feels like ${Math.round(hereNow)}°F` : ""}`}
          className="mt-1 block w-full cursor-pointer accent-[#d55e00]"
        />
        {/* Time-of-day scale: tick every 3 h, label every 6 h (6 AM · noon · 6 PM), day name at midnight. */}
        <div className="relative h-11 text-xs text-ink-muted" aria-hidden>
          {grid.times.map((t, i) => {
            const h = Number(t.slice(11, 13));
            if (h % 3 !== 0) return null;
            const midnight = h === 0;
            const labelled = midnight || h % 6 === 0;
            const now = idx === i;
            // The very first label starts at the left edge instead of centering past it.
            const edge = i === 0 ? "items-start" : "-translate-x-1/2 items-center";
            return (
              <span key={t} className={`absolute top-0 flex flex-col ${edge}`} style={{ left: `calc${at(i)}` }}>
                <span className={`w-px ${midnight ? "h-3 bg-ink" : labelled ? "h-2 bg-current" : "h-1.5 bg-current opacity-50"}`} />
                {midnight ? (
                  <span className="mt-0.5 whitespace-nowrap font-semibold text-ink">{fmtDate(t)}</span>
                ) : labelled ? (
                  <span className={`mt-0.5 hidden whitespace-nowrap sm:block ${now ? "font-semibold text-ink" : ""}`}>
                    {h === 12 ? "Noon" : fmtHour(h)}
                  </span>
                ) : null}
              </span>
            );
          })}
        </div>
        <details className="mt-3 text-xs text-ink-muted">
          <summary className="cursor-pointer">Where this comes from</summary>
          <ul className="mt-1 list-disc pl-5">
            {data.sources.map((s) => (
              <li key={s}>{s}</li>
            ))}
            <li>Map: © OpenStreetMap contributors, OpenFreeMap. Weather data by Open-Meteo.com (CC BY 4.0).</li>
          </ul>
        </details>
      </div>
    </div>
  );
}

function AreaList({
  people,
  onPick,
  onClear,
  onRedo,
}: {
  people: ReplayPatient[];
  onPick: (p: ReplayPatient) => void;
  onClear: () => void;
  onRedo: () => void;
}) {
  const counts = { High: 0, Medium: 0, Low: 0 };
  for (const p of people) counts[p.group]++;
  return (
    <section className="flex max-h-[64vh] flex-col overflow-hidden rounded-tile border border-line bg-page">
      <div className="border-b-4 border-b-layer-graph-fg bg-layer-graph-bg p-4">
        <div className="flex items-start justify-between gap-2">
          <h2 className="text-lg font-bold">
            {people.length} {people.length === 1 ? "person" : "people"} in this area
          </h2>
          <button type="button" onClick={onClear} className="rounded-full px-2 text-xl leading-none text-ink-muted hover:bg-page" aria-label="Clear area">
            ×
          </button>
        </div>
        <ul className="mt-2 flex flex-wrap gap-1.5 text-xs font-semibold">
          {(["High", "Medium", "Low"] as const).map((g) => (
            <li key={g} className="inline-flex items-center gap-1.5 rounded-full border bg-page px-2.5 py-0.5" style={{ borderColor: GROUP_COLORS[g].ink, color: GROUP_COLORS[g].ink }}>
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: GROUP_COLORS[g].css }} />
              {counts[g]} {g.toLowerCase()}
            </li>
          ))}
        </ul>
        <button type="button" onClick={onRedo} className="mt-2 text-sm font-semibold text-layer-graph-fg underline underline-offset-2">
          Select a different area
        </button>
      </div>
      {people.length === 0 ? (
        <p className="p-4 text-sm text-ink-muted">No patients live inside this box. Try a bigger area.</p>
      ) : (
        <ul className="divide-y divide-line overflow-y-auto">
          {people.map((p) => {
            const c = GROUP_COLORS[p.group];
            return (
              <li key={p.id}>
                <button
                  type="button"
                  onClick={() => onPick(p)}
                  className="flex w-full items-start gap-3 border-l-4 px-4 py-3 text-left text-sm hover:bg-surface focus-visible:bg-surface"
                  style={{ borderLeftColor: c.css }}
                >
                  <span className="min-w-0 flex-1">
                    <span className="flex flex-wrap items-center gap-x-2">
                      <span className="font-semibold">{p.name}</span>
                      <span className="text-ink-muted">{p.age}</span>
                      <span className="rounded-full px-2 py-px text-xs font-semibold" style={{ background: c.tint, color: c.ink }}>
                        {p.group}
                      </span>
                    </span>
                    {p.why[0] && <span className="mt-0.5 block truncate text-ink-muted">{p.why.join(" · ")}</span>}
                  </span>
                  <span aria-hidden className="self-center text-ink-muted">›</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function PatientCard({
  p,
  onClose,
  onShowWay,
  routeShown,
  routeNote,
  backLabel = null,
}: {
  p: ReplayPatient;
  onClose: () => void;
  onShowWay: () => void;
  routeShown: boolean;
  routeNote: string | null;
  /** When the patient was opened from an area list: a link back to it. */
  backLabel?: string | null;
}) {
  const c = GROUP_COLORS[p.group];
  const cool = GROUP_COLORS.Low;
  const facts = p.place
    ? [
        p.place.walkMin != null ? `${Math.round(p.place.walkMin)} min walk` : null,
        p.place.leaveBy ? `Leave by ${p.place.leaveBy}` : null,
        p.place.arriveBy ? `Arrive by ${p.place.arriveBy}` : null,
        p.place.hours ? `Open ${p.place.hours}` : null,
      ].filter((x): x is string => !!x)
    : [];
  return (
    <section className="flex max-h-[64vh] flex-col overflow-y-auto rounded-tile border border-line bg-page">
      {backLabel && (
        <button type="button" onClick={onClose} className="border-b border-line px-4 py-2 text-left text-sm font-semibold text-layer-graph-fg hover:bg-surface">
          ← {backLabel}
        </button>
      )}
      {/* Header band in the patient's risk-group color */}
      <div className="flex items-start justify-between gap-2 border-b-4 p-4" style={{ background: c.tint, borderBottomColor: c.css }}>
        <div>
          <h2 className="text-lg font-bold">{p.name}</h2>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm">
            <span className="inline-flex items-center gap-1.5 rounded-full border-2 bg-page px-2.5 py-0.5 text-xs font-semibold" style={{ borderColor: c.ink, color: c.ink }}>
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: c.css }} />
              {p.group} risk
            </span>
            <span className="text-ink-muted">{p.age} · synthetic patient</span>
          </div>
        </div>
        <button type="button" onClick={onClose} className="rounded-full px-2 text-xl leading-none text-ink-muted hover:bg-page" aria-label="Close">
          ×
        </button>
      </div>

      <div className="space-y-4 p-4 text-sm">
        {p.why.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Why</h3>
            <ul className="mt-1.5 flex flex-wrap gap-1.5">
              {p.why.map((w) => (
                <li key={w} className="rounded-full border border-line bg-surface px-2.5 py-0.5">{w}</li>
              ))}
            </ul>
          </div>
        )}

        {p.meds.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Their medicines and the heat</h3>
            {p.shared.length > 0 && (
              <p className="mt-1.5 rounded-tile border-l-4 px-3 py-2 font-semibold" style={{ background: GROUP_COLORS.High.tint, color: GROUP_COLORS.High.ink, borderLeftColor: GROUP_COLORS.High.css }}>
                {p.shared.map((s) => `${s.meds.join(" and ")} both raise the risk of ${s.effect}`).join(". ")}, and so does the heat.
              </p>
            )}
            <ul className="mt-2 space-y-2">
              {p.meds.map((m) => (
                <li key={m.name} className="rounded-tile border border-line border-l-4 border-l-layer-graph-fg bg-surface p-3">
                  <div className="font-semibold capitalize">{m.name}</div>
                  {m.links.length ? (
                    <ul className="mt-2 space-y-1.5">
                      {m.links.slice(0, 3).map((l) => (
                        <li key={l.effect} className="flex flex-wrap items-center gap-1.5">
                          <span className="rounded bg-layer-graph-bg px-2 py-0.5 font-semibold text-layer-graph-fg">{l.effect}</span>
                          <span className="inline-flex items-center gap-1 rounded-full border border-line bg-page py-0.5 pl-2 pr-1 text-xs">
                            medicine
                            <b className="rounded-full bg-layer-graph-bg px-1.5 tabular-nums text-layer-graph-fg">{l.drugStudies}</b>
                          </span>
                          <span className="inline-flex items-center gap-1 rounded-full border border-line bg-page py-0.5 pl-2 pr-1 text-xs">
                            heat
                            <b className="rounded-full bg-hold-tint px-1.5 tabular-nums text-hold-ink">{l.heatStudies}</b>
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-1 text-ink-muted">No medicine → body-effect link in the System graph yet</p>
                  )}
                </li>
              ))}
            </ul>
            <p className="mt-1.5 text-xs text-ink-muted">Numbers are studies in the System graph: medicine → effect, and heat → effect.</p>
          </div>
        )}

        {p.place ? (
          <div className="rounded-tile border border-l-4 p-3" style={{ background: cool.tint, borderColor: cool.css, color: cool.ink }}>
            <h3 className="text-xs font-semibold uppercase tracking-wide">Nearest cool place</h3>
            <p className="mt-1 text-base font-bold text-ink">{p.place.name}</p>
            {p.place.address && <p className="text-ink-muted">{p.place.address}</p>}
            {facts.length > 0 && (
              <ul className="mt-2 flex flex-wrap gap-1.5">
                {facts.map((f) => (
                  <li key={f} className="rounded-full bg-page px-2.5 py-0.5 font-semibold tabular-nums" style={{ color: cool.ink }}>{f}</li>
                ))}
              </ul>
            )}
            {p.place.needsHelp && (
              <p className="mt-2 inline-block rounded-full px-2.5 py-0.5 font-semibold" style={{ background: GROUP_COLORS.High.tint, color: GROUP_COLORS.High.ink }}>
                Needs someone to go with them
              </p>
            )}
            <div>
              <button
                type="button"
                onClick={onShowWay}
                className="mt-3 rounded-full px-4 py-1.5 font-semibold text-white hover:opacity-90"
                style={{ background: cool.ink }}
              >
                {routeShown ? "Showing the way" : "Show the way"}
              </button>
            </div>
            {routeNote && <p className="mt-1 text-xs text-ink-muted">{routeNote}</p>}
          </div>
        ) : (
          <p className="rounded-tile border border-dashed border-line-strong bg-surface p-3 text-ink-muted">No cool place matched for this patient.</p>
        )}

        <Link href={`/messages/${p.id}`} className="block rounded-full bg-primary px-4 py-2 text-center font-semibold text-primary-foreground hover:opacity-90">
          Message {p.name.split(" ")[0]}
        </Link>
      </div>
    </section>
  );
}
