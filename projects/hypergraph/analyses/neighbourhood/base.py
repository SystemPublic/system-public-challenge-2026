"""Tract base for the neighbourhood claims: 2020 tract geometry and ACS covariates.

Sources
  DCP 2020 Census Tracts, NYC Open Data 63ge-mke6 (geometry, NTA codes).
  ACS 2018-2022 5-year, Census Bureau table-based summary file (keyless):
    B01003 population, C17002 ratio of income to poverty, B03002 Hispanic origin by race, B25064 median gross rent.
  ACS 2008-2012 5-year, sequence-based summary file for New York, tracts subset (2010 tracts):
    B01003 (seq 3, col 130), B03002 (seq 5, col 38), B25064 (seq 105, col 54).
  Census 2020-to-2010 tract relationship file for New York (tab20_tract20_tract10_st36.txt), land-area weights.
The Census API now requires a key, which this project does not hold; the summary files need none.

Writes data/derived/neighbourhood/tracts.geojson and tracts_acs.csv; downloads go to data/raw/acs (gitignored).
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402

RAW = ROOT / "data" / "raw" / "acs"
OUT = ROOT / "data" / "derived" / "neighbourhood"
COUNTIES = ("36005", "36047", "36061", "36081", "36085")
UA = {"User-Agent": "Mozilla/5.0 (research script)"}
TB = "https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/5YRData/acsdt5y2022-{t}.dat"
SEQ = "https://www2.census.gov/acs2012_5yr/summaryfile/2008-2012_ACSSF_By_State_By_Sequence_Table_Subset/NewYork/Tracts_Block_Groups_Only/{f}"
REL = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/tract/tab20_tract20_tract10_st36.txt"

SOURCES = []


def fetch(url: str, name: str) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    f = RAW / name
    if not f.exists():
        r = requests.get(url, headers=UA, timeout=600, stream=True)
        r.raise_for_status()
        with open(f, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    SOURCES.append({"kind": "census", "url": url, "file": f"data/raw/acs/{name}"})
    return f


def acs2022(table: str) -> pd.DataFrame:
    f = fetch(TB.format(t=table), f"acsdt5y2022-{table}.dat")
    keep = []
    with open(f) as fh:
        header = fh.readline().rstrip("\n").split("|")
        for line in fh:
            if line.startswith("1400000US36") and line[9:14] in COUNTIES:
                keep.append(line.rstrip("\n").split("|"))
    df = pd.DataFrame(keep, columns=header)
    df["GEOID"] = df["GEO_ID"].str[-11:]
    for c in df.columns:
        if c.startswith(table.upper()):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def acs2012() -> pd.DataFrame:
    g = fetch(SEQ.format(f="g20125ny.csv"), "g20125ny.csv")
    geo = pd.read_csv(g, header=None, dtype=str, encoding="latin-1")
    # columns: 0 FILEID 1 STUSAB 2 SUMLEVEL ... 4 LOGRECNO ... 48 GEOID
    geo = geo[geo[2] == "140"]
    geo = geo[[4, 48]].rename(columns={4: "LOGRECNO", 48: "GEO"})
    geo["GEOID"] = geo["GEO"].str[-11:]
    geo = geo[geo["GEOID"].str[:5].isin(COUNTIES)]
    out = geo[["LOGRECNO", "GEOID"]].copy()
    for seq, cols in {3: {"pop12": 130}, 5: {"tot12": 38, "nhw12": 40}, 105: {"rent12": 54}}.items():
        z = fetch(SEQ.format(f=f"20125ny{seq:04d}000.zip"), f"20125ny{seq:04d}000.zip")
        with zipfile.ZipFile(z) as zf:
            name = [n for n in zf.namelist() if n.startswith("e")][0]
            d = pd.read_csv(zf.open(name), header=None, dtype=str)
        d = d.rename(columns={5: "LOGRECNO"})
        sub = d[["LOGRECNO"] + [c - 1 for c in cols.values()]]
        sub.columns = ["LOGRECNO"] + list(cols)
        out = out.merge(sub, on="LOGRECNO", how="left")
    for c in ("pop12", "tot12", "nhw12", "rent12"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.drop(columns="LOGRECNO")


def crosswalk(a12: pd.DataFrame) -> pd.DataFrame:
    f = fetch(REL, "tab20_tract20_tract10_st36.txt")
    rel = pd.read_csv(f, sep="|", dtype=str)
    rel = rel[rel["GEOID_TRACT_20"].str[:5].isin(COUNTIES)]
    for c in ("AREALAND_PART", "AREALAND_TRACT_10", "AREALAND_TRACT_20"):
        rel[c] = pd.to_numeric(rel[c])
    rel["w10"] = rel["AREALAND_PART"] / rel["AREALAND_TRACT_10"].replace(0, np.nan)
    rel["w20"] = rel["AREALAND_PART"] / rel["AREALAND_TRACT_20"].replace(0, np.nan)
    m = rel.merge(a12, left_on="GEOID_TRACT_10", right_on="GEOID", how="left")
    for c in ("pop12", "nhw12", "tot12"):
        m[c + "_a"] = m[c] * m["w10"]
    m["rent_w"] = m["w20"] * m["rent12"]
    m["rent_wn"] = m["w20"].where(m["rent12"].notna())
    g = m.groupby("GEOID_TRACT_20").agg(pop12=("pop12_a", "sum"), nhw12=("nhw12_a", "sum"), tot12=("tot12_a", "sum"),
                                        rent_w=("rent_w", "sum"), rent_wn=("rent_wn", "sum"))
    g["rent12"] = g["rent_w"] / g["rent_wn"].replace(0, np.nan)
    return g.drop(columns=["rent_w", "rent_wn"]).reset_index().rename(columns={"GEOID_TRACT_20": "GEOID"})


def tracts():
    rows, src = socrata.query("63ge-mke6", select="geoid,boroct2020,borocode,boroname,nta2020,ntaname,shape_area,the_geom",
                              limit=5000)
    SOURCES.append(src)
    feats = [{"type": "Feature", "geometry": r["the_geom"],
              "properties": {k: r.get(k) for k in ("geoid", "boroct2020", "borocode", "boroname", "nta2020", "ntaname", "shape_area")}}
             for r in rows]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tracts.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    return pd.DataFrame([f["properties"] for f in feats])


def main():
    t = tracts()
    pop = acs2022("b01003")[["GEOID", "B01003_E001"]].rename(columns={"B01003_E001": "pop"})
    pov = acs2022("c17002")
    pov["pov_univ"] = pov["C17002_E001"]
    pov["pov_below"] = pov["C17002_E002"] + pov["C17002_E003"]
    race = acs2022("b03002")[["GEOID", "B03002_E001", "B03002_E003"]].rename(columns={"B03002_E001": "tot22", "B03002_E003": "nhw22"})
    rent = acs2022("b25064")[["GEOID", "B25064_E001"]].rename(columns={"B25064_E001": "rent22"})
    rent.loc[rent["rent22"] < 0, "rent22"] = np.nan
    a12 = acs2012()
    a12.loc[a12["rent12"] <= 0, "rent12"] = np.nan
    x12 = crosswalk(a12)
    df = t.rename(columns={"geoid": "GEOID"})
    for d in (pop, pov[["GEOID", "pov_univ", "pov_below"]], race, rent, x12):
        df = df.merge(d, on="GEOID", how="left")
    df["shape_area"] = pd.to_numeric(df["shape_area"])  # square feet (NY State Plane)
    df["land_km2"] = df["shape_area"] * 0.09290304 / 1e6
    df["poverty"] = df["pov_below"] / df["pov_univ"].replace(0, np.nan)
    df["nhw_share22"] = df["nhw22"] / df["tot22"].replace(0, np.nan)
    df["nhw_share12"] = df["nhw12"] / df["tot12"].replace(0, np.nan)
    df["d_nhw"] = df["nhw_share22"] - df["nhw_share12"]
    df["d_logrent"] = np.log(df["rent22"]) - np.log(df["rent12"])
    df["density"] = df["pop"] / df["land_km2"]
    df.to_csv(OUT / "tracts_acs.csv", index=False)
    (OUT / "sources_base.json").write_text(json.dumps(SOURCES, indent=1))
    print(df.describe().T[["count", "mean", "50%"]])


if __name__ == "__main__":
    main()
