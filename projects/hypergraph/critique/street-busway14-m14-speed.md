# Referee report: street-busway14-m14-speed

Verdict recorded: confirmed (support_if met: DiD +5.46%, lower bound +1.69%). The referee rebuilt the deciding number from data.ny.gov with separate code that does not import `analyses/` or `concord/`. The scratch code is in the session scratchpad folder `ref/` (`bus_fetch.py`, `bus_est.py`, `bus_trend.py`). I read `docs/street_space.md` only after the re-estimates below were finished.

## Order of registration and data

The script `bus.py` and the design file `bus_design.json` were committed in 073d33f at 13:12:18. The registration f26cd61 followed at 13:12:22 and names 073d33f. The design query excludes every route beginning with M14 and covers July 2021 to February 2024 (`route_id not like 'M14%'`; cache file written at 13:11:12). The two earlier cached queries of `cudb-vcni` (13:07:25 and 13:07:26) list route ids, month ranges and dimensions, and hold no speeds. The query with M14 speeds for 2019-20 was cached at 13:12:33, after the registration. The outcome was decided at 13:21:51 and committed in c523b83. The design commit holds no outcome number.

## Re-estimate

Data: MTA Bus Speeds: Beginning 2015 (data.ny.gov `cudb-vcni`, rowsUpdatedAt 2026-10-23T15:23:54Z, the same version as the outcome), Manhattan rows January 2019 to February 2024, all day types, periods and trip types (10,038 rows, fetched 13 November 2026). I summed total_mileage and total_operating_time over weekday rows by route and month.

| Version | DiD, % (95% interval) |
|---|---|
| Registrant (outcome) | +5.457 (+1.693 to +9.360) |
| Referee | +5.457 (+1.693 to +9.360) |

There are 39 control routes and 119 placebo estimates (39, 40 and 40 in 2021, 2022 and 2023). The number and the placebo standard deviation (0.01854 log) reproduce exactly.

## The placebo distribution

The 119 placebo DiDs have mean zero by construction within each season. Their empirical 2.5% and 97.5% points are -4.32% and +3.49%, and 2 of 119 (1.7%) are at least as large as the M14 estimate. The distribution has heavier tails than a normal one (excess kurtosis 1.9), and the median absolute deviation gives a robust standard deviation of 1.24%, below the 1.85% used. The normal interval is therefore not too narrow for the bulk of routes. The seasonal standard deviations differ (1.52%, 2.29% and 1.71%). The M14 itself, treated in the same way in 2021, 2022 and 2023, gives +0.27%, +0.66% and +0.14%, so the M14 has no large route-specific seasonal swing between these windows once the busway was in place.

The placebo covers seasonal noise. It does not cover a route in its first months after a service change. No placebo route was three months into a new Select Bus Service.

## Does the SBS launch inflate the gain?

Yes, and probably by most of the estimate. M14 speed relative to the 39 controls, by month, with July to September 2019 set to zero on average:

| Month | Jan-Jun 2019 (local) | Jul 2019 | Aug 2019 | Sep 2019 | Oct 2019 | Nov | Dec | Jan 2020 | Feb 2020 |
|---|---|---|---|---|---|---|---|---|---|
| Relative speed, % | -6.8 to -2.3 | -1.9 | -2.6 | +4.5 | +5.5 | +6.1 | +5.5 | +4.3 | +4.6 |

The step came in September 2019, a month before the busway opened on 3 October. From August to September the M14 gained 7.1 points on the controls, against a standard deviation of 2.1 points for one-month relative changes of other Manhattan routes in 2021 to 2024. In 2022 and 2023 the M14 also rose against the controls in September, by 1.7 and 1.8 points, so part of the September step is seasonal, but most of it is not. Measured against September 2019 alone the busway months are +0.7% faster; against July and August alone they are +7.4% faster. The registered baseline averages a slow start-up (July, August) with a month that already had most of the gain.

I could not identify what changed in September 2019. Possible causes are the SBS settling in (off-board fare use, operators learning the stops), the start of bus-lane camera enforcement, or school-term traffic that slowed the controls more than the M14. The registration named SBS learning as an alternative. The comparison with September alone was chosen by me after seeing the data, so under rule 4 it decides nothing. It does show that the registered test cannot separate the busway from what happened in September.

## Problems

