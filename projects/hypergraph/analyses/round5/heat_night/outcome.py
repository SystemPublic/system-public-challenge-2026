"""Write the outcome of heat-night-minimum from data/derived/round5/heat_night/results.json."""
import json
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data/derived/round5/heat_night"
r = json.loads((D / "results.json").read_text())
x = json.loads((D / "exploratory.json").read_text())
des = json.loads((D / "prereg_design.json").read_text())
reg = json.loads((ROOT / "claims/registered/heat-night-minimum.json").read_text())
f = lambda v: "%.3f (%.3f to %.3f)" % (v["estimate"], v["lo"], v["hi"])
ny, ch = r["new_york"], r["chicago"]
pa, pb = ny["part_a"], ny["part_b"]
ca, cb = ch["part_a"], ch["part_b"]


def b_label(v):
    return "met" if v["lo"] > 1 else "reversed" if v["hi"] < 1 else "not separated"


same = (ny["scored"]["support"] and ch["scored"]["support"]) or (ny["scored"]["refute"] and ch["scored"]["refute"])
opp = (ny["scored"]["support"] and ch["scored"]["refute"]) or (ny["scored"]["refute"] and ch["scored"]["support"])
comp = des["composition"]["composed"]["ratio_lo_median_hi"]
rec = {
    "id": "heat-night-minimum",
    "verdict": r["verdict"],
    "parts": {"a_new_york": ny["scored"], "a_chicago": ch["scored"],
              "b_new_york": b_label(pb["night_over_day_ratio_of_ratios"]), "b_chicago": b_label(cb["night_over_day_ratio_of_ratios"]),
              "c_replication": "replicated" if same else "not replicated" if opp else "inconclusive"},
    "city_effect": {"label": "New York shooting incidents per 5 C of the preceding night's minimum (Central Park TMIN) at fixed TMAX, shooting days with TMAX >= 27 C, 2006-2026",
                    "estimate": pa["primary"]["estimate"], "lo": pa["primary"]["lo"], "hi": pa["primary"]["hi"],
                    "scale": "rate ratio per 5 C TMIN", "null": 1, "n": pa["n_days"]},
    "graph_effect": {"label": "Composed from graph findings: room temperature to sleep (Valham 2012) and sleep to aggression (Street 2016), with an assumed outdoor-to-bedroom slope",
                     "estimate": comp[1], "lo": comp[0], "hi": comp[2], "scale": "rate ratio per 5 C TMIN", "null": 1},
    "graph_evidence": reg["graph_evidence"],
    "sources": json.loads((D / "sources.json").read_text()) + [
        {"kind": "sysgraph", "api": "https://public-api.system.com v1.0", "uncached_requests": 124, "file": "data/derived/round5/heat_night/graph.json"}],
    "prediction_scored": (
        "partial. (a) New York %s per 5 C of the preceding night's minimum, inside the predicted 0.98 to 1.08; the lower limit is below 1.00 and the upper limit is above the "
        "refutation threshold %.3f, so neither rule is met. Chicago %s, inside the predicted 0.98 to 1.06; neither rule met (threshold %.3f); replication inconclusive. "
        "(b) New York night %s and day %s, ratio of ratios %s: the night ratio is below the predicted 1.08 to 1.20, and the two are not separated. Chicago night %s and day %s, "
        "ratio of ratios %s: both inside the predicted ranges, not separated."
        % (f(pa["primary"]), ny["scored"]["refute_threshold"], f(ca["primary"]), ch["scored"]["refute_threshold"],
           f(pb["n_night"]), f(pb["n_day"]), f(pb["night_over_day_ratio_of_ratios"]),
           f(cb["n_night"]), f(cb["n_day"]), f(cb["night_over_day_ratio_of_ratios"]))),
    "settle": ("Hourly temperature (airport hourly observations) matched to shootings by hour would say whether shootings in the small hours follow the temperature of that hour. "
               "A sleep path needs a nightly sleep measure; the weather record cannot isolate it, and an effect of the size the graph's findings imply (about 1.01 per 5 C) is "
               "below what twenty years of one city's shootings can detect."),
    "research_needed": [
        {"question": "Do shootings between midnight and 06:00 follow the temperature of that hour, at a fixed maximum of the day before?",
         "data": "Hourly airport temperature and humidity (NOAA ISD or LCD) with shootings by hour, several cities",
         "design": "Hourly case-crossover or distributed-lag model; register the 00:00 to 05:59 block as the primary", "priority": "high"},
        {"question": "How many minutes of sleep are lost per degree of outdoor night temperature in housing without air conditioning?",
         "data": "Wearable sleep panels linked to location and housing; indoor temperature loggers",
         "design": "Within-person panel; the graph holds no such finding", "priority": "medium"}],
    "figures": ["figures/round5/heat_night_minimum.png"],
    "notes": (
        "Registered secondary results. The following night's minimum (TMIN of d+1), not the preceding one, carries a rate ratio above 1 on hot days: New York %s, Chicago %s; "
        "with both minima in the model the preceding night is %s and %s and the following night %s and %s. For night shootings the following-night ratio is %s and %s; for day "
        "shootings %s and %s. By six-hour block, the interval of the ratio 33 against 27 C excludes 1 only from 00:00 to 05:59: New York %s, Chicago %s; from 18:00 to 23:59 it is %s and %s. "
        "In the all-day spline model with both minima, the 33 against 27 C ratio is %s in New York and %s in Chicago. "
        "On shooting days (06:00 to 05:59) the 33 against 27 C ratio for all shootings is %s in New York and %s in Chicago, smaller than on calendar days. "
        "Exploratory, after the results (analyses/round5/heat_night/exploratory.py): on calendar-day counts the same data give %s and %s, so in New York about half of the "
        "published hot-day excess comes from shootings before 06:00 on the hot date, which precede that day's maximum. The pooled two-city estimate for the preceding night is %s. "
        "The composed graph prediction, 1.012 (1.000 to 1.031), lies inside both cities' intervals, and so does 1.00; the test does not discriminate (D 0.13 and 0.37)."
        % (f(pa["secondary"]["following_only"]), f(ca["secondary"]["following_only"]),
           f(pa["secondary"]["both_nights_preceding"]), f(ca["secondary"]["both_nights_preceding"]),
           f(pa["secondary"]["both_nights_following"]), f(ca["secondary"]["both_nights_following"]),
           f(pa["secondary"]["n_night_following"]), f(ca["secondary"]["n_night_following"]),
           f(pa["secondary"]["n_day_following"]), f(ca["secondary"]["n_day_following"]),
           f(pb["block_00-06"]), f(cb["block_00-06"]), f(pb["block_18-24"]), f(cb["block_18-24"]),
           f(pb["excess_with_both_tmin"]["rr_33_vs_27"]), f(cb["excess_with_both_tmin"]["rr_33_vs_27"]),
           f(pb["n"]), f(cb["n"]), f(x["new_york"]["calendar_day_33_vs_27"]), f(x["chicago"]["calendar_day_33_vs_27"]),
           f(r["pooled_two_cities"]))),
}
print(claims.outcome(rec))
print(rec["prediction_scored"]); print(rec["notes"])
