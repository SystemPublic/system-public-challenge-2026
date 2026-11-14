"""Write the outcomes of heat-ac-shootings, heat-ac-heat-calls and heat-school-out from results.json.
The registered conditions are applied literally."""
import json

from analyses.heat_solutions.common import DER, ROOT
from concord import claims

R = json.loads((DER / "results.json").read_text())
X = json.loads((DER / "exploratory.json").read_text())
SRC = json.loads((DER / "sources.json").read_text())
REG = {i: json.loads((ROOT / f"claims/registered/{i}.json").read_text()) for i in ("heat-ac-shootings", "heat-ac-heat-calls", "heat-school-out")}
FIGS = ["figures/heat_solutions/heat_solutions.png"]
f = lambda v, n=3: f"{v['estimate']:.{n}f} ({v['lo']:.{n}f} to {v['hi']:.{n}f})"
DEV = ("One line of run.py was changed after registration and before any result existed: the hour of a shooting is now read as the text before the first colon, "
       "because some times in the file are not zero-padded and the registered line stopped with an error at that point. No model had run.")


def verdict(v, null, yard):
    if v["lo"] > null:
        return "confirmed"
    if v["hi"] < yard and v["lo"] <= null:
        return "contested"
    return "unsettled"


A, B, S = R["heat_ac_shootings"], R["heat_ac_heat_calls"], R["heat_school_out"]
ya = REG["heat-ac-shootings"]["can_it_fail"]["yardstick_half"]
yb = REG["heat-ac-heat-calls"]["can_it_fail"]["yardstick"]
pa, pb, ps = A["primary_low_vs_high_half"], B["primary_low_vs_high_half"], S["primary_out_of_school_irr"]
va, vb, vs = verdict(pa, 0, ya), verdict(pb, 0, yb), verdict(ps, 1.0, 1.10)
print(va, vb, vs)

claims.outcome({
    "id": "heat-ac-shootings", "verdict": va,
    "verdict_note": ("Confirmed by the registered rule: the heat slope of shootings is steeper in the low-AC half of districts over the whole year. The difference comes from days below 27 C, "
                     "when air conditioners are not in use, and reverses above 27 C, so the result is not evidence that air conditioning reduces shootings."),
    "city_effect": {"label": "Difference between the log rate ratios of shootings per 5 C of TMAX, low-AC half minus high-AC half of community districts, 2006-2026",
                    "estimate": pa["estimate"], "lo": pa["lo"], "hi": pa["hi"], "scale": "difference of log rate ratios per 5 C", "null": 0, "n": pa["days"]},
    "graph_effect": None, "graph_evidence": REG["heat-ac-shootings"]["graph_evidence"],
    "sources": [SRC[0], SRC[3]] + [{"kind": "ehdp", "file": "hvi-nta-2020.csv", "repository": "github.com/nychealth/EHDP-data", "commit": "547482b9df589006543e13e8cdf6546e00ed9998"}],
    "prediction_scored": (f"partial. The difference is {f(pa)}; the predicted range was -0.02 to +0.05 with a best guess of +0.01, and the registrant gave 'confirmed' a probability of 0.2. "
                          f"The lower limit is above 0, so the support rule is met. The estimate is close to the size expected if households without air conditioning carried half the slope ({ya:.3f})."),
    "settle": ("Shootings by census tract or block with the tract's housing type and air-conditioning share (the Housing and Vacancy Survey microdata give it by sub-borough and building type), "
               "and a temperature measured in the district. A design with a change in air conditioning over time is needed to say anything causal: residential electricity by ZIP code and month "
               "(New York State Utility Energy Registry, 2016 on) gives a yearly measure of cooling use per account that could serve."),
    "research_needed": [
        {"question": "Does the heat slope of shootings in a ZIP code fall in years when its summer residential electricity use per account rises?", "data": "Utility Energy Registry monthly ZIP electricity (data.ny.gov tzb9-c2c6, g2x3-izm4); NYPD shootings by coordinates",
         "design": "ZIP by year panel of summer slopes on the ratio of July-August to April-May residential use per account, ZIP and year fixed", "priority": "medium"},
        {"question": "Why is the slope of shootings below 27 C steeper in low-AC, low-income districts?", "data": "Shootings by location type and hour; 311 street-noise complaints by district", "design": "The outdoor-activity proxies of heat-mech-outdoors by district half", "priority": "medium"}],
    "figures": FIGS,
    "notes": (DEV + f" Registered secondary results. Rate ratios per 5 C: low-AC half {f(A['slopes_by_half']['low'])}, high-AC half {f(A['slopes_by_half']['high'])}. Bottom against top third {f(A['terciles_bottom_vs_top'])}. "
              f"Within the low-income half {f(A['low_income_districts_only'])}; within the high-income half {f(A['high_income_districts_only'])}. Shootings between 00:00 and 05:59 {f(A['hours_00_to_06'])}. "
              f"Days with TMAX of 27 C or more {f(A['days_tmax_27_or_more'])}: on hot days the slope is steeper in the HIGH-AC half. May to September {f(A['warm_season'])}. 2006 to 2019 {f(A['2006_2019'])}; 2020 to 2026 {f(A['2020_2026'])}. "
              f"District slopes on air-conditioning share per 10 points: {f(A['district_slopes_on_ac_per_10_points']['ac_only']['ac10'])} alone and {f(A['district_slopes_on_ac_per_10_points']['ac_and_income']['ac10'])} with income, {A['district_slopes_on_ac_per_10_points']['n_districts']} districts. "
              f"Housing Bureau jurisdiction against other incidents {f(A['housing_jurisdiction_vs_other'])}, within the low-AC half {f(A['housing_vs_other_within_low_ac_districts'])}. Public-housing buildings against other apartment buildings {f(A['public_housing_building_vs_apartment_building'])}. "
              f"Exploratory, after the results: in one piecewise model the difference is {f(X['shootings_piecewise']['below_27'])} per 5 C below 27 C and {f(X['shootings_piecewise']['above_27'])} above 27 C. "
              f"Leaving out one borough at a time gives 0.038 to 0.052, with the lower limit at or below 0 without the Bronx, Brooklyn or Queens. The public-housing building contrast is {f(X['public_housing_building_vs_apartment_piecewise']['below_27'])} below 27 C and {f(X['public_housing_building_vs_apartment_piecewise']['above_27'])} above; "
              f"shootings at other apartment buildings have a flat slope ({f(X['building_slopes']['apt'])}) and the location field is blank for about half of incidents."),
})

