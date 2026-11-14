"""Graph side of the Chicago transfer study: studies behind temperature x violence-side relationships.

Run: ~/.venvs/nyc-concordance/bin/python -m analyses.transfer.graph_temp_violence
Writes data/derived/graph/transfer_chicago/temp_violence_studies.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import analyses.transfer.gcount as gc  # noqa: E402
from concord import sysgraph as g  # noqa: E402

OUT = ROOT / "data" / "derived" / "graph" / "transfer_chicago"
T = {"4FaXcuNJRt": "temperature", "mUxSLRMwIy": "air temperature", "wpUeTjUbAc": "extreme heat", "rRpdh5vkse": "extreme cold",
     "KORxmct3X4": "extreme weather", "mPpkf6sGMO": "weather", "VbhaEHYy0f": "cold weather", "dINFs04idR": "hot",
     "GPTaDwgorI": "global warming"}
V = {"2qLKgaxkm_": "violence", "YZku29igbl": "homicide", "Sb3zGs-d5I": "violent crime", "V7ImOTxbql": "crime", "y83mBL5cYb": "aggression",
     "RdEfyciCY-": "aggressive behavior", "1pnN2AtyJB": "assault", "bYLGUlP0n-": "domestic violence", "QmevDxhzPZ": "intimate partner violence",
     "X7hfhwez9f": "gun violence", "14UOQBVakG": "firearm", "5-tHcH0EjT": "shooting", "VllUJmqrNV": "exposure to violence",
     "TLeQZQ_leT": "suicide", "cAz2Cd_y0K": "completed suicide", "aZJPqtlgv4": "attempted suicide", "rULjCt1BqH": "injury"}


def main():
    rels, studies = [], {}
    for tc, tl in T.items():
        for vc, vl in V.items():
            for r in g.relationships_between(tc, vc):
                rid = r["relationship_id"]
                st = g.relationship_studies(rid)
                rels.append({"relationship_id": rid, "temperature_side": tl, "violence_side": vl, "num_findings": r["num_findings"],
                             "num_studies": r["num_studies"], "study_ids_returned": [s["study_id"] for s in st]})
                for s in st:
                    d = studies.setdefault(s["study_id"], {"pubmed_id": s.get("pubmed_id"), "doi": s.get("doi"), "population": s.get("population"), "pairs": []})
                    d["pairs"].append([tl, vl])
    out = {"relationships": rels, "studies": studies, "api_requests_uncached": gc.N["uncached"]}
    (OUT / "temp_violence_studies.json").write_text(json.dumps(out, indent=1))
    print(len(rels), "relationships", len(studies), "studies", gc.N)


if __name__ == "__main__":
    main()
