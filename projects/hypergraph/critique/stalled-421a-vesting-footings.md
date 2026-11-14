# Referee report: stalled-421a-vesting-footings

The recorded verdict is contested. I recommend keeping contested as the verdict on the registered citywide comparison. Correct the outcome notes and `docs/stalled.md` where they draw conclusions about the 421-a mechanism, because the pooled comparison is confounded by project size and by the change of permit system. Register a new claim restricted to large residential jobs, or to the HPD list of vested projects, with job-number matching.

I wrote my own code before reading `docs/stalled.md` and `docs/case_334_van_brunt.md`. My scripts are outside the repo and are not committed. They use my own SoQL queries, not the registrant's cached parquet files or the registrant's scripts.

## Data

All queries were run on 13 November 2026 between 12:10 and 12:23 EST.

- ipu4-2q9a, DOB Permit Issuance, rowsUpdatedAt 2026-11-12T00:36:38Z. FO permits on NB jobs (48,730 rows), and INITIAL NB permits on NB jobs (98,578 rows).
- rbx6-tga4, DOB NOW: Build – Approved Permits, rowsUpdatedAt 2026-11-12T19:44:18Z. Foundation work type (27,708 rows).
- w9ak-ipjd, DOB NOW: Build – Job Application Filings, rowsUpdatedAt 2026-11-11T21:29:13Z. New Building jobs (59,107 rows; the registrant's fetch of 12 November had 59,039).
- bs8b-p36w, DOB Certificate Of Occupancy, rowsUpdatedAt 2026-11-11T21:35:47Z. NB rows (53,531).
- pkdm-hqz6, DOB NOW: Certificate of Occupancy, rowsUpdatedAt 2026-11-11T21:01:41Z. All rows (84,095).
- ic3t-wcy2, DOB Job Application Filings (legacy), rowsUpdatedAt 2026-11-11T23:14:49Z. Proposed dwelling units for the cohort's legacy jobs.

## 1. Rebuilding the deciding number

I first re-implemented the registered rule as written: the BBL column of the permit, jobs with a malformed or missing BBL dropped, and a CO on the same BBL within 1,096 days. My code gives the registrant's numbers exactly: window sizes 541, 516, 497, 290, 393, 807 and 366, and D1 = −0.208 (−0.250 to −0.167) and D2 = +0.092 (+0.035 to +0.149), with 4,000 draws and a different seed. The registrant's code therefore implements the registered rule correctly.

My own estimate differs from the registered one in two ways. I keep jobs whose permit has no BBL. I match a certificate to a job by job number, using both CO tables; pkdm-hqz6 carries BIS job numbers for BIS jobs, so the registration's reason for matching by lot ("job numbers change between BIS and DOB NOW") does not hold. The 36-month no-CO rates (difference in proportions, 10,000 bootstrap draws) are:

| Window | n | No CO within 36 months |
|---|---|---|
| 2017 | 543 | 0.407 |
| 2018 | 519 | 0.505 |
| 2019 | 513 | 0.429 |
| 2020 | 296 | 0.314 |
| 2021 | 413 | 0.358 |
| 2022 (rush) | 933 | 0.363 |
| 2023 | 473 | 0.271 |

D1 = −0.083 (−0.122 to −0.044). D2 = +0.093 (+0.043 to +0.143). Matching by job number or BIN gives D1 = −0.080 (−0.119 to −0.040). The refute condition (upper bound of D1 below 0.03) is met under every matching I tried, and the upper bound is far from the threshold, so rule 9 does not apply.

## 2. Does the verdict follow from the registration and PRECEDENCE?

The verdict follows. The refute condition is a disjunction, and its first part is met; under rule 1 the verdict is contested. The script, seed (20261113) and draws (2,000) were committed with the registration in ea9ff50, as rule 9 requires. The outcome was written 1 minute 52 seconds after the registration commit. File times show that `vesting_window_sizes.json` (11:54:48) was written before the registration (11:55:23) and `vesting_result.json` (11:55:33) after it. The job-or-lot measure in `vesting_exploratory.py` was written after the result (11:56:30). The outcome labels it exploratory, and it decides nothing.

Two points should be stated in the outcome. First, the registrant was not blind to completion data in general. The CO tables were fetched on 12 November for the construction claims, and the referee of construction-four-year-completion had already reported that job-number matching works across both CO tables. The choice of lot matching was a design error and was not chosen after these data were seen, but the doc's phrase "before any completion data were read" is true only of this cohort. Second, the refute condition is met by any citywide fall in the no-CO rate between 2017-2019 and 2022, whatever its cause. The rates fell from 2017-2019 to 2020-2023 in every horizon I computed (at 48 months, 0.27, 0.31 and 0.28 for 2017-2019 against 0.19, 0.23 and 0.24 for 2020-2022), and against the 2021 window D1 is +0.005 (−0.051 to +0.061). The contested verdict refutes the statement that the rush window stalled more than 2017-2019. It says little about the mechanism in the statement's "because" clause.

## 3. Matching, cohorts, censoring and project type

### Matching

The outcome explains the lot-matching defect as lots merged, split or converted to condominium billing lots after the permit. I checked the 456 jobs that have a CO under their own job number within 36 months but none on their lot. For 57% of them the matched CO record has no BBL at all. For 14% the CO is on a condominium billing lot (lot 7501 or higher). The rest are on a different lot, often in another block. Blank BBLs on CO records, not lot changes, are the main cause. The outcome notes and the doc should give this cause.

### Exclusion by missing BBL

The registered rule drops jobs whose permit has no BBL, and the losses differ by window: 2 jobs in 2017 (0.4%), 16 in 2019 (3%), 126 in 2022 (14%) and 107 in 2023 (23%). Most of the 2022 and 2023 losses are DOB NOW jobs (100 and 98). Dropping them changes the cohorts being compared.

### Cohort definition

The cohort is NB jobs with a separate initial foundation permit, not all NB starts. Its coverage changed between the windows. Among legacy NB jobs whose first NB or FO permit fell in the window, 52%, 51% and 55% had an FO permit in 2017, 2018 and 2019, against 67% in 2022. Among DOB NOW NB jobs whose first permit fell in the window, 87% had a Foundation permit in 2022 and 80% in 2023. Part of the rise from about 520 starts a year to 807 is the DOB NOW practice of issuing a separate foundation permit to nearly every job. Counting first NB-or-foundation permits instead, the windows had 1,043, 1,017 and 924 legacy jobs in 2017-2019 and 1,225 jobs in 2022 (464 legacy, 761 DOB NOW). The excess is about 230 jobs (23%), not about 290 (56%). A foundation permit also does not date the pouring of footings, which is what 421-a counted.

### Censoring

The 36-month horizon ends by 14 June 2026 for every window, and the data run to November 2026. Counts of NB certificates per quarter in pkdm-hqz6 are steady from 2024 Q1 (1,557) to 2026 Q3 (1,791), so I see no recording lag that would bias D2. The 48-month rate for 2023 (0.22) is not fully observed and should not be read.

### Project type

This is the most important problem. 421-a(16) mattered mainly for multifamily rental projects, but the test pools them with one- and two-family houses, and the size mix changed. Using proposed dwelling units (w9ak-ipjd for DOB NOW jobs, ic3t-wcy2 for legacy jobs; units known for 88% of jobs), 28% of the 2022 window had 50 or more units, against 13% in 2017-2019 and 7% in 2023. The size-specific differences go in opposite directions (EXPLORATORY; I chose these strata after seeing the pooled result, and they decide nothing):

| Proposed units | D1 (2022 − 2017-19) | D2 (2022 − 2023) |
|---|---|---|
| 0-2 | −0.310 (−0.368 to −0.252) | −0.150 (−0.215 to −0.087) |
| 3-9 | +0.046 (−0.064 to +0.157) | +0.314 (+0.186 to +0.443) |
| 10-49 | −0.088 (−0.185 to +0.010) | +0.033 (−0.138 to +0.205) |
| 50+ | +0.108 (+0.013 to +0.204) | +0.385 (+0.233 to +0.524) |

Among jobs of 50 or more units, 59% of the 2022 window (n 254) had no CO at 36 months, against 48% of 2017-2019 (n 174) and 21% of 2023 (n 34). The pooled D1 is negative mainly because one- and two-family jobs in 2022 finished much faster (no-CO rate 0.15 against 0.46). That fall is itself unexplained; 10% of 2022 jobs and 23% of 2023 jobs report zero proposed units, against 3-4% in earlier windows, so the DOB NOW unit field may also be coded differently. The control years also vary widely within strata (50+ units: 0.49, 0.60 and 0.33), so the subgroup result is not strong. It is enough to show that the citywide result cannot be read as evidence against the footings mechanism for the projects it concerned.

## 4. The prose in docs/stalled.md

The doc reports the registered numbers correctly and labels the exploratory work. It claims more than the numbers support in four places.

1. The heading "the 421-a rush did not produce extra stalled foundations" and the sentence that the footings rule "did not leave a citywide excess of unfinished buildings" are stronger than the test. The test compared all foundation-permit jobs, most of them small. Among large jobs, where the trade-press claim (72 vested projects, about 33,000 units) applies, the exploratory difference points the other way.
2. "Changing the commencement rule in 485-x or a successor would not, on this evidence, remove many stalled sites" is a policy conclusion that the pooled comparison cannot carry, for the same reason.
3. "The footings rule therefore brought forward about 290 starts" is a causal attribution from a count whose coverage changed with the permit system. The excess measured on all NB starts is about 230, and part of it may have other causes.
4. The explanation of the matching defect (lot changes) is mostly wrong, as shown above.

The novelty section is modest and mostly accurate. It says that the window counts and completion rates "have not, as far as we found, been published" and that "neither result is a new mechanism". The search behind "as far as we found" is not described, so the claim cannot be checked. The finding that lot matching misses many certificates is useful to the repo, but its stated cause should be corrected. The statement that the data "do not support [the trade-press] assertion at the scale of the city" is true of the pooled comparison only, and should say that the pooled cohort is mostly small projects.

## 5. What would settle it

The settle condition is right to ask for HPD's list of vested projects. I would add three things: job-number matching of certificates; a cohort defined on all NB starts (first NB or foundation permit), so that coverage does not change with the permit system; and a comparison within size strata, registered before the strata are examined. A registration restricted to jobs of 50 or more units, with the 2017-2019 and 2023 windows as controls, could be scored now.
