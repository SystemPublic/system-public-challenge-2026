# Referee report: restaurants-nta-harshness

Verdict recorded: contested (rule 1, refute_if met). I rebuilt the analysis table and the deciding permutation test with separate code that does not import `analyses/restaurants/` or `concord/`. The scratch code is outside the repository, in the session scratchpad folder `ref_rest/` (`nta_build.py`, `nta_test.py`, `nta_power.py`, `nta_power2.py`). I read `docs/restaurants.md` only after the re-estimates below were finished. The note's trend and survivorship sections are reviewed in `critique/restaurants-score-complaints.md`.

## Order of registration and data

The script commit 48147d6 (14:18:17 on 13 November) is an ancestor of the registration 55dabf1 (14:18:37), and the branch `origin/prereg/restaurants-nta-harshness` exists. `evenness_test.py` has not changed since 48147d6. The registered run's log, `evenness_run.log`, was created at 14:18:46, after the registration. The outcome was decided at 14:26:29.

The registrant's transcript confirms the account of the frequency result. At 14:17:42 the registrant ran the script with `n_crit` replaced by Poisson(2) draws and 300 permutations. The output showed the harshness statistic on synthetic data (ratio 0.72) and the frequency test on the real inspection counts (p 0.013, tau 0.016). Nothing in that output bears on the adjusted critical-violation counts.

Two other early looks happened, and the registration mentions neither.

- At 14:12 the registrant read `docs/underlay_drift.md`, which the registration cites. That note reports, from the same snapshot, the share of A grades by Manhattan ZIP code (83.1% in 10002 to 95.5% in 10023) and how the ranking of ZIP codes changes in the live table. This is a raw, unadjusted geographic summary of a measure close to the outcome. It shows that raw rates are uneven, which the outcome also reports. It could not have shown the adjusted result.
- The inspection extract fetched at 14:08 for the complaint cohort holds `nta` and the number of critical violations for every Manhattan inspection from 2022 on. The transcript shows no grouping of it by place before the registration.

I judge that neither look could have shown the deciding result. The registration should still have named the drift note's ZIP table as seen.

## Data

- Underlay `nyc/restaurant-inspections` v1.0.0, hash `ulv2:07a7f08a0d5c85649920f8adc6946d27c17f5e2d75e9ee07c0ad4ae0fcc6739c`, read from the raw records in `~/opt/nyc-concordance/underlay/records_v1.0.0.ndjson` (10,536 restaurants, 25,341 inspections, 76,870 violations, inspections 2024-01-02 to 2026-06-09).
- 2020 NTA boundaries, 9nt8-h7nd, rowsUpdatedAt 2026-11-02T19:20:21Z, which I fetched myself.

## Re-estimate

| | Registrant | Referee |
|---|---|---|
| Inspections; restaurants; NTAs | 12,228; 8,157; 31 | 12,228; 8,157; 31 |
| Mean critical violations per initial inspection | 1.839 | 1.839 |
| S observed; null mean | 42.59; 38.39 | 42.61; 38.65 |
| Permutation p, seed 20261113, 10,000 draws | 0.307 | 0.323 |
| p with other seeds and draws | 0.305-0.313 | 0.309 (seed 7); 0.269 (300 draws, restaurant count refitted each draw) |
| Unadjusted S / null mean | 4.2 | 4.19 |
| tau, registrant's formula | 0.000 | 0.000 (tau² = -0.0008) |
| tau, centred contrasts | not computed | 0.024 |

The test reproduces. The p values differ only because my code draws the permutations in a different order. p is about 0.3 under every seed, far from 0.10, so rule 9 does not apply.

The tau estimator is biased downward. The registrant's formula takes the variance of the NTA effects measured against a reference NTA and subtracts the mean squared standard error of those contrasts. Each contrast's variance includes the reference NTA's variance, which does not add to the spread of the contrasts, so the formula subtracts that variance once too often. With effects centred on the Manhattan mean, the estimate is 0.024. In simulation at a true tau of 0.049, the registrant's estimator has a median of 0.040 and the centred one 0.054. The bias does not change this verdict, because the p condition fails. It does make the support_if condition harder to meet than the registration intended.

## Was the refutation condition registered, and could the test detect harshness?

The condition `refute_if: Permutation p > 0.10` is in the registration 55dabf1, so rule 1 applies as registered. A p value above 0.10 is absence of evidence. It counts as refutation only to the extent that the test had the power to detect the predicted effect. I estimated that power by thinning the real counts. For a true tau, I drew an effect u_j ~ N(0, tau²) for each NTA, replaced each count y by Binomial(y, exp(u_j − max u)), refitted the registered null model and ran the permutation test with 500 draws. This keeps the real restaurant mix, covariates and dispersion. Rows are 100 or 150 replicates each.

| True tau | P(p ≤ 0.01) | P(support_if), registrant's tau | P(support_if), centred tau | P(refute_if: p > 0.10) |
|---|---|---|---|---|
| 0.025 | 0.09 | 0.00 | 0.01 | 0.39 |
| 0.035 | 0.32 | 0.05 | 0.19 | 0.18 |
| 0.040 | 0.69 | 0.04 | 0.45 | 0.12 |
| 0.050 | 0.81 | 0.29 | 0.59 | 0.02 |
| 0.075 | 0.99 | 0.91 | 0.98 | 0.00 |

