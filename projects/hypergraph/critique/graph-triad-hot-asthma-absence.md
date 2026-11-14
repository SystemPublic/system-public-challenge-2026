# Referee report: graph-triad-hot-asthma-absence

Verdict recorded: unsettled. The referee did not register this claim and did not read the registrant's write-ups. Scratch code is in the session scratchpad under `referee-graph-triad-cold-asthma-absence/ref_absence.py`, which runs both arms.

## (a) Does the verdict follow from the registered conditions?

The verdict follows. Support required a ratio above 1 with a Newey-West interval that excludes 1, and refutation the reverse. The ratio is 1.009 (0.970 to 1.050), so neither condition is met and rule 2 gives unsettled. Rule 8 gives the same verdict: the registration reports an expected D of 0.02, and the observed D is 0.1. No measure chosen after the data decides anything.

The timing is in order. The registration is stamped 22:51:37 and was committed at 22:51:43 (86c42fc). The branch `prereg/graph-triad-hot-asthma-absence` exists on GitHub at 0c97c85, committed 22:51:45. The attendance datasets were first touched at 22:51:54 (two-row samples), the grouped queries were fetched at 22:53:04 to 22:56:15, and the outcome is stamped 22:58:13. The weather file was fetched at 20:23:55 and the count of exposed days computed from it is disclosed. The analysis script was first committed with the outcome, so git does not show that it was fixed before the data. The model in it matches the registered plan.

The recorded stance (0.219) is computed by the rule for a direct effect. Under rules 7 and 8, which apply to a bridge with an endpoint test, the stance is about 0.04. Both are near the middle and the difference does not matter for the verdict.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I rebuilt the daily series from the cached Socrata responses and the cached Central Park file with my own code and reproduce the estimate: 1.0090 (0.9698 to 1.0499), 601 school days in May, June and September, 66 exposed. The files do not overlap in dates and both date formats are parsed correctly. The secondary lag 0 to 2 exposure shifts over kept school days and not calendar days, which affects Mondays only. I found no error that bears on the verdict.

| Variant | Ratio | 95% interval |
|---|---|---|
| Registered | 1.009 | 0.970 to 1.050 |
| Standard errors clustered by school year | 1.009 | 0.961 to 1.059 |
| School year by week fixed effects | 1.004 | 0.962 to 1.048 |
| School year by month fixed effects | 1.007 | 0.970 to 1.045 |
| Days within 3 school days of a recess dropped (45 exposed) | 1.005 | 0.964 to 1.047 |
| TMAX at or above 32 C (25 exposed) | 1.003 | 0.944 to 1.065 |
| Without June (49 exposed) | 1.000 | 0.965 to 1.036 |
| September only (26 exposed) | 0.995 | 0.948 to 1.043 |
| May and June only (40 exposed) | 1.014 | 0.964 to 1.067 |
| Placebo: TMAX at or above 30 C two days later, adjusting for today | 1.021 | 0.985 to 1.058 |
| Leave one school year out (range of 13) | 0.991 to 1.023 | |

No variant moves the estimate away from 1. The small positive point estimate comes from May and June. The placebo exposure two days ahead is as large as the estimate itself, which suggests that what little there is reflects the end-of-year decline in attendance and not the day's heat. An influenza control is not relevant in this arm; the state's weekly series does not run through June or September.

The raw means differ more than the model does (10.6% absent on exposed days against 9.4% on others), because hot days fall late in June. The week-of-year terms remove this, as planned.

## (c) Is the comparison with the research fair?

The comparison is loose. I checked PMID 27343213 against PubMed. The abstract gives a cumulative relative risk over lags 0 to 3 of 1.19 (1.06 to 1.34) for 30 C against 27 C in the hot season in Hong Kong, 2004 to 2011, as the outcome says. The outcome is asthma hospitalisation at all ages, and the abstract states that adults were most sensitive and children under 5 least. The temperature is a daily mean in a subtropical city. The city exposure is a same-day maximum of 30 C or more against all other school days in New York, and the outcome is absence from all causes among school-age children. The registration lists these differences among its alternatives. The composed ratio (1.0026) and the city estimate are on the same scale.

## (d) Alternative explanation not addressed

For a null result the question is what could hide an effect. The citywide rate is dominated by absences unrelated to heat, and Central Park's maximum is a poor measure of conditions in classrooms without air conditioning. A citywide sum cannot show an effect confined to such schools. The portal's files are by school, so a school-level analysis is possible, but air-conditioning status by school and year is not in these files. The registration names this route in its `settle` text.

## (e) Could the test have failed?

The test of direction could have failed in either direction. The standard error on the log scale is 0.020, so a true ratio of about 1.06 or more would have been confirmed with probability above 0.8, and a ratio below about 0.96 would have been contested. The registrant's expected range of 1.00 to 1.08 was mostly not detectable. The test of the triad could not have failed: the composed ratio of 1.0026 would need a standard error near 0.001. The observed z against the composed prediction is 0.32 and against no effect 0.44, and D = 0.1.

Recommendation: keep, because the interval includes 1 under the registered model and under every variant, and the test could not have detected the composed size.
