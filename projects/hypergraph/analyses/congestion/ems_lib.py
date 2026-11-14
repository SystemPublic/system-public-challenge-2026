"""Estimators for the EMS and fire travel-time tests. Written before registration.

Panel: calendar month x area x toll period. y = log(sum of travel seconds / incidents) over
incidents with a valid response time. The contrast series is
    d_t = y(zone, period, t) - y(comparison, period, t)
and the difference-in-differences is the coefficient on post in an OLS of d_t on post and
calendar-month dummies, with Newey-West (HAC) standard errors, 3 lags. The triple difference
uses d_t(peak) - d_t(overnight). 1-4 January 2025 are dropped (before the toll).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from analyses.congestion.common import DER, is_peak

AREAS_OUT = ("north", "bklic", "rest")


def load(kind="ems", years=range(2019, 2025)) -> pd.DataFrame:
    df = pd.concat([pd.read_csv(DER / f"{kind}_{y}.csv") for y in years if (DER / f"{kind}_{y}.csv").exists()])
    df["d"] = pd.to_datetime(df["d"])
    df = df[~((df.d >= "2025-01-01") & (df.d < "2025-01-05"))]
    df["peak"] = is_peak(df.d.dt.dayofweek, df.hh)
    df["period"] = np.where(df.peak, "peak", "overnight")
    df["month"] = df.d.dt.to_period("M").dt.to_timestamp()
    return df


def panel(df, value="travel", by=("month", "area", "period"), where=None) -> pd.DataFrame:
    if where is not None:
        df = df[where(df)]
    g = df.groupby(list(by), as_index=False)[[value, "n"]].sum()
    g["y"] = np.log(g[value] / g["n"])
    return g


def series(p, zone="crz", comp=AREAS_OUT, period="peak", value="travel"):
    """Log ratio of mean travel time, zone over comparison (comparison areas pooled by incidents)."""
    q = p[p.period == period]
    z = q[q.area == zone].set_index("month")
    c = q[q.area.isin(list(comp))].groupby("month")[[value, "n"]].sum()
    return (np.log(z[value] / z["n"]) - np.log(c[value] / c["n"])).dropna().rename("d")


def did(d: pd.Series, start, pre_from, post_to=None, lags=3) -> dict:
    x = d[(d.index >= pd.Timestamp(pre_from))]
    if post_to is not None:
        x = x[x.index <= pd.Timestamp(post_to)]
    f = pd.DataFrame({"d": x.values, "post": (x.index >= pd.Timestamp(start)).astype(int), "calm": x.index.month})
    m = smf.ols("d ~ post + C(calm)", data=f).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    b, se = float(m.params["post"]), float(m.bse["post"])
    return {"log": b, "se": se, "pct": 100 * (np.exp(b) - 1), "lo": 100 * (np.exp(b - 1.96 * se) - 1),
            "hi": 100 * (np.exp(b + 1.96 * se) - 1), "n_months": int(m.nobs), "n_post": int(f.post.sum())}


def triple(p, zone="crz", comp=AREAS_OUT, value="travel"):
    return (series(p, zone, comp, "peak", value) - series(p, zone, comp, "overnight", value)).dropna()
