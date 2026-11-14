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

# Keep, for every record of the Underlay snapshot, the type, the id and the data fields that
# evenness_test.load_snapshot() reads, in the snapshot's own order; drop the other fields and the record hashes.
# Write it gzipped with a fixed timestamp, so the same snapshot always gives the same bytes.
import gzip, json
KEEP = {"Restaurant": ("name", "cuisineDescription", "latitude", "longitude"),
        "Inspection": ("restaurantId", "inspectionDate", "inspectionType", "score", "grade"),
        "Violation": ("inspectionId", "criticalFlag")}
dst = OUT / "prepared" / "underlay"
dst.mkdir(parents=True, exist_ok=True)
n = 0
with open(OPT / "underlay" / "records_v1.0.0.ndjson") as fi, open(dst / "records_v1.0.0_min.ndjson.gzip", "wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as fo:
        for line in fi:
            r = json.loads(line)
            d = r["data"]
            k = KEEP.get(r["type"], KEEP["Violation"])
            fo.write((json.dumps({"id": r["id"], "type": r["type"], "data": {x: d[x] for x in k if x in d}},
                                 separators=(",", ":"), ensure_ascii=False) + "\n").encode())
            n += 1
print(json.dumps({"records": n}))
