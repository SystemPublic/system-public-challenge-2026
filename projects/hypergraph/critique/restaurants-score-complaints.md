# Referee report: restaurants-score-complaints

Verdict recorded: unsettled (rule 11, with rule 2 also sufficient). I rebuilt the deciding numbers with separate code that does not import `analyses/restaurants/` or `concord/`, from my own extracts of 43nn-pn8j and erm2-nwe9. The scratch code is outside the repository, in the session scratchpad folder `ref_rest/` (`fetch.py`, `complaints.py`). I read `docs/restaurants.md` only after the re-estimates below were finished. This report also covers the trend and survivorship sections of that note; the evenness section is reviewed in `critique/restaurants-nta-harshness.md`.

## Order of registration and data

The script commit 0c147b3 (14:11:24 on 13 November) is an ancestor of the registration a70335a (14:12:00), and the branch `origin/prereg/restaurants-score-complaints` exists. `complaints_test.py`, `common.py` and `power_complaints.py` have not changed since 0c147b3. The model has no resampling, so rule 9 has no seed to check.

The Socrata cache and the registrant's transcript show what was read before 14:12:00. The inspection extract that defines the exposure cohort (scores, BBL, NTA) was fetched at 14:08:53 and 14:09:07. The 311 queries before the registration were aggregates: Food Poisoning complaints by year and borough, by descriptor and location type, and by year for restaurant locations with a BBL (the power check, 14:09:33). Two synthetic checks of the model at 14:10 used Poisson(0.1) fake outcomes. The restaurant-level Food Poisoning extract was fetched at 14:13:16, and the Noise - Commercial extract at 14:14 (two pages) and 14:23 to 14:27 (four pages). The outcome was decided at 14:27:38. I found no restaurant-level outcome data read before the registration.

## Data

- DOHMH New York City Restaurant Inspection Results, 43nn-pn8j, rowsUpdatedAt 2026-11-12T23:06:40Z, the same version as the registrant's. My extract has 92,061 visit rows from 2022 on, the same count.
- 311 Service Requests, erm2-nwe9, rowsUpdatedAt 2026-11-13T02:35:58Z, one day newer than the registrant's (2026-11-12T02:36:01Z). I pulled all Food Poisoning complaints (13,278) and all Noise - Commercial complaints (291,425) from January 2022 to June 2026, with BBL and address, and applied the filters myself. Of 10,378 Food Poisoning complaints at Restaurant/Bar/Deli/Bakery, 9,983 carry a valid BBL.

## Re-estimate

| | Registrant | Referee |
|---|---|---|
| Cohort; valid BBL; single-restaurant lot | 10,360 (single lot) | 17,588; 17,144; 10,360 |
| Food Poisoning complaints, days 1-365 | 876 | 876 |
| Primary IRR, not-A against A (95% CI) | 1.124 (0.957-1.319) | 1.130 (0.962-1.326) |
| Placebo IRR, Noise - Commercial | 1.673 (1.111-2.519) | 1.672 (1.117-2.504) |
| Ratio of IRRs | 0.672 (0.433-1.043) | 0.676 (0.438-1.043) |
| D against no effect; against the placebo | -2.09; -0.97 | -1.64; -0.74 |

The numbers reproduce to the second decimal. The small differences come from the newer 311 version. support_if fails on both halves (lower bounds 0.96 and 0.44 against 1.00), and refute_if fails (upper bound 1.33 against 1.10).

## Rule 11

Rule 11 was applied correctly. The placebo's lower bound (1.11) exceeds 1.00, so it meets the first half of support_if, and refute_if is not met, so the verdict is unsettled. Rule 11 is not needed for this verdict, because support_if is not met in any case and rule 2 gives the same result. The outcome's phrase "the placebo decides the matter under rule 11 regardless" is correct but should say that rule 2 alone gives the same verdict.

The placebo's result is not produced by a few lots. Its Pearson dispersion is 68, one lot has 1,809 noise complaints, and the 20 lots with the most complaints hold 27% of them. The placebo still meets support under a negative binomial model (alpha 1; 1.64, 1.32-2.04) and with a binary outcome, any noise complaint in the year (1.17, 1.08-1.26). The design therefore picks up a lot-level difference between not-A and A-range restaurants that has nothing to do with food.

## Single-lot restriction, matching and window

