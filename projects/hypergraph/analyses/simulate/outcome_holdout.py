"""Write the outcome of sim-crz-holdout-2026 from data/derived/simulate/holdout_result.json.
The registered conditions are applied literally. Run: python -m analyses.simulate.outcome_holdout
"""
import json
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "simulate"


def main():
    R = json.loads((DER / "holdout_result.json").read_text())
    S = json.loads((DER / "panel_holdout_sources.json").read_text())
    s1, s2, sb = R["slopes"]["speed_primary_pooled"], R["slopes"]["ambulance"], R["slopes"]["speed_by_band"]
    L = R["level"]
    beta = R["fit"]["speed_flow_pooled"]["est"]
    support = s1["lo"] > 0 and s1["lo"] <= 1 <= s1["hi"]
    refute = s1["hi"] < 0.5
    verdict = "confirmed" if support else "contested" if refute else "unsettled"
    s2_support = s2["lo"] > 0 and s2["lo"] <= 1 <= s2["hi"]
    bands = L["by_band"]
    rec = {
        "id": "sim-crz-holdout-2026",
        "verdict": verdict,
        "verdict_note": ("The speed link of the simulator did not transfer to the held-out months: the elasticity of zone speed to vehicle "
                         f"entries was {s1['slope'] * beta:.2f} in January-June 2026 against {beta:.2f} fitted on 2025, and the estimate "
                         "rests on two storm days. The ambulance link did transfer in slope."),
        "city_effect": {"label": "S1: held-out elasticity of zone taxi speed to vehicle entries as a ratio of the elasticity fitted on 2025 "
                                 f"({beta:.3f}); non-holiday weekdays 5 January to 30 June 2026, by band of hours",
                        "estimate": s1["slope"], "lo": s1["lo"], "hi": s1["hi"], "scale": "ratio of held-out to fitted elasticity",
                        "null": 0, "n": s1["n"]},
        "graph_effect": None,
        "components": {"S2_ambulance": s2, "S1_band_specific": sb, "level": L},
        "sources": [S["entries"][0], S["ems"][0], S["speed"][0]],
        "prediction_scored": (
            f"miss on the primary. S1 = {s1['slope']:.2f} ({s1['lo']:.2f} to {s1['hi']:.2f}), n = {s1['n']} band-days on {R['holdout_days']} days: "
            "the interval lies above zero, so the sign is as fitted, but its upper bound is below 0.5 and refute_if is met. "
            f"As an elasticity the held-out value is {s1['slope'] * beta:.3f} ({s1['hi'] * beta:.3f} to {s1['lo'] * beta:.3f}). "
            f"Secondary (a), the ambulance link: S2 = {s2['slope']:.2f} ({s2['lo']:.2f} to {s2['hi']:.2f}), a "
            f"{'hit' if s2_support else 'miss'} by the same conditions. Secondary (b), band-specific elasticities: "
            f"{sb['slope']:.2f} ({sb['lo']:.2f} to {sb['hi']:.2f}). Secondary (c), levels against January-June 2025: "
            f"speed predicted from entries has a mean absolute error of {L['mean_abs_speed_err_pct']:.1f}% over the four bands against "
            f"{L['mean_abs_speed_naive_err_pct']:.1f}% for predicting no change, a miss, as I expected, and worse than I expected because "
            f"entries fell ({bands['am']['entries_change_pct']:.1f}% in the morning band, {bands['mid']['entries_change_pct']:.1f}% at midday) "
            "while speed also fell, so the model predicted a rise. Travel time predicted through the chain: "
            f"{L['mean_abs_tt_chain_err_pct']:.1f}% against {L['mean_abs_tt_naive_err_pct']:.1f}% for no change, a miss. Travel time predicted "
            f"from the observed fall in speed (the blind test of the ambulance link): {L['mean_abs_tt_link_err_pct']:.1f}%, better than no "
            "change but above the registered 4%, a miss: travel times rose by 10% to 15% and the speed fall accounts for under half of that."),
        "settle": ("Counts of vehicles and of people inside the zone by hour, not only vehicles crossing its edge, so that speed can be related "
                   "to what is on the streets; and a second price. The toll rises to $12 in 2028, which will give the first measured "
                   "response of entries and speed to a change in the toll other than its introduction."),
        "research_needed": [
            {"question": "What sets traffic speed inside a priced zone once entries are priced: vehicles crossing the cordon, trips made inside it, "
                         "deliveries and kerb activity, or people on foot?",
             "data": "Vehicle counts inside the zone, kerb and delivery activity, pedestrian counts, by hour and weekday",
             "design": "Daily panel with weather and event controls; the 2028 toll step as a natural experiment", "priority": "high"},
            {"question": "Why did ambulance travel times in the zone rise by 10% to 15% from the first half of 2025 to the first half of 2026?",
             "data": "EMS incidents (76xm-jjuj) with unit availability and hospital turnaround times",
             "design": "Decomposition by call volume, unit hours and street speed", "priority": "high"}],
        "figures": ["figures/simulate/holdout_levels.png"],
        "notes": (
            "Exploratory, after the outcome was read, and not part of the verdict. The standard error of S1 (0.05) is a seventh of the one "
            "expected at registration (0.35). The held-out period contains two storm days, 26 January and 23 February 2026, when vehicle "
            "entries were 40% and 13% of a normal weekday. On those days entries collapsed and taxi speed rose little, and they fix the "
            "estimate. Without the four weekdays whose entries were under 80% of the median, the held-out elasticity is +0.08 (se 0.54), "
            "which neither supports nor refutes the fitted value; pooled over 2025 and 2026 without those days it is -0.23 (se 0.23). The two "
            "storm Mondays were known from subway entries (transit-weekday-pattern) and the registration should have excluded them; it did "
            "not, so the verdict stands as registered. The level result does not depend on the storm days: from January-June 2025 to "
            "January-June 2026 vehicle entries per weekday fell from 507,000 to 480,000 and zone taxi speed fell in every band. Yellow-taxi "
            "trips inside the zone also fell, from 51,000 to 45,000 a weekday, so the speed series comes from a changing set of trips. "
            "On 2025 weekdays, Mondays and Fridays have 2.8% fewer daytime vehicle entries than Tuesday to Thursday, 10.1% higher taxi "
            "speed and 6.8% shorter ambulance travel times: the weekday pattern of speed follows people present in the zone (subway entries "
            "are 13.8% lower on those days) and not vehicle entries."),
    }
    print(claims.outcome(rec), verdict)


if __name__ == "__main__":
    main()
