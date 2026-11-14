# Referee report: retimed-daytime-burglary

Verdict recorded: contested. The referee re-ran the analysis from the cached complaint records. Scratch code is outside the repository (session scratchpad, folder `referee-retimed-daytime-burglary`).

## (a) Does the verdict follow from the registered conditions?

Only for one bootstrap seed. The second refutation condition is "the lower bound of the 95% interval of the citywide ratio is above 0.95". The outcome reports a lower bound of 0.9525. The registration fixed 2,000 draws and did not fix a seed; the seed (7) is a default in `lib.py`, which was not committed until 00:06:16 and was last modified at 23:55, after the burglary results were written at 23:53. With the same 2,000 draws and 40 other seeds the lower bound ranges from 0.947 to 0.956 and is above 0.95 in 62% of them. With 50,000 draws it is 0.9509. The registrant's own check with 20,000 draws gave 0.9499. A normal interval from the bootstrap standard error gives 0.9507, and from a Poisson standard error 0.9534. The true percentile is within 0.001 of the threshold and the registered procedure cannot place it on either side.

The outcome states this openly. It then applies rule 1 and records "contested". I do not think rule 1 requires that. The registered condition does not say which of two equally valid runs of the procedure counts, so the condition is neither clearly met nor clearly unmet, and rule 2 applies.

No measure chosen after the data decided the verdict. The registration is dated 23:48:46, committed at 23:48:55 (52f3c02), and the branch `prereg/retimed-daytime-burglary` exists on the remote with a commit at 23:48:57 holding only the registration file. The complaint records were fetched at 23:53:00 and 23:53:05. The design query, which pooled Monday to Friday by year, was written at 23:47 and is disclosed. The outcome is dated 00:05:03.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no coding error. My re-estimate of the ratio is 1.0114 with a lower bound of 0.9525 (seed 7, the registrant's script and groups), identical to the outcome, on 13,965 baseline and 6,660 recent complaints. The two datasets do not overlap (no duplicate complaint numbers), monthly counts for 2026 are level through September, and three records lack coordinates. The district join reproduces the secondary contrast: 0.868 (0.761 to 0.988).

Robustness variants the registrant did not run, all citywide:

- Recent period 2023-2025 only, which uses the historic file alone: 0.999 (0.936 to 1.061).
- Recent period 2024 to September 2026: 0.981 (0.914 to 1.053).
- Baseline 2018-2019: 1.006 (0.924 to 1.096).
- Start time 09:00 to 16:59: 1.046 (0.971 to 1.124).
- Start times not on the hour (53% of records): 0.974 (0.893 to 1.058). On the hour: 1.077 (0.985 to 1.173).
- Start and end within one day: 0.988 (0.920 to 1.055).
- Public housing excluded: 0.985 (0.925 to 1.049).
- Storm weeks kept: 1.009 (0.950 to 1.072).

Every variant has a lower bound below 0.95 except the 09:00 to 16:59 window. The lower bound for the storm-week variant, 0.9496, is as close to the threshold as the primary. The registrant's own sensitivity runs are mixed in the same way: the lower bound is 0.904 for complaints ending the day they began, 0.946 for completed burglaries and 0.952 for the 2017-19 baseline. The exclusion of a 5% fall does not survive ordinary changes to the specification.

The mix of premises changed. Public housing is 5.2% of baseline complaints (732) and 10.9% of recent ones (726), and in that category the ratio is 1.24 (1.00 to 1.52). The rise in share pulls the citywide ratio up. Without it the point estimate is below 1.

The yearly log ratio of Monday-and-Friday to midweek is 0.18 in 2023, 0.06 in 2024, 0.04 in 2025 and 0.18 in 2026. Its standard deviation over the four recent years is 0.074 against a Poisson expectation of 0.051. Treating years as units, the difference between periods is +0.021 with a standard error of 0.040, a ratio interval of about 0.94 to 1.10. The week bootstrap may be slightly too narrow.

## (c) Is the comparison with the research fair?

No research number is compared. Cohen and Felson is cited for the direction only, and the registration says the citation is from memory. I checked one graph finding named in the registration, PMID 35491751, against its PubMed abstract: restaurant openings in Oakland were related to a 5.3% increase in burglaries (relative risk 1.05, 1.04 to 1.06). The number is right. The study concerns alcohol outlets, which the registration does not say, and it has no bearing on occupancy.

The predicted size takes the fall in morning-peak subway entries (about 10%) as the fall in empty homes and assumes burglaries fall by half to all of it. Subway entries count commuters, not households at home, and a household is empty only if every member is out. The mapping from exposure to prediction is loose, so missing the range says little about the mechanism.

## (d) Alternative explanation not addressed

The recorded day is when the victim's absence began. Friday is the peak day in both periods because people leave for the weekend. Work at home on Fridays would be expected to coincide with more Friday departures for long weekends, which adds Friday start dates and offsets any true fall. Complaints with a window of two days or more have a ratio of 1.11 (0.96 to 1.29) and those within one day 0.99 (0.92 to 1.06), which is the direction this explanation predicts. The registration lists the recording issue but the outcome does not use the window length to examine it. Monday fell by 2.1% and Friday rose by 3.9%, which also fits.

The rise in the public-housing share is a second unaddressed change in composition, different from the package-theft alternative that was named.

The secondary district contrast has the registered sign and an interval that excludes zero (-13.2%). A permutation of the 48 districts into random halves gives a two-sided p of 0.08, so the week bootstrap overstates its precision. The outcome is right to give it no weight in the verdict.

## (e) Could the test have failed?

It could fail to confirm, and the registration said so: a prior of 0.25 and a standard error of 0.031 against a central prediction of -0.075. The estimate is 2.7 standard errors from the central prediction, 1.9 from the small end of the range (-0.05) and 0.36 from no effect, so D = -7.3. The data favour no change over the registered fall. The registration also said an estimate above +0.011 would refute, and the estimate is +0.0114. A refutation rule that triggers on a point estimate 0.36 standard errors above zero is a threshold on where the interval happens to end, and here it ends on the threshold.

Recommendation: change the verdict to unsettled. The refutation condition is met in 62% of bootstrap seeds and at 0.9509 with 50,000 draws, and it fails under seven of eight alternative specifications, so the registered procedure does not determine it; the notes should keep the statement that no fall is seen and that a fall of more than about 5% to 7% is unlikely.
