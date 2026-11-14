# Referee report: graph-confounders-surftemp-ed

Verdict recorded: unsettled. The referee did not register this claim and did not read the registrant's write-ups. Scratch code is in the session scratchpad under `referee-graph-confounders-surftemp-ed/referee_heat_b.py`.

## (a) Does the verdict follow from the registered conditions?

Yes, by a margin of 0.09 percentage points. Support required a change between -2.5 and +0.5, a bootstrap interval inside -5.2 to +5.2, an upper limit of the adjusted slope below zero and a largest VIF of 10 or less. The change is +0.59 (-1.27 to +3.42). The first condition fails and the other three are met. Refutation required a change of +3.4 or more, or -5.2 or less, with an interval excluding zero, and is not met. The registration assigns this to unsettled. The built-form models, which move the slope by +7.6, are registered secondary models and are reported as not deciding.

The registration is stamped 23:43:38 and committed at the same second (0bc45fa). The branch `prereg/graph-confounders-surftemp-ed` exists on GitHub at 8c03da0, committed 23:43:46. The EHDP file for older adults living alone (2146) has a modification time of 23:44:18, after the push, which agrees with the registration's statement that it had not been downloaded. The outcome is stamped 23:57:40. The analysis script was first committed with the outcome, so its state at registration cannot be checked in git.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I reproduce the result from `cd.csv`: original -10.3, graph set -9.7 (-17.6 to -1.2), change +0.59 (-1.27 to +3.42) with the registered seed and (-1.36 to +3.25) with another. The change is a difference of two percentages; on the log scale the coefficient moves by +0.0066.

The living-alone measure is reported by PUMA. Districts 101 and 102, 104 and 105, 201 and 202, and 203 and 206 carry the same value in pairs. Six of these eight districts are in the sample of 54. A bootstrap that resamples the pairs together gives (-1.49 to +3.30), so this does not change the result. The built-form secondary models use the population density that is overstated for these districts (see the report on graph-confounders-trees-surftemp). With the density corrected, the built-form model gives -3.1 (-11.8 to +6.5), a change of +7.3 (+0.4 to +15.9), close to the registrant's figures.

Other variants: with borough terms in both models the change is -0.83 (-5.46 to +3.35), and the interval then leaves the -5.2 limit of condition (b). Without Manhattan (n = 45) the change is +1.56 (-1.46 to +5.09) and the adjusted slope's interval includes zero. Leaving out one district at a time gives changes from +0.28 to +0.93, and 12 of the 54 deletions bring the change to +0.5 or below. The miss of condition (a) is within what one district decides.

## (c) Is the comparison with the research fair?

Only loosely. The graph's two findings are odds ratios for death during a single heat wave among case patients who were mostly old or isolated. The city outcome is an age-adjusted rate of emergency visits for heat stress at all ages over five summers. The registrant converted the odds ratios to an expected coefficient of 0.003 to 0.008 log rate per point of living alone through assumptions about the share of visits made by older adults. The outcome says the estimated coefficient (+0.0065, SE 0.0096) "lies in the range" derived from the graph. Its interval runs from -0.012 to +0.025, so it is equally consistent with zero and with three times the derived value, and the agreement carries no information.

I checked PMID 11988377 (Naughton et al. 2002) against its PubMed abstract. Living alone has OR = 8.1 (1.4 to 48.1), with 63 case patients and 77 controls matched on neighbourhood and age, and a working air conditioner has OR = 0.2 (0.1 to 0.7). The registration's summary matches.

The stance of -0.242 is computed as though the claim predicted a negative change. The claim predicts a change near zero, for which the stance formula has no meaningful null (rule 6), and the value should be null.

## (d) Alternative explanation not addressed

The claim does not address why the district association is negative. The secondary result on built form is the registrant's answer, and it was found after the data were seen. Road share, which carries that result, has a correlation of +0.51 with surface temperature because streets are hot surfaces, so adding it removes part of the exposure itself. With the waterfront lot share added, the interval of the built-form change includes zero (+7.0, -0.4 to +16.1). Differences between districts in where people are during the day, in outdoor work and in use of emergency departments remain unmeasured, as the earlier referee of heat-surftemp-ed noted.

## (e) Could the test have failed?

The claim predicts almost no change, and the share of older adults living alone has a correlation of -0.15 with surface temperature, so the covariate had little capacity to move the slope in either direction. Refutation required a change of +3.4 with an interval excluding zero and was unlikely under any plausible truth. Support was not certain either: with a bootstrap standard error of 1.15, a true change of exactly zero falls inside the 3-point support band in about 65% of samples. Against the centre of the prediction (-0.5) the change has z = +0.95. Against no change z = +0.52. The result is closer to no effect than to the prediction, and the test cannot separate the two.

Recommendation: keep. The verdict follows from the registered band and the estimate reproduces exactly; the outcome should say that the miss of 0.09 points is smaller than the effect of removing one district, drop the statement that the living-alone coefficient agrees with the graph, and set the stance to null.
