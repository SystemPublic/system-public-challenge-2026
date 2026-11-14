"""What the System Public Graph holds on heat combined with medications and chronic conditions.

Three passes, all by variable-name search (concept search returns little for these terms):
  A. paired searches "<heat word> <drug or condition word>"; every variable returned is kept
     if its name holds a heat word, and its associations are followed;
  B. drug and condition terms alone; variables whose name also holds a heat word are followed;
  C. heat-outcome terms (heat-related illness, hospitalisation, death, heatstroke); every
     association of those variables is followed and kept when the other variable names a drug
     class or a condition of interest.
Each kept association is written with both variable names, the statistic, the PubMed id and
the term that found it. Writes data/derived/heat_drugs/graph.json. Uncached requests are counted.
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
import requests  # noqa: E402

from concord import sysgraph as g  # noqa: E402
from graph_evidence import normalise  # noqa: E402

DER = ROOT / "data/derived/heat_drugs"
N_REQ = [0]
_get = requests.get


def counted(*a, **k):
    N_REQ[0] += 1
    return _get(*a, **k)


requests.get = counted

HEAT_WORDS = ["heat", "heatwave", "temperature", "hot", "hyperthermia"]
TARGET_WORDS = ["antipsychotic", "neuroleptic", "psychotropic", "anticholinergic", "diuretic", "beta blocker",
                "beta-blocker", "ACE inhibitor", "angiotensin", "SSRI", "antidepressant", "lithium", "insulin",
                "sulfonylurea", "SGLT2", "opioid", "medication", "drug", "schizophrenia", "psychiatric", "mental",
                "psychosis", "diabetes", "dementia", "Alzheimer", "kidney", "renal"]
OUTCOME_TERMS = ["heat-related illness", "heat-related hospitalization", "heat-related death", "heat-related mortality",
                 "heatstroke", "heat stroke", "heat illness", "heat wave mortality", "heat wave hospital",
                 "extreme heat", "heat exposure", "high temperature mortality", "temperature mortality"]

HEAT_RE = re.compile(r"\bheat|heatwave|temperature|\bhot\b|hypertherm|thermoreg|warm", re.I)
CLASS_RE = {
    "antipsychotic": r"antipsychot|neurolept|clozapine|olanzapine|haloperidol|risperidone|quetiapine|phenothiazine",
    "anticholinergic": r"anticholinerg",
    "diuretic": r"diuretic|furosemide|thiazide",
    "beta blocker": r"beta.?block|β.?block",
    "ACE inhibitor / ARB": r"ace inhib|angiotensin|\barb\b",
    "SSRI / antidepressant": r"ssri|serotonin reuptake|antidepress",
    "lithium": r"lithium",
    "insulin": r"insulin",
    "sulfonylurea": r"sulfonylurea|sulphonylurea",
    "SGLT2 inhibitor": r"sglt",
    "opioid": r"opioid|opiate|methadone",
    "psychotropic (any)": r"psychotrop|psychiatric (drug|medic)",
    "medication (any)": r"medicat|\bdrug|prescri",
    "schizophrenia / psychosis": r"schizo|psychos|psychotic",
    "mental illness": r"mental|psychiatr",
    "diabetes": r"diabet",
    "dementia": r"dementia|alzheimer|cognitive impair",
    "kidney disease": r"kidney|renal",
}
CLASS_RE = {k: re.compile(v, re.I) for k, v in CLASS_RE.items()}


def classes(text: str) -> list[str]:
    return [k for k, r in CLASS_RE.items() if r.search(text or "")]


def follow(v: dict, found_by: str, rows: list, seen_assoc: set, require_class_in_other: bool):
    vid = v["system_id"]
    try:
        assoc = g.variable_associations(vid, max_items=300)
    except Exception:
        return
    for a in assoc:
        aid = a.get("system_id") or json.dumps(a, sort_keys=True)[:200]
        side = "2" if a.get("variable_1_id") == vid else "1"
        other = a.get(f"variable_{side}_name") or "?"
        both = (v.get("name") or "") + " || " + other
        cl = classes(both)
        if require_class_in_other and not classes(other):
            continue
        if not HEAT_RE.search(both) or not cl:
            continue
        if aid in seen_assoc:
            continue
        seen_assoc.add(aid)
        n = normalise(a)
        rows.append({"association_id": a.get("system_id"), "found_by": found_by, "variable": v.get("name"),
                     "other": other, "classes": cl, "statistic": a.get("system_statistic_type"),
                     "value": a.get("statistic_value"), "ci": [a.get("ci_lower"), a.get("ci_upper")],
                     "p": a.get("p_value"), "direction": n["direction"], "significant": n["significant"],
                     "pubmed_id": a.get("pubmed_id"), "study_id": a.get("study_id")})


def main():
    rows, seen_var, seen_assoc, searches = [], set(), set(), {}
    # A. paired searches
    for h in HEAT_WORDS:
        for t in TARGET_WORDS:
            term = f"{h} {t}"
            vs = g.variables(term, limit=100)
            searches[term] = len(vs)
            for v in vs:
                if v["system_id"] in seen_var or not HEAT_RE.search(v.get("name") or ""):
                    continue
                seen_var.add(v["system_id"])
                follow(v, "A:" + term, rows, seen_assoc, False)
        print("A", h, len(rows), "req", N_REQ[0], flush=True)
    # B. drug and condition terms alone
    for t in TARGET_WORDS:
        vs = g.variables(t, limit=100)
        searches[t] = len(vs)
        for v in vs:
            if v["system_id"] in seen_var or not HEAT_RE.search(v.get("name") or ""):
                continue
            seen_var.add(v["system_id"])
            follow(v, "B:" + t, rows, seen_assoc, False)
    print("B", len(rows), "req", N_REQ[0], flush=True)
    # C. heat outcomes, other side names a drug or condition
    for t in OUTCOME_TERMS:
        vs = g.variables(t, limit=100)
        searches[t] = len(vs)
        for v in vs[:60]:
            if v["system_id"] in seen_var:
                continue
            seen_var.add(v["system_id"])
            follow(v, "C:" + t, rows, seen_assoc, True)
        print("C", t, len(rows), "req", N_REQ[0], flush=True)
        if N_REQ[0] > 850:
            print("request budget reached")
            break
    out = {"associations": rows, "searches": searches, "variables_followed": len(seen_var),
           "_meta": {"uncached_requests": N_REQ[0], "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                     "api": g.API_VERSION}}
    DER.mkdir(parents=True, exist_ok=True)
    (DER / "graph.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print("rows", len(rows), "variables followed", len(seen_var), "uncached requests", N_REQ[0])


if __name__ == "__main__":
    main()
