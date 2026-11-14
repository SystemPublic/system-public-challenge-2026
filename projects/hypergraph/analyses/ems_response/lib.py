"""Estimators for the registered EMS tests (written before registration; see the registrations
ems-traffic-hourly-elasticity, ems-traffic-share-2019-2026 and ems-taxi-2026-onset).

Loading
  ems_hourly()   date x hour x area (crz, north) x sev EMS sums: 2017-2018 from this folder
                 (analyses.ems_response.ems_fetch hourly), 2019-2026 from
                 data/derived/congestion/ems_YYYY.csv (analyses.congestion.ems_fetch, same query
                 over all areas; only crz and north rows are used).
  taxi_hourly()  date x hour x area taxi sums from taxi_hourly_*.csv in this folder.
Panel: cells (date, hour, area) with area crz<->taxi cbd and north<->taxi north. EMS mean
travel time y = log(sum travel / n); taxi pace x = log(hours / miles). Cells need at least
2 EMS incidents and 20 taxi trips. x_lead = x of the same area and hour 7 days later.

T1 (fe_elasticity): weighted (EMS n) OLS of y on x, x_lead (joint), or each alone, with
controls log n_cell and log n_manhattan_hour, after absorbing date x area and
area x year x weekday x hour fixed effects by alternating projections. Standard errors
clustered by ISO week (Monday start). 95% intervals are estimate +- 1.96 se.
T2 (traffic_share): see function.
T3 (onset): see function.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from analyses.ems_response.common import DER, ROOT

CONG = ROOT / "data" / "derived" / "congestion"
EXCLUDE = ("2020-03-01", "2021-06-30")


def ems_hourly(years) -> pd.DataFrame:
    parts = []
    for y in years:
        f = DER / f"ems_hourly_{y}.csv"
        if not f.exists():
            f = CONG / f"ems_{y}.csv"
        parts.append(pd.read_csv(f))
    d = pd.concat(parts)
    d = d[d.area.isin(["crz", "north"])].copy()
    d["d"] = pd.to_datetime(d["d"].str[:10])
    return d


def taxi_hourly() -> pd.DataFrame:
    """Own files first (taxi_hourly_*.csv and taxi_parts/), then the cbd and north rows of
    data/derived/congestion/taxi_speed_*.csv (July 2023 to June 2026, same areas and filter f1,
    from repro-mmr-cbd-speed's files) for months not computed here. (Added after registration
    because the TLC file host refused further downloads on 13 November; same definitions.)"""
    own = sorted(DER.glob("taxi_hourly_*.csv")) + sorted((DER / "taxi_parts").glob("*.csv"))
    t = pd.concat([pd.read_csv(f) for f in own] + [pd.read_csv(f) for f in sorted(CONG.glob("taxi_speed_*.csv"))])
    t["d"] = pd.to_datetime(t["d"])
    return t.drop_duplicates(["d", "hh", "area"]).reset_index(drop=True)


def panel(years, sev=None, min_ems=2, min_taxi=20) -> pd.DataFrame:
    e = ems_hourly(years)
    tot = e.groupby(["d", "hh"]).n.sum().rename("n_mh").reset_index()
    if sev:
        e = e[e.sev == sev]
    e = e.groupby(["d", "hh", "area"])[["n", "travel"]].sum().reset_index()
    e = e.merge(tot, on=["d", "hh"])
    t = taxi_hourly()
    t = t[t.area.isin(["cbd", "north"])].copy()
    t["area"] = t.area.replace({"cbd": "crz"})
    t = t[t.n >= min_taxi]
    t["x"] = np.log(t.hrs / t.miles)
    lead = t[["d", "hh", "area", "x"]].copy()
    lead["d"] = lead.d - pd.Timedelta(days=7)
    t = t.merge(lead.rename(columns={"x": "x_lead"}), on=["d", "hh", "area"], how="left")
    p = e.merge(t[["d", "hh", "area", "x", "x_lead", "n"]].rename(columns={"n": "n_taxi"}),
                on=["d", "hh", "area"])
    p = p[(p.n >= min_ems) & (p.travel > 0)].copy()
    p = p[~((p.d >= EXCLUDE[0]) & (p.d <= EXCLUDE[1]))]
    p["y"] = np.log(p.travel / p.n)
    p["ln_n"] = np.log(p.n)
    p["ln_nmh"] = np.log(p.n_mh)
    p["fe1"] = p.d.dt.strftime("%Y-%m-%d") + p.area
    p["fe2"] = p.area + p.d.dt.year.astype(str) + p.d.dt.dayofweek.astype(str) + p.hh.astype(str)
    p["week"] = (p.d - pd.to_timedelta(p.d.dt.dayofweek, unit="D")).dt.strftime("%Y-%m-%d")
    return p


def demean(df, cols, fes, w, tol=1e-9, it=500):
    X = df[cols].to_numpy(float).copy()
    codes = [pd.factorize(df[f])[0] for f in fes]
    for _ in range(it):
        old = X.copy()
        for c in codes:
            sw = np.bincount(c, weights=w)
            for j in range(X.shape[1]):
                m = np.bincount(c, weights=w * X[:, j]) / sw
                X[:, j] -= m[c]
        if np.max(np.abs(X - old)) < tol:
            break
    return X


def wls_cluster(y, X, w, cl):
    sw = np.sqrt(w)
    Xw, yw = X * sw[:, None], y * sw
    XtX_inv = np.linalg.inv(Xw.T @ Xw)
    b = XtX_inv @ Xw.T @ yw
    u = yw - Xw @ b
    g = pd.factorize(cl)[0]
    S = np.zeros((X.shape[1], X.shape[1]))
    for k in range(g.max() + 1):
        idx = g == k
        s = Xw[idx].T @ u[idx]
        S += np.outer(s, s)
    G = g.max() + 1
    n, k = X.shape
    V = XtX_inv @ S @ XtX_inv * G / (G - 1) * (n - 1) / (n - k)
    return b, np.sqrt(np.diag(V))


def fe_elasticity(p, regs, controls=("ln_n", "ln_nmh")) -> dict:
    q = p.dropna(subset=["x", "x_lead"]).copy()
    cols = ["y", *regs, *controls]
    Z = demean(q, cols, ["fe1", "fe2"], q.n.to_numpy(float))
    b, se = wls_cluster(Z[:, 0], Z[:, 1:], q.n.to_numpy(float), q.week.to_numpy())
    out = {"n_cells": int(len(q)), "n_incidents": int(q.n.sum()), "n_weeks": int(q.week.nunique())}
    for i, r in enumerate([*regs, *controls]):
        out[r] = {"est": float(b[i]), "se": float(se[i]), "lo": float(b[i] - 1.96 * se[i]),
                  "hi": float(b[i] + 1.96 * se[i])}
    return out


def t1(years, sev=None) -> dict:
    p = panel(years, sev)
    res = {"joint": fe_elasticity(p, ["x", "x_lead"]), "x_only": fe_elasticity(p, ["x"]),
           "lead_only": fe_elasticity(p, ["x_lead"])}
    # difference beta_x - beta_lead in the joint model, se from a refit on (x - x_lead, x_lead)
    p2 = p.copy()
    p2["xd"] = p2.x
    p2["s"] = p2.x + p2.x_lead
    j = fe_elasticity(p2, ["xd", "s"])  # y = a xd + c s => b_x = a + c, b_lead = c; diff = a
    res["diff_x_minus_lead"] = j["xd"]
    return res


def traffic_share(beta: float, beta_se: float, base=("2019-01-01", "2019-09-30"),
                  post=("2026-01-01", "2026-09-30"), sev="hi", draws=20000, seed=20261113) -> dict:
    """T2. Manhattan (crz + north), life-threatening (sev hi), all hours, January-September.
    D = log mean EMS travel (post) - log mean EMS travel (base).
    Traffic term = beta * sum_{area,hour} w_post * [log pace_taxi(post) - log pace_taxi(base)],
    with w_post the post-period share of EMS incidents in each area-hour cell and taxi pace the
    period's total hours / total miles in that cell. Share S = traffic term / D. Interval: beta
    drawn normal(beta, beta_se) and a day-block bootstrap (resampling dates within each period)
    for D and the pace changes; 'draws' draws with 'seed'. S at beta = 1 is reported as S1."""
    yrs = sorted({int(base[0][:4]), int(post[0][:4])})
    e = ems_hourly(yrs)
    e = e[e.sev == sev]
    t = taxi_hourly()
    t = t[t.area.isin(["cbd", "north"])].copy()
    t["area"] = t.area.replace({"cbd": "crz"})

    def per(a, b):
        ee = e[(e.d >= a) & (e.d <= b)]
        tt = t[(t.d >= a) & (t.d <= b)]
        return ee, tt

    eb, tb = per(*base)
    ep, tp = per(*post)
    rng = np.random.default_rng(seed)

    def stats(eb, tb, ep, tp):
        D = np.log(ep.travel.sum() / ep.n.sum()) - np.log(eb.travel.sum() / eb.n.sum())
        w = ep.groupby(["area", "hh"]).n.sum()
        w = w / w.sum()
        pb = tb.groupby(["area", "hh"])[["hrs", "miles"]].sum()
        pp = tp.groupby(["area", "hh"])[["hrs", "miles"]].sum()
        dp = np.log(pp.hrs / pp.miles) - np.log(pb.hrs / pb.miles)
        return D, float((w * dp.reindex(w.index)).sum())

    D0, P0 = stats(eb, tb, ep, tp)
    # day-block bootstrap
    def boot(ee, tt):
        days = ee.d.unique()
        pick = rng.choice(days, len(days))
        ce = pd.Series(pick).value_counts()
        e2 = ee.merge(ce.rename("k"), left_on="d", right_index=True)
        t2 = tt.merge(ce.rename("k"), left_on="d", right_index=True)
        for c in ("n", "travel"):
            e2[c] = e2[c] * e2.k
        for c in ("hrs", "miles"):
            t2[c] = t2[c] * t2.k
        return e2, t2
    nb = 400
    Ds, Ps = [], []
    for _ in range(nb):
        a1, b1 = boot(eb, tb)
        a2, b2 = boot(ep, tp)
        d_, p_ = stats(a1, b1, a2, b2)
        Ds.append(d_); Ps.append(p_)
    Ds, Ps = np.array(Ds), np.array(Ps)
    idx = rng.integers(0, nb, draws)
    bet = rng.normal(beta, beta_se, draws)
    S = bet * Ps[idx] / Ds[idx]
    S1 = Ps / Ds
    q = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
    return {"D_log": float(D0), "D_pct": float(100 * np.expm1(D0)), "D_ci": q(Ds),
            "pace_change_log": float(P0), "pace_change_pct": float(100 * np.expm1(P0)), "pace_ci": q(Ps),
            "beta": beta, "beta_se": beta_se,
            "S": float(beta * P0 / D0), "S_ci": q(S), "S1": float(P0 / D0), "S1_ci": q(S1),
            "bootstrap_days_draws": nb, "draws": draws, "seed": seed, "base": base, "post": post, "sev": sev}


def weekly(years, sev=None):
    e = ems_hourly(years)
    if sev:
        e = e[e.sev == sev]
    t = taxi_hourly()
    t = t[t.area.isin(["cbd", "north"])]
    iso = lambda d: d.dt.isocalendar()
    ew = e.assign(yr=iso(e.d).year, wk=iso(e.d).week).groupby(["yr", "wk"])[["n", "travel"]].sum()
    tw = t.assign(yr=iso(t.d).year, wk=iso(t.d).week).groupby(["yr", "wk"])[["hrs", "miles"]].sum()
    w = pd.DataFrame({"e": np.log(ew.travel / ew.n), "p": np.log(tw.hrs / tw.miles)}).dropna()
    w = w[(w.index.get_level_values("wk") <= 52)]
    prev = w.copy()
    prev.index = pd.MultiIndex.from_arrays([prev.index.get_level_values(0) + 1, prev.index.get_level_values(1)],
                                           names=["yr", "wk"])
    yoy = (w - prev).dropna()
    return w, yoy


def hac_ols(y, X, lags=4):
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    u = y - X @ b
    S = (X * u[:, None]).T @ (X * u[:, None])
    for L in range(1, lags + 1):
        wgt = 1 - L / (lags + 1)
        G = (X[L:] * u[L:, None]).T @ (X[:-L] * u[:-L, None])
        S += wgt * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    return b, np.sqrt(np.diag(V))


def onset(yoy: pd.DataFrame, start=(2025, 27), split=(2026, 1), end=(2026, 39), lags=4) -> dict:
    """T3. yoy = weekly log change against the same ISO week a year earlier (Manhattan crz + north,
    all hours, all severities). Window start..end. Model e_w = a + b p_w + c post_w (post = weeks
    from 'split'), HAC 'lags'. b: does EMS travel track taxi pace week to week? c: the 2026 step in
    EMS travel not accounted for by taxi pace. Also the raw steps in e and p (post mean - pre mean)."""
    idx = yoy.index.to_frame(index=False)
    key = idx.yr * 100 + idx.wk
    m = ((key >= start[0] * 100 + start[1]) & (key <= end[0] * 100 + end[1])).to_numpy()
    s = yoy[m]
    post = ((s.index.get_level_values(0) * 100 + s.index.get_level_values(1)) >= split[0] * 100 + split[1]).astype(float)
    X = np.column_stack([np.ones(len(s)), s.p.to_numpy(), post])
    b, se = hac_ols(s.e.to_numpy(), X, lags)
    out = {"n_weeks": int(len(s)),
           "b": {"est": float(b[1]), "se": float(se[1]), "lo": float(b[1] - 1.96 * se[1]), "hi": float(b[1] + 1.96 * se[1])},
           "c": {"est": float(b[2]), "se": float(se[2]), "lo": float(b[2] - 1.96 * se[2]), "hi": float(b[2] + 1.96 * se[2])},
           "step_e": float(s.e[post == 1].mean() - s.e[post == 0].mean()),
           "step_p": float(s.p[post == 1].mean() - s.p[post == 0].mean())}
    X2 = np.column_stack([np.ones(len(s)), s.p.to_numpy()])
    b2, se2 = hac_ols(s.e.to_numpy(), X2, lags)
    out["b_alone"] = {"est": float(b2[1]), "se": float(se2[1]), "lo": float(b2[1] - 1.96 * se2[1]),
                      "hi": float(b2[1] + 1.96 * se2[1])}
    return out
