"""commute-fhv-subway-distance: 2024 app (HVFHV) pickups per resident against distance to the nearest station.

Unit: TLC taxi zone. Registered sample: Bronx, Brooklyn, Queens, Staten Island; airports, unknown zones and
zones under 2,000 residents excluded. See claims/registered/commute-fhv-subway-distance.json.
"""
from __future__ import annotations

import io
import json
import zipfile

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from analyses.commuting import acs_sf
from analyses.commuting.common import DER, fetch, savefig
from analyses.mobility.common import nys
from concord import socrata

NYC = {"36005": "Bronx", "36047": "Brooklyn", "36061": "Manhattan", "36081": "Queens", "36085": "Staten Island"}
PL = "https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/New_York/ny2020.pl.zip"
GAZ = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_gaz_tracts_36.txt"
LODES = "https://lehd.ces.census.gov/data/lodes/LODES8/ny/wac/ny_wac_S000_JT00_2021.csv.gz"
ZONES = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip"
EXCLUDE = {1, 132, 138, 264, 265}


def tracts():
    with zipfile.ZipFile(fetch(PL, "ny2020.pl.zip")) as zf:
        geo = pd.read_csv(io.BytesIO(zf.read("nygeo2020.pl")), sep="|", header=None, dtype=str, encoding="latin-1")
        seg = pd.read_csv(io.BytesIO(zf.read("ny000012020.pl")), sep="|", header=None, dtype=str)
    geo = geo[(geo[2] == "140") & (geo[4] == "00")][[7, 8]].rename(columns={7: "logrecno", 8: "geoid"})
    seg = seg[[4, 5]].rename(columns={4: "logrecno", 5: "pop"})
    t = geo.merge(seg, on="logrecno")
    t["tract"] = t["geoid"].str[-11:]
    t["pop"] = t["pop"].astype(float)
    t = t[t["tract"].str[:5].isin(NYC)]
    gz = pd.read_csv(fetch(GAZ, "2020_gaz_tracts_36.txt"), sep="\t", dtype={"GEOID": str})
    gz.columns = [c.strip() for c in gz.columns]
    t = t.merge(gz[["GEOID", "INTPTLAT", "INTPTLONG"]], left_on="tract", right_on="GEOID")
    acs_cols = {"B19025": ["B19025_E001"], "B11001": ["B11001_E001"], "B08201": ["B08201_E001", "B08201_E002"]}
    srcs = [{"kind": "census-2020-pl94171", "url": PL, "table": "P1_001N (P0010001), summary level 140"},
            {"kind": "census-gazetteer", "url": GAZ, "vintage": "2020 tracts, internal points"}]
    for tab, cols in acs_cols.items():
        a, s = acs_sf.table_2023(tab, cols, "1400000US36")
        a["tract"] = a["GEO_ID"].str[-11:]
        t = t.merge(a[["tract"] + cols], on="tract", how="left")
        srcs.append(s)
    w = pd.read_csv(fetch(LODES, "ny_wac_S000_JT00_2021.csv.gz"), dtype={"w_geocode": str}, usecols=["w_geocode", "C000"])
    w["tract"] = w["w_geocode"].str[:11]
    t = t.merge(w.groupby("tract")["C000"].sum().rename("jobs"), on="tract", how="left").fillna({"jobs": 0})
    srcs.append({"kind": "lehd-lodes", "url": LODES, "vintage": "LODES8 WAC 2021, all jobs (C000), 2020 blocks"})
    g = gpd.GeoDataFrame(t, geometry=gpd.points_from_xy(t["INTPTLONG"], t["INTPTLAT"]), crs=4326)
    return g, srcs


