"""Register heat-extremes-downturn. Run once, before any count on a day at or above 35 C is read."""
import json
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[2]
pw = json.loads((ROOT / "data/derived/heat_extremes/power.json").read_text())
days = {c: {k: v[k] for k in ("days", "d32_35", "d35_38", "d38p", "d41p", "d44p", "p95", "p99", "mean_38p", "mean_32_35")} for c, v in pw["cities"].items()}

rec = {
    "id": "heat-extremes-downturn",
    "kind": "confirmation",
    "statement": ("In US cities with many very hot days (Phoenix, Tucson, Dallas, Austin), police-recorded aggravated assaults are less frequent on days "
                  "with a maximum temperature of 38 C or more than on days at 32 to 35 C in the same city, year, month and weekday position: "
                  "violence turns down at extreme heat and does not keep rising in a straight line."),
    "graph_evidence": [
        {"relationship_id": ["4FaXcuNJRt|YZku29igbl"], "concepts": ["temperature", "homicide"], "n_findings": 4, "n_studies": 2, "direction": "+",
         "summary": ("Xu et al. 2020 (nine US cities) report a linear temperature-homicide association, significant in Chicago and New York; Rahman et al. 2023 "
                     "(California) report a monotonic association, +4.9% homicide per 5 C of same-day maximum. Both abstracts were read in PubMed on 13 Nov 2026. "
                     "The graph stores three of the four values wrongly (percent stored as odds ratios), as docs/heat.md records; the shape words are from the abstracts."),
         "pubmed_ids": [32738768, 36858215]},
        {"relationship_id": ["temperature|firearm"], "concepts": ["temperature", "firearm"], "n_findings": 1, "n_studies": 1, "direction": "+",
         "summary": ("Lyons et al. 2022 (100 US cities, shootings 2015 to 2020): risk rises almost monotonically with daily maximum temperature, with a local peak "
                     "at the 84th percentile of each city's temperature range (relative risk 1.17, 1.12 to 1.21, against the median). Abstract read 13 Nov 2026. "
                     "This is the only graph finding that describes a peak, and it places it at a percentile of the local climate, not at a fixed temperature."),
         "pubmed_ids": [36525273]}],
    "graph_evidence_note": ("Taken from the concept-level search cached in data/derived/graph/transfer_chicago/temp_violence_studies.json (13 temperature-violence "
                            "relationships, 23 studies, most on suicide and injury). The graph's findings on temperature and violence therefore predict a monotonic "
                            "rise (the refuting result here), with one hint of a percentile-based peak. A wider search of study variable names "
                            "(analyses/heat_extremes/graph_shape.py) was still running when this was registered; its results are reported in docs/heat_extremes.md "
                            "and did not inform the prediction."),
    "literature": [
        {"citation": "Gamble JL, Hess JJ. Temperature and violent crime in Dallas, Texas. West J Emerg Med 2012;13:239-46.", "doi": "10.5811/westjem.2012.3.11746",
         "finding": "Daily aggravated crime in Dallas 1993-1999 rises with daily mean temperature, moderates above 80 F (26.7 C) and turns negative above 90 F (32.2 C) daily mean."},
        {"citation": "Rotton J, Cohn EG. Violence is a curvilinear function of temperature in Dallas: a replication. J Pers Soc Psychol 2000;78:1074-81.", "doi": "10.1037/0022-3514.78.6.1074",
         "finding": "Assault calls in Dallas 1994-1995 are an inverted-U function of temperature in daylight hours and linear at night."},
        {"citation": "Bushman BJ, Wang MC, Anderson CA. Is the curve relating temperature to aggression linear or curvilinear? J Pers Soc Psychol 2005;89:62-6.", "doi": "10.1037/0022-3514.89.1.62",
         "finding": "The Minneapolis inverted U (peak at 74.9 F in 3-hour data) disappears when time of day is controlled; the relation is positive and linear in the evening and night."},
        {"citation": "Stevens HR et al. Hot and bothered? Associations between temperature and crime in Australia. Int J Biometeorol 2019;63:747-62.", "doi": "10.1007/s00484-019-01689-y",
         "finding": "Daily assaults in New South Wales rise with maximum temperature and the rise slows above 30 C; thefts decline above 30 C."}],
    "prediction": {
        "direction": "-",
        "magnitude": ("Downturn hypothesis: pooled rate ratio for days at or above 38 C against days at 32 to 35 C between 0.88 and 0.98. Linear-rise alternative: the "
                      "slope below 35 C carried to the mean temperature of the days at or above 38 C, which is 6 to 9 C above the mean of the reference days; at the "
                      "published slopes of 5 to 15% per 5 C this is a rate ratio of 1.06 to 1.25."),
        "support_if": ("The 95% upper limit of the DerSimonian-Laird random-effects pooled rate ratio over Phoenix, Tucson, Dallas and Austin is below 1.00."),
        "refute_if": ("The 95% lower limit of the same pooled rate ratio is above 1.00 (assaults are still more frequent at 38 C and above than at 32 to 35 C; no downturn)."),
        "otherwise": ("Unsettled: the pooled interval includes 1.00, which is what a plateau gives. The report then says whether the interval excludes the linear "
                      "prediction computed in test.py (linear_alternative), and gives each city's estimate."),
    },
    "plan": (
        "Data, built by analyses/heat_extremes/build.py before this registration. Daily counts of police-recorded aggravated assaults by date of occurrence from each "
        "city's own portal: Phoenix (phoenixopendata.com crime CSV, UCR category AGGRAVATED ASSAULT, distinct incident numbers, Nov 2015 to Nov 2025), Tucson (Tucson Police "
        "reported-crimes feature layers 2018 to 2026, UCR summary ASSAULT, AGGRAVATED, distinct incident numbers), Dallas (dallasopendata.com qv6i-rri7, nibrs_crime beginning "
        "AGG ASSAULT, distinct incident numbers, 2017 on), Austin (data.austintexas.gov fdj4-gpfu, category Aggravated Assault, 2003 on), and for the descriptive curves "
        "Los Angeles (data.lacity.org 63jg-8b9z and 2nrs-mtv8, codes 230, 231, 235, 236, 2010 to 2023), Philadelphia (phl.carto.com incidents_part1_part2, the two "
        "Aggravated Assault codes, by dispatch date, 2006 on), Chicago (ijzp-q8t2, FBI codes 04A and 04B, 2006 on) and New York (qgea-i56i, felony assault ky_cd 106, 2006 to 2025). "
        "Series end 31 Aug 2026 unless stated. Temperature: GHCN-Daily TMAX at Phoenix Sky Harbor USW00023183, Tucson USW00023160, Dallas Love Field USW00013960, Austin Camp "
        "Mabry USW00013958, Los Angeles downtown USW00093134, Philadelphia USW00013739, Chicago Midway USW00014819, Central Park USW00094728.\n"
        "Qualifying cities. A city enters the pooled test with at least 100 days at or above 38.0 C and 100 days at 32.0 to 34.9 C. From temperatures alone "
        "(power.py) these are Phoenix, Tucson, Dallas and Austin. US stations record whole degrees F, so the hot bin is 101 F and above and the reference bin is 90 to 94 F.\n"
        "Model (analyses/heat_extremes/model.py and test.py, committed with this registration). Per city, a negative binomial GLM of the daily count on indicators for "
        "bins of TMAX (below 8, 8-14, 14-20, 20-23, 23-26, 26-29, 29-32, 32-35 as reference, 35-38, 38 and above) with C(dow) + C(month) + C(year) + hol + dom1 + wet, "
        "HC0 standard errors; alpha estimated once per city by maximum likelihood with a linear temperature term. The city estimate is the coefficient of the 38-and-above bin. "
        "The four log rate ratios are pooled by DerSimonian-Laird random effects; the pooled 95% interval decides the verdict. No resampling and no seed are involved.\n"
        "Registered sensitivity, reported and not deciding: year-by-month strata in place of month and year; May to September only; without 2020 and 2021; the steps "
        "35-38, 38-41 and 41-and-above each against 32-35; the fixed-effect pool; the linear prediction from the slope below 35 C.\n"
        "Planned description, not deciding (analyses/heat_extremes/describe.py): the curve by 3 C bin for all eight cities and pooled; the curve by percentile of each city's "
        "own TMAX distribution; a comparison of stacked models with one curve common to all cities in degrees C against one common in percentiles (the adaptation question); "
        "piecewise-linear slopes below and above 35 C. Exploratory and labelled so: New York shootings by position in runs of days at or above 32 C."),
    "alternatives": [
        "Plateau: the rate stops rising above about 35 C and neither falls nor rises (verdict unsettled).",
        "Linear rise: the rate at 38 C and above exceeds the rate at 32 to 35 C by the amount the slope below 35 C predicts (verdict contested).",
        "Seasonal confounding: days at 38 C and above fall in June to August and reference days in spring and autumn; month and year terms, and the year-by-month sensitivity, address this.",
        "Recording: on very hot days fewer assaults may be reported or recorded on the day; the counts are by date of occurrence, which limits this, and it cannot be excluded.",
        "Adaptation: the turning point may lie at a percentile of the local climate and not at a fixed temperature, in which case Phoenix and Austin would differ at 38 C."],
    "prior": 0.3,
    "registrant": "Claude (agent, heat-extremes study, 13 Nov 2026)",
    "can_it_fail": {
        "source": "data/derived/heat_extremes/power.json, from analyses/heat_extremes/power.py (seed 20261113, 60 simulated series per scenario on the real calendars and temperatures).",
        "days_by_city": days,
        "simulated": pw["pooled"],
        "D": {k: round(v, 1) for k, v in pw.items() if k.startswith("D_")},
        "reading": ("With the larger dispersion tried (alpha 0.15) the pooled standard error is 0.022 on the log scale. The squared standardised distance between a downturn "
                    "of 0.95 and a linear rise of 1.06 is 24, between 0.95 and 1.00 it is 5.3, and between 1.06 and 1.00 it is 6.8; all exceed the rule 8 threshold of 4. "
                    "In simulation a true ratio of 1.00 gives 'unsettled' in 97% of series, a true 0.95 gives 'confirmed' in 40 to 68%, and a true 1.06 gives 'contested' in 63 to 83%. "
                    "The test can therefore return any of the three verdicts."),
    },
    "already_seen": ("Before registering I read, for each city, yearly totals and the overall mean daily count (printed by build.py) and the count of days by temperature. "
                     "I saw seven Chicago daily counts from January 2006 while timing a query. No count was tabulated or modelled against temperature for any of the eight cities' "
                     "aggravated assaults. Known from earlier work in this project, for shootings and not assaults: the New York shootings curve keeps rising to 35 C (docs/heat.md), "
                     "and unadjusted Chicago gunshot cases by 3 C bin (8.9 a day at 27-30 C, 9.5 at 30-33, 8.9 at 33-36). Neither city is in the pooled test. "
                     "test.py was run once on simulated counts to check that it executes."),
    "rules": "Verdict precedence rules 1, 2, 8, 9 and 10 of concord.claims.PRECEDENCE apply; the conditions are on interval bounds.",
}

if __name__ == "__main__":
    print(claims.register(rec))
