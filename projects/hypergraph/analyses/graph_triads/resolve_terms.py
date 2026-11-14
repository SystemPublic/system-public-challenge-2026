"""Stage 1: search the graph for each urban exposure term and print the labels returned."""
import json
from common import g, OUT, used
TERMS = ["noise", "traffic", "pollution", "nitrogen", "particulates", "particulate", "ozone", "heat", "temperature", "green", "greenspace", "park", "tree",
         "urban", "density", "crowding", "overcrowding", "housing", "homelessness", "homeless", "transport", "transportation", "walking", "cycling", "bicycle",
         "shift", "light", "flood", "flooding", "rats", "rodent", "pest", "cockroach", "eviction", "food", "alcohol", "poverty", "unemployment",
         "neighbourhood", "neighborhood", "walkability", "built", "commuting", "crime", "mold", "smoke", "lead"]
res = {}
for t in TERMS:
    rows = g.concepts(t, limit=50)
    res[t] = [{"system_id": r["system_id"], "label": r.get("wikidata_label"), "desc": (r.get("wikidata_description") or "")[:60]} for r in rows]
    print(t, "|", "; ".join(f"{r['label']}" for r in res[t][:50]))
(OUT / "term_search.json").write_text(json.dumps(res, indent=1))
print("uncached so far", used())
