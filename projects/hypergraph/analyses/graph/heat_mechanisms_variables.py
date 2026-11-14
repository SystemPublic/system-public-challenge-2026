"""Outcomes linked to study variables whose NAME mentions heat (variable side).

Step 3 of the heat-mechanisms experiment. Like tools/graph_paths.consequences, but it
pools several terms, keeps every association row, and does not look up outcome concept
labels (one API call each); outcomes are grouped by concept id and labelled by their
most frequent variable name. Writes data/derived/graph/heat_mechanisms/variable_side.json.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from concord import sysgraph as g  # noqa: E402
from graph_evidence import normalise  # noqa: E402

OUT = ROOT / "data" / "derived" / "graph" / "heat_mechanisms"
TERMS = {"ambient temperature": 150, "heat wave": 150, "extreme heat": 150, "hot days": 150}


def main():
    seen, rows = set(), []
    nvars = {}
    for term, lim in TERMS.items():
        vs = g.variables(term, limit=lim)
        nvars[term] = len(vs)
        for v in vs:
            vid = v["system_id"]
            if vid in seen:
                continue
            seen.add(vid)
            for a in g.variable_associations(vid, max_items=300):
                side = "2" if a.get("variable_1_id") == vid else "1"
                n = normalise(a)
                rows.append({"term": term, "exposure": v.get("name"), "outcome": a.get(f"variable_{side}_name"),
                             "outcome_concept": a.get(f"variable_{side}_concept_id"),
                             "stat": a.get("system_statistic_type"), "value": a.get("statistic_value"),
                             "lo": a.get("ci_lower"), "hi": a.get("ci_upper"), "p": a.get("p_value"),
                             "direction": n["direction"], "significant": n["significant"], "flags": n["flags"],
                             "pmid": a.get("pubmed_id"), "study_id": a.get("study_id"), "assoc_id": a.get("system_id")})
    groups = {}
    for r in rows:
        k = r["outcome_concept"] or "name:" + (r["outcome"] or "?").lower()[:60]
        d = groups.setdefault(k, {"key": k, "names": Counter(), "n": 0, "plus": 0, "minus": 0, "studies": set()})
        d["names"][r["outcome"]] += 1
        d["n"] += 1
        d["plus"] += r["direction"] == "+"
        d["minus"] += r["direction"] == "-"
        d["studies"].add(r["study_id"])
    gl = [{"key": d["key"], "label": d["names"].most_common(1)[0][0], "n_findings": d["n"], "plus": d["plus"],
           "minus": d["minus"], "n_studies": len(d["studies"])} for d in groups.values()]
    gl.sort(key=lambda d: (-d["n_studies"], -d["n_findings"]))
    (OUT / "variable_side.json").write_text(json.dumps({"terms": nvars, "variables": len(seen), "associations": len(rows),
                                                        "outcome_groups": gl, "rows": rows}, indent=1))
    print(nvars, len(seen), "variables", len(rows), "associations", len(gl), "outcome groups")


if __name__ == "__main__":
    main()
