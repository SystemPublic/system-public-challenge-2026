"""Estimators for the taxi-speed tests (written before registration).

Input: taxi_speed_*.csv from analyses.congestion.taxi_speed (date, hour, area, n, miles, hrs).
Monthly speed of a group of cells = total miles / total hours. Contrast series
d_t(group) = log speed(cbd) - log speed(north). DiD = coefficient on post in OLS of d_t on post
and calendar-month dummies, HAC 3 lags (analyses.congestion.ems_lib.did). Days from 1 to 4
January 2025 are dropped. Federal holidays are dropped from weekday groups.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from analyses.congestion.common import DER, is_peak
from analyses.reproduction.register_mmr_cbd_speed import FEDERAL_HOLIDAYS_OBSERVED

GROUPS = {
    "peak": lambda x: x.peak,
    "overnight": lambda x: ~x.peak,
    "wk_peak": lambda x: x.peak & (x.dow < 5),
    "wk_business": lambda x: (x.dow < 5) & (x.hh >= 8) & (x.hh < 18),
    "wkend_peak": lambda x: x.peak & (x.dow >= 5),
    "monfri_peak": lambda x: x.peak & x.dow.isin([0, 4]),
    "midweek_peak": lambda x: x.peak & x.dow.isin([1, 2, 3]),
    "all": lambda x: x.peak | ~x.peak,
}


def load(files=None) -> pd.DataFrame:
    files = files or sorted(DER.glob("taxi_speed_*.csv"))
    df = pd.concat([pd.read_csv(f) for f in files]).drop_duplicates(["d", "hh", "area"])
    df["d"] = pd.to_datetime(df["d"])
    df = df[~((df.d >= "2025-01-01") & (df.d < "2025-01-05"))]
    df["dow"] = df.d.dt.dayofweek
    hol = df.d.dt.strftime("%Y-%m-%d").isin(set(FEDERAL_HOLIDAYS_OBSERVED))
    df = df[~(hol & (df.dow < 5))]
    df["peak"] = is_peak(df.dow, df.hh)
    df["month"] = df.d.dt.to_period("M").dt.to_timestamp()
    return df


def series(df, group: str, area_pair=("cbd", "north")) -> pd.Series:
    x = df[GROUPS[group](df)]
    g = x.groupby(["month", "area"])[["miles", "hrs"]].sum()
    s = np.log(g.miles / g.hrs).unstack("area")
    return (s[area_pair[0]] - s[area_pair[1]]).rename(group) if area_pair[1] else s[area_pair[0]].rename(group)
