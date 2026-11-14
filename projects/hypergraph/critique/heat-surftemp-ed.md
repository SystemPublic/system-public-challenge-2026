# Referee report: heat-surftemp-ed

Verdict recorded: contested. Recommendation: keep the verdict, and narrow its scope in the label to the area-level association.

## (a) Does the verdict follow from the registered conditions?

Yes. The registered refutation was an adjusted slope that is negative with an upper limit below zero. The estimate is -10.3% per F (-17.5 to -2.6), n = 54. The registration was made before the outcome, and the unadjusted, adjusted and covariate set match the plan.

## (b) Errors in code, units, joins or dates

I re-ran the model and several sensitivities from `bridge_cd.csv`:

| Variant | % per F | 95% interval |
|---|---|---|
| Registered adjusted model | -10.3 | -17.5 to -2.6 |
| Without the AC term | -9.9 | -16.5 to -2.7 |
| Excluding Manhattan (n = 45) | -11.9 | -20.5 to -2.4 |
| Excluding Staten Island | -8.7 | -16.5 to -0.3 |
| With borough fixed effects | -11.2 | -22.0 to +1.1 |
| Adding vegetative cover | -8.3 | -16.8 to +1.0 |

Leave-one-out estimates range from -12.2 to -8.7. The sign is stable. The interval reaches zero with borough effects or vegetative cover, so the evidence against a positive area-level slope is moderate.

Three data issues should be stated. The exposure is a single Landsat afternoon (2018), while the outcome is a 2018-22 five-year rate. Covariates are unweighted NTA means, and four CDs lose their covariates through the NTA-to-CD mapping. CDs 101 and 105 are suppressed. None of these is a coding error.

## (c) Is the research comparison fair?

No graph finding exists. The literature cited (Madrigano 2015) concerns individual heat-wave mortality by surface temperature around the residence, which is a different outcome, scale and population. "Contested" here contests an ecological bridge that the registrant composed. It does not contest a published finding, and the label should say so.

## (d) Alternative not addressed

The highest ED rates are in CDs 303 (Bedford-Stuyvesant), 111 (East Harlem), 414 (the Rockaways), 206-207 (central Bronx) and 501 (Staten Island North Shore). The Rockaways and Staten Island have cool surfaces, beaches and more outdoor work and car travel. Exposure away from home (named) is acknowledged but not tested. Differences in ED access and use by district (distance to ED, insurance mix) are not covered by the poverty, race and AC terms.

## (e) Is the settle condition right?

Yes. Daily ED counts by neighbourhood in a case-crossover with neighbourhood temperature as a modifier would separate exposure from composition.

## Recommendation

Keep "contested", and label it as an area-level association that contradicts the registrant's bridge, not the research. Report the borough-effects sensitivity beside the verdict.
