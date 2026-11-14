# Referee report: heat-extremes-downturn

The recorded verdict is contested. I recommend keeping it, because the registered refutation condition is met, and change the label and notes as listed at the end. The verdict is correct as a statement that the registered downturn did not occur. It is not robust as a statement that assaults are more frequent at 38 C and above than at 32 to 35 C.

Referee code: `analyses/critique/referee_heat_extremes.py`. It rebuilds the daily series of the four deciding cities from the raw Phoenix file, the raw Tucson file, the cached Dallas query and the cached GHCN-Daily files with its own code, without importing `analyses/heat_extremes`, and prints its results. For the questions on time of day, report date, family violence and station choice I fetched incident-level rows for Dallas (28,238 rows) and Austin (49,029 rows) and five second weather stations on 13 November 2026 into `~/opt/nyc-concordance/heat_extremes/referee/`. I did not read `docs/heat_extremes.md` or any other write-up of this claim.

## (a) Does the verdict follow from the registered conditions?

The verdict follows. The refutation condition is a 95% lower limit of the DerSimonian-Laird pooled rate ratio above 1.00. The pooled ratio is 1.035 (1.008 to 1.063), so the condition is met and rule 1 gives contested. `outcome.py` codes the three conditions as written. There is one deciding test and no choice among measures.

Nothing was decided by a measure chosen after the data were seen. `build.py`, `model.py`, `test.py`, `describe.py` and `power.py` are in the registration commit 96174c4 (07:58:36 on 13 November 2026, on the remote branch `prereg/heat-extremes-downturn`), and their diff from that commit to the working tree is empty. The registration is stamped 07:58:34 and `test_results.json` was written at 07:58:45, eleven seconds later. The daily count files were built between 07:43 and 07:49, before the registration, which the registration says. The repository cannot show that no model was fitted to them in those minutes. One fact supports the registrant's account: the power simulation of 07:50 assumed a dispersion of 0.05 to 0.15, and the fitted values are 0.006 to 0.017. A registrant who had fitted the counts would have known this.

The margin is small. The lower limit is 1.008, the z against 1.00 is 2.56 (p = 0.010), and no single city excludes 1.00 (p = 0.09, 0.05, 0.54 and 0.09). The outcome says the condition is met "by less than the sampling error (rule 10)". Rule 10 concerns conditions written on a point estimate. This condition is on an interval bound, so the reference to rule 10 does not apply, and the sentence should give the margin (0.008) and the variants below instead.

The outcome's notes say that the data "fit a plateau above about 35 C better than either registered alternative". The registration assigns a plateau to the verdict unsettled and a linear rise to contested. The recorded verdict and the recorded reading therefore point to different registered alternatives. The verdict is the one the conditions give. The notes should say this directly: the condition was written as "lower limit above 1.00", and a small rise that is well short of the linear prediction meets it.

## (b) Errors in code, units, joins, dates, geography or uncertainty

The deciding numbers reproduced. My rebuilt daily counts equal the registrant's on every day in all four cities (Phoenix 59,432 incidents, Tucson 19,572, Dallas 22,960, Austin 48,660), and the temperatures are identical. My refit gives Phoenix 1.038 (0.994 to 1.084), Tucson 1.062 (0.999 to 1.130), Dallas 0.977 (0.906 to 1.052), Austin 1.040 (0.994 to 1.087) and a pooled 1.035 (1.008 to 1.063), Q = 3.07. The registered sensitivity results S1 to S3 also match to the third decimal. I found no coding error that changes a number.

The table gives the pooled ratio under variants. Those above the line were run by the registrant.

