#!/usr/bin/env python
"""For each target pair and each candidate shared concept, fetch the findings on both
links (exposure side and outcome side) with variable names, statistic and PubMed id.
Writes data/derived/graph/confounders/links_<pair>.json. Cached API calls only repeat free.
Run: ~/.venvs/nyc-concordance/bin/python analyses/graph_confounders/links.py [pair]"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(Path(__file__).parent))
import graph_paths as gp  # noqa: E402
from concord import sysgraph as g  # noqa: E402
from graph_evidence import normalise  # noqa: E402
from shared import TARGET  # noqa: E402

OUT = ROOT / "data/derived/graph/confounders"
PER_REL = 100   # findings read per relationship (one request)
# number of top-ranked shared concepts read, plus named extras lower in the list
TOPN = {"green__temperature": 22, "temperature__heat-illness": 24, "green__heat-illness": 12,
        "active-travel__obesity": 24, "housing-vacancy__gun-violence": 24}
EXTRA = {
    "active-travel__obesity": ["park", "built environment", "crime", "urban area", "socioeconomic status", "diet",
                               "population density", "smoking", "neighborhood characteristics", "energy intake",
                               "income", "employment", "poverty", "household income", "motor car", "rural area"],
    "housing-vacancy__gun-violence": ["recreational drug use", "homeless person", "rural area", "educational stage",
                                      "urban area", "social vulnerability", "employment", "marital status",
                                      "exposure to violence", "lead poisoning", "poverty", "population density",
                                      "unemployment", "socioeconomic status", "household income", "insurance",
                                      "home environment", "family characteristics"],
    "green__temperature": [], "temperature__heat-illness": ["home environment", "humidity", "air conditioning", "socioeconomic status", "poverty", "income"],
    "green__heat-illness": [],
}


def rows_for(pool, xid, max_per_side=300):
    out = []
    for cid in pool:
        nb = gp.neighbours(cid)
        if xid not in nb:
            continue
        for rid in nb[xid]["relationship_ids"]:
            if len(out) >= max_per_side:
                break
            for a in g.relationship_associations(rid, max_items=PER_REL):
                n = normalise(a)
                out.append({"relationship_id": rid, "association_id": a.get("system_id"),
                            "v1": a.get("variable_1_name"), "v2": a.get("variable_2_name"),
                            "stat": a.get("system_statistic_type"), "value": a.get("statistic_value"),
                            "lo": a.get("ci_lower"), "hi": a.get("ci_upper"), "p": a.get("p_value"),
                            "direction": n["direction"], "significant": n["significant"], "flags": n["flags"],
                            "pubmed_id": a.get("pubmed_id"), "study_id": a.get("study_id")})
    return out


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for name, (A, B) in TARGET.items():
        if only and name != only:
            continue
        sh = json.loads((OUT / f"shared_{name}.json").read_text())["shared"]
        want = [s for s in sh[:TOPN[name]]] + [s for s in sh[TOPN[name]:] if s["label"] in EXTRA[name]]
        res = {}
        for s in want:
            res[s["label"]] = {"system_id": s["system_id"], "findings_with_a": s["findings_with_a"],
                               "findings_with_b": s["findings_with_b"], "rank": sh.index(s) + 1,
                               "a_side": rows_for(A, s["system_id"]), "b_side": rows_for(B, s["system_id"])}
        (OUT / f"links_{name}.json").write_text(json.dumps(res, indent=1))
        print(name, len(res), "concepts", sum(len(v["a_side"]) + len(v["b_side"]) for v in res.values()), "findings read")


if __name__ == "__main__":
    main()
