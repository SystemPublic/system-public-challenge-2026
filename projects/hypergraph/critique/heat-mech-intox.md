# Referee report: heat-mech-intox

Verdict recorded: unsettled. Recommendation: keep the verdict.

Scratch code and output: `referee-heat-mech-outdoors/ref.py`, `boot.py` and `boot.out` in the session scratchpad (the two heat-mechanism claims share one script). All re-estimates read `data/derived/graph/heat_mechanisms/mediators_daily.csv`.

## (a) Does the verdict follow from the registered conditions?

Yes. The claim is that there is no measurable step. Confirmation required A below 0.10 with an upper bootstrap limit below 0.25. Contest required A of at least 0.25 with a lower limit above 0.10 and a positive proxy coefficient. A is 0.141 (0.095 to 0.188), which meets neither, so rule 2 of PRECEDENCE gives unsettled. The year-by-month variant (0.165, 0.124 to 0.217) lies in the same band. The first-link prediction is scored separately, as registered, and is a hit: 1.045 (1.041 to 1.048) per 5 C against 1.01 to 1.06. The score of partial is correct.

Nothing was decided by a measure chosen after the data were seen.

The registration was committed at 22:21:55 and 22:21:56 on 12 November 2026 (cddeb94 and f7ec41f), and `prereg/heat-mech-intox` exists on the remote at f7ec41f. The EMS query for DRUG and EDP dispatches was fetched at 22:37:26, and the 311 queries at 22:25:41 and 22:33:30. The outcome was decided at 23:34:28. Earlier cache files for 76xm-jjuj date from 15:59 to 16:08 and belong to the SHOT and STAB dispatches and the 2023 totals by call type that the registration lists as already seen. The push time cannot be checked from the repository.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error. The code fills missing EMS days with zero, which would be wrong if the dispatch file ended before 31 August 2026. It does not: the series has no zero day, its minimum is 85, and the 2026 mean (223 a day) is in line with 2025. My refit gives A = 0.141 (b0 = 0.1365, b1 = 0.1172, 7,548 days), and a week bootstrap with a different seed gives 0.090 to 0.184.

Variants the registrant did not run:

| Variant | A | Interval or note |
|---|---|---|
| Primary, refit | 0.141 | 0.090 to 0.184 |
| Street-noise complaints already in both models (2010 to 2026) | 0.166 | 0.086 to 0.277 |
| Year-by-month and week-of-year terms | 0.191 | |
| Week-of-year terms in place of month | 0.152 | |
| TMIN, previous-day TMAX and rain amount added to both models | 0.094 | of a smaller base slope (0.095) |
| 2010 to 2019; 2022 to 2026 | 0.154; 0.107 | |
| Friday to Sunday; Monday to Thursday | 0.122; 0.133 | |
| Top and bottom 0.5% of dispatch days removed | 0.121 | |
| Next-day dispatches (negative control) | 0.017 | |
| Dispatches seven days later; seven days earlier | 0.002; -0.001 | |

The share stays between 0.09 and 0.19 in every variant. No variant moves it below 0.10 with any margin or near 0.25. The verdict does not depend on a choice of specification.

## (c) Is the comparison with the research fair?

Partly. I checked Nori-Sarma et al. 2022 (PMID 35195664) against its PubMed abstract: the IRR for emergency department visits for substance use disorders on days of extreme heat is 1.08 (1.07 to 1.10), as recorded. The outcome there is an insurance claim for an emergency visit with a substance use diagnosis among insured adults, in May to September, in a case-crossover design. The exposure is a day at the 95th percentile of the county's warm-season maximum. The city measure is an ambulance dispatch coded DRUG over the whole year, per 5 C. The registration converts the published figure to a per-5 C range by assuming a reference about 20 C cooler; the abstract does not give the reference, so that conversion is an assumption and the first-link hit (1.045 inside 1.01 to 1.06) is a match with a range the registrant built. The direction comparison is fair. The graph has no finding on whether intoxication on a given day raises shootings that day, so the attenuation has no research counterpart; the alcohol and violence findings it holds are not daily.

## (d) Alternative explanation not addressed

The registration names the possibility that dispatches measure people in public view. I tested it with the proxy the sister claim uses: with street-noise complaints already in the model, drug dispatches still remove 0.166 of the remaining slope, so that alternative, as far as noise complaints measure street presence, does not account for the result. The alternative that is not addressed is a same-day event that produces both ambulance calls for intoxication and shootings without heat acting through intoxication: parades, street parties, paydays and large gatherings. The share is confined to the same day (0.028 for the previous day, 0.017 for the next day), which is what such events would produce and also what drinking on the day would produce. The holiday term covers federal holidays only. The call type also cannot separate alcohol from opioids, and the two need not move together with heat.

## (e) Could the test have failed?

Yes, and the prediction did fail. The registered prior for no measurable step was 0.75 and the predicted range for A was -0.02 to 0.08. With a bootstrap standard error of 0.024, A is 5.9 standard errors from zero, 4.6 above the middle of the predicted range, 1.7 above the 0.10 ceiling for confirmation and 4.6 below the 0.25 floor for contest. The claim of no step is therefore not supported, and a step as large as a quarter of the slope is excluded. The registered rule has no verdict for a small non-zero share other than unsettled.

Recommendation: keep. Neither registered condition is met, and A stays between 0.09 and 0.19 in every variant I ran.
