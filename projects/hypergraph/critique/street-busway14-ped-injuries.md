# Referee report: street-busway14-ped-injuries

Verdict recorded: contested (refute_if met: lower bound 0.895, above 0.65). The referee rebuilt the deciding number from NYC Open Data with separate code that does not import `analyses/` or `concord/`, including my own corridor endpoints. The scratch code is in the session scratchpad folder `ref/` (`ped_fetch.py`, `ped_est.py`, `ped_names.py`). I read `docs/street_space.md` only after the re-estimates below were finished.

## Order of registration and data

`peds_common.py`, `peds_power.py`, `peds_test.py` and `peds_power.json` were committed in 073d33f at 13:12:18. The registration f470dd5 followed at 13:12:25 and names 073d33f. The two earlier cached crash queries with the corridor box end on 30 September 2019 (written at 13:08:14 and 13:10:23). The query covering October 2019 to September 2022 was cached at 13:12:39, after the registration. The design commit holds no outcome number. Other agents in this repository have queried `h9gi-nx95` for other claims; I did not check whether any of their results covered this corridor after September 2019, and the registrant does not list them as seen.

## Re-estimate

Data: Motor Vehicle Collisions - Crashes (`h9gi-nx95`), crashes with a pedestrian injured or killed, January 2013 to December 2022, in a box slightly larger than the registrant's (11,789 rows), plus crashes without coordinates whose street names mention one of the five streets (126 rows). rowsUpdatedAt was 2026-11-13T14:30:16Z when I fetched, a day later than the outcome's 2026-11-12T14:31:25Z. The counts below are identical, so the update did not touch these rows.

I located the end points of each corridor as the median coordinates of crashes before 2019 whose on-street and cross-street names give the 9th and 3rd Avenue intersections, and assigned crashes within 30 m of the segment (20 m past each end), the nearest corridor winning.

| Version | T pre | T post | C pre | C post | Ratio of rate ratios (95% interval) |
|---|---|---|---|---|---|
| Registrant (outcome) | 128 | 44 | 564 | 147 | 1.319 (0.895 to 1.943) |
| Referee, 30 m | 128 | 44 | 564 | 147 | 1.319 (0.895 to 1.943) |
| Referee, 15 m | 127 | 41 | 550 | 144 | 1.233 (0.829 to 1.834) |
| Referee, 20 m | 128 | 43 | 552 | 145 | 1.279 (0.865 to 1.891) |
| Referee, 45 m | 134 | 45 | 574 | 150 | 1.285 (0.877 to 1.884) |
| Referee, against 23rd Street only | 128 | 44 | 112 | 37 | 1.041 (0.628 to 1.725) |

My end points agree with the registrant's to five decimal places, so the geometry is not independent in its method, only in its code. The number reproduces exactly and is stable across buffer widths; refute_if is met under each of them.

## Corridor geocoding

Of the crashes assigned to 14th Street, 97% before the busway and 74% after it name 14th Street in the on-street, cross-street or off-street field. On the other corridors the share is 90% to 96% in both periods. I read the 11 post-busway crashes on 14th Street that do not name it. Ten are at 14th Street intersections recorded under the avenue only (3rd Avenue, 8th Avenue, University Place, Union Square East); one is recorded as "59 West Drive" at a point near 7th Avenue. The coordinates are correct; the names are incomplete. The change on 14th Street is consistent with more crashes involving vehicles that the busway forces to turn onto the avenues, but that is my reading and was not tested.

The geocoding choice matters. A count based on street names alone (exploratory, my choice) gives 105 and 22 crashes on 14th Street and 422 and 106 on the comparison streets, a ratio of 0.83 (0.50 to 1.38), on the other side of 1 and with refute_if not met. The coordinate method is the registered one and is the better one, since names are incomplete after 2019. The name-based number shows that the registered ratio depends on counting intersection crashes recorded under the avenue.

Crashes with no coordinates are excluded. Those whose names mention the five streets number 14 before and 2 after on 14th Street, and 41 and 13 on the comparison streets. My query did not restrict by borough, so these counts include streets of the same number outside Manhattan and are an upper bound. Adding them all gives a ratio of 1.23.

## The pandemic confound and the trend before the busway

Pedestrian-injury crashes on the comparison streets fell from 112.8 to 49.0 a year (-57%) and on 14th Street from 25.6 to 14.7 (-43%). The Midtown streets fell most: 57th Street from 21.0 to 7.3 a year. If Midtown lost more pedestrians and vehicles in 2020 to 2022 than the area around 14th Street, the comparison streets' fall is exaggerated and the ratio is biased upward, toward the refutation. The outcome says this. The open data give no pedestrian or vehicle volumes by corridor to measure the size of the bias.

Two further checks bear on it. First, 14th Street was already rising relative to the comparison streets before the busway. With false breaks in October 2016 and October 2017, the same estimator gives 1.16 (0.79 to 1.72) and 1.15 (0.78 to 1.71). Second, the ratio does not fall as the pandemic recedes: from July 2021 to September 2022 it is 1.41 (0.84 to 2.36), and from January to September 2022 it is 1.39 (0.71 to 2.74). Against 23rd Street, the comparison street least affected by the loss of office workers, the ratio is 1.04 and its lower bound (0.63) is below 0.65, so refute_if would not be met for that comparison alone.

For the true ratio to be 0.65 or less, the pandemic would have had to lower crash exposure on the comparison streets about twice as much as on 14th Street (1.32 / 0.65 = 2.0), or 1.8 times after allowing for the trend before the busway. That is possible for 57th Street but large for the pooled comparison. I consider the refutation of a one-third fall reasonably secure for the pooled comparison and not secure against 23rd Street alone.

## Problems

1. The test cannot separate the busway from the pandemic. This is the most important problem, but it biases the ratio toward refutation by an amount that would have to be about twofold to reverse the verdict, which is unlikely for the pooled comparison.
2. 14th Street was rising relative to the comparison streets before the busway (false-break ratios 1.15 and 1.16). The outcome does not report this.
3. The share of 14th Street crashes recorded under an avenue name rose after the busway. The registered coordinate method counts them; a name-based count would not, and gives 0.83.
4. Crash counts do not measure risk per pedestrian. Pedestrian volumes on 14th Street probably rose after the busway, as the registration says, which would hide a fall in risk.

## Does docs/street_space.md claim more than the numbers support?

It does slightly. The Pedestrians paragraph reports the numbers correctly and states the pandemic confound in the right direction. Its claim that "the pandemic emptied Midtown more than the residential streets around 14th Street" is plausible but is not measured in the note. The closing sentence of the tradeoff section, "A safety benefit should not be promised from removing through traffic alone; on 14th Street it did not appear in three years of crash records", is fair as a statement that no benefit was detected. It should not be read as evidence of no benefit: against 23rd Street the interval runs from 0.63 to 1.73, which includes a fall of a third. "The safety side shows no measurable gain" is accurate.

## Recommendation

Keep `contested`. The number reproduces, refute_if is met under every buffer width, and the main confound biases toward the result by less than would be needed to reverse it. Add to the notes the false-break ratios (1.16 and 1.15), the 2022-only ratio (1.39), the rise in crashes recorded under avenue names on 14th Street (97% to 74% naming 14th Street), and that refute_if is not met against 23rd Street alone. In the docs, describe the safety result as "no fall detected", not as "did not appear".
