"""Outcome analysis for levers-vacant-lot-trial-match (registered at commit 2a7c4b4).

Inputs: data/derived/levers/lots_records.csv (lots_fetch.py), lots_naip.csv (lot_ndvi.py),
shootings_2023_2025.csv (city_metrics.py). Writes data/derived/levers/lot_test_results.json and lot_types.csv.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "levers"
FT = 300 / 0.3048          # 300 m in feet (EPSG:2263)


def load_shootings(path):
    """Shooting points. In 5ucz-vwe8 as fetched on 13 November 2026 the latitude and longitude columns are
    swapped (latitude holds values near -74), so they are swapped back when that is the case."""
    sh = pd.read_csv(path).drop_duplicates("incident_key").dropna(subset=["latitude", "longitude"])
    if sh.latitude.median() < 0:
        sh = sh.rename(columns={"latitude": "longitude", "longitude": "latitude"})
    return sh


def naip_class(v):
    if not np.isfinite(v):
        return "no_image"
    return "vegetated" if v >= 0.5 else ("mixed" if v >= 0.2 else "bare_or_paved")


def buffered_shootings(lots: pd.DataFrame, sh: gpd.GeoDataFrame) -> float:
    g = gpd.GeoSeries(gpd.points_from_xy(lots.longitude, lots.latitude), crs=4326).to_crs(2263)
    u = g.buffer(FT).union_all()
    return int(sh.within(u).sum())


def main():
    rec = pd.read_csv(D / "lots_records.csv", dtype={"bbl": str})
    nai = pd.read_csv(D / "lots_naip.csv", dtype={"bbl": str})[["bbl", "n_px", "ndvi_median", "veg_share", "brightness", "naip_item"]]
    df = rec.merge(nai, on="bbl", how="left")
    df["naip_class"] = df.veg_share.map(lambda v: naip_class(v) if pd.notna(v) else "not_read")
    hs = df[df.high_shooting]
    n_hs = len(hs)
    types = hs.groupby(["type", "small", "naip_class"]).size().rename("n").reset_index()
    types.to_csv(D / "lot_types.csv", index=False)

    idle = hs.type.isin(["private_idle", "city_interim"])
    small = hs.small
    veg = hs.veg_share >= 0.2
    trial = hs[idle & small & veg]
    trial_noimg = hs[idle & small]
    broad = hs[hs.type.isin(["private_idle", "city_interim", "stalled"]) & small & veg]

    sh = load_shootings(D / "shootings_2023_2025.csv")
    shg = gpd.GeoSeries(gpd.points_from_xy(sh.longitude, sh.latitude), crs=4326).to_crs(2263)
    near = buffered_shootings(trial, shg)
    per_year = near / 3
    g = {"greening": (6.8, 2.7, 10.6), "cleanup": (9.2, 4.8, 13.2)}
    prevented = {k: {"estimate": round(per_year * a / 100, 1), "lo": round(per_year * lo / 100, 1), "hi": round(per_year * hi / 100, 1)}
                 for k, (a, lo, hi) in g.items()}
    near_all = buffered_shootings(hs[idle & small], shg) / 3

    res = {
        "n_lu11_lots_citywide": int(len(df)),
        "n_lu11_in_high_shooting_tracts": int(n_hs),
        "high_shooting_tracts": "top decile of 2,208 tracts by shootings 2019-2024 (>= 10), 235 tracts with ties, 51% of shootings",
        "by_type_high_shooting": hs.type.value_counts().to_dict(),
        "small_by_type_high_shooting": hs[small].type.value_counts().to_dict(),
        "naip_read": int(hs.n_px.fillna(0).gt(0).sum()),
        "naip_class_of_small_idle": hs[idle & small].naip_class.value_counts().to_dict(),
        "trial_like_n": int(len(trial)),
        "trial_like_share": round(len(trial) / n_hs, 3),
        "trial_like_without_imagery_n": int(len(trial_noimg)),
        "trial_like_with_stalled_n": int(len(broad)),
        "trial_like_by_owner": trial.ownertype.fillna("private").replace({"C": "city"}).value_counts().to_dict(),
        "trial_like_by_borough": trial.borough.value_counts().to_dict(),
        "trial_like_area_m2_total": round(float(trial.lotarea.sum() * 0.092903)),
        "shootings_within_300m_trial_like_per_year": round(per_year, 1),
        "shootings_within_300m_small_idle_any_cover_per_year": round(near_all, 1),
        "shootings_citywide_per_year_2023_2025": round(len(sh) / 3, 1),
        "prevented_per_year": prevented,
        "cost_initial_usd": round(float(trial.lotarea.sum() * 0.092903 * 5)),
        "cost_maintenance_usd_per_year": round(float(trial.lotarea.sum() * 0.092903 * 0.5)),
    }
    res["reach_summary"] = {"value": res["trial_like_n"], "unit": "vacant lots in high-shooting tracts that resemble the Philadelphia trial lots (registered test)"}
    (D / "lot_test_results.json").write_text(json.dumps(res, indent=1, default=int))
    print(json.dumps(res, indent=1, default=int))


if __name__ == "__main__":
    main()