claims.outcome({
    "id": "heat-ac-heat-calls", "verdict": vb,
    "verdict_note": ("Contested by the registered refutation rule: the heat slope of ambulance calls coded HEAT does not differ between the halves, and the interval excludes the difference expected if all calls came from homes. "
                     "Calls are located where the patient was found, so this does not show that air conditioning fails to protect at home."),
    "city_effect": {"label": "Difference between the log rate ratios of EMS HEAT calls per 5 C of TMAX, low-AC half minus high-AC half of community districts, May-September 2006-2026",
                    "estimate": pb["estimate"], "lo": pb["lo"], "hi": pb["hi"], "scale": "difference of log rate ratios per 5 C", "null": 0, "n": pb["days"]},
    "graph_effect": {"label": "Difference expected from the case-control odds of heat death with a working air conditioner (0.23; Naughton 2002, Semenza 1996), if every call came from a home", "estimate": yb, "lo": None, "hi": None,
                     "scale": "difference of log rate ratios per 5 C", "null": 0},
    "graph_evidence": REG["heat-ac-heat-calls"]["graph_evidence"],
    "sources": [SRC[2], SRC[3]] + [{"kind": "ehdp", "file": "hvi-nta-2020.csv", "repository": "github.com/nychealth/EHDP-data", "commit": "547482b9df589006543e13e8cdf6546e00ed9998"}],
    "prediction_scored": (f"miss. The difference is {f(pb)}; the predicted range was 0 to +0.12. The upper limit is below the yardstick {yb:.3f} and the lower limit is below 0, so the refutation rule is met. "
                          "Joint reading as registered: this claim is not confirmed, so the answer to whether low-AC districts have steeper slopes for both outcomes is 'the data cannot tell'; for heat calls alone the answer is no."),
    "settle": ("Heat illness by place of residence. The Health Department holds daily syndromic ED visits with the patient's ZIP code; the public file is citywide. EMS records with a location type (home, street, workplace) would separate the calls that household air conditioning can affect."),
    "research_needed": [
        {"question": "Is the heat slope of heat-illness ED visits by ZIP code of residence steeper where fewer households have air conditioning?", "data": "DOHMH syndromic surveillance by residence ZIP (not public); Housing and Vacancy Survey", "design": "Daily case-crossover by ZIP with air conditioning and income as effect modifiers", "priority": "high"},
        {"question": "What share of EMS HEAT calls come from homes?", "data": "FDNY EMS dispatch records with location type", "design": "Tabulation by temperature band", "priority": "medium"}],
    "figures": FIGS,
    "notes": (DEV + f" {B['n_events_in_districts']} calls in May to September on {pb['days']} days with at least one call. Registered secondary results. Bottom against top third {f(B['terciles_bottom_vs_top'])}. "
              f"Within the low-income half {f(B['low_income_districts_only'])}; within the high-income half {f(B['high_income_districts_only'])}. Days with TMAX of 27 C or more {f(B['days_tmax_27_or_more'])}. "
              f"Without the six Manhattan districts below 59th Street {f(B['without_manhattan_below_59th_street'])}: the slope is flatter in the low-AC half. District slopes on air-conditioning share per 10 points: "
              f"{f(B['district_slopes_on_ac_per_10_points']['ac_only']['ac10'])} alone, {f(B['district_slopes_on_ac_per_10_points']['ac_and_income']['ac10'])} with income, {B['district_slopes_on_ac_per_10_points']['n_districts']} districts. "
              f"The registered negative binomial fit of the high-AC half's own slope returned a degenerate interval (2.335 to 2.335) and is not used; an exploratory Poisson refit gives {f(X['heat_call_slopes_poisson']['low'])} for the low-AC half and {f(X['heat_call_slopes_poisson']['high'])} for the high-AC half. "
              f"{100 * B['share_of_all_heat_calls_in_may_to_september']:.0f}% of HEAT calls fall in May to September."),
})

