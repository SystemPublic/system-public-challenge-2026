"""Registered test for the 14th Street busway (fixed before registration).

c_m: monthly contrast, t14 pairs minus control pairs (analyses.street_space.series.contrast), for
the weekday sample (Mon-Fri except federal holidays, pickup 07-18) on log duration (s_lt) or log
distance (s_ld). Input: all months July 2016 to the last month given.

d_m = c_m - c_{m-12} (year-over-year change of the contrast).
E_t = mean(d_m, m = Oct t .. Feb t+1) - mean(d_m, m = Jul t .. Sep t)
      (the change in the busway season against a year earlier, net of the same change in the
      summer just before it; this removes the slow drift of the contrast seen in the design run).
Busway: t = 2019. Placebos: t = 2017 and t = 2018.
Standard error: s * sqrt(1/5 + 1/3), where s is the standard deviation of d_m over all months
from July 2017 to September 2019 (every pre-busway month with a year-earlier value).
95% interval: E +/- 1.96 se. Reported in percent as 100*(exp(.)-1).
Secondary (not deciding): the same E for the busway (06-21 all days) and overnight samples, and
the day-bootstrap DiD of analyses.street_space.estimate on Oct-Feb a year apart.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from analyses.street_space.common import DER, PAIRS
from analyses.street_space.estimate import load
from analyses.street_space.series import contrast

WINTER = [10, 11, 12, 1, 2]
SUMMER = [7, 8, 9]


def season_E(c: pd.Series, t: int):
    d = c - c.shift(12, freq="MS").reindex(c.index)
    w = [pd.Timestamp(f"{t if m >= 10 else t + 1}-{m:02d}-01") for m in WINTER]
    s = [pd.Timestamp(f"{t}-{m:02d}-01") for m in SUMMER]
    if any(x not in d.index or pd.isna(d[x]) for x in w + s):
        return None, d
    return float(d[w].mean() - d[s].mean()), d


def run(files, samples=("weekday", "busway", "overnight"), vars_=("s_lt", "s_ld")):
    df = load(files)
    pct = lambda v: round(100 * (np.exp(v) - 1), 3)
    out = {}
    for smp in samples:
        for v in vars_:
            c, _ = contrast(df, smp, v)
            c.index = pd.to_datetime(c.index)
            _, d = season_E(c, 2019)
            pre = d[(d.index >= "2017-07-01") & (d.index <= "2019-09-01")].dropna()
            s = float(pre.std(ddof=1))
            se = s * np.sqrt(1 / 5 + 1 / 3)
            res = {"s_monthly_yoy_log": round(s, 5), "se_log": round(se, 5), "n_pre_months": int(len(pre)),
                   "d_pct": {str(k.date()): pct(x) for k, x in d.dropna().items()}}
            for t in (2017, 2018, 2019):
                e, _ = season_E(c, t)
                res[str(t)] = None if e is None else {"E_pct": pct(e), "lo_pct": pct(e - 1.96 * se), "hi_pct": pct(e + 1.96 * se),
                                                       "z": round(e / se, 2)}
            out[f"{smp}_{v}"] = res
    return out


if __name__ == "__main__":
    tag = sys.argv[1]
    res = run([PAIRS / f for f in sys.argv[2:]])
    (DER / f"test_{tag}.json").write_text(json.dumps(res, indent=1))
    for k, r in res.items():
        print(k, "s=", r["s_monthly_yoy_log"], "se=", r["se_log"], {t: r[t] for t in ("2017", "2018", "2019")})
