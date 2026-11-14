"""Fetch and tidy NCEI Global Hourly (ISD) observations for a heat-wave replay window,
and compute the NWS heat index (Rothfusz regression).

Source: NCEI Access Data Service, dataset=global-hourly
    https://www.ncei.noaa.gov/access/services/data/v1?dataset=global-hourly&stations=<USAF+WBAN>
        &startDate=<UTC>&endDate=<UTC>&format=csv&includeStationName=true
Stations: Central Park 72505394728 (KNYC), LaGuardia 72503014732 (KLGA).

Raw CSVs are cached in data/raw/climate/hourly/; the tidy output is
data/processed/replay_heatwave_hourly.csv (local time America/New_York + UTC).

Only routine hourly METARs (REPORT_TYPE FM-15) are kept, so there is one row per station-hour.
ISD fields decoded: TMP, DEW (deg C x10, quality code), WND (dir deg, speed m/s x10), SLP (hPa x10).
Values with ISD missing sentinels (+9999 / 9999 / 999) or a failing quality code (3, 7) are dropped.

Usage:
    uv run --with pandas python scripts/climate_hourly_replay.py --start 2025-06-19 --end 2025-06-28
"""
import argparse
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/climate/hourly"
OUT = ROOT / "data/processed/replay_heatwave_hourly.csv"
STATIONS = {"72505394728": ("USW00094728", "Central Park", "KNYC"),
            "72503014732": ("USW00014732", "LaGuardia", "KLGA")}
BAD_Q = {"3", "7"}


def heat_index_f(t, rh):
    """NWS heat index, https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml"""
    t = np.asarray(t, float)
    rh = np.asarray(rh, float)
    simple = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + rh * 0.094)
    hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh - 0.22475541 * t * rh
          - 0.00683783 * t * t - 0.05481717 * rh * rh + 0.00122874 * t * t * rh
          + 0.00085282 * t * rh * rh - 0.00000199 * t * t * rh * rh)
    with np.errstate(invalid="ignore"):
        adj1 = ((13 - rh) / 4) * np.sqrt(np.clip((17 - np.abs(t - 95.0)) / 17, 0, None))
    hi = np.where((rh < 13) & (t >= 80) & (t <= 112), hi - adj1, hi)
    hi = np.where((rh > 85) & (t >= 80) & (t <= 87), hi + ((rh - 85) / 10) * ((87 - t) / 5), hi)
    out = np.where(((simple + t) / 2) >= 80, hi, simple)
    return np.where(np.isnan(t) | np.isnan(rh), np.nan, out)


def rh_pct(t_c, td_c):
    es = np.exp(17.625 * t_c / (243.04 + t_c))
    e = np.exp(17.625 * td_c / (243.04 + td_c))
    return np.clip(100 * e / es, 0, 100)


def parse_val(series, idx_val, idx_q, missing, scale):
    parts = series.fillna("").str.split(",", expand=True)
    if parts.shape[1] <= max(idx_val, idx_q):
        return pd.Series(np.nan, index=series.index)
    v = pd.to_numeric(parts[idx_val], errors="coerce")
    q = parts[idx_q].str.strip()
    v = v.where(~v.isin(missing) & ~q.isin(BAD_Q))
    return v / scale


def fetch(usaf_wban, start, end):
    RAW.mkdir(parents=True, exist_ok=True)
    f = RAW / f"isd_{usaf_wban}_{start.replace('-', '')}_{end.replace('-', '')}.csv"
    if not f.exists():
        # local-day window -> UTC with margin (EDT/EST offset <= 5 h)
        s = (pd.Timestamp(start)).strftime("%Y-%m-%dT00:00:00")
        e = (pd.Timestamp(end) + pd.Timedelta(days=1, hours=6)).strftime("%Y-%m-%dT%H:00:00")
        url = ("https://www.ncei.noaa.gov/access/services/data/v1?dataset=global-hourly"
               f"&stations={usaf_wban}&startDate={s}&endDate={e}&format=csv&includeStationName=true")
        subprocess.run(["curl", "-sS", "-f", "-o", str(f), url], check=True)
    return f


def tidy(f, usaf_wban, start, end):
    df = pd.read_csv(f, dtype=str, low_memory=False)
    df = df[df["REPORT_TYPE"].str.strip() == "FM-15"].copy()
    ghcn, name, icao = STATIONS[usaf_wban]
    utc = pd.to_datetime(df["DATE"]).dt.tz_localize("UTC")
    local = utc.dt.tz_convert("America/New_York")
    t_c = parse_val(df["TMP"], 0, 1, [9999], 10.0)
    td_c = parse_val(df["DEW"], 0, 1, [9999], 10.0)
    wdir = parse_val(df["WND"], 0, 1, [999], 1.0)
    wspd = parse_val(df["WND"], 3, 4, [9999], 10.0)
    slp = parse_val(df["SLP"], 0, 1, [99999], 10.0) if "SLP" in df else np.nan
    out = pd.DataFrame({
        "station_id": ghcn, "isd_id": usaf_wban, "icao": icao, "station_name": name,
        "time_utc": utc.dt.strftime("%Y-%m-%dT%H:%M:%SZ").values,
        "time_local": local.dt.strftime("%Y-%m-%dT%H:%M:%S%z").values,
        "date_local": local.dt.strftime("%Y-%m-%d").values,
        "hour_local": local.dt.hour.values,
        "temp_f": np.round(t_c * 9 / 5 + 32, 1).values,
        "dewpoint_f": np.round(td_c * 9 / 5 + 32, 1).values,
        "rh_pct": np.round(rh_pct(t_c, td_c), 1).values,
        "wind_dir_deg": wdir.values,
        "wind_speed_mph": np.round(wspd * 2.23694, 1).values,
        "sea_level_pressure_hpa": np.asarray(slp),
    })
    out["heat_index_f"] = np.round(heat_index_f(out["temp_f"], out["rh_pct"]), 1)
    out = out[(out["date_local"] >= start) & (out["date_local"] <= end)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-06-19")
    ap.add_argument("--end", default="2025-06-28")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    frames = [tidy(fetch(s, a.start, a.end), s, a.start, a.end) for s in STATIONS]
    df = pd.concat(frames, ignore_index=True).sort_values(["station_id", "time_utc"])
    df.to_csv(a.out, index=False)
    print(len(df), "rows ->", a.out)
    daily = df.groupby(["station_name", "date_local"]).agg(
        n=("temp_f", "count"), tmax=("temp_f", "max"), tmin=("temp_f", "min"),
        hi_max=("heat_index_f", "max"), td_max=("dewpoint_f", "max"))
    print(daily.to_string())


if __name__ == "__main__":
    main()
