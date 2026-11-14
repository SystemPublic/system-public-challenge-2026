"""Outcome of heat-trees-canopy-within-nta, written from data/derived/heat/canopy_naip_results.json.
  python -m analyses.heat.outcome_canopy
"""
import json

from analyses.heat.common import DER
from concord import claims

r = json.loads((DER / "canopy_naip_results.json").read_text())
m = r["models"]


def c(k, v):
    x = m[k]["coef"][v]
    return x["estimate"], x["lo"], x["hi"]


def t(k, v):
    return "%.2f (%.2f to %.2f)" % c(k, v)


p = c("primary_veg50", "v50")
e = r["exposure"]
OUT = {
 "id": "heat-trees-canopy-within-nta",
 "verdict": "confirmed",
 "city_effect": {"label": "Sensor afternoon (12-18 h) air temperature on vegetation share (NAIP 2022, NDVI > 0.2) within 50 m; NTA by flight date by day fixed effects, light-pole indicator, SE clustered by sensor",
                 "estimate": p[0], "lo": p[1], "hi": p[2], "scale": "C per 10 percentage points of vegetation share", "null": 0,
                 "n": m["primary_veg50"]["n"], "sensors": m["primary_veg50"]["sensors"]},
 "graph_effect": {"label": "No graph finding on vegetation and air temperature. Literature (Ziter et al. 2019, not in the graph): more than 1.5 C from none to full canopy within 60-90 m, about 0.15 C per 10 points on average and 0.25 C per 10 points above 40% canopy",
                  "estimate": -0.15, "lo": -0.25, "hi": -0.02, "scale": "C per 10 percentage points (registered range, not an interval)", "null": 0},
 "sources": [{**x, "data_access": x.get("data_access", "open")} for x in r["sources"]] + [
     {"kind": "sysgraph", "api": "System Public Graph v1.0", "dataset": "Dataverse v2.1, doi:10.7910/DVN/7V6JDO",
      "file": "data/derived/heat/graph_evidence.json", "note": "cached evidence of 12 Nov 2026; live lookup pending (no API key on this machine)", "data_access": "open"},
     {"kind": "derived", "file": "data/derived/heat/hyperlocal_sensors.csv", "note": "street-tree counts within 50 m from claim heat-trees-airtemp-hyperlocal (2015 Street Tree Census uvpi-gqnh), used in S7 only", "data_access": "open"}],
 "prediction_scored": "hit: %s C per 10 percentage points within 50 m, inside the registered range of -0.02 to -0.25. The three support conditions hold: the upper limit is below 0; the 19 July tiles alone give %s; with the ring share in the model the 50 m slope is %s. The secondary prediction is a partial hit: the night slope is negative and smaller than the afternoon slope, %s, but slightly larger in size than the registered 0 to -0.06." % (
     t("primary_veg50", "v50"), t("s3_july19_only", "v50"), t("placebo_ring_joint", "v50"), t("secondary_night_veg50", "v50")),
 "placebo": {"label": "vegetation share of the ring 200-300 m from the sensor", "alone": dict(zip(("estimate", "lo", "hi"), c("placebo_ring_alone", "vring"))),
             "joint_ring": dict(zip(("estimate", "lo", "hi"), c("placebo_ring_joint", "vring"))),
             "joint_local": dict(zip(("estimate", "lo", "hi"), c("placebo_ring_joint", "v50"))),
             "result": "not null: the ring coefficient is as large as the local one"},
 "sensitivity": {k: {v: dict(zip(("estimate", "lo", "hi"), c(k, v))) for v in m[k]["coef"] if v != "lp"} | {"n": m[k]["n"], "sensors": m[k]["sensors"]}
                 for k in m if k.startswith("s") },
 "settle": "The verdict follows the registered conditions, but the placebo was not null. The vegetation share 200 to 300 m away predicts sensor temperature as strongly as the share within 50 m, so the data show that greener parts of a neighbourhood are cooler in the afternoon and do not show that the vegetation within 50 m is the cause. Three things would separate these: canopy and impervious cover from the city's 2017 LiDAR land cover (canopy apart from grass, close in time to the sensors), with building height and street width held fixed; a distance-decay analysis of the NDVI already cached, by rings from 0 to 500 m; and a change design, in which sensors (or the 2022 and later heat-mapping traverses) are compared before and after planting or removal recorded in Forestry Tree Points (hn5i-inap).",
 "research_needed": [
  {"question": "At what distance does vegetation stop predicting street-level afternoon air temperature in NYC, and is the 50 m association causal?",
   "data": "2017 LiDAR land cover (6 in), building footprints and heights, the cached NAIP NDVI rings, Hyperlocal Temperature Monitoring",
   "design": "Ring-by-ring model within NTA and day with building height and impervious cover as covariates; pre-register the ring widths", "priority": "high"},
  {"question": "Does the count of street trees measure canopy? Here the count within 50 m and the NAIP vegetation share within 50 m have a correlation of %.2f across sensors." % e["corr_veg50_trees50"],
   "data": "2015 Street Tree Census with trunk diameter; LiDAR canopy", "design": "Compare tree count, summed basal area and canopy share around the same points", "priority": "medium"},
  {"question": "The System graph has no finding on urban vegetation and air temperature.", "data": "Ziter et al. 2019; Alonzo et al. 2021; Shiflett et al. 2017",
   "design": "Add the urban microclimate literature to the graph", "priority": "medium"}],
 "figures": ["figures/heat/heat_canopy_naip.png"],
 "notes": "%d sensors with imagery (all had 100%% of the 50 m disc), %d sensors and %d sensor-days in %d NTA-by-day cells with at least two sensors; %d sensors lie under 19 July 2022 tiles and %d under 15 September tiles; no disc mixes dates. The 50 m vegetation share has mean %.1f%%, SD %.1f points (%.1f within NTA and flight date), and %.0f%% of sensors are at 40%% or more. Street-tree mounts average %.1f%% and light-pole mounts %.1f%%. Sensitivity: 100 m share %s; mean NDVI within 50 m %s C per 0.1; 15 September tiles only %s; street-tree mounts %s; light-pole mounts %s; days with Central Park maximum at or above 30 C %s; with the street-tree count in the model %s, and the count itself %s C per 10 trees. Placebo: ring share alone %s; jointly, ring %s and 50 m share %s. Descriptive bins against under 10%%: 10-20%% %s, 20-30%% %s, 30-40%% %s, 40%% and over %s C. Unregistered check of georeferencing: within 5 m of the sensor the vegetation share is 0.59 at street-tree mounts and 0.11 at light-pole mounts. Limits stated in the registration apply: imagery three to four years after the temperatures, uncalibrated NDVI, grass counted with canopy, sensors sited in 23 high-vulnerability NTAs. The afternoon temperatures had been used by the earlier claim before this registration; the vegetation values had not been seen." % (
     r["sensors_with_exposure"], m["primary_veg50"]["sensors"], m["primary_veg50"]["n"], m["primary_veg50"]["cells"],
     e["flight_dates"]["2022-07-19"], e["flight_dates"]["2022-09-15"], 100 * e["veg50_mean"], 100 * e["veg50_sd"], 100 * e["veg50_within_nta_sd"],
     100 * e["share_sensors_veg50_ge_40pct"], 100 * e["veg50_mean_street_tree"], 100 * e["veg50_mean_light_pole"],
     t("s1_veg100", "v100"), t("s2_ndvi50", "n50"), t("s3_sept15_only", "v50"), t("s5_street_tree_mounts", "v50"), t("s5_light_pole_mounts", "v50"),
     t("s6_hot_days_tmax30", "v50"), t("s7_with_tree_count", "v50"), t("s7_with_tree_count", "tr50"),
     t("placebo_ring_alone", "vring"), t("placebo_ring_joint", "vring"), t("placebo_ring_joint", "v50"),
     t("descriptive_bins", "b10"), t("descriptive_bins", "b20"), t("descriptive_bins", "b30"), t("descriptive_bins", "b40")),
}

if __name__ == "__main__":
    print(claims.outcome(OUT))
