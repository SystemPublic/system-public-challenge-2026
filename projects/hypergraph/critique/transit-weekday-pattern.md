# Referee report: transit-weekday-pattern

Verdict recorded: confirmed. The referee read the registration, the outcome, `analyses/transit/weekday_pattern.py`, `data/derived/transit/weekday_pattern.json` and the cached queries, and rebuilt the daily series from the cache in a scratch folder. The registrants' documents in `docs/` were not read.

## (a) Does the verdict follow from the registered conditions?

Yes. All three registered support conditions are met in the primary analysis. (a) The recent Monday/Friday deficit is 13.8% with a lower limit of 12.3%, Monday 16.4% and Friday 11.2%. (b) The recent midweek range is 2.77 points against a limit of 3. (c) The Delta is 8.7 points (6.9 to 10.9). The placebo (2019 minus 2018) is 0.74 points, inside the registered 1.5, so the registered penalty on condition (c) does not apply. No measure chosen after the data were seen enters the verdict.

The registration was committed at 20:17:29 on 12 November 2026 (commit b696a08), and the branch `prereg/transit-weekday-pattern` exists on GitHub with a tip committed at 20:17:36; the local reflog shows the branch on the remote by 20:27:03. The station table was fetched at 20:13:38, before registration, which the registration declares. The first ridership query was fetched at 20:19:01 and the last at 21:21:05. The outcome was decided at 21:22:20. The registration also declares four checks made before registering (metadata, one day's list of complexes with a row count in two datasets, and the minimum and maximum timestamp). These are not in the cache and cannot be verified; as described they contain no ridership sums.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error. Rebuilding from the cached hourly queries gives the same numbers: Delta 8.70 (6.90 to 10.86), recent deficit 13.82% (12.28 to 15.85), midweek range 2.77 (1.77 to 4.06), placebo 0.74 (-0.82 to 2.53), and 4.2 points for the rest of the system. The holiday rule, the week rule and the join on complex id work as registered. The complex-level sums match the area sums.

The estimator is a mean of weekly ratios, and it is sensitive to single disrupted days. On Monday 26 January and Monday 23 February 2026 CBD entries were 38% and 20% of the week's midweek mean. The outcome reports this and gives the median. I added a rule-based variant and three others:

| Variant | Recent deficit | Midweek range | Delta | 95% interval |
|---|---|---|---|---|
| Registered primary | 13.8 | 2.77 | 8.7 | 6.9 to 10.9 |
| Weeks with a day under 70% of the week's median day dropped (2 recent, 0 in 2019) | 12.6 | 2.19 | 7.4 | 6.4 to 8.5 |
| Ratio of period sums | 13.7 | 2.71 | 8.6 | |
| Weeks holding Good Friday, Rosh Hashanah or Yom Kippur dropped | 13.7 | 2.95 | 8.7 | 7.0 to 11.0 |
| September 2025 to August 2026 | 13.5 | 2.69 | 8.4 | 6.7 to 10.6 |

All three conditions are met in every variant. With the two disrupted weeks dropped, Monday is 13.6% and Friday 11.5%. The size is nearer 7.4 than 8.7 once the two storm Mondays are set aside, and the later transfer claim for Chicago took its band from 8.7.

Condition (b) is met with little margin. The bootstrap interval of the range runs to 4.06, and 68% of bootstrap resamples give a range of 3 points or less. The margin is larger under the outlier rule (2.19, interval 1.47 to 3.02) and smaller when religious-observance weeks are dropped (2.95).

## (c) Is the comparison with the research or the published figure fair?

There is no research estimate to compare with. The registration says so in `literature_gap`, and the graph side is empty (`graph_effect` is null and no finding is cited), so there is no finding to check against PubMed. The nearest published figure is the MTA's statement for fall 2022 that system-wide Thursday ridership was about 12.5% above Monday, which is system-wide, for another year, and read from a news report. The outcome does not score against it, which is right. Two literature entries are marked by the registrant as unverified (a search snippet for Motte-Baumvol et al. and secondary reports for the SWAA day-of-week shares), and they should not be quoted as findings.

## (d) Alternative explanation not addressed

The registered `edge` names hybrid work as the cause, and the test measures only the pattern. The outcome's `settle` field says this. Three things in the results bear on the cause and are not discussed as such. The rest of the system also changed, by 4.2 points (2.2 to 6.6), and outer-borough AM-peak entries by 9.4 points, so about half of the CBD change is a system-wide change that is not specific to the office district. The registrant predicted the largest change in the PM peak, when office workers enter CBD stations, and found it in the AM peak (15.2 against 12.5), which the office-worker account does not predict for entries inside the CBD. The MTA's reduction of Monday and Friday service from 2023 is named and not tested; the trajectory (10.4% in 2022, before the service change, and 14.1% in 2023) is compatible with a service effect of a few points and with continued change in work patterns, and the data here cannot separate them. The 2019 and 2025 datasets are also built from different fare media (MetroCard against OMNY with MetroCard), which the registrant names and which has no evident weekday dependence.

## (e) Could the test have failed?

Yes. The registrant put 0.6 on condition (b) and 0.45 on the whole, and (b) passes by 0.23 points. The claim is not an endpoint or transfer test, so there is no composed prediction; for reference, z of the Delta against no change is 8.6 and against the registered threshold of 4 points is 4.7, and against the middle of the registered range (7 points) it is 1.7. With the two disrupted weeks dropped, z against no change is 14.

Recommendation: keep. All three registered conditions are met, I reproduced every deciding number from the cache, and the verdict is the same under four variants the registrant did not run, although condition (b) passes narrowly and the outcome supports the pattern and not its attribution to hybrid work.
