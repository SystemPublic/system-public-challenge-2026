#!/usr/bin/env python
"""Consequences of the re-timed week, read from the System Public Graph.

Step 1 of the experiment in docs/graph_experiments.md ("Consequences of the re-timed week").
For seven exposure families (commuting, telework, active commuting, sedentary time,
daily steps, isolation and loneliness, working hours) it searches study-variable names,
keeps the names that match the family's pattern, fetches every association of each kept
variable, and groups the other variable of each association by its concept.

Variable search matches any word of the term ("working from home" returns "locus of
control both at work and at home"), so the family patterns below do the real selection.

Writes, under data/derived/graph/retimed_week/:
  associations.csv         one row per finding (family, exposure name, outcome name and concept,
                           statistic, interval, p, direction, PMID)
  outcomes_by_family.csv   outcome concept x family: findings, studies, sign split
  variables.json           variables searched, kept and capped, per family
  requests.json            uncached API requests made by each run of this script

Re-runs from the cache without new requests. API v1.0; no version identifier is served.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import requests  # noqa: E402

from concord import sysgraph as g  # noqa: E402
from graph_evidence import normalise  # noqa: E402

OUT = ROOT / "data" / "derived" / "graph" / "retimed_week"
N_REQ = [0]
_orig = requests.get


def _counted(*a, **k):
    N_REQ[0] += 1
    return _orig(*a, **k)


requests.get = _counted

TERMS = ["commute time", "commuting", "commute", "telework", "telecommuting", "remote work", "working from home",
         "work from home", "home working", "sedentary", "sitting time", "daily steps", "walking to work",
         "active commuting", "social isolation", "loneliness", "working hours", "shift work", "overtime"]

# family -> (keep pattern, drop pattern, cap on variables)
FAMILIES = {
    "commuting": (r"commut", r"school|student|child|adolescen|active(ly)? commut|hearing specialist|trainee", 260),
    "telework": (r"telework|telecommut|remote(ly)? work|work(ing|ed|s)? remotely|work(ing|ed|s)? (from|at) home|"
                 r"home[- ]?work|home-based (tele)?work|\bWFH\b|hybrid work|home office", r"homework|care home|nursing home", 110),
    "active commuting": (r"walk(ing|ed)? (or (bik|cycl)\w+ )?to work|active(ly)? commut|cycl\w* to work|bik\w* to work|"
                         r"active travel|active transport|commut\w* (by|on) (foot|bic|bik|cycl)", r"school|student|child|adolescen", 90),
    "sedentary time": (r"sedentary (time|behaviou?r)|sitting time|time (spent )?sitting|occupational sitting|prolonged sitting",
                       r"\bapp\b|apps", 70),
    "daily steps": (r"daily step|steps (per|a|/) ?day|step count|steps taken", r"children|boys|girls", 40),
    "isolation and loneliness": (r"social(ly)? isolat|lonel", r"COVID-19 social isolation\)|intervention", 60),
    "working hours": (r"overtime|long working hours|working hours|work hours|shift work|night shift", r"", 60),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    allv: dict[str, str] = {}
    for t in TERMS:
        for v in g.variables(t, limit=150):
            allv.setdefault(v["system_id"], v["name"])
    kept, rows = {}, []
    for fam, (keep, drop, cap) in FAMILIES.items():
        m = [(i, n) for i, n in allv.items() if re.search(keep, n, re.I) and not (drop and re.search(drop, n, re.I))]
        kept[fam] = {"matched": len(m), "fetched": min(len(m), cap), "names": [n for _, n in m[:cap]]}
        for vid, vname in m[:cap]:
            for a in g.variable_associations(vid, max_items=500):
                side = "2" if a.get("variable_1_id") == vid else "1"
                n = normalise(a)
                rows.append({
                    "family": fam, "association_id": a.get("system_id"), "exposure_variable": vname,
                    "exposure_is_variable": "1" if side == "2" else "2",
                    "outcome_variable": a.get(f"variable_{side}_name"),
                    "outcome_concept_id": a.get(f"variable_{side}_concept_id") or "",
                    "statistic": a.get("system_statistic_type"), "value": a.get("statistic_value"),
                    "ci_lower": a.get("ci_lower"), "ci_upper": a.get("ci_upper"), "p": a.get("p_value"),
                    "direction": n["direction"] or "", "significant": n["significant"],
                    "flags": ";".join(n["flags"]), "study_id": a.get("study_id"), "pubmed_id": a.get("pubmed_id"),
                })
    # one finding can be reached from two kept variables of the same family; keep one copy per family
    seen, uniq = set(), []
    for r in rows:
        k = (r["family"], r["association_id"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    rows = uniq
    # outcome groups
    grp = defaultdict(lambda: {"n": 0, "studies": set(), "plus": 0, "minus": 0, "unsigned": 0, "sig": 0})
    for r in rows:
        key = (r["family"], r["outcome_concept_id"] or "name:" + (r["outcome_variable"] or "?").lower()[:60])
        d = grp[key]
        d["n"] += 1
        d["studies"].add(r["study_id"])
        d["plus" if r["direction"] == "+" else "minus" if r["direction"] == "-" else "unsigned"] += 1
        d["sig"] += 1 if r["significant"] else 0
    # label the concepts that matter (two or more findings in a family), to save requests
    need = {k[1] for k, d in grp.items() if not k[1].startswith("name:") and d["n"] >= 2}
    labels = {}
    for cid in sorted(need):
        c = g.concept(cid)
        labels[cid] = c.get("wikidata_label") or cid
    for r in rows:
        r["outcome_concept"] = labels.get(r["outcome_concept_id"], "")
    with open(OUT / "associations.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    out = []
    for (fam, key), d in grp.items():
        out.append({"family": fam, "outcome_concept_id": "" if key.startswith("name:") else key,
                    "outcome": labels.get(key, key[5:] + " (ungrounded)" if key.startswith("name:") else key),
                    "n_findings": d["n"], "n_studies": len(d["studies"]), "plus": d["plus"], "minus": d["minus"],
                    "unsigned": d["unsigned"], "significant": d["sig"]})
    out.sort(key=lambda x: (x["family"], -x["n_studies"], -x["n_findings"]))
    with open(OUT / "outcomes_by_family.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    (OUT / "variables.json").write_text(json.dumps({"terms": TERMS, "distinct_variables_returned": len(allv),
                                                    "families": kept}, indent=1))
    log = OUT / "requests.json"
    hist = json.loads(log.read_text()) if log.exists() else []
    hist.append({"script": "analyses/graph/retimed_week.py", "run": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                 "uncached_requests": N_REQ[0], "findings": len(rows)})
    log.write_text(json.dumps(hist, indent=1))
    print("uncached requests", N_REQ[0], "findings", len(rows))
    for fam in FAMILIES:
        print(fam, kept[fam]["matched"], kept[fam]["fetched"], sum(1 for r in rows if r["family"] == fam))


if __name__ == "__main__":
    main()
