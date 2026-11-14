"use client";

import Link from "next/link";
import { useSelection } from "@/lib/selection";
import { Reveal } from "@/components/Reveal";

const CARDS = [
  {
    href: "/learn",
    kicker: "01 · Learn",
    title: "One marker, one drug, one diagram.",
    body: "What the marker is, which drug it affects, and why that matters — in under ninety seconds.",
    glyph: "lens",
  },
  {
    href: "/forecast",
    kicker: "02 · Map",
    title: "Where it has been observed.",
    body: "A map over time, drawn from a separately attributed observation source.",
    glyph: "map",
  },
  {
    href: "/alert",
    kicker: "03 · Alert",
    title: "Watch a marker.",
    body: "Save a watch. When qualifying new evidence appears, get a plain explanation and a link to the paper.",
    glyph: "bell",
  },
] as const;

export function TabCards() {
  const { hrefWithSelection } = useSelection();
  return (
    <section aria-labelledby="cards-h" className="border-t border-line bg-surface py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <h2 id="cards-h" className="font-display text-4xl font-semibold tracking-tight sm:text-5xl">
          Where to next
        </h2>
        <ul className="mt-12 grid gap-5 md:grid-cols-3">
          {CARDS.map((c, i) => (
            <Reveal as="li" key={c.href} delay={i * 110}>
              <Link
                href={hrefWithSelection(c.href)}
                className="group flex h-full flex-col rounded-[var(--radius)] border border-line bg-bg p-6 shadow-[var(--shadow)] transition-all hover:-translate-y-1 hover:border-line-strong"
              >
                <Glyph kind={c.glyph} />
                <p className="mt-6 font-mono text-xs uppercase tracking-[0.18em] text-muted">{c.kicker}</p>
                <h3 className="mt-2 font-display text-2xl font-semibold text-balance">{c.title}</h3>
                <p className="mt-3 flex-1 text-muted text-pretty">{c.body}</p>
                <span className="mt-6 inline-flex items-center gap-1 font-medium">
                  Open <span aria-hidden className="transition-transform group-hover:translate-x-1">→</span>
                </span>
              </Link>
            </Reveal>
          ))}
        </ul>
      </div>
    </section>
  );
}

function Glyph({ kind }: { kind: "lens" | "map" | "bell" }) {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" aria-hidden fill="none" stroke="currentColor" strokeWidth="1.8" className="text-drug">
      {kind === "lens" && (
        <>
          <circle cx="20" cy="20" r="15" />
          <circle cx="20" cy="20" r="6" />
          <path d="M20 2v6M20 32v6M2 20h6M32 20h6" />
        </>
      )}
      {kind === "map" && (
        <>
          <path d="M5 9l10-4 10 4 10-4v26l-10 4-10-4-10 4Z" />
          <path d="M15 5v26M25 9v26" />
        </>
      )}
      {kind === "bell" && (
        <>
          <path d="M10 28V18a10 10 0 0 1 20 0v10l3 3H7Z" />
          <path d="M17 35a3 3 0 0 0 6 0" />
        </>
      )}
    </svg>
  );
}
