# Referee report: sim-crz-holdout-2026

Verdict recorded: contested. Recommendation: keep the verdict, rewrite the verdict note and the effect label as listed at the end, and correct the stance. Two storm days, 23 February and 26 January 2026, fix S1 = 0.29, the number that decides the verdict, so it does not estimate the elasticity on ordinary days. This report calls them the two storm days. The four low days are those two and the day after each (24 February and 27 January), on which entries were under 0.80 of the median weekday.

Referee code: `analyses/critique/referee_sim_holdout.py`. It rebuilds the band-by-day panels from `data/derived/simulate/panel_calib.csv` and `panel_holdout.csv` with its own code, without importing `analyses/simulate/fit_links.py`, and prints its results. I read the registration, the outcome, the code in `analyses/simulate/` and `sim/`, the data in `data/derived/simulate/`, and `viz/simulate_model.js`. I did not read `docs/policy_simulation.md` or any other write-up. Three inputs lie outside `data/derived/simulate/` and I used them as data: the cached Central Park weather file, the yellow-taxi trip files that `build_data.py` reads, and `data/derived/congestion/bus_speed_cbd.csv`, a monthly bus speed series built by another analysis. The bus series is the only speed measure in the repository that does not come from taxis.

The second half of this report reviews the simulator in `sim/`. It carries no verdict and ends with a list of defects.

## (a) Does the verdict follow from the registered conditions?

The verdict follows from the registered conditions. The refutation condition is an upper bound of the 95% interval of S1 below 0.5. S1 is 0.286 (0.190 to 0.383) on 492 band-days, so the condition is met and precedence rule 1 gives "contested". The outcome script codes the two conditions as written.

Nothing was decided by a measure chosen after the data. The exclusion of storm days appears only in the notes and is labelled exploratory. `build_data.py`, `fit_links.py` and `fits_calib.json` are in the registration commit and are unchanged in the working tree.

The timestamps are in order. The registration is stamped 08:05:49 on 13 November 2026 and its commit, 0d9c9a4 on the remote branch `prereg/sim-crz-holdout-2026`, is at 08:05:59. The 2026 entries were fetched at 08:06:27 and the 2026 ambulance data at 08:08:25. The outcome was decided at 08:12:34. The first fetch came 28 seconds after the commit. Git records when a commit was made and not when it was pushed, so the repository cannot show that the push preceded the fetch. The cache holds no query of 2026 vehicle entries before the registration. The earlier ambulance queries that reach into 2026 are counts of incidents and contain no travel times. The 2026 taxi files were on disk from 19:57 on 12 November, and the registration says that half-year mean speeds from them had been seen. The outcome commit, 1819abd, is on local `main` and is not yet on the remote.

The registered standard error is conditional on the fitted elasticity. When the uncertainty of the fitted value (-0.409, se 0.104) is carried into the ratio, the standard error of S1 rises from 0.049 to 0.088 and the interval becomes 0.11 to 0.46. The condition is still met.

The verdict depends on 23 February 2026. Without that day, the upper bound of S1 is 0.51 and the refutation condition is not met. That day was in the registered sample, so the verdict stands.

## (b) Errors in code, units, joins, dates, geography or uncertainty

Every number I checked reproduced.

| Quantity | Outcome | Referee |
|---|---|---|
| Fitted speed elasticity, 2025 | -0.409 (se 0.104) | -0.409 (se 0.104) |
| Fitted ambulance elasticity, 2025 | -0.572 (se 0.078) | -0.572 (se 0.078) |
| S1 | 0.286 (0.190 to 0.383) | 0.286 (0.190 to 0.383) |
| S2 | 1.104 (0.725 to 1.483) | 1.104 (0.725 to 1.483) |
| Held-out elasticity without the four low days | +0.08 (se 0.54) | +0.080 (se 0.539) |
| Pooled 2025 and 2026 without those days | -0.23 (se 0.23) | -0.227 (se 0.234) |
| Entries per weekday, January to June | 507,000 and 480,000 | 507,233 and 479,819 |
| Taxi trips inside the zone per weekday | 51,000 and 45,000 | 50,965 and 44,893 |

I found four small problems in the code and the text.

The level test measures the change in entries as a difference of mean logs. The two storm days have logs far below the rest, so the figures in the outcome (-8.3% in the morning band, -6.7% at midday) overstate the fall. The ratios of arithmetic means are -6.1% and -5.5%. The predicted speeds use the same log means and are affected in the same way.

