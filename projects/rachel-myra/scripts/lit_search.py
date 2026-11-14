"""Literature search for The Missing Label (spec §8.4 steps 1-2).

Runs fixed, saved queries against PubMed (NCBI E-utilities) and Europe PMC:
  * 15 drugs/classes x heat block (MeSH Hot Temperature, Heat Stress Disorders,
    Heat Stroke, Extreme Heat, Hyperthermia, Hypohidrosis + free-text heat terms)
  * a count-only grid: each drug x each single heat term (the evidence funnel)
  * storage/stability queries (insulin, epinephrine auto-injectors, inhalers,
    glucose test strips/meters, mail-order delivery)

Retrieval uses the animal-only exclusion filter on PubMed and a per-query cap
(CAP below); both full and filtered counts are saved.  Records are fetched
(title, abstract, year, journal, DOI, PMID, PMCID, publication types, MeSH).

Outputs (data/raw/literature/):
  queries.json          every query string, per source
  query_counts.csv      hit counts per query (funnel)
  heat_term_grid.csv    drug x single-heat-term counts (PubMed + Europe PMC)
  pubmed_ids/*.txt      PMIDs retrieved per query
  epmc_raw/*.jsonl      Europe PMC core results per query
  abstracts.jsonl       one merged record per unique paper
and data/processed/literature_records.csv (flat, no abstract truncation).

Usage:  uv run --with requests python -I scripts/lit_search.py [--grid-only|--skip-grid]
"""
import csv, json, os, re, sys, time
import xml.etree.ElementTree as ET
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "literature")
PROC = os.path.join(ROOT, "data", "processed")
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
TOOL = "missing-label-hackathon"
CAP = 2000  # max records retrieved per query per source
ANIMAL_FILTER = ' NOT ("Animals"[Mesh] NOT "Humans"[Mesh])'

# ---------- heat terms ----------
HEAT_PUBMED = {
    "MeSH Hot Temperature": '"Hot Temperature"[Mesh]',
    "MeSH Heat Stress Disorders": '"Heat Stress Disorders"[Mesh]',
    "MeSH Heat Stroke": '"Heat Stroke"[Mesh]',
    "MeSH Extreme Heat": '"Extreme Heat"[Mesh]',
    "MeSH Hyperthermia": '"Hyperthermia"[Mesh]',
    "MeSH Hypohidrosis": '"Hypohidrosis"[Mesh]',
    "heat wave/heatwave": '("heat wave"[tiab] OR "heat waves"[tiab] OR heatwave*[tiab])',
    "high ambient temperature": '("ambient temperature*"[tiab] OR "high temperature*"[tiab] OR "hot weather"[tiab] OR "extreme heat"[tiab] OR "summer heat"[tiab])',
    "heat illness free text": '("heat stroke"[tiab] OR heatstroke[tiab] OR "heat illness*"[tiab] OR "heat-related illness*"[tiab] OR "heat exhaustion"[tiab] OR hyperthermia[tiab] OR hypohidrosis[tiab] OR anhidrosis[tiab] OR oligohidrosis[tiab])',
}
HEAT_PUBMED_ALL = "(" + " OR ".join(HEAT_PUBMED.values()) + ")"

HEAT_EPMC = {
    "heat stroke/illness": '(TITLE_ABS:"heat stroke" OR TITLE_ABS:heatstroke OR TITLE_ABS:"heat illness" OR TITLE_ABS:"heat-related illness" OR TITLE_ABS:"heat exhaustion")',
    "hyperthermia": "(TITLE_ABS:hyperthermia)",
    "hypohidrosis/anhidrosis": "(TITLE_ABS:hypohidrosis OR TITLE_ABS:anhidrosis OR TITLE_ABS:oligohidrosis)",
    "heat wave/heatwave": '(TITLE_ABS:"heat wave" OR TITLE_ABS:"heat waves" OR TITLE_ABS:heatwave OR TITLE_ABS:heatwaves)',
    "high ambient temperature": '(TITLE_ABS:"ambient temperature" OR TITLE_ABS:"hot weather" OR TITLE_ABS:"extreme heat" OR TITLE_ABS:"high temperature" OR TITLE_ABS:"summer heat")',
    "heat stress": '(TITLE_ABS:"heat stress" OR TITLE_ABS:"heat exposure")',
}
HEAT_EPMC_ALL = "(" + " OR ".join(HEAT_EPMC.values()) + ")"
HEAT_EPMC_FULLTEXT = '("heat stroke" OR heatstroke OR "heat illness" OR "heat wave" OR heatwave OR hyperthermia OR hypohidrosis OR anhidrosis OR "extreme heat" OR "hot weather")'


