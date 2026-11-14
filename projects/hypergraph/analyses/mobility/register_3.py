"""Third registration: active commuting and adult obesity across UHF42 neighbourhoods.

Written after seeing which EHDP periods exist for the indicators, not their values.
"""
import json
from pathlib import Path

from concord import claims
from analyses.mobility.register_1 import REGISTRANT, g

REC = {
    "id": "mob-active-commute-obesity",
    "kind": "confirmation",
    "statement": ("Across New York City's UHF42 neighbourhoods, a higher share of workers who walk or cycle to work "
                  "goes with a lower share of adults with obesity, after adjusting for neighbourhood poverty."),
    "graph_evidence": [
        g("physical activity -> obesity", "dPeET-pgVN|cj7G775u_Q"),
        g("walking -> obesity", "_2dhcsFISl|cj7G775u_Q"),
        {"note": ("The graph's physical activity -> obesity findings are split in sign (the ratio findings mix "
                  "'activity predicts lower obesity' with 'inactivity predicts higher obesity', so the sign of a ratio "
                  "depends on the coding of the exposure). There is no concept for cycling or active commuting; "
                  "variable search finds a few commuting variables (e.g. 'active commuting to/from school', "
                  "'being a non-active commuter').")},
    ],
    "literature": [
        {"citation": "Flint E, Cummins S, Sacker A (2014). Associations between active commuting, body fat, and body mass index: population based, cross sectional study in the United Kingdom. BMJ 349:g4887.",
         "doi": "10.1136/bmj.g4887", "finding": "Men commuting by active or public modes had BMI about 1 kg/m2 lower than car commuters; women about 0.7 kg/m2."},
        {"citation": "Celis-Morales CA et al. (2017). Association between active commuting and incident cardiovascular disease, cancer, and mortality. BMJ 357:j1456.",
         "doi": "10.1136/bmj.j1456", "finding": "Cycle commuting associated with lower CVD incidence and mortality (UK Biobank)."},
    ],
    "prediction": {
        "direction": "-",
        "magnitude": ("Unadjusted slope: -2 to -6 percentage points of adult obesity per 10 points of walk-or-bike "
                      "commute share. Poverty-adjusted: -0.5 to -4 points per 10 points."),
        "support_if": "Poverty-adjusted slope below 0 with a 95% interval below 0.",
        "refute_if": "Poverty-adjusted slope at or above 0 with an interval that excludes -0.5.",
    },
    "plan": ("Data: EHDP (github.com/nychealth/EHDP-data, commit 547482b9df589006543e13e8cdf6546e00ed9998): indicator "
             "2415 commuting modes, measures 1304 (bicycle %) + 1307 (walked %), UHF42, ACS 2015-19; indicator 2063 adult "
             "obesity %, measure 506, UHF42, mean of 2017, 2018 and 2019 (CHS, self-reported BMI); indicator 103 poverty %, "
             "measure 221, UHF42, 2015-19. Model: OLS of obesity % on active-commute % (per 10 points), then adding poverty "
             "%; HC3 standard errors; sensitivity adding borough fixed effects and excluding Manhattan. Figure: scatter of "
             "UHF neighbourhoods coloured by poverty with the fitted adjusted slope and the slope implied by Flint et al. "
             "(about -1 kg/m2 BMI for active commuters, translated to obesity prevalence only qualitatively)."),
    "alternatives": [
        "Income, education and race/ethnicity composition (poverty is the named confounder; others are not measured here)",
        "Density and Manhattan: walking to work is common where jobs are close, which is also where incomes are high",
        "Reverse causation and selection: people with lower BMI choose to walk or cycle, or choose walkable neighbourhoods",
        "Commute mode covers workers only; obesity covers all adults",
    ],
    "prior": 0.5,
    "registrant": REGISTRANT,
}

if __name__ == "__main__":
    print(claims.register(REC))
