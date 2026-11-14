# Referee report: retimed-ems-presence

Verdict recorded: confirmed. The referee re-ran the analysis from the cached queries and from five new Socrata queries. Scratch code is outside the repository (session scratchpad, folder `referee-retimed-ems-presence`).

## (a) Does the verdict follow from the registered conditions?

Yes. Support required the 95% interval of the contrast C to lie below zero. C is -0.029 (-0.045 to -0.011). No measure chosen after the data decided the verdict. The pooled contrast, the six districts, the 54 units, the hours, both periods and the bootstrap were all named in the registration.

The registration is dated 23:48:46 and was committed at 23:48:55 (5c3e763). The branch `prereg/retimed-ems-presence` exists on the remote and points to a commit made at 23:48:59 that holds only the registration file. The primary queries for 2016, 2019 and the two recent years were fetched between 23:51:09 and 23:54:06, after the push. The queries for 2017 and 2018 were fetched at 23:44:05 and 23:44:43, before registration. The registration discloses this: 2018 is half of the baseline, and the registrant had seen the 2017-to-2018 contrast (-0.013), not any recent year. The outcome is dated 00:05:03.

Two things cannot be shown from git. The estimator `lib.py` and the exposure files were not committed until 00:06:16, with the outcome, so "written before registration" rests on file times. `lib.py` and `ems.py` were last modified at 23:55, after registration and after the first EMS fetches. The current `lib.py` reproduces the taxi results written at 23:50 to the last digit, so the estimator itself did not change in a way that matters. The bootstrap seed (7) was not registered. Five other seeds give upper bounds for C between -0.011 and -0.012, so the seed does not matter here.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error that changes the result. My re-estimate is C = -0.0288 (-0.0447 to -0.0109), elasticity 0.45 (0.17 to 0.70), identical to the outcome. A Poisson standard error from the eight pooled counts is 0.0081 against the bootstrap 0.0087, so there is little overdispersion by week. No query was truncated (about 23,700 rows each against a limit of 50,000).

The interval of the elasticity treats the denominator, -0.0639, as known. It is an estimate from subway entries with its own error, and its periods differ from the outcome's (2019 against November 2025 to October 2026 for entries; 2018-2019 against October 2024 to September 2026 for incidents). The interval of the elasticity is therefore somewhat too narrow. This does not affect the verdict, which rests on C.

Incidents without a district code rose from about 1.0% of daytime incidents in every earlier year to 2.4% in October 2025 to September 2026, with a step in January 2026 (about 900 a month before, 2,000 to 2,900 after). The rise is mostly in Queens and Brooklyn, and in Manhattan it is spread evenly over weekdays (367 on Mondays and 390 on Fridays against a midweek mean of 403 for January to September 2026). It is too small and too even to produce the contrast, but the outcome does not mention it.

Robustness variants the registrant did not run:

- Night placebo. Incidents from 20:00 to 05:59, same districts, weeks and estimator: C = +0.009 (-0.014 to +0.032). Evening only (20:00 to 23:59): +0.001 (-0.033 to +0.034). The fall is confined to the working day.
- Comparison group. Against the six other Manhattan districts (107 to 112) C is -0.021 (-0.043 to +0.002). Against districts outside Manhattan it is -0.030 (-0.047 to -0.013). Adding the five districts without a reliable station to the rest gives -0.029 (-0.046 to -0.012).
- Leaving out one business-district district at a time gives -0.016 to -0.036. Without district 105 (Midtown) it is -0.016 (-0.036 to +0.004). Alone, 105 gives -0.071 and 104 gives -0.039; 103 and 106 give 0.000 and +0.011. District 106 has nearly the largest thinning of entries (-0.136) and no change in incidents.
- Baseline 2016-2019: -0.030 (-0.044 to -0.015). Each single baseline year against each single recent year gives a negative C, from -0.013 to -0.048. The first recent year gives larger falls than the second.
- Adjacent years before 2020 give +0.024, -0.013 and -0.001, each with a standard error near 0.013. Year-to-year movement is about the size of the sampling error and no larger.
- With the two storm weeks kept: -0.028 (-0.044 to -0.011).

## (c) Is the comparison with the research fair?

No research figure is compared. The registration says the graph holds no finding on call volume and people present, and `graph_effect` is empty. I checked one finding named as a near miss, PMID 23918257, against its PubMed abstract: ambulance calls from places other than casinos fell after a smoke-free law, incidence rate ratio 0.772 (0.685 to 0.871). The registration describes it correctly and does not use it as evidence.

The elasticity is per unit of thinning of subway entries, not per person present, as the outcome notes. The registered slope across 54 districts on the same scale is 0.30 (-0.17 to 0.75), which does not contradict 0.45 and does not confirm it.

## (d) Alternative explanation not addressed

The result depends on Midtown. Five of the six districts thinned by similar amounts, but the fall in incidents is in 105, 104 and 101, and is absent in 106 and 103. A dose-response within the business district is therefore not shown, and something particular to Midtown on Mondays and Fridays (events, hotels, the large shelter intake sites that operated there in 2023 to 2025, a change in station or unit coverage) is not separated from office attendance. Call type would separate them, and the outcome's settle condition asks for location type but not call type, which the dataset already has.

The second gap is the direction of the change within the week. The business-district index fell on Friday (1.010 to 0.956) and Monday (0.987 to 0.962) while Wednesday rose (0.998 to 1.013). Part of the contrast is a midweek rise, which also follows from concentrated office days, but the statement says incidents "fell on Mondays and Fridays".

## (e) Could the test have failed?

Yes. The registration's design check put the standard error of C at 0.009 and the realised value is 0.0087. A true elasticity of zero would have met the support condition 2.5% of the time. As an elasticity the standard error is 0.136. The estimate is 0.37 standard errors from the central prediction of 0.4 and 3.3 from no effect, so D = 10.8. The 2016-17 against 2018-19 placebo (-0.002) and the night placebo (+0.009) both came out null, which they need not have done.

Recommendation: keep. The registered condition is met, the number reproduces, and the night placebo and alternative baselines agree; the notes should say that the contrast loses significance without district 105 and against the rest of Manhattan.
