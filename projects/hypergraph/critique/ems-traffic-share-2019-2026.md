# Referee report: ems-traffic-share-2019-2026

The recorded verdict is confirmed, with S1 = 0.331 (0.295 to 0.367): if ambulance pace had moved one for one with taxi pace, traffic would account for a third of the rise in Manhattan life-threatening travel time from January-September 2019 to January-September 2026. My independent rebuild gives 0.333 (0.298 to 0.368), from a rise of 34.8% in travel time (registrant 35.0%) and of 10.4% in taxi time per mile weighted by the 2026 incidents (registrant 10.5%). The registered condition (upper bound below 0.5) is met by 0.13, and other seeds and ten times the bootstrap draws do not move the bound near 0.5. Under rules 1 and 9 the verdict stands.

The citywide decomposition that the doc builds on this claim does not stand as written. I reproduce its arithmetic: 0.40 minutes of wait, 0.01 of call mix, 0.34 of traffic at the measured elasticity, 0.35 more at one for one, and a remainder of 1.23 minutes. The remainder is a residual. Unit locations at dispatch are not observed, so it cannot be called distance to a free unit; it holds every cause not modelled. The doc calls it "the expected result of fewer free ambulances" and concludes that "both point to fewer free ambulances". The numbers are consistent with that reading but do not test it.

I wrote my own code before reading `docs/ems_response.md`. My scripts are outside the repo and are not committed.

## Data

- 76xm-jjuj, EMS Incident Dispatch Data (FDNY), rowsUpdatedAt 2026-10-07T14:42:18Z, fetched 13 November 2026 from 13:49 EST with my own SoQL: Manhattan by date, hour, ZIP area (the registered crz and north lists) and severity group; citywide by year, month, borough, hour and severity group; and citywide January-September by year, initial call type, borough and severity group. All with `valid_incident_rspns_time_indc='Y'`, summing `incident_travel_tm_seconds_qy` and `dispatch_response_seconds_qy`.
- TLC yellow trip records for 2019-01 to 2019-09 (`~/opt/nyc-concordance/tlc_yellow_1720/`) and 2026-01 to 2026-09 (`~/opt/nyc-concordance/ems_response/tlc/`, Last-Modified 25 March to 29 October 2026), aggregated by my own DuckDB query with filter f1. Both periods of the deciding comparison come from raw files, so the post-registration change to `lib.taxi_hourly` (congestion rows for July 2023 to December 2025) does not touch the deciding number. It touches only the secondary 2019-2025 comparison.
- Mayor's Management Report, FDNY chapter, FY2019, FY2021, FY2023, FY2025 and FY2026 (PDFs in `~/opt/nyc-concordance/mmr/`).

## Order of registration and data

As for ems-traffic-hourly-elasticity: estimators in f44ab0b (13:26:37), registration in d75fa5e (13:27:13), the registrant's 2019 and 2026 taxi files written from 13:32 to 13:40, outcome in e63ef7f (13:43:44). The EMS rows for 2019 and 2026 had been in the repo since 1819abd (08:44:57) and the monthly taxi speeds for January-June 2026 had been reported in repro-mmr-cbd-speed, which the registration cites. The registrant knew before registering that Manhattan taxi speed fell 6 to 9% in early 2026 and that EMS travel time had risen. The registration discloses both.

## 1. Rebuilding the deciding number

Only the first row is registered and deciding.

| Quantity | Registrant | Referee |
|---|---|---|
| S1, Jan-Sep 2019 to Jan-Sep 2026, severity 1-3 (deciding) | 0.331 (0.295 to 0.367) | 0.333 (0.298 to 0.368), seed 7, 1,000 day-block draws |
| Same, seed 99, 1,000 draws | | (0.296 to 0.370) |
| Same, seeds 1 and 2026, 4,000 draws (ten times the registered 400) | | (0.294 to 0.370) and (0.295 to 0.370) |
| Change in log mean travel time | 0.300 | 0.299 |
| Change in log taxi time per mile, 2026 incident weights | 0.099 | 0.099 |
| S at the life-threatening elasticity (0.49) | 0.162 (0.142 to 0.184) | 0.49 × 0.333 = 0.163 |
| S1, 2019 to 2025 (secondary) | 0.202 (0.140 to 0.262) | 0.203 |
| S1, lower severities (secondary) | 0.261 | 0.263 |

The registered bootstrap has 400 day-block draws for D and the pace change and seed 20261113. I re-ran it with four other seeds, two of them with ten times the registered day-block draws; the upper bound is 0.37 under all of them, 0.13 from the threshold, so rule 9 is met.

## 2. Does the verdict follow from the registration and PRECEDENCE?

It does. The upper bound of S1 is below 0.5, and rule 1 gives confirmed. The estimate is inside the registered 0.05 to 0.45. S1 assumes beta = 1. The registration lists, as an alternative, that ambulances may be slowed more than taxis; the outcome should keep saying that S1 is an upper bound only if beta ≤ 1.

## 3. The decomposition of the 2.32 minutes (exploratory in the outcome and the doc)

The arithmetic reproduces from my own data. Citywide, severity 1-3, 2019 (full year) against January-September 2026, mean travel time rose from 6.465 to 8.393 minutes (+1.928) and mean wait for assignment from 0.496 to 0.891 (+0.396), a total of +2.324 minutes.

| Part | Doc (min) | Referee (min) | Note |
|---|---|---|---|
| Wait for a unit | 0.40 | 0.396 | |
| Call mix, borough × hour | 0.01 | 0.012 | call type gives 0.010 |
| Traffic at beta 0.49 | 0.34 | 0.33 to 0.37 | see below |
| Traffic, further amount at beta = 1 | 0.35 | 0.33 to 0.38 | |
| Remainder | 1.23 | 1.17 to 1.25 | |

