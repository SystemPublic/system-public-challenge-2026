"""Shared estimator for the re-timed-week consequence tests.

A panel has one row per unit (taxi zone or community district) and date with a
count n. For each unit and period the outcome is r = ln(mean Monday and Friday
count / mean Tuesday-to-Thursday count) over retained weeks; Y = r(recent) -
r(baseline). Retained weeks follow the dose map: no federal holiday and no day
from 24 December to 1 January in the week. Two further weeks are dropped in
2026 (Mondays 26 January and 23 February), when subway entries on the Monday
were 38% and 20% of that week's midweek level (docs/transit.md).

slope: OLS of Y on the exposure E across units (unweighted).
contrast: Y of pooled counts in one group of units minus Y in another.
Intervals: 2.5 and 97.5 percentiles of 2,000 bootstrap draws that resample
weeks within each period (all units together) and, for the slope, units too.
"""
from __future__ import annotations
import datetime as dt, importlib.util, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data/derived/round2/retimed_consequences"
sys.path.insert(0, str(ROOT))
_spec = importlib.util.spec_from_file_location("wp", ROOT / "analyses/transit/weekday_pattern.py")
STORM_WEEKS = {dt.date(2026, 1, 26), dt.date(2026, 2, 23)}


def retained_weeks(start: dt.date, end: dt.date) -> list[dt.date]:
    from concord import socrata
    dom = socrata.DOMAIN  # weekday_pattern.py points the client at data.ny.gov when it loads; put it back
    wp = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(wp)
    socrata.DOMAIN = dom
    return [w for w in wp.retained_weeks(start, end) if w not in STORM_WEEKS]


def week_arrays(panel: pd.DataFrame, units: list, weeks: list[dt.date]):
    """Return MF[u, w] (sum of Mon and Fri counts) and TWT[u, w] (sum of Tue-Thu counts)."""
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"]).dt.date
    wk = {w + dt.timedelta(i): (j, i) for j, w in enumerate(weeks) for i in range(5)}
    p = p[p.date.isin(wk) & p.unit.isin(units)]
    ui = {u: i for i, u in enumerate(units)}
    MF = np.zeros((len(units), len(weeks))); TWT = np.zeros_like(MF)
    for u, d, n in zip(p.unit, p.date, p.n):
        j, i = wk[d]
        (MF if i in (0, 4) else TWT)[ui[u], j] += n
    return MF, TWT


def _r(MF, TWT, idx=None):
    if idx is not None:
        MF, TWT = MF[:, idx], TWT[:, idx]
    return np.log((MF.sum(1) / 2) / (TWT.sum(1) / 3))


def estimate(A0, A1, E, groups: dict | None = None, B=2000, seed=7):
    """A0, A1: (MF, TWT) for baseline and recent. E: exposure per unit. groups: name -> boolean mask."""
    rng = np.random.default_rng(seed)
    E = np.asarray(E, float)
    groups = groups or {}

    def stats(i0, i1, iu):
        Y = _r(*A1, i1) - _r(*A0, i0)
        out = {"mean_Y": float(np.mean(Y[iu]))}
        x, y = E[iu], Y[iu]
        ok = np.isfinite(y)
        out["slope"] = float(np.polyfit(x[ok], y[ok], 1)[0]) if ok.sum() > 2 and np.ptp(x[ok]) > 0 else np.nan
        for g, m in groups.items():
            a = np.log((A1[0][m][:, i1].sum() / 2) / (A1[1][m][:, i1].sum() / 3)) - \
                np.log((A0[0][m][:, i0].sum() / 2) / (A0[1][m][:, i0].sum() / 3))
            out["Y_" + g] = float(a)
        return out

    n0, n1, nu = A0[0].shape[1], A1[0].shape[1], len(E)
    pt = stats(np.arange(n0), np.arange(n1), np.arange(nu))
    draws = [stats(rng.integers(0, n0, n0), rng.integers(0, n1, n1), rng.integers(0, nu, nu)) for _ in range(B)]
    d = pd.DataFrame(draws)
    res = {k: {"estimate": v, "lo": float(d[k].quantile(.025)), "hi": float(d[k].quantile(.975)), "se": float(d[k].std())}
           for k, v in pt.items()}
    gs = list(groups)
    for i in range(len(gs)):
        for j in range(i + 1, len(gs)):
            k = f"{gs[i]}_minus_{gs[j]}"
            dd = d["Y_" + gs[i]] - d["Y_" + gs[j]]
            res[k] = {"estimate": pt["Y_" + gs[i]] - pt["Y_" + gs[j]], "lo": float(dd.quantile(.025)),
                      "hi": float(dd.quantile(.975)), "se": float(dd.std())}
    res["n_units"] = nu; res["n_weeks"] = [n0, n1]
    return res
