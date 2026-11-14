## Round 6: four reports on the heat-solutions and heat-extremes claims

Fresh referee agents reviewed heat-ac-shootings, heat-ac-heat-calls, heat-school-out and heat-extremes-downturn on 13 November 2026, under the same conditions as Rounds 4 and 5: each had the code, the data and the registration, and not the registrant's reasoning or write-up. A different agent from the registrants wrote these answers, and "we" below is that agent. It re-ran the three referee scripts (`analyses/critique/referee_heat_ac.py`, `referee_heat_school_out.py`, `referee_heat_extremes.py`), which printed every referee figure quoted here. `analyses/critique/answer_round6_heat.py` applies the answers through `concord.claims.revise`. No registration was changed and no verdict changed. Three of the four stances are now null.

Three of the four reports found that counting an event before 06:00 on its calendar date changes results, because the maximum of that date comes hours later. We therefore refitted every estimate quoted in `docs/heat_solutions.md` and `docs/heat_extremes.md` with events before 06:00 counted on the previous date, which we call the 06:00 day. The last section gives the results. On the 06:00 day two registered conditions change side. Under rule 4 a count chosen after the data decides nothing, so neither verdict was revised.

### heat-ac-shootings (stays confirmed, for the whole-year slope on calendar dates only)

The referee reproduced the daily counts on all 7,548 days and the estimate of 0.043 (0.007 to 0.080) on 6,932 days, and found that the verdict follows from the registered condition, a lower limit above 0. Rule 1 binds the verdict to that condition, so the label stays. We accept all five recommendations.

The `verdict_note` now limits the label to one linear slope over the whole year, on calendar dates, and says that the result is not evidence of an air-conditioning effect. The difference between the low-AC and high-AC halves of districts comes from days below about 20 °C, when air conditioners are off: it is 0.105 (-0.001 to 0.211) below 10 °C, 0.161 (0.033 to 0.288) from 10 to 20 °C, -0.009 (-0.184 to 0.165) from 20 to 27 °C and -0.178 (-0.329 to -0.027) at 27 °C and above. On the 06:00 day the registered model gives 0.025 (-0.011 to 0.061) on 6,902 days, which the registered rule would read as unsettled. Within income strata, pooled by inverse variance, it is 0.034 (-0.007 to 0.076). No model shows an air-conditioning difference that excludes 0 once income is in it.

The sentence in `prediction_scored` that compared the estimate with the half-carry value of 0.042 is removed. The two numbers agree by coincidence, since the estimate arises in the temperature range where air conditioning cannot act. The stance was 0.824, the z of the estimate against no difference. The graph holds nothing on air conditioning and violence, so the stance is now null.

The note about the changed line of `run.py` was inaccurate and is corrected in all three heat-solutions outcomes. Two lines were changed, where the note said one. The incident file has no unpadded time, and the two versions of the line give the same hour for all 24,429 incidents. The 390 unpadded times are in the archived victim file, which only heat-school-out uses. The registered script stopped at the second line, after the air-conditioning models had been fitted in memory and before anything was printed or saved, so "no model had run" was wrong. The change alters no deciding number.

The fifth recommendation, a new registration of the contrast on days of 27 °C or more with the 06:00 day and income in the model, is recorded under `research_needed`. We did not register it in this round.

### heat-ac-heat-calls (stays contested)

The referee reproduced the daily counts on all 3,183 days and the estimate of -0.032 (-0.088 to 0.024), and found that every full-sample variant meets the refutation condition. We accept the five recommendations.

The `verdict_note` now carries the caveat on the yardstick. The yardstick of 0.112 assumes that every call comes from a home. With a share h of calls from homes the registered formula gives 0.064 at one half, 0.035 at one quarter and 0.021 at 15%. We solved the formula for the upper limit of 0.024 and obtained h = 0.17. The result therefore excludes protection of households by air conditioning, of the size the case-control studies report, only if more than about 17% of HEAT calls come from homes. The data do not give that share, and 62% of calls fall between 12:00 and 17:59. The stance of -0.505 read as city data disagreeing with those studies, which the outcome does not test, and it is now null.

The notes now report the 864 calls without a usable district (583 with none and 281 with a park or airport code), the 23 calls of September 2026 that the calendar leaves out, and the cause of the negative binomial failure: the dispersion estimate for the high-AC half diverges and `count_fit` has no upper bound on it. We did not change `run.py`, which was fixed with the registration under rule 9. The notes also record that the negative point estimate comes from 2020 to 2026 (-0.112, -0.207 to -0.017, against 0.006, -0.062 to 0.075, for 2006 to 2019) and that it is -0.075 (-0.148 to -0.003) without Manhattan. Only 3% of calls fall before 06:00, and on the 06:00 day the estimate is -0.027 (-0.083 to 0.028).

