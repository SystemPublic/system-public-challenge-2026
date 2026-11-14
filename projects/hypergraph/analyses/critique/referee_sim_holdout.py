"""Referee re-estimation for sim-crz-holdout-2026. Written by the blind referee, not the registrant.

Run from the repository root:
    ~/.venvs/nyc-concordance/bin/python analyses/critique/referee_sim_holdout.py

It rebuilds the band-by-day panels from data/derived/simulate/panel_calib.csv and
panel_holdout.csv with its own code (it does not import analyses/simulate/fit_links.py),
refits the deciding models and runs variants the registrant did not run. Weather is read
from the cached Central Park GHCN-Daily file. Two sections use data outside
data/derived/simulate/: the yellow-taxi trip files kept outside Dropbox (trip mix and
vendor checks) and data/derived/congestion/bus_speed_cbd.csv (a speed series that does not
come from taxis). Each of those sections is skipped when its input is absent. The last
section checks the simulator (sim/) and the browser model (viz/simulate_model.js, needs node).
It fetches nothing, prints its results and writes no file.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DER = ROOT / "data/derived/simulate"
NOAA = ROOT / "data/cache/noaa/USW00094728.csv"
TLC = Path.home() / "opt" / "nyc-concordance" / "tlc_yellow"
BUS = ROOT / "data/derived/congestion/bus_speed_cbd.csv"
HOL = {"2024-01-01", "2024-01-15", "2024-02-19", "2024-05-27", "2024-06-19", "2024-07-04", "2024-09-02", "2024-10-14",
       "2024-11-11", "2024-11-28", "2024-12-25", "2025-01-01", "2025-01-20", "2025-02-17", "2025-05-26", "2025-06-19",
       "2025-07-04", "2025-09-01", "2025-10-13", "2025-11-11", "2025-11-27", "2025-12-25", "2026-01-01", "2026-01-19",
       "2026-02-16", "2026-05-25", "2026-06-19"}
BANDS = ["night", "am", "mid", "pm"]
FE = "C(band)*C(ym) + C(band)*C(dow)"


def band_of(h):
    return np.where((h >= 21) | (h < 5), "night", np.where(h < 10, "am", np.where(h < 16, "mid", "pm")))


def weather():
    w = pd.read_csv(NOAA, usecols=["DATE", "PRCP", "SNOW", "SNWD", "TMAX", "TMIN"], parse_dates=["DATE"])
    w = w[w.DATE >= "2024-01-01"].rename(columns={"DATE": "date"})
    for c in ("PRCP", "SNOW", "SNWD", "TMAX", "TMIN"):
        w[c] = pd.to_numeric(w[c], errors="coerce")
    w["prcp_mm"], w["snow_mm"], w["snwd_mm"] = w.PRCP / 10, w.SNOW.fillna(0), w.SNWD.fillna(0)
    w["tmax"], w["tmin"] = w.TMAX / 10, w.TMIN / 10
    w["wet"] = (w.prcp_mm >= 1).astype(int)
    w["lprcp"] = np.log1p(w.prcp_mm.fillna(0))
    w["snowday"] = (w.snow_mm > 0).astype(int)
    w["snowcover"] = (w.snwd_mm > 0).astype(int)
    return w[["date", "prcp_mm", "snow_mm", "snwd_mm", "tmax", "tmin", "wet", "lprcp", "snowday", "snowcover"]]


def panel(name, lo, hi):
    p = pd.read_csv(DER / name)
    p["d"] = pd.to_datetime(p.date)
    p = p[(p.d >= lo) & (p.d < hi)].copy()
    p["band"] = band_of(p.hour.values)
    p["dow"] = p.d.dt.dayofweek
    xmas = ((p.d.dt.month == 12) & (p.d.dt.day >= 24)) | ((p.d.dt.month == 1) & (p.d.dt.day == 1))
    p = p[(p.dow < 5) & ~p.date.isin(HOL) & ~xmas]
    p["tt_sum"] = p.ems_travel_s_lt.fillna(0) * p.ems_n_lt.fillna(0)
    g = p.groupby(["d", "band", "dow"], as_index=False).agg(
        trips=("trips", "sum"), miles=("miles", "sum"), hrs=("hours", "sum"), q=("entries", "sum"),
        q_tlc=("entries_tlc", "sum"), q_car=("entries_car", "sum"), q_truck=("entries_truck", "sum"),
        n_lt=("ems_n_lt", "sum"), tt_sum=("tt_sum", "sum"))
    g = g[g.hrs > 0].rename(columns={"d": "date"})
    g["v"] = g.miles / g.hrs
    g["lv"] = np.log(g.v)
    g["lq"] = np.log(g.q.where(g.q > 0))
    g["lq_other"] = np.log((g.q - g.q_tlc).where(g.q > g.q_tlc))
    g["lq_tlc"] = np.log(g.q_tlc.where(g.q_tlc > 0))
    g["ltt"] = np.log((g.tt_sum / g.n_lt).where(g.n_lt > 0))
    g["ldist"] = np.log(g.miles / g.trips)
    g["ltrips"] = np.log(g.trips)
    g["ym"] = g.date.dt.strftime("%Y-%m")
    g["wk"] = g.date.dt.strftime("%G-%V")
    return g.merge(weather(), on="date", how="left")


def ols(formula, d, term):
    cols = [c for c in d.columns if c in formula.replace("(", " ").replace(")", " ").replace(":", " ").replace("*", " ").split()]
    d = d.dropna(subset=list(set(cols)))
    m = smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": d.wk})
    return float(m.params[term]), float(m.bse[term]), int(m.nobs), d.date.nunique()


def show(label, r, scale=1.0):
    e, se, n, nd = r
    e, se = e * scale, se * abs(scale)
    print(f"  {label:58s} {e:+.3f}  se {se:.3f}  ({e - 1.96 * se:+.3f} to {e + 1.96 * se:+.3f})  n {n}, days {nd}")
    return e, se


def section(t):
    print("\n" + "=" * 100 + "\n" + t + "\n" + "=" * 100)


def main():
    K = panel("panel_calib.csv", "2025-01-06", "2026-01-01")
    C24 = panel("panel_calib.csv", "2024-01-01", "2025-01-01")
    H = panel("panel_holdout.csv", "2026-01-05", "2026-07-01")
    WX = "C(band):wet + C(band):lprcp + C(band):snowday + C(band):snowcover + C(band):tmax + C(band):I(tmax**2)"

    section("1. Registered numbers, refitted with referee code")
    b, bse = show("calibration: lv ~ FE + lq (pooled, 2025)", ols(f"lv ~ {FE} + lq", K, "lq"))
    th, thse = show("calibration: ltt ~ FE + lv (2025)", ols(f"ltt ~ {FE} + lv", K, "lv"))
    H["z1"], H["z2"] = b * H.lq, th * H.lv
    s1, s1se = show("held-out S1: lv ~ FE + z1", ols(f"lv ~ {FE} + z1", H, "z1"))
    s2, s2se = show("held-out S2: ltt ~ FE + z2", ols(f"ltt ~ {FE} + z2", H, "z2"))
    print(f"  S1 as an elasticity {s1 * b:+.3f}; z against the prediction (S1 = 1) {(s1 - 1) / s1se:+.1f}; z against no relation {s1 / s1se:+.1f}")
    print(f"  S2: z against the prediction {(s2 - 1) / s2se:+.1f}; z against no relation {s2 / s2se:+.1f}")
    print(f"  S1 interval with the calibration se carried (delta method on the ratio): "
          f"se {np.hypot(s1se, s1 * bse / abs(b)):.3f}")

    section("2. How much do entries vary within the fixed effects? (calibration and held-out)")
    for nm, d in (("2025", K), ("2026 H1", H)):
        d = d.dropna(subset=["lq", "lv"]).copy()
        d["rq"] = smf.ols(f"lq ~ {FE}", d).fit().resid
        d["rv"] = smf.ols(f"lv ~ {FE}", d).fit().resid
        a = d.rq.abs()
        print(f"  {nm}: residual sd of log entries {d.rq.std():.4f}, of log speed {d.rv.std():.4f}; "
              f"share of band-days with |residual entries| < 2% {100 * (a < 0.02).mean():.0f}%, < 5% {100 * (a < 0.05).mean():.0f}%, "
              f"> 10% {100 * (a > 0.10).mean():.1f}%")
        ssx = (d.rq ** 2).sum()
        top = d.assign(sh=d.rq ** 2 / ssx).groupby("date").sh.sum().sort_values(ascending=False).head(8)
        print("    share of the residual variance of log entries by date (top 8): "
              + ", ".join(f"{k:%Y-%m-%d} {100 * v:.0f}%" for k, v in top.items()))
        print(f"    top 8 dates together: {100 * top.sum():.0f}% of the identifying variance")
    dq = K.groupby("date").q.sum()
    print("  2025 lowest daily entries relative to the median weekday: "
          + ", ".join(f"{k:%Y-%m-%d} {v:.2f}" for k, v in (dq / dq.median()).sort_values().head(8).items()))
    dq = H.groupby("date").q.sum()
    low = (dq / dq.median()).sort_values()
    print("  2026 lowest daily entries relative to the median weekday: " + ", ".join(f"{k:%Y-%m-%d} {v:.2f}" for k, v in low.head(8).items()))
    LOW4 = list(low.index[low < 0.8])
    wx = weather().set_index("date")
    print("  weather on the 2026 low days (prcp mm, snowfall mm, snow depth mm, tmax C):")
    for k in low.head(6).index:
        r = wx.loc[k]
        print(f"    {k:%Y-%m-%d} {k:%a} entries {low[k]:.2f}  prcp {r.prcp_mm:.1f} snow {r.snow_mm:.0f} depth {r.snwd_mm:.0f} tmax {r.tmax:.1f}")

    section("3. Is the calibration elasticity (-0.41) stable? Variants on 2025")
    cdq = K.groupby("date").q.sum()
    crel = cdq / cdq.median()
    Cx = K.merge(crel.rename("rel").reset_index(), on="date")
    show("registered", ols(f"lv ~ {FE} + lq", K, "lq"))
    show("without weekday effects (band x month only)", ols("lv ~ C(band)*C(ym) + lq", K, "lq"))
    show("band x ISO week effects in place of band x month", ols("lv ~ C(band)*C(wk) + C(band)*C(dow) + lq", K, "lq"))
    show("band x month x weekday effects", ols("lv ~ C(band)*C(ym)*C(dow) + lq", K, "lq"))
    show("weather controls by band", ols(f"lv ~ {FE} + {WX} + lq", K, "lq"))
    show("weather controls and band x week effects", ols(f"lv ~ C(band)*C(wk) + C(band)*C(dow) + {WX} + lq", K, "lq"))
    show("without days whose entries are < 0.90 of the median", ols(f"lv ~ {FE} + lq", Cx[Cx.rel >= 0.90], "lq"))
    show("without days whose entries are < 0.95 of the median", ols(f"lv ~ {FE} + lq", Cx[Cx.rel >= 0.95], "lq"))
    extra = pd.to_datetime(["2025-04-18", "2025-07-03", "2025-11-26", "2025-11-28", "2025-12-22", "2025-12-23", "2025-01-06",
                            "2025-09-22", "2025-09-23", "2025-09-24", "2025-09-25", "2025-09-26", "2025-10-02", "2025-09-23", "2025-09-24"])
    show("without quasi-holidays and UN week (list in the code)", ols(f"lv ~ {FE} + lq", K[~K.date.isin(extra)], "lq"))
    show("dry days only (prcp < 1 mm, no snow)", ols(f"lv ~ {FE} + lq", K[(K.wet == 0) & (K.snowday == 0)], "lq"))
    for nm, a_, b_ in (("Q1", "2025-01-01", "2025-04-01"), ("Q2", "2025-04-01", "2025-07-01"), ("Q3", "2025-07-01", "2025-10-01"),
                       ("Q4", "2025-10-01", "2026-01-01"), ("H1", "2025-01-01", "2025-07-01"), ("H2", "2025-07-01", "2026-01-01")):
        show(f"2025 {nm}", ols(f"lv ~ {FE} + lq", K[(K.date >= a_) & (K.date < b_)], "lq"))
    for bnd in BANDS:
        show(f"band {bnd} alone", ols("lv ~ C(ym) + C(dow) + lq", K[K.band == bnd], "lq"))
    show("entries other than taxis and for-hire vehicles", ols(f"lv ~ {FE} + lq_other", K, "lq_other"))
    show("taxi and for-hire entries", ols(f"lv ~ {FE} + lq_tlc", K, "lq_tlc"))
    m = smf.ols(f"lv ~ {FE} + lq_other + lq_tlc", K).fit(cov_type="cluster", cov_kwds={"groups": K.wk})
    print(f"  both in one model: other {m.params.lq_other:+.3f} (se {m.bse.lq_other:.3f}), taxi and for-hire {m.params.lq_tlc:+.3f} (se {m.bse.lq_tlc:.3f})")
    show("control: log taxi trips in the speed sample", ols(f"lv ~ {FE} + ltrips + lq", K, "lq"))
    show("control: log mean trip distance", ols(f"lv ~ {FE} + ldist + lq", K, "lq"))
    show("control: both", ols(f"lv ~ {FE} + ltrips + ldist + lq", K, "lq"))
    # placebo: entries of the same weekday one week later, and one week earlier
    Cs = K.sort_values(["band", "date"]).copy()
    key = Cs.set_index(["band", "date"]).lq
    for lag in (7, -7):
        Cs[f"lq_l{lag}"] = [key.get((b_, d_ + pd.Timedelta(days=lag)), np.nan) for b_, d_ in zip(Cs.band, Cs.date)]
    show("placebo: entries one week later (own entries not in the model)", ols(f"lv ~ {FE} + lq_l7", Cs, "lq_l7"))
    show("placebo: entries one week later, own entries in the model", ols(f"lv ~ {FE} + lq + lq_l7", Cs, "lq_l7"))
    # permutation of log entries within band x month x weekday cells
    d = K.dropna(subset=["lq", "lv"]).copy()
    rng = np.random.default_rng(1)
    est = []
    for _ in range(300):
        d["lqp"] = d.groupby(["band", "ym", "dow"]).lq.transform(lambda x: rng.permutation(x.values))
        est.append(smf.ols(f"lv ~ {FE} + lqp", d).fit().params.lqp)
    est = np.array(est)
    print(f"  permutation within band x month x weekday (300 draws): mean {est.mean():+.3f}, sd {est.std():.3f}, "
          f"share at or below the fitted value {np.mean(est <= b):.3f}")
    print("  (a permuted value that is still negative shows what the band x month and band x weekday effects leave unabsorbed)")

    section("4. Held-out speed link: variants on January-June 2026 (elasticity scale; fitted value %.3f)" % b)
    Hx = H.merge(low.rename("rel").reset_index(), on="date")
    storms = pd.to_datetime(["2026-01-26", "2026-02-23"])
    print("  days under 0.80 of the median:", ", ".join(f"{k:%Y-%m-%d}" for k in LOW4))
    rows = [("registered", H), ("without 26 Jan and 23 Feb", H[~H.date.isin(storms)]), ("without the days under 0.80", H[~H.date.isin(LOW4)]),
            ("without the days under 0.90", Hx[Hx.rel >= 0.90]), ("without the days under 0.95", Hx[Hx.rel >= 0.95]),
            ("dry days only", H[(H.wet == 0) & (H.snowday == 0) & (H.snowcover == 0)])]
    held = {}
    for nm, d in rows:
        held[nm] = show(nm, ols(f"lv ~ {FE} + lq", d, "lq"))
    show("weather controls by band, all days", ols(f"lv ~ {FE} + {WX} + lq", H, "lq"))
    show("weather controls by band, without the days under 0.80", ols(f"lv ~ {FE} + {WX} + lq", H[~H.date.isin(LOW4)], "lq"))
    show("band x week effects, without the days under 0.80", ols("lv ~ C(band)*C(wk) + C(band)*C(dow) + lq", H[~H.date.isin(LOW4)], "lq"))
    for nm in ("registered", "without the days under 0.80", "without the days under 0.90"):
        e, se = held[nm]
        print(f"  {nm}: held-out minus fitted {e - b:+.3f}, z of the difference with both standard errors {(e - b) / np.hypot(se, bse):+.2f}; "
              f"S1 = {e / b:.2f} ({(e + 1.96 * se) / b:.2f} to {(e - 1.96 * se) / b:.2f})")
    # leave one date out
    dates = sorted(H.date.unique())
    loo = []
    for dt in dates:
        e, se, _, _ = ols(f"lv ~ {FE} + lq", H[H.date != dt], "lq")
        loo.append((e, se, dt))
    lo_ = sorted(loo)
    print("  leave one date out, held-out elasticity: min %+.3f (without %s), max %+.3f (without %s)"
          % (lo_[0][0], f"{lo_[0][2]:%Y-%m-%d}", lo_[-1][0], f"{lo_[-1][2]:%Y-%m-%d}"))
    print("    S1 upper bound after dropping each single date: max %.2f" % max((e - 1.96 * se) / b for e, se, _ in loo))
    PP = pd.concat([K, H])
    show("pooled 2025 + 2026 H1, all days", ols(f"lv ~ {FE} + lq", PP, "lq"))
    show("pooled 2025 + 2026 H1, without the 2026 days under 0.80", ols(f"lv ~ {FE} + lq", PP[~PP.date.isin(LOW4)], "lq"))
    print("  speed and entries on the four low days against the mean of the same band, month and weekday (other days):")
    for dt in LOW4:
        x = H[H.date == dt]
        for _, r in x.iterrows():
            o = H[(H.band == r.band) & (H.ym == r.ym) & (H.date != dt) & ~H.date.isin(LOW4)]
            print(f"    {dt:%Y-%m-%d} {r.band:5s} entries {100 * (r.q / o.q.mean() - 1):+6.1f}%  speed {100 * (r.v / o.v.mean() - 1):+6.1f}%  "
                  f"taxi trips {100 * (r.trips / o.trips.mean() - 1):+6.1f}%  ambulance travel {100 * (np.exp(r.ltt) / np.exp(o.ltt).mean() - 1):+6.1f}%")

    section("5. Held-out ambulance link: does S2 rest on the low-entry days?")
    rows = [("registered", H), ("without 26 Jan and 23 Feb", H[~H.date.isin(storms)]), ("without the days under 0.80", H[~H.date.isin(LOW4)]),
            ("without the days under 0.90", Hx[Hx.rel >= 0.90]), ("dry days only", H[(H.wet == 0) & (H.snowday == 0) & (H.snowcover == 0)])]
    for nm, d in rows:
        e, se = show(nm + " (elasticity)", ols(f"ltt ~ {FE} + lv", d, "lv"))
        print(f"      S2 = {e / th:.2f} ({(e + 1.96 * se) / th:.2f} to {(e - 1.96 * se) / th:.2f}); z against 1 {(e / th - 1) / (se / abs(th)):+.1f}, "
              f"against 0 {(e / th) / (se / abs(th)):+.1f}")
    show("weather controls by band, all days", ols(f"ltt ~ {FE} + {WX} + lv", H, "lv"))
    show("weather controls by band, without the days under 0.80", ols(f"ltt ~ {FE} + {WX} + lv", H[~H.date.isin(LOW4)], "lv"))
    show("band x week effects, all days", ols("ltt ~ C(band)*C(wk) + C(band)*C(dow) + lv", H, "lv"))
    show("without weekday effects", ols("ltt ~ C(band)*C(ym) + lv", H, "lv"))
    loo = [ols(f"ltt ~ {FE} + lv", H[H.date != dt], "lv")[:2] + (dt,) for dt in dates]
    lo_ = sorted(loo)
    print("  leave one date out: min %+.3f (without %s), max %+.3f (without %s)" % (lo_[0][0], f"{lo_[0][2]:%Y-%m-%d}", lo_[-1][0], f"{lo_[-1][2]:%Y-%m-%d}"))
    d = H.dropna(subset=["ltt", "lv"]).copy()
    d["rv"] = smf.ols(f"lv ~ {FE}", d).fit().resid
    top = d.assign(sh=d.rv ** 2 / (d.rv ** 2).sum()).groupby("date").sh.sum().sort_values(ascending=False).head(6)
    print("  share of the residual variance of log speed by date (top 6): " + ", ".join(f"{k:%Y-%m-%d} {100 * v:.0f}%" for k, v in top.items()))
    print("  calibration variants of the ambulance link (2025):")
    show("registered", ols(f"ltt ~ {FE} + lv", K, "lv"))
    show("weather controls", ols(f"ltt ~ {FE} + {WX} + lv", K, "lv"))
    show("band x week effects", ols("ltt ~ C(band)*C(wk) + C(band)*C(dow) + lv", K, "lv"))
    show("control: log life-threatening calls in the band", ols(f"ltt ~ {FE} + np.log(n_lt) + lv", K, "lv"))
    show("held-out, control: log life-threatening calls", ols(f"ltt ~ {FE} + np.log(n_lt) + lv", H, "lv"))

    section("6. Why did speed fall from January-June 2025 to January-June 2026?")
    A = K[K.date < "2025-07-01"]
    A24 = C24[C24.date < "2024-07-01"]
    print("  by band, ratio of means, 2026 H1 over 2025 H1 (and 2025 H1 over 2024 H1 for the taxi series):")
    for bnd in BANDS:
        a, h, z = A[A.band == bnd], H[H.band == bnd], A24[A24.band == bnd]
        f = lambda x, y, k: 100 * (x[k].mean() / y[k].mean() - 1)
        sp = lambda x: x.miles.sum() / x.hrs.sum()
        print(f"    {bnd:5s} entries {f(h, a, 'q'):+5.1f}%  non-taxi {100 * ((h.q - h.q_tlc).mean() / (a.q - a.q_tlc).mean() - 1):+5.1f}%  "
              f"taxi/FHV entries {f(h, a, 'q_tlc'):+5.1f}%  taxi trips {f(h, a, 'trips'):+5.1f}%  "
              f"trip miles {100 * ((h.miles.sum() / h.trips.sum()) / (a.miles.sum() / a.trips.sum()) - 1):+5.1f}%  "
              f"trip minutes {100 * ((h.hrs.sum() / h.trips.sum()) / (a.hrs.sum() / a.trips.sum()) - 1):+5.1f}%  speed {100 * (sp(h) / sp(a) - 1):+5.1f}%  "
              f"| 2025/2024: trips {f(a, z, 'trips'):+5.1f}%  speed {100 * (sp(a) / sp(z) - 1):+5.1f}%")
    allp = pd.concat([C24, K, H])
    day = allp[allp.band != "night"].groupby("ym").agg(miles=("miles", "sum"), hrs=("hrs", "sum"), trips=("trips", "sum"), q=("q", "sum"),
                                                        nd=("date", "nunique"))
    day["v"] = day.miles / day.hrs
    print("  monthly daytime (05:00-20:59) weekday taxi speed, change on the same month a year earlier; entries per day likewise:")
    for ym in day.index:
        prev = f"{int(ym[:4]) - 1}{ym[4:]}"
        if prev in day.index:
            qe = "" if day.q[prev] == 0 else f"  entries/day {100 * ((day.q[ym] / day.nd[ym]) / (day.q[prev] / day.nd[prev]) - 1):+5.1f}%"
            print(f"    {ym}  speed {day.v[ym]:.2f} mph {100 * (day.v[ym] / day.v[prev] - 1):+5.1f}%  trips/day {100 * ((day.trips[ym] / day.nd[ym]) / (day.trips[prev] / day.nd[prev]) - 1):+5.1f}%{qe}")
    print("  weather, non-holiday weekdays January-June:")
    for nm, d in (("2025", A), ("2026", H)):
        x = d.drop_duplicates("date")
        print(f"    {nm}: days {len(x)}, wet days {int(x.wet.sum())}, days with snowfall {int(x.snowday.sum())}, days with snow on the ground {int(x.snowcover.sum())}, "
              f"total prcp {x.prcp_mm.sum():.0f} mm, mean tmax {x.tmax.mean():.1f} C")
    for nm, sel in (("dry days without snow or snow cover", lambda d: d[(d.wet == 0) & (d.snowday == 0) & (d.snowcover == 0)]),
                    ("March to June only", lambda d: d[d.date.dt.month >= 3])):
        a, h = sel(A), sel(H)
        print(f"    {nm}: speed change by band " + ", ".join(
            f"{bnd} {100 * (h[h.band == bnd].miles.sum() / h[h.band == bnd].hrs.sum()) / (a[a.band == bnd].miles.sum() / a[a.band == bnd].hrs.sum()) - 100:+.1f}%"
            for bnd in BANDS))
    # year-on-year model with weather: lv ~ band x month-of-year + band x dow + weather + year dummy
    Y = pd.concat([A.assign(y26=0), H.assign(y26=1)])
    Y["moy"] = Y.date.dt.month
    for nm, f in (("no weather", "lv ~ C(band)*C(moy) + C(band)*C(dow) + y26"), ("weather controls", f"lv ~ C(band)*C(moy) + C(band)*C(dow) + {WX} + y26"),
                  ("weather and log entries", f"lv ~ C(band)*C(moy) + C(band)*C(dow) + {WX} + lq + y26"),
                  ("weather, entries, trips and trip distance", f"lv ~ C(band)*C(moy) + C(band)*C(dow) + {WX} + lq + ltrips + ldist + y26")):
        show("2026 effect on log speed, " + nm, ols(f, Y, "y26"))
    show("2026 effect on log ambulance travel time, weather controls", ols(f"ltt ~ C(band)*C(moy) + C(band)*C(dow) + {WX} + y26", Y, "y26"))
    show("  the same with log speed in the model", ols(f"ltt ~ C(band)*C(moy) + C(band)*C(dow) + {WX} + lv + y26", Y, "y26"))

    if TLC.exists() and (TLC / "yellow_tripdata_2026-06.parquet").exists():
        section("6b. Taxi trip files: trip mix, vendors and recording (weekdays 05:00-20:59, trips inside the zone, R1 filter)")
        import duckdb
        from analyses.reproduction.register_mmr_cbd_speed import CBD_ZONES
        cbd = ",".join(map(str, CBD_ZONES))
        files = [str(TLC / f"yellow_tripdata_{m}.parquet") for m in pd.period_range("2025-01", "2026-06", freq="M")]
        con = duckdb.connect()
        q = f"""
          with t as (
            select cast(tpep_pickup_datetime as date) as d, hour(tpep_pickup_datetime) as h, VendorID as vendor, trip_distance as dist,
                   date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) as dur, PULocationID as pu, DOLocationID as do_,
                   strftime(tpep_pickup_datetime, '%Y-%m') as ym, filename
            from read_parquet({files}, filename=true, union_by_name=true)
            where PULocationID in ({cbd}) and DOLocationID in ({cbd}))
          select ym, d, vendor, pu, do_,
                 case when dist < 1 then 'a <1' when dist < 2 then 'b 1-2' when dist < 3 then 'c 2-3' else 'd 3+' end as bin,
                 count(*) as n, sum(dist) as miles, sum(dur) / 3600.0 as hrs,
                 sum(case when dur % 60 = 0 then 1 else 0 end) as n_whole_min,
                 sum(case when round(dist * 10) = dist * 10 then 1 else 0 end) as n_tenth
          from t
          where regexp_extract(filename, '(\\d{{4}}-\\d{{2}})', 1) = ym and h between 5 and 20 and dayofweek(d) between 1 and 5
            and dist > 0 and dist <= 50 and dur between 60 and 10800 and dist / (dur / 3600.0) between 0.5 and 50
          group by all"""
        T = con.execute(q).df()
        T["d"] = pd.to_datetime(T.d)
        T = T[~T.d.dt.strftime("%Y-%m-%d").isin(HOL)]
        T["per"] = np.where((T.d >= "2025-01-06") & (T.d < "2025-07-01"), "2025H1", np.where((T.d >= "2026-01-05") & (T.d < "2026-07-01"), "2026H1", ""))
        P_ = T[T.per != ""]
        tot = P_.groupby("per").agg(n=("n", "sum"), miles=("miles", "sum"), hrs=("hrs", "sum"))
        tot["v"] = tot.miles / tot.hrs
        print(f"  speed 2025H1 {tot.v['2025H1']:.3f}, 2026H1 {tot.v['2026H1']:.3f}, change {100 * (tot.v['2026H1'] / tot.v['2025H1'] - 1):+.1f}%; "
              f"trips {100 * (tot.n['2026H1'] / tot.n['2025H1'] - 1):+.1f}%")
        g = P_.groupby(["per", "bin"]).agg(n=("n", "sum"), miles=("miles", "sum"), hrs=("hrs", "sum")).reset_index()
        g["v"] = g.miles / g.hrs
        w = g.pivot(index="bin", columns="per", values=["n", "v", "hrs", "miles"])
        print("  by trip distance (miles): share of trips 2025H1, 2026H1; speed 2025H1, 2026H1, change")
        for bn in w.index:
            print(f"    {bn:6s} {100 * w['n']['2025H1'][bn] / w['n']['2025H1'].sum():5.1f}% {100 * w['n']['2026H1'][bn] / w['n']['2026H1'].sum():5.1f}%   "
                  f"{w['v']['2025H1'][bn]:.2f} {w['v']['2026H1'][bn]:.2f} {100 * (w['v']['2026H1'][bn] / w['v']['2025H1'][bn] - 1):+.1f}%")
        # speed with the 2025 mix of origin-destination pairs held fixed (hours weighted)
        od = P_.groupby(["per", "pu", "do_"]).agg(n=("n", "sum"), miles=("miles", "sum"), hrs=("hrs", "sum")).reset_index()
        o = od.pivot(index=["pu", "do_"], columns="per", values=["n", "miles", "hrs"]).dropna()
        o = o[(o["n"]["2025H1"] >= 200) & (o["n"]["2026H1"] >= 200)]
        r = np.log((o["miles"]["2026H1"] / o["hrs"]["2026H1"]) / (o["miles"]["2025H1"] / o["hrs"]["2025H1"]))
        wgt = o["hrs"]["2025H1"]
        print(f"  within origin-destination zone pairs ({len(o)} pairs with 200 or more trips in both periods, "
              f"{100 * o['n']['2025H1'].sum() / tot.n['2025H1']:.0f}% of 2025 trips): speed change weighted by 2025 hours "
              f"{100 * (np.exp((r * wgt).sum() / wgt.sum()) - 1):+.1f}%; median pair {100 * (np.exp(r.median()) - 1):+.1f}%; "
              f"share of pairs slower {100 * (r < 0).mean():.0f}%")
        dm = np.log((o["miles"]["2026H1"] / o["n"]["2026H1"]) / (o["miles"]["2025H1"] / o["n"]["2025H1"]))
        tm = np.log((o["hrs"]["2026H1"] / o["n"]["2026H1"]) / (o["hrs"]["2025H1"] / o["n"]["2025H1"]))
        print(f"    within pairs: recorded miles per trip {100 * (np.exp((dm * wgt).sum() / wgt.sum()) - 1):+.1f}%, minutes per trip {100 * (np.exp((tm * wgt).sum() / wgt.sum()) - 1):+.1f}%")
        vg = P_.groupby(["per", "vendor"]).agg(n=("n", "sum"), miles=("miles", "sum"), hrs=("hrs", "sum"), wm=("n_whole_min", "sum"), tn=("n_tenth", "sum")).reset_index()
        print("  by vendor: period, vendor, share of trips, speed, miles per trip, minutes per trip, share of durations in whole minutes, share of distances in tenths")
        for _, x in vg.iterrows():
            print(f"    {x.per} vendor {int(x.vendor)}  {100 * x.n / tot.n[x.per]:5.1f}%  {x.miles / x.hrs:.2f} mph  {x.miles / x.n:.2f} mi  {60 * x.hrs / x.n:.1f} min  "
                  f"{100 * x.wm / x.n:.1f}%  {100 * x.tn / x.n:.1f}%")
        mv = T.groupby(["ym", "vendor"]).agg(n=("n", "sum"), miles=("miles", "sum"), hrs=("hrs", "sum")).reset_index()
        mv["v"] = mv.miles / mv.hrs
        pv = mv.pivot(index="ym", columns="vendor", values="v")
        pn = mv.pivot(index="ym", columns="vendor", values="n")
        print("  monthly speed by vendor (mph) and vendor share of trips:")
        for ym in pv.index:
            print("    " + ym + "  " + "  ".join(f"v{int(c)} {pv.loc[ym, c]:.2f} ({100 * pn.loc[ym, c] / pn.loc[ym].sum():.0f}%)" for c in pv.columns if pd.notna(pv.loc[ym, c])))
        # the same months for trips under 3 miles that neither start nor end in the zone, and records with missing fields
        f2 = [str(TLC / f"yellow_tripdata_{m}.parquet") for m in pd.period_range("2024-10", "2026-06", freq="M") if (TLC / f"yellow_tripdata_{m}.parquet").exists()]
        dur = "date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime)"
        inz, outz = f"PULocationID in ({cbd}) and DOLocationID in ({cbd})", f"PULocationID not in ({cbd}) and DOLocationID not in ({cbd}) and trip_distance < 3"
        q2 = f"""
          select strftime(tpep_pickup_datetime, '%Y-%m') as ym,
                 sum(case when {inz} then trip_distance end) / sum(case when {inz} then {dur} / 3600.0 end) as v_in,
                 sum(case when {outz} then trip_distance end) / sum(case when {outz} then {dur} / 3600.0 end) as v_out,
                 sum(case when {inz} and payment_type = 0 then 1 else 0 end) * 1.0 / sum(case when {inz} then 1 else 0 end) as share_missing,
                 sum(case when {inz} and payment_type = 0 then trip_distance end) / sum(case when {inz} and payment_type = 0 then {dur} / 3600.0 end) as v_in_missing,
                 sum(case when {inz} and payment_type <> 0 then trip_distance end) / sum(case when {inz} and payment_type <> 0 then {dur} / 3600.0 end) as v_in_complete
          from read_parquet({f2}, filename=true, union_by_name=true)
          where regexp_extract(filename, '(\\d{{4}}-\\d{{2}})', 1) = strftime(tpep_pickup_datetime, '%Y-%m')
            and dayofweek(tpep_pickup_datetime) between 1 and 5 and hour(tpep_pickup_datetime) between 5 and 20
            and trip_distance > 0 and trip_distance <= 50 and {dur} between 60 and 10800 and trip_distance / ({dur} / 3600.0) between 0.5 and 50
          group by 1 order by 1"""
        E = con.execute(q2).df().set_index("ym")
        print("  change on the same month a year earlier (all weekdays, holidays included): speed inside the zone; speed of trips under 3 miles")
        print("  wholly outside the zone; inside the zone for records with and without missing payment fields; share of such records")
        for ym in E.index:
            p = f"{int(ym[:4]) - 1}{ym[4:]}"
            if p in E.index:
                c = lambda k: 100 * (E[k][ym] / E[k][p] - 1)
                print(f"    {ym}  inside {c('v_in'):+5.1f}%  outside {c('v_out'):+5.1f}%  complete records {c('v_in_complete'):+5.1f}%  "
                      f"records with missing fields {c('v_in_missing'):+5.1f}%  share missing {100 * E.share_missing[p]:.0f}% -> {100 * E.share_missing[ym]:.0f}%")
    else:
        print("\n(taxi trip files not present on this machine; section 6b skipped)")

    if BUS.exists():
        section("6c. Bus speeds (MTA, monthly, weekdays), a series that does not come from taxis")
        B = pd.read_csv(BUS)
        B["ym"] = B.month.str[:7]
        B = B[(B.day_type == "Weekday") & B.hour_of_day.between(5, 20)]
        for rel in sorted(B.cbd_relation.unique()):
            x = B[B.cbd_relation == rel]
            def sp(lo, hi, x=x):
                y = x[(x.ym >= lo) & (x.ym <= hi)]
                return y.miles.sum() / y.hours.sum(), y.miles.sum()
            (a, am), (h, hm), (z, zm) = sp("2025-01", "2025-06"), sp("2026-01", "2026-06"), sp("2024-01", "2024-06")
            print(f"    {rel:10s} Jan-Jun speed 2024 {z:.2f}, 2025 {a:.2f}, 2026 {h:.2f} mph; 2025/2024 {100 * (a / z - 1):+.1f}%, 2026/2025 {100 * (h / a - 1):+.1f}%; "
                  f"bus miles 2026/2025 {100 * (hm / am - 1):+.1f}%")
            by = x.groupby("ym").agg(m=("miles", "sum"), h=("hours", "sum"))
            by["v"] = by.m / by.h
            print("      monthly change on a year earlier: " + ", ".join(
                f"{ym[2:]} {100 * (by.v[ym] / by.v[str(int(ym[:4]) - 1) + ym[4:]] - 1):+.1f}" for ym in by.index if ym >= "2025-07" and str(int(ym[:4]) - 1) + ym[4:] in by.index))

    section("7. Simulator checks (sim/, viz/simulate_model.js)")
    from sim import model, scenarios
    P = model.load()
    S = json.loads((DER / "scenarios.json").read_text())
    th = model.draw(P, S["draws"], S["seed"])
    print("  draws against the stated ranges (value, lo, hi in parameters.json; then the 2.5%, 50%, 97.5% points of the draws):")
    for k, p in P["parameters"].items():
        qs = np.quantile(th[k], [0.025, 0.5, 0.975])
        flag = "" if abs(qs[1] - p["value"]) < 0.03 * (p["hi"] - p["lo"]) else "   <- central value is not the median of the draws"
        print(f"    {k:17s} {p['dist']:8s} value {p['value']:+.3f} [{p['lo']:+.3f}, {p['hi']:+.3f}]   draws {qs[0]:+.3f} {qs[1]:+.3f} {qs[2]:+.3f}   "
              f"P(>0) {np.mean(th[k] > 0):.3f}{flag}")
    base = model.simulate(P, model.toll_now(P), th)
    cen = model.central(P)
    base_c = model.simulate(P, model.toll_now(P), cen)
    SC = scenarios.build(P)
    print("  scenarios.json against a fresh run with the current parameters.json (median speed %, median revenue); and central values:")
    keys = ["entries_pct", "speed_pct", "revenue_musd", "ambulance_s", "arrest_survivors", "retail_pct", "crashes_pct"]
    py_central = {}
    for name, s in SC.items():
        if name == "current":
            continue
        r = model.simulate(P, s["toll"], th)
        rc = model.simulate(P, s["toll"], cen)
        py_central[name] = {k: float(rc[k][0] - (base_c[k][0] if k == "revenue_musd" else 0)) for k in keys}
        st = S["scenarios"][name]["vs_current"]
        rev = r["revenue_musd"] - base["revenue_musd"]
        print(f"    {name:17s} stored speed {st['speed_pct']['median']:+.3f} fresh {np.median(r['speed_pct']):+.3f} | stored revenue {st['revenue_musd']['median']:+.2f} "
              f"fresh {np.median(rev):+.2f} ({np.quantile(rev, 0.025):+.2f} to {np.quantile(rev, 0.975):+.2f}) | central: speed {py_central[name]['speed_pct']:+.3f} "
              f"revenue {py_central[name]['revenue_musd']:+.3f} entries {py_central[name]['entries_pct']:+.3f} | P(speed up) {np.mean(r['speed_pct'] > 0):.3f}")
        if name.endswith("_rn"):
            wd = (r["revenue_musd"] - base["revenue_musd"]) / base["revenue_musd"]
            print(f"      revenue relative to current over draws: {100 * np.quantile(wd, 0.025):+.2f}% to {100 * np.quantile(wd, 0.975):+.2f}%; "
                  f"factor stored {S['scenarios'][name]['factor']:.4f}, fresh {s['factor']:.4f}")
    # is "a revenue-neutral differentiated schedule lowers entries" built into the functional form?
    rng = np.random.default_rng(7)
    cnt, tot_ = 0, 0
    for _ in range(200):
        t = model.toll_now(P).copy()
        t[:, 1:] = rng.uniform(4, 16, (5, 3))
        tn, f = scenarios.revenue_neutral(P, t)
        rr = model.simulate(P, tn, cen)
        if abs(rr["revenue_musd"][0] - base_c["revenue_musd"][0]) < 0.01:
            tot_ += 1
            cnt += rr["entries_pct"][0] < 0
    print(f"  random daytime toll tables scaled to current revenue at central values: {cnt} of {tot_} lower total entries")
    # sign of every output under a symmetric range for beta_speed
    P2 = json.loads(json.dumps(P))
    P2["parameters"]["beta_speed"].update(lo=-0.61, hi=0.61, value=0.0)
    th2 = model.draw(P2, S["draws"], S["seed"])
    r2 = model.simulate(P2, SC["uniform_12"]["toll"], th2)
    print(f"  uniform $12 with beta_speed uniform on -0.61 to +0.61: P(speed up) {np.mean(r2['speed_pct'] > 0):.2f}, "
          f"P(ambulance faster) {np.mean(r2['ambulance_s'] < 0):.2f}, P(survivors up) {np.mean(r2['arrest_survivors'] > 0):.2f}")
    r3 = model.simulate(P, SC["uniform_12"]["toll"], th)
    print(f"  uniform $12 as shipped: P(speed up) {np.mean(r3['speed_pct'] > 0):.3f}, P(ambulance faster) {np.mean(r3['ambulance_s'] < 0):.3f}, "
          f"P(survivors up) {np.mean(r3['arrest_survivors'] > 0):.3f}, P(retail down) {np.mean(r3['retail_pct'] < 0):.3f}")
    js = ROOT / "viz/simulate_model.js"
    pj = ROOT / "viz/data/simulate_params.js"
    if pj.exists():
        txt = pj.read_text()
        PJ = json.loads(txt[txt.index("window.SIM_PARAMS = ") + len("window.SIM_PARAMS = "):].rstrip().rstrip(";"))
        print("  viz/data/simulate_params.js equals parameters.json:", PJ == P)
        if PJ != P:
            for k in P["parameters"]:
                if PJ["parameters"].get(k) != P["parameters"][k]:
                    a_, b_ = PJ["parameters"].get(k, {}), P["parameters"][k]
                    print(f"    differs: {k}: browser value/lo/hi {a_.get('value')}/{a_.get('lo')}/{a_.get('hi')} {a_.get('dist')}; "
                          f"python {b_['value']}/{b_['lo']}/{b_['hi']} {b_['dist']}")
            for k in P:
                if k != "parameters" and PJ.get(k) != P[k]:
                    print("    differs: section", k)
    if shutil.which("node") and js.exists():
        tolls = {n: np.asarray(s["toll"]).tolist() for n, s in SC.items() if n != "current"}
        code = ("const M=require(process.argv[1]);const P=JSON.parse(process.argv[2]);const T=JSON.parse(process.argv[3]);"
                "const c=M.central(P);const b=M.simulate(P,M.tollNow(P),c);const o={};"
                "for(const k in T){const s=M.simulate(P,T[k],c);s.revenue_musd-=b.revenue_musd;delete s.byDay;o[k]=s;}"
                "const d=M.draw(P,10000,20261113);const u=M.compare(P,T['uniform_12'],d);delete u.byDay;o._mc=u;console.log(JSON.stringify(o));")
        out = subprocess.run(["node", "-e", code, str(js), json.dumps(P), json.dumps(tolls)], capture_output=True, text=True)
        if out.returncode == 0:
            J = json.loads(out.stdout)
            worst = max(abs(J[n][k] - py_central[n][k]) for n in py_central for k in keys)
            print(f"  browser model against Python at central values, 8 scenarios x 7 outputs: largest absolute difference {worst:.2e}")
            st = S["scenarios"]["uniform_12"]["vs_current"]
            print("  uniform $12, Monte Carlo intervals, browser generator against Python (median, lo, hi):")
            for k in keys:
                print(f"    {k:17s} browser {J['_mc'][k]['median']:+.3f} ({J['_mc'][k]['lo']:+.3f} to {J['_mc'][k]['hi']:+.3f})   python {st[k]['median']:+.3f} ({st[k]['lo']:+.3f} to {st[k]['hi']:+.3f})")
        else:
            print("  node failed:", out.stderr[:300])


if __name__ == "__main__":
    main()
