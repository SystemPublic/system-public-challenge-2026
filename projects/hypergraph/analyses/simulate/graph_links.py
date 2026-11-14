"""What the System Public Graph holds on each link of the congestion-pricing chain.

For each link a list of search terms for study-variable names and a pattern for the
variable at the other end. Writes data/derived/simulate/graph_links.json: counts and
the findings (statistic, interval, PubMed id), with no abstract text.
Run: python -m analyses.simulate.graph_links        (about 150 API requests, cached)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from concord import sysgraph as g

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "simulate" / "graph_links.json"

LINKS = {
    "toll -> vehicle entries": (["congestion charge", "congestion pricing", "road pricing", "toll"],
                                r"traffic|vehicle|volume|trips|car use|driving"),
    "vehicle entries -> speed": (["traffic volume", "traffic congestion"], r"speed|travel time|delay"),
    "speed -> ambulance travel time": (["traffic congestion", "ambulance response time", "EMS response time"],
                                       r"ambulance|ems|response time|emergency medical"),
    "ambulance time -> survival": (["ambulance response time", "EMS response time", "response time interval",
                                    "time to defibrillation"],
                                   r"surviv|mortal|death|discharge|neurolog"),
    "visits -> retail activity": (["footfall", "pedestrian volume", "retail sales", "foot traffic"],
                                  r"sales|revenue|retail|spend|business|restaurant"),
    "toll -> retail activity": (["congestion charge", "congestion pricing", "road pricing"], r"sales|retail|business|econom"),
    "entries or speed -> crashes": (["traffic volume", "traffic speed", "congestion charge"],
                                    r"crash|collision|injur|accident|fatal"),
}


def main():
    out = {}
    for link, (terms, pat) in LINKS.items():
        rx = re.compile(pat, re.I)
        found, nvars = [], 0
        for t in terms:
            vs = g.variables(t, limit=12)
            vs = [v for v in vs if any(w in (v.get("name") or "").lower() for w in t.lower().split()[:1])]
            nvars += len(vs)
            for v in vs:
                vid = v["system_id"]
                for a in g.variable_associations(vid, max_items=200):
                    side = "2" if a.get("variable_1_id") == vid else "1"
                    other = a.get(f"variable_{side}_name") or ""
                    if rx.search(other):
                        found.append({"term": t, "variable": v.get("name"), "other": other,
                                      "statistic": a.get("system_statistic_type"), "value": a.get("statistic_value"),
                                      "ci": [a.get("ci_lower"), a.get("ci_upper")], "p": a.get("p_value"),
                                      "pubmed_id": a.get("pubmed_id"), "study_id": a.get("study_id")})
        seen, uniq = set(), []
        for f in found:
            k = (f["pubmed_id"], f["variable"], f["other"], f["value"])
            if k not in seen:
                seen.add(k)
                uniq.append(f)
        out[link] = {"terms": terms, "other_end_pattern": pat, "variables_matched": nvars, "n_findings": len(uniq),
                     "n_studies": len({f["study_id"] for f in uniq}), "findings": uniq}
        print(link, nvars, len(uniq), out[link]["n_studies"])
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
