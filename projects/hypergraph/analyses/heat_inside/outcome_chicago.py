"""Outcome of transfer-chicago-inside-outside. Usage: python -m analyses.heat_inside.outcome_chicago"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims

ROOT = Path(__file__).resolve().parents[2]
r = json.loads((ROOT / "data/derived/heat_inside_chicago/results.json").read_text())
p = r["primary"]
ratio, ins, out = p["ratio_inside_to_outside"], p["inside_irr_per_5c"], p["outside_irr_per_5c"]
se2 = math.hypot(ins["se_log"], out["se_log"])
e2 = math.log(ratio["estimate"])
wide = {"estimate": ratio["estimate"], "lo": math.exp(e2 - 1.96 * se2), "hi": math.exp(e2 + 1.96 * se2), "se_log": se2}


def s(d):
    return f"{d['estimate']:.3f} ({d['lo']:.3f} to {d['hi']:.3f})"


support = ratio["hi"] < 1.0
refute = ins["lo"] > 1.05 and ratio["lo"] <= 1.0 <= ratio["hi"]
verdict = "confirmed" if support else ("contested" if refute else "unsettled")
REC = {
    "id": "transfer-chicago-inside-outside", "verdict": verdict,
    "city_effect": {"label": "ratio of the inside to the outside rate ratio of shootings per 5 C, Chicago 2010 to 2026",
                    "estimate": wide["estimate"], "lo": wide["lo"], "hi": wide["hi"], "scale": "ratio of rate ratios", "null": 1, "n": p["n_days"],
                    "interval_note": f"from the two separate Poisson fits with robust errors; the registered quasi-binomial interval is {ratio['lo']:.3f} to {ratio['hi']:.3f}, "
                                     f"which is too narrow because the Pearson scale is {ratio['dispersion']:.2f} on sparse daily counts"},
    "all_effects": {"ratio_registered": ratio, "ratio_from_separate_fits": wide, "inside_irr_per_5c": ins, "outside_irr_per_5c": out,
                    "inside_incidents": p["inside"], "outside_incidents": p["outside"], "classes": r["classes"], "porch_excluded": r["porch_excluded"],
                    "exploratory_after_the_run": {"homes_only_vs_street_alley_sidewalk": {"inside_irr": 1.056, "inside_lo": 1.021, "inside_hi": 1.092, "inside_n": 2856, "ratio": 0.931, "ratio_lo": 0.898, "ratio_hi": 0.964},
                                                  "commercial_interiors_vs_street": {"inside_irr": 1.002, "inside_lo": 0.939, "inside_hi": 1.069, "inside_n": 749, "ratio": 0.883, "ratio_lo": 0.827, "ratio_hi": 0.943}}},
    "sources": json.loads((ROOT / "data/derived/heat_inside_chicago/sources.json").read_text())
               + [{"kind": "derived", "path": "data/derived/graph/transfer_chicago/chicago_heat_daily.csv", "note": "Chicago weather and calendar terms"}],
    "prediction_scored": f"partial: the support condition is met, since the ratio is {s(ratio)} as registered and {s(wide)} with the wider error, both below 1.00. "
                         f"The predicted sizes were missed: the ratio is above the predicted 0.80 to 0.95, and inside shootings rise {s(ins)}, above the predicted 0.95 to 1.08. "
                         "New York's finding that inside shootings do not rise is not reproduced.",
    "settle": "A location field that separates rooms from porches, yards and garages, as New York's does. Chicago's description is free text.",
    "research_needed": [{"question": "Do shootings inside homes rise with heat less where homes are cooled?", "data": "shootings by premises type with household air conditioning by tract",
                         "design": "the same daily model, with the inside slope allowed to differ by air-conditioning share", "priority": "high"}],
    "figures": [],
    "notes": f"In Chicago shootings outside rise {s(out)} per 5 C and shootings classed inside rise {s(ins)}. The inside slope is smaller, as registered, but it is not zero as it was in New York. "
             "The registered classes were written from description names and are flawed: about a third of the incidents classed inside have descriptions that include a porch, a yard, or a parking lot or garage "
             "(for example RESIDENCE PORCH/HALLWAY, RESIDENCE - YARD, PARKING LOT / GARAGE), because the inside pattern was tested first. Exploratory runs after the registered one, which decide nothing: "
             "homes only (apartment, house, residence, hallway, basement, stairwell) against street, alley and sidewalk give 1.056 (1.021 to 1.092) inside and a ratio of 0.931 (0.898 to 0.964); "
             "commercial interiors give 1.002 (0.939 to 1.069) and a ratio of 0.883 (0.827 to 0.943). Read together with New York, the transferable statement is that shootings inside rise less with heat than shootings outside, "
             "and that the size of the difference depends on the city and on what counts as inside. No referee has read this outcome yet.",
}
if __name__ == "__main__":
    print(claims.outcome(REC), verdict)
