# What the research and New York City's data confirm, contest and connect

This report was prepared for the System hackathon, Build Challenge 4, on 12 November 2026 and updated on 13 November 2026. The code, data records and every claim are in this repository. The dashboard is `viz/index.html`.

## 1. One lot, many records

On 8 November 2026 Jeff Vernon photographed a vacant lot in Red Hook, Brooklyn. It held rebar mats and foam forms, with reeds growing over them. We tried to find out from public records what the lot is and what is happening on it (`docs/case_red_hook.md`, `figures/construction2/red_hook_timeline.png`).

The photograph carries no GPS, so the lot was identified from its neighbouring buildings. It is one of two adjoining lots on block 555.

The records do not agree with each other or with the photograph.

- Lot 124 (348 Van Brunt St) was sold on 30 June 2026 for $1.795M, with $4.5M in construction loans. It has a new-building filing for five storeys and eight units, under plan review since July 2026. It has no permit on record. A 2020 job had its plans approved but was never permitted.
- PLUTO, updated in August 2026, still names the seller as owner.
- Lot 27 (100 Sullivan St) has had a new-building permit since 2024. A foundation permit was signed off in August 2025, and a $2.55M construction mortgage was recorded in September 2026. It is the only recorded foundation work on either lot. The materials in the photograph therefore point to lot 27 more than to lot 124.
- The latest public aerial image (NAIP, July 2022) shows both lots bare.

No single source shows what is on this lot. The project asks the same question at city scale: what do separate city records and the published research say when they are read together?

## 2. Method

We used the System Public Graph (Dataverse v2.1, API v1.0) for the research side. NYC Open Data, NOAA GHCN-Daily, the city's Environment and Health Data Portal and NAIP images supplied the city side.

Every hypothesis was registered before the city data that test it were queried. A registration states the direction, the expected size, the condition for support, the condition for refutation, the rival explanations and a prior probability. The registration is hashed and committed to git. The outcome is written afterwards and scored against it (`concord/claims.py`).

Each outcome was then read by a fresh referee agent. The referee had the code and data but not the registrant's reasoning. The answers to each objection are recorded in `critique/ANSWERS.md`. When an outcome changed, the earlier one was kept in a history field.

Four rounds of criticism changed nine verdicts, and the sixth round changed a tenth. Each change moved a verdict towards the middle or to "no test". The rules for reading a verdict (`PRECEDENCE` in `concord/claims.py`) came from these rounds. There are ten rules, and the main ones are these:

- the registered conditions decide;
- a measure chosen after the data were seen never decides;
- a bridge, which chains two relationships into one prediction, is rated no higher than its weakest link;
- an endpoint test counts only if it could have failed. An endpoint test checks a bridge's composed prediction against a dataset that was not used to build it.

### The fourth referee round

On 13 November 2026 fresh referee agents reviewed 30 of the later claims (`critique/ANSWERS.md`, "Round 4"). Each referee had the registration, the outcome, the code and the data, and re-ran the analysis in a scratch folder.

Two verdicts changed. retimed-daytime-burglary went from contested to unsettled, because its refutation bound (0.9525 against a threshold of 0.95) was above the threshold in only 62% of other bootstrap seeds. graph-triad-cold-asthma-absence went from confirmed to unsettled, because its endpoint test does not separate the chain from no effect. One recommended change was not accepted: graph-concordance-matrix stays confirmed, because its registered condition is met, and its outcome now says in narrower terms what is confirmed. Before the round there were 21 confirmed, 11 contested, 24 unsettled, 4 "no test" and 1 bridged. After it there are 20, 10, 26, 4 and 1.

The round added two rules, both written after the outcomes were known. Rule 9 fixes the analysis script, the number of resampling draws and the random seed with the registration. A condition that is met under some seeds and not under others counts as neither met nor unmet. Rule 10 keeps a verdict that rests on a point estimate whose interval crosses the registered threshold, and requires the outcome to state the margin.

