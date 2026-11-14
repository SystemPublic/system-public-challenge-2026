# Referee report: turn-calming-ped

Verdict recorded: confirmed (rule 1), with an exploratory placebo and a trend-adjusted ratio in the notes. I rebuilt the deciding ratio of ratios with separate code that does not import `analyses/turn_restrictions/` or `concord/`. The scratch code is outside the repository, in the session scratchpad folder `ref_turn/` (`build.py`, `est.py`, `decomp.py`, `checks.py`, `eb.py`, `eb2.py`). I used the registrant's raw extracts but none of their derived tables, and I read `docs/turn_restrictions.md` only after the re-estimates below were finished. This report also covers the points that the three turn-calming claims share; the reports for `turn-calming-leftturn` and `turn-calming-displacement` refer to it.

## Order of registration and data

The analysis script `did.py`, the site builder `sites.py`, `sites.json`, the power check and the fetch script were committed in bd2a8d9 at 13:17:58 on 13 November. The three registrations were committed in 85b40af at 13:18:40, and bd2a8d9 is its ancestor. The branches `origin/prereg/turn-calming-ped`, `-leftturn` and `-displacement` exist. `did.py` and `sites.json` have not changed since bd2a8d9. The two later commits before the outcome (711bddd at 13:23:45 and e9a887b at 13:53:45) change only the paging in `fetch_crashes.py`. The design has no resampling, so rule 9 has no seed to check.

The site-level crash extract `crashes.csv` was written at 13:43:23 and `left_vehicles.csv` at 14:01:50, both after the registration. The Socrata cache holds two vehicle-table queries made before it, at 13:16:11 and 13:16:29. Both are citywide aggregates: the distribution of `pre_crash` in January 2019, and the count of 'Making Left Turn' vehicles by year. They contain no site-level data. The crash-table queries in the cache between 13:07 and 13:12 cover a Manhattan box and the crosstown streets at 3rd and 9th Avenues. Their where-clauses match `analyses/street_space/peds_common.py`, so they belong to the busway agent. The outcome was decided at 14:04:20 and committed in bd2ae75 at 14:05:24. The order is as the registration states.

## Data

- VZV Turn Traffic Calming, `sm2x-35i7`, rowsUpdatedAt 2026-11-01T11:46:54Z. I pulled it myself: 1,601 rows, the same version the registrant used.
- Motor Vehicle Collisions - Crashes, `h9gi-nx95`. I used the registrant's raw extract, which was fetched at version 2026-11-12T14:31:25Z. A count against the current version (2026-11-13T14:30:16Z) with the same filter gives the same 1,798,550 rows, all with distinct collision ids.
- Motor Vehicle Collisions - Vehicles, `bm4k-52h4`, rowsUpdatedAt 2026-11-13T15:33:26Z. The extract has 227,926 rows and 207,891 distinct collision ids, and a count query on the current version gives the same two numbers. Paging by offset therefore lost or duplicated no rows.
- For the exploratory checks: VZV Leading Pedestrian Interval Signals, `xc4v-ntf4`, rowsUpdatedAt 2026-11-01T11:29:33Z, 6,810 rows, used as a pool of untreated signalized intersections.

I dropped records whose treatment label names a right turn or a bike island, or that have no date or location. I projected to UTM zone 18N (the registrant used an equirectangular approximation) and merged records within 40 m, earliest date first. This gives 1,207 sites, as in `sites.json`. I assigned crashes within 40 m, stacked cohorts by install quarter from 2016Q3 to 2023Q2, and used as controls the sites installed more than 24 months after the cohort quarter ends. I fitted the conditional Poisson model (a binomial GLM of the post share on cohort effects and a treated indicator) with site-clustered standard errors, and added a site-cluster bootstrap (400 draws) and a Mantel-Haenszel pooled ratio as checks.

## Re-estimate

| Pedestrians injured or killed within 40 m | Registrant | Referee |
|---|---|---|
| Registered ratio of ratios (95% CI) | 0.8482 (0.7787-0.9240) | 0.8486 (0.7790-0.9243) |
| Site-cluster bootstrap interval | not run | 0.777-0.926 |
| Mantel-Haenszel pooled ratio | not run | 0.848 |
| Treated sites; pedestrians before and after | 712; 1,966 and 1,706 | 711; 1,965 and 1,706 |
| 30 m radius | 0.8436 | 0.8422 |
| Cohorts avoiding March-June 2020 | 0.827 (0.737-0.928) | 0.828 (0.737-0.929) |
| Placebo, installation 12 months early (exploratory) | 0.9119 (0.8252-1.0078) | 0.9111 (0.8244-1.0068) |
| Trend-adjusted (exploratory) | 1.0279 (0.8207-1.2873) | 1.0303 (0.8226-1.2904) |

