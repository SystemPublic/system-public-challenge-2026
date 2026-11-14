// Exposure metrics: port of scripts/thermal_sim/metrics.py.
// MKT (USP <1079.2>): T_mk = (dH/R) / -ln( mean_i exp(-dH/(R*T_i)) ), T in kelvin.

import { PARAMS } from "./params.ts";

export const THRESHOLDS_C = [25, 30, 37, 40];

export function mktC(tempsC: number[], deltaHkJmol?: number): number {
  const dh = (deltaHkJmol ?? PARAMS.mkt.delta_h_kj_mol) * 1000;
  const a = dh / PARAMS.mkt.R_gas;
  const x = tempsC.map((c) => -a / (c + 273.15));
  const m = Math.max(...x);
  let s = 0;
  for (const xi of x) s += Math.exp(xi - m);
  const lme = m + Math.log(s / x.length);
  return a / -lme - 273.15;
}

export type Summary = {
  peak_c: number;
  min_c: number;
  mean_c: number;
  mkt_c: number;
  minutes_above: Record<string, number>;
  duration_min: number;
};

/** Metrics over a trace whose first sample is the initial state (time-weighted metrics use samples[1:]). */
export function summarize(tempsC: number[], dtS: number = PARAMS.num.dt_s, deltaHkJmol?: number, thresholds: number[] = THRESHOLDS_C): Summary {
  const body = tempsC.length > 1 ? tempsC.slice(1) : tempsC;
  const minutes_above: Record<string, number> = {};
  for (const th of thresholds) minutes_above[String(th)] = (body.filter((x) => x > th).length * dtS) / 60;
  let peak = -Infinity;
  let low = Infinity;
  for (const x of tempsC) {
    if (x > peak) peak = x;
    if (x < low) low = x;
  }
  return {
    peak_c: peak,
    min_c: low,
    mean_c: body.reduce((a, b) => a + b, 0) / body.length,
    mkt_c: mktC(body, deltaHkJmol),
    minutes_above,
    duration_min: (body.length * dtS) / 60,
  };
}
