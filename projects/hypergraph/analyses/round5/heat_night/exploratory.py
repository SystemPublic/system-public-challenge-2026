"""heat-night-minimum, exploratory, run after the registered results were read. Not registered.
1. The 33 against 27 C ratio on calendar-day counts (the counting of the earlier claims) from this study's data.
2. Shootings from 00:00 to 05:59 of the shooting day's night against that night's minimum (TMIN of d+1) and TMAX of d, all days, spline.
Writes data/derived/round5/heat_night/exploratory.json."""
import json
from pathlib import Path

import pandas as pd

from analyses.round5.heat_night import run as R

ROOT = Path(__file__).resolve().parents[3]
out = {}
for c in R.CITIES:
    d = pd.read_csv(R.DER / f"{c}_daily.csv", index_col=0, parse_dates=True).dropna(subset=["TMAX", "TMIN", "TMIN_next"])
    o = {"calendar_day_33_vs_27": R.spline_fit(d, "n_cal")["rr_33_vs_27"],
         "shooting_day_33_vs_27": R.spline_fit(d, "n")["rr_33_vs_27"]}
    for y in ("n_00_06", "n_18_24", "n_12_18", "n_06_12"):
        o[f"{y}_with_following_tmin"] = R.spline_fit(d, y, ["tminn5"])
    out[c] = o
(R.DER / "exploratory.json").write_text(json.dumps(out, indent=1))
f = lambda v: f"{v['estimate']:.3f} ({v['lo']:.3f}-{v['hi']:.3f})"
for c, o in out.items():
    print(c, "cal", f(o["calendar_day_33_vs_27"]), "sd", f(o["shooting_day_33_vs_27"]))
    for k, v in o.items():
        if "with" in k:
            print("  ", k, "tmax33v27", f(v["rr_33_vs_27"]), "tmin_next/5C", f(v["tminn5"]))
