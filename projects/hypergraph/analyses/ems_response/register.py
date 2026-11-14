"""Registrations for the EMS response decomposition. Run once, before any 2019-2026 taxi data
are computed and before the 2019-2026 EMS hourly files are read by this thread.
Estimators: analyses/ems_response/lib.py at commit f44ab0b. Calibration (2017-2018, not used
by any test): data/derived/ems_response/calibration.json."""
from concord import claims

COMMON_ALT = [
    "Fewer ambulance unit-hours (MMR: in-service hours per day 8,891 in FY22 to 8,109 in FY26), so the nearest free unit is farther away (a distance effect, not traffic)",
    "Hospital closures and diversions lengthening repositioning (Mount Sinai Beth Israel closed 2025)",
    "Call mix and geography (more calls in slow areas or hours)",
    "Recording changes (share of incidents without a valid response time rose from 4.4% in 2023 to 9.5% in 2026)",
    "A shared within-hour cause, such as rain or an event, that slows traffic and also raises demand in that hour",
]
GRAPH = [{"summary": "The graph holds no finding on the elasticity of emergency-vehicle travel time to general traffic speed. It holds a lights-and-sirens time saving of 3.02 min (Minneapolis, PMID 9795322) and survival odds ratios of 1.02 to 1.24 per minute of shorter response (docs/congestion_tradeoffs.md).",
          "pubmed_ids": ["9795322", "20798090"]}]

claims.register({
    "id": "ems-traffic-hourly-elasticity",
    "kind": "confirmation",
    "statement": "Within a day, Manhattan ambulance travel time rises in hours when yellow-taxi trips in the same area are slower than usual, with an elasticity between 0.3 and 0.9, and taxi pace a week later does not predict it.",
    "graph_evidence": GRAPH,
    "literature": [{"citation": "docs/congestion_tradeoffs.md, bridge-crz-ems-travel registration", "finding": "Monthly zone-relative elasticity of ambulance travel time to taxi speed 0.32 (five specifications 0.14 to 0.49), October 2019 to December 2024."},
                   {"citation": "Calibration 2017-2018 (this thread, calibration.json, seen before registration)", "finding": "Same model on 2017-2018: elasticity 0.70 (0.64 to 0.75), lead coefficient in the joint model -0.04 (-0.08 to 0.01); life-threatening only 0.53 (0.46 to 0.61)."}],
    "prediction": {"direction": "+", "magnitude": "elasticity of mean EMS travel time to taxi pace (hours per mile) 0.3 to 0.9; lead coefficient near 0",
                   "support_if": "Joint model (x and x_lead together), all severities, 2019-01-01 to 2026-09-30 without 2020-03-01 to 2021-06-30: the 95% lower bound of beta_x is above 0.10, AND the 95% lower bound of beta_x - beta_lead is above 0.10.",
                   "refute_if": "The 95% upper bound of beta_x is below 0.10, OR the 95% upper bound of beta_x - beta_lead is below 0 (future traffic predicts at least as well as current traffic)."},
    "plan": "lib.t1(range(2019, 2027)) at commit f44ab0b. Cells: date x hour x area (crz with taxi cbd, north with taxi north), at least 2 EMS incidents with travel > 0 and 20 taxi trips. y = log mean EMS travel seconds (76xm-jjuj, valid response time, 2019-2026 rows from data/derived/congestion/ems_YYYY.csv); x = log taxi hours per mile (TLC yellow trip files, filter f1, analyses/ems_response/taxi_hourly.py); x_lead = x of the same area and hour 7 days later. Controls log n of the cell and log Manhattan EMS n of the hour. Fixed effects date x area and area x year x weekday x hour, weights EMS n, standard errors clustered by week. No resampling. Discrimination (rule 8): the 2017-2018 calibration gives se(beta_x) = 0.030, so D against no effect at a predicted 0.4 is 181. Secondary (reported, not deciding): life-threatening only (sev hi); x alone; lead alone; by year.",
    "alternatives": COMMON_ALT,
    "prior": 0.8,
    "registrant": "claude (ems_response thread)",
})

