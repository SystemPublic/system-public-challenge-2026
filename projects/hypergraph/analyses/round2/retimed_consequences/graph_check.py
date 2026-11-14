"""Gap check in the System Public Graph for the three consequences. Counts uncached requests."""
import hashlib, json, sys, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from concord import sysgraph
OUT = ROOT / "data/derived/round2/retimed_consequences"
TERMS = {"taxi and for-hire demand": ["taxi", "ride-hailing", "ridesharing", "uber"],
         "daytime burglary": ["burglary", "burglaries", "guardianship", "home occupancy"],
         "EMS presence": ["ambulance", "emergency medical services", "EMS calls", "daytime population", "ambient population"],
         "same-day working at home": ["working from home", "telework", "remote work"]}
KEEP = {"taxi and for-hire demand": ["demand", "trips", "ridership", "pickup", "use of", "usage"],
        "daytime burglary": ["burglar"],
        "EMS presence": ["call", "dispatch", "volume", "demand", "daytime", "ambient", "weekday", "day of"],
        "same-day working at home": ["day", "burglar", "ambulance", "taxi", "crime"]}
unc = 0
def variables(term, limit=100):
    global unc
    params = {"search": f"name:{term}", "limit": limit}
    q = urllib.parse.urlencode(sorted(params.items()), doseq=True)
    sig = hashlib.sha256(f"/v1/variables?{q}".encode()).hexdigest()[:24]
    if not (sysgraph.CACHE / f"{sig}.json").exists():
        unc += 1
    return sysgraph.get("/v1/variables", params).get("data", [])
res = {}
for topic, terms in TERMS.items():
    names = {}
    for t in terms:
        for v in variables(t):
            names[v.get("system_id") or v.get("name")] = v.get("name")
    rel = sorted({n for n in names.values() if n and any(k in n.lower() for k in KEEP[topic])})
    res[topic] = {"search_terms": terms, "variables_matching": len(names), "names_with_relevant_words": rel}
    print(topic, len(names), len(rel)); [print("   ", n[:150]) for n in rel[:40]]
res["uncached_requests"] = unc
json.dump(res, open(OUT / "graph_gap_check.json", "w"), indent=1, ensure_ascii=False)
print("uncached", unc)