The referees also corrected numbers without changing verdicts. Population density had been overstated for eight community districts in graph-confounders-trees-surftemp. An interval in transfer-chicago-weekday-pattern had come from an unpaired bootstrap. Five stances were set to null because their intervals did not measure the uncertainty of the claim. Nearly every report noted that the analysis script was first committed with the outcome, so the plan text and the file times, not the git history, show that the model was fixed before the data were seen.

Twelve outcomes now carry a `verdict_note`, one or two sentences on what the verdict label does and does not mean. The dashboard shows the note and the reason for each revision.

### The fifth referee round

Two claims were registered after the fourth round, heat-night-minimum and transfer-chicago-concordance-matrix, and referees reviewed both on 13 November 2026 (`critique/ANSWERS.md`, "Round 5"). Neither verdict changed. The Chicago claim stays confirmed for its registered count, and its outcome now says that the count does not test the explanation it was designed around. The referee of the heat claim found that the earlier heat claims counted shootings by calendar date, so that shootings between midnight and 06:00 were regressed on a maximum that came later. With those shootings counted with the previous day, the slopes per 5 °C are unchanged within 0.012 and no registered condition changes side, but the rise in New York from 27 to 33 °C falls from 1.102 (1.038 to 1.171) to 1.051 (0.988 to 1.118). Fourteen outcomes then carried a `verdict_note`.

### The sixth referee round

Ten claims were registered on 13 November 2026, and a referee reviewed each on the same day under the conditions of the earlier rounds (`critique/ANSWERS.md`, "Round 6"; `critique/answers_round6_heat.md`, `critique/answers_round6_afford.md`, `critique/answers_round6_crz.md`). Each referee rebuilt the deciding number with separate code, and all ten reproduced.

One verdict changed. bridge-crz-ems-travel went from confirmed to unsettled under rule 8, because its endpoint test cannot tell the composed chain from no effect (D = 0.14, against the 4 that the rule requires). Before the round the ten claims were five confirmed, three contested and two unsettled. After it they are four, three and three.

The reading of most of the other nine was narrowed, and each outcome's `verdict_note` records how. Three of the four heat reports found that counting a shooting or an assault before 06:00 on its calendar date changes results, because the maximum of that date comes hours later. With such events counted on the previous date, the registered condition of heat-ac-shootings and that of heat-extremes-downturn are no longer met, and about half of the excess in heat-school-out goes. Those counts were chosen after the data, so under rule 4 no verdict was revised. Two affordability results were found not to be blind, because a faulty simulated run had shown a distorted view of the result before registration. No rule was added. Twenty-five outcomes now carry a `verdict_note`.

## 3. The set of relationships

There are 74 registered claims, and 73 have outcomes. Twenty-five are confirmed, 13 contested, 30 unsettled and one bridged. Four could not be tested. The claim without an outcome, construction-2022-rush-units-2027, is prospective: its data do not exist until 2027.

The dashboard places each claim on a scale from −1, where the city data contradict the research, to +1, where they agree. The interval is drawn as a bar, so an unsettled claim visibly crosses the middle.

The dashboard lists all 74 claims. The first four sections below describe the main results among the first 27 claims, of which ten are confirmed, four contested, ten unsettled, one bridged and two not tested. Some of those ten confirmations are links inside a bridge, or replications of another claim. Of the four contested claims, one is a link of the trees chain and one is described under the usual case. The later sections list the 46 claims added on 12 and 13 November, each with its verdict after the fourth, fifth and sixth referee rounds and its main estimate with a 95% interval, as recorded in the outcome files. Where an earlier write-up in `docs/` gives a different verdict or number, the outcome file is the current one.

### Confirmations

