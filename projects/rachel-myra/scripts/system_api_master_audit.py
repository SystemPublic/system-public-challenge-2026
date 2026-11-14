"""Task 1 (spec 8.5a role 5, auditor): look up every paper we cite in the System API.

Inputs (IDs pulled from all three, then normalised to PMID + PMCID + DOI with
data/processed/literature_id_map.csv and the pmid/pmcid/doi columns already resolved
in citation_verification.csv):
  data/master_list_graph_status.csv          (pmid column)
  data/Drug heat risk master list.csv        (Key citations free text: PMID / DOI / PMC ids)
  data/processed/citation_verification.csv   (master_list + report citations)

API calls (all cached in data/raw/system/api/cache/, see system_api_client.py):
  GET /v1/studies?filter=pubmed_id:A||B||...   batched PMID lookup (falls back to one at a time)
  GET /v1/studies?filter=doi:<doi>             for papers with no PMID or not found by PMID
  GET /v1/studies/{study_id}/associations      every finding System extracted from the paper

Outputs:
  data/processed/system_api_master_list_papers.csv     one row per cited paper: indexed?, study ids, n findings
  data/processed/system_api_master_list_findings.csv   one row per (paper, System finding); papers with
                                                        no findings get one row with blank finding columns

Run:  uv run --with requests python scripts/system_api_master_audit.py
"""
import csv, re, sys, os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from system_api_client import Client  # noqa: E402
from system_api_common import (P, PROC, IdMap, norm_doi, norm_pmcid, norm_pmid, paper_key,  # noqa: E402
                               write_csv)


def collect_citations(idmap):
    """Return {paper_key: {pmid, pmcid, doi, cited_in:set}}."""
    papers = {}

    def add(pmid, pmcid, doi, where):
        pmid, pmcid, doi = idmap.resolve(pmid, pmcid, doi)
        if not (pmid or pmcid or doi):
            return
        k = paper_key(pmid, pmcid, doi)
        rec = papers.setdefault(k, {"pmid": pmid, "pmcid": pmcid, "doi": doi, "cited_in": set()})
        for f, v in (("pmid", pmid), ("pmcid", pmcid), ("doi", doi)):
            if v and not rec[f]:
                rec[f] = v
        rec["cited_in"].add(where)

    for r in csv.DictReader(open(P("data", "master_list_graph_status.csv"), encoding="utf-8")):
        add(r["pmid"], "", "", f"graph_status:{r['row_id']}")
    for r in csv.DictReader(open(P("data", "Drug heat risk master list.csv"), encoding="utf-8-sig")):
        txt = r.get("Key citations") or ""
        for m in re.finditer(r"PMID:?\s*(\d{5,9})", txt):
            add(m.group(1), "", "", f"master_list:{r['ID']}")
        for m in re.finditer(r"\b(PMC\d{5,9})\b", txt):
            add("", m.group(1), "", f"master_list:{r['ID']}")
        for m in re.finditer(r"(10\.\d{4,9}/[^\s;,()]+[^\s;,().])", txt):
            add("", "", m.group(1), f"master_list:{r['ID']}")
    for r in csv.DictReader(open(P("data", "processed", "citation_verification.csv"), encoding="utf-8")):
        add(r["pmid"], r["pmcid"], r["doi"], f"{r['source']}:{r['location']}")
    # merge records that resolved to the same paper under different keys (e.g. DOI-only vs PMID)
    by_doi = {v["doi"]: k for k, v in papers.items() if v["doi"] and v["pmid"]}
    for k in [k for k, v in papers.items() if not v["pmid"] and v["doi"] in by_doi]:
        papers[by_doi[papers[k]["doi"]]]["cited_in"] |= papers.pop(k)["cited_in"]
    return papers