The clustered standard error of S1, 0.049, comes from a sample in which two dates carry 84% of the variation in log entries that remains after the fixed effects (23 February 74%, 26 January 10%). A cluster-robust error is not reliable with that much leverage in two clusters. With any single date dropped, the held-out elasticity stays between -0.088 and -0.123, because each of the two storm days alone is enough to fix it.

The holiday list holds federal holidays only. In 2025 the day after Thanksgiving (28 November) alone carries 31% of the residual variation in log entries, and eight dates carry 48% (among them 23 December, 23 September, Good Friday, 2 October, 3 July and 6 January). The fit therefore rests on near-holidays more than on ordinary days, although removing them changes it little (table below).

The night band joins 00:00 to 04:59 and 21:00 to 23:59 of the same calendar date. Each "night" is therefore the end of one night and the start of the next This does not change any number that decides the verdict.

### The calibration elasticity

The registered fit is stable in sign under changes of the fixed effects, weather controls and exclusions. Its size is not stable, and adding the number of taxi trips inside the zone reduces it to -0.09.

| Variant on 2025 | Elasticity (se) |
|---|---|
| Registered | -0.409 (0.104) |
| Band by month effects only, no weekday effects | -0.753 (0.038) |
| Band by ISO week effects | -0.359 (0.111) |
| Band by month by weekday effects | -0.431 (0.132) |
| Weather controls by band (rain, snowfall, snow cover, temperature) | -0.496 (0.109) |
| Without days under 0.95 of median entries | -0.567 (0.152) |
| Without Good Friday, 3 July, days around Thanksgiving and Christmas, UN week | -0.369 (0.112) |
| Dry days only | -0.594 (0.132) |
| January to March | -0.154 (0.145) |
| April to June | -0.229 (0.168) |
| July to September | -0.294 (0.501) |
| October to December | -0.583 (0.117) |
| Morning band alone | -0.549 (0.084) |
| Evening band alone | -0.096 (0.242) |
| Entries other than taxis and for-hire vehicles | -0.299 (0.105) |
| Log taxi trips inside the zone added | -0.087 (0.111) |
| Log taxi trips and log mean trip distance added | -0.366 (0.097) |
| Placebo: entries of the same band one week later | +0.051 (0.074) |

Season, weather and holidays do not produce the estimate. Weather controls make it larger, week effects leave it at -0.36, and removing the near-holidays leaves it at -0.37. The placebo is near zero.

Three results limit how the estimate can be read. First, only the last quarter of 2025 gives an estimate that differs from zero. The registration reported the same instability as a first half of -0.20 and a second half of -0.51. Second, the coefficient falls from -0.75 to -0.41 when weekday effects are added and to -0.09 when the number of taxi trips made inside the zone is added. Taxi trips inside the zone measure how busy the zone is. Days with more entries are days with more activity of every kind, and entries have little association with speed beyond that. The trip-distance control moves the estimate back to -0.37, so this result depends on the specification, but it shows that the day-level slope cannot be assigned to vehicles crossing the cordon. Third, in a model with both, taxi and for-hire entries have the same coefficient as other entries (-0.22 each), although only the other entries respond to the entry toll.

### Can a day-level regression identify the relation?

A day-level regression cannot identify the relation on ordinary days. After the registered fixed effects the residual standard deviation of log entries in 2025 is 0.032. Sixty-five per cent of band-days lie within 2% of their expected entries and 93% within 5%. The variation that remains comes from near-holidays and weather, which change the streets as well as the entries. Demand shocks (a busy day) give a negative slope. Supply shocks give a positive one: on 27 January 2026, the day after the storm, entries were 16% to 23% below normal and speed was 8% to 31% below normal. The fitted slope is a mixture of the two, and the mixture changes with the weather of the period. The estimates by quarter and the held-out estimates below show this.

### The held-out speed elasticity

