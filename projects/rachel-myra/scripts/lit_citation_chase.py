"""Citation chasing from key reviews (spec §8.4 step 2).

Seeds (spec §8.4): Hospers 2024, Tews 2026, Kalisch Ellett 2016, Layton 2020 and
the 2025 schizophrenia/thermoregulation review (Sci Total Environ, PII
S0048969725016055, per docs/schizophrenia-sbh-focus.md).

Each seed is first resolved by an OpenAlex title search; the hit is accepted
only if its DOI equals the DOI the repo cites (report / docs) or, for the
Sci Total Environ review, the Crossref record for that PII.  Unresolved seeds
are skipped and logged.

For each resolved seed: backward (references) and forward (cited-by) citations
from OpenAlex, plus the same from Europe PMC (/references, /citations) when the
seed has a PMID.  OpenAlex without an API key has a shared $0.10/day budget, so
calls are kept to a minimum and the remaining budget is logged.

Outputs:
  data/raw/literature/citation_chase/seeds_resolved.json
  data/raw/literature/citation_chase/openalex_*.json, epmc_*.json (raw)
  data/processed/citation_chase.csv  (one row per seed x linked work x direction)

Usage: uv run --with requests python -I scripts/lit_citation_chase.py
"""
import csv, json, os, re, sys, time
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "literature", "citation_chase")
OUT = os.path.join(ROOT, "data", "processed", "citation_chase.csv")
OA = "https://api.openalex.org/"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
SELECT = "id,doi,title,publication_year,ids,primary_location,type,cited_by_count,authorships"

SEEDS = [
    {"seed": "Hospers 2024", "title_query": "effect of prescription and over-the-counter medications on core temperature heat stress meta-analysis", "expected_doi": "10.1016/j.eclinm.2024.102886"},
    {"seed": "Tews 2026", "title_query": "Recognizing and Mitigating the Effects of Medication on Heat", "expected_doi": "10.3390/pharmacy14030074"},
    {"seed": "Kalisch Ellett 2016", "title_query": "Kalisch Ellett medicines hospitalisation dehydration heat-related illness veterans", "expected_doi": "10.1111/jcpt.12418"},
    {"seed": "Layton 2020", "title_query": "Heatwaves, medications, and heat-related hospitalization in older Medicare beneficiaries with chronic conditions", "expected_doi": "10.1371/journal.pone.0243665"},
    {"seed": "Schizophrenia heat review 2025 (Sci Total Environ)", "title_query": "schizophrenia thermoregulation heat review", "expected_doi": None, "pii": "S0048969725016055"},
]

S = requests.Session()
S.headers["User-Agent"] = "missing-label-hackathon/0.1 (research script)"
budget = {"remaining_usd": None, "calls": 0}


def get(url, params=None, gap=1.0, tries=5):
    for i in range(tries):
        time.sleep(gap)
        try:
            r = S.get(url, params=params, timeout=60)
        except requests.RequestException as e:
            print("retry", e, file=sys.stderr)
            time.sleep(2 ** i + 2)
            continue
        if "openalex" in url:
            budget["calls"] += 1
            budget["remaining_usd"] = r.headers.get("x-ratelimit-remaining-usd", budget["remaining_usd"])
        if r.status_code == 200:
            return r
        if r.status_code in (429, 500, 502, 503, 504):
            if r.status_code == 429 and "openalex" in url:
                print("OpenAlex budget/rate limit hit", file=sys.stderr)
                return None
            time.sleep(2 ** i + 2)
            continue
        print("HTTP", r.status_code, url, file=sys.stderr)
        return None
    return None


def save(name, obj):
    json.dump(obj, open(os.path.join(RAW, name), "w"), indent=1)


def norm_doi(d):
    return (d or "").lower().replace("https://doi.org/", "")


def oa_row(w):
    loc = (w.get("primary_location") or {}).get("source") or {}
    ids = w.get("ids") or {}
    return {"openalex_id": (w.get("id") or "").replace("https://openalex.org/", ""), "doi": norm_doi(w.get("doi")),
            "pmid": (ids.get("pmid") or "").replace("https://pubmed.ncbi.nlm.nih.gov/", "").strip("/"),
            "pmcid": (ids.get("pmcid") or "").replace("https://www.ncbi.nlm.nih.gov/pmc/articles/", "").strip("/"),
            "title": w.get("title") or "", "year": w.get("publication_year") or "", "journal": loc.get("display_name", ""),
            "first_author": ((w.get("authorships") or [{}])[0].get("author") or {}).get("display_name", "") if w.get("authorships") else "",
            "type": w.get("type", ""), "cited_by_count": w.get("cited_by_count", "")}


