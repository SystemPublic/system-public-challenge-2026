"""Hand coding of the findings in the 15 most balanced split relationships and the two tested ones.

Each relationship gets a substantive question, and each finding one code, assigned from the variable
names and, where they were not enough, the PubMed abstract (data/derived/graph/splits/abstracts.json):
  c  consistent with the stated direction once the names are read (the stored sign may be either)
  a  against it
  x  not about the question: another construct under the same concept, a grounding or extraction error
Codes are keyed by PubMed id; where one study has findings coded differently, by stored sign.
Output: data/derived/graph/splits/coded_findings.json and moderators.csv.
"""
import csv, json
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/derived/graph/splits"

C = {
 "mzjKzH-tab|esiPwRl8Y5": dict(label="neighbourhood features → diabetes",
   question="an adverse neighbourhood feature goes with more diabetes (a favourable one with less)", diagnosis="umbrella exposure",
   moderator="The concept 'residence characteristics' holds deprivation, problems and car dependence (stored +) and green space, walkability and resources (stored -). No study disagrees with another.",
   default="c", codes={"17503110": "x", "26428459": "x", "38127347": "x", "26198685": "x"}),
 "qt5dLX7UCR|yvzAi6nThy": dict(label="social isolation → cognition",
   question="social isolation goes with worse cognition", diagnosis="outcome polarity",
   moderator="'Cognitive impairment' (stored +) and 'cognitive function' (stored -) are grounded to one concept. All 18 findings agree.",
   default="c", codes={}),
 "qKoYi3_qt5|DU5dF5vxkA": dict(label="school → binge drinking",
   question="a better school environment or a school programme goes with less binge drinking", diagnosis="umbrella exposure",
   moderator="'School' holds prevention programmes, alcohol policy and connectedness (protective) together with years of schooling, suspension, private and business schools, low grades and non-attendance, which are six other exposures.",
   default="x", codes={"17506149": "c", "27090500": "c", "30406009": "c", "31499244": "c", "34507060": "c", "30269908": "c"}),
 "YsxVx5JJqR|vUwiaNEBVo": dict(label="rural residence → patient survival",
   question="rural residence goes with worse survival after diagnosis", diagnosis="real, moderated",
   moderator="Worse in lung, colorectal, medulloblastoma and drug-resistant TB cohorts (France, US, Lithuania); better in young small-cell lung cancer (California) and oesophagogastric cancer (north-east Scotland); explained by tract income in the colorectal study. Disease, health system and adjustment for income separate the sides. The outcome is grounded to 'survival skill', and PMID 17933419 is stored with the wrong sign.",
   default="c", codes={"29191590": "a", "35606259": "a", "31285671": {"+": "a", "-": "c"}, "31365445": "x", "20446997": "x", "21450010": "c"}),
 "_2dhcsFISl|YtQ5lW8obL": dict(label="walking → body mass index",
   question="more walking goes with lower body mass index", diagnosis="extraction errors",
   moderator="Two of the six positive findings are errors (PMID 19782925, an inverse correlation stored as +0.75; PMID 31893356, an odds ratio of 0.65 stored as a coefficient) and three are non-significant before-after differences.",
   default="c", codes={"22870410": "a", "27600387": "a", "33362350": "x", "33941196": "x"}),
 "4FaXcuNJRt|vUwiaNEBVo": dict(label="temperature → 'survival skill'",
   question="none", diagnosis="grounding error",
   moderator="Body temperature of patients, horses and cats, grounded to ambient 'temperature'; survival grounded to 'survival skill'.",
   default="x", codes={}),
 "_2dhcsFISl|vsSdYqnwOM": dict(label="walking → hip fracture",
   question="more walking, or better walking ability, goes with fewer hip fractures", diagnosis="exposure polarity",
   moderator="Walking difficulty and needing help (stored +) and hours walked (stored -) are one concept.",
   default="c", codes={"16510325": "x", "24284784": "x"}),
 "p6FsFfmYfe|QPxlNKv3zV": dict(label="immigrant status → mortality",
   question="immigrants have lower mortality than the native-born", diagnosis="real, moderated",
   moderator="Lower among immigrants in Canadian cancer and stroke cohorts and Swedish diabetes cohorts, with the advantage shrinking with years since arrival and gone in the second generation; higher among Soviet immigrants to Israel except those with high income, and after heart failure admission. Income, origin and time since arrival separate the sides.",
   default="c", codes={"25082349": "x", "41348505": "x", "40038881": "a", "33294584": {"+": "a", "-": "c"}, "28605254": {"+": "x", "-": "c"}}),
 "gHk1te7A9Z|UBLYDhO7ul": dict(label="humidifier → humidity",
   question="none", diagnosis="not an urban exposure",
   moderator="Bench comparisons of respiratory humidifiers; the sign is the order of the two devices.",
   default="x", codes={}),
 "_2dhcsFISl|2Uj74diYJP": dict(label="walking → frailty",
   question="more walking goes with less frailty", diagnosis="exposure polarity",
   moderator="Slow walking and walking aids (stored +) against walking exercise (stored -). One positive finding is a housing exposure, living in a walk-up building (odds ratio 2.02 for frailty), grounded to 'walking'.",
   default="c", codes={"29351629": "x", "28285311": "x"}),
 "qKoYi3_qt5|Beh6MhlW0g": dict(label="school → menstrual hygiene",
   question="private, urban or higher-grade schooling goes with better menstrual hygiene practice", diagnosis="outcome and exposure polarity",
   moderator="'Poor practice' and 'good practice', 'public' and 'private', are grounded alike. Four rows are two results of PMID 36194593 stored twice.",
   default="c", codes={"35978966": "x", "38361840": "x"}),
 "qKoYi3_qt5|PDDW6UukdU": dict(label="school → smoker",
   question="a school programme or good school adjustment goes with less smoking", diagnosis="umbrella exposure",
   moderator="Three positive findings are loss to follow-up among tuberculosis patients with little schooling.",
   default="c", codes={"35365112": "x"}),
 "2gR7THM-gS|dPeET-pgVN": dict(label="neighbourhood safety → physical activity",
   question="a neighbourhood perceived as safe goes with more physical activity", diagnosis="exposure polarity",
   moderator="'Anxiety about safety' and 'neighbourhood challenges' (stored -) against 'perceived safety' (stored +). Two findings remain against, one of them daytime crime safety in Nigeria.",
   default="c", codes={"22520066": {"+": "c", "-": "a"}, "28923051": "a"}),
 "bIwjlkmcHV|zep3Q7Phhu": dict(label="poverty → HPV vaccination",
   question="poorer adolescents, or adolescents in poorer areas, are more often vaccinated against HPV", diagnosis="real, moderated",
   moderator="US adolescents below the poverty line or in high-poverty areas are more often vaccinated (free vaccine through the Vaccines for Children programme); women aged 18 to 26 below the poverty line less often complete the series, and near-poor girls less often start. Age group, and with it who pays, separates the sides.",
   default="c", codes={"23508594": "a", "22257616": "a"}),
 "OI_Yok9JP4|_Oa_0jWALE": dict(label="noise → mental health",
   question="noise goes with worse mental health", diagnosis="outcome polarity",
   moderator="'Poor mental health' (stored +) and a mental health score (stored -). The one positive coefficient on the score (PMID 35466022) is for a decrease in noise.",
   default="c", codes={}),
 "4FaXcuNJRt|EAshH_Ko3h": dict(label="temperature → asthma (tested in NYC)",
   question="colder days bring more asthma visits or admissions (short-term effect of temperature level)", diagnosis="exposure polarity and three exposures in one",
   moderator="16 of 17 short-term level findings say colder is worse; they are stored + because the variable is 'low temperature' or 'cold (5th percentile)'. Nine findings are about day-to-day change, where season decides the sign, and three compare climates.",
   default="c", codes={"31651344": "a", "21432566": "x", "33230642": "x", "34599899": "x", "36435499": "x", "23035136": "x",
                        "29529393": "x", "7889426": "x", "14982513": "x", "32213400": "x"}),
 "4FaXcuNJRt|DZBybMvxDI": dict(label="temperature → COVID-19 (tested in NYC)",
   question="higher temperature goes with less COVID-19 transmission", diagnosis="real, moderated by design",
   moderator="13 of the 22 findings against are unadjusted correlations of temperature with case counts over the first months of 2020; 13 of the 20 consistent findings come from models of transmission with lags or controls. Three rows stored + are negative in substance and one is body temperature.",
   default=None, codes={"34189495": "c", "34966171": "c", "35257688": "c", "34375443": "x"}),
}

