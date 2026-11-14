# Referee report: transfer-chicago-inside-outside

Date: 14 November 2026. Referee: an independent Claude agent with no part in the registration or the outcome.

Files read: `claims/registered/transfer-chicago-inside-outside.json`, `analyses/heat_inside/test_chicago.py`, `data/derived/heat_inside_chicago/results.json` and `daily.csv`, `claims/outcomes/transfer-chicago-inside-outside.json`, the `PRECEDENCE` string in `concord/claims.py`, and `critique/referee_2026-11-14_moon_inside.md`. Nothing under `claims/`, `analyses/` or `data/derived/` was changed. The script was rerun with its output folder redirected to a scratch folder.

## Summary

The registered numbers reproduce exactly. The verdict `confirmed` follows from `support_if` under the registered error and under every corrected error I tried, with an upper bound of 0.993 to 0.994 against the threshold of 1.00.

There are two errors.

1. The registered interval (0.956 to 0.980) is too narrow by a factor of 2.04. The cause is a calculation error in statsmodels, not sparse counts as the outcome says. The true Pearson scale is 1.04, not 0.25. The correct quasi-binomial interval is 0.943 to 0.994.
2. The location classes put 2,132 of the 5,746 incidents classed inside (37%) under descriptions that also match the outside pattern. The classes also change meaning in 2019 to 2020, when the city relabelled its descriptions. This error works against the claim: with the ambiguous descriptions removed the ratio is 0.918 (0.888 to 0.948).

The outcome's prose says the size of the inside/outside difference "depends on the city". The data do not show that. Most of the difference between Chicago and New York comes from the flawed classes, and the remainder is within sampling error.

## Git order

| item | commit | local time |
|---|---|---|
| registration and script | c7d45d2 | 10:51:41 |
| Socrata fetch (`sources.json`, cache file time) | | 10:51:45 |
| results and outcome | 7d648ae | 10:52:52 |

The script was committed with the registration and four seconds before the fetch. The order is correct, on local times only. The cache folder holds no earlier query of this dataset by date and location; the five older `gumc-mgzr` cache files have dates and counts, or case numbers and times, with no location.

Two procedural points, both minor.

- The outcome was committed 67 seconds after the fetch. In that time the registered run, the exploratory runs and the notes were all produced. This is possible for an agent but leaves no time for anyone to have read the output.
- The undated counts listed in `already_seen` (STREET 10,475, APARTMENT 1,026, PORCH 618) do not match the dated data (STREET 16,927, APARTMENT 1,348, PORCH 255 as a bare description). The registration expected about 2,800 inside and 14,500 outside incidents and the run found 5,744 and 33,330. The undated query is not in the cache, so I could not check what was counted. The classes were therefore written from a list that differs from the data the script used.

## Does the script do what the plan says?

The model is as planned: a binomial regression of the daily inside count out of inside plus outside on `t5`, weekday, year, month, holiday and wet day, with a Pearson scale. The secondary runs are as planned.

The classes are not as the registration describes them.

### Error 1: descriptions that match both patterns are classed inside (severity: major for the size of the effect, not for the verdict)

`classify` tests `INSIDE_RX` before `OUTSIDE_RX`. The descriptions that match both, with incident counts over the whole period:

| description | incidents |
|---|---|
| RESIDENCE PORCH/HALLWAY | 746 |
| RESIDENCE - PORCH / HALLWAY | 297 |
| PARKING LOT / GARAGE (NON RESIDENTIAL) | 337 |
| PARKING LOT/GARAGE(NON.RESID.) | 330 |
| RESIDENCE - YARD (FRONT / BACK) | 240 |
| HOSPITAL BUILDING / GROUNDS (two spellings) | 171 |
| LAKEFRONT / WATERFRONT / RIVERBANK (two spellings) | 9 |
| CTA PARKING LOT / GARAGE / OTHER PROPERTY | 2 |
| total | 2,132 |

