// Heat-wave probability (spec §6.6, NOAA only, no custom ML):
//   0-7 days  → NWS/CDC HeatRisk by ZIP (a forecast level, not a probability)
//   6-14 days → CPC 6-10 / 8-14 day outlooks tilting the historical odds
//   3-4 weeks → CPC week 3-4 outlook tilting the historical odds
//   1-13 months → CPC monthly / seasonal outlooks tilting the historical odds
//   otherwise → historical odds of being inside a heat wave on that calendar date
// Heat wave (history files) = ≥3 consecutive days with TMAX ≥ 90 °F (data/raw/climate/README.md).

import type { HeatRiskLevel } from "../types/health-system.ts";
import type { HeatWaveOutlook } from "../types/patient.ts";
import { parseCsv } from "./csv.ts";

export interface HeatRiskDay {
  date: string;
  level: HeatRiskLevel;
}
export type HeatRiskByZip = Map<string, HeatRiskDay[]>;

export interface CpcOutlook {
  outlook: string;
  issued: string;
  valid_start: string | null;
  valid_end: string | null;
  valid_season: string | null;
  favored_category: string | null;
  p_above_normal_est_pct: number | null;
}

export interface HistoricalOdds {
  /** MM-DD → probability of being inside a heat wave (0-1). */
  pInHeatwave: Map<string, number>;
  /** MM-DD → probability of any heat-wave day within the next 14 days (0-1). */
  pWithin14d: Map<string, number>;
  column: string;
}

export interface ForecastInputs {
  heatrisk: HeatRiskByZip;
  heatriskLabel: string;
  cpc: CpcOutlook[];
  history: HistoricalOdds;
}

// ---------------------------------------------------------------- parsers

export function heatRiskFromCurrentJson(j: any): HeatRiskByZip {
  const out: HeatRiskByZip = new Map();
  for (const [zip, v] of Object.entries<any>(j?.zips ?? {})) {
    const days: HeatRiskDay[] = (v.days ?? [])
      .filter((d: any) => typeof d.heatrisk === "number")
      .map((d: any) => ({ date: String(d.valid_utc).slice(0, 10), level: Math.max(0, Math.min(4, d.heatrisk)) as HeatRiskLevel }));
    out.set(zip, days.sort((a, b) => a.date.localeCompare(b.date)));
  }
  return out;
}

export function heatRiskFromReplayCsv(text: string): HeatRiskByZip {
  const out: HeatRiskByZip = new Map();
  for (const r of parseCsv(text)) {
    const lvl = Number(r.heatrisk_day1);
    if (!Number.isFinite(lvl)) continue;
    const arr = out.get(r.zip) ?? [];
    arr.push({ date: r.date, level: lvl as HeatRiskLevel });
    out.set(r.zip, arr);
  }
  for (const a of out.values()) a.sort((x, y) => x.date.localeCompare(y.date));
  return out;
}

export function cpcFromJson(j: any): CpcOutlook[] {
  return (j?.outlooks ?? []).map((o: any) => ({
    outlook: o.outlook,
    issued: o.issued,
    valid_start: o.valid_start ?? null,
    valid_end: o.valid_end ?? null,
    valid_season: o.valid_season ?? null,
    favored_category: o.favored_category ?? null,
    p_above_normal_est_pct: typeof o.p_above_normal_est_pct === "number" ? o.p_above_normal_est_pct : null,
  }));
}

export function historyFromCsv(text: string, column: string, within14Column: string): HistoricalOdds {
  const p = new Map<string, number>();
  const w = new Map<string, number>();
  for (const r of parseCsv(text)) {
    p.set(r.month_day, Number(r[column]) || 0);
    w.set(r.month_day, Number(r[within14Column]) || 0);
  }
  return { pInHeatwave: p, pWithin14d: w, column };
}

// ---------------------------------------------------------------- helpers

