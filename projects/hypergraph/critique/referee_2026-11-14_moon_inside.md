# Referee report: moon-full-emergencies, heat-inside-outside, heat-inside-outside-2006

14 November 2026. Independent referee (Claude, a fresh agent with no part in the registrations).
Scratch scripts are in the session scratchpad under `referee/` (`rerun.py`, `moon_rob.py`, `moon_rob2.py`, `heat_rob.py`, `dedup.py`); nothing under `claims/`, `analyses/` or `data/` was changed.
Every check beyond the registered scripts is exploratory and decides nothing under rule 4.

## Summary

All three sets of numbers reproduce exactly. All three verdicts follow from `support_if` as written.

I found one error that affects reported numbers. The standard error of the registered inside/outside ratio is too small by a factor of about 1.6 to 1.7, because of how statsmodels combines `freq_weights` with HC1. The corrected intervals are still below 1.00, so neither verdict changes, but the intervals, the `z` values and the stance values in the two outcomes should be corrected.

The notes of the two inside/outside outcomes claim more than the result supports. The test shows that the outdoor slope is steeper than the indoor slope. It does not separate "more people in contact outdoors" from a direct effect of heat on people who are in the heat.

For the moon claim, rule 11 read literally gives `unsettled`, because the placebo also meets `support_if`. I think the rule was not written for equivalence claims and recommend `confirmed`, but the coordinator should record how rule 11 applies to a claim with direction 0.

## 1. moon-full-emergencies

### Order of commits

`analyses/moon/test.py` and the registration are in the same commit, f673f98 at 07:10:45. `data/derived/moon/results.json` has a file time of 07:10:56 and was committed with the outcome in 44d469d at 07:12:57. The order is correct. The margin is 11 seconds, and the four commits are not pushed, so the order rests on local commit times and file times only. The registration does not name the commit hash that rule 9 asks for; it cannot name its own commit, and "committed with this registration" is the nearest statement possible.

### Does the script do what the plan says

The script does what the plan says. I checked these points.

- Full-moon dates. PyEphem instants are in UTC and are converted to New York dates. For 52 of the 262 full moons the New York date differs from the UTC date, and the script uses the New York date. Seven dates checked against known full moons (for example 31 October 2020, 25 January 2024, 5 November 2025) are correct. Gaps between successive dates are 29 or 30 days.
- The window is the full-moon date and one day either side: 741 exposed days of 7,305 for shootings, which is 247 full moons times 3.
- The model has day of week, year-by-month effects, holiday, maximum temperature and its square, and a wet-day indicator, with Newey-West errors at 7 lags, as planned.
- The EMS series has no missing days (3,530 days). Crash days with no injury crash would be set to zero; none occur.

One limit on reproduction: the crash file is at `~/opt/nyc-concordance/turn_restrictions/crashes.csv`, outside the repository, so the crash result can be rerun only on a machine that has that file.

### Reproduction

A rerun with the output folder redirected to scratch gave a `results.json` identical byte for byte to the committed one: shootings 1.007 (0.966 to 1.049), ambulance incidents 0.997 (0.991 to 1.004), injury crashes 1.002 (0.987 to 1.018).

### Verdict against the rules

`support_if` is met: each 95% interval is inside its bound (0.93 to 1.07, 0.98 to 1.02, 0.97 to 1.03). `refute_if` is not met: no 98.3% interval excludes 1.00. Rule 1 gives `confirmed`.

Rule 11 is a problem of wording (severity: moderate, procedural). It says that when the placebo itself meets `support_if` the verdict is unsettled. Here the 23-day placebo intervals are also inside the bounds, so the placebo meets `support_if`. For a claim of no effect that is the expected and reassuring result, since it shows the design has no bias of its own, and the registration's `refute_if` uses the placebo in the sensible way. Rule 11 needs a sentence that exempts claims with direction 0, or says what the placebo must show for them. The registration also cites rule 12 for the placebo; rule 12 concerns before-and-after designs and does not apply.

