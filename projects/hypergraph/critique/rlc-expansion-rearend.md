# Referee report: rlc-expansion-rearend

Verdict recorded: confirmed (rule 1), with the placebo year reported in the notes. The referee rebuilt the deciding ratio of ratios with separate code that does not import `analyses/street_safety/` or `concord/`. The scratch code is outside the repository, in the session scratchpad folder `ref/` (`fetch.py`, `coding.py`, `est.py`, `diag.py`, `tickets_daily.py`, `misdate.py`). I read `docs/street_safety.md` only after the re-estimate below was finished.

## Order of registration and data

The analysis script `rlc_did.py`, the site lists, the power check and the seed were committed in 793cc32 at 12:39:13 on 13 November. The registration was committed in 3e74706 at 12:39:17, and 793cc32 is its ancestor. The branch `origin/prereg/rlc-expansion-rearend` exists. `rlc_did.py` has not changed since 793cc32. It contains no outcome numbers; the only crash rates in that commit are the assumed rates in `power.json`.

The crash cache in `data/cache/socrata/` holds four queries made before the registration, at 12:18:40 to 12:19:13. All are citywide aggregates for June 2024 (counts by point of impact and pre-crash action, the count of rear-struck collisions, and the count citing 'Following Too Closely'). They fed the power assumptions and contain no site-level data. The first site-level crash pages were fetched at 12:43:28, after the registration. The outcome was decided at 13:11:25 and committed in c00c09c at 13:12:23. The order is as the registration states.

## Re-estimate

Data, fetched by the referee at 13:14 on 13 November 2026:

- Motor Vehicle Collisions - Crashes, `h9gi-nx95`, rowsUpdatedAt 2026-11-13T14:30:16Z (the registrant used the version of 2026-11-12T14:31:25Z), crashes from January 2022 to October 2026 with coordinates, 416,766 rows.
- Motor Vehicle Collisions - Vehicles, `bm4k-52h4`, rowsUpdatedAt 2026-11-13T15:33:26Z, every vehicle with point of impact 'Center Back End', 96,904 rows. The caller's brief named the vehicles table `bk4m-6pyy`; that id does not exist on NYC Open Data, and `bm4k-52h4` is the table the registration names.
- Camera intersections: the registrant's `data/derived/street_safety/rlc_sites_geo.json`, built from Parking Violations Issued `8zf9-spf8`, `m5vz-tzqv` (rowsUpdatedAt 2026-03-12T16:35:39Z), `9mwx-gamw` (2026-08-18T22:28:35Z) and `pvqr-7yc4` (2026-10-15T14:03:32Z), violation code 7. Control pool: `lpi_gazetteer.json` from `xc4v-ntf4`.

I merged approaches within 60 m, kept intersections first ticketed January to August 2026, built the pool (LPI before 2024, more than 300 m from any located camera), assigned crashes within 50 m and matched three controls per site on the pre-window count of all crashes, as the registration specifies.

| Version | Rear-end proxy, ratio of ratios (95% interval) | Placebo year |
|---|---|---|
| Registrant (outcome) | 1.327 (1.061-1.650) | 1.250 (1.052-1.488) |
| Referee, registered design | 1.327 (1.061-1.650) | 1.250 (1.052-1.488) |

The counts agree: 283 treated intersections and a pool of 4,590. The number reproduces exactly, including the bootstrap bounds. The one-day difference in crash table versions changed nothing at these sites. Rule 8 gives D = 6.50 against the band centre 1.33. Rule 9 is satisfied: the registrant's lower bounds with 20,000 draws and seeds 1 to 10 are 1.067 to 1.073.

## Activation dates and locations

The registered activation month is the first month in which an intersection had a ticket on the 1st or 15th. I read every day from 1 June 2025 to 31 August 2026 (code 7 tickets grouped by approach text, the three fiscal-year tables, 641 queries) and matched the approach strings to the treated sites.

