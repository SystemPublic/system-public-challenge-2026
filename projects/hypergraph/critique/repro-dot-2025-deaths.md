# Referee report: repro-dot-2025-deaths

Verdict recorded: contested. The referee did not register the claim and did not read the registrant's interpretive documents. Scratch work is in the session scratchpad under `referee-repro-dot-2025-deaths/`.

## (a) Does the verdict follow from the registered conditions?

Yes. The support condition needs the 2025 and 2024 citywide deaths and both injury counts within tolerance under the primary readings. Deaths are 229 against 205 (tolerance 195 to 215) and 268 against 253 (241 to 265), so support is not met. The refutation condition is that no registered reading puts the 2025 death count within tolerance. D1 and D2 both give 229, and D3 was registered as not computable. Refutation is met and rule 1 of PRECEDENCE gives contested. Rule 3 (no_test) does not apply, because the registration said in advance that D3 could not be computed and D1 and D2 were run as planned.

No measure chosen after the data were seen decides the verdict. The person-type breakdown and the join of persons to boroughs are labelled exploratory.

The times are in order. The registration records 19:56:43, the commit on main is 19:56:45, and the branch `prereg/repro-dot-2025-deaths` exists on GitHub (95b8927, commit time 19:56:50) with the same file content. The first fetch is 19:58:20, the last 20:02:10, and the outcome was decided at 20:04:55. I could not check GitHub's own push time. The registration lists cache files fetched earlier by other agents that hold 2025 deaths for parts of the city, and states that the registrant did not open them. That cannot be verified. The registrant's expectation (open data below DOT) was wrong in direction, which is some evidence that the totals were not known.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error that changes the deciding number. I queried both tables again on 13 November (persons `rowsUpdatedAt` 12 November 17:31 UTC) with yearly aggregates and with row-level pulls. Deaths by crash date are 229 in 2025 and 268 in 2024 in both the persons table and the crash table. Every killed-person row has a distinct `unique_id`, there are no repeated persons within a collision, and I found no pair of fatal crash rows sharing date, time and coordinates. Pedestrian deaths are 119 and 124. Person types are as reported (occupants 111 to 66, other motorized 11 to 34).

Robustness variants the registrant did not run:

Earlier years. The two tables give 231, 244, 269, 297, 290, 280, 268 and 229 deaths for 2018 to 2025. The 2024 and 2025 gaps against DOT are both positive. From memory, DOT's totals for 2019 to 2021 were about 220, 243 and 273, which would make the open tables about 24 deaths higher in each of those years as well. I did not check those three DOT figures in this review. If they are right, the 2025 gap of 24 is the usual gap and not something particular to 2025, and the registered 5% tolerance was likely to be missed in most years.

Excluding medical events. Removing fatal crashes whose contributing factor is illness, loss of consciousness, physical disability or falling asleep removes 12 deaths in 2025 and 8 in 2024. That gives 217 (5.9% above DOT, still outside the tolerance) and 260 (2.8% above, inside). No reading puts 2025 within tolerance.

Excluding limited-access roads. Removing in addition crashes whose street name is an expressway, parkway, bridge, tunnel or highway gives 165 in 2025 and 189 in 2024, far below DOT. DOT does not exclude highways as a class.

Completeness by month. November 2025 has 7 recorded deaths. The other months of 2025 have 13 to 29, and November 2024 has 23. This may be a real low or incomplete recording in the open table. If November is incomplete, the open-data total for 2025 is above 229 and the gap is larger. The outcome does not mention this.

Year-on-year change. DOT's fall from 2024 to 2025 is 19.0% (253 to 205). The open tables give 14.6% (268 to 229). The direction agrees and the sizes differ by about a quarter.

Dates and windows are handled correctly: `crash_date` is a date at midnight, so the year boundaries and the 15 December window include the right days. The coordinate method converts degrees to metres with one factor for both axes, which is rough but affects only crashes outside every polygon. Borough results do not decide the verdict.

The city effect has no interval. That is correct, since these are counts of records and not samples. The stance is null, which follows rule 6.

## (c) Is the comparison with the published figure fair?

Only in part, and the registration says so (`data_access` is "partly_open"). DOT's count comes from a reconciled file that is not published. The open tables are NYPD's collision records. They cover the same city and year but not the same definition of a traffic death. The claim as registered tests whether the open tables reproduce DOT's number, and they do not. It does not test whether DOT's number is right. The word "contested" on the dashboard could be read as a finding against DOT's count. The outcome's notes say that the likely cause is DOT's exclusions, and the label should say that too.

The injury comparison is fair and reproduces within 0.5% over the same window in both years. I summed the registrant's cached daily series again and obtained 47,744 and 51,775; a fresh aggregate query of my own did not return in time, so the injury counts are checked for arithmetic and not re-fetched. The stated figures were taken from the press release by the registrant. The borough figures sum to 205 and 253, which is a check on the transcription. There is no graph evidence for this claim.

## (d) Alternative explanation not addressed

The outcome attributes the gap to deaths that DOT excludes, without testing it. The medical-event variant above shows that the one exclusion visible in the open data accounts for about half of the 2025 gap at most (12 of 24) and for 8 of 15 in 2024. The rest is unexplained. Not addressed: deaths that NYPD records and later reclassifies (suicides, homicides by vehicle, crashes on private property), which are corrected in DOT's file but not in the open table; and the possible incompleteness of November 2025. The change in person-type coding in 2025 (other motorized 11 to 34) is raised as a research question and does not affect the total.

## (e) Could the test have failed?

The claim could have been confirmed: injuries reproduce within 0.5%, 2024 deaths miss by 5.9% against a 5% tolerance, and the medical-event variant brings 2024 inside. The 2025 death count was unlikely to pass if the earlier-year gaps are as I recall them, so the outcome was more predictable than the prior of 0.3 suggests. A z value in the usual sense does not apply, because the two figures are counts of the same events and not independent samples. In units of the registered tolerance (10.25 deaths for 2025, 12.65 for 2024) the 2025 gap is 2.3 and the 2024 gap is 1.2. If the two counts were treated as independent Poisson draws, the 2025 gap would be about 1.2 standard errors (24 over the square root of 434), so the gap matters as a difference of definition and not as a difference between two noisy counts.

Recommendation: keep. The re-estimate is 229 against DOT's 205, as the registrant found, and the registered refutation condition is met; the label should state that the open NYPD tables do not reproduce DOT's reconciled count, and not that DOT's count is wrong.
