"""Composed prediction for bridge-crz-injury-crashes-v2, from link estimates only.

This script reads no crash data. It is run, and its output committed with the
registration, before the endpoint (NYPD crashes, h9gi-nx95) is queried for v2.

The v2 endpoint compares the zone with Manhattan north of 60th Street instead of
the rest of the city, so the speed link is the CBD-versus-CBD-Adjacent contrast
from mob-crz-traffic (data/derived/mobility/crz_traffic_results.json), +4.16%
(1.60 to 6.79), not the CBD-versus-Greater-NYC contrast (+5.75%). The MTA does
not publish the boundary of "CBD Adjacent"; it is taken as the nearest measured
stand-in for Manhattan north of 60th Street. The volume link, the speed exponent
and the volume elasticity are drawn exactly as in compose.py.

Primary: speed and volume drawn independently (as in v1).
Sensitivity (reported, not deciding): log speed change and log volume change
drawn with correlation -0.5, so that a larger speed rise goes with a larger
volume fall, as the referee suggested.
Output: data/derived/bridges/composed_predictions_v2.json
"""
from __future__ import annotations

import json

import numpy as np

from analyses.bridges.common import DER, NDRAW, ROOT
from analyses.bridges.compose import summary, tnorm

SEED_V2 = 20261113


def draw(rng, rho: float):
    tr = json.loads((ROOT / "data/derived/mobility/crz_traffic_results.json").read_text())
    tr = tr.get("results", tr)
    sp = tr["speed_CBD_vs_CBD Adjacent"]
    m_s, sd_s = sp["estimate_log"], sp["se"]
    m_v = (np.log(0.97) + np.log(0.88)) / 2
    sd_v = (np.log(0.97) - np.log(0.88)) / 3.92
    n = NDRAW
    z1 = rng.normal(size=n)
    z2 = rho * z1 + np.sqrt(1 - rho ** 2) * rng.normal(size=n)
    s = np.exp(m_s + sd_s * z1)
    v = np.exp(m_v + sd_v * z2)
    e = tnorm(rng, 1.2, 0.5, n)
    b = tnorm(rng, 0.9, 0.2, n)
    rr = s ** e * v ** b
    return {
        "speed_link": {"est_pct": sp["pct"], "lo_pct": sp["lo_pct"], "hi_pct": sp["hi_pct"],
                       "from": "mob-crz-traffic, CBD vs CBD Adjacent"},
        "rho_speed_volume": rho,
        "speed_term_pct": summary(s ** e),
        "volume_term_pct": summary(v ** b),
        "composed_injury_crashes_pct": summary(rr),
    }


def main():
    rng = np.random.default_rng(SEED_V2)
    out = {"seed": SEED_V2, "draws": NDRAW,
           "primary_independent": draw(rng, 0.0),
           "sensitivity_correlated": draw(rng, -0.5)}
    (DER / "composed_predictions_v2.json").write_text(json.dumps(out, indent=1))
    for k in ("primary_independent", "sensitivity_correlated"):
        c = out[k]["composed_injury_crashes_pct"]
        print(k, {a: round(b, 4) for a, b in c.items()})


if __name__ == "__main__":
    main()
