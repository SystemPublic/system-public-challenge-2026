"""Build data/forecast/graph-findings.json (GraphDataset) from the graph recon output.

Usage (from the repo root):
  # 1. (once, network) resolve publication metadata through OpenAlex; raw responses cached
  python3 -I scripts/forecast/graph/build_layer.py openalex data/forecast/raw/graph/sp_findings.json data/forecast/raw/openalex
  # 2. (offline) build the pinned layer
  python3 -I scripts/forecast/graph/build_layer.py build data/forecast/raw/graph/sp_findings.json data/forecast/raw/openalex data/forecast/graph-findings.json data/forecast/graph-vetted.json
  # 3. (offline, needs the full Dataverse studies file) extract the study rows used
  python3 -I scripts/forecast/graph/build_layer.py subset data/forecast/raw/graph/sp_findings.json <studies.tsv> data/forecast/raw/graph/dataverse-studies-subset.tsv

sp_findings.json is produced by analyze.py (in this folder) from the cached API responses.
OpenAlex requests send no email address and no key.
"""
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

KIND = {"sp_outcome": "sp", "k540e_haplotype": "codon540"}
# The Alert tab data pack's 3 haplotype_findings (commit a1cc503); in our pull they are other_dhps records.
HAPLOTYPE_IDS = {"o23pQ-icgn", "gD0V6goixf", "489sn1mPQa"}
FIELD = {"study.population": "study.population",
         "association.variable_1_name": "variable_name",
         "association.variable_2_name": "variable_name"}
UA = "resistance-observatory-hackathon/0.1"
RETRIEVED_AT = "2026-11-14T16:05:21Z"  # mtime of the newest cached Graph API response

SELECTION_RULE = (
    "Variables were found by name search in the System Public Graph API (terms for sulfadoxine-pyrimethamine "
    "and for pfdhps/dihydropteroate synthase, including K540E and 540E), then all associations of the kept "
    "variables were fetched. A finding is 'sp' when a variable name refers to SP (sulfadoxine, sulphadoxine, "
    "Fansidar, SP, SPAQ, IPTp-SP) and no dhps variable is involved. A finding is 'codon540' when a variable name "
    "explicitly includes 540E (for example K540E, 540K/E, Glu-540, dhps540Glu); dhps findings that do not name "
    "540E are excluded. A country is attached only when its name appears in the Graph study population text or "
    "in a variable name. Only findings naming at least one country are listed."
)
NOTES_TEMPLATE = [
    "The Graph has no geography field: countries are matched from the free text of each study's population description.",
    "The Graph has no per-finding publication date: dates and titles come from OpenAlex, looked up by PubMed ID or DOI.",
    "System's documentation says about 20% of associations served by the API are known-bad extractions; these findings have not been checked against the papers.",
    "{n} SP findings have no study record, so they have no population text and their country is unknown.",
]


def s(x):
    return None if x is None or x == "" else str(x)


def num(x):
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def kind_of(r):
    if r["system_id"] in HAPLOTYPE_IDS:
        return "haplotype"
    return KIND.get(r["kind"])


def load(path):
    recs = json.load(open(path, encoding="utf-8"))
    return [r for r in recs if kind_of(r)]


def graph_countries(r):
    out, seen = [], set()
    for c in r.get("countries") or []:
        if c.get("source") != "graph_record" or c.get("field") not in FIELD:
            continue
        k = (c["iso3"], FIELD[c["field"]])
        if k in seen:
            continue
        seen.add(k)
        out.append({"iso3": c["iso3"], "matchedText": c["matched_text"], "field": FIELD[c["field"]]})
    return out


def displayed(r):
    """Country-naming findings, plus the global haplotype findings (shown as not country-specific)."""
    return bool(graph_countries(r)) or kind_of(r) == "haplotype"


def fetch_openalex(recs, outdir):
    kept = [r for r in recs if displayed(r)]
    have_pmid, have_doi = load_openalex(outdir)  # only fetch ids not already cached
    pmids = sorted({s(r["pubmed_id"]) for r in kept if s(r["pubmed_id"])} - set(have_pmid))
    dois = sorted({s(r["doi"]).lower() for r in kept if not s(r["pubmed_id"]) and s(r["doi"])} - set(have_doi))
    os.makedirs(outdir, exist_ok=True)
    start = len([f for f in os.listdir(outdir) if f.endswith(".json")])
    jobs = [("pmid", pmids[i:i + 50]) for i in range(0, len(pmids), 50)]
    jobs += [("doi", dois[i:i + 50]) for i in range(0, len(dois), 50)]
    for n, (key, ids) in enumerate(jobs):
        url = ("https://api.openalex.org/works?filter=" + key + ":" + "|".join(urllib.parse.quote(i, safe="/.") for i in ids)
               + "&select=id,doi,ids,title,publication_date,publication_year&per-page=100")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.load(resp)
        with open(os.path.join(outdir, f"works_{key}_{start + n:02d}.json"), "w", encoding="utf-8") as fh:
            json.dump({"_request": "GET " + url, "_retrieved": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "response": body}, fh, ensure_ascii=False, indent=1)
        print(key, len(ids), "->", len(body.get("results", [])))


