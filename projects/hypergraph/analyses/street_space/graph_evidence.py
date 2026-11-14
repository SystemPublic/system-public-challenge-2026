"""System Public Graph searches for street-space reallocation: traffic volume, bus lanes,
pedestrian zones, road closure, congestion, travel time. Writes
data/derived/street_space/graph_evidence.json (variable hits and their associations)."""
from __future__ import annotations

import json
from pathlib import Path

from concord import sysgraph as sg

OUT = Path(__file__).resolve().parents[2] / "data" / "derived" / "street_space" / "graph_evidence.json"
TERMS = ["traffic volume", "traffic", "bus lane", "pedestrian", "pedestrianization", "road closure",
         "car-free", "congestion", "travel time", "street closure", "bus", "retail sales", "road space"]


def main():
    res = {}
    for t in TERMS:
        vs = sg.variables(t, limit=50)
        res[t] = [{"system_id": v.get("system_id"), "name": v.get("name"), "concept": v.get("concept_label") or v.get("wikidata_label")} for v in vs]
        print(t, len(vs))
    OUT.write_text(json.dumps({"api": sg.API_VERSION, "dataset": sg.DATASET_VERSION, "variables": res}, indent=1))


if __name__ == "__main__":
    main()


# Variables read in detail (chosen from the search output above).
DETAIL = ["U34KTySDCD", "GlHfryOlBp", "Qu-Vin6Tq-", "hPfVszjBiD", "aujJlM_IGI", "iD0lYU2CMq", "LjEa5hpOrg", "XSxbFEAcg2"]


def detail():
    out = {}
    for vid in DETAIL:
        a = sg.variable_associations(vid, max_items=50)
        out[vid] = [{k: x.get(k) for k in ("association_id", "variable_1_name", "variable_2_name", "statistic_type",
                                             "statistic_value", "ci_lower", "ci_upper", "p_value", "study_id", "pubmed_id")}
                    for x in a]
    p = OUT.with_name("graph_detail.json")
    p.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__" and len(__import__("sys").argv) > 1:
    for k, v in detail().items():
        print("==", k)
        for x in v:
            print("  ", x)
