# Referee report: mob-crz-air

Verdict recorded: unsettled. Recommendation: change to no_test. The registered primary test (NO2) could not be run, and the PM2.5 secondary is not robust.

## (a) Does the verdict follow from the registered conditions?

The registration made NO2 the primary test and PM2.5 secondary. The EPA AQS daily NO2 files contain no Manhattan monitor for 2022-2025, so the primary test was not run. The concord/claims.py definition of no_test ("the data could not address the question") fits the registered primary. The PM2.5 result (-5.2%, -9.5 to -0.9) has an interval that excludes zero in the predicted direction, so by the generic rule it would be "confirmed" on the secondary. The outcome instead chose unsettled because a same-days comparison gives -0.3%. That judgement is defensible, but it is made after seeing the data and is not the registered rule.

## (b) Errors in code, units, joins or dates

I inspected the raw AQS PM2.5 files. The in-zone monitor (PS 19) is a 24-hour FRM sampler running one day in three, and it begins in 2023, not 2022. The comparison monitors mix FRM samplers with continuous FEM monitors that report both "1 HOUR" and "24-HR BLK AVG" rows; `load()` averages all POCs and sample durations within a site-day. FRM and FEM readings differ systematically, and the comparison set changes over time (IS 74, PS 314 and PS 274 start in 2023). Date fixed effects do not remove a change in the method mix of the comparison group. These are the most likely source of the -5% estimate, as the outcome's same-days check suggests.

## (c) Is the research comparison fair?

There is no graph finding. The literature cited (Fraser et al. 2025; DOHMH 2026) addresses the same question, but with different networks and outcome definitions (daily maximum PM2.5 against a counterfactual). The comparison is descriptive only.

## (d) Alternative not addressed

A one-monitor comparison cannot separate the policy from local change near PS 19 (construction, school-day sources). This alternative was named but nothing in the analysis tests it.

## (e) Is the settle condition right?

Yes. An in-zone NO2 record with a pre-period is the missing information. The settle condition should also ask for a single, consistent method (FRM only, or FEM only) in the PM2.5 comparison.

## Recommendation

Change to no_test for the registered primary, and report the PM2.5 estimate as exploratory, recomputed with FRM monitors only and a fixed comparison set.
