# Referee report: stalled-flood-zone-starts

The recorded verdict is unsettled. I recommend keeping it. My rebuild with certificates matched by job number puts the borough-stratified difference at zero, with an interval of about ±0.05, so neither registered condition is close to being met. The registrant's negative estimate depends on a matching rule that counts certificates of other buildings on the same lot, and on the large share of one- and two-family houses among floodplain starts. The outcome notes and `docs/stalled.md` should say this, and the doc should not say that flood rules are "not associated with slower completion".

I wrote my own code before reading `docs/stalled.md`. My scripts are outside the repo and are not committed. They use my own SoQL queries, not the registrant's job files.

## Data

All queries were run on 13 November 2026 between 12:10 and 12:23 EST.

- ipu4-2q9a, DOB Permit Issuance, rowsUpdatedAt 2026-11-12T00:36:38Z: FO permits on NB jobs, 48,730 rows.
- rbx6-tga4, DOB NOW: Build – Approved Permits, rowsUpdatedAt 2026-11-12T19:44:18Z: Foundation work type, 27,708 rows.
- w9ak-ipjd, DOB NOW: Build – Job Application Filings, rowsUpdatedAt 2026-11-11T21:29:13Z: New Building jobs, 59,107 rows.
- bs8b-p36w, DOB Certificate Of Occupancy, rowsUpdatedAt 2026-11-11T21:35:47Z: NB rows, 53,531.
- pkdm-hqz6, DOB NOW: Certificate of Occupancy, rowsUpdatedAt 2026-11-11T21:01:41Z: all rows, 84,095.
- 64uk-42ks, PLUTO, rowsUpdatedAt 2026-08-24T20:48:51Z: pfirm15_flag, land use and community district for the cohort's lots.
- ic3t-wcy2, DOB Job Application Filings (legacy), rowsUpdatedAt 2026-11-11T23:14:49Z: proposed dwelling units for legacy jobs.

## 1. Rebuilding the deciding number

The registered statistic is the Mantel-Haenszel risk difference, stratified by borough, in the share of jobs with no certificate of occupancy within 1,096 days of the first initial foundation permit, floodplain minus elsewhere. The registrant's value is −0.049 (−0.098 to −0.002), n 3,276, of which 401 are in the floodplain.

My cohort is the same set of December-to-June windows, 2017-2023, built from my own queries. I keep DOB NOW jobs whose permit has no BBL, but they cannot be placed in PLUTO and drop out here. For legacy jobs I use the geocoded BBL column of the permit where present and the permit's borough, block and lot otherwise. 3,342 jobs match current PLUTO, and 410 of them are in the 2015 preliminary floodplain (Manhattan 31, Bronx 19, Brooklyn 126, Queens 198, Staten Island 36). Bootstrap intervals use 4,000 draws, resampling within borough and flood strata.

| Certificate matching | Risk difference, flood minus other |
|---|---|
| Job number (my primary measure) | −0.001 (−0.051 to +0.049) |
| Job number or BIN | −0.006 (−0.055 to +0.044) |
| Lot (BBL) only | −0.036 (−0.085 to +0.012) |
| Registrant: job number or lot | −0.049 (−0.098 to −0.002) |

No-CO rates at 36 months under job-number matching, floodplain against elsewhere, are: Manhattan 0.839 (n 31) against 0.541 (n 196); Bronx 0.368 (19) against 0.366 (396); Brooklyn 0.460 (126) against 0.408 (1,017); Queens 0.313 (198) against 0.429 (1,126); Staten Island 0.306 (36) against 0.132 (197).

## 2. Does the verdict follow from the registration and PRECEDENCE?

It does. Under the registered measure the upper bound of the interval was −0.0023 with the registered seed and draws, below zero with 20,000 draws, and above zero under 1 of 20 other seeds. Rule 9 makes such a condition neither met nor unmet, and rule 2 then gives unsettled. The rule-9 re-run was done as the rule asks. Under my rebuild the question does not arise, because the interval is centred on zero.

The script, seed and draws were committed with the registration in fc819e5 at 11:59:11, and `flood_result.json` was written at 11:59:40. The outcome measure (no CO by job number or lot, with certificates up to 60 days before the start allowed) was written at 11:56:30, after the registrant had seen the job-level outcomes of stalled-421a-vesting-footings. The outcome discloses this. The PLUTO flood flags had not been fetched at that time, so the measure was not chosen with the flood result in view. The registrant had, however, seen the no-CO rate of every job and its borough. That is a small risk to the order of model and data, not evidence of a choice made to fit the result. The 60-day allowance has no effect: no job in my cohort has a certificate under its own job number dated before its foundation permit.

