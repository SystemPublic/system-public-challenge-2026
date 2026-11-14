"""Step 1 (graph side only): neighbours of every mapped concept, and which indicator pairs have findings."""
import csv
import itertools
import json

import common as C
from indicators import BY_KEY, INDICATORS, KEYS

g = C.g


def rels(cid):
    return g.page_all(f"/v1/concepts/{cid}/relationships", limit=1000, max_items=40000)


def main():
    C.OUT.mkdir(parents=True, exist_ok=True)
    with open(C.OUT / "indicator_concepts.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["indicator", "role", "label", "source", "polarity", "concept_id", "concept_label", "note"])
        for r in INDICATORS:
            src = ":".join(str(x) for x in r[3])
            for cid, lab in (r[5] or [("", "")]):
                w.writerow([r[0], r[1], r[2], src, r[4], cid, lab, r[6]])
    c2k = {}
    for k in KEYS:
        for cid, _ in BY_KEY[k]["concepts"]:
            assert cid not in c2k, cid
            c2k[cid] = k
    pair = {}
    nrel = {}
    for cid in c2k:
        rs = rels(cid)
        nrel[cid] = len(rs)
        for r in rs:
            s, t = (r.get("source_concept") or {}).get("system_id"), (r.get("target_concept") or {}).get("system_id")
            if s in c2k and t in c2k and c2k[s] != c2k[t]:
                a, b = sorted([c2k[s], c2k[t]])
                d = pair.setdefault((a, b), {})
                d[r["relationship_id"]] = {"num_findings": r.get("num_findings"), "num_studies": r.get("num_studies"),
                                           "source": r["source_concept"].get("wikidata_label"), "target": r["target_concept"].get("wikidata_label")}
    out = []
    for a, b in itertools.combinations(KEYS, 2):
        a, b = sorted([a, b])
        rs = pair.get((a, b), {})
        out.append({"a": a, "b": b, "relationships": rs, "n_findings": sum(x["num_findings"] or 0 for x in rs.values()),
                    "n_studies_sum": sum(x["num_studies"] or 0 for x in rs.values()),
                    "mappable": bool(BY_KEY[a]["concepts"] and BY_KEY[b]["concepts"])})
    (C.OUT / "pairs_relationships.json").write_text(json.dumps({"concept_relationship_counts": nrel, "pairs": out}, indent=1))
    have = [p for p in out if p["relationships"]]
    print("concepts", len(c2k), "pairs", len(out), "mappable", sum(p["mappable"] for p in out), "with findings", len(have),
          "relationships", sum(len(p["relationships"]) for p in have), "with >=3 studies", sum(p["n_studies_sum"] >= 3 for p in have),
          "rels in >=3", sum(len(p["relationships"]) for p in have if p["n_studies_sum"] >= 3))
    print(sorted(nrel.items(), key=lambda x: -x[1])[:12])
    print("uncached so far", C.used())


if __name__ == "__main__":
    main()
