"""Write the outcome of graph-concordance-matrix."""
import json
import sys

import common as C

sys.path.insert(0, str(C.ROOT))
from concord import claims  # noqa: E402

R = json.loads((C.OUT / "results.json").read_text())
X = json.loads((C.OUT / "explore.json").read_text())
d, r = R["deciding"], R["raw"]
src = json.loads((C.OUT / "city_sources.json").read_text())
rec = {
    "id": "graph-concordance-matrix",
    "verdict": "confirmed",
    "city_effect": {"label": "Share of 109 qualifying indicator pairs whose poverty-partialled Spearman correlation across 42 UHF neighbourhoods has the literature's majority sign (interval: bootstrap of neighbourhoods)",
                    "estimate": round(d["agreement"], 3), "lo": round(d["bootstrap_ci95"][0], 3), "hi": round(d["bootstrap_ci95"][1], 3),
                    "scale": "proportion of pairs", "null": 0.5, "n": d["n"]},
    "graph_effect": {"label": "Literature sign: majority sign of signed API findings per pair, at least 3 studies and 80% consistency; 105 of 109 positive", "estimate": None, "lo": None, "hi": None, "scale": "sign", "null": 0},
    "graph_evidence": [
        {"relationship_id": "579 relationships among 80 concepts", "n_findings": 8792, "summary": "data/derived/graph/concordance/graph_findings.csv; per-pair signs in literature_signs.csv"},
        {"pubmed_id": 35232120, "concepts": "nitrogen dioxide | ozone", "check": "abstract confirms r between -0.68 and -0.78; the only correctly extracted NO2-ozone finding among ten"},
        {"pubmed_id": 29156623, "concepts": "nitrogen dioxide | ozone", "check": "graph error: satellite NO2 from the Ozone Monitoring Instrument against ground NO2, grounded to ozone"},
        {"pubmed_id": 17723619, "concepts": "nitrogen dioxide | ozone", "check": "graph error: Pearson r = 1.00 is not in the abstract"},
        {"pubmed_id": 37229603, "concepts": "PM 2.5 | diabetes", "check": "abstract confirms OR 1.31 (1.22-1.41) per IQR; women after childbirth, Taiwan"},
        {"pubmed_id": 36402182, "concepts": "PM 2.5 | diabetes", "check": "graph error: percent changes stored as hazard ratios (0.13, 0.11, -0.30), which reverses the sign"},
        {"pubmed_id": 22950554, "concepts": "traffic-related pollution | mortality rate", "check": "abstract confirms MRR 1.13 (1.04-1.23) per doubling of NO2; Danish cohort"},
        {"pubmed_id": 33957920, "concepts": "nitrogen dioxide | all-cause mortality", "check": "abstract confirms RR 1.005 and 1.024 for the 6th and 10th deciles; US Medicare"},
        {"pubmed_id": 37230219, "concepts": "PM 2.5 | obesity", "check": "abstract confirms OR 1.43 (1.37-1.49) per SD; China Multi-Ethnic Cohort"},
        {"pubmed_id": 34176531, "concepts": "alcohol consumption | Mortality, Premature", "check": "abstract confirms HR 1.17 (1.08-1.26) per 10 g/d; Spanish graduates"},
    ],
    "sources": src + [{"kind": "sysgraph-api", "api_version": "v1.0", "fetched": "2026-11-12", "note": "no version identifier; associations not filtered against the Dataverse CSV",
                       "uncached_requests": C.used()}],
    "prediction_scored": ("hit: predicted 65% (55 to 75) for the deciding correlation and 78% (68 to 88) raw; observed "
                          f"{d['agreement']:.1%} and {r['agreement']:.1%}. The support condition is met ({d['agreement']:.1%} is at least 60% and above the "
                          f"area-shuffle null's 97.5th percentile of {d['perm_null_area_shuffle']['q975']:.1%})."),
    "settle": ("Whether the literature's sign carries information beyond 'adverse conditions occur together' is not settled: a rule of "
               f"'always positive' reaches {X['always_positive_benchmark']['deciding']:.1%}, and the sign-shuffle null gives p = "
               f"{d['perm_null_sign_shuffle']['p_ge_obs']:.2f}. A set of pairs with more negative literature signs (protective exposures with "
               "concepts in the graph), individual-level data, or tract-level outcomes would settle it."),
    "research_needed": [
        {"question": "Do NO2, PM2.5 and traffic relate to mortality, diabetes and birth outcomes in the literature's direction within New York once residential sorting is removed?",
         "data": "geocoded vital statistics or SPARCS records with NYCCAS surfaces; movers", "design": "individual-level cohort or within-neighbourhood contrasts", "priority": "high"},
        {"question": "Is household air conditioning associated with fewer preterm births and infant deaths after adjustment for income and housing type?",
         "data": "NYCHVS microdata linked to birth records by sub-borough; summer births", "design": "season-by-AC interaction", "priority": "medium"},
        {"question": "Which of the 948 concept pairs without findings are unstudied and which are grounding gaps?",
         "data": "variable-name search of the graph for each pair; a literature search for the 229 pairs with |rho| of at least 0.5", "design": "audit", "priority": "medium"},
    ],
    "figures": ["figures/graph/concordance_matrix.png"],
    "notes": ("Raw agreement " + f"{r['agreement']:.1%} (bootstrap {r['bootstrap_ci95'][0]:.1%} to {r['bootstrap_ci95'][1]:.1%}); deciding {d['agreement']:.1%} "
              f"({d['bootstrap_ci95'][0]:.1%} to {d['bootstrap_ci95'][1]:.1%}); area-shuffle null 95% range {d['perm_null_area_shuffle']['q025']:.1%} to "
              f"{d['perm_null_area_shuffle']['q975']:.1%}. Agreement by kind of pair (deciding): {X['by_kind']}. Without the five previously analysed pairs: "
              f"{X['without_previously_analysed']['deciding']:.1%}. Exploratory: without the negation rule {X['no_negation_rule']['deciding']:.1%} of "
              f"{X['no_negation_rule']['n']} pairs; partialling population density as well as poverty {X['partial_poverty_and_density']['agreement']:.1%} of "
              f"{X['partial_poverty_and_density']['n']}. Correction to the registration text: 50 of the 56 indicators have a concept, not 48. "
              "The bootstrap interval is not centred on the estimate because resampling neighbourhoods with replacement creates ties. "
              "Several EHDP measures have no recent UHF42 release (pedestrian injuries and heat ED visits 2014, infant deaths 2013, housing "
              "conditions 2017, tree shade 2014, walkability 2011). Traffic volume is published as vehicle miles without an area denominator. "
              "The negation rule has false positives ('non-cystic fibrosis', 'compared to lowest quartile'). Individual pairs are exploratory."),
}
print(claims.outcome(rec))
