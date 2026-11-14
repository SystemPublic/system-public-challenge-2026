"""Register the concordance-matrix procedure before any city correlation is computed."""
import sys

import pandas as pd

import common as C

sys.path.insert(0, str(C.ROOT))
from concord import claims  # noqa: E402

L = pd.read_csv(C.OUT / "literature_signs.csv")
q = L[L["qualifies"]]
seen = [("asthma_adult", "no2"), ("asthma_adult", "pm25"), ("asthma_adult", "cockroaches"), ("asthma_adult", "poverty"), ("asthma_adult", "asthma_child")]
rec = {
    "id": "graph-concordance-matrix",
    "kind": "confirmation",
    "statement": ("Across New York City's 42 UHF neighbourhoods, the sign of the correlation between two published indicators matches the "
                  "majority sign of the System Public Graph's findings for the same pair of concepts more often than chance, for the pairs "
                  "on which the graph holds at least 3 studies and at least 80% sign consistency."),
    "graph_evidence": [{
        "concepts": "80 concepts mapped to 48 of 56 city indicators (data/derived/graph/concordance/indicator_concepts.csv)",
        "n_findings": int(L["n_findings"].sum()), "n_studies": None,
        "direction": f"{int((q['lit_sign'] > 0).sum())} of {len(q)} qualifying pairs have a positive literature sign after polarity",
        "summary": (f"Of 1,540 indicator pairs, 1,225 have a concept at both ends, {int((L['n_findings'] > 0).sum())} have at least one finding, "
                    f"{int((L['n_studies_signed'] >= 3).sum())} have signed findings from at least 3 studies and {len(q)} of those have at least 80% of "
                    "signed findings on one side (data/derived/graph/concordance/literature_signs.csv, written before this registration; "
                    "API v1.0, 12 Nov 2026, associations not filtered against the Dataverse CSV because no local copy exists on this machine)."),
        "pubmed_ids": [],
    }],
    "literature": [],
    "prediction": {
        "direction": "+",
        "magnitude": ("Share of qualifying pairs whose city correlation has the literature's sign: 65% (range 55% to 75%) for the deciding "
                      "correlation, 78% (range 68% to 88%) for the raw correlation. The null is 50%."),
        "support_if": ("The agreement rate of the deciding correlation is at least 60% and above the 97.5th percentile of the null in which "
                       "each indicator's values are shuffled across neighbourhoods independently (2,000 shuffles, poverty held fixed)."),
        "refute_if": "The agreement rate of the deciding correlation is at most 40% and below the 2.5th percentile of the same null.",
    },
    "plan": (
        "Unit: UHF42 neighbourhood (n = 42). Indicators: the 56 in analyses/graph_concordance/indicators.py, fixed before this registration; "
        "EHDP measures use the latest period with at least 40 areas reported, and an indicator with no such period is dropped. Project tables "
        "(shootings, vacant land, modelled noise, population density) are aggregated from tracts to UHF42 by the tract's representative point. "
        "Literature sign: for each pair, all API associations linking any concept of one indicator to any concept of the other, in either "
        "order; a finding is signed when tools/graph_evidence.normalise gives a direction, the statistic is not a group difference and it has no "
        "data-check flag; the sign is multiplied by the two polarities and flipped for each variable name carrying a negation word "
        "(analyses/graph_concordance/graph_signs.py). A pair qualifies with signed findings from at least 3 studies and at least 80% of signed "
        "findings on one side. City sign: Spearman correlation across neighbourhoods, raw, and partialled for poverty (correlation of the "
        "residuals of each indicator's ranks on poverty's ranks). The poverty-partialled correlation decides; for pairs that include poverty the raw "
        "correlation decides. Reported: agreement rate raw and deciding; the area-shuffle null; a 95% bootstrap interval from resampling "
        "neighbourhoods (2,000 draws); a second null that shuffles literature signs among qualifying pairs; the agreement a rule of 'always "
        "positive' would reach, since almost all qualifying literature signs are positive; agreement among pairs with |rho| of at least 0.2 and 0.3; "
        "and the rate with the five previously analysed pairs removed. Individual pairs, including the strongest disagreements and agreements "
        "(ranked by |deciding rho| among qualifying pairs), are exploratory leads and not tests. Pairs with a concept at both ends and no "
        "findings, and indicators with no concept, are listed as gaps. "
        "Disclosure: no city correlation for this matrix was computed before registration and no EHDP value was loaded in this study; only "
        "EHDP metadata (measure names, periods, geographies) was read to choose indicators. The project has already analysed, at UHF42, NO2 and "
        "PM2.5 against asthma ED visits (mob-asthma-pollution: positive after poverty adjustment, interval includes no effect), walking and "
        "cycling to work against obesity (mob-active-commute-obesity, graph-confounders-commute-obesity: negative), commute time against "
        "depression with exercise, obesity and subway access as covariates (commute-time-depression), and rodents, cockroaches and housing "
        "problems against child asthma ED visits (nbhd-rodents-asthma: positive); at tract level vacant land against shootings "
        "(nbhd-vacant-shootings: positive) and modelled noise against 311 complaints; at NTA and community district level green space, "
        f"surface temperature, air conditioning and heat illness (heat claims). Of the {len(q)} qualifying pairs, five overlap pairs whose "
        f"direction the project has seen: {seen}. The registrant also knows from general knowledge that NO2 and traffic are highest in "
        "Manhattan's wealthy core and that most adverse health outcomes in New York follow poverty."),
    "alternatives": [
        "Ecological confounding: neighbourhood correlations reflect who lives where (poverty, age, race, migration), not the individual-level relation in the literature.",
        "Common valence: nearly all qualifying literature signs are positive between two adverse conditions, so agreement may show only that adverse conditions cluster in the same neighbourhoods; the 'always positive' benchmark and the sign-shuffle null measure this.",
        "Extraction and grounding error in the graph (about a fifth of API findings; negations in variable names) biases the literature sign.",
        "Measurement: survey estimates for 42 areas are noisy, and self-reported diagnosis depends on access to care.",
        "Dependence: pairs share indicators, so the effective number of independent pairs is much smaller than the count.",
    ],
    "prior": 0.6,
    "registrant": "Claude (graph discovery study: concordance matrix)",
}
print(claims.register(rec))