def lookup_studies(c, papers):
    """Return {paper_key: [study dicts]}; adds 'lookup' (how it was found) to each paper."""
    found = defaultdict(list)
    pm = {v["pmid"]: k for k, v in papers.items() if v["pmid"]}
    pmids = sorted(pm)
    batch_ok = True
    for i in range(0, len(pmids), 20):
        chunk = pmids[i:i + 20]
        res = None
        if batch_ok:
            try:
                res = c.paged("/studies", page=100, cap=500, filter="pubmed_id:" + "||".join(chunk))
            except RuntimeError as e:
                print("batch pubmed_id filter failed, falling back to singles:", str(e)[:120])
                batch_ok = False
        if res is None:
            res = []
            for p in chunk:
                res += (c.get("/studies", filter=f"pubmed_id:{p}", limit=10) or {}).get("data", [])
        for s in res:
            k = pm.get(norm_pmid(s.get("pubmed_id")))
            if k:
                found[k].append(s)
    # sanity check the batch filter: a batch result must not silently drop papers that a single lookup finds
    if batch_ok and pmids:
        probe = [p for p in pmids if not found.get(pm[p])][:3]
        for p in probe:
            single = (c.get("/studies", filter=f"pubmed_id:{p}", limit=10) or {}).get("data", [])
            if single:
                print(f"WARNING: batch filter missed PMID {p}; re-running singles")
                for q in pmids:
                    if not found.get(pm[q]):
                        for s in (c.get("/studies", filter=f"pubmed_id:{q}", limit=10) or {}).get("data", []):
                            found[pm[q]].append(s)
                break
    for k, v in papers.items():
        v["lookup"] = "pubmed_id" if found.get(k) else ""
        if not found.get(k) and v["doi"]:
            for d in dict.fromkeys([v["doi"], v["doi"].upper()]):
                res = (c.get("/studies", filter=f"doi:{d}", limit=10) or {}).get("data", [])
                if res:
                    found[k] += res
                    v["lookup"] = "doi"
                    break
    return found


FIND_FIELDS = ["system_id", "variable_1_name", "variable_2_name", "statistic_type", "system_statistic_type",
               "statistic_value", "ci_lower", "ci_upper", "ci_level", "p_value", "p_value_equality",
               "variable_1_id", "variable_2_id", "variable_1_concept_id", "variable_2_concept_id",
               "variable_1_wikidata_id", "variable_2_wikidata_id"]


def main():
    c = Client()
    idmap = IdMap()
    papers = collect_citations(idmap)
    print(f"{len(papers)} distinct cited papers")
    studies = lookup_studies(c, papers)
    paper_rows, find_rows = [], []
    for k, v in sorted(papers.items()):
        sts = studies.get(k, [])
        assocs = []
        for s in sts:
            for a in c.paged(f"/studies/{s['study_id']}/associations", page=100, cap=2000):
                assocs.append((s, a))
        base = {"paper_key": k, "pmid": v["pmid"], "pmcid": v["pmcid"], "doi": v["doi"],
                "cited_in": " | ".join(sorted(v["cited_in"])), "indexed": bool(sts),
                "found_by": v.get("lookup", ""), "study_ids": " | ".join(s["study_id"] for s in sts),
                "study_type": " | ".join(str(s.get("study_type") or "") for s in sts),
                "population": " | ".join(str(s.get("population") or "") for s in sts)[:500],
                "n_findings": len(assocs)}
        paper_rows.append(base)
        if not assocs:
            find_rows.append({**base, "study_id": ""})
        for s, a in assocs:
            find_rows.append({**base, "study_id": s["study_id"], **{f: a.get(f, "") for f in FIND_FIELDS}})
        print(f"{k:40s} indexed={bool(sts)!s:5s} findings={len(assocs):3d}  ({c.stats()})")
    write_csv(os.path.join(PROC, "system_api_master_list_papers.csv"), paper_rows)
    write_csv(os.path.join(PROC, "system_api_master_list_findings.csv"), find_rows,
              list(paper_rows[0].keys()) + ["study_id"] + FIND_FIELDS)
    n_idx = sum(r["indexed"] for r in paper_rows)
    n_f = sum(r["n_findings"] > 0 for r in paper_rows)
    print(f"cited={len(paper_rows)} indexed={n_idx} with_findings={n_f} findings={sum(r['n_findings'] for r in paper_rows)}")
    print(c.stats())


if __name__ == "__main__":
    main()
