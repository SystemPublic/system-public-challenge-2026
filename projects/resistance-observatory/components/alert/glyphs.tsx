import type { AlertEvent, ChangeKind } from "@/lib/alert/derive";

/**
 * The three kinds of change, each with its own form so colour is never the
 * only encoding:
 *   prevalence shift  -> triangle, pointing the way the number moved
 *   new signal        -> ring with a centre dot (a first sighting)
 *   association       -> diamond (a link between two variables)
 * Used at the same shape in the feed, the timeline and the chart.
 */
export function kindPath(kind: ChangeKind, direction: "up" | "down" | undefined, r: number): string {
  if (kind === "prevalence_shift") {
    const s = direction === "down" ? -1 : 1;
    return `M0 ${-r * s} L${r} ${r * 0.8 * s} L${-r} ${r * 0.8 * s} Z`;
  }
  if (kind === "association") return `M0 ${-r} L${r} 0 L0 ${r} L${-r} 0 Z`;
  return "";
}

export function KindMark({
  kind,
  direction,
  r = 6,
  filled = true,
  className = "",
}: {
  kind: ChangeKind;
  direction?: "up" | "down";
  r?: number;
  filled?: boolean;
  className?: string;
}) {
  if (kind === "new_signal") {
    return (
      <g className={className}>
        <circle r={r} fill="var(--surface)" stroke="currentColor" strokeWidth={1.8} />
        <circle r={Math.max(1.6, r * 0.34)} fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth={1} />
      </g>
    );
  }
  return (
    <path
      className={className}
      d={kindPath(kind, direction, r)}
      fill={filled ? "currentColor" : "var(--surface)"}
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinejoin="round"
    />
  );
}

export function KindGlyph({
  event,
  size = 18,
  quiet = false,
}: {
  event: Pick<AlertEvent, "kind" | "direction">;
  size?: number;
  quiet?: boolean;
}) {
  return (
    <svg width={size} height={size} viewBox="-10 -10 20 20" aria-hidden className="shrink-0 overflow-visible">
      <KindMark kind={event.kind} direction={event.direction} r={7} filled={!quiet} />
    </svg>
  );
}

/** Form for each evidence source: circle = genome counts, bar = paper, square = graph. */
export function SourceGlyph({ source, size = 12 }: { source: AlertEvent["source"]; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" aria-hidden className="shrink-0">
      {source === "genomes" && <circle cx="6" cy="6" r="4.4" fill="none" stroke="currentColor" strokeWidth="1.8" />}
      {source === "papers" && <rect x="4.4" y="0.8" width="3.2" height="10.4" rx="1" fill="currentColor" />}
      {source === "graph" && <rect x="1.6" y="1.6" width="8.8" height="8.8" rx="1.5" fill="currentColor" />}
    </svg>
  );
}

export const SOURCE_TONE = {
  genomes: "text-fg",
  papers: "text-gap",
  graph: "text-drug",
} as const;
