# Critique round 1: summary and answers

A fresh referee agent reviewed the 16 heat, mobility and construction claims on 12 November 2026. It had the registrations, outcomes, code and data, and none of the registrants' reasoning. Its reports are in `critique/<id>.md`. The coordinator wrote the answers. `analyses/critique/answer_round1.py` applies the accepted changes through `concord.claims.revise`, which keeps every earlier outcome in the outcome's `history` field. No registration was changed.

## Referee's table, ordered by severity

| # | Claim | Verdict before | Recommendation | Answer | Verdict after |
|---|---|---|---|---|---|
| 1 | construction-four-year-completion | confirmed | change to unsettled; re-register the restricted cohorts | accepted | unsettled |
| 2 | construction-permit-funnel | confirmed | change to unsettled | accepted | unsettled |
| 3 | mob-crz-air-nyccas | unsettled | contested, or state which rule takes precedence | accepted both | contested |
| 4 | mob-crz-air | unsettled | no_test | accepted | no_test |
| 5 | heat-trees-ed-chain | contested | keep; fix stance | accepted (weakest-link stance) | contested |
| 6 | mob-active-commute-obesity | confirmed | keep; drop the comparison with research | accepted | confirmed |
| 7 | heat-surftemp-ed | contested | keep; narrow the label to the area level | accepted | contested |
| 8 | construction-aerial-triangulation | unsettled | keep; fix stance | accepted (stance null) | unsettled |
| 9 | mob-crz-traffic | confirmed | keep | — | confirmed |
| 10 | heat-trees-surftemp | unsettled | keep | — | unsettled |
| 11 | mob-asthma-pollution | unsettled | keep | — | unsettled |
| 12 | construction-sheds-outnumber-nb | confirmed | keep for the permit counts only | accepted (stance null) | confirmed |
| 13 | heat-trees-airtemp-hyperlocal | unsettled | keep | — | unsettled |
| 14 | mob-speedcam-247 | unsettled | keep | — | unsettled |
| 15 | heat-ed-syndromic | confirmed | keep | — | confirmed |
| 16 | heat-shootings | confirmed | keep | — | confirmed |

## The precedence rule

The referee found that two claims had been decided by opposite rules. One followed the generic verdict definitions in `concord/claims.py`. The other followed its registered refutation condition. The project now states one rule, `concord.claims.PRECEDENCE`.

The registration's own conditions decide the verdict when either is met. Neither met gives unsettled. A registered test that could not be run gives no_test. A measure chosen after the data were seen never decides a verdict.

A bridge takes the stance of its weakest link. A proportion or count with no null that expresses the research direction gets no stance.

## What the round changed

Before the round there were 9 confirmed, 3 contested and 7 unsettled, with no no_test. After it, counting the three neighbourhood claims under separate review, there are 7 confirmed, 3 contested, 8 unsettled and 1 no_test.

Two of the changes moved verdicts toward the middle. In both, a registrant had replaced the registered statistic with a better one after seeing the data. The substantive points still hold: permit rows overstate buildings, and most permitted buildings are finished within a few years. They are now reported as exploratory measures that call for new registrations.

## A limitation the round did not remove

The order "prediction, then data" rests only on git commit order inside one afternoon. Commits are local and can be rewritten. Pushing the repository to a remote, or timestamping the registration hashes with a public service, would make the order checkable by others.

## Round 1b: neighbourhood claims

A second fresh referee reviewed the three neighbourhood claims. All three verdicts follow from their registered conditions, and all three were kept. The answers add the referee's qualifications to each outcome's notes (`analyses/critique/answer_round1b.py`).

| Claim | Verdict | Referee | Answer |
|---|---|---|---|
| nbhd-vacant-shootings | confirmed | keep; the association disappears within NTAs (IRR 0.98, 0.94 to 1.01); not equal to Philadelphia | accepted; noted |
| nbhd-noise311-exposure | unsettled | keep; separate street noise from neighbour noise in the settle condition | accepted; noted |
| nbhd-rodents-asthma | confirmed | keep as registered but fragile: the housing control contains rodents; fails with race adjustment or without Sunset Park | accepted; noted; not to be used in any bridge before re-analysis |

The rodent result shows a problem with confirmations at neighbourhood level. Its control variable contained part of the exposure, and the registration did not catch this. The shootings result is "confirmed" between neighbourhoods and null within them. That is the usual pattern of an ecological association that the research's own design (a randomised trial at lot level) does not share.

## Round 2: bridges

A third fresh referee reviewed the four bridge claims. It confirmed from commit order and cache fetch times that every composed prediction was fixed before its endpoint was queried. It also noted that rule 7 was committed 30 seconds after the bridge outcomes. That rule governs how a verdict is displayed and named, and it was written after the outcomes were seen.

The referee's main objection was that an endpoint test must be able to fail. The crash bridge's composed prediction is near zero, because the speed term and the volume term cancel. Its endpoint lies 0.32 standard errors from the chain and 0.43 from no effect, so a chain with no content would have passed with probability above 0.99. We accepted this and added rule 8. An endpoint test decides a bridge only when it favours the chain over no effect by a likelihood ratio of about 7 or more (D = z_null² − z_chain² ≥ 4). The stance is scaled down when it does not.

