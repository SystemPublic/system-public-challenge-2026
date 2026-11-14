"""Rerun the deciding number of bridge-heat-shootings-ems from the package's inputs.

The claim's script, analyses/bridges/ems_shot.py, builds the heat-shootings daily frame (analyses/heat/shootings.py
build()), adds daily FDNY EMS dispatch counts (ems_daily()), fits a link model, the endpoint model and four
sensitivity models, and writes into data/derived/bridges/. It reads the composed prediction from
composed_predictions.json, written by analyses/bridges/compose.py. This wrapper points the Socrata and NOAA caches at
the package's inputs, blocks network access, reruns compose.py's bridge1() and bridge2() with its seed and draw count
(bridge1 first, as in compose.main(), since both draw from one generator), calls build(), ems_daily(), nb_fit(), irr()
and compat() unchanged, and prints the endpoint IRR, its compatibility with the composed prediction, and the STAB
contrast that the registration names as a check outside the causal chain.
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
import numpy as np  # noqa: E402
from concord import noaa, socrata  # noqa: E402

socrata.CACHE = INP / "data" / "cache" / "socrata"
noaa.CACHE = INP / "data" / "cache" / "noaa"
from analyses.bridges import compose, ems_shot as B  # noqa: E402
from analyses.bridges.common import SEED  # noqa: E402

rng = np.random.default_rng(SEED)
compose.bridge1(rng)
comp = compose.bridge2(rng)["composed_irr_per5C"]

df, _ = B.build()
w, _ = B.ems_daily()
for c in ("SHOT", "T-SHOT", "STAB"):
    df[c] = w[c].reindex(df.index).fillna(0).astype(int) if c in w else 0
df = df.dropna(subset=["TMAX"])
r, alpha = B.nb_fit(B.FORM.format(x="t5").replace("n ~", "SHOT ~"), df)
e = B.irr(r, "t5")
c = B.compat(float(r.params["t5"]), float(r.bse["t5"]), comp["mean_log"], comp["sd_log"])
s = B.irr(B.nb_fit(B.FORM.format(x="t5").replace("n ~", "STAB ~"), df)[0], "t5")
print(json.dumps({"estimate": e["estimate"], "lo": e["lo"], "hi": e["hi"], "n": int(len(df)), "alpha": alpha,
                  "composed_median": comp["median"], "compat_z": c["z"], "stab_contrast": s["estimate"],
                  "stab_contrast_lo": s["lo"], "stab_contrast_hi": s["hi"]}))
