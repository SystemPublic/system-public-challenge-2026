# Referee report: retimed-taxi-fhv-pickups

Verdict recorded: unsettled. The referee re-ran the analysis from the zone-day counts in `data/derived/round2/retimed_consequences/taxi_cache`. Scratch code is outside the repository (session scratchpad, folder `referee-retimed-taxi-fhv-pickups`). I did not re-read the TLC parquet files, so the counts themselves are taken as given.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required two things: the interval of the slope above zero and the interval of the top-third minus bottom-third contrast below zero. The slope is 0.50 (0.13 to 0.81). The contrast is -0.011 (-0.034 to +0.015). The second condition fails. Refutation required the slope interval below zero or its upper bound below 0.3, and neither holds. Rule 2 gives unsettled. The exploratory split into business-district and other zones (`taxi_exploratory.py`, written at 23:53 after the results at 23:50) is labelled as unregistered and decides nothing.

The registration is dated 23:48:46 and was committed at 23:48:54 (e0b4eec). The branch `prereg/retimed-taxi-fhv-pickups` exists on the remote, with a commit at 23:48:56 holding only the registration file. The 2019 and 2026 counts were tabulated between 23:49:46 and 23:49:59, less than a minute after the push. The 2018 counts used for the design check were tabulated at 23:44, as disclosed. The outcome is dated 00:05:03.

The interval between push and tabulation is short, and `taxi.py` was last modified at 23:49. The two 2026 for-hire months, about 13 and 15 million trips, are recorded as remote column scans that finished 10 and 2 seconds after the local files. That is fast but possible for two columns, and the cache files carry the same times. I found nothing that shows the 2026 counts were seen earlier. The estimator and exposure files were not committed until 00:06:16.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error. My re-estimate is slope 0.5039 (0.1286 to 0.8083) and contrast -0.0111 (-0.0343 to +0.0150) on 147 zones, identical to the outcome. The retained weeks are right: seven in 2019 and six in 2026, with Presidents' Day weeks and the week of 23 February 2026 dropped (that Monday had 113,000 pickups against about 580,000 on other Mondays).

The uncertainty is understated. The bootstrap resamples seven and six weeks, and a percentile interval from so few weeks is too narrow. The registration says as much about the design check. The yellow-only placebo for 2018 against 2019 gave a slope of -0.30 (-0.63 to +0.01), which shows that a slope of this size with the wrong sign can arise between adjacent years with no change in work at home.

Robustness variants the registrant did not run:

- Leaving out one week at a time. The slope ranges from 0.47 to 0.58 and its interval stays above zero in all 13 cases. The contrast ranges from -0.005 to -0.020 and its interval includes zero in all 13. The verdict does not depend on any one week.
- Rank correlation. Spearman's rho between Y and E across the 147 zones is 0.11 (p = 0.17). The least-squares slope depends on a small number of zones with large thinning.
- Controls. With a business-district indicator the slope is 0.26 (standard error 0.15) and the indicator is -0.035 (0.011). With borough indicators the slope is 0.51 (0.13). The slope is therefore not only a borough difference, but about half of it is the business district against everything else, as the outcome says.
- Weekend placebo. The change in the weekend-to-midweek ratio of pickups has a slope of -0.79 on E (robust standard error 0.19). Zones where Monday and Friday entries thinned gained weekend pickups relative to midweek. Monday and Friday are not the only days that moved with E, so the registered ratio does not isolate office days.
- Three other bootstrap seeds give lower bounds for the slope of 0.11 to 0.13.

## (c) Is the comparison with the research fair?

No research figure is compared, and `graph_effect` is empty. I checked the nearest finding named in the registration, PMID 32253258, against its PubMed abstract. The abstract gives an odds ratio of 1.046 (1.032 to 1.060) for any injury crash per additional 100 rideshare trips originating in a taxi zone-hour, in New York City in 2017 and 2018. The registration quotes the number correctly but leaves out "per 100 trips". It treats rideshare trips as an exposure for crashes, not as an outcome of commuting, and the registration says so.

Outcome and exposure are on the same scale (change in the log Monday-and-Friday ratio), for the same zones. The periods differ: entries are 2019 against November 2025 to October 2026, pickups are two months of each year.

## (d) Alternative explanation not addressed

The two registered measures disagree and the outcome does not resolve why. A slope of 0.5 implies a contrast of -0.038 between thirds whose pooled E differs by 0.077. The observed contrast, -0.011, implies a slope of about 0.14. The exploratory split suggests the reason (a fall in the business district, a rise in residential zones that thinned more), but that reading was formed after the data. An unnamed alternative fits the same pattern: trips moved to the home end on days worked at home, so pickups in residential zones rose on Mondays and Fridays where commuting fell most. The registration's research question names it but no registered test separates it.

The baseline months are the first two months of high-volume for-hire reporting and of the congestion surcharge of February 2019. The registration lists the 2025 congestion charge but not the 2019 surcharge. Weather on the 13 sampled Mondays and Fridays is listed as an alternative and not examined.

## (e) Could the test have failed?

It could have been refuted: the registration put the chance of meeting the refutation condition at about half if the true slope were zero. It could not easily be confirmed, because the contrast had an expected standard error of 0.014 against a predicted -0.038 and the two conditions were both required.

For the slope, the estimate is 0.02 standard errors from the central prediction of 0.5 and 2.9 from no effect (standard error 0.174), so D = 8.4. For the contrast, the estimate is 2.1 standard errors from the predicted -0.038 and 0.9 from no effect (standard error 0.0128), so D = -3.7. On the contrast the data favour no effect over the prediction.

Recommendation: keep. Unsettled follows from the registered conditions and survives every variant; the notes should add that the contrast is 2.1 standard errors from its own prediction and that the rank correlation across zones is 0.11.
