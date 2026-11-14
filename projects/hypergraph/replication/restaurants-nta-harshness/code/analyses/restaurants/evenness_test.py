"""Registered tests restaurants-nta-harshness and restaurants-nta-frequency: are detected critical
violations per routine inspection, and routine inspections per restaurant, even across Manhattan's
2020 NTAs once restaurant mix is adjusted for?

Fixed source: the Underlay snapshot nyc/restaurant-inspections v1.0.0 (hash ulv2:07a7f08a...739c,
Manhattan, inspections 2024-01-02 to 2026-06-09), read from ~/opt/nyc-concordance/underlay/. The
live table deletes closed restaurants and revises recent scores and violations downward
(docs/underlay_drift.md), so the snapshot is used. NTA: point-in-polygon of the restaurant's
coordinates in the 2020 NTA boundaries (NYC Open Data 9nt8-h7nd). Restaurants without coordinates
and NTAs with fewer than 20 restaurants (parks, airports) are dropped.

Harshness. Unit: Cycle Inspection / Initial Inspection. Outcome: critical violation records.
Null model (Poisson GLM): cuisine group (top 20), chain (name with >= 5 CAMIS in the snapshot),
inspection quarter, day of week, log of Manhattan inspections that day (workload), log of the
number of restaurants in the NTA (restaurant presence), and whether the restaurant's first
observed inspection in the snapshot was a pre-permit inspection (new restaurant).
Frequency. Unit: restaurant with at least one Cycle Inspection / Initial Inspection. Outcome:
number of cycle initial inspections. Null model: Poisson GLM with offset log(days from the
restaurant's first observed inspection to 2026-06-09), the A/B/C band of its first cycle initial
score (the city's schedule depends on it), cuisine group, chain, log NTA restaurant count, new.
Statistic (both): S = sum over NTAs of (sum of y - mu)^2 / (sum of mu), mu from the null model.
Permutation null: NTA labels permuted across restaurants (a restaurant keeps all its inspections),
10,000 draws, numpy default_rng(20261113). Effect size: NTA fixed effects added to the null model,
robust SE clustered by restaurant, tau = sqrt(max(0, var(b_nta) - mean(se^2))) on the log scale.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

import common as c

SNAP = Path.home() / "opt" / "nyc-concordance" / "underlay" / "records_v1.0.0.ndjson"
SNAP_HASH = "ulv2:07a7f08a0d5c85649920f8adc6946d27c17f5e2d75e9ee07c0ad4ae0fcc6739c"
END = pd.Timestamp("2026-06-09")
NDRAW = 10_000
SEED = 20261113
MIN_REST = 20


def load_snapshot():
    R, I, V = [], [], []
    with SNAP.open() as f:
        for line in f:
            r = json.loads(line)
            d = r["data"]
            if r["type"] == "Restaurant":
                R.append({"camis": r["id"], "name": d.get("name"), "cuisine": d.get("cuisineDescription"),
                          "lat": d.get("latitude"), "lon": d.get("longitude")})
            elif r["type"] == "Inspection":
                I.append({"iid": r["id"], "camis": d.get("restaurantId"), "date": d.get("inspectionDate"),
                          "itype": d.get("inspectionType"), "score": d.get("score"), "grade": d.get("grade")})
            else:
                V.append({"iid": d.get("inspectionId"), "crit": d.get("criticalFlag") == "Critical"})
    R, I, V = pd.DataFrame(R), pd.DataFrame(I), pd.DataFrame(V)
    I["date"] = pd.to_datetime(I["date"])
    I["n_crit"] = I.iid.map(V[V.crit].groupby("iid").size()).fillna(0).astype(int)
    I["n_viol"] = I.iid.map(V.groupby("iid").size()).fillna(0).astype(int)
    return R, I


def nta_polygons():
    import geopandas as gpd
    import requests
    f = c.DER / "nta2020.geojson"
    if not f.exists():
        r = requests.get("https://data.cityofnewyork.us/resource/9nt8-h7nd.geojson", params={"$limit": 1000}, timeout=120)
        r.raise_for_status()
        f.write_text(r.text)
    g = gpd.read_file(f)
    return g[g.boroname == "Manhattan"][["nta2020", "ntaname", "geometry"]]


def assign_nta(R):
    import geopandas as gpd
    g = nta_polygons()
    R = R.dropna(subset=["lat", "lon"])
    R = R[(R.lat > 40.5) & (R.lon < -73.8)]
    pts = gpd.GeoDataFrame(R, geometry=gpd.points_from_xy(R.lon, R.lat), crs="EPSG:4326").to_crs(g.crs)
    j = gpd.sjoin(pts, g, how="inner", predicate="within")
    return pd.DataFrame(j.drop(columns=["geometry", "index_right"]))


def design(df, cols, cat):
    X = pd.get_dummies(df[cols], columns=cat, drop_first=True, dtype=float)
    X = X.loc[:, X.std() > 0]
    return sm.add_constant(X, has_constant="add")


def score_stat(resid, mu, g, ng):
    a = np.bincount(g, weights=resid, minlength=ng)
    b = np.bincount(g, weights=mu, minlength=ng)
    return float(np.sum(a * a / b))


def permutation(df, y, X, offset=None, label="nta2020"):
    m = sm.GLM(df[y].values, X, family=sm.families.Poisson(), offset=offset).fit()
    mu = m.fittedvalues if offset is None else m.predict(X, offset=offset)
    mu = np.asarray(mu)
    resid = df[y].values - mu
    codes, uniq = pd.factorize(df[label])
    rcodes, runiq = pd.factorize(df["camis"])
    rest_nta = pd.Series(codes).groupby(rcodes).first().values  # one NTA per restaurant
    obs = score_stat(resid, mu, codes, len(uniq))
    rng = np.random.default_rng(SEED)
    null = np.empty(NDRAW)
    for k in range(NDRAW):
        perm = rng.permutation(rest_nta)
        null[k] = score_stat(resid, mu, perm[rcodes], len(uniq))
    p = (1 + np.sum(null >= obs)) / (NDRAW + 1)
    disp = float(m.pearson_chi2 / m.df_resid)
    return {"S_obs": obs, "S_null_mean": float(null.mean()), "S_null_q99": float(np.quantile(null, 0.99)),
            "S_ratio": obs / float(null.mean()), "p": float(p), "n_draws": NDRAW, "seed": SEED,
            "n_ntas": len(uniq), "n_units": len(df), "dispersion_null_model": round(disp, 2)}, mu


def nta_effects(df, y, X, offset=None, label="nta2020"):
    D = pd.get_dummies(df[label], dtype=float)
    D = D.sub(D.mean())  # effects relative to the Manhattan mean (sum-to-zero style centring)
    Xf = pd.concat([X.drop(columns=[x for x in X.columns if x.startswith("log_nta_rest")]), D.iloc[:, 1:]], axis=1)
    m = sm.GLM(df[y].values, Xf, family=sm.families.Poisson(), offset=offset).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(df["camis"])[0]})
    b = m.params[D.columns[1:]]
    se = m.bse[D.columns[1:]]
    # put the omitted level back: effects measured from the first NTA, recentred to mean zero
    full = pd.concat([pd.Series({D.columns[0]: 0.0}), b])
    full = full - full.mean()
    tau2 = max(0.0, float(np.var(b, ddof=1) - np.mean(se ** 2)))
    return full, se, math.sqrt(tau2)


def main():
    R, I = load_snapshot()
    Rn = assign_nta(R)
    counts = Rn.groupby("nta2020").size()
    keep = counts[counts >= MIN_REST].index
    Rn = Rn[Rn.nta2020.isin(keep)].copy()
    Rn["log_nta_rest"] = np.log(Rn.nta2020.map(counts))
    Rn["cuis"] = c.cuisine_group(Rn.cuisine)
    nm = c.norm_dba(Rn.name)
    Rn["chain"] = nm.map(nm.value_counts()).ge(5).astype(float)
    I = I.sort_values("date")
    first = I.groupby("camis").head(1).set_index("camis")
    Rn["new"] = Rn.camis.map(first.itype.str.startswith("Pre-permit")).fillna(False).astype(float)
    Rn["first_date"] = Rn.camis.map(first.date)
    work = I.groupby("date").size()
    ci = I[I.itype == "Cycle Inspection / Initial Inspection"].merge(Rn, on="camis")
    ci["log_work"] = np.log(ci.date.map(work))
    ci["q"] = ci.date.dt.to_period("Q").astype(str)
    ci["dow"] = ci.date.dt.dayofweek.astype(str)
    Xh = design(ci, ["cuis", "chain", "q", "dow", "log_work", "log_nta_rest", "new"], ["cuis", "q", "dow"])
    harsh, mu_h = permutation(ci, "n_crit", Xh)
    eff_h, se_h, tau_h = nta_effects(ci, "n_crit", Xh)
    harsh["tau_log"] = tau_h
    harsh["mean_crit_per_initial"] = float(ci.n_crit.mean())
    harsh["n_restaurants"] = int(ci.camis.nunique())

    # frequency
    band = ci.sort_values("date").groupby("camis").head(1).set_index("camis").score
    rf = Rn[Rn.camis.isin(ci.camis)].copy()
    rf["n_ci"] = rf.camis.map(ci.groupby("camis").size())
    rf["band"] = rf.camis.map(band).pipe(lambda s: np.where(s >= 28, "C", np.where(s >= 14, "B", "A")))
    rf["days"] = (END - rf.first_date).dt.days.clip(lower=30)
    Xf = design(rf, ["band", "cuis", "chain", "log_nta_rest", "new"], ["band", "cuis"])
    off = np.log(rf.days.values / 365.25)
    freq, _ = permutation(rf, "n_ci", Xf, offset=off)
    eff_f, se_f, tau_f = nta_effects(rf, "n_ci", Xf, offset=off)
    freq["tau_log"] = tau_f
    freq["mean_ci_per_restaurant_year"] = float(rf.n_ci.sum() / (rf.days.sum() / 365.25))

    names = Rn.drop_duplicates("nta2020").set_index("nta2020").ntaname
    tab = pd.DataFrame({"ntaname": names, "restaurants": counts.reindex(names.index),
                        "initial_inspections": ci.groupby("nta2020").size(),
                        "crit_per_initial_raw": ci.groupby("nta2020").n_crit.mean(),
                        "crit_obs_over_expected": ci.groupby("nta2020").n_crit.sum() / pd.Series(mu_h, index=ci.index).groupby(ci.nta2020).sum(),
                        "harsh_rr_adj": np.exp(eff_h), "freq_ci_per_rest_year_raw": rf.groupby("nta2020").n_ci.sum() / (rf.groupby("nta2020").days.sum() / 365.25),
                        "freq_rr_adj": np.exp(eff_f)})
    tab.index.name = "nta2020"
    tab.round(4).to_csv(c.DER / "evenness_nta.csv")
    out = {"source": {"kind": "underlay", "collection": "nyc/restaurant-inspections", "version": "v1.0.0", "hash": SNAP_HASH,
                      "url": "https://www.underlay.org/api/collections/nyc/restaurant-inspections", "dates": "2024-01-02 to 2026-06-09"},
           "nta_source": {"dataset": "9nt8-h7nd", "name": "2020 Neighborhood Tabulation Areas (NTAs)"},
           "harshness": harsh, "frequency": freq}
    for k in ("harshness", "frequency"):
        r = out[k]
        r["support_if_met"] = r["p"] <= 0.01 and r["tau_log"] >= 0.05
        r["refute_if_met"] = r["p"] > 0.10
    c.write_json("evenness_test.json", out)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
