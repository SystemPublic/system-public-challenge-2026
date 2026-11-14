# Referee report: ems-hospital-turnaround-wait

The recorded verdict is confirmed, with a same-day elasticity of the daily mean wait for an ambulance assignment to the daily mean time at hospital of 4.55 (3.21 to 5.88). My independent rebuild gives 4.54 (3.20 to 5.88). The registered support condition (lower bound above 0.2) is met by a wide margin and survives every control I could add, so under rule 1 the verdict stands. The practical reading does not stand. Tomorrow's time at hospital predicts today's wait more strongly than yesterday's does, and with week fixed effects neither lag has any association with the wait. The association is contemporaneous and is at least partly a shared daily cause or a recording effect. It does not show that shortening hospital offload would shorten waits, and the outcome and the doc should not present hospital turnaround as an established lever.

I wrote my own code before reading `docs/health_gaps.md`. My scripts are outside the repo and are not committed. They use my own SoQL queries through `concord/socrata.py`, aggregated by day and half-day (incidents created before and after noon), not the registrant's daily file.

## Data

- 76xm-jjuj, EMS Incident Dispatch Data (FDNY), rowsUpdatedAt 2026-10-07T14:42:18Z. Forty queries (two per half-year, 2017 to 2026), fetched 13 November 2026 between 12:33 and 12:42 EST. Per day and half-day: incident count; count and sum of `dispatch_response_seconds_qy` where `valid_dispatch_rspns_time_indc='Y'`; count of held calls; count of respiratory call types (DIFFBR, DIFFFC, RESPIR, RESPFC, ASTHMB, ASTHFC); count of transports (disposition 82); and the count and sum of close minus hospital arrival for transports, 0 to 4 hours, close and arrival in the same calendar month (the registered definition, written in my own SoQL).
- NOAA GHCN-Daily, Central Park (USW00094728), via `concord/noaa.py`, NCEI file Last-Modified 12 November 2026: daily maximum temperature, precipitation and snowfall.
- US federal holidays (pandas calendar) and 24 December to 1 January.

## Order of registration and data

The fetch and model scripts were committed in 6278c85 at 11:54:40 and the registration in be7f692 at 11:54:58 on 13 November. The registrant's first daily query was fetched at 11:55:08 and the outcome was committed in 8759fa7 at 12:21:23. The shared cache holds earlier queries of 76xm-jjuj by other agents (from 12 November and from 07:38 to 08:49 on 13 November), including hourly response times for 2024-2025 and annual sums of dispatch time. None holds hospital time. The registration discloses that the MMR annual figures were read before it. The order is as the outcome states.

## 1. Rebuilding the deciding number