### Exploratory robustness

Other error models, 3-day window:

| outcome | registered (HAC 7) | quasi-Poisson | negative binomial | HAC 30 lags |
|---|---|---|---|---|
| shootings | 1.007 (0.966 to 1.049) | 1.007 (0.963 to 1.052) | 1.007 (0.964 to 1.052) | 1.007 (0.965 to 1.051) |
| ambulance incidents | 0.997 (0.991 to 1.004) | 0.997 (0.992 to 1.002) | 0.997 (0.993 to 1.002) | 0.997 (0.991 to 1.004) |
| injury crashes | 1.002 (0.987 to 1.018) | 1.002 (0.987 to 1.018) | did not converge | 1.002 (0.986 to 1.019) |

Pearson dispersion is 1.1 for shootings, 8.5 for ambulance incidents and 2.5 for crashes. The registered Newey-West intervals are as wide as or wider than the alternatives. All stay inside the bounds.

Other windows (HAC 7):

| outcome | day only | 5 days | 7 days |
|---|---|---|---|
| shootings | 1.033 (0.957 to 1.114) | 1.009 (0.974 to 1.045) | 0.974 (0.945 to 1.003) |
| ambulance incidents | 0.997 (0.990 to 1.005) | 0.999 (0.994 to 1.005) | 1.000 (0.995 to 1.006) |
| injury crashes | 0.980 (0.957 to 1.003) | 0.998 (0.986 to 1.011) | 0.999 (0.987 to 1.011) |

The 5-day and 7-day windows are inside the bounds for all three outcomes. The day-only windows are too imprecise for the shooting and crash bounds, as the outcome already reports.

One unexpected result for shootings. I moved the 3-day window to every position in the lunar cycle. A window centred 4 days before the full moon gives 0.914 (z = -3.9), with 0.905 in 2006 to 2015 and 0.926 in 2016 to 2025. The windows centred 5, 3 and 2 days before are also low (0.952, 0.939, 0.958). A cosine of lunar phase has a joint p of 0.048. Placebo cycles of 23, 31 and 37 days, moved through all their positions, give a largest |z| of 2.3 to 2.4. With 29 correlated positions a z of -3.9 is unlikely by chance (Bonferroni p about 0.003), and I have no explanation for it. It may be an alias of day-of-month patterns with the 29.5-day cycle. It does not bear on the registered window, which is at 1.007. It does mean the outcome should not be read as "shootings show no lunar pattern". Ambulance incidents and crashes show nothing comparable (largest |z| 1.85 and 1.99).

### Prose in the notes

Two sentences compare unlike quantities (severity: minor).

- "The injury-crash interval excludes the graph's 1.042 for crash transports in Japan." The graph finding is for full-moon nights. The city estimate is for all hours of three calendar days. If the 4.2% applied only to night hours of one night, and night hours hold roughly a quarter to a third of crashes, the expected ratio in the registered window would be about 1.004 to 1.005, which is inside the city interval. The city result does not exclude the Japanese finding; it excludes an all-day effect of that size.
- The Finnish homicide ratio of 0.85 is compared with shooting incidents, a different outcome. The sentence should say so.

### Recommended verdict

I recommend `confirmed`. All three intervals are inside the registered bounds under every error model and window width I tried, provided rule 11 is read as not applying to an equivalence claim.

## 2. heat-inside-outside (2022 to 2026)

### Order of commits

`analyses/heat_inside/test.py` and the registration are in commit 44d469d at 07:12:57. The source records give fetch times of 07:13:18 and 07:13:24, and the derived files have a file time of 07:13:24. Results and outcome are in 645fc26 at 07:14:02. The order is correct, by about 20 seconds, on local times only.

### Does the script do what the plan says

The model terms match the plan. The data handling is sound.

