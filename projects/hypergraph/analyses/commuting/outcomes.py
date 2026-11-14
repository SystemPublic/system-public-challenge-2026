"""Outcomes for the commuting claims, from the results files written by the analysis scripts."""
import json

from concord import claims
from analyses.commuting.common import DER

c = json.loads((DER / "commute_depression_results.json").read_text())
f = json.loads((DER / "fhv_subway_results.json").read_text())
cr, fr = c["results"], f["results"]
p, q = cr["primary"], fr["primary"]


def fmt(r, k="slope"):
    return f"{r[k]:+.2f} ({r['lo']:+.2f} to {r['hi']:+.2f})"


COMMUTE = {
    "id": "commute-time-depression",
    "verdict": "unsettled",
    "city_effect": {"label": "age-adjusted adult depression, percentage points per 5 min of mean commute, adjusted for poverty and subway access",
                    "estimate": round(p["slope"], 3), "lo": round(p["lo"], 3), "hi": round(p["hi"], 3),
                    "scale": "points per 5 minutes", "null": 0, "n": p["n"]},
    "graph_effect": {"label": "depression OR, 60-120 vs <=30 min commute (PMID 37342827)", "estimate": 1.23, "lo": 1.13,
                     "hi": 1.33, "scale": "odds ratio", "null": 1},
    "sources": c["sources"] + [{"kind": "dataverse", "doi": "doi:10.7910/DVN/7V6JDO", "version": "2.1",
                                 "file": "data/derived/commuting/graph_evidence.json"}],
    "prediction_scored": ("miss: the adjusted slope is negative, " + fmt(p) + " points per 5 minutes, against a predicted "
                          "+0.05 to +0.3. Its interval includes 0, so neither registered condition is met."),
    "settle": ("Individual-level data that hold commute time, depression and income for the same New York residents: "
               "the CHS does not ask about commute time. Adding a commute-time question to the CHS, or linking ACS "
               "microdata (PUMS) commute times to a health outcome at the person level, would settle whether the "
               "research association holds in New York. A neighbourhood comparison cannot: the research-implied "
               "slope (at most +0.3 points per 5 minutes) is smaller than the standard error of this design (about 0.44)."),
    "research_needed": [
        {"question": "Does commute time predict depression or poor sleep among New York workers, net of income?",
         "data": "NYC Community Health Survey with a commute-time item; or ACS PUMS joined to a survey with health outcomes",
         "design": "person-level logistic regression by commute-time band, adjusted for income, age, occupation and borough",
         "priority": "high"},
        {"question": "Why do long-commute neighbourhoods have much more obesity and inactivity than poverty and subway access predict?",
         "data": "CHS 2017-19 (obesity, exercise) with car commuting share, age structure and race/ethnicity by UHF42",
         "design": "registered neighbourhood model adding car-commute share and composition; then a within-person panel elsewhere",
         "priority": "medium"},
        {"question": "The System graph has no concept for commuting or commute time; its 51 findings with a commute-time exposure (38 on sleep, mental health, inactivity or self-rated health) are reachable only by variable search",
         "data": "System Public Graph", "design": "add a commute-time concept and ground these variables to it", "priority": "medium"},
    ],
    "figures": ["figures/commuting/commute_time_depression_uhf42.png"],
    "notes": (
        f"Across 42 UHF neighbourhoods mean one-way commute time (ACS 2015-19) ranges from 25.7 minutes (Greenwich Village-SoHo) to "
        f"50.2 minutes (Rockaways). Adjusted for poverty and subway access, depression changes by {fmt(p)} points per 5 minutes; "
        f"unadjusted {fmt(cr['unadjusted'])}; poverty only {fmt(cr['poverty_only'])}; with borough fixed effects "
        f"{fmt(cr['boro_fe'])}. The share commuting 60 minutes or more gives {fmt(cr['exposure_60plus_per10'])} points per "
        "10 points of share. Manhattan neighbourhoods have short commutes and above-predicted depression, which pulls the "
        "slope down. Secondary outcomes (registered as reported only): no exercise in the past 30 days rises "
        f"{fmt(cr['no_exercise'])} points per 5 minutes and obesity {fmt(cr['obesity'])} points per 5 minutes, both adjusted. "
        "These are far larger than any commute effect the research implies, and they repeat the pattern of "
        "mob-active-commute-obesity: long-commute neighbourhoods are outer, car- and bus-dependent and differ in "
        "composition. They are associations, not tests. The ACS commute data were read from the Census summary files "
        "because the Census API now requires a key; the ZCTA crosswalk matched 214 ZCTAs.")
}