Rule 8 was also written after the outcomes. It makes verdicts stricter, not looser, and it applies to both bridges.

| Claim | Before | Referee | Answer | After |
|---|---|---|---|---|
| bridge-crz-injury-crashes | bridged | re-analyse; the test cannot separate the chain from no effect; an unregistered geocoding change affects the endpoint | accepted (rule 8, D = 0.08); re-analysis listed as exploratory research needed | unsettled |
| bridge-heat-shootings-ems | bridged | keep under the registered rule but report it as weak: 37% of dispatches are the same victims, and a stabbing contrast would also pass | accepted; discriminates from no effect (D ≈ 471) but not specific; noted | bridged |
| bridge-shot-ems-link | confirmed | keep as a record-keeping check; stance null | accepted | confirmed |
| bridge-crz-crash-link | no_test | keep; not scored; the elasticity is an assumption | accepted | no_test |

## Round 3: commuting

A fourth fresh referee reviewed the two commuting claims, re-ran both, and found no code error that changes a verdict.

| Claim | Verdict | Referee | Answer |
|---|---|---|---|
| commute-time-depression | unsettled | keep; the test had about 10% power and could not have produced support; the estimate's sign depends on weighting | accepted; the prediction is scored "uninformative"; the settle condition is rewritten |
| commute-fhv-subway-distance | contested | keep; but the city data agree with the published source (Barajas and Brown 2021) and contradict only the registrant | accepted; the stance is drawn against the research direction, so the dashboard shows agreement with the research |

The FHV claim separates two things the word "contested" can mean: disagreement with the registrant's bet, and disagreement with the research. The verdict records the first, and the stance on the dashboard records the second.

## Round 4: thirty reports on the later claims

Fresh referee agents reviewed 30 claims on 13 November 2026: 27 claims in the further, reproduction, transfer, transit, re-timed week, heat mechanism, graph-confounder and graph-split groups, and the three discovery studies. Each referee had the registration, the outcome, the code and the data, and re-ran the analysis in a scratch folder. The coordinator wrote the answers, and "we" below is the coordinator. `analyses/critique/answer_round4.py` applies them through `concord.claims.revise`. No registration was changed.

Two verdicts changed. retimed-daytime-burglary went from contested to unsettled, and graph-triad-cold-asthma-absence went from confirmed to unsettled. One recommendation to change a verdict was not accepted: graph-concordance-matrix stays confirmed under rule 1, with a narrower statement of what is confirmed. Before the round there were 21 confirmed, 11 contested, 24 unsettled, 4 no_test and 1 bridged. After it there are 20 confirmed, 10 contested, 26 unsettled, 4 no_test and 1 bridged.

Five results were recomputed by the coordinator before they were written into outcomes: the subway rate of 1.653, the two Chinatown tract sets, the population-density correction, the paired interval for the Loop, and the street-noise shares by period. The other figures quoted below are the referees' re-estimates.

### Criticisms that apply to several claims

Three criticisms recur. Two new rules in `concord.claims.PRECEDENCE` answer them: rule 9 answers the first two and rule 10 the third. Both rules were written after the outcomes were known.

The first is that a verdict turned on a bootstrap seed. Rule 9 says that the script, the number of draws and the seed are fixed with the registration, and that a condition met under some seeds and not others is neither met nor unmet. Among decided claims it changes the burglary verdict only.

The second is that analysis scripts were first committed with the outcome. Nearly every report says this. For those claims the evidence that the model was fixed before the data were seen is the plan text and the file times. The git history does not show it. Rule 9 requires the script to be committed with the registration from now on. No verdict changes on this ground. Several referees also said that the time of a push cannot be read from the repository, so the record shows that a registration was committed before the data, not that it was public before the data. bridge-crz-injury-crashes-v2 and further-subway-crime-per-million-repro have no prereg branch of their own, so their registration times rest on commits to the main branch.

The third is that thresholds were applied to point estimates whose intervals cross them. Rule 10 keeps such verdicts under rule 1 and requires the outcome to state the margin. It changes no verdict. It applies to further-datacentre-share-manhattan-v2, graph-confounders-surftemp-ed, graph-confounders-commute-obesity, transfer-chicago-weekday-pattern and graph-concordance-matrix.

Some outcomes now carry a `verdict_note`, one or two sentences on what the label does and does not mean. The dashboard does not yet display this field.

### Verdicts changed

#### retimed-daytime-burglary (contested to unsettled)

The referee objected that the refutation bound, 0.9525 against a threshold of 0.95, depends on the bootstrap seed. The bound is above 0.95 in 62% of 40 other seeds and is 0.9509 with 50,000 draws. We accept this. The registration did not fix the seed, so the registered procedure does not determine which side of 0.95 the bound falls on. Rule 2 applies and the verdict is unsettled.

The referee also found that seven of eight further specifications have a lower bound below 0.95, that the share of public-housing complaints doubled, and that complaints with an occurrence window of two days or more behave as extra Friday departures would predict. We accept this and added it to the notes. The notes keep the statement that no fall is seen and that a fall of more than about 5% to 7% is unlikely.

#### graph-triad-cold-asthma-absence (confirmed to unsettled)

