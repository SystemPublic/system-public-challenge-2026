// Display metadata for buckets, meters, badges and layers. Client-safe (no fs).
// Tailwind class strings are written out in full so the scanner picks them up.

import type {
  BadgeCode,
  Bucket,
  CompassArrow,
  Layer,
  Level,
  Meter,
} from "@lib/types/knowledge-base.ts";

export const BUCKET_ORDER: Bucket[] = [
  "hold_or_substitute",
  "adjust_dose",
  "monitor",
  "storage",
];

export interface BucketStyle {
  label: string;
  /** Plain-language explanation shown under the label / in tooltips. */
  plain: string;
  /** Letter paired with color so color is never the only cue. */
  letter: string;
  /** Classes per evidence strength: solid = strong, tint = some, outline = early signs. */
  solid: string;
  tint: string;
  outline: string;
  /** Text/border color on white. */
  ink: string;
  dot: string;
}

export const BUCKETS: Record<Bucket, BucketStyle> = {
  hold_or_substitute: {
    label: "Hold / substitute",
    plain: "Think about pausing or switching before heat season",
    letter: "H",
    solid: "bg-hold-solid text-hold-on border-hold-solid",
    tint: "bg-hold-tint text-hold-ink border-hold-ink",
    outline: "bg-page text-hold-ink border-hold-ink",
    ink: "text-hold-ink border-hold-ink",
    dot: "bg-hold-solid",
  },
  adjust_dose: {
    label: "Adjust dose",
    plain: "The dose may need a second look in hot weather",
    letter: "A",
    solid: "bg-adjust-solid text-adjust-on border-adjust-solid",
    tint: "bg-adjust-tint text-adjust-ink border-adjust-ink",
    outline: "bg-page text-adjust-ink border-adjust-ink",
    ink: "text-adjust-ink border-adjust-ink",
    dot: "bg-adjust-solid",
  },
  monitor: {
    label: "Monitor",
    plain: "Keep the medicine; check on the person and their levels",
    letter: "M",
    solid: "bg-monitor-solid text-monitor-on border-monitor-solid",
    tint: "bg-monitor-tint text-monitor-ink border-monitor-ink",
    outline: "bg-page text-monitor-ink border-monitor-ink",
    ink: "text-monitor-ink border-monitor-ink",
    dot: "bg-monitor-solid",
  },
  storage: {
    label: "Store cool",
    plain: "Heat can damage the medicine itself",
    letter: "S",
    solid: "bg-store-solid text-store-on border-store-solid",
    tint: "bg-store-tint text-store-ink border-store-ink",
    outline: "bg-page text-store-ink border-store-ink",
    ink: "text-store-ink border-store-ink",
    dot: "bg-store-solid",
  },
};

export const METER: Record<Meter, { label: string; filled: number; fill: "solid" | "tint" | "outline" }> = {
  strong: { label: "Strong", filled: 3, fill: "solid" },
  some: { label: "Some", filled: 2, fill: "tint" },
  early_signs: { label: "Early signs", filled: 1, fill: "outline" },
};

export const LEVEL: Record<Level, { label: string; filled: number }> = {
  high: { label: "High", filled: 3 },
  moderate: { label: "Moderate", filled: 2 },
  low: { label: "Low", filled: 1 },
};

export const BADGES: Record<BadgeCode, { symbol: string; label: string; cls: string }> = {
  double_verified: {
    symbol: "✓✓",
    label: "Double-verified: number found in the abstract and System agrees",
    cls: "bg-verify-double-bg text-verify-double-fg",
  },
  verified: {
    symbol: "✓",
    label: "Verified: number found in the abstract",
    cls: "bg-verify-single-bg text-verify-single-fg",
  },
  corroborated: {
    symbol: "↗",
    label: "Corroborated by other studies in the System graph",
    cls: "bg-verify-corrob-bg text-verify-corrob-fg",
  },
  conflict: {
    symbol: "⚠",
    label: "Conflict or mislabel between our reading and System's",
    cls: "bg-verify-conflict-bg text-verify-conflict-fg",
  },
  unverified: {
    symbol: "?",
    label: "Unverified: not shown on public labels",
    cls: "bg-verify-unverified-bg text-verify-unverified-fg",
  },
};

export const LAYERS: Record<Layer, { symbol: string; label: string; cls: string }> = {
  graph: { symbol: "①", label: "In System graph", cls: "bg-layer-graph-bg text-layer-graph-fg" },
  literature: { symbol: "②", label: "Literature", cls: "bg-layer-lit-bg text-layer-lit-fg" },
  fda_reports: { symbol: "③", label: "FDA reports", cls: "bg-layer-fda-bg text-layer-fda-fg" },
  label: { symbol: "L", label: "FDA label", cls: "bg-verify-unverified-bg text-verify-unverified-fg" },
  guidance: { symbol: "G", label: "Guidance only", cls: "bg-verify-unverified-bg text-verify-unverified-fg" },
};

export const COMPASS: Record<CompassArrow, { symbol: string; label: string; cls: string }> = {
  up: { symbol: "↑", label: "Acts stronger in heat", cls: "text-compass-up" },
  down: { symbol: "↓", label: "Acts weaker in heat", cls: "text-compass-down" },
  depends: { symbol: "↕", label: "Depends", cls: "text-compass-depends" },
};

/** Short prescriber chips for tiles. Unknown specialties fall back to 3 letters. */
const PRESCRIBER_ABBR: Record<string, string> = {
  "primary care": "PC",
  pediatrics: "Peds",
  psychiatry: "Psych",
  cardiology: "Cardio",
  endocrinology: "Endo",
  nephrology: "Neph",
  neurology: "Neuro",
  urology: "Uro",
  "pain medicine": "Pain",
  allergy: "Allergy",
  pulmonology: "Pulm",
  geriatrics: "Geri",
};

export function prescriberAbbr(p: string): string {
  const key = p.trim().toLowerCase();
  return PRESCRIBER_ABBR[key] ?? p.slice(0, 1).toUpperCase() + p.slice(1, 4);
}
