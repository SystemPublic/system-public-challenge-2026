# Referee report: all-boats-trees-rent

Verdict recorded: unsettled. Recommendation: keep the verdict, and change the notes and the stance as listed at the end.

The referee did not register this claim and did not read `docs/all_boats.md` or any other write-up. The referee read the registration, the outcome, `analyses/all_boats/tree_change.py`, `tree_test.py` and `tree_test_posthoc.py`, the files in `data/derived/all_boats/`, the script that built the rent variable (`analyses/neighbourhood/base.py`) and the verdict rules in `concord/claims.py`. Referee code: `analyses/critique/referee_trees_rent.py`. It rebuilds the tree counts from the downloaded tree points and the rent change from the raw ACS summary files without importing the registrant's code, prints its results and writes no file.

## (a) Does the verdict follow from the registered conditions?

Yes. The support condition is an interval wholly above 0.009 and the refutation condition is an interval wholly below 0.018. The primary slope is 0.0127 (0.0018 to 0.0235) log points per 100 trees. The lower limit is below 0.009 and the upper limit is above 0.018, so neither condition is met and rule 2 gives unsettled. The estimate is 0.66 standard errors above the support threshold and 0.96 below the refutation threshold, so neither condition was missed narrowly.

Nothing was decided by a measure chosen after the data. The registration, `tree_test.py`, `tree_change.py`, the tree counts and the power file are in commit f960e5d (07:46:55, branch `prereg/all-boats-trees-rent`), and none of them differs from the working tree. The registration time is 07:46:53. The tree points were fetched at 07:44:08, before registration; they are the exposure, and the registration says they were seen. The crime queries were fetched at 07:48:44 and 07:52:56, the results file was written at 07:52 and the outcome at 07:53:23. The post hoc file was written at 07:57 and is labelled post hoc.

One limit on blindness should be recorded. The outcome variable `d_logrent` was not fetched after registration. It had been on disk in `data/derived/neighbourhood/tracts_acs.csv` since 12 November and had been used in an earlier claim. The registration says only its marginal distribution had been read. The repository cannot show this, and the order of model and data rests on that statement and on the fixed script. The git record also holds the commit time and not the push time.

## (b) Errors in code, units, joins, dates, geography or uncertainty

Every number I checked reproduced. My tree counts equal the registrant's in every tract. My 2008-12 and 2018-22 rents, rebuilt from the summary files, equal the registrant's to the dollar. My refit gives 0.0127 (0.0018 to 0.0235) with a standard error of 0.0055 on 2,048 tracts and 196 clusters, and 0.0084 (-0.0027 to 0.0196) without baseline rent. I found no error in the joins or the units. The findings below concern what the two variables measure.

### The tree change is partly not a change in planted trees

The net change mixes three things: new planting, loss of existing trees, and differences between the two censuses. The files hold only coordinates, status and diameter, so I could not examine the inclusion rules or the volunteer coverage of 2015 directly. I used diameter instead. A tree of 3 inches or less in 2015 was almost certainly planted after 2005, and a tree of 12 inches or more was almost certainly not.

By borough, living trees in a tract changed as follows.

| Borough | 2005 | 2015 | Change | Change in trees of 12 in or more |
|---|---|---|---|---|
| Manhattan | 49,099 | 62,716 | +27.7% | +47.7% |
| Bronx | 57,348 | 80,291 | +40.0% | +7.9% |
| Brooklyn | 140,457 | 169,751 | +20.9% | +1.1% |
| Queens | 231,033 | 237,887 | +3.0% | -5.4% |
| Staten Island | 97,568 | 101,443 | +4.0% | +3.9% |

The citywide gain of 13% is plausible as a real gain, since 93,000 living trees in 2015 are 3 inches or less and 228,000 are 6 inches or less. The borough pattern is less clean. The count of large trees in Manhattan rose by 48%, which planting cannot produce in ten years; growth of trees across the 12-inch line, a difference in how diameter was measured, or fuller coverage in 2015 could. Large trees in Queens fell by 5%, which is consistent with storm losses. In the 2005 file 8,840 rows (1.5%) have a longitude of zero and fall in no tract. Their borough cannot be recovered from the downloaded columns, so the 2005 counts are too low by an unknown amount in unknown tracts, and the gain is overstated there.

