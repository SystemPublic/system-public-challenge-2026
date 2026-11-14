# Referee report: commute-time-depression

Verdict recorded: unsettled. Recommendation: keep the verdict, and change the prediction score from "miss" to "uninformative".

## (a) Does the verdict follow from the registered conditions?

Yes. The registered test is the HC3 slope of age-adjusted depression on mean commute minutes, adjusted for poverty and subway access. I re-ran it from the cached ACS summary files and EHDP files and obtained the recorded result, -0.77 (-1.63 to +0.10) points per 5 minutes, n = 42. The interval includes zero, so neither support_if nor refute_if is met, and PRECEDENCE rule 2 gives unsettled. Nothing in the outcome suggests the conditions were changed after the data were seen.

## (b) Errors in code, units, joins, denominators or model

I found no error that changes the verdict.

The ZCTA to UHF42 crosswalk at the registered commit has 215 rows and no ZCTA assigned to two UHFs, so summing ZCTA counts within UHF does not double-count. One row maps to code 9999 and drops out on the merge with the EHDP data. The numerator (B08013_001, aggregate minutes) and the denominator (B08303_001, workers who did not work at home) describe the same population, so the mean is correct. Values run from 25.7 to 50.2 minutes, which is plausible.

The depression measure (2417/1324) is the PHQ-8 score of 10 or more, age-adjusted, pooled 2017-18. It measures current symptoms, not diagnosis, so a diagnosis-access explanation does not apply. The EHDP note that "UHF42 data for correlates are based on UHF34 data" refers to correlate breakdowns. The 42 values used here are distinct UHF42 estimates.

The model has one weakness that the registration did not anticipate. The CHS estimates differ greatly in precision; five are flagged for large relative standard error, and three of these are in Manhattan or Staten Island. Unweighted OLS gives them equal weight. Weighting each neighbourhood by the inverse variance from its published interval changes the slope to +0.19 (-0.78 to +1.16). Dropping Manhattan changes it to +0.67 (-0.73 to +2.07). The negative point estimate therefore depends on a few imprecise Manhattan neighbourhoods. Neither variant was registered, so neither can decide the verdict, but the outcome's statement that the sign is "opposite to the prediction" overstates what the data show.

The interval uses 1.96 rather than a t quantile with 38 degrees of freedom. This makes no difference to the verdict.

## (c) Is the research comparison fair?

The direction comparison is fair. The size comparison could not succeed. The registration predicts +0.05 to +0.3 points per 5 minutes and says a slope above +1 would indicate confounding. The standard error of the design is about 0.44 points. If the true slope were +0.3, the chance that the lower limit would exceed zero is about 10%; at +0.05 it is about 3%. The support condition could be met only by an estimate near +0.9 or more, which is close to the range the registration itself calls confounded. The registration could not have confirmed the research association except through confounding. This was knowable before the data were queried, from the expected standard error of a 42-unit regression.

For this reason "miss" is the wrong prediction score. The interval (-1.63 to +0.10) touches the lower end of the predicted range, and the test had little power against that range. "Uninformative" describes the result.

## (d) Alternative not addressed

The registration lists composition and dilution but the model adjusts for neither. The most specific unaddressed alternative is differential reporting on the PHQ-8. Several of the lowest-depression neighbourhoods with long commutes (Flushing 5.5, West Queens 6.1, Borough Park 5.5, Bayside 4.9, and the southern Staten Island neighbourhoods) have large Asian immigrant or Orthodox Jewish populations, in which there is evidence that symptom questionnaires give lower scores at equal distress. Such reporting differences would bias the slope towards a negative value regardless of any commute effect. Selection into work is a second unaddressed alternative: people with depression are less likely to be employed, and the commute measure describes only workers. Adjusting for the employment-to-population ratio would address the dilution alternative directly.

## (e) Is the settle condition right?

Partly. The outcome is right that a neighbourhood comparison cannot settle the question, and its arithmetic (implied slope at most 0.3 against a standard error of 0.44) agrees with mine. Of the two routes it proposes, only the first is feasible. A commute-time item added to the CHS would give person-level data in New York. ACS PUMS cannot be linked to a health survey at the person level, because PUMS records are anonymous and carry no identifier shared with any health survey. The second route should be removed or restated as a statistical match, which would not settle the question.

## Recommendation

Keep unsettled. Change prediction_scored to state that the test had about 10% power against the upper predicted slope, and report the weighted and non-Manhattan slopes in the notes as unregistered checks that reverse the sign. Remove the PUMS linkage from the settle condition.
