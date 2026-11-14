import type { ReactNode } from "react";

type ChipProps = {
  children: ReactNode;
  tone?: "neutral" | "drug" | "signal" | "gap";
  /** Optional leading glyph so colour is never the only encoding. */
  glyph?: "dot" | "square" | "triangle" | "none";
  title?: string;
  className?: string;
};

const TONES = {
  neutral: "border-line text-muted",
  drug: "border-drug/50 text-drug",
  signal: "border-signal/50 text-signal",
  gap: "border-gap/60 text-gap",
} as const;

export function Chip({ children, tone = "neutral", glyph = "none", title, className = "" }: ChipProps) {
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${TONES[tone]} ${className}`}
    >
      {glyph !== "none" ? <Glyph kind={glyph} /> : null}
      {children}
    </span>
  );
}

function Glyph({ kind }: { kind: "dot" | "square" | "triangle" }) {
  return (
    <svg width="8" height="8" viewBox="0 0 8 8" aria-hidden className="shrink-0">
      {kind === "dot" && <circle cx="4" cy="4" r="3.5" fill="currentColor" />}
      {kind === "square" && <rect x="0.5" y="0.5" width="7" height="7" fill="currentColor" />}
      {kind === "triangle" && <path d="M4 0.5 7.5 7.5H0.5Z" fill="currentColor" />}
    </svg>
  );
}
