"""Write the outcome of heat-extremes-downturn from test_results.json, applying the registered conditions literally."""
import json
from pathlib import Path

import numpy as np

from concord import claims

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "heat_extremes"
t = json.loads((D / "test_results.json").read_text())
ds = json.loads((D / "describe.json").read_text())
src = json.loads((D / "sources.json").read_text())
p, lin = t["pooled"]["random"], t["linear_alternative"]["pooled"]["random"]
z_lin = (lin["log"] - p["log"]) / float(np.hypot(lin["se"], p["se"]))
verdict = "confirmed" if p["hi"] < 1 else "contested" if p["lo"] > 1 else "unsettled"
f = lambda e: f"{e['estimate']:.3f} ({e['lo']:.3f} to {e['hi']:.3f})"
n_hot = {c: t["cities"][c]["days"] for c in t["qualifying"]}
sens = {k: {x: round(v["pooled"]["random"][x], 3) for x in ("estimate", "lo", "hi")} for k, v in t["sensitivity"].items() if isinstance(v, dict) and v.get("pooled")}
ab = ds["slopes"]["pooled_above_35"]["random"]
rec = {
    "id": "heat-extremes-downturn",
    "verdict": verdict,
    "city_effect": {"label": "Aggravated assaults, days at 38 C or more against days at 32 to 35 C, pooled over Phoenix, Tucson, Dallas and Austin",
                    "estimate": p["estimate"], "lo": p["lo"], "hi": p["hi"], "scale": "rate ratio", "null": 1,
                    "n": f"{sum(n_hot.values())} days at 38 C or more and {sum(t['cities'][c]['days_ref'] for c in t['qualifying'])} reference days in four cities"},
    "graph_effect": {"label": "Lyons et al. 2022, shootings in 100 US cities: almost monotonic rise, local peak at the 84th percentile; no comparable contrast in the graph",
                     "estimate": None, "lo": None, "hi": None, "scale": "shape only", "null": 1},
    "by_city": {c: {k: round(v, 3) if isinstance(v, float) else v for k, v in t["cities"][c].items()} for c in t["cities"]},
    "heterogeneity": {"I2": t["pooled"]["I2"], "Q": t["pooled"]["Q"], "fixed_effect": {k: round(t["pooled"]["fixed"][k], 3) for k in ("estimate", "lo", "hi")}},
    "sensitivity": sens,
    "linear_alternative": {"pooled_prediction": {k: round(lin[k], 3) for k in ("estimate", "lo", "hi")}, "z_observed_below_linear": round(z_lin, 2),
                           "by_city": {c: round(v["linear_prediction"], 3) for c, v in t["linear_alternative"]["cities"].items()}},
    "sources": [s for c in src["sources"].values() for s in c],
    "prediction_scored": ("miss. The registered downturn (pooled ratio 0.88 to 0.98) was not found. The refutation condition is met: the pooled lower limit is "
                          f"{p['lo']:.3f}, above 1.00 by less than the sampling error (rule 10), and it falls to 0.997 when 2020 and 2021 are left out."),
    "settle": ("Hourly counts with indoor and outdoor location would show whether the flat rate above 35 C hides a fall outdoors and a rise indoors, as Stevens et al. "
               "report for New South Wales. More days above 41 C outside Phoenix would show whether the lower estimates at 41 C and above are a turn or noise."),
    "research_needed": [
        {"question": "Does the rate fall above 41 C?", "data": "Aggravated assaults in more desert cities (Las Vegas, Mesa, Palm Springs, cities in the Gulf and South Asia)", "design": "the same within-city contrast with 41 C and above as the hot bin", "priority": "high"},
        {"question": "Is the plateau an average of an outdoor fall and an indoor rise?", "data": "premise type and hour of each incident (Phoenix and Los Angeles publish both)", "design": "the same curve by premise type and by day and night", "priority": "high"}],
    "figures": ["figures/heat_extremes/dose_response_by_city.png"],
    "notes": (f"Registered result. Pooled rate ratio {f(p)}; Phoenix {f(t['cities']['phoenix'])}, Tucson {f(t['cities']['tucson'])}, Dallas {f(t['cities']['dallas'])}, "
              f"Austin {f(t['cities']['austin'])}; I2 = {t['pooled']['I2']:.2f}. The rate at 38 C and above is 3.5% higher than at 32 to 35 C, so there is no downturn at 38 C. "
              f"It is also lower than the straight-line prediction from each city's slope below 35 C, {f(lin)} (z = {z_lin:.1f}), so the rise slows. "
              f"Planned description, not deciding: the piecewise-linear slope above 35 C is {f(ab)} per 5 C against {f(ds['slopes']['pooled_20_to_35']['random'])} per 5 C from 20 to 35 C; "
              "the steps against 32 to 35 C are 1.010 for 35 to 38 C, 1.041 for 38 to 41 C and 1.007 for 41 C and above. The verdict label 'contested' means that the downturn hypothesis "
              "is refuted at 38 C; the data fit a plateau above about 35 C better than either registered alternative."),
}
if __name__ == "__main__":
    print(claims.outcome(rec), verdict, f(p), "z_lin", round(z_lin, 2))
