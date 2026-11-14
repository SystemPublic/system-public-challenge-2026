"""Registrations for the commuting claims (written before any NYC values for them were queried).

What had been looked at before writing this file: the System graph CSV (commute-time variables,
analyses/commuting/graph_evidence.py), the PubMed abstracts of the findings relied on, the EHDP
metadata (which measures, periods and geographies exist, not their values), the column list and
description of TLC dataset c5iv-bn4s (not its rows for this question), and the literature.

Note for c5iv-bn4s: mob-crz-traffic (another agent) queried monthly trip counts by zone from this
dataset and reported only CBD versus non-CBD totals. This registrant did not read those rows.
"""
import json
import sys

from concord import claims
from analyses.commuting.common import DER, REGISTRANT

GE = json.loads((DER / "graph_evidence.json").read_text())


def ge(group, note):
    s = GE["summary"][group]
    return {"concepts": f"commute time (variable search) -> {group}", "n_findings": s["n_findings"],
            "n_studies": s["n_studies"], "direction": "+",
            "summary": f"{s['ratios_above_1']} of {s['ratios']} ratio findings above 1. {note}",
            "pubmed_ids": s["pubmed_ids"], "source": "data/derived/commuting/graph_evidence.json"}


COMMUTE = {
    "id": "commute-time-depression",
    "kind": "confirmation",
    "statement": ("Across New York City's 42 UHF neighbourhoods, a longer mean travel time to work goes with a higher "
                  "age-adjusted share of adults with depression, after adjusting for poverty and walking access to the subway."),
    "graph_evidence": [
        ge("mental health", "Abstracts read: PMID 37342827 (Korea, KWCS, n about 50,000): depression OR 1.06 (1.01-1.11) for "
           "30-60 min, 1.23 (1.13-1.33) for 60-120 min, 1.31 (1.09-1.57) for >120 min vs <=30 min. PMID 22039952 (Scania, "
           "Sweden): ORs 1.2-1.6 for poor mental health and low vitality with public-transport commutes >60 min."),
        ge("sleep", "PMID 31890330 (Korea): sleep problems OR about 2 for commutes >50 min. PMID 31836613 (Sweden, "
           "fixed-effects): sleep problems OR 1.16 (1.00-1.35) for >5 h/week among those working >40 h/week."),
        ge("physical inactivity", "PMID 31836613: physical inactivity OR 1.25 (1.03-1.51), same subgroup."),
        {"note": ("The graph has no concept for commuting or commute time; these rows come from variable-name search. "
                  "It holds no finding linking commute time to BMI or obesity. PMID 25501883, which the search also "
                  "returns, measures physical activity during commuting, not commute duration, and is not used.")},
    ],
    "literature": [
        {"citation": "Hoehner CM, Barlow CE, Allen P, Schootman M (2012). Commuting distance, cardiorespiratory fitness, and metabolic risk. Am J Prev Med 42(6):571-578.",
         "doi": "10.1016/j.amepre.2012.02.020", "finding": "Longer commuting distance associated with lower fitness, higher BMI and blood pressure (Texas)."},
        {"citation": "Christian TJ (2012). Trade-offs between commuting time and health-related activities. J Urban Health 89:746-757.",
         "doi": "10.1007/s11524-012-9678-6", "finding": "Each added minute of commuting is associated with less time in physical activity, food preparation and sleep (ATUS)."},
    ],
    "prediction": {
        "direction": "+",
        "magnitude": ("Implied by the individual-level ORs (about 1.06-1.3 for longer commutes, applied to a depression "
                      "prevalence near 10% among workers, who are about 60% of adults): +0.05 to +0.3 percentage points of "
                      "depression per 5 minutes of mean commute. An adjusted slope above +1 point per 5 minutes would be too "
                      "large to be a commute effect and would indicate confounding."),
        "support_if": ("The slope of age-adjusted depression % on mean commute minutes, adjusted for poverty % and subway "
                       "walking access %, is above 0 and its 95% interval (HC3) excludes 0."),
        "refute_if": "The same adjusted slope is below 0 and its 95% interval excludes 0.",
    },
    "plan": ("Exposure: mean one-way travel time to work (minutes), workers 16+ who did not work at home, ACS 2015-2019 "
             "5-year, ZCTA level from the Census API (B08013_001E aggregate minutes / B08303_001E workers), summed to "
             "UHF42 with zcta_to_uhf.csv from github.com/nychealth/EHDP-data at commit 547482b9df589006543e13e8cdf6546e00ed9998. "
             "Secondary exposure, reported only: share of those workers commuting 60 minutes or more (B08303_012E + _013E). "
             "Primary outcome: EHDP indicator 2417, measure 1324, depression (adults), age-adjusted %, CHS 2017-18, UHF42. "
             "Covariates: EHDP 103/221 poverty % (ACS 2015-19) and 2391/1227 % of residents within 1/4 mile of a subway "
             "entrance (2018). Model: OLS, HC3, slope per 5 minutes; n = 42 (fewer if suppressed). Secondary outcomes, "
             "reported and not deciding the verdict: no exercise in past 30 days (100 - EHDP 2060/500, mean of CHS "
             "2017-2019) and obesity (2063/506, 2017-2019). Sensitivity: borough fixed effects; unadjusted slope. "
             "Figure: UHF42 map of mean commute time and binned or partial-regression scatter."),
    "alternatives": [
        "Poverty and income: long commutes in New York are concentrated in lower-income outer-borough neighbourhoods",
        "Transit access: neighbourhoods far from the subway have long bus commutes; the subway-access covariate is meant to absorb this",
        "Composition: age, race and ethnicity, immigrant share and occupation differ between neighbourhoods and are not adjusted",
        "Dilution: commute time describes workers; depression describes all adults, including those not working",
        "Ecological fallacy: a neighbourhood slope need not hold for individuals",
    ],
    "prior": 0.25,
    "registrant": REGISTRANT,
}

