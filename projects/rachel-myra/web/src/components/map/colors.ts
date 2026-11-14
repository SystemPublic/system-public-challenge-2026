// RGB copies of the risk-group tokens in web/src/styles/tokens.css (deck.gl needs arrays).
// Keep in sync with --risk-* there. HTML should use the CSS variables (see RISK_CSS).

export type RiskGroup = "High" | "Medium" | "Low";
export const RISK_GROUPS: RiskGroup[] = ["High", "Medium", "Low"];

import { heatRgba } from "@/components/replay/colors";

type RGB = [number, number, number];

function hex(h: string): RGB {
  const n = parseInt(h.replace("#", ""), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

export const RISK_HEX: Record<RiskGroup, { solid: string; tint: string; ink: string; on: string }> = {
  High: { solid: "#d55e00", tint: "#fbe3d6", ink: "#a0410a", on: "#141414" },
  Medium: { solid: "#f0c419", tint: "#fdf4d3", ink: "#7a5c00", on: "#141414" },
  Low: { solid: "#0e7c86", tint: "#d9f0f1", ink: "#0a5f66", on: "#ffffff" },
};

export const RISK_RGB: Record<RiskGroup, { solid: RGB; ink: RGB }> = {
  High: { solid: hex(RISK_HEX.High.solid), ink: hex(RISK_HEX.High.ink) },
  Medium: { solid: hex(RISK_HEX.Medium.solid), ink: hex(RISK_HEX.Medium.ink) },
  Low: { solid: hex(RISK_HEX.Low.solid), ink: hex(RISK_HEX.Low.ink) },
};

/** CSS values with hex fallbacks, for HTML legends, chips and cards. */
export const RISK_CSS: Record<RiskGroup, { solid: string; tint: string; ink: string; on: string }> = {
  High: { solid: "var(--risk-high, #d55e00)", tint: "var(--risk-high-tint, #fbe3d6)", ink: "var(--risk-high-ink, #a0410a)", on: "var(--risk-high-on, #141414)" },
  Medium: { solid: "var(--risk-medium, #f0c419)", tint: "var(--risk-medium-tint, #fdf4d3)", ink: "var(--risk-medium-ink, #7a5c00)", on: "var(--risk-medium-on, #141414)" },
  Low: { solid: "var(--risk-low, #0e7c86)", tint: "var(--risk-low-tint, #d9f0f1)", ink: "var(--risk-low-ink, #0a5f66)", on: "var(--risk-low-on, #ffffff)" },
};

/** Heat shading (neighborhood heat vulnerability 1 = cooler … 5 = hotter).
 *  Same ramp as the "feels like" time-lapse (replay/colors.ts HEAT_STOPS: pale yellow → orange →
 *  pink → deep purple), sampled at 5 evenly spaced points from 88° to 116°, so every heat scale
 *  in the app reads the same way. */
const HEAT_SAMPLES_F = [88, 95, 102, 109, 116];
export const HEAT_RGB: RGB[] = HEAT_SAMPLES_F.map((f) => {
  const [r, g, b] = heatRgba(f);
  return [Math.round(r), Math.round(g), Math.round(b)];
});
export const HEAT_HEX = HEAT_RGB.map(([r, g, b]) => `rgb(${r},${g},${b})`);

/** Help places (cool places): blue, same as "Places to cool off" in helpTypes.ts.
 *  Was bluish green, which looked like the teal "Low risk" people. */
export const HELP_HEX = "#2563eb";
export const HELP_INK_HEX = "#1d4ed8";
export const HELP_RGB = hex(HELP_HEX);
export const SUBWAY_HEX = "#141414";
export const ROUTE_HEX = "#141414";
