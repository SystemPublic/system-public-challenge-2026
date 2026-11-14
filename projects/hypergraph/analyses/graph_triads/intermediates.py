"""Stage 3: neighbours of each candidate intermediate B (a neighbour of some exposure with >= MIN_S studies).

Demographic covariates and all-cause mortality are excluded before fetching (HAND_GENERIC).
A second, computed generic list (degree-based) is made in triads.py from what is fetched here.
"""
import json, hashlib, sys
from common import g, OUT, used
MIN_S = 5
CAP = 190
BUDGET = int(sys.argv[1]) if (__name__ == "__main__" and len(sys.argv) > 1) else 750
HAND_GENERIC = {"mortality rate", "age group", "gender", "sex", "body mass index", "ethnicity", "educational stage", "income", "socioeconomic status",
                "age", "survival rate", "survival skill", "marital status", "race", "education", "old age", "human aging", "COVID-19"}

def rels_any(cid):
    """Use the 100-row pages if another agent already cached them, else 1000-row pages."""
    q = "limit=100&offset=0"
    f = g.CACHE / (hashlib.sha256(f"/v1/concepts/{cid}/relationships?{q}".encode()).hexdigest()[:24] + ".json")
    lim = 100 if f.exists() else 1000
    return g.page_all(f"/v1/concepts/{cid}/relationships", limit=lim, max_items=40000)

def neigh(cid):
    out = {}
    for r in rels_any(cid):
        s, t = r.get("source_concept") or {}, r.get("target_concept") or {}
        o = t if s.get("system_id") == cid else s
        oid = o.get("system_id")
        if not oid or oid == cid:
            continue
        d = out.setdefault(oid, {"label": o.get("wikidata_label") or oid, "f": 0, "s": 0, "rids": []})
        d["f"] += int(r.get("num_findings") or 0); d["s"] += int(r.get("num_studies") or 0); d["rids"].append(r["relationship_id"])
    return out

if __name__ == "__main__":
    ex = json.loads((OUT / "exposure_neighbours.json").read_text())
    aid = {v["system_id"] for v in ex.values()}
    B = {}
    for lab, v in ex.items():
        for oid, d in v["neighbours"].items():
            if d["s"] >= MIN_S and d["label"] not in HAND_GENERIC and oid not in aid:
                b = B.setdefault(oid, {"label": d["label"], "max_s": 0, "n_exposures": 0})
                b["max_s"] = max(b["max_s"], d["s"]); b["n_exposures"] += 1
    order = sorted(B.items(), key=lambda kv: (-kv[1]["max_s"], -kv[1]["n_exposures"]))
    print(len(order), "candidate intermediates; fetching up to", CAP)
    f = OUT / "intermediate_neighbours.json"
    res = json.loads(f.read_text()) if f.exists() else {}
    for oid, b in order[:CAP]:
        if oid in res:
            continue
        if used() >= BUDGET:
            print("budget stop at", b["label"]); break
        n = neigh(oid)
        # keep only links with >= 3 studies to hold the file small; degree is kept in full
        res[oid] = {"label": b["label"], "max_s": b["max_s"], "n_exposures": b["n_exposures"], "degree": len(n),
                    "n_findings": sum(d["f"] for d in n.values()),
                    "neighbours": {k: d for k, d in n.items() if d["s"] >= 3}}
        print(f"{b['label'][:40]:40s} maxS={b['max_s']:3d} deg={len(n):5d} used={used()}")
        f.write_text(json.dumps(res))
    (OUT / "intermediate_candidates.json").write_text(json.dumps(dict(order), indent=0))
    print("fetched", len(res), "uncached so far", used())
