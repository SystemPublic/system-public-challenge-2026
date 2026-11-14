# Referee report: bridge-crz-injury-crashes-v2

Verdict recorded: unsettled. Recommendation: keep the verdict.

Scratch work is in the session scratchpad under `referee-bridge-crz-injury-crashes-v2/` (`reest.py`, `var2.py`, `recover.py`). All numbers below come from the cached Q1 rows (60,416 rows, fetched 12 November 19:35:11) except the recovery of records without coordinates, which uses one new query to h9gi-nx95 made on 13 November at 00:52 (11,858 injury crashes without coordinates, 2022-2025).

## (a) Does the verdict follow from the registered conditions?

Yes. The registration says the verdict is unsettled when the 2024 placebo interval excludes zero. The placebo is +15.2% (+4.8 to +26.6), so the rule returns unsettled whatever the 2025 estimate is. The primary estimate also fails the other conditions: D is -0.11 at B0, and the three deciding points give unsettled, contested above and unsettled. No measure chosen after the data decides anything. The remark about the July to October 2024 dip in coverage is labelled exploratory.

The timestamps are in order. The registration was committed in `ce3586a` at 19:31:56 on 12 November, together with `compose_v2.py` and `composed_predictions_v2.json`. The crash rows were fetched at 19:35:11, the coverage tables at 19:35:36 and 19:35:40, and the outcome was decided at 19:37:23 and committed at 19:38:07. The stored hash of the registration matches its content. There is no branch `prereg/bridge-crz-injury-crashes-v2` on GitHub; `git ls-remote` returns nothing for it. The registration is on `origin/main`, and the outcome says it was pushed at about 00:32 UTC, but the push time cannot be checked from the repository, and the next commit (`d31e769`) records that push times were not refreshed. The order of commit and fetch times is consistent with registration before data. The proof that it was public before the query is weaker than for claims with a prereg branch.

The analysis script `crz_crashes_v2.py` was first committed with the outcome, after the data. I read it against the plan and found no departure: the areas, the model, the bias formulas and the decision rule are as registered.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I reproduced the deciding numbers exactly: +4.49% (-2.70 to +12.21), se 0.0364 on the log scale, placebo +15.2% (+4.8 to +26.6), annual counts 2,581/2,955, 2,710/3,181, 2,763/2,795 and 2,726/2,891. A regression on the monthly log ratio of zone to north with Newey-West errors gives the same point estimate and nearly the same interval (-2.4 to +11.9), so stacking the two areas in one HAC regression does no harm.

I found three problems, none of which changes the verdict.

First, the two areas are not the same kind of road network. The zone is the largest geofence polygon, which leaves out the FDR Drive and the West Side Highway. The north area takes every Manhattan point north of 60th Street, including the Henry Hudson Parkway, the FDR Drive, the Harlem River Drive and the bridge approaches. By street name, 357 to 397 of the north area's injury crashes a year are on these roads (12 to 14 percent), against 3 to 6 in the zone. Without them the estimate is +6.1% (-0.8 to +13.5) and the placebo +16.4% (+5.6 to +28.2).