- Deduplication. The two files hold the same 3,172 incident-location counts for 2022 to 2024. Of 1,370 date-by-location cells, 2 differ, and they are one incident dated 22 June 2024 in one file and 27 June 2024 in the other. Nothing is counted twice.
- Blank location. The located incidents equal all incidents in `shootings_daily.csv` in every year and every month (the unlocated share is 0.000 throughout). The share of blanks cannot vary by season because there are none in 5ucz-vwe8.
- The weather join loses no days. The series ends on 31 August 2026 because the weather file ends there; the shooting file runs to 28 September 2026.

Error (severity: moderate; changes reported intervals, not the verdict). The registered model passes the daily share with `freq_weights` and asks for HC1 errors. In statsmodels this combination gives a standard error of 0.0282 for the log ratio. The same model fitted to one row per incident with HC1 gives 0.0450, clustered by day 0.0450, the ordinary binomial error 0.0459, and the grouped model with `var_weights` and HC1 0.0449. The registered error is therefore not a robust error for this model; it is too small by a factor of 1.6. The registration's own expected error was "about 0.05".

The outcome's explanation is also wrong. The notes say the registered interval "treats incidents as independent and is narrower". Treating incidents as independent gives 0.046, not 0.028. The narrow interval is a software artefact.

### Reproduction

The rerun (from the cached queries) gave `results.json` and `daily.csv` identical byte for byte: ratio 0.860 (0.814 to 0.909), inside 0.992 (0.917 to 1.072), outside 1.156 (1.115 to 1.198), 655 inside and 3,646 outside incidents.

### Verdict against the rules

`support_if` is met as registered (upper bound 0.909). With the corrected error the interval is 0.787 to 0.939, and the condition is still met. `refute_if` is not met. Rule 1 gives `confirmed`. The stance `z` of 5.35 should be about 3.4.

### Exploratory robustness

Ratio of inside to outside rate ratios per 5 C, with corrected errors (day as the unit):

| specification | estimate (95% interval) |
|---|---|
| registered terms, HC1 by day | 0.860 (0.787 to 0.939) |
| quasi-binomial | 0.860 (0.785 to 0.941) |
| clustered by year-month | 0.860 (0.792 to 0.934) |
| year-by-month fixed effects | 0.841 (0.766 to 0.923) |
| May to September only (237 inside) | 0.754 (0.622 to 0.915) |
| October to April only | 0.874 (0.792 to 0.966) |

Every interval is below 1.00. The inside count per 5 C is 0.98 (0.90 to 1.07) with year-by-month effects.

### Prose in the notes

The notes say the result "favours the account in which heat puts more people in contact outdoors, and limits the direct accounts to effects that work through being outside". This is more than the test supports (severity: moderate, interpretation).

- The exposure is outdoor maximum temperature at Central Park. Most New York dwellings and shops are cooled, so people inside are mostly not in the heat. A direct effect of heat on temper predicts a rise where people are hot, which is mainly outside. It predicts a ratio below 1, the same as the routine-activity account. The registration's `rivals_separated` assumes that direct effects "act on people wherever they are", and the result depends on that assumption. The registration lists the opposite case (homes without air conditioning) among its alternatives, and the outcome's `settle` field names it, but the notes draw the conclusion anyway.
- Sleep loss and medication effects would follow night-time temperature and lagged heat. The model has same-day maximum temperature only, so it does not test them.
- If heat moved people from inside to outside, the routine-activity account would predict fewer inside shootings on hot days. The inside count is flat (0.99, 0.92 to 1.07). A flat count is also what a fall from displacement plus a small direct rise would give. The interval allows a rise of 7% per 5 C inside, which is within the 5 to 9% the graph reports for homicide.
- The inside share is strongly seasonal (25% in December and February, 10% in June and July), and inside shootings are a different mix of events, as the notes say.

A supported sentence would be: shootings recorded as outside rise about 16% per 5 C and shootings recorded as inside show no rise, with a ratio of 0.86 (0.79 to 0.94); this is what the routine-activity account predicts, and it is also what a direct effect predicts if people inside are not exposed to the heat.

### Recommended verdict

