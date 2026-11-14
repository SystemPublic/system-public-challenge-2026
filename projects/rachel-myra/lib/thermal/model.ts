// Lumped-capacitance package model: scalar TypeScript port of
// scripts/thermal_sim/model.py. Keep the two line-by-line in sync; the test
// harness (lib/thermal/test/compare.ts) checks they agree on the precomputed
// demo scenarios. Physics and assumptions: scripts/thermal_sim/README.md.

import { ENVIRONMENTS, PACKAGING, PARAMS } from "./params.ts";
import type { Packaging } from "./params.ts";

export type Leg = [env: string, start: number, end: number]; // epoch seconds (UTC)

export type WeatherInput = {
  start_utc: number; // epoch seconds of the first hourly value
  step_s?: number; // default 3600
  temp_c: number[];
  wind_ms: number[];
  cloud: number[]; // 0..1
};

export type Weather = WeatherInput & {
  step_s: number;
  hours: number[];
  hub_ema: number[];
  home_ema: number[];
};

const TWO_OVER_PI = 2 / Math.PI;

export function emaHourly(temp: number[], tauH: number): number[] {
  const a = 1 - Math.exp(-1 / tauH);
  const out: number[] = new Array(temp.length);
  let acc = temp[0];
  for (let i = 0; i < temp.length; i++) {
    if (i > 0) acc = acc + a * (temp[i] - acc);
    out[i] = acc;
  }
  return out;
}

export function makeWeather(w: WeatherInput): Weather {
  const step = w.step_s ?? 3600;
  const cloud = w.cloud.map((c) => Math.min(1, Math.max(0, c)));
  return {
    ...w,
    cloud,
    step_s: step,
    hours: w.temp_c.map((_, i) => w.start_utc + step * i),
    hub_ema: emaHourly(w.temp_c, PARAMS.env.hub_tau_h),
    home_ema: emaHourly(w.temp_c, PARAMS.env.home_tau_h),
  };
}

/** Linear interpolation on the hourly grid, clamped at both ends (like numpy.interp). */
export function interp(w: Weather, arr: number[], t: number): number {
  const n = w.hours.length;
  if (t <= w.hours[0]) return arr[0];
  if (t >= w.hours[n - 1]) return arr[n - 1];
  const x = (t - w.hours[0]) / w.step_s;
  const i = Math.floor(x);
  const f = (t - w.hours[i]) / (w.hours[i + 1] - w.hours[i]);
  return arr[i] + f * (arr[i + 1] - arr[i]);
}

export type Sun = { cosz: number; sinz: number; ghi: number; dni: number; dhi: number };

/** NOAA solar position + Haurwitz clear sky + Kasten-Czeplak clouds + Erbs split. */
export function solar(t: number, cloud: number): Sun {
  const S = PARAMS.solar;
  const lat = (PARAMS.site.lat_deg * Math.PI) / 180;
  const lon = PARAMS.site.lon_deg;
  const days = Math.floor(t / 86400);
  const hour = (t - days * 86400) / 3600;
  const d = new Date(days * 86400 * 1000);
  const doy = Math.round((Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) - Date.UTC(d.getUTCFullYear(), 0, 1)) / 86400000) + 1;
  const g = ((2 * Math.PI) / 365) * (doy - 1 + (hour - 12) / 24);
  const eqt = 229.18 * (0.000075 + 0.001868 * Math.cos(g) - 0.032077 * Math.sin(g) - 0.014615 * Math.cos(2 * g) - 0.040849 * Math.sin(2 * g));
  const decl = 0.006918 - 0.399912 * Math.cos(g) + 0.070257 * Math.sin(g) - 0.006758 * Math.cos(2 * g) + 0.000907 * Math.sin(2 * g) - 0.002697 * Math.cos(3 * g) + 0.00148 * Math.sin(3 * g);
  const tst = hour * 60 + eqt + 4 * lon;
  const ha = ((tst / 4 - 180) * Math.PI) / 180;
  let cosz = Math.sin(lat) * Math.sin(decl) + Math.cos(lat) * Math.cos(decl) * Math.cos(ha);
  cosz = Math.min(1, Math.max(-1, cosz));
  const sinz = Math.sqrt(1 - cosz * cosz);
  const up = cosz > S.cosz_min;
  const cz = up ? cosz : 1;
  const ghiClear = up ? S.haurwitz_a * cz * Math.exp(-S.haurwitz_b / cz) : 0;
  const cl = Math.min(1, Math.max(0, cloud));
  const ghi = ghiClear * (1 - S.kc_a * Math.pow(cl, S.kc_b));
  const i0 = S.solar_const * (1 + 0.033 * Math.cos((2 * Math.PI * doy) / 365));
  const kt = up ? ghi / (i0 * cz) : 0;
  const df = kt <= 0.22 ? 1 - 0.09 * kt : kt <= 0.8 ? 0.9511 - 0.1604 * kt + 4.388 * kt ** 2 - 16.638 * kt ** 3 + 12.336 * kt ** 4 : 0.165;
  const dhi = ghi * df;
  const dni = up ? (ghi - dhi) / cz : 0;
  return { cosz: up ? cosz : 0, sinz: up ? sinz : 0, ghi, dni, dhi };
}

