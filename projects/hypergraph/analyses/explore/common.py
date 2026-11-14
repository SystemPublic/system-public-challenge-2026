"""Shared helpers for the exploration scripts: paths, NTA geography, PLUTO loading, point assignment."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = Path.home() / "opt" / "nyc-concordance" / "explore"
OUT = ROOT / "data" / "derived" / "explore"
FIG = ROOT / "figures" / "explore"
TRACTS = ROOT / "data" / "derived" / "neighbourhood" / "tracts.geojson"
TRACTS_ACS = ROOT / "data" / "derived" / "neighbourhood" / "tracts_acs.csv"
BORO = {"MN": "1", "BX": "2", "BK": "3", "QN": "4", "SI": "5"}
BORONAME = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}


@lru_cache(maxsize=1)
def tracts() -> gpd.GeoDataFrame:
    g = gpd.read_file(TRACTS).set_crs(4326, allow_override=True)
    return g


@lru_cache(maxsize=1)
def tract_table() -> pd.DataFrame:
    t = pd.read_csv(TRACTS_ACS, dtype={"GEOID": str, "boroct2020": str, "borocode": str})
    return t


@lru_cache(maxsize=1)
def ntas() -> gpd.GeoDataFrame:
    """2020 Neighborhood Tabulation Areas, dissolved from the 2020 tracts (EPSG:2263, feet)."""
    g = tracts()
    col = "nta2020" if "nta2020" in g.columns else "nta"
    name = "ntaname"
    d = g.to_crs(2263).dissolve(by=col, aggfunc={name: "first", "boroname": "first"}).reset_index()
    d = d.rename(columns={col: "nta", name: "name", "boroname": "boro"})
    d["km2"] = d.geometry.area * 0.3048 ** 2 / 1e6
    return d


def points_to_nta(lon, lat) -> np.ndarray:
    """NTA code for each point (None outside the city)."""
    n = ntas()[["nta", "geometry"]]
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(np.asarray(lon, float), np.asarray(lat, float)), crs=4326).to_crs(2263)
    j = gpd.sjoin(pts, n, how="left", predicate="within")
    j = j[~j.index.duplicated(keep="first")]
    return j["nta"].values


def xy_to_nta(x, y) -> np.ndarray:
    n = ntas()[["nta", "geometry"]]
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(np.asarray(x, float), np.asarray(y, float)), crs=2263)
    j = gpd.sjoin(pts, n, how="left", predicate="within")
    j = j[~j.index.duplicated(keep="first")]
    return j["nta"].values


@lru_cache(maxsize=1)
def nta_pop() -> pd.DataFrame:
    """Population and ACS 2018-2022 / 2008-2012 measures per NTA, aggregated from tracts.
    Medians (rent) are population-weighted means of tract medians, an approximation."""
    t = tract_table().copy()
    t["nta"] = t["nta2020"]

    def wmean(g, c):
        m = g[c].notna() & (g["pop"] > 0)
        return np.average(g.loc[m, c], weights=g.loc[m, "pop"]) if m.any() else np.nan

    rows = []
    for nta, g in t.groupby("nta"):
        rows.append({"nta": nta, "pop": g["pop"].sum(), "pov_below": g["pov_below"].sum(), "pov_univ": g["pov_univ"].sum(),
                     "nhw22": g["nhw22"].sum(), "tot22": g["tot22"].sum(), "nhw12": g["nhw12"].sum(), "tot12": g["tot12"].sum(),
                     "rent22": wmean(g, "rent22"), "rent12": wmean(g, "rent12")})
    d = pd.DataFrame(rows)
    d["poverty"] = d.pov_below / d.pov_univ
    d["nhw_share22"] = d.nhw22 / d.tot22
    d["d_nhw"] = d.nhw22 / d.tot22 - d.nhw12 / d.tot12
    d["d_logrent"] = np.log(d.rent22 / d.rent12)
    return d


def norm_street(s: str) -> str:
    s = re.sub(r"\s+", " ", str(s).upper().strip())
    s = s.replace(" AVE ", " AVENUE ").replace(" ST ", " STREET ")
    s = re.sub(r"\bAVE$", "AVENUE", s)
    s = re.sub(r"\bST$", "STREET", s)
    s = re.sub(r"\bBLVD$", "BOULEVARD", s)
    s = re.sub(r"\bPL$", "PLACE", s)
    s = re.sub(r"\bRD$", "ROAD", s)
    s = re.sub(r"(\d+)(ST|ND|RD|TH)\b", r"\1", s)
    return s


ADDR_RE = re.compile(r"^\d[\d\-/]*[A-Z]?\s+(?:1/2\s+)?(.*)$")


def address_street(a: str) -> str:
    a = re.sub(r"\s+", " ", str(a).upper().strip())
    m = ADDR_RE.match(a)
    return norm_street(m.group(1) if m else a)


@lru_cache(maxsize=1)
def pluto() -> pd.DataFrame:
    """Current PLUTO (selected columns) with state-plane coordinates in feet and NTA."""
    from pyproj import Transformer
    p = pd.read_csv(RAW / "pluto" / "pluto_current.csv", dtype=str)
    for c in ("lotarea", "bldgarea", "numfloors", "unitsres", "unitstotal", "yearbuilt", "latitude", "longitude"):
        p[c] = pd.to_numeric(p[c], errors="coerce")
    p["bbl"] = p["bbl"].str.split(".").str[0]
    p["boro"] = p["bbl"].str[0]
    tr = Transformer.from_crs(4326, 2263, always_xy=True)
    ok = p.latitude.notna()
    x, y = tr.transform(p.loc[ok, "longitude"].values, p.loc[ok, "latitude"].values)
    p["x"] = np.nan
    p["y"] = np.nan
    p.loc[ok, "x"] = x
    p.loc[ok, "y"] = y
    t = tract_table()[["boroct2020", "nta2020"]].rename(columns={"boroct2020": "bct2020", "nta2020": "nta"})
    p["bct2020"] = p["bct2020"].str.split(".").str[0]
    p = p.merge(t, on="bct2020", how="left")
    p["street"] = p["address"].map(address_street)
    return p


def tag_srgb(path):
    import subprocess
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(path)],
                   check=True, capture_output=True)
