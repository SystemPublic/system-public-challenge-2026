// The toll-schedule chain of sim/model.py, in the browser. Same formulas, same parameter file.
// The random draws use a different generator from numpy, so intervals agree with the
// Python results only to within Monte Carlo error; central values agree exactly.
// No distribution is truncated, so each central value is the median of its draws.
// The entries-to-speed elasticity has a range that crosses zero, so speed, ambulance time
// and survivors take either sign; compare() reports the share of draws with an improvement.
(function (root) {
  const BANDS = ["night", "am", "mid", "pm"];

  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function draw(P, n, seed) {
    const rnd = mulberry32(seed);
    const normal = () => Math.sqrt(-2 * Math.log(1 - rnd())) * Math.cos(2 * Math.PI * rnd());
    const out = [];
    for (let i = 0; i < n; i++) out.push({});
    for (const [name, p] of Object.entries(P.parameters)) {
      for (let i = 0; i < n; i++) {
        let x;
        if (p.dist === "uniform") x = p.lo + (p.hi - p.lo) * rnd();
        else if (p.dist === "loguniform") x = Math.exp(Math.log(p.lo) + (Math.log(p.hi) - Math.log(p.lo)) * rnd());
        else if (p.dist === "normal") x = (p.lo + p.hi) / 2 + (p.hi - p.lo) / 3.92 * normal();
        else throw new Error("unknown dist for " + name);
        out[i][name] = x;
      }
    }
    return out;
  }

  function central(P) {
    const o = {};
    for (const [k, p] of Object.entries(P.parameters)) o[k] = p.value;
    return o;
  }

  function table(P, key) {
    return [0, 1, 2, 3, 4].map(w => BANDS.map(b => P.baseline[b][String(w)][key]));
  }

  function tollNow(P) {
    return [0, 1, 2, 3, 4].map(() => BANDS.map(b => P.current_toll[b]));
  }

  // one schedule, one parameter draw -> outputs (levels for revenue; changes from the baseline for the rest)
  function simulate(P, toll, th, base) {
    const B = base || (P._base = P._base || {
      q0: table(P, "entries"), qx0: table(P, "entries_tlc"), v0: table(P, "speed_mph"), tt0: table(P, "ems_lt_travel_s"),
      arr: table(P, "ems_arrest_per_day"), lt: table(P, "ems_lt_per_day"), t0: tollNow(P)
    });
    const wk = P.constants.weeks_per_year;
    let sQo = 0, sQoT = 0, sQo0 = 0, sQo0T0 = 0;
    const qo = [], qo0 = [];
    for (let w = 0; w < 5; w++) {
      qo.push([]); qo0.push([]);
      for (let b = 0; b < 4; b++) {
        const a0 = B.q0[w][b] - B.qx0[w][b];
        const a = a0 * Math.exp(-th.k_toll * (toll[w][b] - B.t0[w][b]));
        qo0[w].push(a0); qo[w].push(a);
        sQo += a; sQoT += a * toll[w][b]; sQo0 += a0; sQo0T0 += a0 * B.t0[w][b];
      }
    }
    const tbar = sQoT / sQo, tbar0 = sQo0T0 / sQo0;
    let s2 = 0;
    const qo2 = qo.map((row, w) => row.map((a, b) => {
      const x = a * Math.exp(-th.k_shift * (toll[w][b] - tbar)) / Math.exp(-th.k_shift * (B.t0[w][b] - tbar0));
      s2 += x; return x;
    }));
    const f = sQo / s2;
    let rev = 0, qSum = 0, q0Sum = 0, dayQo = 0, dayQo0 = 0, wv = 0, wlnv = 0, ltSum = 0, dtt = 0, surv = 0, crash = 0;
    const byDay = [];
    for (let w = 0; w < 5; w++) {
      let dq = 0, dq0 = 0, dw = 0, dl = 0;
      for (let b = 0; b < 4; b++) {
        const a = qo2[w][b] * f, q = a + B.qx0[w][b], q0 = B.q0[w][b];
        const v = B.v0[w][b] * Math.pow(q / q0, th.beta_speed);
        const tt = B.tt0[w][b] * Math.pow(v / B.v0[w][b], th.theta_ems);
        rev += a * toll[w][b];
        qSum += q; q0Sum += q0; dq += q; dq0 += q0;
        if (b > 0) { dayQo += a; dayQo0 += qo0[w][b]; wv += q0; wlnv += q0 * Math.log(v / B.v0[w][b]); dw += q0; dl += q0 * Math.log(v / B.v0[w][b]); }
        ltSum += B.lt[w][b]; dtt += B.lt[w][b] * (tt - B.tt0[w][b]);
        const odds = th.base_survival / (1 - th.base_survival) * Math.exp(-th.surv_per_min * (tt - B.tt0[w][b]) / 60);
        surv += B.arr[w][b] * (odds / (1 + odds) - th.base_survival);
        crash += Math.pow(q / q0, th.crash_volume) * Math.pow(v / B.v0[w][b], th.crash_speed) * q0;
      }
      byDay.push({ entries_pct: 100 * (dq / dq0 - 1), speed_pct: 100 * (Math.exp(dl / dw) - 1) });
    }
    const removed = 1 - dayQo / dayQo0, dlnv = wlnv / wv;
    return {
      entries_pct: 100 * (qSum / q0Sum - 1),
      speed_pct: 100 * (Math.exp(dlnv) - 1),
      revenue_musd: rev * th.charge_factor * wk / 1e6,
      ambulance_s: dtt / ltSum,
      arrest_survivors: surv * wk,
      retail_pct: 100 * th.retail_per_visit * (-th.car_share * th.spend_ratio * (1 - th.diversion) * removed + th.amenity * dlnv),
      crashes_pct: 100 * (crash / q0Sum - 1),
      byDay: byDay
    };
  }

  function quantiles(xs) {
    const s = Float64Array.from(xs).sort();
    const q = p => { const i = p * (s.length - 1), a = Math.floor(i); return s[a] + (s[Math.min(a + 1, s.length - 1)] - s[a]) * (i - a); };
    return { lo: q(0.025), median: q(0.5), hi: q(0.975) };
  }

  // +1: a rise is an improvement; -1: a fall is; 0: neither direction is called an improvement
  const BETTER = { entries_pct: 0, speed_pct: 1, revenue_musd: 1, ambulance_s: -1, arrest_survivors: 1, retail_pct: 1, crashes_pct: -1 };

  // a schedule against the current one, over the draws
  function compare(P, toll, draws) {
    const keys = ["entries_pct", "speed_pct", "revenue_musd", "ambulance_s", "arrest_survivors", "retail_pct", "crashes_pct"];
    const acc = {}; keys.forEach(k => acc[k] = []);
    const day = [0, 1, 2, 3, 4].map(() => ({ entries_pct: [], speed_pct: [] }));
    const t0 = tollNow(P);
    for (const th of draws) {
      const s = simulate(P, toll, th), b = simulate(P, t0, th);
      keys.forEach(k => acc[k].push(k === "revenue_musd" ? s[k] - b[k] : s[k]));
      s.byDay.forEach((d, w) => { day[w].entries_pct.push(d.entries_pct); day[w].speed_pct.push(d.speed_pct); });
    }
    const out = {};
    keys.forEach(k => {
      out[k] = quantiles(acc[k]);
      out[k].p_improve = BETTER[k] ? acc[k].filter(x => x * BETTER[k] > 0).length / acc[k].length : null;
    });
    out.byDay = day.map(d => ({ entries_pct: quantiles(d.entries_pct), speed_pct: quantiles(d.speed_pct) }));
    return out;
  }

  const api = { BANDS, BETTER, draw, central, simulate, compare, tollNow, quantiles };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.SimModel = api;
})(typeof window !== "undefined" ? window : globalThis);
