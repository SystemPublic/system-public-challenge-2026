"""Exposure metrics: peak, minutes above thresholds, mean kinetic temperature.

Mean kinetic temperature (USP <1079.2>, Haynes 1971):

    T_mk = (dH/R) / ( -ln( (1/n) * sum_i exp(-dH / (R * T_i)) ) )      [K]

for n equally spaced temperatures T_i (kelvin).  dH defaults to 83.144 kJ/mol,
which makes dH/R = 10 000 K.  By Jensen's inequality T_mk >= arithmetic mean,
with equality only for a constant history.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, Optional, Sequence

import numpy as np

from .params import v

THRESHOLDS_C = (25.0, 30.0, 37.0, 40.0)


def mkt_c(temps_c: Sequence[float], delta_h_kj_mol: Optional[float] = None) -> float:
    dh = (delta_h_kj_mol if delta_h_kj_mol is not None else v("mkt", "delta_h_kj_mol")) * 1000.0
    r = v("mkt", "R_gas")
    a = dh / r
    tk = np.asarray(temps_c, float) + 273.15
    # log-mean-exp for numerical safety
    x = -a / tk
    m = x.max()
    lme = m + math.log(np.mean(np.exp(x - m)))
    return a / (-lme) - 273.15


def minutes_above(temps_c: Sequence[float], thr: float, dt_s: float) -> float:
    return float(np.sum(np.asarray(temps_c) > thr) * dt_s / 60.0)


def minutes_outside(temps_c: Sequence[float], lo: float, hi: float, dt_s: float) -> float:
    t = np.asarray(temps_c)
    return float(np.sum((t < lo) | (t > hi)) * dt_s / 60.0)


def summarize(temps_c: Sequence[float], dt_s: Optional[float] = None,
              delta_h_kj_mol: Optional[float] = None,
              thresholds: Iterable[float] = THRESHOLDS_C) -> Dict[str, object]:
    """Metrics over a trace whose first sample is the initial state.

    Time-weighted metrics use samples[1:] (each sample closes one dt interval);
    peak/min use all samples.
    """
    dt = dt_s if dt_s is not None else v("num", "dt_s")
    t = np.asarray(temps_c, float)
    body = t[1:] if len(t) > 1 else t
    return {
        "peak_c": round(float(t.max()), 3),
        "min_c": round(float(t.min()), 3),
        "mean_c": round(float(body.mean()), 3),
        "mkt_c": round(mkt_c(body, delta_h_kj_mol), 3),
        "minutes_above": {str(int(th)): minutes_above(body, th, dt) for th in thresholds},
        "duration_min": float(len(body) * dt / 60.0),
    }
