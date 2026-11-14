"""Extract establishment counts by ZIP code and year from Census ZIP Code Business Patterns, 1998 to 2023.

Industries: snack and nonalcoholic beverage bars (NAICS 722213 to 2011, 722515 from 2012; coffee shops, with
doughnut, ice cream, juice and bagel shops), art dealers (453920 to 2021, 459920 from 2022), independent
artists, writers and performers (711510, employers only), and all industries.
ZIP codes: every ZIP code in current PLUTO, plus Hudson County, New Jersey.
From 2017 the Census Bureau withholds cells with fewer than three establishments, so small counts drop to
missing in those years; a missing cell is written as absent, not zero.
Output data/derived/explore/zbp_extract.csv (zip, year, series, est).
"""
from __future__ import annotations

import io
import zipfile

import pandas as pd

from common import OUT, RAW, pluto

HUDSON = ["07302", "07304", "07305", "07306", "07307", "07310", "07311", "07030", "07002", "07087", "07086", "07093",
          "07047", "07094", "07032", "07029"]
SERIES = {"722213": "snack_beverage", "722515": "snack_beverage", "453920": "art_dealers", "459920": "art_dealers",
          "711510": "independent_artists", "------": "all"}


def main():
    zips = set(pluto().zipcode.dropna().str[:5]) | set(HUDSON)
    rows = []
    for y in range(1998, 2024):
        zf = zipfile.ZipFile(RAW / "zbp" / f"zbp{str(y)[2:]}detail.zip")
        d = pd.read_csv(io.BytesIO(zf.read(zf.namelist()[0])), dtype=str, encoding="latin-1")
        d.columns = [c.lower() for c in d.columns]
        d = d[d.zip.isin(zips) & d.naics.isin(SERIES)]
        d["est"] = pd.to_numeric(d.est, errors="coerce")
        d["series"] = d.naics.map(SERIES)
        d["year"] = y
        rows.append(d[["zip", "year", "series", "naics", "est"]])
        print(y, d.groupby("series").est.sum().to_dict(), flush=True)
    pd.concat(rows).to_csv(OUT / "zbp_extract.csv", index=False)


if __name__ == "__main__":
    main()