function coolantProps(p: Packaging): [number, number, number, number] {
  const d = (PARAMS.coolant_types as Record<string, { melt_c: number; latent_j_kg: number; c_solid: number; c_liquid: number }>)[p.coolant_type];
  return [d.melt_c, d.latent_j_kg, d.c_solid, d.c_liquid];
}

export function coolantT(H: number, m: number, melt: number, L: number, cs: number, cl: number): number {
  const ms = m > 0 ? m : 1;
  if (H < 0) return melt + H / (ms * cs);
  if (H <= ms * L) return melt;
  return melt + (H - ms * L) / (ms * cl);
}

export function coolantH(Tc: number, m: number, melt: number, L: number, cs: number, cl: number): number {
  return Tc < melt ? m * cs * (Tc - melt) : m * L + m * cl * (Tc - melt);
}

export type RunResult = { t: number[]; temp: number[]; coolant: (number | null)[]; env: string[] };

/** Expand legs into per-step start times and environments (uniform dt). */
export function legsToGrid(legs: Leg[]): { times: number[]; env: string[] } {
  const dt = PARAMS.num.dt_s;
  const t0 = legs[0][1];
  const t1 = legs[legs.length - 1][2];
  const K = Math.round((t1 - t0) / dt);
  const times: number[] = new Array(K);
  const env: string[] = new Array(K).fill(legs[0][0]);
  for (let k = 0; k < K; k++) times[k] = t0 + dt * k;
  for (const [name, a, b] of legs) {
    for (let k = 0; k < K; k++) if (times[k] >= a - 1e-6 && times[k] < b - 1e-6) env[k] = name;
  }
  return { times, env };
}

