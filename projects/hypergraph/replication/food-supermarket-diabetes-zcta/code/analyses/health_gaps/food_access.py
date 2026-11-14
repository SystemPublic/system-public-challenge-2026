"""Registered test for claim food-supermarket-diabetes-zcta (script fixed before any outcome is read).

Unit: NYC ZIP code tabulation areas (ZCTA, 2020) assigned to a NYC county by the Census ZCTA-county
relationship file (largest land overlap), with adult population >= 5,000.
Outcome: SPARCS adult Prevention Quality Indicators by patient ZIP (health.data.ny.gov 5q8c-d6xq),
diabetes PQIs 01 (short-term complications), 03 (long-term complications), 14 (uncontrolled), 16
(lower-extremity amputation); summed observed and summed expected rates per 100,000 over the three
latest years in the file; outcome = log(observed / expected) (expected is the age-sex expected rate).
Exposure: supermarkets per 10,000 residents in the ZIP: NY State Retail Food Stores (data.ny.gov
9a8c-vfzj), establishment type containing 'A' (retail store), square_footage >= 6,000 (FRESH minimum),
counted by zip_code; x = log2((count + 0.5) / population * 10,000).
Covariates (ACS 2019-2023 5-year, ZCTA): log residential density (population / land km2, 2020 Gazetteer),
percent below poverty, log median household income, median age.
Primary model: OLS of the outcome on x + log density + poverty + log income + median age, weighted by
population, HC3 standard errors. Effect reported as ratio per doubling = exp(beta).
Secondary (not deciding): + percent Black and percent Hispanic; + percent households without a car;
threshold 10,000 sq ft; per-area density instead of per-resident (log2 stores per km2), with and without
log residential density (the chicken-and-egg check); all food stores (type A any size).
Writes data/derived/health_gaps/food_access.json and food_zcta.csv.
"""
from __future__ import annotations
import io
import json
import os
import subprocess
import zipfile
import numpy as np
import pandas as pd
import requests
import statsmodels.formula.api as smf
from concord import socrata
from analyses.health_gaps.common import DER

OPT = os.path.expanduser("~/opt/nyc-concordance/census")
NYC = {"36005": "Bronx", "36047": "Brooklyn", "36061": "Manhattan", "36081": "Queens", "36085": "Staten Island"}
REL = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt"
GAZ = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_zcta_national.zip"
SF = "https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/acsdt5y2023-{t}.dat"
ACS = ("https://api.census.gov/data/2023/acs/acs5?get=B01003_001E,B19013_001E,B17001_001E,B17001_002E,"
       "B01002_001E,B03002_001E,B03002_004E,B03002_012E,B08201_001E,B08201_002E,B09021_001E"
       "&for=zip%20code%20tabulation%20area:*")


def _dl(url, name):
    os.makedirs(OPT, exist_ok=True)
    f = os.path.join(OPT, name)
    if not os.path.exists(f):
        subprocess.run(["curl", "-s", "-f", "-m", "300", "-A", "Mozilla/5.0", "-o", f, url], check=True)
    return f


def zctas():
    rel = pd.read_csv(_dl(REL, "zcta_county_rel.txt"), sep="|", dtype=str)
    rel["al"] = pd.to_numeric(rel["AREALAND_PART"])
    rel = rel[rel["GEOID_ZCTA5_20"].notna()]
    top = rel.sort_values("al").groupby("GEOID_ZCTA5_20").tail(1)
    top = top[top["GEOID_COUNTY_20"].isin(NYC)]
    z = pd.DataFrame({"zcta": top["GEOID_ZCTA5_20"], "county": top["GEOID_COUNTY_20"].map(NYC)})
    gz = zipfile.ZipFile(_dl(GAZ, "gaz_zcta_2020.zip"))
    g = pd.read_csv(gz.open(gz.namelist()[0]), sep="\t", dtype={"GEOID": str})
    g.columns = [c.strip() for c in g.columns]
    z = z.merge(g[["GEOID", "ALAND"]].rename(columns={"GEOID": "zcta"}), on="zcta")
    # Deviation (13 Nov 2026, after registration, before any outcome was read): the Census API now
    # requires a key, so the same ACS 2019-2023 variables are read from the table-based summary files.
    a = None
    for t in ("b01003", "b19013", "b17001", "b01002", "b03002", "b08201", "b09021"):
        f = _dl(SF.format(t=t), f"acsdt5y2023-{t}.dat")
        x = pd.read_csv(f, sep="|", dtype={"GEO_ID": str}, usecols=lambda c: c == "GEO_ID" or "_E0" in c)
        x = x[x.GEO_ID.str.startswith("860Z200US")]
        x["zcta"] = x.GEO_ID.str[-5:]
        x = x.drop(columns="GEO_ID")
        x.columns = [c if c == "zcta" else c.replace("_E", "_0").replace("_0", "_", 1) + "E" for c in x.columns]
        a = x if a is None else a.merge(x, on="zcta", how="outer")
    for c in a.columns:
        if c != "zcta":
            a[c] = pd.to_numeric(a[c], errors="coerce")
    z = z.merge(a, on="zcta")
    z["pop"] = z.B01003_001E
    z["adults"] = z.B09021_001E
    z["density"] = z["pop"] / (z.ALAND / 1e6)
    z["poverty"] = 100 * z.B17001_002E / z.B17001_001E
    z["income"] = z.B19013_001E.where(z.B19013_001E > 0)
    z["med_age"] = z.B01002_001E.where(z.B01002_001E > 0)
    z["black"] = 100 * z.B03002_004E / z.B03002_001E
    z["hisp"] = 100 * z.B03002_012E / z.B03002_001E
    z["nocar"] = 100 * z.B08201_002E / z.B08201_001E
    z["land_km2"] = z.ALAND / 1e6
    src = [{"kind": "census", "url": REL}, {"kind": "census", "url": GAZ}, {"kind": "census-acs", "url": SF.format(t="<table>"), "tables": ["B01003", "B19013", "B17001", "B01002", "B03002", "B08201", "B09021"], "vintage": "ACS 2019-2023 5-year, table-based summary file"}]
    return z, src


