# Referee report: graph-confounders-commute-obesity

Verdict recorded: unsettled. The referee did not register this claim and did not read the registrant's write-ups. Scratch code is in the session scratchpad under `referee-graph-confounders-commute-obesity/referee_commute.py`.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required a primary estimate between -4.0 and +0.5 with an HC3 half-width of 3.0 or less. Refutation required -5.0 or below. The primary estimate is -4.40 with a half-width of 3.18, which the registration assigns to unsettled on both counts. No measure chosen after the data decides anything. The secondary model with park access and unemployment (-3.25) falls inside the support range, and the outcome correctly reports it as not deciding.

The order of events is consistent with registration before data. The registration file is stamped 22:22:45 and was committed at 22:22:52 (713f50e). The branch `prereg/graph-confounders-commute-obesity` exists on GitHub at 7b6d1f0, committed 22:22:53. The EHDP indicator files for the new covariates in `~/opt/nyc-concordance/ehdp` have modification times of 22:23:28 to 22:23:30. The covariate table was written at 22:24:23 and the outcome at 22:25:19. Two things cannot be checked from the record. The analysis script was first committed with the outcome, so git does not show that it was fixed before the data arrived. The registration says the EHDP metadata file was read to choose the measures, but the copy of `metadata.json` on disk is dated 22:28:01, after the outcome, so the earlier reading left no trace.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I rebuilt six of the columns from the pinned EHDP files and they match the registrant's table exactly. I reproduce the primary estimate: -4.40 (-7.58 to -1.23), n = 42. The measures and periods are those registered. Measure 1058 is the percent of adults who report living in a neighbourhood safe from crime, and the walkability index is a 2011 sum of z-scores that includes residential density, intersection density, land-use mix and subway stops.

The half-width condition depends on the choice of HC3, which was registered. With eight regressors, 42 units and high-leverage Manhattan neighbourhoods, HC3 gives 3.18, HC2 2.53, HC1 2.35 and the classical formula 2.08. The verdict does not turn on this, because the point estimate fails the support range under every choice.

Variants the registrant did not run:

| Variant | Slope per 10 points | 95% interval |
|---|---|---|
| Registered primary | -4.40 | -7.58 to -1.23 |
| Weighted by the precision of the obesity estimate (from the CHS intervals) | -4.27 | -8.78 to +0.24 |
| Graph set with borough terms | -4.16 | -8.43 to +0.11 |
| Without Manhattan (n = 32) | -7.60 | -12.98 to -2.22 |
| Perceived safety from 2015 only | -4.45 | -8.29 to -0.62 |
| Perceived safety from 2016 only | -4.35 | -7.48 to -1.22 |
| Leave one UHF out (range of 42) | -5.60 to -3.73 | |

Dropping UHF 305 puts the estimate inside the support range, and dropping UHF 307 puts it inside the refutation range. A paired bootstrap over neighbourhoods (5000 resamples) gives an attenuation of 28% with a 95% interval from -14% to +64%. The share of resamples in the support range is 0.42 and the share in the refutation range is 0.30. The registered thresholds are applied to a point estimate, and the data cannot distinguish an attenuation of one third from none.

The registration named, and did not register, a random-covariate comparison. I ran it. Six noise covariates added to poverty give slopes from -6.59 to -5.36 (central 95% of 2000 draws), and the same range results when the six real covariates are permuted across neighbourhoods. None of the 2000 draws reaches -4.40. The attenuation of 26% is therefore not what any eight covariates produce.

## (c) Is the comparison with the research fair?

The graph_effect entry sets the city slope beside "below 1 point per 10", derived from Flint et al. (2014), an individual-level BMI difference between commuting modes. The city quantity is a prevalence slope across 42 areas. The two differ in unit, outcome and scale, as the earlier referee of mob-active-commute-obesity said. The claim itself is about a change in the city slope and does not need this comparison.

I checked one cited graph finding. PMID 17465178 (Rundle et al. 2007) reports population density Beta = -.25, p < .001, for BMI in New York City after individual and neighbourhood adjustment. The registration's summary matches the abstract.

The stance of +0.876 on the outcome is computed from the sign of the adjusted slope. The claim is about attenuation, and its prediction was scored a miss. A stance near +0.9 presents a missed prediction as strong agreement.

## (d) Alternative explanation not addressed

Spatial dependence is not addressed. The 42 neighbourhoods are contiguous and the borough terms widen the interval to include zero, so the HC3 interval is likely too narrow. Age structure and income above the poverty line are named and left out. The walkability index is from 2011 and has a correlation of 0.85 with the exposure, and the leave-one-out result (-5.09 without it) shows that most of the attenuation rests on this one variable. Whether that is removed confounding or removed exposure variation cannot be decided with these data, which the outcome states.

## (e) Could the test have failed?

Yes. All three verdicts were reachable, and the bootstrap shares above (0.42 support, 0.30 refutation) show that sampling variation alone could have produced any of them. Against the centre of the predicted range (-2.5) the estimate has z = -1.17. Against no attenuation (-5.97, taking the adjusted standard error) z = +0.97. Against a slope of zero z = -2.72. The test does not separate the prediction from no attenuation.

Recommendation: keep. The verdict follows from the registered thresholds and the estimate reproduces exactly; the outcome should add the bootstrap interval of the attenuation (-14% to +64%) and set the stance to null.
