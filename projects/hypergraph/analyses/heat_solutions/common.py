"""Shared helpers for the heat-solutions analyses: areas, air conditioning, school calendar."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DER = ROOT / "data/derived/heat_solutions"
FIG = ROOT / "figures/heat_solutions"
EHDP = ROOT / "data/derived/heat/ehdp"
DER.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
END = "2026-08-31"
CONTROLS = "C(dow) + C(month) + C(year) + hol + wet"
BORO = {"MN": 1, "BX": 2, "BK": 3, "QN": 4, "SI": 5}

# First and last day of classes for students, NYC public schools. 2006-07 to 2018-19 agree with
# the first and last dates in the daily attendance files (data/derived/graph/triads/absence_daily.csv;
# the 2014 file ends early). Later years are from the Department of Education calendars.
FIRST_DAY = {2006: "09-05", 2007: "09-04", 2008: "09-02", 2009: "09-09", 2010: "09-08", 2011: "09-08", 2012: "09-06",
             2013: "09-09", 2014: "09-04", 2015: "09-09", 2016: "09-08", 2017: "09-07", 2018: "09-05", 2019: "09-05",
             2020: "09-21", 2021: "09-13", 2022: "09-08", 2023: "09-07", 2024: "09-05", 2025: "09-04", 2026: "09-10"}
LAST_DAY = {2006: "06-28", 2007: "06-27", 2008: "06-26", 2009: "06-26", 2010: "06-28", 2011: "06-28", 2012: "06-27",
            2013: "06-26", 2014: "06-26", 2015: "06-26", 2016: "06-28", 2017: "06-28", 2018: "06-26", 2019: "06-26",
            2020: "06-26", 2021: "06-25", 2022: "06-27", 2023: "06-27", 2024: "06-26", 2025: "06-26", 2026: "06-26"}
# School years taught wholly or mostly remotely: the June 2020, September 2020 and June 2021 transitions are left out.
SKIP = {("end", 2020), ("start", 2020), ("end", 2021)}


def cd_table() -> pd.DataFrame:
    """One row per community district: households with air conditioning (%), median income, percent Black.
    The Health Department's Heat Vulnerability Index file gives these by 2020 neighbourhood tabulation
    area; air conditioning is constant or nearly constant within a district, so the district value is the mean."""
    a = pd.read_csv(EHDP / "hvi-nta-2020.csv")
    g = a.groupby("CDTACode").agg(ac=("PCT_HOUSEHOLDS_AC", "mean"), income=("MEDIAN_INCOME", "mean"),
                                  black=("PCT_BLACK_POP", "mean"), hvi=("HVI_RANK", "mean")).reset_index()
    g["cd"] = [BORO[c[:2]] * 100 + int(c[2:]) for c in g["CDTACode"]]
    g = g.sort_values("cd").reset_index(drop=True)
    g["low_ac"] = (g["ac"] < g["ac"].median()).astype(int)
    g["ac_tert"] = pd.qcut(g["ac"].rank(method="first"), 3, labels=[1, 2, 3]).astype(int)
    g["low_income"] = (g["income"] < g["income"].median()).astype(int)
    return g


def fix_latlon(a, b):
    """The shootings file 5ucz-vwe8 holds latitude and longitude in swapped columns for most rows.
    Returns (lat, lon) with the value between 40 and 41.5 as latitude."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    sw = (a < 0) & (b > 0)
    return np.where(sw, b, a), np.where(sw, a, b)


def to_cd(lat, lon) -> np.ndarray:
    """Community district code (101..503) for each point, 0 where the point is in none (parks, water)."""
    import geopandas as gpd
    polys = gpd.read_file(EHDP / "CD.geojson")[["GEOCODE", "geometry"]]
    pts = gpd.GeoDataFrame({"i": np.arange(len(lat))}, geometry=gpd.points_from_xy(lon, lat), crs=polys.crs)
    j = gpd.sjoin(pts, polys, how="left", predicate="within").drop_duplicates("i").sort_values("i")
    return j["GEOCODE"].fillna(0).astype(int).values


def calendar(start="2006-01-01", end=END) -> pd.DataFrame:
    """Daily frame with Central Park weather, the calendar terms of heat-shootings, and the school calendar.
    summer_out is 1 from the day after the last day of classes to the day before the first day."""
    from analyses.heat.common import holidays
    from concord import noaa
    w, src = noaa.daily("central_park")
    idx = pd.date_range(start, end, freq="D")
    d = pd.DataFrame(index=idx).join(w[["TMAX", "TMIN", "PRCP"]])
    d["dow"], d["month"], d["year"] = d.index.day_of_week, d.index.month, d.index.year
    d["hol"] = d.index.isin(holidays(start, end)).astype(int)
    d["wet"] = (d["PRCP"] >= 1.0).astype(int)
    d["t5"] = d["TMAX"] / 5.0
    d["summer_out"] = 0
    d["win"], d["rel"] = "", np.nan
    for y in range(d.index.year.min(), d.index.year.max() + 1):
        last, first = pd.Timestamp(f"{y}-{LAST_DAY[y]}"), pd.Timestamp(f"{y}-{FIRST_DAY[y]}")
        d.loc[(d.index > last) & (d.index < first), "summer_out"] = 1
        for kind, t0 in (("end", last), ("start", first)):
            if (kind, y) in SKIP:
                continue
            # rel: days from the transition; rel > 0 after the last day, rel < 0 before the first day, are days out of school
            r = (d.index - t0).days
            m = (np.abs(r) <= 60)
            d.loc[m, f"rel_{kind}"] = r[m]
    d.attrs["source"] = src
    return d


def window(d: pd.DataFrame, half: int) -> pd.DataFrame:
    """Weekdays that are not public holidays within `half` calendar days of a transition, stacked.
    out = 1 on days out of school. trend_end and trend_start are the days from the transition for each kind."""
    parts = []
    for kind in ("end", "start"):
        c = f"rel_{kind}"
        if c not in d:
            continue
        k = d[d[c].abs() <= half].copy()
        k["kind"] = kind
        k["rel"] = k[c]
        k["out"] = ((k["rel"] > 0) if kind == "end" else (k["rel"] < 0)).astype(int)
        parts.append(k)
    k = pd.concat(parts)
    k = k[(k["dow"] < 5) & (k["hol"] == 0)].dropna(subset=["TMAX"]).copy()
    k["wy"] = k["kind"] + k["year"].astype(str)
    k["trend_end"] = np.where(k["kind"] == "end", k["rel"], 0) / 30.0
    k["trend_start"] = np.where(k["kind"] == "start", k["rel"], 0) / 30.0
    k["date"] = k.index
    return k.reset_index(drop=True)


SCHOOL_FORM = "out + t5 + trend_end + trend_start + C(dow) + wet + C(wy)"
