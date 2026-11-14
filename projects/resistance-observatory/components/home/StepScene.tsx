"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { usePrefersReducedMotion } from "@/lib/motion";

/**
 * A pinned, scroll-stepped section. The panel sticks to the viewport while
 * the user scrolls through one viewport-height per step; an
 * IntersectionObserver on invisible per-step sentinels picks the active step.
 * No scroll library, no scroll listeners.
 *
 * Reduced motion: no pinning. The visual renders in its final state and every
 * caption is listed in full.
 */
export function StepScene({
  id,
  eyebrow,
  heading,
  steps,
  visual,
  tone = "drug",
  note,
}: {
  id: string;
  eyebrow: string;
  heading: ReactNode;
  steps: ReactNode[];
  visual: (step: number) => ReactNode;
  tone?: "drug" | "signal";
  /** A short caption shown under the steps for the whole scene. */
  note?: ReactNode;
}) {
  const reduced = usePrefersReducedMotion();
  const [step, setStep] = useState(0);
  const sentinels = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    if (reduced) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) setStep(Number((e.target as HTMLElement).dataset.step));
        }
      },
      { rootMargin: "-50% 0px -50% 0px", threshold: 0 },
    );
    sentinels.current.forEach((el) => el && io.observe(el));
    return () => io.disconnect();
  }, [reduced, steps.length]);

  const last = steps.length - 1;
  const active = reduced ? last : step;
  const accent = tone === "drug" ? "bg-drug" : "bg-signal";

  const panel = (
    <div className="mx-auto grid w-full max-w-6xl items-center gap-10 px-4 sm:px-6 md:grid-cols-[1.1fr_1fr]">
      <div className="order-2 md:order-1">
        <p className="mb-3 font-mono text-xs uppercase tracking-[0.18em] text-muted">{eyebrow}</p>
        <h2 id={`${id}-h`} className="font-display text-4xl font-semibold tracking-tight sm:text-5xl text-balance">
          {heading}
        </h2>
        <ol className="mt-8 space-y-4">
          {steps.map((s, i) => (
            <li
              key={i}
              aria-current={i === active ? "step" : undefined}
              className={[
                "flex gap-4 text-lg transition-opacity duration-500",
                reduced || i <= active ? "opacity-100" : "opacity-35",
              ].join(" ")}
            >
              <span
                aria-hidden
                className={[
                  "mt-2.5 h-1.5 shrink-0 rounded-full transition-all duration-500",
                  i === active ? `w-8 ${accent}` : "w-3 bg-line-strong",
                ].join(" ")}
              />
              <span>
                <span className="sr-only">Step {i + 1}: </span>
                {s}
              </span>
            </li>
          ))}
        </ol>
        {note ? <p className="mt-8 max-w-md border-t border-line pt-4 text-sm text-muted text-pretty">{note}</p> : null}
      </div>
      <div className="order-1 md:order-2">{visual(active)}</div>
    </div>
  );

  if (reduced) {
    return (
      <section id={id} aria-labelledby={`${id}-h`} className="py-24">
        {panel}
      </section>
    );
  }

  return (
    <section
      id={id}
      aria-labelledby={`${id}-h`}
      className="relative"
      style={{ height: `${steps.length * 90 + 30}vh` }}
    >
      {steps.map((_, i) => (
        <div
          key={i}
          ref={(el) => {
            sentinels.current[i] = el;
          }}
          data-step={i}
          aria-hidden
          className="pointer-events-none absolute left-0 w-px"
          style={{ top: `${i * 90}vh`, height: "90vh" }}
        />
      ))}
      <div className="sticky top-[57px] flex h-[calc(100dvh-57px)] items-center">{panel}</div>
    </section>
  );
}
