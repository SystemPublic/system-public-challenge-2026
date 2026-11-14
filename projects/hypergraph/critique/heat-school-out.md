# Referee report: heat-school-out

Verdict recorded: unsettled. Recommendation: keep the verdict, and change the notes as listed at the end.

Referee code: `analyses/critique/referee_heat_school_out.py`. It rebuilds the school-window series from the cached incident and victim queries and the cached Central Park file with its own code, imports nothing from `analyses/heat_solutions`, prints its results and writes no file. I did not read `docs/heat_solutions.md` or any other write-up of this claim.

## (a) Does the verdict follow from the registered conditions?

Yes. Support needs a 95% lower limit above 1.00. Refutation needs an upper limit below 1.10 with a lower limit at or below 1.00. The estimate is 1.105 (0.997 to 1.224). The lower limit is below 1.00 and the upper limit is above 1.10, so neither condition is met and the registration says unsettled. The outcome states the margin of 0.003, as rule 10 requires.

Nothing in the deciding number was chosen after the data. The registration names `run.py` by hash (ff13670222b73baa), and the file at commit 481093e has that hash. `common.py` in the working tree has the registered hash. The working copy of `run.py` differs from the registered one in two lines, the reading of the hour for incidents and for victims. The outcome says one line. The hour does not enter the primary model, which uses the date only, and the incident file has no unpadded time; the 390 unpadded times are in the victim file. The change cannot have affected the deciding number.

The timestamps are in order and close together. The registration is stamped 07:52:12 and its commit on `origin/prereg/heat-school-out` is at 07:53:09. The incident query with dates, times and coordinates was fetched at 07:53:21 and the victim query at 07:53:24. The outcome was decided at 07:58:34. Twelve seconds separate the commit from the fetch, and git records the commit time and not the push time. Before registration the cache held daily counts of shootings (fetched on 12 November and again at 07:48:57 on 13 November for the design) and the incident times fetched at 01:24:57 for heat-night-minimum. The registration discloses both under `already_seen`. I found no script that joins either to a school calendar before 07:53.

The registered expected standard error was 0.045. The realised one is 0.052, so the test had somewhat less power than the registration said.

## (b) Errors in code, units, joins, dates, geography or uncertainty

Every number I checked reproduced. My window has the same 2,260 weekdays, the same 1,125 days out and the same 7,199 shootings, with identical counts on every row. My refit gives 1.105 (0.997 to 1.224), 1.217 (1.057 to 1.402) for 21 days, 1.106 (0.998 to 1.224) with quadratic trends, 1.067 and 1.131 for the end and the start, and the four exploratory hour blocks to the third decimal.

I found four problems. The first is the largest.

**1. Shootings before 06:00 are counted on the calendar date, and the night of a public holiday then falls on a recess weekday.** Public holidays are dropped, but the day after one is kept, and it carries the holiday night's shootings after midnight. The twelve weekdays dated 5 July in the window have a mean of 6.08 shootings before 06:00, against 0.89 on other days, and 8.83 shootings in all, against about 3.2. These are the night of 4 July. They are coded as days out of school about a week after the last day of classes. The window has 74 weekdays that follow a public holiday, 29 of them out of school.

| Variant | Rate ratio, out against school |
|---|---|
| Registered | 1.105 (0.997 to 1.224) |
| Without the weekday after a public holiday | 1.060 (0.957 to 1.173) |
| A term for the weekday after a holiday | 1.078 (0.976 to 1.190) |
| Shootings before 06:00 on those days removed | 1.022 (0.924 to 1.130) |
| Shooting days from 06:00 to 05:59, weekdays chosen by shooting day | 1.044 (0.951 to 1.146) |
| Calendar date, shootings from 06:00 to 23:59 only | 0.999 (0.890 to 1.120) |
| Without 1 to 8 July | 1.069 (0.962 to 1.188) |
| Without 1 to 8 July and the week before Labor Day | 1.046 (0.938 to 1.166) |

The whole of the registered excess is in shootings before 06:00. From 06:00 to 23:59 the ratio is 1.00. About half of the excess goes when the mornings after holidays are left out.

