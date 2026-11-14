"""Registration of heat-trees-canopy-within-nta. Run once, before any NAIP pixel at a sensor is read:
  python -m analyses.heat.register_canopy
"""
from concord import claims

REC = {
 "id": "heat-trees-canopy-within-nta",
 "kind": "confirmation",
 "statement": "Within the same neighbourhood (NTA) and day, NYC hyperlocal temperature sensors with a larger share of vegetation within 50 m, measured from the 2022 NAIP near-infrared aerial flight, record lower afternoon (12-18 h) air temperature.",
 "edge": {"cause": "vegetation cover within 50 m (tree canopy and other green vegetation)", "effect": "afternoon air temperature at street level"},
 "related": ["heat-trees-airtemp-hyperlocal", "heat-trees-surftemp", "heat-trees-ed-chain"],
 "graph_evidence": [
  {"relationship_id": "(concepts I2CN3brExA tree, lHLIKbfnYp green space, RF7tCwCaa5 vegetation cover)",
   "concepts": ["tree", "green space", "air temperature"], "n_findings": 0, "n_studies": 0, "direction": "0",
   "summary": "From the cached audit of 12 Nov 2026 (data/derived/heat/graph_evidence.json, data/derived/graph_audit/evidence/green-space__heat-stroke.json): the tree concept has no relationships; green space has 14, none with temperature. A live lookup is pending, because the System API key is not on this machine.",
   "pubmed_ids": []},
  {"relationship_id": "hsryqxdFzE|PCdVJWVRyS", "concepts": ["NDVI", "thermodynamic temperature"], "n_findings": 1, "n_studies": 1,
   "direction": "-",
   "summary": "One finding, stored as r = -1.0 between NDVI and land surface temperature (Hasan et al. 2022, one city in Bangladesh). The abstract gives no number and the row is absent from the Dataverse CSV, so it is used for direction only. It concerns surface temperature, not air temperature.",
   "pubmed_ids": [35060045]},
  {"relationship_id": "sSuplgYnDQ|mUxSLRMwIy", "concepts": ["surface temperature", "air temperature"], "n_findings": 2, "n_studies": 2,
   "direction": "+", "summary": "Satellite surface temperature tracks ground air temperature (r about 0.9), from the cached evidence used in heat-trees-airtemp-hyperlocal.", "pubmed_ids": []}
 ],
 "literature": [
  {"citation": "Ziter CD, Pedersen EJ, Kucharik CJ, Turner MG. Scale-dependent interactions between tree canopy cover and impervious surfaces reduce daytime urban heat during summer. PNAS 2019;116:7575-7580.",
   "doi": "10.1073/pnas.1817561116",
   "finding": "Bicycle transects in Madison, Wisconsin, summer 2016. Daytime air temperature fell nonlinearly with canopy cover, most above 40% canopy. Going from none to full canopy corresponded to a mean daytime decrease of 0.7 C for canopy within a 10 m radius, 1.3 C within 30 m and more than 1.5 C within 60 or 90 m. At 90 m, raising canopy from 40% to 80% gave about 1 C. At night the decrease from none to full canopy was 0.3 to 0.5 C. (Numbers read from the results text on PubMed Central, PMC6462107, on 12 Nov 2026.)",
   "data_used": "The authors' own bicycle-mounted air temperature readings, with canopy and impervious cover from land-cover maps.",
   "data_access": "open",
   "data_access_note": "The paper states that all data and code are available through the Environmental Data Initiative. The project's earlier record (data/derived/data_access/literature.json) lists this paper as unknown; the statement was read on PubMed Central on 12 Nov 2026 and the deposit itself was not opened."},
  {"citation": "Alonzo M, Baker ME, Gao Y, Shandas V. Spatial configuration and time of day impact the magnitude of urban tree canopy cooling. Environmental Research Letters 2021;16:084028.",
   "doi": "10.1088/1748-9326/ac12f2",
   "finding": "More than 70,000 car-mounted air temperature readings in Washington, DC on one hot summer day. All tree canopy cooled by 1.8 +/- 0.6 C in the afternoon, 1.7 +/- 0.4 C in the evening and 0.5 +/- 0.3 C before dawn. Canopy over unpaved ground had little afternoon effect below about 40% cover. (Abstract, read 12 Nov 2026.)",
   "data_used": "Vehicle-traverse air temperatures from a volunteer heat-mapping campaign; high-resolution land cover.",
   "data_access": "unknown",
   "data_access_note": "The abstract page gives no data statement; the full text was not read."},
  {"citation": "Shiflett SA, Liang LL, Crum SM, Feyisa GL, Wang J, Jenerette GD. Variation in the urban vegetation, surface temperature, air temperature nexus. Science of the Total Environment 2017;579:495-505.",
   "doi": "10.1016/j.scitotenv.2016.11.069",
   "finding": "About 300 fixed air temperature sensors in greater Los Angeles with airborne NDVI. Vegetation was associated with cooler daytime surface temperature, but with cooler air temperature mainly at night. No effect size was verified and none is used here; the paper is cited as a fixed-sensor study in which the daytime air temperature link was weak.",
   "data_used": "The authors' sensor network; airborne NDVI and surface temperature.",
   "data_access": "unknown",
   "data_access_note": "The DOI was not resolved in this session; the summary comes from the abstract as indexed."}
 ],
 "already_seen": "The project has already tested these sensors. Claim heat-trees-airtemp-hyperlocal (registered and decided 12 Nov 2026) regressed the same afternoon temperatures on the count of live street trees within 50 m and found -0.05 C per 10 trees (-0.16 to +0.07), unsettled; within 100 m, -0.01 (-0.05 to +0.03); light-pole sensors read 1.26 C warmer than tree-mounted sensors. The registrant of this claim has read that registration, outcome, script and referee report, and has seen the sensor table (data/derived/heat/hyperlocal_sensors.csv: coordinates, NTA, mount type, street-tree counts within 50 and 100 m). The afternoon sensor-day temperatures are in data/cache/socrata (queries of 12 Nov 2026, 15:30-15:31); their values were used by the earlier analysis, and this registrant has not opened them. No night-time temperatures have been queried by the project. No NAIP pixel at any sensor has been read: before this registration the registrant read only the NAIP catalogue metadata (tile ids, dates and footprints of the 2022 flight) and ran the exposure code on two Staten Island points, where there are no sensors. The exposure was not chosen after the temperature data in the sense that matters: canopy measured at block level was named as the design that would settle the earlier claim (docs/heat.md and the earlier outcome's settle field), the radii of 50 m and 100 m are the earlier claim's radii, and the vegetation values at the sensors are unknown to the registrant. The earlier result does inform the prior, which is lower than the earlier 0.55.",
 "prediction": {
  "direction": "-",
  "magnitude": "Per 10 percentage points of vegetation share (NDVI above 0.2) within 50 m, afternoon air temperature lower by 0.02 to 0.25 C. The upper end is Ziter's slope above 40% canopy at 90 m (1 C per 40 points); the linear average over the whole canopy range at 30 to 90 m is 0.13 to 0.15 C per 10 points; the lower end allows for the flat part of the curve below 40% cover, where most street sensors are expected to lie, for grass counted as vegetation, and for attenuation from the three-year gap. Secondary: the night-time (00-05 h) slope is negative and smaller in size than the afternoon slope, between 0 and -0.06 C per 10 points.",
  "support_if": "All three hold: (a) the primary slope is negative and the upper limit of its 95% interval (standard errors clustered by sensor) is below 0; (b) the point estimate from the sensors under 19 July 2022 tiles alone is negative; (c) in the model that also includes the vegetation share of the ring 200 to 300 m from the sensor, the point estimate for the 50 m share is negative.",
  "refute_if": "The primary slope is positive and the lower limit of its 95% interval is above 0.",
  "otherwise": "Unsettled. If the primary interval lies wholly between -0.02 and 0, or wholly above -0.02 without excluding 0, the outcome says that the literature's range is excluded at this exposure range, and the verdict is still unsettled. The verdict is no_test if fewer than 300 sensors have imagery for at least 95% of the 50 m disc, or if the standard deviation of the 50 m share within NTA and flight date is below 2 percentage points."
 },
 "plan": "Sensors and temperature: Hyperlocal Temperature Monitoring (NYC Open Data qdq3-9eqn, data.cityofnewyork.us), summers 2018 and 2019. Sensor-day mean of airtemp over hours 12 to 18, by SoQL (group by sensor_id, day), keeping sensor-days with at least 5 of the 7 hours, converted to C; this is the earlier claim's query and is read from the cache. Sensor position, NTA and mount type from the same dataset; a sensor listed at two positions keeps the one with the most readings. Exposure: USDA NAIP, 2022 New York State flight only (0.6 m, four bands), from the Microsoft Planetary Computer STAC collection 'naip'; New Jersey tiles of 10 July 2022 that overlap western Manhattan and the Bronx are not used. The catalogue shows tiles dated 19 July 2022 west of about longitude -73.875 and 15 September 2022 east of it, so the September tiles cover Queens and also the eastern Bronx and eastern Brooklyn; where the two overlap the 19 July tile is used. For each sensor, NDVI = (NIR - red)/(NIR + red) on a 0.6 m grid; the vegetation share is the share of imaged pixels with NDVI above 0.2 within 50 m (primary) and 100 m of the sensor; the mean NDVI in the same discs; and the vegetation share of the ring 200 to 300 m away (placebo). Each sensor's flight date is the date of the tile at its position. Sensors with imagery for less than 95% of the 50 m disc are dropped. Model: OLS of sensor-day afternoon temperature on the 50 m vegetation share (scaled to 10 percentage points) and a light-pole indicator, with fixed effects for NTA by flight date by day, so that no comparison crosses neighbourhoods, days or flight dates; cells with one sensor are dropped; standard errors clustered by sensor. The unit of identification is the sensor (about 420 in 23 NTAs). Pre-specified sensitivity checks, none of which decides the verdict except as written in support_if: S1 share within 100 m; S2 mean NDVI within 50 m and 100 m (per 0.1) in place of the thresholded share; S3 sensors under 19 July tiles only, and under 15 September tiles only; S4 dropping sensors whose 100 m disc mixes two dates or lacks 5% or more of its pixels; S5 street-tree mounts and light-pole mounts separately (the referee of the earlier claim noted that a tree-mounted sensor sits under canopy by construction); S6 days when the Central Park maximum (GHCN-Daily USW00094728) was 30 C or more; S7 adding the 2015 street-tree count within 50 m from the earlier claim. Secondary outcome: mean temperature over hours 0 to 5 (at least 5 of 6 hours), same model. Placebo: the ring 200 to 300 m share in place of the 50 m share, and jointly with it. Ziter's largest scale was 90 m, so a ring coefficient as large as the local one would point to block-type or neighbourhood gradients, not to the vegetation near the sensor. Descriptive only: coefficients for bins of the 50 m share (10-20, 20-30, 30-40, 40% and over, against under 10%), the correlation of the share with the street-tree count, and the share by mount type. Code: analyses/heat/canopy_naip.py, written before registration and run on two Staten Island points only.",
 "limits_stated_in_advance": [
  "The imagery is from summer 2022 and the temperatures from summers 2018 and 2019. Trees planted, grown or removed in the three to four years between add error to the exposure, which biases the slope toward zero. The 2019 NAIP flight is not used because its near-infrared band is shifted and the fixed threshold classes roofs as vegetation (concordance-kit aerial-naip notes).",
  "NAIP is 8-bit digital numbers, not reflectance. The 0.2 threshold is a convention, not calibrated; it is applied within one flight year, and the two dates are never compared with each other.",
  "NDVI counts lawns and shrubs as well as tree canopy, and shadowed canopy can fall below the threshold. Ziter measured canopy.",
  "Sensors were sited in high heat-vulnerability neighbourhoods on trees and light poles, not at random; the result applies to those 23 NTAs."
 ],
 "alternatives": [
  "Mount type: a sensor in a street tree is shaded by that tree and has vegetation within 50 m by construction (light-pole indicator; S5)",
  "Block type: greener blocks are residential side streets with less traffic, lower buildings and less waste heat (ring placebo; within-NTA comparison)",
  "Exposure error from the 2018-2019 to 2022 gap and from NDVI in shadow (attenuation; cannot be separated, stated as a limit)",
  "Flight-date radiometry: the same threshold marks different things on 19 July and 15 September (flight date in the fixed effect; S3)",
  "Sea-breeze or elevation gradients inside an NTA that happen to align with vegetation (not separated)"
 ],
 "prior": 0.3,
 "prior_note": "Probability of 'confirmed'. The street-tree count gave a weak negative slope with an interval including zero on the same sensors, the exposure range probably lies mostly below Ziter's 40% threshold, and the imagery is three years late. Probability of 'contested' 0.03; the rest unsettled.",
 "registrant": "Claude (agent), for Jeff Vernon",
}

if __name__ == "__main__":
    print(claims.register(REC))