- **Heat and shootings.** Daily shootings rose by a factor of 1.146 per 5 °C of Central Park maximum temperature (1.130 to 1.163; 24,429 incidents, 2006 to 2026). Heat-related ED visits rose by a factor of 4.09 per 5 °C. Both agree with the published estimates. The graph has no finding that links temperature to gun violence, so the research estimate for that claim came from the published literature.
- **Congestion pricing and speed.** Taxi and FHV speeds in the zone rose by 5.7% (2.9 to 8.6), relative to the rest of the city.
- **Vacant land and shootings.** Shootings rose by a factor of 1.17 per quintile of vacant-land share across 2,208 census tracts. This is similar in size to the Philadelphia evidence. The association disappears within neighbourhoods, so it is a between-neighbourhood pattern.
- **Visible construction.** On 1 November 2026, 7,585 jobs had an active sidewalk-shed permit and 3,301 had an active new-building permit. Most construction a pedestrian sees is facade work and repair, not new buildings.
- **Permit rows and buildings.** The legacy permit table has 6.9 rows per new-building job for 2010 to 2019. Two out-of-sample replications gave 5.9 (2000 to 2009) and 12.8 (DOB NOW). Counting permit rows overstates the number of buildings several times over.

### Conflicts

- **Congestion pricing and NO2.** The research predicts lower NO2 in the zone. The city's own monitoring network shows +0.9% (−2.2 to +4.2), which meets the registered refutation. To settle it, one would need a zone-edge monitor network with a pre-period, together with traffic-composition data, since trucks and buses were priced differently.
- **Trees, heat and ED visits.** This is the challenge's own example of a bridge. Neighbourhoods with more trees have slightly warmer surfaces, and neighbourhoods with hotter surfaces have fewer heat-related ED visits. Both associations run opposite to the research. Density, wealth and race drive tree cover, surface temperature and ED use at once, so the neighbourhood-level data cannot test the bridge. Within-neighbourhood or individual-level data would settle it, as would using the timing of tree planting as an instrument.

### Bridges

- **Heat, shootings and EMS: bridged.** In the city data, heat raises shootings, and each shooting produces about 1.25 EMS gunshot dispatches. Together these predict an EMS rate ratio of 1.099 per 5 °C. The observed ratio is 1.111 (1.100 to 1.121). The referee showed that the test is not specific: a general claim that heat raises violence-related EMS dispatches would also pass it.
- **Congestion pricing, speed and crashes: unsettled.** The speed and volume terms cancel, so the composed prediction is near zero. An endpoint near zero cannot distinguish the chain from no effect.

### The usual case

One contested claim shows that "contested" can mean two things. We predicted that app-based taxi pickups per resident would rise with distance from the subway, as the transit-desert argument suggests. They fall: the elasticity is −0.30 (−0.38 to −0.21) across 174 outer-borough taxi zones. That contradicts our bet but agrees with the one peer-reviewed study (Barajas and Brown 2021). The verdict records the disagreement with the bet. The dashboard's agreement scale records the agreement with the research.

Nine other claims among the first 27 are unsettled and two could not be tested. In most of them, the research reports an individual-level or randomised effect, while the city publishes area-level aggregates. Air pollution and asthma is an example: the NYC estimate of 1.22 per 10 ppb NO2 is close to the research value but has an interval from 0.81 to 1.85.

### Reproductions of published city numbers

Six claims recompute a number that a city or state agency published (`docs/reproduction.md`, `docs/further.md`). They have no research side. The verdict says whether the open data reproduce the number under the registered reading of the agency's method.

- repro-mmr-cbd-speed is confirmed. The recomputed yellow-taxi speed in the Manhattan business district for fiscal 2026 is 6.62 mph against the published 6.5 mph. The difference is 0.12 mph, and it runs from −0.07 to 0.14 mph across the readings that reproduce both years. Five of the nine registered readings pass, so the agency's method is not identified.
- repro-dcp-2025-completions is confirmed. The Housing Database gives 38,689 units completed in new buildings in 2025 against the published 38,682, a difference of 0.02% (−0.32 to 0.36; the band is the size of one earlier revision, not a sampling interval). The match is on release 26Q2.1, not on the 25Q4 release that the snapshot used. The permit figure in the same snapshot was not reproduced.
- repro-dot-2025-deaths is contested. The open NYPD tables give 229 traffic deaths for 2025 against DOT's 205, which is 11.7% more, against a tolerance of 5%. A count has no sampling interval. The injury counts reproduce within 0.5%. The verdict says that the open tables do not reproduce DOT's reconciled count. It does not say that DOT's count is wrong.
- further-subway-crime-per-million-repro is contested. The registered table gives 1.11 major felonies per million riders in 2025 against the State's 1.65, a ratio of 0.67 (0.64 to 0.71). The referee showed that NYPD subway complaints over subway ridership give 1.653. That reading was found after the data, so it cannot decide the verdict.
- further-chinatown-shift is contested. The recomputed change in Chinatown's Asian and Pacific Islander residents from 2010 to 2020 is −21.5% (−26.7 to −16.2; 90% margin of the survey), inside the registered band. The 2010 and 2020 counts are each about 7% below the published ones, outside the 5% tolerance. The published table uses two different sets of census tracts for the two years.
- further-repro-dsny-rat-sightings is unsettled. The recomputed fall in 311 rat sightings is 20.9% against the stated 20.6%. One of the two annual counts is 1.15% above the published count, outside the 1% tolerance. These are counts and have no interval.