### heat-school-out (stays unsettled)

The referee reproduced the window (2,260 weekdays, 7,199 shootings) and the estimate of 1.105 (0.997 to 1.224), and found four problems. We accept all four and the six recommended changes to the notes.

The first problem is the largest. Public holidays are dropped from the window, but the weekday after one is kept, and a shooting before 06:00 is counted on its calendar date. The twelve weekdays dated 5 July average 6.08 shootings before 06:00 against 0.89 on other days. These are the night of 4 July, counted as days out of school a week after classes end. Without the 74 weekdays that follow a public holiday the ratio is 1.060 (0.957 to 1.173), and on the 06:00 day it is 1.044 (0.951 to 1.146). On the log scale these remove 42% and 57% of the registered excess. The coordinator's brief described the excess as largely the night of 4 July; the figures support "about half", and the notes say that. The registered excess is entirely in shootings before 06:00: from 06:00 to 23:59 the ratio is 0.999 (0.890 to 1.120).

The estimate falls as the window widens, from 1.217 (1.057 to 1.402) at 21 days to 1.105 at the registered 42 and 1.024 (0.945 to 1.109) at 70. A lasting effect of the recess would not shrink in this way. The notes replace "a 10% rise" with the range across windows, 1.02 to 1.22, and say that the margin of 0.003 is smaller than the effect of the window, the error estimator, the remote-teaching years or a one-day change in the dates. About 8% of school-side days are closures, and high schools end regular classes before the registered last day; both bias the estimate towards 1. The window stacks 184 dates twice; with each date kept once the ratio is 1.114 (1.002 to 1.238). The reference to rule 10 in the earlier verdict note is dropped, because that rule concerns conditions on a point estimate.

The exploratory ratio of 1.40 (1.14 to 1.72) for shootings between 00:00 and 05:59 is corrected. Without the mornings after public holidays it is 1.18 (0.97 to 1.44), and counted with the preceding day it is 1.13 (0.96 to 1.32). Its block boundary differs from the registered table, it is the largest of four blocks chosen after the data, and a placebo transition inside the term gives 0.68 (0.50 to 0.93), so its nominal interval is too narrow. The notes now state the referee's finding that victims under 18 shift towards the hours before 06:00 more than adults do (interaction 2.04, 1.25 to 3.33, on 118 victims), as an exploratory result that needs its own registration.

The stance was 0.741. The graph holds no finding on school terms and shootings, and the one cited paper points the other way. The stance is now null, as the referee offered. The brief did not list this change.

We do not accept one recommendation as written. The referee proposes a rule for all claims on shootings by date that would count shootings before 06:00 on the previous date or drop the day after each excluded holiday. We accept the criticism, and the re-estimates are in the outcomes. We did not add a verdict rule, as in Round 5: under rule 4 a count chosen after the data cannot decide a verdict already given. New registrations on shootings by date should state the day.

### heat-extremes-downturn (stays contested, reworded)

The referee rebuilt the four daily series from the raw files, reproduced the pooled ratio of 1.035 (1.008 to 1.063), and found that the registered refutation condition, a lower limit above 1.00, is met. We accept the seven requested changes.

The result is now worded as "no downturn at 38 °C; the rate is level or slightly higher", and not as "assaults are more frequent at 38 °C and above". The two conditions were met with very different margins. The downturn band of 0.88 to 0.98 is excluded under every variant (z = 4.1 against 0.98). The lower limit above 1.00 is fragile, and the `verdict_note` and `prediction_scored` list where it fails: a Hartung-Knapp interval (0.992 to 1.081); the daily minimum in the model (1.019, 0.984 to 1.056); second weather stations (1.017, 0.987 to 1.049); the 06:00 day; without 2020 and 2021 (0.997); without 2018 (0.998); and without any one of Phoenix, Tucson and Austin. The registration assigned a plateau to unsettled, and the notes now say that the label contested follows from the literal condition. The reference to rule 10 is removed. A `stance_note` says that the stance of -0.857 measures disagreement with the registered downturn and not agreement with the graph's monotonic rise.

The notes now disclose that the four series are not the same offence. Dallas withholds family violence (35 of 23,334 incidents), and in Austin 47% of incidents are family violence or strangulation. The Austin split shows no difference: 1.039 (0.976 to 1.106) for family violence and 1.038 (0.976 to 1.104) for the rest. The notes record the break in the Phoenix file in September 2025. We could not find the reason the series was ended on 30 November 2025; neither the registration nor `build.py` gives one, and the notes say so. Ending it on 31 August 2025 gives the same estimate.