def resolve_seed(sd):
    expected = sd.get("expected_doi")
    if sd.get("pii"):
        r = get("https://api.crossref.org/works", {"filter": f"alternative-id:{sd['pii']}", "rows": 2}, gap=0.5)
        items = r.json()["message"]["items"] if r else []
        save("crossref_pii_" + sd["pii"] + ".json", items)
        if len(items) == 1:
            expected = norm_doi(items[0]["DOI"])
            sd["crossref_title"] = " ".join(items[0].get("title", []))
            sd["title_query"] = sd["crossref_title"] or sd["title_query"]
    sd["expected_doi_used"] = expected
    r = get(OA + "works", {"search": sd["title_query"], "per-page": 5, "select": SELECT})
    hits = r.json().get("results", []) if r else []
    save("openalex_search_" + re.sub(r"\W+", "_", sd["seed"]) + ".json", hits)
    for w in hits:
        if expected and norm_doi(w.get("doi")) == expected:
            sd["resolved"] = oa_row(w)
            sd["resolved_by"] = "openalex title search; DOI matches cited DOI"
            return sd
    if expected:  # title search missed; try direct DOI lookup to confirm
        r = get(OA + "works/doi:" + expected, {"select": SELECT})
        if r:
            sd["resolved"] = oa_row(r.json())
            sd["resolved_by"] = "openalex DOI lookup (title search top-5 did not contain it)"
            return sd
    sd["resolved"] = None
    sd["resolved_by"] = "UNRESOLVED: skipped"
    return sd


def oa_references(wid):
    r = get(OA + "works/" + wid, {"select": "id,referenced_works"})
    refs = [x.replace("https://openalex.org/", "") for x in (r.json().get("referenced_works") or [])] if r else []
    out = []
    for i in range(0, len(refs), 50):
        rr = get(OA + "works", {"filter": "openalex_id:" + "|".join(refs[i:i + 50]), "per-page": 50, "select": SELECT})
        if rr:
            out.extend(rr.json().get("results", []))
    return refs, out


def oa_citedby(wid, cap=600):
    out, cursor = [], "*"
    while cursor and len(out) < cap:
        r = get(OA + "works", {"filter": "cites:" + wid, "per-page": 200, "cursor": cursor, "select": SELECT})
        if not r:
            break
        d = r.json()
        out.extend(d.get("results", []))
        cursor = d.get("meta", {}).get("next_cursor")
        if not d.get("results"):
            break
    return out


def epmc_links(pmid, kind):
    out, page = [], 1
    while True:
        r = get(f"{EPMC}MED/{pmid}/{kind}", {"format": "json", "pageSize": 1000, "page": page}, gap=0.5)
        if not r:
            break
        d = r.json()
        key = "referenceList" if kind == "references" else "citationList"
        sub = "reference" if kind == "references" else "citation"
        items = (d.get(key) or {}).get(sub, []) or []
        out.extend(items)
        if len(items) < 1000:
            break
        page += 1
    return out


def main():
    os.makedirs(RAW, exist_ok=True)
    rows = []
    seeds = [resolve_seed(dict(s)) for s in SEEDS]
    for sd in seeds:
        print(sd["seed"], "->", sd["resolved_by"], (sd["resolved"] or {}).get("openalex_id"), file=sys.stderr)
        if not sd["resolved"]:
            continue
        wid = sd["resolved"]["openalex_id"]
        tag = re.sub(r"\W+", "_", sd["seed"])
        refs_ids, refs = oa_references(wid)
        save(f"openalex_refs_{tag}.json", refs)
        cites = oa_citedby(wid)
        save(f"openalex_citedby_{tag}.json", cites)
        sd["openalex_n_references_listed"] = len(refs_ids)
        sd["openalex_n_references_fetched"] = len(refs)
        sd["openalex_n_cited_by"] = len(cites)
        for direction, ws in (("reference", refs), ("cited_by", cites)):
            for w in ws:
                rows.append({"seed": sd["seed"], "seed_openalex_id": wid, "seed_doi": sd["resolved"]["doi"],
                             "direction": direction, "source": "openalex", **oa_row(w)})
        pmid = sd["resolved"].get("pmid")
        if pmid:
            for kind, direction in (("references", "reference"), ("citations", "cited_by")):
                items = epmc_links(pmid, kind)
                save(f"epmc_{kind}_{tag}.json", items)
                sd[f"epmc_n_{kind}"] = len(items)
                for it in items:
                    rows.append({"seed": sd["seed"], "seed_openalex_id": wid, "seed_doi": sd["resolved"]["doi"],
                                 "direction": direction, "source": "europepmc", "openalex_id": "",
                                 "doi": norm_doi(it.get("doi")), "pmid": it.get("pmid", "") or (it.get("id", "") if it.get("source") == "MED" else ""),
                                 "pmcid": it.get("pmcid", ""), "title": it.get("title", ""),
                                 "year": it.get("pubYear", ""), "journal": it.get("journalAbbreviation", "") or it.get("journalTitle", ""),
                                 "first_author": (it.get("authorString", "") or "").split(",")[0], "type": "", "cited_by_count": it.get("citedByCount", "")})
        else:
            sd["epmc_note"] = "no PMID for seed; Europe PMC links not fetched"
    save("seeds_resolved.json", {"access_date": "2026-11-14", "openalex_calls": budget["calls"],
                                 "openalex_remaining_usd_after": budget["remaining_usd"], "seeds": seeds})
    cols = ["seed", "seed_openalex_id", "seed_doi", "direction", "source", "openalex_id", "doi", "pmid", "pmcid", "title",
            "year", "journal", "first_author", "type", "cited_by_count"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print("rows", len(rows), "openalex calls", budget["calls"], "remaining usd", budget["remaining_usd"], file=sys.stderr)


if __name__ == "__main__":
    main()
