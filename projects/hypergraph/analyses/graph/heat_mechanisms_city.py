"""heat-mech-outdoors and heat-mech-intox: proxies for people outdoors and for intoxication
as steps between daily temperature and shootings.

Registered plans: claims/registered/heat-mech-outdoors.json, heat-mech-intox.json.
Re-runs from a clean cache. Outputs in data/derived/graph/heat_mechanisms/:
mediators_daily.csv, city_results.json, mediator_curves.csv, city_sources.json.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from patsy import build_design_matrices, dmatrix, dmatrices

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from analyses.heat import shootings as hs  # noqa: E402
from concord import socrata  # noqa: E402

OUT = ROOT / "data" / "derived" / "graph" / "heat_mechanisms"
END = "2026-08-31"
NBOOT = 500
CONTROLS = "C(dow) + C(month) + C(year) + hol + wet"
CONTROLS_YM = "C(dow) + C(ym) + hol + wet"
warnings.filterwarnings("ignore")


def fetch_311():
    out, srcs = {}, []
    for ds, a, b in (("76ig-c548", "2010-01-01", "2019-12-31"), ("erm2-nwe9", "2020-01-01", END)):
        rows, src = socrata.query_all(
            ds, select="date_trunc_ymd(created_date) as d, complaint_type, count(*) as n",
            where=f"complaint_type in ('Noise - Street/Sidewalk', 'Drinking') and created_date between '{a}T00:00:00' and '{b}T23:59:59'",
            group="d, complaint_type", order="d, complaint_type")
        srcs.append(src)
        for r in rows:
            out[(pd.Timestamp(r["d"]), r["complaint_type"])] = int(r["n"])
    s = pd.Series(out).unstack().fillna(0)
    return s.rename(columns={"Noise - Street/Sidewalk": "noise_street", "Drinking": "drinking311"}), srcs


def fetch_ems():
    rows, src = socrata.query_all(
        "76xm-jjuj", select="date_trunc_ymd(incident_datetime) as d, initial_call_type, count(*) as n",
        where=f"incident_datetime between '2006-01-01' and '{END}T23:59:59' and initial_call_type in ('DRUG', 'DRUGFC', 'EDP', 'EDPC', 'EDPM')",
        group="d, initial_call_type", order="d, initial_call_type")
    s = pd.Series({(pd.Timestamp(r["d"]), r["initial_call_type"]): int(r["n"]) for r in rows}).unstack().fillna(0)
    df = pd.DataFrame({"ems_drug": s.get("DRUG", 0) + s.get("DRUGFC", 0),
                       "ems_edp": s.get("EDP", 0) + s.get("EDPC", 0) + s.get("EDPM", 0)})
    return df, [src]


def fetch_bike():
    """Daily bicycle counts per sensor, one query per year; panel = sensors reporting on >= 90% of the year's analysed days."""
    frames, srcs = [], []
    for y in range(2014, 2027):
        b = END if y == 2026 else f"{y}-12-31"
        rows, src = socrata.query_all(
            "ct66-47at", select="date_trunc_ymd(timestamp) as d, sensor_id, sum(counts) as c, count(*) as k",
            where=f"travelmode = 'bike' and timestamp between '{y}-01-01T00:00:00' and '{b}T23:59:59'",
            group="d, sensor_id", order="d, sensor_id")
        srcs.append(src)
        f = pd.DataFrame(rows)
        if len(f):
            f["d"] = pd.to_datetime(f["d"])
            f["c"] = pd.to_numeric(f["c"], errors="coerce")
            f["k"] = pd.to_numeric(f["k"])
            frames.append(f)
    a = pd.concat(frames)
    a = a[a["k"] >= 90]  # a sensor-day needs at least 90 of 96 quarter-hours
    a["year"] = a["d"].dt.year
    daily, panel = {}, {}
    for y, g in a.groupby("year"):
        ndays = (pd.Timestamp(END if y == 2026 else f"{y}-12-31") - pd.Timestamp(f"{y}-01-01")).days + 1
        cnt = g.groupby("sensor_id")["d"].nunique()
        keep = cnt[cnt >= 0.9 * ndays].index
        panel[int(y)] = len(keep)
        w = g[g["sensor_id"].isin(keep)].pivot_table(index="d", columns="sensor_id", values="c")
        w = w.dropna()  # days on which every panel sensor reported
        daily.update(w.sum(axis=1).to_dict())
    return pd.Series(daily, name="bike").sort_index(), srcs, panel