The referee objected that the claim is a bridge registered six hours after rule 8 was adopted, and that its endpoint test does not discriminate between the composed prediction and no effect. The endpoint is 3.81 standard errors from the composed prediction and 4.19 from no effect, so D = z_null² − z_chain² = 3.0, below the 4 that rule 8 requires. We accept this. The verdict is unsettled, and the stance is now the endpoint stance of rules 7 and 8 (-0.78) in place of the stance of a direct effect (0.97).

The referee also controlled for influenza, which the registrant had named and left out, and found the direct association robust: 1.10 (1.05 to 1.15) as registered and 1.07 (1.02 to 1.13) with laboratory-confirmed influenza in the model. The association also survives week-by-year effects, clustering by school year, and dropping days near a recess. We accept this, and the notes record it. The asthma chain accounts for about 8% of the association. The association should be registered as a direct claim that does not name asthma.

### A recommended change not accepted

#### graph-concordance-matrix (stays confirmed)

The referee recommended unsettled, on four grounds. A rule that always answers "positive" scores 64.2% against 66.1% for the graph's signs. The registered sign-shuffle null gives p = 0.14. Exposure-with-outcome pairs agree at 29 of 56. The lower bootstrap bound (59.6%) is below the 60% threshold. We accept the facts and do not accept the change of verdict. The registered support condition is written on the agreement rate itself (at least 60% and above the area-shuffle null's 97.5th percentile of 58.7%), and it is met, so rule 1 applies. Rule 8 covers bridges with endpoint tests. This claim is not a bridge. Extending rule 8 to it after the data would be a new rule applied retroactively against a registered condition.

The referee's second option is taken. The outcome now says what is confirmed: adverse indicators are positively correlated across neighbourhoods after partialling poverty. It says that the test does not show that the graph's signs carry information about the city. The stance is measured against the always-positive rate and falls from 0.94 to 0.20 (-0.45 to 0.90).

### Verdicts kept, with a number, stance or meaning corrected

#### further-subway-crime-per-million-repro (contested)

The referee objected that the label reads as a failure of the State's number, when it records the registrant's wrong guess about which data the State used. The rate in the registered table (MTA Major Felonies, yeek-jhmu) is per subway and bus rider. NYPD subway complaints over subway ridership from 1 January to 14 December 2025 give 1.653 and a fall of 29.5%, which reproduces the published 1.65 and 30%. We accept this, after a fresh query confirmed 2,028 complaints over 1,226.8 million rides. The notes and the settle field say this, and the sentence about arrests is removed. The verdict stays. The subway-only reading was found after the data, and under rule 4 a measure found after the data cannot decide a verdict. It should be registered as a new claim.

#### further-chinatown-shift (contested)

The referee objected that the notes wrongly attribute the mismatch to a boundary drawn closer to the Chinatown core. One tract set matches AALDEF's 2010 table exactly and a different set matches its 2020 column exactly, so the published table compares two areas. We accept this, after both matches were reproduced from the tract tables. The wrong sentence is replaced. On a fixed area the Asian decline is 24% to 26% when 2020 is measured with the ACS, the total falls, and the published growth of the other groups is mostly produced by the change of area.

The referee also noted that the stance treats a 90% margin as 95% and measures direction while the verdict measures counts. We accept this. The stance is recomputed (z = 6.75) and has a note. The notes also say that the undercount check raised the 2020 counts only, although the census may have overcounted Asian residents.

#### graph-confounders-trees-surftemp (unsettled)

The referee found that population density is overstated by about a factor of two for eight districts that share four PUMAs. With the error corrected the change is -0.25 (-0.99 to +0.58) in place of -0.40 (-1.11 to +0.34). We accept this and re-checked it. The `city_effect` field now gives the corrected change with the registered figure beside it, and the prediction is rescored from partial to miss, because the corrected change is outside the predicted band.

The referee also showed that the slope falls because the exposure's denominator changes, not because confounding is removed. With trees per km2 of street as the exposure the slope is -0.82 without any graph covariate. We accept this and record it as exploratory.

#### graph-confounders-commute-obesity (unsettled)

The referee objected that the stance (+0.88) is the sign of the slope, while the claim is about attenuation and its prediction was a miss. We accept this. The stance is set to null. The referee added a bootstrap interval for the attenuation (-14% to +64%), a leave-one-out result that reaches both the support and the refutation range, and the random-covariate comparison the registration had named. All are recorded.

#### graph-confounders-surftemp-ed (unsettled)

The referee objected that the stance (-0.24) assumes a predicted negative change when the claim predicts none. We accept this. The stance is set to null under rule 6. The referee also objected to the statement that the living-alone coefficient agrees with the graph, since its interval includes both zero and a value three times the derived one. We accept this. The statement is withdrawn. The miss of 0.09 points is smaller than the effect of removing one district, and the built-form secondary models used the overstated density; both are recorded with the corrected figures.

#### transfer-chicago-weekday-pattern (contested)

