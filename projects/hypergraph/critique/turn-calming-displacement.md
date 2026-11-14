# Referee report: turn-calming-displacement

Verdict recorded: unsettled (rule 2). support_if requires the 95% interval of the ring ratio of ratios to lie within 0.88-1.12, and the lower bound was 0.876. refute_if (lower bound above 1.00) is not met. The design, data, order of registration and my separate code are the same as for `turn-calming-ped`. That report (`critique/turn-calming-ped.md`) covers the shared checks.

The outcome counts pedestrians injured or killed 50-200 m from each site, excluding crashes within 40 m of any calming record of any date.

## Re-estimate

| Ring 50-200 m | Registrant | Referee |
|---|---|---|
| Pedestrians, registered ratio of ratios (95% CI) | 0.9234 (0.8760-0.9734) | 0.9255 (0.8779-0.9756) |
| Site-cluster bootstrap interval | not run | 0.881-0.974 |
| Treated sites | 746 | 745 |
| Cohorts avoiding March-June 2020 | 0.964 (0.893-1.040) | 0.966 (0.895-1.042) |
| Placebo, installation 12 months early (exploratory) | 0.9346 (0.8768-0.9963) | 0.9365 (0.8785-0.9984) |
| Trend-adjusted (exploratory) | 1.0631 (0.9213-1.2268) | 1.0610 (0.9193-1.2246) |
| Secondary: left-turn crashes in the ring | 0.9449 (0.8985-0.9937) | 0.9450 (0.8985-0.9939) |
| Secondary, trend-adjusted (exploratory) | 1.0885 (0.9703-1.2210) | 1.0908 (0.9718-1.2242) |

The estimates agree to about 0.002. The small difference comes from my UTM projection against the registrant's equirectangular one, which moves a few crashes across the 50 m and 200 m edges. My Wald lower bound is 0.878 and my bootstrap lower bound is 0.881. support_if is therefore missed by 0.002 to 0.004 on the Wald bound and met by 0.001 on the bootstrap bound. In the sense of rule 10, the condition is missed within the variation of the procedure. The registration names the Wald interval, so rule 1 gives `unsettled`, and I agree with it.

## Why the verdict should stay unsettled even if the bound had passed

The ring has the same placebo problem as the sites. The placebo ratio for the ring (0.937) is almost the registered ratio (0.926). Against the placebo as the null, z is -0.28. Had support_if been met, the design would have confirmed "no displacement" with a ratio of 0.93 that it also produces where no calming exists. The trend-adjusted ring ratio is 1.06 (0.92-1.22) for pedestrians and 1.09 (0.97-1.22) for left-turn crashes. Displacement of about +20% to the adjacent intersections is therefore not excluded by these data, and neither is a spillover benefit.

## Geometry of the ring

- Crash coordinates are snapped to intersection nodes (see the pedestrian report). Crashes within 80 m of a site cluster at 0-5 m (the site's own node) and again at 60-80 m, where the 60-80 m band has 59,629 crashes against about 10,000 in each 10 m band from 30 to 60 m. In practice the ring therefore counts crashes coded to the neighbouring intersections, which suits a displacement test.
- The sites are close together. 46% of sites have another calming site within 200 m, and 20% within 100 m. DOT installs calming along corridors, so a treated site's ring usually contains other treated or later-treated intersections. Crashes within 40 m of those intersections are removed, but the blocks between them remain. The ring of one site can also overlap the ring of a control site in the same cohort. The ring outcome is therefore partly a corridor outcome, and the corridor trends are the trends the placebo picks up.
- The exclusion of crashes near any calming site, whatever its date, is reasonable. It keeps a later-treated neighbour's own effect out of the ring.

## Does docs/turn_restrictions.md claim more than the numbers support?

The note says: "There is no sign that injuries moved to the next intersection. The ring 50-200 m away fell as well (0.92)." This reads the ring's registered ratio at face value, while the same note argues, correctly, that the site-level ratios of the same design are biased downwards by about the size of the placebo. Read with the same correction, the ring gives 1.06 (0.92-1.22). The note should say that the design cannot detect displacement of the size that matters, because its own bias in the ring is about -7%. The statement that "the placebo for the ring (0.935) favours the artefact", in the outcome's notes, is accurate and should also appear in the note.

## Recommendation

1. Keep `unsettled`. State in `prediction_scored` that the lower bound missed by 0.004 (registrant) or 0.002 (referee) within the procedure's variation, as rule 10 asks. State also that a pass would not have been informative, given the ring placebo of 0.935.
2. Revise the note's displacement sentence as above.
3. In the successor design (pedestrian report, recommendation 3), define the ring by intersection nodes rather than by radius: the adjacent nodes on the cross street and the parallel streets, excluding nodes that DOT treated within the windows. Register a placebo for the ring as well. For left-turn bans, as opposed to calming, the ring should follow the detour routes, which need a dated list of bans that NYC Open Data does not hold.