b = REG["heat-school-out"]["composed_prediction"]
claims.outcome({
    "id": "heat-school-out", "verdict": vs,
    "verdict_note": (f"Unsettled by a margin of 0.003: the lower limit of the rate ratio is {ps['lo']:.3f} against the threshold 1.00 (rule 10). The point estimate is a 10% rise, above the predicted range. "
                     "The rise is the same for victims over 25 as for victims under 18, so it may be the season and not the school calendar."),
    "city_effect": {"label": "Rate ratio of shooting incidents, weekdays out of school against school weekdays at the same temperature, within 42 days of the last or first day of classes, 2006-2026",
                    "estimate": ps["estimate"], "lo": ps["lo"], "hi": ps["hi"], "scale": "rate ratio", "null": 1, "n": ps["weekdays"]},
    "graph_effect": None, "graph_evidence": REG["heat-school-out"]["graph_evidence"],
    "sources": [SRC[0], SRC[1], SRC[3]],
    "prediction_scored": (f"miss. The rate ratio is {f(ps)} on {ps['weekdays']} weekdays and {ps['shootings']} shootings; the predicted range was 0.95 to 1.08. Neither rule is met: the lower limit is at or below 1.00 and the upper limit is above 1.10."),
    "settle": ("Cities whose school years end on different dates give the same calendar day in and out of school at the same season; a pooled test over several cities would separate school from season. "
               "Within New York the first day of classes moves between 2 and 13 September, which gives too few days."),
    "research_needed": [
        {"question": "Do shootings rise on the day school ends in cities with different term dates, at the same day of the year and temperature?", "data": "Shooting incidents and school calendars for Chicago, Philadelphia, Los Angeles, Baltimore", "design": "Stacked regression discontinuity in time with day-of-year terms shared across cities", "priority": "high"},
        {"question": "Is the after-midnight excess during the recess specific to weekdays?", "data": "NYPD shootings by hour", "design": "The same window with Friday and Saturday nights as the comparison", "priority": "medium"}],
    "figures": FIGS,
    "notes": (DEV + f" Registered secondary results. Window of 21 days {f(S['window_21_days'])}. Quadratic trends {f(S['quadratic_trends'])}. End of term only {f(S['end_of_term_only'])}; start of term only {f(S['start_of_term_only'])}. "
              f"Victims under 18 {f(S['victims_u18'])} ({S['victims_u18']['victims']} victims, to 2024); 18 to 24 {f(S['victims_a1824'])}; 25 or older {f(S['victims_a25'])}. Odds that a victim is under 18 on days out of school {f(S['under_18_share_odds_ratio'])}. "
              f"The heat-shootings model on all days: {f(S['heat_slope_without_recess_term'])} per 5 C without a term for the summer recess and {f(S['heat_slope_with_recess_term'])} with it; the term itself is {f(S['recess_term_irr'])} and removes "
              f"{100 * S['share_of_log_slope_removed']:.1f}% of the log slope. The arithmetic done before registration gave the same answer: {b['arithmetic']} "
              f"Exploratory, after the results, by hour block with temperature held fixed: 00:00 to 05:59 {f(X['school_by_hour_block']['00-05'])}; 06:00 to 14:59 {f(X['school_by_hour_block']['06-14'])}; "
              f"15:00 to 19:59 {f(X['school_by_hour_block']['15-19'])}; 20:00 to 23:59 {f(X['school_by_hour_block']['20-23'])}."),
})