def main():
    sources = []
    tz = gpd.read_file("zip://" + str(fetch(ZONES, "taxi_zones.zip")) + "!taxi_zones/taxi_zones.shp").to_crs(2263)
    tz["LocationID"] = tz["LocationID"].astype(int)
    tz = tz.dissolve(by="LocationID", aggfunc="first").reset_index()
    sources.append({"kind": "tlc-taxi-zones", "url": ZONES, "note": "TLC taxi_zones shapefile"})
    srows, ssrc = nys("39hk-dx4f", select="gtfs_stop_id, complex_id, division, stop_name, borough, gtfs_latitude, gtfs_longitude",
                      limit=5000)
    sources.append(ssrc)
    st = pd.DataFrame(srows)
    st[["gtfs_latitude", "gtfs_longitude"]] = st[["gtfs_latitude", "gtfs_longitude"]].astype(float)
    st = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st["gtfs_longitude"], st["gtfs_latitude"]), crs=4326).to_crs(2263)
    print("stations:", len(st), st["division"].value_counts().to_dict())

    tr, tsrc = tracts()
    sources += tsrc
    tr = tr.to_crs(2263)
    tr = gpd.sjoin(tr, tz[["LocationID", "borough", "geometry"]], how="inner", predicate="within")
    near = gpd.sjoin_nearest(tr[["tract", "geometry"]], st[["stop_name", "geometry"]], distance_col="d_ft")
    near = near.groupby("tract")["d_ft"].min()
    tr["dist_km"] = tr["tract"].map(near) * 0.3048 / 1000
    tr["pd"] = tr["pop"] * tr["dist_km"]
    ok = tr["B19025_E001"].notna() & tr["B11001_E001"].notna()  # income only where both are reported
    tr["inc_ok"] = tr["B19025_E001"].where(ok)
    tr["hh_ok"] = tr["B11001_E001"].where(ok)
    z = tr.groupby("LocationID").agg(pop=("pop", "sum"), pd=("pd", "sum"), inc=("inc_ok", "sum"),
                                     hh=("hh_ok", "sum"), hhv=("B08201_E001", "sum"), novehicle=("B08201_E002", "sum"),
                                     jobs=("jobs", "sum"), n_tracts=("tract", "count"))
    z["dist_km"] = z["pd"] / z["pop"]
    z["mean_hh_income"] = (z["inc"] / z["hh"]).where(z["hh"] > 0)
    z["no_vehicle_pct"] = 100 * z["novehicle"] / z["hhv"]
    z["jobs_per_res"] = z["jobs"] / z["pop"]

    rows, src = socrata.query("c5iv-bn4s", select="industry, pickup_dropoff, locationid, sum(trip_count) as n",
                              where="metric_month >= '2024-01-01' and metric_month < '2025-01-01'",
                              group="industry, pickup_dropoff, locationid")
    sources.append(src)
    months, msrc = socrata.query("c5iv-bn4s", select="metric_month, count(*) as n",
                                 where="metric_month >= '2024-01-01' and metric_month < '2025-01-01'", group="metric_month")
    print("months in 2024:", len(months), sorted(m["metric_month"][:7] for m in months))
    t = pd.DataFrame(rows)
    t["n"] = t["n"].astype(float)
    t["locationid"] = pd.to_numeric(t["locationid"], errors="coerce")
    print(t.groupby(["industry", "pickup_dropoff"])["n"].sum())
    piv = t.pivot_table(index="locationid", columns=["industry", "pickup_dropoff"], values="n", aggfunc="sum").fillna(0)
    piv.columns = [f"{a}|{b}" for a, b in piv.columns]
    hv = [c for c in piv.columns if "High Volume" in c]
    pick = [c for c in hv if "ick" in c][0]
    drop = [c for c in hv if "rop" in c][0]
    taxi_pick = [c for c in piv.columns if ("Yellow" in c or "Green" in c) and "ick" in c]
    z["hv_pickups"] = piv[pick].reindex(z.index).fillna(0)
    z["hv_dropoffs"] = piv[drop].reindex(z.index).fillna(0)
    z["taxi_pickups"] = piv[taxi_pick].sum(axis=1).reindex(z.index).fillna(0)
    z = z.join(tz.set_index("LocationID")[["zone", "borough"]])
    z["pickups_per_res"] = z["hv_pickups"] / z["pop"]
    z.drop(columns=["pd"]).to_csv(DER / "fhv_subway_zones.csv", float_format="%.4f")

    base = z[~z.index.isin(EXCLUDE) & (z["pop"] >= 2000)].copy()
    for c in ["pickups_per_res", "dist_km", "mean_hh_income", "jobs_per_res"]:
        base[f"l_{c}"] = np.log(base[c])
    base["l_jobs1"] = np.log(1 + base["jobs_per_res"])
    base["l_drop"] = np.log(base["hv_dropoffs"] / base["pop"])
    base["l_taxi"] = np.log((base["taxi_pickups"] + 1) / base["pop"])
    outer = base[base["borough"] != "Manhattan"].copy()
    cov = "l_mean_hh_income + l_jobs1"
    fit = lambda f, data=outer: smf.ols(f, data=data).fit(cov_type="HC3")

    def el(m, term="l_dist_km"):
        b, se = m.params[term], m.bse[term]
        return {"elasticity": float(b), "lo": float(b - 1.96 * se), "hi": float(b + 1.96 * se),
                "p": float(m.pvalues[term]), "n": int(m.nobs), "r2": float(m.rsquared)}

    res = {
        "primary": el(fit(f"l_pickups_per_res ~ l_dist_km + {cov}")),
        "unadjusted": el(fit("l_pickups_per_res ~ l_dist_km")),
        "plus_no_vehicle": el(fit(f"l_pickups_per_res ~ l_dist_km + {cov} + no_vehicle_pct")),
        "borough_fe": el(fit(f"l_pickups_per_res ~ l_dist_km + {cov} + C(borough)")),
        "dropoffs": el(fit(f"l_drop ~ l_dist_km + {cov}")),
        "all_boroughs": el(fit(f"l_pickups_per_res ~ l_dist_km + {cov}", base)),
        "yellow_green_pickups": el(fit(f"l_taxi ~ l_dist_km + {cov}")),
        "income_coef": el(fit(f"l_pickups_per_res ~ l_dist_km + {cov}"), "l_mean_hh_income"),
        "no_vehicle_coef": el(fit(f"l_pickups_per_res ~ l_dist_km + {cov} + no_vehicle_pct"), "no_vehicle_pct"),
    }
    for b in ["Bronx", "Brooklyn", "Queens", "Staten Island"]:
        sub = outer[outer["borough"] == b]
        if len(sub) > 8:
            res[f"within_{b}"] = el(fit(f"l_pickups_per_res ~ l_dist_km + {cov}", sub))
    for k, v in res.items():
        print(f"{k:22s} {v['elasticity']:+.3f} ({v['lo']:+.3f} to {v['hi']:+.3f}) p={v['p']:.3g} R2={v['r2']:.2f} n={v['n']}")
    desc = outer[["pickups_per_res", "dist_km", "mean_hh_income", "jobs_per_res", "no_vehicle_pct", "pop"]].describe().round(3)
    print(desc)
    print(outer.groupby("borough")[["pickups_per_res", "dist_km", "no_vehicle_pct"]].median().round(2))
    corr = outer[["l_pickups_per_res", "l_dist_km", "l_mean_hh_income", "l_jobs1", "no_vehicle_pct"]].corr().round(3)
    print(corr)
    out = {"results": res, "describe_outer": desc.to_dict(), "corr_outer": corr.to_dict(),
           "n_zones_outer": int(len(outer)), "n_stations": int(len(st)), "sources": sources}
    (DER / "fhv_subway_results.json").write_text(json.dumps(out, indent=1, default=str))

    # ---- figure
    fig = plt.figure(figsize=(13, 5.8))
    ax = fig.add_axes([0.0, 0.02, 0.52, 0.9])
    m = tz.merge(z[["pickups_per_res"]], left_on="LocationID", right_index=True, how="left")
    m.loc[m["LocationID"].isin(EXCLUDE) | m["LocationID"].map(z["pop"]).lt(2000), "pickups_per_res"] = np.nan
    m["v"] = np.log10(m["pickups_per_res"])
    m.loc[m["LocationID"] == 199, "v"] = np.nan  # Rikers Island: jail population, no households
    m.plot(column="v", cmap="magma_r", ax=ax, edgecolor="white", lw=0.25, legend=True, vmin=0.5, vmax=2.0,
           legend_kwds={"label": "App pickups per resident, 2024 (log10)", "shrink": 0.6},
           missing_kwds={"color": "#e6e6e6"})
    st.plot(ax=ax, color="#1f6fb2", markersize=1.6)
    ax.set_axis_off()
    ax.set_title("(a) High-volume for-hire pickups per resident by taxi zone; blue dots are stations;\nManhattan shown but not in the registered sample; grey: excluded", fontsize=10)
    ax = fig.add_axes([0.6, 0.12, 0.38, 0.75])
    rx = smf.ols(f"l_dist_km ~ {cov}", outer).fit().resid + outer["l_dist_km"].mean()
    ry = smf.ols(f"l_pickups_per_res ~ {cov}", outer).fit().resid + outer["l_pickups_per_res"].mean()
    cols = {"Bronx": "#c0392b", "Brooklyn": "#2c3e50", "Queens": "#16a085", "Staten Island": "#8e44ad"}
    for b, col in cols.items():
        k = outer["borough"] == b
        ax.scatter(np.exp(rx[k]), np.exp(ry[k]), s=10, color=col, alpha=0.35, label=b)
    bins = pd.qcut(rx, 10)
    bx = np.exp(rx.groupby(bins, observed=True).mean())
    by = np.exp(ry.groupby(bins, observed=True).mean())
    ax.plot(bx, by, "o", color="k", ms=6, label="decile bins (adjusted)")
    e = res["primary"]
    xx = np.linspace(rx.min(), rx.max(), 50)
    ax.plot(np.exp(xx), np.exp(ry.mean() + e["elasticity"] * (xx - rx.mean())), color="k", lw=1,
            label=f"adjusted elasticity {e['elasticity']:+.2f} ({e['lo']:+.2f} to {e['hi']:+.2f})")
    ax.set_xscale("log")
    ax.set_yscale("log")
    from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator
    ax.xaxis.set_major_locator(FixedLocator([0.2, 0.5, 1, 2, 5]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels(["0.2", "0.5", "1", "2", "5"])
    ax.yaxis.set_major_locator(FixedLocator([3, 5, 10, 20, 50, 100]))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_yticklabels(["3", "5", "10", "20", "50", "100"])
    ax.set_xlabel("Population-weighted distance to nearest station, km (adjusted)")
    ax.set_ylabel("App pickups per resident, 2024 (adjusted)")
    e = res["primary"]
    ax.set_title(f"(b) Outer-borough zones (n = {e['n']}), adjusted for income and jobs", fontsize=10)
    ax.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3)
    fig.suptitle("Ride-hail pickups and distance to the subway (TLC c5iv-bn4s, 2024; MTA 39hk-dx4f; Census 2020; ACS 2019-23; LODES 2021)", fontsize=9, y=1.06)
    print(savefig(fig, "fhv_pickups_subway_distance.png"))


if __name__ == "__main__":
    main()
