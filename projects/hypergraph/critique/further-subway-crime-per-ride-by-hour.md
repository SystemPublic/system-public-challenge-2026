# Referee report: further-subway-crime-per-ride-by-hour

Verdict recorded: unsettled. Recommendation: keep the verdict.

Scratch work is in `referee-further-subway-crime-per-ride-by-hour/` in the session scratchpad (`hour.py`, `v21.py`). It reads `data/derived/further_subway/raw.json`; the comparison of ridership tables uses the xfre-bxip query made for the companion report.

## (a) Does the verdict follow from the registered conditions?

Yes. Support needed three things: A at least 3.0 with a lower bound of at least 2.0, a lower bound of G[0-5] above 1, and B at least 1.10. I recomputed all three from the cached aggregates and they equal the registrant's: A is 15.0 (13.3 to 17.0), G[0-5] is 0.965 (0.861 to 1.082) and B is 0.90 (0.79 to 1.02). The first condition is met and the other two are not. Refutation needed an upper bound of A below 3.0 or an upper bound of G[0-5] below 1. Neither holds. The rule gives unsettled.

Nothing was decided by a measure chosen after the data were seen. The registration was committed at 20:28:09 on 12 November 2026 and the branch `prereg/further-subway-crime-per-ride-by-hour` exists on the remote with a commit at 20:28:15. The first complaint query is at 20:28:39, the ridership queries run from 20:29:45 to 21:13:44, and the outcome is dated 21:15:55. The analysis script was created at 20:48:48, after the complaint aggregates were cached and before the 2025 and 2026 ridership needed for any rate was fetched (21:11 and 21:13). The bands, periods, numerator and interval methods in the script are those in the registration.

The outcome reports the six registered sensitivity checks. S5 (calendar 2025) gives G[0-5] of 1.06 (0.95 to 1.19), on the other side of 1 from the primary reading, and S4 (violent types) gives 1.12 (0.93 to 1.36). Neither meets a condition, and the outcome does not lean on either.

## (b) Errors in code, units, joins, dates or uncertainty

I found no error that changes a number. Hours are taken from the first two characters of the complaint time and no complaint lacks a time. The ridership hour is the hour beginning, as registered. The year totals of the hourly tables agree with the MTA monthly subway ridership table to 0.15% in 2019 and are 1.3% above it in January to November 2025. That drift lowers G by about 1.4% and is small against the interval.

The exact binomial interval for G treats months as exchangeable Poisson counts. The 2019 monthly counts in the 0-5 band are overdispersed (Pearson dispersion 2.6 over 12 months; 43 to 76 complaints a month), and the latest 12 months are not (0.66). A bootstrap over months gives G[0-5] of 0.967 (0.849 to 1.098), a little wider than the registered interval. The verdict is the same.

Robustness variants the registrant did not run:

| Variant | G[0-5] or equivalent | Note |
|---|---|---|
| Hours 1 to 4 only (hour 0 dropped, since midnight attracts default times) | 0.94 (0.83 to 1.06) | A rises to 20.4 |
| January to September 2026 against the same months of 2019 | 1.00 (0.87 to 1.14) | 2026 file only |
| October to December 2025 against the same months of 2019 | 0.88 (0.70 to 1.11) | historic file only |
| Month bootstrap | 0.97 (0.85 to 1.10) | allows overdispersion |
| Robbery alone, 0-5 | 0.73 (0.55 to 0.95) | 89 against 146 |
| Felony assault alone, 0-5 | 1.95 (1.44 to 2.64) | 119 against 73 |
| Grand larceny alone, 0-5 | 0.88 (0.77 to 1.02) | 339 against 458 |

No variant of the registered quantity moves the verdict. The by-type rows show what the pooled figure hides, and I return to them under (d).

The complaint counts for the last quarter (July to September 2026: 159, 152, 176) are in line with earlier months, so late reporting has not visibly thinned the newest data.

## (c) Is the comparison with the published figure fair?

Only in part. The statement ends "so the State's all-day fall in crime per rider does not describe the late-night hours". The State's fall is measured from 2021. The registered test measures the late-night rate from 2019. These are different baselines, and the outcome's sentence about "the State's all-day fall" needs that qualification.

On the State's own baseline the answer is different from the one on the 2019 baseline. Using calendar 2025 against 2021 with the same numerator and denominator, the all-day rate per million entries fell from 2.35 to 1.64, a ratio of 0.70 (0.66 to 0.75), which is the State's 30 percent. The 0-5 rate fell from 24.2 to 19.5, a ratio of 0.81 (0.71 to 0.92), and the rate for hours 5 to 24 fell by 0.65 (0.61 to 0.70). The late-night fall since 2021 is therefore smaller than the daytime fall, about 19 percent against 35 percent. Against 2019 the late-night rate is level and the all-day rate is 8 percent up. Both statements are true together because the late-night rate rose less than the daytime rate between 2019 and 2021 as a ratio. This comparison is mine and was made after the data were seen; it decides nothing, and it is the natural second registration.

The first condition (A at least 3) compares rates per fare entry across hours. A was already 16.1 in 2019, so its size says nothing about the period after 2020, and with 2.4% of entries and 26% of complaints in the band it reflects the denominator as much as risk. The outcome says this in its limits.

The claim has no graph evidence (the lookup was pending and `graph_effect` is null), so there is no finding to check against PubMed. The Smith and Clarke review is cited from memory and the Citizens Budget Commission survey from news summaries; neither supplies a number that the test uses.

## (d) Alternative explanations not addressed

The offence-mix alternative was registered and answered only by S4, which pools the four violent types. Within the 0-5 band, felony assault complaints per entry are about twice their 2019 level (1.95, 1.44 to 2.64) while robbery is down by a quarter and grand larceny by about an eighth. The pooled G near 1 is the sum of a rise in assaults and a fall in thefts. A reader who takes "the late-night rate is at its 2019 level" as a statement about personal safety would be misled. Changes in how assaults are charged and recorded after 2020 (for example more assaults on transit workers and police charged as felonies) are a rival explanation for the assault rise and are not examined.

The placebo excludes 1 (1.05, 1.02 to 1.07) and is reported as "small". With B below 1 the placebo no longer has anything to explain, so this does not matter for the verdict.

Police deployment by hour changed during the period (the overnight train patrols that began in early 2025). More officers present can raise recorded complaints, especially assaults on officers, and lower victim-reported thefts. This is not named.

## (e) Could the test have failed?

Yes, on the second and third conditions. The standard error of log G[0-5] is 0.057, so refutation needed G below about 0.89 and support needed G above about 1.12 together with B of 1.10. The result is z = -0.62 from no change since 2019 and z = -3.8 from the lower edge of the registered prediction (1.2), and z = -9.9 from the middle of the predicted range. The magnitude prediction of 1.2 to 2.2 is rejected. The refutation rule was written as an upper bound below 1, so a rate at its 2019 level is unsettled under the rule even though the predicted rise did not occur. The outcome's `prediction_scored` says this.

The first condition could hardly have failed, as noted under (c).

Recommendation: keep. Neither registered condition is met, the re-estimate equals the registrant's (0.965, 0.861 to 1.082), and no variant moves it across a threshold; the outcome should add that against the State's 2021 baseline the late-night rate fell by about 19 percent and the daytime rate by about 35 percent, and that late-night felony assaults per entry have roughly doubled since 2019.
