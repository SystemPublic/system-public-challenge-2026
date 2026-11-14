"""Rerun the deciding number of heat-shootings from the package's inputs.

The claim's script, analyses/heat/shootings.py, runs the primary model and every sensitivity analysis and
writes its results into the repository's data/derived/heat/. This wrapper is the smallest change that reruns
only the deciding number: it points the Socrata and NOAA caches at the package's inputs, blocks network access,
calls shootings.build() and shootings.nb_fit() unchanged, and prints the IRR per 5 C of Central Park TMAX.
"""
import argparse, json, sys
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
from concord import noaa, socrata  # noqa: E402

socrata.CACHE = INP / "data" / "cache" / "socrata"
noaa.CACHE = INP / "data" / "cache" / "noaa"
from analyses.heat import shootings  # noqa: E402

df, _ = shootings.build()
d = df.dropna(subset=["TMAX"])
res, alpha = shootings.nb_fit(shootings.FORM.format(x="t5"), d)
r = shootings.irr(res, "t5")
print(json.dumps({"estimate": r["estimate"], "lo": r["lo"], "hi": r["hi"], "n": int(len(d)),
                  "n_incidents": int(d["n"].sum()), "alpha": alpha}))
