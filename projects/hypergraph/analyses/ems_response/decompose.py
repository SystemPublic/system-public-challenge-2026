"""Exploratory decomposition of the rise in life-threatening (initial severity 1-3) ambulance
travel time, 2019 to 2025 and 2026 (January-September), from ems_ybh.csv and ems_ytype.csv.
Mean travel T = sum_cells w_cell t_cell. Mix effect = T(w_new, t_old) - T(w_old, t_old);
within-cell effect = T(w_new, t_new) - T(w_new, t_old). Cells: borough x hour, or initial call type.
Also night (01-05) against day (07-19) changes by borough, the wait (dispatch) change, and MMR
supply ratios. Writes data/derived/ems_response/decomposition.json."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from analyses.ems_response.common import DER

ybh = pd.read_csv(DER / "ems_ybh.csv")
ybh = ybh[(ybh.sev == "hi") & (ybh.borough != "UNKNOWN")]
yt = pd.read_csv(DER / "ems_ytype.csv")
yt = yt[yt.sev == "hi"]
out = {}


def mixsplit(df, key, y0, y1):
    a = df[df.y == y0].groupby(key)[["n", "travel"]].sum()
    b = df[df.y == y1].groupby(key)[["n", "travel"]].sum()
    c = a.join(b, lsuffix="0", rsuffix="1", how="inner")
    w0, w1 = c.n0 / c.n0.sum(), c.n1 / c.n1.sum()
    t0, t1 = c.travel0 / c.n0, c.travel1 / c.n1
    T00, T10, T11 = (w0 * t0).sum(), (w1 * t0).sum(), (w1 * t1).sum()
    return {"T_old_s": T00, "T_new_s": T11, "change_s": T11 - T00, "mix_s": T10 - T00, "within_s": T11 - T10,
            "mix_share": (T10 - T00) / (T11 - T00), "cells": int(len(c))}


for y1 in (2025, 2026):
    out[f"borough_hour_2019_{y1}"] = mixsplit(ybh, ["borough", "hh"], 2019, y1)
    out[f"calltype_2019_{y1}"] = mixsplit(yt, ["ct"], 2019, y1)
    blk = ybh.assign(blk=np.select([ybh.hh.between(1, 5), ybh.hh.between(7, 19)], ["night", "day"], "shoulder"))
    g = blk.groupby(["y", "borough", "blk"])[["n", "travel", "dispatch"]].sum()
    t = (g.travel / g.n).unstack("y")
    out[f"night_day_pct_2019_{y1}"] = (100 * (t[y1] / t[2019] - 1)).round(1).unstack("blk").to_dict("index")
    gc = blk.groupby(["y", "blk"])[["n", "travel"]].sum()
    tc = (gc.travel / gc.n).unstack("y")
    out[f"night_day_pct_city_2019_{y1}"] = (100 * (tc[y1] / tc[2019] - 1)).round(1).to_dict()
yr = ybh.groupby("y")[["n", "travel", "dispatch", "response"]].sum()
out["annual_city"] = {int(y): {"n": int(r.n), "travel_min": r.travel / r.n / 60, "dispatch_min": r.dispatch / r.n / 60}
                      for y, r in yr.iterrows()}
yb = ybh.groupby(["y", "borough"])[["n", "travel"]].sum()
out["annual_borough_travel_min"] = (yb.travel / yb.n / 60).round(2).unstack("borough").to_dict("index")
# MMR supply (FDNY chapter; fiscal years; in-service hours series as revised in MMR FY2026)
mmr = {"inservice_hours_per_day": {"FY21": 9442, "FY22": 8891, "FY23": 8686, "FY24": 8653, "FY25": 8572, "FY26": 8109},
       "lt_incidents": {"FY19": 567757, "FY20": 564827, "FY21": 515598, "FY22": 564412, "FY23": 605140, "FY24": 633361,
                        "FY25": 620467, "FY26": 610771},
       "all_ems_incidents": {"FY21": 1388043, "FY22": 1531959, "FY23": 1613316, "FY24": 1644446, "FY25": 1615531, "FY26": 1605979},
       "peak_ambulances_in_service": {"FY15": 405, "FY16": 426, "FY17": 457, "FY18": 472, "FY19": 460, "FY20": 491, "FY21": 516,
                                       "FY22": 497, "FY23": 466},
       "lt_response_end_to_end": {"FY19": "9:22", "FY22": "10:17", "FY24": "10:52", "FY25": "11:21", "FY26": "13:09"},
       "source": "Mayor's Management Report, FDNY chapter, FY2019, FY2021, FY2023, FY2025, FY2026 (PDFs in ~/opt/nyc-concordance/mmr; nyc.gov/assets/operations/downloads/pdf/mmrYYYY/fdny.pdf)"}
per = {fy: mmr["all_ems_incidents"][fy] / (mmr["inservice_hours_per_day"][fy] * 365) for fy in mmr["inservice_hours_per_day"]}
mmr["all_incidents_per_unit_hour"] = {k: round(v, 3) for k, v in per.items()}
out["mmr"] = mmr
(DER / "decomposition.json").write_text(json.dumps(out, indent=1, default=float))
print(json.dumps({k: v for k, v in out.items() if k != "mmr"}, indent=1, default=float)[:6000])
print(mmr["all_incidents_per_unit_hour"])
