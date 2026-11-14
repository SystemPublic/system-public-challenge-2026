"use client";

import { useInView } from "@/lib/motion";
import { Reveal } from "@/components/Reveal";

/**
 * The gap: a finding is published; it takes time to reach the people choosing
 * drugs. No duration is shown: the evidence graph holds no figure for it.
 */
export function Gap() {
  const { ref, inView } = useInView<HTMLDivElement>({ threshold: 0.45 });

  return (
    <section aria-labelledby="gap-h" className="py-32">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal>
          <p className="mb-3 font-mono text-xs uppercase tracking-[0.18em] text-gap">The gap</p>
          <h2 id="gap-h" className="max-w-4xl font-display text-4xl font-semibold tracking-tight sm:text-6xl text-balance">
            The evidence arrives. Then it waits.
          </h2>
          <p className="mt-6 max-w-2xl text-lg text-muted text-pretty">
            New findings about resistance markers are published continuously, scattered
            across the literature. A paper that changes the picture can sit for a long time
            before it reaches the people deciding which drugs to use.
          </p>
        </Reveal>

        <div
          ref={ref}
          data-on={inView ? "true" : "false"}
          className="group mt-20"
          role="img"
          aria-label="Timeline: a finding is published; time passes; it reaches the people choosing drugs."
        >
          <div className="relative grid grid-cols-[auto_1fr_auto] items-center gap-4">
            <Node glyph="paper" label="Finding published" tone="drug" />
            <div className="relative h-10">
              <div className="absolute inset-x-0 top-1/2 border-t-2 border-dashed border-gap/70" />
              <div
                className="absolute top-1/2 h-3 w-3 -translate-y-1/2 rounded-full bg-gap transition-[left] duration-[2400ms] ease-in-out left-0 group-data-[on=true]:left-[calc(100%-0.75rem)]"
              />
            </div>
            <Node glyph="people" label="Reaches people choosing drugs" tone="gap" />
          </div>
        </div>

        <Reveal className="mt-24">
          <p className="max-w-3xl font-display text-2xl leading-snug sm:text-3xl text-pretty">
            Resistance Observatory asks one question, marker by marker:{" "}
            <span className="text-drug">does this new finding change the picture?</span>
          </p>
          <p className="mt-4 max-w-2xl text-sm text-muted">
            The demo replays real publication history from a frozen evidence snapshot, in the
            order findings were actually published. It is not live surveillance.
          </p>
        </Reveal>
      </div>
    </section>
  );
}

function Node({ glyph, label, tone }: { glyph: "paper" | "people"; label: string; tone: "drug" | "gap" }) {
  const color = tone === "drug" ? "var(--drug)" : "var(--gap)";
  return (
    <div className="flex w-28 flex-col items-center gap-2 text-center sm:w-40">
      <svg width="56" height="56" viewBox="0 0 56 56" aria-hidden>
        <circle cx="28" cy="28" r="26" fill="var(--surface)" stroke={color} strokeWidth="2" />
        {glyph === "paper" ? (
          <g fill="none" stroke={color} strokeWidth="2">
            <path d="M19 15h13l6 6v20H19Z" />
            <path d="M32 15v6h6M23 27h10M23 32h10M23 37h7" />
          </g>
        ) : (
          <g fill="none" stroke={color} strokeWidth="2">
            <circle cx="22" cy="23" r="4" />
            <circle cx="34" cy="23" r="4" />
            <path d="M14 39c1-6 5-9 8-9s7 3 8 9M26 39c1-6 5-9 8-9s7 3 8 9" />
          </g>
        )}
      </svg>
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}