### Transit, vegetation and other city claims

Ten further claims test a relationship in city data (`docs/transit.md`, `docs/further.md`, `docs/heat.md`, `docs/bridges.md`).

- transit-weekday-pattern is confirmed. The Monday and Friday deficit in subway entries in the Manhattan business district, relative to Tuesday to Thursday, grew by 8.7 percentage points (6.9 to 10.9) between 2019 and the 12 months to October 2026. The pattern is confirmed. Its attribution to hybrid work is not tested, and about half of the change also appears outside the business district.
- transit-gtrain-substitution is unsettled. Uber and Lyft pickups rose by 0.043 log points (0.001 to 0.084) in zones whose G-only stations had no service in summer 2024. The permutation test across zones gives p = 0.19, and the registration required p below 0.05.
- transit-fhv-price-subway could not be tested. The registered first stage failed: taxi pickups did not fall after the 2019 surcharge (+1.8%, −0.9 to 4.6). The subway estimate, −0.7% (−2.0 to 0.6), is not used for the verdict.
- heat-trees-canopy-within-nta is confirmed. Within the same neighbourhood and day, afternoon air temperature is 0.20 °C lower per 10 percentage points of vegetation within 50 m of the sensor (0.15 to 0.25 lower; 420 sensors). Vegetation 200 to 300 m away predicts temperature as strongly, so the confirmed claim is the association and not a local cooling effect.
- bridge-crz-injury-crashes-v2 is unsettled. Injury crashes in the congestion zone changed by +4.5% (−2.7 to 12.2) relative to Manhattan north of 60th Street, against a composed prediction of −2.2% (−9.2 to 5.5). The 2024 placebo is +15.2% (4.8 to 26.6), so the two areas were diverging before pricing began.
- further-zonej-demand-growth is contested. Weather-normalised electricity use in NYISO Zone J changed by −0.75% a year over 2015 to 2025 (−0.84 to −0.67 as registered; −1.03 to −0.48 with errors clustered by year), against a registered claim of growth above 0.5% a year. The fall is a step of about −5.7% across 2020 and 2021 and not a steady trend. The result does not test NYISO's statewide forecast.
- further-tidal-flooding-311 could not be tested. There were 20 rain-free flood days against a registered minimum of 30. The secondary rate ratio of 15.7 (4.3 to 33.4) is not used for the verdict. The claim was registered again as further-tidal-flooding-trend, listed under round 2.
- further-containers-rats-cd9 is unsettled. Rat sightings in the containerised district changed by a rate ratio of 1.02 (0.86 to 1.23) relative to four adjacent districts. The spread across untreated districts gives a wider interval, 0.69 to 1.49.
- further-datacentre-share-manhattan is contested. Its upper-bound measure, whole-building electricity of every listed building, was 11.8 percentage points above the national 4.4% share (11.1 to 12.5). The measure counted all the electricity of mixed-use buildings as data-centre use. The second registration, listed under round 2, supersedes it.
- further-subway-crime-per-ride-by-hour is unsettled. Late-night major felonies per subway entry are 0.97 times their 2019 level (0.86 to 1.08), so the registered claim that the late-night rate stayed above 2019 is neither supported nor refuted. The late-night rate is 15.0 times the daytime rate (13.3 to 17.0).

### Graph experiments

