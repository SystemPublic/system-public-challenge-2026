"""heat-shootings: daily NYC shooting incidents and Central Park TMAX.

Registered plan: claims/registered/heat-shootings.json. Re-runs from a clean cache.
Outputs: data/derived/heat/shootings_daily.csv, shootings_results.json, shootings_curve.csv
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from analyses.heat.common import DER, holidays
from concord import noaa, socrata

END = "2026-08-31"


def daily_counts():
    rows, src = socrata.query_all("5ucz-vwe8", select="date_trunc_ymd(occur_date) as d, count(distinct incident_key) as n",
                                  group="d", order="d")
    s = pd.Series({pd.Timestamp(r["d"]): int(r["n"]) for r in rows}, name="n")
    rows_h, src_h = socrata.query_all("833y-fsy8", select="date_trunc_ymd(occur_date) as d, count(distinct incident_key) as n, "
                                      "sum(case(statistical_murder_flag=true, 1, true, 0)) as murders_victims",
                                      group="d", order="d")
    h = pd.DataFrame(rows_h)
    h["d"] = pd.to_datetime(h["d"])
    h = h.set_index("d").astype(int)
    return s, src, h, src_h


def murder_incidents():
    rows, src = socrata.query_all("833y-fsy8", select="date_trunc_ymd(occur_date) as d, count(distinct incident_key) as n",
                                  where="statistical_murder_flag=true", group="d", order="d")
    return pd.Series({pd.Timestamp(r["d"]): int(r["n"]) for r in rows}, name="murder_incidents"), src


def build():
    s, src, h, src_h = daily_counts()
    m, src_m = murder_incidents()
    w, src_w = noaa.daily("central_park")
    idx = pd.date_range("2006-01-01", END, freq="D")
    df = pd.DataFrame(index=idx)
    df["n"] = s.reindex(idx).fillna(0).astype(int)
    df["n_hist"] = h["n"].reindex(idx)
    df.loc[df.index <= "2024-12-31", "n_hist"] = df.loc[df.index <= "2024-12-31", "n_hist"].fillna(0)
    df["murder_inc"] = m.reindex(idx)
    df.loc[df.index <= "2024-12-31", "murder_inc"] = df.loc[df.index <= "2024-12-31", "murder_inc"].fillna(0)
    df = df.join(w[["TMAX", "TMIN", "PRCP"]])
    df["dow"] = df.index.day_of_week
    df["month"] = df.index.month
    df["year"] = df.index.year
    df["hol"] = df.index.isin(holidays("2006-01-01", END)).astype(int)
    df["wet"] = (df["PRCP"] >= 1.0).astype(int)
    df["t5"] = df["TMAX"] / 5.0
    df["tmin5"] = df["TMIN"] / 5.0
    df["t5_l01"] = (df["TMAX"] + df["TMAX"].shift(1)) / 2 / 5.0
    df.index.name = "date"
    return df, [src, src_h, src_m, src_w]


FORM = "n ~ {x} + C(dow) + C(month) + C(year) + hol + wet"


def nb_fit(formula, data):
    # estimate alpha by ML, then refit the GLM with that alpha and robust SE
    ml = smf.negativebinomial(formula, data).fit(disp=0, maxiter=200)
    alpha = float(ml.params["alpha"])
    res = smf.glm(formula, data, family=sm.families.NegativeBinomial(alpha=alpha)).fit(cov_type="HC0")
    return res, alpha


def irr(res, name):
    b, se = res.params[name], res.bse[name]
    return {"estimate": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * se)), "hi": float(np.exp(b + 1.96 * se)),
            "p": float(res.pvalues[name])}


def main():
    df, sources = build()
    d = df.dropna(subset=["TMAX"]).copy()
    out = {"n_days": int(len(d)), "n_incidents": int(d["n"].sum()), "period": [str(d.index.min().date()), str(d.index.max().date())]}
    chk = d.loc[:"2024-12-31"]
    out["check_vs_historic"] = {"sum_5ucz": int(chk["n"].sum()), "sum_833y": int(chk["n_hist"].sum()),
                                "days_differ": int((chk["n"] != chk["n_hist"]).sum())}
    res, alpha = nb_fit(FORM.format(x="t5"), d)
    out["primary"] = {**irr(res, "t5"), "alpha": alpha, "scale": "IRR per 5 C TMAX lag 0"}
    sens = {}
    r, _ = nb_fit(FORM.format(x="t5_l01"), d.dropna(subset=["t5_l01"]))
    sens["lag01"] = irr(r, "t5_l01")
    r, _ = nb_fit(FORM.format(x="tmin5"), d.dropna(subset=["tmin5"]))
    sens["tmin"] = irr(r, "tmin5")
    ws = d[d["month"].between(5, 9)]
    r, _ = nb_fit(FORM.format(x="t5"), ws)
    sens["warm_season"] = irr(r, "t5")
    r, _ = nb_fit(FORM.format(x="t5"), d.loc[:"2019-12-31"])
    sens["2006_2019"] = irr(r, "t5")
    r, _ = nb_fit(FORM.format(x="t5"), d.loc["2020-01-01":])
    sens["2020_on"] = irr(r, "t5")
    dm = d.loc[:"2024-12-31"].copy()
    dm["n"] = dm["murder_inc"]
    r, _ = nb_fit(FORM.format(x="t5"), dm)
    sens["murder_incidents_2006_2024"] = irr(r, "t5")
    # exploratory, not registered: weekday vs weekend split as in Reeping & Hemenway
    d["wkend"] = ((d["dow"] >= 5) | (d["hol"] == 1)).astype(int)
    r, _ = nb_fit("n ~ t5 + t5:wkend + C(dow) + C(month) + C(year) + hol + wet", d)
    b = r.params
    cov = r.cov_params()
    we_b = b["t5"] + b["t5:wkend"]
    we_se = float(np.sqrt(cov.loc["t5", "t5"] + cov.loc["t5:wkend", "t5:wkend"] + 2 * cov.loc["t5", "t5:wkend"]))
    sens["exploratory_weekday"] = irr(r, "t5")
    sens["exploratory_weekend_holiday"] = {"estimate": float(np.exp(we_b)), "lo": float(np.exp(we_b - 1.96 * we_se)),
                                           "hi": float(np.exp(we_b + 1.96 * we_se))}
    out["sensitivity"] = sens

    # spline curve, RR vs median TMAX
    med = float(d["TMAX"].median())
    p84 = float(d["TMAX"].quantile(0.84))
    p95 = float(d["TMAX"].quantile(0.95))
    knots_df = 4
    from patsy import build_design_matrices, dmatrix
    basis = dmatrix(f"cr(x, df={knots_df}, constraints='center') - 1", {"x": d["TMAX"].values})
    B = np.asarray(basis)
    scols = [f"s{i}" for i in range(B.shape[1])]
    for i, c in enumerate(scols):
        d[c] = B[:, i]
    rs, alpha_s = nb_fit("n ~ " + " + ".join(scols) + " + C(dow) + C(month) + C(year) + hol + wet", d)
    grid = np.arange(np.floor(d["TMAX"].quantile(0.005)), np.ceil(d["TMAX"].quantile(0.995)) + 0.5, 0.5)
    Xg = np.asarray(build_design_matrices([basis.design_info], {"x": grid})[0])
    Xr = np.asarray(build_design_matrices([basis.design_info], {"x": np.array([med])})[0])
    D = Xg - Xr
    bb = rs.params[scols].values
    V = rs.cov_params().loc[scols, scols].values
    eta = D @ bb
    se = np.sqrt(np.einsum("ij,jk,ik->i", D, V, D))
    curve = pd.DataFrame({"tmax_c": grid, "rr": np.exp(eta), "lo": np.exp(eta - 1.96 * se), "hi": np.exp(eta + 1.96 * se)})
    curve.to_csv(DER / "shootings_curve.csv", index=False)

    def rr_at(t):
        r_ = curve.iloc[(curve["tmax_c"] - t).abs().argmin()]
        return {"tmax_c": float(t), "rr": float(r_["rr"]), "lo": float(r_["lo"]), "hi": float(r_["hi"])}
    out["curve"] = {"median_tmax_c": med, "p84_tmax_c": p84, "p95_tmax_c": p95, "rr_p84": rr_at(p84), "rr_p95": rr_at(p95),
                    "rr_max": rr_at(float(curve.loc[curve["rr"].idxmax(), "tmax_c"])), "df": knots_df}
    # descriptive: mean count by TMAX bin
    d["bin"] = pd.cut(d["TMAX"], bins=np.arange(-15, 42, 3))
    desc = d.groupby("bin", observed=True)["n"].agg(["mean", "count"]).reset_index()
    desc["bin"] = desc["bin"].astype(str)
    desc.to_csv(DER / "shootings_by_tmax_bin.csv", index=False)
    out["sources"] = sources
    df.drop(columns=["bin"], errors="ignore").to_csv(DER / "shootings_daily.csv")
    (DER / "shootings_results.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "sources"}, indent=1, default=str))


if __name__ == "__main__":
    main()