def load_openalex(outdir):
    by_pmid, by_doi = {}, {}
    if not os.path.isdir(outdir):
        return by_pmid, by_doi
    for fn in sorted(os.listdir(outdir)):
        if not fn.endswith(".json"):
            continue
        for w in json.load(open(os.path.join(outdir, fn), encoding="utf-8"))["response"].get("results", []):
            ids = w.get("ids") or {}
            pm = ids.get("pmid")
            if pm:
                by_pmid[pm.rstrip("/").rsplit("/", 1)[-1]] = w
            d = w.get("doi") or ids.get("doi")
            if d:
                by_doi[d.lower().replace("https://doi.org/", "")] = w
    return by_pmid, by_doi


def paper(r, by_pmid, by_doi):
    w = by_pmid.get(s(r["pubmed_id"]) or "") or by_doi.get((s(r["doi"]) or "").lower())
    if not w:
        return {"title": None, "publishedDate": None, "year": None, "source": None}
    return {"title": w.get("title"), "publishedDate": w.get("publication_date"),
            "year": w.get("publication_year"), "source": "openalex"}


def build(recs, oa_dir, out_path, vetted_path=None):
    by_pmid, by_doi = load_openalex(oa_dir)
    vetted = json.load(open(vetted_path, encoding="utf-8"))["ids"] if vetted_path and os.path.exists(vetted_path) else {}
    sp = [r for r in recs if kind_of(r) == "sp"]
    c5 = [r for r in recs if kind_of(r) == "codon540"]
    hp = [r for r in recs if kind_of(r) == "haplotype"]
    totals = {
        "sp": len(sp),
        "spNamingCountry": sum(1 for r in sp if graph_countries(r)),
        "spWithoutStudyRecord": sum(1 for r in sp if not r.get("study_record_source")),
        "codon540": len(c5),
        "codon540NamingCountry": sum(1 for r in c5 if graph_countries(r)),
        "papersBehindCodon540": len({s(r["pubmed_id"]) or s(r["doi"]) for r in c5}),
        "haplotype": len(hp),
        "haplotypeNamingCountry": sum(1 for r in hp if graph_countries(r)),
    }
    for r in hp:
        if not graph_countries(r):
            print("haplotype finding names no country (shown as not country-specific):", r["system_id"])
    findings = []
    for r in recs:
        cs = graph_countries(r)
        if not displayed(r):
            continue
        st = r.get("study") or {}
        findings.append({
            "systemId": r["system_id"], "kind": kind_of(r),
            "spLooksLikeUptake": bool(r.get("sp_variable_looks_like_uptake_measure")),
            "variable1": (r.get("variable_1") or {}).get("name") or "",
            "variable2": (r.get("variable_2") or {}).get("name") or "",
            "statisticType": r.get("statistic_type") or "",
            "statisticValue": num(r.get("statistic_value")), "ciLower": num(r.get("ci_lower")),
            "ciUpper": num(r.get("ci_upper")), "pValue": num(r.get("p_value")),
            "studyId": s(r.get("study_id")), "pubmedId": s(r.get("pubmed_id")), "doi": s(r.get("doi")),
            "population": st.get("population") or None, "countries": cs, "paper": paper(r, by_pmid, by_doi),
            "inVettedCsv": vetted.get(r["system_id"]),
        })
    findings.sort(key=lambda f: (f["kind"], f["systemId"]))
    notes = [n.format(n=totals["spWithoutStudyRecord"]) for n in NOTES_TEMPLATE]
    out = {
        "source": {
            "id": "system-public-graph", "label": "System Public Graph", "licence": "CC BY-NC 4.0",
            "citation": "System, Inc. (2026). System Public Graph (Version 2.1) [Data set]. DOI: https://doi.org/10.7910/DVN/7V6JDO",  # verbatim, as in the Alert tab data pack README
            "url": "https://public-api.system.com/v1/", "retrievedAt": RETRIEVED_AT, "notes": notes,
        },
        "version": "2.1", "snapshot": "2026-07-01", "selectionRule": SELECTION_RULE,
        "totals": totals, "findings": findings,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    dated = sum(1 for f in findings if f["paper"]["source"])
    print("totals", totals, "findings", len(findings), "with OpenAlex metadata", dated)


def subset(recs, studies_path, out_path):
    ids = {s(r.get("study_id")) for r in recs if graph_countries(r) and s(r.get("study_id"))}
    n = 0
    with open(studies_path, newline="", encoding="utf-8", errors="replace") as fin, \
            open(out_path, "w", newline="", encoding="utf-8") as fout:
        rd = csv.reader(fin)
        wr = csv.writer(fout)
        wr.writerow(next(rd))
        for row in rd:
            if row and row[0] in ids:
                wr.writerow(row)
                n += 1
    print("study rows written", n, "of", len(ids), "study ids used")


if __name__ == "__main__":
    mode = sys.argv[1]
    recs = load(sys.argv[2])
    if mode == "openalex":
        fetch_openalex(recs, sys.argv[3])
    elif mode == "build":
        build(recs, sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else None)
    elif mode == "subset":
        subset(recs, sys.argv[3], sys.argv[4])
    else:
        sys.exit("mode must be openalex | build | subset")