**2. The estimate depends on the window, and it does not behave like a step.** The registration fixed 42 days and reported 21. I ran nine widths.

| Half-width (days) | Rate ratio |
|---|---|
| 14 | 1.169 (0.992 to 1.379) |
| 21 | 1.217 (1.057 to 1.402) |
| 28 | 1.167 (1.030 to 1.322) |
| 35 | 1.126 (1.006 to 1.260) |
| 42 | 1.105 (0.997 to 1.224) |
| 49 | 1.079 (0.981 to 1.186) |
| 56 | 1.071 (0.981 to 1.170) |
| 63 | 1.052 (0.968 to 1.144) |
| 70 | 1.024 (0.945 to 1.109) |

The lower limit is above 1.00 at 21, 28 and 35 days and below it at 14 and at 42 or more. A persistent effect of the recess would not shrink as the window grows. Leaving out the days within 7 days of a transition gives 1.055 (0.910 to 1.224), and within 10 days 0.961 (0.820 to 1.125). The raw means show why. Around the end of term, shootings before 06:00 average 0.71 to 0.80 per weekday until two weeks before the last day, 1.15 in the last eight days of term, 1.59 in the first week of recess, 1.44 in the second, and 1.02 to 1.08 from the third week to the sixth. The excess is a peak of about two weeks around the turn of June and July. It is not a change of level that lasts through the recess.

**3. Some school-side days are not school days, which biases the estimate towards 1.** The registration says closures inside the term are counted as school days. In the windows covered by the attendance file (September 2006 to June 2019) I count 66 school-side weekdays with no attendance record outside the last 12 days of term: Anniversary Day, Clerical Day, Eid, Rosh Hashanah and Yom Kippur. That is about 8% of the school-side days. Dropping them gives 1.139 (1.004 to 1.291) against 1.153 (1.019 to 1.305) for the same years as registered; counting them as out gives 1.083 (0.977 to 1.202). The attendance file also lacks 86 weekdays in the last 12 days of term. I could not establish why. High schools hold Regents examinations and no regular classes from about the middle of June, so for students of high-school age classes end one to two weeks before the registered last day. Leaving out the 10 days before the last day gives 1.186 (1.058 to 1.329). This variant was chosen after I saw that those days run high, so it is not evidence for the claim. It shows that the date of the transition is uncertain by more than a week for the age group the claim is about.

**4. 184 dates appear twice.** The end window runs to about 7 August and the start window begins about 28 July, so the days between are stacked in both, as days out of school. HC0 errors treat the two copies as independent. With errors clustered by date the interval is 0.995 to 1.227; with each date kept once it is 1.114 (1.002 to 1.238). The September 2026 window has only days out of school (the data end on 31 August) and contributes nothing; dropping it changes nothing.

The school calendar is correct where I could check it. The first and last days for 2006-07 to 2018-19 equal the first and last dates in the attendance file, except June 2014, where the file ends on 16 June as the code comment says. I checked the Department of Education calendars or reports of them for 2019-20 (5 September 2019, 26 June 2020), 2020-21 (remote days from 16 September, blended teaching from 21 September 2020, last day 25 June 2021), 2021-22 (13 September 2021, 27 June 2022), 2025-26 (4 September 2025, 26 June 2026) and September 2026 (10 September). All agree with `common.py`. I did not check June 2006, 2022-23, 2023-24 or 2024-25 against a source. Moving every transition one day earlier gives 1.143 (1.032 to 1.266) and one day later 1.083 (0.977 to 1.201), so a one-day error would move the lower limit across 1.00. The federal holiday list in the installed pandas includes Juneteenth from 2021, so 18 June 2021 and the later Juneteenth dates are dropped as the registration describes.

The verdict margin of 0.003 is smaller than the effect of any of these choices. Variants of the standard error and the years:

