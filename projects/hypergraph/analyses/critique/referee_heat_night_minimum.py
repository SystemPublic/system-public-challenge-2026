"""Referee re-estimation for heat-night-minimum. Written by the blind referee, not the registrant.

Run from the repository root:
    ~/.venvs/nyc-concordance/bin/python analyses/critique/referee_heat_night_minimum.py

It rebuilds the daily series from the cached incident queries and the cached GHCN-Daily files
with its own code (it does not import analyses/round5/heat_night/run.py or the round 2 model
code), refits the deciding models, and runs variants the registrant did not run. It reads the
cache only and fetches nothing. It prints its results and writes no file.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pandas.tseries.holiday import USFederalHolidayCalendar
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
SOC = ROOT / "data/cache/socrata"
NOAA = ROOT / "data/cache/noaa"
DER = ROOT / "data/derived/round5/heat_night"
CAL = "C(dow) + C(month) + C(year) + hol + wet"
CITY = {
    "new_york": {"file": "5ucz-vwe8-53bd22685413061872ba5b52.json", "station": "USW00094728", "start": "2006-01-01",
                 "alt": {"LaGuardia": "USW00014732", "JFK": "USW00094789"}, "half": 1.0753814560820047},
    "chicago": {"file": "gumc-mgzr-a8e75462cf3c43d1413589a9.json", "station": "USW00014819", "start": "2010-01-01",
                "alt": {"O'Hare": "USW00094846"}, "half": 1.0348194642937028},
}
LAST = "2026-08-30"
BLOCKS = ["06_12", "12_18", "18_24", "00_06"]


def weather(sid):
    w = pd.read_csv(NOAA / f"{sid}.csv", low_memory=False, usecols=["DATE", "TMAX", "TMIN", "PRCP"])
    w["DATE"] = pd.to_datetime(w["DATE"])
    w = w.set_index("DATE").asfreq("D")
    w[["TMAX", "TMIN", "PRCP"]] = w[["TMAX", "TMIN", "PRCP"]] / 10.0
    return w


def stamps(name):
    rows = pd.DataFrame(json.loads((SOC / CITY[name]["file"]).read_text())["rows"])
    if "ts" in rows:
        return pd.to_datetime(rows["ts"]).dropna()
    return pd.to_datetime(rows["d"].str[:10] + " " + rows["t"].str[:8]).dropna()


def build(name, ts=None, sid=None):
    c = CITY[name]
    ts = stamps(name) if ts is None else ts
    idx = pd.date_range(c["start"], LAST, freq="D")
    sday = (ts - pd.Timedelta(hours=6)).dt.normalize()
    h = ts.dt.hour
    blk = np.select([(h >= 6) & (h < 12), (h >= 12) & (h < 18), h >= 18], ["06_12", "12_18", "18_24"], "00_06")
    tab = pd.crosstab(sday, blk).reindex(idx).fillna(0).astype(int)
    d = pd.DataFrame(index=idx)
    for b in BLOCKS:
        d["n_" + b] = tab[b] if b in tab else 0
    d["n_day"] = d["n_06_12"] + d["n_12_18"]
    d["n_night"] = d["n_18_24"] + d["n_00_06"]
    d["n"] = d["n_day"] + d["n_night"]
    d["n_cal"] = ts.dt.normalize().value_counts().reindex(idx).fillna(0).astype(int)
    # shootings from 00:00 to 05:59 on the calendar date itself (before that date's maximum)
    d["n_early_same_date"] = ts[h < 6].dt.normalize().value_counts().reindex(idx).fillna(0).astype(int)
    w = weather(sid or c["station"])
    d["TMAX"], d["TMIN"], d["PRCP"] = w["TMAX"].reindex(idx), w["TMIN"].reindex(idx), w["PRCP"].reindex(idx)
    for k, col, s in [("TMIN_next", "TMIN", -1), ("TMIN_next2", "TMIN", -2), ("TMAX_next", "TMAX", -1), ("TMAX_prev", "TMAX", 1),
                      ("PRCP_next", "PRCP", -1), ("TMIN_prev", "TMIN", 1)]:
        d[k] = w[col].shift(s).reindex(idx)
    d["dow"], d["month"], d["year"] = idx.dayofweek, idx.month, idx.year
    hol = USFederalHolidayCalendar().holidays(c["start"], "2026-08-31")
    extra = pd.DatetimeIndex([f"{y}-{md}" for y in range(idx[0].year, 2027) for md in ("07-04", "12-31", "01-01")])
    d["hol"] = idx.isin(hol.union(extra)).astype(int)
    d["wet"] = (d["PRCP"] >= 1.0).astype(int)
    d["wet_next"] = (d["PRCP_next"] >= 1.0).astype(int)
    d["ym"] = d["year"] * 100 + d["month"]
    d["doy"] = idx.dayofyear
    d["sin1"], d["cos1"] = np.sin(2 * np.pi * d["doy"] / 365.25), np.cos(2 * np.pi * d["doy"] / 365.25)
    d["sin2"], d["cos2"] = np.sin(4 * np.pi * d["doy"] / 365.25), np.cos(4 * np.pi * d["doy"] / 365.25)
    for k in ("TMAX", "TMIN", "TMIN_next", "TMIN_next2", "TMAX_next", "TMAX_prev", "TMIN_prev"):
        d[k + "5"] = d[k] / 5
    for i, k in enumerate((15, 21, 27)):
        d[f"k{i}"] = np.clip(d["TMAX"] - k, 0, None)
    return d


def alpha_ml(y, rhs, d):
    try:
        a = float(smf.negativebinomial(f"{y} ~ {rhs}", d).fit(disp=0, maxiter=400).params["alpha"])
        return a if np.isfinite(a) and a > 0 else None
    except Exception:
        return None


def fit(d, y, rhs, alpha_rhs=None, family="nb", cov="HC0", cal=CAL):
    """GLM with log link. alpha by ML from alpha_rhs (default: TMAX5 + calendar, as registered)."""
    full = f"{y} ~ {rhs} + {cal}"
    if family == "poisson":
        fam = sm.families.Poisson()
    else:
        a = alpha_ml(y, (alpha_rhs or "TMAX5") + " + " + cal, d)
        fam = sm.families.NegativeBinomial(alpha=a if a else 0.05)
    kw = {"cov_type": "HC0"} if cov == "HC0" else {"cov_type": "HAC", "cov_kwds": {"maxlags": 7}}
    return smf.glm(full, d, family=fam).fit(**kw)


def rr(r, term, mult=1.0):
    b, s = r.params[term] * mult, r.bse[term] * mult
    return b, s, f"{np.exp(b):.3f} ({np.exp(b - 1.96 * s):.3f} to {np.exp(b + 1.96 * s):.3f})"


def contrast(r, hi=33, lo=27):
    """33 against 27 C from the piecewise-linear TMAX terms TMAX, k0, k1, k2."""
    names = ["TMAX", "k0", "k1", "k2"]
    v = np.array([hi - lo] + [max(hi - k, 0) - max(lo - k, 0) for k in (15, 21, 27)], float)
    b = float(v @ r.params[names].values)
    s = float(np.sqrt(v @ r.cov_params().loc[names, names].values @ v))
    return b, s, f"{np.exp(b):.3f} ({np.exp(b - 1.96 * s):.3f} to {np.exp(b + 1.96 * s):.3f})"


SPL = "TMAX + k0 + k1 + k2"


def spline(d, y, extra="", **kw):
    return fit(d, y, SPL + extra, alpha_rhs="TMAX5", **kw)


def binom(d, num, den, rhs, cal=CAL):
    p = d[d[den] > 0]
    y, X = __import__("patsy").dmatrices(f"{num} ~ {rhs} + {cal}", p, return_type="dataframe")
    return sm.GLM(np.column_stack([p[num].values, (p[den] - p[num]).values]), X, family=sm.families.Binomial()).fit(cov_type="HC0")


def main():
    reg = json.loads((DER / "results.json").read_text())
    for name in CITY:
        print("\n" + "=" * 100 + "\n" + name)
        ts = stamps(name)
        d = build(name, ts)
        # --- data checks
        theirs = pd.read_csv(DER / f"{name}_daily.csv", index_col=0, parse_dates=True)
        same = {k: int((d[k] != theirs[k]).sum()) for k in ("n", "n_day", "n_night", "n_00_06", "n_18_24", "n_cal")}
        print("days where my count differs from the registrant's daily file:", same)
        m = ts.dt.minute
        print(f"incidents {len(ts)}; time exactly 00:00: {((ts.dt.hour == 0) & (m == 0)).mean():.4f}; minute 0: {(m == 0).mean():.3f};"
              f" minute multiple of 5: {(m % 5 == 0).mean():.3f}; hour 0: {(ts.dt.hour == 0).mean():.4f}; hour 1: {(ts.dt.hour == 1).mean():.4f};"
              f" hour 23: {(ts.dt.hour == 23).mean():.4f}")
        print("shares by block (06-12, 12-18, 18-24, 00-06):", [round(float(d['n_' + b].sum() / d['n'].sum()), 3) for b in BLOCKS])

        hot = d[d["TMAX"] >= 27].dropna(subset=["TMAX", "TMIN", "TMIN_next", "TMAX_prev"]).copy()
        print(f"hot days {len(hot)}, shootings {int(hot['n'].sum())}; corr(TMIN, TMAX) {hot['TMIN'].corr(hot['TMAX']):.2f};"
              f" corr(TMIN, TMIN_next) {hot['TMIN'].corr(hot['TMIN_next']):.2f}; corr(TMIN_next, TMAX) {hot['TMIN_next'].corr(hot['TMAX']):.2f};"
              f" corr(TMIN_next, TMAX_next) {hot['TMIN_next'].corr(hot['TMAX_next']):.2f}")
        print("alpha (ML, hot days, no TMIN):", alpha_ml("n", "TMAX5 + " + CAL, hot), " registrant:", reg[name]["part_a"]["primary"]["alpha"])

        # --- (a) primary and variants
        print("\n(a) preceding night's minimum, per 5 C, hot days")
        b, s, txt = rr(fit(hot, "n", "TMAX5 + TMIN5"), "TMIN5")
        p = reg[name]["part_a"]["primary"]
        print(f"  my refit                         {txt}   registrant {p['estimate']:.3f} ({p['lo']:.3f} to {p['hi']:.3f})")
        lo, hi = np.exp(b - 1.96 * s), np.exp(b + 1.96 * s)
        print(f"  support (lo > 1.00): {lo > 1}; refute (hi < {CITY[name]['half']:.4f} and lo <= 1): {hi < CITY[name]['half'] and lo <= 1}")
        print(f"  z against no effect {b / s:.2f}; z against composed 1.012 {(b - np.log(1.0124)) / np.hypot(s, 0.0078):.2f};"
              f" z against the half-excess threshold {(b - np.log(CITY[name]['half'])) / s:.2f}")
        var = {
            "Poisson, HC0": fit(hot, "n", "TMAX5 + TMIN5", family="poisson"),
            "NB, HAC 7 lags": fit(hot, "n", "TMAX5 + TMIN5", cov="HAC"),
            "alpha from the model with TMIN": fit(hot, "n", "TMAX5 + TMIN5", alpha_rhs="TMAX5 + TMIN5"),
            "year-by-month terms": fit(hot, "n", "TMAX5 + TMIN5", cal="C(dow) + C(ym) + hol + wet"),
            "harmonics added": fit(hot, "n", "TMAX5 + TMIN5 + sin1 + cos1 + sin2 + cos2"),
            "TMAX_prev and TMIN_prev added": fit(hot.dropna(subset=["TMIN_prev"]), "n", "TMAX5 + TMIN5 + TMAX_prev5 + TMIN_prev5"),
            "rain amount (log1p PRCP) added": fit(hot.assign(lp=np.log1p(hot["PRCP"].fillna(0))), "n", "TMAX5 + TMIN5 + lp"),
            "without 2020 and 2021": fit(hot[~hot["year"].isin([2020, 2021])], "n", "TMAX5 + TMIN5"),
            "TMAX 27 to 31 C only": fit(hot[hot["TMAX"] < 31], "n", "TMAX5 + TMIN5"),
        }
        for k, r in var.items():
            print(f"  {k:32s} {rr(r, 'TMIN5')[2]}")
        for lab, sid in CITY[name]["alt"].items():
            da = build(name, ts, sid)
            ha = da[da["TMAX"] >= 27].dropna(subset=["TMAX", "TMIN", "TMIN_next", "TMAX_prev"])
            print(f"  {('station ' + lab):32s} {rr(fit(ha, 'n', 'TMAX5 + TMIN5'), 'TMIN5')[2]}  (n {len(ha)})")
            print(f"  {('  following night, ' + lab):32s} {rr(fit(ha, 'n', 'TMAX5 + TMIN_next5'), 'TMIN_next5')[2]}")

        # --- (b) day, night, ratio of ratios, blocks
        a = d.dropna(subset=["TMAX", "TMIN", "TMIN_next"]).copy()
        print("\n(b) ratio 33 against 27 C, all shooting days, piecewise-linear TMAX")
        res = {}
        for y in ["n", "n_cal", "n_day", "n_night"] + ["n_" + b for b in BLOCKS]:
            res[y] = contrast(spline(a, y))
            print(f"  {y:12s} {res[y][2]}   z {res[y][0] / res[y][1]:.2f}  p {2 * stats.norm.sf(abs(res[y][0] / res[y][1])):.4f}")
        print(f"  night over day (binomial)        {contrast(binom(a, 'n_night', 'n', SPL))[2]}")
        a["n_rest"] = a["n"] - a["n_00_06"]
        e = contrast(binom(a, "n_00_06", "n", SPL))
        print(f"  00-06 over the other 18 hours    {e[2]}  p {2 * stats.norm.sf(abs(e[0] / e[1])):.4f}")
        a["n_nt"] = a["n_night"]
        e = contrast(binom(a, "n_00_06", "n_night", SPL))
        print(f"  00-06 over 18-24 (binomial)      {e[2]}  p {2 * stats.norm.sf(abs(e[0] / e[1])):.4f}")
        print("  00-06 block, variants:")
        print(f"    HAC 7 lags                     {contrast(spline(a, 'n_00_06', cov='HAC'))[2]}")
        print(f"    year-by-month terms            {contrast(spline(a, 'n_00_06', cal='C(dow) + C(ym) + hol + wet'))[2]}")
        print(f"    calendar terms of date d+1 too {contrast(spline(a.assign(dow1=(a['dow'] + 1) % 7, hol1=a['hol'].shift(-1).fillna(0)), 'n_00_06', extra=' + hol1'))[2]}")
        for k0, k1 in ((2006, 2015), (2016, 2026)):
            s_ = a[a["year"].between(k0, k1)]
            if len(s_) > 1500:
                print(f"    {k0} to {k1}                   {contrast(spline(s_, 'n_00_06'))[2]}")
        # times exactly at 00:00 removed (possible default value)
        ts2 = ts[~((ts.dt.hour == 0) & (ts.dt.minute == 0))]
        a2 = build(name, ts2).dropna(subset=["TMAX", "TMIN", "TMIN_next"])
        print(f"    without times of exactly 00:00 {contrast(spline(a2, 'n_00_06'))[2]}")
        # alternative six-hour cuts: is 00-06 a sharp boundary or one of several possible windows?
        hh = ts.dt.hour
        for w0, w1 in ((22, 4), (2, 6), (0, 3), (3, 6), (21, 24), (18, 21)):
            mask = ((hh >= w0) | (hh < w1)) if w0 > w1 else ((hh >= w0) & (hh < w1))
            cnt = ((ts[mask] - pd.Timedelta(hours=6)).dt.normalize()).value_counts().reindex(a.index).fillna(0).astype(int)
            print(f"    window {w0:02d}-{w1:02d}                   {contrast(spline(a.assign(nw=cnt), 'nw'))[2]}")
        # early-morning shootings against the maximum of the day before and of the same date
        a3 = a.dropna(subset=["TMAX_prev"]).copy()
        r3 = fit(a3, "n_early_same_date", "TMAX5 + TMAX_prev5 + TMIN5")
        print("  00-06 shootings of calendar date d on TMAX d, TMAX d-1, TMIN d (linear, per 5 C):",
              rr(r3, "TMAX5")[2], "|", rr(r3, "TMAX_prev5")[2], "|", rr(r3, "TMIN5")[2])

        # --- following night
        print("\nfollowing night's minimum (TMIN of d+1), per 5 C, hot days")
        h2 = hot.dropna(subset=["TMIN_next2", "TMAX_next", "PRCP_next"]).copy()
        rows = {
            "alone (registered secondary)": (fit(hot, "n", "TMAX5 + TMIN_next5"), "TMIN_next5"),
            "with preceding": (fit(hot, "n", "TMAX5 + TMIN5 + TMIN_next5"), "TMIN_next5"),
            "HAC 7 lags": (fit(hot, "n", "TMAX5 + TMIN5 + TMIN_next5", cov="HAC"), "TMIN_next5"),
            "year-by-month terms": (fit(hot, "n", "TMAX5 + TMIN5 + TMIN_next5", cal="C(dow) + C(ym) + hol + wet"), "TMIN_next5"),
            "plus wet_next": (fit(h2, "n", "TMAX5 + TMIN5 + TMIN_next5 + wet_next"), "TMIN_next5"),
            "plus TMAX_next and wet_next": (fit(h2, "n", "TMAX5 + TMIN5 + TMIN_next5 + TMAX_next5 + wet_next"), "TMIN_next5"),
            "  TMAX_next in that model": (fit(h2, "n", "TMAX5 + TMIN5 + TMIN_next5 + TMAX_next5 + wet_next"), "TMAX_next5"),
            "placebo: TMIN of d+2 alone": (fit(h2, "n", "TMAX5 + TMIN_next25"), "TMIN_next25"),
            "placebo: TMIN d+2 with d+1": (fit(h2, "n", "TMAX5 + TMIN5 + TMIN_next5 + TMIN_next25"), "TMIN_next25"),
            "  TMIN d+1 in that model": (fit(h2, "n", "TMAX5 + TMIN5 + TMIN_next5 + TMIN_next25"), "TMIN_next5"),
        }
        for k, (r, t) in rows.items():
            print(f"  {k:32s} {rr(r, t)[2]}")
        for b_ in BLOCKS:
            r = fit(hot, "n_" + b_, "TMAX5 + TMIN5 + TMIN_next5")
            print(f"  block {b_}: following {rr(r, 'TMIN_next5')[2]}   preceding {rr(r, 'TMIN5')[2]}")
        r = fit(h2, "n_day", "TMAX5 + TMIN5 + TMIN_next5")
        print(f"  day shootings (06-18, before the following night): {rr(r, 'TMIN_next5')[2]}")
        # all days, spline, both minima
        r = spline(a, "n", " + TMIN5 + TMIN_next5")
        print(f"  all days, spline + both minima: 33 vs 27 {contrast(r)[2]}; preceding {rr(r, 'TMIN5')[2]}; following {rr(r, 'TMIN_next5')[2]}")

    # pooled preceding-night estimate
    est = []
    for name in CITY:
        d = build(name)
        hot = d[d["TMAX"] >= 27].dropna(subset=["TMAX", "TMIN", "TMIN_next", "TMAX_prev"])
        b, s, _ = rr(fit(hot, "n", "TMAX5 + TMIN5"), "TMIN5")
        est.append((b, s))
    w = np.array([1 / s ** 2 for _, s in est])
    e = float(sum(wi * b for wi, (b, _) in zip(w, est)) / w.sum())
    s = float(w.sum() ** -0.5)
    print(f"\npooled preceding night: {np.exp(e):.3f} ({np.exp(e - 1.96 * s):.3f} to {np.exp(e + 1.96 * s):.3f}); z null {e / s:.2f}")


if __name__ == "__main__":
    main()