def tiab(terms):
    return " OR ".join(f'"{t}"[tiab]' if (" " in t or "-" in t) else f"{t}[tiab]" for t in terms)


def epmc_terms(terms):
    return "(" + " OR ".join(f'TITLE_ABS:"{t}"' if (" " in t or "-" in t) else f"TITLE_ABS:{t}" for t in terms) + ")"


# ---------- drug blocks: (PubMed block, Europe PMC term list) ----------
DRUGS = {
    "lithium": (
        '(("Lithium Compounds"[Mesh] OR "Lithium Carbonate"[Mesh] OR lithium[tiab]) NOT (batter*[tiab] OR cathode*[tiab] OR anode*[tiab] OR electrode*[tiab]))',
        ['"lithium" AND NOT (TITLE_ABS:battery OR TITLE_ABS:batteries OR TITLE_ABS:cathode OR TITLE_ABS:anode)'],
    ),
    "loop diuretics": ('("Sodium Potassium Chloride Symporter Inhibitors"[Mesh] OR "Furosemide"[Mesh] OR ' + tiab(["furosemide", "frusemide", "bumetanide", "torsemide", "torasemide", "loop diuretic*"]) + ")",
                       ["furosemide", "frusemide", "bumetanide", "torsemide", "torasemide", "loop diuretic", "loop diuretics"]),
    "thiazides": ('("Sodium Chloride Symporter Inhibitors"[Mesh] OR "Thiazides"[Mesh] OR ' + tiab(["thiazide*", "hydrochlorothiazide", "chlorthalidone", "indapamide", "bendroflumethiazide"]) + ")",
                  ["thiazide", "thiazides", "hydrochlorothiazide", "chlorthalidone", "indapamide", "bendroflumethiazide"]),
    "ACE inhibitors/ARBs": ('("Angiotensin-Converting Enzyme Inhibitors"[Mesh] OR "Angiotensin Receptor Antagonists"[Mesh] OR ' + tiab(["ACE inhibitor*", "angiotensin-converting enzyme inhibitor*", "angiotensin receptor blocker*", "ARBs", "lisinopril", "ramipril", "enalapril", "perindopril", "losartan", "valsartan", "candesartan", "irbesartan", "telmisartan"]) + ")",
                            ["ACE inhibitor", "ACE inhibitors", "angiotensin-converting enzyme inhibitor", "angiotensin receptor blocker", "angiotensin receptor blockers", "lisinopril", "ramipril", "enalapril", "perindopril", "losartan", "valsartan", "candesartan", "irbesartan", "telmisartan"]),
    "SGLT2 inhibitors": ('("Sodium-Glucose Transporter 2 Inhibitors"[Mesh] OR ' + tiab(["SGLT2", "SGLT-2", "SGLT2i", "gliflozin*", "empagliflozin", "dapagliflozin", "canagliflozin", "ertugliflozin"]) + ")",
                         ["SGLT2", "SGLT-2", "SGLT2i", "gliflozin", "empagliflozin", "dapagliflozin", "canagliflozin", "ertugliflozin"]),
    "insulin (incl. pumps)": ('("Insulin/therapeutic use"[Mesh] OR "Insulin/adverse effects"[Mesh] OR "Insulin Infusion Systems"[Mesh] OR ' + tiab(["insulin pump*", "insulin pen*", "insulin therapy", "insulin-treated", "insulin users", "insulin-dependent", "insulin analog*", "CSII"]) + ")",
                              ["insulin pump", "insulin pumps", "insulin pen", "insulin pens", "insulin therapy", "insulin-treated", "insulin users", "insulin analog", "insulin analogue", "CSII"]),
    "metformin": ('("Metformin"[Mesh] OR metformin[tiab])', ["metformin"]),
    "anticholinergics (oxybutynin)": ('("Cholinergic Antagonists"[Mesh] OR "Muscarinic Antagonists"[Mesh] OR ' + tiab(["anticholinergic*", "antimuscarinic*", "oxybutynin", "tolterodine", "solifenacin", "trospium", "benztropine", "trihexyphenidyl", "anticholinergic burden"]) + ")",
                                      ["anticholinergic", "anticholinergics", "antimuscarinic", "oxybutynin", "tolterodine", "solifenacin", "trospium", "benztropine", "trihexyphenidyl"]),
    "antipsychotics (incl. clozapine)": ('("Antipsychotic Agents"[Mesh] OR ' + tiab(["antipsychotic*", "neuroleptic*", "clozapine", "olanzapine", "quetiapine", "risperidone", "haloperidol", "aripiprazole", "chlorpromazine", "paliperidone"]) + ")",
                                         ["antipsychotic", "antipsychotics", "neuroleptic", "neuroleptics", "clozapine", "olanzapine", "quetiapine", "risperidone", "haloperidol", "aripiprazole", "chlorpromazine", "paliperidone"]),
    "SSRIs": ('("Selective Serotonin Reuptake Inhibitors"[Mesh] OR ' + tiab(["SSRI", "SSRIs", "serotonin reuptake inhibitor*", "sertraline", "fluoxetine", "citalopram", "escitalopram", "paroxetine", "fluvoxamine"]) + ")",
              ["SSRI", "SSRIs", "selective serotonin reuptake inhibitor", "sertraline", "fluoxetine", "citalopram", "escitalopram", "paroxetine", "fluvoxamine"]),
    "topiramate/zonisamide": ('("Topiramate"[Mesh] OR "Zonisamide"[Mesh] OR topiramate[tiab] OR zonisamide[tiab])', ["topiramate", "zonisamide"]),
    "ADHD stimulants": ('("Methylphenidate"[Mesh] OR "Dextroamphetamine"[Mesh] OR "Lisdexamfetamine Dimesylate"[Mesh] OR "Amphetamine"[Mesh:NoExp] OR ' + tiab(["methylphenidate", "dexmethylphenidate", "lisdexamfetamine", "dextroamphetamine", "mixed amphetamine salts", "ADHD medication*", "stimulant medication*"]) + ' OR (amphetamine*[tiab] AND (ADHD[tiab] OR "attention deficit"[tiab])))',
                        ["methylphenidate", "dexmethylphenidate", "lisdexamfetamine", "dextroamphetamine", "mixed amphetamine salts", "ADHD medication", "stimulant medication"]),
    "beta blockers": ('("Adrenergic beta-Antagonists"[Mesh] OR ' + tiab(["beta blocker*", "beta-blocker*", "beta-adrenergic blocker*", "metoprolol", "propranolol", "atenolol", "carvedilol", "bisoprolol", "nebivolol"]) + ")",
                      ["beta blocker", "beta blockers", "beta-blocker", "beta-blockers", "metoprolol", "propranolol", "atenolol", "carvedilol", "bisoprolol", "nebivolol"]),
    "fentanyl/opioid patches": ('("Fentanyl"[Mesh] OR fentanyl[tiab] OR (("Transdermal Patch"[Mesh] OR transdermal[tiab] OR patch*[tiab]) AND ("Analgesics, Opioid"[Mesh] OR opioid*[tiab] OR buprenorphine[tiab])))',
                                ["fentanyl", '"transdermal opioid"', '"buprenorphine patch"', '"opioid patch"']),
    "epinephrine auto-injectors": ('(' + tiab(["epinephrine auto-injector*", "epinephrine autoinjector*", "adrenaline auto-injector*", "adrenaline autoinjector*", "EpiPen*", "Auvi-Q"]) + ' OR ((epinephrine[tiab] OR adrenaline[tiab]) AND (auto-injector*[tiab] OR autoinjector*[tiab])))',
                                   ["epinephrine auto-injector", "epinephrine autoinjector", "adrenaline auto-injector", "adrenaline autoinjector", "EpiPen"]),
}

