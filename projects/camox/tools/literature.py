"""Literature search: OpenAlex (works with citations and abstracts) and PubMed (NCBI E-utilities)."""
import datetime
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


def lookup_dois(dois: list[str]) -> list:
    """Title, year, venue and citation count for up to 50 DOIs (OpenAlex). Use it to name the papers behind
    findings before citing them. DOIs OpenAlex doesn't know are left out."""
    clean = sorted({d.lower().removeprefix("https://doi.org/") for d in dois if d})[:50]
    if not clean:
        return []
    params = {"filter": "doi:" + "|".join(clean), "per_page": 50,
              "select": "doi,display_name,publication_year,primary_location,cited_by_count"}
    if os.environ.get("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    return [{"doi": (w["doi"] or "").removeprefix("https://doi.org/"), "title": w["display_name"],
             "year": w["publication_year"], "cited_by_count": w["cited_by_count"],
             "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name")}
            for w in get_json("https://api.openalex.org/works", params)["results"]]


def count_openalex(query: str, year_from: int | None = None) -> dict:
    """How many OpenAlex works match a query (all fields), in total and per publication year since year_from
    (default: the last 15 years). Compare it with the graph's study count to see how much of the literature the
    graph holds."""
    year_from = year_from or datetime.date.today().year - 15
    params = {"search": query, "filter": f"from_publication_date:{year_from}-01-01", "group_by": "publication_year"}
    if os.environ.get("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    total = get_json("https://api.openalex.org/works", {"search": query, "per_page": 1, "select": "id",
                                                        **({"api_key": params["api_key"]} if "api_key" in params else {})})
    years = get_json("https://api.openalex.org/works", params)["group_by"]
    return {"query": query, "total_works": total["meta"]["count"],
            "by_year": sorted((int(g["key"]), g["count"]) for g in years if str(g["key"]).isdigit())}
