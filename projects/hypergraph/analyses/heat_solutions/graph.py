"""What the System Public Graph holds on interventions against heat, by variable-name search.

For each term: the study variables whose name matches, and for the variables whose name
contains one of the term's required words, their associations. Each association is kept
with the other variable's name, the statistic and the PubMed id. Associations whose other
variable names violence or heat illness or mortality are marked. Writes
data/derived/heat_solutions/graph.json. Requests that were not in the cache are counted.
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

DER = ROOT / "data/derived/heat_solutions"
N_REQ = [0]
_get = requests.get


def counted(*a, **k):
    N_REQ[0] += 1
    return _get(*a, **k)


requests.get = counted

# term -> words of which at least one must be in the variable name
TERMS = {
    "air conditioning": ["air condition", "air-condition"],
    "air conditioner": ["air condition", "air-condition"],
    "cooling center": ["cooling"],
    "cooling": ["cooling"],
    "tree canopy": ["canopy", "tree"],
    "street trees": ["tree"],
    "vacant lot": ["vacant"],
    "greening": ["greening"],
    "green space": ["green space", "greenspace", "greenness"],
    "summer youth employment": ["summer", "youth employment"],
    "summer jobs": ["summer job", "summer employment"],
    "swimming pool": ["pool"],
    "park": ["park "],
    "street lighting": ["lighting"],
    "heat warning": ["warning", "alert", "action plan"],
    "heat action plan": ["warning", "alert", "action plan"],
    "school calendar": ["school"],
    "summer vacation": ["vacation", "summer break", "holiday"],
    "school holidays": ["holiday", "vacation"],
}
VIOLENCE = re.compile(r"violen|crime|homicid|assault|shoot|firearm|gun|aggress|injur", re.I)
HEAT = re.compile(r"heat|mortal|death|hypertherm|emergency|hospital", re.I)
MAX_VARS = 45


def main():
    out = {}
    for term, need in TERMS.items():
        try:
            vs = g.variables(term, limit=100)
        except Exception as e:
            out[term] = {"error": str(e)}
            continue
        keep = [v for v in vs if any(w in (v.get("name") or "").lower() + " " for w in need)]
        rows = []
        for v in keep[:MAX_VARS]:
            vid = v["system_id"]
            try:
                assoc = g.variable_associations(vid, max_items=200)
            except Exception:
                continue
            for a in assoc:
                side = "2" if a.get("variable_1_id") == vid else "1"
                other = a.get(f"variable_{side}_name") or "?"
                n = normalise(a)
                rows.append({"variable": v.get("name"), "other": other, "statistic": a.get("system_statistic_type"),
                             "value": a.get("statistic_value"), "ci": [a.get("ci_lower"), a.get("ci_upper")],
                             "p": a.get("p_value"), "direction": n["direction"], "pubmed_id": a.get("pubmed_id"),
                             "violence": bool(VIOLENCE.search(other)), "heat_or_death": bool(HEAT.search(other))})
        out[term] = {"variables_returned": len(vs), "variables_kept": len(keep), "variables_followed": min(len(keep), MAX_VARS),
                     "kept_names": sorted({v.get("name") for v in keep})[:80], "associations": rows}
        print(term, len(vs), len(keep), len(rows), "viol", sum(r["violence"] for r in rows), "heat", sum(r["heat_or_death"] for r in rows),
              "req", N_REQ[0], flush=True)
        if N_REQ[0] > 900:
            print("request budget reached")
            break
    out["_meta"] = {"uncached_requests": N_REQ[0], "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "api": g.API_VERSION}
    (DER / "graph.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
