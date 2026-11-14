## Round 6: three reports on the congestion-toll claims

Fresh referee agents reviewed crz-storefront-vacancy, bridge-crz-ems-travel and sim-crz-holdout-2026 on 13 November 2026, under the same conditions as Rounds 4 and 5. Each had the registration, the outcome, the code and the data, and did not read the write-ups. A different agent from the registrants wrote these answers, and "we" below is that agent. It re-ran the two referee scripts (`analyses/critique/referee_crz.py` for the vacancy and ambulance claims, and `analyses/critique/referee_sim_holdout.py`), which printed every referee figure quoted here. `analyses/critique/answer_round6_crz.py` applies the answers through `concord.claims.revise`, which keeps each earlier outcome in `history`. No registration was changed.

One verdict changed. bridge-crz-ems-travel went from confirmed to unsettled under rule 8. The other two verdicts are kept under rule 1, each with a `verdict_note` that says what the label covers. Among the three claims there were 2 confirmed and 1 contested before the round, and there are 1 confirmed, 1 unsettled and 1 contested after it.

### bridge-crz-ems-travel (confirmed to unsettled)

The claim is a bridge: a prediction composed from two links and checked at an endpoint. It composed the measured rise in taxi speed in the zone with a pre-toll elasticity of ambulance travel time to taxi speed, and predicted that peak ambulance travel time in the zone would change by about -1.7% relative to the rest of the city. The estimate is -0.9% (-3.0 to +1.4) over 32 months.

The referee objected that the registered support condition measured discrimination against a fall in proportion to speed (-5.4%), where D is 17.0, and that rule 8 defines D against no effect, where it is 0.14. D is the difference between the squared standardised distances of the endpoint from no effect and from the composed prediction, and rule 8 requires at least 4. We accept this, and the verdict is unsettled. Rule 1 lets a registration's conditions decide a verdict. Rule 8 is the exception for bridges with an endpoint test, and it says that a test that does not discriminate gives unsettled however well the endpoint matches. The registration named rules 1, 2 and 8 for its verdict and could not replace the D that rule 8 defines. Round 4 moved graph-triad-cold-asthma-absence in the same way at D = 3.0. That round kept graph-concordance-matrix because it is not a bridge, and that reason is not available here. The registrant had written in the plan that the test could not tell the chain from no effect, so the change corrects the label. The registrant's account of the test was accurate.

The referee simulated the registered rule at the observed standard error. It returns confirmed with probability 0.80 if the toll had no effect, 0.87 if the chain is true, 0.50 if travel time rose by 1%, and 0.01 if it fell in proportion to speed. Any estimate from -3.04% to +0.99% met the support condition. We reproduced these values.

We accept the referee's further findings, and the outcome now records them.

- The one thing the registered estimate establishes, that travel time did not fall in proportion to speed (z = 4.18), does not survive a linear trend in the two pre-toll years. The estimate is then -3.13% (-7.47 to +1.42), 1.03 standard errors from the proportional fall. The trend term was chosen after the data and decides nothing under rule 4.
- The registered interval is too narrow. The same estimator at 17 false start dates in 2023 and 2024 gives -0.2% to +4.9%, with a standard deviation of 0.016 on the log scale against a standard error of 0.011.
- The overnight control argues against the toll as the cause. In overnight hours, when the toll is a quarter as large, the zone's relative travel time fell by 4.0% (1.7 to 6.3). Peak minus overnight is +3.3% (+1.4 to +5.2), 4.0 combined standard errors from the composed prediction. The overnight series is itself unstable before the toll, so we do not read it as showing that the toll slowed ambulances.
- The elasticity link is unstable: -0.32 as registered, -0.62 without the pandemic months, -0.49 for 2022 to 2024 and -1.13 for 2023 and 2024. The overnight ratio has nearly the same slope (-0.29) as the peak ratio.
- The number of lives has no determined sign. The registered peak estimate gives +0.3 a year (-0.7 to +2.0), peak minus overnight gives -1.4 (-4.1 to -0.2), and total response time gives -0.3 (-4.6 to +2.9). The outcome now says that the figure is not a result and gives the range as about -1.5 to +2.

Two smaller points are recorded and not corrected. The zone's ZIP list includes Roosevelt Island (10044), which is outside the toll zone; with the zone defined by dispatch areas the estimate is -0.79% (-3.10 to +1.59). The script was fixed with the registration under rule 9. The prediction is quoted as -1.68% (the median of the draws) in the statement and as -1.8% (from the mean of the log) in the notes, and the notes now say which is which.

The stance was already computed under rules 7 and 8 and stays at 0.04.

### crz-storefront-vacancy (stays confirmed, on the registered comparison only)

The claim predicted that the share of storefronts vacant in the zone would not rise relative to the rest of the city in the first year. The estimate is -0.47 points (-1.08 to +0.17) and both registered support conditions are met. The referee reproduced the numbers, found the conditions still met in four variants (-0.76, -0.36, -0.47 and -0.46), and recommended keeping the verdict with a narrower label. We keep confirmed under rule 1 and accept the label. The `verdict_note` now says the following.

