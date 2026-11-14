# Referee report: repro-dcp-2025-completions

Verdict recorded: confirmed. The referee did not register the claim and did not read the registrant's interpretive documents. Scratch work is in the session scratchpad under `referee-repro-dcp-2025-completions/`.

## (a) Does the verdict follow from the registered conditions?

Yes. The support condition is that R1 (new-building jobs, `compltyear` 2025, sum of `classaprop`) falls within 4% of 38,682, that is 37,135 to 40,229. R1 is 38,689. Under rule 1 of PRECEDENCE the verdict is confirmed. R1 is also inside the 2% band. No measure chosen after the data were seen decides the verdict. The permit count, the borough counts and the permit-year breakdown are reported as secondary or exploratory, as registered.

The times are in order. The registration file records 19:56:34, its commit on main is 19:56:37, and the branch `prereg/repro-dcp-2025-completions` exists on GitHub (bc791bc, commit time 19:56:42) with the same file content as main. The first query in the outcome's sources was fetched at 19:57:16 and the outcome was decided at 19:58:20. I could not check the time GitHub received the push, only the commit time and that the branch is there.

Two things weaken the timing as evidence. The analysis script was saved 31 seconds after the registration and the outcome 104 seconds after, so the script was prepared with the registration. That is allowed. The project's cache held a row-level copy of all 35,188 new-building rows with `compltyear` and `classaprop`, fetched at 15:21 the same day by another agent, so R1 could have been computed before registration from a file on disk. The registration discloses this file and says only its headers were read. That statement cannot be verified. The prior of 0.6 and the wide 4% band do not suggest that the answer was known.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error. I fetched the rows again (13 November, 00:49, same `rowsUpdatedAt` of 30 September 2026, version 26Q2.1) and recomputed at row level instead of by SoQL aggregation. R1 is 38,689 from 1,014 jobs, with no duplicate job numbers and no missing `classaprop`. R2 is 40,567. The borough sums are Manhattan 4,874, Bronx 5,683, Brooklyn 18,046, Queens 9,608 and Staten Island 478, as in the outcome. R1 for 2024 is 33,859, equal to DCP's 25Q4 figure.

Robustness variants the registrant did not run all return 38,689: dating completion by the year of `datecomplt` instead of `compltyear`, summing `classanet` instead of `classaprop`, and keeping only rows flagged residential. Adding hotel and other Class B units gives 40,540, close to R2, which supports the outcome's reading of why `units_co` is higher. No single job is as large as the 4% band (the largest is 1,050 units; the band is 1,547), so the result does not depend on one record.

R3 is not an independent reading in this release, because all 1,014 jobs have status 5. The outcome says so.

The interval on the city effect (plus or minus 0.34%) is the size of one earlier revision, not a sampling interval, and the outcome labels it that way. The stance of 0.974 is computed from that interval and has no statistical meaning. A count of records has no sampling error, so the only uncertainty is revision between releases.

The release differs from the one the snapshot used. Of the 2025 completions in 26Q2.1, 209 jobs with 19,800 units have a last-update date after 15 January 2026, and DCP edited `classaprop` by hand on 19 jobs with 1,583 units. The boroughs show small offsetting differences (Queens +8, Brooklyn -2, Staten Island +1). The match to 7 units is therefore a match after revision and not proof that the 25Q4 figure was computed by exactly this rule, but a different rule that happened to land within 7 units in total and within 8 in every borough is very unlikely.

The permit count is not reproduced, as the outcome reports: P1 is 18,539 against 17,673. I looked for a simple rule that gives 17,673 in this release and did not find one. Jobs still at status 3 give 17,249. Excluding jobs whose `classaprop` DCP edited gives 17,564. Permits dated December 2025 hold 4,138 units, so late recording of December permits is a plausible source of the 866 extra units. This needs the 25Q4 file.

## (c) Is the comparison with the published figure fair?

Yes for the headline. The outcome, the unit (housing units), the period (calendar 2025) and the geography (citywide and borough) are the same. The data release is later than the snapshot's, which the registration states and the tolerance allows for. The stated numbers were taken from `docs/reproduction_inventory.md`, a transcription of the StoryMap. I did not check the transcription against the StoryMap. The five borough figures sum to 38,682 only because Manhattan was obtained by subtraction, so the Manhattan match (4,874) is the one borough comparison that depends on the transcribed total. There is no graph evidence for this claim.

## (d) Alternative explanation not addressed

The registered alternative that the snapshot counts units incrementally, as certificates are issued, is not ruled out by direct evidence. It is made unlikely by the borough agreement, since an incremental count would differ from R1 by thousands of units (the aggregate table gives 43,654 for all job types). The alternative that the 25Q4 release gave a different R1 and later revisions moved it to within 7 units by coincidence is not tested. The registered follow-up on the archived 25Q4 file would test it and has not been run.

The outcome's notes say the high 2025 count "is therefore the 2022 permit surge reaching certificates of occupancy, not a rise in new starts". The permit-year table supports the first half (23,669 of 38,689 units were permitted in 2022). This is labelled exploratory and does not bear on the verdict.

## (e) Could the test have failed?

Yes. The second registered reading, `units_co`, misses the band at +4.9%, and the secondary permit count misses at +4.9%. A reader who chose `units_co` for "units completed" would not have reproduced the figure. The band was wide: 4% is 1,547 units, about twelve times the 2024 revision. Taking the 0.34% revision (132 units) as the unit of uncertainty, R1 is 0.05 units from the stated figure and R2 is 14 units from it. "No effect" has no meaning for a reproduction, so the relevant contrast is between readings, and the test separates R1 from R2 clearly.

Recommendation: keep. R1 recomputed at row level is 38,689 against 38,682, the verdict follows from the registered rule, and three further variants give the same number; the label should say the match is on release 26Q2.1 and that the permit figure was not reproduced.