These studies ask what the graph adds to a city analysis (`docs/graph_experiments.md`).

The coverage study looked up both ends of each of the 44 claims registered at the time. Six claims had concepts at both ends and a finding that links them. Nine had both concepts and no linking finding. Nine had only study variables at one end, and 20 had nothing usable at one end. The graph holds nothing on permits, electricity, congestion pricing or transit operations.

- graph-confounders-commute-obesity is unsettled. With the adjustment set read from the graph's shared neighbours, obesity is 4.40 percentage points lower per 10 points of walking or cycling to work (1.23 to 7.58 lower; 42 neighbourhoods). The slope is 26% smaller than with poverty alone. The registration required one third, and the referee's bootstrap interval for the attenuation runs from −14% to +64%.
- heat-mech-outdoors is confirmed. Street-noise complaints, a proxy for people outdoors, remove 0.44 (0.33 to 0.56) of the temperature slope of shootings over 2010 to 2026. The share is 0.24 in 2010 to 2019 and 0.84 in 2022 to 2026, and next-day complaints, a negative control, remove 0.10.
- heat-mech-intox is unsettled. EMS dispatches for drugs and alcohol remove 0.14 (0.09 to 0.19) of the slope. This is above the registered ceiling of 0.10 and below the 0.25 that would contest the claim.

### Discovery studies

These studies start from the graph and ask what it makes testable in city data (`docs/graph_discovery.md`).

- graph-concordance-matrix is confirmed. For 109 pairs of neighbourhood indicators on which the graph holds consistent findings, the sign of the city correlation matches the literature's majority sign in 66.1% of pairs (59.6% to 78.0%). The registered condition, at least 60%, is met on the point estimate. A rule that always answers "positive" scores 64.2%, and pairs of an exposure with an outcome agree in 29 of 56. The confirmed claim is that adverse indicators are positively correlated across neighbourhoods after poverty is partialled out. The test does not show that the graph's signs carry information about the city.
- transfer-chicago-heat-shootings is confirmed. In Chicago, shootings rise by a factor of 1.131 per 5 °C (1.120 to 1.143), against 1.146 (1.130 to 1.163) in New York. The average slope transfers, but the shape differs: the Chicago curve flattens above 20 °C and the New York curve steepens.
- transfer-chicago-weekday-pattern is contested. The Monday and Friday deficit in the Chicago Loop grew by 15.9 points (12.0 to 22.7), above the registered limit of 13.1 and about 1.8 times the New York change. The sign and the midweek plateau transfer, and the size does not. The interval crosses the limit, and rule 10 applies.
- graph-triad-cold-asthma-absence is unsettled. School absence on cold days is 1.10 times that on other days of the same week of the year (1.05 to 1.15), and 1.07 with an influenza control. The chain through asthma predicts 1.007 and accounts for about 8% of the association. The endpoint test does not separate the chain from no effect (D = 3.0, below the 4 that rule 8 requires). The referee round changed this verdict from confirmed.
- graph-triad-hot-asthma-absence is unsettled. The absence ratio on hot school days is 1.009 (0.970 to 1.050).
- split-temp-covid-growth is unsettled. Weekly growth in COVID-19 hospital admissions changes by +0.0058 log points per 1 °C of temperature anomaly (−0.0036 to 0.0152), against a registered range of −0.030 to −0.003.
- split-temp-asthma-ems is unsettled. In October to March, asthma EMS dispatches change by a factor of 1.002 per 5 °C (0.993 to 1.012), against a registered range of 0.95 to 0.99. The bound applies to variation within a month at lags of up to three days.

### Round 2

Round 2 registered again, or followed up, eight earlier results (`docs/round2.md`).