| Daily first ticket against the registered month | Sites |
|---|---|
| Same month | 134 |
| One month earlier | 126 |
| Two months earlier | 15 |
| Three months earlier | 7 |
| Seven months earlier | 1 |

The sampling therefore dates activation late at 149 of 283 sites (53%). It never dates it early. Because the design drops the activation month and starts the post window a month later, a late date only shortens the post window and discards a month with cameras running; the post window still contains only camera months. For the 23 sites misdated by two or more months, some camera months fall between the true and recorded activation and are excluded, which costs data but adds no bias of note. One site is a real error: Neptune Avenue at Shell Road (Brooklyn), recorded as April 2026, issued a ticket on 12 September 2025, so its 2025 pre window includes camera months. One site among 283 cannot move the estimate.

Location is accurate where it can be checked. Of the treated sites, 110 also appear by name in the LPI table; the OSM and LPI points differ by a median of 1 m and none by more than 50 m. No treated name pair matched OSM nodes more than 100 m apart. The weaker point is the 117 of 585 camera names that were never located, 68 of them from the 2026 expansion. They are missing from the treated set and from the 300 m exclusion. With a looser name match I found 14 of them in the LPI table, and one became a matched control: Flatlands Avenue at East 59th Street, a camera from January 2026. The contamination is small, but the 19% of new sites left out are not a random subset: they are the names with abbreviations or run-together words ("E103RD ST", "NEWDORP LN").

## The placebo and regression to the mean

The bias is in the controls, and the data show it directly. Per site, in the registered design:

| Arm | All crashes, pre (mean of 2 years) | Post | Post / pre |
|---|---|---|---|
| Camera sites | 4.70 | 4.34 | 0.92 |
| Matched controls | 4.13 | 3.23 | 0.78 |
| All pool intersections, same borough (no matching) | 1.88 | 1.86 | 0.99 |

The camera sites have about 2.5 times the crashes of a typical LPI intersection. Controls chosen to match them on noisy pre-window counts are intersections whose counts were high by chance in those same windows, and their counts then fall by 22% while the pool as a whole is flat. This is regression to the mean in the control arm, created by matching on the outcome in the pre window. It produces the placebo ratios of 1.25 to 1.30.

Two comparisons that do not select controls on the pre-window counts remove most of the bias. Both were chosen by me after seeing the data, so under rule 4 they decide nothing.

| Comparison (exploratory) | Rear-end proxy | Placebo year | All crashes |
|---|---|---|---|
| Registered: matched on pre-window counts | 1.327 (1.061-1.650) | 1.250 (1.052-1.488) | 1.181 (1.081-1.289) |
| All pool intersections of the borough | 1.028 (0.853-1.227) | 1.056 (0.907-1.213) | 0.932 (0.866-1.001) |
| Matched on the same months three years earlier (2023; 2022 for the placebo) | 1.054 (0.855-1.305) | 0.982 (0.806-1.198) | 0.964 (0.883-1.053) |

With either comparison the placebo sits near 1.0, which is what a valid design should give, and the rear-end ratio falls to about 1.03 to 1.05 with intervals that include 1.00. The registered estimate of 1.33 is almost entirely the bias. The registrant's own post hoc adjustment (2026 estimate over placebo, 1.06, 0.80 to 1.40) agrees.

## Does the verdict follow under the rules?

Under the letter of the rules, yes. support_if requires the lower bound above 1.00 and D of at least 4. Both are met under every seed, and rule 4 prevents the placebo, or any adjustment chosen afterwards, from deciding.

Rule 8 is met only formally. Its purpose, stated with it, is that the test must tell the predicted effect from no effect. Its "no effect" is a ratio of 1.00, but the registered placebo shows that this design returns about 1.25 when there is no camera. Applied to the placebo year itself, the registered conditions are met: the lower bound is 1.052 and D = 5.8. A design that confirms the claim in a year without cameras cannot discriminate the claim from no effect. Measured against the placebo as the null (difference of logs, standard errors combined), z_null is 0.42 and D is -2.3, well short of 4.

