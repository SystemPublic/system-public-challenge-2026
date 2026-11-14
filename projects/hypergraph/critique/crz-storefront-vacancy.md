# Referee report: crz-storefront-vacancy

Verdict recorded: confirmed. Recommendation: keep the verdict, and change what the label says (wording at the end).

The re-estimates are in `analyses/critique/referee_crz.py` (`python -m analyses.critique.referee_crz vacancy`). It uses its own code on the cached rows of 92iy-9c3n and calls the registrant's `did` function once to check exact reproduction. One further query, for the address fields of reporting year 2025, was made in the session scratchpad to find out what the February filing is. I did not read `docs/congestion_tradeoffs.md` or any other write-up.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required a point estimate of at most +0.5 points and an upper bound below +1.2 on the comparison with all other city ZIPs. The estimate is -0.47 (-1.08 to +0.17). Nothing was decided by a measure chosen after the data.

The timestamps are in order, with little room. The registration, `vacancy.py`, `common.py` and the design file were committed on the branch `prereg/crz-storefront-vacancy` at 08:09:54 on 13 November. The rows for reporting year 2025 were fetched at 08:10:10 and the outcome was decided at 08:12:54. The registration hash matches its content, and the registration and the scripts on the branch are identical to those on `main`. The time the branch was pushed cannot be read from the repository. The registrant had seen row counts for 2025 by filing date before registering, and no vacancy values, as the registration states.

The registered statement says "a rise of 1.2 points is excluded". That sentence is true of one comparison and one source of error. Sections (b) and (e) give the cases in which it is not true.

## (b) Errors in code, units, joins, dates, geography or uncertainty

The deciding numbers reproduce. My code gives -0.47 (-1.06 to +0.16), and the registrant's function on my rows gives -0.4674 (-1.0809 to +0.1739), the recorded values. The secondary comparisons also reproduce: north -0.23 (-1.33 to +0.88), downtown Brooklyn and Long Island City +1.09 (-0.60 to +2.85), rest of the city -0.56 (-1.18 to +0.08). Zone vacancy was 1,859 of 15,083 on 31 December 2024 and 1,931 of 15,442 a year later. Outside it was 3,529 of 47,045 and 3,971 of 48,733.

The registry's reporting did not change between the two deciding years. Reporting years 2023, 2024 and 2025 each have the same three filings: a main filing due in June (62,923, 62,128 and 64,175 rows), a February filing in which every row is vacant (2,496, 2,320 and 2,284 rows), and an August filing about vacancy on 30 June. The February filing is about the same size in the zone in both years (971 and 922 rows). The 2024 February filing codes vacancy as "Y" and the others as "YES", which does not matter because the registered analysis drops that filing.

The reporting did change one year earlier, and this affects the pre-trend. Up to reporting year "2022 and 2023" there was a single filing due in August. From reporting year 2023 there is the June filing and the separate all-vacant February filing. The coding of `primary_business_activity` changed at the same point (food services falls from 13,665 rows to 30, educational services rises from 937 to 20,473), so the registry was restructured, not only rescheduled. The registered pre-toll difference for 2023, -1.40, compares a filing made under the old structure with one made under the new. If the February rows are added to the June rows, the 2023 difference is +1.14 and not -1.40. I could not settle which treatment is right. In reporting year 2025, 44 percent of February rows match a vacant June row on tax lot and address, and 53 percent match some June row, so the February filing partly duplicates the June filing and partly adds to it. The practical consequence is that only one clean pre-toll difference exists under the present filing structure, the one for 2024 (-0.45), and the registration's "expectation without any toll effect of about -0.5" rests on that single year. The figure of three earlier years with mean -0.86 should not be used.

Coverage also changed earlier. Between the filings for 31 December 2020 and 2021 the registry lost 18 percent of its rows outside the zone (58,575 to 48,013) and 9 percent inside (16,965 to 15,443). The registration notes the fall in the zone but not that it was twice as large outside.

Variants the registrant did not run, all for 2025 against 2024 and all other ZIPs:

- February filing added to the main filing: -0.76 (-1.70 to +0.16). The zone then falls by 0.19 points and the outside rises by 0.57.
- Tax lots present in the main filing of both years (88 percent of rows): -0.36 (-0.95 to +0.25).
- Bootstrap over ZIP codes in place of tax lots: -0.47 (-1.19 to +0.24). Vacancy is correlated within neighbourhoods, so this is the more defensible interval. It changes little.
- Without Roosevelt Island: -0.46. ZIP 10044 is in the zone list in `common.py` (through the range 10041 to 10048) and is not in the toll zone. It has about 25 storefronts a year.

All four leave the registered conditions met. Within the zone the change is uneven: among ZIPs with 300 or more storefronts it runs from -4.0 points (10038) to +2.1 (10036) and +1.9 (10022).