| Variant on January to June 2026 | Elasticity (se) | As S1 |
|---|---|---|
| Registered | -0.117 (0.020) | 0.29 |
| Without 26 January and 23 February | +0.096 (0.429) | -0.23 |
| Without the four days under 0.80 of median entries | +0.080 (0.539) | -0.19 |
| Without the eight days under 0.90 | -0.469 (0.361) | 1.14 |
| Without the 22 days under 0.95 | -0.926 (0.158) | 2.26 |
| Dry days without snowfall or snow cover (76 days) | -1.136 (0.158) | 2.78 |
| Weather controls, all days | -0.177 (0.029) | 0.43 |
| Weather controls, without the four days | -0.338 (0.278) | 0.83 |
| Band by week effects, without the four days | -0.455 (0.183) | 1.11 |

The held-out elasticity ranges from +0.10 to -1.14 depending on how 22 winter days are treated. The two storm days fix the registered value. On 23 February entries were 78% to 95% below normal and taxi speed was 18% to 71% above normal. A constant elasticity of -0.41 predicts a rise of about 150% for a 90% fall in entries. Speed on signalled streets under snow cannot rise that far, so those days show that the log-linear form fails at large changes. They do not measure the response to a change of a few per cent. On dry days the held-out elasticity is more than twice the fitted one and its interval lies wholly below the fitted value.

The difference between the held-out and the fitted elasticity is +0.29 with z = 2.75 on all days, +0.49 with z = 0.89 without the four low days, and -0.06 with z = -0.16 without the eight days under 0.90.

### The held-out ambulance slope

S2 does not depend on the low-entry days. The outcome notes do not report this.

| Variant on January to June 2026 | Elasticity (se) | S2 |
|---|---|---|
| Registered | -0.632 (0.111) | 1.10 (0.72 to 1.48) |
| Without 26 January and 23 February | -0.699 (0.136) | 1.22 (0.76 to 1.69) |
| Without the four days under 0.80 | -0.690 (0.144) | 1.21 (0.71 to 1.70) |
| Without the eight days under 0.90 | -0.642 (0.152) | 1.12 (0.60 to 1.64) |
| Weather controls, all days | -0.503 (0.075) | 0.88 |
| Band by week effects | -0.390 (0.087) | 0.68 |
| Dry days without snow | -0.384 (0.123) | 0.67 (0.25 to 1.09) |

Leaving out any single date keeps the elasticity between -0.57 and -0.67. No date carries more than 9% of the residual variation in log speed, although the four days after the January storm (27 to 30 January) carry 25% together. The sign holds in every variant. The size falls from about -0.6 to about -0.4 when the comparison is made within weeks or on dry days, so part of the registered slope is weather that slows taxis and ambulances together. The 2025 fit moves less under the same changes (-0.53 with week effects, -0.63 with weather controls).

## (c) Is the comparison with the research fair?

The outcome makes no comparison with research. The System Public Graph holds no finding that relates vehicle volume to speed or speed to ambulance travel time as a dose and a response, and the outcome leaves `graph_effect` empty. The claim is registered as a confirmation, but it tests the project's own fitted model against later data.

The parameter file notes that the January 2025 toll step implies an elasticity of -0.5 to -1.4. That is the only estimate in the project from a change in the toll, and it is at least as large as the fitted value. It is not used in the test.

## (d) Which alternative explanation is not addressed?

Taxi speed fell in 2026 and the model does not explain the fall. I checked four possible causes.

A change in the trip mix does not explain it. Speed fell in every distance class (-10.6% under one mile, -3.8% over three miles). Within 1,344 pairs of origin and destination zones, weighted by 2025 hours, speed fell 8.9%, and 97% of pairs were slower. Recorded miles per trip within pairs fell 1.1% and minutes rose 8.6%.

I found no change in vendor shares, in rounding or in records with missing fields. Both vendors show the same fall (7.47 to 6.93 mph and 7.73 to 7.10 mph), their shares moved by three points, and the rounding of distances and durations did not change. Records with missing payment fields are faster than complete records and their share did not rise enough to matter.

Weather explains a small part. The first half of 2026 had 23 weekdays with snow on the ground against 11 in 2025, but fewer wet days. On dry days without snow the fall is 3% to 8% by band, and from March to June it is 4% to 8%. With weather controls the 2026 effect on log speed is -0.066 (se 0.009), and -0.076 with entries in the model.

