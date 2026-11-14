# Referee report: heat-night-minimum

Verdict recorded: unsettled. Recommendation: keep the verdict, and change the notes as listed at the end.

Referee code: `analyses/critique/referee_heat_night_minimum.py`. It rebuilds the daily series from the cached incident queries and the cached GHCN-Daily files with its own code, without importing `analyses/round5/heat_night/run.py` or `analyses/round2/hot_end/model.py`, and prints its results. I did not read `docs/round5.md`, `docs/what_the_graph_adds.md` or any other write-up of this claim.

## (a) Does the verdict follow from the registered conditions?

Yes. The support condition is a New York lower limit above 1.00, and the refutation condition is an upper limit below 1.075 with a lower limit at or below 1.00. The New York estimate is 1.033 (0.962 to 1.109). The lower limit is below 1.00 and the upper limit is above 1.075, so neither condition is met and the registration says unsettled. Chicago is 1.009 (0.967 to 1.054) against its threshold of 1.035, so neither condition is met there, and the replication is inconclusive by the registered rule. Part (b) is not separated in either city (New York 1.039, 0.897 to 1.204; Chicago 1.092, 0.998 to 1.196). The conditions were applied literally, and `scored()` in `run.py` codes them as written.

Nothing was decided by a measure chosen after the data were seen. The script was committed at 19037d5 and has not changed since (the diff of `run.py`, the round 2 model code, `analyses/heat/common.py` and `concord/` from 19037d5 to the working tree is empty).

The timestamps are in order but close together. The registration commits (19037d5 and 49a9380) are at 01:24:29 on 13 November 2026. The remote branch `prereg/heat-night-minimum` holds commit 44edbc9 at 01:24:38, which contains the registration, the script and the design. The New York incident query with `occur_time` was fetched at 01:24:57 and the Chicago query at 01:25:32. The outcome was decided at 01:27:27. The cache holds no earlier query of either dataset with a time of day; the earlier queries are daily counts, yearly counts and coordinates. Nineteen seconds separate the remote commit from the first fetch, and git records the commit time and not the push time, so the repository cannot show that the push preceded the fetch.

One feature of the registered threshold should be recorded. The refutation threshold of 1.075 was derived from the published calendar-day excess of 1.122. On the shooting days that this claim uses (06:00 to 05:59), the excess from 27 to 33 C is 1.051 (0.988 to 1.118) in New York and 1.035 (0.991 to 1.082) in Chicago. Half of those excesses corresponds to about 1.032 and 1.021 per 5 C of minimum. The upper limits (1.109 and 1.054) are above these values too, so the verdict would be the same. The threshold stays as registered.

## (b) Errors in code, units, joins, dates, geography or uncertainty

Every number I checked reproduced. My daily counts equal the registrant's on every day in both cities for all shootings, day, night, the 00:00 to 05:59 block, the 18:00 to 23:59 block and calendar-day counts. My refit of part (a) gives 1.033 (0.962 to 1.109) in New York and 1.009 (0.966 to 1.054) in Chicago. The part (b) ratios, the six-hour blocks, the following-night ratios, the two-minima models and the pooled estimate of 1.016 (0.979 to 1.054) all match to the third decimal.

I found one small error. `run.py` builds the following night's minimum and the previous day's maximum by shifting rows of the weather file, not calendar days. The Midway file lacks 28 February 2012 and 16 August 2017, so on the four adjacent days the shifted values come from two days away. Two of those days are hot. With a calendar shift Chicago has 1,479 hot days and not 1,481, and the estimate is unchanged at 1.009. The Central Park file has no gap.

Times of day look usable. Times of exactly 00:00 are 0.04% of New York incidents and 0.4% of Chicago incidents, and 7% of times in each city fall on the hour, so there is no default value piled at midnight. Removing the 00:00 times changes nothing.

Variants for part (a) that the registrant did not run, rate ratio per 5 C of the preceding night's minimum:

