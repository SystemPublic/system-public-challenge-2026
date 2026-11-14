"""Cardiac arrest: can a test of deaths on scene fail, and what does a change in response time
imply in lives per year?

  design   pre-toll data only (2019-2024). Computes the number of cardiac-arrest calls
           (final_call_type ARREST) in the zone, the share closed with disposition 83 (patient
           pronounced dead), the standard error a difference-in-differences on that share would
           have, the change the research predicts, and the discrimination D. Writes arrest_design.json.
  lives    composes lives per year from a response-time change with kit.bridge-style draws
           (200,000 draws, seed 20261113). Uses the measured EMS change if ems_results.json exists,
           and always reports the composed (predicted) change. Writes arrest_lives.json.
  describe exploratory: the share pronounced dead by area, period and year including 2025-26.

Research link (System Public Graph, abstracts read): the odds of survival to discharge after
out-of-hospital cardiac arrest per minute of shorter EMS response. Five findings with a
per-minute unit: 1.02 (Grunau 2019, PMID 30576783, ALS interval), 1.08 (Lee 2019, 30795948),
1.12 (Kobayashi 2020, 31350130, as 0.89 per minute longer), 1.22 (Huang 2021, 33628510),
1.24 (O'Keeffe 2011, 20798090). Drawn lognormal with median 1.12 and 95% interval 1.02 to 1.24.
Baseline survival to discharge is not in the city's open data; it is drawn uniform 0.03 to 0.10
of treated arrests (US registry values are near 0.09 to 0.10; older New York studies are lower).
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from analyses.congestion.common import DER, is_peak

SEED, DRAWS = 20261113, 200_000
OR_MIN = {"median": 1.12, "lo": 1.02, "hi": 1.24}
BASE = (0.03, 0.10)


def load(years):
    df = pd.concat([pd.read_csv(DER / f"arrest_{y}.csv", dtype={"disp": str}) for y in years if (DER / f"arrest_{y}.csv").exists()])
    df["d"] = pd.to_datetime(df.d)
    df = df[~((df.d >= "2025-01-01") & (df.d < "2025-01-05"))]
    df["peak"] = is_peak(df.d.dt.dayofweek, df.hh)
    df["year"] = df.d.dt.year
    df["dead"] = (df.disp == "83") * df.n
    df["attended"] = df.disp.isin(["82", "83"]) * df.n      # transported or pronounced dead
    df["zone"] = df.area == "crz"
    return df


def table(df):
    g = df.groupby(["year", "zone", "peak"])[["n", "dead", "attended", "response", "travel"]].sum()
    v = df[df.valid == "Y"].groupby(["year", "zone", "peak"])[["n", "response"]].sum()
    g["share_dead_of_attended"] = g.dead / g.attended
    g["mean_response_s"] = v.response / v.n
    return g.reset_index()


def design():
    df = load(range(2019, 2025))
    t = table(df)
    z = t[(t.zone) & (t.peak) & (t.year >= 2023)]
    o = t[(~t.zone) & (t.peak) & (t.year >= 2023)]
    n_zone_yr = float(z.attended.mean())
    p = float(z.dead.sum() / z.attended.sum())
    resp_min = float(z.mean_response_s.mean() / 60)
    # se of a DiD on the share: two zone samples (2 pre years, 1.7 post years) and two large outside samples
    se_z = np.sqrt(p * (1 - p) * (1 / (2 * n_zone_yr) + 1 / (1.7 * n_zone_yr)))
    po, no = float(o.dead.sum() / o.attended.sum()), float(o.attended.mean())
    se_o = np.sqrt(po * (1 - po) * (1 / (2 * no) + 1 / (1.7 * no)))
    se = float(np.hypot(se_z, se_o))
    # year-to-year placebo DiDs of the share, peak hours
    w = t[t.peak].pivot(index="year", columns="zone", values="share_dead_of_attended")
    pl = (w[True] - w[False]).diff().dropna()
    ems = json.loads((DER / "ems_design.json").read_text())
    vz = df[(df.valid == "Y") & df.zone & df.peak & (df.year >= 2023)]
    travel_share = float(vz.travel.sum() / vz.response.sum())
    dt_min = resp_min * (1 - np.exp(ems["composed"]["mean_log"])) * travel_share
    # change in the share dead on scene if survival odds rise by OR per minute: deaths avoided / attended
    surv = np.mean(BASE)
    d_share = -surv * (1 - surv) * np.log(OR_MIN["median"]) * dt_min
    out = {"zone_peak_attended_arrests_per_year_2023_24": n_zone_yr, "share_pronounced_dead_zone_peak": p,
           "share_pronounced_dead_outside_peak": po, "mean_response_min_zone_peak": resp_min,
           "sampling_se_of_did_share": se, "placebo_did_share_by_year": {int(k): float(v) for k, v in pl.items()},
           "placebo_sd": float(pl.std()), "predicted_minutes_saved": float(dt_min), "travel_share": travel_share,
           "predicted_change_in_share": float(d_share), "D_expected": float((d_share / se) ** 2),
           "can_fail": bool((d_share / se) ** 2 >= 4),
           "table": t.to_dict("records")}
    (DER / "arrest_design.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: v for k, v in out.items() if k != "table"}, indent=1))


def lives():
    rng = np.random.default_rng(SEED)
    des = json.loads((DER / "arrest_design.json").read_text())
    ems = json.loads((DER / "ems_design.json").read_text())
    n = des["zone_peak_attended_arrests_per_year_2023_24"]
    resp = des["mean_response_min_zone_peak"]
    sd_or = (np.log(OR_MIN["hi"]) - np.log(OR_MIN["lo"])) / 3.92
    lor = rng.normal(np.log(OR_MIN["median"]), sd_or, DRAWS)
    base = rng.uniform(*BASE, DRAWS)
    out = {"inputs": {"attended_arrests_zone_peak_per_year": n, "mean_response_min": resp, "or_per_minute": OR_MIN,
                      "baseline_survival_uniform": BASE, "draws": DRAWS, "seed": SEED}}
    scen = {"composed_prediction": (ems["composed"]["mean_log"], ems["composed"]["sd_log"])}
    f = DER / "ems_results.json"
    if f.exists():
        r = json.loads(f.read_text())
        for k, lab in [("endpoint", "measured_jan_aug_2025"), ("endpoint_full_period", "measured_to_sep_2026")]:
            scen[lab] = (r[k]["log"], r[k]["se"])
        tr = r.get("ems.all.response.all_outside", {}).get("peak", {})
        for k, lab in [("primary_jan_aug_2025", "measured_response_jan_aug_2025"), ("full_to_sep_2026", "measured_response_to_sep_2026")]:
            if k in tr:
                scen[lab] = (tr[k]["log"], tr[k]["se"], "response")
    for lab, s in scen.items():
        chg = rng.normal(s[0], s[1], DRAWS)
        # minutes saved: travel is the part of response that moves; a response-time estimate applies to all of it
        minutes = -(np.exp(chg) - 1) * resp * (1.0 if len(s) == 3 else des.get("travel_share", 0.55))
        d_surv = base * (1 - base) * lor * minutes
        L = n * d_surv
        q = lambda x: [float(v) for v in np.quantile(x, [0.025, 0.5, 0.975])]
        out[lab] = {"seconds_saved_lo_med_hi": q(60 * minutes), "lives_per_year_lo_med_hi": q(L),
                    "p_lives_positive": float((L > 0).mean())}
    (DER / "arrest_lives.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


def describe():
    df = load(range(2019, 2027))
    t = table(df)
    t.to_csv(DER / "arrest_table.csv", index=False)
    df["post"] = df.d >= "2025-01-05"
    x = df[df.year >= 2023].groupby(["zone", "peak", "post"])[["dead", "attended"]].sum()
    x["share"] = x.dead / x.attended
    print(x.to_string())
    res = {}
    for pk in (True, False):
        s = x.xs(pk, level="peak").share
        n = x.xs(pk, level="peak").attended
        did = (s[(True, True)] - s[(True, False)]) - (s[(False, True)] - s[(False, False)])
        se = np.sqrt(sum(s[k] * (1 - s[k]) / n[k] for k in s.index))
        res["peak" if pk else "overnight"] = {"did_share_points": 100 * float(did), "lo": 100 * float(did - 1.96 * se),
                                              "hi": 100 * float(did + 1.96 * se), "n_zone_post": int(n[(True, True)])}
    (DER / "arrest_exploratory.json").write_text(json.dumps(res, indent=1))
    print(res)


if __name__ == "__main__":
    {"design": design, "lives": lives, "describe": describe}[sys.argv[1]]()
