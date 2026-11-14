"""Run the three registered tests (estimators in lib.py) and write
data/derived/ems_response/results.json. Secondary results are labelled."""
from __future__ import annotations
import json, sys
import numpy as np
from analyses.ems_response import lib
from analyses.ems_response.common import DER

Y = list(range(2019, 2027))
r = {}
p = lib.panel(Y)
r["taxi_months"] = sorted(p.d.dt.strftime("%Y-%m").unique().tolist())
r["t1"] = lib.t1(Y)
r["t1_hi"] = lib.t1(Y, sev="hi")
r["t1_by_year"] = {}
for y in Y:
    try:
        r["t1_by_year"][y] = lib.t1([y])["joint"]["x"]
    except Exception as e:  # year without data
        r["t1_by_year"][y] = str(e)
b = r["t1_hi"]["x_only"]["x"]
r["t2"] = lib.traffic_share(b["est"], b["se"])
r["t2_2025"] = lib.traffic_share(b["est"], b["se"], post=("2025-01-01", "2025-09-30"))
r["t2_all_sev"] = lib.traffic_share(r["t1"]["x_only"]["x"]["est"], r["t1"]["x_only"]["x"]["se"], sev="lo")
w, yoy = lib.weekly([2023, 2024, 2025, 2026])
r["t3"] = lib.onset(yoy)
r["t3_placebo_year"] = lib.onset(yoy, start=(2024, 27), split=(2025, 1), end=(2025, 39))
wh, yoyh = lib.weekly([2024, 2025, 2026], sev="hi")
r["t3_hi"] = lib.onset(yoyh)
yoy.reset_index().to_csv(DER / "weekly_yoy.csv", index=False)
(DER / "results.json").write_text(json.dumps(r, indent=1, default=str))
for k in ("t1", "t1_hi"):
    print(k, {kk: (v["x"] if "x" in v else v.get("x_lead", v.get("xd"))) for kk, v in r[k].items()})
print("diff", r["t1"]["diff_x_minus_lead"])
print("t2", {k: r["t2"][k] for k in ("D_pct", "D_ci", "pace_change_pct", "pace_ci", "S", "S_ci", "S1", "S1_ci")})
print("t2_2025", {k: r["t2_2025"][k] for k in ("D_pct", "pace_change_pct", "S1", "S1_ci")})
print("t3", r["t3"]); print("t3 placebo", r["t3_placebo_year"])
