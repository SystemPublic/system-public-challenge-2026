"""Step 1: search the graph's variable names for each intervention's terms."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import budget
from budget import g, ROOT
from interventions import INTERVENTIONS, GENTRIFICATION_TERMS
OUT = ROOT / "data/derived/all_boats"
res = {}
for key, spec in INTERVENTIONS.items():
    seen = {}
    for t in spec["terms"]:
        for v in g.variables(t, limit=100):
            nm = v.get("name") or ""
            if re.search(spec["keep"], nm, re.I) and not re.search(spec["drop"], nm, re.I):
                seen[v["system_id"]] = {"id": v["system_id"], "name": nm, "term": t}
    res[key] = list(seen.values())
    print(key, len(res[key]), "| used", budget.used())
gent = {}
for t in GENTRIFICATION_TERMS:
    for v in g.variables(t, limit=100):
        gent[v["system_id"]] = {"id": v["system_id"], "name": v.get("name") or "", "term": t}
res["_gentrification"] = list(gent.values())
(OUT / "variables_matched.json").write_text(json.dumps(res, indent=1))
print("gentrification-side vars", len(gent), "used", budget.used())