This is 37.1% of the 5,746 incidents classed inside, a little more than the "about a third" in the outcome's notes. A further 121 incidents are in garages (RESIDENCE-GARAGE, GARAGE, RESIDENCE - GARAGE and similar), and one RIVER BANK incident is inside because the pattern contains BANK.

Three consequences follow.

- The registration says "A porch is outdoors but at home; it is classed outside". The script classes 1,043 porch/hallway incidents inside and only the 255 bare PORCH incidents outside. The registered secondary run (`porch_excluded`) does remove all of them, and gives 0.944.
- The same place is classed differently before and after the city relabelled its descriptions. RESIDENTIAL YARD (FRONT/BACK), 412 incidents, all 2010 to 2020, is outside. RESIDENCE - YARD (FRONT / BACK), 240 incidents, nearly all 2018 to 2026, is inside. Year terms absorb the change in level but not a change in the slope.
- The incidents wrongly added to the inside class are mostly outdoor ones, which rise with heat. They pull the inside slope up and the ratio towards 1.00. The error therefore makes the registered test harder to pass, not easier.

Two outside matches are wrong and too small to matter: BOWLING ALLEY (2) and GAS STATION, which is partly indoor (710).

### Error 2: the Pearson scale of 0.25 is a calculation error (severity: major for the reported interval, not for the verdict)

The script fits the binomial model with a two-column response and `scale="X2"`. For that form statsmodels computes the Pearson statistic on the daily proportions without weighting by the number of incidents in the day. I computed the statistic both ways from the fitted model:

| calculation | Pearson chi-square / residual df |
|---|---|
| without the daily totals (what the script used) | 0.248894 (the registered `dispersion` to six places) |
| with the daily totals (the correct statistic) | 1.039 |

The mean day has 6.5 classified incidents, so omitting the totals divides the statistic by about four. The data are not underdispersed; the scale is 1.04. The registered standard error of 0.0066 should be 0.0134.

The outcome's `interval_note` says the interval is "too narrow because the Pearson scale is 0.25 on sparse daily counts". The interval is too narrow, but the reason given is wrong. The plan asked for "the Pearson scale, which is the error the referee of the New York claims required", and the script did not deliver that.

Defensible intervals for the registered classes, ratio of the inside to the outside rate ratio per 5 C:

| error | estimate (95% interval) | se of log |
|---|---|---|
| registered (wrong scale 0.249) | 0.968 (0.956 to 0.980) | 0.0066 |
| quasi-binomial, correct Pearson scale 1.039 | 0.968 (0.943 to 0.994) | 0.0134 |
| binomial, scale 1 | 0.968 (0.943 to 0.993) | 0.0132 |
| binomial, HC1 with the day as the unit | 0.968 (0.943 to 0.994) | 0.0136 |
| binomial, clustered by year-month | 0.968 (0.943 to 0.993) | 0.0131 |
| binomial, bootstrap of days (300 draws) | 0.968 (0.944 to 0.992) | 0.0134 |
| stacked Poisson with interactions, clustered by day | 0.967 (0.941 to 0.993) | 0.0137 |
| two separate Poisson fits, treated as independent | 0.967 (0.940 to 0.993) | 0.0139 |

All of them agree. I recommend the correct quasi-binomial interval, 0.943 to 0.994, as the reported one, because it is the registered model with its scale computed correctly.

The outcome reports 0.942 to 0.995 from the two separate Poisson fits. That interval is close to the right one. It pairs the binomial estimate (0.9679) with a standard error from the Poisson fits, whose own ratio is 0.9665, and it assumes the two fits are independent. The stacked model shows the assumption costs nothing here.

## Reproduction

