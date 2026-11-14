# Referee report: bridge-crz-injury-crashes

Verdict recorded: bridged (first recorded as confirmed, relabelled under rule 7). Recommendation: needs re-analysis before the verdict stands. The endpoint must be re-estimated with a comparison that is not exposed to the 2025 change in geocoding, and the stance must be reported against a no-effect alternative as well as against the chain.

## (a) Was the composed prediction fixed before the endpoint was queried?

Yes. `compose.py` and `composed_predictions.json` were committed in `a4b6f1e` at 16:04:49 on 12 November, and the registration in `29033c7` at 16:04:50. The zone crash rows (`h9gi-nx95-434a…`, `-4c48…`) were fetched at 16:05:32 and 16:05:34, the citywide monthly totals at 16:05:42, and the missing-coordinate counts at 16:05:44 and 16:06:08. The geofence (`srxy-5nxn`) was fetched at 16:01, before registration, but it is not endpoint data.

One earlier crash query exists. `h9gi-nx95-298b…`, fetched at 15:31:58, holds citywide monthly crashes by day of week and time band from 2019, for mob-speedcam-247. It has no zone split, so it could not have shown the zone-versus-rest result. The registrant also states a recollection of 2025 reports that zone injuries fell. This was disclosed, and it pushed the directional bet the wrong way, so it did not help the result.

Rule 7 was added after the outcome was known. The outcome was decided at 16:10:34 and committed in `f024acb` at 16:11:46; rule 7 was committed in `3d8ac0d` at 16:12:16. The rule's text says "Added 13 Nov 2026", a day after the commit. The relabelling from confirmed to bridged does not change the substance, but the switch of stance from the weakest link (0.963) to endpoint agreement (0.903) is a scoring rule chosen after the data were seen. Under rule 4 of the same list, it should be marked as such.

## (b) Errors in composition, uncertainty, units, geography or endpoint model

The composition is algebraically correct: log RR = E·log(1+dS) + b·log(1+dV), with the terms reported. I found three problems.

First, the speed and volume changes are drawn independently. They are not independent: the speeds rose because volume fell. If the two are positively linked in magnitude (more relief gives both a larger speed rise and a larger volume fall), the two terms cancel more often and the composed interval is narrower than reported. The independent draw widens the prediction and lowers the power of the test.

Second, the baselines differ across links and endpoint. The speed link is 2025 against 2023-24, relative to Greater NYC. The volume change is the MTA vehicle-miles series against 2024 with no comparison area, mixed with TLC trips relative to outside the zone. The endpoint is 2025 against 2022-24, relative to the rest of the city. The composition treats these as one contrast.

Third, and most important, the endpoint is exposed to a change in geocoding that is of the same size as the effect being tested. From the cached counts (`h9gi-nx95-b14f…`), injury crashes without coordinates were 4,191 of 39,336 in 2022 (10.7 percent), 3,213 of 40,473 in 2023, 3,481 of 40,229 in 2024 (8.7 percent), and 973 of 37,426 in 2025 (2.6 percent). Geocoded injury crashes therefore rose by about 7 percent relative to all injury crashes in 2025. The design compares geocoded crashes inside the zone with geocoded crashes outside it. If the newly geocoded crashes fall in the zone and the rest in proportion, there is no bias. If they fall mostly outside the zone (most of the missing records in 2022-24 have no borough, and the borough field was filled in 2025), the zone-versus-rest estimate is biased downward by about 7 to 8 points. If the Manhattan-coded rise in missing coordinates (2.1 to 4.4 percent) also applies to the zone, the bias is about 10 points.

The outcome's correction of 2 to 3 points rests on one of these assumptions. Under the others, the corrected estimate is about +9 percent (z = 1.7) or about +11.5 percent (z = 2.1). The second value crosses the registered refutation threshold. The verdict depends on an assumption that was not registered and that the data at hand cannot settle.

The endpoint model uses calendar-month terms common to both areas. Seasonality in midtown and lower Manhattan may differ from the outer boroughs. An area-by-month interaction, as in the Poisson secondary, would be more appropriate. The Poisson result (+1.5 percent) suggests this does not matter much here.

## (c) Is the endpoint independent of the links?

Largely yes. The links use MTA and TLC speed, trip and vehicle-miles series, and the endpoint uses NYPD crash records. No event is counted in both. One shared element is the zone boundary itself, and a small one: crashes slow traffic, so crash counts and speeds are mildly linked by construction. This is minor at monthly resolution.

## (d) Is the test informative?

Weakly. With the composed mean log -0.0035 and combined SE 0.053, the test refutes only if the observed change is below -10.2 percent or above +10.6 percent. Any change between those values confirms the bridge.

A chain with no content, predicting exactly zero, would have passed with probability above 0.99 given the observed standard error of 0.031. Against the chain, the observed value gives z = 0.32. Against no effect at all it gives z = 0.43. The endpoint does not separate the composed chain from the hypothesis that pricing had no effect on injury crashes. The power to refute is about 0.5 against a true change of -10 percent and near 1 only beyond about -15 or +15 percent. The test does rule out a London-sized decline, as the outcome says, but that is a test of the London analogy, not of this chain.

The cause is that the two link terms cancel. The composed prediction is near zero, and the endpoint is near zero, so agreement carries little information. A stance of 0.903 on the dashboard overstates the support. I suggest reporting the endpoint's z against the chain and against zero side by side, or scaling the rule 7 stance by how far the composed prediction is from the null in units of the combined SE.

## (e) Alternative explanation not addressed

The registration names pre-trends, reporting changes, pedestrian exposure, spillover and other 2025 Manhattan changes. The one that is not addressed is the no-effect hypothesis itself, which the design cannot distinguish from the chain. Of the named alternatives, the geocoding change is addressed only with one favourable assumption.

The 2024 placebo is also weaker than it appears. Its interval (-5.4 to +14.0) is wider than the primary interval, and the all-crash and pedestrian-cyclist placebos are +5.4 and +7.1 percent. A pre-existing upward drift in the zone of a few points a year cannot be excluded, and with it the trend-adjusted 2025 effect would be negative.

## Recommendation

Needs re-analysis. Re-estimate the endpoint against Manhattan north of 60th Street, or against the CBD-adjacent area used in mob-crz-traffic. Both are in the same borough and share the geocoding regime. Also report the primary estimate restricted to months and records where coordinate coverage is stable, and the bias under each assumption about the missing records. If the verdict survives, keep bridged, but record that the endpoint test cannot separate the chain from no effect. The stance should reflect that.
