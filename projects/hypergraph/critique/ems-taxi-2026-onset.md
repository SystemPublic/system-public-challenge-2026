# Referee report: ems-taxi-2026-onset

The recorded verdict is confirmed, with a slope of weekly year-on-year change in Manhattan ambulance travel time on that of taxi time per mile of b = 0.895 (0.539 to 1.251) and a 2026 step net of taxi pace of c = −0.034 (−0.081 to 0.013), over ISO weeks 2025-W27 to 2026-W39. My independent rebuild gives b = 0.913 (0.556 to 1.269) and c = −0.037 (−0.084 to 0.011). Both registered conditions are met.

The registered placebo year also meets support_if. For 2024-W27 to 2025-W39 with the split at 2025-W01, I get b = 0.690 (0.226 to 1.153) and c = 0.010 (−0.026 to 0.046): the lower bound of b is above 0.1 and the interval of c includes 0. Rule 11 says that when a registered placebo meets support_if, the verdict is unsettled. Applied as written, it changes this verdict from confirmed to unsettled. I set out below why the rule fits this design poorly, but the text decides, and I recommend unsettled unless the PRECEDENCE is amended for support conditions that predict an absence.

The D of 6.1 in the outcome is reproduced (5.96), but it is a measure chosen after the data (rule 4) against an alternative that the registration did not name. Against the residual step the registration did name (0.05 log), D is 10.5.

I wrote my own code before reading `docs/ems_response.md`. My scripts are outside the repo and are not committed.

## Data

- 76xm-jjuj, EMS Incident Dispatch Data (FDNY), rowsUpdatedAt 2026-10-07T14:42:18Z, fetched 13 November 2026 from 13:49 EST with my own SoQL (Manhattan, valid response time, by date, hour, ZIP area and severity group). Weekly sums of travel seconds and incidents for the registered crz and north areas, ISO weeks, week 53 dropped.
- TLC yellow trip records: 2026-01 to 2026-09 from `~/opt/nyc-concordance/ems_response/tlc/` (Last-Modified 25 March to 29 October 2026), aggregated by my own DuckDB query with filter f1. 2024 and 2025, which every year-on-year difference in the window needs, are not on disk (`~/opt/nyc-concordance/tlc_yellow/` is empty). For them I used `data/derived/congestion/taxi_speed_*.csv`, as the registrant did; versions in `data/derived/reproduction/mmr_cbd_speed_files.json`.

## Order of registration and data

As for the two other claims of this thread: estimators in f44ab0b (13:26:37), registration in d75fa5e (13:27:13), outcome in e63ef7f (13:43:44). For this claim the order matters more. The EMS weekly series and the taxi speeds for July 2023 to June 2026 were in the repo from 1819abd (08:44:57), and the registration cites the citywide fall in taxi speeds from January 2026 found by repro-mmr-cbd-speed. The registrant therefore knew the taxi step before registering, though the prior of 0.25 suggests it did not expect the ambulance series to follow it. The test is not blind to the timing of the step.

## Rule 9: the change to `lib.taxi_hourly` after registration

