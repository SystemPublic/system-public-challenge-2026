# Referee report: mob-asthma-pollution

Verdict recorded: unsettled. Recommendation: keep the verdict.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required a poverty-adjusted NO2 rate ratio above 1 with an interval above 1. The estimate is 1.22 (0.81-1.85). Refutation required a ratio at or below 1 with an interval excluding the research value. Neither condition is met. The outcome scores the registrant's mechanism prediction (strong unadjusted gradient that shrinks on adjustment) as a miss, which is correct.

## (b) Errors in code, units, joins or dates

`asthma_pollution.py` uses the registered years (2017-19), the age 5-17 rate, NYCCAS NO2 and PM2.5 for the same years, and poverty for 2015-19. It correctly avoids the PM2.5-attributable indicator. The NO2 conversion (1.88 ug/m3 per ppb) is standard. The model is unweighted OLS of the log rate. A Poisson or negative binomial model with population offsets would weight UHFs by their counts; with 42 units and rates per 10,000, this would change the interval more than the estimate.

## (c) Is the research comparison fair?

Not fully. Khreis et al. (2017) pooled studies of asthma incidence (new onset) in children. The city outcome is the ED visit rate, which mixes prevalence, exacerbation and care-seeking. The two are different quantities. The outcome draws the research slope through the city mean as if they were the same. The comparison should be labelled as indicative only.

## (d) Alternative not addressed

NO2 and PM2.5 are highest in midtown and lower Manhattan, where daytime population far exceeds residents. NYCCAS concentrations describe where pollution is, and ED rates are counted by home address; children in high-poverty UHFs may be exposed at school or on routes outside their home UHF. Housing conditions (pests, mould) are named but not measured; EHDP has housing-maintenance indicators by UHF.

## (e) Is the settle condition right?

Yes. A within-neighbourhood time-series or case-crossover design is the right test, and the outcome names it.

## Recommendation

Keep "unsettled". Label the research comparison as incidence versus ED visits.
