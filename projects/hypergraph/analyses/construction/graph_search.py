"""Search the System graph for construction, vacant land and housing supply evidence.
Writes data/derived/construction/graph_search.json. Run from the repo root."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import sysgraph as sg

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "construction"
OUT.mkdir(parents=True, exist_ok=True)

terms = sys.argv[1:] or ["construction", "vacant", "permit", "permits", "housing", "building", "buildings",
                         "zoning", "demolition", "renovation", "scaffolding", "completion", "development"]
res = {}
for t in terms:
    v = sg.variables(t, limit=50)
    c = sg.concepts(t, limit=20)
    res[t] = {"variables": [{k: x.get(k) for k in ("variable_id", "id", "name", "concept_id", "concept", "study_id")} | {"_raw_keys": list(x.keys())} for x in v],
              "concepts": [{k: x.get(k) for k in ("system_id", "wikidata_id", "wikidata_label")} for x in c]}
    print(t, len(v), "variables", len(c), "concepts")
    for x in v[:50]:
        print("   V", x.get("name"))
    for x in c[:20]:
        print("   C", x.get("system_id"), x.get("wikidata_label"))
f = OUT / "graph_search.json"
old = json.loads(f.read_text()) if f.exists() else {}
old.update(res)
f.write_text(json.dumps(old, indent=1))
