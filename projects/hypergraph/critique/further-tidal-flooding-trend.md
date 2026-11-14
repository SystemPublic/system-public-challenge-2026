# Referee report: further-tidal-flooding-trend

Verdict recorded: confirmed. Recommendation: keep the verdict.

The referee read the registration, the outcome, `analyses/round2_tidal/*.py` and `data/derived/round2/tidal_trend/*`. The registrant's write-ups in `docs/` were not read. The re-analysis is in the scratch folder `referee-further-tidal-flooding-trend/` (`tidal_reest.py`, `zip_loo.py`).

## (a) Does the verdict follow from the registered conditions?

Yes. Part 1 alone decides. The minimum-data rule is met (173 dry days at or above the knot, 2,042 complaints in the coastal set). The coastal rate ratio per 10 cm above the knot is 2.00 (1.64 to 2.38) and the coastal-over-other ratio is 1.74 (1.43 to 2.09); both lower limits are above 1.00. The shifted-tide placebos are 0.99 and 0.97 with intervals that include 1. Rule 1 of PRECEDENCE gives confirmed. No measure chosen after the data decided anything; the knot, the ZIP sets and the complaint patterns were fixed in the registration.

The order of events is correct. The Battery water levels and the rain data were read at 23:39 on 12 November 2026, before registration, and the registration discloses this and says what was looked at (aggregate counts of dry days above water levels, not counts by year). The registration was committed at 23:44:14 and the branch `prereg/further-tidal-flooding-trend` exists on GitHub with a commit at 23:44:15 that contains only the registration. The first 311 query for 2010 to 2019 was fetched at 00:04:34 on 13 November and the daily counts from 00:15 to 00:22. The analysis script was last changed at 00:13:55, before the daily counts arrived. The outcome was decided at 00:35:27.

One departure from the plan is reported and does not affect the result. The queries were run with `agency = 'DEP'` and in one-year pieces because the registered query timed out. The agency split shows that all 249,360 matching records in 2010 to 2019 belong to DEP.

The prediction score is fair. The estimate of 2.00 is at the top of the registered range of 1.10 to 2.0 and far from the registrant's centre of 1.3, and the other-ZIP estimate (1.15) misses its registered range of 0.95 to 1.10. Part 2a is scored partial as registered.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error. The datum is MHHW, the water level and the complaints are both in local time, the Sandy window is dropped, and the tidal-over-other ratio is the difference of two coefficients fitted on the same resampled days. I reproduced the primary result with an independent bootstrap: 2.00 (1.64 to 2.34), other ZIPs 1.15 (1.03 to 1.26), ratio 1.74 (1.46 to 2.05).

Variants not run by the registrant (coastal rate ratio per 10 cm above the knot, then the coastal-over-other ratio):

| Variant | Coastal | Ratio to other ZIPs |
|---|---|---|
| No rain of 1 mm or more on days t-2 and t-3 as well (975 days) | 1.99 (1.64 to 2.71) | 1.70 (1.35 to 2.40) |
| No rain of 1 mm or more on days t-2 to t-7 (237 days, 30 above the knot) | 2.54 (1.32 to 3.61) | 2.10 (1.27 to 3.78) |
| Controls for rain on days t-2 to t-7, snow depth and mean wind speed | 1.98 (1.72 to 2.22) | 1.72 (1.45 to 1.97) |
| No snow on the ground and none in 7 days | 1.97 (1.65 to 2.33) | 1.75 (1.47 to 2.10) |
| May to September | 1.95 (1.44 to 2.64) | 1.91 (1.53 to 2.32) |
| October to April | 1.91 (1.53 to 2.35) | 1.62 (1.30 to 1.98) |
| Days with mean wind below the median | 2.35 (1.66 to 3.01) | 2.12 (1.61 to 2.57) |
| Year-by-month fixed effects (Poisson, robust errors) | 1.77 (1.56 to 2.02) | about 1.58 |
| The 7 days at or above 0.563 m dropped | 2.15 (1.65 to 2.65) | 1.97 (1.63 to 2.44) |
| The 10 days with the most coastal complaints dropped | 1.82 (1.60 to 2.17) | 1.62 (1.38 to 1.94) |

