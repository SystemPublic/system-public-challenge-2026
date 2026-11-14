"""NOAA GHCN-Daily station data, fetched from NCEI's public access files (no token).

Central Park is USW00094728, LaGuardia USW00014732, JFK USW00094789.
TMAX/TMIN are tenths of a degree C in the raw files; this module converts to deg C.
The source record cites the station, the NCEI file URL and its Last-Modified header.
"""
from __future__ import annotations

import io
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache" / "noaa"
URL = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/{sid}.csv"
STATIONS = {"central_park": "USW00094728", "laguardia": "USW00014732", "jfk": "USW00094789"}


def daily(station: str = "central_park", refresh: bool = False):
    import pandas as pd
    sid = STATIONS.get(station, station)
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{sid}.csv"
    meta = CACHE / f"{sid}.meta"
    url = URL.format(sid=sid)
    if refresh or not f.exists():
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        f.write_bytes(r.content)
        meta.write_text(r.headers.get("Last-Modified", "") + "\n" + time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    df = pd.read_csv(f, low_memory=False, usecols=lambda c: c in {"DATE", "TMAX", "TMIN", "TAVG", "PRCP", "SNOW"})
    df["DATE"] = pd.to_datetime(df["DATE"])
    for c in ("TMAX", "TMIN", "TAVG"):
        if c in df:
            df[c] = df[c] / 10.0
    if "PRCP" in df:
        df["PRCP"] = df["PRCP"] / 10.0  # mm
    lm, fetched = (meta.read_text().split("\n") + ["", ""])[:2]
    src = {"kind": "noaa-ghcnd", "station": sid, "url": url, "last_modified": lm, "fetched": fetched,
           "dataset": "GHCN-Daily v3 (NCEI), doi:10.7289/V5D21VHZ"}
    return df.set_index("DATE"), src