The referee found that the interval for Loop minus rest of system (-1.1 to 15.7) came from separate bootstrap samples for two series observed in the same weeks. A paired bootstrap gives 7.1 (6.2 to 8.0). We accept this and re-checked it. The corrected interval replaces the old one, and the secondary prediction that the Loop changed more is scored as met. The referee found that State/Lake has no entries on 234 days of the recent period. We accept this and record it. Excluding the station moves the result by 0.2 points.

The referee also showed that the 13.1 threshold is not robustly exceeded (12.4 to 16.1 across variants) and that one week of 2019 supplies the excess. We accept this and record it under rule 10. The verdict stays, as the referee advised: with disrupted weeks dropped in both cities the Loop is still 1.8 times the New York figure.

#### transfer-chicago-hot-end (unsettled)

The referee objected that the stance (0.86) describes only the shootings half of part (a), which was not blind, and says nothing about part (b), which failed. We accept this. The stance has a note. It is not set to null, because the referee did not ask for that and the value is a correct summary of the half it describes. The referee's intervals with autocorrelation-robust errors and the finding that part (a) depends on subscriber trips are recorded.

#### transit-gtrain-substitution (unsettled)

The referee objected that the stance (0.77) uses the clustered interval, which the outcome itself calls too narrow. We accept this. The stance is recomputed with the permutation standard deviation and is now 0.58 (z = 1.32). The weighted estimate (+0.020), the contradiction in the registration over zone 256, the stations on zone borders and the closures and reduced service inside the reference period are recorded.

#### further-datacentre-share-manhattan-v2 (confirmed)

The referee objected that the stance's interval does not include reporting error or tenant metering and that the national 4.4% is not a like-for-like comparison. We accept this. The stance is set to null. The referee found that D1 counts campus rows twice, that fifteen buildings classed as data centres are left out of the high figure, and that condition (b) passes by 0.011 points and fails at a PUE of 1.3. We accept this, and the notes record it. The conditions are still met when the double counting is removed and when the omitted buildings are added, so the verdict stays.

#### repro-dcp-2025-completions (confirmed)

The referee objected that the interval is the size of one earlier revision of the data and not a sampling interval, so the stance has no statistical meaning. We accept this. The stance is set to null, as for repro-dot-2025-deaths. The notes now say that the match is on release 26Q2.1 and that the permit figure was not reproduced.

#### repro-dot-2025-deaths (contested)

The referee objected that the label could be read as a finding against DOT's count. We accept this. The notes and a `verdict_note` say that the open NYPD tables do not reproduce DOT's reconciled count, and that the claim cannot test whether DOT's count is right. The referee's exclusion of medical events (217, still outside tolerance) and the low count for November 2025 are recorded. The referee's recollection of gaps in 2019 to 2021 is recorded as unverified.

#### repro-mmr-cbd-speed (confirmed)

The referee objected that fiscal 2026 rounds to 6.6 and not to the published 6.5, that five of nine registered readings of the published method pass, so the test does not identify which one DOT used, and that the interval is conditioned on the readings that passed. We accept this. All three are in the notes, and the stance has a note on its interval. The registration has no statement of the data the registrant had seen. That cannot be added to a registration and is recorded here.

### Verdicts kept, with qualifications added to the notes

#### heat-mech-outdoors (confirmed)

The referee found that the share of the heat-shootings slope removed by street-noise complaints is 0.24 in 2010 to 2019 and 0.84 in 2022 to 2026, and that next-day complaints, a negative control, remove 0.10. We accept this and re-ran the referee's script. The split by period and the negative control are in the notes with the referee's reading that complaints after 2020 may share a cause with shootings. The verdict stays because the registered conditions and the registered tripwire are met on the pooled series.

#### heat-mech-intox (unsettled)

The referee found no error and a share between 0.09 and 0.19 in every variant. The referee noted that same-day events such as parades and paydays are an unaddressed alternative, and that the first link was scored a hit against a range the registrant built. We accept this, and the notes record it.

#### further-zonej-demand-growth (contested)

The referee objected that the registered interval is about three times too narrow, and that the negative trend is a step of -5.7% across the pandemic window with a flat trend otherwise. We accept this. The `city_effect` field now gives the year-clustered interval (-1.03 to -0.48) and the step model beside the registered interval. The refutation condition is met under every method. The notes say that the verdict concerns the registered Zone J claim and not NYISO's statewide forecast. The missing PAL days are recorded. So is the Gold Book forecast comparison, which the registration said to report as not done with fewer than five editions.

#### further-containers-rats-cd9 (unsettled)

The referee objected that the interval is too narrow, since untreated districts vary twice as much as the bootstrap allows, and that the registered quasi-Poisson check was not reported. We accept this. The `city_effect` field now gives the wider interval (0.69 to 1.49) and the referee's fit of the check. The dependence on the pre-trend and on repeat calls, and the installation of bins inside the pre-period, are recorded.

#### further-subway-crime-per-ride-by-hour (unsettled)

The referee objected that the State's fall is measured from 2021 and the test from 2019. On the 2021 baseline the late-night rate fell about 19% and the daytime rate about 35%. The referee also found that late-night felony assaults per entry roughly doubled while robbery and larceny fell. We accept this and record it as exploratory.

#### further-tidal-flooding-trend (confirmed)

