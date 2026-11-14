"""Stage 4 (no network): classify kept associations, attach study records, detect countries.
Inputs: work/assoc.json, work/studies_api.json, dataverse/studies.tsv (optional; Graph's own
Dataverse deposit of the studies table, same fields as /v1/studies, 'population_string').
Output: sp_findings.json"""
import csv, json, os, re, sys
from collections import defaultdict
from fetch import is_sp_name, is_dhps_name, WORK, HERE
import apilib
OUT_DIR = apilib.RAW  # data/forecast/raw/graph

csv.field_size_limit(10**9)
EXPLICIT_540 = re.compile(r"540\s*E|540\s*K\s*/\s*E|Glu-?540|K540\s*E|SGEAA|dhps540Glu|540Glu", re.I)
QUINT = re.compile(r"quintuple|sextuple", re.I)
UPTAKE = re.compile(r"uptake|utili[sz]ation|\buse\b|usage|adherence|coverage|receiv|doses?\b|awareness|knowledge|taking|timely|timing|complete|optimal|adequate|non-adherence|program|implementation|administration|delivery|access", re.I)

# ISO3 -> list of regexes (word-bounded). Ordered so longer names are consumed first.
C = {
 "AFG": ["Afghanistan"], "AGO": ["Angola"], "BEN": ["Benin"], "BWA": ["Botswana"], "BFA": ["Burkina Faso"],
 "BDI": ["Burundi"], "CMR": ["Cameroon"], "CPV": ["Cape Verde", "Cabo Verde"], "CAF": ["Central African Republic"],
 "TCD": ["Chad"], "COM": ["Comoros"], "COD": ["Democratic Republic of (?:the )?Congo", r"\bDR ?Congo", r"\bDRC\b", "Congo-Kinshasa", "Zaire"],
 "COG": ["Republic of (?:the )?Congo", "Congo-Brazzaville", r"(?<!Democratic Republic of the )(?<!Democratic Republic of )(?<!DR )(?<!DR)\bCongo\b(?!-Kinshasa)"],
 "CIV": ["C[oô]te d['’]Ivoire", "Ivory Coast"], "DJI": ["Djibouti"], "EGY": ["Egypt"], "GNQ": ["Equatorial Guinea"],
 "ERI": ["Eritrea"], "SWZ": ["Eswatini", "Swaziland"], "ETH": ["Ethiopia"], "GAB": ["Gabon"], "GMB": [r"\bGambia"],
 "GHA": ["Ghana"], "GIN": [r"(?<!Papua New )(?<!Equatorial )\bGuinea\b(?!-Bissau| Bissau)"], "GNB": ["Guinea-Bissau", "Guinea Bissau"],
 "KEN": ["Kenya"], "LSO": ["Lesotho"], "LBR": ["Liberia"], "LBY": ["Libya"], "MDG": ["Madagascar"], "MWI": ["Malawi"],
 "MLI": [r"\bMali\b"], "MRT": ["Mauritania"], "MUS": ["Mauritius"], "MAR": ["Morocco"], "MOZ": ["Mozambique"],
 "NAM": ["Namibia"], "NER": [r"\bNiger\b"], "NGA": ["Nigeria"], "RWA": ["Rwanda"], "STP": ["S[aã]o Tom[eé]"],
 "SEN": ["Senegal"], "SLE": ["Sierra Leone"], "SOM": ["Somalia"], "ZAF": ["South Africa"], "SSD": ["South Sudan"],
 "SDN": [r"(?<!South )\bSudan\b"], "TZA": ["Tanzania", "Zanzibar"], "TGO": [r"\bTogo\b"], "UGA": ["Uganda"],
 "ZMB": ["Zambia"], "ZWE": ["Zimbabwe"], "DZA": ["Algeria"], "TUN": ["Tunisia"],
 "IND": [r"\bIndia\b"], "PAK": ["Pakistan"], "BGD": ["Bangladesh"], "NPL": ["Nepal"], "LKA": ["Sri Lanka"],
 "MMR": ["Myanmar", "Burma"], "THA": ["Thailand"], "KHM": ["Cambodia"], "LAO": [r"\bLaos\b", "Lao PDR", "Lao People"],
 "VNM": ["Viet ?nam"], "MYS": ["Malaysia"], "IDN": ["Indonesia"], "PHL": ["Philippines"], "PNG": ["Papua New Guinea"],
 "SLB": ["Solomon Islands"], "VUT": ["Vanuatu"], "TLS": ["Timor-Leste", "East Timor"], "CHN": [r"\bChina\b"],
 "YEM": ["Yemen"], "SAU": ["Saudi Arabia"], "IRN": [r"\bIran\b"], "OMN": [r"\bOman\b"], "AFR": [],
 "BRA": ["Brazil"], "COL": ["Colombia"], "PER": [r"\bPeru\b"], "VEN": ["Venezuela"], "BOL": ["Bolivia"],
 "ECU": ["Ecuador"], "GUY": ["Guyana"], "SUR": ["Suriname"], "GUF": ["French Guiana"], "HTI": ["Haiti"],
 "HND": ["Honduras"], "NIC": ["Nicaragua"], "GTM": ["Guatemala"], "MEX": ["Mexico"], "PAN": ["Panama"],
 "USA": ["United States", r"\bUSA\b", r"\bU\.S\.A?\b"], "GBR": ["United Kingdom", r"\bUK\b", "England", "Scotland"],
 "FRA": ["France"], "DEU": ["Germany"], "ITA": [r"\bItaly\b"], "ESP": [r"\bSpain\b"], "NLD": ["Netherlands"],
 "BEL": ["Belgium"], "CHE": ["Switzerland"], "SWE": ["Sweden"], "DNK": ["Denmark"], "NOR": ["Norway"],
 "AUS": ["Australia"], "CAN": ["Canada"], "JPN": ["Japan"], "KOR": ["South Korea", "Republic of Korea"],
 "TUR": ["Turkey", "T[uü]rkiye"], "ISR": ["Israel"], "IRQ": [r"\bIraq\b"], "PRT": ["Portugal"],
}
del C["AFR"]
NAMES = {"COD": "Democratic Republic of the Congo", "COG": "Republic of the Congo", "CIV": "Côte d'Ivoire",
         "TZA": "Tanzania", "GMB": "The Gambia", "GIN": "Guinea", "GNB": "Guinea-Bissau", "PNG": "Papua New Guinea",
         "SDN": "Sudan", "LAO": "Laos", "NER": "Niger", "MLI": "Mali", "TGO": "Togo", "IND": "India", "CHN": "China",
         "USA": "United States", "GBR": "United Kingdom", "PER": "Peru", "IRN": "Iran", "IRQ": "Iraq", "OMN": "Oman",
         "ITA": "Italy", "ESP": "Spain", "VNM": "Viet Nam", "STP": "Sao Tome and Principe", "CIV": "Côte d'Ivoire"}
