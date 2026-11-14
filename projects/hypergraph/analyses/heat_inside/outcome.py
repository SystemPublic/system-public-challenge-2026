"""Outcomes of heat-inside-outside and heat-inside-outside-2006. Usage: python -m analyses.heat_inside.outcome"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims

ROOT = Path(__file__).resolve().parents[2]


def s(d):
    return f"{d['estimate']:.3f} ({d['lo']:.3f} to {d['hi']:.3f})"


for cid, folder in (("heat-inside-outside", "heat_inside"), ("heat-inside-outside-2006", "heat_inside_2006")):
    r = json.loads((ROOT / "data/derived" / folder / "results.json").read_text())
    ratio, ins, out = r["ratio_inside_to_outside"], r["inside_irr_per_5c"], r["outside_irr_per_5c"]
    # Wider interval from the two separate Poisson fits, which allow overdispersion (reported, deciding nothing).
    se2 = math.hypot(ins["se_log"], out["se_log"])
    e2 = math.log(ins["estimate"] / out["estimate"])
    wide = {"estimate": math.exp(e2), "lo": math.exp(e2 - 1.96 * se2), "hi": math.exp(e2 + 1.96 * se2), "se_log": se2}
    support = ratio["hi"] < 1.0
    refute = ins["lo"] > 1.05 and ratio["lo"] <= 1.0 <= ratio["hi"]
    verdict = "confirmed" if support else ("contested" if refute else "unsettled")
    rec = {
        "id": cid, "verdict": verdict,
        "city_effect": {"label": f"ratio of the inside to the outside rate ratio of shootings per 5 C, New York City {r['first'][:4]} to {r['last'][:4]}",
                        "estimate": ratio["estimate"], "lo": ratio["lo"], "hi": ratio["hi"], "scale": "ratio of rate ratios", "null": 1, "n": r["n_days"]},
        "all_effects": {"ratio_registered": ratio, "ratio_from_separate_poisson_fits": wide, "inside_irr_per_5c": ins, "outside_irr_per_5c": out,
                        "inside_incidents": r["inside"], "outside_incidents": r["outside"], "first": r["first"], "last": r["last"]},
        "sources": json.loads((ROOT / "data/derived" / folder / "sources.json").read_text())
                   + [{"kind": "derived", "path": "data/derived/heat/shootings_daily.csv", "note": "Central Park weather and calendar terms"}],
        "prediction_scored": f"hit: outside {s(out)} per 5 C, inside {s(ins)}, ratio {s(ratio)}; the upper bound of the ratio is below 1.00. "
                             f"The ratio computed from the two separate fits, which allow overdispersion, is {s(wide)}, also below 1.00.",
        "settle": "Whether the people shot inside were in rooms without cooling. Shootings by premises type and building air conditioning would test a direct effect of indoor heat.",
        "research_needed": [{"question": "Does domestic violence, which happens mostly inside, rise with heat in New York?",
                             "data": "NYPD complaints flagged as domestic, by day", "design": "the same daily model, inside and outside premises", "priority": "high"}],
        "figures": [],
        "notes": "Shootings recorded as outside rise with temperature and shootings recorded as inside do not. A direct effect of heat on temper, "
                 "sleep or medication acts on a person wherever they are, and predicts a rise inside as well, unless the affected person goes "
                 "outside before the shooting. The result therefore favours the account in which heat puts more people in contact outdoors, "
                 "and limits the direct accounts to effects that work through being outside. Inside shootings are a different mix of events "
                 "(domestic, commercial), so the comparison is not of like with like. The registered binomial interval treats incidents as "
                 "independent and is narrower than the interval from the separate fits; both are reported. No referee has read this outcome yet.",
    }
    print(claims.outcome(rec), verdict)