The referee objected that 2.00 per 10 cm depends on the knot and that the Rockaway ZIP codes carry the effect. We accept this, and the notes record it. The referee's split of the water level into predictable tide and remainder, which is evidence against the weather rival, is also in the notes. The referee found three psychotherapy trials filed under flooding in the graph findings file. No outcome cites them, `docs/round2.md` already describes the mis-grounding, and the file is left as fetched.

#### retimed-ems-presence (confirmed)

The referee found that the contrast depends on Midtown district 105: without district 105 the interval includes zero, and the interval of the contrast with the rest of Manhattan also includes zero. We accept this and record it, with the night placebo that supports the claim. The settle field now asks for call type. The rise in incidents without a district code and the elasticity interval, which is too narrow, are recorded.

#### retimed-taxi-fhv-pickups (unsettled)

The referee objected that the two registered measures disagree, that the rank correlation across zones is 0.11, and that a weekend placebo has a slope of -0.79. We accept this, and the notes record it.

#### split-temp-asthma-ems (unsettled)

The referee objected that the sign of the cool-season slope depends on how time is controlled, so the bound applies only within a month at short lags. We accept this. The settle field is reworded. The referee's test of the difficulty-breathing codes and the finding that one Hefei study supplies several graph rows are recorded.

#### split-temp-covid-growth (unsettled)

The referee found that the last weeks of the admissions file are incomplete and that the filter let one incomplete week through. We accept this and record it. Dropping the last three weeks gives +0.0078 (-0.0009 to +0.0165). The unstable sign under precision weights and the mixed coding of PMID 33162141 are recorded.

#### transfer-chicago-heat-shootings (confirmed)

The referee found no error and noted that the average slope transfers while the shape does not: Chicago flattens above 20 C and New York steepens. We accept this, and the notes record it.

#### transit-weekday-pattern (confirmed)

The referee noted that the size is nearer 7.4 than 8.7 without two disrupted weeks, that condition (b) passes narrowly, and that the outcome supports the pattern and not its attribution to hybrid work. We accept this, and the notes record it.

#### heat-trees-canopy-within-nta (confirmed)

The referee asked that the label say the confirmed claim is the association, since vegetation 200 to 300 m away is as strong as the local share. We accept this. The referee's ring model and the alternative of shade on the sensor housing are recorded, with the difference in slope between 2018 and 2019.

#### bridge-crz-injury-crashes-v2 (unsettled)

The referee found that the comparison area includes highways, that the record format changed differently in the two areas, and that the verdict `bridged` could not have been reached under the registered rule. We accept this, and the notes record it. The registration attributes PMID 23411678 to the wrong authors. A registration cannot be edited, so the correction (Harris et al. 2013) is in the outcome's notes.

#### graph-triad-hot-asthma-absence (unsettled)

The referee found no error and added a placebo: exposure two days ahead gives 1.021, as large as the estimate. We accept this, and the notes record it. The stance is set by the endpoint formula (0.04) so that both arms of the triad are treated alike.

### What the round did not do

No new claim was registered. The candidates are the subway rate on NYPD complaints over subway ridership, the Chinatown change on the two exact tract sets, the cold-day absence association without asthma, the late-night rate on the State's 2021 baseline, and street trees per km of street. The analysis scripts of decided claims were not corrected: the density error, the unpaired bootstrap and the missing quasi-Poisson check remain in the code, and the corrected numbers are in the outcomes.

## Round 5: two reports on the round 5 claims

Fresh referee agents reviewed heat-night-minimum and transfer-chicago-concordance-matrix on 13 November 2026, under the same conditions as Round 4. A different agent from the registrants wrote these answers, and "we" below is that agent. It re-ran both referee scripts, which printed the figures quoted here. `analyses/critique/answer_round5.py` applies the answers through `concord.claims.revise`. No registration was changed and no verdict changed. With these two claims there are 64 registrations and 63 outcomes: 21 confirmed, 10 contested, 27 unsettled, 4 no_test and 1 bridged.

### heat-night-minimum (stays unsettled)

The referee reproduced every number and found that the verdict follows from the registered conditions. Twelve further specifications give New York estimates between 0.997 and 1.060, each with an interval that includes 1.00. We accept the report's six requested changes.

The ratio for shootings between 00:00 and 05:59 was reported as 1.13 without its unit. It is the ratio for 33 against 27 °C, which is 6 °C. Per 5 °C it is 1.106 (1.017 to 1.201) in New York and 1.107 (1.033 to 1.185) in Chicago. The six-hour blocks were registered as a table with no prediction about which block would carry the excess, so the choice of the block after midnight was made after the data. The notes now say this and give the p values corrected for four blocks: 0.07 in New York, 0.016 in Chicago and 0.0008 for the two cities together.

The notes now say that the excess after midnight, the association with the following night's minimum and the difference between calendar days and shooting days are one observation: shootings in the small hours follow the temperature of the night in which they occur. They record that the New York following-night ratio falls from 1.112 to 1.073 (0.989 to 1.164) with the next day's maximum and rain in the model, that two placebo checks pass, and that humidity was named as a rival and not tested.

