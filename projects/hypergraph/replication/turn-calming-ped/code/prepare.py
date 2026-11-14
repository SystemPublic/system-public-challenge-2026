"""Build the prepared inputs of this package from the files they are cut from.

The builder ran this file once, with ROOT the repository, OPT ~/opt/nyc-concordance and OUT the folder whose
contents became inputs/prepared/. A reader who has the source files (pointed to by sha256 in manifest.json,
inputs.files[].prepared_from) can run it the same way and compare the sha256 of each output.
    python code/prepare.py ROOT OPT OUT
"""
import sys
from pathlib import Path
ROOT, OPT, OUT = (Path(a) for a in sys.argv[1:4])
sys.path.insert(0, str(ROOT))

# Keep the crashes with at least one pedestrian injured or killed that lie within 40.5 m of a left-turn calming
# site, after the same coordinate filter that did.load_crashes() applies. The pedestrian count within 40 m of a
# site (the deciding outcome and the placebo) is a sum over these crashes only; the others add zero. The rings (50-200 m) are not reproduced from this cut.
import csv, json, math
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(ROOT / "analyses" / "turn_restrictions"))
from sites import xy
src = OPT / "turn_restrictions"
sites = json.loads((ROOT / "data/derived/turn_restrictions/sites.json").read_text())["sites"]
tree = cKDTree(np.array([[s["x"], s["y"]] for s in sites]))
dst = OUT / "prepared" / "turn_restrictions"
dst.mkdir(parents=True, exist_ok=True)
keep_ids, n_in, n_out = set(), 0, 0
with open(src / "crashes.csv", newline="") as fi, open(dst / "crashes.csv", "w", newline="") as fo:
    rd = csv.DictReader(fi)
    cols = ["collision_id", "crash_date", "latitude", "longitude", "number_of_pedestrians_injured",
            "number_of_pedestrians_killed"]
    wr = csv.DictWriter(fo, fieldnames=cols, quoting=csv.QUOTE_ALL, lineterminator="\n", extrasaction="ignore")
    wr.writeheader()
    for r in rd:
        n_in += 1
        try:
            lat, lon = float(r["latitude"]), float(r["longitude"])
        except (TypeError, ValueError):
            continue
        if not (40.45 < lat < 40.95 and -74.3 < lon < -73.65):
            continue
        if int(r["number_of_pedestrians_injured"] or 0) + int(r["number_of_pedestrians_killed"] or 0) == 0:
            continue
        x, y = xy(lat, lon)
        if tree.query_ball_point([x, y], 40.5):
            wr.writerow(r)
            keep_ids.add(r["collision_id"])
            n_out += 1
with open(src / "left_vehicles.csv", newline="") as fi, open(dst / "left_vehicles.csv", "w", newline="") as fo:
    rd = csv.DictReader(fi)
    wr = csv.DictWriter(fo, fieldnames=["collision_id"], quoting=csv.QUOTE_ALL, lineterminator="\n", extrasaction="ignore")
    wr.writeheader()
    for r in rd:
        if r["collision_id"] in keep_ids:
            wr.writerow(r)
print(json.dumps({"crashes_read": n_in, "crashes_kept": n_out}))
