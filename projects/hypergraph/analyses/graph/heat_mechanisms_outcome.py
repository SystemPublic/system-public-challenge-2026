"""Write the outcomes of heat-mech-outdoors and heat-mech-intox from city_results.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

D = ROOT / "data" / "derived" / "graph" / "heat_mechanisms"
R = json.loads((D / "city_results.json").read_text())
S = json.loads((D / "city_sources.json").read_text())
X = json.loads((D / "exploratory_hot_end.json").read_text())
GRAPH_SRC = {"kind": "system-public-graph", "api": "v1.0", "fetched": "2026-11-12",
             "note": "responses cached in data/cache/sysgraph; derived tables in data/derived/graph/heat_mechanisms/"}
FIGS = ["figures/graph/heat_mechanisms_paths.png", "figures/graph/heat_mechanisms_curves.png"]


def e3(e):
    return f"{e['estimate']:.3f} ({e['lo']:.3f} to {e['hi']:.3f})"


def A(r):
    return f"{r['attenuation']:.3f} ({r['attenuation_lo']:.3f} to {r['attenuation_hi']:.3f})"


def eff(key, label):
    p = R[key]["primary"]
    return {"label": label, "estimate": p["attenuation"], "lo": p["attenuation_lo"], "hi": p["attenuation_hi"],
            "scale": "share of the log IRR of shootings per 5 C removed by adding the proxy", "null": 0, "n": p["n_days"]}


def sens(key):
    r = R[key]
    return ("year-by-month terms " + A(r["s1_year_by_month"]) + f"; without 2020-2021 {r['s2_excl_2020_2021']['attenuation']:.3f}; "
            f"May-September {r['s3_warm_season']['attenuation']:.3f}; proxy lagged one day {r['s4_mediator_lag1']['attenuation']:.3f}")


n, b, dr, ed, dk, sc = R["noise_street"], R["bike"], R["ems_drug"], R["ems_edp"], R["drinking311"], R["shootings_curve"]

outdoors = {
    "id": "heat-mech-outdoors",
    "verdict": "confirmed",
    "city_effect": eff("noise_street", "Attenuation of the heat-shootings slope by daily 311 Noise - Street/Sidewalk complaints, 2010-2026"),
    "graph_effect": {"label": "Walking practice per 1 C of daily maximum temperature, Kim 2022 (rural Korea); the graph's only signed "
                              "finding on heat and being outdoors", "estimate": 0.95, "lo": 0.94, "hi": 0.97, "scale": "OR per 1 C", "null": 1},
    "sources": S["shootings_weather"] + S["c311"] + S.get("bike", []) + [GRAPH_SRC],
    "prediction_scored": (
        f"partial. First link hit: street noise complaints IRR {e3(n['first_link']['irr_per_5C'])} per 5 C, inside the registered "
        f"1.15 to 1.45. Hot-end flattening hit: from 27 to 33 C complaints change by {e3(n['first_link']['rr_33_vs_27'])} and bicycle "
        f"counts by {e3(b['first_link']['rr_33_vs_27'])}, against {e3(n['first_link']['rr_21_vs_15'])} and "
        f"{e3(b['first_link']['rr_21_vs_15'])} from 15 to 21 C; shootings rise {e3(sc['rr_33_vs_27'])} from 27 to 33 C. Attenuation "
        f"miss on the high side: A = {A(n['primary'])}, above the registered 0.10 to 0.35."),
    "settle": ("Whether the noise proxy carries people outdoors or a common cause of complaints and shootings needs a direct count of "
               "people on residential streets in the evening (pedestrian counters away from commuter routes, or mobility traces), and "
               "NYPD shootings split by indoor and outdoor location and by hour. The bicycle counts, which measure travel, remove none "
               "of the slope."),
    "research_needed": [
        {"question": "Does heat raise shootings above 27 C through anything other than the number of people outdoors?",
         "data": "NYPD shootings by hour and inside/outside; night-time minimum temperature; pedestrian counts on residential streets",
         "design": "Daily model with separate slopes below and above 27 C; outdoor versus indoor incidents; previous-night minimum temperature given the day's maximum", "priority": "high"},
        {"question": "Does more street activity on a given day raise violence on that day, at fixed temperature?",
         "data": "Any city with pedestrian counters or mobility traces and daily violence records",
         "design": "Daily panel with weather held fixed; the System Public Graph holds no such finding, only crime reducing walking", "priority": "high"},
        {"question": "Do people sleep worse on hot nights at the population level, and does aggression follow the next day?",
         "data": "Wearable sleep records by city and date; violence records",
         "design": "Two-stage daily design; the graph counts 8 temperature-sleep quality findings but its API returns none", "priority": "medium"}],
    "figures": FIGS,
    "notes": (
        f"Verdict by the registered rule: the proxy rises with temperature, its coefficient in the shootings model is positive "
        f"({n['primary']['mediator_coef_log1p']['estimate']:.3f}, {n['primary']['mediator_coef_log1p']['lo']:.3f} to "
        f"{n['primary']['mediator_coef_log1p']['hi']:.3f} per unit of log complaints), A = {A(n['primary'])} on {n['primary']['n_days']} days, "
        f"and the year-by-month sensitivity stays above 0.25. Shootings IRR per 5 C falls from {e3(n['primary']['base_irr_per_5C'])} to "
        f"{e3(n['primary']['adjusted_irr_per_5C'])}. Sensitivity: {sens('noise_street')}. The secondary proxy disagrees: bicycle counts "
        f"(IRR {e3(b['first_link']['irr_per_5C'])} per 5 C, {b['primary']['n_days']} days from 2014) give A = {A(b['primary'])}. 311 public "
        f"drinking complaints, registered under heat-mech-intox, also rise with heat (IRR {e3(dk['first_link']['irr_per_5C'])}) and give "
        f"A = {A(dk['primary'])}. So a series that rises with heat does not by that fact remove the slope; the noise complaints share "
        f"day-to-day variation with shootings that the other two series lack. This is mediation by proxy. Exploratory, run after the "
        f"outcome: with a spline of temperature, adding the noise proxy lowers the rise in shootings from 15 to 21 C from "
        f"{e3(X['without_proxy']['rr_21_vs_15'])} to {e3(X['with_proxy']['rr_21_vs_15'])} and from 21 to 27 C from "
        f"{e3(X['without_proxy']['rr_27_vs_21'])} to {e3(X['with_proxy']['rr_27_vs_21'])}, and leaves the rise from 27 to 33 C unchanged "
        f"({e3(X['without_proxy']['rr_33_vs_27'])} and {e3(X['with_proxy']['rr_33_vs_27'])}). Bicycle panel sensors per year: "
        f"{R['bike_panel_sensors_by_year']}."),
}

intox = {
    "id": "heat-mech-intox",
    "verdict": "unsettled",
    "city_effect": eff("ems_drug", "Attenuation of the heat-shootings slope by daily EMS drug and alcohol dispatches, 2006-2026"),
    "graph_effect": {"label": "ED visits for substance use disorders on extreme heat days, Nori-Sarma 2022 (US adults)", "estimate": 1.08,
                     "lo": 1.07, "hi": 1.10, "scale": "IRR, extreme heat day vs reference", "null": 1},
    "sources": S["shootings_weather"] + S["ems"] + S["c311"] + [GRAPH_SRC],
    "prediction_scored": (
        f"partial. First link hit: DRUG dispatches IRR {e3(dr['first_link']['irr_per_5C'])} per 5 C, inside the registered 1.01 to 1.06. "
        f"Attenuation miss: A = {A(dr['primary'])}, above the registered ceiling of 0.10 and below the 0.25 that would contest the "
        f"claim, so neither registered condition is met."),
    "settle": ("Toxicology of shooting victims and arrested shooters by day and temperature (the design of Marzuk et al. 1998, which "
               "found no change in the cocaine-positive share of New York homicide victims on hot days), or alcohol sales by day."),
    "research_needed": [
        {"question": "Do people in New York drink more on hot days, and are shooting victims more often intoxicated on hot days?",
         "data": "Medical examiner toxicology by date; daily alcohol sales or wastewater ethanol markers",
         "design": "Repeat Marzuk et al. 1998 for alcohol and for 2006-2026; the graph's only temperature-alcohol finding compares countries",
         "priority": "medium"}],
    "figures": FIGS,
    "notes": (
        f"EMS drug and alcohol dispatches (mean {dr['first_link']['mean_per_day']:.0f} per day) rise {e3(dr['first_link']['irr_per_5C'])} per "
        f"5 C and keep rising at the hot end ({e3(dr['first_link']['rr_33_vs_27'])} from 27 to 33 C). Adding them lowers the shootings IRR "
        f"from {e3(dr['primary']['base_irr_per_5C'])} to {e3(dr['primary']['adjusted_irr_per_5C'])}. Sensitivity: {sens('ems_drug')}. The "
        f"share falls to {dr['s4_mediator_lag1']['attenuation']:.3f} when the proxy is taken from the previous day, so the association is "
        f"between dispatches and shootings on the same day. Secondary proxies: psychiatric dispatches rise "
        f"{e3(ed['first_link']['irr_per_5C'])} per 5 C and give A = {A(ed['primary'])}, with a negative coefficient in the shootings model; "
        f"311 public drinking complaints rise {e3(dk['first_link']['irr_per_5C'])} per 5 C and give A = {A(dk['primary'])}. The call type "
        f"DRUG does not separate alcohol from other drugs, and dispatches may partly measure people in public view."),
}

if __name__ == "__main__":
    for rec in (outdoors, intox):
        print(claims.outcome(rec).relative_to(ROOT))
