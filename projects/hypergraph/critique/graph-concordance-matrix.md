# Referee report: graph-concordance-matrix

Verdict recorded: confirmed. The referee did not register this claim and did not read the registrant's write-ups. Scratch code is in the session scratchpad under `referee-graph-concordance-matrix/ref_matrix.py`.

## (a) Does the verdict follow from the registered conditions?

The verdict follows from the letter of the registration. Support required an agreement rate of the deciding correlation of at least 60% and above the 97.5th percentile of the area-shuffle null. The rate is 72 of 109 (66.1%) and the null's 97.5th percentile is 58.7%. Under rule 1 of PRECEDENCE this gives confirmed. No measure chosen after the data decides the verdict. The always-positive benchmark, the sign-shuffle null and the strict subsets were all named in the registration as reported quantities.

The order of events is consistent with registration before the city data. The registration is stamped 22:49:55 and was committed at 22:49:56 (1497480). The branch `prereg/graph-concordance-matrix` exists on GitHub at 1a049ae, committed 22:50:03. `city_indicators_uhf42.csv` was written at 22:50, `results.json` at 22:52, and the outcome is stamped 22:54:31. `literature_signs.csv` was written at 22:49, before registration, as the registration says. Two things cannot be checked from git. The analysis scripts were first committed with the outcome at 01:00:54 on 13 November, so git does not show that `matrix.py` (file time 22:37) was fixed before the data. `city.py` has a file time of 22:50, after the registration, and it is the script that selects the EHDP period for each indicator.

"Confirmed" is not the right word for the claim as a reader will understand it. The statement says the city's sign matches the literature's sign more often than chance. The registered null defines chance as 50%, which is the rate when each indicator is shuffled across neighbourhoods. That null is rejected by any set of indicators that are positively correlated with each other, whatever the literature says. Of the 109 literature signs, 105 are positive, so a rule that ignores the literature and always answers "positive" scores 70 of 109 (64.2%). The literature's signs add two pairs to that. The four pairs with a negative literature sign split three to one in the literature's favour (Fisher exact p = 0.13), and the registered sign-shuffle null gives p = 0.14. What the test confirmed is that these indicators, coded so that higher means more of an adverse condition, are positively correlated across neighbourhoods after partialling poverty. It did not show that the graph's signs carry information about the city. The outcome's `settle` text says this, but the verdict label and the stance (0.937) do not.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I recomputed the deciding correlations from `city_indicators_uhf42.csv` and `literature_signs.csv` with my own code and reproduce 72 of 109 (0.6606), raw 0.798, and always-positive 0.642 deciding and 0.761 raw. I found no error in the partial correlation or the agreement count.

The lower bootstrap bound (0.596) is below the 60% threshold, and 5% of my 1,000 resamples of neighbourhoods fall below 60%. The support condition is applied to a point estimate that sits about 1.3 bootstrap standard errors above the threshold.

The 109 pairs involve 30 indicators, and seven indicators (depression, adult asthma, premature death, diabetes, low birthweight, psychiatric hospitalisation, cognitive difficulty) each appear in 12 to 19 pairs. Leaving one indicator out moves the rate between 63.5% and 70.0%. The area-shuffle null accounts for this dependence only under independence of the indicators, which is the hypothesis nobody holds.

Variants the registrant did not run:

| Variant | Pairs | Agreement | Always positive |
|---|---|---|---|
| Registered | 109 | 66.1% | 64.2% |
| Outcome with outcome | 41 | 82.9% | 82.9% |
| Exposure with outcome | 56 | 51.8% | 48.2% |
| Exposure with exposure | 12 | 75.0% | 75.0% |
| Poverty and borough partialled | 109 | 66.1% | 62.4% |
| Poverty and foreign-born share partialled | 109 | 67.0% | 65.1% |
| Poverty and high-school completion partialled | 109 | 65.1% | 63.3% |
| At least 5 signed studies | 88 | 63.6% | 62.5% |
| At least 10 studies and 90% consistency | 36 | 66.7% | 66.7% |

The exposure-with-outcome pairs are the ones in which the literature's sign says something about a cause, and they agree at 29 of 56, which is chance. The overall rate is carried by the 41 pairs of two health outcomes, where agreement and always-positive are the same number. The outcome's breakdown by kind shows part of this (air, traffic and noise pairs at 10 of 27) but does not state the exposure-outcome total.

The indicator periods differ by more than a decade (walkability 2011, infant deaths 2013, pollution 2025). This adds noise but I see no direction of bias. The correction from 48 to 50 mapped indicators is reported in the notes.

## (c) Is the comparison with the research fair?

The comparison is fair only at the level of sign. The literature's findings are mostly individual-level associations from cohorts in other countries, and the city side is a cross-section of 42 areas. The outcome's own check of ten abstracts found four graph errors, including one that reverses a sign. I checked PMID 37229603 against PubMed. The abstract gives an odds ratio for diabetes of 1.31 (1.22 to 1.41) per interquartile range of PM2.5, as the outcome says. The population is Taiwanese women followed for a mean of 10.2 years after childbirth, and the exposure is PM2.5 interpolated to townships. The city pair is adult diabetes prevalence against annual mean PM2.5, which ranges only from 5.7 to 8.8 across UHF areas. The sign is comparable. The exposure contrast and the population are not.

## (d) Alternative explanation not addressed

Common valence is named in the registration and measured, and it accounts for nearly all of the result. The alternative that is not addressed is selection into the qualifying set. A pair qualifies only with three studies and 80% sign consistency, and published associations between two adverse conditions are overwhelmingly positive. The qualifying set therefore contains almost no negative signs by construction, and the test cannot separate "the literature is right about New York" from "the literature and the city both show that bad things go together". Residential sorting within the pollution pairs (dense, wealthy Manhattan has the highest NO2 and the best health) is noted by the registrant and is the likely reason the exposure-outcome pairs sit at chance.

## (e) Could the test have failed?

Against the registered null the test could have failed in principle. The observed rate is z = 3.4 above the null's 50% (null SD 0.047) and z = 0.2 from the predicted 65% (bootstrap SE 0.047). In practice the test was unlikely to fail. An always-positive rule passes the 60% threshold in 78% of bootstrap resamples, so a literature with no information beyond valence would usually have been confirmed. Against the always-positive benchmark the excess is 1.8 percentage points, or two pairs, and the test has four pairs with which to detect it.

The registered condition is met, so rule 1 gives confirmed. Rule 8 sets a precedent for bridges that a test which cannot separate the hypothesis from its main rival is unsettled however well it matches, and the same reasoning applies here: the test does not separate the literature's signs from the always-positive rule. If the project holds rule 1 to bind for a confirmation-kind claim, the label can stay only with the statement reworded to say that adverse indicators are positively correlated after partialling poverty, and with the stance reduced.

Recommendation: change the verdict to unsettled, because an always-positive rule reaches 64.2% against the literature's 66.1%, exposure-outcome pairs agree at 51.8%, and the registered sign-shuffle null (p = 0.14) does not show that the literature's signs add information.
