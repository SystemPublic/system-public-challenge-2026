# Referee report: further-subway-crime-per-million-repro

Verdict recorded: contested. Recommendation: keep the verdict under the register's rules, and rewrite the notes so that it is not read as a failure of the State's number.

Scratch work is in `referee-further-subway-crime-per-million-repro/` in the session scratchpad (`q1.py`, `q2.py`, `q3.py`). It reads `data/derived/further_subway/raw.json` and makes new queries through `concord/socrata.py` to xfre-bxip, sayj-mze2 and vxuj-8kew on data.ny.gov and to qgea-i56i on NYC Open Data.

## (a) Does the verdict follow from the registered conditions?

Yes. Support needed reading R1 to give 1.60 to 1.70 for 2025 and a fall of 27 to 33 percent. I recomputed R1 from the cached table: 1,755 felonies over 1,578 million implied riders, 1.112 per million, and 1.522 for the same months of 2021, a fall of 26.96%. The rate is far outside its band. The fall is also outside, by 0.04 points; the outcome's phrase "at the lower edge of the band" should say "just below the band". R2 to R6 as registered give 1.14, 1.11, 1.11, 6.12 and 1.83, none inside. The refutation condition is met and the rule gives contested.

The reading that does match (NYPD complaints over subway entries) was named in the plan as secondary and was not among R1 to R6, so under rule 4 it decides nothing. The outcome applies that rule correctly.

Timestamps are in order. The registration was committed at 20:28:09 on 12 November 2026. There is no branch named `prereg/further-subway-crime-per-million-repro` on the remote. The file is on the remote in the branch `prereg/further-subway-crime-per-ride-by-hour`, whose commit at 20:28:15 holds both registrations, so it was pushed before the data. The first complaint query is at 20:28:39 and the yeek-jhmu table was fetched at 21:13:53. The outcome is dated 21:15:55. The complaint counts for the secondary reading were in the cache 45 minutes before the registered table was fetched; because the secondary reading was fixed in the plan and cannot decide, this order does no harm.

## (b) Errors in code, units, joins, dates or uncertainty

The registered formula for riders (monthly count divided by the monthly sum of the rate over felony types) is sound for one agency. It is not valid when rates are added across agencies, which makes R5 and R6 meaningless as registered; the outcome says this and gives corrected values. With four of the six readings then equal to R1 or close to it, the registration tested one reading of one table.

The outcome does not explain why the table's rate is low, and its notes say only that the table uses "a larger denominator and a smaller count". I checked the denominator against the MTA monthly ridership table (xfre-bxip, updated 26 October 2026). The riders implied by the NYCT rows equal subway plus NYCT Bus plus MTA Bus ridership: the median ratio over 93 months is 0.998 and the correlation is 0.9998. For January to November 2025 the implied riders are 1,578 million and subway plus bus is 1,581 million, of which the subway is 1,171 million. The column `crimes_per_million_riders` for NYCT is therefore per million subway and bus riders. The State's figure is per subway rider.

The notes also say the felony counts being below the complaint counts "is consistent with" the table description, which says the table counts arrests. That inference is weak. The counts are 90% of the complaint counts (1,755 against 1,940), and arrests for grand larceny and robbery are a much smaller share of complaints than that. The column description in the same metadata reads "the count of Major Felonies committed". The counts resemble incident counts on a somewhat narrower definition than the complaint premise filter, not arrests.

Robustness variants the registrant did not run:

| Reading | 2025 | 2021 | Fall |
|---|---|---|---|
| R1 as registered (table count over implied subway and bus riders, Jan-Nov) | 1.112 | 1.522 | 27.0% |
| Table count over subway ridership only (xfre-bxip, Jan-Nov) | 1.498 | 2.304 | 35.0% |
| Complaints over hourly-table entries, Jan-Nov (the outcome's secondary) | 1.635 | 2.333 | 29.9% |
| Complaints over monthly subway ridership (xfre-bxip), Jan-Nov | 1.656 | 2.337 | 29.1% |
| Complaints over daily subway ridership, 1 Jan to 14 Dec (sayj-mze2 for 2025, vxuj-8kew for 2021) | 1.653 | 2.346 | 29.5% |

The last row uses the days available four days before the release: 2,028 complaints over 1,226.8 million rides in 2025 and 1,695 over 722.4 million in 2021. Counting by report date in place of occurrence date changes the counts by 7 and 4. Every reading that uses NYPD subway complaints over subway ridership gives 1.64 to 1.66 and a fall of 29 to 30 percent.

## (c) Is the comparison with the published figure fair?

It is not the same exposure. The release says "per million riders" in a statement about the subway, and the registered readings divide by subway and bus riders together. The registration took yeek-jhmu as the State's source (`data_used`), while its own `definition` field says the release names no source. The test was therefore of a guess about the source. The guess was reasonable before the data were seen, because the table has a column with the same name as the published statistic.

No graph evidence applies to a reproduction, so there is no finding to check against PubMed.

## (d) Alternative explanations not addressed

The registration's one alternative ("different months, agencies, a different rider count or a different release of the table") covers what happened only in general terms. The specific explanation, that the open table's NYCT rate includes bus riders in the denominator and that the State divided NYPD transit counts by subway ridership, is not stated in the outcome. Whether the bus felonies are in the table's numerator is also open: all NYCT rows are NYPD rows, and the outcome does not test whether 1,755 includes crimes on buses.

## (e) Could the test have failed?

Yes. The primary reading had a 3% band on the rate and a prior of 0.6. Treating the 1,755 felonies as a Poisson count, the standard error of the R1 rate is 0.027, so R1 is about 20 standard errors below 1.65. The claim is a reproduction, so z against no effect does not apply. The complaint-based reading is 0.4 standard errors from 1.65 (1.635 with standard error 0.037).

## What should change in the outcome

The notes should state that the NYCT denominator in yeek-jhmu is subway plus bus ridership, with the check above, and should drop the sentence that the counts are consistent with arrests. `settle` should say that the State's figure is reproduced to two decimal places (1.653) by NYPD subway-premise complaints over subway ridership from 1 January to 14 December 2025, and that this reading was found after the data were seen. That reading should be registered as a new claim, with full-year 2025 and 2024 as the test, as `research_needed` already proposes.

Recommendation: keep. The registered readings all fail, so contested follows from the rule, but the label records a wrong guess about the State's source (a table whose rate is per subway and bus rider), and the published 1.65 and 30 percent are reproduced by complaints over subway ridership.
