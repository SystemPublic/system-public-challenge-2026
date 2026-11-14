"""Find medication x heat findings in the System Public Graph.

Usage: python3 -I heat_meds.py <graph.db> <out_dir>
Writes heat_med_findings.csv and summary.json to out_dir.
"""
import collections
import csv
import json
import os
import re
import sqlite3
import sys

db = sqlite3.connect(sys.argv[1])
out = sys.argv[2]
os.makedirs(out, exist_ok=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heat_meds_lib import DRUGS, STORAGE, drug_classes, heat_tier  # noqa: E402


cols = (
    "system_id pubmed_id study_id statistic_type system_statistic_type statistic_value ci_level ci_lower ci_upper "
    "p_value p_value_equality variable_1_name variable_2_name variable_1_concept_id variable_2_concept_id"
).split()
cur = db.execute(f"SELECT {','.join(cols)} FROM associations")

tot = 0
heat_any = collections.Counter()  # tier -> findings
drug_any = collections.Counter()  # class -> findings anywhere in graph
drug_any_studies = collections.defaultdict(set)
heat_studies = collections.defaultdict(set)
rows = []
storage_rows = []
for r in cur:
    tot += 1
    d = dict(zip(cols, r))
    n1, n2 = d["variable_1_name"] or "", d["variable_2_name"] or ""
    t1, t2 = heat_tier(n1), heat_tier(n2)
    c1, c2 = drug_classes(n1), drug_classes(n2)
    tiers = {t for t in (t1, t2) if t}
    best = "direct" if "direct" in tiers else ("proxy" if "proxy" in tiers else None)
    if best:
        heat_any[best] += 1
        heat_studies[best].add(d["study_id"])
    for c in set(c1 + c2):
        drug_any[c] += 1
        drug_any_studies[c].add(d["study_id"])
    if best and (c1 or c2):
        # cross = heat on one side and drug on the other; same = both in a single variable name
        cross = bool((t1 and c2) or (t2 and c1))
        d["heat_tier"] = best
        d["drug_classes"] = "; ".join(sorted(set(c1 + c2)))
        d["pattern"] = "cross" if cross else "same-variable"
        rows.append(d)
    if (c1 or c2) and (STORAGE.search(n1) or STORAGE.search(n2)):
        d2 = dict(d)
        d2["drug_classes"] = "; ".join(sorted(set(c1 + c2)))
        storage_rows.append(d2)

# attach study metadata
sids = {d["study_id"] for d in rows} | {d["study_id"] for d in storage_rows}
meta = {}
for chunk in [list(sids)[i : i + 500] for i in range(0, len(sids), 500)]:
    q = f"SELECT study_id, doi, population_string, study_type FROM studies WHERE study_id IN ({','.join('?' * len(chunk))})"
    for sid, doi, pop, st in db.execute(q, chunk):
        meta[sid] = (doi, pop, st)
for d in rows + storage_rows:
    d["doi"], d["population"], d["study_type"] = meta.get(d["study_id"], (None, None, None))

fields = ["heat_tier", "pattern", "drug_classes"] + cols + ["doi", "population", "study_type"]
with open(os.path.join(out, "heat_med_findings.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
with open(os.path.join(out, "storage_findings.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["drug_classes"] + cols + ["doi", "population", "study_type"], extrasaction="ignore")
    w.writeheader()
    w.writerows(storage_rows)

by_class = {}
for k in DRUGS:
    sel = [d for d in rows if k in d["drug_classes"].split("; ")]
    by_class[k] = {
        "graph_findings": drug_any[k],
        "graph_studies": len(drug_any_studies[k]),
        "direct_findings": sum(d["heat_tier"] == "direct" for d in sel),
        "direct_studies": len({d["study_id"] for d in sel if d["heat_tier"] == "direct"}),
        "proxy_findings": sum(d["heat_tier"] == "proxy" for d in sel),
        "proxy_studies": len({d["study_id"] for d in sel if d["heat_tier"] == "proxy"}),
    }
summary = {
    "total_associations": tot,
    "heat_findings": dict(heat_any),
    "heat_studies": {k: len(v) for k, v in heat_studies.items()},
    "heat_x_med_findings": len(rows),
    "heat_x_med_studies": len({d["study_id"] for d in rows}),
    "storage_findings": len(storage_rows),
    "by_class": by_class,
}
with open(os.path.join(out, "summary.json"), "w") as f:
    json.dump(summary, f, indent=1)
print(json.dumps(summary, indent=1))