| Variant | New York | Chicago |
|---|---|---|
| Registered | 1.033 (0.962 to 1.109) | 1.009 (0.966 to 1.054) |
| Poisson, HC0 | 1.033 (0.962 to 1.109) | 1.008 (0.965 to 1.053) |
| HAC errors, 7 lags | 1.033 (0.965 to 1.105) | 1.009 (0.966 to 1.055) |
| Year-by-month terms | 1.014 (0.942 to 1.093) | 1.006 (0.962 to 1.053) |
| Annual harmonics added | 1.020 (0.949 to 1.097) | 1.008 (0.965 to 1.054) |
| Previous day's maximum and minimum added | 1.060 (0.969 to 1.160) | 1.042 (0.989 to 1.097) |
| Rain amount added | 1.034 (0.963 to 1.110) | 1.008 (0.965 to 1.052) |
| Without 2020 and 2021 | 1.042 (0.967 to 1.123) | 1.019 (0.973 to 1.068) |
| TMAX from 27 to 31 C | 1.057 (0.972 to 1.149) | 1.011 (0.958 to 1.066) |
| Second station (LaGuardia; O'Hare) | 0.997 (0.924 to 1.076) | 0.996 (0.954 to 1.039) |
| JFK | 1.020 (0.945 to 1.101) | |
| Days whose next minimum is not more than 1 C lower | 1.063 (0.968 to 1.168) | 1.031 (0.975 to 1.090) |

Every interval includes 1.00, and every New York upper limit is above 1.075. No variant changes the verdict. The point estimate moves between 1.00 and 1.06 with the station and the controls, so the value 1.033 should not be read as a measured effect. In Chicago the O'Hare upper limit (1.039) is close to the threshold of 1.035, and the year-by-month and harmonic variants are within 0.02 of it.

## (c) Is the comparison with the research fair?

The outcome does not claim a test of the graph. The composed prediction is 1.012 (1.000 to 1.031), the registered discrimination is D = 0.13 and 0.37, and the registration says the test is not an endpoint test of the chain. That is correct. The chain itself is weak: the room-temperature finding is from 40 sleep apnoea patients, the aggression finding is on school pupils' self-reports, the odds ratio is used as a rate ratio, and the outdoor-to-bedroom slope is assumed. The registration says most of this. The stance of 0.416 (z = 0.88) is the z of the New York estimate against no effect. A reader of the strip could take it as agreement with the graph, which a test with D = 0.13 cannot show. I suggest a null stance or a note beside it.

## (d) Exploratory claims, multiplicity and rival explanations

The excess from 00:00 to 05:59. The ratios 1.128 (1.021 to 1.246) in New York and 1.129 (1.039 to 1.226) in Chicago reproduce. They are ratios for 33 against 27 C of the daily maximum, which is 6 C and not 5 C; the equivalent per 5 C is about 1.105. Any summary that says 1.13 per 5 C is wrong by that factor. The six-hour blocks were listed in the registration as a secondary result with no prediction about which block would carry the excess, so singling out one of four blocks is a choice made after the data. The outcome puts the result under "Registered secondary results", which is accurate for the table and not for the selection. Corrected for four blocks, the New York p-value is 0.07 (0.018 uncorrected) and the Chicago p-value is 0.016 (0.004 uncorrected). The inverse-variance mean of the two cities is 1.129 with z = 3.7, and p is 0.0008 after the correction for four blocks. The contrast with the evening block, which the outcome implies and does not test, is 1.177 (1.037 to 1.334) in New York and 1.132 (1.023 to 1.252) in Chicago from a binomial model of the 00:00 to 05:59 share of night shootings. The result is stable with HAC errors, year-by-month terms, the holiday term of the following date, and in each half of the period (New York 1.125 and 1.136; Chicago 1.177 and 1.106), though the half-period intervals in New York include 1. The boundary at midnight is not sharp in the data: windows of 02:00 to 05:59 give 1.201 and 1.133, 00:00 to 02:59 give 1.087 and 1.121, and 21:00 to 23:59 give 1.006 and 0.998. My reading is that the result is unlikely to be chance, mainly because the same block appears in two cities, and that it remains a finding chosen after the data that needs its own registration. The outcome's `research_needed` entry already proposes that.

The following night's minimum. The ratios 1.112 (1.049 to 1.179) and 1.064 (1.023 to 1.106) reproduce. This variant was in the registered plan with a stated expectation, so it is a registered secondary result and the label is right. It is one of about nine secondary families, and with z of 3.6 and 3.1 it survives a correction for that number. It passes two checks the registrant did not run. The minimum of two nights later has no effect once the following night is in the model (0.984, 0.923 to 1.048; 0.991, 0.953 to 1.031). Day shootings, which happen before the following night, do not follow it (0.924, 0.813 to 1.049; 1.039, 0.970 to 1.113). It is not robust to one control in New York: with the next day's maximum and a wet-day term for the next date, the New York ratio is 1.073 (0.989 to 1.164) and the Chicago ratio is 1.063 (1.006 to 1.122). The next day's maximum and the following night's minimum correlate at 0.76 on hot days, so the weather record cannot fully separate a warm night from a continuing hot spell. At O'Hare the ratio is 1.041 (1.000 to 1.084). By block, the following night's minimum is strongest from 00:00 to 05:59 (1.243, 1.123 to 1.377; 1.139, 1.055 to 1.230), the hours it measures most directly.

The calendar-day statement. The note labelled exploratory says that about half of New York's published hot-day excess comes from shootings before 06:00 on the hot date. The arithmetic is right (1.102 on calendar days against 1.051 on shooting days). Shootings from 00:00 to 05:59 of a date rise by 1.261 (1.140 to 1.396) in New York and 1.222 (1.125 to 1.328) in Chicago from 27 to 33 C of that same date's maximum, which comes later in the day. With that date's minimum added the ratios fall to 1.149 and 1.127, and the minimum carries 1.129 (1.067 to 1.194) and 1.113 (1.070 to 1.158) per 5 C. This is the same observation as the previous two: shootings in the small hours follow the temperature of the night they occur in. It also means the earlier calendar-day claims (heat-shootings, transfer-chicago-heat-shootings) include shootings that precede the maximum they are regressed on. That criticism applies to more than one claim and may deserve a verdict rule.

Rival explanations not addressed.

1. The three post hoc observations are one finding stated three ways, and they should not be counted as three pieces of support.
2. The GHCN minimum is a calendar-day value. On 36% of New York hot days and 38% of Chicago hot days the next date's minimum is more than 1 C lower, and on some of those days the minimum of date d is set late in the evening by a front and not at dawn. The registration names this as measurement error. It also works in a direction the registration does not state: on those days the "preceding" minimum partly measures the evening of the shooting day, which would raise its coefficient. Excluding those days gives 1.063 (0.968 to 1.168) and 1.031 (0.975 to 1.090), still inconclusive.
3. Humidity is named as a rival and no variant addresses it. Dew point is in the hourly airport files and not in GHCN-Daily. A humid night is also a warm night, so the following-night result may be humid heat.
4. A warm night keeps people outdoors after midnight. The registration names routine activity as a rival for a night effect. The outcome does not use the after-midnight result as evidence of a sleep path, and nothing in these data could separate the two.
5. The six-hour shift assigns shootings from 00:00 to 05:59 to the previous date's calendar terms. Adding the next date's holiday term changes nothing (1.131 and 1.121).

## (e) Could the test have failed?

Yes, in both directions, as the registration computed: about 0.5 for refutation under no effect and 0.5 for support under half the excess in New York. The realised standard errors (0.036 and 0.022 on the log scale) equal the design values. For New York, z is 0.88 against no effect, 0.53 against the composed prediction of 1.012, and -1.12 against the threshold of 1.075. For Chicago, z is 0.42, -0.12 and -1.12. D against the composed prediction is about 0.5 in New York and 0.2 in Chicago, far below 4. The data are compatible with no effect of the preceding night, with the graph-sized effect, and with the preceding night carrying half the excess. Unsettled is the correct description.

## Requested changes to the outcome

1. Keep the verdict.
2. In the notes, say that the six-hour blocks carried no registered prediction, that the 00:00 to 05:59 block was singled out after the data, and give the corrected p-values and the contrast with the evening block. State that the ratio is for 6 C of maximum.
3. Add that the New York following-night ratio becomes 1.073 (0.989 to 1.164) with the next day's maximum and rain in the model, and give the placebo results.
4. Say that the after-midnight excess, the following-night minimum and the calendar-day difference are one observation.
5. Record the row-shift error at the Midway gaps (two hot days; no change in any reported digit).
6. Reconsider the stance of 0.416 for a test that the registration says cannot discriminate.

Recommendation: keep.
