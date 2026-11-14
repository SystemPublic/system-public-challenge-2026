# Referee report: heat-trees-surftemp

Verdict recorded: unsettled. Recommendation: keep the verdict.

## (a) Does the verdict follow from the registered conditions?

Yes. The adjusted CD slope is +0.50 F per SD (-0.03 to +1.04), n = 55. The interval includes zero, so neither the support rule (upper limit below zero) nor the refutation rule (lower limit above zero) is met. The NTA secondary and the unregistered borough-effects model both give positive slopes with intervals above zero. The outcome reports them as secondary and does not use them to change the verdict, which is correct.

## (b) Errors in code, units, joins or dates

I re-ran the model from `bridge_cd.csv` and reproduced the estimate. Excluding Manhattan (an unregistered check) gives +0.81 (+0.24 to +1.38). Adding vegetative cover gives +0.35 (-0.26 to +0.97). The area calculation uses an equirectangular projection at 40.7 N, which is adequate at this scale. The CD polygon includes parks and cemeteries, so "street trees per km2 of land" divides by an area that contains large tree-covered spaces with no street trees. This is a definitional problem and the outcome identifies it.

## (c) Is the research comparison fair?

No. The graph row is an NDVI-to-land-surface-temperature finding from Bangladesh, with no value, and it is absent from the Dataverse CSV. NDVI measures vegetation cover; street-tree density per km2 measures street-grid density. The city's vegetative-cover result (-0.62 F per SD, -1.17 to -0.07) is the closer analogue, and it agrees in sign with the research.

## (d) Alternative not addressed

Building height and impervious cover are named but not included as covariates. PLUTO building area per lot area is available by CD and would test the outcome's own explanation.

## (e) Is the settle condition right?

Yes. Canopy from LiDAR, street trees per km of street, and impervious cover as a covariate are the right additions.

## Recommendation

Keep "unsettled". Add the vegetative-cover result to the label as the comparison that matches the research quantity.
