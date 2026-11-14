"""Registered test all-boats-trees-rent, with a declared secondary on violent crime.

Question: did census tracts that gained more street trees between the 2005 and 2015
censuses see rents rise faster between ACS 2008-12 and ACS 2018-22, and did violent crime
fall faster there between 2006-08 and 2016-18?

Usage:
  tree_test.py --dry    replaces both outcomes with simulated noise (seed 20261113) that has
                        the marginal spread of the real outcome and no relation to trees. It
                        gives the standard error the design can reach. It reads no crime data.
  tree_test.py          fetches crime, runs the registered models, writes results.

Unit: 2020 census tracts with ACS population of at least 500, both median rents present
and neither top-coded (2008-12 below 2,000 dollars, 2018-22 below 3,500 dollars).
Exposure: change in living street trees, 2015 minus 2005, in hundreds of trees (dt100).
Primary model (rent): OLS of d_logrent on dt100 + trees2005 per km2 + log rent 2008-12 +
  non-Hispanic white share 2008-12 + log population density 2008-12 + borough; standard
  errors clustered by 2020 NTA. No resampling, so no seed.
Secondary model (crime): Poisson regression of the 2016-18 count of murders, robberies and
  felony assaults (NYPD complaints, offence codes 101, 105, 106) on dt100 + log(1 + count
  2006-08) + the same covariates; clustered by NTA.
Sensitivities (fixed here): (a) without log rent 2008-12; (b) adding the 2018-22 poverty rate;
  (c) exposure as log((trees2015+10)/(trees2005+10)); (d) tracts with at least 50 trees in
  2005; (e) crime limited to premises type STREET.
Distribution: the primary and secondary slopes within thirds of 2008-12 median rent.
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.formula.api as smf
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "data/derived/all_boats"
DRY = "--dry" in sys.argv
EARLY, LATE = (2006, 2008), (2016, 2018)


def base():
    t = pd.read_csv(OUT / "tree_counts_tracts.csv", dtype={"geoid": str})
    a = pd.read_csv(ROOT / "data/derived/neighbourhood/tracts_acs.csv", dtype={"GEOID": str})
    d = t.merge(a, left_on="geoid", right_on="GEOID")
    d = d[(d["pop"] >= 500) & d.rent12.notna() & d.rent22.notna() & (d.rent12 < 2000) & (d.rent22 < 3500) & (d.pop12 > 0) & (d.land_km2 > 0)].copy()
    d["dt100"] = (d.trees2015 - d.trees2005) / 100
    d["dlogtrees"] = np.log((d.trees2015 + 10) / (d.trees2005 + 10))
    d["trees05_km"] = d.trees2005 / d.land_km2 / 1000
    d["lrent12"] = np.log(d.rent12)
    d["ldens12"] = np.log(d.pop12 / d.land_km2)
    d["boro"] = d.borocode.astype(str)
    d["third"] = pd.qcut(d.rent12, 3, labels=["low", "mid", "high"]).astype(str)
    return d


def crime():
    """Counts of murder, robbery and felony assault complaints per tract and period."""
    import geopandas as gpd
    from concord import socrata
    tr = gpd.read_file(ROOT / "data/derived/neighbourhood/tracts.geojson")[["geoid", "geometry"]]
    out, srcs = {}, []
    for name, (y0, y1) in (("early", EARLY), ("late", LATE)):
        rows, src = socrata.query_all(
            "qgea-i56i", select="latitude,longitude,prem_typ_desc",
            where=f"ky_cd in (101,105,106) and cmplnt_fr_dt between '{y0}-01-01T00:00:00' and '{y1}-12-31T23:59:59' and latitude is not null")
        srcs.append(src)
        p = pd.DataFrame(rows)
        p["latitude"], p["longitude"] = p.latitude.astype(float), p.longitude.astype(float)
        g = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p.longitude, p.latitude), crs=4326)
        j = gpd.sjoin(g, tr, predicate="within", how="inner")
        out[f"viol_{name}"] = j.groupby("geoid").size()
        out[f"street_{name}"] = j[j.prem_typ_desc == "STREET"].groupby("geoid").size()
    c = pd.DataFrame(out).fillna(0).astype(int).reset_index().rename(columns={"index": "geoid"})
    c.to_csv(OUT / "violent_crime_tracts.csv", index=False)
    (OUT / "crime_sources.json").write_text(json.dumps(srcs, indent=1))
    return c


def fit_rent(d, x="dt100", extra="", drop_base=False):
    f = f"d_logrent ~ {x} + trees05_km + nhw_share12 + ldens12 + C(boro)" + ("" if drop_base else " + lrent12") + extra
    m = smf.ols(f, d).fit(cov_type="cluster", cov_kwds={"groups": d.nta2020})
    lo, hi = m.conf_int().loc[x]
    return {"estimate": float(m.params[x]), "se": float(m.bse[x]), "lo": float(lo), "hi": float(hi), "n": int(m.nobs)}


def fit_crime(d, y="viol", x="dt100"):
    d = d.assign(lbase=np.log1p(d[f"{y}_early"]))
    m = smf.poisson(f"{y}_late ~ {x} + lbase + trees05_km + lrent12 + nhw_share12 + ldens12 + C(boro)", d).fit(
        disp=0, cov_type="cluster", cov_kwds={"groups": d.nta2020})
    lo, hi = m.conf_int().loc[x]
    return {"estimate": float(m.params[x]), "se": float(m.bse[x]), "lo": float(lo), "hi": float(hi), "n": int(m.nobs)}


def main():
    d = base()
    if DRY:
        rng = np.random.default_rng(20261113)
        sd = float(d.d_logrent.std())
        ses, sec = [], []
        for _ in range(200):
            d["d_logrent"] = rng.normal(0.38, sd, len(d))
            ses.append(fit_rent(d)["se"])
            base_n = rng.poisson(55, len(d)) + 1
            d["viol_early"] = base_n
            d["viol_late"] = rng.poisson(base_n * 0.82 * np.exp(rng.normal(0, 0.25, len(d))))
            sec.append(fit_crime(d)["se"])
        res = {"n": len(d), "sd_dt100": float(d.dt100.std()), "sd_outcome_marginal": sd,
               "se_rent_slope_per_100_trees": float(np.mean(ses)), "se_crime_slope_per_100_trees": float(np.mean(sec)),
               "note": "simulated outcomes with no relation to trees; crime simulated as Poisson with mean 55 per tract and log-normal trend spread 0.25"}
        (OUT / "tree_test_power.json").write_text(json.dumps(res, indent=1))
        print(json.dumps(res, indent=1))
        return
    c = crime()
    d = d.merge(c, on="geoid", how="left").fillna({k: 0 for k in ("viol_early", "viol_late", "street_early", "street_late")})
    res = {"n": len(d), "rent_primary": fit_rent(d), "crime_secondary": fit_crime(d),
           "sens": {"rent_no_baseline_rent": fit_rent(d, drop_base=True), "rent_plus_poverty": fit_rent(d[d.poverty.notna()], extra=" + poverty"),
                    "rent_log_exposure": fit_rent(d, x="dlogtrees"), "rent_min50_trees": fit_rent(d[d.trees2005 >= 50]),
                    "crime_street_only": fit_crime(d, y="street"), "crime_log_exposure": fit_crime(d, x="dlogtrees")},
           "by_rent_third": {t: {"rent": fit_rent(d[d.third == t]), "crime": fit_crime(d[d.third == t]),
                                 "mean_dt100": float(d[d.third == t].dt100.mean())} for t in ("low", "mid", "high")},
           "descriptive": {"mean_dt100": float(d.dt100.mean()), "sd_dt100": float(d.dt100.std()),
                           "viol_early_total": int(d.viol_early.sum()), "viol_late_total": int(d.viol_late.sum())}}
    (OUT / "tree_test_results.json").write_text(json.dumps(res, indent=1))
    d[["geoid", "nta2020", "boro", "third", "trees2005", "trees2015", "dt100", "d_logrent", "viol_early", "viol_late", "street_early", "street_late"]].to_csv(OUT / "tree_test_tracts.csv", index=False)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
