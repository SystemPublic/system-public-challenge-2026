"""Write the outcome of transfer-chicago-hot-end from data/derived/round2/hot_end/results.json."""
import json
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data" / "derived" / "round2" / "hot_end"
r = json.loads((D / "results.json").read_text())
src = json.loads((D / "sources.json").read_text())
L = r["lin"]
f = lambda v: "%.3f (%.3f to %.3f)" % (v["estimate"], v["lo"], v["hi"])
dv = src["divvy"]
divvy_src = {"type": "socrata", "domain": "data.cityofchicago.org", "dataset": "fg6s-gzvg", "name": "Divvy Trips",
             "n_queries": len(dv), "first_query": dv[0], "last_query": dv[-1], "all_queries": "data/derived/round2/hot_end/sources.json"}
heat = json.loads((ROOT / "data/derived/graph/transfer_chicago/heat_results.json").read_text())
sh, px = L["shootings_full"]["rr_33_vs_27"], L["proxy_trips"]["rr_33_vs_27"]
s = L["shares_trips"]
a_ok = px["hi"] < 1.06 and sh["lo"] > 1.0
b_ok = (s["share_21_vs_15"]["estimate"] >= 0.20 and s["share_21_vs_15"]["lo"] > 0.10
        and s["removed_log_33_vs_27"]["estimate"] < 0.028 and s["removed_log_33_vs_27"]["hi"] < 0.057)
a_ref = px["lo"] > 1.06 or sh["hi"] < 1.06
verdict = "confirmed" if (a_ok and b_ok) else ("contested" if a_ref else "unsettled")
rec = {
    "id": "transfer-chicago-hot-end",
    "verdict": verdict,
    "parts": {"a_supported": a_ok, "b_supported": b_ok, "a_refuted": a_ref},
    "city_effect": {"label": "Chicago gunshot-injury cases, ratio 33 C against 27 C of Midway TMAX (piecewise-linear spline), 2010-2026",
                    "estimate": sh["estimate"], "lo": sh["lo"], "hi": sh["hi"], "scale": "rate ratio 33 C vs 27 C", "null": 1, "n": r["n_days_full"]},
    "graph_effect": None,
    "sources": [divvy_src] + (heat.get("sources") or [{"type": "derived", "path": "data/derived/graph/transfer_chicago/chicago_heat_daily.csv",
                                                       "note": "gumc-mgzr and GHCN-Daily USW00014819 as fetched by transfer-chicago-heat-shootings"}]),
    "prediction_scored": ("partial. Part (a) met: Divvy trips change by %s from 27 to 33 C (upper limit below 1.06) and shootings rise by %s (lower limit above 1). "
                          "Part (b) not met: all Divvy trips remove %s of the 15 to 21 C rise, below the registered 0.20; the amount removed from the 27 to 33 C log rise is %s, "
                          "within the registered bound." % (f(px), f(sh), f(s["share_21_vs_15"]), f(s["removed_log_33_vs_27"]))),
    "settle": ("A daily count of people on residential streets in the evening (pedestrian counters, or a noise or gathering complaint series, which Chicago's 311 does not hold), "
               "and Divvy trips after 2019 from the operator's archives, would say whether the decomposition fails because of the proxy or because of the city."),
    "research_needed": [
        {"question": "What accounts for the rise in shootings above 27 C, when outdoor activity is no longer rising?",
         "data": "Hourly indoor temperature in housing without air conditioning; nightly sleep duration (wearable panels); alcohol sales by day and hour; hourly shootings with hourly temperature.",
         "design": "Daily and hourly models with the candidate step added, in two or more cities; night-time minimum temperature as the exposure for the sleep step.", "priority": "high"},
        {"question": "Does a pedestrian or gathering proxy in Chicago remove as much of the mild-day slope as street-noise complaints do in New York?",
         "data": "Chicago police non-emergency noise or disturbance calls by day, if released; pedestrian counters.", "design": "The registered model with that proxy.", "priority": "medium"}],
    "figures": ["figures/round2/hot_end_two_cities.png"],
    "notes": ("Secondary, registered as not deciding: Divvy casual (Customer) trips change by %s from 27 to 33 C and remove %s of the 15 to 21 C rise; subscriber trips change by %s and remove %s. "
              "With the 4-df quantile-knot basis of the New York exploratory analysis the all-trips ratio from 27 to 33 C is %s and the shootings ratio %s; a simulation run before registration "
              "showed that this basis overstates the ratio when the curve bends near 27 C. Shootings on the Divvy window alone: %s. No graph request was made." % (
                  f(L["proxy_customer"]["rr_33_vs_27"]), f(L["shares_customer"]["share_21_vs_15"]), f(L["proxy_subscriber"]["rr_33_vs_27"]), f(L["shares_subscriber"]["share_21_vs_15"]),
                  f(r["q4"]["proxy_trips"]["rr_33_vs_27"]), f(r["q4"]["shootings_full"]["rr_33_vs_27"]), f(L["shootings_window"]["rr_33_vs_27"]))),
}
print(claims.outcome(rec), verdict, rec["parts"])