| Variant | Rate ratio |
|---|---|
| Poisson, HC0 | 1.106 (0.998 to 1.226) |
| Negative binomial, model-based errors | 1.105 (1.003 to 1.217) |
| Clustered by transition | 1.105 (0.998 to 1.223) |
| Clustered by year | 1.105 (0.993 to 1.229) |
| Separate slopes on each side | 1.107 (1.000 to 1.225) |
| TMAX squared and previous day's TMAX added | 1.116 (1.007 to 1.236) |
| With the 2020 and 2021 transitions | 1.102 (1.001 to 1.213) |
| 2006 to 2019 | 1.155 (1.025 to 1.300) |
| 2022 to 2026 | 0.953 (0.765 to 1.187) |
| Leave one year out, range of the lower limit | 0.973 to 1.019, above 1.00 in 7 of 20 |

The lower limit lies between 0.97 and 1.02 across them. The registered rule was applied as written and the verdict is unsettled. Had the remote-schooling transitions been kept, or model-based errors used, the same data would have read confirmed. With the mornings after holidays removed, every one of these variants is unsettled again (1.060, 0.964 to 1.166 with 2020 and 2021; 1.115, 0.991 to 1.254 for 2006 to 2019).

## (c) Is the comparison with the research fair?

There is no research effect to compare with. The graph holds one study, on referrals to domestic violence services in England and Wales, and the outcome sets `graph_effect` to null. The one cited paper (Jacob and Lefgren 2003) is cited from memory and reports more juvenile violent crime on days when school is in session, which is the opposite direction to the registered claim. The registration predicted a positive sign with a best guess of 1.02 and gave "confirmed" a prior of 0.12, so the claim is a test of the registrant's own conjecture. The stance of 0.741 (z = 1.9) will place this claim well towards agreement on the dashboard strip. With no research finding behind it and the problems in (b), a null stance or a note beside it would be more accurate.

The registered side analysis for heat-shootings (the recess term removes 1.5% of the log slope) is a fair use of the calendar. I did not test whether the recess term of 1.139 (1.047 to 1.238) also carries the mornings after 4 July; the `hol` term covers the holiday date and not the following morning.

## (d) Which alternative explanation is not addressed?

The first rival is season. The registration names it and the outcome's verdict note says the rise may be the season. My checks do not separate the two. On Saturdays and Sundays in the same windows, when school is out on both sides, the ratio is 1.011 (0.895 to 1.142). The difference between weekdays and weekends is 1.092 (0.930 to 1.282) in a model with weekday-specific trends and weather, and 0.956 (0.885 to 1.032) in a model that shares them. Placebo transitions 22 to 35 days inside the term or inside the recess, with 21-day windows that contain no real transition, give ratios from 0.912 to 1.085, against 1.217 at the real dates; none is separated from 1. For 1 to 14 September, where the first day of classes moves between 2 and 13 September and the same day of the month is in and out of school in different years, the ratio is 1.253 (0.867 to 1.810) on 171 weekdays. These are compatible with a school effect and with none.

The second rival is calendar events. This is the registered rival that the outcome does not address, and it accounts for the largest part of the estimate (problem 1). The night of 4 July falls on a recess weekday about a week after the last day. The week before Labor Day falls just before the first day.

The exploratory ratio of 1.404 (1.144 to 1.723) for 00:00 to 05:59 reproduces. The outcome labels it "Exploratory, after the results", which is correct. It is the largest of four blocks, chosen after the data, and the block boundaries differ from the registered table of victims by hour, which used 00:00 to 07:59. Corrected for four blocks its p-value is 0.005. The larger problem is the holiday nights. Without the mornings after public holidays the ratio is 1.182 (0.970 to 1.440). On shooting days, for Monday to Thursday nights, it is 1.171 (0.938 to 1.461). A placebo transition 28 days inside the term gives 0.681 (0.499 to 0.927) for this block, so the linear trends do not describe how shootings after midnight grow through May and June, and the nominal interval is too narrow. The block also rises on weekend dates in the same windows, 1.100 (0.926 to 1.306), which answers the second `research_needed` question: the data do not show that the excess is specific to weekdays. The figure 1.40 should not be quoted as a recess effect. A figure near 1.18 with an interval that includes 1 is what the data support once the night of 4 July is set aside.

