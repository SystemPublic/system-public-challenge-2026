"""ACS 5-year summary files from www2.census.gov, read without the (now key-only) Census API.

2019 (2015-19): legacy sequence files, national 'All_Geographies_Not_Tracts_Block_Groups' (for ZCTAs).
2023 (2019-23): table-based summary files (acsdt5y2023-<table>.dat), all geographies in one file.
Files are cached in ~/opt/nyc-concordance/commuting/acs*/ and cited by URL.
"""
from __future__ import annotations

import io
import zipfile

import pandas as pd

from analyses.commuting.common import OPT, fetch

SF19 = "https://www2.census.gov/programs-surveys/acs/summary_file/2019/"
SF23 = "https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/"


def _lookup19():
    f = fetch(SF19 + "documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt", "acs2019_seq_lookup.txt")
    return pd.read_csv(f, dtype=str, encoding="latin-1")


def zcta_2019(table: str, lines: list[int]):
    """Estimates for ZCTAs (all US) for one table and line numbers, 2015-19 ACS. Returns (df, source)."""
    lk = _lookup19()
    rows = lk[lk["Table ID"] == table]
    seq = rows["Sequence Number"].iloc[0]
    start = int(rows["Start Position"].dropna().iloc[0])
    base = SF19 + "data/5_year_seq_by_state/UnitedStates/All_Geographies_Not_Tracts_Block_Groups/"
    z = fetch(base + f"20195us{seq}000.zip", f"acs2019_us_seq{seq}.zip")
    with zipfile.ZipFile(z) as zf:
        name = [n for n in zf.namelist() if n.startswith("e")][0]
        e = pd.read_csv(io.BytesIO(zf.read(name)), header=None, dtype=str)
    g = pd.read_csv(fetch(base + "g20195us.csv", "acs2019_g20195us.csv"), header=None, dtype=str, encoding="latin-1")
    geo = g[[4, 48]].rename(columns={4: "logrecno", 48: "geoid"})
    out = pd.DataFrame({"logrecno": e[5]})
    for ln in lines:
        out[f"{table}_{ln:03d}"] = pd.to_numeric(e[start - 1 + ln - 1], errors="coerce")
    out = out.merge(geo, on="logrecno")
    out = out[out["geoid"].str.startswith("86000US")].copy()
    out["zcta"] = out["geoid"].str[-5:]
    src = {"kind": "census-acs-summary-file", "vintage": "ACS 2015-2019 5-year (legacy sequence files)",
           "table": table, "lines": lines, "sequence": seq,
           "url": base + f"20195us{seq}000.zip", "geography_file": base + "g20195us.csv"}
    return out.drop(columns=["logrecno"]), src


def table_2023(table: str, cols: list[str], geoid_prefix: str):
    """Columns (e.g. 'B19025_E001') of a 2019-23 table-based file for GEO_IDs starting with a prefix."""
    url = SF23 + f"acsdt5y2023-{table.lower()}.dat"
    f = fetch(url, f"acsdt5y2023-{table.lower()}.dat")
    d = pd.read_csv(f, sep="|", dtype=str, usecols=["GEO_ID"] + cols)
    d = d[d["GEO_ID"].str.startswith(geoid_prefix)].copy()
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
        d.loc[d[c] < 0, c] = float("nan")  # negative values are Census annotation codes (e.g. -666666666)
    return d, {"kind": "census-acs-summary-file", "vintage": "ACS 2019-2023 5-year (table-based)",
               "table": table, "columns": cols, "url": url}
