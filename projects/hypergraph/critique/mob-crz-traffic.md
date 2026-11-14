# Referee report: mob-crz-traffic

Verdict recorded: confirmed. Recommendation: keep the verdict.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required a speed DiD above zero with its interval above zero, and a trip DiD below zero. Speed: +5.7% (+2.9 to +8.6). Trips: -9.8% (-12.8 to -6.6). The registration (15:15:19) preceded the outcome (15:19:20) by four minutes. That is short but consistent with a prepared script. The prediction text says "2025 vs 2024" while the plan says the pre-period is 2023-2024. The code follows the plan.

## (b) Errors in code, units, joins or dates

The TLC query used `socrata.query` with the default 50,000-row limit rather than `query_all`. I checked the cached result: it returned 34,771 rows, so it was not truncated. The speed series ends in August 2025, so the post-period is eight months, and calendar-month effects for September-December come only from the pre-period. HAC errors are computed on a stacked two-area panel sorted by area, so the lag window crosses the boundary between the two series. The effect on the interval is small.

The trip DiD has a significant 2024 placebo (-4.5%, -6.3 to -2.7). About half the trip result is a pre-existing trend, as the outcome says. The registered support rule required only a negative trip DiD, so the verdict stands, but the trip half is weak.

## (c) Is the research comparison fair?

There is no graph finding. Stockholm and London figures are traffic counts across a cordon, not speeds or TLC trips, so the outcome correctly leaves graph_effect empty.

## (d) Alternative not addressed

The MTA speed series measures taxi and FHV trips, so it draws on the same TLC trips as the trip-count test. Speed and trips are therefore not independent measurements. A change in which trips are made inside the CBD (shorter or longer trips, a different industry mix after the per-trip surcharge) changes measured speed without any change in general traffic. The analysis does not test this. Return-to-office mandates in early 2025 would push traffic the other way.

## (e) Is the settle condition right?

Yes. A longer post-period, a comparison not affected by diversion, and area-specific trends for trips are the right next steps. Adding a non-TLC speed source (DOT traffic speeds) would address the shared-source problem.

## Recommendation

Keep "confirmed". In the label, state that the confirmation rests on speed, and that the trip result is half pre-trend.
