"""Literature search: OpenAlex (works with citations and abstracts) and PubMed (NCBI E-utilities)."""
import os

from tools._http import get_json

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def search_openalex(query: str, k: int = 10, year_from: int | None = None) -> list:
    """Search scholarly works in OpenAlex (all fields), most relevant first. Each hit has title, year, venue, DOI,
    URL, citation count and the start of the abstract. Use year_from to keep recent work only."""
    params = {"search": query, "per_page": min(k, 25),
              "select": "id,doi,display_name,publication_year,primary_location,cited_by_count,abstract_inverted_index"}
    if year_from:
        params["filter"] = f"from_publication_date:{year_from}-01-01"
    if os.environ.get("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    out = []
    for w in get_json("https://api.openalex.org/works", params)["results"]:
        words = sorted((i, word) for word, ids in (w.get("abstract_inverted_index") or {}).items() for i in ids)
        out.append({"title": w["display_name"], "year": w["publication_year"],
                    "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                    "doi": w["doi"], "url": w["doi"] or w["id"], "cited_by_count": w["cited_by_count"],
                    "abstract": " ".join(word for _, word in words)[:300] or None})
    return out


def search_pubmed(query: str, k: int = 10) -> list:
    """Search PubMed (biomedical literature; PubMed query syntax works, e.g. "malaria[tiab] AND Uganda").
    Each hit has pmid, title, year, journal and DOI."""
    ids = get_json(f"{EUTILS}/esearch.fcgi", {"db": "pubmed", "term": query, "retmode": "json",
                                              "retmax": min(k, 25), "tool": "camox"})["esearchresult"]["idlist"]
    if not ids:
        return []
    res = get_json(f"{EUTILS}/esummary.fcgi", {"db": "pubmed", "id": ",".join(ids), "retmode": "json", "tool": "camox"})["result"]
    return [{"pmid": i, "title": res[i]["title"], "year": res[i]["pubdate"][:4], "journal": res[i]["fulljournalname"],
             "doi": next((a["value"] for a in res[i]["articleids"] if a["idtype"] == "doi"), None)}
            for i in ids if i in res]
