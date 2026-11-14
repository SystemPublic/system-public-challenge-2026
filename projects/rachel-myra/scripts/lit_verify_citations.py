"""Citation verification for the master list and the research report (spec §8.2a checks 1-2).

For every PMID / DOI / PMCID cited in
  data/Drug heat risk master list.csv   (column "Key citations")
  report/Prescribed drug heat risks.md  (inline IDs and link URLs)
this script:
  1. checks the ID exists (PubMed efetch for PMIDs; Crossref for DOIs; Europe PMC
     for PMCIDs; DOI -> PMID via PubMed [doi] search, then Europe PMC.  The PMC ID
     Converter API returned HTTP 403 to Python on 2026-11-14 and is not used),
  2. fetches title + abstract (PubMed, falling back to Europe PMC, then Crossref),
  3. scores the match between the cited label (e.g. "Layton et al., PLoS One 2020")
     and the fetched record (first-author surname, year, journal words, title words),
  4. abstract grounding: checks whether each number quoted with the citation
     appears verbatim in the abstract (after normalising "·" to "." and removing
     thousands separators).  Integers below 10 are listed but not scored.
  5. checks that the row's drug terms / heat terms appear in title+abstract.

Numbers attributed to a citation:
  master list: the parenthetical right after the ID, e.g. "PMID 17513091 (OR 6.0)";
               numbers in the row's other text ("What can go wrong", "Notes",
               "Higher-risk groups") are checked separately (row_text_numbers_*).
  report:      numbers in the text between the previous citation (or paragraph start)
               and this citation, excluding 4-digit years 1900-2030.  Heuristic.

Raw API responses are cached in data/raw/literature/citation_check/.
Output: data/processed/citation_verification.csv

Usage: uv run --with requests python -I scripts/lit_verify_citations.py
"""
import csv, difflib, json, os, re, sys, time, urllib.parse
import xml.etree.ElementTree as ET
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "literature", "citation_check")
OUT = os.path.join(ROOT, "data", "processed", "citation_verification.csv")
MASTER = os.path.join(ROOT, "data", "Drug heat risk master list.csv")
REPORT = os.path.join(ROOT, "report", "Prescribed drug heat risks.md")
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
IDCONV = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
TOOL = "missing-label-hackathon"

S = requests.Session()
S.headers["User-Agent"] = "missing-label-hackathon/0.1 (research script)"
_last = [0.0]


def get(url, params=None, min_gap=0.4, tries=5, ok404=False):
    for i in range(tries):
        w = _last[0] + min_gap - time.time()
        if w > 0:
            time.sleep(w)
        _last[0] = time.time()
        try:
            r = S.get(url, params=params, timeout=60)
            if r.status_code == 200 or (ok404 and r.status_code == 404):
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** i + 1)
                continue
            return r
        except requests.RequestException as e:
            print("retry", e, file=sys.stderr)
            time.sleep(2 ** i + 1)
    return None


def cache(name, fn):
    p = os.path.join(RAW, re.sub(r"[^A-Za-z0-9_.-]", "_", name))
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    txt = fn()
    if txt is not None:
        open(p, "w", encoding="utf-8").write(txt)
    return txt


# ---------- ID extraction ----------
DOI_RE = r"10\.\d{4,9}/[^\s;,\]\"'<>]+"


def clean_doi(d):
    d = urllib.parse.unquote(d).strip().rstrip(".")
    d = d.split("~")[0]
    # balance parentheses: drop trailing ')' that close markdown links
    while d.endswith(")") and d.count(")") > d.count("("):
        d = d[:-1]
    d = re.sub(r"(/pdf|\.pdf)$", "", d.rstrip("."), flags=re.I)
    return d.rstrip(".").lower()