RX = {iso: [re.compile(p if p.startswith(("\\b", "(?")) else r"\b" + p + r"\b", re.I if iso not in ("USA", "GBR", "COD") else 0) for p in ps] for iso, ps in C.items()}


def detect(text):
    hits = []
    if not text:
        return hits
    for iso, rxs in RX.items():
        for rx in rxs:
            m = rx.search(text)
            if m:
                hits.append((iso, m.group(0)))
                break
    isos = {h[0] for h in hits}
    if "COD" in isos and not re.search(r"(?<!Democratic )Republic of (?:the )?Congo|Congo-Brazzaville", text, re.I):
        hits = [h for h in hits if h[0] != "COG"]
    return hits


def load_studies():
    st = {}
    p = os.environ.get("DATAVERSE_STUDIES") or os.path.join(OUT_DIR, "dataverse-studies-subset.tsv")
    tsv_rows = 0
    if os.path.exists(p):
        with open(p, newline="", encoding="utf-8", errors="replace") as fh:
            r = csv.DictReader(fh)
            try:
                for row in r:
                    if row.get("study_id"):
                        st[row["study_id"]] = {"study_id": row["study_id"], "doi": row.get("doi") or None,
                                               "pubmed_id": row.get("pubmed_id") or None,
                                               "population": row.get("population_string"),
                                               "study_type": row.get("study_type") or None, "_source": "dataverse_studies_tsv"}
                        tsv_rows += 1
            except csv.Error:
                pass
    api = json.load(open(os.path.join(WORK, "studies_api.json")))
    for f in os.listdir(OUT_DIR):
        if f.startswith("studies_") and f.endswith(".json"):
            r = json.load(open(os.path.join(OUT_DIR, f)))["response"]
            if "study_id" in r: api.setdefault(r["study_id"], dict(r, _source="api"))
    st.update(api)  # API record wins
    return st, tsv_rows


