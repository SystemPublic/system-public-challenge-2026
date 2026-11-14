import type { ReactNode } from "react";

type Kind = "note" | "limit" | "pending";

const STYLES: Record<Kind, { box: string; label: string; glyph: string }> = {
  note: { box: "border-drug/50 bg-drug-soft/40", label: "Note", glyph: "i" },
  limit: { box: "border-signal/50 bg-signal-soft/40", label: "Limit", glyph: "!" },
  pending: { box: "border-gap/60 bg-gap-soft/50 border-dashed", label: "Pending", glyph: "…" },
};

export function Callout({
  kind = "note",
  title,
  children,
  className = "",
}: {
  kind?: Kind;
  title?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const s = STYLES[kind];
  return (
    <aside
      role="note"
      className={`flex gap-3 rounded-[var(--radius)] border-l-4 border p-4 ${s.box} ${className}`}
    >
      <span
        aria-hidden
        className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full border border-current font-mono text-xs font-bold text-muted"
      >
        {s.glyph}
      </span>
      <div className="text-sm leading-relaxed">
        <p className="mb-1 font-semibold">
          <span className="sr-only">{s.label}: </span>
          {title ?? s.label}
        </p>
        <div className="text-muted">{children}</div>
      </div>
    </aside>
  );
}
