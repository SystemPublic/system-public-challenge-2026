# Referee report: further-chinatown-shift

Verdict recorded: contested. Recommendation: keep the verdict, and correct the notes, which misdescribe why the reproduction fails.

Scratch work is in `referee-further-chinatown-shift/` in the session scratchpad (`reest.py`, `subset.py`, `exact.py`, `exact20.py`, `consistent.py`). It reads only `data/derived/further/*.csv`, `chinatown_sets.json` and the Census lookup files in `~/opt/nyc-concordance/chinatown`.

## (a) Does the verdict follow from the registered conditions?

Yes. Part A decides. Support needed the 2010 count, the 2020 count and the percentage change all inside their bands under B1, D1, M1. I recomputed that reading from the tract tables: 48,749 in 2010 (7.3% below 52,613), 38,279 in the 2018-22 ACS (6.7% below 41,024), change -21.5%. The change is inside its band and both counts are outside theirs, so support fails. The grid in `chinatown_results.json` has no reading with all three inside, so the refutation condition is met and the rule gives contested.

Nothing was decided by a measure chosen after the data were seen. The registration was committed at 20:25:17 on 12 November 2026 and the branch `prereg/further-chinatown-shift` exists on the remote with a commit at 20:25:25. The tract sets file was written at 20:23:36 and its SHA-256 matches the hash in the registration. The four Census count files were downloaded between 20:26:28 and 20:26:33 (01:26Z on 13 November in the sources), the analysis script was created at 20:28:26, and the outcome is dated 20:31:00. The lookup files downloaded before registration (Gazetteer, relationship file, NTA table) are the ones the registration discloses. The 2010 Gazetteer does carry a population column, as disclosed; the sets script does not read it.

The outcome ran M2 for all 15 readings, where the registration listed it for one. That enlarges the grid and could only have made a reproduction easier to find, so it does not affect the verdict.

## (b) Errors in code, units, joins, dates, geography or uncertainty

The column positions used for the PL 94-171 files are correct for both years (P1 fields 6 and 7 for Asian and NHPI alone; P2 fields 2, 5, 6, 8 and 9 for Hispanic and the non-Hispanic groups). The M1 mapping of the 23 B1 tracts gives 24 tracts in 2020, because tract 29 was split. My re-estimate of every number in the primary reading equals the registrant's.

The interval in `city_effect` (-26.7 to -16.2) is the ACS 90% margin applied to the 2020 count. The stance code treats it as a 95% interval, so the stance z of 8.04 should be about 6.7. This changes nothing that is shown. The stance of 0.999 measures agreement with the direction of change and sits beside a contested verdict that measures reproduction of the counts; a reader of the dashboard needs to be told these are two different things.

The robustness variant I ran is a search for the tract set that AALDEF used. The outcome notes say the published totals "do not match any NTA union" and infer "a boundary closer to the Chinatown core". I searched sets formed from B1 by removing up to five tracts and adding up to four of the other 42 populated Manhattan tracts south of 14th Street. One set matches AALDEF's 2010 table exactly on all five rows: B1 without tracts 22.02, 26.01, 26.02 and 28 (the blocks north of Houston Street and east of Avenue B) and with tracts 41, 43 and 45 (Little Italy and the eastern edge of SoHo). Its 2010 census counts are total 116,722, non-Hispanic white 23,314, non-Hispanic Black 8,457, Hispanic 30,227 and non-Hispanic Asian alone 52,613. The next closest set is off by 288 persons summed over the five rows. The Pacific Islander count in the set is 23, so the row labelled "Asian or Pacific Islander" is Asian alone.

I then searched for the 2020 set in the same way, against the 2018-22 ACS. One set matches AALDEF's 2020 column exactly on all five rows (120,173; 30,520; 11,094; 32,840; 41,024), and it is a different set: the 24 tracts of B1 plus tract 41. Tracts 43 and 45 are in AALDEF's 2010 area and not in its 2020 area, and tracts 22.02, 26.01, 26.02 and 28 are in its 2020 area and not in its 2010 area. None of these tracts changed boundary between the two censuses.

