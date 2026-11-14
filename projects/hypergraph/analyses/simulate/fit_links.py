"""Fit the two links that the city's data can estimate, and the holdout test.

  speed-flow     ln speed(day, band) on ln vehicle entries(day, band), by band,
                 with band x month and band x weekday fixed effects
  ambulance      ln EMS travel time (life-threatening segments) on ln speed, pooled,
                 with the same fixed effects

`fit(panel)` returns the estimates; `holdout(calib, hold)` applies the registered
test of sim-crz-holdout-2026. Standard errors are clustered by week.

  python -m analyses.simulate.fit_links calib      # writes fits_calib.json (and a split-2025 rehearsal)
  python -m analyses.simulate.fit_links holdout    # writes holdout_result.json; run after registration only
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "simulate"
BANDS = ["night", "am", "mid", "pm"]
BAND_HOURS = {"night": "21:00-04:59", "am": "05:00-09:59", "mid": "10:00-15:59", "pm": "16:00-20:59"}


def band(h: int) -> str:
    return "night" if (h >= 21 or h < 5) else "am" if h < 10 else "mid" if h < 16 else "pm"


def daily(path, start="2025-01-06", end="2100-01-01") -> pd.DataFrame:
    """Non-holiday weekdays, one row per date and band. Days from 24 December to 1 January are dropped."""
    p = pd.read_csv(path, parse_dates=["date"])
    p = p[(p.date >= start) & (p.date < end)]
    p["band"] = p.hour.map(band)
    p["dow"] = p.date.dt.day_of_week
    xmas = ((p.date.dt.month == 12) & (p.date.dt.day >= 24)) | ((p.date.dt.month == 1) & (p.date.dt.day == 1))
    p = p[(p.dow < 5) & ~p.holiday & ~xmas].copy()
    for k in ("all", "lt", "arrest"):
        p[f"tts_{k}"] = p[f"ems_travel_s_{k}"].fillna(0) * p[f"ems_n_{k}"].fillna(0)
    g = p.groupby(["date", "band", "dow"]).agg(
        trips=("trips", "sum"), miles=("miles", "sum"), hrs=("hours", "sum"), q=("entries", "sum"),
        q_tlc=("entries_tlc", "sum"), q_car=("entries_car", "sum"), q_truck=("entries_truck", "sum"),
        n_all=("ems_n_all", "sum"), n_lt=("ems_n_lt", "sum"), n_arrest=("ems_n_arrest", "sum"),
        tts_all=("tts_all", "sum"), tts_lt=("tts_lt", "sum"), tts_arrest=("tts_arrest", "sum")).reset_index()
    g = g[(g.q > 0) & (g.hrs > 0)]
    g["v"] = g.miles / g.hrs
    g["tt_lt"] = g.tts_lt / g.n_lt
    g["tt_all"] = g.tts_all / g.n_all
    g["lv"], g["lq"], g["ltt"] = np.log(g.v), np.log(g.q), np.log(g.tt_lt)
    g["ym"] = g.date.dt.strftime("%Y-%m")
    g["wk"] = g.date.dt.strftime("%G-%V")
    return g


def _ols(formula, d):
    return smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": d.wk})


def fit(d: pd.DataFrame) -> dict:
    fe = "C(band)*C(ym) + C(band)*C(dow)"
    m = _ols(f"lv ~ {fe} + C(band):lq", d)
    beta = {b: {"est": float(m.params[f"C(band)[{b}]:lq"]), "se": float(m.bse[f"C(band)[{b}]:lq"])} for b in BANDS}
    mp = _ols(f"lv ~ {fe} + lq", d)
    m_nodow = _ols("lv ~ C(band)*C(ym) + C(band):lq", d)
    e = _ols(f"ltt ~ {fe} + lv", d)
    e_nodow = _ols("ltt ~ C(band)*C(ym) + lv", d)
    return {
        "n_days": int(d.date.nunique()), "n_rows": int(len(d)), "period": [str(d.date.min())[:10], str(d.date.max())[:10]],
        "speed_flow_by_band": beta,
        "speed_flow_pooled": {"est": float(mp.params.lq), "se": float(mp.bse.lq)},
        "speed_flow_by_band_without_weekday_effects": {
            b: {"est": float(m_nodow.params[f"C(band)[{b}]:lq"]), "se": float(m_nodow.bse[f"C(band)[{b}]:lq"])} for b in BANDS},
        "ambulance_speed": {"est": float(e.params.lv), "se": float(e.bse.lv)},
        "ambulance_speed_without_weekday_effects": {"est": float(e_nodow.params.lv), "se": float(e_nodow.bse.lv)},
    }


def baseline(d: pd.DataFrame) -> dict:
    """Means by band and weekday over the calibration days: the simulator's starting point."""
    out = {}
    for b in BANDS:
        out[b] = {}
        for w in range(5):
            x = d[(d.band == b) & (d.dow == w)]
            out[b][str(w)] = {
                "entries": float(x.q.mean()), "entries_tlc": float(x.q_tlc.mean()), "entries_car": float(x.q_car.mean()),
                "entries_truck": float(x.q_truck.mean()), "speed_mph": float(x.miles.sum() / x.hrs.sum()),
                "taxi_trip_hours": float(x.hrs.mean()),
                "ems_lt_travel_s": float(x.tts_lt.sum() / x.n_lt.sum()), "ems_lt_per_day": float(x.n_lt.mean()),
                "ems_arrest_per_day": float(x.n_arrest.mean()),
                "ems_arrest_travel_s": float(x.tts_arrest.sum() / max(x.n_arrest.sum(), 1)), "n_days": int(len(x))}
    return out