- further-datacentre-share-manhattan-v2 is confirmed. The high figure for data-centre electricity is 2.26% of Manhattan's benchmarked grid electricity, 2.14 percentage points below the national 4.4% (2.02 to 2.25 below). The low figure is 1.01% (0.96 to 1.06). The result is an allocation of landlord-reported electricity and not a measurement of data-centre load, and one of the four registered conditions passes by 0.01 points.
- further-tidal-flooding-trend is confirmed. On dry days in 2010 to 2019, flooding complaints from the coastal ZIP codes rise by a factor of 2.00 per 10 cm of water level at the Battery above the knot (1.64 to 2.38), and by 1.74 times the rise in other ZIP codes (1.43 to 2.09). The direction and the larger rise on the coast are confirmed. The size depends on the knot, and the Rockaway ZIP codes carry most of the effect.
- graph-confounders-trees-surftemp is unsettled. Adding the graph's common causes changes the slope of surface temperature on street-tree density by −0.25 °F per standard deviation (−0.99 to 0.58), after the referee's correction of population density. The registration required a fall of at least 0.3.
- graph-confounders-surftemp-ed is unsettled. Adding the share of older adults who live alone changes the slope of heat-stress ED visits on surface temperature by +0.59 percentage points per 1 °F (−1.27 to 3.42), which is 0.09 outside the registered band.
- retimed-ems-presence is confirmed. Daytime EMS incidents in the Manhattan business district fell on Mondays and Fridays with an elasticity of 0.45 to subway entries (0.17 to 0.70). The fall is concentrated in Midtown, and without community district 105 the interval includes zero.
- retimed-taxi-fhv-pickups is unsettled. The slope of the change in Monday and Friday pickups on the change in entries across taxi zones is 0.50 (0.13 to 0.81), inside the registered range. The second registered measure, the most-thinned third of zones against the least-thinned third, is −1.1% (−3.4 to 1.5).
- retimed-daytime-burglary is unsettled. The Monday and Friday ratio of daytime residential burglaries changed by a factor of 1.011 (0.953 to 1.077) between 2015 to 2019 and 2023 to 2026, against a registered fall of 5% to 10%. The referee round changed this verdict from contested.
- transfer-chicago-hot-end is unsettled. In Chicago, shootings rise by a factor of 1.058 from 27 to 33 °C (1.014 to 1.105) while bicycle trips change by 0.949 (0.896 to 1.005), as in New York. The proxy removes 0.10 (0.04 to 0.25) of the rise in shootings from 15 to 21 °C, below the registered 0.20.

### Round 5

Round 5 followed up the hot-day rise in shootings and the concordance matrix (`docs/round5.md`).

- heat-night-minimum is unsettled. On days with a maximum of 27 °C or more, New York shootings change by a factor of 1.033 per 5 °C of the preceding night's minimum at a fixed maximum (0.962 to 1.109; 1,667 days), and Chicago shootings by 1.009 (0.967 to 1.054). The interval includes no effect, the 1.012 composed from the graph's findings on sleep, and the 1.075 that would carry half of the hot-day excess. Shootings between 00:00 and 05:59 rise by about 1.11 per 5 °C of the day's maximum in each city, but that block was singled out after the data.
- transfer-chicago-concordance-matrix is confirmed. Of 15 pairs of PM2.5, ozone or traffic with a health outcome, 12 have the literature's sign across Chicago's 77 community areas (80%; bootstrap interval 53% to 87%), against 6 of the same 15 in New York. The confirmed claim is this count. The difference is PM2.5 alone, Chicago's PM2.5 measure is a regional gradient with a range of 0.7 µg/m³, and with position in the city adjusted for 1 of its 6 pairs agrees. The test does not show that residential sorting explains the New York result.
### Round 6

Round 6 registered ten claims on affordability, on what could reduce the rise of shootings with heat, on extreme heat, on street trees and rent, and on the congestion toll (`docs/affordability.md`, `docs/heat_solutions.md`, `docs/heat_extremes.md`, `docs/all_boats.md`, `docs/congestion_tradeoffs.md`, `docs/policy_simulation.md`). Each entry gives the outcome as revised after its referee report.

