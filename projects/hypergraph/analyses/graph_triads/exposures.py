"""Stage 2: the exposure concepts (chosen by label from term_search.json) and their neighbours."""
import json
from common import g, OUT, used, rels
LABELS = ["noise pollution", "traffic noise", "noise", "traffic", "traffic-related pollution", "air pollution", "indoor air pollution",
          "nitrogen dioxide", "particulates", "ozone", "air temperature", "surface temperature", "urban heat island", "heat wave", "hot",
          "green space", "park", "tree", "urban area", "urbanization", "population density", "household crowding", "overcrowding",
          "housing", "housing quality", "housing instability", "public housing", "homeless person", "public transport", "walking",
          "shift work", "light pollution", "artificial light", "flood", "flooding", "rodent control", "pest control", "cockroach",
          "fast food", "food desert", "food insecurity", "poverty", "poverty area", "unemployment", "unemployed", "neighborhood",
          "neighborhood characteristics", "built environment", "crime", "violent crime", "traffic collision"]
EXTRA_SEARCH = {"heat wave": "wave", "public transport": "public", "hot": "hot"}

def find():
    ts = json.loads((OUT / "term_search.json").read_text())
    by = {}
    for rows in ts.values():
        for r in rows:
            by.setdefault(r["label"], r["system_id"])
    for lab, term in EXTRA_SEARCH.items():
        for r in g.concepts(term, limit=50):
            by.setdefault(r.get("wikidata_label"), r["system_id"])
    return {lab: by.get(lab) for lab in LABELS}

def neigh(cid):
    out = {}
    for r in rels(cid):
        s, t = r.get("source_concept") or {}, r.get("target_concept") or {}
        o = t if s.get("system_id") == cid else s
        oid = o.get("system_id")
        if not oid or oid == cid:
            continue
        d = out.setdefault(oid, {"label": o.get("wikidata_label") or oid, "f": 0, "s": 0, "rids": []})
        d["f"] += int(r.get("num_findings") or 0); d["s"] += int(r.get("num_studies") or 0); d["rids"].append(r["relationship_id"])
    return out

if __name__ == "__main__":
    ids = find()
    res = {}
    for lab, cid in ids.items():
        if not cid:
            print("NO CONCEPT", lab); continue
        n = neigh(cid)
        res[lab] = {"system_id": cid, "n_neighbours": len(n), "n_findings": sum(d["f"] for d in n.values()), "neighbours": n}
        top = sorted(n.values(), key=lambda d: -d["s"])[:6]
        print(f"{lab:28s} {cid} nb={len(n):5d} f={res[lab]['n_findings']:6d} | " + "; ".join(f"{d['label']}({d['s']})" for d in top))
    (OUT / "exposure_neighbours.json").write_text(json.dumps(res))
    print("uncached so far", used())
