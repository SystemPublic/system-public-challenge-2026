"""Rerun the deciding number of ems-traffic-share-2019-2026 from the package's inputs.

The claim's script, analyses/ems_response/run_tests.py, runs three registered tests and writes results.json. The
deciding number is T2's S1, from lib.traffic_share(): the share of the January-September 2019 to 2026 rise in
Manhattan life-threatening EMS travel time that the change in taxi pace accounts for at an elasticity of 1. This
wrapper points lib.DER and lib.CONG at the package's inputs, replaces lib.taxi_hourly() by a copy that reads the
named files in the order the original's globs give (it reads every taxi table in two folders, 29 MB, but only the
files below hold rows in the two windows, and the first-occurrence rule of drop_duplicates picks the same rows),
and calls lib.traffic_share() unchanged (400 day-block bootstrap draws, seed 20261113). S1 and its interval do not
depend on the elasticity argument, because the bootstrap draws are taken before the elasticity draws.
"""
import argparse, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
import pandas as pd  # noqa: E402
from analyses.ems_response import lib  # noqa: E402

lib.DER = INP / "data" / "derived" / "ems_response"
lib.CONG = INP / "data" / "derived" / "congestion"
TAXI = ['data/derived/ems_response/taxi_hourly_2019-01_2020-02.csv', 'data/derived/ems_response/taxi_hourly_2026-01_2026-06.csv', 'data/derived/ems_response/taxi_hourly_2026-07_2026-09.csv', 'data/derived/ems_response/taxi_parts/2019-01.csv', 'data/derived/ems_response/taxi_parts/2019-02.csv', 'data/derived/ems_response/taxi_parts/2019-03.csv', 'data/derived/ems_response/taxi_parts/2019-04.csv', 'data/derived/ems_response/taxi_parts/2019-05.csv', 'data/derived/ems_response/taxi_parts/2019-06.csv', 'data/derived/ems_response/taxi_parts/2019-07.csv', 'data/derived/ems_response/taxi_parts/2019-08.csv', 'data/derived/ems_response/taxi_parts/2019-09.csv', 'data/derived/ems_response/taxi_parts/2026-01.csv', 'data/derived/ems_response/taxi_parts/2026-02.csv', 'data/derived/ems_response/taxi_parts/2026-03.csv', 'data/derived/ems_response/taxi_parts/2026-04.csv', 'data/derived/ems_response/taxi_parts/2026-05.csv', 'data/derived/ems_response/taxi_parts/2026-06.csv', 'data/derived/ems_response/taxi_parts/2026-07.csv', 'data/derived/ems_response/taxi_parts/2026-08.csv', 'data/derived/ems_response/taxi_parts/2026-09.csv', 'data/derived/congestion/taxi_speed_2025-01_2026-06.csv']


def taxi_hourly():
    t = pd.concat([pd.read_csv(INP / f) for f in TAXI])
    t["d"] = pd.to_datetime(t["d"])
    return t.drop_duplicates(["d", "hh", "area"]).reset_index(drop=True)


lib.taxi_hourly = taxi_hourly
r = lib.traffic_share(1.0, 0.0)
print(json.dumps({"estimate": r["S1"], "lo": r["S1_ci"][0], "hi": r["S1_ci"][1], "n": 2,
                  "D_pct": r["D_pct"], "pace_change_pct": r["pace_change_pct"]}))