| Variant | Pooled ratio |
|---|---|
| Registered | 1.035 (1.008 to 1.063) |
| Year-by-month terms (S1) | 1.031 (1.003 to 1.061) |
| May to September (S2) | 1.044 (1.009 to 1.080) |
| Without 2020 and 2021 (S3) | 1.027 (0.997 to 1.057) |
| Hartung-Knapp interval, t on 3 degrees of freedom | 1.035 (0.992 to 1.081) |
| Poisson, HC0 | 1.035 (1.008 to 1.063) |
| HAC errors, 7 lags | 1.034 (1.007 to 1.062) |
| Without 2020 only | 1.030 (1.003 to 1.059) |
| June to September with year-by-month terms | 1.034 (0.980 to 1.092) |
| Daily minimum added | 1.019 (0.984 to 1.056) |
| Rain amount and previous day's maximum added | 1.022 (0.987 to 1.059) |
| Second station in Phoenix, Dallas and Austin | 1.017 (0.987 to 1.049) |
| Day from 06:00 to 05:59 in Phoenix, Dallas and Austin | 1.030 (0.993 to 1.069) |
| Hot days in June to August only | 1.029 (0.997 to 1.061) |
| Last 3, 6 or 12 months of each series dropped | 1.034, 1.033, 1.037 (lower limits 1.006 to 1.009) |
| 2017 to 2025 in every city | 1.039 (1.009 to 1.071) |
| Reference bin 29 to 35 C | 1.042 (1.017 to 1.068) |
| Hot bin from 100 F (37.7 C) | 1.041 (1.016 to 1.068) |
| Austin without family violence | 1.034 (1.005 to 1.064) |
| Without Phoenix; Tucson; Dallas; Austin | 1.031 (0.989 to 1.075); 1.029 (0.997 to 1.061); 1.044 (1.015 to 1.073); 1.031 (0.989 to 1.074) |
| Without one calendar year, 24 fits | 1.030 to 1.039; lower limit 0.998 without 2018, otherwise 1.002 to 1.011 |

The point estimate stays between 1.017 and 1.044. The lower limit is at or below 1.00 in eight of the variants and when any city other than Dallas is left out. No variant has a lower limit below 0.98, so the registered downturn band of 0.88 to 0.98 is excluded in all of them. The z of the registered estimate against 0.98 is 4.1. A variant with year-by-month and month-by-weekday terms gave a Phoenix standard error seven times larger than any other fit, and I do not report it.

The interval is the weakest part of the procedure. A DerSimonian-Laird pool of four estimates with a normal quantile is known to give intervals that are too narrow. The Hartung-Knapp interval, which is the usual correction for a small number of studies, is 0.992 to 1.081. The registration fixed the DerSimonian-Laird interval, so the verdict does not change, but a reader should not take 1.008 as a secure bound.

The offence definitions differ between cities. The Dallas file withholds family-violence cases: 23,299 of its incidents are coded "AGG ASSAULT - NFV" and 35 are coded family violence. In Austin 47% of the incidents carry the family-violence flag or a family or strangulation offence type, and the share rose from 37% in 2003 to 2008 to about 50% afterwards. Austin's category also includes deadly conduct (7.5%). Phoenix and Tucson use a UCR summary category with no family-violence field. The four series are therefore not the same offence, and the registration and outcome do not say so. The difference does not explain the Dallas estimate. In Austin the ratio is 1.039 (0.976 to 1.106) for family violence and 1.038 (0.976 to 1.104) for the rest, and pooling Austin's non-family incidents with the other three cities gives 1.034 (1.005 to 1.064). In Phoenix the ratio is 1.008 (0.946 to 1.073) at residences and 1.034 (0.963 to 1.111) outdoors, which do not differ (z = 0.5).

All four series are dated by occurrence, as the plan says. In Dallas 96% of incidents are reported within one day of occurrence and 0.3% after more than 30 days. In Austin the shares are 95% and 1.0%. Dating Dallas by report date gives 0.999 (0.929 to 1.075) against 0.977 by occurrence date. Dating Austin by report date gives 1.037. Restricting to incidents reported within one day changes neither.

Dropping the last 3, 6 or 12 months of each series changes nothing, so late reports are not a concern. The Phoenix file has a break that the outcome does not mention. From 3 September 2025 the file carries no time of day, September 2025 has 417 incidents against about 570 a year earlier, and the count of all offence rows rises by 40% in October 2025. This looks like a change of records system. The file runs to 31 December 2025 and the series was cut at 30 November 2025 without a stated reason. Ending Phoenix at 31 August 2025 gives the same estimate (1.037).

