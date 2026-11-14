# Referee report: heat-ac-heat-calls

Verdict recorded: contested. Recommendation: keep the verdict, with the changes to the notes and the stance listed at the end.

Referee code: `analyses/critique/referee_heat_ac.py`. It rebuilds the district table and the daily series from the cached query, the cached GHCN-Daily files and the Health Department file with its own code, without importing `analyses/heat_solutions`. It prints its results and writes no file. I did not read `docs/heat_solutions.md` or any other write-up of this claim.

## (a) Does the verdict follow from the registered conditions?

Yes, by rule 1. The refutation condition is a 95% upper limit below 0.112 with a lower limit at or below 0. The registered model gives -0.032 (-0.088 to 0.024), so both parts are met. The joint reading with heat-ac-shootings was registered, and the outcome applies it as written: this claim is not confirmed, so the answer for both outcomes together is "the data cannot tell".

Nothing was decided by a measure chosen after the data were seen. The remote branch `prereg/heat-ac-heat-calls` holds a commit at 07:53:08 on 13 November 2026 with the registration and with `run.py` and `common.py` at the registered hashes. The file in the working tree is identical to the committed registration. The dated query of HEAT calls was fetched at 07:54:17 and the outcome was decided at 07:58:34. The earlier queries of this dataset in the cache are counts of HEAT calls by district and by year (07:47), as the registration states. Git records the commit time and not the push time, so the order of push and fetch cannot be shown from the repository.

Two lines of `run.py` were changed after registration, both in how the hour of a shooting is read. Neither line is used for heat calls, and the change cannot affect this claim. The note in the outcome gives an inaccurate reason for the change, which my report on heat-ac-shootings describes.

The registered period is "May to September, 2006 to the last year in the file". The calendar in `common.py` ends on 31 August 2026, so the 23 calls of September 2026 are left out. This is a small departure from the plan and does not change the result.

## (b) Errors in code, units, joins, dates, geography or uncertainty

The deciding numbers reproduced. My daily counts for the two halves equal the registrant's file on all 3,183 days. I find 15,754 calls in the 59 districts in May to September, 51.4% of them in the low-AC half, and 1,920 days with at least one call. My refit gives -0.032 (-0.088 to 0.024). The secondary results match to the third decimal.

The registered negative binomial fit was degenerate and I reproduce the failure. In my own fit the dispersion for the high-AC half diverges to a value near 10^224 and the slope is returned as 2.335 with an interval of no width. The cause is in `count_fit`: it accepts any finite dispersion above 0.0001 and has no upper bound, so a diverged estimate is passed to the model. The low-AC half fits normally (dispersion 0.277, rate ratio 6.675, 6.223 to 7.160). The Poisson refits are 6.835 (6.343 to 7.366) and 7.011 (6.464 to 7.604), as the outcome reports. The halves' own slopes are a secondary result. The deciding model is the binomial one, which does not use `count_fit`. The outcome labels the Poisson refit as exploratory, and that label is correct. The replacement has no bearing on the verdict.

Of 17,688 HEAT calls, 583 have no community district and 281 carry a code that is not one of the 59 districts (park and airport codes). The share without a usable district is 5.8% on days below 30 C and 4.4% on days of 30 C or more, so the loss is not concentrated on hot days. The outcome does not report these counts.

The standard errors are sound. The Pearson statistic is 1.05 per degree of freedom, and HAC errors with 7 lags are smaller than HC0.

Variants the registrant did not run, difference of log rate ratios per 5 C:

| Variant | Estimate |
|---|---|
| Registered model | -0.032 (-0.088 to 0.024) |
| HAC errors, 7 lags | -0.032 (-0.083 to 0.019) |
| Year-by-month terms | -0.025 (-0.084 to 0.035) |
| Without 2020 and 2021 | -0.037 (-0.094 to 0.021) |
| Previous day's maximum added | -0.065 (-0.139 to 0.010) |
| Income halves pooled by inverse variance | -0.020 (-0.091 to 0.052) |
| Piecewise, above 27 C | -0.016 (-0.079 to 0.047) |
| Days of 30 C or more | -0.017 (-0.111 to 0.078) |
| Calls from 10:00 to 19:59 | -0.038 (-0.103 to 0.026) |
| Calls from 20:00 to 09:59 | -0.025 (-0.162 to 0.112) |
| Saturdays and Sundays | -0.041 (-0.160 to 0.079) |
| LaGuardia | -0.020 (-0.070 to 0.030) |
| JFK | -0.012 (-0.065 to 0.041) |
| Night minimum in place of the maximum | -0.063 (-0.129 to 0.002) |
| Without Manhattan | -0.075 (-0.148 to -0.003) |
| Without Brooklyn | 0.010 (-0.054 to 0.074) |
| 2006 to 2019 | 0.006 (-0.062 to 0.075) |
| 2020 to 2026 | -0.112 (-0.207 to -0.017) |

