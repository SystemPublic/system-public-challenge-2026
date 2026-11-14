"""Findings attached to the few graph variables that looked related to the three consequences."""
import hashlib, json, sys, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from concord import sysgraph
OUT = ROOT / "data/derived/round2/retimed_consequences"
LEADS = {"taxi": ["rideshare trips originating within a taxi zone-hour", "ridesharing trips", "ride-hailing service usage"],
         "burglary": ["burglaries", "burglary"],
         "ambulance": ["daytime population density", "call volume (among all EMS calls)", "EMS phone calls", "ambulance calls not originating from casinos",
                       "emergency medical service calls from mobile phones"],
         "telework": ["telework days", "working days (days when participants worked outside the home)", "working remotely 3-4 days per week"]}
SEARCH = {"taxi": ["taxi", "ride-hailing", "ridesharing", "uber"], "burglary": ["burglary", "burglaries"],
          "ambulance": ["ambulance", "emergency medical services", "EMS calls", "daytime population"], "telework": ["telework", "remote work", "working from home"]}
unc = 0
def cached(path, params):
    q = urllib.parse.urlencode(sorted(params.items()), doseq=True)
    return (sysgraph.CACHE / (hashlib.sha256(f"{path}?{q}".encode()).hexdigest()[:24] + ".json")).exists()
out = []
for topic, leads in LEADS.items():
    vs = {}
    for t in SEARCH[topic]:
        for v in sysgraph.get("/v1/variables", {"search": f"name:{t}", "limit": 100}).get("data", []):
            vs[v["system_id"]] = v
    for vid, v in vs.items():
        if not any(v["name"].lower().startswith(l.lower()) for l in leads):
            continue
        path = f"/v1/variables/{vid}/associations"
        if not cached(path, {"limit": 100, "offset": 0}):
            unc += 1
        for a in sysgraph.variable_associations(vid, max_items=100):
            rec = {"topic": topic, "lead": v["name"], **{k: a.get(k) for k in a if k in ("system_id", "variable_1_name", "variable_2_name", "statistic_type", "statistic_value", "ci_lower", "ci_upper", "p_value", "pubmed_id", "study_id", "direction")}}
            if len(out) == 0: print(sorted(a.keys()))
            out.append(rec)
json.dump({"uncached_requests": unc, "findings": out}, open(OUT / "graph_leads.json", "w"), indent=1, ensure_ascii=False)
for r in out:
    print(r["topic"], "|", {k: (str(v)[:90]) for k, v in r.items() if k not in ("topic", "system_id", "study_id")})
print("uncached", unc)