def stores():
    old = socrata.DOMAIN
    socrata.DOMAIN = "https://data.ny.gov"
    try:
        r, s = socrata.query_all("9a8c-vfzj", select="zip_code, estab_type, square_footage",
                                 where="upper(county) in ('BRONX','KINGS','NEW YORK','QUEENS','RICHMOND')", order="license_number")
    finally:
        socrata.DOMAIN = old
    s["kind"] = "data.ny.gov"
    d = pd.DataFrame(r)
    d["sqft"] = pd.to_numeric(d["square_footage"], errors="coerce")
    d["zcta"] = d["zip_code"].astype(str).str[:5]
    d = d[d["estab_type"].astype(str).str.contains("A")]
    out = pd.DataFrame({"stores_all": d.groupby("zcta").size(),
                        "super6k": d[d.sqft >= 6000].groupby("zcta").size(),
                        "super10k": d[d.sqft >= 10000].groupby("zcta").size()}).fillna(0)
    return out.reset_index(), s


def pqi():
    old = socrata.DOMAIN
    socrata.DOMAIN = "https://health.data.ny.gov"
    try:
        yrs, s0 = socrata.query("5q8c-d6xq", select="max(year) as y")
        ymax = int(float(yrs[0]["y"]))
        years = [ymax - 2, ymax - 1, ymax]
        r, s = socrata.query_all("5q8c-d6xq", select="patient_zipcode, year, pqi_number, observed_rate_per_100_000_people, expected_rate_per_100_000_people",
                                 where=f"year in ({','.join(repr(str(y)) for y in years)}) and pqi_number in ('PQI_01','PQI_03','PQI_14','PQI_16','PQI 01','PQI 03','PQI 14','PQI 16')",
                                 order="patient_zipcode, year, pqi_number")
    finally:
        socrata.DOMAIN = old
    s["kind"] = "health.data.ny.gov"
    d = pd.DataFrame(r)
    for c in ("observed_rate_per_100_000_people", "expected_rate_per_100_000_people"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["zcta"] = d["patient_zipcode"].astype(str).str[:5]
    g = d.groupby("zcta")[["observed_rate_per_100_000_people", "expected_rate_per_100_000_people"]].sum()
    g.columns = ["obs", "exp"]
    return g.reset_index(), [s0, s], years, sorted(d["pqi_number"].unique().tolist())


def fit(d, rhs):
    m = smf.wls(f"y ~ {rhs}", data=d, weights=d["pop"]).fit(cov_type="HC3")
    return m


def coef(m, x):
    ci = m.conf_int().loc[x]
    return {"beta": float(m.params[x]), "ratio": float(np.exp(m.params[x])), "lo": float(np.exp(ci[0])),
            "hi": float(np.exp(ci[1])), "se": float(m.bse[x]), "n": int(m.nobs), "r2": float(m.rsquared)}


def main():
    z, src_z = zctas()
    st, src_s = stores()
    pq, src_p, years, pqis = pqi()
    d = z.merge(st, on="zcta", how="left").merge(pq, on="zcta", how="inner")
    for c in ("stores_all", "super6k", "super10k"):
        d[c] = d[c].fillna(0)
    d = d[(d.adults >= 5000) & (d.obs > 0) & (d.exp > 0)].dropna(subset=["poverty", "income", "med_age"])
    d["y"] = np.log(d.obs / d.exp)
    d["x"] = np.log2((d.super6k + 0.5) / d["pop"] * 1e4)
    d["x10"] = np.log2((d.super10k + 0.5) / d["pop"] * 1e4)
    d["xall"] = np.log2((d.stores_all + 0.5) / d["pop"] * 1e4)
    d["xarea"] = np.log2((d.super6k + 0.5) / d.land_km2)
    d["ldens"] = np.log2(d.density)
    d["linc"] = np.log2(d.income)
    base = "ldens + poverty + linc + med_age"
    res = {"years": years, "pqi_numbers": pqis, "n_zcta": int(len(d)),
           "primary": coef(fit(d, f"x + {base}"), "x"),
           "unadjusted": coef(fit(d, "x"), "x"),
           "plus_race": coef(fit(d, f"x + {base} + black + hisp"), "x"),
           "plus_nocar": coef(fit(d, f"x + {base} + nocar"), "x"),
           "sqft10k": coef(fit(d, f"x10 + {base}"), "x10"),
           "all_stores": coef(fit(d, f"xall + {base}"), "xall"),
           "area_unadjusted": coef(fit(d, "xarea"), "xarea"),
           "area_plus_density": coef(fit(d, "xarea + ldens"), "xarea"),
           "area_full": coef(fit(d, f"xarea + {base}"), "xarea"),
           "poverty_per_10pts": coef(fit(d, f"x + {base}"), "poverty"),
           "sources": src_z + [src_s] + src_p}
    res["poverty_per_10pts"] = {k: (float(np.exp(10 * np.log(v))) if k in ("ratio", "lo", "hi") else v) for k, v in res["poverty_per_10pts"].items()}
    d.to_csv(DER / "food_zcta.csv", index=False)
    (DER / "food_access.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "sources"}, indent=1))


if __name__ == "__main__":
    main()
