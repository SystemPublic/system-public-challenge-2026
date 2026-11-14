"""nbhd-rodents-asthma: rodents and child asthma ED visits across UHF42 neighbourhoods.

EHDP data are read from github.com/nychealth/EHDP-data at a pinned commit. The DOHMH Rodent Inspection table
(p937-wjvj) is aggregated by ZIP code with SoQL (mean coordinates give a ZIP centroid, assigned to a UHF42
polygon; UHF42 neighbourhoods are unions of ZIP codes). 311 rodent complaints come from fetch311.py (tract
counts, assigned to UHF42 by tract representative point).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402

COMMIT = "547482b9df589006543e13e8cdf6546e00ed9998"
GH = f"https://raw.githubusercontent.com/nychealth/EHDP-data/{COMMIT}/"
RAW = ROOT / "data" / "raw" / "ehdp"
OUT = ROOT / "data" / "derived" / "neighbourhood"
MEASURES = {  # name: (indicator file, measure id)
    "rodents_bldg_pct": (48, 94),        # NYCHVS homes with mice or rats in the building, percent
    "rodents_inside_pct": (2105, 634),   # CHS adults reporting mice or rats inside, percent (2012 only)
    "asthma_ed_5_17": (2379, 1196),      # asthma ED visits age 5-17, estimated annual rate per 10,000
    "asthma_ed_adult": (2380, 1198),     # asthma ED visits adults, estimated annual rate per 10,000
    "poverty_pct": (103, 221),           # ACS poverty percent
    "housing_problems_pct": (2399, 1248),  # renter homes with any health-related housing problem, percent
    "cockroach_pct": (107, 245),         # NYCHVS homes with cockroaches, percent
}


def ehdp_file(path: str) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    f = RAW / Path(path).name
    if not f.exists():
        r = requests.get(GH + path, timeout=120)
        r.raise_for_status()
        f.write_bytes(r.content)
    return f


def ehdp():
    tp = {t["TimePeriodID"]: t["TimePeriod"] for t in json.loads(ehdp_file("indicators/metadata/TimePeriods.json").read_text())}
    frames = {}
    for name, (ind, mid) in MEASURES.items():
        d = pd.DataFrame(json.loads(ehdp_file(f"indicators/data/{ind}.json").read_text()))
        d = d[(d["MeasureID"] == mid) & (d["GeoType"] == "UHF42")].copy()
        d["period"] = d["TimePeriodID"].map(tp)
        frames[name] = d[["GeoID", "TimePeriodID", "period", "Value"]]
    return frames


def pick(frames, name, period=None):
    d = frames[name]
    if period is None:
        tid = d["TimePeriodID"].max()
    else:
        cand = d[d["period"] == period]
        tid = cand["TimePeriodID"].iloc[0] if len(cand) else d["TimePeriodID"].max()
    s = d[d["TimePeriodID"] == tid].set_index("GeoID")["Value"].astype(float)
    return s, d.loc[d["TimePeriodID"] == tid, "period"].iloc[0]


def uhf_polys():
    g = gpd.read_file(ehdp_file("geography/UHF42.geojson"))
    g = g.to_crs(4326) if g.crs else g.set_crs(4326)
    g["GeoID"] = g["GEOCODE"].astype(int)
    return g[["GeoID", "GEONAME", "BOROUGH", "geometry"]]


def inspections(uhf):
    rows, src = socrata.query(
        "p937-wjvj",
        select="zip_code, avg(latitude) as lat, avg(longitude) as lon, count(*) as n, "
               "sum(case(starts_with(result, 'Failed for Rat Activity'), 1, true, 0)) as rat",
        where="inspection_type = 'Initial' and inspection_date between '2022-01-01T00:00:00' and '2024-12-31T23:59:59' "
              "and latitude > 40 and longitude < -73",
        group="zip_code", limit=5000)
    d = pd.DataFrame(rows)
    for c in ("lat", "lon", "n", "rat"):
        d[c] = pd.to_numeric(d[c])
    pts = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d["lon"], d["lat"]), crs=4326)
    j = gpd.sjoin(pts, uhf, how="inner", predicate="within")
    g = j.groupby("GeoID")[["n", "rat"]].sum()
    g["rat_fail_share"] = g["rat"] / g["n"]
    return g, src


def complaints(uhf):
    c = pd.read_csv(OUT / "complaints311_tracts.csv", dtype={"GEOID": str})
    c = c[c["type"] == "Rodent"].groupby("GEOID")["n"].sum()
    base = pd.read_csv(OUT / "tracts_acs.csv", dtype={"GEOID": str}).set_index("GEOID")
    t = gpd.read_file(OUT / "tracts.geojson").set_crs(4326, allow_override=True)
    t["geometry"] = t.representative_point()
    j = gpd.sjoin(t, uhf, how="inner", predicate="within").set_index("geoid")
    j["pop"] = base["pop"]
    j["rodent311"] = c.reindex(j.index).fillna(0)
    g = j.groupby("GeoID")[["pop", "rodent311"]].sum()
    g["rodent311_per1k_yr"] = 1000 * g["rodent311"] / g["pop"] / 3
    return g


def zs(s):
    return (s - s.mean()) / s.std()


def model(df, x, y, controls=("poverty_pct", "housing_problems_pct")):
    d = df[[x, y, *controls]].dropna().copy()
    d["ly"] = np.log(d[y])
    for v in (x, *controls):
        d["z_" + v] = zs(d[v])
    m0 = smf.ols(f"ly ~ z_{x}", d).fit(cov_type="HC3")
    m1 = smf.ols("ly ~ " + " + ".join("z_" + v for v in (x, *controls)), d).fit(cov_type="HC3")
    rho, p = stats.spearmanr(d[x], d[y])
    ci0, ci1 = m0.conf_int().loc["z_" + x], m1.conf_int().loc["z_" + x]
    return {"x": x, "y": y, "n": int(len(d)), "spearman_rho": float(rho), "spearman_p": float(p),
            "unadjusted": {"estimate": float(m0.params["z_" + x]), "lo": float(ci0[0]), "hi": float(ci0[1])},
            "adjusted": {"estimate": float(m1.params["z_" + x]), "lo": float(ci1[0]), "hi": float(ci1[1]),
                         "p": float(m1.pvalues["z_" + x])},
            "controls": list(controls),
            "control_coefs": {v: float(m1.params["z_" + v]) for v in controls}}


def main():
    fr = ehdp()
    uhf = uhf_polys()
    used = {}
    s, used["rodents_bldg_pct"] = pick(fr, "rodents_bldg_pct")
    df = pd.DataFrame({"rodents_bldg_pct": s})
    yr = used["rodents_bldg_pct"]  # 2017
    for name, period in [("asthma_ed_5_17", yr), ("asthma_ed_adult", yr), ("housing_problems_pct", yr),
                         ("cockroach_pct", yr), ("poverty_pct", "2013-17"), ("rodents_inside_pct", None)]:
        s, used[name] = pick(fr, name, period)
        df[name] = s
    s, used["asthma_ed_5_17_latest"] = pick(fr, "asthma_ed_5_17")
    df["asthma_ed_5_17_latest"] = s
    s, used["poverty_pct_latest"] = pick(fr, "poverty_pct")
    df["poverty_pct_latest"] = s
    insp, isrc = inspections(uhf)
    comp = complaints(uhf)
    df = df.join(insp[["rat_fail_share", "n"]].rename(columns={"n": "initial_inspections"})).join(comp[["rodent311_per1k_yr"]])
    df = df.join(uhf.set_index("GeoID")[["GEONAME", "BOROUGH"]])
    res = {"periods_used": used, "ehdp_commit": COMMIT}
    res["primary"] = model(df, "rodents_bldg_pct", "asthma_ed_5_17")
    res["primary_plus_cockroach"] = model(df, "rodents_bldg_pct", "asthma_ed_5_17",
                                          ("poverty_pct", "housing_problems_pct", "cockroach_pct"))
    res["adult_outcome"] = model(df, "rodents_bldg_pct", "asthma_ed_adult")
    res["chs_inside"] = model(df, "rodents_inside_pct", "asthma_ed_5_17")
    res["inspections_vs_latest"] = model(df.assign(poverty_pct=df["poverty_pct_latest"]), "rat_fail_share",
                                         "asthma_ed_5_17_latest")
    res["complaints_vs_latest"] = model(df.assign(poverty_pct=df["poverty_pct_latest"]), "rodent311_per1k_yr",
                                        "asthma_ed_5_17_latest")
    # how well do the city's operational rodent measures track the survey measure?
    res["validity"] = {
        "rho_hvs_vs_inspection_fail": float(stats.spearmanr(df["rodents_bldg_pct"], df["rat_fail_share"]).statistic),
        "rho_hvs_vs_311_rodent": float(stats.spearmanr(df["rodents_bldg_pct"], df["rodent311_per1k_yr"]).statistic),
        "rho_hvs_vs_poverty": float(stats.spearmanr(df["rodents_bldg_pct"], df["poverty_pct"]).statistic),
        "rho_hvs_vs_housing_problems": float(stats.spearmanr(df["rodents_bldg_pct"], df["housing_problems_pct"]).statistic),
    }
    res["sources"] = [isrc, {"kind": "github", "repo": "nychealth/EHDP-data", "commit": COMMIT,
                             "files": [f"indicators/data/{i}.json" for i, _ in MEASURES.values()] + ["geography/UHF42.geojson"]},
                      {"kind": "derived", "file": "data/derived/neighbourhood/complaints311_tracts.csv",
                       "note": "311 erm2-nwe9 complaint_type 'Rodent' 2022-2024; see complaints311_sources.json"}]
    df.reset_index().rename(columns={"index": "GeoID"}).to_csv(OUT / "rodents_asthma_uhf.csv", index=False)
    (OUT / "rodents_asthma_results.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k not in ("sources",)}, indent=1, default=str)[:5000])


if __name__ == "__main__":
    main()
