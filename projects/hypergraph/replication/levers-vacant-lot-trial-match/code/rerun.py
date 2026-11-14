"""Rerun the deciding number of levers-vacant-lot-trial-match from the package's inputs.

The claim's script, analyses/levers/lot_test.py, reads three derived tables from data/derived/levers/ and
writes its results there. This wrapper copies the three tables from the package's inputs into work/, points
lot_test.D at that folder, calls lot_test.main() unchanged and prints the trial-like share and counts.
The upstream stages (lots_fetch.py, Socrata records; lot_ndvi.py, NAIP imagery) are not rerun.
"""
import argparse, contextlib, json, shutil, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun tried to fetch {a[:1]}")


requests.get = _offline
from analyses.levers import lot_test  # noqa: E402

work = PKG / "work" / "levers"
work.mkdir(parents=True, exist_ok=True)
for f in ("lots_records.csv", "lots_naip.csv", "shootings_2023_2025.csv"):
    shutil.copyfile(INP / "data" / "derived" / "levers" / f, work / f)
lot_test.D = work
with contextlib.redirect_stdout(sys.stderr):
    lot_test.main()
res = json.loads((work / "lot_test_results.json").read_text())
print(json.dumps({"estimate": res["trial_like_share"], "n": res["n_lu11_in_high_shooting_tracts"],
                  "trial_like_n": res["trial_like_n"],
                  "shootings_within_300m_per_year": res["shootings_within_300m_trial_like_per_year"]}))
