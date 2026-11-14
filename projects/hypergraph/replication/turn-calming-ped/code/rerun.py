"""Rerun the deciding number of turn-calming-ped, and the referee's placebo, from the package's inputs.

The claim's script, analyses/turn_restrictions/did.py, reads 1.8 million crash records from
~/opt/nyc-concordance/turn_restrictions/, fits four outcomes and three checks, and writes did_results.json into
the repository. The crash file is 174 MB, so the package carries the crashes within 40.5 m of a calming site
with at least one pedestrian injured or killed (inputs/prepared/, cut by code/prepare.py); the pedestrian
count within 40 m is a sum over these crashes only. This wrapper
points did.OPT at that folder, calls load_crashes(), site_monthly(), stack() and fit() unchanged for the
pedestrian outcome, and then reruns the exploratory placebo of did_explore.py (installation moved 12 months
early) with its window_factory() unchanged.
"""
import argparse, contextlib, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))
sys.path.insert(0, str(PKG / "code" / "analyses" / "turn_restrictions"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
import did as D  # noqa: E402
import did_explore as E  # noqa: E402

D.OPT = INP / "prepared" / "turn_restrictions"
D.OUT = INP / "data" / "derived" / "turn_restrictions"
sites = json.loads((D.OUT / "sites.json").read_text())["sites"]
X, Y, M, PED, LT, _ = D.load_crashes()
counts = D.site_monthly(sites, X, Y, M, PED, LT)
r = D.fit(D.stack(sites, counts, "ped"))
orig = D.window
D.window = E.window_factory(-24, -13, -12, -1)
pl = D.fit(D.stack(sites, counts, "ped"))
D.window = orig
print(json.dumps({"estimate": r["ror"], "lo": r["lo"], "hi": r["hi"], "n": r["n_treated_sites"],
                  "treated_pre": r["treated_pre"], "treated_post": r["treated_post"],
                  "placebo_12m_ror": pl["ror"], "placebo_12m_lo": pl["lo"], "placebo_12m_hi": pl["hi"]}))
