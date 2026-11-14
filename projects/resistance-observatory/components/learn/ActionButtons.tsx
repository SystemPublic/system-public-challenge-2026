"use client";

import Link from "next/link";
import { useSelection } from "@/lib/selection";
import type { Marker } from "@/content/markers";

/**
 * The connective tissue of the product (docs/LEARN.md). Both actions carry the
 * shared selection with markerId set, so Forecast and Alert open on this
 * marker without re-selecting. They are real links (keyboard, middle-click,
 * copyable) — the URL *is* the shared state.
 */
export function ActionButtons({ marker }: { marker: Marker }) {
  const { hrefWithSelection } = useSelection();
  const withMarker = { markerId: marker.id };
  return (
    <div className="flex flex-col gap-3">
      <Link
        href={hrefWithSelection("/forecast", withMarker)}
        className="group flex items-center justify-between gap-4 rounded-[var(--radius)] bg-drug px-5 py-4 text-bg transition-transform hover:-translate-y-0.5"
      >
        <span>
          <span className="block text-lg font-semibold">See where it&rsquo;s been observed</span>
          <span className="block text-sm opacity-75">Map · observed over time</span>
        </span>
        <span aria-hidden className="text-2xl transition-transform group-hover:translate-x-1">→</span>
      </Link>
      <Link
        href={hrefWithSelection("/alert", withMarker)}
        className="group flex items-center justify-between gap-4 rounded-[var(--radius)] border-2 border-fg px-5 py-4 transition-transform hover:-translate-y-0.5"
      >
        <span>
          <span className="block text-lg font-semibold">Watch this marker</span>
          <span className="block text-sm text-muted">Alert · {marker.gene} {marker.alteration} pre-filled</span>
        </span>
        <span aria-hidden className="text-2xl transition-transform group-hover:translate-x-1">→</span>
      </Link>
    </div>
  );
}
