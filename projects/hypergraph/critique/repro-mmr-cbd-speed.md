# Referee report: repro-mmr-cbd-speed

Verdict recorded: confirmed. The referee did not register the claim and did not read the registrant's interpretive documents. Scratch work is in the session scratchpad under `referee-repro-mmr-cbd-speed/`.

## (a) Does the verdict follow from the registered conditions?

Yes. The support condition is that under R1 the fiscal 2025 value is within 0.2 mph of 6.9 and the fiscal 2026 value within 0.2 mph of 6.5. R1 gives 6.949 and 6.617. Rule 1 of PRECEDENCE gives confirmed. R1 was named as primary in the registration, with its zone list, hours, holiday dates, filter and aggregation written out, so no part of the deciding measure was chosen after the data were seen. The comparison areas (Manhattan north of 60th Street, rest of city) and the half-year splits are named in the plan as descriptive.

The times are in order. The registration records 19:56:25, the commit on main is 19:56:25, and the branch `prereg/repro-mmr-cbd-speed` exists on GitHub (016ac7a, commit time 19:56:29) with the same file content. The first trip file was downloaded at 19:56:37, twelve seconds later, and the last at 19:57:48. The results table was written at 19:58:48 and the outcome decided at 20:02:24. I could not check GitHub's own push time.

Three sources in the outcome were fetched before registration: the taxi zone lookup (19:55:09), the MTA zone list (15:16) and the MTA monthly CBD speed series 6p29-6xqn (15:17), the last two by the earlier claim mob-crz-traffic. The zone tables are not outcome data. The MTA series is a related speed measure through August 2025. It runs about 1.7 mph above the MMR figure and covers all hours and for-hire vehicles, so it could not have been used to tune R1 to 6.9 and 6.5. Unlike the other two reproduction claims, this registration has no statement of what data the registrant had seen. It should have one.

The city effect's interval is the range of the difference over the five readings that reproduced both years. An interval built only from readings that passed is conditioned on success and is narrower than the spread of the registered readings (fiscal 2026 runs from 6.43 to 9.13 mph over R1 to R9). It feeds the stance (0.451) and does not decide the verdict.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error. I rebuilt R1 from the 36 parquet files with separate code (zone list and holiday dates read from the registration, ISO weekday, fiscal year from the pickup month). The result is 6.937, 6.949 and 6.617 mph for fiscal 2024, 2025 and 2026, on 5,607,364, 6,094,457 and 5,922,059 trips. These equal the registrant's figures to three decimals. The holiday list is correct for the 33 observed federal holidays in the window. The weekday test in the registrant's code (`dayofweek` between 1 and 5) selects Monday to Friday in duckdb.

Robustness variants the registrant did not run (fiscal 2025, fiscal 2026):

- Trip wholly within 8AM to 6PM (drop-off before 18:00): 6.958, 6.623.
- No holiday exclusion: 7.000, 6.671.
- Also excluding the day after Thanksgiving and 24 to 31 December: 6.936, 6.593.
- Standard rate code only: 6.863, 6.437.
- Positive fare and card or cash payment: 6.874, 6.443.
- Excluding trips that start and end in the same zone: 6.982, 6.650.
- Trips of at least half a mile: 7.020, 6.698.
- Pickups through 6:59PM: 6.991, 6.668.
- Pickups from 7AM through 6:59PM: 7.094, 6.784.
- Vendor 1 only: 6.742, 6.511. Vendor 2 only: 7.009, 6.642.

Every variant passes for fiscal 2025. All pass for fiscal 2026 except the 7AM start (0.28 mph above). Fiscal 2026 ranges from 6.44 to 6.70 over the variants that keep the registered hours, so the published 6.5 lies inside the range that reasonable trip filters produce. The fall from fiscal 2025 to fiscal 2026 is between 0.31 and 0.43 mph in every variant except vendor 1 alone (0.23), against the stated 0.4.

Uncertainty. The outcome gives no sampling interval. A jackknife over days gives a standard error of 0.05 mph for each fiscal year (250 weekdays, daily standard deviation 0.8 mph). A jackknife over months gives 0.12 to 0.15 mph, which mostly reflects the seasonal pattern.

R1 for fiscal 2026 is 6.617, which rounds to 6.6 and not to the published 6.5. The outcome reports the 0.117 mph gap but does not say that the rounded figure differs. The stated figures were transcribed from the MMR PDF by the registrant; I did not check the PDF.

## (c) Is the comparison with the published figure fair?

Mostly. The indicator definition gives the vehicle type, hours, weekdays, area and holiday exclusion, and R1 follows it. The source of DOT's speeds is not stated. If DOT uses GPS traces, the trip-record figure is a different measurement of the same quantity, and agreement to about 0.1 mph in level over three years is good evidence that trip records are either the source or equivalent to it. The fiscal 2024 value (6.937 against 6.9) is a third match that was registered as secondary. There is no graph evidence for this claim.

The reconciliation with mob-crz-traffic in the notes compares speeds across areas and periods. Those comparisons are descriptive and I did not review them in detail. I did confirm the monthly R1 series: January to June 2026 is slower than January to June 2025 in every month, and February 2026 has both the lowest trip count (381,325) and a low speed (6.26 mph).

## (d) Alternative explanation not addressed

The tolerance of 0.2 mph is half the size of the change the indicator reports (0.4 mph), and five of nine registered readings pass. The reproduction therefore shows that trip records give the MMR's level and direction, but it does not identify DOT's method: the ratio of sums, the median, the strict filter, the passenger filter and the mean of months all pass. The remaining 0.1 mph in fiscal 2026 is not explained. My variants show that restricting to standard-rate trips or to trips with a positive fare moves fiscal 2026 to 6.44 and fiscal 2025 to 6.87, which round to 6.4 and 6.9, so a filter of that kind brings the figure below 6.5 and not onto it.

The notes attribute the fiscal 2026 fall to a citywide fall in taxi speeds in January to June 2026. A change in the trip records themselves is not ruled out. The share of vendor 1 fell from 25% of trips in fiscal 2024 to 19% in fiscal 2026 and a new vendor code appears, and vendor 1 trips are 0.1 to 0.3 mph slower. The registrant checked that both vendors show the fall, which I confirm (vendor 1 from 6.74 to 6.51, vendor 2 from 7.01 to 6.64). Weather in February 2026 is another candidate and is not examined.

## (e) Could the test have failed?

Yes. Four of nine registered readings fail: the mean of trip speeds (0.34 and 0.42 mph too high), the two looser geographies (1.6 to 2.7 mph too high) and the minimal filter (fiscal 2025 off by 0.216). The primary reading could have been one of these. With the day-jackknife standard error of 0.05 mph, R1 is 1.0 standard errors from the stated fiscal 2025 value and 2.3 from the stated fiscal 2026 value (1.3 from 6.55, the top of the range that rounds to 6.5). Against no change between the two years, the fiscal 2026 value is 6.5 standard errors below the fiscal 2025 value (0.332 over 0.051), or 4.6 using the standard error of the difference. The test therefore separates the published fall from no fall, and it accepts R1 because of the registered 0.2 mph tolerance and not because R1 is statistically indistinguishable from 6.5.

Recommendation: keep. An independent rebuild gives 6.949 and 6.617 mph, identical to the registrant's, and ten of eleven extra variants stay within the registered tolerance; the label should say that the fiscal 2026 figure reproduces to 0.12 mph (6.6 against 6.5 after rounding) and that the method is not uniquely identified.
