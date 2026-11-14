"""Point-in-polygon assignment to 2020 census tracts (from tracts.geojson written by base.py)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TRACTS = ROOT / "data" / "derived" / "neighbourhood" / "tracts.geojson"


@lru_cache(maxsize=1)
def tracts() -> gpd.GeoDataFrame:
    g = gpd.read_file(TRACTS)
    g = g.set_crs(4326, allow_override=True)
    return g


def points_to_tracts(lon, lat) -> np.ndarray:
    """Return the 2020 tract GEOID for each point (None if outside every tract)."""
    t = tracts()[["geoid", "geometry"]]
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon, lat), crs=4326)
    j = gpd.sjoin(pts, t, how="left", predicate="within")
    j = j[~j.index.duplicated(keep="first")]
    return j["geoid"].values
