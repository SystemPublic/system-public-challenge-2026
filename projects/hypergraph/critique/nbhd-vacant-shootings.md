# Referee report: nbhd-vacant-shootings

Verdict recorded: confirmed. Recommendation: keep the verdict. The outcome should report the within-neighbourhood result given below and should drop the statement that the NYC estimate equals the Philadelphia estimate.

## (a) Does the verdict follow from the registered conditions?

The verdict follows. The support condition was a 95% interval for the adjusted IRR per quintile step with a lower limit above 1.00. The estimate is 1.172 (1.121-1.224), and I reproduced it from `data/derived/neighbourhood/vacant_shootings_tracts.csv`. The registration hash matches its contents, and the registration time (15:24:16) precedes every data fetch recorded in the outcome. The verdict was not moved.

The registered statement also says the association is "weaker than the Philadelphia estimates". The support condition does not test that clause, so it does not affect the verdict. The outcome scores it as a magnitude miss, which is correct.

## (b) Errors in code, units, joins or geography

I found no error that changes the result. The 5ucz-vwe8 cache does hold longitudes in the `latitude` column, as the outcome says, and the script swaps them. Distinct incidents per year match the archived 833y-fsy8 table (7,043 against 7,042). Of the 2,208 tracts, 278 have no vacant land. All of these fall in the lowest quintile, so the arbitrary tie-breaking in `rank(method="first")` does not move tracts between quintiles. Poverty is a proportion, so `pov10` is correctly per 10 percentage points.

Three points of specification need comment.

1. The quintile is entered as a linear term, but the dose-response is not linear. With quintile as a factor, the adjusted IRRs relative to the lowest quintile are 1.30, 1.41, 1.89 and 1.82. The step is concentrated between the second and fourth quintiles. In the high-poverty tercile the rate is flat across the three lowest quintiles (2.1, 2.1, 2.0 per 10,000 per year).
2. HC1 errors ignore spatial dependence between neighbouring tracts. With errors clustered on the 201 NTAs, the interval widens to 1.10-1.25. The verdict is unchanged.
3. The exposure is MapPLUTO 26v2 (2026), but the outcome period is 2019-2024. Lots built on during 2019-2025 are counted as not vacant, and lots cleared after 2024 are counted as vacant. The plan did not address this, and an archived PLUTO version from about 2021 would be closer to the outcome period.

The most important check is not in the outcome. With NTA fixed effects in place of borough fixed effects, the IRR per quintile step is 0.98 (0.94-1.01). The association is between neighbourhoods. Within a neighbourhood, tracts with more vacant land do not have more shootings. The registered model used borough effects, so this does not change the verdict. It does mean the result is consistent with neighbourhood-level confounding.

## (c) Is the research comparison fair?

The comparison of magnitude is not fair. Branas, Rubin and Guo (2013) report aggravated assault per category shift of vacant property counts across Philadelphia block groups. The NYC estimate is shootings per quintile step of vacant share of lot area across census tracts. The outcome, the event, the exposure scale and the unit all differ. That 1.17 is close to 1.18 is a coincidence of two unrelated scales. The outcome's sentence that the NYC estimate "equals the Philadelphia between-unit estimate" should be removed, and so should the comparison in the write-up. The comparison of direction is fair.

## (d) Alternative not addressed

The registration names poverty and disinvestment as confounders, but the adjustment covers poverty only. The NTA fixed-effects result shows that some neighbourhood-level factor varies with vacant land and with shootings, and the tract covariates do not capture it. Candidates include the history of public housing siting, the location of gang territories and policing intensity. Adding the non-Hispanic white share reduced the IRR to 1.13, and adding a squared poverty term with clustered errors gave 1.13 (1.07-1.19). Neither model removes between-neighbourhood confounding.

## (e) Is the settle condition right?

The condition is mostly right. A lot-level before-and-after design and the split between lots staged for construction and long-vacant lots are the right next tests. The third item, refitting with 2010-2014 shootings, does not test reverse causation unless vacancy is also measured later than those shootings. The settle condition should require a vacancy measure from an archived PLUTO version that matches the outcome period. It should also report the within-NTA estimate, because that estimate is what a causal reading would have to explain.

## Recommendation

Keep "confirmed". Add the NTA fixed-effects estimate (0.98, 0.94-1.01) and the NTA-clustered interval to the notes. Remove the claim that the NYC and Philadelphia estimates are equal.