The numbers reproduce to the third decimal. The one-site difference comes from the projection, which moves one pair of records across the 40 m merge threshold. support_if (upper bound below 1.00) is met by 0.076 and is not close under any variant I ran.

## The placebo, and what it shows

Under the rules, the verdict follows. support_if is met, and rule 4 prevents the placebo, which was written after the data, from deciding anything. Rule 11 applies only to registered placebos.

Had the placebo been registered, rule 11 would have made the verdict `unsettled`. The placebo itself narrowly misses support_if (upper bound 1.007 against 1.00), but the estimate does not discriminate from it. Against the placebo as the null, the difference of log ratios is -0.071 with a combined standard error of 0.067, so z_null is 1.06. The distance from the predicted midpoint (0.881) is z_chain = -0.86. D = 1.12 - 0.73 = 0.39, far short of 4.

To see where the placebo comes from, I compared each arm with 4,713 untreated signalized intersections: points from the LPI list, merged within 40 m, and more than 150 m from any calming record. I used the same calendar months for both. Each figure below is the arm's post/pre ratio divided by the pool's post/pre ratio.

| Pedestrians, 40 m (exploratory) | Treated sites | Later-treated controls | Crude ratio of ratios |
|---|---|---|---|
| Registered windows (-24..-1 against +1..+24) | 0.898 | 1.021 | 0.880 |
| Placebo windows (-24..-13 against -12..-1) | 0.945 | 1.032 | 0.916 |

Both arms contribute. Treated sites decline relative to untreated intersections, and the later-treated controls rise slightly. The event-time profile of treated sites shows that the decline is a long trend and has no break at installation. Below, each row gives the treated sites' pedestrian count per month as a multiple of the untreated pool's mean, for installations from 2017 to 2023.

| Months from installation | -48..-37 | -36..-25 | -24..-13 | -12..-1 | 0..11 | 12..23 | 24..35 |
|---|---|---|---|---|---|---|---|
| Treated / pool | 2.96 | 2.82 | 2.72 | 2.58 | 2.44 | 2.32 | 2.31 |

The ratio falls by about 3.5% to 5% a year for the three years before installation and continues at the same rate for two years after it. No pre-installation peak and no step at installation appear. A 25-month extrapolation of the placebo-year change (0.945 per 12 months) predicts 0.889 for the treated arm, and the observed value is 0.898.

The note's explanation is that treated sites are past their crash peak while later-treated sites are still approaching theirs. It predicts that controls installed long after the cohort, whose windows are far from their own selection, would show less bias. They show more. With controls installed more than 36 months after the cohort, the registered ratio is 0.828 and the placebo 0.890. With controls installed more than 48 months after it, the ratios are 0.803 and 0.859. The comparison is therefore between populations of sites with different long-run trends, not chiefly regression to the mean around a selection peak. The treatment labels show the populations directly. Sites installed in 2016-2020 carry Quick Kurb, rubber speed bump and daylighting labels, sites installed in 2019-2021 mostly carry hardened-centerline labels, and every site installed from 2022 onwards is labelled 'Left Turn Treatment'. The early cohorts are thus compared with a later programme at different intersections. For the 363 early-programme treated sites, the registered ratio is 0.841 and the placebo 0.839, the same number.

## Empirical Bayes before-after (exploratory)

I fitted negative binomial safety performance functions on site-years of the untreated pool, with calendar-year effects, and applied the EB method (Hauer 1997; HSM Part B) to the treated sites. The first SPF used a volume proxy: the site's mean annual count of crashes with no pedestrian injured and no left-turning vehicle. The second used crash history from 2014-2015, a period outside every analysed window, applied to installations from 2018 onwards.

| EB index θ for pedestrians (95% CI) | Volume-proxy SPF | Crash-history SPF |
|---|---|---|
| Treated, registered windows | 1.139 (1.072-1.207) | 1.112 (1.041-1.183) |
| Treated, placebo 12 months early | 1.296 (1.196-1.397) | 1.363 (1.253-1.473) |
| Untreated pool, false installation July 2019 | 0.987 (0.950-1.024) | 0.981 (0.944-1.017) |