# ---------- storage / stability queries (PubMed, Europe PMC) ----------
STORAGE = {
    "storage: insulin": (
        '("Insulin"[Mesh] OR insulin[tiab]) AND (storage[tiab] OR stability[tiab] OR potency[tiab] OR degradation[tiab] OR "temperature excursion*"[tiab] OR "Drug Storage"[Mesh] OR "Drug Stability"[Mesh]) AND ("Hot Temperature"[Mesh] OR heat[tiab] OR "high temperature*"[tiab] OR "elevated temperature*"[tiab] OR "room temperature"[tiab] OR "hot climate*"[tiab] OR tropical[tiab])',
        'TITLE_ABS:insulin AND (TITLE_ABS:storage OR TITLE_ABS:stability OR TITLE_ABS:potency OR TITLE_ABS:degradation OR TITLE_ABS:"temperature excursion") AND (TITLE_ABS:heat OR TITLE_ABS:"high temperature" OR TITLE_ABS:"elevated temperature" OR TITLE_ABS:"room temperature" OR TITLE_ABS:"hot climate" OR TITLE_ABS:tropical)',
    ),
    "storage: epinephrine auto-injector": (
        '(' + tiab(["epinephrine auto-injector*", "epinephrine autoinjector*", "adrenaline auto-injector*", "adrenaline autoinjector*", "EpiPen*"]) + ' OR ((epinephrine[tiab] OR adrenaline[tiab]) AND (auto-injector*[tiab] OR autoinjector*[tiab] OR syringe*[tiab]))) AND (temperature*[tiab] OR heat[tiab] OR storage[tiab] OR stability[tiab] OR degradation[tiab] OR expired[tiab] OR "Drug Storage"[Mesh] OR "Drug Stability"[Mesh])',
        '(TITLE_ABS:"epinephrine auto-injector" OR TITLE_ABS:"epinephrine autoinjector" OR TITLE_ABS:"adrenaline auto-injector" OR TITLE_ABS:"adrenaline autoinjector" OR TITLE_ABS:EpiPen) AND (TITLE_ABS:temperature OR TITLE_ABS:heat OR TITLE_ABS:storage OR TITLE_ABS:stability OR TITLE_ABS:degradation OR TITLE_ABS:expired)',
    ),
    "storage: inhalers": (
        '("Metered Dose Inhalers"[Mesh] OR "Dry Powder Inhalers"[Mesh] OR inhaler*[tiab]) AND ("Hot Temperature"[Mesh] OR "Temperature"[Mesh:NoExp] OR temperature*[tiab] OR heat[tiab] OR humidity[tiab]) AND (storage[tiab] OR stability[tiab] OR "dose delivery"[tiab] OR "delivered dose"[tiab] OR performance[tiab] OR "Drug Storage"[Mesh] OR "Drug Stability"[Mesh] OR "aerosol performance"[tiab])',
        '(TITLE_ABS:inhaler OR TITLE_ABS:inhalers) AND (TITLE_ABS:temperature OR TITLE_ABS:heat OR TITLE_ABS:humidity) AND (TITLE_ABS:storage OR TITLE_ABS:stability OR TITLE_ABS:"dose delivery" OR TITLE_ABS:"delivered dose" OR TITLE_ABS:performance)',
    ),
    "storage: glucose test strips/meters": (
        '("Blood Glucose Self-Monitoring"[Mesh] OR "test strip*"[tiab] OR "glucose meter*"[tiab] OR glucometer*[tiab] OR "blood glucose monitor*"[tiab] OR "continuous glucose monitor*"[tiab]) AND ("Hot Temperature"[Mesh] OR temperature*[tiab] OR heat[tiab] OR humidity[tiab]) AND (accuracy[tiab] OR storage[tiab] OR stability[tiab] OR performance[tiab] OR error*[tiab] OR interference[tiab])',
        '(TITLE_ABS:"test strip" OR TITLE_ABS:"test strips" OR TITLE_ABS:"glucose meter" OR TITLE_ABS:"glucose meters" OR TITLE_ABS:glucometer OR TITLE_ABS:"continuous glucose monitor") AND (TITLE_ABS:temperature OR TITLE_ABS:heat OR TITLE_ABS:humidity) AND (TITLE_ABS:accuracy OR TITLE_ABS:storage OR TITLE_ABS:stability OR TITLE_ABS:performance OR TITLE_ABS:error OR TITLE_ABS:errors)',
    ),
    "storage: mail-order / delivery temperature": (
        '("mail order"[tiab] OR "mail-order"[tiab] OR "home delivery"[tiab] OR "pharmacy delivery"[tiab] OR shipping[tiab] OR shipped[tiab] OR "cold chain"[tiab] OR "postal"[tiab]) AND (temperature*[tiab] OR heat[tiab] OR "Hot Temperature"[Mesh]) AND (medication*[tiab] OR medicine*[tiab] OR drug*[tiab] OR insulin[tiab] OR pharmac*[tiab])',
        '(TITLE_ABS:"mail order" OR TITLE_ABS:"mail-order" OR TITLE_ABS:"home delivery" OR TITLE_ABS:"pharmacy delivery" OR TITLE_ABS:shipping OR TITLE_ABS:postal) AND (TITLE_ABS:temperature OR TITLE_ABS:heat) AND (TITLE_ABS:medication OR TITLE_ABS:medications OR TITLE_ABS:medicine OR TITLE_ABS:medicines OR TITLE_ABS:drug OR TITLE_ABS:drugs OR TITLE_ABS:insulin OR TITLE_ABS:pharmacy)',
    ),
    "storage: medicines in heat (general)": (
        '("Drug Storage"[Mesh] OR "Drug Stability"[Mesh] OR "medication storage"[tiab] OR "medicine storage"[tiab] OR "drug storage"[tiab]) AND ("Hot Temperature"[Mesh] OR "Extreme Heat"[Mesh] OR "heat wave*"[tiab] OR heatwave*[tiab] OR "hot climate*"[tiab] OR "high temperature*"[tiab] OR "temperature excursion*"[tiab]) AND ("Humans"[Mesh] OR patient*[tiab] OR home[tiab] OR household*[tiab] OR pharmac*[tiab] OR ambulance*[tiab] OR "emergency medical"[tiab])',
        '(TITLE_ABS:"medication storage" OR TITLE_ABS:"medicine storage" OR TITLE_ABS:"drug storage" OR TITLE_ABS:"drug stability") AND (TITLE_ABS:"heat wave" OR TITLE_ABS:heatwave OR TITLE_ABS:"hot climate" OR TITLE_ABS:"high temperature" OR TITLE_ABS:"temperature excursion" OR TITLE_ABS:ambulance)',
    ),
}