Across the 2,048 sample tracts the net change correlates 0.31 with the count of trees of 3 inches or less in 2015 and -0.35 with the 2005 count (Spearman -0.55 with 2005 trees per square km). The correlation with young trees is 0.6 to 0.7 in Manhattan, the Bronx and Brooklyn, 0.29 in Queens and 0.10 on Staten Island. In Queens and Staten Island, which hold 37% of the sample, the registered exposure mostly measures losses or census differences and not planting. The standard deviation of the change in large trees is 54 per tract against 90 for smaller trees. In a model with both parts, the slope is 0.0097 (-0.0032 to 0.0226) for the change in smaller trees and 0.0201 (0.0018 to 0.0385) for the change in large trees. The part of the exposure that cannot be planting carries at least as much of the association as the part that can.

### Attenuation, and the form of the exposure

The registration names error in the tree change as a bias toward zero. The outcome's statement that the estimate is 29% of the central prediction, with an upper limit of 0.0235 against 0.044, assumes that the bias is small. Variants I ran (slope per 100 trees unless stated):

| Variant | Slope |
|---|---|
| Registered | 0.0127 (0.0018 to 0.0235) |
| Exposure: trees of 3 in or less in 2015 | 0.0147 (-0.0064 to 0.0357) |
| Exposure: trees of 6 in or less in 2015 | 0.0138 (0.0018 to 0.0258) |
| Net change instrumented by trees of 3 in or less | 0.0166 (-0.0078 to 0.0411) |
| Net change instrumented by trees of 6 in or less | 0.0273 (-0.0024 to 0.0570) |
| Net change winsorised at 1% and 99% | 0.0167 (0.0040 to 0.0293) |
| Tracts with a change under 500 trees in size (n 2,038) | 0.0166 (0.0036 to 0.0296) |
| Tracts with a change under 300 trees in size (n 2,001) | 0.0245 (0.0096 to 0.0395) |
| Tracts with a change under 200 trees in size (n 1,916) | 0.0326 (0.0125 to 0.0527) |
| Change per square km, in thousands of trees per square km | 0.0818 (0.0445 to 0.1191) |

The slope depends strongly on a few tracts with very large changes. Forty-seven tracts changed by 300 trees or more; twenty are on Staten Island, and their median area is 0.74 square km against 0.18 for the sample. Without them the slope doubles. The per-area slope corresponds to 0.045 per 100 trees in a tract of median area, which is the central prediction. The instrumented estimates have intervals that reach 0.041 and 0.057. So the data do not exclude the central prediction once the form of the exposure is allowed to vary, and three of these variants would meet the support condition. None of them was registered. Under rule 4 they decide nothing. They show that the registered count of trees per tract, which gives large low-density tracts the most leverage, is the least favourable form for the claim, and that "29% of the prediction" is not a stable description.

No variant meets the refutation condition.

### Rent: crosswalk and margins of error

The crosswalk is not a problem. Of the 2,048 tracts, 2,019 have the same boundary as one 2010 tract, and the slope on those alone is 0.0123 (0.0015 to 0.0232).

The margins of error are large. The median standard error of log median rent is 0.060 in 2008-12 and 0.074 in 2018-22. The mean sampling variance of the rent change is 74% of its total variance, and the median tract's is 27%; a minority of tracts with very wide margins account for the difference. Error in the outcome alone widens the interval without bias. Weighting by precision gives 0.0153 (0.0050 to 0.0256), and the half of tracts with the smaller margins gives 0.0160 (0.0034 to 0.0286).

Error in baseline rent does bias the model, because the same error enters the outcome with the opposite sign. The baseline coefficient of -0.179 is partly this artefact. A moment correction for the error gives a tree slope of 0.0115 (0.0012 to 0.0228) with the median error variance and 0.0073 (-0.0044 to 0.0179) with the mean error variance, with intervals from 400 resamples of neighbourhoods. The outcome's notes already say that the exclusion of zero depends on the baseline rent covariate. The correction supports that reading: the lower limit of the registered interval is not robust.

The sample excludes 135 top-coded tracts. Dropping tracts whose 2018-22 rent is 3,500 dollars or more selects on the outcome and removes the fastest risers. This was registered and its effect cannot be estimated from the files.

### Spatial autocorrelation and the standard error

