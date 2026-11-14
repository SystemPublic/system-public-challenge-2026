#!/usr/bin/env python
"""Concept-level checks for the re-timed week (docs/graph_experiments.md).

1. Neighbours of the seven concepts that exist for the exposures (walking, sedentary lifestyle,
   loneliness, social isolation, sleep, public transport, physical activity), capped at 1,500
   relationships each, and the concepts shared between pairs of them (candidate mediators).
2. Gap checks for four consequences the graph was expected to lack: taxi demand, restaurant
   trade, burglary, crowd safety. Each is searched as a concept and as a variable name; a
   variable counts only if its name matches the pattern given here.

Writes data/derived/graph/retimed_week/concept_neighbours.json and gap_checks.json.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import requests  # noqa: E402

from concord import sysgraph as g  # noqa: E402
import graph_paths as gp  # noqa: E402

OUT = ROOT / "data" / "derived" / "graph" / "retimed_week"
N = [0]
_o = requests.get


def _c(*a, **k):
    N[0] += 1
    return _o(*a, **k)


requests.get = _c

CONCEPTS = ["walking", "sedentary lifestyle", "loneliness", "social isolation", "sleep", "public transport",
            "physical activity"]
PAIRS = [("public transport", "physical activity"), ("public transport", "sleep"), ("walking", "sleep"),
         ("sedentary lifestyle", "sleep"), ("loneliness", "sleep"), ("social isolation", "physical activity"),
         ("public transport", "loneliness"), ("walking", "loneliness")]
GAPS = {
    "taxi demand": (["taxi", "ride-hailing", "ridesharing"], r"taxi|ride-?hail|ride-?shar|uber"),
    "restaurant trade": (["restaurant", "retail"], r"restaurant|retail (sales|trade)|foot traffic|footfall"),
    "burglary": (["burglary", "theft"], r"burglar|break-in"),
    "crowd safety": (["crowding", "crowd", "guardianship", "ridership"],
                     r"crowd|guardian(ship)|ridership|passenger (volume|density)|pedestrian (volume|density|count)"),
}
WORK = r"commut|telework|telecommut|remote(ly)? work|work(ing)? (from|at) home|office|weekday|day of (the )?week|workday|employ"


def main():
    res = {"concepts": {}, "pairs": []}
    nb = {}
    for term in CONCEPTS:
        cs = gp.resolve(term, expand=False)
        exact = [c for c in cs if c["label"].lower() == term]
        if not exact:
            res["concepts"][term] = {"exists": False, "search_returned": [c["label"] for c in cs]}
            continue
        c = exact[0]
        n = gp.neighbours(c["system_id"], max_items=1500)
        nb[term] = n
        top = sorted(n.items(), key=lambda kv: -kv[1]["n_findings"])[:40]
        res["concepts"][term] = {"exists": True, "system_id": c["system_id"], "neighbours": len(n),
                                 "findings": sum(d["n_findings"] for d in n.values()),
                                 "top": [{"system_id": k, "label": d["label"], "n_findings": d["n_findings"],
                                          "n_studies": d["n_studies"], "relationship_ids": d["relationship_ids"]}
                                         for k, d in top]}
    for a, b in PAIRS:
        if a not in nb or b not in nb:
            continue
        ida, idb = res["concepts"][a]["system_id"], res["concepts"][b]["system_id"]
        direct = nb[a].get(idb, {"n_findings": 0, "relationship_ids": []})
        shared = [{"label": nb[a][k]["label"], "with_a": nb[a][k]["n_findings"], "with_b": nb[b][k]["n_findings"]}
                  for k in set(nb[a]) & set(nb[b]) if k not in (ida, idb) and min(nb[a][k]["n_findings"], nb[b][k]["n_findings"]) >= 2]
        shared.sort(key=lambda s: -min(s["with_a"], s["with_b"]))
        res["pairs"].append({"a": a, "b": b, "direct_findings": direct["n_findings"],
                             "relationship_ids": direct["relationship_ids"], "n_shared": len(shared), "shared": shared[:25]})
    res["generated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    (OUT / "concept_neighbours.json").write_text(json.dumps(res, indent=1))

    gaps = {}
    for name, (terms, rx) in GAPS.items():
        cl, vs = [], {}
        for t in terms:
            cl += [c.get("wikidata_label") for c in g.concepts(t, limit=20)]
            for v in g.variables(t, limit=150):
                if re.search(rx, v["name"], re.I):
                    vs[v["system_id"]] = v["name"]
        work = {i: n for i, n in vs.items() if re.search(WORK, n, re.I)}
        # findings of up to 25 matching variables, to see whether any outcome or exposure concerns work travel
        linked = []
        for vid, vname in list(vs.items())[:25]:
            for a in g.variable_associations(vid, max_items=200):
                other = a["variable_2_name"] if a.get("variable_1_id") == vid else a["variable_1_name"]
                linked.append({"variable": vname, "other": other, "statistic": a.get("system_statistic_type"),
                               "value": a.get("statistic_value"), "pubmed_id": a.get("pubmed_id"),
                               "work_related": bool(re.search(WORK, (other or "") + " " + vname, re.I))})
        gaps[name] = {"search_terms": terms, "concepts_returned": sorted(set(filter(None, cl))),
                      "variables_matching": len(vs), "variable_names": list(vs.values())[:60],
                      "variables_naming_work_or_weekday": list(work.values()),
                      "findings_read": len(linked), "findings_work_related": [x for x in linked if x["work_related"]],
                      "sample_findings": linked[:30]}
    (OUT / "gap_checks.json").write_text(json.dumps(gaps, indent=1))
    log = OUT / "requests.json"
    hist = json.loads(log.read_text()) if log.exists() else []
    hist.append({"script": "analyses/graph/retimed_week_concepts.py", "run": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                 "uncached_requests": N[0]})
    log.write_text(json.dumps(hist, indent=1))
    print("uncached requests", N[0])


if __name__ == "__main__":
    main()
