"""Rerun the deciding number of food-supermarket-diabetes-zcta from the package's inputs.

The claim's script, analyses/health_gaps/food_access.py, builds a ZCTA table from Census files kept in
~/opt/nyc-concordance/census (zctas()), the Retail Food Stores query (stores()) and the SPARCS PQI query (pqi()),
fits ten models and writes into data/derived/health_gaps/. This wrapper reruns stores() and pqi() unchanged from the
cached Socrata responses, takes the Census columns that zctas() produced from the derived table food_zcta.csv
(the Census files are not carried), repeats the merge and filter of main() and fits the primary model with fit()
and coef() unchanged. It also prints the unadjusted ratio.
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
import pandas as pd  # noqa: E402
from concord import socrata  # noqa: E402

socrata.CACHE = INP / "data" / "cache" / "socrata"
from analyses.health_gaps import food_access as F  # noqa: E402

CENSUS = ["zcta", "county", "ALAND", "pop", "adults", "density", "poverty", "income", "med_age", "black", "hisp",
          "nocar", "land_km2"]
z = pd.read_csv(INP / "data" / "derived" / "health_gaps" / "food_zcta.csv", dtype={"zcta": str})[CENSUS]
st, _ = F.stores()
pq, _, years, pqis = F.pqi()
d = z.merge(st, on="zcta", how="left").merge(pq, on="zcta", how="inner")
for c in ("stores_all", "super6k", "super10k"):
    d[c] = d[c].fillna(0)
d = d[(d.adults >= 5000) & (d.obs > 0) & (d.exp > 0)].dropna(subset=["poverty", "income", "med_age"])
d["y"] = np.log(d.obs / d.exp)
d["x"] = np.log2((d.super6k + 0.5) / d["pop"] * 1e4)
d["ldens"] = np.log2(d.density)
d["linc"] = np.log2(d.income)
base = "ldens + poverty + linc + med_age"
p = F.coef(F.fit(d, f"x + {base}"), "x")
u = F.coef(F.fit(d, "x"), "x")
print(json.dumps({"estimate": p["ratio"], "lo": p["lo"], "hi": p["hi"], "n": p["n"], "years": years,
                  "unadjusted": u["ratio"], "unadjusted_lo": u["lo"], "unadjusted_hi": u["hi"]}))
