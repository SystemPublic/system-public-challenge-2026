"""Normalise PMID / PMCID / DOI for every literature record (build-plan Step 2, spec §8.2a).

Collects IDs from
  data/raw/literature/abstracts.jsonl          (search hits)
  data/processed/citation_verification.csv     (master list + report citations)
  data/processed/citation_chase.csv            (OpenAlex / Europe PMC citation chase)
and cross-maps them with NCBI E-utilities: esummary (PubMed articleids: pmid, pmc,
doi) for every PMID, and esearch "<doi>"[doi] for DOIs that have no PMID.  The
PMC ID Converter API (pmc.ncbi.nlm.nih.gov/tools/idconv) returned HTTP 403 to
this script on 2026-11-14, so it is not used.  IDs already present in the
PubMed / Europe PMC / OpenAlex metadata are kept; papers whose IDs disagree are
flagged in `conflict`.

Output: data/processed/literature_id_map.csv
  key, pmid, pmcid, doi, in_search, in_citation_check, in_citation_chase,
  ncbi_status, id_sources, conflict
Raw responses: data/raw/literature/ncbi_idmap/*.json

Usage: uv run --with requests python -I scripts/lit_id_map.py
"""
import csv, json, os, sys, time
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIT = os.path.join(ROOT, "data", "raw", "literature")
PROC = os.path.join(ROOT, "data", "processed")
RAWC = os.path.join(LIT, "ncbi_idmap")
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
S = requests.Session()
S.headers["User-Agent"] = "missing-label-hackathon/0.1 (research script)"


def norm_doi(d):
    d = (d or "").strip().lower()
    for p in ("https://doi.org/", "http://doi.org/", "doi:"):
        if d.startswith(p):
            d = d[len(p):]
    return d


def norm_pmc(p):
    p = (p or "").strip().upper()
    return ("PMC" + p) if p.isdigit() else p


