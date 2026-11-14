"""Rerun the deciding number of street-busway14-m14-speed, and its 119 placebo DiDs, from the package's inputs.

The claim's script, analyses/street_space/bus.py, has two stages: design() computes the placebo DiDs (each other
Manhattan route as if treated, seasons 2021-2023) and writes bus_design.json; final() reads it, computes the M14
DiD with the placebo standard deviation as its standard error and writes bus_final.json. This wrapper points the
Socrata cache at the package's inputs, blocks network access, sets bus.DER to work/street_space inside the
package, and calls design() and final() unchanged.
"""
import argparse, contextlib, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
from concord import socrata  # noqa: E402

socrata.CACHE = INP / "data" / "cache" / "socrata"
from analyses.street_space import bus  # noqa: E402

work = PKG / "work" / "street_space"
work.mkdir(parents=True, exist_ok=True)
bus.DER = work
with contextlib.redirect_stdout(sys.stderr):
    bus.design()
    bus.final()
d = json.loads((work / "bus_design.json").read_text())
f = json.loads((work / "bus_final.json").read_text())
import numpy as np  # noqa: E402
m14_log = float(np.log(1 + f["did_pct"] / 100))
print(json.dumps({"estimate": f["did_pct"], "lo": f["lo_pct"], "hi": f["hi_pct"], "n": f["n_controls"],
                  "se_log": f["se_log"], "placebo_sd_log": d["sd_log"], "placebo_n": d["n"],
                  "placebo_n_as_large": int(sum(p["did_log"] >= m14_log for p in d["placebo"]))}))
