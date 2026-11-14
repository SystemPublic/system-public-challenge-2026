"""Fetch PubMed abstracts (title + abstract text) for a list of PMIDs into data/cache/pubmed/ (not tracked).

Usage: python analyses/heat_drugs/abstracts.py PMID [PMID ...]   prints each abstract.
"""
from __future__ import annotations

import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data/cache/pubmed"
URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def fetch(pmids: list[str]) -> dict[str, str]:
    CACHE.mkdir(parents=True, exist_ok=True)
    need = [p for p in pmids if not (CACHE / f"{p}.txt").exists()]
    for i in range(0, len(need), 50):
        r = requests.get(URL, params={"db": "pubmed", "retmode": "xml", "id": ",".join(need[i:i + 50])}, timeout=60)
        r.raise_for_status()
        for art in ET.fromstring(r.content).iter("PubmedArticle"):
            pmid = art.findtext(".//PMID")
            title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
            parts = []
            for a in art.iter("AbstractText"):
                lab = a.get("Label")
                parts.append((lab + ": " if lab else "") + "".join(a.itertext()))
            au = art.find(".//AuthorList/Author/LastName")
            yr = art.findtext(".//PubDate/Year") or art.findtext(".//PubDate/MedlineDate") or ""
            jr = art.findtext(".//Journal/ISOAbbreviation") or ""
            (CACHE / f"{pmid}.txt").write_text(f"{au.text if au is not None else ''} {yr} {jr}\n{title}\n\n" + "\n".join(parts))
        time.sleep(0.4)
    return {p: (CACHE / f"{p}.txt").read_text() if (CACHE / f"{p}.txt").exists() else "" for p in pmids}


if __name__ == "__main__":
    for p, t in fetch(sys.argv[1:]).items():
        print("=" * 20, p, "\n", t, "\n")
