"""Findings on each side of the candidate mediators between temperature and violence.

Step 2 of the heat-mechanisms experiment. For each candidate shared neighbour, fetches
every association on the temperature side and on the violence side, normalises the sign
and writes data/derived/graph/heat_mechanisms/candidate_findings.json.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from concord import sysgraph as g  # noqa: E402
from graph_evidence import normalise  # noqa: E402

OUT = ROOT / "data" / "derived" / "graph" / "heat_mechanisms"
CANDIDATES = ["sleep quality", "physical activity", "physical exercise", "walking", "alcohol consumption",
              "drinking behavior", "alcoholism", "psychological stress", "cortisol", "heart rate", "mental disorder",
              "mental depression", "suicide", "somnolence", "cocaine", "drug overdose", "schizophrenia", "fatigue",
              "psychotropic drug", "social isolation", "urban area", "sedentary lifestyle", "occupational stress",
              "traffic collision", "headache", "blood pressure"]


def rows(rel_ids):
    out = []
    for rid in rel_ids:
        for a in g.relationship_associations(rid, max_items=400):
            n = normalise(a)
            out.append({"relationship_id": rid, "v1": a.get("variable_1_name"), "v2": a.get("variable_2_name"),
                        "stat": a.get("system_statistic_type"), "value": a.get("statistic_value"),
                        "lo": a.get("ci_lower"), "hi": a.get("ci_upper"), "p": a.get("p_value"),
                        "direction": n["direction"], "significant": n["significant"], "flags": n["flags"],
                        "pmid": a.get("pubmed_id"), "study_id": a.get("study_id")})
    return out


def split(rs):
    return {"n": len(rs), "plus": sum(r["direction"] == "+" for r in rs), "minus": sum(r["direction"] == "-" for r in rs),
            "unsigned": sum(r["direction"] not in ("+", "-") for r in rs),
            "significant": sum(bool(r["significant"]) for r in rs), "studies": len({r["study_id"] for r in rs})}


def main():
    sh = json.loads((OUT / "shared_neighbours.json").read_text())
    by = {s["label"]: s for s in sh["shared"]}
    res = {}
    for lab in CANDIDATES:
        s = by.get(lab)
        if not s:
            continue
        t = rows([r for v in s["temp_via"].values() for r in v["relationship_ids"]])
        v = rows([r for k, vv in s["viol_via"].items() if k != "injury" for r in vv["relationship_ids"]])
        res[lab] = {"system_id": s["system_id"], "temp_via": {k: x["n_findings"] for k, x in s["temp_via"].items()},
                    "viol_via": {k: x["n_findings"] for k, x in s["viol_via"].items()},
                    "temp_split": split(t), "viol_split": split(v), "temp": t, "viol": v}
    (OUT / "candidate_findings.json").write_text(json.dumps(res, indent=1))
    for lab, d in res.items():
        print(f"\n== {lab}  temp {d['temp_via']} {d['temp_split']}  viol {d['viol_via']} {d['viol_split']}")
        for r in d["temp"][:14]:
            print(f"   T {r['direction'] or '?'} {str(r['v1'])[:55]} | {str(r['v2'])[:55]} | {r['stat']} {r['value']} [{r['lo']},{r['hi']}] p={r['p']} pmid={r['pmid']}")


if __name__ == "__main__":
    main()
