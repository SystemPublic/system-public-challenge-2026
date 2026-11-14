"""heat-night-minimum: what the System Public Graph holds on night or minimum temperature and
sleep, and on sleep and aggression or violence. API only (the Dataverse copy is not on this
machine), through the cache in data/cache/sysgraph. Writes data/derived/round5/heat_night/graph.json.
Run before the registration; no city data are read here.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from concord import sysgraph as g  # noqa: E402
from graph_evidence import normalise  # noqa: E402

DER = ROOT / "data/derived/round5/heat_night"
DER.mkdir(parents=True, exist_ok=True)

NIGHT_VARS = ["yayQTvS9lD", "1LUWojNDUv", "Q89QMcX8mT", "HJ6iHDyLOu", "QIKebuPnAf", "ifxwdUN7jx", "vuGI8Z7rzh",
              "4_Us9m79KM", "EDYkUy0r3k", "0SZFkEwEQv", "dipcr0PX7c", "2JK1L7MVbU", "_9nBl4B_FR", "_cTKJMhZph",
              "4jpP_DFYV9", "xycYrP2vcv", "ygo-nXuMA0", "hlK5x8naHn", "DiyNCo6rNM", "8a11ooV0z1", "KWsDG6HdPT",
              "FxLNI4temC", "VowrulaZL5"]
TEMP = {"4FaXcuNJRt": "temperature", "mUxSLRMwIy": "air temperature", "dINFs04idR": "hot"}
SLEEP = {"nDIFXeS4Xr": "sleep", "aeY3nW1sT_": "sleep quality", "k4RCuWBkJ3": "sleep duration", "1f0aF1BXj-": "insomnia",
         "7dRlP44-ka": "sleep deprivation", "smZJCBkfGP": "sleep disturbance"}
AGG = {"y83mBL5cYb": "aggression", "RdEfyciCY-": "aggressive behavior", "2qLKgaxkm_": "violence"}
KEEP = ("system_id", "variable_1_name", "variable_2_name", "statistic_type", "system_statistic_type", "statistic_value",
        "ci_lower", "ci_upper", "p_value", "study_id", "pubmed_id")


def slim(a):
    n = normalise(a)
    return {**{k: a.get(k) for k in KEEP}, "direction": n.get("direction"), "significant": n.get("significant"),
            "flags": n.get("flags")}


def pair(x, y):
    out = []
    for rid in (f"{x}|{y}", f"{y}|{x}"):
        rel = g.relationship(rid)
        if not rel or rel.get("error") or not rel.get("relationship_id"):
            continue
        assoc = g.relationship_associations(rid)
        out.append({"relationship_id": rid, "num_findings": rel.get("num_findings"), "num_studies": rel.get("num_studies"),
                    "n_returned": len(assoc), "associations": [slim(a) for a in assoc]})
    return out


def main():
    n0 = len(os.listdir(g.CACHE))
    res = {"night_variables": {}, "temperature_sleep": {}, "sleep_aggression": {}}
    for v in NIGHT_VARS:
        a = g.variable_associations(v)
        res["night_variables"][v] = [slim(x) for x in a]
    for t, tl in TEMP.items():
        for s, sl in SLEEP.items():
            r = pair(t, s)
            if r:
                res["temperature_sleep"][f"{tl} x {sl}"] = r
    for s, sl in SLEEP.items():
        for a, al in AGG.items():
            r = pair(s, a)
            if r:
                res["sleep_aggression"][f"{sl} x {al}"] = r
    res["uncached_requests_this_run"] = len(os.listdir(g.CACHE)) - n0
    (DER / "graph.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("uncached requests", res["uncached_requests_this_run"])
    for sec in ("temperature_sleep", "sleep_aggression"):
        for k, rs in res[sec].items():
            for r in rs:
                print(sec, k, r["relationship_id"], "findings", r["num_findings"], "studies", r["num_studies"], "returned", r["n_returned"])
    for v, a in res["night_variables"].items():
        for x in a:
            print(v, "|", (x["variable_1_name"] or "")[:70], "|", (x["variable_2_name"] or "")[:70], "|", x["system_statistic_type"],
                  x["statistic_value"], x["ci_lower"], x["ci_upper"], x["pubmed_id"])


if __name__ == "__main__":
    main()