The window is 2017-01-01 to 2026-09-30 without March to June 2020, 3,438 days (the registrant's fit drops the first day because of the lag column, giving 3,437). All models use Newey-West errors with 7 lags. Only the first row is registered and deciding; the rest are EXPLORATORY.

| Model | Elasticity (95% CI) |
|---|---|
| Registered: log wait on log time at hospital, log calls, weekday, year-month | 4.54 (3.20 to 5.88) |
| Previous day's time at hospital instead (registered secondary) | 1.06 (0.13 to 1.99) |
| Next day's time at hospital instead (placebo) | 2.40 (1.20 to 3.60) |
| Previous, same and next day together: same day | 4.23 (2.78 to 5.68) |
| Same model: previous day | −0.31 (−1.22 to 0.60) |
| Same model: next day | 1.28 (0.07 to 2.49) |
| + temperature bins, rain, snow, holidays | 4.47 (3.18 to 5.76) |
| + respiratory calls and transports (log) | 4.57 (3.39 to 5.75) |
| Year-week instead of year-month fixed effects, with the controls above | 3.49 (2.22 to 4.75) |
| Same, previous day's time at hospital | −0.55 (−1.48 to 0.38) |
| Same, next day's time at hospital | 0.45 (−0.65 to 1.55) |
| Weekday effects by year, year-week effects, controls | 5.43 (4.15 to 6.71) |
| First differences with weekday | 3.85 (2.10 to 5.60) |
| Registered model, 2017-2019 | 4.23 (2.30 to 6.16) |
| Registered model, 2021-2023 | 6.33 (3.73 to 8.93) |
| Registered model, 2024-2026 | 7.98 (6.11 to 9.85) |

Half-day timing, with weather, holidays, weekday, year-month and both half-days' call counts:

| Wait in | Time at hospital of incidents created in | Elasticity (95% CI) |
|---|---|---|
| afternoon | the same morning | 3.11 (1.82 to 4.39) |
| morning | the same afternoon (reverse order in time) | 1.31 (0.23 to 2.38) |
| morning | the previous afternoon | 0.02 (−0.93 to 0.96) |
| morning | the same morning | 3.66 (2.04 to 5.28) |
| afternoon | the same afternoon | 3.74 (2.71 to 4.76) |

Within a month, the standard deviation of log daily time at hospital is 0.012 (about 30 seconds on a mean near 40 minutes), against 0.42 for log daily wait. The elasticity is identified from day-to-day movements in time at hospital of about 1%.

## 2. Does the verdict follow from the registration and PRECEDENCE?

It does. The registered condition is a lower bound above 0.2 on the primary model; 3.21 meets it, and rule 1 gives confirmed. No resampling is involved, so rule 9 does not apply. The previous-day model, the severity split and the attribution of the trend were named as secondary in the registration. Nothing deciding was chosen after the data. The outcome scores the magnitude as partial, which is right: 4.55 is above the registered range of 0.5 to 3.

## 3. A shared daily cause, and the practical reading

The registration names a common daily shock, staffing, reverse causation and late closing of incidents as alternatives. The checks above bear on them as follows.

Weather, holidays, respiratory call volume and transport volume do not change the estimate (4.47 to 4.57). Measured heat, cold, snow and respiratory surges are not the shared cause.

A slow-moving shared cause within the month is present. The next day's time at hospital predicts today's wait (2.40), more strongly than the previous day's (1.06). A future value cannot cause a past wait, so the lagged estimate of 1.06 cannot be read as the part of the effect that survives common shocks. With year-week fixed effects, which absorb weekly changes in staffing, influenza waves and fleet, both the lag and the lead are near zero (−0.55 and 0.45), while the same-day estimate falls to 3.49.

The remaining association is contemporaneous within hours. Morning time at hospital predicts afternoon waits (3.11), but afternoon time at hospital also predicts morning waits (1.31), which is the wrong order in time, and the previous afternoon predicts nothing (0.02). A queueing effect of hospital time on ambulance availability would decay within hours, so the null at 12 hours does not rule it out. The reverse-order estimate of 1.31 shows that a shared cause within the day is part of the same-day estimate.

Staffing cannot be controlled directly. Units in service are not in 76xm-jjuj. Year-week effects and weekday-by-year effects absorb staffing that changes slowly or follows a weekly pattern; they do not absorb day-to-day shortfalls. A day with fewer ambulances on the road would have longer waits and, if crews at hospitals are not released early, possibly longer measured times at hospital. I could not test this.

The measurement concern is concrete. Time at hospital is incident close minus hospital arrival. If closes are recorded later on busy days, measured time at hospital rises with the wait without any change in offload. Its daily variation is about 30 seconds, small enough for a recording effect of this kind to produce it. The open data hold no transfer-of-care time to separate offload from close-out.

The elasticity also grows as the system nears capacity (4.2 in 2017-2019, 8.0 in 2024-2026), as queueing theory predicts for a causal effect and as it equally predicts for any shared shock. This does not discriminate.

The practical reading in the outcome and the doc extrapolates the same-day elasticity from 1% daily movements to the annual trend ("hospital time would account for 0.53 of the 1.19 rise") and to a policy that would cut offload by several minutes, a change of 10 to 25%. That is far outside the variation that identifies the estimate, and the estimate is not causal. The same data show that in 2026 the wait almost doubled while time at hospital rose 3%. The data are consistent with hospital turnaround mattering, and the literature (Lane et al. 2023) supports the direction, but these data do not show that it is a lever or how large it is.

## 4. The prose in docs/health_gaps.md

I read the doc after finishing the rebuild. Its numbers for this claim match the outcome and my rebuild. It claims more than the numbers support in four places.

1. "The previous day's time at hospital, which these affect less, gives 1.06." The next day's value gives 2.40, and with week fixed effects both are null. The previous-day estimate should not be offered as a lower bound on a causal effect.
2. "The practical reading is that time at hospital matters to waits." The data show a same-day association. The sentence should say that, and that the cause could not be separated from shared daily conditions or from late closing of incidents.
3. The novelty section says the result "is practical in that it names a lever, hospital turnaround". The lever comes from the literature and the MMR, not from this test. The attribution of two thirds of the 2019-2025 rise to hospital time and calls is marked exploratory, but it should also say that it applies a non-causal daily elasticity to changes of 12% and more.
4. The exploratory section says a shortage of ambulances "appears as a longer drive, not a longer wait" for life-threatening calls. That is a reasonable reading of 30 against 53 seconds of wait, but travel time also rises with traffic and with the dispatch-area mix; the sentence states a mechanism the descriptive numbers do not test.

### The power result on the congestion toll and asthma ED visits

I checked `analyses/health_gaps/crz_asthma_power.py` and its output. The numbers in the doc match: the standard deviation of the one-year change in the log ratio of zone to non-Manhattan visits is 0.096 for ages 5 to 17 (excluding 2020-21), the 80%-power detectable change is about 27%, and the predicted changes from the measured NO2 difference are 0.06% to 0.42%, with D below 0.003. The conclusion that a one-year neighbourhood difference in differences cannot detect a toll effect on asthma is supported. Three qualifications belong in the text:

1. "About one hundredth of the smallest effect the city's neighbourhood data could detect" understates the gap for the measured air change (0.06% to 0.42% against 27%, a factor of 60 to 450) and is about right only for the hypothetical 10% NO2 fall (0.7% to 4.6%).
2. The power result is for annual counts in five UHF neighbourhoods. It does not show that no test could be run; a daily syndromic series by ZIP, or several post-toll years, would be more powerful. The doc says these data are not published, which is the correct limit.
3. The prediction uses NO2 only, although the script's description mentions PM2.5. The novelty section says the result is "not stated elsewhere" as far as the author found; it cites no search, so the claim should be dropped or the search described.

The closing sentence, that a health benefit of the toll "will have to be argued from the air change and the research", should note that the measured air change was itself null (+0.9%, −2.2 to +4.2), so the argument from air does not yet have an effect to start from.

## 5. What would settle it

The settle condition (hospital-level transfer-of-care times by day, or a natural experiment such as an offload programme's start date) is right. I would add two things. A pre-registered lead test should accompany any lag model, since a lead that predicts as well as the lag shows a shared cause. Incident close should be replaced by a transfer-of-care time or by the time the unit is next assigned, since close-out recording can move with the wait. FDNY daily units in service, which are not open data, would let staffing enter the model directly.