Each weather station is inside or beside its city, and the daily maximum is spatially coherent, so the stations are reasonable. The 38 C threshold is sensitive to the station all the same. Camp Mabry records 710 days at 38 C or more and Austin-Bergstrom, also inside the city, records 443. Sky Harbor records 1,112 and Phoenix Deer Valley, in the north of the city, records 854 on the same dates. Deer Valley is 1.75 C cooler on average. With the second stations the estimates are Phoenix 1.003 (0.962 to 1.046), Dallas 0.974 and Austin 1.027, and the pool is 1.017 (0.987 to 1.049). A fixed threshold at a warm station is partly a comparison at a lower real temperature across the city, which is one reason the hot bin can sit on the rising part of the curve.

The hot days cluster in particular years and months. In Dallas 73% of the 187 hot days fall in four years (2018, 2022, 2023, 2026). In Phoenix 817 of the 1,132 hot days are in June to August, when there are 13 reference days, so only 46% of Phoenix hot days share a year-month with any reference day. The Phoenix contrast rests on the shoulder months and on the additivity of month and temperature terms. Splitting the hot bin gives Phoenix 1.045 (0.996 to 1.096) outside June to August and 1.020 (0.956 to 1.088) within, so the two sources agree. Leaving out single years moves the pooled estimate little, and only the removal of 2018 puts the lower limit below 1.00.

Incidents from 00:01 to 05:59 are 17% of the Phoenix series, 23% of Dallas and 28% of Austin, and they are counted on the calendar date whose maximum comes ten or more hours later. Phoenix also has 5.4% of incidents at exactly 00:00, which is a default value. Moving the small-hours incidents to the previous date gives Phoenix 1.046 (1.003 to 1.091), Dallas 0.953 (0.885 to 1.027) and Austin 1.036 (0.990 to 1.084), and with Tucson unchanged the pool is 1.030 (0.993 to 1.069). Tucson publishes no time of day. The calendar-date count is the registered measure, so this is a robustness result and not a correction.

## (c) Is the comparison with the research fair?

The outcome claims no numeric comparison with the graph, and `graph_effect` is recorded as shape only. That is right. The graph findings are on homicide and shootings, and the claim is on aggravated assault as each police department defines it. The registered linear band of 1.06 to 1.25 came from published slopes for other outcomes. The observed 1.035 is below 1.06 (z = -1.8) and below the cities' own extrapolated slope of 1.075 (z = 2.6 as the outcome computes it). The stance of -0.857 expresses disagreement with the registered downturn and not agreement with the graph's monotonic rise. A note beside the stance should say so.

The planned statement that one curve in degrees fits better than one curve in percentiles rests on an unequal comparison. The registrant's degree bins hold 2,700 to 6,400 days each. The percentile bins put half of all days into two bins of about 11,500 days, so the percentile model cannot follow the curve over the range where most days lie. With the registrant's bins degrees are better by 496 AIC units, which I reproduce. With ten equal-count bins on each scale the difference is 43. With splines of equal degrees of freedom it is about 450, so the advantage is real over the whole range. It does not bear on adaptation, for two reasons. A scale of degrees from each city's own mean, which is a relative scale, fits as well as absolute degrees or better (3,053 against 2,822 units with ten bins, 3,227 against 3,217 with twenty). The comparison therefore shows that the curve is close to linear in degrees and that a rank transformation distorts it, not that cities share one absolute curve. At the hot end, where the adaptation question lies, the two scales cannot be told apart: among the hottest quarter of each city's days degrees are better by 4 to 17 units, and in the four hot cities alone percentiles are better by 5. The write-up should not present this comparison as evidence against adaptation.

## (d) Which alternative explanation is not addressed?

