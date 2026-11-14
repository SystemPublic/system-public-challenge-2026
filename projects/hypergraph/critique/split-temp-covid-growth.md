# Referee report: split-temp-covid-growth

Verdict recorded: unsettled. Referee script: `referee-split-temp-covid-growth/c.py` in the session scratch folder (not in the repository). The registrants' documents in docs/ were not read.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required a negative growth-rate coefficient with an interval excluding 0, refutation a positive one. The estimate is +0.0058 per C (-0.0036 to +0.0152), so neither is met and the verdict is unsettled under rule 2. The moderator prediction was registered as secondary and does not decide the verdict; it is scored as not met (5 of 22 quarters significantly positive, 23%, against a registered 25%), which is the strict reading. No measure chosen after the data decides anything; the first-wave correlations are labelled exploratory.

The registration was committed at 22:49:54 on 12 November 2026 and the branch prereg/split-temp-covid-growth exists on GitHub with a commit made at 22:50:04. The only earlier query of rc75-m7u3 in the cache (22:48:50) asks for the first date, last date and row count, as the registration discloses. The data were fetched at 22:57:21 and the outcome written at 23:00:32. The script was not committed with the registration and its file time is 22:57, so the order of model and data rests on the plan text, which the script follows.

## (b) Errors in code, units, joins, dates or uncertainty

From the cached query I reproduce the deciding number exactly: +0.0058 (-0.0036 to +0.0152), 291 weeks, standard error 0.0048. Weeks run Monday to Sunday, the exposure window is days 7 to 20 before the Thursday, and there are no gaps in the daily series.

One error of data handling: the end of the file is incomplete. The last five days report 4, 2, 1, 1 and 0 admissions against about 20 a day in the weeks before, which is reporting delay. The week ending 2025-10-12 (57 admissions after 121) passes the filter of 20 and has the most negative growth in the whole sample (-0.75). Dropping the last three weeks gives +0.0078 (-0.0009 to +0.0165). The verdict does not change, but the registered rule did not protect against a truncated tail and the outcome should say so.

Variants the registrant did not run:

| Variant | Coefficient per C | 95% interval |
|---|---|---|
| Registered model | +0.0058 | -0.0036 to +0.0152 |
| Last three weeks dropped | +0.0078 | -0.0009 to +0.0165 |
| Weights for the Poisson variance of the log ratio | -0.0025 | -0.0129 to +0.0079 |
| Year-quarter fixed effects, no harmonics | +0.0080 | -0.0014 to +0.0174 |
| Weeks with at least 100 admissions | +0.0080 | -0.0007 to +0.0166 |
| No lagged growth term | +0.0148 | -0.0089 to +0.0385 |
| October to March weeks | -0.0064 | -0.0200 to +0.0072 |
| April to September weeks | +0.0055 | -0.0093 to +0.0204 |
| Window days 0-6 | -0.0098 | -0.0180 to -0.0015 |
| Window days 7-13 | -0.0026 | -0.0101 to +0.0050 |
| Window days 14-20 | +0.0089 | +0.0012 to +0.0166 |
| Window days 21-27 | -0.0071 | -0.0156 to +0.0014 |

All intervals that use the registered window include 0. The sign is not stable: weighting weeks by their precision makes it negative, and single-week windows alternate in sign, two of them with intervals excluding 0. Alternation of that kind is what serial dependence in weekly growth produces when adjacent exposure windows are entered one at a time, so I do not read the days 0-6 or days 14-20 results as effects. The unsettled verdict is robust.

The quarterly p-values ignore autocorrelation, as registered, so "significant" there is the source studies' standard and not a valid test.

## (c) Is the comparison with the research fair?

No numeric comparison is made and none would be fair: the graph rows mix Pearson correlations, coefficients in cases per degree and relative risks. The city test is a comparison with the transmission-model studies in design only.

I checked association _zZhNuc_Bh (PMID 33162141) against its PubMed abstract. The coefficient -30.52 (-60.24 to -0.78) for maximum temperature in Bangladesh is in the abstract. It is a coefficient on daily confirmed cases in an ARIMAX model, which the graph labels "COVID-19 transmission". The same abstract reports a positive coefficient for Afghanistan (5.10, 0.06 to 10.14) and says temperature had mixed effects in four of five countries, so this one study supplies rows of both signs. The registration codes it among the negative, model-based findings; "mixed" is the accurate code. I did not recount the 20 against 22 split given in the outcome.

## (d) Alternative not addressed

Variant waves are named and said to add noise but not bias. That holds only if wave timing is unrelated to the anomaly. With five and a half years and five or six large waves, a chance alignment of two or three wave onsets with warm or cold spells is enough to move a coefficient of this size, and year fixed effects with harmonics do not remove it. The difference between the cool-season and warm-season estimates (-0.0064 and +0.0055) is the size such alignment would produce. The registrant's proposed multi-city panel with week fixed effects is the right answer.

The registration also does not name care-seeking: care-seeking and admission practice respond to weather within the same week (the days 0-6 coefficient is negative), which affects admissions without any change in transmission.

## (e) Could the test have failed?

It could have been refuted or confirmed, but only for part of the registered range. The standard error is 0.0048, so a true effect smaller in size than about -0.0094 would not have given an interval excluding 0; that is the weakest third of the registered range of -0.003 to -0.030. Against the prediction the estimate is z = 4.6 from the midpoint (-0.0165) and z = 1.8 from the nearest edge (-0.003); the lower limit of the interval, -0.0036, lies just inside the registered range, so the weakest registered effect is not excluded. The estimate is z = 1.21 from no effect. This is a confirmation test, not an endpoint or transfer test.

Recommendation: keep. Neither registered condition is met under the registered model or any variant using the registered window; the outcome should record the incomplete final weeks of the file.
