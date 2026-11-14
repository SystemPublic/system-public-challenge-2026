"""Second pass: what heat links to, what drugs link to, and where they meet.

Usage: python3 -I pathways.py <graph.db> <out_dir>
Writes pathways.json to out_dir.
"""
import collections
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heat_meds_lib import DRUG_RE, drug_classes, heat_tier  # noqa: E402

db = sqlite3.connect(sys.argv[1])
out = sys.argv[2]
I = re.IGNORECASE

MECH = collections.OrderedDict(
    [
        ("Low sodium (hyponatremia)", re.compile(r"hyponatr|serum sodium|plasma sodium", I)),
        ("Dehydration / volume loss", re.compile(r"dehydrat|hypovol|volume depletion|hypohydrat", I)),
        ("Acute kidney injury", re.compile(r"acute kidney injury|\baki\b|acute renal (failure|injury)", I)),
        ("Low blood pressure / fainting", re.compile(r"hypotension|syncope|orthostatic", I)),
        ("Falls", re.compile(r"\bfalls?\b|\bfalling\b", I)),
        ("Low blood sugar", re.compile(r"hypoglyc", I)),
        ("Potassium / electrolytes", re.compile(r"hyperkal|hypokal|electrolyte", I)),
        ("Sweating / body temperature", re.compile(r"\bsweat|hyperhidrosis|anhidrosis|thermoregul|(core|body|rectal|skin)[\s-]?temperature", I)),
    ]
)

concept_label = dict(db.execute("SELECT system_id, wikidata_label FROM concepts"))
cur = db.execute(
    "SELECT study_id, system_statistic_type, ci_lower, p_value, variable_1_name, variable_2_name, "
    "variable_1_concept_id, variable_2_concept_id FROM associations"
)

drug_mech = collections.defaultdict(set)  # (class, mech) -> studies
drug_mech_f = collections.Counter()
heat_mech = collections.defaultdict(set)  # mech -> studies
heat_mech_f = collections.Counter()
heat_other = collections.defaultdict(set)  # concept label -> studies (other side of direct heat)
heat_other_f = collections.Counter()
heat_stat = collections.Counter()
heat_ci = collections.Counter()
all_ci = collections.Counter()
heat_study_ids = set()

for sid, stat, ci, p, n1, n2, c1, c2 in cur:
    n1, n2 = n1 or "", n2 or ""
    all_ci["ci" if ci is not None else "no_ci"] += 1
    all_ci["p" if p is not None else "no_p"] += 1
    t1, t2 = heat_tier(n1), heat_tier(n2)
    d1, d2 = drug_classes(n1), drug_classes(n2)
    m1 = [k for k, rx in MECH.items() if rx.search(n1)]
    m2 = [k for k, rx in MECH.items() if rx.search(n2)]
    for d, m in ((d1, m2), (d2, m1)):
        for dc in d:
            for mk in m:
                drug_mech[(dc, mk)].add(sid)
                drug_mech_f[(dc, mk)] += 1
    for t, m, oc in ((t1, m2, c2), (t2, m1, c1)):
        if t == "direct":
            for mk in m:
                heat_mech[mk].add(sid)
                heat_mech_f[mk] += 1
            lab = concept_label.get(oc)
            if lab:
                heat_other[lab].add(sid)
                heat_other_f[lab] += 1
    if "direct" in (t1, t2):
        heat_stat[stat] += 1
        heat_ci["ci" if ci is not None else "no_ci"] += 1
        heat_ci["p" if p is not None else "no_p"] += 1
        heat_study_ids.add(sid)

# study type for heat studies
st = collections.Counter()
ids = list(heat_study_ids)
for i in range(0, len(ids), 500):
    ch = ids[i : i + 500]
    for (t,) in db.execute(f"SELECT study_type FROM studies WHERE study_id IN ({','.join('?' * len(ch))})", ch):
        st[t or "not labelled"] += 1

res = {
    "mechanisms": list(MECH),
    "classes": [k for k in DRUG_RE],
    "drug_mech_studies": {f"{a}|{b}": len(v) for (a, b), v in drug_mech.items()},
    "drug_mech_findings": {f"{a}|{b}": v for (a, b), v in drug_mech_f.items()},
    "heat_mech_studies": {k: len(v) for k, v in heat_mech.items()},
    "heat_mech_findings": dict(heat_mech_f),
    "heat_top_linked": sorted(((k, len(v), heat_other_f[k]) for k, v in heat_other.items()), key=lambda x: -x[1])[:60],
    "heat_stat_types": dict(heat_stat),
    "heat_ci": dict(heat_ci),
    "all_ci": dict(all_ci),
    "heat_study_types": dict(st),
}
with open(os.path.join(out, "pathways.json"), "w") as f:
    json.dump(res, f, indent=1)
print(json.dumps(res, indent=1))
