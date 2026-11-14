"""The map of heat, medicines and chronic conditions: graph records read against their PubMed abstracts, and the
main studies outside the graph. Writes data/derived/heat_drugs/map.json and viz/data/heat_drugs.js.

Every finding below was read in its PubMed abstract on 13 November 2026 (cached by abstracts.py in data/cache/pubmed/,
not tracked). `graph` is one of:
  correct   a graph record holds this finding, and its variables and numbers match the abstract
  partial   a graph record holds the numbers, but a qualifier that changes the meaning is lost (drug class, city,
            disease category)
  absent    no graph record was found by the searches in graph.py nor by the targeted searches in the doc
Direction: '+' the drug or condition goes with more harm in heat, '-' with less, '0' interval includes the null.
Graph records judged wrong are listed in WRONG and are not drawn.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data/derived/heat_drugs"

NODES = [  # id, label, kind, mechanism (one line)
    ("antipsychotic", "Antipsychotics", "drug", "Impair sweating and central thermoregulation; blunt thirst and the sense of heat."),
    ("anticholinergic", "Anticholinergics", "drug", "Block sweating."),
    ("diuretic", "Diuretics", "drug", "Volume and electrolyte loss."),
    ("betablocker", "Beta blockers", "drug", "Limit the rise in cardiac output that moves heat to the skin."),
    ("acei", "ACE inhibitors / ARBs", "drug", "Impair the thirst and renal response to dehydration; kidney injury."),
    ("ssri", "SSRIs", "drug", "Hyponatraemia; may affect central thermoregulation."),
    ("lithium", "Lithium", "drug", "Narrow therapeutic range; dehydration raises the serum level."),
    ("insulin", "Insulin", "drug", "Faster absorption in heat; hypoglycaemia."),
    ("sulfonylurea", "Sulfonylureas", "drug", "Hypoglycaemia when intake falls and kidney function drops."),
    ("sglt2", "SGLT2 inhibitors", "drug", "Osmotic diuresis; volume depletion."),
    ("opioid", "Opioids", "drug", "Sedation, reduced awareness of heat; overdose risk with heat."),
    ("psychotropic", "Psychotropics, any", "drug", "Class not separated in the study."),
    ("anymed", "Other or any medication", "drug", "Number of medicines, antihypertensives."),
    ("schizophrenia", "Schizophrenia", "condition", "Illness and its treatment both reduce heat defence."),
    ("mental", "Mental illness, any", "condition", "Isolation, reduced self-care, medicines."),
    ("diabetes", "Diabetes", "condition", "Impaired sweating and skin blood flow; dehydration."),
    ("dementia", "Dementia", "condition", "Reduced awareness and help-seeking."),
    ("kidney", "Kidney disease", "condition", "Heat reduces renal blood flow; dehydration injures the kidney."),
]

F = []


def f(node, cite, pmid, design, outcome, measure, est, lo, hi, graph, note="", interaction=False):
    if est is None:
        d = "+" if "increased" in note else "0"
    elif lo is not None and hi is not None:
        d = "+" if lo > 1 else "-" if hi < 1 else "0"
    else:
        d = "+" if est > 1 else "-" if est < 1 else "0"
    F.append({"node": node, "cite": cite, "pmid": pmid, "design": design, "outcome": outcome, "measure": measure,
              "est": est, "lo": lo, "hi": hi, "dir": d, "graph": graph, "note": note, "interaction": interaction})


# ---- drugs
f("antipsychotic", "Martin-Latry 2007", 17513091, "case-control", "ED admission for heat-related pathology, France, August 2003", "OR", 4.6, 1.9, 11.2, "partial",
  "The graph record names the exposure 'use of psychotropic drugs'; the abstract gives 4.6 for antipsychotics.")
f("antipsychotic", "Layton 2020", 33301532, "self-controlled case series", "heat-related hospitalisation, Medicare 65+, June-August 2007-2012", "RR", 1.37, 1.14, 1.66, "absent",
  "Antipsychotic use without a heatwave. Heatwaves raised the rate 21-33% across drug classes; no meaningful synergy between heatwaves and medicines.")
f("antipsychotic", "Chen 2025", 41044101, "case-control", "death during the 2021 British Columbia heat dome, people with schizophrenia", "OR", 2.43, 1.52, 4.01, "absent",
  "Any antipsychotic dispensed in the 30 days before; two or more antipsychotics OR 4.05 (2.41-6.98).", True)
f("antipsychotic", "Kalisch Ellett 2016", 27378245, "sequence symmetry", "hospital admission for dehydration or heat-related illness after starting a medicine, Australian veterans", "ASR", None, None, None, "absent",
  "Significantly increased after starting antipsychotics; the class ratio is not in the abstract (range 1.17-2.79 across classes).")
f("anticholinergic", "Martin-Latry 2007", 17513091, "case-control", "ED admission for heat-related pathology, France, August 2003", "OR", 6.0, 1.8, 19.6, "partial",
  "The graph record names the exposure 'use of psychotropic drugs'; the abstract gives 6.0 for anticholinergic drugs.")
f("anticholinergic", "Layton 2020", 33301532, "self-controlled case series", "heat-related hospitalisation, Medicare 65+", "RR", 1.16, 1.00, 1.35, "absent", "Anticholinergic use without a heatwave.")
f("anticholinergic", "Kalisch Ellett 2016", 27378245, "sequence symmetry", "admission for dehydration or heat-related illness", "ASR", None, None, None, "absent", "Significantly increased after starting anticholinergic agents.")
f("diuretic", "Layton 2020", 33301532, "self-controlled case series", "heat-related hospitalisation, Medicare 65+ with dementia", "RR", 1.54, 1.06, 2.24, "absent",
  "Loop diuretics without a heatwave, dementia subgroup (1.64 in heart failure, 1.84 after myocardial infarction).")
f("betablocker", "Layton 2020", 33301532, "self-controlled case series", "heat-related hospitalisation, Medicare 65+", "RR", None, None, None, "absent", "Beta blockers were not associated.")
f("acei", "Kalisch Ellett 2016", 27378245, "sequence symmetry", "admission for dehydration or heat-related illness", "ASR", 2.79, None, None, "absent",
  "ACE inhibitor with diuretic, the highest of all classes (interval not in the abstract).")
f("ssri", "Kalisch Ellett 2016", 27378245, "sequence symmetry", "admission for dehydration or heat-related illness", "ASR", 1.17, None, None, "absent",
  "SSRIs, the lowest significant class (interval not in the abstract).")
f("insulin", "Visaria 2024", 38060348, "case-crossover", "hypoglycaemia ED visit or admission, insulin users 65+, US Medicare", "OR", 1.38, 1.28, 1.48, "absent",
  "Heat index above the 99th percentile against the 25th-74th. The study is of insulin users only, so it measures heat among users, not a drug-heat interaction.", True)
f("opioid", "Chang 2023", 37897873, "case-crossover", "ED visits for opioid use, California 2005-2019", "OR", 1.041, 1.025, 1.057, "absent",
  "Daily mean temperature, 95th against 50th percentile.", True)
f("psychotropic", "Mangoni 2017", 28796021, "cohort", "hospital length of stay, medical patients 65+ admitted during heat waves", "SHR", 0.89, 0.69, 1.14, "correct",
  "Psychotropic use predicted length of stay in normal weather but not during heat waves.", True)
f("anymed", "Swain 2019", 31842287, "cross-sectional", "self-reported heat illness, Odisha, India, non-slum residents", "aOR", 3.09, 1.15, 8.29, "correct", "'Persons under medication'.")
f("anymed", "Krueger-Kalinski 2001", 11434495, "case-control", "exertional heat illness, long-distance cyclists", "OR", 1.1, 0.8, 1.5, "correct", "Number of current medications that affect heat dissipation.")
f("anymed", "Argaud 2007", 17698677, "cohort", "death after heatstroke, Lyon 2003", "HR", 2.17, 1.17, 4.05, "correct", "Long-term antihypertensive medication.")

# ---- conditions
f("schizophrenia", "Lee 2023", 36938119, "case-control", "death during the 2021 British Columbia heat dome against deaths on the same dates 2012-2020", "OR", 3.07, 2.39, 3.94, "absent",
  "The largest odds ratio of 26 chronic conditions.", True)
f("schizophrenia", "Nori-Sarma 2022", 35195664, "case-crossover", "ED visits for schizophrenia, US adults, extreme-heat days", "IRR", 1.05, 1.03, 1.07, "correct", "", True)
f("schizophrenia", "Tang 2021", 34286435, "time series", "schizophrenia hospitalisations, Hefei, per IQR of excess hourly heat, lag 4", "RR", 1.025, 1.005, 1.046, "correct", "", True)
f("schizophrenia", "Shiloh 2007", 17234387, "cohort", "symptom score (PANSS) of inpatients, all on antipsychotics, against ward temperature", "r", None, None, None, "correct",
  "r = 0.52 to 0.64 in schizophrenia patients (six graph records); increased symptoms with ward temperature; no correlation in other psychoses.", True)
f("mental", "Stafoggia 2006", 16570026, "case-crossover", "death at 30 C against 20 C apparent temperature, four Italian cities", "OR", 1.69, 1.39, 2.07, "correct", "Previous psychiatric disorder; all residents 1.34.", True)
f("mental", "Kaiser 2001", 11563746, "case-control", "heat-related death, Cincinnati 1999 heat wave", "OR", 14.0, 1.8, 633, "correct",
  "17 cases; decedents with a psychotropic prescription may not have been taking it.")
f("mental", "Nori-Sarma 2022", 35195664, "case-crossover", "ED visits for any mental-health condition, extreme-heat days", "IRR", 1.08, 1.07, 1.09, "correct", "", True)
f("mental", "Yoo 2021", 33751353, "time series", "ER visits for mental disorders, Erie and Niagara counties, NY, heat", "RR", 1.16, 1.06, 1.27, "correct", "", True)
f("mental", "Page 2012", 22661680, "time series", "death per 1 C above the 93rd percentile, English primary-care patients with psychosis, dementia or substance misuse", "RR", 1.049, 1.020, 1.078, "absent", "", True)
f("mental", "Bark 1998", 9712220, "cohort", "death during heat waves, New York State psychiatric hospital patients, 1950-1984", "RR", 2.0, None, None, "absent",
  "Twice the general population's risk; highest in the 1970s when antipsychotic doses were high; equal by 1980-84.", True)
f("diabetes", "Moon 2021", 33515577, "meta-analysis", "death of people with diabetes during heatwaves", "RR", 1.18, 1.13, 1.25, "correct", "", True)
f("diabetes", "He 2020", 32000339, "case-crossover", "diabetes deaths, Thailand, 90th percentile heat", "OR", 1.10, 1.06, 1.14, "correct", "", True)
f("diabetes", "Xu 2020", 31869688, "case-crossover", "ED visits for acute kidney injury, Queensland, people with diabetes", "OR", 2.51, 1.91, 3.30, "correct", "", True)
f("diabetes", "Wettstein 2024", 38250197, "time series", "heat-related illness during the 2021 heat dome, Seattle ED patients", "IRR", 3.19, 1.47, 6.94, "correct", "Pre-existing diabetes.")
f("diabetes", "Remigio 2019", 31397862, "case-crossover", "death of dialysis patients with diabetes, Boston, Philadelphia and New York, extreme heat events", "RR", 1.83, 1.51, 2.21, "correct", "", True)
f("dementia", "Byun 2025", 40795076, "case-crossover", "hospital admission for dementia, South Korea, 99th against 50th percentile temperature", "RR", 1.36, 1.19, 1.57, "absent",
  "People with dementia also had larger heat effects on all-cause admission and death.", True)
f("kidney", "Lee 2023", 36938119, "case-control", "death during the 2021 British Columbia heat dome", "OR", 1.36, 1.18, 1.56, "absent", "Chronic kidney disease.", True)
f("kidney", "Zhang 2013", 23168533, "case-crossover", "direct heat-related admission, Adelaide 2009 heatwave", "OR", 1.72, 1.07, 2.94, "correct", "Having renal problems.", True)
f("kidney", "Xu 2020", 31869688, "case-crossover", "ED visits for acute kidney injury, people with chronic kidney disease", "OR", 2.59, 1.89, 3.55, "absent",
  "The graph holds this study's diabetes estimate, and two other estimates with wrong labels, but not this one.", True)
f("kidney", "Remigio 2019", 31397862, "case-crossover", "hospital admission of dialysis patients, three US cities including New York", "RR", 1.27, 1.13, 1.43, "correct", "", True)
f("kidney", "Remigio 2019", 31397862, "case-crossover", "death of dialysis patients", "RR", 1.31, 1.01, 1.70, "correct", "", True)
f("kidney", "Bobb 2014", 25536257, "time series", "admission for renal failure, Medicare, heat wave against matched days", "RR", 1.14, 1.06, 1.23, "absent", "Kidney failure as the outcome of heat.", True)
f("kidney", "Borg 2017", 29078794, "time series", "ED admission for chronic kidney disease per 1 C daily minimum, Adelaide", "IRR", 1.017, 1.001, 1.033, "partial",
  "Seven graph records hold the seven category estimates, each labelled only 'eight renal disease categories'.", True)

# graph records read and judged wrong (index into graph.json associations, where found there)
WRONG = [
    {"cite": "Thayakaran 2024", "pmid": 37280056, "record": "ACE inhibitor prescriptions during periods of lower ambient temperature -> serum potassium, RR 1.33",
     "why": "The abstract gives 1.33 for ACE inhibitor prescribing per unit of potassium; no heat outcome."},
    {"cite": "Goedel 2019", "pmid": 31205291, "record": "average ambient temperature on the day of fatal opioid overdose, OR 1.3",
     "why": "1.3 is for COLD weather (0 C against 11 C over seven days); the record loses the sign."},
    {"cite": "Schmeltz 2017", "pmid": 29036206, "record": "heat-related illness hospitalisation: schizophrenia RR 1.0; dementia RR 1.0; drug abuse RR 1.0; age 40+ RR 1.0",
     "why": "Four records hold 1.0 where the abstract says these were associated with more heat-illness hospitalisation and gives no number.", "n": 4},
    {"cite": "Yoo 2021", "pmid": 33751353, "record": "extreme temperatures (both heat and cold) -> mental-disorder ER visits, RR 1.25", "why": "1.25 is the cold effect."},
    {"cite": "Yang 2016", "pmid": 26580729, "record": "ambient temperature -> diabetes mortality, RR 1.20 (1.12-1.30)", "why": "1.20 is the low-temperature effect; heat is 1.29 (1.11-1.47)."},
    {"cite": "Xu 2020", "pmid": 31869688, "record": "'males aged >64 with pre-existing diseases' OR 2.48; 'hourly temperature increases' OR 2.21",
     "why": "2.48 is for males and 2.21 for heart failure; the labels are mixed.", "n": 2},
    {"cite": "Thongprayoon 2020", "pmid": 32679822, "record": "chronic kidney disease -> in-hospital death after heat stroke OR 3.5 (and the same 3.5 on two other records)",
     "why": "The abstract gives no such number; CKD was a risk factor for kidney injury, not a stated odds of death.", "n": 3},
    {"cite": "Sun 2021", "pmid": 34819309, "record": "extreme heat -> ED visits for renal disease, RR 30.4", "why": "30.4% excess risk, i.e. RR 1.30, stored as 30.4."},
]
PARTIAL_EXTRA = [  # partial records not drawn as separate findings
    {"cite": "Remigio 2019", "pmid": 31397862, "n": 2, "why": "1.15 and 1.45 are Boston-only estimates; the records omit the city."},
    {"cite": "Borg 2017", "pmid": 29078794, "n": 6, "why": "The other six category estimates, each without its category."},
    {"cite": "Martin-Latry 2007", "pmid": 17513091, "n": 1, "why": "Anxiolytics OR 2.4 under 'use of psychotropic drugs'."},
]
CORRECT_EXTRA = [  # correct records read but not drawn
    {"cite": "Moon 2021", "n": 1, "why": "morbidity RR 1.10"}, {"cite": "Remigio 2019", "n": 2, "why": "COPD 1.60 and heart failure 1.55 among dialysis patients"},
    {"cite": "Schmeltz 2017", "n": 4, "why": "sex, race and insurance risk ratios"}, {"cite": "Shiloh 2007", "n": 5, "why": "the other five PANSS correlations"},
    {"cite": "Krueger-Kalinski 2001", "n": 1, "why": "duplicate record"}, {"cite": "Li 2022", "n": 1, "why": "heat illness -> later psychiatric disorder, HR 3.85 (reverse direction)"},
    {"cite": "Kim 2019; Bai 2014", "n": 3, "why": "heat -> acute kidney injury and renal admissions (outcome, not modifier)"},
]
LITERATURE_NOT_FOUND = {"lithium": "No study of lithium and ambient heat found in the graph or in a short PubMed search.",
                        "sulfonylurea": "No study found in the graph or in a short PubMed search.",
                        "sglt2": "No epidemiological study found; the PubMed search for SGLT2 and heat returned laboratory papers only."}


def tally():
    drawn = {"correct": 0, "partial": 0}
    for x in F:
        if x["graph"] in drawn:
            drawn[x["graph"]] += 1
    # the six Shiloh records count once in F; add the rest in CORRECT_EXTRA
    correct = drawn["correct"] + sum(c["n"] for c in CORRECT_EXTRA)
    partial = drawn["partial"] + sum(c["n"] for c in PARTIAL_EXTRA)
    wrong = sum(w.get("n", 1) for w in WRONG)
    return {"correct": correct, "partial": partial, "wrong": wrong, "read": correct + partial + wrong,
            "findings_drawn": len(F), "findings_drawn_in_graph": sum(x["graph"] != "absent" for x in F),
            "findings_drawn_absent": sum(x["graph"] == "absent" for x in F)}


def main():
    t = tally()
    out = {"nodes": [{"id": a, "label": b, "kind": c, "mechanism": d} for a, b, c, d in NODES], "findings": F,
           "wrong_records": WRONG, "partial_extra": PARTIAL_EXTRA, "correct_extra": CORRECT_EXTRA,
           "not_found": LITERATURE_NOT_FOUND, "tally": t,
           "graph_search": "analyses/heat_drugs/graph.py, 13 Nov 2026: 463 variables followed, 142 associations kept, 535 uncached requests",
           "graph_api": "System Public Graph API v1.0"}
    DER.mkdir(parents=True, exist_ok=True)
    (DER / "map.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    (ROOT / "viz/data/heat_drugs.js").write_text("window.HEAT_DRUGS = " + json.dumps(out, ensure_ascii=False) + ";\n")
    print(json.dumps(t))


if __name__ == "__main__":
    main()
