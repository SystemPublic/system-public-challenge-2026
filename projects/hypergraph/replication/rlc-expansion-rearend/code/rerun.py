"""Rerun the deciding number of rlc-expansion-rearend, and its registered placebo, from the package's inputs.

The claim's script, analyses/street_safety/rlc_did.py, reads 323,685 crash records (h9gi-nx95, seven cached pages,
120.7 MB) and the rear-end vehicle records (bm4k-52h4), matches each camera intersection to three control
intersections, and writes its results into the repository. The package carries the crashes within 50.5 m of a
camera or control intersection (inputs/prepared/, cut by code/prepare.py from the cached pages, which are pointed
to by sha256); build() sums crashes within 50 m of these points only. This wrapper replaces fetch_crashes() with a
reader of that cut, and calls load_sites(), control_pool(), crash_arrays(), build(), placebo(), rr_from() and boot()
unchanged (B=2000, seed 20261113) for the rear-end outcome and for the registered placebo year.
"""
import argparse, gzip, json, sys
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
from analyses.street_safety import rlc_did as R  # noqa: E402

R.DER = INP / "data" / "derived" / "street_safety"
with gzip.open(INP / "prepared" / "street_safety" / "crashes_near_sites.json.gzip", "rb") as f:
    rows = json.loads(f.read())
treated, all_cam, _ = R.load_sites()
pool = R.control_pool(all_cam)
cx, cy, cym, vals = R.crash_arrays(rows)
out = {}
for tag, sets in (("", R.build(treated, pool, cx, cy, cym, vals)), ("placebo_", R.placebo(treated, pool, cx, cy, cym, vals))):
    rr, parts = R.rr_from(sets, "rear_end")
    lo, hi, se = R.boot(sets, "rear_end")
    out.update({f"{tag}estimate": round(rr, 4), f"{tag}lo": round(lo, 4), f"{tag}hi": round(hi, 4), f"{tag}n": len(sets)})

print(json.dumps(out))
