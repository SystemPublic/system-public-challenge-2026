"""heat-ed-syndromic: daily heat-syndrome ED visits (DOHMH syndromic surveillance) and Central Park TMAX.

Registered plan: claims/registered/heat-ed-syndromic.json.
Data: github.com/nychealth/EHDP-data, branch production, key-topics/heat-syndrome, pinned to a commit SHA.
Outputs: data/derived/heat/ed_daily.csv, ed_results.json, ed_curve.csv, ed_yearly.csv
"""
from __future__ import annotations

import io
import json
import time

import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
import statsmodels.formula.api as smf

from analyses.heat.common import DER, holidays
from concord import noaa

SHA = "547482b9df589006543e13e8cdf6546e00ed9998"  # production head on 2026-10-24
RAW = f"https://raw.githubusercontent.com/nychealth/EHDP-data/{SHA}/"
CACHE = DER / "ehdp"
FILES = ["key-topics/heat-syndrome/previous_years.csv", "key-topics/heat-syndrome/edheat1720_supp.csv"] + \
        [f"key-topics/heat-syndrome/edheat{y}_live.csv" for y in range(2021, 2027)]


def fetch(path: str) -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / path.replace("/", "__")
    if not f.exists():
        r = requests.get(RAW + path, timeout=60)
        r.raise_for_status()
        f.write_bytes(r.content)
    return pd.read_csv(f)


def source(path):
    return {"kind": "github", "repo": "nychealth/EHDP-data", "commit": SHA, "path": path, "url": RAW + path,
            "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z")}


def load():
    parts = []
    prev = fetch(FILES[0])
    prev["date"] = pd.to_datetime(prev["END_DATE"])
    prev["src"] = "previous_years"
    parts.append(prev)
    for p in FILES[2:]:
        x = fetch(p)
        x["date"] = pd.to_datetime(x["END_DATE"])
        x["src"] = p.split("/")[-1]
        parts.append(x)
    df = pd.concat(parts)[["date", "HEAT_ED_VISIT_COUNT", "MAX_DAILY_TEMP", "src"]]
    df = df.sort_values(["date", "src"]).drop_duplicates("date", keep="last").set_index("date")
    supp = fetch(FILES[1])
    supp["date"] = pd.to_datetime(supp["END_DATE"], format="%m/%d/%Y")
    supp = supp.set_index("date")
    return df, supp


def nb_fit(formula, data):
    ml = smf.negativebinomial(formula, data).fit(disp=0, maxiter=300)
    alpha = float(ml.params["alpha"])
    return smf.glm(formula, data, family=sm.families.NegativeBinomial(alpha=alpha)).fit(cov_type="HC0"), alpha


def irr(res, name):
    b, se = res.params[name], res.bse[name]
    return {"estimate": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * se)), "hi": float(np.exp(b + 1.96 * se)),
            "p": float(res.pvalues[name])}


