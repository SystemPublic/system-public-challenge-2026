"""heat-night-minimum, before registration: the composed prediction and what the test can detect.

Reads weather and calendar columns only (TMAX, TMIN, PRCP and the calendar terms of the daily
files that heat-shootings and transfer-chicago-heat-shootings wrote). The shootings columns are
not read. The mean count on hot days comes from the tables of mean count by TMAX bin that those
two studies published (seen). Writes data/derived/round5/heat_night/prereg_design.json.

1. Composition (concordance-kit/kit/bridge.py). Links, per 5 C of night minimum at fixed maximum:
   outdoor night minimum -> bedroom temperature: slope uniform 0.2 to 0.6 C per C (assumed; the
     graph holds only a correlation, Zuurbier 2021, R2 = 0.34 between outdoor and bedroom
     temperature, stored as r = 0.34);
   bedroom temperature -> sleep: 30 minutes less total sleep at 24 C than at 16 C (Valham 2012,
     PMID 22467989; the graph holds the sleep-efficiency contrast of the same trial, -6 points,
     and the 30 minutes is from the abstract), 3.75 minutes per C;
   sleep -> aggression: odds ratio 0.90 (0.81 to 1.00) per hour of sleep (Street 2016,
     PMID 28923255, in the graph), so 1.111 (1.00 to 1.235) per hour lost, taken as a rate ratio.
   Hours lost per 5 C = 5 * slope * 3.75 / 60, between 0.0625 and 0.1875 (mean 0.125, sd 0.036).
2. Detectability. Standard error of the log rate ratio per 5 C of TMIN on days with TMAX >= 27 C,
   from the Fisher information of the registered model at a constant mean (the published hot-day
   mean) and the published dispersion.
3. The yardstick for refutation: the rate ratio per 5 C of TMIN that would carry half of the
   published hot-day excess (33 against 27 C: New York 1.122, Chicago 1.058), given how much TMIN
   rises per degree of TMAX on hot days.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from patsy import dmatrix

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT.parent / "concordance-kit"))
from kit import bridge  # noqa: E402

DER = ROOT / "data/derived/round5/heat_night"
DER.mkdir(parents=True, exist_ok=True)
CONTROLS = "C(dow) + C(month) + C(year) + hol + wet"
COLS = ["date", "TMAX", "TMIN", "PRCP", "dow", "month", "year", "hol", "wet"]
CITY = {
    "new_york": {"daily": "data/derived/heat/shootings_daily.csv", "bins": "data/derived/heat/shootings_by_tmax_bin.csv",
                 "alpha": 0.040, "excess_33_vs_27": 1.122},
    "chicago": {"daily": "data/derived/graph/transfer_chicago/chicago_heat_daily.csv",
                "bins": "data/derived/graph/transfer_chicago/heat_by_tmax_bin.csv", "alpha": 0.030, "excess_33_vs_27": 1.058},
}


def hot_mean(path):
    b = pd.read_csv(ROOT / path)
    lo = b["bin"].str.extract(r"\(([-\d.]+),")[0].astype(float)
    k = b[lo >= 27]
    return float((k["mean"] * k["count"]).sum() / k["count"].sum())


def city(name, c):
    d = pd.read_csv(ROOT / c["daily"], usecols=COLS, index_col=0, parse_dates=True).dropna(subset=["TMAX", "TMIN"])
    h = d[d["TMAX"] >= 27].copy()
    h["t5"], h["tmin5"] = h["TMAX"] / 5, h["TMIN"] / 5
    X = np.asarray(dmatrix(f"t5 + tmin5 + {CONTROLS}", h, return_type="dataframe"))
    names = dmatrix(f"t5 + tmin5 + {CONTROLS}", h, return_type="dataframe").columns.tolist()
    mu = hot_mean(c["bins"])
    w = mu / (1 + c["alpha"] * mu)
    V = np.linalg.pinv(X.T @ X * w)
    se = float(np.sqrt(V[names.index("tmin5"), names.index("tmin5")]))
    Z = np.asarray(dmatrix(f"TMAX + {CONTROLS}", h, return_type="dataframe"))
    zn = dmatrix(f"TMAX + {CONTROLS}", h, return_type="dataframe").columns.tolist()
    b = float(np.linalg.lstsq(Z, h["TMIN"].values, rcond=None)[0][zn.index("TMAX")])
    resid_sd = float(np.std(h["TMIN"].values - Z @ np.linalg.lstsq(Z, h["TMIN"].values, rcond=None)[0]))
    half = math.exp(0.5 * math.log(c["excess_33_vs_27"]) * 5 / (6 * b))
    return {"n_hot_days": int(len(h)), "mean_count_hot_days": mu, "alpha": c["alpha"],
            "tmin_per_c_tmax_hot_days": b, "sd_tmin_given_tmax_and_calendar": resid_sd,
            "se_log_rr_per_5c_tmin": se, "mde_rr_80pct": math.exp(2.8 * se),
            "rr_carrying_half_the_excess": half,
            "p_refute_if_no_effect": float(0.5 * (1 + math.erf(((math.log(half) / se) - 1.96) / math.sqrt(2)))),
            "p_support_if_half": float(0.5 * (1 + math.erf(((math.log(half) / se) - 1.96) / math.sqrt(2))))}


def main():
    links = [{"name": "aggression per hour of sleep lost (Street 2016, 1/0.90)", "estimate": 1 / 0.90, "lo": 1.0, "hi": 1 / 0.81,
              "exponent": {"mean": 0.125, "sd": 0.036}}]
    comp = bridge.compose(links, draws=20000, seed=1)
    out = {"composition": {"links": links, **comp,
                           "hours_lost_per_5c": "5 C x bedroom slope (uniform 0.2 to 0.6) x 3.75 min per C / 60 = 0.0625 to 0.1875 h"}}
    for name, c in CITY.items():
        r = city(name, c)
        r["discrimination_of_composed"] = bridge.discrimination(comp["composed"]["mean_log"], comp["composed"]["sd_log"],
                                                                r["se_log_rr_per_5c_tmin"])
        out[name] = r
    (DER / "prereg_design.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