def epmc_drug(terms):
    if len(terms) == 1 and terms[0].startswith('"lithium"'):
        return '(TITLE_ABS:lithium AND NOT (TITLE_ABS:battery OR TITLE_ABS:batteries OR TITLE_ABS:cathode OR TITLE_ABS:anode))'
    out = []
    for t in terms:
        if t.startswith('"') and t.endswith('"'):
            out.append(f"TITLE_ABS:{t}")
        elif " " in t or "-" in t:
            out.append(f'TITLE_ABS:"{t}"')
        else:
            out.append(f"TITLE_ABS:{t}")
    return "(" + " OR ".join(out) + ")"


def epmc_drug_fulltext(terms):
    if terms[0].startswith('"lithium"'):
        return "(lithium NOT battery NOT batteries)"
    return "(" + " OR ".join(t if t.startswith('"') else (f'"{t}"' if (" " in t or "-" in t) else t) for t in terms) + ")"


# ---------- HTTP helpers ----------
S = requests.Session()
S.headers["User-Agent"] = "missing-label-hackathon/0.1 (research script)"
_last = [0.0]


def get(url, params=None, data=None, min_gap=0.4, tries=6):
    for i in range(tries):
        wait = _last[0] + min_gap - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = S.post(url, data=data, timeout=120) if data is not None else S.get(url, params=params, timeout=120)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** i + 1)
                continue
            r.raise_for_status()
        except requests.RequestException as e:
            print("  retry", i, e, file=sys.stderr)
            time.sleep(2 ** i + 1)
    raise RuntimeError(f"failed: {url} {params}")