I recommend `confirmed`. The upper bound of the ratio is below 1.00 with the corrected standard error and under every specification tried; the interval, `z` and the mechanism sentence in the notes need correction.

## 3. heat-inside-outside-2006 (2006 to 2026)

### Order of commits

`test_2006.py` and the registration are in commit cfd2556 at 07:13:15. The first claim's data were fetched at 07:13:18 and this claim's at 07:13:26 to 07:13:27, so the registration precedes both runs by seconds, as it says. `test_2006.py` differs from `test.py` only in the start date, the output folder and the docstring.

### Script and data

The points for claim 2 apply. Two more are specific to this claim.

- The location field for 2006 to 2021 exists only in 5ucz-vwe8. The archived file 833y-fsy8 returns no located rows before 2022 (the same 1,370 rows for both queries). The field is filled for every incident in every year, which suggests that NYPD filled the earlier years afterwards by some rule. I could not check that rule (severity: minor to moderate, unknown). The estimate is the same before and after 2022, which argues against a change of definition large enough to matter.
- The two claims are not independent. The 2022 to 2026 data are a fifth of the days of this one. They should be counted as one result. On the disjoint years 2006 to 2021 the ratio is 0.863 (0.826 to 0.901).

The standard-error error is the same: registered 0.0115, corrected 0.0200 (one row per incident, clustered by day), a factor of 1.7.

### Reproduction

The rerun output was identical byte for byte: ratio 0.861 (0.842 to 0.881), inside 1.009 (0.975 to 1.044), outside 1.174 (1.155 to 1.192), 3,471 inside and 20,958 outside incidents.

### Verdict against the rules

`support_if` is met as registered and with the corrected interval, 0.828 to 0.896. Rule 1 gives `confirmed`. The stance `z` of 13.03 should be about 7.5.

### Exploratory robustness

| specification | estimate (95% interval, day as the unit) |
|---|---|
| registered terms, HC1 by day | 0.861 (0.828 to 0.896) |
| quasi-binomial | 0.861 (0.828 to 0.896) |
| clustered by year-month | 0.861 (0.830 to 0.894) |
| year-by-month fixed effects | 0.862 (0.827 to 0.899) |
| May to September only | 0.849 (0.781 to 0.923) |
| October to April only | 0.864 (0.826 to 0.903) |
| excluding 2020 and 2021 | 0.855 (0.821 to 0.890) |
| 2006 to 2019 | 0.855 (0.817 to 0.895) |
| 2006 to 2021 | 0.863 (0.826 to 0.901) |

The result is stable. The unlocated share is zero in every year and month. Mean inside incidents per day fall from 0.52 on days at or below 5 C to 0.40 on days above 30 C before adjustment, and are flat after month and year terms (1.009, 0.975 to 1.044).

### Prose in the notes

The notes are the same text as claim 2 and the same objection applies. With this sample the inside interval is narrower (a rise of more than 4.4% per 5 C is excluded), so the statement that inside shootings do not rise with outdoor temperature is well supported. The inference to mechanism is not, for the reasons given above.

### Recommended verdict

I recommend `confirmed`. The corrected interval of 0.83 to 0.90 is far below 1.00 and stable across periods, seasons and error models; the reported interval, `z` and mechanism sentence need correction, and the result should not be counted separately from claim 2.

## Corrections requested

1. In both inside/outside outcomes, report the corrected intervals (0.787 to 0.939 and 0.828 to 0.896) beside the registered ones, correct the stance `z`, and replace the sentence that explains the narrow interval.
2. Rewrite the mechanism sentence in both notes so that it does not rank routine activity above direct effects.
3. In the moon notes, qualify the comparisons with the Japanese and Finnish findings.
4. Amend rule 11, or record a ruling, for claims with direction 0.
5. Optionally register the pre-full-moon dip in shootings as a new claim on data not yet seen (for example 2026 onwards), since it was found after the data.

I did not check the registration hashes or the construction of the three daily series from their raw sources.