So the published table compares two different areas. On one area in both years the figures are as follows.

| Area held fixed | Total | NH Asian (ACS 2018-22) | NH Asian (2020 census) | NH white | NH Black | Hispanic |
|---|---|---|---|---|---|---|
| AALDEF's 2010 set (22 tracts) | -7.7% | -25.7% (90% margin -30.5 to -20.9) | -12.9% | +15.8% | +15.1% | -7.4% |
| AALDEF's 2020 set (25 tracts) | -6.6% | -23.6% (-28.5 to -18.8) | -11.6% | +15.0% | +8.1% | -7.8% |
| As published (2010 set, then 2020 set) | +3% | -22% | | +31% | +31% | +9% |

Percentages for groups other than Asian use the ACS for 2020. The mixed comparison in the last row reproduces every published percentage. The Asian decline is about the same on a fixed area (-24% to -26% against the ACS). The published total growth of 3%, the 31% growth of white and Black residents, the 9% growth of Hispanic residents and the statement that the area "gained roughly 12,000 white, Black, and Hispanic residents" come from the change of area. On AALDEF's 2010 set the three groups together gained about 2,700 and the total fell.

This search is exploratory and was made after the data were seen. Under rule 4 it decides nothing. Two exact matches on five numbers each are not a chance result, though, and they replace the outcome's guess about the boundary.

I did not re-run Parts B and C or the placebos. They do not decide the verdict.

## (c) Is the comparison with the published figure fair?

The registered comparison used the same sources as the report (2010 census, 2018-22 ACS) and the same unit. It could not use the same geography because the report publishes no tract list, and the registration said so. The 5% tolerance on counts was a reasonable test of whether an NTA union stands in for AALDEF's line; it does not, by 7%.

The outcome's own headline, that the decennial-to-decennial decline is about half the published one (-10.3% in B1), is confirmed on AALDEF's own tracts (-11.6% to -12.9%). The ACS estimate of Asian residents is below the 2020 census count in the same tracts by 3.5 standard errors in B1, as the outcome reports.

The claim has no graph evidence (the lookup was pending at registration and `graph_effect` is null), so there is no finding to check against PubMed.

## (d) Alternative explanations not addressed

The registered alternatives did not include a change of boundary between the report's own two time points. That is what happened.

The undercount check runs in one direction only. The registration raises 2020 Asian counts by 3% and 5%. The Census Bureau's Post-Enumeration Survey estimated a net overcount of the Asian population in 2020 nationally, and the 2018-22 ACS pools interviews from 2021 and 2022, after pandemic out-migration, with interviews from before it. The gap between the ACS and the census in these tracts can therefore come from a census that is too high, an ACS that is too low, or real change within the ACS window. The outcome names the first two in `settle`; it does not name the third.

Group quarters and student housing in tracts 41, 43 and 45 were not examined. They matter now that those tracts are known to be in the 2010 base.

## (e) Could the test have failed?

Yes, in both directions. With a 5% band on counts and three boundaries the registrant gave a prior of 0.4 for reproduction. B3 overshoots and B2 undershoots the 2010 count, so a boundary between them could have landed inside the band. The claim is a reproduction and not an endpoint or transfer test, so z against a composed prediction does not apply. For reference, the primary 2020 count is 1.8 standard errors below 41,024 using the ACS margin, and the 2010 count is a full census count 3,864 below 52,613.

## What should change in the outcome

The notes should say that an exact tract set was found for each year, that the two sets differ, and that the published growth figures for the total and for the non-Asian groups depend on that difference. The sentence about "a boundary closer to the Chinatown core" should be removed. The first item in `research_needed` can be replaced by a request to AALDEF to confirm the two tract lists. A new claim can be registered on the two exact sets, with the fixed-area change as the prediction, if the result is to be shown as a reproduction.

Recommendation: keep. No registered reading reproduces the counts, so contested follows from the rule, and the exact tract sets found afterwards show that the published change mixes two areas, which supports the label for the table as a whole while leaving the Asian decline of about 22 to 26 percent intact.
