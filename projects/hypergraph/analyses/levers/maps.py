"""Maps for the three place-targetable levers that rank highest (exploratory, not registered).

1. Vacant-lot greening: shootings 2023-2025 by 2020 tract; vacant lots by type; trial-like lots.
2. Housing repair: asthma ED visits, children 5-17, rate by community district (EHDP); buildings with open class C
   HPD violations per district.
3. Speed humps: pedestrian injury crashes 2023-2025; speed-reducer locations found feasible and not yet installed.
Writes figures/levers/*.png (sRGB) and data/derived/levers/maps_summary.json.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402

D = ROOT / "data" / "derived" / "levers"
FIG = ROOT / "figures" / "levers"
EHDP = Path.home() / "opt" / "nyc-concordance" / "ehdp"
S: dict = {}
SRC: dict = {}


def load_shootings(path):
    """Shooting points. In 5ucz-vwe8 as fetched on 13 November 2026 the latitude and longitude columns are
    swapped (latitude holds values near -74), so they are swapped back when that is the case."""
    sh = pd.read_csv(path).drop_duplicates("incident_key").dropna(subset=["latitude", "longitude"])
    if sh.latitude.median() < 0:
        sh = sh.rename(columns={"latitude": "longitude", "longitude": "latitude"})
    return sh


def tag(p):
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(p)],
                   capture_output=True)


def base(ax):
    ax.set_axis_off()
    ax.set_aspect("equal")


def greening():
    tr = gpd.read_file(ROOT / "data/derived/neighbourhood/tracts.geojson").to_crs(2263)
    sh = load_shootings(D / "shootings_2023_2025.csv")
    shg = gpd.GeoDataFrame(sh, geometry=gpd.points_from_xy(sh.longitude, sh.latitude), crs=4326).to_crs(2263)
    j = gpd.sjoin(shg, tr[["geometry"]], predicate="within")
    tr["shoot"] = j.groupby("index_right").size().reindex(tr.index).fillna(0) / 3
    lots = pd.read_csv(D / "lots_records.csv", dtype={"bbl": str})
    nai = pd.read_csv(D / "lots_naip.csv", dtype={"bbl": str})[["bbl", "veg_share"]]
    lots = lots.merge(nai, on="bbl", how="left")
    lg = gpd.GeoDataFrame(lots, geometry=gpd.points_from_xy(lots.longitude, lots.latitude), crs=4326).to_crs(2263)
    trial = lg[lg.high_shooting & lg.small & lg["type"].isin(["private_idle", "city_interim"]) & (lg.veg_share >= 0.2)]
    fig, ax = plt.subplots(figsize=(9, 9))
    tr.plot(column="shoot", ax=ax, cmap="Reds", vmin=0, vmax=np.nanpercentile(tr.shoot, 99), linewidth=0,
            legend=True, legend_kwds={"label": "shooting incidents a year, 2023-2025, per tract", "shrink": 0.5})
    lg.plot(ax=ax, color="#888888", markersize=0.3, alpha=0.5)
    trial.plot(ax=ax, color="#1f5fa8", markersize=2.5)
    base(ax)
    ax.set_title("Vacant lots (grey, 24,663) and lots like the Philadelphia trial's (blue)\nagainst shootings per tract", fontsize=10)
    p = FIG / "map_greening.png"
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig); tag(p)
    # how concentrated: share of LU11 lots in tracts holding the top half of shootings
    S["greening"] = {"lu11_lots_in_high_shooting_tracts_share": round(float(lots.high_shooting.mean()), 3),
                     "trial_like": int(len(trial))}


def housing():
    tp = {t["TimePeriodID"]: t for t in json.load(open(EHDP / "TimePeriods.json"))}
    d = pd.DataFrame(json.load(open(EHDP / "2379.json")))
    d = d[(d.MeasureID == 1196) & (d.GeoType == "CD")]
    d["yr"] = d.TimePeriodID.map(lambda i: tp[i]["TimePeriod"])
    d = d[d.TimePeriodID.map(lambda i: tp[i]["TimeType"] == "year")]
    last = d.yr.astype(int).max()
    d = d[d.yr.astype(int) == last][["GeoID", "Value"]].rename(columns={"GeoID": "cd", "Value": "asthma_rate"})
    rows, src = socrata.query("wvxf-dwi5", select="boroid,communityboard,count(distinct buildingid) as b",
                              where="violationstatus='Open' and class='C'", group="boroid,communityboard")
    SRC["hpd_open_c_by_cd"] = src
    h = pd.DataFrame(rows)
    h["cd"] = pd.to_numeric(h.boroid) * 100 + pd.to_numeric(h.communityboard)
    h["b"] = pd.to_numeric(h.b)
    m = d.merge(h[["cd", "b"]], on="cd", how="inner")
    cdg = gpd.read_file(ROOT / "data/derived/heat/ehdp/CD.geojson")
    idcol = [c for c in cdg.columns if c.lower() in ("geoid", "borocd", "cd", "geocode")][0]
    cdg["cd"] = pd.to_numeric(cdg[idcol])
    cdg = cdg.merge(m, on="cd", how="left").to_crs(2263)
    fig, ax = plt.subplots(figsize=(9, 9))
    cdg.plot(column="asthma_rate", ax=ax, cmap="Purples", legend=True, linewidth=0.3, edgecolor="white",
             legend_kwds={"label": f"asthma ED visits per 10,000 children aged 5-17, {last}", "shrink": 0.5})
    c = cdg.copy(); c["geometry"] = c.representative_point()
    c.plot(ax=ax, markersize=c.b / 40, facecolor="none", edgecolor="#b8860b", linewidth=0.8)
    base(ax)
    ax.set_title("Asthma ED visits (shade) and buildings with open class C\nHPD violations (circles), by community district", fontsize=10)
    p = FIG / "map_housing.png"
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig); tag(p)
    rho = m[["asthma_rate", "b"]].rank().corr().iloc[0, 1]
    top = m.sort_values("asthma_rate", ascending=False).head(12)
    S["housing"] = {"year": int(last), "n_cd": int(len(m)), "spearman_asthma_vs_classC_buildings": round(float(rho), 2),
                    "classC_buildings_in_12_highest_asthma_cds_share": round(float(top.b.sum() / m.b.sum()), 3),
                    "asthma_id_col": idcol}


def humps():
    rows, src = socrata.query("9n6h-pt9g", select="projectstatus,fromlatitude,fromlongitude,tolatitude,tolongitude,borough",
                              where="projectstatus in ('BC prioritized installation queue','Accept planning proposal of Feasible','Planning proposal - Feasible')")
    SRC["srts_feasible"] = src
    q = pd.DataFrame(rows)
    for c in ("fromlatitude", "fromlongitude", "tolatitude", "tolongitude"):
        q[c] = pd.to_numeric(q[c], errors="coerce")
    q["lat"] = q[["fromlatitude", "tolatitude"]].mean(axis=1)
    q["lon"] = q[["fromlongitude", "tolongitude"]].mean(axis=1)
    q = q.dropna(subset=["lat", "lon"])
    q = q[(q.lat > 40.4) & (q.lon < -73.6)]
    rows, src = socrata.query_all("h9gi-nx95", select="collision_id,latitude,longitude,number_of_pedestrians_injured,number_of_pedestrians_killed",
                                  where="crash_date >= '2023-01-01T00:00:00' and crash_date < '2026-01-01T00:00:00' and (number_of_pedestrians_injured > 0 or number_of_pedestrians_killed > 0)")
    SRC["ped_crashes"] = src
    c = pd.DataFrame(rows)
    for k in ("latitude", "longitude"):
        c[k] = pd.to_numeric(c[k], errors="coerce")
    c = c[(c.latitude > 40.4) & (c.longitude < -73.6)]
    cg = gpd.GeoSeries(gpd.points_from_xy(c.longitude, c.latitude), crs=4326).to_crs(2263)
    qg = gpd.GeoSeries(gpd.points_from_xy(q.lon, q.lat), crs=4326).to_crs(2263)
    near_q = cg.within(qg.buffer(100 / 0.3048).union_all())
    fig, ax = plt.subplots(figsize=(9, 9))
    hb = ax.hexbin(cg.x, cg.y, gridsize=90, cmap="Oranges", mincnt=1, bins="log")
    fig.colorbar(hb, ax=ax, shrink=0.5, label="crashes injuring or killing a pedestrian, 2023-2025 (log)")
    ax.scatter(qg.x, qg.y, s=3, c="#1f5fa8")
    base(ax)
    ax.set_title("Pedestrian injury crashes (hexagons) and speed-reducer locations\nfound feasible but not installed (blue)", fontsize=10)
    p = FIG / "map_humps.png"
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig); tag(p)
    S["humps"] = {"feasible_locations": int(len(q)), "ped_crashes_2023_2025": int(len(c)),
                  "ped_crashes_within_100m_of_feasible_location_share": round(float(near_q.mean()), 3)}


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    greening(); housing(); humps()
    (D / "maps_summary.json").write_text(json.dumps({"summary": S, "sources": SRC}, indent=1, default=str))
    print(json.dumps(S, indent=1))


if __name__ == "__main__":
    main()
