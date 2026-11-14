# Referee report: further-zonej-demand-growth

Verdict recorded: contested. Recommendation: keep the verdict.

The referee read the registration, the outcome, `analyses/further/zonej_*.py`, `data/derived/further/zonej_*` and the PAL files in `~/opt/nyc-concordance/nyiso`. The registrant's write-ups in `docs/` were not read. The re-analysis is in the scratch folder `referee-further-zonej-demand-growth/reest.py`.

## (a) Does the verdict follow from the registered conditions?

Yes. The refutation condition is an upper 95 percent HAC limit of the energy trend below +0.5 percent a year. The primary model gives -0.752 percent a year (-0.837 to -0.666), so the condition is met and rule 1 of PRECEDENCE gives contested. No measure chosen after the data decided anything. The annual-level interval is labelled unregistered and is not used for the verdict.

The order of events is correct. The registration was committed at 20:23:09 on 12 November 2026 and the branch `prereg/further-zonej-demand-growth` exists on GitHub with a commit at 20:23:16 that contains only the registration file. The 132 PAL files were fetched from 20:23:26 to 20:23:59, the Central Park weather file at 20:23:55, LaGuardia at 20:25:01 and the Gold Book PDFs at 20:25:20. The results file was written at 20:25:04 and the outcome was decided at 20:26:45. The Power Trends PDF and a Gold Book index page were downloaded at 20:20 to 20:21, before registration, and the registration discloses both.

Two small departures from the plan do not affect the verdict. The registration says the Gold Book part is "reported as not done" with fewer than five readable editions at a three-year horizon; three editions apply and the outcome reports a mean and interval anyway. It scores neither bias condition as met, which is the same result as not done. The `last_modified_range` in the outcome's source record is the alphabetical minimum and maximum of date strings ("Fri, 01 Apr 2022" to "Wed, 04 Dec 2019") and is not a range of dates.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I reproduced the primary estimate exactly: -0.752 (-0.837 to -0.666), n = 3,521 days. Units and conversions are correct (tenths of a degree C to F, MW to MWh). Daily energy is computed as mean load times 24 hours, not as the registered sum of 5-minute load times 5/60. The two differ only on the two daylight-saving days a year and on days with missing intervals, and the difference is negligible.

The PAL series has no data for 1 to 24 April 2017 and 1 to 7 April 2021 (31 days). The outcome does not report this. Month effects absorb most of it and the leave-one-year-out range of the trend is -0.89 to -0.69.

The HAC interval with 14 lags is too narrow. The trend is identified by nine to eleven years, and residuals are correlated over much longer than two weeks. Variants not run by the registrant:

| Variant (Zone J energy trend, percent a year) | Estimate | 95% interval |
|---|---|---|
| Primary, HAC 14 lags (registered) | -0.752 | -0.837 to -0.666 |
| HAC 365 lags | -0.752 | -0.981 to -0.522 |
| Standard errors clustered by year | -0.752 | -1.027 to -0.475 |
| Bootstrap that resamples whole calendar years | -0.752 | -1.176 to -0.517 |
| Trend plus a step after 30 June 2021, HAC 60 lags | +0.031 | -0.222 to +0.285 |
| Step and separate slopes: 2015 to March 2020 | -0.186 | -0.497 to +0.126 |
| Step and separate slopes: July 2021 to 2025 | +0.36 | about -0.02 to +0.75 |

The realistic standard error is about 0.14, three times the registered one. The upper limit is still below +0.5 in every whole-period variant, so the verdict does not depend on the interval method.

The step model matters for interpretation. A single step of -5.7 percent (-7.1 to -4.2) across the excluded pandemic window accounts for the whole negative trend; with the step in the model the trend is +0.03 percent a year. The estimate of -0.75 is therefore a level shift divided by eleven years and not a steady decline. The outcome's settle text says this. The refutation condition is still met in the step model (upper limit +0.29), so the claim of growth above 0.5 percent a year over 2015 to 2025 fails under both readings.

The summer-peak trend is -0.78 (-0.94 to -0.63) with the registered errors and -0.78 (-1.13 to -0.43) clustered by year. The design-day peak series in the outcome is a straight line by construction, because the peak model has a linear trend and no year terms; it shows no information beyond the slope.

## (c) Is the comparison with the published statement fair?

Only in part. The NYISO Power Trends sentence is about the whole state system and about forecasts ("is increasing and becoming more uncertain"). The test is a backward-looking trend for Zone J alone over 2015 to 2025. A flat or falling Zone J history does not contradict a statewide forecast of growth driven by upstate large loads, and the registration lists this as an alternative. The verdict should be read as "the registered operational claim about Zone J was refuted", not as "NYISO's statement is wrong". Measured load is net of behind-the-meter solar, so it is also not the same quantity as end-use demand. No graph finding is cited (the registration records the lookup as pending), so there is no PubMed abstract to check.

## (d) Alternative explanation not addressed

Behind-the-meter solar is named and not corrected. Its growth lowers net load and summer peak over the period and could account for a few tenths of a percent a year, but not for a 5.7 percent step in 2020 to 2021. The larger unaddressed point is that the registered model cannot separate a lasting loss of commercial load after 2020 from a decline, because the window that contains the change is excluded and a straight line is drawn across it. The post-2021 slope is +0.36 percent a year in my step model and +0.56 in the registrant's S4; the interval of the first includes both zero and +0.5, so whether Zone J demand is growing now is open. Humidity is absent from the weather model, which matters for the peak more than for energy.

## (e) Could the test have failed?

Yes. The registrant's prior was 0.2 and the expected value was 0.0 with a range of -0.6 to +0.6. With the year-clustered standard error of 0.14, a true trend of zero gives an upper limit of about +0.28 and meets the refutation condition, and a true trend above about +0.8 would not. The test separates the registered threshold from the result: the estimate is 8.8 standard errors below +0.5 using the year-clustered error (28 using the registered error) and 5.3 below zero (17 with the registered error). Against the registrant's own expected value of 0.0 the estimate is 5.3 clustered standard errors low and lies outside the stated range, which the outcome reports.

Recommendation: keep. The refutation condition is met under every interval method and under a model with a pandemic level shift, although the registered interval is about three times too narrow and the result is a 2020 to 2021 step, not a steady decline.
