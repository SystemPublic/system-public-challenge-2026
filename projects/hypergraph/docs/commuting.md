# Commuting and taxi routes

This note reports two registered claims on commuting in New York City. The first asks whether neighbourhoods with longer commutes have more depression. The second asks whether app-based for-hire trips are more common where the subway is far away. Both were registered and committed (commit `eb1e22f`) before the city data that test them were queried. The outcomes are in `claims/outcomes/`, and the scripts in `analyses/commuting/` re-run every number below.

The earlier mobility work (`docs/mobility.md`) covered congestion pricing and speeds, air quality, speed cameras, and walking or cycling to work against obesity. These claims do not repeat it.

| Claim | Verdict | City estimate (95% interval) | Prediction scored |
|---|---|---|---|
| commute-time-depression | unsettled | −0.77 (−1.63 to +0.10) percentage points of adults with depression per 5 minutes of mean commute | miss |
| commute-fhv-subway-distance | contested | elasticity −0.30 (−0.38 to −0.21) of app pickups per resident with respect to distance to a station | miss |

## The research side

The System Public Graph (Dataverse v2.1) has no concept for commuting or commute time, only one for telecommuting. A search of variable names finds 289 associations that mention commuting. Of these, 51 have commute time or distance as the exposure. Of these, seventeen report an odds or risk ratio for a mental-health outcome and fourteen for sleep, and almost all of these ratios are above 1. The graph holds no finding that links commute time to BMI or obesity. `analyses/commuting/graph_evidence.py` writes the list to `data/derived/commuting/graph_evidence.json`.

I read the PubMed abstracts of the findings the first claim relies on, and the graph records them correctly. A Korean survey of about 50,000 workers (PMID 37342827) reports odds ratios for depression of 1.06 for commutes of 30 to 60 minutes and 1.23 for 60 to 120 minutes, against commutes of 30 minutes or less. A Swedish fixed-effects study (PMID 31836613) reports more physical inactivity and sleep problems with long commutes, but only among people who work more than 40 hours a week. One finding returned by the search (PMID 25501883) measures physical activity during the commute, not its length, and was not used.

The graph has no concepts for ride-hailing, taxis or the subway. The second claim rests on the transport literature. Barajas and Brown (2021) found in Chicago that ride-hail trips are more common where rail service is good, not in transit deserts. The registration cited this finding as the result that would contradict its prediction.

## Commute time and depression (commute-time-depression): unsettled

The exposure is mean one-way travel time to work for workers who do not work at home, from the ACS 2015-19. It ranges from 25.7 minutes in Greenwich Village-SoHo to 50.2 minutes in the Rockaways. The outcome is the age-adjusted share of adults with depression in the Community Health Survey 2017-18. Both are measured for the 42 UHF neighbourhoods. The model adjusts for poverty and for the share of residents within a quarter mile of a subway entrance.

Depression falls by 0.77 points (−1.63 to +0.10) for each 5 minutes of mean commute. The interval includes zero, so neither the registered confirmation condition nor the refutation condition is met, and the verdict is unsettled. The sign is opposite to the prediction. Manhattan neighbourhoods have short commutes and more depression than poverty predicts, and they pull the slope down. With borough fixed effects the slope is −0.55 (−1.73 to +0.62).

This design could not have detected the effect reported in the research. When the odds ratios from the research are applied to New York's depression rate and the share of adults who work, they imply a neighbourhood slope of at most +0.3 points per 5 minutes. The standard error of the neighbourhood slope is about 0.44 points, larger than that expected effect. Only individual data could test the association, and the Community Health Survey does not ask about commute time.

The secondary outcomes give a different picture. Adjusted in the same way, the share of adults who did no exercise in the past month rises 2.2 points (1.2 to 3.2) per 5 minutes, and obesity rises 4.0 points (2.8 to 5.3). These slopes are far larger than any commute effect in the research. Neighbourhoods with long commutes are in the outer boroughs, depend on cars and buses, and differ in age and ethnic composition. The same pattern appeared in mob-active-commute-obesity (`docs/mobility.md`). It is an association between places, not a test of whether commuting affects health.

