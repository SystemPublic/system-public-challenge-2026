# Referee report: nbhd-noise311-exposure

Verdict recorded: unsettled. Recommendation: keep the verdict.

## (a) Does the verdict follow from the registered conditions?

The verdict follows. Support required a bootstrap 95% interval above zero for the rent-change coefficient minus the modelled-noise coefficient. Refutation required an interval below zero. The estimate is -0.034 (-0.091 to 0.024), which spans zero. I reproduced the point estimate and the coefficients from `noise311_tracts.csv`. The registration hash is intact.

The outcome reports the white-share contrast, 0.10 (0.04 to 0.15), as secondary and does not use it for the verdict. That is correct. The statement names white-share change, but the support rule names only rent change.

## (b) Errors in code, units, joins or geography

I found no error that changes the verdict. I checked the tile classification against the cached PNG tiles. Every opaque pixel matches one of the seven legend colours exactly, so the colour lookup loses nothing. Rents are nominal, but the log difference is standardised, so a common inflation factor has no effect.

The fitted model includes the white-share change and liquor licences alongside rent change. The plan lists "neighbourhood change" and nightlife as predictors, so this follows the plan. I refitted without the white-share change, and then with only the plan's controls (density, poverty, borough). The contrast stayed between -0.04 and -0.03, and its bootstrap interval still spanned zero in the first case (-0.089 to 0.015). The two change measures are nearly uncorrelated (Spearman 0.09), so they do not split one effect. With errors clustered on NTA, the modelled-noise coefficient is 0.037 (-0.026 to 0.101).

The exposure is a tract mean over all land, including parks and highway rights-of-way, rather than a mean over residential lots. The energy-mean version behaves very differently from the class mean (Spearman with residential complaints 0.07 against 0.22). This shows that the exposure measure depends heavily on how loud road corridors are weighted. A population-weighted or residential-lot mean would be closer to what residents hear.

## (c) Is the research comparison fair?

There is no research quantity to compare. The graph effect shown (hypertension OR 1.11 per 10 dB) is on a different construct and is shown only to name the research exposure scale. The claim is a measurement-validity claim, and the registered contrast does not measure validity directly. A difference between two standardised regression coefficients says which predictor explains more variance in complaints. It does not say whether complaints track exposure.

## (d) Alternative not addressed

Housing form is not addressed. Residential noise complaints come mostly from neighbours through shared walls and floors. Their rate per resident should depend on the share of residents in multi-unit buildings, on building age and on construction type. These vary across tracts independently of traffic noise and of rent change. Density stands in for this only partly. Repeat callers are a second omission. A small number of addresses can supply a large share of a tract's complaints, and the count-by-location aggregation in `fetch311.py` would show this, but the outcome does not report it.

## (e) Is the settle condition right?

The condition is partly right. Measured sound levels are the right reference for street, vehicle and commercial complaints. They are the wrong reference for residential complaints, which concern indoor noise from neighbours that street sensors such as SONYC do not record. The settle condition should separate the two. For street and vehicle complaints, compare complaints with outdoor levels at sensor sites. For residential complaints, use indoor measurements or a survey of noise heard at home, such as the NYC Community Health Survey item on noise, against complaint rates. The proposed reporting-propensity model is the right way to test the neighbourhood-change part of the claim.

## Recommendation

Keep "unsettled". Report how concentrated complaints are among repeat addresses, and add a housing-form covariate (share of units in buildings with five or more units) in any re-registration.
