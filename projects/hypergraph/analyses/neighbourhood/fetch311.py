"""Aggregate 311 complaints (erm2-nwe9) to locations with SoQL, then to 2020 census tracts.

One SoQL query per complaint type and year: count(*) grouped by latitude, longitude, paged with $offset.
Writes data/derived/neighbourhood/complaints311_tracts.csv (tract x type counts) and complaints311_sources.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402
from analyses.neighbourhood.geo import points_to_tracts  # noqa: E402

OUT = ROOT / "data" / "derived" / "neighbourhood"
TYPES = ["Noise - Residential", "Noise - Street/Sidewalk", "Noise - Vehicle", "Noise - Commercial",
         "Noise", "Noise - Helicopter", "Rodent"]
YEARS = [2022, 2023, 2024]


def fetch(ctype: str, year: int):
    where = (f"complaint_type = '{ctype}' and created_date between '{year}-01-01T00:00:00' and "
             f"'{year}-12-31T23:59:59' and latitude is not null")
    rows, src = socrata.query_all("erm2-nwe9", select="latitude, longitude, count(*) as n", where=where,
                                  group="latitude, longitude", order="latitude, longitude", page=50000)
    d = pd.DataFrame(rows)
    d["n"] = pd.to_numeric(d["n"])
    d["lat"] = pd.to_numeric(d["latitude"])
    d["lon"] = pd.to_numeric(d["longitude"])
    return d, src


PARTS = OUT / "c311"


def one(t: str, y: int):
    PARTS.mkdir(parents=True, exist_ok=True)
    slug = t.replace(" ", "").replace("/", "-")
    f = PARTS / f"{slug}_{y}.csv"
    if f.exists():
        return
    d, src = fetch(t, y)
    d["GEOID"] = points_to_tracts(d["lon"].values, d["lat"].values)
    g = d.groupby("GEOID")["n"].sum().reset_index()
    g["type"], g["year"] = t, y
    src["n_complaints"] = int(d["n"].sum())
    src["n_in_tracts"] = int(g["n"].sum())
    g.to_csv(f, index=False)
    (PARTS / f"{slug}_{y}.source.json").write_text(json.dumps(src, indent=1))
    print(t, y, src["n_complaints"], src["n_in_tracts"], flush=True)


def combine():
    parts = sorted(PARTS.glob("*.csv"))
    pd.concat([pd.read_csv(f, dtype={"GEOID": str}) for f in parts]).to_csv(OUT / "complaints311_tracts.csv", index=False)
    srcs = [json.loads(f.read_text()) for f in sorted(PARTS.glob("*.source.json"))]
    (OUT / "complaints311_sources.json").write_text(json.dumps(srcs, indent=1))
    print("combined", len(parts), "parts")


if __name__ == "__main__":
    if sys.argv[1:] == ["combine"]:
        combine()
    else:
        for t in (sys.argv[1:] or TYPES):
            for y in YEARS:
                one(t, y)