def ids_in(text):
    """Return list of (type, value, start, end) for IDs found in text."""
    out = []
    for m in re.finditer(r"PMIDs?:?\s?(\d{5,9})((?:\s*[;,]\s*\d{5,9}\b)*)", text):
        out.append(("pmid", m.group(1), m.start(), m.start(2)))
        for m2 in re.finditer(r"\d{5,9}", m.group(2)):
            out.append(("pmid", m2.group(0), m.start(2) + m2.start(), m.start(2) + m2.end()))
    for m in re.finditer(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d{5,9})", text):
        out.append(("pmid", m.group(1), m.start(), m.end()))
    for m in re.finditer(r"EXT_ID:(\d{5,9})", text):
        out.append(("pmid", m.group(1), m.start(), m.end()))
    for m in re.finditer(r"curehunter\.com/public/pubmed(\d{5,9})", text):
        out.append(("pmid", m.group(1), m.start(), m.end()))
    for m in re.finditer(r"db\.cngb\.org/data_resources/literature/(\d{5,9})", text):
        out.append(("pmid", m.group(1), m.start(), m.end()))
    for m in re.finditer(r"(PMC\d{4,9})", text):
        out.append(("pmcid", m.group(1), m.start(), m.end()))
    for m in re.finditer(r"(?:doi\.org/|DOI:?\s|/doi/|/articles/|/abstract/|ejournals/pdf/|id=)(10(?:\.|%2E)\d{4,9}(?:/|%2F)[^\s;,\]\"'<>]+)", text, flags=re.I):
        out.append(("doi", clean_doi(m.group(1)), m.start(), m.end()))
    # de-duplicate overlapping
    seen, res = set(), []
    for t in sorted(out, key=lambda x: x[2]):
        k = (t[0], t[1], t[2])
        if k not in seen:
            seen.add(k)
            res.append(t)
    return res


NUM_RE = re.compile(r"(?<![\w.])[+\-~±≈]?(\d{1,3}(?:,\d{3})+|\d+(?:[.·]\d+)?)")


def numbers_in(text, skip_years=False):
    text = re.sub(r"\]\([^)]*\)", "]", text)            # drop link URLs
    text = re.sub(r"(PMID|PMC|DOI)[ :]?\S+", " ", text)  # drop IDs
    text = re.sub(r"10\.\d{4,9}/\S+", " ", text)
    nums = []
    for m in NUM_RE.finditer(text):
        n = m.group(1).replace(",", "").replace("·", ".")
        if skip_years and re.fullmatch(r"(19|20)\d\d", n):
            continue
        if re.fullmatch(r"\d{7,}", n):  # bare IDs
            continue
        if n not in nums:
            nums.append(n)
    return nums


def norm_abs(a):
    a = a.replace("·", ".").replace(" ", " ")
    return re.sub(r"(?<=\d),(?=\d{3}\b)", "", a)


def num_present(n, abstract):
    return re.search(r"(?<![\d.])" + re.escape(n) + r"(?!\d|\.\d)", abstract) is not None


def scorable(n):
    return "." in n or int(float(n)) >= 10


# ---------- collect citations ----------
def from_master():
    rows = list(csv.DictReader(open(MASTER, encoding="utf-8-sig")))
    cites = []
    for r in rows:
        kc = r["Key citations"]
        rowtext = " ".join(r[c] for c in ("What can go wrong", "Notes", "Higher-risk groups"))
        for part in kc.split(";"):
            for typ, val, s, e in ids_in(part):
                rest = part[e:]
                m = re.match(r"\s*\(([^)]*)\)", rest)
                paren = m.group(1) if m else ""
                label = part[:s].strip(" ,")
                cites.append({"source": "master_list", "location": r["ID"], "id_type": typ, "id_value": val,
                              "cited_label": label, "claim_text": paren, "claimed_numbers": numbers_in(paren),
                              "row_numbers": [n for n in numbers_in(rowtext) if scorable(n)],
                              "drug_terms": drug_terms(r["Drug or class"] + "," + r["Example drugs"]),
                              "master_citation_status": r["Citation status"]})
    return cites


def drug_terms(s):
    terms = []
    for t in re.split(r"[,/;()]| and | or ", s):
        t = t.strip().lower()
        t = re.sub(r"\b\d+\s*mg\b", "", t).strip()
        if len(t) >= 4 and t not in terms:
            terms.append(t)
    return terms


