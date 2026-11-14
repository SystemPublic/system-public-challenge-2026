"""Inventory the concepts involved in drug -> X <- heat traversal.

For every finding, the drug side and heat side are detected by variable NAME
(rules in heat_meds_lib.py); the other side is taken at CONCEPT level.

Usage: python3 -I bridges.py <graph.db> <reference_dir>
Writes to reference_dir:
  drug_concepts.csv    which concepts drug-class variables are grounded to
  heat_concepts.csv    which concepts heat-exposure variables are grounded to
  bridge_concepts.csv  concepts linked to BOTH a drug class and heat exposure
"""
import collections
import csv
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heat_meds_lib import DRUG_RE, drug_classes, heat_tier  # noqa: E402

db = sqlite3.connect(sys.argv[1])
out = sys.argv[2]
os.makedirs(out, exist_ok=True)

concepts = {r[0]: (r[1], r[2]) for r in db.execute("SELECT system_id, wikidata_id, wikidata_label FROM concepts")}
cur = db.execute(
    "SELECT study_id, variable_1_name, variable_2_name, variable_1_concept_id, variable_2_concept_id FROM associations"
)

drug_self = collections.defaultdict(collections.Counter)  # class -> concept -> findings
heat_self = collections.Counter()  # concept -> findings (direct tier)
heat_self_st = collections.defaultdict(set)
proxy_self = collections.Counter()
drug_to = collections.defaultdict(lambda: collections.defaultdict(set))  # class -> other concept -> studies
heat_to = collections.defaultdict(set)  # other concept -> studies
heat_side_concepts = set()
drug_side_concepts = set()

for sid, n1, n2, c1, c2 in cur:
    n1, n2 = n1 or "", n2 or ""
    t = (heat_tier(n1), heat_tier(n2))
    d = (drug_classes(n1), drug_classes(n2))
    c = (c1, c2)
    for i in (0, 1):
        j = 1 - i
        for k in d[i]:
            drug_self[k][c[i]] += 1
            if not d[j]:  # other side is not itself a drug variable
                drug_to[k][c[j]].add(sid)
        if d[i]:
            drug_side_concepts.add(c[i])
        if t[i] == "direct":
            heat_self[c[i]] += 1
            heat_self_st[c[i]].add(sid)
            heat_side_concepts.add(c[i])
            if t[j] != "direct":
                heat_to[c[j]].add(sid)
        elif t[i] == "proxy":
            proxy_self[c[i]] += 1


def lab(cid):
    return concepts.get(cid, ("", ""))


with open(os.path.join(out, "drug_concepts.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["drug_class", "concept_id", "wikidata_id", "wikidata_label", "n_findings"])
    for k in DRUG_RE:
        for cid, n in drug_self[k].most_common():
            if n >= 3:
                w.writerow([k, cid, *lab(cid), n])

with open(os.path.join(out, "heat_concepts.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["tier", "concept_id", "wikidata_id", "wikidata_label", "n_findings", "n_studies"])
    for cid, n in heat_self.most_common():
        if n >= 2:
            w.writerow(["direct", cid, *lab(cid), n, len(heat_self_st[cid])])
    for cid, n in proxy_self.most_common():
        if n >= 5:
            w.writerow(["proxy", cid, *lab(cid), n, ""])

rows = []
for k in DRUG_RE:
    for cid, st in drug_to[k].items():
        h = len(heat_to.get(cid, ()))
        if h >= 2 and len(st) >= 2 and cid not in heat_side_concepts:
            rows.append([k, cid, *lab(cid), len(st), h, min(len(st), h)])
rows.sort(key=lambda r: (r[0], -r[6], -r[4]))
with open(os.path.join(out, "bridge_concepts.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["drug_class", "concept_id", "wikidata_id", "wikidata_label", "drug_studies", "heat_studies", "weaker_arm"])
    w.writerows(rows)

# console summary: bridge concepts ranked by how many of the focus classes reach them
focus = ["Diuretics", "Beta blockers", "ACE inhibitors / ARBs", "Anticholinergics", "Antipsychotics",
         "Antidepressants", "Lithium", "Insulin (as therapy)", "SGLT2 inhibitors"]
agg = collections.defaultdict(dict)
for r in rows:
    if r[0] in focus:
        agg[(r[3], r[5])][r[0]] = r[4]
print("bridge rows:", len(rows), "| distinct bridge concepts (focus classes):", len(agg))
for (label, h), m in sorted(agg.items(), key=lambda x: (-len(x[1]), -x[0][1]))[:70]:
    print(f"{label[:38]:38} heat={h:<4} classes={len(m)}  " + ", ".join(f"{k.split()[0]}:{v}" for k, v in m.items()))
print("\nheat-side concepts (top):")
for cid, n in heat_self.most_common(25):
    print("  ", lab(cid)[1], n, len(heat_self_st[cid]))
print("\ndrug-side top concepts per focus class:")
for k in focus:
    print("  ", k, "->", "; ".join(f"{lab(cid)[1]} ({n})" for cid, n in drug_self[k].most_common(6)))
