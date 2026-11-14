# Referee report: heat-ac-shootings

Verdict recorded: confirmed. Recommendation: keep "confirmed" for the statement as registered, and add the narrowing notes listed at the end. The result does not support any statement about air conditioning, and it depends on how the day is defined.

Referee code: `analyses/critique/referee_heat_ac.py`. It rebuilds the district table, the district of each shooting and the daily series from the cached query, the cached GHCN-Daily files and the Health Department files with its own code, without importing `analyses/heat_solutions`. It prints its results and writes no file. I did not read `docs/heat_solutions.md` or any other write-up of this claim.

## (a) Does the verdict follow from the registered conditions?

Yes, by rule 1. The support condition is a 95% lower limit of the difference above 0. The registered model gives 0.043 (0.007 to 0.080), so the condition is met. Nothing was decided by a measure chosen after the data were seen.

The timestamps are in order and close together. The registration records 07:52:12 on 13 November 2026. The remote branches `prereg/heat-ac-shootings` and `prereg/heat-ac-heat-calls` hold commits at 07:53:07 and 07:53:08 with the registration, `run.py` (sha256 ff13670222b73baa) and `common.py` (sha256 c271c2fae50f98b5), which match the plan. The dated shootings query was fetched at 07:53:21, 13 seconds after the commit. Git records the commit time and not the push time, so the repository cannot show that the push preceded the fetch. The queries in the cache before the registration are the ones the registration lists: undated coordinates by incident (07:45), counts of HEAT calls by district and by year (07:47) and citywide daily counts of shootings (07:48). No query by district and date precedes the registration. The results file was written at 07:54:43 and the outcome at 07:58:34.

The change to `run.py` after registration is two lines, 170 and 224. Both replace `str[:2]` with `str.split(":").str[0]` when reading the hour. The outcome's account of this change is inaccurate in two details. First, the shootings incident file has no time that is not zero-padded. The registered line raises no error on any of its 24,429 rows, and the two versions give the same hour for every incident. The unpadded times (390 of 29,744) are in the victims file 833y-fsy8, which only heat-school-out uses, so the error occurred at line 224. Second, line 224 comes after the air-conditioning models in `main()`, so in the failed run those models had been fitted in memory. The script prints and writes only at its end, so no result was displayed or saved before the change. The change cannot affect any number in this claim: the primary model does not use the hour, and the one secondary result that does (00:00 to 05:59) is identical under both lines. The note should say this instead of "some times in the file are not zero-padded" and "no model had run".

Does the registered condition measure what the claim states? It measures the statement literally. The statement is about one linear slope over all days of the year, and the condition tests that slope. It does not measure what the claim's title, yardstick and graph evidence are about, which is air conditioning. The yardstick of 0.042 assumes that households without air conditioning carry half of the citywide slope. The data place the difference on days when air conditioners are off. In my refit the difference is 0.105 (-0.001 to 0.211) on days below 10 C, 0.161 (0.033 to 0.288) from 10 to 20 C, -0.009 (-0.184 to 0.165) from 20 to 27 C and -0.178 (-0.329 to -0.027) at 27 C and above. From October to April it is 0.075 (0.031 to 0.119), and from May to September it is -0.028 (-0.095 to 0.039). The piecewise model gives 0.073 (0.032 to 0.113) below 27 C and -0.123 (-0.237 to -0.009) above. The sign above the knot is negative for knots at 24, 27 and 30 C and at LaGuardia and JFK. The `prediction_scored` sentence that the estimate "is close to the size expected if households without air conditioning carried half the slope" should be removed. The agreement of 0.043 with 0.042 is a coincidence of two numbers, since the range of temperature that produces the 0.043 is the range in which air conditioning cannot act.

## (b) Errors in code, units, joins, dates, geography or uncertainty

The deciding numbers reproduced. My daily counts for the two halves equal the registrant's file on all 7,548 days. My district table gives the same split for all 59 districts (median 91.711%, means 86.063% and 94.292%). My refit of the primary model gives 0.043 (0.007 to 0.080) on 6,932 days. The halves' own rate ratios, the terciles, the income halves, the periods, the hot-day contrast, the district regression and the leave-one-borough-out results all match to the third decimal.