The outcome JSON does not state the result that victims under 18 shift to the hours after midnight. That result rests on the registered table `hourly_under18.csv`, and the table has 16 cells and no intervals. The table shows 51 victims under 18 between 00:00 and 07:59 on school days and 108 on days out. The other age groups move the same way (18 to 24: 375 to 615; 25 or older: 632 to 837). In my count models the ratio for victims shot before 06:00 is 3.56 (1.52 to 8.33) for under 18, 1.57 (1.13 to 2.18) for 18 to 24 and 1.35 (1.04 to 1.76) for 25 or older; from 06:00 to 23:59 all three are near 1.00. Without the mornings after holidays they are 2.19 (0.88 to 5.41), 1.31 (0.94 to 1.83) and 1.14 (0.88 to 1.48). The share of under-18 victims shot before 06:00 is 8.5% on school days and 21.1% on days out without those mornings, and the interaction of out with under 18 in a model of that share is 2.04 (1.25 to 3.33). So victims under 18 do shift towards the hours after midnight more than adults do, on 118 victims. This is the one result here that points to school-age youth in particular. It was found after the data, among at least 16 cells and 4 blocks, it has no control for season beyond temperature and year, and it needs its own registration. Any write-up that states it should give the counts and call it exploratory.

In all, the outcome reports about ten registered secondary estimates, a 16-cell table and four exploratory hour blocks. Only the 21-day window (p = 0.006) and the 00:00 to 05:59 block have intervals that exclude 1, and neither would survive both a correction for that number and the removal of the mornings after holidays (21 days: 1.170, 1.014 to 1.350, p = 0.03).

## (e) Could the test have failed?

The test could have failed. The registration computed D = 4.49 for a ratio of 1.10 and a probability of 0.56 of meeting the refutation rule if there were no effect. The estimate is z = 1.90 from no effect, z = 1.53 from the best guess of 1.02 and z = 0.43 from the upper end of the predicted range (1.08). The prediction is scored a miss because the point estimate is above the range; the interval contains the whole range above 0.997. With the mornings after holidays left out, the estimate of 1.060 is inside the predicted range and z against no effect is 1.12.

The refutation rule is not met under any variant I ran: the smallest upper limit is 1.109 (70 days). The support rule is met under some variants and not under others, which under rules 2 and 9 leaves the verdict unsettled.

## Recommended changes to the notes

1. State that the registered estimate counts the night of 4 July on 5 July, a recess weekday, and give 1.060 (0.957 to 1.173) without the weekday after a public holiday and 1.044 (0.951 to 1.146) on shooting days.
2. State that the excess is entirely in shootings before 06:00 (06:00 to 23:59: 0.999, 0.890 to 1.120) and that it is a peak of about two weeks around the turn of June and July.
3. Replace "a 10% rise" as the summary with the range across windows, 1.02 to 1.22, and say that the margin of 0.003 is smaller than the effect of the window, the error estimator, the remote-schooling years and a one-day change in the dates.
4. Say that two lines of `run.py` were changed, not one.
5. Give the 00:00 to 05:59 block as 1.18 (0.97 to 1.44) without the mornings after holidays beside 1.40, and note that the block boundary differs from the registered table.
6. Record that about 8% of school-side days are closures and that high-school classes end before the registered last day; both bias the estimate towards 1.
7. Consider a rule for all claims on shootings by date that would either count shootings before 06:00 on the previous date or drop the day after each excluded holiday. The same point arose in the report on heat-night-minimum.

Sources for the calendar check: [2026-27 school year calendar](https://www.schools.nyc.gov/calendar/2026-2027-school-year-calendar), [2025-26 school year calendar](https://schools.nyc.gov/calendar/2025-2026-school-year-calendar), [2020-21 calendar for families](https://schools.nyc.gov/docs/default-source/default-document-library/school-calendar-for-families-2020-2021), [Chalkbeat on the 13 September 2021 start](https://chalkbeat.org/newyork/2021/5/4/22418922/nyc-first-day-school-september-13), [2021-22 calendar](https://temp.schools.nyc.gov/docs/default-source/default-document-library/doe-calendar-sy-21-22).

Recommendation: keep the verdict (unsettled), with the notes changed as above.
