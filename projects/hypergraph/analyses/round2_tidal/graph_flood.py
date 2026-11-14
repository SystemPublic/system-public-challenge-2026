"""What the System Public Graph links to flooding. Counts uncached requests."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tools"))
import requests
from concord import sysgraph as g
import graph_paths as gp

N = {"n": 0}
_orig = requests.get
def counted(*a, **k):
    N["n"] += 1
    return _orig(*a, **k)
g.requests.get = counted

OUT = ROOT / "data" / "derived" / "round2" / "tidal_trend"; OUT.mkdir(parents=True, exist_ok=True)
res = {}
for term in sys.argv[1:]:
    cs = g.concepts(term, limit=50)
    res[term] = [{"id": c["system_id"], "label": c.get("wikidata_label")} for c in cs]
    print(term, "->", [(c["system_id"], c.get("wikidata_label")) for c in cs][:15])
print("uncached requests so far", N["n"])
(OUT / "graph_concept_search.json").write_text(json.dumps(res, indent=1))