The coordinate correction is right. Of 24,429 incidents, 23,988 have a negative value in the latitude column and a positive value in the longitude column, 437 are in the right order (all of them from 2026), and 4 have 0 and 0. After the correction 24,425 points are inside the city's bounding box, and 24,367 fall in one of the 59 districts. If the correction is reversed, no point falls in any polygon. The 62 unassigned incidents are the 4 zero points and points in parks or on the water. The rule in `fix_latlon` (swap when the first value is negative and the second positive) handles both orders.

The districts are not households. The air-conditioning share varies within a district by up to 3.6 points across tabulation areas, and 12 districts are within 1 point of the median, so the split is coarse near the cut. The two halves differ by 8 points of households, and 81.6% of incidents are in the low half. The registration states both facts.

The definition of the day matters, and this is the main problem with the confirmation. The model counts a shooting on its calendar date and regresses it on that date's maximum. Shootings from 00:00 to 05:59 are 34.7% of incidents (8,480), and the maximum of their date comes hours later. With the day defined from 06:00 to 05:59, so that a small-hours shooting is counted with the preceding afternoon, the primary difference is 0.025 (-0.011 to 0.061) on 6,902 days. The lower limit is below 0 and the upper limit is above 0.042, which the registered rule reads as unsettled. The parts are as follows. Shootings from 06:00 to 23:59 alone give 0.051 (0.006 to 0.096). Small-hours shootings give 0.034 (-0.027 to 0.095) on the same date's maximum, as registered, and -0.019 (-0.079 to 0.041) on the previous date's maximum. The confirmation therefore holds for shootings after 06:00 and is lost when the small-hours shootings are attached to the afternoon that preceded them. By rule 4 my variant does not decide the verdict. The referee of heat-night-minimum raised the same point about calendar days for the citywide claims.

Variants the registrant did not run, difference of log rate ratios per 5 C:

| Variant | Calendar day | Day from 06:00 to 05:59 |
|---|---|---|
| Registered model | 0.043 (0.007 to 0.080) | 0.025 (-0.011 to 0.061) |
| HAC errors, 7 lags | 0.043 (0.008 to 0.078) | 0.025 (-0.010 to 0.060) |
| Year-by-month terms | 0.051 (0.012 to 0.089) | 0.030 (-0.008 to 0.068) |
| Without 2020 and 2021 | 0.058 (0.020 to 0.097) | 0.037 (-0.002 to 0.076) |
| Previous day's maximum added | 0.069 (0.023 to 0.115) | 0.044 (-0.001 to 0.090) |
| Income halves pooled by inverse variance | 0.034 (-0.007 to 0.076) | 0.023 (-0.018 to 0.065) |
| Piecewise, below 27 C | 0.073 (0.032 to 0.113) | 0.044 (0.004 to 0.084) |
| Piecewise, above 27 C | -0.123 (-0.237 to -0.009) | -0.087 (-0.205 to 0.031) |
| Days of 27 C or more | -0.178 (-0.329 to -0.027) | -0.133 (-0.284 to 0.017) |
| LaGuardia | 0.037 (0.001 to 0.074) | |
| JFK | 0.048 (0.007 to 0.088) | |

The standard errors are sound. The Pearson statistic of the binomial model is 1.03 per degree of freedom, and HAC errors with 7 lags are slightly smaller than HC0. The calendar-day result survives year-by-month terms and a second and third weather station. It does not survive the 06:00 day, and the lower limit is at or below 0 without the Bronx, without Brooklyn and without Queens (the outcome reports this). The two periods differ: 0.068 (0.025 to 0.112) for 2006 to 2019 and -0.023 (-0.088 to 0.042) for 2020 to 2026, and the interaction term is -0.040 (-0.077 to -0.003).

## (c) Is the comparison with the research fair?

