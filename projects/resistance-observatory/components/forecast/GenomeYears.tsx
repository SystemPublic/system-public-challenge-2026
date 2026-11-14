import type { GenomeYear } from "@/lib/forecast/types";

/** One row per sampled year; gaps in sampling get a divider row. Real table. */
export function GenomeYears({ years }: { years: GenomeYear[] }) {
  const rows: React.ReactNode[] = [];
  let prev: number | null = null;
  for (const y of years) {
    if (prev !== null && y.year > prev + 1) {
      const a = prev + 1;
      const b = y.year - 1;
      rows.push(
        <tr key={`gap-${a}`}>
          <td colSpan={3} className="py-1 text-center text-[0.8125rem] italic text-muted">
            <span className="border-y border-dashed border-line-strong px-2">
              not sampled {a === b ? a : `${a}–${b}`}
            </span>
          </td>
        </tr>,
      );
    }
    const frac = y.tested > 0 ? Math.min(1, y.withE / y.tested) : 0;
    rows.push(
      <tr key={y.year}>
        <th scope="row" className="py-1 pr-2 text-left text-[0.8125rem] font-normal tabular-nums text-fg">
          {y.year}
        </th>
        <td className="w-full py-1 pr-2">
          <div
            className="h-2.5 w-full rounded-[2px] border border-line-strong"
            aria-hidden
          >
            {y.withE > 0 && (
              <div className="h-full bg-drug" style={{ width: `${Math.max(frac * 100, 2)}%` }} />
            )}
          </div>
        </td>
        <td className="whitespace-nowrap py-1 text-right text-[0.8125rem] tabular-nums text-fg">
          {y.withE} / {y.tested}
          {y.other > 0 && <span className="text-muted"> {"\u00b7"} {y.other} other</span>}
        </td>
      </tr>,
    );
    prev = y.year;
  }
  const anyOther = years.some((y) => y.other > 0);
  return (
    <div>
    <table className="w-full border-collapse">
      <caption className="sr-only">
        Samples carrying K540E out of samples tested, by collection year. Years without
        samples are listed as not sampled.
      </caption>
      <thead>
        <tr className="text-[0.75rem] uppercase tracking-[0.18em] text-muted">
          <th scope="col" className="pb-1 text-left font-normal">Year</th>
          <th scope="col" className="pb-1 text-left font-normal">Share</th>
          <th scope="col" className="whitespace-nowrap pb-1 text-right font-normal">K540E / tested</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    {anyOther && (
      <p className="mt-1 text-[0.8125rem] text-muted">
        other = samples with a different amino acid at codon 540; they are not K540E.
      </p>
    )}
    </div>
  );
}
