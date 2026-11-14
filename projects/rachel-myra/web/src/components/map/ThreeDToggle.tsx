"use client";

export function ThreeDToggle({ on, onChange, large = false }: { on: boolean; onChange: (v: boolean) => void; large?: boolean }) {
  const base = large ? "px-4 py-2 text-base" : "px-3 py-1 text-sm";
  return (
    <div role="group" aria-label="Map view" className="inline-flex overflow-hidden rounded-full border border-[var(--ui-line-strong,#6b6b66)] bg-white shadow-sm">
      {[false, true].map((v) => (
        <button
          key={String(v)}
          type="button"
          aria-pressed={on === v}
          onClick={() => onChange(v)}
          className={`${base} font-semibold ${on === v ? "bg-[var(--bucket-store-solid,#0e7c86)] text-white" : "text-[var(--ui-ink,#141414)]"}`}
        >
          {v ? "3D" : "2D"}
        </button>
      ))}
    </div>
  );
}