The rerun read the cached query of 10:51:45 and wrote `results.json` and `daily.csv` identical byte for byte to the committed files: ratio 0.968 (0.956 to 0.980), inside 1.102 (1.074 to 1.129), outside 1.140 (1.127 to 1.152), 5,744 inside and 33,330 outside incidents on 6,085 days, and 0.944 (0.930 to 0.957) with porches excluded. The registered intervals for both ratio runs carry Error 2.

## Verdict against the rules

`support_if` is "the 95% upper bound of the ratio of the inside to the outside rate ratio is below 1.00". The registered bound is 0.980. The corrected bound is 0.994. The condition is met either way. `refute_if` needs an interval that includes 1.00 and is not met. Rule 1 gives `confirmed`.

Rule 9 does not change this. The script was committed with the registration, and the condition is met under the registered procedure and under each corrected error, so the verdict does not turn on a part of the procedure that was left open. The rule's "neither met nor unmet" case concerns resampled bounds that vary by seed, and no bound here crosses 1.00 under any error model.

Rule 10 does not apply, because the condition is written on an interval bound. In its spirit the outcome should state the margin: the corrected upper bound is 0.994, which is 0.006 below the threshold, and the z value is about 2.4, not the 4.9 that the registered error implies.

Rule 4 applies to the interval the outcome chose after the run (separate Poisson fits) and to the exploratory classes. Neither decides anything, and neither needs to.

The class error does not weaken the verdict. Every corrected classification moves the ratio further below 1.00.

The magnitude predictions were missed, as the outcome says. The ratio of 0.968 is above the predicted 0.80 to 0.95, and the inside rate ratio of 1.102 is above the predicted 0.95 to 1.08. With the ambiguous descriptions excluded both fall inside the predicted ranges (0.918 and 1.046), but that classification was chosen after the data and counts for nothing under rule 4.

## Exploratory robustness

All of this was chosen after the data were seen. Errors are binomial with HC1 by day. "Ambiguous excluded" drops from the inside class every description that names a porch, yard, parking lot, garage or grounds, and leaves the outside class as registered. "Homes only" is apartment, house, residence, hallway, basement, stairwell and vestibule without those words, against street, alley and sidewalk.

Classes:

| classes | inside n | ratio | inside rate ratio per 5 C |
|---|---|---|---|
| registered | 5,744 | 0.968 (0.943 to 0.994) | 1.102 (1.074 to 1.129) |
| outside pattern tested first | 3,613 | 0.918 (0.890 to 0.948) | 1.049 (1.018 to 1.081) |
| ambiguous excluded | 3,510 | 0.918 (0.888 to 0.948) | 1.046 (1.015 to 1.079) |
| homes only vs street, alley, sidewalk | 2,875 | 0.932 (0.899 to 0.965) | 1.056 (1.021 to 1.092) |

The homes-only figures match the outcome's (0.931, 0.898 to 0.964; inside 1.056).

Specifications, ratio of rate ratios:

| specification | registered classes | ambiguous excluded | homes only |
|---|---|---|---|
| registered terms | 0.968 (0.943 to 0.994) | 0.918 (0.888 to 0.948) | 0.932 (0.899 to 0.965) |
| year-by-month fixed effects | 0.969 (0.942 to 0.996) | 0.919 (0.888 to 0.952) | 0.933 (0.898 to 0.968) |
| May to September | 0.977 (0.931 to 1.026) | 0.915 (0.861 to 0.972) | 0.923 (0.864 to 0.986) |
| October to April | 0.965 (0.934 to 0.996) | 0.919 (0.884 to 0.955) | 0.935 (0.896 to 0.976) |
| excluding 2020 and 2021 | 0.965 (0.937 to 0.993) | 0.908 (0.877 to 0.940) | 0.928 (0.893 to 0.964) |
| 2010 to 2017 | 0.953 (0.915 to 0.993) | 0.863 (0.819 to 0.909) | 0.885 (0.834 to 0.939) |
| 2018 to 2026 | 0.979 (0.945 to 1.014) | 0.950 (0.912 to 0.990) | 0.957 (0.916 to 1.001) |