Second, the way crashes are recorded changed, and it changed differently in the two areas. In 2022 and 2023 about 750 north-area injury crashes a year on ordinary streets carried an on-street name only (the registration's class "other"), against 300 to 375 in the zone. In 2025 such records are gone from both areas (Broadway in the north area: 67, 86, 29, 0). In 2024 the north area lost 424 of these records and gained only 85 intersection records, while the zone lost 121 and gained 216. The 2024 placebo difference sits in this class. The registered stable-class restriction was correctly not run, and it could not have helped: restricting to intersection and address records gives -9.9% (-14.6 to -4.9), which is produced by records moving between classes, not by crashes.

Third, the estimate depends on which pre-period years are used. Against 2024 alone it is -4.9% (-10.6 to +1.1). Against 2022-2023 alone it is +9.5% (+5.7 to +13.5). With a linear trend in the log ratio it is -8.2% (-17.3 to +1.9). A false start in January 2023 gives -2.4% (-10.0 to +5.8). The zone-to-north ratio stepped up in 2024 and partly returned in 2025, so the registered +4.5% is an average over two regimes.

The variant the registrant did not run is a direct recovery of records without coordinates. I matched the 11,858 injury crashes without coordinates to geocoded crashes with the same pair of street names, or the same address, and assigned them to the area where the geocoded matches fall. This recovers 64, 24, 37 and 3 zone crashes and 52, 31, 16 and 2 north crashes for 2022 to 2025. With them added the estimate is +4.1% (-3.2 to +12.0), z_chain 1.18, z_null 1.09, and the placebo is +15.7% (+5.7 to +26.8). Allocating on-street-only records in proportion to geocoded records of the same street name (an overstatement, since names such as Broadway occur in other boroughs) adds 153, 138 and 249 north crashes in 2022 to 2024 and gives +8.8% (+2.3 to +15.7), z_chain 2.15, with a placebo of +13.6% (+6.2 to +21.6). The match covers only 12 to 16 percent of intersection records without coordinates, because the lookup contains Manhattan and its edges only. Within that limit, missing coordinates do not explain the 2024 divergence, and the registered bias bounds (-2.0% to +11.6%) are not narrowed much.

## (c) Is the comparison with the research fair?

Only loosely, and the registration says so. The speed link is the MTA's CBD against CBD Adjacent, whose boundary is unpublished, and the volume link has no comparison area. The endpoint's comparison area includes limited-access highways that neither link describes. The exponents come from Elvik's power model, which is not in the graph.

I checked the three graph findings against PubMed. The numbers are right in all three: IRR 1.27 (1.13 to 1.44) for higher speed roads in PMID 26759927, OR 2.02 (1.73 to 2.36) for speeds above 20 mph in PMID 21399547, and adjusted OR 0.52 (0.29 to 0.92) for motor vehicle speeds below 30 km/h in PMID 23411678. The attribution of the third is wrong. PMID 23411678 is Harris et al., Injury Prevention 2013;19:303-310, not Teschke et al. 2012, and the odds ratio applies to intersections only. None of the three measures a change in injury crashes when mean network speed changes by 4 percent, so they support the sign of the speed term and nothing about its size.

## (d) Alternative explanation not addressed

The change in how crash locations are recorded, described under (b), is not among the registered alternatives. The registration treats geocoding as a matter of coverage. The data show a change of record format as well, and it bears on the two areas unequally. The 2024 fall in the north area (3,181 to 2,795) is listed under research needed, which is right. The highway asymmetry between the two areas is not mentioned.

## (e) Could the test have failed?

It could have returned contested, but only at extreme values, and it could not have returned bridged. At the observed standard error, the bridged condition holds at one point only when the log estimate is between about -0.125 and -0.085, a window 0.04 wide. The registration requires it at B0, B_up and B_down together, and those three points are 0.13 apart on the log scale (the bias inputs were known before registration). No estimate satisfies all three. The power table in the registration gives the chance of bridged as 0.06 to 0.16 if the chain is true; with the bias-bound requirement it was zero. Contested required the primary estimate to be above about +15.6% or below about -17%. Unsettled was close to certain before the data.

At the primary estimate z against the composed prediction is 1.25 and z against no effect is 1.21 (D = -0.11). With the strict recovery of ungeocoded records they are 1.18 and 1.09. The endpoint does not separate the chain from no effect, and with a composed prediction of -2.2% and a standard error near 3.6 points it could not have done so.

Recommendation: keep. The registered rule returns unsettled, the numbers reproduce exactly, and every variant I ran (highways removed, ungeocoded records recovered, other pre-periods) leaves either the placebo above zero or the estimate dependent on the choice of pre-period.