- afford-gentrification-prevalence is confirmed. Of the 22 sub-borough areas with the lowest rents in 2000, 8 had both rent and the share of college graduates grow faster than the city's by 2022-2024 (36%; Wilson interval 20% to 57%), and across all 55 areas the two kinds of growth have a rank correlation of 0.68 (0.50 to 0.80). The registrant saw a distorted simulated view of the result before registering, so this is a measurement under a fixed definition and not a blind prediction. The count runs from 5 to 12 under 35 other versions of the definition. Six of the other 33 areas also meet both conditions (18% against 36%; Fisher p = 0.21), so the data do not show that low-rent areas gentrified more often than other areas.
- afford-poor-count-shift is confirmed. The log change in the number of residents below the poverty line from 2000 to 2022-2024 was 0.283 lower in the 8 gentrified areas than in the 14 other low-rent areas (−0.544 to −0.021). The registered condition, an upper limit below 0, is met by 0.02. Six of the 22 single removals of an area put the upper limit at or above 0, and with borough terms the interval includes zero (−0.173, −0.479 to +0.132). The end period follows a change of survey boundaries. An exploratory repeat with 2017-2019 gives −0.24 (−0.35 to −0.14). The claim concerns the change of a count and is not evidence on displacement.
- heat-ac-shootings is confirmed. The slope of shootings on temperature is steeper in the half of community districts with less household air conditioning: the difference of log slopes per 5 °C is 0.043 (0.007 to 0.080; 6,932 days). The result is not evidence of an air-conditioning effect. The difference comes from days below about 20 °C, when air conditioners are off, and at 27 °C and above it is −0.178 (−0.329 to −0.027). It is 0.025 (−0.011 to 0.061) when the day runs from 06:00 to 05:59, and 0.034 (−0.007 to 0.076) within income halves pooled.
- heat-ac-heat-calls is contested. The heat slope of ambulance calls coded HEAT does not differ between the two halves of districts: −0.032 (−0.088 to 0.024; 15,754 calls on 1,920 days). The interval excludes the 0.112 expected if every call came from a home. Calls are located where the patient was found, so the result excludes household protection of the size the case-control studies report only if more than about 17% of HEAT calls come from homes, and the data do not give that share.
- heat-school-out is unsettled. On weekdays within 42 days of the last or first day of classes, shootings on days out of school are 1.105 times those on school days at the same temperature (0.997 to 1.224; 2,260 weekdays). About half of the excess is holiday nights, chiefly the night of 4 July, counted on the following weekday: the ratio is 1.060 (0.957 to 1.173) without weekdays after a public holiday and 1.044 (0.951 to 1.146) on days from 06:00 to 05:59. It falls from 1.217 at a 21-day window to 1.024 at 70 days. A term for the summer recess removes 1.5% of the log slope of shootings on temperature.
- heat-extremes-downturn is contested. Pooled over Phoenix, Tucson, Dallas and Austin, aggravated assaults on days at 38 °C or more are 1.035 times those on days at 32 to 35 °C (1.008 to 1.063; 2,696 hot days). Contested means here that the registered downturn, a ratio of 0.88 to 0.98, is refuted. The rate is level or slightly higher. The lower limit above 1.00 is fragile: it is 0.992 with a Hartung-Knapp interval and 0.994 on a day from 06:00 to 05:59. As a planned description, the slope per 5 °C is 1.060 (1.046 to 1.073) from 20 to 35 °C and 1.003 (0.985 to 1.022) above 35 °C.
- all-boats-trees-rent is unsettled. Across 2,048 census tracts the change in log median rent from 2008-12 to 2018-22 rose by 0.0127 per 100 added street trees (0.0018 to 0.0235), and neither registered condition is met. Over other defensible forms the slope is 0.007 to 0.033 with intervals from below zero to 0.057, and the measure of trees is only partly a measure of planting. These data cannot say whether street trees raised rents.
- crz-storefront-vacancy is confirmed. Storefront vacancy in the congestion zone changed by −0.47 percentage points relative to the rest of the city between the end of 2024 and the end of 2025 (−1.08 to +0.17). Zone vacancy itself rose by 0.2 points, and vacancy elsewhere rose by 0.65. A rise of 1.2 points relative to the whole rest of the city is ruled out, with sampling error only, and nothing smaller is. It is not ruled out against downtown Brooklyn and Long Island City (+1.09, −0.60 to +2.85) or against the zone's earlier values (upper bound +1.66).
- bridge-crz-ems-travel is unsettled. Peak ambulance travel time in the zone changed by −0.9% relative to the rest of the city (−3.0 to +1.4; 32 months), against a composed prediction of −1.8%. The endpoint test cannot tell the chain from no effect (D = 0.14), and the referee round changed this verdict from confirmed. No improvement is shown. Overnight, when the toll is a quarter as large, the zone's relative travel time fell by 4.0% (1.7 to 6.3), which argues against the toll as the cause. The number of lives is not a result: its sign is not determined.
- sim-crz-holdout-2026 is contested. The elasticity of zone taxi speed to vehicle entries on held-out weekdays of January to June 2026 is 0.29 of the value fitted on 2025 (0.19 to 0.38; 123 days), below the registered limit of 0.5. Two storm days carry 84% of the identifying variation, and without 23 February alone the verdict would be unsettled. Vehicle entries vary by about 3% within the fixed effects, so day-level data cannot identify the relation in either year. The ambulance link transferred in slope (1.10 of the fitted value, 0.72 to 1.48).