The figure is `figures/commuting/commute_time_depression_uhf42.png`. It maps mean commute time and plots depression against commute time after adjustment.

## App trips and distance to the subway (commute-fhv-subway-distance): contested

The unit is the TLC taxi zone. The registered sample covers the Bronx, Brooklyn, Queens and Staten Island. It excludes the airports and zones with fewer than 2,000 residents, which leaves 174 zones. The outcome is 2024 pickups by high-volume for-hire companies (Uber, Lyft and similar) per resident, from TLC's monthly zone counts. The exposure is the population-weighted straight-line distance from census tracts to the nearest subway or Staten Island Railway station. The model adjusts for mean household income and jobs per resident.

In 2024 TLC recorded 239.5 million app pickups and 40.6 million yellow taxi pickups. The median outer-borough zone had 17 app pickups per resident and lay 0.61 km from a station. Pickups per resident fall as distance rises, with an elasticity of −0.30 (−0.38 to −0.21). A zone twice as far from the subway has about 18% fewer app pickups per resident. The whole interval lies below zero, opposite to the prediction, so the registered refutation condition is met and the verdict is contested. The result agrees with Barajas and Brown's finding in Chicago.

The registered checks support the result. Adding borough fixed effects gives −0.17 (−0.26 to −0.08), using drop-offs instead of pickups gives −0.32, and including all five boroughs gives −0.34. Yellow and green taxi pickups fall faster with distance, with an elasticity of −0.65. Within each borough the slope is negative or uncertain, except on Staten Island, where it is +0.18 (0.00 to 0.35) over 18 zones.

One registered check reverses the sign. When the model also adjusts for the share of households without a car, the elasticity becomes +0.14 (+0.04 to +0.25). Each percentage point of households without a car goes with about 2.8% more app pickups per resident. Distance and the share of households without a car are correlated at −0.76 across zones, so this estimate rests on the zones where the two differ. This estimate suggests that app trips replace subway trips for households without cars, while most households far from the subway own cars and seldom need an app trip. The analysis plan named this model as a check, not the test, so it does not decide the verdict. A new registration with its own data should test this explanation.

The figure is `figures/commuting/fhv_pickups_subway_distance.png`. It maps pickups per resident with station locations and shows a binned scatter of adjusted pickups against adjusted distance.

## What would settle these questions

- For commute time and health, person-level data are needed. These could come from a commute-time question in the Community Health Survey, or from a survey that records both commute time and health for the same New Yorkers.
- For app trips, the NYC Citywide Mobility Survey records trips, home location and car ownership for the same households. With it, a registered test could ask whether car-free households far from the subway make more app trips.
- Congestion pricing may have changed the routes of taxi trips that would otherwise cross the congestion relief zone. The TLC trip records carry a congestion fee field from 2025. Trip distances for origin-destination pairs whose straight line crosses the zone could be compared with pairs that do not, before and after January 2025. This was a candidate third claim and was not run.
- The System graph needs concepts for commute time, ride-hailing and transit access. Its commute-time findings can now be found only by searching variable names.

## Data versions

Each outcome file lists its sources.

- ACS 2015-19 commute tables B08303 and B08013 by ZCTA come from the Census legacy summary files (sequences 0022 and 0027 and the geography file `g20195us.csv`). The Census API now requires a key, so the files were read directly.
- ACS 2019-23 tract tables B19025, B11001 and B08201 come from the table-based summary files.
- Tract populations come from the 2020 PL 94-171 file for New York, and tract internal points from the 2020 Gazetteer.
- Jobs come from LEHD LODES8 WAC 2021.
- EHDP indicators and the ZCTA-to-UHF crosswalk come from github.com/nychealth/EHDP-data at commit `547482b9df589006543e13e8cdf6546e00ed9998`.
- TLC zone counts come from NYC Open Data `c5iv-bn4s`, and stations from data.ny.gov `39hk-dx4f`. Both records carry `rowsUpdatedAt`, the exact SoQL and the fetch time.
- Taxi zone boundaries come from the TLC shapefile `taxi_zones.zip`.

Large files are kept in `~/opt/nyc-concordance/commuting/` and cited by URL.
