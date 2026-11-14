# Referee report: ems-traffic-hourly-elasticity

The recorded verdict is confirmed, with an elasticity of Manhattan ambulance travel time to same-hour yellow-taxi time per mile of 0.633 (0.601 to 0.664) in the joint model with the next-week lead. My independent rebuild gives 0.636 (0.605 to 0.668), and beta_x − beta_lead = 0.624 (0.573 to 0.674) against the registrant's 0.621 (0.570 to 0.671). Both registered conditions are met by a wide margin, so under rule 1 the verdict stands.

The registered placebo is weak. Taxi pace a week later cannot detect a shared cause within the hour, such as rain, an event or a demand surge, because such causes do not recur a week later, and the 2017-2018 calibration had already shown the registrant that the lead would be near zero (−0.04). I ran same-hour placebos. Brooklyn taxi pace in the same hour, entered with Manhattan pace, has a coefficient of 0.048 (0.018 to 0.077), and the Manhattan coefficient does not move (0.630). Pace two hours later has 0.075 (0.030 to 0.119) with current pace in the model, which lowers the current coefficient to 0.50. The elasticity is not a common citywide shock. Its size as a causal ratio ("an ambulance is slowed by about two thirds as much as a taxi") depends on the time window and is not identified.

I wrote my own code before reading `docs/ems_response.md`. My scripts are outside the repo and are not committed.

## Data

