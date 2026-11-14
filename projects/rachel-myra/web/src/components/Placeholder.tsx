/** A clearly-labelled box for a visual or feature that is not built yet. */
export function Placeholder({ title, children, spec }: { title: string; children?: React.ReactNode; spec?: string }) {
  return (
    <section className="rounded-tile border border-dashed border-line-strong bg-surface p-4">
      <h3 className="font-semibold">
        {title} <span className="text-xs font-normal text-ink-muted">(not built yet{spec ? `; spec ${spec}` : ""})</span>
      </h3>
      {children && <div className="mt-1 text-sm text-ink-muted">{children}</div>}
    </section>
  );
}
