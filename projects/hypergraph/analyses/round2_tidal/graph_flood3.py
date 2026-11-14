import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tools"))
import requests
from concord import sysgraph as g
import graph_paths as gp
from graph_evidence import normalise
N = {"n": 0}
_orig = requests.get
def counted(*a, **k):
    N["n"] += 1; return _orig(*a, **k)
g.requests.get = counted
OUT = ROOT / "data" / "derived" / "round2" / "tidal_trend"
nb = json.load(open(OUT / "graph_flood_neighbours.json"))
res = {}
want = [("flooding", "post-traumatic stress disorder"), ("flood", "diarrhea"), ("flood", "dysentery"), ("flood", "post-traumatic stress disorder"), ("flood", "mortality rate"), ("flood", "malaria")]
for src, lab in want:
    for d in nb[src]["top"]:
        if d["label"] == lab:
            rows = []
            for rid in d["relationship_ids"]:
                for a in g.relationship_associations(rid):
                    n = normalise(a)
                    rows.append({"pubmed_id": a.get("pubmed_id"), "v1": a.get("variable_1_name"), "v2": a.get("variable_2_name"),
                                 "stat": a.get("system_statistic_type"), "value": a.get("statistic_value"), "ci": [a.get("ci_lower"), a.get("ci_upper")],
                                 "p": a.get("p_value"), "direction": n["direction"], "significant": n["significant"], "flags": n["flags"]})
            res[f"{src}->{lab}"] = rows
            print(f"{src} -> {lab}: {len(rows)} findings, studies {len({r['pubmed_id'] for r in rows})}, signs +{sum(r['direction']=='+' for r in rows)} -{sum(r['direction']=='-' for r in rows)}, sig {sum(bool(r['significant']) for r in rows)}")
            for r in rows[:6]: print("    ", r["pubmed_id"], "|", r["v1"], "|", r["v2"], "|", r["stat"], r["value"], r["ci"], r["direction"])
(OUT / "graph_flood_findings.json").write_text(json.dumps(res, indent=1, default=str))
print("uncached", N["n"])
