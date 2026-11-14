"""Rerun the deciding number of mob-crz-traffic, and its registered 2024 placebo, from the package's inputs.

The claim's script, analyses/mobility/crz_traffic.py, fits the speed and trip difference-in-differences, the
by-industry models and two descriptive series, writes five tables and a figure into the repository. This wrapper
points the Socrata cache at the package's inputs, blocks network access, and repeats only the lines of main()
that build the speed and trip frames, calling did() and placebo() unchanged.
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
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from concord import socrata  # noqa: E402

socrata.CACHE = INP / "data" / "cache" / "socrata"
from analyses.mobility import crz_traffic as C  # noqa: E402
from analyses.mobility.common import nys  # noqa: E402

rows, _ = nys("6p29-6xqn", select="month, zone, zonal_speed", order="month")
sp = pd.DataFrame(rows)
sp["month"] = pd.to_datetime(sp["month"])
sp["speed"] = sp["zonal_speed"].astype(float)
sp = sp.rename(columns={"zone": "area"})
w = sp[sp["month"] >= "2023-01-01"]
g = w[w["area"].isin(["CBD", "Greater NYC"])]
s = C.did(g, "CBD", "speed")
sp_pl = C.placebo(g, "CBD", "speed")

zrows, _ = nys("yfdc-w5jh", select="taxi_zone")
cbd = {int(r["taxi_zone"]) for r in zrows}
rows, _ = socrata.query("c5iv-bn4s", select="metric_month, industry, locationid, sum(trip_count) as n",
                        where="metric_month >= '2023-01-01'", group="metric_month, industry, locationid")
t = pd.DataFrame(rows)
t["n"] = t["n"].astype(float)
t["locationid"] = pd.to_numeric(t["locationid"], errors="coerce")
t["month"] = pd.to_datetime(t["metric_month"])
t["area"] = np.where(t["locationid"].isin(cbd), "CBD", "Outside CBD")
tm = t.groupby(["month", "area"], as_index=False)["n"].sum()
tr = C.did(tm, "CBD", "n")
tr_pl = C.placebo(tm, "CBD", "n")
print(json.dumps({"estimate": s["pct"], "lo": s["lo_pct"], "hi": s["hi_pct"], "n": s["n"],
                  "trips_pct": tr["pct"], "trips_n": tr["n"],
                  "placebo2024_speed_pct": sp_pl["pct"], "placebo2024_trips_pct": tr_pl["pct"]}))