FHV = {
    "id": "commute-fhv-subway-distance",
    "verdict": "contested",
    "city_effect": {"label": "elasticity of 2024 HVFHV pickups per resident with respect to distance to nearest station, adjusted for income and jobs",
                    "estimate": round(q["elasticity"], 3), "lo": round(q["lo"], 3), "hi": round(q["hi"], 3),
                    "scale": "log-log elasticity", "null": 0, "n": q["n"]},
    "graph_effect": None,
    "sources": f["sources"],
    "prediction_scored": ("miss: the elasticity is " + fmt(q, "elasticity") + ", negative with an interval that excludes 0, "
                          "so the registered refute_if is met. The direction is the complement pattern of Barajas and Brown (2021)."),
    "settle": ("The substitution hypothesis is about residents' trips, and zone pickups mix residents with visitors. Trip "
               "records linked to the rider's home (or a travel survey such as the NYC Citywide Mobility Survey with "
               "household car ownership and distance to the subway) would separate two explanations: that app trips are "
               "rarer far from the subway because households there own cars, or that they are rarer because app trips are "
               "mostly made in dense, mixed-use areas whatever the subway access. The no-vehicle sensitivity points to the "
               "first, but it was not the registered test."),
    "research_needed": [
        {"question": "Among households without a car, do app trips rise with distance from the subway?",
         "data": "NYC Citywide Mobility Survey (DOT) trip diaries with home location and vehicle ownership",
         "design": "registered person-level count model of app trips on home-to-station distance, stratified by car ownership",
         "priority": "high"},
        {"question": "Does the positive elasticity after adjusting for no-vehicle share replicate out of sample?",
         "data": "c5iv-bn4s for a year not used here (e.g. 2022), or HVFHV trip records with drop-off at home zones in the evening",
         "design": "new registration with the no-vehicle model as primary; note that years are not independent samples of zones",
         "priority": "medium"},
        {"question": "Did congestion pricing change the origin-destination pattern of taxi trips that would cross the zone?",
         "data": "TLC yellow and HVFHV trip records 2024 and 2025 (cbd_congestion_fee field from 2025)",
         "design": "difference in trip distance for OD pairs whose straight line crosses the zone versus matched pairs that do not",
         "priority": "medium"},
        {"question": "The System graph holds no concepts for ride-hailing, taxis, subway or transit access",
         "data": "System Public Graph", "design": "add transport-geography literature", "priority": "low"},
    ],
    "figures": ["figures/commuting/fhv_pickups_subway_distance.png"],
    "notes": (
        f"Sample: {q['n']} taxi zones in the Bronx, Brooklyn, Queens and Staten Island (175 met the population rule; Rikers "
        "Island dropped because it has no household income). In 2024 TLC recorded 239.5 million app pickups, 40.6 million "
        "yellow taxi pickups and 0.66 million green taxi pickups (c5iv-bn4s). The median zone outside Manhattan had 17.2 app "
        f"pickups per resident and a population-weighted distance of 0.61 km to a station. Registered sensitivities: unadjusted "
        f"{fmt(fr['unadjusted'], 'elasticity')}; borough fixed effects {fmt(fr['borough_fe'], 'elasticity')}; drop-offs "
        f"{fmt(fr['dropoffs'], 'elasticity')}; all boroughs {fmt(fr['all_boroughs'], 'elasticity')}; yellow and green taxis "
        f"{fmt(fr['yellow_green_pickups'], 'elasticity')}. Adding the share of households with no vehicle reverses the sign: "
        f"{fmt(fr['plus_no_vehicle'], 'elasticity')}, with each point of no-vehicle share adding "
        f"{100 * fr['no_vehicle_coef']['elasticity']:.1f}% (log points x 100) to pickups per resident. Distance and no-vehicle "
        "share are correlated at -0.76 across zones, so this model rests on the zones where the two diverge. Within boroughs: "
        f"Bronx {fmt(fr['within_Bronx'], 'elasticity')}, Brooklyn {fmt(fr['within_Brooklyn'], 'elasticity')}, Queens "
        f"{fmt(fr['within_Queens'], 'elasticity')}, Staten Island {fmt(fr['within_Staten Island'], 'elasticity')}. "
        "A first run treated Census annotation codes (negative income values) as numbers; they are now set to missing, "
        "which changed the primary estimate from -0.29 to -0.30 and restored 11 zones.")
}

if __name__ == "__main__":
    for r in (COMMUTE, FHV):
        print(claims.outcome(r))
