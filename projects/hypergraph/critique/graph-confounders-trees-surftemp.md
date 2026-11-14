# Referee report: graph-confounders-trees-surftemp

Verdict recorded: unsettled. The referee did not register this claim and did not read the registrant's write-ups. Scratch code is in the session scratchpad under `referee-graph-confounders-trees-surftemp/referee_heat.py`.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required a change of -0.30 F per SD or more negative, a paired bootstrap interval of the change that excludes zero, and a largest VIF of 10 or less. The change is -0.40 (-1.11 to +0.34) with a largest VIF of 3.88. The second condition fails, the refutation condition (a positive change) is not met, and the registration assigns this to unsettled. The road-share-only model, whose interval does exclude zero, is a registered secondary model and is reported as not deciding.

The registration is stamped 23:43:38 and committed at the same second (e0719f9). The branch `prereg/graph-confounders-trees-surftemp` exists on GitHub at 48e0642, committed 23:43:44. The first PLUTO query grouped by district was fetched at 23:44:02 and the tract queries at 23:49:08. The outcome is stamped 23:57:40. The EHDP file that holds total population (2325) had been on disk since 22:23:29 for another claim, which the registration discloses. The outcome says two lines of the script were changed after registration. The script was first committed with the outcome (30ed4aa) and its file time is 23:49, so git cannot show what changed.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I reproduce the primary result from `cd.csv`: original +0.50, graph set +0.10 (-0.62 to +0.83), change -0.40 (-1.11 to +0.34) with the registered seed and -0.40 (-1.12 to +0.36) with another seed.

There is a geography error in population density. EHDP reports ACS measures for community districts by PUMA, and four PUMAs each cover two districts. Districts 101 and 102 both carry a population of 155,694, 104 and 105 both carry 158,185, 201 and 202 both carry 149,867, and 203 and 206 both carry 171,827. Each of these eight districts is given the population of its pair divided by its own area, so its density is overstated by about a factor of two. When each pair's population is divided by the pair's combined area, the change is -0.25 (-0.99 to +0.58) and the slope under the graph set is +0.25 (-0.56 to +1.07). Condition (a) is then not met either. The verdict is the same, but the statement in `prediction_scored` that the change lies inside the predicted band depends on the error.

Road share is computed as land not in tax lots. Waterfront lots (PLUTO lot type 2) extend past the shoreline used for land area, which is why district 414 has a negative road share. The same bias lowers the road share of other waterfront districts: the eight lowest values after 414 are 101, 313, 208, 318, 202, 111, 210 and 503. I queried PLUTO lot area by district and lot type and added the waterfront lot area share as a covariate. The primary change becomes -0.44 (-1.11 to +0.31), so this bias does not drive the result.

Other variants: without district 414 the change is -0.32 (-1.09 to +0.45); with borough terms in both models it is -0.64 (-1.35 to -0.00); leaving out one district at a time gives -0.54 to -0.26, with 54 of 55 at -0.30 or below.

## (c) Is the comparison with the research fair?

No. The predicted size was derived from a correlation of 0.82 between population density and land surface temperature across Landsat pixels of one municipality that runs from countryside to town centre. Across New York's districts the correlation is +0.04 (0.00 after the density correction). The registration anticipated a lower value, and the outcome reports that the route was not the one derived from the graph. The graph_effect entry (-0.75, -1.1 to -0.4) is therefore a derivation by the registrant, not a research estimate of the same quantity.

None of the graph findings for this claim has a PubMed id. I checked the Prizren study (doi 10.22630/srees.2324) against its Crossref abstract, which gives r = 0.8206 from a regression of surface temperature on population density. The stored value matches.

## (d) Alternative explanation not addressed

The mechanical coupling named in the registration accounts for the whole result, and the outcome understates this. Street trees per km2 of land equals street trees per km2 of street multiplied by the road share. I used street trees per km2 of street (land outside tax lots) as the exposure with the analyst's two covariates and no graph covariates. The slope is -0.82 F per SD (-1.51 to -0.13, n = 54), the research direction. Adding population density and footprint share to that model changes it by +0.07 (-0.24 to +0.38). The positive original slope is produced by the denominator of the exposure, and the two covariates that the graph's findings name with a size (population density, built-up area) move the slope up, not down. This measure was chosen after the data were seen and decides nothing; it should be registered as a new claim. Its own weakness is that road share has a correlation of +0.51 with surface temperature, so dividing by street area builds a negative association into the exposure.

## (e) Could the test have failed?

Yes. With a bootstrap standard error of 0.37, the test would have ended as unsettled for most true changes inside the predicted band: a true change of -0.4 excludes zero in about one resample in five. Against the centre of the graph-derived range (-0.75) the change has z = +0.96. Against no change z = -1.10. The difference of squares is 0.28, far below the 4 that rule 8 asks of an endpoint test, so the result does not separate the prediction from no effect.

Recommendation: keep. The verdict follows from the registration under both the registered and the corrected population density; the notes should record the PUMA duplication, the corrected change of -0.25 (-0.99 to +0.58), and that the fall in the slope is a change of exposure denominator.