This claim depends on the substitution more than the others do, since every pre-2026 week in the window and every week of the base year come from the congestion files. I checked the substitution as in the report on ems-traffic-hourly-elasticity: the congestion script uses the same zones, filter and sums, and for January to June 2026, where both sources exist, the 8,686 cbd and north cells are identical. The split week 2026-W01 coincides with the change of source (congestion rows before it, the registrant's own files after it), so the identity on the overlap is what rules out a step created by the change of source. The substitution did not change the registered procedure in substance. The estimator `onset` was not changed.

## 1. Rebuilding the deciding numbers

I used statsmodels OLS with Newey-West errors (4 lags), not the registrant's `hac_ols`. Rows 1 and 2 are registered and deciding; rows marked EXPLORATORY are mine.

| Model | b (95% CI) | c (95% CI) |
|---|---|---|
| Registered: 2025-W27 to 2026-W39, split 2026-W01, all severities | 0.913 (0.556 to 1.269) | −0.037 (−0.084 to 0.011) |
| Registrant | 0.895 (0.539 to 1.251) | −0.034 (−0.081 to 0.013) |
| Placebo year 2024-W27 to 2025-W39, split 2025-W01 (registered secondary) | 0.690 (0.226 to 1.153) | 0.010 (−0.026 to 0.046) |
| Life-threatening only (registered secondary) | 0.981 (0.669 to 1.294) | −0.021 (−0.053 to 0.011) |
| EXPLORATORY: without 2026-W05 to W07 | 0.844 (0.279 to 1.408) | −0.033 (−0.086 to 0.019) |
| EXPLORATORY: without the top tenth of weeks by taxi change | 0.773 (0.048 to 1.498) | −0.031 (−0.086 to 0.024) |

The raw steps (2026 weeks against the second half of 2025, each against the same week a year earlier) are +3.3 log points for ambulance travel (registrant +3.4) and +7.6 for taxi time per mile (registrant +7.6). The small difference in the ambulance step probably comes from the borough filter in my query.

Three weeks in late January and February 2026 (W05 to W07) have year-on-year changes of 0.14 to 0.21 in log taxi time per mile and 0.19 to 0.22 in log ambulance travel time, against means of 0.056 and 0.099 over the 2026 weeks. They carry much of b. Without the top tenth of weeks by taxi change, the lower bound of b is 0.05, below the registered 0.1. This is exploratory and does not decide anything, but the outcome should say that the slope rests largely on a few weeks.

## 2. Does the verdict follow from the registration and PRECEDENCE?

Rule 1 alone gives confirmed: the lower bound of b is above 0.1 and the interval of c includes 0. Rule 8: the registration's discrimination statement concerned b against no effect and a residual 2026 step of 0.05. For b, with the realised se of 0.18 and a predicted 0.7, D against no effect is about 24. For c, the chain value is 0 and the named alternative is 0.05; z_chain = −1.51, z_alt = −3.57, D = 10.5. Both values are above the threshold of 4.

Rule 11 applies because the registration names the 2024-25 window "as a placebo year". The placebo meets support_if (lower bound of b 0.226, c from −0.026 to 0.046), so the rule's first clause is met and the verdict is unsettled.

The rule fits this design poorly. Rule 11 was written for a placebo where no effect can exist. Here the claim has two parts. Part b (ambulance travel tracks taxi pace week by week) is expected to hold in every year, so the placebo year is not a "no effect" window for b. Part c is a prediction of absence (no residual step), and a placebo that also shows no step is the result that shows the design does not produce a spurious step. On that reading the placebo passed. A support condition that predicts an absence will always be met by a placebo that works, so rule 11 as written cannot distinguish a passing placebo from a failing one for such conditions. I recommend that the answer either apply rule 11 as written (unsettled), or amend PRECEDENCE to say that for a condition predicting an absence, the placebo is scored on whether it shows the effect the claim excludes; under that amendment the placebo passes and confirmed stands. The amendment would be made after the data and, by rule 4, should not decide this claim; so unsettled is the verdict I recommend.

## 3. The D of 6.1

The outcome computes z_chain = c / se(c) and z_alt = (c − step_e) / se(c), with the alternative "none of the step is traffic" placed at c equal to the raw ambulance step. I reproduce D = 5.96 (registrant 6.1). It has three problems.

1. The registration named a different alternative (a residual step of 0.05) and a different measure for b. A measure chosen after the data decides nothing (rule 4), and the outcome uses this D as the discrimination statement.
2. In this regression c equals step_e − b × step_p exactly (−0.0367 = 0.0330 − 0.913 × 0.0764). The distance from c to step_e is b × step_p, so the post-hoc test is a test that b × step_p differs from 0. Its standard error is se(b) × step_p = 0.014, not se(c) = 0.024. On the right scale the alternative is rejected more strongly (z of about 5), so 6.1 understates the discrimination. The number is still not the registered one and should be replaced by the registered comparison (D = 10.5 for c).
3. c is negative: ambulance travel rose less in 2026 than taxi pace predicts at b = 0.91. At the hourly elasticity of 0.63, the taxi step predicts +4.8 points against the observed +3.3. The 2026 step is at most proportional to the taxi step.

## 4. The prose in docs/ems_response.md

I read the doc after finishing the rebuild. Its numbers for this claim match the outcome and my rebuild. It claims more than the numbers support in three places.

1. "The test separates this from the alternative that none of the step is traffic (D = 6.1)." This is the post-hoc D. The registered discrimination (D = 10.5 against a residual step of 0.05) should be reported instead, and the verdict should follow rule 11.
2. "The step of 2026 in Manhattan is traffic." The weekly test shows that the step in ambulance travel is in proportion to the step in taxi pace. It does not show cause: the reason taxi speeds fell is unknown, and a cause that slowed taxis (winter weather, street works) may also have lengthened the distance to free units. The sentence should say that the 2026 step is no larger than the taxi step accounts for. The slope also rests on three winter weeks.
3. "The same model for 2024-25 gives a slope of 0.68 and no step." This is correct and should add that the placebo year meets the registered support condition.

## 5. What would settle it

The settle text (FHV trip speeds by borough and week, the cause of the January 2026 taxi slowdown) is right. Two additions. A daily snow and precipitation control from GHCN-Daily (Central Park) would show whether the winter weeks drive b. A future registration of this design should state the placebo condition separately from support_if, for example "the placebo year's c interval includes 0 and its upper bound is below 0.05", so that rule 11 can be applied as intended.
