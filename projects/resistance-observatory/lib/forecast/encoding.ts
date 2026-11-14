/**
 * Visual encoding shared by the map and the legend, so the two cannot drift.
 *
 * Three states, each with its own fill AND its own mark (colour is never the
 * only signal):
 *   not_sampled          quiet land, no mark
 *   tested_not_detected  diagonal hatch + hollow ring
 *   detected             continuous single-hue mint ramp + filled dot
 *
 * The ramp is continuous on purpose: no bin edges, because bin edges would read
 * as thresholds and this tab defines none. On a dark surface the low end sits
 * close to the surface (dim) and the high end is bright, lightness rising
 * monotonically (interpolated in OKLab).
 */
import type { GenomeSnapshot, GenomeState } from "./types";

export const LAND_NOT_SAMPLED = "#0d2233";
export const HATCH_BG = "#16344a";
export const HATCH_LINE = "#6f8aa0";
export const RAMP_LOW = "#1b5a57";
export const RAMP_HIGH = "#70e0ca";
export const SELECT_STROKE = "#70e0ca";
/** Filled dot for "detected" (light, so it reads on every ramp colour); the ring for "tested, not detected" is hollow. */
export const DETECTED_DOT = "#f5f4ef";

export const HATCH_PATTERN_ID = "fc-hatch";

export const STATE_LABEL: Record<GenomeState, string> = {
  not_sampled: "Not sampled",
  tested_not_detected: "Tested, K540E not detected",
  detected: "K540E detected",
};

export const STATE_LEGEND_TEXT: Record<GenomeState, string> = {
  not_sampled: "Not sampled (no genomes in the dataset yet)",
  tested_not_detected: "Tested, K540E not detected",
  detected: "K540E detected",
};

