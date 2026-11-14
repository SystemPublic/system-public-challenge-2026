# Referee report: heat-trees-canopy-within-nta

Verdict recorded: confirmed. Referee script: `referee-heat-trees-canopy-within-nta/h.py` in the session scratch folder (not in the repository). The registrants' documents in docs/ were not read.

## (a) Does the verdict follow from the registered conditions?

Yes. The registration required three things: the primary slope negative with an upper limit below 0; a negative point estimate under the 19 July tiles alone; and a negative point estimate for the 50 m share when the 200-300 m ring is also in the model. The values are -0.20 (-0.25 to -0.15), -0.21 and -0.17. Rule 1 of PRECEDENCE then gives confirmed, and it does so whatever the placebo shows, because condition (c) was written as a sign condition on the local coefficient and not as a condition on the ring. None of the no_test conditions applies (423 sensors with full imagery; within-NTA standard deviation 12.7 points). No measure chosen after the data decides the verdict; the bins and the 5 m check are labelled descriptive or unregistered.

The registered statement is an association ("sensors with a larger share ... record lower temperature"). The verdict confirms that association. The registration itself said that a ring coefficient as large as the local one "would point to block-type or neighbourhood gradients, not to the vegetation near the sensor", and that is what was found, so the verdict should not be read as support for the causal edge recorded in the registration's `edge` field. The outcome's settle field says this.

The registration was committed at 20:17:43 on 12 November 2026 and the branch prereg/heat-trees-canopy-within-nta exists on GitHub with a commit at 20:17:51. The 423 per-sensor NDVI files in ~/opt/nyc-concordance/naip_sensors were written between 20:18:02 and 20:23:20, after registration, which supports the statement that no pixel at a sensor had been read. The afternoon temperatures were fetched at 15:31 and used by the earlier claim; the registration discloses this. The night query ran at 20:23:39 and the outcome was written at 20:25:18. The script canopy_naip.py was not committed with the registration and its file time is 20:24, so "written before registration" cannot be checked from git; the code I read follows the plan.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error. Temperatures are converted from Fahrenheit (raw range 53 to 110 F). I recomputed the 50 m share from the cached NDVI arrays and it matches the sensor table to within 0.9 percentage points. From the cached temperatures and the sensor table I reproduce the deciding number exactly: -0.201 (-0.247 to -0.154), 86,451 sensor-days, 420 sensors, 23 NTAs.

One feature of the data should be recorded. All 87,500 sensor-days have 7 of 7 afternoon hours, and each year has exactly 43,750 rows (350 sensors by 125 days). The published file is a balanced panel, so it was gap-filled or cleaned before publication, and the registered filter of 5 of 7 hours removed nothing.

Variants the registrant did not run:

| Variant | C per 10 points within 50 m | 95% interval |
|---|---|---|
| Registered model | -0.201 | -0.247 to -0.154 |
| Standard errors clustered by NTA (23 clusters) | -0.201 | -0.261 to -0.141 |
| 2018 only | -0.140 | -0.199 to -0.082 |
| 2019 only | -0.236 | -0.289 to -0.183 |
| Sensors below 40% share | -0.152 | -0.232 to -0.072 |
| NDVI threshold 0.3 | -0.238 | -0.290 to -0.185 |
| NDVI threshold 0.1 | -0.178 | -0.221 to -0.136 |
| Share in the 5-50 m annulus (mount tree excluded) | -0.200 | -0.246 to -0.153 |
| Sensor means, with a separate north-south and east-west gradient in each NTA | -0.144 | -0.191 to -0.097 |
| Leave one NTA out (range of 23 estimates) | -0.176 to -0.213 | |

The primary result survives all of these. The slope below 40% share is negative, which goes against the registration's expectation of a flat part of the curve there.

I also fitted the distance-decay model that the outcome names as a way to settle the claim, using rings from the cached arrays, all in one model:

| Ring | C per 10 points | 95% interval |
|---|---|---|
| 0-25 m | -0.165 | -0.214 to -0.115 |
| 25-50 m | +0.021 | -0.047 to +0.089 |
| 50-100 m | -0.050 | -0.147 to +0.048 |
| 100-200 m | -0.023 | -0.160 to +0.113 |
| 200-300 m | -0.212 | -0.332 to -0.093 |

The association has two parts: vegetation within 25 m of the sensor, and vegetation 200 to 300 m away. Nothing is attributable to the 25 to 200 m range once those two are in the model. The ring widths were chosen by me after the data were seen, so this is exploratory.

## (c) Is the comparison with the literature fair?

Partly. Ziter et al. measured tree canopy from land-cover maps and air temperature from a moving bicycle; this claim uses a vegetation share from uncalibrated NDVI that includes grass, three to four years after the temperatures, and fixed sensors of which 73% hang in a tree. The registration lists these differences. The registered range of -0.02 to -0.25 spans a factor of 12 and was built to allow for them, so "inside the registered range" is a weak statement about size. On like-for-like radius the city slope is larger than Ziter's: -0.19 per 10 points for the 0-25 m disc alone against Ziter's 0.07 (10 m) to 0.13 (30 m).

The claim has no graph finding on vegetation and air temperature, as the outcome states. I checked the one graph row cited for direction (PMID 35060045, Hasan et al. 2022) against its PubMed abstract. The abstract reports a "strong significant negative correlation between LST and NDVI" in Mymensingh from Landsat images and gives no coefficient. The stored r = -1.0 is therefore not a published number, and the finding concerns land surface temperature. The registration says both things and uses the row for direction only, which is correct.

## (d) Alternative not addressed

Block type is named and the ring placebo was meant to separate it; the placebo failed, and the outcome reports that. What is not addressed is shade on the sensor itself, as distinct from cooler air. A sensor housing in afternoon sun reads above air temperature, and canopy within 25 m is what shades it. The pattern in the ring model (all of the local association inside 25 m, none from 25 to 200 m) fits shading of the instrument at least as well as it fits cooling of the air, and the light-pole indicator (+1.17 C) shows that exposure of the mount matters at this size. The equal slope at light-pole mounts (-0.21) rules out the mount's own tree as the explanation but not shade from neighbouring crowns or from buildings. Building height and street orientation are not in the model. Night-time readings are free of solar loading, and the night slope is a third of the afternoon one (-0.07), which is the size that both readings predict.

The slope differs between years (-0.14 in 2018, -0.24 in 2019) with largely different sensors in the two years. The outcome does not report this.

## (e) Could the test have failed?

The test could have failed. The registrant's prior was 0.30, the earlier street-tree count on the same sensors gave an interval including 0, and with a standard error of 0.024 any true slope weaker than about -0.05 would have left the verdict unsettled. Conditions (b) and (c) were sign conditions and added little. The estimate is z = 8.5 from no effect (6.6 with NTA clustering) and z = 2.8 from the midpoint of the registered range (-0.135), inside the range. This is a confirmation test, not an endpoint or transfer test.

Recommendation: keep. The registered conditions are met, the number reproduces and survives the variants above; the dashboard label should say that the confirmed claim is the association, since the ring at 200-300 m stays as large as the local share in every model.