Every full-sample variant has a lower limit below 0 and an upper limit below 0.112. No variant changes the verdict. The point estimate is negative in all but two rows. The time-of-day problem that affects the shootings claim is small here: 472 of 15,754 calls (3%) fall between 00:00 and 05:59.

## (c) Is the comparison with the research fair?

It is not a like-for-like comparison, and the outcome should say so more plainly. The research figure is an odds ratio of 0.23 for death in a heat wave among individuals with a working air conditioner. The city figure is a difference between two halves of the city in the slope of ambulance calls that a dispatcher coded HEAT, located where the patient was found. The yardstick of 0.112 converts the first into the second by assuming that every call comes from a home, that the odds ratio for death applies to ambulance calls, and that the hot-day contrast is spread evenly over 10 C. The registration states the first assumption and names the dilution by calls from streets and workplaces as an alternative.

The yardstick shrinks with the share of calls that come from homes. With my recomputation it is 0.114 if all calls come from homes, 0.064 at one half, 0.035 at one quarter and 0.021 at 15%. The upper limit of 0.024 excludes shares above about 17% under the registration's other assumptions. Of the calls, 62% fall between 12:00 and 17:59, which is consistent with many of them coming from outdoors. The result therefore says that HEAT calls do not rise faster in low-AC districts. It says nothing about protection by air conditioning at home unless more than about a sixth of these calls come from homes, and the data do not give that share.

The outcome carries a stance of -0.505, which on the strip reads as city data disagreeing with the case-control studies. Those studies are not tested by this outcome. I recommend a null stance, or a note beside the stance that the comparison depends on the assumed share of calls from homes.

## (d) Which alternative explanation is not addressed?

Income is confounded with air conditioning here as in the shootings claim (Spearman 0.699; 23 of 29 low-AC districts are low-income). Within the low-income half the difference is -0.121 (-0.229 to -0.012), and within the high-income half it is 0.057 (-0.038 to 0.153). The two strata differ in sign, and the pooled value is -0.020 (-0.091 to 0.052). The low-income result rests on 1,065 calls in six high-AC districts and is one of several secondary results, so it should not be read as a finding.

Manhattan has 37% of all HEAT calls, eight of its twelve districts are in the high-AC half, and many of the people there by day are visitors and workers. Without the six districts below 59th Street the difference is -0.078 (-0.143 to -0.013), and without Manhattan it is -0.075 (-0.148 to -0.003). The slope is then flatter in the low-AC half, which is the opposite of the claim. The registration listed the first of these as a secondary result, and the outcome reports it.

Three explanations for a flatter or equal slope in low-AC districts are not addressed. Residents of poorer districts may go to an emergency department on foot or not call at all, which the registration names. Dispatch coding may differ between areas: the same patient may be coded HEAT in one borough and as an unconscious or sick person in another. The period matters: the difference is 0.006 (-0.062 to 0.075) for 2006 to 2019 and -0.112 (-0.207 to -0.017) for 2020 to 2026, so the negative estimate comes from the recent years, when calls rose (1,483 in 2026 against 385 in 2020).

## (e) Could the test have failed?

It could have been confirmed. The registrant's prior for "confirmed" was 0.45. The design made refutation very likely if there was no true difference (probability 0.988), because the yardstick was set at the largest value the research could imply. The estimate is z = -1.11 from no difference and z = -5.03 from the yardstick. The test separates "no difference" from "the full home effect" and not from a diluted effect of the size that a home share below a sixth would give. "Contested" is the label that rule 1 assigns, and the verdict note already says that the result does not show that air conditioning fails to protect at home. The note is needed for the label to be read correctly.

## Recommended changes

1. Keep the verdict "contested". Keep the second sentence of the verdict note, and add that the upper limit excludes the yardstick only if more than about 17% of HEAT calls come from homes.
2. Set the stance to null, or attach the note in (c).
3. Report the 864 calls without a usable district and the 23 calls of September 2026 that the calendar leaves out.
4. Say in the notes that the negative binomial failure is a divergence of the dispersion estimate that `count_fit` does not catch, and add an upper bound to that check in later scripts.
5. Correct the shared note on the changed line as described in the report on heat-ac-shootings.

Recommendation: keep.