def main():
    ed, supp = load()
    w, src_w = noaa.daily("central_park")
    d = ed.join(w[["TMAX", "TMIN", "PRCP"]], how="left")
    d = d[d.index.month.isin([5, 6, 7, 8, 9])].dropna(subset=["TMAX", "HEAT_ED_VISIT_COUNT"]).copy()
    d["n"] = d["HEAT_ED_VISIT_COUNT"].astype(int)
    d["dow"] = d.index.day_of_week
    d["month"] = d.index.month
    d["year"] = d.index.year
    d["hol"] = d.index.isin(holidays(str(d.index.min().date()), str(d.index.max().date()))).astype(int)
    d["t5"] = d["TMAX"] / 5.0
    out = {"n_days": int(len(d)), "n_visits": int(d["n"].sum()), "period": [str(d.index.min().date()), str(d.index.max().date())],
           "years": sorted(map(int, d["year"].unique()))}
    # cross-checks
    j = d.join(supp[["HEAT_ED_VISIT_COUNT"]].rename(columns={"HEAT_ED_VISIT_COUNT": "supp"}), how="inner")
    out["check_previous_vs_supp_2017_2020"] = {"days": int(len(j)), "sum_previous": int(j["n"].sum()), "sum_supp": int(j["supp"].sum()),
                                               "corr": float(j[["n", "supp"]].corr().iloc[0, 1])}
    lga_c = (d["MAX_DAILY_TEMP"] - 32) * 5 / 9
    out["check_tmax_cp_vs_lga_heat_index"] = {"corr": float(np.corrcoef(lga_c, d["TMAX"])[0, 1]),
                                              "mean_diff_c": float((lga_c - d["TMAX"]).mean())}
    form = "n ~ t5 + C(dow) + C(month) + C(year) + hol"
    res, alpha = nb_fit(form, d)
    out["primary"] = {**irr(res, "t5"), "alpha": alpha, "scale": "IRR per 5 C TMAX lag 0, May-September"}
    # spline curve vs warm-season median
    from patsy import build_design_matrices, dmatrix
    med = float(d["TMAX"].median())
    p95 = float(d["TMAX"].quantile(0.95))
    basis = dmatrix("cr(x, df=4, constraints='center') - 1", {"x": d["TMAX"].values})
    B = np.asarray(basis)
    sc = [f"s{i}" for i in range(B.shape[1])]
    for i, c in enumerate(sc):
        d[c] = B[:, i]
    rs, _ = nb_fit("n ~ " + " + ".join(sc) + " + C(dow) + C(month) + C(year) + hol", d)
    grid = np.arange(np.floor(d["TMAX"].quantile(0.005)), np.ceil(d["TMAX"].quantile(0.995)) + 0.5, 0.5)
    D = np.asarray(build_design_matrices([basis.design_info], {"x": grid})[0]) - \
        np.asarray(build_design_matrices([basis.design_info], {"x": np.array([med])})[0])
    bb = rs.params[sc].values
    V = rs.cov_params().loc[sc, sc].values
    eta = D @ bb
    se = np.sqrt(np.einsum("ij,jk,ik->i", D, V, D))
    curve = pd.DataFrame({"tmax_c": grid, "rr": np.exp(eta), "lo": np.exp(eta - 1.96 * se), "hi": np.exp(eta + 1.96 * se)})
    curve.to_csv(DER / "ed_curve.csv", index=False)
    r95 = curve.iloc[(curve["tmax_c"] - p95).abs().argmin()]
    out["curve"] = {"median_tmax_c": med, "p95_tmax_c": p95, "rr_p95": {k: float(r95[k]) for k in ("rr", "lo", "hi")}}
    # piecewise: slope below and above 27 C (descriptive check of the registered shape)
    d["below"] = np.minimum(d["TMAX"], 27) / 5
    d["above"] = np.maximum(d["TMAX"] - 27, 0) / 5
    rp, _ = nb_fit("n ~ below + above + C(dow) + C(month) + C(year) + hol", d)
    out["piecewise_27c"] = {"below": irr(rp, "below"), "above_extra": irr(rp, "above")}
    bins = pd.cut(d["TMAX"], bins=np.arange(9, 42, 3))
    tab = d.groupby(bins, observed=True)["n"].agg(["mean", "count"]).reset_index()
    tab["TMAX"] = tab["TMAX"].astype(str)
    tab.to_csv(DER / "ed_by_tmax_bin.csv", index=False)
    # yearly, citywide: visits vs days >= 32.2 C (90 F), from the same daily file (descriptive)
    w_ws = w[w.index.month.isin([5, 6, 7, 8, 9])]
    hot = (w_ws["TMAX"] >= 32.2).groupby(w_ws.index.year).sum().rename("days_90f")
    yearly = d.groupby("year")["n"].sum().rename("syndromic_visits").to_frame().join(hot)
    from scipy.stats import spearmanr
    rho = spearmanr(yearly["syndromic_visits"], yearly["days_90f"])
    out["yearly"] = {"spearman_rho": float(rho.statistic), "p": float(rho.pvalue), "n_years": int(len(yearly))}
    yearly.to_csv(DER / "ed_yearly.csv")
    out["sources"] = [source(p) for p in FILES] + [src_w]
    d.drop(columns=sc + ["below", "above"]).to_csv(DER / "ed_daily.csv")
    (DER / "ed_results.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "sources"}, indent=1, default=str))
    print(tab.to_string())
    print(yearly.to_string())


if __name__ == "__main__":
    main()
