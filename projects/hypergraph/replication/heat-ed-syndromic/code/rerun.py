"""Rerun the deciding number of heat-ed-syndromic from the package's inputs.

The claim's script, analyses/heat/ed_syndromic.py, fits the primary model, a spline curve, a piecewise model and a
yearly correlation, and writes five files into data/derived/heat/. This wrapper points its EHDP cache and the NOAA
cache at the package's inputs, blocks network access, calls load() and nb_fit() unchanged and repeats only the
lines of main() that build the model frame and fit the primary model.
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
from concord import noaa  # noqa: E402

noaa.CACHE = INP / "data" / "cache" / "noaa"
from analyses.heat import ed_syndromic as E  # noqa: E402
from analyses.heat.common import holidays  # noqa: E402

E.CACHE = INP / "data" / "derived" / "heat" / "ehdp"
ed, supp = E.load()
w, _ = noaa.daily("central_park")
d = ed.join(w[["TMAX", "TMIN", "PRCP"]], how="left")
d = d[d.index.month.isin([5, 6, 7, 8, 9])].dropna(subset=["TMAX", "HEAT_ED_VISIT_COUNT"]).copy()
d["n"] = d["HEAT_ED_VISIT_COUNT"].astype(int)
d["dow"] = d.index.day_of_week
d["month"] = d.index.month
d["year"] = d.index.year
d["hol"] = d.index.isin(holidays(str(d.index.min().date()), str(d.index.max().date()))).astype(int)
d["t5"] = d["TMAX"] / 5.0
res, alpha = E.nb_fit("n ~ t5 + C(dow) + C(month) + C(year) + hol", d)
r = E.irr(res, "t5")
print(json.dumps({"estimate": r["estimate"], "lo": r["lo"], "hi": r["hi"], "n": int(len(d)),
                  "n_visits": int(d["n"].sum()), "alpha": alpha}))
