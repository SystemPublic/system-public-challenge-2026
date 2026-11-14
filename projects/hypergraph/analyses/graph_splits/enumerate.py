"""Step 1 of the split-literature study: list relationships of urban exposure concepts.

For each exposure concept (chosen by hand from concept-search results, see FAMILIES)
this lists its relationships through the API (tools/graph_paths.neighbours does the
same with pages of 100; this uses pages of 1000 to save requests) and keeps those
with at least 8 findings from at least 5 studies. Output:
data/derived/graph/splits/candidates.json.
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import sysgraph as g

FAMILIES = {
 "air pollution": ["air pollution", "traffic-related pollution", "air pollutant", "particulates", "nitrogen dioxide",
                   "nitrogen oxide", "ozone", "sulfur dioxide", "carbon monoxide", "soot", "indoor air pollution",
                   "environmental pollution"],
 "noise": ["noise pollution", "traffic noise", "noise"],
 "heat and cold": ["hot", "heat wave", "cold", "cold weather", "Extreme Cold", "air temperature", "temperature",
                   "surface temperature", "urban heat island", "weather", "extreme weather", "humidity", "relative humidity"],
 "green space": ["green space", "park", "tree", "vegetation cover", "Normalized Difference Vegetation Index",
                 "vegetation", "built environment"],
 "active travel and transport": ["walking", "cycling", "public transport", "traffic"],
 "urban or rural residence": ["urban area", "urbanization", "urban population", "rural area", "rural population",
                              "residence characteristics", "city", "population density"],
 "crowding": ["household crowding", "overcrowding"],
 "housing": ["housing", "housing quality", "housing instability", "public housing", "renting", "homeless person", "ownership"],
 "neighbourhood deprivation": ["neighborhood", "neighborhood characteristics", "social deprivation", "poverty",
                               "poverty area", "child poverty", "Residential segregation"],
 "unemployment": ["unemployed", "unemployment"],
 "night work": ["shift work"],
 "social isolation": ["social isolation", "loneliness"],
 "migration status": ["migrant", "immigrant", "immigration", "emigration and immigration", "refugee",
                      "transient and migrant people", "migrant worker"],
 "school": ["school", "primary school", "school attendance", "school enrollment", "school violence", "bullying"],
}

def find(label):
    for word in sorted(label.replace("-", " ").split(), key=len, reverse=True):
        for r in g.concepts(word, limit=50):
            if (r.get("wikidata_label") or "").lower() == label.lower():
                return r
    return None

def rels(cid):
    out, seen, off = [], set(), 0
    while True:
        rows = g.get(f"/v1/concepts/{cid}/relationships", {"limit": 1000, "offset": off}).get("data", [])
        for r in rows:
            if r["relationship_id"] not in seen:
                seen.add(r["relationship_id"]); out.append(r)
        if len(rows) < 1000: break
        off += 1000
    return out

def main():
    concepts, cands = [], []
    for fam, labels in FAMILIES.items():
        for lab in labels:
            c = find(lab)
            if not c:
                concepts.append({"family": fam, "label": lab, "found": False}); continue
            rs = rels(c["system_id"])
            keep = [r for r in rs if (r.get("num_findings") or 0) >= 8 and (r.get("num_studies") or 0) >= 5
                    and r["source_concept"]["system_id"] != r["target_concept"]["system_id"]]
            concepts.append({"family": fam, "label": lab, "found": True, "system_id": c["system_id"],
                             "n_relationships": len(rs), "n_findings": sum(r.get("num_findings") or 0 for r in rs),
                             "n_ge8x5": len(keep)})
            for r in keep:
                cands.append({"family": fam, "exposure": lab, "exposure_id": c["system_id"], "relationship_id": r["relationship_id"],
                              "source": r["source_concept"]["wikidata_label"], "target": r["target_concept"]["wikidata_label"],
                              "num_findings": r["num_findings"], "num_studies": r["num_studies"]})
            print(f"{fam:28s} {lab:38s} rels {len(rs):5d} kept {len(keep)}")
    out = ROOT / "data/derived/graph/splits/candidates.json"
    out.write_text(json.dumps({"concepts": concepts, "candidates": cands, "api": g.API_VERSION}, indent=1))
    print(len(cands), "candidate relationships;", len({c['relationship_id'] for c in cands}), "distinct")

if __name__ == "__main__":
    main()
