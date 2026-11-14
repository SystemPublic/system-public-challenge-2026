"""PubMed abstracts for the restaurant analyses, cached in data/derived/levers/abstracts/<pmid>.txt."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "derived" / "restaurants" / "abstracts"
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def search(term: str, n: int = 10) -> list[str]:
    r = requests.get(EU + "esearch.fcgi", params={"db": "pubmed", "term": term, "retmode": "json", "retmax": n}, timeout=30)
    time.sleep(0.4)
    return r.json()["esearchresult"]["idlist"]


def abstract(pmid: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{pmid}.txt"
    if f.exists():
        return f.read_text()
    r = requests.get(EU + "efetch.fcgi", params={"db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "text"}, timeout=30)
    time.sleep(0.4)
    r.raise_for_status()
    f.write_text(r.text)
    return r.text


if __name__ == "__main__":
    if sys.argv[1] == "search":
        print(search(" ".join(sys.argv[2:])))
    else:
        for p in sys.argv[1:]:
            print(abstract(p)); print("=" * 30)
