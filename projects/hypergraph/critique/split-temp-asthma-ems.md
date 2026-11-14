# Referee report: split-temp-asthma-ems

Verdict recorded: unsettled. Referee scripts: `referee-split-temp-asthma-ems/a.py` and `b.py` in the session scratch folder (not in the repository). The registrants' documents in docs/ were not read.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required a cool half-year rate ratio per +5 C below 1 with an interval excluding 1, and refutation the reverse. The estimate is 1.0023 (0.9927 to 1.0120), so neither condition is met and rule 2 of PRECEDENCE gives unsettled. The prediction is scored a miss, which is correct: the interval lies above the registered range of 0.95 to 0.99. No measure chosen after the data decides anything. The by-month slopes are labelled exploratory.

The order of events is consistent with registration before data. The registration was committed at 22:49:54 on 12 November 2026, and the branch prereg/split-temp-asthma-ems exists on GitHub with a commit made at 22:50:02 (I can see the commit time and that the branch exists, not the time of the push). The two asthma queries in data/cache/socrata were fetched at 22:55:41 and 22:55:48, and no earlier cached query of 76xm-jjuj contains an asthma code. The Central Park file was fetched at 20:23:55, before registration; that is the exposure and its earlier use is disclosed. The outcome was written at 23:00:32. The analysis script was not committed with the registration and its file time (22:56) is after the fetch, so the claim that the model was fixed in advance rests on the plan text, which the script does follow.

One deviation is declared: the series starts on 2006-10-01 because the call types first appear on 2006-09-28. I confirmed the first non-zero day is 2006-09-28 and that there are no zero days afterwards.

## (b) Errors in code, units, joins, dates or uncertainty

I found no error. Temperatures are converted from tenths of a degree in concord/noaa.py and divided by 5 in the script. The four-day mean is the day and the three days before it. There are no missing temperature days. From the cached query I reproduce the deciding number exactly: 1.0023 (0.9927 to 1.0120), 3,645 days. The Pearson dispersion is 1.44, which the Newey-West errors allow for; with 28 lags the interval is 0.9919 to 1.0129.

Annual asthma dispatches fall from about 24,000 in 2014 to about 9,000 in 2024. Year-month fixed effects absorb this, but the decline is large enough that a change in call-typing practice should be considered (see d).

Variants the registrant did not run, all for the cool half-year:

| Variant | Rate ratio per +5 C | 95% interval |
|---|---|---|
| Registered model | 1.0023 | 0.9927 to 1.0120 |
| Plus a linear day trend inside each month | 0.9951 | 0.9862 to 1.0042 |
| Year fixed effects and four annual harmonics instead of year-month, lags 0-3 | 0.9849 | 0.9715 to 0.9985 |
| Same, lags 0-14 | 0.9654 | 0.9386 to 0.9928 |
| Year-month fixed effects, lags 0-21 | 1.0273 | 1.0059 to 1.0491 |
| Days at or below the 5th percentile (-1.5 C) against other days, year-month effects | 1.019 | 0.991 to 1.048 |
| December to February only | 0.9971 | 0.9835 to 1.0109 |
| Before March 2020 | 0.9977 | 0.9872 to 1.0083 |

The sign of the cool-season slope depends on how time is controlled. With year effects and harmonics the slope is negative and its interval excludes 1, which would have met the support condition; with year-month effects and a 21-day window it is positive with an interval excluding 1. The first of these compares cold and warm spells across a whole winter and so is open to influenza timing; the second leaves little variation inside a month. Neither was registered and neither changes the verdict, but the notes should not describe the result as a bound that holds generally. It is a bound on the slope within a calendar month at lags of up to four days.

## (c) Is the comparison with the research fair?

The direction comparison is fair and the size comparison is not attempted, which is right (graph_effect has no estimate). The studies report relative risks at the 5th temperature percentile against a median or optimum, cumulated over lags of up to 21 days, for hospital admissions or emergency visits, mostly of children, in East Asian cities. The city measure is ambulance dispatches for all ages, a linear slope per 5 C over four days within a month. The outcome's settle field says this.

I checked association qLlYYVLSmN (PMID 35817164) against its PubMed abstract. The value 2.16 (1.38 to 3.38) is in the abstract, but it is the relative risk of cold on days with high PM2.5; the same abstract gives 1.64 (1.06 to 2.54) on days with low PM2.5. The graph row's variable name, "cold (5th percentile of temperature)", drops the stratum. The row nAROqDqWGF, 1.52 (0.98 to 2.36), is the low-PM10 stratum of the same study. So one Hefei study contributes several rows that are strata of one analysis, and the count "16 of 17 findings" overstates the number of independent results; the registration's "7 studies" is the better count.

## (d) Alternative not addressed

The registration names the absorption of asthma calls by the difficulty-breathing codes and does not test it. I queried DIFFBR, DIFFFC, RESPIR and RESPFC by day (one new Socrata query, cached in the scratch folder) and fitted the registered model. In the cool half-year these dispatches rise with temperature, 1.0125 (1.0055 to 1.0196), and asthma plus breathing codes together give 1.0113 (1.0046 to 1.0181). In the warm half-year the figure is 1.0261 (1.0172 to 1.0352). Reclassification on cold days therefore does not hide a cold effect: the broader respiratory outcome moves in the direction opposite to the prediction. This is a general activity or call-volume response to milder days as much as a respiratory one, and a comparison series (all medical calls) would be needed to separate the two.

The registration does not name a further possibility: the fall in asthma-coded dispatches after 2014 may reflect a change in how calls are typed, and the within-month slope is an average over two regimes (2006-2013: 1.0026; 2013-2026: 1.0019, so no difference appears).

## (e) Could the test have failed?

The test could have failed in either direction. The standard error of the log rate ratio is 0.0049. A true rate ratio of 0.97, the middle of the registered range, would have given z of about 6. Against the prediction the estimate is z = 6.7 from the midpoint (0.97) and z = 2.5 from the nearest edge (0.99). Against no effect it is z = 0.48. The claim is a confirmation test, not an endpoint or transfer test, so rules 7 and 8 do not apply.

Recommendation: keep. The registered conditions give unsettled and the reproduction is exact; the notes should say the bound applies to within-month variation at short lags, since the sign changes under other time controls.