def pubmed_count(term):
    r = get(EUTILS + "esearch.fcgi", {"db": "pubmed", "term": term, "retmode": "json", "retmax": 0, "tool": TOOL})
    return int(r.json()["esearchresult"]["count"])


def pubmed_ids(term, cap=CAP):
    r = get(EUTILS + "esearch.fcgi", {"db": "pubmed", "term": term, "retmode": "json", "retmax": cap, "sort": "relevance", "tool": TOOL})
    d = r.json()["esearchresult"]
    return int(d["count"]), d["idlist"]


def epmc_count(q):
    r = get(EPMC, {"query": q, "format": "json", "pageSize": 1, "resultType": "lite"}, min_gap=0.3)
    return int(r.json().get("hitCount", 0))


def epmc_fetch(q, cap=CAP):
    out, cursor = [], "*"
    count = None
    while len(out) < cap:
        r = get(EPMC, {"query": q, "format": "json", "pageSize": min(1000, cap - len(out)), "resultType": "core", "cursorMark": cursor}, min_gap=0.5)
        d = r.json()
        count = d.get("hitCount", 0)
        res = d.get("resultList", {}).get("result", [])
        out.extend(res)
        nxt = d.get("nextCursorMark")
        if not res or not nxt or nxt == cursor:
            break
        cursor = nxt
    return count, out


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