- Restriction. The single-lot rule keeps 10,360 of 17,144 cohort restaurants with a valid BBL (60%). The 6,784 restaurants on lots with more than one CAMIS have 2,801 of the 3,677 Food Poisoning complaints linked to cohort lots (76%), so the test uses a quarter of the linked complaints. The rule is computed from the live table, which drops closed restaurants. A lot whose other restaurant closed and was deleted therefore counts as a single-restaurant lot, and complaints about the closed restaurant can be assigned to the survivor. This affects few lots in a 365-day window, but it is not zero. 386 cohort restaurants sit on condominium unit lots (lot numbers 7501-7599). I did not check whether 311 geocodes complaints there to the same unit lot or to the billing lot.
- Matching by address. I also matched complaints by house number, normalised street and ZIP code. This links 641 complaints, against 876 by BBL, and the two methods give the same count for 97.9% of restaurants. The address-matched IRR is 1.26 (1.05-1.51), which would meet the first half of support_if, but the address-matched placebo is 1.38 (1.07-1.80) and also meets it. Address matching was not registered and decides nothing here (rule 4); under it the verdict would still be unsettled under rule 11.
- Window. The last cohort inspection is 2025-06-30 and the complaint extract runs to 2026-07-01, so every restaurant has a full 365-day window. Including day 0 adds 3 complaints and changes nothing. Shorter windows give the same picture: days 1-90 give 1.39 (1.03-1.88) for Food Poisoning and 1.49 (1.10-2.01) for noise, and days 181-365 give 1.10 and 1.95. In the 365 days before the inspection the IRRs are 1.18 (1.01-1.38) and 1.36 (1.11-1.68). Both outcomes are associated with the score before and after the inspection, which fits a stable property of the lot more than an effect of the inspection.
- Survivorship. The cohort contains only restaurants listed in the live table in November 2026. The registration names this bias, and the outcome reports it.

## Does docs/restaurants.md claim more than the numbers support?

The complaint section matches the outcome and my numbers. Three sentences go further than the numbers.

- "The design cannot tell an effect of hygiene from the fact that busy bars and restaurants both score worse and draw more calls." The first half is what the placebo shows. The second half states a mechanism as a fact. Customer volume is not measured, and the placebo shows only that not-A lots draw more noise complaints, for reasons the data do not identify.
- The design section says that a complaint is linked only when the lot holds one restaurant. It should add that this rule drops 76% of the linked complaints, and that the single-lot restaurants are a selected group (smaller buildings), as the registration's own alternatives say.
- "Like Jones (2004) and Petran (2012), it finds at most a weak link." The test cannot exclude IRRs up to 1.33, the literature's midpoint, so it is equally consistent with a moderate link. The note should say that the result is uninformative about the size of the link, not that the link is weak.

### Trends, 2012 to 2025 (exploratory)

The figures quoted match `trends_pooled.csv`. The interpretation goes further than the series supports, for three reasons.

- The decline from 2012 to 2017 ends at the two most filtered points in the series. The 2017 value (1.71 critical violations per initial inspection, the lowest point) comes from a copy captured 2.85 years later that holds 15,779 initial inspections, against 23,070 to 27,850 in 2018 and 2019. The 2012 value holds 12,983, about half a normal year. Where the archive allows a comparison at similar retention (50% to 80% of a year's inspections kept), surviving inspections show 0.051 fewer critical violations on average, up to 0.12 fewer. The 2017 trough could therefore be an artefact of filtering, and the true value may be near the 2016 and 2018 values (1.72 and 1.73).
- The sentence on recent years ("rose to 1.98 in 2022 and were 1.90 and 1.92 in 2024 and 2025") leaves out 2023, at 1.81. The series after 2021 is not monotone, and 2022 holds only 15,517 initial inspections, during the post-closure backlog.
- The note ties the 2012-2017 rise in A grades to Wong et al. and says that "the most recent years have lost part of it", but it also says that changes in the violation code list and scoring rules were not checked. The interpretation should wait for that check.

### Survivorship (exploratory)

The average quoted, 0.019 fewer critical violations per inspection among survivors (about 1%), includes six comparisons against the May 2021 copy (inspection years 2017 to 2019, citywide and Manhattan). These show +0.04 to +0.05 at 98% retention. A 2% loss cannot produce that, so these rows reflect the 2021 copy's different coding of the critical flag, not survivorship. Without that copy, the 33 comparisons with at least 30% retained average -0.030 (-1.6%), with a range of -0.117 to +0.023. The note's range "-0.15 to +0.05" includes a comparison with 20% retained (-0.147) and the 2021 coding artefact (+0.05). In any case, the comparison measures only the loss between the earliest copy that holds a year and later copies. Restaurants that closed before the earliest copy are never seen, so the estimate is a lower bound on the bias for each year. The statement that "the bias is about 1%" and is "small next to the changes in the series" should become: about 1.5% to 3% where it can be measured, up to 0.12 violations (a third of the series' range) at the most filtered points, and not measured before each year's first copy.

## Recommendation

1. Keep `unsettled`. support_if fails under rule 2, and rule 11 applies as well. The placebo meets support under every variant I ran.
2. In `prediction_scored` or the notes, say that rule 2 alone gives the verdict, and report that the single-lot rule drops 76% of the linked complaints.
3. Revise the note's sentences on mechanism ("busy bars"), on the size of the link ("at most a weak link"), on the 2017 trough and 2023, and on the survivorship estimate, as described above.
4. A successor claim could register address-based linkage for all lots, with complaints divided among the restaurants on a lot, and a placebo with a lower variance, such as any noise complaint in the year. It should be registered before any 311 data after June 2026 are read.
