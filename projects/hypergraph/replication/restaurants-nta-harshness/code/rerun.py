"""Rerun the deciding number of restaurants-nta-harshness from the package's inputs.

The claim's script, analyses/restaurants/evenness_test.py, reads the Underlay snapshot nyc/restaurant-inspections
v1.0.0 (51 MB) from ~/opt/nyc-concordance/underlay/, runs the harshness and frequency tests, and writes into the
repository. The package carries the snapshot with only the fields load_snapshot() reads (inputs/prepared/, cut by
code/prepare.py). This wrapper unpacks it into work/, points evenness_test.SNAP and common.DER at the package,
calls load_snapshot(), assign_nta(), design(), permutation() (10,000 draws, seed 20261113) and nta_effects()
unchanged, and repeats the lines of main() that build the harshness frame.
"""
import argparse, gzip, json, shutil, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))
sys.path.insert(0, str(PKG / "code" / "analyses" / "restaurants"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
import numpy as np  # noqa: E402
import common as c  # noqa: E402
import evenness_test as E  # noqa: E402

work = PKG / "work"
work.mkdir(exist_ok=True)
snap = work / "records_v1.0.0_min.ndjson"
with gzip.open(INP / "prepared" / "underlay" / "records_v1.0.0_min.ndjson.gzip", "rb") as fi, open(snap, "wb") as fo:
    shutil.copyfileobj(fi, fo)
E.SNAP = snap
c.DER = INP / "data" / "derived" / "restaurants"

R, I = E.load_snapshot()
Rn = E.assign_nta(R)
counts = Rn.groupby("nta2020").size()
keep = counts[counts >= E.MIN_REST].index
Rn = Rn[Rn.nta2020.isin(keep)].copy()
Rn["log_nta_rest"] = np.log(Rn.nta2020.map(counts))
Rn["cuis"] = c.cuisine_group(Rn.cuisine)
nm = c.norm_dba(Rn.name)
Rn["chain"] = nm.map(nm.value_counts()).ge(5).astype(float)
I = I.sort_values("date")
first = I.groupby("camis").head(1).set_index("camis")
Rn["new"] = Rn.camis.map(first.itype.str.startswith("Pre-permit")).fillna(False).astype(float)
work_n = I.groupby("date").size()
ci = I[I.itype == "Cycle Inspection / Initial Inspection"].merge(Rn, on="camis")
ci["log_work"] = np.log(ci.date.map(work_n))
ci["q"] = ci.date.dt.to_period("Q").astype(str)
ci["dow"] = ci.date.dt.dayofweek.astype(str)
Xh = E.design(ci, ["cuis", "chain", "q", "dow", "log_work", "log_nta_rest", "new"], ["cuis", "q", "dow"])
harsh, _ = E.permutation(ci, "n_crit", Xh)
_, _, tau = E.nta_effects(ci, "n_crit", Xh)
print(json.dumps({"estimate": tau, "n": int(len(ci)), "permutation_p": harsh["p"], "n_ntas": harsh["n_ntas"],
                  "n_restaurants": int(ci.camis.nunique()), "S_over_null_mean": harsh["S_ratio"]}))
