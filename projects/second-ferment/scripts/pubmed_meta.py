"""Fetch title, journal, year and authors for PubMed IDs, with a cache.

Usage (from the repo root):
  python3 -I scripts/pubmed_meta.py data/derived/evidence/pmids.txt data/pubmed/summaries.json

Uses NCBI E-utilities esummary, 200 IDs per request, about 3 requests a second. Already-cached IDs are skipped.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ids_path, out_path = sys.argv[1:3]
os.makedirs(os.path.dirname(out_path), exist_ok=True)
cache = json.load(open(out_path)) if os.path.exists(out_path) else {}
ids = [x.strip() for x in open(ids_path) if x.strip().isdigit()]
todo = [i for i in ids if i not in cache]
print("PMIDs:", len(ids), "to fetch:", len(todo))
for k in range(0, len(todo), 200):
    batch = todo[k:k + 200]
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(batch), "retmode": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": "heatrx-hackathon/0.1"})
    for attempt in range(3):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=60))
            break
        except Exception as e:  # network hiccup: wait and retry
            print("retry", attempt, e)
            time.sleep(2 + attempt * 3)
    else:
        continue
    res = data.get("result", {})
    for i in batch:
        r = res.get(i)
        if not r or "error" in r:
            continue
        authors = [a.get("name", "") for a in r.get("authors", [])]
        cache[i] = {"title": r.get("title", ""), "journal": r.get("source", ""),
                    "year": (r.get("pubdate", "") or "")[:4],
                    "authors": (authors[0] + (" et al." if len(authors) > 1 else "")) if authors else ""}
    time.sleep(0.4)
json.dump(cache, open(out_path, "w"))
print("cached:", len(cache))
