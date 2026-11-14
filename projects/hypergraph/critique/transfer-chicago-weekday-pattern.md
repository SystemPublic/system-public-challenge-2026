# Referee report: transfer-chicago-weekday-pattern

Verdict recorded: contested (the size of the New York result does not transfer). The referee read the registration, the outcome, `analyses/transfer/chicago_weekday.py`, `analyses/transit/weekday_pattern.py`, the derived data in `data/derived/graph/transfer_chicago/` and the cached queries, and re-ran the analysis in a scratch folder. The registrants' documents in `docs/` were not read.

## (a) Does the verdict follow from the registered conditions?

Yes, under precedence rule 1. The registered refutation condition is a Loop Delta above 13.1 points, and the registered primary gives 15.9 (12.0 to 22.7). The data ended on 31 August 2026, so the recent period is the registered fallback, September 2025 to August 2026. The registrant found that one week of the 2019 baseline accounts for the excess over 13.1, reported the estimate without it (12.9) as exploratory, and did not let it decide the verdict. That is the correct use of rule 4.

The registration was committed at 22:32:30 on 12 November 2026 (commit 4bf91ba), and the branch `prereg/transfer-chicago-weekday-pattern` exists on GitHub with a tip committed at 22:32:33. The station table was fetched at 22:34:12 and the ridership at 22:34:24 to 22:34:28. The outcome was decided at 22:54:41. The registration declares that station names and coordinates had been read before registering in order to fix the Loop box; that read is not in the cache, and it contained no ridership. The time of the push cannot be read from the local clone. The script has a modification time of 22:34, after the registration commit, and was first committed with the outcome, so its content at run time cannot be checked against a commit made before the data.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I reproduced the primary exactly: Delta 15.92 (12.0 to 22.7), recent Monday/Friday deficit 18.2%, 2019 deficit 2.3%. I found one error in an interval, one undocumented change in the station set, and a weakness in the estimator.

The estimator is a mean over weeks of a ratio whose denominator is the week's Tuesday to Thursday mean. In the week of 28 January 2019 Loop entries on Wednesday and Thursday were 27% and 73% of that mean, so Monday and Friday score 227% and 213% and the week's Monday/Friday deficit is -120%. The other 41 weeks of 2019 lie between -2% and +10%. This one week moves the 2019 mean from 5.3% to 2.3% and the Delta from 12.9 to 15.9. The standard deviation of the weekly values is 19.4 points in 2019 against 3.6 in the recent period and 3.2 in 2018, and the upper limit of 22.7 is produced by resamples that draw this week several times.

Estimates under variants, with the registered ones marked:

| Variant | Loop Delta, points | 95% interval | Against 13.1 |
|---|---|---|---|
| Registered primary | 15.9 | 12.0 to 22.7 | above |
| Registered S1, median over weeks | 13.5 | 12.4 to 15.2 | above |
| Registered S2, days only | 13.6 | | above |
| Ratio of period sums in place of mean of weekly ratios (mine) | 14.1 | 11.9 to 17.2 | above |
| Weeks with a day under 70% of the week's median day dropped, both periods (mine) | 12.9 | 11.6 to 14.2 | below |
| Same rule, State/Lake station excluded (mine) | 13.2 | 11.8 to 14.4 | above |
| Baseline 2018 in place of 2019 (mine) | 12.4 | 10.9 to 13.8 | below |
| Baseline 2018 and 2019 pooled (mine) | 14.2 | 11.7 to 17.9 | above |

The estimates run from 12.4 to 16.1 and the threshold of 13.1 lies inside that range. The label contested, as against unsettled, therefore depends on how one week is treated.

State/Lake (station 40260), one of the 15 Loop stations and the fourth busiest in 2019, has no entries on 234 days of the recent period. The outcome says "15 Loop stations" for both periods. Excluding it from both periods changes the Delta by 0.2 points, so the effect is small, but the outcome should state it.

The interval for the Loop minus rest-of-system difference, -1.1 to 15.7, is wrong. The script draws separate bootstrap samples of weeks for the Loop and for the rest of the system, although both are observed in the same weeks and the January 2019 week affects both. Resampling the same weeks for both gives 7.1 (6.2 to 8.0). The registered secondary prediction that the Loop rose more than the rest of the system is therefore clearly met, and the outcome understates it.

## (c) Is the comparison with New York fair?

Partly. The definitions are the same. Three things differ. The periods differ by two months (New York November to October, Chicago September to August). New York on Chicago's period gives 8.4 (6.7 to 10.6), so this matters little. The New York figure of 8.7 that sets the band is itself raised by two disrupted Mondays (26 January and 23 February 2026); with the same outlier rule applied to both cities and the same period, New York is 7.1 (6.1 to 8.2) and the Loop 12.9 (11.6 to 14.2), a ratio of 1.8, which is outside 50% of New York's value. On that like-for-like basis the result still does not transfer in size. The areas are the third difference. The Loop box holds 15 stations in an office core, while the New York CBD is 65 complexes south of 60th Street, including residential districts. New York's registered office-core check (25 complexes within 1.2 km of Grand Central or Wall Street) gives 10.6 (8.7 to 12.8), or 9.3 (8.2 to 10.3) with the outlier rule. Against that core the Loop's 12.9 is 1.4 times as large, inside 50% and outside 25%, which the registration would call partial transfer. The claim has no graph evidence, so there is no finding to check against PubMed.

## (d) Alternative explanation not addressed

The registrant named the lower level of recovery in the Loop (entries at 57% of 2019 against 75% in the New York CBD). It is not tested, and it is the simplest account of a larger Delta: if non-office trips are spread evenly over the week and office trips fell more in Chicago, the ratio moves further without any difference in which days people work at home. The Friday deficit in the Loop (20.1%) exceeds the Monday deficit (16.4%), the reverse of New York, which points to a difference in composition or schedules. Metra commuters who transfer to the 'L' are a possible source. The area mismatch described under (c) is a second alternative that is not named.

## (e) Could the test have failed?

Yes, and it did by the registered rule; the prior was 0.4. With the registered intervals, z against the prediction (New York's 8.7) is 2.5 and z against no change is 5.9. With the disrupted weeks dropped in both cities the standard errors fall from 2.7 to 0.7 points for Chicago, and z against New York's 7.4 is 6.5 and against no change about 20. The test separates no change from change, and Chicago from New York. It does not separate 12.9 from 13.1.

Recommendation: keep. The registered refutation condition is met by the registered primary, and a like-for-like comparison with disrupted weeks removed in both cities still puts the Loop at 1.8 times the New York CBD, although the fixed 13.1 threshold is not robustly exceeded (12.4 to 16.1 across variants) and the Loop minus rest interval should be corrected to 6.2 to 8.0.