# ---------- efetch parsing ----------
def text_of(el):
    return "".join(el.itertext()).strip() if el is not None else ""


def parse_pubmed_xml(xml):
    recs = []
    root = ET.fromstring(xml)
    for art in root.iter("PubmedArticle"):
        mc = art.find("MedlineCitation")
        a = mc.find("Article")
        pmid = text_of(mc.find("PMID"))
        title = text_of(a.find("ArticleTitle"))
        parts = []
        for at in a.findall("Abstract/AbstractText"):
            lab = at.get("Label")
            t = text_of(at)
            parts.append(f"{lab}: {t}" if lab else t)
        abstract = "\n".join(p for p in parts if p)
        journal = text_of(a.find("Journal/Title"))
        year = text_of(a.find("Journal/JournalIssue/PubDate/Year"))
        if not year:
            md = text_of(a.find("Journal/JournalIssue/PubDate/MedlineDate"))
            m = re.search(r"(19|20)\d\d", md)
            year = m.group(0) if m else ""
        if not year:
            ad = a.find("ArticleDate/Year")
            year = text_of(ad)
        ids = {i.get("IdType"): text_of(i) for i in art.findall("PubmedData/ArticleIdList/ArticleId")}
        doi = ids.get("doi", "")
        if not doi:
            for e in a.findall("ELocationID"):
                if e.get("EIdType") == "doi":
                    doi = text_of(e)
        pubtypes = [text_of(p) for p in a.findall("PublicationTypeList/PublicationType")]
        mesh = []
        for mh in mc.findall("MeshHeadingList/MeshHeading"):
            d = mh.find("DescriptorName")
            quals = [text_of(q) for q in mh.findall("QualifierName")]
            mesh.append(text_of(d) + ("/" + "/".join(quals) if quals else ""))
        kws = [text_of(k) for k in mc.findall("KeywordList/Keyword")]
        recs.append({
            "pmid": pmid, "pmcid": ids.get("pmc", ""), "doi": doi.lower(), "title": title, "abstract": abstract,
            "year": year, "journal": journal, "publication_types": pubtypes, "mesh": mesh, "keywords": kws,
            "language": text_of(a.find("Language")),
        })
    return recs


def efetch(pmids):
    recs = []
    for i in range(0, len(pmids), 200):
        batch = pmids[i:i + 200]
        r = get(EUTILS + "efetch.fcgi", data={"db": "pubmed", "id": ",".join(batch), "retmode": "xml", "tool": TOOL})
        recs.extend(parse_pubmed_xml(r.content))
        print(f"  efetch {i + len(batch)}/{len(pmids)}", file=sys.stderr)
    return recs


