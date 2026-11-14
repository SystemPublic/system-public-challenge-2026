import type { ReactNode } from "react";
import {
  AMBER,
  DETECTED_DOT,
  HATCH_BG,
  HATCH_LINE,
  LAND_NOT_SAMPLED,
  PAPER_READ_FILL,
  paperRampGradientCss,
  rampColor,
  rampGradientCss,
  type MapLayer,
} from "@/lib/forecast/encoding";

type Kind = "not_sampled" | "tested_not_detected" | "detected";

/** Land swatch plus the state marker, exactly as the map draws them. */
function Swatch({ kind }: { kind: Kind }) {
  const id = `fc-leg-hatch-${kind}`;
  return (
    <svg width="28" height="14" viewBox="0 0 28 14" aria-hidden className="shrink-0">
      <defs>
        <pattern id={id} width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="4" height="4" fill={HATCH_BG} />
          <line x1="0" y1="0" x2="0" y2="4" stroke={HATCH_LINE} strokeWidth="1.3" />
        </pattern>
      </defs>
      <rect
        x="0.5"
        y="0.5"
        width="14"
        height="13"
        rx="2"
        fill={
          kind === "not_sampled"
            ? LAND_NOT_SAMPLED
            : kind === "tested_not_detected"
              ? `url(#${id})`
              : rampColor(0.6)
        }
        stroke="#2f607f"
        strokeWidth="1"
      />
      {kind === "tested_not_detected" ? (
        <circle cx="22" cy="7" r="4" fill="#050d17" stroke="#f5f4ef" strokeWidth="1.5" />
      ) : null}
      {kind === "detected" ? (
        <circle cx="22" cy="7" r="4.5" fill={DETECTED_DOT} stroke="#050d17" strokeWidth="1.5" />
      ) : null}
    </svg>
  );
}

/** The same pennant the map draws. */
function FlagGlyph({ ring = false, placeholder = false }: { ring?: boolean; placeholder?: boolean }) {
  return (
    <svg width="22" height="20" viewBox="-6 -25 26 28" aria-hidden className="shrink-0">
      {ring ? <circle cx={5} cy={-12} r={11} fill="none" stroke={AMBER} strokeWidth={1.7} /> : null}
      <line x1={0} y1={1} x2={0} y2={-19} stroke={AMBER} strokeWidth={1.6} strokeLinecap="round" />
      <path
        d="M0.8 -19 L13 -15 L0.8 -11 Z"
        fill={placeholder ? "rgba(242,189,118,0.3)" : AMBER}
        stroke={placeholder ? AMBER : "#050d17"}
        strokeWidth={1.2}
        strokeDasharray={placeholder ? "2 1.6" : undefined}
      />
    </svg>
  );
}

function ChangedGlyph() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden className="shrink-0">
      <circle cx="12" cy="12" r="9.5" fill="none" stroke={AMBER} strokeWidth="1.9" />
      <circle cx="12" cy="12" r="4.5" fill={DETECTED_DOT} stroke="#050d17" strokeWidth="1.5" />
    </svg>
  );
}

/** Paper squares, exactly as the map draws them: read = larger solid square. */
export function SquareGlyph({ read }: { read: boolean }) {
  const half = read ? 6 : 4.5;
  return (
    <svg width="14" height="14" viewBox="2 2 14 14" aria-hidden className="shrink-0">
      <rect
        x={9 - half}
        y={9 - half}
        width={half * 2}
        height={half * 2}
        fill={read ? PAPER_READ_FILL : "#050d17"}
        stroke={read ? "#050d17" : "#f5f4ef"}
        strokeWidth={read ? 1.25 : 1.6}
      />
    </svg>
  );
}

function Ramp({ css, lo, hi }: { css: string; lo: string; hi: string }) {
  return (
    <span className="flex shrink-0 items-center gap-1 tabular-nums text-muted">
      <span>{lo}</span>
      <span className="h-2 w-[38px] rounded-[2px] border border-line" style={{ background: css }} aria-hidden />
      <span>{hi}</span>
    </span>
  );
}

