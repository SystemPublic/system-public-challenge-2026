"""Step 2: fetch the associations of the matched variables (one request per variable).

Variables are taken shortest name first (short names are the plain exposure, long names
carry subgroup qualifiers), up to CAP per intervention (CAPS for some). Writes one row per association.
"""
import csv, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import budget
from budget import g, ROOT
from graph_evidence import normalise
from interventions import INTERVENTIONS
OUT = ROOT / "data/derived/all_boats"
CAP = 30
# Second pass (same day): more variables for the features the question names and for the largest sets.
CAPS = {"street_trees": 60, "green_space": 60, "air_conditioning": 60, "recreation_centres": 50, "third_places": 56,
        "libraries": 50, "public_pools": 45, "housing_repair": 45, "supermarkets": 40, "transit_access": 45}
EXTRA_DROP = r"fusarium|blight (resist|incid|sever|index|infect|rating)|sheath|tuber|cassava|chickpea|apple|blossom|wheat|orchard|leaf|seedling|pig|cattle|broiler|mice|rats?\b|poultry|larva|soil"
vars_ = json.loads((OUT / "variables_matched.json").read_text())
rows = []
for key, spec in INTERVENTIONS.items():
    vs = [v for v in vars_[key] if not re.search(EXTRA_DROP, v["name"], re.I)]
    vs.sort(key=lambda v: len(v["name"]))
    for v in vs[:CAPS.get(key, CAP)]:
        for a in g.variable_associations(v["id"], max_items=100):
            side = "2" if a.get("variable_1_id") == v["id"] else "1"
            n = normalise(a)
            rows.append({"intervention": key, "exposure_var": v["name"], "outcome_var": a.get(f"variable_{side}_name"),
                         "outcome_concept_id": a.get(f"variable_{side}_concept_id"), "statistic": a.get("system_statistic_type"),
                         "value": a.get("statistic_value"), "ci_lower": a.get("ci_lower"), "ci_upper": a.get("ci_upper"),
                         "p": a.get("p_value"), "direction": n["direction"], "significant": n["significant"],
                         "flags": "|".join(n["flags"]), "study_id": a.get("study_id"), "pubmed_id": a.get("pubmed_id"),
                         "association_id": a.get("system_id")})
    print(key, "vars", min(len(vs), CAPS.get(key, CAP)), "of", len(vs), "rows", sum(r["intervention"] == key for r in rows), "| used", budget.used(), flush=True)
# variables named for gentrification or displacement: what are they linked to?
gv = [v for v in vars_["_gentrification"] if re.search(r"gentrif|residential displac|property value|hous(e|ing) price|\brents?\b|rental price|home value", v["name"], re.I)
      and not re.search(EXTRA_DROP, v["name"], re.I)]
gv.sort(key=lambda v: (0 if re.search("gentrif", v["name"], re.I) else 1, len(v["name"])))
for v in gv[:45]:
    for a in g.variable_associations(v["id"], max_items=100):
        side = "2" if a.get("variable_1_id") == v["id"] else "1"
        n = normalise(a)
        rows.append({"intervention": "_gentrification", "exposure_var": v["name"], "outcome_var": a.get(f"variable_{side}_name"),
                     "outcome_concept_id": a.get(f"variable_{side}_concept_id"), "statistic": a.get("system_statistic_type"),
                     "value": a.get("statistic_value"), "ci_lower": a.get("ci_lower"), "ci_upper": a.get("ci_upper"),
                     "p": a.get("p_value"), "direction": n["direction"], "significant": n["significant"],
                     "flags": "|".join(n["flags"]), "study_id": a.get("study_id"), "pubmed_id": a.get("pubmed_id"),
                     "association_id": a.get("system_id")})
print("gentrification vars", min(len(gv), 45), "of", len(gv), "| used", budget.used())
with open(OUT / "associations.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "rows")
