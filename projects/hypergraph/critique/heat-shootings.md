# Referee report: heat-shootings

Verdict recorded: confirmed. Recommendation: keep the verdict.

## (a) Does the verdict follow from the registered conditions?

Yes. Confirmation required a lower limit above 1 for the IRR per 5 C. The estimate is 1.146 (1.130-1.163). The prediction is scored partial because the spline RR at the 84th percentile (1.42) exceeds the registered 1.05-1.25. That score is correct.

## (b) Errors in code, units, joins or dates

`shootings.py` follows the plan. Days with no incident are filled with zero; I checked that the series runs to 31 August 2026 with no unfilled tail (monthly totals for 2025-2026 are 35-77). The count check against the historic file agrees to 2 incidents. Robust HC0 errors do not allow for serial correlation. I refitted with HAC errors (7 lags) and with year-by-month fixed effects in place of separate month and year terms, which addresses the registrant's named alternative of residual seasonality and the 2020-21 rise:

| Variant | IRR per 5 C | 95% interval |
|---|---|---|
| Primary, HAC errors | 1.146 | 1.129-1.164 |
| Year-by-month fixed effects, HAC errors | 1.148 | 1.130-1.166 |

The result is unchanged.

## (c) Is the research comparison fair?

Partly. The graph comparison (Xu 2020) is homicide against daily mean temperature over lags 0-7. The city analysis uses shooting incidents against TMAX at lag 0. The Lyons et al. comparison at the 84th percentile uses a different temperature metric and reference, as the outcome acknowledges. The direction comparison is fair, but the size comparison is not.

## (d) Alternative not addressed

Exposure is one station (Central Park) for the whole city. This gives non-differential error that biases toward the null, so it does not threaten the verdict. Within-day timing (shootings after midnight are assigned to the next day's TMAX) is a related source of exposure error.

## (e) Is the settle condition right?

Yes. Fitting the Lyons model to the NYPD series is the right way to compare sizes, and outdoor-activity data would address mechanism.

## Recommendation

Keep "confirmed".