claims.register({
    "id": "ems-traffic-share-2019-2026",
    "kind": "conflict",
    "statement": "Slower traffic accounts for less than half of the rise in Manhattan life-threatening ambulance travel time from January-September 2019 to January-September 2026, even if ambulance pace moved one for one with taxi pace.",
    "graph_evidence": GRAPH,
    "literature": [{"citation": "MMR FY2026, FDNY chapter", "finding": "FDNY attributes the FY2026 rise to fewer ambulance tours (in-service hours down 5%) and 11 hospital ambulances leaving the 911 system."},
                   {"citation": "repro-mmr-cbd-speed (seen before registration)", "finding": "CBD weekday taxi speed 6.94, 6.95, 6.62 mph in FY24-FY26; January-June 2026 taxi speeds 9.2% below January-June 2025 in the CBD and 5.9% in Manhattan north of 60th Street."}],
    "prediction": {"direction": "-", "magnitude": "S1 (traffic share at beta = 1) between 0.05 and 0.45; S at the T1 beta between 0.03 and 0.35",
                   "support_if": "The 95% upper bound of S1 is below 0.5.",
                   "refute_if": "The 95% lower bound of S1 is above 0.5."},
    "plan": "lib.traffic_share(beta, beta_se) at commit f44ab0b, base 2019-01-01 to 2019-09-30, post 2026-01-01 to 2026-09-30, sev hi, Manhattan crz + north, all hours. D = change in log mean EMS travel; pace term = EMS-incident-weighted (post-period area-hour shares) change in log taxi hours per mile by area and hour. S1 = pace term / D (deciding). S = beta x pace term / D with beta and its se from the deciding T1 fit (x only, sev hi) is reported. Interval: day-block bootstrap within each period, 400 draws, then 20,000 draws combining beta, seed 20261113. Discrimination: the predicted S1 near 0.2 is far from 0.5 if the bootstrap half-width is below 0.15, which a 9-month comparison with about 60,000 incidents a period gives. Secondary: other periods (2019 vs 2025), all severities, the overnight hours 01-05 as a check (traffic is light, so a rise there is distance or supply).",
    "alternatives": COMMON_ALT + ["Ambulances may be slowed more than taxis by congestion (beta above 1), for example where cars cannot pull over; then S1 understates the traffic share."],
    "prior": 0.8,
    "registrant": "claude (ems_response thread)",
})

claims.register({
    "id": "ems-taxi-2026-onset",
    "kind": "confirmation",
    "statement": "Week by week from July 2025 to September 2026, the change in Manhattan ambulance travel time against the same week a year earlier tracks the change in taxi pace, and the January 2026 step in ambulance travel time is no larger than taxi pace accounts for.",
    "graph_evidence": GRAPH,
    "literature": [{"citation": "repro-mmr-cbd-speed outcome notes", "finding": "Citywide fall in taxi speeds from January 2026, cause not found."}],
    "prediction": {"direction": "+", "magnitude": "b (EMS yoy on taxi-pace yoy) 0.3 to 1.0; c (the 2026 step net of taxi pace) near 0 if traffic explains the jump",
                   "support_if": "In lib.onset(yoy) over ISO weeks 2025-W27 to 2026-W39 with split 2026-W01 (HAC 4): the 95% lower bound of b is above 0.1 AND the 95% interval of c includes 0.",
                   "refute_if": "The 95% upper bound of b is below 0.1, OR the 95% lower bound of c is above 0 (ambulance travel stepped up in 2026 by more than taxi pace accounts for)."},
    "plan": "lib.weekly(range(2024, 2027)) then lib.onset at commit f44ab0b; all severities, all hours, Manhattan crz + north pooled; weeks 53 dropped. Discrimination (rule 8): 2018-vs-2017 calibration gives se(b) = 0.21 and se(c) = 0.018, so D for b at a predicted 0.7 against no effect is 11, and a 2026 residual step of 0.05 log would be 2.7 se from 0. Secondary: life-threatening only; the same model for 2024-W27 to 2025-W39 as a placebo year.",
    "alternatives": COMMON_ALT,
    "prior": 0.25,
    "registrant": "claude (ems_response thread)",
})
print("registered")
