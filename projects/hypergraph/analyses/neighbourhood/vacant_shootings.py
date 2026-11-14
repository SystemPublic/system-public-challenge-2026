"""nbhd-vacant-shootings: vacant land share (MapPLUTO) and shootings per resident by 2020 census tract.

Run base.py first. Writes data/derived/neighbourhood/vacant_shootings_tracts.csv, vacant_shootings_results.json
and figures/neighbourhood/vacant_shootings.png.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402
from analyses.neighbourhood.geo import points_to_tracts  # noqa: E402

OUT = ROOT / "data" / "derived" / "neighbourhood"
FIG = ROOT / "figures" / "neighbourhood"
BORO = {"1": "36061", "2": "36005", "3": "36047", "4": "36081", "5": "36085"}
YEARS = (2019, 2024)


def pluto():
    srcs = []
    rows, src = socrata.query("64uk-42ks", select="bct2020, landuse, ownertype, count(*) as n, sum(lotarea) as area",
                              group="bct2020, landuse, ownertype", limit=50000)
    srcs.append(src)
    d = pd.DataFrame(rows)
    d["n"] = pd.to_numeric(d["n"])
    d["area"] = pd.to_numeric(d["area"])
    d = d.dropna(subset=["bct2020"])
    d["vac"] = d["landuse"].eq("11")
    d["vac_city"] = d["vac"] & d["ownertype"].eq("C")
    d["vac_priv"] = d["vac"] & ~d["ownertype"].isin(["C", "X", "O", "M"])
    g = d.groupby("bct2020").apply(lambda x: pd.Series({
        "lots": x["n"].sum(), "lot_area": x["area"].sum(),
        "vac_lots": x.loc[x["vac"], "n"].sum(), "vac_area": x.loc[x["vac"], "area"].sum(),
        "vac_area_city": x.loc[x["vac_city"], "area"].sum(), "vac_area_priv": x.loc[x["vac_priv"], "area"].sum(),
    }), include_groups=False).reset_index()
    g["GEOID"] = g["bct2020"].str[0].map(BORO) + g["bct2020"].str[1:]
    vrows, vsrc = socrata.query("64uk-42ks", select="version", group="version")
    src_version = vrows[0]["version"] if vrows else None
    srcs[0]["pluto_version"] = src_version
    return g, srcs


def shootings():
    where = f"occur_date between '{YEARS[0]}-01-01T00:00:00' and '{YEARS[1]}-12-31T23:59:59' and latitude is not null"
    rows, src = socrata.query_all("5ucz-vwe8", select="incident_key, occur_date, latitude, longitude", where=where,
                                  order="incident_key")
    d = pd.DataFrame(rows)
    d = d.drop_duplicates("incident_key")
    d["lat"] = pd.to_numeric(d["latitude"])
    d["lon"] = pd.to_numeric(d["longitude"])
    # In 5ucz-vwe8 (fetched Nov 2026) the 'latitude' column holds longitudes and vice versa. Swap when detected.
    swapped = bool((d["lat"] < 0).mean() > 0.5)
    if swapped:
        d["lat"], d["lon"] = d["lon"].copy(), d["lat"].copy()
    src["note"] = "latitude/longitude columns swapped in source; corrected" if swapped else "coordinates as published"
    # cross-check with the archived historic table (victim-level rows): distinct incidents 2019-2023
    xr, xsrc = socrata.query("833y-fsy8", select="date_extract_y(occur_date) as y, count(distinct incident_key) as n",
                             where="occur_date between '2019-01-01T00:00:00' and '2024-12-31T23:59:59'", group="y", order="y")
    return d, [src, xsrc], xr


def irr_table(m, var, step=1.0):
    b, se = m.params[var], m.bse[var]
    return {"estimate": float(np.exp(b * step)), "lo": float(np.exp((b - 1.96 * se) * step)),
            "hi": float(np.exp((b + 1.96 * se) * step)), "p": float(m.pvalues[var])}


def main():
    base = pd.read_csv(OUT / "tracts_acs.csv", dtype={"GEOID": str, "boroct2020": str})
    g, s1 = pluto()
    sh, s2, xcheck = shootings()
    sh["GEOID"] = points_to_tracts(sh["lon"].values, sh["lat"].values)
    yr = pd.to_datetime(sh["occur_date"]).dt.year
    counts = sh.groupby("GEOID").size().rename("shootings")
    by_year = sh.assign(y=yr).groupby("y").size().to_dict()
    df = base.merge(g, on="GEOID", how="left").merge(counts, on="GEOID", how="left")
    df["shootings"] = df["shootings"].fillna(0)
    df = df[(df["pop"] >= 500) & df["poverty"].notna() & (df["lot_area"] > 0)].copy()
    df["vac_share"] = df["vac_area"] / df["lot_area"]
    df["vac_share_city"] = df["vac_area_city"] / df["lot_area"]
    df["vac_share_priv"] = df["vac_area_priv"] / df["lot_area"]
    df["vac_lots_per1k"] = 1000 * df["vac_lots"] / df["lots"]
    df["vac_q"] = pd.qcut(df["vac_share"].rank(method="first"), 5, labels=False)  # 0..4
    df["log_pop"] = np.log(df["pop"])
    df["log_density"] = np.log(df["density"])
    df["pov10"] = df["poverty"] * 10  # per 10 percentage points
    df["borough"] = df["boroname"]
    df["z_vac"] = (df["vac_share"] - df["vac_share"].mean()) / df["vac_share"].std()
    df["z_city"] = (df["vac_share_city"] - df["vac_share_city"].mean()) / df["vac_share_city"].std()
    df["z_priv"] = (df["vac_share_priv"] - df["vac_share_priv"].mean()) / df["vac_share_priv"].std()
    df["z_lots"] = (df["vac_lots_per1k"] - df["vac_lots_per1k"].mean()) / df["vac_lots_per1k"].std()

    fam = sm.families.NegativeBinomial(alpha=1.0)
    res = {}

    def fit(formula):
        # estimate alpha by ML first, then refit GLM with that alpha and robust SE
        nb = smf.negativebinomial(formula, df, offset=df["log_pop"]).fit(disp=0, maxiter=200)
        alpha = float(nb.params["alpha"])
        m = smf.glm(formula, df, family=sm.families.NegativeBinomial(alpha=alpha), offset=df["log_pop"]).fit(cov_type="HC1")
        return m, alpha

    m0, a0 = fit("shootings ~ vac_q")
    m1, a1 = fit("shootings ~ vac_q + pov10 + log_density + C(borough)")
    m2, _ = fit("shootings ~ z_vac + pov10 + log_density + C(borough)")
    m3, _ = fit("shootings ~ z_city + z_priv + pov10 + log_density + C(borough)")
    m4, _ = fit("shootings ~ z_lots + pov10 + log_density + C(borough)")
    m5, _ = fit("shootings ~ vac_q + pov10 + log_density + C(borough) + nhw_share22")
    res["unadjusted_per_quintile"] = irr_table(m0, "vac_q")
    res["adjusted_per_quintile"] = irr_table(m1, "vac_q")
    res["adjusted_per_sd"] = irr_table(m2, "z_vac")
    res["adjusted_city_owned_per_sd"] = irr_table(m3, "z_city")
    res["adjusted_private_per_sd"] = irr_table(m3, "z_priv")
    res["adjusted_vacant_lots_per_1k_per_sd"] = irr_table(m4, "z_lots")
    res["adjusted_plus_race_per_quintile"] = irr_table(m5, "vac_q")
    res["poverty_per_10pp"] = irr_table(m1, "pov10")
    res["alpha"] = [a0, a1]
    # without Staten Island (large natural vacant land, few shootings)
    sub = df[df["borough"] != "Staten Island"].copy()
    sub["vac_q"] = pd.qcut(sub["vac_share"].rank(method="first"), 5, labels=False)
    nb = smf.negativebinomial("shootings ~ vac_q + pov10 + log_density + C(borough)", sub, offset=sub["log_pop"]).fit(disp=0, maxiter=200)
    m6 = smf.glm("shootings ~ vac_q + pov10 + log_density + C(borough)", sub,
                 family=sm.families.NegativeBinomial(alpha=float(nb.params["alpha"])), offset=sub["log_pop"]).fit(cov_type="HC1")
    res["adjusted_per_quintile_no_staten_island"] = irr_table(m6, "vac_q")
    # descriptive
    q = df.groupby("vac_q").agg(vac_share_min=("vac_share", "min"), vac_share_max=("vac_share", "max"),
                                pop=("pop", "sum"), shootings=("shootings", "sum"), poverty=("poverty", "median"))
    q["rate_per_10k_per_year"] = 1e4 * q["shootings"] / q["pop"] / (YEARS[1] - YEARS[0] + 1)
    res["quintiles"] = q.reset_index().to_dict(orient="records")
    df["pov_t"] = pd.qcut(df["poverty"], 3, labels=["low", "middle", "high"])
    t = df.groupby(["pov_t", "vac_q"], observed=True).agg(pop=("pop", "sum"), shootings=("shootings", "sum"), n=("GEOID", "size"))
    t["rate"] = 1e4 * t["shootings"] / t["pop"] / (YEARS[1] - YEARS[0] + 1)
    res["poverty_tercile_by_quintile"] = t.reset_index().astype({"pov_t": str}).to_dict(orient="records")
    res["n_tracts"] = int(len(df))
    res["n_shootings_in_tracts"] = int(df["shootings"].sum())
    res["n_shootings_total"] = int(len(sh))
    res["shootings_by_year_5ucz"] = {int(k): int(v) for k, v in by_year.items()}
    res["crosscheck_833y_distinct_incidents_by_year"] = xcheck
    res["citywide_vacant_share_of_lot_area"] = float(g["vac_area"].sum() / g["lot_area"].sum())
    res["sources"] = s1 + s2
    df.drop(columns=["pov_t"]).to_csv(OUT / "vacant_shootings_tracts.csv", index=False)
    (OUT / "vacant_shootings_results.json").write_text(json.dumps(res, indent=1, default=str))
    for k, v in res.items():
        if isinstance(v, dict) and "estimate" in v:
            print(f"{k:45s} {v['estimate']:.3f} [{v['lo']:.3f}, {v['hi']:.3f}] p={v['p']:.3g}")
    print(pd.DataFrame(res["quintiles"]))
    print(t)
    print("n", res["n_tracts"], "shootings", res["n_shootings_in_tracts"], "/", res["n_shootings_total"])


if __name__ == "__main__":
    main()
