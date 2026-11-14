# Referee report: further-datacentre-share-manhattan-v2

Verdict recorded: confirmed. Recommendation: keep the verdict, with the reservations in (a) and (c).

The referee read the registration, the outcome, `analyses/round2/datacentre_v2/analysis.py`, `data/derived/round2/datacentre_v2/results.json` and the cached Local Law 84 file `data/derived/further/ll84_mn_bx.csv`. The registrant's write-ups in `docs/` were not read. The re-analysis is in the scratch folder `referee-further-datacentre-share-manhattan-v2/dc_reest.py`.

## (a) Does the verdict follow from the registered conditions?

Yes, by the registered rule that point estimates decide. All four support conditions are met: the high figure is 2.26 percent of D1 and 2.41 percent of D2, both below 4.4; the low figure is 1.011 percent of D1, inside 1.0 to 1.3; the high figure is inside 1.8 to 3.5; and the listed buildings' excess (1.70 percent of D1) is above the placebo's 97.5th percentile (0.21). No measure chosen after the data decided anything.

The order of events is correct. The registration was committed at 23:40:54 on 12 November 2026 and the branch `prereg/further-datacentre-share-manhattan-v2` exists on GitHub with a commit at 23:40:56 that contains only the registration. The one new query (Utility Energy Registry totals) was written at 23:41:05, the results at 23:41:50, and the outcome was decided at 23:42:42. The Local Law 84 file was fetched at 20:26:27 for the first claim. The analysis script was created 56 seconds after the registration, so it was composed before or while registering; the file times show no run before the registration.

The test was weak, and the registration says so. The registrant had seen the first run's totals: reported IT energy at 0.83 percent of D1 and the listed buildings' whole-building electricity at 2.23 percent. The low figure before the cap is 0.83 times 1.4 = 1.16, the centre of the registered range 1.0 to 1.3. The high figure was bounded between 1.66 and 3.9 before any new number was read, and the registered range is 1.8 to 3.5. Only the effect of the cap and the size of the excess over the office median were unseen.

Condition (b) passes by 0.011 percentage points. The bootstrap interval for the low figure is 0.96 to 1.06 and includes the limit. A PUE of 1.3 in place of 1.4 gives 0.98 and fails (b).

## (b) Errors in code, units, joins, dates, geography or uncertainty

I reproduced every primary number: D1 17.064 TWh over 10,647 rows, median office intensity 9.64 kWh per square foot over 538 offices, low figure 1.011 percent, high figure 2.262 percent, excess 1.695 percent. The units are correct: `electricity_use_grid_purchase_1` is kWh and `data_center_it_site_energy` is kWh in the dataset's column metadata.

D1 counts campuses twice. Of the 10,647 rows, 1,153 belong to a parent property: 468 parent rows (2.16 TWh) and 685 child rows (1.68 TWh). The registered D1 sums both. Variants not run by the registrant:

| Variant | Low figure, % | High figure, % |
|---|---|---|
| Registered D1 | 1.01 | 2.26 |
| D1 without child rows (15.39 TWh) | 1.12 | 2.51 |
| D1 without parent rows (14.90 TWh) | 1.16 | 2.59 |
| Baseline: 75th percentile office (12.0 kWh/ft2) | 1.01 | 2.16 |
| Baseline: 90th percentile office (15.9 kWh/ft2) | 1.01 | 2.02 |
| Adding whole-building electricity of the 15 other rows whose largest use type is "Data Center" (99 GWh) | 1.01 | 2.84 |
| Without the largest contributor to each figure | 0.51 | 1.64 |

All four conditions remain met in the first six variants, and removing the double counting moves the low figure away from the edge of its range. The last row shows the concentration: the Western Union Building supplies 86 of the 173 GWh in the low figure, and 111 Eighth Avenue supplies 107 of the 289 GWh of excess. Each condition (b) and (c) rests on one building's report.

The join for 60 Hudson Street is correct. The outcome says the lot "again joins to 56 Hudson Street" as if that were a mismatch. The row is named "Western Union Building", its largest use type is "Data Center", and 56 Hudson Street is another address of the same block-filling building.

33 Whitehall Street appears twice (two property records on one lot with the same floor area and almost the same electricity, 5.38 GWh each). Both rows are in D1 and in the excess. The effect is 1.5 GWh of excess and is immaterial.

The high figure omits buildings that the owners themselves classify as data centres. Seventeen Manhattan rows have largest use type "Data Center"; only two (Western Union Building and 5120 Broadway) enter the estimate. The other fifteen, mostly Verizon central offices, hold 99 GWh. The high figure is therefore not an upper figure, as the plan calls it. With them the share is 2.84 percent, still inside the registered range.

The bootstrap interval (2.15 to 2.38) resamples only the buildings outside the numerator. It measures nothing about the uncertainty that matters, which is reporting error and tenant metering, and the stance z of 36 has no meaning. The outcome's note says the interval excludes these.

## (c) Is the comparison with the published figure fair?

No, and the registration lists the reasons as alternatives. The 4.4 percent is a 2023 national figure from a bottom-up model of server stock, over all US electricity including industry. The Manhattan figure is a 2024 allocation from landlord-reported whole-building electricity, over the electricity of large buildings in one borough. Landlord reports omit tenant meters, and carrier-hotel tenants commonly hold their own Con Edison accounts. The outcome's reverse bound says the unreported load would have to be 1.9 times the allocated load for the share to reach 4.4 percent. That is not a large factor for tenant-metered colocation, so the data do not show that Manhattan's true data-centre share is below the national one. They show that the share visible in Local Law 84 is. I read the LBNL sentence as quoted in the registration and did not re-open the source. No graph finding is cited, so there is no PubMed abstract to check.

## (d) Alternative explanation not addressed

Tenant metering is named and is not addressed; it is the main reason the result cannot be read as a measurement. Two further points are not named. First, the excess estimator counts any intensity above the office median as data-centre load. The listed buildings at 13 to 17 kWh per square foot (33 Whitehall, 75 Broad, 32 Old Slip, 150 Varick) sit at the 83rd to 92nd percentile of ordinary offices and are not distinguishable from them, and 111 Eighth Avenue is largely a corporate office. Second, the placebo for condition (d) cannot fail in practice. It draws ordinary offices and measures their excess over their own median, so the draws are near zero by construction, while the listed set was chosen for being carrier hotels. The outcome says this.

## (e) Could the test have failed?

Condition (a) could not: the registrant put its probability of failing at 0.03 and the seen numbers bound the high figure at 3.9. Conditions (b) and (c) could have failed and (b) nearly did, by 0.011 points, about 0.4 of the bootstrap standard error (0.026). This is not an endpoint or transfer test, so z against a prediction and against no effect do not apply in the usual sense. For the record, the high figure is 2.14 points below 4.4, and the low figure is 0.15 points below the 1.16 that the seen numbers implied, because the cap binds at the Western Union Building.

Recommendation: keep. The registered conditions are met and stay met when the double-counted campus rows are removed and when the omitted "Data Center" buildings are added, but condition (b) passes by 0.01 points and the result describes landlord-reported electricity, not metered data-centre load.