Four points about the arithmetic.

1. The traffic share is a share of the log change (S1 = 0.356 = 0.0928 / 0.261), multiplied by the minute change. Scaling the 2019 travel time by exp(0.0928) gives 0.63 minutes at beta = 1, not 0.69. The difference (0.06 minutes) moves to the remainder.
2. The base is the full year 2019 and the post period is January to September 2026. With January-September 2019 as the base the total is +2.35 minutes. The difference is small.
3. The citywide traffic term depends on the choice of taxi area for Manhattan. The doc uses trips with both ends anywhere in Manhattan; with the registered cbd and north areas pooled, Manhattan log taxi time per mile rose 0.089 by day and 0.124 at night rather than 0.058 and 0.065, and the citywide S1 becomes 0.389 instead of 0.356. The doc's "at most 36%" should be "about 36 to 39%, if beta ≤ 1".
4. The outer-borough traffic terms rest on yellow trips with both ends in Brooklyn, Queens or the Bronx, which are few and concentrated in a few neighbourhoods. Queens taxi time per mile at night fell 13% from 2019 to 2026. Staten Island was given the mean of the other boroughs. The doc labels this exploratory and says the measure is thin, which is right.

## 4. Can the remainder be called distance to a free unit?

It cannot, on these data. The remainder is everything in the travel-time rise that the call mix and the taxi pace term do not explain. Distance to the assigned unit is one candidate. Others are equally consistent with the numbers:

- Ambulance-specific slowing that taxis do not share, or a response to lasting street changes (bus and bike lanes, construction, double parking) larger than the within-hour elasticity implies. The hourly elasticity identifies the response to hour-to-hour variation, not to seven years of change.
- Changes in which unit's arrival is recorded. Paramedic Response Units (non-transporting) were added from fiscal 2025 and are now counted in in-service hours (MMR FY2026). Eleven hospital-based ambulances left the 911 system in fiscal 2026.
- Recording. The share of severity 1-3 incidents without a valid response time rose from 1.8% (2019) to 3.2% (2026) (`ems_valid.csv`). The doc is right that this is small.

The night comparison is the doc's main evidence for distance. Citywide, travel time rose 27.8% at 01:00-05:59 and 31.8% at 07:00-19:59 (my January-September figures). Traffic is lighter at night but not absent: Manhattan taxi time per mile at night rose 13% (cbd and north pooled, a log change of 0.124) from 2019 to 2026. A night rise close to the day rise is evidence that something other than daytime congestion grew. It does not identify distance. The inverse-square-root calculation in the doc (a 28% rise in night travel would follow from 39% fewer free units) is a scale argument with no measured input for free units; it should not be presented as support.

## 5. The MMR in-service-hours figures

The figures in `decompose.py` and the registration match the published reports.

| Indicator | Script | Report |
|---|---|---|
| Average ambulance in-service hours per day, FY22-FY26 | 8,891, 8,686, 8,653, 8,572, 8,109 | MMR FY2026 table: same |
| Same, FY21 | 9,442 | MMR FY2025 table: 9,442 |
| Peak ambulances in service, FY15-FY23 | 405 to 466 | MMR FY2019, FY2021, FY2023 tables: same |
| End-to-end life-threatening response by ambulances, FY19, FY22, FY24-FY26 | 9:22, 10:17, 10:52, 11:21, 13:09 | MMR FY2021 and FY2026 tables: same |
| Life-threatening incidents, FY19-FY26 | 567,757 to 610,771 | same |

The in-service-hours series was redefined twice: in the FY2025 report (ALS and BLS ambulances only, and a correction of a mathematical error, with FY20-FY25 revised) and in the FY2026 report (PRUs included from fiscal 2025, which changes FY25 from 8,399 to 8,572). The script takes FY21 from the FY2025 revision and FY22-FY26 from the FY2026 revision; since PRUs began in fiscal 2025, the two revisions agree for FY21 to FY24. The doc's "fell 14% from fiscal 2021" uses a pandemic year as the base; from FY22 the fall is 8.8%. The report's own statement for FY26 is a 5% fall.

## 6. The prose in docs/ems_response.md

I read the doc after finishing the rebuild. Its numbers match the outcome and my rebuild. It claims more than the numbers support in these places.

1. The table's last row and the section "What the remainder is" call the remainder "longer distances to a free unit". It should be called the unexplained part, with distance as one candidate. Section 3 should not say that the wait and the remainder "both point to fewer free ambulances"; the wait does measure a shortage of free units at the moment of the call, the remainder does not.
2. "The night rise is close to the day rise everywhere, and traffic cannot produce it." Manhattan night taxi time per mile rose 5 to 14% depending on the area, so traffic can produce part of the night rise. The sentence should say that the night rise is larger than the night traffic change.
3. "At most 36%" should carry the assumption beta ≤ 1 and the sensitivity to the Manhattan taxi area (36 to 39%).
4. In the levers section, "the larger part is in the number of free ambulances" and "the evidence here supports supply levers" go beyond the analysis, which tested no supply measure. The residual is consistent with a supply explanation, and the MMR gives that explanation; this analysis does not confirm it.

## 7. What would settle it

The settle text is right: unit locations at assignment, and units free by hour. Two open-data steps would narrow the remainder. The share of incidents answered by a unit from another dispatch area, if `incident_dispatch_area` and a unit field can be linked, would measure cross-area response directly. High-volume FHV trip speeds by borough would replace the thin yellow-taxi measure outside Manhattan.
