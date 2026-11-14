"""Exploratory, not a registered test: job-level difference between the 25Q4 archive and the
portal copy (26Q2.1, cached new-building rows) for new-building jobs with PermitYear 2025
and with CompltYear 2025.

  python -I analyses/reproduction/dcp_2025_release_diff.py CSV_25Q4 PORTAL_CACHE_JSON OUT_JSON
"""
import csv
import json
import sys


def num(x):
    x = (x or "").strip()
    return float(x) if x else 0.0


def main(csv_path, cache_path, out_path):
    old = {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["Job_Type"] == "New Building":
                old[r["Job_Number"]] = {"py": r["PermitYear"].strip(), "cy": r["CompltYear"].strip(),
                                        "u": num(r["ClassAProp"]), "st": r["Job_Status"], "dp": r["DatePermit"][:10]}
    new = {}
    for r in json.load(open(cache_path))["rows"]:
        new[r["job_number"]] = {"py": r.get("permityear", ""), "cy": r.get("compltyear", ""),
                                "u": num(r.get("classaprop")), "st": r.get("job_status", ""),
                                "dp": (r.get("datepermit") or "")[:10]}
    out = {"new_building_jobs": {"25Q4": len(old), "26Q2.1": len(new)}}
    for key, label in (("py", "permits_2025"), ("cy", "completions_2025")):
        a = {j for j, v in old.items() if v[key] == "2025" and (key == "cy" or not v["st"].startswith("9"))}
        b = {j for j, v in new.items() if v[key] == "2025" and (key == "cy" or not v["st"].startswith("9"))}
        added, dropped, both = b - a, a - b, a & b
        add_absent = [j for j in added if j not in old]
        add_moved = [j for j in added if j in old]
        month = {}
        for j in added:
            m = new[j]["dp"][:7]
            month[m] = month.get(m, 0) + new[j]["u"]
        out[label] = {
            "units_25Q4": sum(old[j]["u"] for j in a), "units_26Q2.1": sum(new[j]["u"] for j in b),
            "jobs_25Q4": len(a), "jobs_26Q2.1": len(b),
            "added_jobs": len(added), "added_units": sum(new[j]["u"] for j in added),
            "added_absent_from_25Q4_jobs": len(add_absent), "added_absent_from_25Q4_units": sum(new[j]["u"] for j in add_absent),
            "added_present_in_25Q4_other_year_or_status_jobs": len(add_moved),
            "added_present_in_25Q4_other_year_or_status_units": sum(new[j]["u"] for j in add_moved),
            "dropped_jobs": len(dropped), "dropped_units": sum(old[j]["u"] for j in dropped),
            "dropped_still_in_26Q2.1_jobs": sum(1 for j in dropped if j in new),
            "common_jobs_units_changed": sum(1 for j in both if old[j]["u"] != new[j]["u"]),
            "common_jobs_net_unit_change": sum(new[j]["u"] - old[j]["u"] for j in both),
        }
        if key == "py":
            out[label]["added_units_by_permit_month"] = dict(sorted(month.items()))
    with open(out_path, "w") as g:
        json.dump(out, g, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
