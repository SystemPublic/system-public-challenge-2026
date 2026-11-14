"""Estimator for the 14th Street busway tests (fixed before registration).

For each directed pair p and window w (pre, post), the mean of log trip duration (or log trip
distance) over trips in the sample's days and pickup hours. Delta_p = mean_post - mean_pre.
DiD = mean of Delta_p over t14 pairs - mean of Delta_p over control pairs (c_mid and c_down
pooled, equal weight per pair). Pairs need MIN_TRIPS trips in each window. Reported as
100*(exp(DiD)-1) percent. Interval: bootstrap over calendar days, resampled with replacement
within each window separately (keeping all pairs and hours of a day together), DRAWS draws,
SEED, percentile 2.5 and 97.5.

Samples:
  weekday   Monday to Friday except federal holidays, pickup hour 07 to 18 (busway active)
  busway    every day, pickup hour 06 to 21 (all busway hours)
  overnight every day, pickup hour 22 to 05 (busway not in force; L train slowdown in force on
            weeknights and weekends of the post window but not of the pre window)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from analyses.street_space.common import DER, SEED, DRAWS, MIN_TRIPS

HOLIDAYS = {"2017-10-09", "2017-11-10", "2017-11-23", "2017-12-25", "2018-01-01", "2018-01-15", "2018-02-19",
            "2018-10-08", "2018-11-12", "2018-11-22", "2018-12-25", "2019-01-01", "2019-01-21", "2019-02-18",
            "2019-10-14", "2019-11-11", "2019-11-28", "2019-12-25", "2020-01-01", "2020-01-20", "2020-02-17"}

SAMPLES = {
    "weekday": lambda x: (x.dow < 5) & (~x.hol) & (x.hh >= 7) & (x.hh <= 18),
    "busway": lambda x: (x.hh >= 6) & (x.hh <= 21),
    "overnight": lambda x: (x.hh >= 22) | (x.hh <= 5),
}


def load(files) -> pd.DataFrame:
    df = pd.concat([pd.read_csv(f) for f in files])
    df["d"] = pd.to_datetime(df["d"])
    df["dow"] = df.d.dt.dayofweek
    df["hol"] = df.d.dt.strftime("%Y-%m-%d").isin(HOLIDAYS)
    df["treated"] = df.g == "t14"
    return df


def _window(df, w):
    return df[(df.d >= w[0]) & (df.d <= w[1])]


def _matrices(df, sample, w, var):
    x = _window(df, w)
    x = x[SAMPLES[sample](x)]
    s = x.groupby(["d", "pu", "do"])[[var, "n"]].sum()
    S = s[var].unstack(["pu", "do"]).fillna(0.0)
    N = s["n"].unstack(["pu", "do"]).fillna(0.0)
    return S, N


def did(df, sample, pre, post, var="s_lt", draws=DRAWS, seed=SEED):
    Sa, Na = _matrices(df, sample, pre, var)
    Sb, Nb = _matrices(df, sample, post, var)
    pairs = [p for p in Sa.columns if p in Sb.columns and Na[p].sum() >= MIN_TRIPS and Nb[p].sum() >= MIN_TRIPS]
    grp = df.drop_duplicates(["pu", "do"]).set_index(["pu", "do"]).g
    treated = np.array([grp[p] == "t14" for p in pairs])
    Sa, Na, Sb, Nb = (M[pairs].to_numpy() for M in (Sa, Na, Sb, Nb))

    def est(wa, wb):
        ma = (wa @ Sa) / (wa @ Na)
        mb = (wb @ Sb) / (wb @ Nb)
        dp = mb - ma
        return dp[treated].mean() - dp[~treated].mean(), dp

    point, dp = est(np.ones(len(Sa)), np.ones(len(Sb)))
    rng = np.random.default_rng(seed)
    bs = np.empty(draws)
    for i in range(draws):
        wa = rng.multinomial(len(Sa), np.full(len(Sa), 1 / len(Sa)))
        wb = rng.multinomial(len(Sb), np.full(len(Sb), 1 / len(Sb)))
        bs[i] = est(wa, wb)[0]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    pct = lambda v: 100 * (np.exp(v) - 1)
    return {"sample": sample, "var": var, "pre": list(pre), "post": list(post),
            "did_pct": round(float(pct(point)), 3), "lo_pct": round(float(pct(lo)), 3), "hi_pct": round(float(pct(hi)), 3),
            "se_log": round(float(bs.std()), 5), "n_pairs_treated": int(treated.sum()), "n_pairs_control": int((~treated).sum()),
            "trips_pre": int(Na.sum()), "trips_post": int(Nb.sum()), "treated_trips_pre": int(Na[:, treated].sum()),
            "treated_trips_post": int(Nb[:, treated].sum()),
            "pair_changes_pct": {f"{p[0]}-{p[1]}": round(float(pct(v)), 2) for p, v in zip(pairs, dp)},
            "draws": draws, "seed": seed}
