"""Fallback for tasks 1-2 when the System API key is rejected (HTTP 403 on 14 Nov 2026 overnight run).

Runs the SAME verification code (scripts/system_api_verify.py) but with System findings taken from the
public Dataverse bulk release (v2.1, ~2.0M findings) instead of the API (~5.9M). No API calls.
Everything is labelled `_dataverse_fallback`; it is NOT the API result and must not be quoted as such.

Steps
 1. Collect every cited paper (same collection as system_api_master_audit.py: master_list_graph_status.csv,
    the master list's Key citations, citation_verification.csv; IDs normalised with literature_id_map.csv).
 2. Scan data/raw/system/dataverse/studies.csv for those PMIDs / DOIs -> "indexed in Dataverse".
 3. Pull their findings from data/raw/system/dataverse/associations.csv (by study_id).
 4. Corroboration index from the existing Dataverse outputs data/processed/system_drug_mediator_findings.csv
    and system_drug_heat_direct_findings.csv (unflagged rows only), converted to the evidence schema.
 5. Run system_api_verify.main(...) with suffix `_dataverse_fallback`.
Outputs
  data/raw/system/api/fallback/master_list_findings_dataverse.csv
  data/raw/system/api/fallback/evidence_findings_dataverse.csv
  data/processed/system_api_master_list_findings_dataverse_fallback.csv (copy of 1-3 for the app)
  data/processed/system_api_verification_dataverse_fallback.csv, ..._numbers_..., ..._reverse_check_...,
  data/processed/system_api_verification_summary_dataverse_fallback.json
Run:  uv run python scripts/system_api_dataverse_fallback.py
"""
import csv, os, shutil, sys

sys.path.insert(0, os.path.dirname(__file__))
from system_api_common import (P, PROC, API_DIR, DV_STUDIES, IdMap, norm_doi, norm_pmid, dataverse_lookup,  # noqa: E402
                               direction, write_csv)
from system_api_master_audit import collect_citations, FIND_FIELDS  # noqa: E402
import system_api_verify  # noqa: E402

FB = os.path.join(API_DIR, "fallback")


def main():
    os.makedirs(FB, exist_ok=True)
    papers = collect_citations(IdMap())
    pm = {v["pmid"]: k for k, v in papers.items() if v["pmid"]}
    dois = {v["doi"]: k for k, v in papers.items() if v["doi"]}
    studies = {}
    with open(DV_STUDIES, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            k = pm.get(norm_pmid(r["pubmed_id"])) or dois.get(norm_doi(r["doi"]))
            if k:
                studies.setdefault(k, []).append(r)
    sids = {s["study_id"] for v in studies.values() for s in v}
    assoc = dataverse_lookup((), sids, cache=os.path.join(FB, "dataverse_assoc_cited_studies.csv"))
    by_study = {}
    for a in assoc:
        by_study.setdefault(a["study_id"], []).append(a)
    rows = []
    for k, v in sorted(papers.items()):
        sts = studies.get(k, [])
        fs = [(s, a) for s in sts for a in by_study.get(s["study_id"], [])]
        base = {"paper_key": k, "pmid": v["pmid"], "pmcid": v["pmcid"], "doi": v["doi"],
                "cited_in": " | ".join(sorted(v["cited_in"])), "indexed": bool(sts), "found_by": "dataverse_studies",
                "study_ids": " | ".join(s["study_id"] for s in sts),
                "study_type": " | ".join(s.get("study_type") or "" for s in sts),
                "population": " | ".join(s.get("population_string") or "" for s in sts)[:500], "n_findings": len(fs)}
        if not fs:
            rows.append({**base, "study_id": ""})
        for s, a in fs:
            rows.append({**base, "study_id": s["study_id"], **{f: a.get(f, "") for f in FIND_FIELDS}})
    mf = write_csv(os.path.join(FB, "master_list_findings_dataverse.csv"), rows,
                   list(rows[0].keys())[:11] + ["study_id"] + FIND_FIELDS)
    shutil.copy(mf, os.path.join(PROC, "system_api_master_list_findings_dataverse_fallback.csv"))
    print(f"cited={len(papers)} in_dataverse_studies={len(studies)} with_findings={sum(1 for k in studies if any(by_study.get(s['study_id']) for s in studies[k]))} findings={len(assoc)}")

    ev = []
    for fn, leg, gcol in (("system_drug_mediator_findings.csv", "drug_mediator", "mediator_group"),
                          ("system_drug_heat_direct_findings.csv", "drug_heat", "heat_group")):
        for r in csv.DictReader(open(os.path.join(PROC, fn), encoding="utf-8")):
            if r.get("auto_flags_heuristic"):
                continue
            ev.append({"system_id": r["association_id"], "study_id": r["study_id"], "leg": leg,
                       "group_a": r["drug_group"], "group_b": r[gcol],
                       "direction_if_ratio": direction(r["statistic_value"], r["statistic_type"], r["system_statistic_type"])})
    ef = write_csv(os.path.join(FB, "evidence_findings_dataverse.csv"), ev)
    # concept edges from the Dataverse relationships subset, converted to the API relationships schema
    rel = []
    for r in csv.DictReader(open(os.path.join(PROC, "system_relationships_subset.csv"), encoding="utf-8")):
        rel.append({"relationship_id": r["relationship_id"], "num_studies": r["num_studies"],
                    "source_groups": " | ".join(f"{r['source_kind']}:{x.strip()}" for x in r["source_groups"].replace(";", "|").split("|") if x.strip()),
                    "target_groups": " | ".join(f"{r['target_kind']}:{x.strip()}" for x in r["target_groups"].replace(";", "|").split("|") if x.strip())})
    rf = write_csv(os.path.join(FB, "relationships_dataverse.csv"), rel)
    system_api_verify.main(master_findings=mf, evidence_findings=ef, relationships=rf,
                           suffix="_dataverse_fallback", findings_source="dataverse_v2.1_fallback (API key rejected)")


if __name__ == "__main__":
    main()
