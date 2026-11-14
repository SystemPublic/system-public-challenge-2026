"use client";

// Patient "medicine cabinet": the patient's own medicine bottles on a shelf, with stems running to
// what each one can do to their body in the heat. Hover or tap bottles (several at once) to light up
// their effects; effects hit by 2+ chosen medicines are marked "adds up".
// Data: panel_scores_replay.json → patients[].stacking.mechanisms (label, drugs). Nothing invented.

import { useMemo, useRef, useState, useLayoutEffect } from "react";

export interface CabinetEffect {
  id: string;
  title: string; // e.g. "Blood pressure"
  signs: string | null; // e.g. "dizziness, fainting"
  drugs: string[];
}

// Bottle colors from the app palette (app teal + Okabe–Ito).
const BOTTLE = ["#0e7c86", "#e69f00", "#cc79a7", "#009e73", "#d55e00", "#56b4e9"];

export function MedicineCabinet({ effects, title = "Your medicines in the heat", hint = "Tap your medicines.", addsUp = "Adds up", compact = false }: {
  effects: CabinetEffect[];
  title?: string;
  hint?: string;
  addsUp?: string;
  /** Clinician view with many medicines: narrower bottles so one row fits ~15. Patient view unchanged. */
  compact?: boolean;
}) {
  const drugs = useMemo(() => Array.from(new Set(effects.flatMap((e) => e.drugs))), [effects]);
  const color = useMemo(() => new Map(drugs.map((d, i) => [d, BOTTLE[i % BOTTLE.length]])), [drugs]);
  const [picked, setPicked] = useState<string[]>([]);
  const [hover, setHover] = useState<string | null>(null);
  const active = hover && !picked.includes(hover) ? [...picked, hover] : picked;

  // Stem geometry: measured from the DOM so it works at any width.
  const box = useRef<HTMLDivElement | null>(null);
  const bottleRefs = useRef(new Map<string, HTMLElement>());
  const effRefs = useRef(new Map<string, HTMLElement>());
  const [lines, setLines] = useState<{ d: string; drug: string; eff: string }[]>([]);
  const [size, setSize] = useState({ w: 0, h: 0 });
  useLayoutEffect(() => {
    const measure = () => {
      const root = box.current?.getBoundingClientRect();
      if (!root) return;
      const out: { d: string; drug: string; eff: string }[] = [];
      for (const e of effects) {
        const er = effRefs.current.get(e.id)?.getBoundingClientRect();
        if (!er) continue;
        for (const d of e.drugs) {
          const br = bottleRefs.current.get(d)?.getBoundingClientRect();
          if (!br) continue;
          const x1 = br.left + br.width / 2 - root.left, y1 = br.bottom - root.top;
          const x2 = er.left + er.width / 2 - root.left, y2 = er.top - root.top;
          const my = (y1 + y2) / 2;
          out.push({ d: `M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2}`, drug: d, eff: e.id });
        }
      }
      setLines(out);
      setSize({ w: root.width, h: root.height });
    };
    measure();
    // Re-measure once fonts settle (labels can rewrap), and on any resize.
    document.fonts?.ready.then(measure).catch(() => {});
    const ro = new ResizeObserver(measure);
    if (box.current) ro.observe(box.current);
    return () => ro.disconnect();
  }, [effects, drugs]);

  if (!effects.length) return null;
  const toggle = (d: string) => setPicked((p) => (p.includes(d) ? p.filter((x) => x !== d) : [...p, d]));
  const hits = (e: CabinetEffect) => e.drugs.filter((d) => active.includes(d));
  const anyActive = active.length > 0;

  return (
    <section className="space-y-2">
      <h2 className="text-patient-lg font-bold">{title}</h2>
      <p className="text-base text-ink-muted">{hint}</p>
      <div ref={box} className="relative rounded-2xl border border-line bg-surface p-3">
        {/* stems */}
        <svg className="pointer-events-none absolute inset-0" width={size.w} height={size.h} aria-hidden>
          {lines.map((l) => {
            const on = active.includes(l.drug);
            return (
              <path
                key={`${l.drug}-${l.eff}`}
                d={l.d}
                fill="none"
                stroke={color.get(l.drug)}
                strokeWidth={on ? 4 : 2}
                strokeOpacity={on ? 0.95 : anyActive ? 0.08 : 0.3}
                strokeLinecap="round"
              />
            );
          })}
        </svg>

        {/* shelf of bottles */}
        <div className={`relative flex flex-wrap justify-center ${compact ? "gap-1" : "gap-3"} border-b-4 border-[#6b6b66] pb-2`}>
          {drugs.map((d) => {
            const on = active.includes(d);
            const c = color.get(d)!;
            return (
              <button
                key={d}
                type="button"
                ref={(el) => {
                  if (el) bottleRefs.current.set(d, el);
                }}
                onClick={() => toggle(d)}
                onMouseEnter={() => setHover(d)}
                onMouseLeave={() => setHover(null)}
                aria-pressed={picked.includes(d)}
                className={`flex ${compact ? "w-[74px]" : "w-[84px]"} flex-col items-center rounded-lg p-1 focus-visible:outline-2`}
              >
                {/* cap */}
                <span className="block h-3 w-9 rounded-t-md" style={{ background: "#6b6b66" }} />
                {/* bottle */}
                <span
                  className={`flex ${compact ? "h-16 w-11" : "h-20 w-14"} items-center justify-center rounded-b-xl rounded-t-md border-2 shadow-sm`}
                  style={{ borderColor: c, background: on ? c : `${c}22` }}
                >
                  <span className="rounded bg-page px-1 text-[10px] font-bold leading-tight text-ink">Rx</span>
                </span>
                <span className={`mt-1 text-center ${compact ? "text-xs" : "text-sm"} font-semibold capitalize leading-tight ${on ? "text-ink" : "text-ink-muted"}`}>{d}</span>
              </button>
            );
          })}
        </div>

        {/* what it can do */}
        <div className="relative mt-16 grid grid-cols-2 gap-2">
          {effects.map((e) => {
            const h = hits(e);
            const stacked = h.length >= 2;
            return (
              <div
                key={e.id}
                ref={(el) => {
                  if (el) effRefs.current.set(e.id, el);
                }}
                className={`rounded-xl border-2 p-2 text-center transition ${
                  h.length ? "border-hold-ink bg-hold-tint" : anyActive ? "border-line bg-page opacity-50" : "border-line bg-page"
                }`}
              >
                <p className="font-bold leading-tight">{e.title}</p>
                {e.signs && <p className="text-sm leading-tight text-ink-muted">{e.signs}</p>}
                {stacked && (
                  <p className="mt-1 inline-block rounded-full bg-hold-solid px-2 py-0.5 text-xs font-bold text-ink">
                    {addsUp} ×{h.length}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
