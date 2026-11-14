# Referee report: nbhd-rodents-asthma

Verdict recorded: confirmed. Recommendation: keep the verdict under the registered rule, but the outcome must state that the result does not survive adjustment for ethnoracial composition or the removal of one neighbourhood. If the verdict is meant to support the bridge from household allergen to neighbourhood ED rates, the claim needs re-analysis with a housing-problems control that excludes rodents and with race and ethnicity adjusted.

## (a) Does the verdict follow from the registered conditions?

The verdict follows. Support required a 95% interval above zero for the adjusted coefficient. The estimate is 0.467 (0.063-0.872) with HC3 errors, and I reproduced it from `rodents_asthma_uhf.csv`. A bootstrap over the 42 neighbourhoods gives 0.13-0.87. The registration hash is intact, and it names the model, the controls and the measure IDs used. The verdict was not moved. The registrant expected "unsettled" and reported "confirmed" when the data gave that result.

## (b) Errors in code, units, joins or geography

The control variable contains the exposure. EHDP measure 1248, "Housing problems, percent", is defined as renter households reporting any health-related problem, and the list includes "cockroaches, mice or rats in the building". The alternative named in the plan, measure 86, also includes rodent infestation. This is why the rodent measure and the control correlate at 0.90. Adjusting for a composite that contains the exposure does not isolate rodents from other housing problems. The coefficient then compares rodents with a mixture of rodents, cockroaches and other defects among renters only. The adjusted estimate is therefore not interpretable as "net of housing problems", as the statement claims.

The time periods are aligned (2017 for the NYCHVS measures and the ED rate, 2013-2017 for poverty). NYCHVS is sampled by sub-borough area, so the UHF42 values carry sampling error that the model ignores. This error biases toward zero and does not explain a positive result.

## (c) Is the research comparison fair?

The comparison is not fair, and the outcome partly says so. The graph effect is an odds ratio for health care use per tenfold bed mouse allergen among mouse-sensitised children. The city effect is a change in a log neighbourhood rate per SD of the share of households reporting mice or rats anywhere in the building. The unit, the exposure, the population and the scale all differ. The direction comparison is fair. A comparison of magnitude is not possible.

## (d) Alternative not addressed

Ethnoracial composition is listed as not handled, and it matters. I aggregated the 2018-2022 ACS non-Hispanic white share from tracts to UHF42 by representative point and added it to the registered model. The rodent coefficient fell to 0.35 (-0.09 to 0.78). Race stands in here for differences in ED use, primary-care access and housing stock that poverty does not capture. Removing Sunset Park alone also moves the interval to -0.06 to 0.90. With 42 units and four correlated predictors, the confirmation rests on one or two neighbourhoods and one omitted covariate.

Borough fixed effects do not remove the association (0.48, 0.11-0.86), so the result is not only a Bronx effect.

## (e) Is the settle condition right?

The condition is right. Household-level data linking reported rodents or measured allergen to ED use, and a within-neighbourhood design around pest management in NYCHA, are the right tests. Item (2), adding race, smoking, PM2.5 and primary-care access to the neighbourhood model, should be done now, because the race adjustment alone already removes the result. Item (2) should also replace measure 1248 with a housing-problems measure that excludes pests, or build one from NYCHVS microdata.

## Recommendation

Keep "confirmed" as the registered result. Add to the notes the race-adjusted estimate (0.35, -0.09 to 0.78), the Sunset Park leave-one-out interval, and the fact that measure 1248 includes mice, rats and cockroaches. The stance should be lowered to match. If the project wants a verdict on whether rodents explain neighbourhood asthma ED rates beyond housing quality, register a re-analysis with a pest-free housing control and race adjusted.
