"""Pull graph-level context from the System Public Graph API.

1. The malaria neighbourhood: relationships touching the 'malaria' concept, sorted by num_studies
   (same traversal as System's own Demo 1), tagged by whether the neighbour is one of our interventions.
2. Intervention concept relationships (mosquito net, malaria vaccine, chemoprevention if present).
3. Coverage of the hand-verified anchor papers across three layers:
   Beta API study record / Beta API associations / fixed Dataverse CSV.
"""
from __future__ import annotations

import pandas as pd

from common import GRAPH, RAW_CSV, VERIFIED, SystemAPI, write_json

CONCEPT_LABELS = ["malaria", "mosquito net", "malaria vaccine", "malaria prevention", "chemoprevention",
                  "insecticide-treated net", "indoor residual spraying"]


def find_exact(api: SystemAPI, label: str):
    hits = api.paginate("/v1/concepts", {"search": f"wikidata_label:{label}"}, page_size=50, max_records=300)
    exact = [c for c in hits if (c.get("wikidata_label") or "").strip().lower() == label.lower()]
    return exact[0] if exact else None


def rel_summary(r: dict, anchor_id: str) -> dict:
    src, tgt = r["source_concept"], r["target_concept"]
    other = tgt if src["system_id"] == anchor_id else src
    return {
        "relationship_id": r["relationship_id"],
        "direction": "anchor → other" if src["system_id"] == anchor_id else "other → anchor",
        "other_id": other["system_id"], "other_label": other.get("wikidata_label"),
        "other_wikidata": other.get("wikidata_id"),
        "num_studies": r.get("num_studies"), "num_findings": r.get("num_findings"),
        "last_published_date": r.get("last_published_date"),
    }


def main() -> None:
    api = SystemAPI()
    concepts = {lab: find_exact(api, lab) for lab in CONCEPT_LABELS}
    found = {k: v for k, v in concepts.items() if v}
    print("concepts found:", {k: v["system_id"] for k, v in found.items()})
    out = {"concepts": found, "neighbourhoods": {}}
    for lab, c in found.items():
        rels = api.paginate(f"/v1/concepts/{c['system_id']}/relationships", {"sort": "num_studies:desc"},
                            page_size=100, max_records=300 if lab == "malaria" else 100)
        rels = [r for r in rels if r["source_concept"]["system_id"] != r["target_concept"]["system_id"]]
        out["neighbourhoods"][lab] = [rel_summary(r, c["system_id"]) for r in rels]
        print(lab, "relationships:", len(rels))

    # 3-layer coverage of verified anchors
    ver = pd.read_csv(VERIFIED / "evidence_verified.csv", dtype=str, keep_default_na=False)
    pmids = sorted(set(ver["pmid"]))
    csv_counts = {p: 0 for p in pmids}
    for chunk in pd.read_csv(RAW_CSV, usecols=["pubmed_id"], dtype=str, chunksize=500_000):
        vc = chunk[chunk["pubmed_id"].isin(pmids)]["pubmed_id"].value_counts()
        for p, n in vc.items():
            csv_counts[p] += int(n)
    coverage = []
    for p in pmids:
        rows = api.get("/v1/studies", {"filter": f"pubmed_id:{p}", "limit": 5}).get("data", [])
        sid = (rows[0].get("system_id") or rows[0].get("study_id")) if rows else None
        n_assoc = None
        if sid:
            n_assoc = len(api.paginate(f"/v1/studies/{sid}/associations", page_size=100, max_records=500))
        coverage.append({"pmid": p, "short_ref": ver.loc[ver.pmid == p, "short_ref"].iloc[0],
                         "api_study": bool(sid), "system_study_id": sid,
                         "api_associations": n_assoc, "csv_associations": csv_counts[p]})
    out["anchor_coverage"] = coverage
    for c in coverage:
        print(c)
    write_json(GRAPH / "graph_context.json", out)


if __name__ == "__main__":
    main()
