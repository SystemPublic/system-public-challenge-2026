"""Collect what the System Public Graph holds on gentrification, displacement, eviction and rent burden.
Variable-name search (the concepts are weak for urban exposures). Writes
data/derived/affordability/graph_findings.json: one row per association, no abstract text."""
import json, sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tools"))
from concord import sysgraph as g
from graph_evidence import normalise

TERMS = {"gentrification": 100, "gentrifying": 50, "gentrified": 50, "eviction": 100, "evicted": 50,
         "displacement": 100, "rent burden": 50, "housing cost burden": 50, "housing affordability": 50,
         "neighborhood change": 50, "unaffordable housing": 50, "forced move": 50, "residential instability": 50}
# words that must appear in the variable name for the broad terms
NEED = {"displacement": r"resident|hous|neighbo|gentrif|forced|urban|tenant|famil|communit",
        "rent burden": r"rent", "housing cost burden": r"hous", "housing affordability": r"hous|afford",
        "neighborhood change": r"neighbo", "forced move": r"move|reloc", "residential instability": r"resid|hous"}
n_req = 0
rows = []; seen = set(); nvars = {}
for term, lim in TERMS.items():
    vs = g.variables(term, limit=lim); n_req += 1
    keep = [v for v in vs if term not in NEED or re.search(NEED[term], (v.get("name") or "").lower())]
    nvars[term] = {"matched": len(vs), "kept": len(keep)}
    for v in keep:
        vid = v["system_id"]
        if vid in seen: continue
        seen.add(vid)
        assoc = g.variable_associations(vid, max_items=300); n_req += 1
        for a in assoc:
            side = "2" if a.get("variable_1_id") == vid else "1"
            n = normalise(a)
            rows.append({"term": term, "variable_id": vid, "variable": v.get("name"),
                         "other": a.get(f"variable_{side}_name"), "other_concept_id": a.get(f"variable_{side}_concept_id"),
                         "statistic": a.get("system_statistic_type"), "value": a.get("statistic_value"),
                         "ci_lower": a.get("ci_lower"), "ci_upper": a.get("ci_upper"), "p": a.get("p_value"),
                         "direction": n["direction"], "significant": n["significant"], "flags": n["flags"],
                         "pubmed_id": a.get("pubmed_id"), "study_id": a.get("study_id"), "association_id": a.get("system_id")})
out = ROOT / "data/derived/affordability/graph_findings.json"
out.write_text(json.dumps({"terms": nvars, "requests_upper_bound": n_req, "api": g.API_VERSION, "dataset": g.DATASET_VERSION, "rows": rows}, indent=1))
print(nvars, "requests<=", n_req, "rows", len(rows), "variables", len(seen), "pmids", len({r["pubmed_id"] for r in rows}))