/** Simulate one package through a list of legs. temp[0] is the initial state. */
export function simulateLegs(weather: Weather, legs: Leg[], pkgId: string, T0: number): RunResult {
  const { times, env } = legsToGrid(legs);
  const p = PACKAGING[pkgId];
  if (!p) throw new Error(`unknown packaging ${pkgId}`);
  for (const e of env) if (!(ENVIRONMENTS as readonly string[]).includes(e)) throw new Error(`unknown environment ${e}`);
  const H_ = PARAMS.heat;
  const E = PARAMS.env;
  const M = PARAMS.mailbox;
  const dt = PARAMS.num.dt_s;
  const A_top = p.L * p.W;
  const A_bot = A_top;
  const A_side = 2 * (p.L + p.W) * p.H;
  const sideProj = TWO_OVER_PI * p.H * (p.L + p.W);
  const R_wall = p.R_wall;
  const alpha = p.absorptance;
  const C = p.contents_kg * p.contents_c;
  const mc = p.coolant_kg;
  const hasC = mc > 0;
  const Cw = p.wall_c_per_area * (A_top + A_bot + A_side);
  const hasW = Cw > 0;
  const [cMelt, cL, cCs, cCl] = coolantProps(p);
  let T = T0;
  let Tw = T0;
  let H = coolantH(p.coolant_start_c, mc, cMelt, cL, cCs, cCl);

  const R_in = H_.R_film_still;
  const hStill = 1 / R_in;
  const eps = H_.emissivity;
  const sigma = H_.sigma;
  const dR = H_.lw_sky_deficit;
  const rhoG = PARAMS.solar.ground_albedo;
  const fSh = H_.shade_diffuse_factor;
  const fwall = PARAMS.coolant.wall_fraction;
  const Gpc = p.coolant_G_W_K;
  const mbTop = M.L * M.W;
  const mbSide = 2 * (M.L + M.W) * M.H;
  const mbProj = TWO_OVER_PI * M.H * (M.L + M.W);
  const mbArea = 2 * mbTop + mbSide;
  const mbC = M.mass_kg * M.c;
  const tauTruck = E.truck_tau_min * 60;

  const temp: number[] = [T];
  const cool: (number | null)[] = [hasC ? coolantT(H, mc, cMelt, cL, cCs, cCl) : null];
  let truck: number | null = null;
  let mbox: number | null = null;

  for (let k = 0; k < times.length; k++) {
    const t = times[k];
    const e = env[k];
    const Ta = interp(weather, weather.temp_c, t);
    const wind = interp(weather, weather.wind_ms, t);
    const cl = interp(weather, weather.cloud, t);
    const s = solar(t, cl);
    const { ghi, dni, dhi } = s;
    const cz = s.cosz;
    const sz = s.sinz;

    const vp = Math.max(H_.porch_wind_factor * wind, H_.porch_wind_min);
    const Tk = Ta + 273.15;
    const hO = H_.hc_a + H_.hc_b * vp + 4 * eps * sigma * Tk ** 3;
    const lw = (eps * dR * (1 - cl)) / hO;

    const truckTarget = Ta + (E.truck_beta * ghi) / 1000;
    if (truck === null) truck = truckTarget;
    const mbAbs = M.absorptance * (mbTop * (dni * cz + dhi) + mbProj * dni * sz + mbSide * 0.5 * (dhi + rhoG * ghi));
    const mbG = hO * mbArea;
    const mbTarget = Ta + (mbAbs - eps * dR * (1 - cl) * mbTop) / mbG;
    if (mbox === null) mbox = mbTarget;

    const hubT = E.hub_set_c + E.hub_f * (interp(weather, weather.hub_ema, t) + E.hub_gain_c - E.hub_set_c);
    const noac = interp(weather, weather.home_ema, t) + E.home_gain_c;

    let indoorT: number;
    switch (e) {
      case "pharmacy": indoorT = E.pharmacy_c; break;
      case "fridge": indoorT = E.fridge_c; break;
      case "truck": indoorT = truck; break;
      case "hub": indoorT = hubT; break;
      case "mailbox_sun": indoorT = mbox; break;
      case "lobby": indoorT = E.lobby_c; break;
      case "home_ac": indoorT = Math.min(E.home_ac_set_c, noac); break;
      case "home_noac": indoorT = noac; break;
      case "home_noac_top": indoorT = noac + E.home_topfloor_c; break;
      default: indoorT = Ta;
    }
    const sun = e === "porch_sun";
    const outdoor = sun || e === "porch_shade";

    const qTop = sun ? dni * cz + dhi : fSh * dhi;
    const qSide = sun ? (sideProj * dni * sz + A_side * 0.5 * (dhi + rhoG * ghi)) / A_side : fSh * 0.5 * (dhi + rhoG * ghi);
    const Tfloor = sun ? Ta + (H_.floor_absorptance * ghi) / H_.h_floor_eff : Ta;

    const TsaTop = outdoor ? Ta + (alpha * qTop) / hO - (sun ? lw : 0) : indoorT;
    const TsaSide = outdoor ? Ta + (alpha * qSide) / hO : indoorT;
    const TsaBot = outdoor ? Tfloor : indoorT;
    const hf = outdoor ? hO : hStill;
    const RoutB = outdoor ? H_.R_contact_floor : 1 / hf;
    const Row = hasW ? 0.5 * R_wall : R_wall + R_in;
    const Uts = 1 / (1 / hf + Row);
    const Ub = 1 / (RoutB + Row);
    const Go = Uts * (A_top + A_side) + Ub * A_bot;
    const To = (Uts * (A_top * TsaTop + A_side * TsaSide) + Ub * A_bot * TsaBot) / Go;
    const Gi = (A_top + A_side + A_bot) / (0.5 * R_wall + R_in);
    const Gw = hasW ? Gi : Go;
    const Teq = hasW ? Tw : To;

    const Tc = coolantT(H, mc, cMelt, cL, cCs, cCl);
    const Gp = hasC ? (1 - fwall) * Gw + Gpc : Gw;
    const Teqp = hasC ? ((1 - fwall) * Gw * Teq + Gpc * Tc) / Gp : Teq;
    const Tnew = Teqp + (T - Teqp) * Math.exp((-dt * Gp) / C);
    const Qc = hasC ? fwall * Gw * (Teq - Tc) + Gpc * (T - Tc) : 0;
    H = H + Qc * dt;
    const Gwt = Go + Gi;
    const TwTgt = (Go * To + Gi * T) / Gwt;
    Tw = hasW ? TwTgt + (Tw - TwTgt) * Math.exp((-dt * Gwt) / Cw) : Tnew;
    T = Tnew;

    truck = truckTarget + (truck - truckTarget) * Math.exp(-dt / tauTruck);
    mbox = mbTarget + (mbox - mbTarget) * Math.exp((-dt * mbG) / mbC);

    temp.push(T);
    cool.push(hasC ? coolantT(H, mc, cMelt, cL, cCs, cCl) : null);
  }
  const tAll = times.concat([times[times.length - 1] + dt]);
  return { t: tAll, temp, coolant: cool, env };
}
