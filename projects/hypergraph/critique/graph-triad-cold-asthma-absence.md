# Referee report: graph-triad-cold-asthma-absence

Verdict recorded: confirmed. The referee did not register this claim and did not read the registrant's write-ups. Scratch code is in the session scratchpad under `referee-graph-triad-cold-asthma-absence/` (`ref_absence.py`, `flu.py`).

## (a) Does the verdict follow from the registered conditions?

The verdict follows from the registration's own support condition and conflicts with rule 8. The support condition was a ratio above 1 with a Newey-West interval that excludes 1. The ratio is 1.101 (1.053 to 1.152), so rule 1 gives confirmed. The claim is registered as kind `bridge`, with a chain, a composed prediction (1.0073, interval 1.0008 to 1.0173) and a discrimination check that the registration itself reports as failed (expected D = 0.23). Rule 8 was committed at 16:18:10 on 12 November (55446b6), more than six hours before this registration, and says that an endpoint test with D below 4 is unsettled however well the endpoint matches. With the observed numbers, z against the composed prediction is 3.81, z against no effect is 4.19, and D = 3.0, which is still below 4. The support condition was written as a test of direction only, which a bridge registered after rule 8 was not free to do. The recorded stance (0.97) is the stance of a direct effect against its null. The rule 7 and 8 stance for the chain is about -0.78, because the endpoint lies 3.8 standard errors above what the chain predicts.

No measure chosen after the data decides the verdict. The timing is in order. The registration is stamped 22:51:37 and was committed at 22:51:43 (3c393f8). The branch `prereg/graph-triad-cold-asthma-absence` exists on GitHub at c6ab903, committed 22:51:47. The first contact with the attendance datasets is a two-row sample of each at 22:51:54 to 22:52:32, the grouped queries were fetched at 22:53:04 to 22:56:15, and the outcome is stamped 22:58:13. The weather file was fetched at 20:23:55 and its use before registration is disclosed. `test_absence.py` has a file time of 22:54 and was first committed with the outcome, so git does not show that it was fixed before the data. Its last edit falls between a failed query on the 2015-2018 file (counts stored as text) and the successful one at 22:56, when no estimate could yet have been computed. The model in the script matches the registered plan.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I rebuilt the daily series from the cached Socrata responses and the cached Central Park file with my own code and reproduce the estimate exactly: 1.1012 (1.0526 to 1.1521), 587 school days, 98 exposed. The five files do not overlap in dates, the two date formats are parsed correctly, and absent plus present equals enrolled to within 6% on every kept day.

Three small departures from the plan do not change the result. The snow indicator uses the previous kept school day and not the previous calendar day, so snow on a Sunday is not carried to Monday (corrected: 1.100). The lag 0 to 2 secondary exposure has the same defect. The exclusion of days with absence above 30% removes the most extreme days, which are disproportionately cold or snowy, and this works against the claim. Of the 145 cold-season weekdays with TMAX at or below 0 C, 118 have attendance records and 98 are kept.

The Newey-West interval is somewhat narrow. Exposed days are unevenly spread over years (1 in 2011-12, 15 in 2013-14).

| Variant | Ratio | 95% interval |
|---|---|---|
| Registered | 1.101 | 1.053 to 1.152 |
| Standard errors clustered by school year (13 clusters) | 1.101 | 1.039 to 1.167 |
| School year by week fixed effects | 1.096 | 1.040 to 1.155 |
| School year by month fixed effects | 1.090 | 1.041 to 1.142 |
| Snowfall in the previous 3 calendar days and snow on the ground added | 1.099 | 1.047 to 1.155 |
| Days with no recent snowfall and no snow on the ground (34 exposed) | 1.176 | 1.098 to 1.259 |
| Days within 3 school days of a recess dropped (62 exposed) | 1.128 | 1.063 to 1.196 |
| Five highest-absence exposed days dropped | 1.070 | 1.027 to 1.114 |
| Median regression | 1.089 | 1.064 to 1.114 |
| 2009-10 onward, registered model (71 exposed) | 1.071 | 1.016 to 1.129 |
| 2009-10 onward, with log weekly laboratory-confirmed influenza, this week and the previous week | 1.070 | 1.015 to 1.127 |
| 2009-10 onward, influenza, snow on ground, recent snowfall and near-recess indicator | 1.061 | 1.000 to 1.127 |
| Placebo: TMAX at or below 0 C two days later, adjusting for today | 1.009 | 0.968 to 1.051 |
| Leave one school year out (range of 13) | 1.086 to 1.116 | |

