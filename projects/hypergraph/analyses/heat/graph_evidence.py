"""Collect System Public Graph evidence for the heat topic.

Writes data/derived/heat/graph_evidence.json: for each chosen concept-pair
relationship, its counts and every association (variables, statistic, value,
interval, p, pubmed id); and for chosen variables, their associations.
All responses come through concord.sysgraph and are cached.
"""
from __future__ import annotations

import json
from pathlib import Path

from concord import sysgraph as s

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "heat" / "graph_evidence.json"

# relationship ids (source|target) chosen by reading the concept neighbourhoods
RELS = {
    # heat and violence
    "temperature -> homicide": "4FaXcuNJRt|YZku29igbl",
    "temperature -> suicide": "4FaXcuNJRt|TLeQZQ_leT",
    "temperature -> injury": "4FaXcuNJRt|rULjCt1BqH",
    "temperature -> mental disorder": "4FaXcuNJRt|-0HrxUPkp2",
    "extreme heat -> suicide": "wpUeTjUbAc|TLeQZQ_leT",
    "urban area -> violence": "kC0GoD2RzW|2qLKgaxkm_",
    # heat and health
    "thermodynamic temperature -> mortality rate": "PCdVJWVRyS|QPxlNKv3zV",
    "extreme heat -> mortality rate": "wpUeTjUbAc|QPxlNKv3zV",
    "temperature -> all-cause mortality": "4FaXcuNJRt|oEWjV89s3H",
    "thermodynamic temperature -> morbidity": "PCdVJWVRyS|3D_xrEmUvX",
    "heat illness -> temperature": "PtQBvGm5CM|4FaXcuNJRt",
    "extreme heat -> heat illness": "wpUeTjUbAc|PtQBvGm5CM",
    "hot -> heat illness": "dINFs04idR|PtQBvGm5CM",
    "urban area -> heat illness": "kC0GoD2RzW|PtQBvGm5CM",
    "housing -> heat illness": "IFcQ3j86qe|PtQBvGm5CM",
    "air conditioning -> heat stroke": "OnRtQgvIkg|rYCo7LTyzN",
    "thermodynamic temperature -> air conditioning": "PCdVJWVRyS|OnRtQgvIkg",
    "temperature -> emergency medical services": "gILy0ZWbmD|4FaXcuNJRt",
    "thermodynamic temperature -> emergency medical services": "PCdVJWVRyS|gILy0ZWbmD",
    "hyperthermia -> mortality rate": "FDJ4Gulj_Q|QPxlNKv3zV",
    # bridge links: vegetation, surface and air temperature, neighbourhood
    "NDVI -> thermodynamic temperature": "hsryqxdFzE|PCdVJWVRyS",
    "thermodynamic temperature -> NDVI": "PCdVJWVRyS|hsryqxdFzE",
    "NDVI -> ethnicity": "hsryqxdFzE|EhpdS79G1u",
    "thermodynamic temperature -> income": "PCdVJWVRyS|6yoKTYSOJa",
    "ethnicity -> temperature": "EhpdS79G1u|4FaXcuNJRt",
    "surface temperature -> air temperature": "sSuplgYnDQ|mUxSLRMwIy",
    "urban area -> surface temperature": "kC0GoD2RzW|sSuplgYnDQ",
    "deforestation -> surface temperature": "u1YgwfRTTz|sSuplgYnDQ",
    "population density -> surface temperature": "WLNXo1tGFr|sSuplgYnDQ",
    "urban area -> urban heat island": "kC0GoD2RzW|UbF0-c8zHb",
    "neighborhood characteristics -> urban heat island": "2gR7THM-gS|UbF0-c8zHb",
    "population density -> urban heat island": "WLNXo1tGFr|UbF0-c8zHb",
    "urban area -> thermodynamic temperature": "kC0GoD2RzW|PCdVJWVRyS",
    "urban area -> green space": "kC0GoD2RzW|lHLIKbfnYp",
}

VARS = {
    "rates of heat-related emergency department admissions": "u7xiLrAgHi",
    "ED visits for ICD-10 heat illness and cardiorespiratory codes": "FO-6O3XHC3",
    "increase in mortality due to a heat wave": "tL1k6wbDy9",
    "effect of temperatures above 75th percentile (heat waves)": "F5U_Ia9lMt",
    "lidar-derived canopy fraction": "wH2nKo1xoi",
    "LiDAR-based canopy loss": "Az1XWKFSFD",
    "background land surface temperature": "sUeVohbPHX",
    "personal heat exposure": "FWrHgors91",
    "level of greenness (NDVI) in residential area": "tYbPolLaCd",
}

KEEP = ("association_id", "variable_1", "variable_2", "statistic_type", "statistic_value", "ci_lower",
        "ci_upper", "p_value", "direction", "study_id", "pubmed_id", "doi", "population", "finding",
        "summary", "sentence")


def slim(a: dict) -> dict:
    out = {}
    for k, v in a.items():
        if isinstance(v, dict):
            out[k] = v.get("name") or v.get("wikidata_label") or v.get("system_id")
        elif not isinstance(v, list):
            out[k] = v
    return out


def main():
    res = {"api": s.API_VERSION, "dataset": s.DATASET_VERSION, "relationships": {}, "variables": {}}
    for label, rid in RELS.items():
        rel = s.relationship(rid)
        assoc = s.relationship_associations(rid, max_items=300) if rel and not rel.get("error") else []
        res["relationships"][label] = {
            "relationship_id": rid,
            "num_findings": rel.get("num_findings"), "num_studies": rel.get("num_studies"),
            "associations": [slim(a) for a in assoc],
        }
    for label, vid in VARS.items():
        assoc = s.variable_associations(vid, max_items=200)
        res["variables"][label] = {"variable_id": vid, "associations": [slim(a) for a in assoc]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(OUT.relative_to(ROOT), sum(len(v["associations"]) for v in res["relationships"].values()),
          sum(len(v["associations"]) for v in res["variables"].values()))


if __name__ == "__main__":
    main()
