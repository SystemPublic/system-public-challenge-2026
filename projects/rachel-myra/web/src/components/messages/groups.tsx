// Risk-group chip styles (Okabe–Ito palette: High = orange, Medium = yellow, Low = teal).
export type RiskGroup = "High" | "Medium" | "Low";

export const GROUP_STYLE: Record<RiskGroup, { solid: string; tint: string; ink: string }> = {
  High: { solid: "#d55e00", tint: "#fbe3d6", ink: "#a0410a" },
  Medium: { solid: "#f0c419", tint: "#fdf4d3", ink: "#7a5c00" },
  Low: { solid: "#0e7c86", tint: "#d9f0f1", ink: "#0a5f66" },
};

export function GroupChip({ group }: { group: RiskGroup }) {
  const s = GROUP_STYLE[group];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border-2 px-2.5 py-0.5 text-xs font-semibold"
      style={{ borderColor: s.ink, background: s.tint, color: s.ink }}
    >
      <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: s.solid }} />
      {group} risk
    </span>
  );
}