The influenza series is the New York State count of laboratory-confirmed cases by county and week (health.data.ny.gov `jr8b-6gh6`, rows updated 29 May 2026, fetched 13 November 01:03:55), summed over the five city counties. It begins in October 2009, so the control is available for 450 of the 587 days. The city's influenza-like-illness visit series is not on the open data portal for these years. Adding influenza moves the estimate from 1.071 to 1.070. Fixed effects for each week of each school year, which absorb any weekly epidemic curve, give 1.096. Holidays next to cold spells do not explain the result either: 36 of the 98 exposed days are within three school days of a recess, and dropping all such days raises the estimate. Absence rises in steps with cold: against days with TMAX of 5 to 10 C, the ratio is 1.06 at 0 to 5 C, 1.11 at -5 to 0 C and 1.34 at or below -5 C (14 days).

The association between cold days and absence is therefore robust in direction. Its size depends on a few extreme days, including 7 January 2014 (absence 25.6%, TMAX -7.1 C). A defensible range is 1.06 to 1.10.

## (c) Is the comparison with the research fair?

The comparison is not like for like, and the outcome says so in part. I checked PMID 35817164 against PubMed. The abstract gives RR 1.64 (1.06 to 2.54) for cold at the 5th percentile of temperature on days with lower PM2.5, in Hefei in 2013 to 2016. The outcome is childhood asthma hospitalisation, the exposure comes from a distributed-lag model and is cumulative over lags, and the same abstract gives 2.16 (1.38 to 3.38) on days with higher PM2.5. The registrant used the lower stratum, which is the cautious choice. The city exposure is a same-day indicator of TMAX at or below 0 C, which holds on 17% of kept winter days and is not a 5th percentile. The outcome is absence from all causes. The second link (PMID 11487757) is confirmed by its abstract: 92 children with asthma in Rochester, Minnesota had 2.21 (1.41 to 3.01) more days absent. The composition assumes that asthma absences scale with asthma hospitalisations, and it rests on the registrant's assumed prevalence and mean days absent, as disclosed. The composed size (0.7%) and the city estimate (10%) are on the same scale and differ by a factor of about 13.

## (d) Alternative explanation not addressed

Influenza was the rival the registrant named and left uncontrolled. The controls above do not support it. The alternative that remains is a direct effect of cold on attendance that has nothing to do with health: travel on foot and by bus in severe cold, parents keeping children at home, and ice or snow on the ground. The dose-response pattern and the larger estimate on days without snow fit this. The data cannot separate it from short-latency illness of any kind, since absence is not recorded by reason. Asthma is at most a small part: the chain accounts for about 8% of the log ratio.

## (e) Could the test have failed?

The test of direction could have failed. With a standard error of 0.023 on the log scale, a true ratio of 1.00 would have given unsettled with probability 0.95, and the refutation condition was reachable. The observed z against no effect is 4.19 (3.25 with clustering by school year). The test of the triad could not have failed. The composed ratio of 1.0073 could not be told from 1 (expected D = 0.23), and any positive association from any cause satisfies the support condition. The observed z against the composed prediction is 3.81, so the endpoint rejects the chain's size while agreeing with its sign.

Recommendation: change the verdict to unsettled, because the claim is a bridge registered after rule 8 and its endpoint test does not discriminate (D = 3.0, below 4); the cold-day association of 1.06 to 1.10 survives the influenza, snow and recess controls and should be registered as a direct claim that does not name asthma.
