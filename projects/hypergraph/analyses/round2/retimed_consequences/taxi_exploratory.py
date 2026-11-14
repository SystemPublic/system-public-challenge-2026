"""Exploratory, not registered: pooled Y for CBD zones, for zones outside the CBD by thinning, and by borough."""
import datetime as dt, json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib, taxi_data
D = dt.date
ex = pd.read_csv(lib.OUT / "taxi_by_zone.csv")
w19 = lib.retained_weeks(D(2019, 2, 1), D(2019, 3, 31)); w26 = lib.retained_weeks(D(2026, 2, 1), D(2026, 3, 31))
P0, _ = taxi_data.panel(["yellow", "fhvhv"], ["2019-02", "2019-03"]); P1, _ = taxi_data.panel(["yellow", "fhvhv"], ["2026-02", "2026-03"])
u = ex.taxi_zone_id.tolist()
A0, A1 = lib.week_arrays(P0, u, w19), lib.week_arrays(P1, u, w26)
cbd = (ex.cbd_share_entries >= 0.5).values
med = ex.E_day[~cbd].median()
G = {"cbd": cbd, "noncbd_more_thinning": ~cbd & (ex.E_day <= med).values, "noncbd_less_thinning": ~cbd & (ex.E_day > med).values}
r = lib.estimate(A0, A1, ex.E_day.values, G)
out = {k: r[k] for k in r if k.startswith("Y_") or "_minus_" in k}
out["n"] = {k: int(v.sum()) for k, v in G.items()}
out["pooled_E_note"] = "E_day medians: " + json.dumps({k: float(ex.E_day[v].median()) for k, v in G.items()})
json.dump(out, open(lib.OUT / "taxi_exploratory.json", "w"), indent=1)
for k, v in out.items():
    print(k, v if not isinstance(v, dict) or "estimate" not in v else f"{v['estimate']:.4f} ({v['lo']:.4f} to {v['hi']:.4f})")
