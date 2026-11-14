"""nbhd-noise311-exposure: do 311 noise complaints by tract track modelled noise or neighbourhood change?

Needs base.py, noise_map.py and fetch311.py outputs. Writes noise311_tracts.csv and noise311_results.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from analyses.neighbourhood.geo import points_to_tracts  # noqa: E402

OUT = ROOT / "data" / "derived" / "neighbourhood"
SLA = "https://data.ny.gov/resource/9s3h-dpkz.json"
ON_PREMISES = ["Restaurant", "Food & Beverage Business", "Club", "Cabaret", "Night Club", "Bottle Club",
               "Restaurant Brewer", "Hotel", "For-profit Club"]
NYC_COUNTIES = ["New York", "Kings", "Queens", "Bronx", "Richmond"]


def liquor():
    f = OUT / "liquor_onprem_tracts.csv"
    sf = OUT / "liquor_source.json"
    if f.exists():
        return pd.read_csv(f, dtype={"GEOID": str}), json.loads(sf.read_text())
    where = ("premisescounty in (" + ",".join(f"'{c}'" for c in NYC_COUNTIES) + ") and description in ("
             + ",".join("'" + d.replace("'", "''") + "'" for d in ON_PREMISES) + ")")
    params = {"$select": "licensepermitid, description, georeference", "$where": where, "$limit": 50000}
    r = requests.get(SLA, params=params, timeout=180)
    r.raise_for_status()
    rows = r.json()
    meta = requests.get("https://data.ny.gov/api/views/9s3h-dpkz.json", timeout=60).json()
    d = pd.DataFrame(rows).dropna(subset=["georeference"])
    d["lon"] = d["georeference"].map(lambda g: g["coordinates"][0])
    d["lat"] = d["georeference"].map(lambda g: g["coordinates"][1])
    d["GEOID"] = points_to_tracts(d["lon"].values, d["lat"].values)
    g = d.groupby("GEOID").size().rename("onprem_licences").reset_index()
    src = {"kind": "ny-open-data", "dataset": "9s3h-dpkz", "name": meta.get("name"),
           "url": "https://data.ny.gov/d/9s3h-dpkz",
           "rows_updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(meta.get("rowsUpdatedAt", 0))),
           "query": params, "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "n_rows": len(rows),
           "n_geocoded": int(len(d)), "n_in_tracts": int(g["onprem_licences"].sum())}
    g.to_csv(f, index=False)
    sf.write_text(json.dumps(src, indent=1))
    return g, src


def z(s):
    return (s - s.mean()) / s.std()


def main():
    base = pd.read_csv(OUT / "tracts_acs.csv", dtype={"GEOID": str})
    nm = pd.read_csv(OUT / "noise_map_tracts.csv", dtype={"GEOID": str})
    c = pd.read_csv(OUT / "complaints311_tracts.csv", dtype={"GEOID": str})
    lq, lsrc = liquor()
    wide = c.pivot_table(index="GEOID", columns="type", values="n", aggfunc="sum").fillna(0)
    nyears = c["year"].nunique()
    df = base.merge(nm, on="GEOID", how="left").merge(wide.reset_index(), on="GEOID", how="left").merge(lq, on="GEOID", how="left")
    df["onprem_licences"] = df["onprem_licences"].fillna(0)
    for t in wide.columns:
        df[t] = df[t].fillna(0)
    df = df[(df["pop"] >= 500) & df["d_logrent"].notna() & df["d_nhw"].notna() & df["poverty"].notna()].copy()
    per = 1000 / df["pop"] / nyears
    df["res_rate"] = df["Noise - Residential"] * per
    df["street_rate"] = (df["Noise - Street/Sidewalk"] + df["Noise - Vehicle"]) * per
    df["comm_rate"] = df["Noise - Commercial"] * per
    df["all_rate"] = df[[t for t in wide.columns if t.startswith("Noise")]].sum(axis=1) * per
    for k in ("res", "street", "comm", "all"):
        df[f"y_{k}"] = np.log1p(df[f"{k}_rate"])
    df["log_density"] = np.log(df["density"])
    df["log_bars"] = np.log1p(df["onprem_licences"])
    df["borough"] = df["boroname"]
    for v in ("noise_mean_db", "noise_leq_db", "share_ge60", "d_logrent", "d_nhw", "log_density", "poverty", "log_bars", "nhw_share22"):
        df["z_" + v] = z(df[v])
    res = {"n_tracts": int(len(df)), "years": sorted(c["year"].unique().tolist())}
    # Spearman correlations
    rho = {}
    for y in ("res_rate", "street_rate", "comm_rate", "all_rate"):
        for x in ("noise_mean_db", "noise_leq_db", "d_logrent", "d_nhw", "onprem_licences", "density", "poverty"):
            r, p = stats.spearmanr(df[y], df[x])
            rho[f"{y}~{x}"] = {"rho": round(float(r), 3), "p": float(p)}
    res["spearman"] = rho
    form = "{y} ~ z_noise_mean_db + z_d_logrent + z_d_nhw + z_log_bars + z_log_density + z_poverty + C(borough)"
    models = {}
    for k in ("res", "street", "comm", "all"):
        m = smf.ols(form.format(y=f"y_{k}"), df).fit(cov_type="HC3")
        models[k] = {v: {"b": float(m.params[v]), "lo": float(m.conf_int().loc[v, 0]), "hi": float(m.conf_int().loc[v, 1])}
                     for v in m.params.index if v.startswith("z_")}
        models[k]["r2"] = float(m.rsquared)
    res["ols"] = models
    # registered contrast: rent change minus modelled noise, residential complaints, bootstrap over tracts
    rng = np.random.default_rng(20261112)
    diffs, diffs_street, diffs_nhw = [], [], []
    f_res = form.format(y="y_res")
    f_st = form.format(y="y_street")
    for _ in range(1000):
        b = df.sample(len(df), replace=True, random_state=int(rng.integers(1e9)))
        m = smf.ols(f_res, b).fit()
        diffs.append(m.params["z_d_logrent"] - m.params["z_noise_mean_db"])
        diffs_nhw.append(m.params["z_d_nhw"] - m.params["z_noise_mean_db"])
        m2 = smf.ols(f_st, b).fit()
        diffs_street.append(m2.params["z_d_logrent"] - m2.params["z_noise_mean_db"])
    full = smf.ols(f_res, df).fit()
    full_st = smf.ols(f_st, df).fit()
    res["contrast_res"] = {"label": "beta(rent change) - beta(modelled noise), log(1+residential complaints per 1,000/yr), per SD",
                           "estimate": float(full.params["z_d_logrent"] - full.params["z_noise_mean_db"]),
                           "lo": float(np.percentile(diffs, 2.5)), "hi": float(np.percentile(diffs, 97.5))}
    res["contrast_street"] = {"label": "same contrast for street/sidewalk + vehicle complaints",
                              "estimate": float(full_st.params["z_d_logrent"] - full_st.params["z_noise_mean_db"]),
                              "lo": float(np.percentile(diffs_street, 2.5)), "hi": float(np.percentile(diffs_street, 97.5))}
    res["contrast_res_nhw"] = {"label": "secondary (named in the statement, not the registered contrast): beta(change in non-Hispanic white share) - beta(modelled noise), residential",
                               "estimate": float(full.params["z_d_nhw"] - full.params["z_noise_mean_db"]),
                               "lo": float(np.percentile(diffs_nhw, 2.5)), "hi": float(np.percentile(diffs_nhw, 97.5))}
    # sensitivity: energy-mean Leq instead of class-mean
    m = smf.ols(f_res.replace("z_noise_mean_db", "z_noise_leq_db"), df).fit(cov_type="HC3")
    res["sensitivity_leq_res"] = {v: float(m.params[v]) for v in ("z_noise_leq_db", "z_d_logrent", "z_d_nhw")}
    # binned descriptive: residential rate by noise decile and by rent-change decile
    for x in ("noise_mean_db", "d_logrent"):
        q = pd.qcut(df[x].rank(method="first"), 10, labels=False)
        res[f"bins_{x}"] = df.groupby(q).agg(x=(x, "median"), res=("res_rate", "median"), street=("street_rate", "median"),
                                             n=("GEOID", "size")).reset_index(drop=True).to_dict(orient="records")
    res["totals"] = {t: int(c.loc[c["type"] == t, "n"].sum()) for t in c["type"].unique()}
    res["liquor_source"] = lsrc
    df.to_csv(OUT / "noise311_tracts.csv", index=False)
    (OUT / "noise311_results.json").write_text(json.dumps(res, indent=1, default=str))
    for k, v in models.items():
        print(k, {a: round(b["b"], 3) for a, b in v.items() if isinstance(b, dict)}, "r2", round(v["r2"], 3))
    print("contrast_res", res["contrast_res"])
    print("contrast_street", res["contrast_street"])
    print("contrast_res_nhw", res["contrast_res_nhw"])
    print("sens", res["sensitivity_leq_res"])
    for k, v in rho.items():
        print(f"{k:40s} {v['rho']:+.3f}")


if __name__ == "__main__":
    main()
