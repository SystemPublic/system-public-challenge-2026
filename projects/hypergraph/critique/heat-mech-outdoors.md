# Referee report: heat-mech-outdoors

Verdict recorded: confirmed. Recommendation: keep the verdict, and add the period split and the next-day control below to the notes.

Scratch code and output: `referee-heat-mech-outdoors/ref.py`, `boot.py` and `boot.out` in the session scratchpad. All re-estimates read `data/derived/graph/heat_mechanisms/mediators_daily.csv`.

## (a) Does the verdict follow from the registered conditions?

Yes. Confirmation required three things: the proxy's IRR per 5 C with a lower limit above 1 (1.330, 1.317 to 1.343), a positive proxy coefficient in the shootings model with a lower limit above 0 (0.229, 0.181 to 0.277), and A of at least 0.25 with a lower bootstrap limit above 0.10 (0.440, 0.327 to 0.564). The registered tripwire was the year-by-month variant, which gives 0.322 (0.214 to 0.438) and stays on the same side of 0.25. The prediction score of partial is correct, because A is above the registered range of 0.10 to 0.35.

Nothing was decided by a measure chosen after the data were seen. The range-by-range result (no attenuation from 27 to 33 C) is labelled exploratory in the notes and takes no part in the verdict.

The timestamps are in order. The registration was committed at 22:21:54 on 12 November 2026 (commits 1c25636 and 7a5eca1), and the branch `prereg/heat-mech-outdoors` exists on the remote at 7a5eca1. The daily 311 queries were fetched at 22:25:41 and 22:33:30 and the bicycle queries from 22:37:28 to 22:44:34. The outcome was decided at 23:34:28. The shootings and weather series were fetched earlier that day, and the registration discloses this. Three earlier cache files for erm2-nwe9 mention the street-noise complaint type; I opened them and they hold totals by type, counts by latitude and longitude, and one address search, with no daily series. Git records the commit time and not the push time, so I cannot show from the repository that the branch reached the remote before 22:25.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error in the code. My refit gives A = 0.440 from b0 = 0.1406 and b1 = 0.0787 on 6,087 days, and a week bootstrap with a different seed (300 resamples) gives 0.321 to 0.562. The series covers every day from 1 January 2010 to 31 August 2026, with one zero day. Complaint volume rises from 50 a day in 2010 to 565 in 2020; year terms and the log transform absorb the level.

Variants the registrant did not run:

| Variant | A | Interval or note |
|---|---|---|
| Primary, refit | 0.440 | 0.321 to 0.562 |
| 2010 to 2019 only | 0.242 | 0.142 to 0.373 |
| 2022 to 2026 only | 0.842 | 0.512 to 1.359 |
| Year-by-month and week-of-year terms | 0.305 | 0.204 to 0.416 |
| Week-of-year terms in place of month | 0.427 | |
| TMIN, previous-day TMAX and rain amount added to both models | 0.516 | of a smaller base slope (0.095) |
| Friday to Sunday; Monday to Thursday | 0.497; 0.446 | |
| Top and bottom 0.5% of complaint days removed | 0.419 | |
| EMS drug dispatches already in both models | 0.455 | |
| Days with TMAX below 27 C | 0.496 | |
| Days with TMAX of 24 C or more | -0.044 | |
| Next-day complaints in place of same-day (negative control) | 0.104 | 0.051 to 0.159 |
| Complaints seven days later; seven days earlier | 0.007; 0.004 | |

Two of these matter. The share is not stable over time: it is 0.24 in the ten years before 2020, just under the 0.25 threshold, and 0.84 after 2021. The pooled 0.44 is an average over two different regimes of 311 use, and the registered sensitivity that drops 2020 and 2021 (0.335) does not show this. The second is the negative control. Tomorrow's complaints cannot be caused by today's street activity, and they still remove 0.10 of the slope. Part of the same-day share therefore comes from variation that complaints and shootings share over a few days. It is a small part, since the share from complaints a week away is zero.

The interval for A holds the dispersion fixed and resamples weeks, as registered. This is adequate.

## (c) Is the comparison with the research fair?

The direction comparison is fair only in a loose sense. I checked Kim et al. 2022 (PMID 36444549) against its PubMed abstract: the odds ratio of walking practice per 1 C of daily maximum temperature is 0.95 (0.94 to 0.97) in rural areas and 0.98 (0.97 to 1.00) in urban areas, as the registration says. The study is a cross-sectional survey of habitual walking (30 minutes a day on five days a week) against the mean maximum of the preceding seven days in Korea. The city measure is a daily count of complaints about noise. Outcome, exposure window, unit and scale all differ, and the urban value (0.98, upper limit 1.00) is the relevant one for New York, not the rural value recorded in `graph_effect`. No size comparison can be made. The graph holds no finding for the second link (street activity to violence), so the attenuation has nothing to be compared with.

## (d) Alternative explanation not addressed

The registration names open windows, shared causes within a month and physiology. It does not name a change in what a complaint measures. After 2020 the complaint count is four to ten times its 2010 to 2014 level and removes most of the slope; before 2020 it removes a quarter. Either the proxy became a better measure of street gatherings, or complaints after 2020 respond to the same gatherings and disorder that produce shootings (and to police presence), which is a common cause and not a step from heat. The data here cannot separate the two. A second point is that bicycle counts and public-drinking complaints, which also rise with heat, remove 0.04 and 0.03. The claim that people outdoors is the step rests on one proxy out of three.

## (e) Could the test have failed?

Yes. The registered prior was 0.30, the predicted range for A was 0.10 to 0.35, and two other proxies in the same run gave shares near zero. A is 7.3 standard errors from zero and 3.1 from the 0.25 threshold (bootstrap standard error 0.060). It is 3.6 standard errors above the middle of the predicted range, so the prediction of size was missed on the high side. On the 2010 to 2019 data alone the claim would have been unsettled (A = 0.242, below 0.25).

Recommendation: keep. The registered conditions are met and the tripwire variant agrees, but the notes should state that the share is 0.24 before 2020 and 0.84 after 2021 and that next-day complaints remove 0.10.