There is no research to compare with. The graph holds nothing on air conditioning and violence, and `graph_effect` is null. The second graph record is about heat-related death and hospital admission, which is a different outcome. The one cited paper (Heilmann and others, Los Angeles) is cited from memory and concerns poverty and housing age, not air conditioning. The outcome nevertheless carries a stance of 0.824 (z = 2.34). That number is the z of the city estimate against no difference, and on the strip it will be read as agreement with research. Rule 6 gives a null stance when the city effect has no value that expresses a research direction. I recommend a null stance here.

## (d) Which alternative explanation is not addressed?

Income is named as the rival and is not separated. I confirm the Spearman correlation of 0.699 between air-conditioning share and median income, and 23 of the 29 low-AC districts are in the low-income half. The air-conditioning share also correlates at -0.72 with the percentage of Black residents, which the registration does not mention. Within the low-income half the contrast rests on 1,088 incidents in six high-AC districts, and within the high-income half it is 0.018 (-0.034 to 0.069). The income-stratified estimates pooled by inverse variance give 0.034 (-0.007 to 0.076), which includes 0. The income contrast with air conditioning ignored is 0.028 (-0.002 to 0.057). The district regression, which treats both as continuous, gives -0.032 per 10 points of air conditioning (-0.077 to 0.013) alone and -0.033 (-0.079 to 0.013) with income. No model separates the two, and none shows an air-conditioning difference that excludes 0 once income is in the model. The outcome reports these numbers but the verdict note does not name income.

Three explanations fit the temperature pattern better than air conditioning does. The first is outdoor life: in districts with more street activity, shootings rise as days go from cold to mild, and the rise is complete by about 20 C. The second is saturation: the low-AC districts' share of incidents is already 82%, and on hot days activity in the other districts may catch up. The third is that the linear term is a poor description of both halves, so a difference of two linear slopes summarises a difference in the shape of two curves. The outcome's `research_needed` entry on the slope below 27 C covers the first. Borough composition is a further rival: the estimate within Brooklyn is 0.053 (-0.008 to 0.115), within Queens 0.044 (-0.028 to 0.117), within Manhattan 0.000 (-0.086 to 0.086), and the Bronx has only 169 incidents in high-AC districts.

The hot-day reversal is itself one of about ten registered secondary results. Its p-value is 0.02 uncorrected, and with the 06:00 day its interval includes 0. It should be reported as a secondary result that contradicts the air-conditioning reading, not as a finding that high-AC districts are more heat-sensitive.

## (e) Could the test have failed?

Yes. The registered design gives a probability of 0.025 for support and 0.67 for refutation when there is no difference, and the registrant's prior for "confirmed" was 0.2. The estimate is z = 2.34 from no difference and z = 0.09 from the half-carry value, so D = 5.46, above the threshold of 4 in rule 8. The test discriminated between its two registered hypotheses. It could not discriminate between air conditioning and any other reason for a steeper whole-year slope in poorer districts, and the registration says so under `alternatives`.

## Recommended changes

1. Keep the verdict "confirmed" under rule 1, with the label narrowed to the whole-year slope on calendar days. The verdict note should say that the difference is 0.025 (-0.011 to 0.061) when the day runs from 06:00 to 05:59, that it comes from days below about 20 C and from October to April, that the sign reverses at 27 C and above, and that the interval includes 0 once the income halves are pooled.
2. Remove the sentence in `prediction_scored` that compares the estimate with the half-carry value.
3. Set the stance to null, since the graph has no finding on air conditioning and violence.
4. Correct the note on the changed line: the unpadded times are in the victims file, the change does not alter any hour in the incident file, and the air-conditioning models had been fitted but not printed or saved when the first run stopped.
5. Register a new claim if the air-conditioning question is to be tested: the contrast on days of 27 C or more, with the day from 06:00 to 05:59 and with income in the model.

Recommendation: keep "confirmed", narrowed as in item 1. If the repository adopts the 06:00 day as a verdict rule for shootings claims, the verdict under that rule is unsettled.
