# Referee report: further-containers-rats-cd9

Verdict recorded: unsettled. Recommendation: keep the verdict.

Scratch work is in the session scratchpad under `referee-further-containers-rats-cd9/` (`reest.py`, `var.py`). It uses `data/derived/further/cd_monthly_311.csv` and `dohmh_initial_monthly.csv`, and one new query to erm2-nwe9 made on 13 November at 00:54 (rat sightings and distinct addresses by month in districts 7, 9, 10, 11 and 12).

## (a) Does the verdict follow from the registered conditions?

Yes. Support needed the upper bound of the rate ratio below 1.00; it is 1.23. Refutation, evaluated only when support fails, needed the lower bound above 0.90; it is 0.86. Neither is met, and the verdict is unsettled under rule 2. The placebo-year interval (0.89 to 1.36) includes 1, and the DOHMH odds ratio is above 1, so condition (c) fails as well. Nothing was decided by a measure chosen after the data.

The registration was committed at 20:24:13 on 12 November, and the branch `prereg/further-containers-rats-cd9` exists on GitHub with a commit at 20:24:19 that holds the same file. The 311 queries were fetched at 20:24:58 and 20:25:11 and the DOHMH query at 20:25:34. The outcome was decided at 20:26:12. The stored hash of the registration matches its content. The first query came 39 seconds after the branch commit, so the order is right but the margin is small, and the time of the push cannot be read from the repository. The analysis script was first committed with the outcome. I read it against the plan.

One registered item is missing. The plan says a quasi-Poisson GLM with district and period effects "is reported as a check". The script does not fit it, and neither `results.json` nor the outcome reports it. The registered event study by quarter is saved as a monthly series only. Neither omission bears on the verdict.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I reproduced the deciding number exactly: R = 1.018 (0.861 to 1.234), from 380 and 492 sightings in CD9 and 2,439 and 3,214 in the comparison districts. The new query returns the same four counts. The district codes are read correctly ('09 MANHATTAN'; the Bronx row and the unspecified rows are excluded). The DOHMH figures also reproduce: active signs in 747 of 4,893 initial inspections before and 723 of 4,900 after in CD9, odds ratio 1.095.

The interval is too narrow. The month-pair bootstrap treats the district totals as fixed apart from which months are drawn, and its standard deviation on the log scale is 0.093. I computed the same rate ratio for each of the other eleven Manhattan districts against the rest (excluding CD9), over the same windows. No containers were installed in them, and their ratios run from 0.77 (CD12) to 1.56 (CD3), with a standard deviation of 0.196 on the log scale. District-level noise from year to year is about twice what the bootstrap reports. CD9's ratio against all other Manhattan districts (0.95) ranks fourth lowest of twelve. With that spread, an interval for CD9 is roughly 0.69 to 1.49.

Other variants:

| Variant | R | 95% interval |
|---|---|---|
| Registered primary | 1.018 | 0.861 to 1.234 |
| Quasi-Poisson, district and month effects (the registered check, dispersion 2.0) | 1.018 | 0.832 to 1.245 |
| Quasi-Poisson, district and one period effect (dispersion 6.5) | 1.018 | 0.704 to 1.470 |
| Distinct addresses in place of calls (new query) | 1.111 | 0.953 to 1.293 |
| Monthly log ratio, June 2022 to May 2026, calendar-month terms | 1.078 | 0.990 to 1.174 |
| The same with a linear trend | 0.924 | 0.798 to 1.070 |

The count of distinct addresses removes repeat calls about the same building. On that measure CD9 fell 16 percent (370 to 309) and the comparison districts 25 percent (2,582 to 1,941). Its lower bound is above 0.90, so the registered refutation condition would be met on that measure. It was not the registered outcome and does not decide.

The pre-period is not flat. CD9's sightings as a share of the comparison districts' were 0.133, 0.144, 0.153 and 0.156 in the four June-to-May years from 2022. The share rose each year before the bins and rose less in the post year. A model with a linear trend reads that as a relative fall of 8 percent, and a model without it reads a rise of 8 percent. The outcome mentions the non-parallel pre-trend but does not show how much the answer depends on it.

In the DOHMH data, initial inspections in CD12 fell from 3,707 to 2,126 while CD9's were flat. Inspection effort moved, so the comparison share is not a stable reference. The outcome says this.

## (c) Is the comparison with the research or the published figure fair?

There is no published figure for CD9. The DSNY release gives citywide counts for December to November years, and the Mayor's release says sightings dropped without a number or a district. The claim tests the direction of the city's causal sentence at district level with the city's own measure, which is fair. The predicted range of 0.75 to 0.95 is the registrant's own and not a published effect. There is no graph evidence (the lookup is recorded as pending), so there was no finding to check against PubMed. Walsh 2014 and Murray 2018 are cited from abstracts read through search summaries, and the registration says so.

## (d) Alternative explanation not addressed

The registration names regression to the mean and differential reporting. Two things are not addressed. First, the bins were installed during April and May 2025, inside the pre-period, and the first two months of service (June and July 2025, 59 and 57 sightings) were the highest of the post year. Installation work and publicity may have changed who called at the boundary of the two windows. The pre-period also contains one unusual month: July 2024 had 86 sightings in CD9, against 31 and 37 in the months on either side, which is 17 percent of the pre-period total. Without the July pair the ratio is 1.06. Second, the on-street bins serve the larger residential buildings on the streets where they stand, and district boundaries stand in for the treated area. A district-wide ratio near 1 is compatible with a real fall on treated blocks. The outcome lists the bin locations under research needed.

## (e) Could the test have failed?

Refutation was possible: it needed a ratio above about 1.06. Support was possible only for ratios below about 0.83, so most of the predicted range (0.83 to 0.95) could not have been confirmed. If the true ratio were 0.85, the chance of meeting condition (a) was about 0.4 with the bootstrap interval, before the placebo and DOHMH conditions. With the spread across districts found in (b), support would have needed a ratio below about 0.68.

This is not an endpoint or transfer test, but for reference: against no effect z is 0.19 with the bootstrap standard deviation; against the middle of the predicted range (0.85) z is 1.94, and against its upper edge (0.95) it is 0.74. With the spread across placebo districts these are 0.09, 0.92 and 0.35. The data do not separate the prediction from no effect.

Recommendation: keep. The registered conditions return unsettled, the estimate reproduces exactly, and the variants run from 0.92 to 1.11 depending on the treatment of the pre-trend and of repeat calls.
