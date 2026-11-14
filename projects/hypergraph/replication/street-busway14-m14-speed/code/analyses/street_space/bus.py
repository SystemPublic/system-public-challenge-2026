"""M14 bus speed test (fixed before any M14 speed after September 2019 is read).

Data: MTA Bus Speeds: Beginning 2015 (data.ny.gov cudb-vcni), monthly by route, day type, period
(peak, off-peak) and trip type, with total_operating_time and total_mileage. Manhattan routes start in
January 2019 in this dataset; the M14A+ and M14D+ Select Bus Service rows start in June 2019.

Speed of a route in a window = total mileage / total operating time, weekdays (day_type 1), both periods.
Treated: M14A+ and M14D+ pooled. Controls: every other Manhattan local, limited or SBS route present in
every month of the windows. log ratio R = log speed(window B) - log speed(window A).
DiD = R(M14) - mean R(controls), reported as 100(exp(.)-1).
Windows: A = July to September (summer), B = October to the next February.
Busway: A = Jul-Sep 2019 (SBS running, no busway), B = Oct 2019-Feb 2020.
Null distribution (design): the same DiD for each control route r in turn as if it were treated
(against the other controls) in the seasons 2021, 2022 and 2023 (2020 is the pandemic; season 2024
ends after congestion pricing began on 5 January 2025). se = sd of those placebo DiDs.

Usage: python -m analyses.street_space.bus design | final
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from analyses.mobility.common import nys
from analyses.street_space.common import DER

TREATED = ["M14A+", "M14D+"]


def fetch(a, b, routes_where="borough='Manhattan'"):
    rows, src = nys("cudb-vcni", select="month, route_id, sum(total_mileage) as mi, sum(total_operating_time) as hr",
                    where=f"{routes_where} and day_type='1' and month between '{a}' and '{b}'",
                    group="month, route_id", order="month, route_id", limit=50000)
    df = pd.DataFrame(rows)
    df["month"] = pd.to_datetime(df.month.str[:10])
    df[["mi", "hr"]] = df[["mi", "hr"]].astype(float)
    return df, src


def window_R(df, A, B, routes):
    out = {}
    for r in routes:
        x = df[df.route_id == r]
        a = x[(x.month >= A[0]) & (x.month <= A[1])]
        b = x[(x.month >= B[0]) & (x.month <= B[1])]
        out[r] = np.log(b.mi.sum() / b.hr.sum()) - np.log(a.mi.sum() / a.hr.sum())
    return out


def complete(df, A, B):
    months = pd.date_range(A[0], B[1], freq="MS")
    x = df[df.month.isin(months)]
    c = x.groupby("route_id").month.nunique()
    return sorted(c[c == len(months)].index)


def seasons(t):
    return (f"{t}-07-01", f"{t}-09-01"), (f"{t}-10-01", f"{t + 1}-02-01")


def design():
    df, src = fetch("2021-07-01", "2024-02-01", "borough='Manhattan' and route_id not like 'M14%'")
    plac = []
    for t in (2021, 2022, 2023):
        A, B = seasons(t)
        routes = complete(df, A, B)
        R = window_R(df, A, B, routes)
        for r in routes:
            others = [R[q] for q in routes if q != r]
            plac.append({"season": t, "route": r, "did_pct": round(100 * (np.exp(R[r] - np.mean(others)) - 1), 3),
                         "did_log": R[r] - np.mean(others)})
    p = pd.DataFrame(plac)
    sd = float(p.did_log.std(ddof=1))
    out = {"placebo": plac, "sd_log": sd, "n": len(p), "abs_95pct_log": float(p.did_log.abs().quantile(0.95)),
           "source": src}
    (DER / "bus_design.json").write_text(json.dumps(out, indent=1, default=float))
    print(p.groupby("season").did_pct.describe())
    print("sd_log", round(sd, 4), "abs 95%", round(out["abs_95pct_log"], 4))


def final():
    d = json.loads((DER / "bus_design.json").read_text())
    df, src = fetch("2019-07-01", "2020-02-01")
    A, B = seasons(2019)
    routes = complete(df, A, B)
    controls = [r for r in routes if not r.startswith("M14")]
    tr = df[df.route_id.isin(TREATED)].groupby("month")[["mi", "hr"]].sum().reset_index()
    tr["route_id"] = "M14"
    R = window_R(pd.concat([df, tr]), A, B, controls + ["M14"])
    did = R["M14"] - np.mean([R[r] for r in controls])
    se = d["sd_log"]
    pct = lambda v: round(float(100 * (np.exp(v) - 1)), 3)
    lv = {}
    for w, (a, b) in {"jul_sep_2019": A, "oct19_feb20": B}.items():
        x = tr[(tr.month >= a) & (tr.month <= b)]
        c = df[df.route_id.isin(controls) & (df.month >= a) & (df.month <= b)]
        lv[w] = {"m14_mph": round(x.mi.sum() / x.hr.sum(), 3), "controls_mph": round(c.mi.sum() / c.hr.sum(), 3)}
    m14_monthly = (tr.set_index("month").mi / tr.set_index("month").hr).round(3)
    out = {"did_pct": pct(did), "lo_pct": pct(did - 1.96 * se), "hi_pct": pct(did + 1.96 * se), "se_log": se,
           "R_m14_pct": pct(R["M14"]), "R_controls_mean_pct": pct(np.mean([R[r] for r in controls])),
           "n_controls": len(controls), "levels": lv, "m14_monthly_mph": {str(k.date()): v for k, v in m14_monthly.items()},
           "source": src}
    (DER / "bus_final.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: v for k, v in out.items() if k != "source"}, indent=1))


if __name__ == "__main__":
    {"design": design, "final": final}[sys.argv[1]]()
