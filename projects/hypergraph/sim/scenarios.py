"""Toll schedules to compare, as tables [weekday Mon..Fri, band night/am/mid/pm] in dollars.

A revenue-neutral version multiplies the three daytime tolls of a schedule by one factor,
found by bisection at the central parameter values, so that weekday revenue equals that of
the current schedule. Revenue then differs from the current schedule only through
parameter uncertainty. Only the daytime tolls are scaled and only weekday revenue is held.
The bisection needs revenue to rise with the factor, which `revenue_neutral` checks.

With exponential demand and one toll response for every cell, revenue is concave in the toll,
so a schedule that spreads tolls needs a higher traffic-weighted mean toll to hold revenue.
Every revenue-neutral schedule therefore lowers total entries. That is a property of the
functional form and not a finding (critique/sim-crz-holdout-2026.md, simulator defect 2).
"""
from __future__ import annotations

import numpy as np

from sim import model

NIGHT, DAY = 0, slice(1, 4)


def flat(P, peak=None, night=None) -> np.ndarray:
    t = model.toll_now(P).copy()
    if peak is not None:
        t[:, DAY] = peak
    if night is not None:
        t[:, NIGHT] = night
    return t


def weekday_peaks(P, peaks) -> np.ndarray:
    t = flat(P)
    for w, p in enumerate(peaks):
        t[w, DAY] = p
    return t


def evening(P, pm) -> np.ndarray:
    t = flat(P)
    t[:, 3] = pm
    return t


def revenue_neutral(P, toll: np.ndarray) -> tuple[np.ndarray, float]:
    c = model.central(P)
    target = model.simulate(P, model.toll_now(P), c)["revenue_musd"][0]
    lo, hi = 0.2, 3.0

    def rev(f):
        t = toll.copy()
        t[:, DAY] = toll[:, DAY] * f
        return model.simulate(P, t, c)["revenue_musd"][0]

    grid = [rev(f) for f in np.linspace(lo, hi, 57)]
    if not (np.all(np.diff(grid) > 0) and grid[0] < target < grid[-1]):
        raise ValueError("revenue does not rise with the scaling factor over 0.2 to 3.0, so bisection cannot be used")
    for _ in range(60):
        f = (lo + hi) / 2
        t = toll.copy()
        t[:, DAY] = toll[:, DAY] * f
        if model.simulate(P, t, c)["revenue_musd"][0] < target:
            lo = f
        else:
            hi = f
    t = toll.copy()
    t[:, DAY] = toll[:, DAY] * f
    return t, f


def build(P) -> dict[str, dict]:
    S = {
        "current": dict(label="Current: $9 on every weekday, 05:00-21:00", toll=flat(P)),
        "midweek_high": dict(label="Tue-Thu $12, Mon and Fri $6", toll=weekday_peaks(P, [6, 12, 12, 12, 6])),
        "monfri_high": dict(label="Mon and Fri $12, Tue-Thu $6", toll=weekday_peaks(P, [12, 6, 6, 6, 12])),
        "evening_high": dict(label="$13.50 from 16:00 to 21:00, $9 before", toll=evening(P, 13.5)),
        "uniform_12": dict(label=f"${P['constants']['phase2_peak_toll']:g} on every weekday (the 2028 rate)",
                           toll=flat(P, peak=P["constants"]["phase2_peak_toll"])),
    }
    for k in ("midweek_high", "monfri_high", "evening_high"):
        t, f = revenue_neutral(P, S[k]["toll"])
        S[k + "_rn"] = dict(label=S[k]["label"].split(",")[0] + f" pattern, scaled by {f:.3f} to hold revenue", toll=t, factor=f)
    return S
