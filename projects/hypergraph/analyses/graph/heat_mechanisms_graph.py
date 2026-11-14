"""Shared neighbours of temperature-side and violence-side concepts in the System Public Graph.

Step 1 of the heat-mechanisms experiment. Pools the neighbours of each side with
tools/graph_paths and writes the shared neighbours, with the concepts each was reached
through, to data/derived/graph/heat_mechanisms/shared_neighbours.json.
Re-runs from the sysgraph cache.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import graph_paths as gp  # noqa: E402

OUT = ROOT / "data" / "derived" / "graph" / "heat_mechanisms"

# Concept ids were chosen by reading the search results for each term in the task
# (search matches whole words; "heat" returns heat-shock proteins, "hot weather",
# "ambient temperature" and "summer" return nothing).
TEMP = {"temperature": "4FaXcuNJRt", "air temperature": "mUxSLRMwIy", "heat wave": "k9BAffdSqv",
        "extreme heat": "wpUeTjUbAc", "hot": "dINFs04idR", "weather": "mPpkf6sGMO", "season": "RAmMULqqF1"}
VIOL = {"violence": "2qLKgaxkm_", "gun violence": "X7hfhwez9f", "homicide": "YZku29igbl", "assault": "1pnN2AtyJB",
        "firearm": "14UOQBVakG", "crime": "V7ImOTxbql", "violent crime": "Sb3zGs-d5I", "aggression": "y83mBL5cYb",
        "aggressive behavior": "RdEfyciCY-", "anger": "B2ZmiLUPao", "irritability": "eGsmX1QS3n",
        "hostility": "ioB3UJ8IJL", "shooting": "5-tHcH0EjT", "domestic violence": "bYLGUlP0n-",
        "intimate partner violence": "QmevDxhzPZ", "injury": "rULjCt1BqH"}


def pool(side):
    pooled, sizes = {}, {}
    for lab, cid in side.items():
        nb = gp.neighbours(cid)
        sizes[lab] = {"neighbours": len(nb), "findings": sum(d["n_findings"] for d in nb.values())}
        for oid, d in nb.items():
            p = pooled.setdefault(oid, {"label": d["label"], "n_findings": 0, "n_studies": 0, "via": {}})
            p["n_findings"] += d["n_findings"]
            p["n_studies"] += d["n_studies"]
            p["via"][lab] = {"n_findings": d["n_findings"], "relationship_ids": d["relationship_ids"]}
    return pooled, sizes


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pt, st = pool(TEMP)
    pv, sv = pool(VIOL)
    tid, vid = set(TEMP.values()), set(VIOL.values())
    direct = [{"temp": t, "viol": pt[v]["label"], **pt[v]["via"][t]} for v in vid if v in pt for t in pt[v]["via"]]
    shared = []
    for oid in set(pt) & set(pv):
        if oid in tid or oid in vid:
            continue
        a, b = pt[oid], pv[oid]
        # the same link without "season" on one side and without "injury" on the other
        a_ns = sum(v["n_findings"] for k, v in a["via"].items() if k != "season")
        b_ni = sum(v["n_findings"] for k, v in b["via"].items() if k != "injury")
        shared.append({"system_id": oid, "label": a["label"], "temp_findings": a["n_findings"],
                       "viol_findings": b["n_findings"], "temp_findings_excl_season": a_ns,
                       "viol_findings_excl_injury": b_ni, "temp_via": a["via"], "viol_via": b["via"]})
    shared.sort(key=lambda s: (-min(s["temp_findings_excl_season"], s["viol_findings_excl_injury"]),
                               -min(s["temp_findings"], s["viol_findings"])))
    res = {"temp_concepts": TEMP, "viol_concepts": VIOL, "temp_sizes": st, "viol_sizes": sv,
           "direct": direct, "n_shared": len(shared), "shared": shared}
    (OUT / "shared_neighbours.json").write_text(json.dumps(res, indent=1))
    print("temp sizes", st)
    print("viol sizes", sv)
    print("direct", [(d["temp"], d["viol"], d["n_findings"]) for d in direct])
    print("shared", len(shared))
    for s in shared[:120]:
        print(f"{s['temp_findings_excl_season']:4d}/{s['temp_findings']:4d}  {s['viol_findings_excl_injury']:4d}/{s['viol_findings']:4d}  {s['label']}")


if __name__ == "__main__":
    main()
