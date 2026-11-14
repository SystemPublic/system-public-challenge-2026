"""Fetch PubMed abstracts by PMID (NCBI E-utilities, generic client name), cached in abstracts.json."""
import json, re, sys, time
import requests
from common import OUT
F = OUT / "abstracts.json"

def fetch(pmids):
    cache = json.loads(F.read_text()) if F.exists() else {}
    need = [str(p) for p in pmids if p and str(p) not in cache]
    for i in range(0, len(need), 80):
        chunk = need[i:i + 80]
        r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                         params={"db": "pubmed", "id": ",".join(chunk), "retmode": "xml"},
                         headers={"User-Agent": "research-script/1.0"}, timeout=60)
        r.raise_for_status()
        for art in re.findall(r"<PubmedArticle>.*?</PubmedArticle>", r.text, flags=re.S):
            pm = re.search(r"<PMID[^>]*>(\d+)</PMID>", art).group(1)
            title = re.sub(r"<[^>]+>", "", (re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", art, flags=re.S) or [None, ""])[1])
            ab = " ".join(re.sub(r"<[^>]+>", "", a) for a in re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", art, flags=re.S))
            yr = (re.search(r"<PubDate>.*?<Year>(\d{4})</Year>", art, flags=re.S) or [None, ""])[1]
            cache[pm] = {"title": title, "abstract": ab, "year": yr}
        for p in chunk:
            cache.setdefault(p, {"title": "", "abstract": "", "year": ""})
        time.sleep(0.4)
    F.write_text(json.dumps(cache))
    return cache

def snippet(ab, value, width=260):
    """Sentences of the abstract that contain the stored statistic, else the end of the abstract."""
    if value is not None:
        for v in {f"{float(value):g}", f"{float(value):.2f}", f"{float(value):.1f}"}:
            i = ab.find(v)
            if i >= 0:
                return True, ab[max(0, i - width): i + width // 2]
    return False, ab[-width * 2:]

if __name__ == "__main__":
    c = fetch(sys.argv[1:])
    for p in sys.argv[1:]:
        print(p, c[p]["year"], c[p]["title"], "\n", c[p]["abstract"], "\n")
