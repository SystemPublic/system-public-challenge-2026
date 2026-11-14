"""Build NYC daily climate history, heat-wave list and day-of-year heat-wave odds
from NOAA GHCN-Daily station CSVs (Central Park USW00094728, LaGuardia USW00014732).

Inputs (downloaded from
https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/<station>.csv):
    data/raw/climate/ghcnd/USW00094728.csv
    data/raw/climate/ghcnd/USW00014732.csv

Outputs:
    data/processed/nyc_daily_climate.csv      daily TMAX/TMIN/TAVG/dew point/RH/wind/precip, 1991-01-01 .. latest, both stations
    data/processed/nyc_heatwaves.csv          every heat wave (>=3 consecutive days TMAX>=90F) per station, 1991..latest
    data/raw/climate/normals/normals_daily_1991-2020_<station>.csv  (optional; NOAA 1991-2020 daily normals,
        https://www.ncei.noaa.gov/data/normals-daily/1991-2020/access/<station>.csv) merged into the odds file
    data/processed/nyc_heatwave_daily_odds.csv  per calendar day (MM-DD): historical probability of being inside a
                                              heat wave (Central Park and LaGuardia), 1991-2025 complete years

GHCN units: temperatures and dew point in tenths of deg C, PRCP in tenths of mm, AWND in tenths of m/s,
RH in percent. Values with a non-blank quality flag (2nd field of *_ATTRIBUTES) are dropped (set to NaN).

Usage:
    uv run --with pandas python scripts/climate_ghcnd.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/climate/ghcnd"
OUT = ROOT / "data/processed"
STATIONS = {"USW00094728": "Central Park", "USW00014732": "LaGuardia"}
START = "1991-01-01"
ODDS_YEARS = (1991, 2025)  # complete years used for the climatological odds
HW_TMAX_F = 90.0
HW_MIN_DAYS = 3

TEMP_ELEMS = ["TMAX", "TMIN", "TAVG", "ADPT", "AWBT"]
OTHER_ELEMS = ["RHAV", "RHMN", "RHMX", "AWND", "PRCP"]


def c10_to_f(s):
    return (s / 10.0) * 9 / 5 + 32


def heat_index_f(t_f, rh):
    """NWS heat index (Rothfusz regression with Steadman simple formula and adjustments).
    https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml"""
    t = np.asarray(t_f, dtype=float)
    rh = np.asarray(rh, dtype=float)
    simple = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + rh * 0.094)
    hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh - 0.22475541 * t * rh
          - 0.00683783 * t * t - 0.05481717 * rh * rh + 0.00122874 * t * t * rh
          + 0.00085282 * t * rh * rh - 0.00000199 * t * t * rh * rh)
    with np.errstate(invalid="ignore"):
        adj1 = ((13 - rh) / 4) * np.sqrt(np.clip((17 - np.abs(t - 95.0)) / 17, 0, None))
    hi = np.where((rh < 13) & (t >= 80) & (t <= 112), hi - adj1, hi)
    adj2 = ((rh - 85) / 10) * ((87 - t) / 5)
    hi = np.where((rh > 85) & (t >= 80) & (t <= 87), hi + adj2, hi)
    use_full = ((simple + t) / 2) >= 80
    out = np.where(use_full, hi, simple)
    out = np.where(np.isnan(t) | np.isnan(rh), np.nan, out)
    return out


def rh_from_t_td_f(t_f, td_f):
    t = (np.asarray(t_f, float) - 32) * 5 / 9
    td = (np.asarray(td_f, float) - 32) * 5 / 9
    es = np.exp(17.625 * t / (243.04 + t))
    e = np.exp(17.625 * td / (243.04 + td))
    return np.clip(100 * e / es, 0, 100)


def load_station(sid):
    df = pd.read_csv(RAW / f"{sid}.csv", dtype=str, low_memory=False)
    df = df[df["DATE"] >= START].copy()
    out = pd.DataFrame({"date": df["DATE"], "station_id": sid, "station_name": STATIONS[sid]})
    for el in TEMP_ELEMS + OTHER_ELEMS:
        if el not in df.columns:
            out[el] = np.nan
            continue
        v = pd.to_numeric(df[el].str.strip(), errors="coerce")
        attr = df.get(f"{el}_ATTRIBUTES")
        if attr is not None:
            qflag = attr.fillna(",,,").str.split(",", expand=True)[1].fillna("").str.strip()
            v = v.where(qflag == "")
        out[el] = v.values
    res = pd.DataFrame({
        "date": out["date"].values,
        "station_id": sid,
        "station_name": STATIONS[sid],
        "tmax_f": c10_to_f(out["TMAX"]).round(1).values,
        "tmin_f": c10_to_f(out["TMIN"]).round(1).values,
        "tavg_f": c10_to_f(out["TAVG"]).round(1).values,
        "dewpoint_avg_f": c10_to_f(out["ADPT"]).round(1).values,
        "wetbulb_avg_f": c10_to_f(out["AWBT"]).round(1).values,
        "rh_avg_pct": out["RHAV"].values,
        "rh_min_pct": out["RHMN"].values,
        "rh_max_pct": out["RHMX"].values,
        "wind_avg_mph": (out["AWND"] / 10 * 2.23694).round(1).values,
        "prcp_in": (out["PRCP"] / 254.0).round(2).values,
    })
    # Approximate daily peak heat index: TMAX with RH computed from TMAX and the DAILY-AVERAGE dew point.
    rh_at_tmax = rh_from_t_td_f(res["tmax_f"], res["dewpoint_avg_f"])
    res["heat_index_max_approx_f"] = np.round(heat_index_f(res["tmax_f"], rh_at_tmax), 1)
    return res


def find_heatwaves(d):
    d = d.sort_values("date").reset_index(drop=True)
    dates = pd.to_datetime(d["date"])
    hot = (d["tmax_f"] >= HW_TMAX_F).values
    waves, i, n = [], 0, len(d)
    while i < n:
        if hot[i]:
            j = i
            while j + 1 < n and hot[j + 1] and (dates[j + 1] - dates[j]).days == 1:
                j += 1
            if j - i + 1 >= HW_MIN_DAYS:
                seg = d.iloc[i:j + 1]
                waves.append({
                    "station_id": d["station_id"].iloc[0],
                    "station_name": d["station_name"].iloc[0],
                    "start_date": seg["date"].iloc[0],
                    "end_date": seg["date"].iloc[-1],
                    "length_days": j - i + 1,
                    "peak_tmax_f": seg["tmax_f"].max(),
                    "peak_tmax_date": seg.loc[seg["tmax_f"].idxmax(), "date"],
                    "mean_tmax_f": round(seg["tmax_f"].mean(), 1),
                    "warmest_tmin_f": seg["tmin_f"].max(),
                    "warmest_tmin_date": seg.loc[seg["tmin_f"].idxmax(), "date"] if seg["tmin_f"].notna().any() else "",
                    "mean_tmin_f": round(seg["tmin_f"].mean(), 1),
                    "nights_tmin_ge_75f": int((seg["tmin_f"] >= 75).sum()),
                    "nights_tmin_ge_80f": int((seg["tmin_f"] >= 80).sum()),
                    "peak_heat_index_approx_f": seg["heat_index_max_approx_f"].max(),
                    "max_dewpoint_avg_f": seg["dewpoint_avg_f"].max(),
                })
            i = j + 1
        else:
            i += 1
    return waves


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames = [load_station(s) for s in STATIONS]
    daily = pd.concat(frames, ignore_index=True)
    daily.to_csv(OUT / "nyc_daily_climate.csv", index=False)
    print("daily rows", len(daily), daily.groupby("station_id")["date"].agg(["min", "max", "count"]).to_dict())

    waves, odds_cols = [], {}
    for sid, d in daily.groupby("station_id"):
        w = find_heatwaves(d)
        waves += w
        # day-of-year odds
        d = d.copy()
        d["dt"] = pd.to_datetime(d["date"])
        d["in_hw"] = False
        for hw in w:
            m = (d["date"] >= hw["start_date"]) & (d["date"] <= hw["end_date"])
            d.loc[m, "in_hw"] = True
        y0, y1 = ODDS_YEARS
        d = d[(d["dt"].dt.year >= y0) & (d["dt"].dt.year <= y1)]
        d["md"] = d["dt"].dt.strftime("%m-%d")
        g = d.groupby("md")
        key = "cp" if sid == "USW00094728" else "lga"
        odds_cols[f"{key}_years_observed"] = g["tmax_f"].count()
        odds_cols[f"{key}_p_in_heatwave"] = g["in_hw"].mean().round(4)
        odds_cols[f"{key}_p_tmax_ge_90"] = g["tmax_f"].apply(lambda s: (s >= 90).mean()).round(4)
        odds_cols[f"{key}_p_tmin_ge_75"] = g["tmin_f"].apply(lambda s: (s >= 75).mean()).round(4)
        odds_cols[f"{key}_mean_tmax_f"] = g["tmax_f"].mean().round(1)
        odds_cols[f"{key}_mean_tmin_f"] = g["tmin_f"].mean().round(1)
        # heat wave starting within the next 14 days (incl. today)
        starts = pd.to_datetime(pd.Series([hw["start_date"] for hw in w]))
        rows = []
        for md in sorted(d["md"].unique()):
            hits, yrs = 0, 0
            for yr in range(y0, y1 + 1):
                try:
                    base = pd.Timestamp(f"{yr}-{md}")
                except ValueError:
                    continue
                yrs += 1
                ends = pd.to_datetime(pd.Series([hw["end_date"] for hw in w]))
                # any heat-wave day in [base, base+13]
                if (((starts <= base + pd.Timedelta(days=13)) & (ends >= base)).any()):
                    hits += 1
            rows.append((md, round(hits / yrs, 4) if yrs else np.nan))
        odds_cols[f"{key}_p_heatwave_within_14d"] = pd.Series(dict(rows))

    odds = pd.DataFrame(odds_cols)
    odds.index.name = "month_day"
    # 15-day centered smoothing (circular) of the in-heat-wave probability for a less noisy bar
    for key in ("cp", "lga"):
        s = odds[f"{key}_p_in_heatwave"].values
        k = 7
        ext = np.concatenate([s[-k:], s, s[:k]])
        odds[f"{key}_p_in_heatwave_smoothed15d"] = np.round(np.convolve(ext, np.ones(2 * k + 1) / (2 * k + 1), "valid"), 4)
    # NOAA 1991-2020 daily normals (data/raw/climate/normals/normals_daily_1991-2020_<station>.csv), if present
    for sid, key in (("USW00094728", "cp"), ("USW00014732", "lga")):
        nf = ROOT / f"data/raw/climate/normals/normals_daily_1991-2020_{sid}.csv"
        if nf.exists():
            nd = pd.read_csv(nf, dtype=str).set_index("DATE")
            for col, name in (("DLY-TMAX-NORMAL", "normal_tmax_f"), ("DLY-TMIN-NORMAL", "normal_tmin_f"),
                              ("DLY-TMAX-STDDEV", "normal_tmax_sd_f")):
                odds[f"{key}_{name}"] = pd.to_numeric(nd[col].str.strip(), errors="coerce").reindex(odds.index)
    odds.reset_index().to_csv(OUT / "nyc_heatwave_daily_odds.csv", index=False)

    hw = pd.DataFrame(waves).sort_values(["station_id", "start_date"])
    hw.to_csv(OUT / "nyc_heatwaves.csv", index=False)
    print("heat waves:", hw.groupby("station_name").size().to_dict())
    print(hw[hw.start_date >= "2018"].to_string())


if __name__ == "__main__":
    main()
