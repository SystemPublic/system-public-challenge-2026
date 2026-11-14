"""Composed predictions for the two bridges, computed from the link estimates only.

This script reads no endpoint data. It is run, and its output committed, before
the endpoint datasets (NYPD crashes h9gi-nx95 by zone; FDNY EMS dispatches
76xm-jjuj by day) are queried for these claims.

Bridge 1, bridge-crz-injury-crashes
  log RR(injury crashes, zone vs rest of city, 2025 vs 2022-24)
      = E_speed * log(1 + dS) + b_vol * log(1 + dV)
  dS     relative speed change, mob-crz-traffic: +5.75% (2.95 to 8.62), normal on log scale
  dV     relative vehicle volume change in the zone: -7.6% (-3 to -12), normal on log scale.
         From mob-crz-traffic notes: TLC trips -9.8% relative to outside (about half of it a
         pre-existing trend), MTA zone vehicle-miles -3.8% (AGPS) to -11.0% (connected vehicles)
         against 2024, no comparison area.
  E_speed power-model exponent for injury crashes on urban roads, Elvik (2009): 1.2.
         Draw N(1.2, 0.5) truncated at 0; the urban estimate rests on few studies.
  b_vol  elasticity of injury crashes with respect to traffic volume, N(0.9, 0.2) truncated at 0
         (range of exponents in safety performance functions for urban roads, about 0.5 to 1.3).
  Severity companion: persons killed, E = 2.6 (Elvik 2009 urban, fatal accidents), N(2.6, 0.8).

Bridge 2, bridge-heat-shootings-ems
  IRR(EMS gunshot dispatches per 5 C) = w * IRR_s + (1 - w) * IRR_s ** k
  IRR_s  heat-shootings: 1.146 (1.130 to 1.163) per 5 C, normal on log scale
  w      share of SHOT dispatches that are victims of NYPD-recorded shooting incidents, U(0.25, 0.5)
  k      temperature gradient of the other SHOT dispatches (shots-fired reports without a recorded
         victim, unfounded and duplicate calls) as a fraction of the shootings gradient, U(0, 1)
"""
from __future__ import annotations

import json

import numpy as np

from analyses.bridges.common import DER, NDRAW, SEED


def lognorm_from_ci(rng, est, lo, hi, n):
    m = np.log(est)
    sd = (np.log(hi) - np.log(lo)) / 3.92
    return np.exp(rng.normal(m, sd, n))


def tnorm(rng, mu, sd, n, lo=0.0):
    x = rng.normal(mu, sd, n)
    bad = x < lo
    while bad.any():
        x[bad] = rng.normal(mu, sd, bad.sum())
        bad = x < lo
    return x


def summary(x, pct=True):
    q = np.quantile(x, [0.025, 0.5, 0.975])
    f = (lambda v: 100 * (v - 1)) if pct else (lambda v: v)
    return {"median": float(f(q[1])), "lo": float(f(q[0])), "hi": float(f(q[2])),
            "mean_log": float(np.mean(np.log(x))), "sd_log": float(np.std(np.log(x))),
            "p_below_null": float(np.mean(x < 1))}


def bridge1(rng):
    n = NDRAW
    s = lognorm_from_ci(rng, 1.0575, 1.0295, 1.0862, n)
    m_v = (np.log(0.97) + np.log(0.88)) / 2
    sd_v = (np.log(0.97) - np.log(0.88)) / 3.92
    v = np.exp(rng.normal(m_v, sd_v, n))
    e = tnorm(rng, 1.2, 0.5, n)
    b = tnorm(rng, 0.9, 0.2, n)
    speed_term = s ** e
    vol_term = v ** b
    rr = speed_term * vol_term
    e_fat = tnorm(rng, 2.6, 0.8, n)
    rr_fat = s ** e_fat * vol_term
    # point composition with central values, for the text
    point = 1.0575 ** 1.2 * np.exp(m_v) ** 0.9
    return {
        "links": {
            "speed_change_pct": {"est": 5.75, "lo": 2.95, "hi": 8.62, "from": "mob-crz-traffic"},
            "volume_change_pct": {"est": float(100 * (np.exp(m_v) - 1)), "lo": -12.0, "hi": -3.0,
                                  "from": "mob-crz-traffic notes (TLC trips, MTA VMT)"},
            "E_speed_injury": {"mean": 1.2, "sd": 0.5, "from": "Elvik 2009, urban injury accidents"},
            "b_volume": {"mean": 0.9, "sd": 0.2, "from": "safety performance function exponents, urban"},
            "E_speed_fatal": {"mean": 2.6, "sd": 0.8, "from": "Elvik 2009, urban fatal accidents"},
        },
        "speed_term_pct": summary(speed_term),
        "volume_term_pct": summary(vol_term),
        "composed_injury_crashes_pct": summary(rr),
        "composed_injury_crashes_point_pct": float(100 * (point - 1)),
        "composed_fatal_pct": summary(rr_fat),
        "nilsson_E2_point_pct": float(100 * (1.0575 ** 2 * np.exp(m_v) ** 0.9 - 1)),
    }


def bridge2(rng):
    n = NDRAW
    irr_s = lognorm_from_ci(rng, 1.146, 1.130, 1.163, n)
    w = rng.uniform(0.25, 0.5, n)
    k = rng.uniform(0.0, 1.0, n)
    irr = w * irr_s + (1 - w) * irr_s ** k
    return {
        "links": {
            "irr_shootings_per5C": {"est": 1.146, "lo": 1.130, "hi": 1.163, "from": "heat-shootings"},
            "w_share_victim_dispatches": {"uniform": [0.25, 0.5]},
            "k_gradient_other_dispatches": {"uniform": [0.0, 1.0]},
        },
        "composed_irr_per5C": {**summary(irr, pct=False)},
        "bounds": {"if_only_victims_follow_heat": float(1 + 0.375 * 0.146), "if_all_follow_heat": 1.146},
    }


def main():
    rng = np.random.default_rng(SEED)
    out = {"seed": SEED, "draws": NDRAW, "bridge-crz-injury-crashes": bridge1(rng),
           "bridge-heat-shootings-ems": bridge2(rng)}
    (DER / "composed_predictions.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