The referee found that `run.py` shifts rows of the weather file where it should shift calendar days. The Midway file lacks two dates. With the shift corrected, Chicago has 1,479 hot days in place of 1,481 and the estimate is 1.009 (0.966 to 1.054) against 1.009 (0.967 to 1.054). We did not correct the script. It was fixed with the registration under rule 9, and the correction would change the registered count of days. The outcome records the error.

The stance was 0.416, the z of the estimate against no effect. The registration says that the test cannot tell the effect implied by the graph (1.012) from no effect, with D of 0.13 and 0.37. The stance is now null, as for the claims treated in the same way in Round 4.

The referee also found that the earlier claims counted shootings by calendar date, so that shootings between 00:00 and 05:59 precede the maximum they are regressed on, and suggested a verdict rule. We accept the criticism and did not add a rule. Under rule 4 a count chosen after the data cannot decide those verdicts. We re-estimated the registered models with shootings before 06:00 counted with the previous day (`analyses/critique/round5_night_of_check.py`) and added the results to the outcomes of heat-shootings and heat-mech-outdoors. No registered condition changes side in either claim.

| Quantity | Calendar date | Shooting day, 06:00 to 05:59 |
|---|---|---|
| New York, rate ratio per 5 °C (heat-shootings) | 1.146 (1.130 to 1.163) | 1.135 (1.118 to 1.152) |
| Chicago, rate ratio per 5 °C (transfer-chicago-heat-shootings) | 1.131 (1.120 to 1.143) | 1.134 (1.122 to 1.146) |
| Share of the slope removed by street-noise complaints (heat-mech-outdoors) | 0.44 (0.33 to 0.56) | 0.53 (0.41 to 0.66) |
| The same with year-by-month terms | 0.32 (0.21 to 0.44) | 0.41 (0.30 to 0.54) |
| New York, 33 against 27 °C, piecewise-linear | 1.102 (1.038 to 1.171) | 1.051 (0.988 to 1.118) |
| New York, 33 against 27 °C, cubic spline | 1.122 (1.072 to 1.173) | 1.090 (1.041 to 1.141) |
| Chicago, 33 against 27 °C, piecewise-linear | 1.059 (1.014 to 1.105) | 1.035 (0.991 to 1.082) |

The average slopes do not depend on the count. The rise above 27 °C does: between a quarter and a half of it, on the log scale, came from shootings after midnight counted on the hot date. One registered condition of a third claim would change side. Part (a) of transfer-chicago-hot-end requires the lower limit of the Chicago ratio for 33 against 27 °C to be above 1.00, and on shooting days the limit is 0.991. That claim is unsettled already, its outcome was not revised, and the point was reported to the coordinator.

### transfer-chicago-concordance-matrix (stays confirmed, for the count only)

The referee reproduced the counts and the bootstrap interval under another seed, found that every registered support condition is met, and recommended keeping confirmed under rule 1 for the count only. The alternative offered was unsettled, if the clause of the statement about residential sorting is read as part of what the label covers. We keep confirmed. Rule 1 says that the registration's support and refutation conditions decide the verdict when they are met. The support condition names four things: at least 12 pairs, a share of at least 60%, a lower bootstrap limit above 0.370, and a share above New York's on the same pairs. All four hold, under the registered seed, five other seeds and the referee's. The sorting clause is in the statement and in no condition. Round 4 treated graph-concordance-matrix and transit-weekday-pattern in the same way: the label covers what the condition tested, and a `verdict_note` says what it does not cover.

We accept the referee's findings about what the count means, and the outcome's `verdict_note` and notes now state them. The difference between the cities is PM2.5 alone: 5 of 6 pairs in Chicago against 0 of 6 in New York, and 7 of 9 against 6 of 9 without them. Chicago's PM2.5 has a range of 0.7 µg/m³, and a plane in the coordinates of the areas explains 85% of its variance. With the coordinates partialled out together with poverty, 1 of the 6 PM2.5 pairs agrees. The effective number of areas for the PM2.5 pairs is 12 to 31, and none of the fifteen correlations has p below 0.05 at its effective number. Against a null that shuffles the three exposures together, 12 or more pairs occur with probability 0.04, and a count as extreme in either direction with probability 0.08. A city at the general agreement rate of about 70% would also have passed. The result therefore does not test the sorting explanation, and the write-ups no longer say that it supports it.

Three corrections were made. Four agreeing pairs have a correlation under 0.1, not three. Prediction (b), that PM2.5 rises with poverty in Chicago, is rescored from hit to partial: the registered scoring rule, a bootstrap interval that excludes zero, gives a hit, but the bootstrap treats areas as independent, and at an effective number of about 10 areas the correlation of +0.29 has p = 0.43. The stance falls from 0.987 to 0.748 (0.102 to 0.829). It is now measured against the exposure-shuffle null (mean 7.5 pairs, standard deviation 2.3) in place of New York's 0.370.

We do not accept one statement. The report says that the claim has no prereg branch. `git ls-remote` on the remote lists `refs/heads/prereg/transfer-chicago-concordance-matrix` at commit 2805fb3. The commit was made at 01:23:04, four seconds before the first Chicago Health Atlas file was cached, and holds the registration and the three scripts with the content of commits 499547c and 0ba7f1a. The outcome records this in a `prereg` field. The referee's wider point stands for this claim as for the others: git records the commit time and not the push time.