The fall is not specific to the zone. Taxi trips under three miles that neither start nor end in the zone slowed by 10.1%, 13.1%, 5.4%, 4.0%, 4.3% and 2.6% in January to June 2026 against a year earlier. Trips inside the zone slowed by 8.5%, 13.2%, 6.0%, 5.9%, 5.4% and 9.4%. In December 2025 both series were within 2% of the year before, so the change begins in January 2026 in both. Zone entries cannot explain a fall outside the zone. Bus speeds do not show the same pattern. In the zone they fell 3.9% over the half-year, with the fall concentrated in January to March (-5.6%, -10.4%, -4.7%) and gone by May (+1.0%). Outside the zone they fell 0.6%.

So from January 2026 taxi trips take about 8% longer over the same distances across the city, and buses do not. I could not find the cause in the files I had. Candidates are a change in how trip start and end times are recorded that leaves no trace in the fields I checked, a change in taxi operations, or a citywide change in general traffic that bus lanes shield buses from. Until this is explained, the level test of the speed link measures a citywide shift in the taxi series, and the taxi speed series should not be compared across the two years. Relative to short trips outside the zone, speed inside the zone changed by between -2% and +2% from January to May, while entries fell by 4% to 12%.

The outcome addresses the first registered rival least, that days with more entries are days with more people and deliveries. The taxi-trip control in (b) supports it. The outcome's last note makes the same point from the weekday pattern.

Ambulance travel times rose by 11.3% (se 1.1) from 2025 to 2026 with weather controlled, and by 8.0% with taxi speed also in the model. The outcome reports this. The simulator's chain (toll to entries to speed to ambulance travel time) has no term for this rise.

## (e) Could the test have failed?

The test could fail and did fail, but not in the way the registration expected. The registration expected a standard error of 0.35 for S1 from the rehearsal inside 2025. The realised standard error is 0.049 because of the storm days. Against the prediction S1 = 1, z is -14.5. Against no relation, z is +5.8. The discrimination statistic D = z_null² - z_chain² is negative, so the endpoint is closer to no relation than to the fitted elasticity.

On ordinary days the test cannot discriminate. Without the four low days the standard error of S1 is 1.32, so the 95% interval is wider than five units and neither registered condition can be met. If the fitted elasticity were right, D would be expected to be about 0.6, below the threshold of 4 in rule 8. A test restricted to ordinary days of one half-year would return "unsettled" whatever the truth.

For S2, z against the prediction is +0.5 and against no relation +5.7, so D is 32. The ambulance slope was tested and passed.

## Recommendation on the verdict

Keep "contested". The registered condition is met, it remains met when the calibration uncertainty is carried, and no rule allows a day to be excluded after the data. The verdict means that the fitted link did not predict the held-out days as registered. Make these changes to the outcome.

1. Rewrite the verdict note. It should not state the held-out elasticity as -0.12 against -0.41. It should say that the registered slope is fixed by 23 February and 26 January 2026, that the verdict would be "unsettled" without 23 February alone, and that on the remaining days the held-out elasticity is between +0.1 and -1.1 depending on how 22 winter days are treated.
2. Change the effect label in the same way, or mark the estimate as depending on two days.
3. Correct the stance. It is recorded as +0.994 (z = 5.81), which places a contested claim at the agreeing end of the dashboard strip. The value is computed against no relation. S1 lies 14.5 standard errors from the registered prediction.
4. State the entries change by band as a ratio of means (-6.1% and -5.5%), or say that the figures are geometric.
5. Add to the notes that taxi speed fell by a similar amount outside the zone from January 2026 and that bus speeds did not, so the level miss of the speed link cannot be assigned to the link.
6. Register a successor before more data are read. It should fix in advance an exclusion for snow days and near-holidays, use weather controls, carry the calibration uncertainty into the interval, and include a calculation showing that the test can discriminate. Entries and ambulance data exist through the autumn of 2026. A day-level design may not reach D = 4 even with a full year, in which case the 2028 toll step is the first test.

One line: keep the verdict, with the note, label and stance changed.

# Review of the simulator (no verdict)

I ran `sim` with the current `parameters.json` and compared the result with `scenarios.json`, checked the draws against the stated ranges, tested the revenue-neutral scenarios, and ran `viz/simulate_model.js` under node against the Python model.

Three things are correct. A fresh run with 10,000 draws and the fixed seed reproduces every stored median and interval in `scenarios.json`. The browser model gives the same central values as the Python model: over eight scenarios and seven outputs the largest absolute difference is 4.5e-13. Its Monte Carlo intervals, from a different generator, agree with the Python intervals to within sampling error (for the uniform $12 schedule, speed +0.81% (0.04 to 2.56) against +0.82% (0.04 to 2.54)). `viz/data/simulate_params.js` equals `parameters.json`.