FHV = {
    "id": "commute-fhv-subway-distance",
    "kind": "confirmation",
    "statement": ("Outside Manhattan, New York City taxi zones whose residents live farther from a subway or Staten Island "
                  "Railway station have more high-volume for-hire (app) pickups per resident in 2024, after adjusting for "
                  "household income and jobs per resident."),
    "graph_evidence": [
        {"note": ("The System graph has no concept for ride-hailing, taxis or the subway, and 'public transport' links "
                  "to health outcomes only. Variable search finds 7 associations mentioning ride-hail, all from one "
                  "study. The claim therefore rests on transport literature found on the web.")},
    ],
    "literature": [
        {"citation": "Barajas JM, Brown A (2021). Not minding the gap: Does ride-hailing serve transit deserts? J Transport Geography 90:102918.",
         "doi": "10.1016/j.jtrangeo.2020.102918",
         "finding": ("Chicago: after controls, more ride-hail trip ends where rail service is prevalent and fewer where only "
                     "bus serves; ride-hail does not concentrate in transit deserts. This is the rival (complement) direction.")},
        {"citation": "Transit-desert substitution argument (e.g. Schaller Consulting reports for NYC; TLC fact books)",
         "doi": None, "finding": "App trips grew fastest in the outer boroughs, attributed in part to poor transit coverage. Not peer-reviewed."},
    ],
    "prediction": {
        "direction": "+",
        "magnitude": ("Elasticity of 2024 app pickups per resident with respect to population-weighted distance to the "
                      "nearest station: +0.10 to +0.50."),
        "support_if": "The adjusted elasticity on log distance is above 0 and its 95% interval (HC3) excludes 0.",
        "refute_if": "The adjusted elasticity is below 0 and its 95% interval excludes 0 (the complement direction of Barajas and Brown).",
    },
    "plan": ("Unit: TLC taxi zones in the Bronx, Brooklyn, Queens and Staten Island, excluding airports (zones 1, 132, 138), "
             "unknown zones (264, 265) and zones with fewer than 2,000 residents. Outcome: 2024 pickups (12 months) of "
             "industry 'FHV - High Volume' from NYC Open Data c5iv-bn4s, divided by 2020 census population. Exposure: "
             "population-weighted mean straight-line distance (km) from 2020 census tract internal points (Census "
             "Gazetteer 2020) to the nearest station in MTA Subway Stations (data.ny.gov 39hk-dx4f, including SIR); tracts "
             "assigned to zones by internal point in the TLC taxi_zones shapefile. Population: 2020 Census P1_001N by tract. "
             "Covariates: log mean household income (ACS 2019-23 B19025_001E / B11001_001E, summed over tracts) and log jobs "
             "per resident (LEHD LODES8 WAC 2021, all jobs, blocks to tracts). Model: OLS of log pickups per resident on "
             "log distance and covariates, HC3. Sensitivity, reported only: adding share of households with no vehicle "
             "(ACS B08201_002E / _001E), borough fixed effects, drop-offs instead of pickups, all boroughs including "
             "Manhattan, and yellow plus green taxi trips. Figures: zone map of pickups per resident with stations; "
             "binned scatter against distance."),
    "alternatives": [
        "Car ownership: households far from the subway own cars and need fewer app trips (the no-vehicle sensitivity addresses this)",
        "Non-resident demand: pickups count visitors and workers leaving a zone, not only residents (jobs per resident addresses part)",
        "Bus service quality and express buses, not measured",
        "Former livery-cab markets in the Bronx and upper Manhattan, which moved to app platforms",
        "Income: app trips are expensive; poverty and income are correlated with distance in both directions across boroughs",
    ],
    "prior": 0.35,
    "registrant": REGISTRANT,
}

if __name__ == "__main__":
    for rec in (COMMUTE, FHV) if len(sys.argv) < 2 else [r for r in (COMMUTE, FHV) if r["id"] in sys.argv[1:]]:
        print(claims.register(rec))