// --- OKLab interpolation ------------------------------------------------------
type RGB = [number, number, number];
const hexToRgb = (h: string): RGB => {
  const n = parseInt(h.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
const toLin = (c: number) => {
  const v = c / 255;
  return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
};
const fromLin = (v: number) => {
  const c = v <= 0.0031308 ? v * 12.92 : 1.055 * Math.pow(v, 1 / 2.4) - 0.055;
  return Math.round(Math.min(1, Math.max(0, c)) * 255);
};
function rgbToOklab([r8, g8, b8]: RGB): RGB {
  const r = toLin(r8), g = toLin(g8), b = toLin(b8);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ];
}
function oklabToHex([L, A, B]: RGB): string {
  const l = Math.pow(L + 0.3963377774 * A + 0.2158037573 * B, 3);
  const m = Math.pow(L - 0.1055613458 * A - 0.0638541728 * B, 3);
  const s = Math.pow(L - 0.0894841775 * A - 1.291485548 * B, 3);
  const r = fromLin(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s);
  const g = fromLin(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s);
  const b = fromLin(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s);
  return "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
}
const LOW_LAB = rgbToOklab(hexToRgb(RAMP_LOW));
const HIGH_LAB = rgbToOklab(hexToRgb(RAMP_HIGH));

/** Continuous ramp, share in [0,1] -> colour. No bins. */
export function rampColor(share: number): string {
  const t = Number.isFinite(share) ? Math.min(1, Math.max(0, share)) : 0;
  return oklabToHex([
    LOW_LAB[0] + (HIGH_LAB[0] - LOW_LAB[0]) * t,
    LOW_LAB[1] + (HIGH_LAB[1] - LOW_LAB[1]) * t,
    LOW_LAB[2] + (HIGH_LAB[2] - LOW_LAB[2]) * t,
  ]);
}

/** CSS gradient stops for the legend bar, sampled from the same function. */
export function rampGradientCss(): string {
  const stops = Array.from({ length: 11 }, (_, i) => `${rampColor(i / 10)} ${i * 10}%`);
  return `linear-gradient(to right, ${stops.join(", ")})`;
}

/** Share of samples carrying K540E in the latest sampled year, or null. */
export function latestShare(s: GenomeSnapshot | undefined): number | null {
  if (!s || !s.latest || s.latest.tested <= 0) return null;
  return s.latest.withE / s.latest.tested;
}

/** Fill for a country given its snapshot (absent = not sampled). */
export function fillFor(s: GenomeSnapshot | undefined): string {
  if (!s || s.state === "not_sampled") return LAND_NOT_SAMPLED;
  if (s.state === "tested_not_detected") return `url(#${HATCH_PATTERN_ID})`;
  return rampColor(latestShare(s) ?? 0);
}

export function stateOf(s: GenomeSnapshot | undefined): GenomeState {
  return s ? s.state : "not_sampled";
}

// --- Alerts and "changed this year" ------------------------------------------
/** Amber is reserved for alerts and "new"; never used for prevalence. */
export const AMBER = "#f2bd76";

export const ALERT_LEGEND_TEXT = "Alert from the Alert tab (computed on genome counts, by collection year)";
export const newInYearText = (year: number) => `New in ${year}`;
export const changedInYearText = (year: number) =>
  `Changed in ${year}: first genomes sampled or first detection in our data`;
export const alertCountText = (n: number, year: number) =>
  `${n} ${n === 1 ? "alert" : "alerts"} from the Alert tab as of ${year}`;

// --- Short map labels ---------------------------------------------------------
const SHORT_LABEL: Record<string, string> = {
  COD: "DR Congo",
  COG: "Congo",
  CAF: "Central African Rep.",
  ATF: "Fr. Southern Lands",
  BIH: "Bosnia and Herz.",
  CPV: "Cabo Verde",
  FLK: "Falkland Is.",
  FSM: "Micronesia",
  HMD: "Heard and McDonald Is.",
  IOT: "Br. Indian Ocean Terr.",
  KNA: "St Kitts and Nevis",
  MNP: "N. Mariana Is.",
  SGS: "S. Georgia",
  SPM: "St Pierre and Miquelon",
  STP: "São Tomé and Príncipe",
  TCA: "Turks and Caicos",
  VCT: "St Vincent and Gren.",
  VGB: "Br. Virgin Is.",
  VIR: "US Virgin Is.",
  WLF: "Wallis and Futuna",
};

/** Map label: a short display name for long names (over 20 characters). */
export function mapLabel(iso3: string, name: string): string {
  return SHORT_LABEL[iso3] ?? name;
}

// --- "Papers and the Graph" layer --------------------------------------------
/** Layer shown on the map. Genome is the default. */
export type MapLayer = "genome" | "papers";

/**
 * Paper-count ramp: a cool slate-to-pale single hue from the muted text family
 * (#b0bdcb). Deliberately not the mint genome ramp and not amber. Continuous,
 * linear from 1 paper to the current maximum; no bins.
 */
export const PAPER_RAMP_LOW = "#2c3d4f";
// High end stops at mid-light so the white "read" square still reads as filled on it.
export const PAPER_RAMP_HIGH = "#a3b3c3";
const P_LOW_LAB = rgbToOklab(hexToRgb(PAPER_RAMP_LOW));
const P_HIGH_LAB = rgbToOklab(hexToRgb(PAPER_RAMP_HIGH));

export function paperRampColor(count: number, max: number): string {
  const t = max > 1 ? Math.min(1, Math.max(0, (count - 1) / (max - 1))) : 1;
  return oklabToHex([
    P_LOW_LAB[0] + (P_HIGH_LAB[0] - P_LOW_LAB[0]) * t,
    P_LOW_LAB[1] + (P_HIGH_LAB[1] - P_LOW_LAB[1]) * t,
    P_LOW_LAB[2] + (P_HIGH_LAB[2] - P_LOW_LAB[2]) * t,
  ]);
}

export function paperRampGradientCss(): string {
  const stops = Array.from({ length: 11 }, (_, i) => `${paperRampColor(1 + i, 11)} ${i * 10}%`);
  return `linear-gradient(to right, ${stops.join(", ")})`;
}

/** Square marker: filled when the Graph has read at least one of the country's papers. */
export const PAPER_READ_FILL = "#f5f4ef";
export const PAPER_SOURCE_LINE =
  "Papers: PubMed list · countries machine-read from abstracts · by publication date";
export const paperLabelSuffix = (read: number, total: number) => `${read}/${total} read`;
