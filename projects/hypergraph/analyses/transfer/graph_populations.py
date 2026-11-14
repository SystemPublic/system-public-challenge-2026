"""Classify the free-text population field of studies behind the temperature-violence, telework, commuting and ridership findings.
Rule-based on keywords; the unclassified remainder is listed for reading. Writes populations_table.json and populations_classified.csv.
Run: ~/.venvs/nyc-concordance/bin/python -m analyses.transfer.graph_populations
"""
import csv, json, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "graph" / "transfer_chicago"
REG = [  # order matters: first match wins; multi-country texts are caught first
    ("Multi-country", r"\b(\d+|two|three|several) (countries|nations)\b|worldwide|globally|multinational|152 countries|14 countries|12 West African|Uganda, Zimbabwe|Madrid and Lisbon|London \(United Kingdom\) and in Italy|studies examining|individuals included in studies"),
    ("United States", r"\bU\.?S\.?\b|United States|American|California|Louisiana|Oregon|Washington State|Iowa\b|Chicago|New York|Idaho|Vermont|New Jersey|mid-Atlantic|National Sleep Foundation|Kentucky|Texas|Florida|Massachusetts|Baltimore|Philadelphia|ECHO\)|blood donors"),
    ("Japan", r"Japan|Osaka|Tokyo"),
    ("Korea", r"Korea"),
    ("China", r"China|Chinese|Shanghai|Wuhan|Wuhu|prefectures? of Japan|WeChat"),
    ("Canada", r"Canad|Toronto|Ontario"),
    ("Europe", r"Swiss|Swedish|Sweden|Cambridge|Barcelona|Nutrinet|Gothenburg|Dutch|Netherlands|German|Spanish|Spain|Madrid|Italy|Italian|Polish|Poles|France|French|Norway|Finland|Finnish|Austria|Switzerland|Geneva|Portug|London|United Kingdom|\bUK\b|England|Brussels|Belgi|Sweden|Danish|Denmark|Ireland|Scotland|Greece"),
    ("Latin America", r"Latin America|Brazil|Colombia|Bogot|Manaus|Curitiba|Mexic|Chile|Argentin|Peru"),
    ("Other Asia/Africa/Oceania", r"Dhaka|Sydney|Nepean|Kuwait|Thailand|Chiang Mai|Pakistan|India|Kenya|Uganda|Africa|Australia|New Zealand|Māori|Iran|Turkey|Saudi|Israel|Bangladesh|Nigeria|Ghana|Egypt|Vietnam|Indonesia|Malaysia|Singapore|Taiwan|Hong Kong"),
]
CITY = re.compile(r"\b(cities|city|metropolitan|urban|Chicago|New York|Los Angeles|Boston|Philadelphia|Baltimore|Detroit|Washington, DC|San Francisco)\b", re.I)
US_BIG = re.compile(r"Chicago|New York|Los Angeles|Boston|Philadelphia|Baltimore|Detroit|San Francisco|most populous cities|large US cities|100 US cities", re.I)


def region(t):
    if not t:
        return "No population given"
    for name, rx in REG:
        if re.search(rx, t, re.I):
            return name
    return "Unspecified"


def table(ids, studies):
    rows = []
    for s in ids:
        p = (studies.get(s) or {}).get("population")
        r = region(p)
        rows.append({"study_id": s, "pubmed_id": (studies.get(s) or {}).get("pubmed_id"), "population": p, "region": r,
                     "us_large_city": bool(p and r in ("United States", "Multi-country") and US_BIG.search(p)),
                     "names_chicago_or_nyc": bool(p and re.search(r"Chicago|New York", p, re.I))})
    return rows


def main():
    tv = json.loads((OUT / "temp_violence_studies.json").read_text())
    tw = json.loads((OUT / "telework_commute_studies.json").read_text())
    vv = json.loads((OUT / "violence_variable_temperature_hits.json").read_text())
    S = dict(tw["studies"])
    sets = {}
    # violence side: grounded relationships restricted to interpersonal violence (not suicide, not occupational injury), and a wider set
    inter = {"homicide", "intimate partner violence", "firearm", "violence", "violent crime", "crime", "aggression", "aggressive behavior",
             "assault", "domestic violence", "gun violence", "shooting", "exposure to violence"}
    ids_inter = [k for k, v in tv["studies"].items() if any(p[1] in inter for p in v["pairs"])]
    ids_all = list(tv["studies"])
    studies_tv = tv["studies"]
    sets["temperature x interpersonal violence (grounded)"] = table(ids_inter, studies_tv)
    sets["temperature x any violence-side concept incl. suicide and injury (grounded)"] = table(ids_all, studies_tv)
    # variable-name hits: add the two violent-crime studies and Xu; fetched populations are not in the cache for these, so use pubmed ids
    extra = {"38331944": "Nationwide, South Korea, 2016-2020 (abstract)", "35061073": "Khayelitsha township, South Africa, 2006-2016 (abstract)"}
    sets["interpersonal violence incl. ungrounded variable hits"] = sets["temperature x interpersonal violence (grounded)"] + [
        {"study_id": "pm" + k, "pubmed_id": int(k), "population": v, "region": "Korea" if "Korea" in v else "Other Asia/Africa/Oceania", "us_large_city": False, "names_chicago_or_nyc": False} for k, v in extra.items()]
    for g in ("telework", "ridership", "commuting"):
        sets[g] = table(tw[g]["study_ids"], S)
    summ = {}
    for name, rows in sets.items():
        c = Counter(r["region"] for r in rows)
        n = len(rows)
        have = sum(1 for r in rows if r["population"])
        summ[name] = {"n_studies": n, "n_with_population": have, "regions": dict(c.most_common()),
                      "n_us": c.get("United States", 0), "n_us_large_city": sum(r["us_large_city"] for r in rows),
                      "n_names_chicago_or_nyc": sum(r["names_chicago_or_nyc"] for r in rows)}
    (OUT / "populations_table.json").write_text(json.dumps(summ, indent=1))
    with open(OUT / "populations_classified.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["set", "study_id", "pubmed_id", "region", "us_large_city", "names_chicago_or_nyc", "population"])
        for name, rows in sets.items():
            for r in rows:
                w.writerow([name, r["study_id"], r["pubmed_id"], r["region"], r["us_large_city"], r["names_chicago_or_nyc"], r["population"]])
    print(json.dumps(summ, indent=1))
    for name, rows in sets.items():
        for r in rows:
            if r["region"] in ("Unspecified",):
                print("UNCLEAR", name[:20], r["study_id"], (r["population"] or "")[:120])


if __name__ == "__main__":
    main()