The residuals of the primary model are spatially correlated (Moran's I 0.087 on the six nearest tracts, permutation p 0.001), and so is the tree change (0.260). Clustering by neighbourhood handles most of this. Conley standard errors with a Bartlett kernel are 0.0050 at 1 km, 0.0053 at 2 km, 0.0059 at 5 km and 0.0064 at 10 km, against 0.0055 as registered. Clustering by the 60 four-character districts gives 0.0055. At 10 km the interval is 0.0002 to 0.0251. With fixed effects for the 60 districts the slope is 0.0095 (-0.0005 to 0.0196), close to the registrant's post hoc result with neighbourhood fixed effects. The verdict does not change under any of these. The exclusion of zero does.

## (c) Is the comparison with the research fair?

The arithmetic of the prediction is right: 131 dollars per tree on 300,000 dollars is 0.044% per tree and 0.044 log points per 100 trees. Four things make the comparison loose.

1. The median price of 300,000 dollars is an assumption and is not from the paper, whose sales span thirty years. At 200,000 dollars the prediction is 0.066 (0.026 to 0.105) and at 400,000 dollars it is 0.033 (0.013 to 0.052). The refutation threshold moves with this assumption between 0.013 and 0.026, and the observed upper limit of 0.0235 lies inside that range.
2. The Portland outcome is the median sale price of single-family houses. The New York outcome is median gross rent, and a large share of New York rentals is rent-stabilised, as the registration notes. A percentage effect on prices need not carry over to rents.
3. The Portland exposure is a count of trees planted. The New York exposure is a net change in living trees between two censuses, which the previous section shows is only partly planting.
4. The Portland estimate is at a lag of six years after planting. The New York baseline (2008-12) lies inside the planting period (2005 to 2015), so part of any effect is already in the baseline rent.

Points 2 to 4 all make a New York slope below the Portland figure expected even if the Portland association transferred. The outcome is right to give `graph_effect` as null, since the graph holds no finding on this edge.

## (d) Which alternative explanation is not addressed?

Directed planting. The net change is larger in tracts with lower baseline rent (Spearman -0.22), a lower white share (-0.25) and higher poverty (0.30). The count of young trees does not show this pattern (0.09, 0.15 and -0.08). So the correlation of the registered exposure with poverty comes more from where few trees stood in 2005 and where trees were lost than from where trees were planted. The covariates adjust for this in part.

New construction. The registrant found after the data that adding population change gives 0.0085 (-0.0022 to 0.0193), and I reproduce it. Street trees are required with new buildings, and new buildings carry higher rents. This rival is not in the registration and is not answered.

Pre-trend. Whether trees went where rents were already rising cannot be tested with the files on disk. `data/raw/acs` holds ACS 2008-12 and 2018-22 only, and no 2000 census rent. This is the main unaddressed rival for any positive reading.

Borough. Separate models give Manhattan 0.082 (-0.018 to 0.182), Brooklyn 0.029 (-0.003 to 0.060), Queens 0.007 (-0.011 to 0.024), Staten Island 0.009 (-0.011 to 0.028) and the Bronx -0.001 (-0.014 to 0.013). No borough's interval excludes zero. The Bronx had the largest gain (40%) and shows no association.

The crime result is exploratory and decides nothing, as the outcome says. I did not re-estimate it.

## (e) Could the test have failed?

Yes. At the realised standard error the estimate had to exceed 0.0198 for support and fall below 0.0072 for refutation. With no association the probability of refutation was 0.90. With the central prediction the probability of support was above 0.99. With the lower end of the prediction (0.018) the probability of support was 0.37 and of refutation 0.03. The estimate is 2.29 standard errors from no effect, -5.67 from the central prediction and -0.96 from the lower end. D for the central prediction against no effect is -26.9, and D for the lower end against no effect is 4.3. On the registered model the data reject the central Portland-sized slope and cannot separate a slope a third of that size from none. Section (b) shows that the rejection of the central value depends on the form of the exposure.

The stance of 0.817 (z 2.29) is the distance of the estimate from no effect. A reader of the strip would take it as agreement with the prediction, while the registered model puts the estimate 5.7 standard errors below the predicted value and the verdict is unsettled.

## Requested changes to the outcome

1. Keep the verdict.
2. Reconsider the stance of 0.817, or put a note beside it that it measures distance from zero and not agreement with the predicted size.
3. In the notes, say that the net change correlates 0.31 with young trees and -0.35 with the 2005 count, that 8,840 trees of 2005 have no usable coordinates, and that in Queens and Staten Island the exposure mostly measures losses or census differences.
4. Say that the slope is sensitive to 47 tracts with changes of 300 trees or more (0.0245 without them) and to the per-area form, and that these variants were chosen after the data.
5. Say that the lower limit is not robust: it includes zero without baseline rent, with population change, with district fixed effects and with the correction for error in baseline rent.
6. State that the 300,000 dollar price is assumed and that the thresholds scale with it, and that the baseline rent window lies inside the planting period.
7. Record that no pre-trend test was possible, and add new construction to the rivals.
8. A new registration could use trees of 3 inches or less in 2015 per square km as the exposure and 2000 census rent for the pre-trend.

Recommendation: keep.
