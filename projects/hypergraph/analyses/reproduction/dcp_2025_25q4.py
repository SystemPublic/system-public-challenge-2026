"""repro-dcp-2025-completions, registered follow-up: the registered readings computed on
DCP's archived 25Q4 release of the Housing Database (the release the snapshot used).

The archive is untrusted data kept outside the repo. Run with an isolated interpreter and
pass the paths as arguments:

  python -I analyses/reproduction/dcp_2025_25q4.py CSV OUT_JSON

Only the standard library is used. The readings are those of the registration:
R1 = sum of ClassAProp, Job_Type 'New Building', CompltYear 2025; R2 the same with Units_CO;
R3 = R1 restricted to Job_Status '5. Completed Construction'; P1 = sum of ClassAProp,
'New Building', PermitYear 2025, excluding Job_Status '9. Withdrawn'; P2 = P1 with withdrawn.
"""
import csv
import json
import sys
from collections import Counter, defaultdict


def num(x):
    x = (x or "").strip()
    return float(x) if x else 0.0


def main(csv_path, out_path):
    R = Counter()
    boro = defaultdict(float)
    by_status = defaultdict(float)
    permits_by_status = defaultdict(float)
    by_year = defaultdict(float)
    versions = Counter()
    jobnos = Counter()
    n_rows = n_missing = 0
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            n_rows += 1
            versions[r["Version"]] += 1
            if r["Job_Type"] != "New Building":
                continue
            cy, py, st = r["CompltYear"].strip(), r["PermitYear"].strip(), r["Job_Status"]
            if cy:
                by_year[cy] += num(r["ClassAProp"])
            if cy == "2025":
                jobnos[r["Job_Number"]] += 1
                if not r["ClassAProp"].strip():
                    n_missing += 1
                R["jobs"] += 1
                R["R1"] += num(r["ClassAProp"])
                R["R2"] += num(r["Units_CO"])
                if st.startswith("5"):
                    R["R3"] += num(r["ClassAProp"])
                boro[r["Boro"]] += num(r["ClassAProp"])
                by_status[st] += num(r["ClassAProp"])
            if py == "2025":
                permits_by_status[st] += num(r["ClassAProp"])
    P2 = sum(permits_by_status.values())
    P1 = sum(v for k, v in permits_by_status.items() if not k.startswith("9"))
    out = {
        "release": dict(versions), "rows": n_rows,
        "readings": {k: R[k] for k in ("R1", "R2", "R3", "jobs")},
        "duplicate_job_numbers_2025": sum(1 for v in jobnos.values() if v > 1),
        "missing_classaprop_2025": n_missing,
        "boro_R1": dict(sorted(boro.items())),
        "completions_2025_by_status": dict(by_status),
        "permits_2025_by_status": dict(permits_by_status), "P1": P1, "P2": P2,
        "R1_by_year": {k: by_year[k] for k in sorted(by_year) if k >= "2015"},
    }
    with open(out_path, "w") as g:
        json.dump(out, g, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
