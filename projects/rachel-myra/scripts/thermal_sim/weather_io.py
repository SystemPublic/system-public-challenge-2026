"""Load hourly weather into the regular-hourly ``Weather`` format.

Sources (all treated as untrusted input and range-checked):

* NCEI Global Hourly (ISD) extracts in data/raw/thermal_sim/ (fetched by this
  package's ``fetch_weather`` notes in README): TMP (air temperature), WND
  (wind speed), GF1/GA1-GA3 (sky cover in oktas) for Central Park
  (72505394728) and LaGuardia (72503014732), June-August 2024 and 2025.
* data/processed/replay_heatwave_hourly.csv, written by another agent
  (temp_f, wind_speed_mph per station). It has no cloud cover, so cloud is
  joined from the ISD extract for the same station and hour.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .model import Weather

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw" / "thermal_sim"
REPLAY = REPO / "data" / "processed" / "replay_heatwave_hourly.csv"
STATION_FILES = {"laguardia": "isd_laguardia_{y}_JJA.csv", "central_park": "isd_central_park_{y}_JJA.csv"}
REPLAY_STATION = {"laguardia": "LaGuardia", "central_park": "Central Park"}


def _okta(code: pd.Series) -> pd.Series:
    c = pd.to_numeric(code.astype(str).str.split(",").str[0], errors="coerce")
    c = c.where(c.between(0, 10))
    return c.mask(c > 8, 8.0)  # 09 obscured / 10 partial obscuration -> overcast


def read_isd(station: str, years=(2024, 2025)) -> pd.DataFrame:
    """Hourly (UTC, top of hour) temp_c, wind_ms, cloud from ISD extracts."""
    frames = []
    for y in years:
        f = RAW / STATION_FILES[station].format(y=y)
        if not f.exists():
            continue
        d = pd.read_csv(f, dtype=str)
        t = pd.to_datetime(d["DATE"], utc=True, errors="coerce")
        tmp = d["TMP"].str.split(",", expand=True)
        temp = pd.to_numeric(tmp[0], errors="coerce") / 10.0
        temp = temp.where(~tmp[1].isin(["3", "7"]) & temp.between(-40, 50))
        w = d["WND"].str.split(",", expand=True)
        wind = pd.to_numeric(w[3], errors="coerce") / 10.0
        wind = wind.where(~w[4].isin(["3", "7"]) & wind.between(0, 60))
        okt = pd.concat([_okta(d[c].fillna("99")) for c in ["GF1", "GA1", "GA2", "GA3"] if c in d], axis=1).max(axis=1)
        frames.append(pd.DataFrame({"t": t, "temp_c": temp, "wind_ms": wind, "cloud": okt / 8.0}))
    df = pd.concat(frames).dropna(subset=["t"])
    df["hour"] = df["t"].dt.round("h")
    return df.groupby("hour")[["temp_c", "wind_ms", "cloud"]].mean()


def regularize(df: pd.DataFrame, start=None, end=None) -> pd.DataFrame:
    idx = pd.date_range(start or df.index.min(), end or df.index.max(), freq="h", tz="UTC")
    out = df.reindex(idx)
    out = out.interpolate(limit=6, limit_direction="both")
    out["temp_c"] = out["temp_c"].ffill().bfill()
    out["wind_ms"] = out["wind_ms"].ffill().bfill().fillna(2.0)
    out["cloud"] = out["cloud"].ffill().bfill().fillna(0.3)
    return out


def to_weather(df: pd.DataFrame) -> Weather:
    start = df.index[0].timestamp()
    return Weather(start, df["temp_c"].to_numpy(), df["wind_ms"].to_numpy(), df["cloud"].to_numpy())


def summer_weather(station: str = "laguardia", year: Optional[int] = None) -> Weather:
    years = (year,) if year else (2024, 2025)
    parts = []
    for y in years:
        df = read_isd(station, (y,))
        parts.append(regularize(df, pd.Timestamp(f"{y}-06-01", tz="UTC"), pd.Timestamp(f"{y}-09-01", tz="UTC")))
    return [to_weather(p) for p in parts] if len(parts) > 1 else to_weather(parts[0])


def replay_weather(station: str = "laguardia") -> Weather:
    """Heat-wave replay series, padded with ISD hours before/after for spin-up."""
    r = pd.read_csv(REPLAY)
    r = r[r["station_name"] == REPLAY_STATION[station]].copy()
    r["hour"] = pd.to_datetime(r["time_utc"], utc=True).dt.round("h")
    temp = (pd.to_numeric(r["temp_f"], errors="coerce") - 32.0) * 5.0 / 9.0
    wind = pd.to_numeric(r["wind_speed_mph"], errors="coerce") * 0.44704
    rp = pd.DataFrame({"temp_c": temp.where(temp.between(-40, 50)).values,
                       "wind_ms": wind.where(wind.between(0, 60)).values}, index=r["hour"]).groupby(level=0).mean()
    isd = read_isd(station, (2025,))
    start, end = rp.index.min(), rp.index.max()
    df = isd.copy()
    df.loc[rp.index.intersection(df.index), ["temp_c", "wind_ms"]] = rp.loc[rp.index.intersection(df.index)].values
    extra = rp.index.difference(df.index)
    if len(extra):
        df = pd.concat([df, rp.loc[extra].assign(cloud=np.nan)]).sort_index()
    df = regularize(df, start - pd.Timedelta(hours=48), end)
    return to_weather(df)


def replay_window() -> tuple:
    r = pd.read_csv(REPLAY, usecols=["time_utc", "date_local"])
    return r["date_local"].min(), r["date_local"].max()
