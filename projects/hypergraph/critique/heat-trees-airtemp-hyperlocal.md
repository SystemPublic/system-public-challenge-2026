# Referee report: heat-trees-airtemp-hyperlocal

Verdict recorded: unsettled. Recommendation: keep the verdict.

## (a) Does the verdict follow from the registered conditions?

Yes. The slope is -0.047 C per 10 trees (-0.159 to +0.066). The interval includes zero, so neither condition is met. The estimate lies just outside the predicted range (-0.05 to -0.5), and "miss" is a fair score of the magnitude.

## (b) Errors in code, units, joins or dates

`hyperlocal.py` demeans temperature, tree count and the light-pole indicator within NTA-day and clusters by sensor. This is the registered within estimator. The cluster-robust variance does not count the 5,043 absorbed fixed effects in its small-sample correction; with 86,451 observations and 420 clusters, the effect is negligible. Temperature is converted from F to C before averaging, which is correct.

The effective sample is smaller than 86,451 suggests. The tree count is fixed for each sensor, so the slope is identified from differences between about 420 sensors within 23 NTAs. Clustering by sensor accounts for this.

## (c) Is the research comparison fair?

No graph finding exists. Ziter et al. (2019), cited in the settle condition, measured canopy cover along bicycle transects, not counts of street trees within 50 m of a fixed sensor. The prediction range was the registrant's own.

## (d) Alternative not addressed

Install type enters only as a level shift (+1.26 C for light poles). A sensor mounted on a tree has at least one tree within 50 m by construction and sits in that tree's shade. The tree effect may differ by mount type, and an interaction was not tested. The sensors were also sited in high-vulnerability neighbourhoods, so the result applies to those 23 NTAs, not to the city.

## (e) Is the settle condition right?

Yes. Mobile transects with LiDAR canopy, or sensors sited by design across tree-density strata, would settle it.

## Recommendation

Keep "unsettled".