def from_report():
    cites = []
    lines = open(REPORT, encoding="utf-8").read().split("\n")
    for ln, line in enumerate(lines, 1):
        found = ids_in(line)
        prev_end = 0
        # link spans so that we can attach the link label
        links = [(m.start(), m.end(), m.group(1)) for m in re.finditer(r"\[([^\]]+)\]\((?:[^()]|\([^()]*\))*\)", line)]
        for typ, val, s, e in found:
            label = ""
            lstart = s
            for ls, le, lt in links:
                if ls <= s < le:
                    label, lstart = lt, ls
            if not label:
                # inline "Author 2026, PMID x" in prose or table cell
                seg = line[max(0, s - 80):s]
                seg = re.split(r"[|;(]", seg)[-1]
                label = seg.strip(" ,")
            bounds = [le for ls, le, lt in links if le <= lstart] + [fe for ft, fv, fs, fe in found if fe <= lstart]
            start = max(bounds + [prev_end, 0])
            if line.lstrip().startswith("|"):
                start = max(start, line.rfind("|", 0, s) + 1)
            claim = line[start:lstart]
            cites.append({"source": "report", "location": f"line {ln}", "id_type": typ, "id_value": val,
                          "cited_label": label, "claim_text": re.sub(r"\]\([^)]*\)", "]", claim).strip()[-400:],
                          "claimed_numbers": numbers_in(claim, skip_years=True), "row_numbers": [],
                          "drug_terms": [], "master_citation_status": ""})
            prev_end = max(prev_end, e)
            for ls, le, lt in links:
                if ls <= s < le:
                    prev_end = max(prev_end, le)
    # dedupe identical (location, id)
    seen, out = set(), []
    for c in cites:
        k = (c["location"], c["id_type"], c["id_value"])
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out


# ---------- lookups ----------
def text_of(el):
    return "".join(el.itertext()).strip() if el is not None else ""


def pubmed_record(pmid):
    xml = cache(f"pubmed_{pmid}.xml", lambda: (lambda r: r.text if r is not None else None)(
        get(EUTILS + "efetch.fcgi", {"db": "pubmed", "id": pmid, "retmode": "xml", "tool": TOOL})))
    if not xml or "<PubmedArticle>" not in xml:
        return None
    art = ET.fromstring(xml.encode()).find(".//PubmedArticle")
    mc = art.find("MedlineCitation")
    a = mc.find("Article")
    if text_of(mc.find("PMID")) != pmid:
        return None
    abstract = "\n".join(((at.get("Label") + ": ") if at.get("Label") else "") + text_of(at) for at in a.findall("Abstract/AbstractText"))
    year = text_of(a.find("Journal/JournalIssue/PubDate/Year")) or (re.findall(r"(?:19|20)\d\d", text_of(a.find("Journal/JournalIssue/PubDate/MedlineDate"))) or [""])[0] or text_of(a.find("ArticleDate/Year"))
    ids = {i.get("IdType"): text_of(i) for i in art.findall("PubmedData/ArticleIdList/ArticleId")}
    authors = [text_of(au.find("LastName")) or text_of(au.find("CollectiveName")) for au in a.findall("AuthorList/Author")]
    return {"pmid": pmid, "title": text_of(a.find("ArticleTitle")), "abstract": abstract, "year": year,
            "journal": text_of(a.find("Journal/Title")), "journal_abbrev": text_of(a.find("Journal/ISOAbbreviation")),
            "authors": authors, "doi": ids.get("doi", "").lower(), "pmcid": ids.get("pmc", ""),
            "pubtypes": [text_of(p) for p in a.findall("PublicationTypeList/PublicationType")]}


def idconv(idv):
    """PMC ID Converter returned HTTP 403 to this script on 2026-11-14; disabled.
    PMCIDs are resolved via Europe PMC (PMCID:) and DOIs via PubMed [doi] search."""
    return {}


def pmid_for_doi(doi):
    c = idconv(doi)
    if c.get("pmid"):
        return c["pmid"]
    txt = cache(f"esearch_doi_{doi}.json", lambda: (lambda r: r.text if r is not None else None)(
        get(EUTILS + "esearch.fcgi", {"db": "pubmed", "term": f'"{doi}"[doi]', "retmode": "json", "tool": TOOL})))
    try:
        ids = json.loads(txt)["esearchresult"]["idlist"]
        if len(ids) == 1:
            return ids[0]
    except Exception:
        pass
    e = epmc(f'DOI:"{doi}"')
    return e.get("pmid", "") if e else ""


