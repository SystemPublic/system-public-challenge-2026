"""Write the outcomes of afford-gentrification-prevalence and afford-poor-count-shift from the results files."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from concord import claims
D = ROOT / "data/derived/affordability"
r = json.load(open(D / "gentrification_results.json")); b = json.load(open(D / "boundary_check.json"))
src = [json.load(open(D / "furman_source.json")), {"kind": "sysgraph", "file": "data/derived/affordability/graph_findings.json", "requests": 246, "findings": 335, "pubmed_ids": 155}]
c1, c2 = r["claim1"], r["claim2"]; w = c2["log_change_poor_count_gent_minus_not"]; e = b["end_2017_19"]
BOUND = ("Found after the outcome: the 2022 American Community Survey moved to 2020 public-use microdata areas, and in the Furman file the population of 28 of 55 areas "
         "changes by more than 8% between 2021 and 2022 (7 of 55 at the 2012 change, 13 in an ordinary year). The registered end period, 2022-2024, is therefore on different boundaries from 2000 for about half the areas. ")
claims.outcome({
 "id": "afford-gentrification-prevalence", "verdict": c1["verdict"],
 "city_effect": {"label": "share of the 22 lowest-rent areas of 2000 whose rent and college share both grew faster than the city's by 2022-2024", "estimate": c1["k"] / 22,
                 "lo": c1["k_wilson"][0], "hi": c1["k_wilson"][1], "scale": "proportion (Wilson interval)", "null": 0, "n": 22},
 "graph_effect": {"label": "share of eligible neighbourhoods classed as gentrifying in studies the graph holds (Bhavsar 2022, 5 of 28; Spitzer 2023, 23.8% of tracts; Alroy 2023, 14 of 42)", "estimate": 0.24, "lo": 0.18, "hi": 0.33, "scale": "proportion, range across three studies", "null": 0},
 "sources": src,
 "prediction_scored": "hit. k = 8 (predicted 6 to 10, best guess 8), k2 = 8, Spearman 0.68 (0.50 to 0.80; predicted 0.3 to 0.7). All six areas named in advance are in the set, with Morningside Heights/Hamilton Heights and Washington Heights/Inwood, which were not named; no Bronx area is in it (the registration says eight Bronx low-start areas; there are seven). The prediction was made after a noisy view of the outcome, described under already_seen in the registration.",
 "settle": "Tract-level data on fixed boundaries for 2000, 2010 and 2020 onward (the Census API with a key, or the NHGIS time series) would show how much of each area changed and remove the 2022 boundary break.",
 "research_needed": [{"question": "How many of New York's low-rent census tracts of 2000 gentrified, on fixed boundaries?", "data": "Census 2000 SF3 and ACS five-year tract tables with a 2000-2010-2020 crosswalk", "design": "The same two-condition definition at tract level, with the end period chosen before the data are read", "priority": "high"}],
 "figures": ["figures/affordability/rent_rank_trajectories.png", "figures/affordability/rent_growth_vs_college.png"],
 "notes": ("Reading: real but a minority. 8 of 22 low-rent areas (36%, Wilson 20% to 57%) met both conditions: Bedford Stuyvesant, Brooklyn Heights/Fort Greene, Bushwick, Central Harlem, Morningside Heights/Hamilton Heights, "
           "North Crown Heights/Prospect Heights, Washington Heights/Inwood and Williamsburg/Greenpoint. City rent growth was 41% in constant dollars and the city's college share rose 14.7 points. Five of the eight (the Brooklyn areas) "
           "rose 32 to 38 rank places in rent; the three upper Manhattan areas passed the rent condition by 1 to 9 points of growth and moved 4 to 8 places. Secondary: 6 of the other 33 areas met both conditions; 8 of 22 with the low-start group defined on income; "
           "9 of 22 met the rent condition and 12 of 22 the college condition; the Spearman correlation of 2000 rent with 2022-2024 rent is 0.71. " + BOUND +
           f"Exploratory check with the end period 2017-2019: k = {e['k']} (South Crown Heights added), Spearman {e['spearman']:.2f}, {e['k_other_33']} of the other 33. The reading does not change.")})
claims.outcome({
 "id": "afford-poor-count-shift", "verdict": c2["verdict"],
 "verdict_note": "Confirmed on the registered condition (upper limit below 0) by a margin of 0.02 log points, on an end period affected by a boundary change. The exploratory repeat on 2017-2019 gives a narrower interval with the same sign.",
 "city_effect": {"label": "difference in mean log change of the number of poor residents, 2000 to 2022-2024, gentrified minus other low-rent areas", "estimate": w["diff"], "lo": w["lo"], "hi": w["hi"],
                 "scale": "difference in log change", "null": 0, "n": 22},
 "sources": src,
 "prediction_scored": "hit. -0.28 (-0.54 to -0.02) against a predicted -0.45 to -0.10, best guess -0.25. The upper limit is 0.02 from the threshold.",
 "settle": "Records that follow people: the ACS or census linked files used by Brummet and Reed, Medicaid enrolment histories as in Dragan, Ellen and Glied, or the hospital records of Lim 2017, compared between gentrifying and other low-rent areas.",
 "research_needed": [{"question": "Do poor residents of gentrifying New York neighbourhoods leave at a higher rate than poor residents of other low-rent neighbourhoods, and where do they go?", "data": "Linked individual address histories (Medicaid, SPARCS, tax records)", "design": "Cohort of residents at baseline, exit and destination by neighbourhood type", "priority": "high"},
                     {"question": "The graph holds no finding on exit rates by neighbourhood type.", "data": "Freeman and Braconi 2004; Ding, Hwang and Divringi 2016; Dragan, Ellen and Glied 2020; Brummet and Reed 2019", "design": "Add the economics and planning literature to the graph", "priority": "medium"}],
 "figures": ["figures/affordability/poor_count_change.png"],
 "notes": ("The number of residents below the poverty line fell 29% in the 8 gentrified areas (341,000 to 241,000), 10% in the 14 other low-rent areas and 3% in the other 33; the city total fell 11%. "
           "Secondary (b): the share of low-income renters paying 30% or more changed by -0.2 points in gentrified areas and -1.8 in the others, difference 1.6 (-0.7 to 4.0). " + BOUND +
           f"Exploratory repeat with the end period 2017-2019 and the registered groups: {e['poor_count_registered_groups']['diff']:.2f} ({e['poor_count_registered_groups']['lo']:.2f} to {e['poor_count_registered_groups']['hi']:.2f}); "
           f"the poverty rate fell {abs(e['poverty_rate_points_registered_groups']['diff']):.1f} points more in gentrified areas ({abs(e['poverty_rate_points_registered_groups']['hi']):.1f} to {abs(e['poverty_rate_points_registered_groups']['lo']):.1f}). "
           "A fall in the count does not show displacement: the data cannot separate residents who left from residents who died or whose income rose.")})
print("outcomes written")