def nb_alpha(formula, data):
    ml = smf.negativebinomial(formula, data).fit(disp=0, maxiter=300)
    return float(ml.params["alpha"])


def glm(y, X, alpha):
    return sm.GLM(y, X, family=sm.families.NegativeBinomial(alpha=alpha)).fit(cov_type="HC0")


def ci(res, name, exp=True):
    b, se = res.params[name], res.bse[name]
    f = np.exp if exp else (lambda v: v)
    return {"estimate": float(f(b)), "lo": float(f(b - 1.96 * se)), "hi": float(f(b + 1.96 * se))}


def attenuation(d, med, controls=CONTROLS, boot=0, seed=1, lag=False):
    d = d.copy()
    d["lm"] = np.log1p(d[med].shift(1) if lag else d[med])
    d = d.dropna(subset=["lm", "t5", "n"])
    y, X0 = dmatrices(f"n ~ t5 + {controls}", d, return_type="dataframe")
    X1 = X0.copy()
    X1["lm"] = d["lm"].values
    y = y.iloc[:, 0]
    try:
        a0 = nb_alpha(f"n ~ t5 + {controls}", d)
    except Exception:
        a0 = None
    if a0 is None or not np.isfinite(a0) or a0 <= 0:
        a0 = 0.05
    r0, r1 = glm(y, X0, a0), glm(y, X1, a0)
    b0, b1 = r0.params["t5"], r1.params["t5"]
    out = {"n_days": int(len(d)), "period": [str(d.index.min().date()), str(d.index.max().date())], "alpha": a0,
           "base_irr_per_5C": ci(r0, "t5"), "adjusted_irr_per_5C": ci(r1, "t5"),
           "mediator_coef_log1p": ci(r1, "lm", exp=False), "attenuation": float(1 - b1 / b0)}
    if boot:
        rng = np.random.default_rng(seed)
        wk = ((d.index - pd.Timestamp("2006-01-02")).days // 7).values
        groups = {}
        for i, w in enumerate(wk):
            groups.setdefault(w, []).append(i)
        keys = list(groups)
        y_, X0_, X1_ = y.values, X0.values, X1.values
        j = list(X0.columns).index("t5")
        A = []
        for _ in range(boot):
            idx = np.concatenate([groups[k] for k in rng.choice(keys, len(keys))])
            try:
                fam = sm.families.NegativeBinomial(alpha=a0)
                p0 = sm.GLM(y_[idx], X0_[idx], family=fam).fit().params[j]
                p1 = sm.GLM(y_[idx], X1_[idx], family=fam).fit().params[j]
                A.append(1 - p1 / p0)
            except Exception:
                continue
        out["attenuation_lo"], out["attenuation_hi"] = float(np.percentile(A, 2.5)), float(np.percentile(A, 97.5))
        out["boot_ok"] = len(A)
    return out


def first_link(d, med):
    d = d.dropna(subset=[med, "t5"]).copy()
    d["m"] = d[med].round().astype(int)
    f = f"m ~ t5 + {CONTROLS}"
    a = nb_alpha(f, d)
    y, X = dmatrices(f, d, return_type="dataframe")
    r = glm(y.iloc[:, 0], X, a)
    out = {"irr_per_5C": ci(r, "t5"), "alpha": a, "n_days": int(len(d)), "mean_per_day": float(d["m"].mean())}
    # spline, RR against 15 C
    basis = dmatrix("cr(x, df=4, constraints='center') - 1", {"x": d["TMAX"].values})
    B = np.asarray(basis)
    yc, Xc = dmatrices(f"m ~ {CONTROLS}", d, return_type="dataframe")
    for i in range(B.shape[1]):
        Xc[f"s{i}"] = B[:, i]
    sc = [f"s{i}" for i in range(B.shape[1])]
    rs = glm(yc.iloc[:, 0], Xc, a)
    grid = np.arange(-5, 36.5, 1.0)
    Xg = np.asarray(build_design_matrices([basis.design_info], {"x": grid})[0])
    Xr = np.asarray(build_design_matrices([basis.design_info], {"x": np.array([15.0])})[0])
    D = Xg - Xr
    bb, V = rs.params[sc].values, rs.cov_params().loc[sc, sc].values
    eta, se = D @ bb, np.sqrt(np.einsum("ij,jk,ik->i", D, V, D))
    curve = pd.DataFrame({"series": med, "tmax_c": grid, "rr": np.exp(eta), "lo": np.exp(eta - 1.96 * se), "hi": np.exp(eta + 1.96 * se)})

    def contrast(t1, t0):
        x = (np.asarray(build_design_matrices([basis.design_info], {"x": np.array([float(t1)])})[0])
             - np.asarray(build_design_matrices([basis.design_info], {"x": np.array([float(t0)])})[0]))[0]
        e, s = float(x @ bb), float(np.sqrt(x @ V @ x))
        return {"estimate": float(np.exp(e)), "lo": float(np.exp(e - 1.96 * s)), "hi": float(np.exp(e + 1.96 * s))}
    out["rr_21_vs_15"], out["rr_33_vs_27"] = contrast(21, 15), contrast(33, 27)
    return out, curve


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df, src0 = hs.build()
    c311, s311 = fetch_311()
    ems, sems = fetch_ems()
    df = df.join(c311).join(ems)
    df.loc["2010-01-01":, ["noise_street", "drinking311"]] = df.loc["2010-01-01":, ["noise_street", "drinking311"]].fillna(0)
    df[["ems_drug", "ems_edp"]] = df[["ems_drug", "ems_edp"]].fillna(0)
    sources = {"shootings_weather": src0, "c311": s311, "ems": sems}
    panel = None
    try:
        bike, sb, panel = fetch_bike()
        df = df.join(bike)
        sources["bike"] = sb
    except Exception as e:  # the registered plan allows this to be reported as not done
        df["bike"] = np.nan
        sources["bike_error"] = str(e)[:300]
    df["ym"] = df["year"].astype(str) + "-" + df["month"].astype(str)
    df = df.dropna(subset=["TMAX"])
    df.to_csv(OUT / "mediators_daily.csv")
    (OUT / "city_sources.json").write_text(json.dumps(sources, indent=1, default=str))

    res, curves = {"bike_panel_sensors_by_year": panel}, []
    # the shootings series through the same spline code, for the shape comparison
    dd = df.rename(columns={"n": "shootings"})
    fl, cv = first_link(dd, "shootings")
    res["shootings_curve"] = fl
    curves.append(cv)
    for med in ("noise_street", "bike", "ems_drug", "ems_edp", "drinking311"):
        d = df.dropna(subset=[med])
        if len(d) < 500:
            res[med] = {"not_done": "series unavailable"}
            continue
        fl, cv = first_link(d, med)
        curves.append(cv)
        r = {"first_link": fl, "primary": attenuation(d, med, boot=NBOOT)}
        r["s1_year_by_month"] = attenuation(d, med, controls=CONTROLS_YM, boot=NBOOT)
        r["s2_excl_2020_2021"] = attenuation(d[~d["year"].isin([2020, 2021])], med)
        r["s3_warm_season"] = attenuation(d[d["month"].between(5, 9)], med)
        r["s4_mediator_lag1"] = attenuation(d, med, lag=True)
        res[med] = r
        print(med, json.dumps({"irr": fl["irr_per_5C"], "A": r["primary"]["attenuation"], "lo": r["primary"]["attenuation_lo"],
                               "hi": r["primary"]["attenuation_hi"], "A_ym": r["s1_year_by_month"]["attenuation"]}), flush=True)
        (OUT / "city_results.json").write_text(json.dumps(res, indent=1))
    pd.concat(curves).to_csv(OUT / "mediator_curves.csv", index=False)
    (OUT / "city_results.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
