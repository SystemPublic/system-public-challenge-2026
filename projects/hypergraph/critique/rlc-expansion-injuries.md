# Referee report: rlc-expansion-injuries

Verdict recorded: unsettled (rule 2). The referee rebuilt the deciding ratio of ratios with separate code that does not import `analyses/street_safety/` or `concord/`. The scratch code is outside the repository, in the session scratchpad folder `ref/` (`fetch.py`, `est.py`, `diag.py`, `tickets_daily.py`, `misdate.py`). I read `docs/street_safety.md` only after the re-estimate was finished. The checks of order, activation dates, locations and proxy coding are shared with `critique/rlc-expansion-rearend.md` and are summarised here.

## Order of registration and data

The script, site lists, seed and power check were committed in 793cc32 (12:39:13, 13 November 2026), the registration in 3e74706 (12:39:17), and 793cc32 is its ancestor; `origin/prereg/rlc-expansion-injuries` exists. `rlc_did.py` is unchanged since then and holds no outcome numbers. The only crash data read before registration were four citywide aggregates for June 2024 used in the power check. Site-level crash pages were first fetched at 12:43:28. The outcome was decided at 13:11:25 and committed in c00c09c.

## Re-estimate

Data: `h9gi-nx95` (Motor Vehicle Collisions - Crashes, rowsUpdatedAt 2026-11-13T14:30:16Z; the registrant's version was 2026-11-12T14:31:25Z), January 2022 to October 2026, 416,766 geolocated rows; camera intersections from the registrant's `rlc_sites_geo.json` (Parking Violations Issued `8zf9-spf8`, `m5vz-tzqv`, `9mwx-gamw`, `pvqr-7yc4`, violation code 7); control pool from `lpi_gazetteer.json` (`xc4v-ntf4`). The outcome is persons injured plus persons killed within 50 m. The vehicles table `bm4k-52h4` is not used by this outcome. (The caller's brief named it `bk4m-6pyy`, which does not exist.)

| Version | Persons injured or killed, ratio of ratios (95% interval) | Placebo year |
|---|---|---|
| Registrant (outcome) | 1.038 (0.907-1.192) | 1.263 (1.100-1.445) |
| Referee, registered design | 1.038 (0.907-1.192) | 1.263 (1.100-1.445) |

The number reproduces exactly, with 283 treated sites and 4,590 pool intersections. Pedestrians injured or killed (secondary) also reproduces: 1.289 (1.029-1.637), placebo 1.357.

## Does the verdict follow?

Yes. support_if needs the upper bound below 1.00 and D of at least 4; the upper bound is 1.192 and D = -11.99. refute_if needs the lower bound above 0.95; it is 0.907. Neither is met, so rule 2 gives `unsettled`. The lower bound is not close to 0.95 under any seed the registrant reports (0.909 to 0.912), so rule 9 does not bear on it.

## Activation dates and locations

Daily ticket counts from 1 June 2025 to 31 August 2026 show that the 1st-and-15th sampling dates activation late at 149 of 283 sites (126 by one month, 22 by two or three months, one by seven months) and never early. Because the activation month is dropped, a late date shortens the post window but leaves only camera months in it. One site, Neptune Avenue at Shell Road, had a ticket on 12 September 2025, so its 2025 pre window includes camera months. Locations agree with the LPI table to a median of 1 m at the 110 treated sites found in both. 68 of the 363 new camera names were never located; one of these (Flatlands Avenue at East 59th Street) was picked as a matched control. None of this moves the estimate by an amount that matters.

The injury counts did not change their coding. Persons injured per geolocated crash were 0.560 in 2023, 0.590 in 2024, 0.586 in 2025 and 0.605 in January to October 2026. The contributing-factor break of May 2025 does not affect this outcome.

## The placebo and regression to the mean

For this claim the bias runs against the prediction. Controls matched on pre-window crash counts are intersections that were high by chance in those windows. Their counts then fall: in the registered design, persons injured at the controls fell to 0.82 of the pre level, while the whole LPI pool of the same boroughs stayed flat (all crashes 0.99). The placebo, with no cameras, gives 1.263. A design that adds about 25% to the ratio cannot detect a 5% to 30% reduction.

Two comparisons that do not select controls on pre-window counts, chosen by me after the data and therefore deciding nothing under rule 4, give a different picture:

| Comparison (exploratory) | Persons injured or killed | Placebo year | Pedestrians |
|---|---|---|---|
| Registered: matched on pre-window counts | 1.038 (0.907-1.192) | 1.263 (1.100-1.445) | 1.289 (1.029-1.637) |
| All pool intersections of the borough | 0.839 (0.750-0.934) | 1.009 (0.905-1.126) | 1.027 (0.837-1.263) |
| Matched on the same months three years earlier | 0.807 (0.702-0.921) | 0.982 (0.851-1.127) | 1.035 (0.817-1.320) |

In both, the placebo is close to 1.00 and the 2026 estimate is a reduction of about 16% to 19%, inside the registered band of 0.70 to 0.95. Had either been the registered design, support_if would have been met (upper bounds 0.934 and 0.921; D = 9.9 and 9.6). The registrant's own post hoc ratio to the placebo, 0.821 (0.672-0.993), agrees. Pedestrian injuries show no clear change in any comparison.

These comparisons are not free of other biases. The camera sites carry about 2.5 times the crashes of the average pool intersection, so the unmatched comparison assumes that busy and quiet intersections share a trend. The camera sites were chosen by DOT, perhaps after a run of crashes, which would itself produce a fall (regression to the mean in the treated arm, the bias the meta-analyses warn of). A fall of 16% to 19% is therefore an upper estimate of the camera effect.

## Does docs/street_safety.md claim more than the numbers support?

For this claim the note claims little beyond the numbers. It reports `unsettled` correctly and labels the placebo adjustment exploratory. The sentence "If this adjustment is right, the new cameras reduced injuries by about 18% without a clear rise in rear-end crashes" is conditional and labelled; my exploratory comparisons support the size of the figure but share its status. The note could say that the registered design was biased against this prediction, so `unsettled` here reflects the design and not the data. The Flatbush section says the city data "cannot yet measure the cameras' effect on pedestrians"; that is right, since pedestrian injuries are near 1.0 in every unbiased comparison with wide intervals.

## Recommendation

Keep `unsettled`. Add to the notes that the bias shown by the placebo works against the predicted reduction, that two comparisons not selected on pre-window counts give 0.84 (0.75-0.93) and 0.81 (0.70-0.92) with placebos near 1.00, and that these are exploratory under rule 4. Register a successor now, before more post data arrive, with controls not selected on pre-window counts (the whole borough LPI pool, matching on a period outside the pre window, or not-yet-treated camera sites), daily activation dates, a registered placebo condition, and an allowance for selection of the treated sites by DOT (empirical Bayes expected counts). This claim is the more promising of the two for a confirmation in that successor.