### What the round did not do

No new claim was registered. The candidates are the block from 00:00 to 05:59 as a primary outcome with hourly temperature and dew point, and the concordance matrix in many cities with one pollution measure. `run.py` was not corrected. The verdicts of the claims that counted shootings by calendar date were not re-decided, and the stability over time of the share removed by street-noise complaints was not re-examined on shooting days.


# Round 6 (13 November 2026)

Ten claims registered on 13 November were each reviewed by a blind referee. Every deciding number reproduced. One verdict changed (bridge-crz-ems-travel, confirmed to unsettled) and the reading of most others was narrowed. The answers follow in three parts.

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


## Round 6: three reports on the affordability and street tree claims

Fresh referee agents reviewed afford-gentrification-prevalence, afford-poor-count-shift and all-boats-trees-rent on 13 November 2026, under the same conditions as Round 4: each had the code, the data and the registration, and none had the registrant's reasoning or the write-ups. A different agent from the registrants wrote these answers, and "we" below is that agent. `analyses/critique/answer_round6_afford.py` applies the answers through `concord.claims.revise`. Before it revises anything it re-runs both referee scripts (`referee_afford.py` and `referee_trees_rent.py`) and stops if any figure quoted in an outcome is absent from their output. No registration was changed and no verdict changed. The three stances are now null. A stance is the score, shown on the viewer's strip, for how far a city estimate agrees with the direction the research gives. The rules cited below by number are the precedence rules in `concord/claims.py`. `docs/affordability.md` and `docs/all_boats.md` were edited to agree with the revised outcomes.

### afford-gentrification-prevalence (stays confirmed, as a measurement)

The claim was that a minority, between 4 and 11, of the 22 sub-borough areas with the lowest rent in 2000 had both rent and the share of college graduates rise faster than the city's by 2022-2024, with a positive association between the two across all 55 areas. The referee rebuilt the area table with separate code and reproduced the count of 8 of 22, the count of 8 from the 2005-2007 baseline, and the rank correlation of 0.68 (0.50 to 0.80). All registered conditions are met, and under rule 1 the verdict follows from the registered conditions, so the verdict stays confirmed. We accept all seven requested changes.

The prediction was not blind, because before registering the registrant read the output of a code test that multiplied the real later values by random noise when it should have replaced them. The referee rebuilt that test and showed that the output the registrant read carried information about the real result. Over 400 other seeds the simulated count has a mean of 6.9, about 5.4 of the areas in a simulated set are among the true eight, and the simulated count is between 4 and 11 in 79% of draws. The registration states that the thresholds and the script were written before that run. The repository cannot confirm the order: no commit precedes the registration commit at 07:47:16, the script's last save at 07:43:44 is compatible with either order, and the file that the test wrote is no longer in `data/derived/affordability/`. The referee judged tuning unlikely, because the window of 4 to 11 is wider than a count of 6 in that output would suggest and because two of the six areas named in the prediction were not in the list that output showed. We accept that judgement, and that the repository cannot confirm the order. The outcome now carries a `verdict_note` that calls the result a measurement under a fixed definition, and `prediction_scored` reads "not blind" in place of "hit".

The count depends on how the rent and college conditions are defined. Over the referee's 35 combinations of seven rent rules and five college rules it ranges from 5 to 12, and 34 of the 35 are between 5 and 11. Five Brooklyn areas are in the set under every end period tried and exceed the city's rent growth by 42 to 96 percentage points. The three upper Manhattan areas exceed it by 8.7, 7.9 and 0.8 points, and Washington Heights/Inwood leaves the set in five of the ten other end periods. The notes now say that five areas changed by a wide margin and that two to five more are near the threshold.

The low-rent areas are not distinguishable from the rest. Six of the other 33 areas meet both conditions, which is 18% against 36%. We recomputed Fisher's exact test of the two shares and obtained p = 0.21, as the referee did. The notes now say that the data do not show that low-rent areas gentrified more often than other areas. They also record the referee's point about the benchmark: the city's growth in rent and in college share is above the median area's, so the reading "common" (12 or more of 22) was unlikely under this benchmark, and the correlation condition was the one most likely to refute the claim.

The stance of 0.957 is now null. Under rule 6 the stance is null when the city effect has no null value that expresses the research direction, and the rule's example is a raw proportion with a null of 0, which is what the city effect is here. The `graph_effect` of 0.24 (0.18 to 0.33) (the share of neighbourhoods classed as gentrifying in studies held by the System Public Graph) is now labelled as the lowest and highest of three studies' shares and not as an interval.

### afford-poor-count-shift (stays confirmed, for the change of a count)

The claim was that the number of residents below the poverty line fell more in the 8 gentrified areas than in the 14 other low-rent areas. The registered condition is an upper limit of the Welch interval below zero. The referee reproduced the difference in mean log change of -0.283 (-0.544 to -0.021, n = 22, p = 0.036). We accept all eight requested changes.

We do not accept one part of the referee's reasoning. The report recommends keeping the verdict because end periods before the 2022 boundary change give a clearer result, -0.243 (-0.350 to -0.137) for 2017-2019. Those periods were chosen after the data, and under rule 4 a measure chosen after the data decides nothing. Under rule 1 the verdict stays confirmed because the registered condition is met, and the `verdict_note` records that the earlier periods do not decide it.

