# Referee report: commute-fhv-subway-distance

Verdict recorded: contested. Recommendation: keep the verdict, and rewrite the settle condition so that it addresses the registered claim rather than a different one.

## (a) Does the verdict follow from the registered conditions?

Yes. The registered test is the HC3 elasticity of 2024 high-volume pickups per resident on population-weighted distance to the nearest station, adjusted for log mean household income and log jobs per resident, in 174 outer-borough zones. From the derived zone file I obtained the recorded -0.295 (-0.378 to -0.213). The interval lies below zero, so refute_if is met and PRECEDENCE rule 1 gives contested.

The outcome reports one change made after a first run: Census annotation codes (negative income values) had been read as numbers. Setting them to missing moved the estimate from -0.29 to -0.30 and restored 11 zones. This is a data correction, not a choice that favours a result.

## (b) Errors in code, units, joins, denominators or model

I found no error that changes the verdict.

The plan registered log jobs per resident; the code uses log(1 + jobs per resident). With the registered form the estimate is -0.295 (-0.375 to -0.215), so the change has no effect, but it is an unannounced departure from the plan and should be stated in the notes.

The station file has 496 rows (445 complexes), including 21 Staten Island Railway stops, as registered. Several rows per complex do not matter for a nearest-station distance. Tracts are assigned to zones by internal point; zone populations sum to 8.77 million against a 2020 city total of 8.80 million, so about 0.4% of residents fall outside any zone. The pickup query covers all 12 months of 2024, and the HVFHV total (239.5 million) is of the expected order for 2024; I did not check it against a TLC publication. Distances are in feet in EPSG 2263 and converted correctly to kilometres. Straight-line distance ignores rivers and barriers, which matters little for a nearest station.

The denominator mixes populations. Pickups include trips by visitors and workers, while the denominator counts residents. The registration names this, and the jobs covariate addresses only part of it.

## (c) Is the research comparison fair, and is "contested" the right reading?

Under the registration, contested is correct. The registered claim is the association adjusted for income and jobs only. The no-vehicle model was registered as a sensitivity, "reported only", and rule 4 prevents it from deciding the verdict. The sign reversal does not turn a refutation into unsettled.

The reversal is also weaker evidence for substitution than the write-up suggests, for three reasons. First, car ownership is plausibly a mediator: living far from the subway is a reason to own a car. Adjusting for a mediator removes part of the effect of distance, so the conditional elasticity answers a different question from the registered one and does not contradict the total association. Second, the reversal is not stable. With borough fixed effects added it is +0.13 (+0.03 to +0.22), but with Staten Island removed it is +0.09 (-0.03 to +0.20), so it depends on 18 zones in one borough. Third, distance and no-vehicle share are correlated at -0.76, and no-vehicle share correlates with the outcome at 0.68. It is the strongest available proxy for density and urban form, and a coefficient on distance conditional on it rests on a small set of atypical zones.

The research comparison itself needs one correction. The registration's only peer-reviewed source, Barajas and Brown (2021), predicts the negative direction that was found. The positive prediction came from non-peer-reviewed reports, and the graph holds no relevant finding. Since the literature in the registration already disagreed with itself, it should have been registered as a conflict-kind claim. As it stands, "contested" means that the city data contradict the registrant's prediction, not that they contradict the published research. The outcome should say this in one sentence, so that a reader of the verdict table does not count this claim as evidence against the research literature.

## (d) Alternative not addressed

The registration does not name supply. Drivers position themselves where trips are frequent, so waiting times and surge prices are lower in dense zones near the subway and higher at the periphery. Fewer pickups far from stations can then reflect worse service, not lower demand. None of the covariates measures this, and drop-offs (which give the same elasticity, -0.31) do not separate it either, because a rider's choice to use an app in either direction depends on expected waiting time. TLC trip records include request and pickup times for HVFHV trips, so the average wait by zone could be added.

A second, related alternative is that many pickups near stations are first- and last-mile trips from the subway itself, which is a complement mechanism and inflates per-resident pickups near stations.

## (e) Is the settle condition right?

No. The settle condition is written for the substitution hypothesis among car-free households, which is a different claim from the one registered. For the registered claim, the city result is not in doubt: it is negative in every registered sensitivity except the no-vehicle model, including drop-offs, all boroughs, borough fixed effects and yellow and green taxis, and its z is about -7. What would change the reading is evidence that the zone-level association is produced by non-resident or supply-side trips rather than residents' choices. The right settle condition is resident-based trip data (for example HVFHV trip records with evening drop-offs in residential zones, or the Citywide Mobility Survey), analysed for the registered total association. The car-free substitution question belongs in a new registration, as the research_needed list already proposes.

## Recommendation

Keep contested. Add a sentence that the result agrees with the only peer-reviewed source in the registration. State the change in the jobs term. Report the no-vehicle reversal together with its instability when Staten Island is removed. Rewrite the settle condition as in (e).
