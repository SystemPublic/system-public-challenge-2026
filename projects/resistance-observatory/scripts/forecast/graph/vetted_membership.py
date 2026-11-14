"""Pin which pulled Graph records are in System's vetted associations CSV (Harvard Dataverse).

Usage (from the repo root):
  # download (442 MB, not committed) into a scratch folder, e.g.
  #   curl -L -A resistance-observatory-hackathon/0.1 -o <dir>/associations.csv \
  #        https://dataverse.harvard.edu/api/access/datafile/14061020
  python3 -I scripts/forecast/graph/vetted_membership.py csv <associations.csv> <checkedAt ISO> \
      data/forecast/raw/graph/sp_findings.json data/forecast/graph-vetted.json
  # fallback when the CSV is not available: the Alert tab pack's vetted_association_ids
  python3 -I scripts/forecast/graph/vetted_membership.py pack <k540e-graph.json> <checkedAt ISO> \
      data/forecast/raw/graph/sp_findings.json data/forecast/graph-vetted.json

A record is true if its system_id appears in the CSV's `system_id` column (the association id),
false if the complete file was scanned and it does not appear.
"""
import csv
import hashlib
import json
import os
import sys

csv.field_size_limit(sys.maxsize)
mode, src, checked_at, recon_path, out_path = sys.argv[1:6]
ids = sorted({r["system_id"] for r in json.load(open(recon_path, encoding="utf-8"))})
# optional 6th arg: the pack's k540e-graph.json, to also report (not pin) its 26 finding ids
extra = []
if len(sys.argv) > 6:
    pk = json.load(open(sys.argv[6], encoding="utf-8"))
    extra = [x["system_id"] for k in ("haplotype_findings", "stakes_sp") for x in pk[k]]

if mode == "csv":
    want = set(ids) | set(extra)
    found = set()
    rows = 0
    h = hashlib.sha256()

    class Hashing:
        def __init__(self, fh):
            self.fh = fh

        def __iter__(self):
            for line in self.fh:
                h.update(line)
                yield line.decode("utf-8", errors="replace")

    with open(src, "rb") as fh:
        rd = csv.reader(Hashing(fh))
        header = next(rd)
        col = header.index("system_id")
        for row in rd:
            rows += 1
            if len(row) > col and row[col] in want:
                found.add(row[col])
        for _ in fh:  # nothing left; keeps the hash complete if the reader stopped early
            pass
    out = {
        "source": "System Public Graph v2.1 vetted bulk snapshot, Harvard Dataverse doi:10.7910/DVN/7V6JDO",
        "file": os.path.basename(src) if os.path.basename(src) != "associations.csv" else "system-public-graph-v1-associations.csv",
        "checksum": "sha256:" + h.hexdigest(),
        "method": f"Complete file scanned ({rows} data rows); id column `{header[col]}`. true = the record's system_id appears in that column; false = it does not.",
        "checkedAt": checked_at,
        "ids": {i: (i in found) for i in ids},
    }
elif mode == "pack":
    g = json.load(open(src, encoding="utf-8"))
    vet = set(g["vetted_association_ids"])
    out = {
        "source": "FALLBACK: vetted_association_ids in the Alert tab data pack (k540e-data-pack/k540e-graph.json, commit a1cc503), not the Dataverse file itself",
        "file": "k540e-data-pack/k540e-graph.json",
        "checksum": None,
        "method": f"Membership in the pack's list of {len(vet)} ids.",
        "checkedAt": checked_at,
        "ids": {i: (i in vet) for i in ids},
    }
else:
    sys.exit("mode must be csv | pack")

with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
if mode == "csv" and extra:
    print("pack ids in CSV:", {i: (i in found) for i in extra})
print(out["source"], "|", out["checksum"], "|", out["method"], "| true", sum(out["ids"].values()), "of", len(ids))