The registered condition is met by a small margin, and the notes now record how small. Six of the 22 single removals of an area put the upper limit at or above zero. So do the end years 2023 and 2024 taken singly, and the reclassification of Washington Heights/Inwood or East Harlem, which are 0.8 and 2.0 points from the rent threshold. The point estimate is negative in every variant. The main cause is the 2022 change of survey areas, which changes a count directly, because a count is a rate multiplied by a population. The standard error of the difference is 0.050 for 2017-2019 and 0.121 for 2022-2024, and the shift in an area's log change between those periods correlates 0.69 with its population jump between 2021 and 2022.

The notes also record four limits that the registration did not name. Seven of the 14 comparison areas are in the Bronx, and with borough held constant the registered difference is -0.173 (-0.479 to +0.132). The 22 areas adjoin one another in groups, so the interval, which assumes independence, is too narrow by an unknown amount. The gentrified and comparison sets are defined partly by a rising college share from the same survey samples that give the poverty count. Most of the difference arose between 2010-2012 and 2017-2019. On the last point the report's text gives -0.154 as the contrast "to 2017-2019", while the referee's script computes it for the change from 2010-2012 to 2017-2019; the notes give each period as the script computes it.

A falling count cannot show displacement. In the gentrified areas the number of residents above the poverty line rose 24.6% while the number below it fell 29.2%. The same figures would result from poor residents moving out, from deaths and ageing, from rising incomes among residents who stayed, or from households counted in another area after the boundary change. The `verdict_note` now states that the verdict covers the change of a count and is not evidence on displacement.

The stance of 0.786 is now null, because the graph has no finding on counts of poor residents and the studies cited follow individuals, so there is no research direction for the city contrast to agree with. The prediction is no longer scored as a blind hit, because the predicted range was written after the simulated run described above. The registrant states that the part of the output for this claim was not read. The referee's rebuild found nothing that contradicts this, and the notes say that it rests on the registrant's account.

### all-boats-trees-rent (stays unsettled)

The claim was that rents rose faster in census tracts that gained more street trees between the 2005 and 2015 tree censuses, by the amount a Portland study implies, 0.044 log points per 100 trees (0.018 to 0.070). The referee rebuilt the tree counts and the rents from the source files, matched the registrant's values in every tract and refitted the registered slope of 0.0127 (0.0018 to 0.0235) on 2,048 tracts. Neither registered condition is met, and the verdict stays unsettled. We accept all the requested changes to the outcome. We did not make the new registration that the report suggests, and the outcome's `settle` field now describes that proposed registration.

The exposure is only partly planting. The net change in living trees correlates 0.31 with the number of trees of 3 inches or less in 2015 and -0.35 with the 2005 count. In Queens and Staten Island, which hold 37% of the tracts, the correlation with young trees is 0.29 and 0.10, so the exposure there mostly measures losses or differences between the censuses. In the 2005 file 8,840 trees have a longitude of zero and fall in no tract. We computed that this is 12% of the counted citywide gain of 76,583 trees. The change in trees of 12 inches or more, which cannot be planting, has a slope of 0.0201 (0.0018 to 0.0385), against 0.0097 (-0.0032 to 0.0226) for the change in smaller trees.

The size is not stable: over the referee's variants the slope per 100 trees ranges from 0.0073 (-0.0044 to 0.0179), with baseline rent corrected for sampling error, to 0.0326 (0.0125 to 0.0527), with tracts that changed by 200 trees or more left out. The widest interval reaches 0.057, and the slope per square km corresponds to 0.045 per 100 trees at the median tract area, which is the central prediction. The outcome had said that the estimate was 29% of the central prediction. That description holds for the registered form only, and it has been withdrawn from `prediction_scored`. The variants were chosen after the data and decide nothing under rule 4.

The lower limit is not robust. The interval includes zero without baseline rent, with population change, with fixed effects for districts or neighbourhoods, and with the correction for error in baseline rent. The statement that the interval excludes zero has also been withdrawn from `prediction_scored`. The notes record that the 300,000 dollar price behind the prediction is an assumption, that the baseline rent window lies inside the planting period, that new construction is a rival the registration did not name, and that no test of a prior trend was possible because the project holds no rent before 2008-12.

The stance of 0.817 was the distance of the estimate from no effect, and on the strip it read as agreement with the prediction. On the registered model the estimate is 5.67 standard errors below the predicted value, and under other forms it is compatible both with zero and with the prediction, so the stance is now null.

One sentence in the write-up was replaced. `docs/all_boats.md` said that the estimate was 29% of the Portland figure, which a reader would take to mean that New York shows less rent effect than Portland predicts. The note now says that these data cannot say whether street trees raised rents.

### What the round did not do

No new claim was registered. The candidates are the tree test with trees of 3 inches or less per square km as the exposure and 2000 census rent as a test of prior trend, and the gentrification count on census tracts with fixed boundaries. The registered scripts were not changed. The spatial dependence among the 22 sub-borough areas was not estimated. The viewer's data files in `viz/data/` were not regenerated.


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


