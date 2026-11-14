// Display helpers shared by the dashboard components. Pure functions —
// safe in client and server components alike.

/** ρ with an explicit sign; em-dash when no district-level check exists. */
export function fmtRho(r: number | null | undefined, digits = 3): string {
  if (r === null || r === undefined) return "—";
  return (r > 0 ? "+" : "") + r.toFixed(digits);
}

/** Effect sizes mix OR/RR/r — display with 2 decimals, compare directions only. */
export function fmtMed(m: number | null | undefined): string {
  if (m === null || m === undefined) return "—";
  return m.toFixed(2);
}

export function rhoClass(r: number | null | undefined): string {
  if (r === null || r === undefined) return "";
  return r >= 0 ? "pos" : "neg";
}

export function fmtInt(n: number): string {
  return n.toLocaleString("en-US");
}

/** House style: em dashes read as pauses; copy uses colons instead. */
export function deEmdash(s: string): string {
  return s.replace(/\s*—\s*/g, ": ");
}

/** Compact effect label: "OR ≈ 1.39" style, or null when no estimate. */
export function fmtEffect(
  med: number | null | undefined,
  et: string | null | undefined,
): string | null {
  if (med === null || med === undefined || !et) return null;
  const sym: Record<string, string> = {
    odds_ratio: "OR",
    adjusted_odds_ratio: "adj. OR",
    hazard_ratio: "HR",
    adjusted_hazard_ratio: "adj. HR",
    risk_ratio: "RR",
    relative_risk: "RR",
    rate_ratio: "RR",
    incident_rate_ratio: "IRR",
    pearson_r: "r",
    spearman_r: "ρ",
    correlation_coefficient: "r",
    coefficient: "β",
  };
  return `${sym[et] ?? et} ≈ ${med.toFixed(2)}`;
}

/**
 * Effect direction for ratio-family statistics (OR/RR > 1 = up) and
 * additive/correlational ones (sign of the estimate). Null when unknown.
 */
export function effectDirection(
  med: number | null | undefined,
  et: string | null | undefined,
): "up" | "down" | null {
  if (med === null || med === undefined || !et) return null;
  const additive =
    et === "pearson_r" ||
    et === "spearman_r" ||
    et === "correlation_coefficient" ||
    et === "coefficient" ||
    et.startsWith("mean_difference");
  if (additive) return med > 0 ? "up" : "down";
  return med > 1 ? "up" : "down";
}