def holdout_test(f: dict, h: pd.DataFrame) -> dict:
    """The registered slope tests: do the fitted elasticities predict held-out days?
    The outcome is regressed on the fitted elasticity times the regressor, with band x month
    and band x weekday effects, so a slope of 1 means the held-out elasticity equals the fitted one."""
    h = h.copy()
    h["z_pooled"] = f["speed_flow_pooled"]["est"] * h.lq
    h["z_band"] = h.band.map(lambda b: f["speed_flow_by_band"][b]["est"]) * h.lq
    h["ze"] = f["ambulance_speed"]["est"] * h.lv
    fe = "C(band)*C(ym) + C(band)*C(dow)"
    res = {}
    for name, y, x in (("speed_primary_pooled", "lv", "z_pooled"), ("speed_by_band", "lv", "z_band"), ("ambulance", "ltt", "ze")):
        m = _ols(f"{y} ~ {fe} + {x}", h.dropna(subset=[y, x]))
        s, se = float(m.params[x]), float(m.bse[x])
        res[name] = {"slope": s, "se": se, "lo": s - 1.96 * se, "hi": s + 1.96 * se, "n": int(m.nobs)}
    return res


def level_test(f: dict, c: pd.DataFrame, h: pd.DataFrame) -> dict:
    """Predicted and observed mean speed and EMS travel time by band in the held-out days.
    `c` holds the reference days (the same calendar months one year earlier). Predictions:
      speed_pred   reference mean for the band and weekday, moved by the pooled elasticity times
                   the change in log entries
      tt_chain     reference travel time moved by the ambulance elasticity times the PREDICTED change in log speed
      tt_link      reference travel time moved by the ambulance elasticity times the OBSERVED change in log speed
    The naive prediction is the reference mean."""
    cm = c.groupby(["band", "dow"]).agg(lq0=("lq", "mean"), lv0=("lv", "mean"), lt0=("ltt", "mean")).reset_index()
    h = h.merge(cm, on=["band", "dow"])
    h["lv_hat"] = h.lv0 + f["speed_flow_pooled"]["est"] * (h.lq - h.lq0)
    h["lt_chain"] = h.lt0 + f["ambulance_speed"]["est"] * (h.lv_hat - h.lv0)
    h["lt_link"] = h.lt0 + f["ambulance_speed"]["est"] * (h.lv - h.lv0)
    out = {"by_band": {}}
    pct = lambda a, b: float(100 * (a / b - 1))
    for b in BANDS:
        x = h[h.band == b]
        r = {"n": int(len(x)), "entries_change_pct": float(100 * (np.exp((x.lq - x.lq0).mean()) - 1)),
             "speed_ref": float(np.exp(x.lv0.mean())), "speed_pred": float(np.exp(x.lv_hat.mean())),
             "speed_obs": float(np.exp(x.lv.mean())),
             "tt_ref": float(np.exp(x.lt0.mean())), "tt_chain": float(np.exp(x.lt_chain.mean())),
             "tt_link": float(np.exp(x.lt_link.mean())), "tt_obs": float(np.exp(x.ltt.mean()))}
        r["speed_err_pct"] = pct(r["speed_pred"], r["speed_obs"])
        r["speed_naive_err_pct"] = pct(r["speed_ref"], r["speed_obs"])
        r["tt_chain_err_pct"] = pct(r["tt_chain"], r["tt_obs"])
        r["tt_link_err_pct"] = pct(r["tt_link"], r["tt_obs"])
        r["tt_naive_err_pct"] = pct(r["tt_ref"], r["tt_obs"])
        out["by_band"][b] = r
    for k in ("speed_err_pct", "speed_naive_err_pct", "tt_chain_err_pct", "tt_link_err_pct", "tt_naive_err_pct"):
        out["mean_abs_" + k] = float(np.mean([abs(v[k]) for v in out["by_band"].values()]))
    return out


def main(which):
    c = daily(DER / "panel_calib.csv", end="2026-01-01")
    f = fit(c)
    if which == "calib":
        f["baseline"] = baseline(c)
        # rehearsal inside the calibration year: fit January-June 2025, test July-December 2025
        a, b = c[c.date < "2025-07-01"], c[c.date >= "2025-07-01"]
        fa = fit(a)
        f["rehearsal_split_2025"] = {"fit_first_half": {k: fa[k] for k in ("speed_flow_by_band", "speed_flow_pooled", "ambulance_speed")},
                                     "test_second_half": holdout_test(fa, b)}
        (DER / "fits_calib.json").write_text(json.dumps(f, indent=1))
        print(json.dumps({k: v for k, v in f.items() if k != "baseline"}, indent=1))
    else:
        h = daily(DER / "panel_holdout.csv", start="2026-01-05", end="2026-07-01")
        out = {"fit": {k: f[k] for k in ("speed_flow_by_band", "speed_flow_pooled", "ambulance_speed")},
               "slopes": holdout_test(f, h), "level": level_test(f, c[c.date < "2025-07-01"], h),
               "holdout_days": int(h.date.nunique()), "holdout_period": [str(h.date.min())[:10], str(h.date.max())[:10]]}
        (DER / "holdout_result.json").write_text(json.dumps(out, indent=1))
        print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
