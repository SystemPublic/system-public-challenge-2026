# Referee report: food-supermarket-diabetes-zcta

The recorded verdict is confirmed: the adjusted ratio of diabetes admissions per doubling of supermarkets per resident is 0.995 (0.946 to 1.046), inside the registered band of 0.90 to 1.10. My independent rebuild gives the same number to three decimals. I recommend that the verdict stand, because the registered support condition is met and nothing deciding was chosen after the data. The claim is narrower than its framing as a conflict with the graph, however. The outcome is a measure of preventable admissions, and in these data it follows poverty and access to care, not the prevalence of diabetes. The same crude gradient with supermarket supply appears for admissions for urinary tract infection and pneumonia, which no theory of food access predicts. The result therefore says little about the graph's findings on diabetes incidence, and the outcome and the docs should say so.

I wrote my own code before reading `docs/health_gaps.md`. My scripts are outside the repo and are not committed. They use my own queries of the store list and of SPARCS, and my own parsing of the Census files already in `~/opt/nyc-concordance/census/`.

## Data

- 9a8c-vfzj, NY State Retail Food Stores (data.ny.gov), rowsUpdatedAt 2026-10-14T19:08:34Z, fetched 13 November 2026 12:34 EST; 11,159 rows in the five NYC counties, with store names.
- 5q8c-d6xq, SPARCS Adult Prevention Quality Indicators by ZIP (health.data.ny.gov), rowsUpdatedAt 2026-01-13T20:37:43Z, fetched 12:35 EST; all PQIs for 2021-2023, 73,691 rows.
- Census 2020 ZCTA-county relationship file and 2020 Gazetteer (land area, internal points); ACS 2019-2023 5-year table-based summary files B01003, B19013, B17001, B01002, B09021, B03002, B08201.
- EHDP indicator 2169 (CHS adult diabetes, age-adjusted percent, UHF42, 2021 and 2022) and the UHF42 boundaries, from github.com/nychealth/EHDP-data at commit 547482b9 (the commit the repo's heat scripts pin).

## Order of registration and data

The script `analyses/health_gaps/food_access.py` was committed in d787695 at 11:59:38 and the registration in d974897 at 12:00:23 on 13 November. The store list and SPARCS caches were written at 12:03 and the outcome was committed in 7a423e0 at 12:08:36. The two deviations from the committed script (Census summary files in place of the Census API, and an upper-case county filter) change the route to the same variables and do not change the model. I found no earlier query of 5q8c-d6xq or 9a8c-vfzj in the shared cache. The order is as the outcome states.

## 1. Rebuilding the deciding number

My unit set matches the registrant's: 168 ZCTAs whose largest land part lies in NYC, with at least 5,000 adults. Stores are type A licences of at least 6,000 square feet, counted by address ZIP.

| Model (ratio per doubling of supermarkets per 10,000 residents) | Estimate (95% CI) |
|---|---|
| Registered primary, WLS by population, HC3 | 0.995 (0.946 to 1.046) |
| Same, standard errors clustered by UHF42 (42 clusters) | 0.995 (0.948 to 1.045) |
| Unadjusted | 0.895 (0.822 to 0.974) |
| Unweighted OLS | 0.952 (0.880 to 1.030) |
| Excluding pharmacy, dollar-store and general-merchandise chains | 0.985 (0.936 to 1.036) |
| Borough fixed effects | 1.001 (0.951 to 1.053) |
| Without Manhattan | 1.000 (0.953 to 1.049) |
| Without the top decile of stores per resident | 1.028 (0.975 to 1.084) |
| Spatial error model, k = 5 neighbours, unweighted (rho 0.65) | 0.977 (0.935 to 1.020) |
| Catchment supply: own ZCTA plus ZCTAs within 1.5 km | 0.979 (0.925 to 1.037) |
| Catchment supply within 2.5 km | 0.964 (0.885 to 1.050) |
| Own supply with neighbours' supply added (SLX), own term | 1.003 (0.955 to 1.054) |
| Same model, neighbours' term | 0.975 (0.861 to 1.103) |

All of these are EXPLORATORY except the first row; they decide nothing. The registered condition is met under the registered model and under clustering by UHF42 and the spatial error model. It is not met unweighted or with the 2.5 km catchment, where the lower bound falls below 0.90. Those intervals still include 1, so under them the verdict would be unsettled, not contested.

## 2. Does the verdict follow from the registration and PRECEDENCE?

It does. The support condition (interval inside 0.90 to 1.10, estimate at or above 0.95) is met; rule 1 gives confirmed. For a conflict-kind claim, "confirmed" here means that the city data confirm the registered disagreement with the graph. No resampling is involved, so rule 9 does not apply. The secondaries in the outcome are labelled as not deciding.

The `graph_effect` of 0.85 to 0.92 per doubling is a translation of an odds ratio on distance to the nearest supermarket into a ratio per doubling of supply. The registration states it as an approximation, and it was written before the data were read. It is not a quantity the graph holds, and the conflict is between a city admission ratio and a translated survey odds ratio on a different outcome (see section 3).

## 3. Definition, denominator, adjustment, outcome and spatial dependence

### Supermarket definition

The 6,000 square foot threshold on type A licences admits many stores that are not supermarkets. Of 1,212 qualifying licences, at least 271 are pharmacy chains (CVS 71, Duane Reade 46, Walgreens 41), dollar stores, Target and other general-merchandise chains, matched by name. Removing them changes the estimate from 0.995 to 0.985. The definition adds noise but does not move the result. Square footage in this list is the licensed area and is self-reported; the registration is right to call 6,000 square feet the FRESH minimum, but FRESH also requires a share of floor area for fresh food, which the list does not record.

### Denominator

Per-resident supply is high in ZCTAs with few residents and many workers (10018 in Midtown has 7 qualifying stores and 8,764 residents). Stores serve workers and passers-by as well as residents, so the per-resident measure overstates access in business districts. Removing the top decile of supply or Manhattan leaves the estimate at 1.00 to 1.03. Address ZIPs and ZCTAs do not coincide; 8 qualifying stores sit in ZIPs outside the analysis set, which is negligible.

### Adjustment set

Density, poverty, log income and median age are reasonable confounders. Two points matter. First, the expected rate in SPARCS is already age-sex standardised, so median age adjusts a second time for age. Second, poverty carries most of the explanatory weight (ratio 1.22 per 10 points of poverty, R² 0.67), and supply correlates only weakly with poverty (r = −0.11) and log income (r = 0.23) across ZCTAs. The crude gradient of 0.895 is removed by adjustment, which implies that the crude association rests on the few ZCTAs where low supply and high poverty coincide. The adjusted estimate is then identified from variation in supply within strata of poverty, and is as precise as the intervals say only if that variation is not itself a marker of poverty measured with error.

### What the outcome measures

PQIs are defined as admissions that good outpatient care can prevent. They measure access to and quality of primary care as much as disease. Three checks show this in New York:

1. A negative-control outcome behaves like the diabetes outcome. For acute PQIs (bacterial pneumonia and urinary tract infection, PQI 91) the crude ratio per doubling of supermarkets is 0.885 (0.818 to 0.957), the same as for diabetes (0.895), and the adjusted ratio is 0.961 (0.911 to 1.013). Heart failure and hypertension give 0.904 crude and 0.995 adjusted. Supermarket supply predicts crude preventable admissions of all kinds.
2. The diabetes O/E correlates 0.77 with the acute-PQI O/E across ZCTAs. The ratio of the two, a diabetes-specific excess, has a crude ratio per doubling of 1.012 (0.964 to 1.062).
3. At the level of the 42 UHF neighbourhoods, the diabetes admission O/E has an elasticity of 0.19 (SE 0.10) to the CHS age-adjusted prevalence of diabetes, and 0.03 (SE 0.05) once poverty is held. Admissions follow poverty, not prevalence. The CHS prevalence itself has a ratio per doubling of supply of exp(−0.18) = 0.84 with an SE of 0.22 on the log scale once density, poverty, income and age are held. With 42 units that interval runs from about 0.54 to 1.29 and says nothing.

The graph findings the registration names are on diabetes incidence (PMID 36058428), obesity and glycaemic control. The city test is on preventable admissions. A null on admissions does not conflict with an association on incidence unless admissions track incidence, and in New York they track poverty and access to care much more closely. The claim's statement says "hospital admissions for diabetes", which is accurate, but the stance of a conflict with the graph is weaker than the verdict label suggests.

### Spatial dependence

Residuals of the primary model are spatially correlated: Moran's I with five nearest neighbours is 0.35 (permutation p < 0.001); the outcome itself has I = 0.61. HC3 errors assume independence. Clustering by UHF42 leaves the interval almost unchanged (0.948 to 1.045), and a spatial error model gives 0.977 (0.935 to 1.020), still inside the support band. Supply measured over a catchment wider than the ZIP moves the estimate towards the graph's direction (0.964 at 2.5 km) and widens the interval past 0.90. The ZIP is a narrow unit for food shopping in New York, as the registration's second alternative says; the bias is towards the null, and the 2.5 km result shows that a wider unit would not have met the support condition.

## 4. The prose in docs/health_gaps.md

I read the doc after finishing the rebuild above. Its numbers for this claim are correct, including the Red Hook case (ZCTA 11231 has 14 qualifying licences and 39,704 residents in my data). It states that admissions also measure access to primary care. It claims more than the numbers support in three places.

1. "Neither predicts diabetes admissions once income is held" is accurate. The doc then reads it as an answer about diabetes and FRESH ("these data give no reason to expect fewer diabetes admissions from it"). The negative control and the UHF42 comparison above show that the admission measure tracks poverty and the general rate of preventable admissions. They do not show that supply is unrelated to diabetes itself. The sentence should say that the data cannot show an effect of supply on diabetes in either direction.
2. "The secondary models agree" lists only models that leave the unit and the weighting unchanged. Unweighted, or with supply over a 2.5 km catchment, the lower bound falls below 0.90 (0.880 and 0.885), and the estimates (0.952, 0.964) move towards the graph's value. The doc should report that the result depends on the ZIP as the unit of access and on population weights.
3. The novelty paragraph says the result "answers the chicken-and-egg question directly". It answers the per-area question: density explains the per-area gradient. Its claim that per-resident scarcity "follows income" overstates the data, since supply correlates weakly with income (r = 0.23) and poverty (r = −0.11) across ZCTAs.

The doc says the registrations were pushed to their own branches before the data were read. The branches `origin/prereg/food-supermarket-diabetes-zcta` and `origin/prereg/ems-hospital-turnaround-wait` exist and point at the registration commits; I cannot see from the repository when they were pushed.

## 5. What would settle it

The registration's settle condition (a staggered difference in differences on FRESH store openings, with A1C Registry or admission outcomes) is right. I would add a negative-control outcome (acute PQIs) to any admission-based design, and use prevalence or HbA1c rather than admissions where the question is about diabetes itself. A catchment measure of supply (stores within a walking or driving distance of the population, not within the ZIP) should be registered as the primary exposure.