- 76xm-jjuj, EMS Incident Dispatch Data (FDNY), rowsUpdatedAt 2026-10-07T14:42:18Z. I fetched it on 13 November 2026 from 13:49 EST, with my own SoQL sent directly to the resource endpoint: 39 quarterly queries, `borough='MANHATTAN'` and `valid_incident_rspns_time_indc='Y'`, grouped by `date_trunc_ymd(incident_datetime)`, `date_extract_hh(incident_datetime)`, a ZIP-based area (the registered crz and north ZIP lists from `analyses/congestion/common.py`) and severity (initial severity 1-3 against the rest), with count, sum of `incident_travel_tm_seconds_qy` and sum of `dispatch_response_seconds_qy`. The registrant's 2019-2026 rows come from `analyses/congestion/ems_fetch.py`, which has no borough filter; the difference is two cells out of 107,296.
- TLC yellow trip records, monthly parquet, aggregated by my own DuckDB query (filter f1: 0 < miles ≤ 50, 60 s ≤ duration ≤ 3 h, 0.5 to 50 mph; both ends in the area). Local copies: `~/opt/nyc-concordance/tlc_yellow_1720/` for 2017-01 to 2020-02 (Last-Modified 30 June 2022 in the registrant's records) and `~/opt/nyc-concordance/ems_response/tlc/` for 2021-07 to 2023-06 and 2026-01 to 2026-09 (Last-Modified from 30 June 2022 to 29 October 2026, in the `.headers` files beside them). For one month (2019-03) my cbd and north cells match the registrant's `taxi_parts/2019-03.csv` exactly.
- July 2023 to December 2025 are not on disk. The folder `~/opt/nyc-concordance/tlc_yellow/`, which the congestion and reproduction scripts read, is empty. For those months I used `data/derived/congestion/taxi_speed_2023-07_2024-12.csv` and `taxi_speed_2025-01_2026-06.csv`, as the registrant did; their file versions are in `data/derived/reproduction/mmr_cbd_speed_files.json`.

## Order of registration and data

The estimators (`lib.py`, `taxi_hourly.py`, `ems_fetch.py`) and the 2017-2018 calibration were committed in f44ab0b at 13:26:37 on 13 November, and the registration in d75fa5e at 13:27:13. The `prereg/` branch for this claim points at d75fa5e. The registrant's own taxi files for 2019 to 2026 have file times from 13:32 to 13:40, and the outcome was committed in e63ef7f at 13:43:44. The order of estimator, registration and the taxi computation is as stated.

Two qualifications belong in the outcome. The EMS rows for 2019 to 2026 (`data/derived/congestion/ems_YYYY.csv`) and the taxi rows for July 2023 to June 2026 (`taxi_speed_*.csv`) were committed in 1819abd at 08:44:57 on the same day, before the registration. The registration's commit message ("before 2019-2026 taxi data") is therefore not accurate for those 30 months. Nothing shows that the registrant joined them before registering. The prior monthly estimate from the same data (0.32, bridge-crz-ems-travel) is disclosed in the literature field.

## Rule 9: the change to `lib.taxi_hourly` after registration

The registration names `taxi_hourly.py` as the source of taxi pace. After registration, `lib.taxi_hourly` was changed to fill months it had not computed from the congestion files, and `taxi_hourly.py` was changed to download with curl and cache by month. The estimators (`panel`, `fe_elasticity`, `t1`) were not changed (`git diff f44ab0b e63ef7f`).

I checked whether the substitution changed the measure. `analyses/congestion/taxi_speed.py` uses the same CBD and MN_NORTH zone lists, the same filter, pickup date and hour, and the same sums. The two areas do not share a zone, so its `case` assignment of a trip to one area is equivalent to the EMS script's separate counts. For January to June 2026, where both sources exist, the 8,686 cbd and north cells are identical: counts and hours exactly, miles to 4e-11. Restricting the model to months computed from raw files gives 0.649 (0.605 to 0.694) on 65,351 cells. The substitution did not change the registered procedure in substance. No resampling is involved, so the seed and draw provisions of rule 9 do not apply.

## 1. Rebuilding the deciding number

My fixed effects are absorbed by sparse least squares (LSQR on the weighted dummy matrix) rather than by alternating projections, and my week-clustered sandwich is written separately. Only the first row is registered and deciding; rows marked EXPLORATORY are mine.

| Model | Coefficient on taxi pace (95% CI) | Cells |
|---|---|---|
| Registered joint model, beta_x | 0.636 (0.605 to 0.668) | 107,294 |
| Same, beta_lead (next week) | 0.012 (−0.023 to 0.047) | |
| Same, beta_x − beta_lead | 0.624 (0.573 to 0.674) | |
| x alone (registered secondary) | 0.638 (0.607 to 0.669) | 108,370 |
| Lead alone (registered secondary) | 0.164 (0.117 to 0.211) | 107,294 |
| Life-threatening only, joint (registered secondary) | 0.496 (0.467 to 0.525) | 88,086 |
| Joint, raw-file months only | 0.649 (0.605 to 0.694) | 65,351 |
| By year, joint | 0.59 (2025) to 0.69 (2020, January-February) | |

Same-hour placebos (EXPLORATORY; raw-file months, where Brooklyn, Queens and Bronx pace exist):

| Model | Manhattan pace | Placebo term |
|---|---|---|
| Brooklyn pace alone | | 0.151 (0.115 to 0.187) |
| Queens pace alone | | 0.097 (0.066 to 0.128) |
| Manhattan and Brooklyn | 0.630 (0.574 to 0.687) | 0.048 (0.018 to 0.077) |
| Manhattan, Brooklyn and Queens | 0.618 (0.555 to 0.681) | BK 0.060 (0.022 to 0.098); QN 0.023 (−0.010 to 0.056) |
| Manhattan only, same cells as the Brooklyn rows | 0.646 (0.589 to 0.702) | |
| Pace 2 hours later alone | | 0.401 (0.355 to 0.446) |
| Pace 2 hours earlier alone | | 0.488 (0.444 to 0.533) |
| Current, 2 hours earlier and 2 hours later | 0.502 (0.452 to 0.553) | earlier 0.198 (0.152 to 0.244); later 0.075 (0.030 to 0.119) |
| Same, full sample | 0.491 (0.453 to 0.530) | earlier 0.170 (0.133 to 0.208); later 0.088 (0.055 to 0.121) |
| Current and 1 hour later | 0.560 (0.509 to 0.611) | 0.113 (0.062 to 0.164) |
| Current and the other Manhattan area | 0.584 (0.539 to 0.630) | 0.155 (0.115 to 0.196) |

## 2. Does the verdict follow from the registration and PRECEDENCE?

It does. Both lower bounds are far above 0.10, and the estimate is inside the registered 0.3 to 0.9. Rule 1 gives confirmed. The registered placebo (the lead) does not meet support_if, so rule 11 does not change the verdict. Rule 8: with se 0.016 and a predicted 0.4, D against no effect is far above 4.

## 3. Are the fixed effects and the placebo adequate?

The fixed effects (date × area, and area × year × weekday × hour) remove the day's level and the regular hour-of-week pattern. They leave every within-day deviation, including those caused by weather in a given hour, events and demand surges. The incident-count controls are the only defence against those.

The next-week lead is a placebo against slow-moving hour-of-week causes, such as road works lasting several weeks. It is not a placebo against the alternative the registration names ("a shared within-hour cause, such as rain or an event"), since rain next Tuesday at 17:00 is unrelated to rain this Tuesday at 17:00. It was almost bound to pass, and the calibration showed it would.

Brooklyn pace is a better same-hour placebo. Brooklyn yellow trips share the city's weather, holidays and transit disruptions but not Manhattan streets, and Brooklyn ambulances do not serve Manhattan incidents. Alone it has a coefficient of 0.15, which would meet the registered lower bound of 0.10 if it were the test variable, because it is correlated with Manhattan pace. Entered with Manhattan pace it falls to 0.05, and the Manhattan coefficient is unchanged. On the same cells the Manhattan estimate (0.646) is 17 standard errors from the Brooklyn placebo value (0.151), so under rule 11 the design discriminates from this placebo. A citywide within-hour shock contributes at most a small part of the estimate.

Pace in neighbouring hours is a less clean placebo, because traffic persists and because an ambulance dispatched at 17:50 drives in the next hour. Even so, pace two hours later still has 0.075 (0.030 to 0.119) given current pace, and the earlier hour has 0.20. Two readings fit. One is that a single hour's taxi pace measures the traffic an ambulance meets with error, so that neighbouring hours add information; then the current-hour coefficient is attenuated, and the sum of the three coefficients (0.76) is nearer the response to a lasting change. The other is that busy periods spread over several hours, through a shared cause or through queueing (slow traffic keeps units busy and the next unit is farther away). These data cannot separate the two. Either way the coefficient on the current hour alone is not "the" ratio of ambulance slowing to taxi slowing.

## 4. The prose in docs/ems_response.md

I read the doc after finishing the rebuild. Its numbers for this claim match the outcome and my rebuild. It claims more than the numbers support in three places.

1. "An ambulance with lights and sirens is slowed by about two thirds as much as a taxi when traffic slows, and by half on life-threatening calls." This reads the hourly coefficient as a causal ratio. The coefficient moves from 0.64 to 0.50 when adjacent hours are entered and their sum is 0.76, and it is likely attenuated by sampling error in hourly taxi pace. Not every incident uses lights and sirens. The sentence should say that ambulance travel time moves with same-hour taxi pace with an elasticity of 0.63, and that the ratio for a lasting slowdown is not identified.
2. "So the association is not a shared slow-moving cause of the kind that broke the hospital-turnaround test." This is correct as stated, but the doc should add that the lead says nothing about within-hour causes, and report a same-hour placebo. The Brooklyn result above supports the doc's reading better than the lead does.
3. The novelty section calls 0.63 an estimate "of the size of the traffic effect on ambulances in New York ... with a placebo". The placebo was weak and the size depends on the window, as above. "Association" is the right word.

## 5. What would settle it

The settle text (FDNY vehicle location traces on matched segments) is right. Hourly precipitation (NOAA ISD for Central Park) as a control, and a registered same-hour placebo in another borough, would test the named alternative with open data. Repeating the model with high-volume FHV trip speeds would test whether the elasticity is the same where yellow taxis are thin.