## Defects

1. The sign of the speed, ambulance and survival outputs is built in. `beta_speed` is drawn uniformly from -0.61 to 0, `theta_ems` is truncated at 0, and `surv_per_min` is truncated at 0. Every schedule that lowers entries therefore raises speed, shortens ambulance trips and adds survivors in every draw. The stored probabilities are 1.000 for all three. With `beta_speed` drawn from -0.61 to +0.61 they are 0.50. The held-out data without the storm days give +0.08 (se 0.54) and do not exclude a positive value. The `p_positive` values and the table `p_row_beats_column` for these outputs follow from the bounds and should not be presented as findings. The same holds for the sign of the entries response (`k_toll` and `k_shift` are positive by construction).

2. The revenue-neutral scenarios lower entries by construction. With exponential demand and one shared `k_toll`, revenue is concave in the toll below $40, so any schedule that spreads tolls must have a higher traffic-weighted mean toll to hold revenue. I drew 200 random daytime toll tables and scaled each to current revenue: all 200 lowered total entries. Tuesday-to-Thursday high and Monday-and-Friday high are opposite patterns, and in the stored results the functional form makes both raise speed with probability 1.000.

3. The revenue-neutral scenarios are neutral at the central parameter values (difference under $0.001 million) and within -1.5% to +1.2% of current revenue across the draws. The stored medians are slightly negative (-$0.3 to -$0.9 million) because the central values are not the medians of the draws (defect 4). The bisection assumes that revenue rises with the scaling factor. That is true for the stated range of `k_toll` and tolls under $40, and is not checked in the code. Only daytime tolls are scaled, and revenue is weekday revenue only.

4. For eight of the fourteen parameters the central value is not the centre of the range that is drawn. `beta_speed` has value -0.25 and median draw -0.30. `amenity` has value 0 and median draw 0.10. `diversion` has 0.70 and 0.62, `spend_ratio` 1.00 and 1.26, `k_shift` 0.004 and 0.006. The browser page shows central values and the scenario file shows medians, so the two differ for the same schedule (uniform $12: speed +0.77% central, +0.82% median). For retail the difference is one of composition: the central value has no amenity term and the draws all have a positive one.

5. For two normally distributed parameters the draws do not match the stated ranges. The code takes the standard deviation from the width of the range and centres the distribution on the value. `theta_ems` is stated as -0.75 to -0.30 around -0.572, and 95% of the draws lie between -0.80 and -0.34. `surv_per_min` is stated as 0.01 to 0.18 and the draws lie between 0.013 and 0.165. The other intervals follow from the stated ranges.

6. The speed link is applied to a change it was not estimated on. `beta_speed` comes from day-to-day variation of a few per cent, which section (b) shows is confounded with activity in the zone, and the simulator applies it to toll-induced changes in non-taxi entries. One pooled value is used in every band. The fitted values by band run from -0.10 (se 0.24) in the evening to -0.56 at midday, and the evening-toll scenario rests on the band with no detectable relation. The model file says the chain is one of associations. The scenario output does not carry that statement.

7. The parameters are drawn independently. `beta_speed` and `theta_ems` were fitted on the same days and enter the ambulance output as a product. The effect on the intervals is small next to defect 1.

8. The baselines are 2025 means. In January to June 2026 taxi speed was 7% lower and ambulance travel time 11% higher with weather controlled, for reasons the chain does not contain. Absolute outputs (speed in mph, mean ambulance seconds) are out of date. Outputs stated as changes are less affected.

9. The hot-night illustration applies the weekday night-band baseline and elasticity to 43 nights a year that include weekends, and its outputs are positive by construction for the reason in defect 1. The median of 0.0005 shooting deaths averted a year is zero for practical purposes and should be shown as zero.

10. `build_parameters.py` replaces `theta_ems`, `k_toll` and `surv_per_min` with values from `data/derived/congestion/parameters.json` when that file holds parameters of the mapped names. No parameter is replaced at present. The other file was rewritten after `parameters.json` was built, so a rebuild can change the simulator's results without a change in `sim/` or `analyses/simulate/`. The source of each parameter should be fixed in one place.
