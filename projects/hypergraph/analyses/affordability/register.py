"""Register afford-gentrification-prevalence and afford-poor-count-shift (run once, before the outcome panel is read)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from concord import claims

LOW = ("Mott Haven/Hunts Point, Morrisania/Belmont, East Harlem, Central Harlem, Brownsville/Ocean Hill, Bedford Stuyvesant, "
       "Lower East Side/Chinatown, Coney Island, Rockaways, Williamsburg/Greenpoint, Highbridge/South Concourse, "
       "North Crown Heights/Prospect Heights, Bushwick, Morningside Heights/Hamilton Heights, Soundview/Parkchester, "
       "University Heights/Fordham, East New York/Starrett City, Washington Heights/Inwood, Throgs Neck/Co-op City, "
       "South Crown Heights, Brooklyn Heights/Fort Greene, Kingsbridge Heights/Mosholu")
SEEN = ("Read before registration: the 2000 values of every indicator for the 55 sub-borough areas and the city (rent, income, college share, "
        "poverty, population), which fix the low-start group; the workbook's column names, data dictionary and the count of non-missing cells "
        "by year. Not read directly: any value after 2000 for rent, college share, poverty or population. One leak occurred. The code test "
        "(`gentrification_test.py --simulate`) was meant to replace later-year values with noise; it multiplied the real values by lognormal "
        "noise instead (sigma 0.3 on each annual value, seed 0), and I read its output: k = 6, k2 = 7, Spearman 0.38, and the list of areas it "
        "classed as gentrified (Brooklyn Heights/Fort Greene, Bushwick, Coney Island, Lower East Side/Chinatown, North Crown Heights/Prospect "
        "Heights, Williamsburg/Greenpoint). That output is a noisy view of the outcome: the noise is about as large as the real variation between areas. "
        "The thresholds (k of 12 or more, 4 to 11, 1 or fewer) and the script were written before that run and were not changed after it. "
        "Prior knowledge: the Furman Center's 2016 report classed 15 of 22 low-income sub-borough areas as gentrifying on rent growth above the "
        "median from 1990 to 2014, with one condition (rent) where this test has two; Alroy 2023 classed 14 of 42 neighbourhoods as gentrifying "
        "or hypergentrifying on rent growth from 2000 to 2017. Also seen before registration, none of them a deciding variable: executed evictions "
        "by community district and year (6z8x-wfk4), IRS county outflows, and the graph findings listed.")
GRAPH = [
 {"association_id": "variable-name search 'gentrification', 'gentrifying', 'gentrified'", "concepts": ["gentrification (variable names)", "health and injury outcomes"],
  "n_findings": 33, "n_studies": 15, "direction": "0",
  "summary": "The graph holds 33 findings in 15 studies with gentrification as a variable name; all concern health or injury outcomes and none concerns how often low-rent neighbourhoods gentrify. The studies' own counts, read in the abstracts, give a prevalence: Alroy 2023 classed 14 of 42 New York neighbourhoods as gentrifying or hypergentrifying (rent growth 2000 to 2017); Bhavsar 2022 found that 5 of 28 eligible block groups in Durham gentrified; Spitzer 2023 classed 23.8% of 59,379 urban tracts as gentrifying. Gao 2023 found opposite signs for severe maternal morbidity under two definitions (OR 0.89 and 1.18), and Bhavsar reports that results depend on the definition.",
  "pubmed_ids": [37018221, 36367672, 37728889, 37678111, 24022181, 29272306, 29709759]},
 {"association_id": "variable-name search 'displacement', 'eviction', 'rent burden', 'housing cost burden'", "concepts": ["displacement, eviction, rent burden (variable names)", "health outcomes"],
  "n_findings": 150, "n_studies": 60, "direction": "+",
  "summary": "About 150 findings in about 60 studies (collection still running at registration; counts approximate). Lim 2017 followed 12,882 residents of gentrifying New York neighbourhoods who had hospital records: 23% were displaced between 2006 and 2014, and the displaced had 1.8 times (1.5 to 2.2) the rate of emergency visits and hospitalisations, mainly for mental health. Schwartz 2022: New York evictions in 2017 and loss of Medicaid coverage, OR 1.63 (1.38 to 1.92). Graetz 2024: an eviction judgment and 40% (36 to 43) higher mortality; the graph stores the percentages 40, 19, 16 and 12 as hazard ratios. The graph holds no finding that compares the rate at which low-income residents leave gentrifying and non-gentrifying neighbourhoods, which is the disputed question (Freeman and Braconi 2004; Ding, Hwang and Divringi 2016; Dragan, Ellen and Glied 2020).",
  "pubmed_ids": [29272306, 35000688, 38007965, 36120757]}]
LIT = [{"citation": "NYU Furman Center. State of New York City's Housing and Neighborhoods in 2015, Focus on Gentrification. 2016.", "doi": None,
        "finding": "15 of 55 sub-borough areas classed as gentrifying (low income in 1990, rent growth above the median 1990 to 2010-2014), 7 as non-gentrifying, 33 as higher-income."},
       {"citation": "Freeman L, Braconi F. Gentrification and displacement: New York City in the 1990s. J Am Plann Assoc 2004;70:39-52.", "doi": "10.1080/01944360408976337",
        "finding": "Poor households in gentrifying New York neighbourhoods were less likely to move than poor households elsewhere."},
       {"citation": "Dragan K, Ellen IG, Glied S. Does gentrification displace poor children and their families? Reg Sci Urban Econ 2020;83:103481.", "doi": "10.1016/j.regsciurbeco.2019.103481",
        "finding": "Low-income children in New York born 2006 to 2008 in gentrifying areas were no more likely to move than those in areas that stayed poor."}]

claims.register({
 "id": "afford-gentrification-prevalence", "kind": "confirmation",
 "statement": "Among the 22 New York sub-borough areas with the lowest median gross rent in 2000, a minority (4 to 11) had both rent growth and growth in the share of college graduates above the city's by 2022-2024, and across all 55 areas rent growth and growth in the college share are positively associated.",
 "graph_evidence": GRAPH,
 "graph_evidence_note": "Collected 13 November 2026 by analyses/affordability/graph_collect.py (variable-name search, API). Abstracts of PMIDs 29272306, 37728889, 36367672, 24022181, 37018221, 29709759, 33994893, 37678111, 35083727, 38007965, 35000688 and 36120757 were read in PubMed. The graph supplies no effect size for this claim; it supplies the range of prevalence under other definitions (18% to 33%) and the warning that results change with the definition.",
 "literature": LIT,
 "prediction": {"direction": "+",
  "magnitude": "k between 6 and 10 of 22 (27% to 45%), best guess 8. k2 between 5 and 10. Spearman correlation of rent growth with change in college share across 55 areas between 0.3 and 0.7. Areas I expect in the gentrified set: Williamsburg/Greenpoint, Bedford Stuyvesant, Bushwick, Central Harlem, North Crown Heights/Prospect Heights, Brooklyn Heights/Fort Greene. I expect none of the eight Bronx low-start areas in it.",
  "definitions": "Unit: sub-borough area (SBA), 55 in the Furman Center file. Low start: the 22 SBAs (bottom 40%) by median gross rent in 2000 (" + LOW + "). Rent growth: mean of the 2022, 2023 and 2024 values of rent_gross_med_adj divided by the 2000 value, minus 1. College change: mean of the 2022, 2023 and 2024 values of pop_edu_collp_pct minus the 2000 value, in points. Gentrified: both exceed the same quantities computed from the City row. k: gentrified SBAs among the 22. k2: the same count with growth measured from the mean of 2005, 2006 and 2007 to the mean of 2022 to 2024, the low-start group still chosen on 2000 rent (a baseline separate from the selection year, against regression to the mean). rho: Spearman correlation of rent growth and college change over all 55 SBAs, 95% interval by Fisher z with standard error sqrt(1.06/(n-3)).",
  "readings": "common: k >= 12 (Wilson 95% lower limit 0.34, above one third) and k2 >= 11 and the lower limit of rho above 0. myth: k <= 1 (Wilson upper limit 0.22), or the upper limit of rho below 0. real but a minority: k from 4 to 11 and k2 >= 3 and the lower limit of rho above 0. Anything else is undecided.",
  "support_if": "The reading is 'real but a minority'.",
  "refute_if": "The reading is 'common' or 'myth'; the outcome says which.",
  "otherwise": "Unsettled.",
  "secondary_registered": "Reported, not deciding: the count meeting both conditions among the other 33 SBAs; k with the low-start group defined on 2000 median household income; the counts meeting each condition alone; the low-start SBAs whose rent is in the top half (rank 29 or above of 55) in 2022-2024; the Spearman correlation of 2000 rent with 2022-2024 rent."},
 "plan": "Script: analyses/affordability/gentrification_test.py, committed with this registration and run unchanged (PRECEDENCE rule 9). No resampling and no random numbers in the test. Data: data/derived/affordability/furman_panel.csv, built by analyses/affordability/build_panel.py from the NYU Furman Center CoreData workbook Neighorhood_Indicators_CoreDataDownload_2026-05-05.xlsx (sha256 in data/derived/affordability/furman_source.json). The Furman Center computes the SBA values from census 2000 and American Community Survey microdata and adjusts dollars for inflation. The Census API was not used because it requires a key.",
 "can_it_fail": {"binomial_model": "If each low-start SBA met both conditions independently with probability p, P(k <= 1), P(4 <= k <= 11), P(k >= 12) are: p = 0.15: 0.14, 0.43, 0.00; p = 0.25: 0.02, 0.84, 0.00; p = 0.35: 0.00, 0.93, 0.05; p = 0.50: 0.00, 0.58, 0.42; p = 0.65: 0.00, 0.11, 0.89; p = 0.80: 0.00, 0.00, 1.00.",
                 "association": "The count alone cannot separate a real pattern from two unrelated coin flips with p near 0.25, so the reading also requires the lower limit of rho above 0. With n = 55 that happens with probability 0.025 if rho = 0, 0.58 if rho = 0.3, 0.84 if rho = 0.4 and 0.97 if rho = 0.5.",
                 "reading": "The support condition fails with probability about 0.98 if rent growth and college growth are unrelated, and with probability about 0.9 if two thirds of low-rent areas gentrify. It can therefore fail in both directions. It is likely to pass (about 0.6) under my prediction, and the leak described under already_seen raises that."},
 "already_seen": SEEN,
 "alternatives": ["Regression to the mean: an area with an unusually low rent estimate in 2000 would show fast growth without any change. The 2000 values come from the census long form (about one household in six), so sampling error is small, and k2 uses a later baseline.",
                  "Citywide rent growth: every area's rent rose; the definition compares with the city's growth for that reason.",
                  "Rent regulation and public housing hold the median rent of all tenants below the rent a newcomer pays, so median gross rent understates change where many tenants are regulated (Lower East Side, Harlem).",
                  "Boundary changes: the public-use microdata areas behind the SBAs were redrawn in 2012 and 2022; the Furman Center maps them to fixed SBAs, and any error is in its file.",
                  "College share can rise because long-term residents' children graduate or because older residents with less schooling die, without newcomers.",
                  "55 areas of 100,000 to 250,000 people hide change within them; a gentrifying corner of a large area may not move its median."],
 "prior": 0.6, "prior_note": "Probability of 'real but a minority'. About 0.2 for common, 0.02 for myth, the rest undecided.",
 "registrant": "Claude (affordability agent)"})

claims.register({
 "id": "afford-poor-count-shift", "kind": "confirmation",
 "statement": "Among the 22 low-rent sub-borough areas of 2000, the number of residents below the poverty line fell more between 2000 and 2022-2024 in the areas that gentrified (as defined in afford-gentrification-prevalence) than in those that did not.",
 "graph_evidence": GRAPH,
 "graph_evidence_note": "As for afford-gentrification-prevalence. The graph has no finding on counts of poor residents and none that compares exit rates of low-income residents between gentrifying and other poor neighbourhoods. Lim 2017 gives the only number: 23% of a hospital-using cohort in gentrifying New York neighbourhoods moved to a lower-income area or out in eight years, with no comparison group in the graph record.",
 "literature": LIT,
 "prediction": {"direction": "-",
  "magnitude": "Difference in mean log change of the poor count, gentrified minus not gentrified, between -0.45 and -0.10; best guess -0.25 (about 22% fewer poor residents relative to the comparison areas).",
  "definitions": "Poor count: pop_pov_pct / 100 x pop_num. Change: log of the mean-of-2022-2024 count over the 2000 count. Groups: the low-start SBAs classed gentrified and not gentrified by the primary definition of afford-gentrification-prevalence (rent growth and college change from 2000, both above the city's). Interval: Welch t, 95%.",
  "support_if": "The upper limit of the difference (gentrified minus not) is below 0.",
  "refute_if": "The lower limit of the difference is above 0.",
  "otherwise": "Unsettled. If either group has fewer than 3 SBAs the verdict is no_test.",
  "secondary_registered": "Reported, not deciding: (b) the same contrast for the change, in points, of the share of low-income renter households (at or below 80% of area median income) paying 30% or more of income in rent, 2005-2009 to 2020-2024 (rburden_mod_ami_le80); (c) totals of the poor count in 2000 and 2022-2024 for gentrified low-start, other low-start, the other 33 SBAs and all 55."},
 "plan": "Same script and data as afford-gentrification-prevalence (analyses/affordability/gentrification_test.py, claim2 block), run unchanged. This claim is registered before that script has been run on the real panel, so the group membership is not known at registration except through the leak described under already_seen.",
 "can_it_fail": {"assumption": "The spread of the log change in the poor count across SBAs is not known before the data are read; I assume a standard deviation between 0.20 and 0.35.",
                 "standard_error": "With 8 gentrified and 14 other areas the standard error of the difference is 0.09 (sd 0.20), 0.11 (sd 0.25) or 0.16 (sd 0.35); with 5 and 17 it is 0.10, 0.13 or 0.18.",
                 "power": "For a true difference of -0.30 the support condition is met with probability 0.90 (sd 0.20, 8 areas), 0.73 (sd 0.25, 8 areas), 0.60 (sd 0.25, 5 areas) or 0.34 to 0.43 (sd 0.35). With no true difference it is met with probability 0.025. The smallest difference detectable with 80% power is 0.26 to 0.52.",
                 "reading": "The test can fail. An unsettled verdict is likely if the true difference is under 0.25."},
 "already_seen": SEEN + " For this claim: no poverty rate or population after 2000 was read, in any form; the simulated run printed only the first claim's block before the output was cut at 70 lines.",
 "alternatives": ["A fall in the poor count is not displacement. Poor residents can leave, die, or stop being poor; the count cannot tell these apart.",
                  "The poverty line is national and takes no account of rent, so a household above it may still be unable to pay a higher rent.",
                  "Citywide poverty fell over the period; the comparison with other low-rent areas removes the common part.",
                  "New housing adds residents who are not poor and lowers the rate without changing the count; the test uses the count for that reason.",
                  "Public housing and regulated units keep poor residents in place in some gentrifying areas (Lower East Side, Harlem) and weaken the contrast.",
                  "The 2000 poverty count is from the census long form and the later ones from the ACS, which measure income over different reference periods; this affects both groups alike."],
 "prior": 0.5, "prior_note": "Probability that the upper limit is below 0. About 0.03 for contested, the rest unsettled or no_test.",
 "registrant": "Claude (affordability agent)"})
print("registered")
