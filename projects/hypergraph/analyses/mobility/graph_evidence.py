"""Research-side evidence from the System Public Graph for the mobility claims.

Writes data/derived/mobility/graph_evidence.json. Every call is cached by
concord.sysgraph, so a re-run costs no API requests once the cache exists.
"""
from __future__ import annotations

import json
import statistics as st
from collections import Counter
from pathlib import Path

from concord import sysgraph as s

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "mobility" / "graph_evidence.json"

C = {
    "asthma": "EAshH_Ko3h", "particulates": "gX6h_gZWHH", "nitrogen dioxide": "DC_F0GO0WQ",
    "air pollution": "P6IzhScRdx", "traffic-related pollution": "oG8Da1gCE9", "traffic": "HMQHUKEqkM",
    "traffic collision": "5aHRpqbEkQ", "walking": "_2dhcsFISl", "physical activity": "dPeET-pgVN",
    "obesity": "cj7G775u_Q", "pedestrian": "sz00kCqokr",
}
RATIO = {"odds_ratio", "relative_risk_ratio", "hazard_ratio", "incident_rate_ratio", "adjusted_odds_ratio",
         "prevalence_ratio"}


def summarise_assoc(assoc: list[dict]) -> dict:
    ratios = [a for a in assoc if a.get("statistic_type") in RATIO and a.get("statistic_value") is not None]
    vals = [a["statistic_value"] for a in ratios]
    sig_up = sum(1 for a in ratios if (a.get("ci_lower") or 0) > 1)
    sig_down = sum(1 for a in ratios if a.get("ci_upper") is not None and a["ci_upper"] < 1)
    return {
        "n_associations": len(assoc),
        "n_studies": len({a.get("study_id") for a in assoc}),
        "statistic_types": dict(Counter(a.get("statistic_type") for a in assoc)),
        "n_ratio": len(ratios),
        "ratio_above_1": sum(1 for v in vals if v > 1),
        "ratio_below_1": sum(1 for v in vals if v < 1),
        "ratio_ci_excludes_1_above": sig_up,
        "ratio_ci_excludes_1_below": sig_down,
        "ratio_median": round(st.median(vals), 3) if vals else None,
        "ratio_iqr": [round(x, 3) for x in st.quantiles(vals, n=4)[::2]] if len(vals) > 3 else None,
        "pubmed_ids": sorted({a["pubmed_id"] for a in assoc if a.get("pubmed_id")})[:400],
        "examples": [
            {k: a.get(k) for k in ("variable_1_name", "variable_2_name", "statistic_type", "statistic_value",
                                   "ci_lower", "ci_upper", "pubmed_id")}
            for a in sorted(ratios, key=lambda a: -(a.get("statistic_value") or 0))[:3]
        ],
    }


def pair(a: str, b: str) -> list[dict]:
    out = []
    for r in s.relationships_between(C[a], C[b]):
        assoc = s.relationship_associations(r["relationship_id"])
        out.append({"relationship_id": r["relationship_id"], "source": r["source_concept"]["wikidata_label"],
                    "target": r["target_concept"]["wikidata_label"], "num_findings": r["num_findings"],
                    "num_studies": r["num_studies"], "summary": summarise_assoc(assoc)})
    return out


def variable_assoc(vids: list[str]) -> list[dict]:
    rows = []
    for v in vids:
        for a in s.variable_associations(v):
            rows.append({k: a.get(k) for k in ("variable_1_name", "variable_2_name", "statistic_type",
                                               "statistic_value", "ci_lower", "ci_upper", "pubmed_id", "study_id")})
    return rows


def main():
    ev = {"api_version": s.API_VERSION, "dataset_version": s.DATASET_VERSION, "concepts": C, "pairs": {}}
    for a, b in [("particulates", "asthma"), ("nitrogen dioxide", "asthma"), ("air pollution", "asthma"),
                 ("traffic-related pollution", "asthma"), ("traffic", "nitrogen dioxide"),
                 ("traffic", "particulates"), ("traffic", "air pollution"),
                 ("traffic-related pollution", "nitrogen dioxide"),
                 ("walking", "obesity"), ("physical activity", "obesity")]:
        ev["pairs"][f"{a} -> {b}"] = pair(a, b)
    # speed cameras: no concept; the variable search finds the findings
    cams = ["LTqRVS0o7h", "lhdSkZS-Nu", "9QigEsnKpO", "9bq0Qq4wO0", "hU9A1_wTIg", "g7VuSEnvw3"]
    ev["speed_camera_variables"] = variable_assoc(cams)
    # road pricing: searched, nothing found
    ev["road_pricing_search"] = {
        "variable_searches": ["congestion pricing", "road pricing", "congestion charging", "low emission zone",
                              "cordon", "toll"],
        "relevant_hits": [x["name"] for q in ["toll", "traffic reduction"] for x in s.variables(q, limit=25)
                          if any(w in x["name"].lower() for w in ("toll booth", "traffic", "reduction in"))],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(ev, indent=1, ensure_ascii=False))
    for k, v in ev["pairs"].items():
        for r in v:
            sm = r["summary"]
            print(f"{k:45s} {r['relationship_id']:24s} f={r['num_findings']:4d} st={r['num_studies']:3d} "
                  f"ratio n={sm['n_ratio']} >1:{sm['ratio_above_1']} <1:{sm['ratio_below_1']} "
                  f"sig+:{sm['ratio_ci_excludes_1_above']} sig-:{sm['ratio_ci_excludes_1_below']} med={sm['ratio_median']}")
    print(len(ev["speed_camera_variables"]), "speed camera associations")
    print(ev["road_pricing_search"]["relevant_hits"])


if __name__ == "__main__":
    main()
