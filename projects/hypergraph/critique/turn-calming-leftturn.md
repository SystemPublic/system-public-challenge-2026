# Referee report: turn-calming-leftturn

Verdict recorded: confirmed (rule 1), with an exploratory placebo and a trend-adjusted ratio in the notes. The design, data, order of registration and my separate code are the same as for `turn-calming-ped`. That report (`critique/turn-calming-ped.md`) covers the commit order, the dataset versions, the EB method, the cohort stacking and geocoding checks, and the note `docs/turn_restrictions.md`. This report gives the left-turn numbers and the points that differ.

The outcome counts crashes within 40 m of the site in which at least one vehicle in Motor Vehicle Collisions - Vehicles (`bm4k-52h4`, rowsUpdatedAt 2026-11-13T15:33:26Z) has `pre_crash` 'Making Left Turn'. The vehicle extract is complete: 227,926 rows and 207,891 distinct collision ids, matching a count query on the current version. Of these collision ids, 187,824 match a geocoded crash in `h9gi-nx95` within the city box.

## Re-estimate

| Crashes with a left-turning vehicle, 40 m | Registrant | Referee |
|---|---|---|
| Registered ratio of ratios (95% CI) | 0.9041 (0.8473-0.9647) | 0.9040 (0.8472-0.9645) |
| Site-cluster bootstrap interval | not run | 0.843-0.962 |
| Treated sites; crashes before and after | 722; 3,242 and 2,683 | 722; 3,242 and 2,683 |
| 30 m radius | 0.8953 | 0.8934 |
| Cohorts avoiding March-June 2020 | 0.900 (0.821-0.986) | 0.900 (0.821-0.986) |
| Second post year only (exploratory) | 0.906 (0.836-0.983) | 0.906 (0.835-0.983) |
| Placebo, installation 12 months early (exploratory) | 0.9339 (0.8607-1.0133) | 0.9340 (0.8608-1.0134) |
| Trend-adjusted (exploratory) | 1.0425 (0.8692-1.2504) | 1.0422 (0.8688-1.2501) |

The numbers reproduce. support_if (upper bound below 1.00) is met by 0.035, and the bootstrap upper bound is 0.962.

## The placebo

Under rules 1 and 4 the verdict follows. Had the placebo been registered, rule 11 would have made it `unsettled`. Against the placebo as the null, z_null is 0.61 (difference of log ratios -0.033, combined standard error 0.053). The estimate is 3.1 standard errors from the predicted midpoint (0.815), so D = 0.37 - 9.7 = -9.3.

Compared with the 4,713 untreated signalized intersections in the same months (exploratory), the treated sites' left-turn crashes changed by 0.976 relative to the pool, and the later-treated controls by 1.039. In the placebo windows the figures are 0.961 and 1.019. Most of the registered ratio of 0.904 therefore comes from the controls rising, not from the treated sites falling. Measured against untreated intersections, the treated sites fell by 2.4% over 25 months, less than the 3.9% they fell in the 12 placebo months before installation. The event profile (treated per month as a multiple of the pool mean: 2.72, 2.78, 2.64, 2.55 in the four years before installation, then 2.53, 2.59 in the two after) shows no change at installation.

Lengthening the control gap makes both the estimate and the placebo smaller (more than 36 months: 0.884 and 0.921; more than 48 months: 0.858 and 0.900). As for pedestrians, this argues against the note's account of controls approaching their own crash peak, and for different long-run trends in early- and late-treated sites.

The EB before-after gives θ = 1.101 (1.048-1.155) with the volume-proxy SPF and 1.161 (1.098-1.224) with the crash-history SPF. The placebo θ values are 1.160 and 1.245, so the method fails its own placebo here as well, for the reason given in the pedestrian report: the SPFs under-predict the treated sites, and the shrinkage goes too far. It does not measure an effect.

## Points specific to this outcome

The 'Making Left Turn' code roughly halves citywide from 2019 to 2020 (24,582 to 12,636 vehicles in the registrant's citywide query). Calendar-matched controls and the untreated pool absorb this change if it is proportional across sites. Two facts suggest it is not fully proportional. The 2020 cohort, whose pre window straddles the change, gives 1.14, and the 2019 cohort gives 0.71. Restricting to cohorts whose windows avoid March-June 2020 leaves the estimate at 0.900, so the coding change is not what produces the confirmation.

The left-turn outcome is a crash count, most of it without injury. A slower turn would be expected to reduce injury severity more than crash frequency. The outcome cannot show that, and the claim does not assert it.

## Does the verdict stand, and does the note overstate it?

The verdict stands under rules 1 and 4. It is a hit on the registered condition and no evidence that calming reduced left-turn crashes. The note's statements that the data "agree with DOT's reported -18%" and that "the true effect probably lies between the registered ratio and 1" are not supported for this outcome either. The trend-adjusted ratio is 1.04 (0.87-1.25), and measured against untreated intersections the treated sites fell less after installation than in the year before it.

## Recommendation

1. Keep `confirmed` under rules 1 and 4, and show the placebo (0.934, 0.861-1.013) and the trend-adjusted ratio (1.04, 0.87-1.25) beside it wherever it appears. Do not count its stance (0.909) as agreement in summaries. Reword `prediction_scored` so that it says the result is no evidence of a calming effect. The current wording, "the placebo makes the causal reading doubtful", is too weak.
2. Add to the notes the decomposition against untreated intersections (treated 0.976, controls 1.039) and the cohort spread from 0.71 to 1.14.
3. Register a successor (`turn-calming-leftturn-v2`) with the design given in recommendation 3 of the pedestrian report, deciding on months after September 2026. If the successor uses the vehicles table after 2025, it should name how it treats the pre-crash value 'Unknown', which the red-light camera referee found was added in 2026.