def main():
    os.makedirs(RAWC, exist_ok=True)
    recs = []  # (pmid, pmcid, doi, origin)
    for line in open(os.path.join(LIT, "abstracts.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        recs.append((r.get("pmid", ""), r.get("pmcid", ""), norm_doi(r.get("doi")), "search"))
    p = os.path.join(PROC, "citation_verification.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            if r["exists"] == "yes":
                recs.append((r["pmid"], r["pmcid"], norm_doi(r["doi"]), "citation_check"))
    p = os.path.join(PROC, "citation_chase.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            recs.append((r["pmid"], r["pmcid"], norm_doi(r["doi"]), "citation_chase"))

    # union-find over identifiers so that one paper = one row
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    origin = {}
    for pmid, pmc, doi, org in recs:
        pmc = norm_pmc(pmc)
        ids = [i for i in (f"pmid:{pmid}" if pmid else "", f"pmcid:{pmc}" if pmc else "", f"doi:{doi}" if doi else "") if i]
        for i in ids:
            find(i)
            origin.setdefault(i, set()).add(org)
        for a, b in zip(ids, ids[1:]):
            union(a, b)

    # ID mapping via NCBI E-utilities.  The PMC ID Converter API answered
    # HTTP 403 to this script on 2026-11-14, so PubMed esummary (articleids:
    # pubmed / pmc / doi) is used for PMIDs, and esearch "<doi>"[doi] for DOIs
    # that have no PMID yet.  Same underlying NCBI data, different endpoint.
    conv = {}
    n_calls = [0]

    def eget(endpoint, data, fn):
        if os.path.exists(fn):
            return json.load(open(fn))
        for attempt in range(5):
            time.sleep(0.4)
            try:
                r = S.post(EUTILS + endpoint, data={**data, "retmode": "json", "tool": "missing-label-hackathon"}, timeout=120)
                if r.status_code == 200:
                    d = r.json()
                    json.dump(d, open(fn, "w"))
                    n_calls[0] += 1
                    return d
                print("HTTP", r.status_code, endpoint, file=sys.stderr)
            except (requests.RequestException, ValueError) as e:
                print("retry", e, file=sys.stderr)
            time.sleep(2 ** attempt)
        return None

    def add_summary(d):
        for uid in (d or {}).get("result", {}).get("uids", []):
            it = d["result"][uid]
            ids = {a.get("idtype"): a.get("value", "") for a in it.get("articleids", [])}
            key = f"pmid:{uid}"
            conv[key] = it
            for t, v in (("pmcid", ids.get("pmc", "")), ("doi", norm_doi(ids.get("doi", "")))):
                if v:
                    find(f"{t}:{v}")
                    origin.setdefault(f"{t}:{v}", set()).add("esummary")
                    union(key, f"{t}:{v}")

    have_pmid = {i for i in parent if i.startswith("pmid:")}
    groups0 = {}
    for i in list(parent):
        groups0.setdefault(find(i), []).append(i)
    no_pmid_dois = sorted({i[4:] for g in groups0.values() if not any(x.startswith("pmid:") for x in g) for i in g if i.startswith("doi:")})
    # DOIs -> PMIDs (batches of 50 OR-ed DOI searches)
    new_pmids = set()
    for k in range(0, len(no_pmid_dois), 50):
        batch = no_pmid_dois[k:k + 50]
        term = " OR ".join(f'"{d}"[doi]' for d in batch)
        d = eget("esearch.fcgi", {"db": "pubmed", "term": term, "retmax": 500}, os.path.join(RAWC, f"esearch_doi_{k // 50:04d}.json"))
        new_pmids.update((d or {}).get("esearchresult", {}).get("idlist", []))
    print("DOIs without PMID", len(no_pmid_dois), "-> PMIDs found", len(new_pmids), file=sys.stderr)
    pmids = sorted({i[5:] for i in have_pmid} | new_pmids, key=lambda x: int(x) if x.isdigit() else 0)
    for p_ in new_pmids:
        find(f"pmid:{p_}")
        origin.setdefault(f"pmid:{p_}", set()).add("esummary")
    for k in range(0, len(pmids), 200):
        d = eget("esummary.fcgi", {"db": "pubmed", "id": ",".join(pmids[k:k + 200])}, os.path.join(RAWC, f"esummary_{k // 200:04d}.json"))
        add_summary(d)
    print("esummary PMIDs", len(pmids), "calls", n_calls[0], file=sys.stderr)

    groups = {}
    for i in list(parent):
        groups.setdefault(find(i), []).append(i)
    rows = []
    for g in groups.values():
        pm = sorted({i[5:] for i in g if i.startswith("pmid:")})
        pc = sorted({i[6:] for i in g if i.startswith("pmcid:")})
        do = sorted({i[4:] for i in g if i.startswith("doi:")})
        orgs = set().union(*[origin.get(i, set()) for i in g])
        st = sorted({("pubmed_esummary_ok" if not conv[i].get("error") else "esummary_error") for i in g if i in conv}) or ["not_in_pubmed"]
        rows.append({"key": ("PMID:" + pm[0]) if pm else ("PMCID:" + pc[0]) if pc else ("DOI:" + do[0]),
                     "pmid": "|".join(pm), "pmcid": "|".join(pc), "doi": "|".join(do),
                     "in_search": "yes" if "search" in orgs else "no",
                     "in_citation_check": "yes" if "citation_check" in orgs else "no",
                     "in_citation_chase": "yes" if "citation_chase" in orgs else "no",
                     "ncbi_status": "|".join(st), "id_sources": "|".join(sorted(orgs)),
                     "conflict": "yes" if (len(pm) > 1 or len(pc) > 1 or len(do) > 1) else "no"})
    rows.sort(key=lambda r: r["key"])
    with open(os.path.join(PROC, "literature_id_map.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("papers", len(rows), "with pmid", sum(1 for r in rows if r["pmid"]), "with pmcid", sum(1 for r in rows if r["pmcid"]),
          "with doi", sum(1 for r in rows if r["doi"]), "conflicts", sum(1 for r in rows if r["conflict"] == "yes"),
          "eutils calls", n_calls[0], file=sys.stderr)


if __name__ == "__main__":
    main()