def epmc(query):
    txt = cache(f"epmc_{query}.json", lambda: (lambda r: r.text if r is not None else None)(
        get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", {"query": query, "format": "json", "resultType": "core", "pageSize": 2})))
    try:
        res = json.loads(txt)["resultList"]["result"]
        return res[0] if len(res) >= 1 else None
    except Exception:
        return None


def crossref(doi):
    txt = cache(f"crossref_{doi}.json", lambda: (lambda r: r.text if r is not None else None)(
        get("https://api.crossref.org/works/" + urllib.parse.quote(doi), min_gap=0.3, ok404=True)))
    try:
        m = json.loads(txt)["message"]
        yr = ""
        for k in ("published-print", "published-online", "issued", "created"):
            dp = (m.get(k) or {}).get("date-parts")
            if dp and dp[0] and dp[0][0]:
                yr = str(dp[0][0])
                break
        return {"title": " ".join(m.get("title", [])), "journal": " ".join(m.get("container-title", [])),
                "year": yr, "authors": [a.get("family", "") for a in m.get("author", [])],
                "abstract": re.sub(r"<[^>]+>", " ", m.get("abstract", "") or "").strip(), "type": m.get("type", "")}
    except Exception:
        return None


# ---------- scoring ----------
STOP = {"et", "al", "the", "of", "and", "in", "a", "j", "journal", "study", "case", "report", "review"}


def label_score(label, rec):
    """0-1 match between a cited label and a fetched record; None if label has nothing to compare."""
    if not label or not rec:
        return None, ""
    comps, notes = [], []
    lab = re.sub(r"[\[\]*_]", " ", label)
    years = re.findall(r"\b(19\d\d|20\d\d)\b", lab)
    if years and rec.get("year"):
        y = int(years[-1]); ry = int(rec["year"])
        comps.append(1.0 if y == ry else 0.5 if abs(y - ry) == 1 else 0.0)
        notes.append(f"year {y} vs {ry}")
    names = [w for w in re.findall(r"\b([A-Z][a-zA-Z'\-]+)\b", lab) if w.lower() not in STOP]
    am = re.match(r"\s*([A-Z][a-zA-Z'\-]+(?: [A-Z][a-zA-Z'\-]+)?)(?:\s+et al|\s*&|\s+and\s|,?\s+(?:19|20)\d\d\b|,\s)", lab)
    if am and not am.group(1).isupper() and am.group(1).split()[0].lower() not in {"pubmed", "none", "see", "swedish", "french", "japanese", "national", "university", "thieme", "cureus", "front", "plos", "jama", "bmj"}:
        names = [am.group(1).split()[0]] + names
    else:
        names = []
    surnames = [a.lower() for a in rec.get("authors", []) if a]
    if names and surnames:
        cand = names[0]
        hit = any(cand.lower() == s or cand.lower() in s.split() or cand.lower().replace(" ", "") == s.replace(" ", "") for s in surnames)
        # first word may be a journal word, check authors more loosely
        if not hit:
            hit = any(n.lower() in surnames for n in names)
        jtoks = set(re.findall(r"[a-z]+", (rec.get("journal", "") + " " + rec.get("journal_abbrev", "")).lower()))
        if not hit and cand.lower() in jtoks:
            pass  # label starts with a journal name; no author named
        else:
            comps.append(1.0 if hit else 0.0)
            notes.append(f"author {'ok' if hit else 'MISMATCH'} ({cand} vs {', '.join(rec.get('authors', [])[:3])})")
    jt = set(re.findall(r"[a-z]+", (rec.get("journal", "") + " " + rec.get("journal_abbrev", "")).lower())) - STOP
    lt = set(re.findall(r"[a-z]+", lab.lower())) - STOP - {n.lower() for n in names[:1]}
    jlab = [t for t in lt if any(j.startswith(t) for j in jt)]
    if jlab:
        comps.append(1.0)
        notes.append("journal words match")
    # title-like label: long label, compare with title
    words = re.findall(r"[A-Za-z]{3,}", lab)
    if len(words) >= 6 and rec.get("title"):
        r = difflib.SequenceMatcher(None, lab.lower(), rec["title"].lower()).ratio()
        comps.append(r)
        notes.append(f"title sim {r:.2f}")
    if not comps:
        return None, ""
    return round(sum(comps) / len(comps), 2), "; ".join(notes)


HEAT_TERMS = ["heat", "hyperthermi", "temperature", "hot ", "summer", "sweat", "hidrosis", "thermoreg", "warm", "sauna", "climate", "heatwave"]


def resolve(typ, val, cache_res):
    key = (typ, val)
    if key in cache_res:
        return cache_res[key]
    res = {"exists": False, "exists_via": "", "pmid": "", "doi": "", "pmcid": "", "rec": None, "crossref": None, "abstract_source": "", "note": ""}
    if typ == "pmid":
        rec = pubmed_record(val)
        if rec:
            res.update(exists=True, exists_via="pubmed", pmid=val, doi=rec["doi"], pmcid=rec["pmcid"], rec=rec)
        else:
            e = epmc(f"EXT_ID:{val} AND SRC:MED")
            if e:
                res.update(exists=True, exists_via="europepmc", pmid=val, doi=(e.get("doi") or "").lower(), pmcid=e.get("pmcid", ""),
                           rec={"title": e.get("title", ""), "abstract": re.sub(r"<[^>]+>", "", e.get("abstractText", "") or ""),
                                "year": e.get("pubYear", ""), "journal": ((e.get("journalInfo") or {}).get("journal") or {}).get("title", ""),
                                "journal_abbrev": "", "authors": [a.get("lastName", "") for a in (e.get("authorList") or {}).get("author", [])]})
            else:
                res["note"] = "PMID not returned by PubMed efetch or Europe PMC"
    elif typ == "pmcid":
        c = idconv(val)
        if c.get("pmid"):
            res = dict(resolve("pmid", c["pmid"], cache_res))
            res["pmcid"] = val
            res["exists_via"] = "idconv->" + res["exists_via"]
        elif c and not c.get("errmsg"):
            res.update(exists=True, exists_via="idconv (no PMID)", pmcid=val, doi=(c.get("doi") or "").lower())
        else:
            e = epmc(f"PMCID:{val}")
            if e:
                res.update(exists=True, exists_via="europepmc", pmcid=val, pmid=e.get("pmid", ""), doi=(e.get("doi") or "").lower(),
                           rec={"title": e.get("title", ""), "abstract": re.sub(r"<[^>]+>", "", e.get("abstractText", "") or ""),
                                "year": e.get("pubYear", ""), "journal": "", "journal_abbrev": "",
                                "authors": [a.get("lastName", "") for a in (e.get("authorList") or {}).get("author", [])]})
            else:
                res["note"] = "PMCID not found by ID Converter or Europe PMC"
    elif typ == "doi":
        cr = crossref(val)
        res["crossref"] = cr
        pmid = pmid_for_doi(val)
        if pmid:
            sub = resolve("pmid", pmid, cache_res)
            res.update({k: sub[k] for k in ("pmid", "pmcid", "rec")})
            res["doi"] = val
            res["exists"] = True
            res["exists_via"] = ("crossref+" if cr else "") + "pubmed"
        elif cr:
            e = epmc(f'DOI:"{val}"')
            res.update(exists=True, exists_via="crossref", doi=val,
                       rec={"title": cr["title"], "abstract": (re.sub(r"<[^>]+>", "", (e or {}).get("abstractText", "") or "") or cr["abstract"]),
                            "year": cr["year"], "journal": cr["journal"], "journal_abbrev": "", "authors": cr["authors"]})
            res["note"] = "DOI in Crossref, no PMID found"
        else:
            res["note"] = "DOI not found in Crossref, PubMed or Europe PMC"
    # abstract fallback via Europe PMC
    rec = res.get("rec")
    if rec is not None:
        if rec.get("abstract"):
            res["abstract_source"] = "pubmed" if res["exists_via"].endswith("pubmed") else res["exists_via"]
        else:
            e = epmc(f"EXT_ID:{res['pmid']} AND SRC:MED") if res["pmid"] else (epmc(f'DOI:"{res["doi"]}"') if res["doi"] else None)
            ab = re.sub(r"<[^>]+>", "", (e or {}).get("abstractText", "") or "")
            if not ab and res["doi"]:
                cr = res.get("crossref") or crossref(res["doi"])
                ab = (cr or {}).get("abstract", "")
                if ab:
                    res["abstract_source"] = "crossref"
            elif ab:
                res["abstract_source"] = "europepmc"
            rec["abstract"] = ab
    cache_res[key] = res
    return res


def main():
    os.makedirs(RAW, exist_ok=True)
    cites = from_master() + from_report()
    print("citations", len(cites), file=sys.stderr)
    # borrow report labels for master-list IDs without a label
    rep_labels = {}
    for c in cites:
        if c["source"] == "report" and c["cited_label"] and (c["id_type"], c["id_value"]) not in rep_labels:
            rep_labels[(c["id_type"], c["id_value"])] = c["cited_label"]
    cache_res = {}
    rows = []
    for c in cites:
        r = resolve(c["id_type"], c["id_value"], cache_res)
        rec = r.get("rec") or {}
        label = c["cited_label"] or rep_labels.get((c["id_type"], c["id_value"]), "")
        score, snotes = label_score(label, rec) if rec else (None, "")
        ab = norm_abs(rec.get("abstract", "") or "")
        hay = norm_abs((rec.get("title", "") or "") + "\n" + ab)
        claimed = c["claimed_numbers"]
        sc = [n for n in claimed if scorable(n)]
        found = [n for n in sc if num_present(n, hay)]
        missing = [n for n in sc if n not in found]
        rfound = [n for n in c["row_numbers"] if num_present(n, hay)] if hay.strip() else []
        low = hay.lower()
        dfound = [t for t in c["drug_terms"] if t.split()[0][:6] in low]
        heat_hit = any(h in low for h in HEAT_TERMS)
        # crossref vs pubmed title consistency for DOIs
        cr = r.get("crossref")
        cr_sim = ""
        if c["id_type"] == "doi" and cr and rec.get("title") and r["exists_via"].endswith("pubmed"):
            cr_sim = round(difflib.SequenceMatcher(None, cr["title"].lower(), rec["title"].lower()).ratio(), 2)
        flags = []
        if not r["exists"]:
            verdict = "id_not_found"
        elif not ab:
            verdict = "exists_no_abstract"
        elif not sc:
            verdict = "exists_no_numbers_claimed"
        elif not missing:
            verdict = "numbers_all_in_abstract"
        elif found:
            verdict = "numbers_partly_in_abstract"
        else:
            verdict = "numbers_not_in_abstract"
        if score is not None and score < 0.5:
            flags.append("label_mismatch")
        if cr_sim != "" and cr_sim < 0.6:
            flags.append("doi_title_differs_from_pubmed")
        if c["drug_terms"] and hay.strip() and not dfound:
            flags.append("drug_terms_absent")
        if hay.strip() and not heat_hit:
            flags.append("no_heat_terms")
        rows.append({
            "source": c["source"], "location": c["location"], "id_type": c["id_type"], "id_value": c["id_value"],
            "cited_label": label, "claim_text": c["claim_text"], "exists": "yes" if r["exists"] else "no",
            "exists_via": r["exists_via"], "pmid": r["pmid"], "pmcid": r["pmcid"], "doi": r["doi"],
            "fetched_title": rec.get("title", ""), "fetched_year": rec.get("year", ""), "fetched_journal": rec.get("journal", ""),
            "fetched_first_author": (rec.get("authors") or [""])[0], "abstract_source": r["abstract_source"],
            "has_abstract": "yes" if ab else "no", "title_match_score": "" if score is None else score,
            "title_match_notes": snotes, "crossref_vs_pubmed_title_sim": cr_sim,
            "numbers_claimed": " | ".join(claimed), "numbers_found": " | ".join(found), "numbers_missing": " | ".join(missing),
            "row_text_numbers_checked": " | ".join(c["row_numbers"]), "row_text_numbers_found_here": " | ".join(rfound),
            "drug_terms_found": " | ".join(dfound), "heat_terms_present": ("yes" if heat_hit else "no") if hay.strip() else "",
            "master_citation_status": c["master_citation_status"], "verdict": verdict, "flags": "; ".join(flags), "note": r["note"],
        })
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print("rows", len(rows), "unique ids", len({(x['id_type'], x['id_value']) for x in rows}), file=sys.stderr)
    print(Counter(x["verdict"] for x in rows), file=sys.stderr)
    print(Counter(f for x in rows for f in x["flags"].split("; ") if f), file=sys.stderr)


if __name__ == "__main__":
    main()
