"""Build data/forecast/papers.json (PapersDataset) from the Alert tab's data pack.

Usage (from the repo root):
  python3 -I scripts/forecast/build_papers.py k540e-data-pack/k540e-literature.json data/forecast/papers.json [pack commit]

Every paper is kept, including those with no country. A field that is missing or oddly typed
is written as null (or the paper is reported and skipped if a required field is unusable);
nothing is guessed.
"""
import json
import re
import sys

src, out_path = sys.argv[1], sys.argv[2]
commit = sys.argv[3] if len(sys.argv) > 3 else "a1cc503"
MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}
ISO = re.compile(r"^[A-Z]{3}$")

d = json.load(open(src, encoding="utf-8"))
meta = d["_meta"]
problems = []
papers = []
for p in d["papers"]:
    pmid = p.get("pmid")
    if isinstance(pmid, int):
        pmid = str(pmid)
    year = p.get("pub_year")
    title = p.get("title")
    url = p.get("url")
    if not (isinstance(pmid, str) and pmid.isdigit() and isinstance(year, int) and isinstance(title, str)
            and isinstance(url, str)):
        problems.append(f"skipped (required field unusable): {p.get('pmid')!r}")
        continue
    m = p.get("pub_month")
    month = MONTHS.get(m) if isinstance(m, str) else (m if isinstance(m, int) and 1 <= m <= 12 else None)
    if m is not None and month is None:
        problems.append(f"{pmid}: pub_month {m!r} not understood, kept null")
    cs = p.get("countries_iso3")
    if not isinstance(cs, list):
        problems.append(f"{pmid}: countries_iso3 not a list, kept empty")
        cs = []
    bad = [c for c in cs if not (isinstance(c, str) and ISO.match(c))]
    if bad:
        problems.append(f"{pmid}: dropped non-ISO3 country values {bad!r}")
    ig = p.get("in_graph")
    if not isinstance(ig, bool):
        problems.append(f"{pmid}: in_graph {ig!r} not boolean, kept false")
    papers.append({
        "pmid": pmid,
        "doi": p["doi"] if isinstance(p.get("doi"), str) and p["doi"] else None,
        "title": title,
        "journal": p["journal"] if isinstance(p.get("journal"), str) and p["journal"] else None,
        "year": year,
        "month": month,
        "countries": [c for c in cs if isinstance(c, str) and ISO.match(c)],
        "readByGraph": ig is True,
        "url": url,
    })

papers.sort(key=lambda x: (x["year"], x["month"] or 0, x["pmid"]))
searched = re.search(r"searched (\d{4}-\d{2}-\d{2})", meta.get("source", ""))
notes = [
    f"This list comes from the Alert tab's data pack at commit {commit}: PubMed papers whose title or abstract matches the query below.",
    "Countries were machine-read from each abstract and have not been checked by a human.",
    "\"Read by the Graph\" means the System Public Graph holds findings from that paper (its PubMed ID is in the Graph's CSV snapshot).",
    "Abstracts only: full texts were not read.",
    "Definitions differ between papers, so papers are not one survey series.",
    f"Search query (verbatim): {meta.get('query')}",
    f"Method (verbatim): {meta.get('method')}",
]
out = {
    "source": {
        "id": "pubmed-k540e-pack",
        "label": "PubMed papers that mention K540E",
        "licence": meta.get("licence"),
        "citation": meta.get("source"),
        "url": "https://pubmed.ncbi.nlm.nih.gov/",
        "retrievedAt": searched.group(1) if searched else "",
        "notes": notes,
    },
    "total": len(papers),
    "readByGraph": sum(p["readByGraph"] for p in papers),
    "papers": papers,
}
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print("papers", len(papers), "readByGraph", out["readByGraph"],
      "with country", sum(1 for p in papers if p["countries"]), "problems", len(problems))
for x in problems:
    print("  ", x)
