"""Register sim-crz-holdout-2026: the simulator's two fitted links, tested on months not used to fit them.

Run once, before data/derived/simulate/panel_holdout.csv exists:
  python -m analyses.simulate.register_holdout
"""
import json
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[2]
F = json.loads((ROOT / "data/derived/simulate/fits_calib.json").read_text())
b, th = F["speed_flow_pooled"], F["ambulance_speed"]
reh = F["rehearsal_split_2025"]
se_b = reh["test_second_half"]["speed_primary_pooled"]["se"] * abs(reh["fit_first_half"]["speed_flow_pooled"]["est"])
se_t = reh["test_second_half"]["ambulance"]["se"] * abs(reh["fit_first_half"]["ambulance_speed"]["est"])
s1, s2 = se_b / abs(b["est"]), se_t / abs(th["est"])

REC = {
    "id": "sim-crz-holdout-2026",
    "kind": "confirmation",
    "statement": ("The two links of the congestion-pricing simulator that are fitted to city data on non-holiday weekdays of "
                  "6 January to 23 December 2025 predict days of 5 January to 30 June 2026 that were not used to fit them: "
                  f"taxi speed inside the zone south of 60th Street changes by {b['est']:.2f}% for each 1% more vehicle entries "
                  f"in the same band of hours, and ambulance travel time to life-threatening incidents changes by {th['est']:.2f}% "
                  "for each 1% more taxi speed."),
    "graph_evidence": [{
        "concepts": "traffic volume or congestion | travel speed; traffic speed | ambulance travel time",
        "n_findings": 4, "direction": "none usable",
        "summary": ("System Public Graph variable searches (analyses/simulate/graph_links.py, data/derived/simulate/graph_links.json): "
                    "no finding relates vehicle volume to travel speed or travel speed to ambulance travel time as a dose and a response. "
                    "The four findings matched are one study of hospital staff travel times at peak hours against midnight (PMID 29359134), "
                    "which gives no elasticity. The graph has no road-pricing findings (docs/mobility.md).")}],
    "literature": [],
    "prediction": {
        "direction": "+",
        "magnitude": (f"Primary: slope S1 = 1 (the held-out elasticity equals the fitted {b['est']:.3f}, se {b['se']:.3f}). "
                      f"Secondary: slope S2 = 1 for the ambulance link (fitted {th['est']:.3f}, se {th['se']:.3f}). "
                      "Level: I expect the speed level to be over-predicted, see the plan."),
        "support_if": "The 95% interval of S1 lies above 0 and includes 1.",
        "refute_if": "The upper bound of the 95% interval of S1 is below 0.5: the held-out elasticity is under half the fitted one, zero, or of the opposite sign.",
    },
    "plan": (
        "Data, built by analyses/simulate/build_data.py (fixed and committed with this registration): MTA Congestion Relief Zone vehicle "
        "entries (data.ny.gov t6yz-b64h) summed over classes by date and hour; yellow-taxi trips that start and end in the 38 zone taxi "
        "zones under the R1 filter of repro-mmr-cbd-speed, speed = miles / hours; EMS incidents (76xm-jjuj) in community districts 101-106 "
        "with a valid response time and initial severity 1 to 3, mean travel time of the first unit. Unit: date by band of hours "
        "(night 21:00-04:59, am 05:00-09:59, mid 10:00-15:59, pm 16:00-20:59), non-holiday weekdays, 24 December to 1 January dropped. "
        "Estimator, analyses/simulate/fit_links.py (fixed): calibration fit by OLS of log speed on log entries with band x month and "
        "band x weekday effects, one pooled coefficient, standard errors clustered by ISO week; and log travel time on log speed with the "
        "same effects. Test (function holdout_test): on the held-out days, OLS of log speed on z = fitted elasticity x log entries with "
        "band x month and band x weekday effects of the held-out period; S1 is the coefficient of z, interval = estimate +/- 1.96 clustered "
        "se. S2 is the same for log travel time on fitted elasticity x log speed. No resampling is used, so there is no seed. "
        "Secondary, reported and not deciding: (a) S2 scored by the same two conditions as S1; (b) S1 with the band-specific elasticities; "
        "(c) level errors by band (function level_test), against the same band and weekday in 6 January to 30 June 2025: speed predicted from "
        "the change in entries; travel time predicted from the predicted speed (the chain); travel time predicted from the observed change "
        "in speed (the ambulance link alone). A level prediction counts as a hit if its mean absolute error over the four bands is at most "
        "4% and smaller than the error of predicting no change. "
        f"Can the test fail (rule 8)? A rehearsal inside the calibration year (fit January-June 2025, test July-December 2025; "
        f"fits_calib.json) gave a standard error of {se_b:.3f} for the held-out speed elasticity and {se_t:.3f} for the ambulance elasticity. "
        f"On the slope scale these are {s1:.2f} and {s2:.2f}, so if the fitted elasticities are right the expected D against no relation is "
        f"{1 / s1 ** 2:.1f} for S1 and {1 / s2 ** 2:.1f} for S2, both above 4. A world with no relation would meet support_if about 2.5% of "
        "the time. The rehearsal itself gave S1 = 2.5 (1.1 to 3.9): the first-half elasticity was -0.20 and the second-half one about -0.51, "
        "so the elasticity is not stable within 2025 and an interval that excludes 1 is a live possibility; that outcome is unsettled, not confirmed. "
        "What I have already seen of the held-out period: the half-year mean zone speeds for weekdays 08:00-17:59 in the outcome of "
        "repro-mmr-cbd-speed, 7.24 mph in January-June 2025 and 6.57 mph in January-June 2026, a fall of 9%. I have not seen 2026 vehicle "
        "entries, 2026 speeds by day or hour, or any EMS travel time for 2026. Because of the 9% fall, the speed level test (c) is not blind: "
        "with the fitted elasticity it would take about 25% more entries to produce that fall, which I do not expect, so I expect the model "
        "to over-predict the 2026 speed level by 5% to 9% in the am and mid bands and to do little better than predicting no change. "
        "The ambulance level test is blind: with the fitted elasticity a 9% fall in speed predicts about 5% longer travel times in the "
        "am and mid bands in 2026 than in the same months of 2025. "
        "Verdict by PRECEDENCE rule 1 on the primary conditions; otherwise unsettled. The slopes are associations between days: a day "
        "with more entries also has more pedestrians and deliveries, so a confirmed slope does not show what a toll-induced change in "
        "entries would do to speed."),
    "rivals": ["Days with more vehicle entries are days with more people and deliveries in the zone, which slow traffic on their own; the slope then overstates the effect of entries.",
               "Congestion inside the zone holds vehicles at the crossings and lowers counted entries, which biases the slope toward zero.",
               "Changes in the taxi fleet's routes or trip mix between years move measured taxi speed without a change in traffic.",
               "EMS travel time depends on unit availability and call volume, which vary with the same days."],
    "prior": 0.45,
}

if __name__ == "__main__":
    print(claims.register(REC))