1. Most of the estimated gain was present before the busway opened. This is the most important problem. The outcome's notes mention the summer speeding up (5.42, 5.48 and 5.62 mph) but describe it as a trend; the data show a step in September of about the size of the whole estimate.
2. Route-wide speed dilutes a corridor effect, as the outcome says. This works against the claim, so it does not explain the September step.
3. October 2019 includes two days before the busway. The effect on the estimate is small.
4. The DOT corridor figure (22% to 47%) uses a 2018 baseline and includes the SBS; the outcome says so correctly.

## The person-minute break-even

This section covers the "Weighing the three" passage of `docs/street_space.md`, which rests mainly on this claim. I checked each number.

| Quantity | Docs | Referee |
|---|---|---|
| 1.5-mile ride at 5.502 mph | 16.4 min | 16.36 min |
| Saving at +5.457% | 0.85 min | 0.846 min |
| Bus riders' gain, 29,486 boardings | about 25,000 person-min | 24,958 |
| Ride 1 to 2.5 miles | 16,600 to 41,600 | 16,640 to 41,600 |
| Speed interval +1.69% to +9.36% | 8,000 to 41,000 | 8,030 to 41,281 |
| Break-even, taxi point (0.93% of 11.5 min) | about 240,000 trips | 233,000 (241,500 at 0.9%) |
| Break-even, FHV north point (1.56% of 17.6 min) | about 90,000 | 90,961 |
| Break-even, taxi upper (4.32%, 30 s) | about 50,000 | 50,203 |
| Break-even, FHV north upper (6.49%, 69 s) | about 21,000 | 21,860 |

The arithmetic is correct. The assumptions are not symmetric between the two sides.

1. The bus gain is taken at the point estimate with the whole M14 gain credited to the busway. The docs call this an upper figure, but then compare it with driver costs at their point estimates and upper bounds. With the bus gain at its registered lower bound (8,030 person-minutes), the four break-even counts fall to 75,000, 29,300, 16,200 and 7,000 occupant-trips a weekday. With the gain measured against September 2019 alone (+0.7%, about 3,300 person-minutes; exploratory), they fall to 30,900, 12,000, 6,600 and 2,900. Several of these are well below the M14's weekday ridership.
2. The driver costs are zone-pair averages that include trips that never used 14th Street (critique/street-busway14-crosstown-time.md, problem 1). The matching count is all vehicle trips across the corridor area, not only "affected" trips. The docs' word "affected" invites a reader to compare with a count of trips that used 14th Street, which would be the wrong population.
3. Two occupants per vehicle fits a taxi with one passenger. Private cars and trucks carry fewer people per vehicle in Manhattan, and drivers' and passengers' time are both counted while bus operators' time is not.
4. The bus side counts in-vehicle time only. Waiting time and reliability are left out, which understates the bus gain. Ridership of 29,486 includes riders added by the SBS and the L train slowdown, which overstates the busway's share. The 1.5-mile ride is the author's assumption, as the docs say. I did not re-query the ridership datasets (`98u6-vmgs`, `kv7t-n8in`).
5. The busway runs 06:00 to 22:00 every day. The bus figure uses all weekday boardings, while the driver estimates use weekdays 07:00 to 18:00.

## Does the tradeoff section claim more than the numbers support?

It does in part. The bus paragraph reports the registered numbers correctly and says "part of the gain may be the Select Bus Service settling in". The September step suggests most of it was, so "part" understates the problem. The break-even paragraph concludes that drivers would lose more time than bus riders gained "only if 90,000 to 240,000 affected occupant-trips crossed the corridor each weekday". That conclusion depends on crediting the busway with the whole M14 gain. Under the lower bus figures above, the answer at every driver estimate depends on the traffic count the city does not publish, which is what the docs already say for the upper bounds. The final paragraph ("The cost to drivers is small on average and uncertain for the most exposed trips") is supported.

## Recommendation

Keep `confirmed` under rule 1, because the registered condition is met and reproduces. State beside the verdict, in the notes and in `docs/street_space.md`, that the M14's gain relative to other routes appeared in September 2019, before the busway, and that the busway months are +0.7% faster than September alone (exploratory, chosen after the data). The confirmation is of the registered comparison; it is weak evidence that the busway caused a 4% gain in route speed. A successor claim should use segment or AVL data with the SBS start and the busway start as separate breaks, as the outcome's `research_needed` already proposes.