## 3. Matching, cohort, censoring and project type

### Matching

This is the most important problem. The registered measure counts a job as finished when any certificate is issued on its lot after the start. In Queens this turns 19 of the 198 floodplain jobs from unfinished to finished. Eighteen of the 19 are single-family jobs on three lots in Queens blocks 16340 and 16350 (community district 14, at the western end of the Rockaway peninsula), and 13 are on lot 4163500400 alone. These lots appear to be cooperative lots that hold many houses. The certificate that "completes" each job was issued for another house, often within days of the foundation permit (for example a start on 6 April 2017 and a certificate on 10 April 2017). Under the registered measure the Queens floodplain rate is 0.212; under job-number matching it is 0.313. Floodplain jobs share a lot with another cohort job more often than other jobs do (26% against 11%), so the defect biases the comparison toward the floodplain finishing sooner. A certificate dated within a few weeks of a foundation permit cannot be the completion of that building, and a minimum plausible duration would have removed these matches.

### Cohort

The cohort is inherited from the vesting claim. It counts jobs with a separate foundation permit, whose coverage of all new-building starts changed with the move to DOB NOW (see the report on stalled-421a-vesting-footings). The registered rule also drops jobs whose permit has no BBL, and those losses are concentrated in 2022 and 2023. Neither problem is specific to the floodplain, and I do not expect either to change the sign of the result. The December-to-June windows use about half of the available starts, as the settle condition says.

### Censoring

All windows have the full 36 months of follow-up by June 2026, and quarterly counts of NB certificates in pkdm-hqz6 show no recording lag through 2026 Q3. Censoring is not a problem here.

### Project type

Floodplain starts are mostly one- and two-family houses: 83% of Queens floodplain jobs against 59% of other Queens jobs, and 49% of Brooklyn floodplain jobs against 17% of other Brooklyn jobs (units known for 88% of jobs). Most of the Queens floodplain jobs are in community district 14 (143 of 198), where many houses were rebuilt after Hurricane Sandy. Small houses finish sooner, so the borough-only stratification compares small floodplain houses with larger projects elsewhere. Stratifying by borough and size (0-2, 3-9, 10-49 and 50 or more proposed units) gives +0.001 (−0.054 to +0.055). Within size classes (EXPLORATORY; chosen after the data, deciding nothing) the floodplain differences are −0.050 (−0.115 to +0.018) for 0-2 units, +0.256 (+0.054 to +0.437, 21 floodplain jobs) for 3-9, +0.041 (−0.135 to +0.231) for 10-49 and +0.069 (−0.057 to +0.196) for 50 or more. The point estimates for multifamily jobs are positive, which is the registered direction, but the floodplain samples are small.

The registered alternatives named neighbourhood and project size but did not adjust for size. The current PLUTO flag, also named, is a smaller problem: 13% of legacy jobs have a geocoded BBL different from the permit's block and lot, and about 4% of the cohort's jobs with a BBL do not match current PLUTO.

## 4. The prose in docs/stalled.md

The section on this claim reports the registered estimate and the rule-9 reasoning correctly. It claims more than the numbers support in two places.

1. "Flood-zone rules are not associated with slower completion across the city" reads as a finding of no association. The verdict is unsettled. Under job-number matching the difference is −0.001 with an interval from −0.05 to +0.05, which does not exclude the registered magnitude of +0.04, and the multifamily point estimates are positive.
2. "In Queens the 198 floodplain starts finished faster than other Queens starts (0.21 against 0.41 not finished at 36 months)" rests partly on the lot-matching defect described above (0.31 under job-number matching) and partly on the share of single-family houses.

The doc's novelty section makes no novelty claim for this test, and none is warranted. The suggestion that flood rules matter "in particular places, such as the Brooklyn shore" is reasonable as a hypothesis. It is supported only by borough-level differences that were not registered.

## 5. What would settle it

The settle condition (all starts 2014-2023, the flood zone at the date of the permit, a control for project size) is right. I would add certificate matching by job number, with lot matching only as a fallback and with a minimum duration between foundation permit and certificate. I would also register the size strata in advance, because the floodplain mix of one-family houses and larger projects differs by borough.