The statement that one curve in degrees fits the eight cities better than one in percentiles is withdrawn as evidence on adaptation. The bins were unequal. The difference is 496 AIC units with the registrant's bins and 43 with ten equal-count bins. A scale of degrees from each city's own mean fits as well as absolute degrees or better, and in the four hot cities alone percentiles fit better by 5 units.

The exploratory New York heat-wave ratio of 0.84 (0.74 to 0.95) is now marked as not replicating. The same code gives 0.98 (0.91 to 1.06) in Chicago and 1.04 (0.91 to 1.18) in Philadelphia, and the New York result depends on the 32 °C threshold.

### The 06:00 day

`analyses/critique/round6_six_am_solutions.py` refits the heat-solutions estimates with the functions of the registered `run.py`, and changes only the date an event is counted on. `analyses/critique/round6_six_am_extremes.py` rebuilds the daily files of the heat-extremes cities and runs the registered `test.py` and `describe.py` on them. Tucson publishes no time of day and is unchanged. The Phoenix file has no time after 2 September 2025, so that series ends on 31 August 2025. Philadelphia has the dispatch time only. Incidents at exactly 00:00 stay on their date in the assault series, because several portals use that time when the time is unknown. The calendar-date column of each script equals the registered results. The two documents carry fuller tables, and the JSON files in `data/derived/round6_heat/` hold every estimate.

| Quantity | Calendar date | Day from 06:00 to 05:59 |
|---|---|---|
| heat-ac-shootings, difference of slopes per 5 °C (support needs a lower limit above 0) | 0.043 (0.007 to 0.080) | 0.025 (-0.011 to 0.061) |
| The same on days of 27 °C or more | -0.178 (-0.329 to -0.027) | -0.133 (-0.284 to 0.017) |
| The same, income halves pooled | 0.034 (-0.007 to 0.076) | 0.023 (-0.018 to 0.065) |
| heat-ac-heat-calls, difference of slopes per 5 °C | -0.032 (-0.088 to 0.024) | -0.027 (-0.083 to 0.028) |
| heat-school-out, rate ratio for days out of school | 1.105 (0.997 to 1.224) | 1.044 (0.951 to 1.146) |
| The same, 21-day window | 1.217 (1.057 to 1.402) | 1.134 (0.997 to 1.290) |
| Shootings from 00:00 to 05:59, days out of school | 1.404 (1.144 to 1.723) | 1.126 (0.959 to 1.321) |
| Recess term in the all-year model | 1.139 (1.047 to 1.238) | 1.121 (1.036 to 1.214) |
| heat-extremes-downturn, pooled ratio (refutation needs a lower limit above 1.00) | 1.035 (1.008 to 1.063) | 1.030 (0.994 to 1.068) |
| Phoenix | 1.038 (0.994 to 1.084) | 1.044 (1.001 to 1.088) |
| Dallas | 0.977 (0.906 to 1.052) | 0.955 (0.887 to 1.028) |
| Austin | 1.040 (0.994 to 1.087) | 1.037 (0.991 to 1.085) |
| Slope per 5 °C above 35 °C, four hot cities | 1.003 (0.985 to 1.022) | 0.997 (0.978 to 1.016) |
| New York shootings, later days of a heat wave | 0.836 (0.739 to 0.946) | 0.812 (0.718 to 0.919) |
| Chicago and Philadelphia shootings, the same, pooled | 0.996 (0.935 to 1.061) | 0.950 (0.888 to 1.016) |

Two registered conditions change side on the 06:00 day. The support condition of heat-ac-shootings is not met (lower limit -0.011), and the registered rule would read unsettled. The refutation condition of heat-extremes-downturn is not met (lower limit 0.994; the referee's own fit gives 0.993), and the registered rule would read unsettled. Both verdicts are kept under rules 1 and 4, both outcomes state the 06:00 result in their verdict notes, and both were reported to the coordinator. The conditions of heat-ac-heat-calls and heat-school-out are on the same side under both definitions. The four checks are recorded in the file `conditions_on_six_am_day.json` in `data/derived/round6_heat/`.

The 06:00 day does not move every result in one direction. The district contrast and the school-recess excess become weaker, and the heat-call contrast and the shape of the assault curve stay as they were. The New York heat-wave ratio becomes stronger, and on the 06:00 day Chicago and Philadelphia point the same way as New York, with intervals that still include 1.

### What the round did not do

No new claim was registered. The candidates are the district contrast on days of 27 °C or more with income in the model, the shift of victims under 18 towards the hours after midnight, and the heat-wave contrast in three cities. No verdict rule for the 06:00 day was added. `run.py` and `build.py` were not changed. The dashboard export was not re-run. The reason for ending the Phoenix series on 30 November 2025 was not established.
