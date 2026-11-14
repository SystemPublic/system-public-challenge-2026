"""Step 4: choose the findings to read, and fetch their PubMed abstracts.

For every non-empty cell of the raw matrix up to two findings from different papers are chosen: the cell's majority
effect (benefit or harm), a significant finding first, then one with an interval. For a
cell whose majority is benefit but which holds harms, one harm is also chosen.
Abstracts are saved outside the repository (~/opt/nyc-concordance/all_boats/abstracts.json).
The reading is recorded by hand in data/derived/all_boats/verification.csv.
"""
import json, sys, time
from pathlib import Path
import pandas as pd, requests
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/derived/all_boats"
BIG = Path.home() / "opt/nyc-concordance/all_boats"
a = pd.read_csv(OUT / "associations_classified.csv")
a = a[a.pubmed_id.notna()].copy()
a["pubmed_id"] = a.pubmed_id.astype(int)
a["sig"] = a.significant.astype(str).eq("True").astype(int)
a["has_ci"] = a.ci_lower.notna().astype(int)
picks = []
for (iv, dom), g in a.groupby(["intervention", "domain"]):
    nb, nh = (g.effect == "benefit").sum(), (g.effect == "harm").sum()
    wants = ["benefit" if nb >= nh else "harm"]
    if nb >= nh and nh > 0:
        wants.append("harm")
    for w in wants:
        s = g[g.effect == w].sort_values(["sig", "has_ci"], ascending=False)
        s = s.drop_duplicates("pubmed_id")
        for _, r in s.head(2 if w == wants[0] else 1).iterrows():
            picks.append({"intervention": iv, "domain": dom, "claimed": w, "exposure_var": r.exposure_var, "outcome_var": r.outcome_var,
                          "statistic": r.statistic, "value": r.value, "ci_lower": r.ci_lower, "ci_upper": r.ci_upper,
                          "pubmed_id": r.pubmed_id, "association_id": r.association_id})
p = pd.DataFrame(picks)
p.to_csv(OUT / "verification_sample.csv", index=False)
print(len(p), "findings to read;", p.pubmed_id.nunique(), "abstracts")
BIG.mkdir(parents=True, exist_ok=True)
f = BIG / "abstracts.json"
have = json.loads(f.read_text()) if f.exists() else {}
need = [str(x) for x in p.pubmed_id.unique() if str(x) not in have]
for i in range(0, len(need), 100):
    r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                     params={"db": "pubmed", "id": ",".join(need[i:i + 100]), "retmode": "xml"},
                     headers={"User-Agent": "research-client"}, timeout=120)
    for art in ET.fromstring(r.content).iter("PubmedArticle"):
        pmid = art.findtext(".//PMID")
        have[pmid] = {"title": "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else "",
                      "abstract": " ".join("".join(t.itertext()) for t in art.iter("AbstractText")),
                      "types": [t.text for t in art.iter("PublicationType")], "year": art.findtext(".//PubDate/Year")}
    time.sleep(1)
f.write_text(json.dumps(have))
print(len(have), "abstracts held")