def main():
    a = json.load(open(os.path.join(WORK, "assoc.json")))
    assoc = a["assoc"]
    studies, tsv_rows = load_studies()
    out = []
    for k, r in sorted(assoc.items()):
        n1, n2 = r.get("variable_1_name"), r.get("variable_2_name")
        sp = [f for f, n in (("variable_1_name", n1), ("variable_2_name", n2)) if is_sp_name(n)]
        dh = [f for f, n in (("variable_1_name", n1), ("variable_2_name", n2)) if is_dhps_name(n)]
        if not sp and not dh:
            continue
        if dh:
            if any(EXPLICIT_540.search(x or "") for x in (n1, n2)):
                kind = "k540e_haplotype"; k540 = "explicit_540E_text_in_variable_name"
            elif any(QUINT.search(x or "") for x in (n1, n2)) and not re.search(r"436A437G", (n1 or "") + (n2 or "")):
                kind = "other_dhps"; k540 = "quintuple/sextuple named without explicit 540E (composition not stated in Graph text)"
            else:
                kind = "other_dhps"; k540 = None
        else:
            kind = "sp_outcome"; k540 = None
        s = studies.get(r.get("study_id"))
        countries = []
        for field, text in (("association.variable_1_name", n1), ("association.variable_2_name", n2),
                            ("study.population", (s or {}).get("population"))):
            for iso, mt in detect(text):
                countries.append({"iso3": iso, "name": NAMES.get(iso, C[iso][0].replace("\\b", "")), "matched_text": mt,
                                  "field": field, "source": "graph_record"})
        sp_names = [r[f] for f in sp]
        rec = {
            "system_id": r["system_id"], "kind": kind, "k540e_basis": k540,
            "sp_variable_fields": sp, "dhps_variable_fields": dh,
            "sp_variable_looks_like_uptake_measure": bool(sp) and all(UPTAKE.search(n) for n in sp_names),
            "variable_1": {"id": r.get("variable_1_id"), "name": n1, "concept_id": r.get("variable_1_concept_id")},
            "variable_2": {"id": r.get("variable_2_id"), "name": n2, "concept_id": r.get("variable_2_concept_id")},
            "statistic_type": r.get("statistic_type"), "system_statistic_type": r.get("system_statistic_type"),
            "statistic_value": r.get("statistic_value"), "ci_lower": r.get("ci_lower"), "ci_upper": r.get("ci_upper"),
            "ci_level": r.get("ci_level"), "p_value": r.get("p_value"), "p_value_equality": r.get("p_value_equality"),
            "sample_size": None, "direction": None,
            "study_id": r.get("study_id"), "pubmed_id": r.get("pubmed_id") or (s or {}).get("pubmed_id"),
            "doi": (s or {}).get("doi"), "title": None,
            "study": s, "study_record_source": (s or {}).get("_source"),
            "retrieved_via": r.get("_via"),
            "countries": countries,
        }
        out.append(rec)
    json.dump(out, open(os.path.join(OUT_DIR, "sp_findings.json"), "w"), indent=1, ensure_ascii=False)
    # summary numbers
    by = defaultdict(list)
    for x in out: by[x["kind"]].append(x)
    print("tsv rows parsed", tsv_rows, "| vars skipped (budget):", len(a["vars_skipped"]))
    for kind, xs in by.items():
        with_c = [x for x in xs if x["countries"]]
        no_study = [x for x in xs if not x["study"]]
        print(kind, len(xs), "with country:", len(with_c), "no study record:", len(no_study),
              "| in var name:", sum(any(c["field"].startswith("association") for c in x["countries"]) for x in xs),
              "| in population:", sum(any(c["field"] == "study.population" for c in x["countries"]) for x in xs),
              "| uptake-like:", sum(x["sp_variable_looks_like_uptake_measure"] for x in xs))
    return out


if __name__ == "__main__":
    main()
