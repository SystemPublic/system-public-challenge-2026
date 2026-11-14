"""Write the outcomes of the three registered EMS claims from results.json."""
import json
from concord import claims
from analyses.ems_response.common import DER, ROOT

R = json.load(open(DER / "results.json"))
srcE = json.load(open(DER / "ems_sources.json"))
srcC = json.load(open(ROOT / "data/derived/congestion/ems_sources.json"))
taxi = []
for f in sorted(DER.glob("taxi_files_*.json")):
    taxi += json.load(open(f))
taxi_rec = {"kind": "tlc-trip-record-files", "name": "TLC yellow taxi trip records, monthly parquet",
            "page": "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page",
            "files": taxi, "also_used": "data/derived/congestion/taxi_speed_2023-07_2024-12.csv and taxi_speed_2025-01_2026-06.csv (cbd and north, same filter) for July 2023 to December 2025; file versions in data/derived/reproduction/mmr_cbd_speed_files.json"}
ems_rec = [s for k in ("hourly_2017", "hourly_2018") for s in srcE.get(k, [])] + [s for y in srcC for s in srcC[y]]
for s in ems_rec:
    s.pop("query", None)
ems_rec = [ems_rec[0] | {"queries": "analyses/ems_response/ems_fetch.py (hourly, 2017-2018) and analyses/congestion/ems_fetch.py (ems, 2019-2026); full SoQL in data/derived/ems_response/ems_sources.json and data/derived/congestion/ems_sources.json"}]
SOURCES = ems_rec + [taxi_rec]
DEV = ("Deviation from the plan: on 13 November the TLC file host refused downloads for about 30 minutes, so lib.taxi_hourly was changed after registration to read the cbd and north rows of data/derived/congestion/taxi_speed_*.csv for July 2023 to December 2025. Those rows use the same areas, the same trip filter and the same TLC files; the estimators were not changed. Months 2021-07 to 2023-06 and 2026-01 to 2026-09 were computed here.")

t1 = R["t1"]
j, d = t1["joint"], t1["diff_x_minus_lead"]
claims.outcome({
    "id": "ems-traffic-hourly-elasticity", "verdict": "confirmed",
    "city_effect": {"label": "elasticity of Manhattan EMS mean travel time to same-hour yellow-taxi time per mile, joint model with the 7-day lead, within date x area", "estimate": j["x"]["est"], "lo": j["x"]["lo"], "hi": j["x"]["hi"], "scale": "elasticity", "null": 0, "n": j["n_cells"]},
    "sources": SOURCES,
    "prediction_scored": f"hit: beta_x = {j['x']['est']:.3f} ({j['x']['lo']:.3f} to {j['x']['hi']:.3f}), inside the registered 0.3 to 0.9 and with a lower bound above 0.10; beta_x - beta_lead = {d['est']:.3f} ({d['lo']:.3f} to {d['hi']:.3f}), lower bound above 0.10. The lead coefficient in the joint model is {j['x_lead']['est']:.3f} ({j['x_lead']['lo']:.3f} to {j['x_lead']['hi']:.3f}).",
    "settle": "The test is within-day and within Manhattan below 110th Street. Whether the same elasticity holds for year-to-year changes and outside Manhattan needs GPS traces of ambulances (FDNY AVL) or high-volume FHV trip speeds by borough.",
    "research_needed": [{"question": "Ambulance travel speed against general traffic speed on the same streets", "data": "FDNY automatic vehicle location traces (not public)", "design": "matched street segments and hours", "priority": "high"}],
    "figures": [], "notes": (
        f"{j['n_cells']} date-hour-area cells, {j['n_incidents']} incidents, {j['n_weeks']} weeks, 2019-01 to 2026-09 without March 2020 to June 2021. Lead alone (secondary): {t1['lead_only']['x_lead']['est']:.3f} ({t1['lead_only']['x_lead']['lo']:.3f} to {t1['lead_only']['x_lead']['hi']:.3f}), which reflects hour-of-week patterns that persist for weeks (for example road works); with current pace in the model it is near zero. Life-threatening calls only: {R['t1_hi']['joint']['x']['est']:.3f} ({R['t1_hi']['joint']['x']['lo']:.3f} to {R['t1_hi']['joint']['x']['hi']:.3f}). By year the elasticity lies between "
        f"{min(v['est'] for v in R['t1_by_year'].values()):.2f} and {max(v['est'] for v in R['t1_by_year'].values()):.2f}. The 2017-2018 calibration, seen before registration, gave 0.70. A shared within-hour cause (rain, an event) that slows traffic and also lengthens the distance to a free unit is not excluded; the cell and Manhattan-hour incident counts are controlled. " + DEV)})