def main():
    F = json.loads((OUT / "findings.json").read_text())
    sp = pd.read_csv(OUT / "splits.csv").set_index("relationship_id")
    coded, rows = {}, []
    for rid, m in C.items():
        fs = []
        for f in F[rid]:
            if f["direction"] not in ("+", "-"): continue
            k = m["codes"].get(str(f["pmid"]), m["default"])
            if isinstance(k, dict): k = k[f["direction"]]
            if k is None:  # temperature and COVID-19: the stored sign is the code unless listed
                k = "c" if f["direction"] == "-" else "a"
            fs.append({**f, "code": k})
        coded[rid] = {"label": m["label"], "question": m["question"], "diagnosis": m["diagnosis"], "findings": fs}
        n = lambda k, sig=False: sum(1 for f in fs if f["code"] == k and (f["significant"] or not sig))
        s = sp.loc[rid]
        rows.append({"relationship_id": rid, "source": s.source, "target": s.target, "label": m["label"],
                     "stored_pos": int(s.pos), "stored_neg": int(s.neg), "n_studies": int(s.n_studies),
                     "diagnosis": m["diagnosis"], "question": m["question"],
                     "consistent": n("c"), "against": n("a"), "excluded": n("x"),
                     "consistent_sig": n("c", True), "against_sig": n("a", True),
                     "studies_against": len({f["study_id"] for f in fs if f["code"] == "a"}),
                     "moderator": m["moderator"]})
    (OUT / "coded_findings.json").write_text(json.dumps(coded, indent=0))
    with open(OUT / "moderators.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['label'][:45]:45s} stored +{r['stored_pos']}/-{r['stored_neg']}  coded c{r['consistent']} a{r['against']} x{r['excluded']}  sig c{r['consistent_sig']} a{r['against_sig']}  {r['diagnosis']}")
    cov = coded["4FaXcuNJRt|DZBybMvxDI"]["findings"]
    corr = lambda f: str(f["stat"]).startswith(("pearson", "spearman"))
    print("covid: against raw-corr", sum(corr(f) for f in cov if f["code"] == "a"), "of", sum(f["code"] == "a" for f in cov),
          "; consistent raw-corr", sum(corr(f) for f in cov if f["code"] == "c"), "of", sum(f["code"] == "c" for f in cov))

if __name__ == "__main__":
    main()