The result does not depend on the dry-day definition, on season, on wind, on the highest water levels or on the busiest days. Several of the busiest "dry" days are 30 August to 2 September 2011, after Hurricane Irene, with 175 to 187 mm of rain in the previous week; removing them lowers the estimate to 1.82.

I split the water level into a part predictable from lunar and seasonal periods (a harmonic fit, R-squared 0.47, a rough stand-in for the astronomical tide) and the remainder (surge and sea-level anomaly). In a log-linear model over all dry days the coastal rate ratio per 10 cm is 1.083 (standard error 0.020) for the predictable part and 1.136 (0.022) for the remainder; in the other ZIPs they are 1.013 and 1.039. Complaints in the coastal set follow the predictable tide, which weather cannot cause. This is the strongest evidence against the weather rival and the registrant did not run it.

The effect is not uniform across the coastal set. By ZIP (Poisson, robust errors): 11691 2.26, 11692 2.50, 11693 2.52, 11694 2.01, 11224 1.61 (1.15 to 2.27), 11414 1.25 (0.98 to 1.59), 11231 1.10 (0.70 to 1.73). The Rockaway ZIPs carry the result. Howard Beach (11414) supplies 625 of the 2,042 complaints and shows a small rise, and Red Hook shows none. Without 11414 the estimate is 2.15. Among 80 other ZIPs with at least 150 complaints the median ZIP-level rate ratio is 1.08, the 95th percentile is 1.51, and two exceed 1.64 (10036, and 11422, which is in the registered broad coastal set).

## (c) Is the comparison with the research or the published figure fair?

Part 1 is compared with no research finding; the registration records that the graph holds none on water level and flood reports. Part 2a compares the slope of annual tide-day counts with the slope implied by the long-term Battery trend of 2.95 mm a year. The comparison is on the same scale (days per year per year) and the outcome notes that the gauge's own 2010 to 2025 slope is about 4.0 mm a year, so the long-term figure is not the right one for this window.

The outcome cites no graph evidence, but the commit adds `graph_flood_findings.json` with flood and health findings. I checked one against PubMed. PMID 28129752 (Waite et al. 2017, BMC Public Health) reports an adjusted odds ratio for probable PTSD among flooded participants of 7.19 (4.33 to 11.93), which matches the stored record exactly. The same file lists trials of prolonged exposure therapy (PMIDs 29344631, 32758312, 24368465) under "flooding -> post-traumatic stress disorder". "Flooding" there is the name of a psychotherapy technique. Those records do not concern floods and should not be counted as flood evidence anywhere they are used.

## (d) Alternative explanation not addressed

The Battery is used for water in Jamaica Bay and on the Rockaway shore; the registrant names this and it would bias the estimate toward 1. Rain at places other than the two gauges remains possible, but the predictable-tide result and the calm-day result make weather an unlikely explanation of the whole effect. Two points are not addressed. First, the other-ZIP series also rises (1.15, and 1.27 in the highest band), so some common factor moves complaints citywide on high-water days; the ratio of 1.74 removes it only if that factor acts equally in both sets. Second, the hinge shape is wrong: the band model shows complaints already raised at 0.30 to 0.35 m, the log-linear slope over all dry days is 1.11 per 10 cm, and the hinge estimate grows with the knot (1.73, 2.00, 2.38, 2.88). The figure "2.00 per 10 cm" depends on the knot and should not be quoted as a general dose-response. The direction and the coastal specificity do not depend on it.

## (e) Could the test have failed?

Yes. The registrant's simulations gave a little over half a chance of meeting the refutation condition if the true ratio were 1.00, and the prior was 0.35. The bootstrap standard error of the log rate ratio is 0.095, inside the registered 0.09 to 0.15. The estimate is 7.3 standard errors from no effect (z = 0.693 / 0.095) and 4.5 standard errors above the registrant's centre of 1.3 (z = (0.693 - 0.262) / 0.095); it is at the upper edge of the registered range. The claim was confirmed in direction with a size the registrant did not expect. For part 2a the slope of 0.63 days per year per year (standard error 0.38) is 0.2 standard errors from the implied 0.55 and 1.6 from zero, so it cannot tell the implied rate from no trend, as the registration said in advance.

Recommendation: keep. The support conditions are met, the result survives stricter dry-day rules, wind, season and influence checks, and the complaints follow the predictable part of the tide, although the size depends on the knot and the effect is concentrated in the Rockaway ZIP codes.