The uncertainty is understated in one respect. The interval covers sampling of tax lots only. The registration itself says the difference moves from year to year with a standard deviation of about 0.5 points, and the plan's power calculation uses 0.6, but the support condition does not. Adding the year-to-year standard deviation (0.48, from the three registered pre-toll values) to the bootstrap error gives an upper bound of +0.67 against zero. Measured against the mean of 2022 to 2024, the registrant's "trend-adjusted figure", the 2025 value is +0.39 with a standard error of 0.64 and an upper bound of +1.66, which does not exclude 1.2. With three pre-toll values, one of them across a reporting change, that standard deviation is itself poorly known.

## (c) Is the comparison with the research fair?

There is no research comparison. The graph holds nothing on the link, and the outcome correctly leaves `graph_effect` empty. The two literature entries are about retail sales in London and Stockholm, not vacancy, and both are cited from memory. Neither supplies the figure of 1.2 points. The plan shows where the figure comes from: it is the size of effect at which the registered test reaches a discrimination of about 4. The threshold is therefore the resolution of the test, chosen from the design run, and not an effect size taken from prior work. That is a legitimate way to set it, and it was set before the 2025 values were seen. It should be described that way. As written, the registration reads as if the threshold had a basis in the retail literature. The two citations should be checked against the papers before they appear anywhere, or be removed, since nothing in the test depends on them.

A rise of 1.2 points is about 180 more vacant storefronts in the zone, a tenth more than at the end of 2024. Excluding it is a weak statement about harm to business. A loss of sales, a fall in rents, or a turnover of tenants with no net change in vacancy would all leave this measure unchanged.

## (d) Alternative explanation not addressed

The comparison area decides the answer and the registration does not justify the pooled one. The pooled comparison is 47,000 storefronts, mostly on neighbourhood streets in the other boroughs, where vacancy rose by 0.65 points in 2025. The zone's vacancy also rose, by 0.18 points. The negative difference therefore comes from a rise elsewhere and not from an improvement in the zone. In the two comparison areas that resemble the zone, vacancy rose less or fell: +0.41 points in Manhattan from 60th to 110th Street and -0.91 in downtown Brooklyn and Long Island City. Against those two business districts the zone did worse by 1.09 points, with an interval (-0.60 to +2.85) that includes both zero and twice the threshold. That area has four ZIPs and about 2,100 storefronts, so it cannot carry a conclusion either. The data do not say which comparison is right.

Lease length is listed as a limit and is the main one. Commercial leases commonly run five to ten years, so the stock of storefronts whose lease came up in 2025 is a small part of the total, and an effect of the toll on decisions to renew would appear over several years. One filing after the toll cannot distinguish no effect from a delayed one.

Owners report their own vacancy, and the number of rows in the main filing rose by 2.4 percent in the zone and 3.6 percent outside between the two years. The lots that filed in only one of the two years have higher vacancy than the rest (13 to 15 percent in the zone, 10 to 11 percent outside). The balanced-lot variant shows this does not drive the result.

## (e) Could the test have failed?

Only for a large effect. The registration's own calculation gives a rise of 1.2 points about an even chance of meeting the refutation condition, and says that a smaller rise cannot be told from the trend. Support was the expected result under no effect: the registered prior was 0.6, the stated no-toll expectation was -0.5 and the estimate is -0.47. Against a rise of 1.2 points on top of that expectation (an estimate near +0.7), the estimate is 3.6 bootstrap standard errors away, and 2.0 when the year-to-year movement is added. Against no relative change it is 1.5 bootstrap standard errors below zero, and 0.8 with the year-to-year movement added.

## Does "confirmed" overstate?

The verdict follows from the registered rule, so it stands under PRECEDENCE rule 1. The word overstates what was found if it is read as "the toll did not raise vacancy". What was found is narrower: in the first year, vacancy in the zone rose by 0.2 points, vacancy in the rest of the city rose by 0.65 points, and a rise in the zone of 1.2 points or more relative to the rest of the city is excluded when only sampling error is counted. It is not excluded relative to the zone's own earlier trend (upper bound +1.66), and it is not excluded relative to downtown Brooklyn and Long Island City (upper bound +2.85).

The label should say: "Confirmed on the registered comparison only. Zone vacancy rose 0.2 points in the first year and vacancy in the rest of the city rose 0.65. A relative rise of 1.2 points is excluded against the whole rest of the city, and not against the zone's earlier trend or against downtown Brooklyn and Long Island City. Rises below 1.2 points, effects on sales or rents, and effects that take more than one lease cycle are not tested." The outcome's `notes` should drop the mean of the three earlier years, because the 2023 value spans the change in filing structure, and should state that the 1.2-point threshold is the resolution of the test.

Recommendation: keep "confirmed", with the label above.
