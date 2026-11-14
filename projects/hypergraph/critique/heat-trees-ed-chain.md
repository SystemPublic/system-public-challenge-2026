# Referee report: heat-trees-ed-chain

Verdict recorded: contested. Recommendation: keep the verdict as the registered outcome, but correct the dashboard stance and state the precedence rule that produced it.

## (a) Does the verdict follow from the registered conditions?

Yes, by the registered refutation clause: "either link contested". Link heat-surftemp-ed is contested, so the chain is contested. The composed estimate itself (-3.7%, -10.3 to +1.3) is in the predicted direction and its interval includes zero. Under the generic definition in concord/claims.py, contested requires an opposite-signed interval that excludes zero, which this estimate does not meet. The registration was specific, so it governs here. But mob-crz-air-nyccas applied the opposite precedence (see that report), and the project should choose one rule.

The stored stance (+0.55, interval -0.22 to +0.94) is computed from the composed estimate. On the dashboard, a "contested" verdict will therefore sit on the agreeing side of the strip. That is misleading.

## (b) Errors in code, units, joins or dates

I re-ran the CD regressions from `bridge_cd.csv`. The point estimates match: a = +0.43 F per SD, b = -8.8% per F. The bootstrap is correct in form. Three data choices matter:

- `ehdp()` takes the largest TimePeriodID, which gives surface temperature 2018, vegetative cover 2017, ED rate 2018-22 and hospitalization 2013-22. The ED period includes the COVID years.
- Covariates are unweighted means of NTA values within a CD. CDs with two NTAs get a two-point average.
- Tree density uses total CD polygon area, which includes park land.

None of these is a coding error, but each adds measurement error to a 54-unit regression.

## (c) Is the research comparison fair?

There is no graph path. The research on trees and heat illness is about canopy, not street-tree counts per km2. The outcome's own heat-trees-surftemp report shows that street-tree density tracks street-grid density. The chain therefore does not test the quantity the research describes.

## (d) Alternative not addressed

The total association of trees with ED rates (-19.9% per SD) is strong and is left unexplained. Street-tree density is high in dense, transit-rich districts with short travel to EDs and a different age and occupation mix. That alternative, urban form as a common cause, is not named among the confounders.

## (e) Is the settle condition right?

Yes. Within-area designs (case-crossover by ZCTA, planting-timing instruments) are the right ones. The settle condition should add a canopy measure (LiDAR) in place of street-tree counts.

## Recommendation

Keep "contested" as the registered result. Recompute or suppress the stance for chains whose verdict is inherited from a link, and add the precedence rule to concord/claims.py.