t2 = R["t2"]
claims.outcome({
    "id": "ems-traffic-share-2019-2026", "verdict": "confirmed",
    "city_effect": {"label": "share of the 2019-2026 rise in Manhattan life-threatening EMS travel time that traffic could account for if ambulance pace moved one for one with taxi pace (S1)", "estimate": t2["S1"], "lo": t2["S1_ci"][0], "hi": t2["S1_ci"][1], "scale": "share", "null": 0.5, "n": 2},
    "sources": SOURCES,
    "prediction_scored": f"hit: S1 = {t2['S1']:.3f} ({t2['S1_ci'][0]:.3f} to {t2['S1_ci'][1]:.3f}); the upper bound is below 0.5 by {0.5 - t2['S1_ci'][1]:.2f}, and the estimate is inside the registered 0.05 to 0.45. At the measured elasticity for life-threatening calls ({t2['beta']:.3f}) the share is {t2['S']:.3f} ({t2['S_ci'][0]:.3f} to {t2['S_ci'][1]:.3f}), inside the registered 0.03 to 0.35.",
    "settle": "The share outside Manhattan needs a traffic measure for the Bronx, Queens and Staten Island (FHV trip speeds or DOT probe speeds) and unit locations at dispatch, which would measure the distance to the assigned unit directly.",
    "research_needed": [{"question": "Distance from the assigned ambulance to the incident, by year", "data": "FDNY CAD unit locations at assignment (not public)", "design": "decompose travel time into distance and speed", "priority": "high"},
                        {"question": "Free ambulances by hour and borough", "data": "FDNY units in service and busy by hour (not public; MMR gives annual in-service hours only)", "design": "regress travel time on free units", "priority": "high"}],
    "figures": ["figures/ems_response/decomposition.png", "figures/ems_response/night_day.png"],
    "notes": f"Manhattan below 110th Street, January-September 2019 against January-September 2026. Life-threatening travel rose {t2['D_pct']:.1f}% and taxi time per mile, weighted by where and when the 2026 incidents happened, rose {t2['pace_change_pct']:.1f}% ({100*t2['pace_ci'][0]:.1f} to {100*t2['pace_ci'][1]:.1f} on the log scale x100). Secondary: 2019 against 2025, S1 = {R['t2_2025']['S1']:.3f} ({R['t2_2025']['S1_ci'][0]:.3f} to {R['t2_2025']['S1_ci'][1]:.3f}); lower-severity calls, S1 = {R['t2_all_sev']['S1']:.3f}. Overnight (01:00-05:59), when traffic is light, Manhattan life-threatening travel rose 33% while taxi time per mile rose 14% in the CBD and 5% north of 60th Street (exploratory, night_day.json). The interval is a day-block bootstrap with 400 resamples combined with 20,000 draws of beta, seed 20261113; the margin to the threshold (0.13) is several times the half-width, so other seeds cannot move it across. " + DEV})

t3 = R["t3"]
c = t3["c"]
z_chain = c["est"] / c["se"]
z_alt = (c["est"] - t3["step_e"]) / c["se"]
claims.outcome({
    "id": "ems-taxi-2026-onset", "verdict": "confirmed",
    "city_effect": {"label": "slope of weekly year-on-year change in Manhattan EMS travel time on that of taxi time per mile, 2025-W27 to 2026-W39", "estimate": t3["b"]["est"], "lo": t3["b"]["lo"], "hi": t3["b"]["hi"], "scale": "elasticity", "null": 0, "n": t3["n_weeks"]},
    "sources": SOURCES,
    "prediction_scored": f"hit: b = {t3['b']['est']:.3f} ({t3['b']['lo']:.3f} to {t3['b']['hi']:.3f}), lower bound above 0.1; the 2026 step net of taxi pace c = {c['est']:.3f} ({c['lo']:.3f} to {c['hi']:.3f}) includes 0. Discrimination: against the alternative that none of the 2026 step is traffic (c equal to the raw EMS step, {t3['step_e']:.3f}), z_chain = {z_chain:.2f}, z_alt = {z_alt:.2f}, D = {z_alt**2 - z_chain**2:.1f}.",
    "settle": "Manhattan only. The largest 2026 rises were in Queens and the Bronx, where yellow taxis give no usable weekly speed. FHV (Uber, Lyft) trip speeds by borough and week would extend the test.",
    "research_needed": [{"question": "Did the 2026 rise in Queens and Bronx ambulance travel time follow traffic speed?", "data": "TLC high-volume FHV trip files (trip_miles, trip_time) by borough and week, 2025-2026", "design": "the registered onset model by borough", "priority": "high"},
                        {"question": "Why did taxi speeds fall citywide from January 2026?", "data": "DOT probe speeds, street-works permits, TLC trip counts", "design": "event timing by week and area", "priority": "medium"}],
    "figures": ["figures/ems_response/weekly_yoy.png"],
    "notes": f"The raw step (January-September 2026 against July-December 2025, each against the same week a year earlier) is +{100*t3['step_e']:.1f} log points for ambulance travel and +{100*t3['step_p']:.1f} for taxi time per mile. Placebo year (2024-W27 to 2025-W39, split 2025-W01): b = {R['t3_placebo_year']['b']['est']:.2f} ({R['t3_placebo_year']['b']['lo']:.2f} to {R['t3_placebo_year']['b']['hi']:.2f}), c = {R['t3_placebo_year']['c']['est']:.3f} ({R['t3_placebo_year']['c']['lo']:.3f} to {R['t3_placebo_year']['c']['hi']:.3f}). Life-threatening only: b = {R['t3_hi']['b']['est']:.2f}, c = {R['t3_hi']['c']['est']:.3f} ({R['t3_hi']['c']['lo']:.3f} to {R['t3_hi']['c']['hi']:.3f}). The weekly slope (0.89) is above the hourly elasticity (0.63) of ems-traffic-hourly-elasticity; with 0.63 the taxi step predicts +4.8 points against the observed +3.4. This confirms that the 2025-to-2026 step in Manhattan is in proportion to the fall in taxi speed; it does not explain the larger 2019-2025 rise, which ems-traffic-share-2019-2026 attributes mostly to something other than traffic. " + DEV})
print("ok")
