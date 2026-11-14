"""Exploratory: night (01-05) and day (07-19) changes, January-September 2019, 2025 and 2026,
in yellow-taxi speed by area and in life-threatening EMS travel time (Manhattan crz + north
from the hourly files; boroughs from ems_ybh.csv, full years for 2019 and 2025).
Writes data/derived/ems_response/night_day.json."""
import json
import numpy as np
import pandas as pd
from analyses.ems_response import lib
from analyses.ems_response.common import DER

blk = lambda h: np.select([h.between(1, 5), h.between(7, 19)], ["night", "day"], "shoulder")
t = lib.taxi_hourly()
t = t[(t.d.dt.month <= 9) & t.d.dt.year.isin([2019, 2025, 2026])].copy()
t["blk"], t["y"] = blk(t.hh), t.d.dt.year
g = t.groupby(["area", "y", "blk"])[["n", "hrs", "miles"]].sum()
sp = (g.miles / g.hrs).rename("mph").reset_index()
e = lib.ems_hourly([2019, 2025, 2026])
e = e[(e.sev == "hi") & (e.d.dt.month <= 9)].copy()
e["blk"], e["y"] = blk(e.hh), e.d.dt.year
ge = e.groupby(["y", "blk"])[["n", "travel"]].sum()
em = (ge.travel / ge.n / 60).rename("min").reset_index()
out = {"taxi_mph": sp.round(3).to_dict("records"), "taxi_trips": g.n.reset_index().to_dict("records"),
       "ems_mn_lt_travel_min": em.round(3).to_dict("records")}
(DER / "night_day.json").write_text(json.dumps(out, indent=1, default=int))
print(sp.pivot_table(index=["area", "blk"], columns="y", values="mph").round(2))
print(g.n.unstack("y").xs("day", level="blk"))
print(em.pivot_table(index="blk", columns="y", values="min").round(2))