The method behaves correctly on the pool, where θ is close to 1. It fails its own placebo at the treated sites. θ is 1.30 to 1.36 in a year with no calming, because the SPFs predict about 60% fewer pedestrian injuries at treated sites than they have. The excess is persistent, so EB shrinks the before counts too far and under-predicts the after period. The open data hold no pedestrian volume, and without it no SPF I could fit describes these intersections. The EB result is therefore uninformative about the effect. It does show that most of the treated sites' excess over the pool is real and not random, which leaves little room for classic regression to the mean. That fits the steady-trend reading above.

## Cohort stacking, controls and geocoding

- Stacking. 23 cohorts, 711 treated sites and 961 control sites, with controls recurring across cohorts. Clustering by site handles the recurrence. The cohort ratios vary widely: 0.61 for the 2019 cohort (219 to 93 pedestrians, with post windows covering the 2020 lockdown) and 1.18 for the 2020 cohort. The 2022 cohort (183 sites) carries the most weight.
- Controls. A control's post window ends at most two months before its own installation, so DOT's selection period and the control's post window overlap. Lengthening the gap does not reduce the bias, as reported above. The problem is that the later sites are a different population with a different trend, and a longer gap does not change that.
- Co-installation. 193 of the 772 treated cohort sites have more than one calming record. Because the earliest date is used, the later records fall in the post window and do not touch the pre window.
- Geocoding. NYPD coordinates are snapped to intersection nodes. Of the crashes within 80 m of a site, 131,545 lie within 5 m of the site point, against 2,890 at 5-10 m. The median distance from a site to its modal crash coordinate is 0.7 m, and only 2.9% of sites are more than 40 m from it. The calming points are therefore at the nodes, and the 40 m radius effectively counts crashes coded to that intersection. This is why the 30 m and 60 m radii give almost the same ratios (0.842 and 0.853). The radius check cannot detect crashes snapped to the wrong node.

## Does docs/turn_restrictions.md claim more than the numbers support?

The tables match the outcome files and my re-estimates, and the section on the placebo is clear. Four statements go further than the numbers.

- "The data agree with DOT's reported -18% and with the literature's direction." The registered ratio agrees in size. The placebo, the trend adjustment and the event profile show that the design returns about -9% where no calming exists, and the event profile shows no change at installation. The data are consistent with DOT's figure and equally consistent with no effect.
- "The true effect probably lies between the registered ratio and 1." Nothing supports the bound at 1. The trend-adjusted ratio is 1.03 (0.82-1.29), and the profile continues unchanged across installation. An effect of zero, or a small increase, fits as well as -15%.
- The mechanism ("treated sites are past their peak while later-treated sites ... are still approaching theirs") is stated as the likely cause. The control-gap variants argue against it, and the profile shows no peak. The note should say that early- and late-treated sites follow different long-run trends, for reasons the data do not identify.
- "There is no sign that injuries moved to the next intersection." This is addressed in the displacement report. The ring has the same placebo problem, and displacement of up to about +23% is not excluded.

## Recommendation

1. Keep `confirmed` under rules 1 and 4. The placebo was not registered, and a rule written now that let an unregistered check void a verdict would undo rule 4: any later analysis could then unseat any result. A retroactive rule is the wrong response here.
2. Mark the verdict wherever it appears, on the dashboard and in the concordance counts, with the placebo (0.911, 0.824-1.007) and the trend-adjusted ratio (1.03, 0.82-1.29) beside it. Do not count its stance (0.955) as agreement with DOT or the literature in any summary. State in `prediction_scored` that the result is a hit on the registered condition and no evidence of a calming effect.
3. Register a successor claim (`turn-calming-ped-v2`) before any crash data after September 2026 are read. It should use a comparison that is not a later programme: the untreated signalized pool by borough, with site-specific pre-trends over months -60 to -1. It should test for a change in level or slope at installation, include placebo installations at -12 and -24 months as registered validity conditions under rule 11, and decide on post months from October 2026 onwards for the sites installed in 2024Q4-2026Q3. The historical break-in-trend test can be reported now, but only as exploratory.
4. Separately, a forward-only rule is useful: a before-after design at sites selected for treatment must register a pre-period placebo, so that rule 11 can operate. It should bind registrations made after it and change no past verdict.
