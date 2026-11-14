"use client";
// next/dynamic wrapper so MapLibre + deck.gl never run on the server.
import dynamic from "next/dynamic";
import type { ComponentProps } from "react";
import type { DeckMapProps } from "./DeckMap";
import { MapErrorBoundary } from "./MapErrorBoundary";

const MapCanvas = dynamic<DeckMapProps>(() => import("./DeckMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[240px] w-full items-center justify-center rounded-xl bg-[var(--ui-surface,#f7f7f5)] text-sm text-[var(--ui-ink-muted,#4b5563)]">
      Loading map…
    </div>
  ),
});

export default function SafeMapCanvas(props: ComponentProps<typeof MapCanvas>) {
  return (
    <MapErrorBoundary height={props.height}>
      <MapCanvas {...props} />
    </MapErrorBoundary>
  );
}
