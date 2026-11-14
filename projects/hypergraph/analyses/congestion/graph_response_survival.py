"""What the System Public Graph holds on ambulance response time and survival,
and on congestion pricing. Searches study variable names (concept search is weak
for these exposures). Writes data/derived/congestion/graph_response_survival.json.
No abstract text is stored. Request budget: at most ~350 uncached calls.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from concord import sysgraph as g  # noqa: E402
from graph_evidence import normalise  # noqa: E402

DER = ROOT / "data" / "derived" / "congestion"
EXPOSURE_TERMS = ["ambulance response time", "EMS response time", "response time", "response interval",
                  "time to defibrillation", "call to arrival", "prehospital time", "transport time",
                  "time to EMS arrival", "ambulance arrival", "ambulance delay", "scene arrival"]
EXPO_RE = re.compile(r"(ambulance|ems|emergency medical|prehospital|pre-hospital|paramedic|defibrillat|call[- ]to|"
                     r"response (time|interval)|transport time|arrival)", re.I)
TIME_RE = re.compile(r"(time|interval|delay|minute|duration|arrival)", re.I)
OUT_RE = re.compile(r"(surviv|mortal|death|died|discharge|rosc|return of spontaneous|neurolog|cpc|fatal)", re.I)
PRICING_TERMS = ["congestion pricing", "congestion charge", "congestion charging", "road pricing", "cordon pricing",
                 "low emission zone", "congestion relief zone", "traffic congestion"]
BUSINESS_RE = re.compile(r"(retail|sales|restaurant|business|shop|store|revenue|employment|footfall|ambulance|"
                         r"emergency|response)", re.I)


def main():
    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "api": g.API_VERSION, "dataset": g.DATASET_VERSION}
    seen, kept, findings = set(), [], []
    for t in EXPOSURE_TERMS:
        for v in g.variables(t, limit=100):
            name = v.get("name") or v.get("variable_name") or ""
            vid = v["system_id"]
            if vid in seen or not (EXPO_RE.search(name) and TIME_RE.search(name)):
                continue
            seen.add(vid)
            kept.append({"id": vid, "name": name, "term": t})
    kept = kept[:260]
    for v in kept:
        for a in g.variable_associations(v["id"], max_items=200):
            side = "2" if a.get("variable_1_id") == v["id"] else "1"
            other = a.get(f"variable_{side}_name") or ""
            if not OUT_RE.search(other):
                continue
            n = normalise(a)
            findings.append({"exposure": v["name"], "outcome": other, "statistic": a.get("system_statistic_type"),
                             "value": a.get("statistic_value"), "ci": [a.get("ci_lower"), a.get("ci_upper")],
                             "p": a.get("p_value"), "direction": n["direction"], "significant": n["significant"],
                             "flags": n["flags"], "pubmed_id": a.get("pubmed_id"), "doi": a.get("doi"),
                             "study_id": a.get("study_id"), "association_id": a.get("system_id")})
    out["response_time"] = {"terms": EXPOSURE_TERMS, "variables_kept": len(kept), "n_findings": len(findings),
                            "n_studies": len({f["study_id"] for f in findings}), "findings": findings}
    pr = {}
    for t in PRICING_TERMS:
        vs = g.variables(t, limit=100)
        cs = g.concepts(t, limit=20)
        names = [(v.get("name") or v.get("variable_name") or "") for v in vs]
        pr[t] = {"n_variables": len(vs), "n_concepts": len(cs),
                 "concept_labels": [(c.get("wikidata_label") or "") for c in cs][:10],
                 "variable_names": names[:40]}
    out["pricing"] = pr
    (DER / "graph_response_survival.json").write_text(json.dumps(out, indent=1))
    print(len(kept), "variables;", len(findings), "findings;", out["response_time"]["n_studies"], "studies")
    for t, d in pr.items():
        print(t, d["n_variables"], d["n_concepts"], d["concept_labels"][:4])


if __name__ == "__main__":
    main()
