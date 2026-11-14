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
    N["n"] += 1; return _orig(*a, **k)
g.requests.get = counted
OUT = ROOT / "data" / "derived" / "round2" / "tidal_trend"
ids = {"flood disaster": "NfqwQkrVlq", "flooding": "AByRAdx2GF", "flood": "LQWjUNDY2O", "sea level rise": "rSNUatmq8T", "sea level": "4v2R8cNkVy"}
res = {}
for lab, cid in ids.items():
    nb = gp.neighbours(cid)
    rows = sorted(nb.values(), key=lambda d: -d["n_findings"])
    res[lab] = {"id": cid, "n_neighbours": len(nb), "top": [{k: d[k] for k in ("label", "n_findings", "n_studies", "relationship_ids")} for d in rows[:40]]}
    print(lab, len(nb), "neighbours; uncached", N["n"])
    for d in rows[:25]:
        print("   ", d["n_findings"], d["n_studies"], d["label"])
(OUT / "graph_flood_neighbours.json").write_text(json.dumps(res, indent=1))
print("uncached requests", N["n"])