def epmc_to_rec(e):
    mesh = []
    for m in (e.get("meshHeadingList") or {}).get("meshHeading", []) or []:
        q = [x.get("qualifierName", "") for x in (m.get("meshQualifierList") or {}).get("meshQualifier", [])]
        mesh.append(m.get("descriptorName", "") + ("/" + "/".join(q) if q else ""))
    return {
        "pmid": e.get("pmid", "") or "", "pmcid": e.get("pmcid", "") or "", "doi": (e.get("doi", "") or "").lower(),
        "title": e.get("title", "") or "", "abstract": re.sub(r"<[^>]+>", "", e.get("abstractText", "") or ""),
        "year": str(e.get("pubYear", "") or ""), "journal": ((e.get("journalInfo") or {}).get("journal") or {}).get("title", "") or "",
        "publication_types": (e.get("pubTypeList") or {}).get("pubType", []) or [], "mesh": mesh,
        "keywords": (e.get("keywordList") or {}).get("keyword", []) or [], "language": e.get("language", ""),
        "epmc_id": f'{e.get("source", "")}:{e.get("id", "")}', "epmc_source": e.get("source", ""),
    }


def main():
    grid_only = "--grid-only" in sys.argv
    skip_grid = "--skip-grid" in sys.argv
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(PROC, exist_ok=True)
    os.makedirs(os.path.join(RAW, "pubmed_ids"), exist_ok=True)
    os.makedirs(os.path.join(RAW, "epmc_raw"), exist_ok=True)

    # build query table
    queries = []
    for drug, (pm, ep) in DRUGS.items():
        queries.append({"query_id": "drug_" + slug(drug), "group": "drug x heat", "label": drug,
                        "pubmed": f"{pm} AND {HEAT_PUBMED_ALL}",
                        "pubmed_retrieval": f"({pm} AND {HEAT_PUBMED_ALL}){ANIMAL_FILTER}",
                        "epmc": f"{epmc_drug(ep)} AND {HEAT_EPMC_ALL}",
                        "epmc_fulltext_count_only": f"{epmc_drug_fulltext(ep)} AND {HEAT_EPMC_FULLTEXT}"})
    for lab, (pm, ep) in STORAGE.items():
        queries.append({"query_id": slug(lab), "group": "storage/stability", "label": lab,
                        "pubmed": pm, "pubmed_retrieval": pm, "epmc": ep, "epmc_fulltext_count_only": ""})
    json.dump({"access_date": "2026-11-14", "cap_per_query_per_source": CAP,
               "animal_filter_pubmed_retrieval": ANIMAL_FILTER, "heat_terms_pubmed": HEAT_PUBMED,
               "heat_terms_epmc": HEAT_EPMC, "queries": queries}, open(os.path.join(RAW, "queries.json"), "w"), indent=1)

    # grid: drug x single heat term counts
    if not skip_grid:
        grid_path = os.path.join(RAW, "heat_term_grid.csv")
        with open(grid_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["drug", "source", "heat_term", "query", "count"])
            for drug, (pm, ep) in DRUGS.items():
                for hl, hq in HEAT_PUBMED.items():
                    q = f"{pm} AND {hq}"
                    w.writerow([drug, "pubmed", hl, q, pubmed_count(q)])
                for hl, hq in HEAT_EPMC.items():
                    q = f"{epmc_drug(ep)} AND {hq}"
                    w.writerow([drug, "europepmc", hl, q, epmc_count(q)])
                f.flush()
                print("grid", drug, file=sys.stderr)
        if grid_only:
            return

    # retrieval
    pmid_sources = {}   # pmid -> set(query_id)
    epmc_recs = {}      # key -> rec
    counts = []
    for q in queries:
        qid = q["query_id"]
        print("query", qid, file=sys.stderr)
        n_all = pubmed_count(q["pubmed"])
        n_ret, ids = pubmed_ids(q["pubmed_retrieval"])
        open(os.path.join(RAW, "pubmed_ids", qid + ".txt"), "w").write("\n".join(ids))
        for p in ids:
            pmid_sources.setdefault(p, set()).add("pubmed:" + qid)
        n_ep, ep = epmc_fetch(q["epmc"])
        with open(os.path.join(RAW, "epmc_raw", qid + ".jsonl"), "w") as f:
            for e in ep:
                f.write(json.dumps(e) + "\n")
        for e in ep:
            r = epmc_to_rec(e)
            if r["pmid"]:
                pmid_sources.setdefault(r["pmid"], set()).add("europepmc:" + qid)
            else:
                k = "doi:" + r["doi"] if r["doi"] else r["epmc_id"]
                if k in epmc_recs:
                    epmc_recs[k]["found_by"].add("europepmc:" + qid)
                else:
                    r["found_by"] = {"europepmc:" + qid}
                    epmc_recs[k] = r
        n_ft = epmc_count(q["epmc_fulltext_count_only"]) if q["epmc_fulltext_count_only"] else ""
        counts.append({"query_id": qid, "group": q["group"], "label": q["label"],
                       "pubmed_count_all": n_all, "pubmed_count_human_filter": n_ret, "pubmed_retrieved": len(ids),
                       "epmc_count_title_abstract": n_ep, "epmc_retrieved": len(ep),
                       "epmc_count_fulltext_incl_oa": n_ft,
                       "capped": "yes" if (n_ret > CAP or (n_ep or 0) > CAP) else "no"})
        with open(os.path.join(RAW, "query_counts.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(counts[0].keys()))
            w.writeheader()
            w.writerows(counts)

    # fetch PubMed records
    pmids = sorted(pmid_sources, key=int)
    print("unique PMIDs", len(pmids), file=sys.stderr)
    recs = efetch(pmids)
    got = {r["pmid"] for r in recs}
    # PMIDs Europe PMC knows but efetch did not return: fall back to EPMC record
    epmc_by_pmid = {}
    for fn in os.listdir(os.path.join(RAW, "epmc_raw")):
        for line in open(os.path.join(RAW, "epmc_raw", fn)):
            e = json.loads(line)
            if e.get("pmid") and e["pmid"] not in got:
                epmc_by_pmid[e["pmid"]] = epmc_to_rec(e)
    recs.extend(epmc_by_pmid.values())
    # fill missing PMCID / DOI for PubMed recs from EPMC data where possible
    out = []
    for r in recs:
        r["found_by"] = sorted(pmid_sources.get(r["pmid"], []))
        r["record_source"] = "pubmed" if r["pmid"] in got else "europepmc"
        out.append(r)
    pm_dois = {r["doi"] for r in out if r["doi"]}
    for k, r in epmc_recs.items():
        if r["doi"] and r["doi"] in pm_dois:
            continue
        r["found_by"] = sorted(r["found_by"])
        r["record_source"] = "europepmc"
        out.append(r)

    with open(os.path.join(RAW, "abstracts.jsonl"), "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    cols = ["record_id", "pmid", "pmcid", "doi", "epmc_id", "year", "journal", "title", "publication_types", "mesh",
            "has_abstract", "abstract", "language", "found_by", "n_queries", "record_source"]
    with open(os.path.join(PROC, "literature_records.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in out:
            rid = ("PMID:" + r["pmid"]) if r["pmid"] else (("DOI:" + r["doi"]) if r["doi"] else r.get("epmc_id", ""))
            w.writerow({"record_id": rid, "pmid": r["pmid"], "pmcid": r["pmcid"], "doi": r["doi"],
                        "epmc_id": r.get("epmc_id", ""), "year": r["year"], "journal": r["journal"], "title": r["title"],
                        "publication_types": "; ".join(r["publication_types"]), "mesh": "; ".join(r["mesh"]),
                        "has_abstract": "yes" if r["abstract"] else "no", "abstract": r["abstract"],
                        "language": r.get("language", ""), "found_by": "; ".join(r["found_by"]),
                        "n_queries": len({x.split(":", 1)[1] for x in r["found_by"]}), "record_source": r["record_source"]})
    print("total unique records", len(out), file=sys.stderr)


if __name__ == "__main__":
    main()
