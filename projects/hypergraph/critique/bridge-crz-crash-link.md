# Referee report: bridge-crz-crash-link

Verdict recorded: no_test. Recommendation: keep the verdict. Change `prediction_scored` from "partial" to "not scored", and remove the statement that the endpoint "was compatible with it".

## (a) Was the link fixed before the endpoint was queried?

Yes. The link's distributions (speed exponent N(1.2, 0.5), fatal exponent N(2.6, 0.8), volume elasticity N(0.9, 0.2), each truncated at zero) are written into `compose.py`, committed in `a4b6f1e` at 16:04:49 on 12 November. The registration followed at 16:04:49 (`04c828f`). The zone crash data were first fetched at 16:05:32. The only earlier crash query (`h9gi-nx95-298b…`, 15:31:58) was citywide and had no zone split.

## (b) Errors in the link

The exponents are taken correctly from Elvik (2009) for urban injury and fatal accidents. Three points weaken the link as stated.

The graph evidence does not support the link it is attached to. The three graph findings concern injury severity or injury odds given exposure (child pedestrians on higher-speed roads, moped riders above 20 mph, cyclists where traffic is under 30 km/h). The link is an exponent on crash frequency against mean network speed. Severity findings bear on the fatal exponent, if on anything, not on the injury-crash exponent.

The volume elasticity of 0.9 has no source. The registration cites "safety performance functions" but the literature list contains none. The value and its standard deviation are assumptions and should be labelled as such in the outcome's `graph_effect`.

The registrant's own alternatives argue against applying the power model here. Elvik (2013) finds lower effective exponents at low initial speeds, and the zone's speeds are 8 to 9 mph. A standard deviation of 0.5 around 1.2 does not reflect a possible exponent near zero at these speeds. The prior on the exponent is centred on a value the registrant thought likely to be too high.

## (c) Independence

Not applicable in the usual sense. The link has no city data. Its values enter only the composition.

## (d) Is the test informative?

The link is not tested by the endpoint in any useful sense. The endpoint constrains only the sum E·log(1+dS) + b·log(1+dV). With dS about +5.6 percent on the log scale and dV about -7.9 percent, every pair (E, b) with E/b near 1.4 composes to the same prediction, and so does any pair of small values. An endpoint near zero is compatible with E = 0 and b = 0. The outcome's note says this correctly, but `prediction_scored` then calls the link "compatible", which a reader will take as support. The link was not scored, and the field should say so.

## (e) Alternative not addressed

At congested speeds, crash frequency may depend on conflict counts (turning movements, double parking, mid-block crossing) more than on mean speed. The registration names this but the composition gives it no weight. A component of the prior with E near zero would represent it.

## Recommendation

Keep no_test. Set `prediction_scored` to "not scored: the endpoint does not identify the link's parameters". Label the volume elasticity as an assumption in `graph_effect`. The research need recorded in the outcome (segment-level speeds and crashes) is the right one.