For place effects that are independent of the covariates, the p condition reaches 80% power at a between-NTA SD of about 0.05, the bottom of the registered band. The full support_if condition, with the registrant's tau estimator, reaches 80% only at about 0.07. A true tau of 0.05 would have produced p > 0.10 in 2% of replicates, so for effects of this kind the refutation is informative against the registered band. It is much weaker against smaller effects: a 2.5% place effect is "refuted" 39% of the time, and a 4% effect 12% of the time.

## Can the adjustment set absorb a real place effect?

It can, and one covariate decides the result. All p values below are exploratory (rule 4).

| Adjustment set | S / null mean | p |
|---|---|---|
| None | 4.19 | < 0.001 |
| Quarter, day of week, workload only | 4.01 | < 0.001 |
| Restaurant-level only (cuisine, chain, new) | 1.81 | 0.0015 |
| Registered set without cuisine | 1.85 | 0.002 |
| Registered set without the NTA's restaurant count | 1.71 | 0.008 |
| Registered set | 1.10 | 0.32 |

The NTA's restaurant count is a property of the place, with one value per NTA and one free coefficient (−0.047 per log unit, se 0.011). Without it, the NTA effects have an SD of 0.061 (the mean standard error is 0.05, so the excess is about 0.035), and they correlate −0.51 with the log restaurant count. Rates are lower than expected in Midtown-Times Square, East Midtown, the Financial District and Greenwich Village, and higher in Murray Hill-Kips Bay, Washington Heights (North), Gramercy, Manhattanville, Harlem (North) and Chinatown. This is the kind of place gradient the hypothesis was about. Whether it reflects inspectors, restaurants or buildings, the registered model removes the part of it that runs with restaurant density.

The simulation shows the size of the loss. With a true tau of 0.05 correlated 0.7 with log restaurant count, P(p ≤ 0.01) falls from 0.81 to 0.44 and P(refute) rises from 0.02 to 0.15. With the effect fully aligned with restaurant count, P(refute) is 0.99. (In these two runs the estimated tau is not interpretable, because the simulated gradient had the opposite sign to the real one and partly cancelled it.)

The other covariates absorb less. Daily workload is the number of Manhattan inspections on the day, which is the same for every NTA on that day, and NTA explains 1.0% of its variance, so workload is not set by place. Cuisine is partly a property of place (Chinese restaurants in Chinatown, for example), and dropping it gives p = 0.002. Even without the restaurant count the excess SD (about 0.035) is below the 0.05 floor of support_if, so the verdict without that covariate would have been unsettled, not confirmed. The covariate decides between contested and unsettled.

## Does docs/restaurants.md claim more than the numbers support?

The numbers in the evenness section match the outcome and my re-estimates. Four statements go further than the numbers.

- "After adjustment, the 31 NTAs are as even as a random assignment of restaurants would make them." The test cannot detect a place effect of 2.5% to 4% with any reliability, and it cannot see any place effect that runs with restaurant density. The sentence should say that the test rules out a between-NTA SD of 5% or more that is independent of the adjustment set.
- "The registered covariates account for the neighbourhood differences in raw rates." One NTA-level covariate, restaurant count, accounts for most of the drop from p = 0.008 to p = 0.32. "Account for" should read "absorb". The note should report that a density gradient of about 3.5% (correlation −0.51 with log restaurant count) remains unexplained, and that the data cannot say whether it comes from inspection or from the restaurants.
- "Raw neighbourhood differences in violations ... should not be read as harsher inspection of some neighbourhoods." The test supports this sentence only for differences unrelated to restaurant density. The density-related part is neither confirmed nor excluded.
- "Tau is 0.00." The estimator is biased downward, and the centred estimate is 0.024. This changes no verdict.

## Recommendation

1. Keep `contested` under rule 1. The refutation condition was registered before the data, the procedure was fixed in 48147d6, the result does not depend on the seed, and a rule written now to override a registered condition on power grounds would undo rule 1.
2. In the outcome notes, state what the refutation covers. The test rules out a between-NTA SD of 0.05 or more that is independent of the adjustment set (power 0.81, false refutation 0.02). It does not exclude smaller effects or a gradient that runs with restaurant density. Report the result without restaurant count (p = 0.008, excess SD about 0.035) as exploratory. Correct tau to the centred estimate, 0.024. Mention the drift note's ZIP table as an early look.
3. Revise the four sentences in `docs/restaurants.md` listed above.
4. A successor claim (`restaurants-nta-harshness-v2`) could test the density gradient directly, with restaurant count as the exposure and not a covariate. It should name a refutation condition on an interval (for example, the upper bound of the gradient below a stated size), not on a p value, so that absence of evidence and evidence of absence are kept apart. It needs data not yet read, such as the other boroughs, or a later Underlay version with inspections after June 2026.