function Item({ mark, children }: { mark: ReactNode; children: ReactNode }) {
  return (
    <li className="flex min-w-0 items-center gap-1.5">
      {mark}
      <span className="min-w-0 leading-tight">{children}</span>
    </li>
  );
}

/**
 * Compact legend strip along the bottom of the map.
 *   Row A: inline layer switch + title.
 *   Rows B, C: items (genome: 3 per row, or all 6 in one row when wide;
 *              papers: one row).
 *   Row D: the active layer's source line, one line, ellipsis + title.
 */
export function LegendStrip({
  layer,
  asOfYear,
  placeholder = false,
  paperMax,
  wide = false,
  onLayerChange,
}: {
  layer: MapLayer;
  asOfYear: number;
  placeholder?: boolean;
  paperMax: number;
  /** Enough width for all genome items on one row. */
  wide?: boolean;
  onLayerChange: (layer: MapLayer) => void;
}) {
  const papers = layer === "papers";
  const source = papers
    ? "Countries machine-read from paper abstracts · the Graph has no geography field"
    : "Colours: MalariaGEN Pf8 (CC BY 4.0), by collection year · Shapes: Natural Earth";
  return (
    <section
      aria-label={papers ? `Legend: K540E papers and the Graph as of ${asOfYear}` : `Legend: K540E in genome data as of ${asOfYear}`}
      className="fc-card px-3 py-2 text-[12px]"
    >
      <div className="flex items-center gap-3">
        <div role="group" aria-label="Map layer" className="fc-seg fc-seg-sm shrink-0">
          <button type="button" aria-pressed={!papers} onClick={() => papers && onLayerChange("genome")}>
            Genome data
          </button>
          <button type="button" aria-pressed={papers} onClick={() => !papers && onLayerChange("papers")}>
            Papers and the Graph
          </button>
        </div>
        <h2 className="fc-label min-w-0 leading-tight">
          {papers ? `Papers and the Graph · as of ${asOfYear}` : `Genome data · as of ${asOfYear}`}
        </h2>
      </div>
      {papers ? (
        <ul className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1">
          <Item mark={<Ramp css={paperRampGradientCss()} lo="1" hi={String(paperMax)} />}>papers</Item>
          <Item mark={<SquareGlyph read />}>Graph read at least one</Item>
          <Item mark={<SquareGlyph read={false} />}>Graph read none</Item>
          <li className="leading-tight">no mark: no paper</li>
        </ul>
      ) : (
        <ul
          className="mt-1.5 grid items-center gap-x-4 gap-y-1"
          style={{
            gridTemplateColumns: wide
              ? "repeat(6, auto)"
              : "repeat(3, auto)",
            justifyContent: "start",
          }}
        >
          <Item mark={<Swatch kind="not_sampled" />}>Not sampled</Item>
          <Item mark={<Swatch kind="tested_not_detected" />}>Tested, not detected</Item>
          <li className="flex min-w-0 items-center gap-1.5">
            <Swatch kind="detected" />
            <span className="flex flex-col leading-tight">
              <span className="max-w-[200px]">Detected, share of tested samples carrying K540E:</span>
              <span className="flex items-center gap-1.5 whitespace-nowrap">
                <Ramp css={rampGradientCss()} lo="above 0%" hi="100%" />
              </span>
            </span>
          </li>
          <Item mark={<ChangedGlyph />}>Changed in {asOfYear}</Item>
          <Item mark={<FlagGlyph placeholder={placeholder} />}>
            Alert (Alert tab); a number = alerts for that country{placeholder ? "; placeholder" : ""}
          </Item>
          <Item mark={<FlagGlyph ring placeholder={placeholder} />}>New alert in {asOfYear}</Item>
        </ul>
      )}
      <p className="mt-1 truncate text-[12px] text-muted" title={source}>
        {source}
      </p>
    </section>
  );
}
