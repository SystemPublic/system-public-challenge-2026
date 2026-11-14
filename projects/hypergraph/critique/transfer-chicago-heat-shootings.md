# Referee report: transfer-chicago-heat-shootings

Verdict recorded: confirmed (the New York result transfers). The referee read the registration, the outcome, `analyses/transfer/chicago_heat.py`, `analyses/heat/shootings.py`, the derived data in `data/derived/graph/transfer_chicago/` and the cached queries, and re-ran the model in a scratch folder. The registrants' documents in `docs/` were not read.

## (a) Does the verdict follow from the registered conditions?

Yes. The registered support condition is a Chicago IRR per 5 C between 1.110 and 1.183 with a lower 95% limit above 1.00. The primary estimate is 1.131 (1.120 to 1.143). No measure chosen after the data were seen enters the verdict. Midway TMAX is missing on 2 of 6,087 days, so the registered fallback to O'Hare was not triggered.

The registration was committed at 22:32:30 on 12 November 2026 (commit 0166e87), and the branch `prereg/transfer-chicago-heat-shootings` exists on GitHub with a tip committed at 22:32:31. The first Chicago query was fetched at 22:33:08, the weather files at 22:33:29 and 22:33:30, and the outcome was decided at 22:54:41. The order is correct, with a margin of 38 seconds between the commit and the first fetch. The time of the push cannot be read from the local clone, so the record shows that the registration was committed before the data, not that it was public before the data. The analysis script has a modification time of 22:32 and was first committed with the outcome at 22:55:42, so its content at run time cannot be checked against a commit made before the data.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error. I rebuilt the daily series from the cached queries and it matches the derived file on every day: 6,085 days, 41,063 cases, 75 days with no case. Annual totals run from 1,865 (2013) to 3,551 (2016) and 3,550 (2021), which is the known course of Chicago shootings; 2026 has 81 to 154 cases per month through August, so the tail is complete. TMAX and PRCP are converted from tenths. My refit gives the same primary estimate, 1.1314 (1.1201 to 1.1427).

Variants the registrant did not run:

| Variant | IRR per 5 C | 95% interval |
|---|---|---|
| Primary, HAC errors, 7 lags | 1.131 | 1.119 to 1.144 |
| Primary, HAC errors, 28 lags | 1.131 | 1.118 to 1.145 |
| Year-by-month fixed effects, HAC 7 lags | 1.125 | 1.113 to 1.136 |
| Poisson, year-by-month fixed effects | 1.124 | 1.113 to 1.136 |
| Without 2020 and 2021 | 1.135 | 1.123 to 1.147 |
| No month terms | 1.129 | 1.124 to 1.135 |

Every variant stays inside the transfer band. Serial correlation widens the interval by about a tenth. Of the registered sensitivity checks, only May to September (1.105) falls outside the band, into the range the registration calls partial transfer.

The New York figure in the registration covers 2006 to 2026 and the Chicago figure 2010 to 2026. New York refitted from 2010 gives 1.151 (1.132 to 1.170), so the period difference does not change the comparison.

## (c) Is the comparison with the research fair?

The city-to-city comparison is fair: the same model, the same exposure (airport or park TMAX at lag 0), and an outcome unit chosen to match (distinct case against distinct incident). The comparison with the graph is fair in direction only. The outcome's `graph_effect` is Xu et al. 2020, which is intentional homicide against daily mean temperature over lags 0 to 7, in a case-crossover design. I checked it against the PubMed abstract (PMID 32738768): the abstract gives increases of 9.5% (4.3 to 15.0) for Chicago and 8.8% (1.5 to 16.6) for New York per 5 C, as the outcome says, and the outcome is right that a stored odds ratio of 0.095 is a percent change mis-scaled. The nearer city figure for that comparison is the registered check S7, gunshot homicides, 1.115 (1.091 to 1.139), which agrees with Xu's 1.095 (1.043 to 1.150). The Lyons et al. figure (RR 1.17 at the 84th percentile against the median, PMID 36525273) also matches its abstract, and it is on a different scale from an IRR per 5 C.

## (d) Alternative explanation not addressed

The claim compares one linear slope per city, and the two cities have different shapes. A slope fitted separately below and above 20 C gives, for Chicago, 1.148 (1.133 to 1.164) below and 1.104 (1.084 to 1.124) above, and for New York from 2010, 1.137 (1.112 to 1.164) below and 1.174 (1.139 to 1.210) above. Chicago's response flattens on hot days and New York's steepens. The two average slopes agree in part because Chicago has more cold days (TMAX standard deviation 11.7 C against 10.0 C), where its slope is steeper. The registered check S3 (May to September, 1.105) shows the same thing. The verdict concerns the average slope and is correct for it, but "the New York result transfers" should not be read as transfer of the dose-response shape. The repository has a later registration, transfer-chicago-hot-end, which appears to address this. Recording by police rather than by hospitals is named by the registrant and remains untested.

## (e) Could the test have failed?

Yes. The band of 1.110 to 1.183 is about 6 standard errors of the Chicago estimate wide on each side of New York's value, and the estimate lies 3.7 standard errors above the lower edge. Against the prediction (New York's 1.146) z is -1.45 when New York's own uncertainty is included and -2.55 when New York's value is treated as fixed. Against no effect z is 24.2. The test therefore separates transfer from no effect, and from an effect half or one and a half times New York's. The registrant's prior was 0.6.

Recommendation: keep. The registered condition is met by the registered primary estimate, which I reproduced exactly and which stays in the band under six further specifications.
