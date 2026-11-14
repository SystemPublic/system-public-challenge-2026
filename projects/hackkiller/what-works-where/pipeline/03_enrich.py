"""Enrich candidate papers with bibliographic metadata (PubMed) and study context (System API).

- PubMed esummary: title, journal, publication date, DOI (batched, 150 PMIDs per call)
- System /v1/studies?filter=pubmed_id:<pmid>: system study_id, population text, study_type
Country is parsed from the population text first, then the title (author affiliations are never used).
Failures are recorded, not dropped.
"""
from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

from common import INTERIM, ISO3, STUDIES_CSV, log_request, write_json

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

COUNTRIES = [
    "Benin", "Burkina Faso", "Burundi", "Cameroon", "Central African Republic", "Chad", "Congo",
    "Democratic Republic of the Congo", "DRC", "Côte d'Ivoire", "Cote d'Ivoire", "Ivory Coast", "Equatorial Guinea",
    "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea-Bissau", "Guinea", "Kenya", "Liberia", "Madagascar", "Malawi",
    "Mali", "Mauritania", "Mozambique", "Niger", "Nigeria", "Rwanda", "Senegal", "Sierra Leone", "Somalia",
    "South Sudan", "Sudan", "Tanzania", "Togo", "Uganda", "Zambia", "Zimbabwe", "Angola", "Eritrea", "Namibia",
    "India", "Myanmar", "Cambodia", "Laos", "Vietnam", "Thailand", "Indonesia", "Papua New Guinea", "Solomon Islands",
    "Vanuatu", "Bangladesh", "Pakistan", "Afghanistan", "Sri Lanka", "Brazil", "Peru", "Colombia", "Venezuela",
    "Haiti", "Yemen", "Sahel", "sub-Saharan Africa",
]
ALIASES = {"DRC": "Democratic Republic of the Congo", "Cote d'Ivoire": "Côte d'Ivoire",
           "Ivory Coast": "Côte d'Ivoire"}
REGION_NOTES = {"Sahel", "sub-Saharan Africa"}

CRX = re.compile(r"\b(" + "|".join(re.escape(c) for c in sorted(COUNTRIES, key=len, reverse=True)) + r")\b", re.I)


def countries_in(text: str) -> list[str]:
    found = []
    for m in CRX.finditer(text or ""):
        name = next(c for c in COUNTRIES if c.lower() == m.group(1).lower())
        name = ALIASES.get(name, name)
        if name == "Guinea" and re.search(r"(equatorial|papua new|guinea-bissau)", text, re.I):
            continue
        if name == "Niger" and re.search(r"nigeria", m.string[m.start():m.end() + 2], re.I):
            continue
        if name not in found:
            found.append(name)
    return found


def pubmed_meta(pmids: list[str]) -> dict:
    out = {}
    for i in range(0, len(pmids), 150):
        batch = pmids[i:i + 150]
        params = {"db": "pubmed", "id": ",".join(batch), "retmode": "json"}
        r = requests.get(EUTILS, params=params, timeout=60)
        log_request("pubmed", EUTILS, {"db": "pubmed", "n_ids": len(batch)}, r.status_code, None)
        r.raise_for_status()
        res = r.json().get("result", {})
        for pmid in batch:
            d = res.get(pmid)
            if not d or "error" in d:
                out[pmid] = {"pubmed_status": "not returned"}
                continue
            doi = next((a["value"] for a in d.get("articleids", []) if a.get("idtype") == "doi"), None)
            out[pmid] = {
                "pubmed_status": "ok", "title": d.get("title"), "journal": d.get("fulljournalname") or d.get("source"),
                "pubdate": d.get("pubdate"), "year": (d.get("pubdate") or "")[:4], "doi": doi,
                "pubtype": d.get("pubtype", []),
            }
        time.sleep(0.4)
    return out


def offline_studies(study_ids: set[str]) -> dict:
    """Study records from the restored System studies table (no API calls)."""
    out = {}
    for chunk in pd.read_csv(STUDIES_CSV, dtype=str, keep_default_na=False, chunksize=200_000):
        sub = chunk[chunk.study_id.isin(study_ids)]
        for r in sub.itertuples(index=False):
            out[r.study_id] = {"system_study_id": r.study_id, "population": r.population_string or None,
                               "study_type": r.study_type or None, "system_doi": r.doi or None,
                               "study_pmid": r.pubmed_id or None}
    return out


def main() -> None:
    cand = pd.read_csv(INTERIM / "candidates.csv", dtype=str, keep_default_na=False)
    pmids = sorted(set(cand["pubmed_id"]) - {""})
    meta = pubmed_meta(pmids)
    pmid_study = cand.drop_duplicates("pubmed_id").set_index("pubmed_id")["study_id"].to_dict()
    studies = offline_studies(set(pmid_study.values()))
    papers = []
    for p in pmids:
        st = studies.get(pmid_study.get(p))
        flags = []
        if st is None:
            st = {"system_status": "study_lookup_missing"}
            flags.append("study_lookup_missing")
        else:
            st = {**st, "system_status": "ok"}
            if st.get("study_pmid") and st["study_pmid"] != p:
                flags.append("study_pmid_mismatch")
        rec = {"pubmed_id": p, **meta.get(p, {}), **st, "study_flags": flags}
        pop_c = countries_in(rec.get("population") or "")
        title_c = countries_in(rec.get("title") or "")
        rec["countries"] = pop_c or title_c
        rec["country_source"] = "population" if pop_c else ("title" if title_c else "unknown")
        rec["iso3"] = ";".join(ISO3[c] for c in rec["countries"] if c in ISO3)
        rec["region_notes"] = ";".join(c for c in rec["countries"] if c in REGION_NOTES)
        papers.append(rec)
    write_json(INTERIM / "papers.json", papers)
    df = pd.DataFrame(papers)
    print("papers:", len(df), "| pubmed ok:", (df.pubmed_status == "ok").sum(),
          "| offline study ok:", (df.system_status == "ok").sum(),
          "| study flags:", df.study_flags.explode().value_counts().to_dict(),
          "| country known:", (df.country_source != "unknown").sum())
    print(df.country_source.value_counts().to_dict())


if __name__ == "__main__":
    main()