My recommendation is that the verdict should not stand as `confirmed`. The registration named regression to the mean as an alternative and registered the placebo as the check on it, before the data. The check failed by the full size of the predicted effect. I recommend a precedence rule, added now and stated as added after the data as rules 9 and 10 were, that a registered placebo meeting the claim's own support_if voids that support and gives `unsettled` under rule 2. If the rules are not amended, the outcome should keep `confirmed` but its stance should not be counted as agreement with the meta-analyses in any summary, and the dashboard should show the placebo beside it.

## The rear-end proxy

The proxy is a crash in which any vehicle's contributing factor is 'Following Too Closely', or in which a vehicle with point of impact 'Center Back End' was 'Going Straight Ahead', 'Stopped in Traffic', 'Slowing or Stopping' or 'Starting in Traffic'. Parked and backing vehicles are excluded.

The factor coding changed in April and May 2025, not in 2026. Citywide, 'Unspecified' as the first vehicle's factor fell from 25% of crashes to 0%, and a new value, 'Does Not Apply', took 63% of first factors in 2026. 'Following Too Closely' as the first factor fell from about 6% to 1.5% of crashes from May 2025. Counted over all five vehicle slots, as the proxy does, it changed much less: 5,306 crashes in 2024, 5,366 in 2025 and 4,149 in January to October 2026. The vehicle table added a pre-crash value 'Unknown' in 2026 (568 rear-struck vehicles), which the proxy excludes; this removes about 4% of the vehicle component in 2026 at all sites alike. The overlap of the two components fell from 2,809 crashes in 2024 to 1,919 in ten months of 2026.

These changes fall in both arms and in both pre years, so they cancel in the ratio if they act proportionally. They do not change the result: the vehicle component alone gives 1.364 (1.066-1.723), the factor component alone 1.186 (0.871-1.630), and the pre window restricted to 2024 (before the change) gives 1.292 against 1.361 for 2025 alone. Analysts who use the first factor only, or 'Unspecified' as a category, should know that a series break in May 2025 exists.

## Does docs/street_safety.md claim more than the numbers support?

The tables and the explanation of the placebo are accurate. The note is clear that the confirmation does not show that cameras raised rear-end crashes. Two statements go further than the numbers.

- "The rear-end result therefore contradicts NYC DOT's report of a 60% fall in rear-end injury crashes at camera sites." The DOT figure is for rear-end injury crashes at the older camera intersections against a pre-installation average with no controls. This test counts all rear-end proxy crashes, most without injury, at the new sites, with a design biased upward by about 25%. The two numbers measure different things at different sites. What the data support is narrower: in the first four to nine months, none of the comparisons, biased or not, shows anything near a 60% fall in rear-end crashes at the new sites (the lowest lower bound is 0.85, against DOT's 0.40). That is a disagreement with DOT's figure applied to the new sites, not a contradiction of DOT's own measurement.
- The outcome's `prediction_scored` calls the result "a hit on the registered condition, weak as evidence of a camera effect". Given the placebo, it is no evidence of a camera effect, and "weak" understates the problem.

The "Flatbush Avenue" section repeats from the literature that red-light cameras "probably increase rear-end crashes". The city data here do not support that for New York's 2026 sites; the unbiased comparisons give about +3% to +5% with intervals from -15% to +30%.

## Recommendation

1. Change the verdict to `unsettled` by a precedence rule on failed registered placebos, stated as added after the data. If no rule is added, keep `confirmed` with the placebo shown beside it wherever the verdict appears.
2. Add to the notes: activation is dated late at 149 of 283 sites (never early), which shortens post windows and does not bias them; one site (Neptune Avenue at Shell Road) was ticketed in September 2025; 68 new sites are unlocated and one of them is a matched control; the contributing-factor coding break of May 2025.
3. Revise the DOT sentence in the note and in the claim's framing as above.
4. Register a successor before more post data arrive: controls not selected on pre-window counts (the whole LPI pool by borough, or matching on a period outside the pre window, or not-yet-treated camera sites), daily activation dates, and the placebo as a registered validity condition.