1. Night temperature is the first rival. With the daily minimum in the model the pooled ratio is 1.019 (0.984 to 1.056). Very hot days have warm nights, and assaults in the small hours of the calendar date precede the maximum. In Phoenix the incidents of the night that follows a hot day rise by 1.129 (1.019 to 1.251), and the afternoon and evening incidents do not (1.011, 0.956 to 1.069). The excess at 38 C and above may belong to the night and not to the heat of the day. The registration does not name this rival.
2. Time of day in Dallas is the second. Incidents from 12:00 to 23:59 give 0.894 (0.811 to 0.984) in Dallas, 1.063 (1.001 to 1.129) in Austin and 1.011 in Phoenix. The Dallas value agrees with the daylight downturn that Rotton and Cohn reported for the same city. It is one of twelve cells I looked at and is not significant after correction, so it is a lead for a new registration. It does show that a pooled daily count can hide opposite movements by hour, which the outcome's `settle` text already proposes to test.
3. The station and the threshold are described above, and the registered alternatives do not include them.
4. The registrant ran the test without the pandemic years (S3) and reports that the lower limit falls to 0.997. Leaving out 2020 alone keeps it at 1.003.
5. Recording on very hot days is named in the registration and cannot be tested with these files. The report-date variant gives no sign of it.

The exploratory New York heat-wave ratio for days two and later of a run of days at 32 C or more, against first and isolated days, is 0.836 (0.739 to 0.946) for shootings, which reproduces. The contrast and the 32 C threshold were written in `describe.py` before the registration, so the selection is limited, and the registration labels the analysis exploratory. Three things limit it further. It does not replicate with the same code in the other two cities that have shooting series: Chicago gives 0.983 (0.913 to 1.057) and Philadelphia 1.036 (0.912 to 1.177), and the two together give 0.996 (0.935 to 1.061). It depends on the threshold: 1.023 at 29 C, 0.966 at 30, 0.932 at 31, 0.836 at 32, 0.901 at 33 and 0.839 at 34, with only the 32 C interval excluding 1.00. Part of the contrast comes from first days of a run being high (1.098 against isolated days) and not from later days being low. New York felony assaults give 0.965 (0.930 to 1.001), and aggravated assaults in Chicago and Philadelphia give 1.008 and 1.018. The result is stable to year-by-month terms (0.833), to the minimum and the previous day's maximum (0.822) and to leaving out 2020 and 2021 (0.864). It should be reported as a New York shootings result that two other cities do not show, and not as a property of heat waves.

## (e) Could the test have failed?

The test could have failed. The registration's simulation gives each of the three verdicts under the corresponding truth, and the realised pooled standard error (0.0135 on the log scale) is smaller than the simulated 0.018 to 0.022, so the test was sharper than planned. The z of the pooled estimate is 4.1 against the upper end of the predicted band (0.98), 2.56 against no difference, -1.8 against the lower end of the published linear band (1.06) and -2.6 against the cities' own extrapolated slope (1.075). The test separated the downturn from the result clearly. It separated the result from no difference by a margin that most reasonable changes of procedure remove.

## Requested changes

1. Keep the verdict contested. State in `prediction_scored` and the notes that the support condition fails by a wide margin (z = 4.1 against 0.98, and every variant excludes the predicted band), and that the refutation condition is met by 0.008 and is not met with a Hartung-Knapp interval, with the daily minimum in the model, with second stations, with a 06:00 day, without 2020 and 2021, without 2018, or without any one of Phoenix, Tucson and Austin. Remove the reference to rule 10.
2. Word the result as "no downturn at 38 C; the rate is level or slightly higher", and not as "assaults are more frequent at 38 C and above". Say that the registration assigned a plateau to unsettled, and that the label contested comes from the literal condition.
3. Say in the outcome that the Dallas series excludes family violence, that 47% of the Austin series is family violence, and that the Austin split shows no difference.
4. Record the Phoenix break of September 2025 and the reason for ending the series on 30 November 2025.
5. Do not use the degrees-against-percentiles comparison as evidence on adaptation. Report the equal-bin and city-mean versions with it.
6. Report the New York heat-wave ratio with the Chicago and Philadelphia values and the threshold table beside it.
7. Add a note to the stance that it measures disagreement with the registered downturn.

I recommend keeping the verdict (contested), with the changes above.
