#!/usr/bin/env python
"""Stage 1 of the coverage experiment: query the System Public Graph for every end of every registered claim.

Writes data/derived/graph/coverage/ends.json (per end) and pairs.json (per claim).
Does not query any city data. Run from the repo root:
  ~/.venvs/nyc-concordance/bin/python analyses/graph_coverage/collect.py
All responses are cached by concord/sysgraph.py, so a re-run costs no requests.
"""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(Path(__file__).parent)]
from concord import sysgraph as g
from graph_paths import neighbours
from graph_evidence import evidence
from termmap import ENDS, CLAIMS

OUT = ROOT / "data" / "derived" / "graph" / "coverage"
OUT.mkdir(parents=True, exist_ok=True)
NB_CAP = 3000
VAR_LIMIT, VAR_SAMPLE = 100, 10


def label(cid):
    return (g.concept(cid) or {}).get("wikidata_label") or cid


def end_info(name, e):
    info = {"label": name, "concept_ids": e["concepts"], "concept_labels": [label(c) for c in e["concepts"]],
            "searches": {}, "variable_queries": {}}
    for s in e["searches"]:
        rows = g.concepts(s, limit=12)
        info["searches"][s] = [r.get("wikidata_label") for r in rows]
    if not e["concepts"]:
        for q in e["vq"]:
            vs = g.variables(q, limit=VAR_LIMIT)
            sample = vs[:VAR_SAMPLE]
            n_assoc, vars_out = 0, []
            for v in sample:
                aa = g.variable_associations(v["system_id"], max_items=300)
                n_assoc += len(aa)
                own = None
                for a in aa:
                    side = "1" if a.get("variable_1_id") == v["system_id"] else "2"
                    own = a.get(f"variable_{side}_concept_id")
                    break
                vars_out.append({"id": v["system_id"], "name": v["name"], "n_associations": len(aa),
                                 "own_concept_id": own, "own_concept": label(own) if own else None})
            info["variable_queries"][q] = {"n_variables": len(vs), "capped": len(vs) >= VAR_LIMIT,
                                           "sampled": len(sample), "associations_in_sample": n_assoc, "variables": vars_out}
    return info


def main():
    ends = {}
    nb_cache = {}
    t0 = time.time()
    for name, e in ENDS.items():
        ends[name] = end_info(name, e)
        print("end", name, round(time.time() - t0), flush=True)
    (OUT / "ends.json").write_text(json.dumps(ends, indent=1))

    def nb(cid):
        if cid not in nb_cache:
            d = neighbours(cid, max_items=NB_CAP)
            nb_cache[cid] = d
        return nb_cache[cid]

    pairs_out = {}
    pair_cache = {}
    for cid, (c, f, causal) in CLAIMS.items():
        A, B = ENDS[c]["concepts"], ENDS[f]["concepts"]
        rec = {"cause": c, "effect": f, "causal": causal, "pairs": [], "direct_findings": None, "direct_studies": None,
               "shared_neighbours": None, "shared_top": [], "signs": None}
        if A and B:
            direct_f = direct_s = 0
            tot = {"+": 0, "-": 0, "none": 0, "sig+": 0, "sig-": 0}
            for a in A:
                for b in B:
                    if a == b:
                        continue
                    key = (a, b)
                    if key not in pair_cache:
                        rels = g.relationships_between(a, b)
                        nf = sum(int(r.get("num_findings") or 0) for r in rels)
                        ns = sum(int(r.get("num_studies") or 0) for r in rels)
                        sg = None
                        if nf:
                            ev = evidence(a, b, api_only=True)
                            s = ev["summary"]["csv"]
                            sg = {k: s[k] for k in tot}
                            sg["n"] = s["n"]
                            sg["studies"] = s["studies"]
                        pair_cache[key] = {"relationship_ids": [r["relationship_id"] for r in rels], "n_findings": nf, "n_studies": ns, "signs": sg}
                    p = pair_cache[key]
                    rec["pairs"].append({"a": a, "b": b, "a_label": label(a), "b_label": label(b), **p})
                    direct_f += p["n_findings"]
                    direct_s += p["n_studies"]
                    if p["signs"]:
                        for k in tot:
                            tot[k] += p["signs"][k]
            rec["direct_findings"], rec["direct_studies"] = direct_f, direct_s
            rec["signs"] = tot if direct_f else None
            # shared neighbours, pooled over each end's concepts
            pa, pb = {}, {}
            for pool, ids in ((pa, A), (pb, B)):
                for x in ids:
                    for oid, d in nb(x).items():
                        q = pool.setdefault(oid, {"label": d["label"], "n": 0})
                        q["n"] += d["n_findings"]
            skip = set(A) | set(B)
            sh = [{"id": o, "label": pa[o]["label"], "with_cause": pa[o]["n"], "with_effect": pb[o]["n"]}
                  for o in set(pa) & set(pb) if o not in skip and min(pa[o]["n"], pb[o]["n"]) >= 2]
            sh.sort(key=lambda x: -min(x["with_cause"], x["with_effect"]))
            rec["shared_neighbours"] = len(sh)
            rec["shared_top"] = sh[:8]
            rec["neighbours_cause"], rec["neighbours_effect"] = len(pa), len(pb)
            rec["truncated"] = any(len(g.concept_relationships(x, max_items=NB_CAP)) >= NB_CAP for x in A + B)
        pairs_out[cid] = rec
        print("claim", cid, rec["direct_findings"], rec["shared_neighbours"], round(time.time() - t0), flush=True)
        (OUT / "pairs.json").write_text(json.dumps(pairs_out, indent=1))


if __name__ == "__main__":
    main()