export function addDays(iso: string, n: number): string {
  const d = new Date(`${iso.slice(0, 10)}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
export function daysBetween(a: string, b: string): number {
  return Math.round((Date.parse(`${b.slice(0, 10)}T12:00:00Z`) - Date.parse(`${a.slice(0, 10)}T12:00:00Z`)) / 86400000);
}

const SEASONS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** Does a CPC monthly ("Nov 2026") or seasonal ("JJA 2027", "NDJ 2026-2027") label cover the date? */
export function seasonCovers(label: string, iso: string): boolean {
  const y = Number(iso.slice(0, 4));
  const m = Number(iso.slice(5, 7)); // 1-12
  const years = (label.match(/\d{4}/g) ?? []).map(Number);
  const code = label.slice(0, 3);
  const mi = MONTHS.indexOf(code);
  if (mi >= 0) return mi + 1 === m && years.includes(y);
  const si = SEASONS.indexOf(code);
  if (si < 0) return false;
  const months = [0, 1, 2].map((k) => ((si + 11 + k) % 12) + 1); // DJF → 12,1,2
  if (!years.length) return months.includes(m);
  // Assign a year to each month: start at the first year in the label, +1 when the months wrap.
  let yr = years.length === 1 && months[0] > months[2] ? years[0] - 1 : years[0];
  for (let k = 0; k < 3; k++) {
    if (k > 0 && months[k] < months[k - 1]) yr++;
    if (months[k] === m && yr === y) return true;
  }
  return false;
}

function tilt(hist: number, pAbove: number | null): number {
  if (pAbove === null) return hist;
  return Math.max(0, Math.min(1, hist * (pAbove / (100 / 3))));
}

export const FORECAST_METHOD = {
  forecast: "NWS/CDC HeatRisk level for the ZIP and day (deterministic forecast; bar = level / 4, labeled as a level, not a probability)",
  tilt: "p = historical p(in heat wave on this date) × (CPC p(above normal) ÷ 33.3%), capped at 1. Equal chances leaves history unchanged; history 0 stays 0 (e.g. November).",
  history: "Fraction of 1991-2026 years in which this calendar date was inside a heat wave (≥3 days ≥90 °F), 15-day smoothed",
};

export function heatWaveOutlook(targetDate: string, asOf: string, zip: string, inp: ForecastInputs): HeatWaveOutlook {
  const lead = daysBetween(asOf, targetDate);
  // Never use an outlook issued after the as-of date (matters for replays of past heat waves).
  inp = { ...inp, cpc: inp.cpc.filter((o) => !o.issued || o.issued <= asOf) };
  const md = targetDate.slice(5, 10);
  const hist = inp.history.pInHeatwave.get(md) ?? 0;
  const base = { targetDate, leadDays: lead, historical: hist };

  if (lead >= 0 && lead <= 6) {
    const day = inp.heatrisk.get(zip)?.find((d) => d.date === targetDate);
    if (day) {
      return {
        ...base,
        window: "0-7d forecast",
        source: inp.heatriskLabel,
        probability: null,
        heatrisk: day.level,
        barFraction: day.level / 4,
        method: FORECAST_METHOD.forecast,
      };
    }
  }
  const covering = (pred: (o: CpcOutlook) => boolean) =>
    inp.cpc.find((o) => pred(o) && o.valid_start && o.valid_end && targetDate >= o.valid_start && targetDate <= o.valid_end);
  if (lead >= 5 && lead <= 14) {
    const o = covering((o) => /6-10/.test(o.outlook)) ?? covering((o) => /8-14/.test(o.outlook));
    if (o) {
      const p = tilt(hist, o.p_above_normal_est_pct);
      return { ...base, window: "6-14d outlook", source: `NOAA CPC ${o.outlook} outlook (issued ${o.issued}) × NOAA history`, probability: p, heatrisk: null, barFraction: p, method: FORECAST_METHOD.tilt };
    }
  }
  if (lead >= 14 && lead <= 35) {
    const o = covering((o) => /week 3-4/i.test(o.outlook));
    if (o) {
      const p = tilt(hist, o.p_above_normal_est_pct);
      return { ...base, window: "week 3-4 outlook", source: `NOAA CPC ${o.outlook} outlook (issued ${o.issued}) × NOAA history`, probability: p, heatrisk: null, barFraction: p, method: FORECAST_METHOD.tilt };
    }
  }
  if (lead >= 0 && lead <= 400) {
    const o =
      inp.cpc.find((o) => /monthly/i.test(o.outlook) && o.valid_season && seasonCovers(o.valid_season, targetDate)) ??
      inp.cpc.find((o) => /seasonal/i.test(o.outlook) && o.valid_season && seasonCovers(o.valid_season, targetDate));
    if (o) {
      const p = tilt(hist, o.p_above_normal_est_pct);
      return { ...base, window: "monthly/seasonal outlook", source: `NOAA CPC ${o.outlook} (${o.valid_season}, issued ${o.issued}) × NOAA history`, probability: p, heatrisk: null, barFraction: p, method: FORECAST_METHOD.tilt };
    }
  }
  return { ...base, window: "history only", source: `NOAA GHCN-Daily history, Central Park (${inp.history.column})`, probability: hist, heatrisk: null, barFraction: hist, method: FORECAST_METHOD.history };
}

/** HeatRisk for a ZIP on a date (0 when no forecast exists for that day). */
export function heatRiskOn(inp: Pick<ForecastInputs, "heatrisk">, zip: string, date: string): HeatRiskLevel | null {
  return inp.heatrisk.get(zip)?.find((d) => d.date === date)?.level ?? null;
}

/** Max HeatRisk over (asOf, asOf + days], i.e. excluding today. */
export function maxHeatRiskAhead(inp: Pick<ForecastInputs, "heatrisk">, zip: string, asOf: string, days: number): HeatRiskLevel {
  let m = 0;
  for (const d of inp.heatrisk.get(zip) ?? []) {
    const k = daysBetween(asOf, d.date);
    if (k >= 1 && k <= days) m = Math.max(m, d.level);
  }
  return m as HeatRiskLevel;
}
