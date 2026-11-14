// Small, presentational building blocks shared by every screen.
// No hooks, so they work in both server and client components.

import type {
  BadgeCode,
  Bucket,
  CompassArrow,
  Layer,
  Level,
  Meter,
} from "@lib/types/knowledge-base.ts";
import { BADGES, BUCKETS, COMPASS, LAYERS, LEVEL, METER } from "@/lib/ui";

/** The "—" shown wherever data is missing. Never invent a number. */
export function Dash({ what = "No data yet" }: { what?: string }) {
  return (
    <span className="text-missing" title={what}>
      —<span className="sr-only">{what}</span>
    </span>
  );
}

export function BucketChip({ bucket, size = "sm" }: { bucket: Bucket | null; size?: "sm" | "md" }) {
  if (!bucket) return <Dash what="No action bucket yet" />;
  const b = BUCKETS[bucket];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-semibold ${b.tint} ${
        size === "md" ? "text-sm" : "text-xs"
      }`}
      title={b.plain}
    >
      <span aria-hidden className={`inline-flex h-4 w-4 items-center justify-center rounded-sm text-[10px] ${b.solid}`}>
        {b.letter}
      </span>
      {b.label}
    </span>
  );
}

function Segments({ filled, label }: { filled: number; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5" title={label}>
      <span aria-hidden className="inline-flex gap-0.5">
        {[1, 2, 3].map((i) => (
          <span
            key={i}
            className={`h-2.5 w-3 rounded-[2px] border border-line-strong ${i <= filled ? "bg-ink" : "bg-page"}`}
          />
        ))}
      </span>
      <span className="text-xs font-medium">{label}</span>
    </span>
  );
}

/** 3-step evidence meter: Strong / Some / Early signs (spec C8). */
export function EvidenceMeter({ meter }: { meter: Meter | null | undefined }) {
  if (!meter || !METER[meter]) return <Dash what="Evidence not graded yet" />;
  const m = METER[meter];
  return <Segments filled={m.filled} label={m.label} />;
}

/** FLAG ("Check on this person") / CHANGE ("Rethink the medicine") level meter. */
export function LevelMeter({ level }: { level: Level | null | undefined }) {
  if (!level || !LEVEL[level]) return <Dash what="Not scored yet" />;
  const l = LEVEL[level];
  return <Segments filled={l.filled} label={l.label} />;
}

export function VerificationBadge({ code }: { code: BadgeCode }) {
  const b = BADGES[code];
  if (!b) return null;
  return (
    <span className={`inline-flex rounded px-1.5 py-0.5 text-xs font-bold ${b.cls}`} title={b.label}>
      {b.symbol}
      <span className="sr-only"> {b.label}</span>
    </span>
  );
}

export function LayerTag({ layer }: { layer: Layer }) {
  const l = LAYERS[layer];
  if (!l) return null;
  return (
    <span className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium ${l.cls}`}>
      <span aria-hidden>{l.symbol}</span>
      {l.label}
    </span>
  );
}

export function CompassArrowMark({ arrow, large = false }: { arrow: CompassArrow | null | undefined; large?: boolean }) {
  if (!arrow || !COMPASS[arrow]) return <Dash what="Direction not known yet" />;
  const c = COMPASS[arrow];
  return (
    <span className={`inline-flex items-center gap-2 font-semibold ${c.cls}`}>
      <span aria-hidden className={large ? "text-4xl leading-none" : "text-lg leading-none"}>
        {c.symbol}
      </span>
      <span className={large ? "text-base" : "text-xs"}>{c.label}</span>
    </span>
  );
}

/** Guidance-gap "!" badge (ring is drawn by the tile itself). */
export function GapBadge() {
  return (
    <span
      className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-hold-solid text-xs font-bold text-hold-on"
      title="Guidance gap: no guidance gives a drug-specific action"
    >
      !<span className="sr-only">Guidance gap</span>
    </span>
  );
}
