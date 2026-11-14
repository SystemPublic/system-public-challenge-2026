"""Registered test for claim ems-hospital-turnaround-wait (fixed before the daily data are fetched).

Unit: day, citywide. Window: 2017-01-01 to the last complete month, excluding 2020-03-01 to 2020-06-30.
y  = log mean dispatch wait (dispatch_response_seconds_qy, valid dispatch), all severities, same day
x  = log mean hospital turnaround of transported incidents (close - hospital arrival, 0-4 h), same day
controls: log incident count (all incidents), day-of-week dummies, year-month fixed effects
inference: OLS with Newey-West (HAC) standard errors, 7 lags. No resampling, no seed.
Secondary (reported, not deciding): the same model for severity 1-3 and 4-8 separately; the model with
the previous day's turnaround; annual means 2017-2026 of wait, travel, turnaround and count; the share of
the 2019 -> 2025 change in log annual mean wait that the within-month elasticities would attribute to
the changes in turnaround and count.
Writes data/derived/health_gaps/ems_model.json.
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from analyses.health_gaps.common import DER


def daily(sev=None):
    df = pd.read_csv(DER / "ems_daily.csv")
    if sev:
        df = df[df["sev"] == sev]
    g = df.groupby("d")[["n_all", "n_disp", "disp_sum", "n_trav", "trav_sum", "n_hosp", "hosp_sum"]].sum()
    g.index = pd.to_datetime(g.index)
    out = pd.DataFrame({"wait": g.disp_sum / g.n_disp, "travel": g.trav_sum / g.n_trav,
                        "hosp": g.hosp_sum / g.n_hosp, "n": g.n_all, "n_hosp": g.n_hosp})
    if sev:  # volume and turnaround are system-wide whichever severity is modelled
        allg = daily()
        out["n"] = allg["n"]
        out["hosp"] = allg["hosp"]
    return out


def window(d):
    last = d.index.max()
    last_complete = (last + pd.Timedelta(days=1)).to_period("M").start_time - pd.Timedelta(days=1)
    if last.to_period("M") == (last + pd.Timedelta(days=1)).to_period("M"):
        d = d[d.index <= last_complete]
    d = d[(d.index >= "2017-01-01") & ~((d.index >= "2020-03-01") & (d.index <= "2020-06-30"))]
    return d.dropna()


def fit(d, x="lhosp"):
    d = d.copy()
    d["lwait"], d["lhosp"], d["ln"] = np.log(d.wait), np.log(d.hosp), np.log(d.n)
    d["lhosp_l1"] = d["lhosp"].shift(1)
    d["dow"], d["ym"] = d.index.dayofweek, d.index.to_period("M").astype(str)
    d = d.dropna()
    m = smf.ols(f"lwait ~ {x} + ln + C(dow) + C(ym)", data=d).fit(cov_type="HAC", cov_kwds={"maxlags": 7})
    ci = m.conf_int().loc[x]
    return {"beta": float(m.params[x]), "lo": float(ci[0]), "hi": float(ci[1]), "se": float(m.bse[x]),
            "beta_count": float(m.params["ln"]), "count_lo": float(m.conf_int().loc["ln"][0]),
            "count_hi": float(m.conf_int().loc["ln"][1]), "n_days": int(m.nobs),
            "first": str(d.index.min().date()), "last": str(d.index.max().date())}


def main():
    res = {}
    d = window(daily())
    res["primary"] = fit(d)
    res["prev_day_turnaround"] = fit(d, "lhosp_l1")
    for s in ("hi", "lo"):
        res[f"sev_{s}"] = fit(window(daily(s)))
    a = d.groupby(d.index.year).agg(wait=("wait", "mean"), travel=("travel", "mean"), hosp=("hosp", "mean"), n=("n", "mean"))
    res["annual"] = a.round(2).reset_index().to_dict("records")
    if 2019 in a.index and 2025 in a.index:
        dl = np.log(a.loc[2025]) - np.log(a.loc[2019])
        p = res["primary"]
        res["attribution_2019_2025"] = {"dlog_wait": float(dl.wait), "dlog_hosp": float(dl.hosp), "dlog_n": float(dl.n),
                                        "from_hosp": float(p["beta"] * dl.hosp), "from_count": float(p["beta_count"] * dl.n)}
    (DER / "ems_model.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