Every estimate is below 1.00. With the registered classes the intervals for May to September and for 2018 to 2026 include 1.00; each uses about half the data. With the cleaner classes only one interval reaches 1.00 (homes only, 2018 to 2026, upper bound 1.001).

The ratio is nearer 1.00 in the second half of the period under all three classifications. Part of this is the relabelling of 2019 to 2020. Part is a flatter outside slope, 1.17 before 2018 and 1.11 after. The inside rate ratio with the ambiguous descriptions excluded is 1.025 (0.976 to 1.078) for 2010 to 2017 and 1.062 (1.021 to 1.104) for 2018 to 2026.

The inside share has the same seasonal form as in New York and is weaker: 17 to 18% in December to February and 13% in June and July.

## Prose in the outcome

- "The inside slope is smaller, as registered." This is supported.
- "about a third of the incidents classed inside." The figure is 37% (2,132 of 5,746). The notes should also say that the registered text classed porches outside and the script classed 1,043 porch/hallway incidents inside, and that yard descriptions change class when the city relabels them.
- The `interval_note` should give the real cause of the narrow interval (the Pearson statistic was computed without the daily totals; the correct scale is 1.04) and the corrected interval, 0.943 to 0.994.
- "New York's finding that inside shootings do not rise is not reproduced." This is true of the registered classes (1.102, 1.074 to 1.129). It needs a qualification. With comparable classes the Chicago inside rate ratio is 1.046 (1.015 to 1.079) or 1.056 (1.021 to 1.092) for homes, against New York's 1.009 (0.975 to 1.044). The difference between Chicago homes and New York is 0.046 on the log scale with a standard error of 0.024, which is z = 1.9 and comes from a classification chosen after the data. Commercial interiors in Chicago are flat (1.002, 0.939 to 1.069), as in New York.
- "the size of the difference depends on the city and on what counts as inside." The second half is shown: the Chicago ratio moves from 0.968 to 0.918 with the classification. The first half is not shown. The Chicago ratio with the ambiguous descriptions excluded is 0.918 (0.888 to 0.948) and New York's is 0.861 (0.828 to 0.896). That difference is z = 2.5 on an exploratory classification, in a city whose location field is free text and changed in 2019 to 2020. A supported sentence would be: in both cities shootings recorded as inside rise less with heat than shootings recorded as outside; in Chicago a small rise inside remains (about 5% per 5 C in homes), and the data cannot say whether the difference from New York is real or comes from the location field.
- The objection of the New York report applies here too. A smaller inside slope is predicted both by the routine-activity account and by a direct effect of heat on people who are in the heat. The registration's remark that Chicago homes have less air conditioning is in line with a small rise inside, but one pair of cities cannot test it. The `research_needed` entry states the right design.
- The stance `z` of 2.34 was computed from the wider interval and is about right (2.4 with the corrected scale). No change is needed.
- The source record has `"kind": "nyc-open-data"` for a Chicago dataset. This is a label error only.

## Recommended verdict

`confirmed`. The registered condition is met with the registered error (upper bound 0.980) and with the corrected one (0.994), and the classification error biases the ratio towards 1.00, so correcting it strengthens the result.

## Recommended corrections

1. Report the corrected quasi-binomial interval, 0.943 to 0.994, as the city effect, and replace the explanation in `interval_note`.
2. Fix the two-column Pearson scale in a new script version (fit the proportion with `var_weights`, or use HC1 by day), and check whether `analyses/heat_inside/test.py` or any other script uses the two-column form with `scale="X2"`.
3. State the margin: 0.006 below the threshold, z about 2.4.
4. Correct "about a third" to 37% and record the porch and yard inconsistencies.
5. Replace "depends on the city" with the narrower sentence above.
6. If the cleaner classes are to count, register them as a new claim (rule 4). The data have now been seen, so that claim could only be tested on another city or on Chicago data after August 2026.