- Vacancy in the zone itself rose by 0.2 points. The negative difference comes from a rise of 0.65 points in the rest of the city.
- A rise of 1.2 points relative to the whole rest of the city is ruled out, counting sampling error only. Smaller rises are not ruled out.
- The rise is not excluded against the zone's earlier trend (the 2025 value is +0.39 above the mean of 2022 to 2024, with an upper bound of +1.66) or against downtown Brooklyn and Long Island City (+1.09, -0.60 to +2.85).
- The registry changed its filing structure from reporting year 2023, so the 2023 pre-trend value (-1.40, or +1.14 with the new February filing added) spans the change and 2024 is the only clean pre-toll year. The mean of three earlier years (-0.86) is withdrawn from the notes.
- The threshold of 1.2 points is the resolution of the test, set from the design run before the 2025 values were seen. It is not an effect size from the literature. The two papers in the registration were cited from memory and are unverified. The outcome records this in `literature_note`, since the registration cannot be edited.

Sales, rents and effects that take more than one lease cycle are not tested. The stance is unchanged.

### sim-crz-holdout-2026 (stays contested, with the note rewritten)

The claim tested, on January to June 2026, two links fitted on 2025: zone taxi speed on vehicle entries, and ambulance travel time on taxi speed. The held-out slope of the first link was 0.29 (0.19 to 0.38) of the fitted value, below the registered limit of 0.5.

We keep contested under rule 1. The condition is met, it stays met with the error of the fitted elasticity carried (0.11 to 0.46), and no rule allows a day to be excluded after the data. We accept the referee's reading of what the verdict means, and the `verdict_note` and the effect label are rewritten accordingly.

- Two storm days, 23 February and 26 January 2026, carry 84% of the variation that identifies the held-out slope. Without 23 February alone the upper bound is 0.51 and the verdict would be unsettled. On the remaining days the held-out elasticity is between +0.1 and -1.1, depending on how 22 winter days are treated.
- Vehicle entries vary by about 3% within the fixed effects (a residual standard deviation of 0.032 in 2025), and near-holidays and weather supply most of what variation there is. Day-level data cannot identify the relation in either year. The 2025 coefficient falls from -0.41 to -0.09 with taxi trips inside the zone in the model.
- From January 2026 taxi speeds fell across the city. Trips wholly outside the zone slowed by as much as trips inside it (2.6% to 13.1% by month against 5.4% to 13.2%), and bus speeds did not (-3.9% in the zone, mostly January to March, and -0.6% outside). The cause was not found. The level miss of the speed link therefore cannot be assigned to the link.
- The ambulance link does not depend on the storm days (S2 is 1.22 without them) and its D against no relation is 32.
- The entries changes by band were differences of mean logs, which the storm days enlarge. As ratios of means they are -6.1% and -5.5%.

The stance was +0.994, computed against no relation, which put a contested claim at the agreeing end of the dashboard strip. It is now -0.84 (-0.98 to -0.23), measured against the registered threshold of 0.5 with the calibration error carried. Its note says that the value rests on the two storm days.

We did not register a successor. The referee asked for one with exclusions for snow days and near-holidays fixed in advance, and warned that it might not discriminate. On ordinary days the standard error of the slope is 1.32 on 119 days. A discrimination of 4 between a slope of 1 and a slope of 0 needs a standard error of 0.5, which is about 830 ordinary weekdays. A test on the data to autumn 2026 could not fail, and rule 8 says not to register such a test. The rise of the toll to $12 in 2028 is the first change that can test the link.

### The simulator

The second half of the same report lists ten defects in the simulator (`sim/`). Nine are fixed in code or stated in the output. The seventh, independent draws, is stated and left as it is. `docs/policy_simulation.md` gives the new results.

1. The sign of the speed, ambulance and survival outputs was built in. The entries-to-speed elasticity is now -0.23 (-0.69 to +0.23), the fit on the ordinary weekdays of both periods (`analyses/simulate/fit_pooled.py`), and its range crosses zero. Each output reports the share of draws with an improvement. For speed that share is 0.84 for every schedule that lowers entries, and the output says that this describes the parameter and not the schedule. The sign of the toll response stays positive by assumption, and the output says so.
2. Schedules scaled to hold revenue lower entries by construction. The property is kept and is stated in `scenarios.json`, in the command-line output, on the page and in the note.
3. The scaling now checks that revenue rises with the factor. The medians of revenue for the scaled schedules are now zero to within $0.03 million.
4. Every central value is the median of its draws, and `python -m sim check` verifies it.
5. No distribution is truncated, and the bounds of each normal range are the 2.5% and 97.5% points of its draws.
6. The output now carries the statements that the chain composes associations, that the speed link is applied to a change it was not estimated on, and that one value is used in every band.
7. The parameters are still drawn independently. This is stated and not fixed.
8. The output states that the baselines are 2025 means and are out of date as levels.
9. The hot-night illustration now covers the 30.5 weekday nights a year that its weekday baselines describe, and its deaths averted are reported as zero.
10. Values from `data/derived/congestion/parameters.json` now enter through one mapping table of nine entries with their source claims, and the build records the hash of that file. Three parameters are measured (the two elasticities and survival per minute) and eleven remain assumptions.

With these changes revenue is the only output on which the schedules differ. For speed, ambulance time, survivors, retail activity and injury crashes the 95% interval of every schedule includes zero.

### What the round did not do

`analyses/congestion/common.py` was not corrected for Roosevelt Island. `data/derived/congestion/parameters.json` was not edited; three of its notes (the mean of -0.86 for vacancy and the two lives figures) are now out of date. The cause of the citywide fall in taxi speed was not found. The closure of Mount Sinai Beth Israel was not examined. The two retail citations were not checked against the papers.