## 4. The graph as an object

The graph (`docs/graph.md`) has 1,999,877 associations from 844,435 studies, grounded to 45,721 Wikidata concepts.

- **Coverage.** Urban, environmental and social topics make up about 2% of associations. "Heat wave" has one finding. The graph held no findings on permits, completions or road pricing.
- **API and deposit.** 46% of sampled API associations are absent from the Dataverse deposit, mostly rows with an ungrounded variable. Among fully grounded rows, 19.9% are absent, which matches the documented error rate. API responses carry no version identifier.
- **Sign of findings.** The record for a relationship gives the number of findings but not their sign. In 52% of relationships with five or more signed findings, there are significant findings in both directions.
- **Extraction errors.** We checked findings our claims relied on against their abstracts. The errors included an ED-visit change stored as a crime effect, percent changes stored as odds ratios, and "eviction moratoriums" grounded to the plant genus *Eupatorium*.

The later studies found further grounding errors. Nine of the 21 findings between "flood" and post-traumatic stress disorder are trials of the therapy technique called flooding. A finding on the body temperature lost by trauma patients is stored under ambient temperature.

For a project like this, the graph works best as an index into the literature, with each finding checked against its source, and not as a table of effect sizes.

## 5. Research needed

The dashboard's research-needed map groups every claim's "settle" condition by the kind of data or design that is missing. Three needs appear repeatedly:

- **Individual-level or within-area data.** Most confirmations and conflicts here rest on ecological (area-level) data. The research they are compared with does not.
- **Measurement independent of reporting.** 311 complaints measure how readily people report as much as they measure exposure. Permit records measure paperwork as much as building. Sensors, inspections and aerial images give a second record, but public NAIP images stop in 2022.
- **Registrations made before the data exist.** Only a prospective test is out of sample for the four-year completion rate. The four-year window for the 2023 cohort closes in 2027. One such test is now registered: construction-2022-rush-units-2027 predicts the share of units permitted in the first half of 2022 that will be complete by 30 June 2027. GitHub received the registration on 12 November 2026, before its data exist.

## 6. Versions and provenance

Every NYC result carries the dataset id, its `rowsUpdatedAt`, the exact SoQL and the fetch time. NOAA results carry the station file's Last-Modified header. The Dataverse files are checked against the manifest's SHA-256.

The evidence that each prediction came before its data is the git history and the fetch times recorded in each outcome (`docs/provenance.md`). All 74 registration hashes match. Each of the 63 earlier registration commits precedes its outcome commit, and each of the ten registrations of round 6 was committed alone to a branch `prereg/<id>` with a commit time 12 to 40 minutes before the commit of its outcome. Where an outcome cites data fetched before its registration, the data are an exposure, a zone boundary or a link reused by a bridge, not the outcome measure. The repository was pushed to a private GitHub remote on 12 November 2026. GitHub's push times are a third-party record, but the 27 earlier claims arrived in one push with their outcomes, so that record does not separate them. Making the repository public, or timestamping the registration hashes with a public service, would let others check it. The claim set can be exported as an Underlay collection (`tools/underlay_export.py`), but the collection has not been published.
