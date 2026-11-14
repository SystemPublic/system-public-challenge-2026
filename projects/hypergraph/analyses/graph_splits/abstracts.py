"""Fetch PubMed abstracts (NCBI E-utilities, no key) for the findings of the relationships read
in the moderator analysis. Output: data/derived/graph/splits/abstracts.json (pmid -> text)."""
import json, sys, time, re
from pathlib import Path
import requests, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/derived/graph/splits"
EXTRA = [("temperature", "asthma"), ("temperature", "COVID-19"), ("temperature", "acute myocardial infarction"),
         ("temperature", "heart failure"), ("particulates", "birth mass")]

def main():
    d = pd.read_csv(OUT / "splits.csv"); F = json.loads((OUT / "findings.json").read_text())
    rids = list(pd.read_csv(OUT / "top15.csv").relationship_id)
    rids += [d[(d.source == s) & (d.target == t)].relationship_id.iloc[0] for s, t in EXTRA]
    pm = sorted({str(f["pmid"]) for r in rids for f in F[r] if f.get("pmid") and f["direction"] in ("+", "-")})
    f = OUT / "abstracts.json"
    have = json.loads(f.read_text()) if f.exists() else {}
    todo = [p for p in pm if p not in have]
    for i in range(0, len(todo), 40):
        b = todo[i:i + 40]
        r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                         params={"db": "pubmed", "id": ",".join(b), "rettype": "medline", "retmode": "text"},
                         headers={"User-Agent": "research-script/1.0"}, timeout=120)
        r.raise_for_status()
        for rec in re.split(r"\n\n(?=PMID- )", r.text.strip()):
            m = re.match(r"PMID- (\d+)", rec)
            if not m: continue
            get = lambda tag: " ".join(x.strip() for x in re.findall(rf"^{tag}\s*- (.*(?:\n      .*)*)", rec, re.M)).replace("\n      ", " ")
            have[m.group(1)] = {"title": get("TI"), "abstract": get("AB"), "year": get("DP")[:4], "journal": get("TA")}
        time.sleep(0.5)
    f.write_text(json.dumps(have, indent=0))
    print(len(pm), "pmids;", sum(1 for p in pm if have.get(p, {}).get("abstract")), "with abstracts")

if __name__ == "__main__":
    main()
