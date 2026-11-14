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

# Read the crash and vehicle records with rlc_did.fetch_crashes() from the repository's Socrata cache (the seven
# h9gi-nx95 pages and the bm4k-52h4 page), and keep the crashes within 50.5 m of a camera intersection or of an
# intersection in the control pool. rlc_did.build() sums crashes within 50 m of these points only, so the matched
# sets, the deciding ratio and the placebo are the same on this cut. Written as gzipped JSON with a fixed timestamp.
import gzip, json
import numpy as np
from concord import socrata
socrata.requests.get = None  # the cache must answer every query; a missing page fails here
sys.path.insert(0, str(ROOT / "analyses" / "street_safety"))
import rlc_did as R
from scipy.spatial import cKDTree
treated, all_cam, _ = R.load_sites()
pool = R.control_pool(all_cam)
pts = [R.xy(s["lat"], s["lon"]) for s in treated] + [R.xy(r["lat"], r["lon"]) for r in pool]
tree = cKDTree(np.array([[float(x), float(y)] for x, y in pts]))
rows, _ = R.fetch_crashes()
cx, cy, _, _ = R.crash_arrays(rows)
d, _ = tree.query(np.c_[cx, cy], k=1)
keep = [r for r, di in zip(rows, d) if di <= 50.5]
dst = OUT / "prepared" / "street_safety"
dst.mkdir(parents=True, exist_ok=True)
with open(dst / "crashes_near_sites.json.gzip", "wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as fo:
        fo.write(json.dumps(keep, sort_keys=True, separators=(",", ":")).encode())
print(json.dumps({"crashes_read": len(rows), "crashes_kept": len(keep)}))
