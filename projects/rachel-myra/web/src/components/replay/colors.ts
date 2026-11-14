// Colors for the time-lapse, in the app's Okabe–Ito palette (tokens.css).
// Risk groups: High = orange (Hold vermillion), Medium = yellow, Low = teal (Store-cool teal).
export const GROUP_COLORS = {
  High: { css: "#d55e00", rgb: [213, 94, 0] as [number, number, number], tint: "#fbe3d6", ink: "#a0410a" },
  Medium: { css: "#f0c419", rgb: [240, 196, 25] as [number, number, number], tint: "#fdf4d3", ink: "#7a5c00" },
  Low: { css: "#0e7c86", rgb: [14, 124, 134] as [number, number, number], tint: "#d9f0f1", ink: "#0a5f66" },
} as const;

// Radar-style "feels like" ramp: transparent when it's comfortable, then yellow → orange →
// vermillion → reddish purple → deep purple as it gets dangerous. [°F, r, g, b, alpha 0-1]
export const HEAT_STOPS: [number, number, number, number, number][] = [
  [84, 253, 244, 211, 0],
  [88, 253, 236, 160, 0.32],
  [92, 240, 196, 25, 0.46],
  [96, 230, 159, 0, 0.55],
  [100, 213, 94, 0, 0.62],
  [104, 204, 121, 167, 0.66],
  [108, 160, 70, 150, 0.7],
  [112, 110, 35, 115, 0.74],
  [116, 70, 20, 85, 0.78],
];

export function heatRgba(f: number | null | undefined): [number, number, number, number] {
  if (f == null || !Number.isFinite(f) || f <= HEAT_STOPS[0][0]) return [0, 0, 0, 0];
  for (let i = 1; i < HEAT_STOPS.length; i++) {
    const a = HEAT_STOPS[i - 1], b = HEAT_STOPS[i];
    if (f <= b[0]) {
      const t = (f - a[0]) / (b[0] - a[0]);
      return [a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t, a[3] + (b[3] - a[3]) * t, a[4] + (b[4] - a[4]) * t];
    }
  }
  const z = HEAT_STOPS[HEAT_STOPS.length - 1];
  return [z[1], z[2], z[3], z[4]];
}

/** Solid version for chips, the clock dot and the strip (no transparency). */
export function heatColor(f: number | null | undefined): string {
  if (f == null || !Number.isFinite(f)) return "#d4d4d0";
  if (f <= 88) return "#d9f0f1";
  const [r, g, b] = heatRgba(Math.max(f, 88.01));
  return `rgb(${Math.round(r)},${Math.round(g)},${Math.round(b)})`;
}
