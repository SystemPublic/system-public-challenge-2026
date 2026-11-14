"""Register heat-ac-shootings, heat-ac-heat-calls and heat-school-out. Run once, after design.py and before run.py."""
import hashlib
import json
import math

import pandas as pd

from analyses.heat_solutions.common import DER, ROOT
from concord import claims

D = json.loads((DER / "prereg_design.json").read_text())
G = json.loads((DER / "graph.json").read_text())
sha = {f: hashlib.sha256((ROOT / "analyses/heat_solutions" / f).read_bytes()).hexdigest()[:16] for f in ("run.py", "common.py")}
r3 = lambda x: round(float(x), 3)
S, E, SC = D["shootings_ac"], D["heat_calls_ac"], D["school"]
h = S["halves"]
c = pd.read_csv(DER / "design_cd_counts.csv")
u = 100 - c["ac"]
u_low = float((u * c.heat_calls)[c.low_ac == 1].sum() / c.heat_calls[c.low_ac == 1].sum()) / 100
u_high = float((u * c.heat_calls)[c.low_ac == 0].sum() / c.heat_calls[c.low_ac == 0].sum()) / 100
RR_NOAC = 1 / 0.23          # a working air conditioner: odds of heat death 0.2 to 0.3 (Naughton 2002, Semenza 1996); 0.23 taken
hot_ratio = math.log((1 + (RR_NOAC - 1) * u_low) / (1 + (RR_NOAC - 1) * u_high))
YARD_CALLS = hot_ratio / 2  # the contrast between a mild and a hot day spans about 10 C, two units of TMAX/5
YARD_SHOOT = h["diff_if_no_ac_households_carry_half"]
SCRIPT = (f"Script: analyses/heat_solutions/run.py (sha256 {sha['run.py']}) with analyses/heat_solutions/common.py (sha256 {sha['common.py']}), committed with this "
          "registration and run unchanged. No resampling and no random numbers; all intervals are Wald intervals from HC0 standard errors (rule 9). "
          "The script was exercised before registration on simulated records only (--simulate, seed 1). ")
AC_DATA = ("Air conditioning: percent of households with air conditioning by community district, from the Health Department's Heat Vulnerability Index file "
           "(EHDP-data hvi-nta-2020.csv, from the Housing and Vacancy Survey; the value is constant or nearly constant within a district). "
           f"The 59 districts are split at the median ({r3(D['ac_table']['ac_median'])}%): the low half averages {r3(D['ac_table']['ac_mean_low'])}% and the high half {r3(D['ac_table']['ac_mean_high'])}%. ")
SEEN_COMMON = ("design.py read the coordinates and jurisdiction code of shooting incidents without their dates and the count of EMS HEAT incidents by district and by year, "
               "to count events per district; it read no dated record at district level. No model, table or query of shootings or EMS calls by district and date exists in the repository. ")


def gsum(term, kind):
    rows = [r for r in G[term]["associations"] if r[kind]]
    return len(rows), sorted({r["pubmed_id"] for r in rows if r["pubmed_id"]})


ac_heat_n, ac_heat_pm = gsum("air conditioner", "heat_or_death")
graph_ac = [
    {"association_id": "variables searched by name: air conditioning, air conditioner", "concepts": ["air conditioning (variable names)", "violence, crime, aggression, injury"],
     "n_findings": 0, "n_studies": 0, "direction": "0",
     "summary": (f"{G['air conditioning']['variables_returned']} and {G['air conditioner']['variables_returned']} variables match; none of their associations has a violence, crime, aggression or "
                 "shooting variable on the other side. The graph holds nothing on air conditioning and violence."), "pubmed_ids": []},
    {"association_id": "variables searched by name: air conditioner", "concepts": ["working air conditioner at home", "heat-related death or hospital admission"],
     "n_findings": ac_heat_n, "n_studies": 4, "direction": "-",
     "summary": ("Case-control studies of heat waves: odds of heat-related death with a working air conditioner 0.2 (0.1 to 0.7) in Chicago 1999 (Naughton 2002), 0.3 in Chicago 1995 "
                 "(Semenza 1996), 0.03 (0 to 0.2) in Cincinnati 1999 (Kaiser 2001); odds of heat-related hospital admission with an air conditioner in the bedroom 0.12 (0.02 to 0.74) in "
                 "Adelaide 2009 (Zhang 2016). The four abstracts were read in PubMed and match. A fifth record (Saito 2019, 'no air conditioner', HR 1.71) is wrong: the abstract gives 1.71 for a "
                 "deprivation index, not for air conditioning."), "pubmed_ids": [11988377, 8649494, 11563746, 27256088, 30634562]},
]

rec_a = {
    "id": "heat-ac-shootings",
    "kind": "confirmation",
    "statement": ("The rise of shootings with daily maximum temperature is steeper in the New York community districts where fewer households have air conditioning than in the districts "
                  "where more have it."),
    "graph_evidence": graph_ac,
    "graph_evidence_note": "Collected on 13 November 2026 by analyses/heat_solutions/graph.py (variable-name search, API only); data/derived/heat_solutions/graph.json.",
    "literature": [{"citation": "Heilmann K, Kahn ME, Tang CK. The urban crime and heat gradient in high and low poverty areas. J Public Econ 2021;197:104408.", "doi": "10.1016/j.jpubeco.2021.104408",
                    "finding": "Los Angeles: heat raises violent crime more in poorer neighbourhoods and in older housing; cited from memory, not re-read."}],
    "prediction": {
        "direction": "+",
        "magnitude": ("Difference between the log rate ratios per 5 C of the low-AC half and the high-AC half of districts: between -0.02 and +0.05, best guess +0.01. "
                      f"The citywide log rate ratio is 0.136 (1.146 per 5 C). If households without air conditioning carried half of it, the difference would be {r3(YARD_SHOOT)}; if all of it, {r3(2 * YARD_SHOOT)}."),
        "support_if": "The 95% lower limit of the difference is above 0. This alone decides 'confirmed'.",
        "refute_if": (f"The 95% upper limit is below {r3(YARD_SHOOT)} and the lower limit is at or below 0. {r3(YARD_SHOOT)} is the difference expected if households without air conditioning "
                      f"carried half of the citywide slope: slope of a group = 0.136 x (0.5 + 0.5 x u_g / u), with u_g the share of households without air conditioning "
                      f"({r3(h['no_ac_share_low_group_pct'])}% in the low half, {r3(h['no_ac_share_high_group_pct'])}% in the high half, {r3(h['no_ac_share_all_pct'])}% overall, weighted by shootings)."),
        "otherwise": "Unsettled.",
        "secondary_registered": ("Reported, not deciding: the two halves' own rate ratios; bottom against top third of districts; the same contrast within the low-income half and within the "
                                 "high-income half of districts (income is the rival); shootings between 00:00 and 05:59; days with TMAX of 27 C or more; May to September; 2006 to 2019 and 2020 to 2026; "
                                 "a weighted regression of each district's own heat slope (districts with 150 or more incidents) on its air-conditioning share, alone and with log median income; "
                                 "incidents under Housing Bureau jurisdiction (public housing) against all others, citywide and within the low-AC half; incidents at public-housing buildings against "
                                 "those at other apartment buildings (location_desc)."),
    },
    "plan": (SCRIPT + AC_DATA +
             "Outcome: NYPD shooting incidents 5ucz-vwe8, one row per incident_key, 2006-01-01 to 2026-08-31, assigned to a community district from their coordinates "
             "(the file holds latitude and longitude in swapped columns for most rows; common.fix_latlon restores them). Temperature: Central Park GHCN-Daily TMAX. "
             "Model: binomial GLM, logit link, of the day's incidents in the low-AC half out of the day's incidents in all districts, on TMAX/5 and the calendar terms of heat-shootings "
             "(C(dow) + C(month) + C(year) + hol + wet). Each district is compared with itself across days, so the level of violence in a district does not enter; the coefficient of TMAX/5 "
             "is the difference between the two halves' log rate ratios per 5 C."),
    "can_it_fail": {"source": "data/derived/heat_solutions/prereg_design.json (analyses/heat_solutions/design.py)",
                    "expected_se": h["se_diff_log_rr_per_5c"], "smallest_detectable_difference_80pct": h["mde_80pct"], "yardstick_half": YARD_SHOOT, "D_half": h["D_half"],
                    "p_refute_if_no_difference": h["p_refute_if_no_difference"], "p_support_if_half": h["p_support_if_half"],
                    "low_income_half_only": {k: S["low_income_districts_only"][k] for k in ("events", "share_in_low_ac", "se_diff_log_rr_per_5c", "D_half")},
                    "reading": (f"Expected standard error {r3(h['se_diff_log_rr_per_5c'])}; D for the half-carry difference is {r3(h['D_half'])} (rule 8 needs 4). With no true difference the refutation "
                                f"rule is met with probability {r3(h['p_refute_if_no_difference'])} and the support rule with 0.025. The contrast within low-income districts has D of "
                                f"{r3(S['low_income_districts_only']['D_half'])} and cannot decide anything; it is reported only.")},
    "already_seen": ("The citywide slope (1.146 per 5 C), its shape, its hours and the night-minimum results. " + SEEN_COMMON +
                     f"From the undated coordinates I know that {r3(h['share_in_low_ac'])} of mapped incidents fall in the low-AC half and that {S['jurisdiction_counts'].get('2')} incidents are under Housing Bureau jurisdiction."),
    "alternatives": [
        f"Income: air conditioning and median income have a Spearman correlation of {r3(D['ac_table']['spearman_ac_income'])} across districts, and {D['ac_table']['low_ac_and_low_income']} of the 29 low-AC districts are in the low-income half. A steeper slope in low-AC districts may be a steeper slope in poor districts for any reason (street life, housing density, policing).",
        "Place of occurrence is not place of residence; a shooting is assigned to where it happened.",
        "The survey measures whether a household has an air conditioner, not whether it runs it; households that cannot pay for electricity are counted as having one.",
        "A district is large (about 140,000 residents) and the contrast between halves is 8 percentage points of households, so an effect confined to households without air conditioning must be large to appear.",
        "Temperature is measured at one station; low-AC districts are also hotter at street level, which would steepen their slope without any role for air conditioning."],
    "prior": 0.2,
    "prior_note": "Probability of 'confirmed'. About 0.45 for refuted and 0.35 for unsettled.",
    "registrant": "Claude (heat solutions agent)",
}

rec_b = {
    "id": "heat-ac-heat-calls",
    "kind": "confirmation",
    "statement": ("The rise of ambulance calls for heat illness with daily maximum temperature is steeper in the New York community districts where fewer households have air conditioning "
                  "than in the districts where more have it."),
    "graph_evidence": graph_ac[1:],
    "graph_evidence_note": rec_a["graph_evidence_note"],
    "literature": [{"citation": "Madrigano J, Ito K, Johnson S, Kinney PL, Matte T. A case-only study of vulnerability to heat wave-related mortality in New York City (2000-2011). Environ Health Perspect 2015;123:672-678.",
                    "doi": "10.1289/ehp.1408178", "finding": "Deaths during heat waves were more likely among Black residents, at home, and in census tracts with more public assistance and less green space; cited from memory, not re-read."}],
    "prediction": {
        "direction": "+",
        "magnitude": (f"Difference between the log rate ratios per 5 C of the low-AC half and the high-AC half: between 0 and +0.12, best guess +0.04. If every call came from a home and "
                      f"homes without air conditioning had {r3(RR_NOAC)} times the rate on hot days (odds 0.23 with a working air conditioner), the hot-day log ratio between the halves would be "
                      f"{r3(hot_ratio)} and the difference per 5 C about {r3(YARD_CALLS)}."),
        "support_if": "The 95% lower limit of the difference is above 0. This alone decides 'confirmed'.",
        "refute_if": (f"The 95% upper limit is below {r3(YARD_CALLS)} and the lower limit is at or below 0. {r3(YARD_CALLS)} = 0.5 x ln[(1 + (RR - 1) u_low) / (1 + (RR - 1) u_high)], RR = 1/0.23, "
                      f"u_low = {r3(u_low)} and u_high = {r3(u_high)} the shares of households without air conditioning in the two halves weighted by calls; the factor 0.5 spreads the hot-day contrast over 10 C."),
        "otherwise": "Unsettled.",
        "secondary_registered": ("Reported, not deciding: the two halves' own rate ratios; bottom against top third; within the low-income half and within the high-income half; days with TMAX of 27 C or more; "
                                 "without the six Manhattan districts below 59th Street, where visitors and workers outnumber residents by day; a weighted regression of each district's own slope "
                                 "(100 or more calls) on its air-conditioning share, alone and with log median income."),
        "joint_reading_registered": ("The question whether low-AC districts have steeper slopes for BOTH shootings and heat illness is answered 'yes' only if this claim and heat-ac-shootings are both confirmed, "
                                     "'no for shootings only' if this claim is confirmed and heat-ac-shootings is refuted, and otherwise 'the data cannot tell'."),
    },
    "plan": (SCRIPT + AC_DATA +
             "Outcome: EMS Incident Dispatch Data 76xm-jjuj, incidents with final_call_type = 'HEAT', by date of incident_datetime and by the communitydistrict field (place of the incident), "
             "May to September, 2006 to the last year in the file. Temperature: Central Park TMAX. Model: binomial GLM of the day's calls in the low-AC half out of the day's calls in all districts "
             "on TMAX/5 and C(dow) + C(month) + C(year) + hol + wet."),
    "can_it_fail": {"source": "data/derived/heat_solutions/prereg_design.json", "expected_se": E["halves"]["se_diff_log_rr_per_5c"], "yardstick": YARD_CALLS,
                    "D_yardstick": (YARD_CALLS / E["halves"]["se_diff_log_rr_per_5c"]) ** 2, "share_in_low_ac": E["halves"]["share_in_low_ac"], "calls_by_year": E["by_year"],
                    "reading": (f"Expected standard error {r3(E['halves']['se_diff_log_rr_per_5c'])} (Fisher information with the daily total following the published curve of heat ED visits); "
                                f"D for the yardstick is {r3((YARD_CALLS / E['halves']['se_diff_log_rr_per_5c']) ** 2)}. With no true difference the refutation rule is met with probability about "
                                f"{r3(0.5 * (1 + math.erf((YARD_CALLS / E['halves']['se_diff_log_rr_per_5c'] - 1.96) / math.sqrt(2))))}.")},
    "already_seen": ("The citywide daily series of heat-syndrome ED visits and its slope (4.09 per 5 C); the district rates of heat-stress ED visits over five years (heat-surftemp-ed), which are "
                     "higher in several low-AC districts in level. " + SEEN_COMMON + f"From the undated counts I know that {r3(E['halves']['share_in_low_ac'])} of HEAT calls fall in the low-AC half."),
    "alternatives": [
        "Income and health: low-AC districts are poorer and have more chronic illness, which raises heat illness at a given temperature with or without air conditioning.",
        "Place: a call is assigned to where the patient was found. Calls from streets, parks, workplaces and events do not depend on household air conditioning and dilute the contrast; refutation therefore does not show that air conditioning fails to protect.",
        "Low-AC districts are hotter at street level than Central Park by more than high-AC districts are.",
        "Dispatch coding: HEAT is the dispatcher's call type, and its use may differ between boroughs and years; year terms absorb changes over time that are common to both halves only.",
        "Propensity to call an ambulance, as against walking to an emergency department, differs between districts."],
    "prior": 0.45,
    "prior_note": "Probability of 'confirmed'. About 0.2 for refuted.",
    "registrant": "Claude (heat solutions agent)",
}

k = SC["all_shootings_half42"]
b = SC["bias_arithmetic"]
rec_c = {
    "id": "heat-school-out",
    "kind": "confirmation",
    "statement": ("On weekdays within six weeks of the last and first day of classes in New York public schools, shootings are more frequent on days out of school than on school days "
                  "at the same temperature."),
    "graph_evidence": [
        {"association_id": "variables searched by name: school calendar, summer vacation, school holidays", "concepts": ["school holidays (variable names)", "violence"], "n_findings": 2, "n_studies": 1, "direction": "-",
         "summary": ("40 variables match; the only violence outcome is referrals to domestic violence services, which fell during school holidays in England and Wales (Panovska-Griffiths 2022), "
                     "a finding about access to services. The graph holds nothing on school terms and shootings, assault or youth violence."), "pubmed_ids": [35291956]}],
    "graph_evidence_note": rec_a["graph_evidence_note"],
    "literature": [{"citation": "Jacob BA, Lefgren L. Are idle hands the devil's workshop? Incapacitation, concentration, and juvenile crime. Am Econ Rev 2003;93:1560-1577.", "doi": "10.1257/000282803322655446",
                    "finding": "Juvenile property crime falls and juvenile violent crime rises on days when school is in session; cited from memory, not re-read."}],
    "prediction": {
        "direction": "+",
        "magnitude": "Rate ratio of shooting incidents, days out of school against school days: between 0.95 and 1.08, best guess 1.02.",
        "support_if": "The 95% lower limit of the rate ratio is above 1.00. This alone decides 'confirmed'.",
        "refute_if": "The 95% upper limit is below 1.10 and the lower limit is at or below 1.00: a rise of 10% or more when school is out is excluded.",
        "otherwise": "Unsettled.",
        "secondary_registered": ("Reported, not deciding: a 21-day window; quadratic trends; the end and the start of term separately; victims under 18, 18 to 24 and 25 or older (archived file 833y-fsy8, to 2024); "
                                 "the odds that a victim is under 18 on days out of school; a table of victims by age group and hour block; the heat-shootings model on all days with and without a term for "
                                 "the summer recess, and the share of the log slope that the term removes."),
    },
    "composed_prediction": {
        "chain": "school out -> shootings (unknown size g) ; school out is correlated with temperature within June and September only, because heat-shootings holds month and year fixed.",
        "arithmetic": (f"The coefficient of TMAX/5 in a regression of the summer-recess indicator on the terms of heat-shootings is {r3(b['delta_summer_out_per_t5'])}. A school effect of ln g on shootings "
                       f"biases the log slope by ln g x {r3(b['delta_summer_out_per_t5'])}: {round(100 * b['share_of_slope_if_10pct'], 1)}% of the slope if g = 1.10 and {round(100 * b['share_of_slope_if_25pct'], 1)}% if g = 1.25. "
                       f"For the school calendar to produce a tenth of the 14.6%, shootings would have to be {r3(b['irr_out_needed_for_a_tenth_of_slope'])} times as frequent when school is out."),
        "reading": "Computed from the calendar and the weather alone, before any outcome was read: the registered slope cannot contain more than a few percent of school-calendar effect.",
    },
    "plan": (SCRIPT +
             "School calendar: first and last day of classes for each year (common.FIRST_DAY, LAST_DAY; 2006-07 to 2018-19 agree with the daily attendance files, later years from Department of Education calendars). "
             "The June 2020, September 2020 and June 2021 transitions are left out (remote teaching). Days: Monday to Friday, not public holidays, within 42 calendar days of a transition, 2006 to August 2026. "
             "A day is out of school if it is after the last day or before the first day. Closures inside the term (religious holidays, Juneteenth after 2022) are counted as school days unless they are federal holidays, which are dropped. "
             "Outcome: shooting incidents per day (5ucz-vwe8). Model: negative binomial GLM, log link, on out + TMAX/5 + a linear trend in days from the transition for each kind of transition "
             "+ C(dow) + wet + a term for each transition (kind by year); dispersion by maximum likelihood."),
    "can_it_fail": {"source": "data/derived/heat_solutions/prereg_design.json", "weekdays": k["weekdays"], "days_out": k["days_out"], "expected_se_log_irr": k["se_log_irr"],
                    "smallest_detectable_irr_80pct": k["mde_irr_80pct"], "D_for_1.10": k["D_for_irr_1.10"],
                    "under_18": SC["victims_under_18_half42"],
                    "reading": (f"Expected standard error {r3(k['se_log_irr'])} on {k['weekdays']} weekdays; D for a ratio of 1.10 is {r3(k['D_for_irr_1.10'])} (rule 8 needs 4). With no effect the refutation rule is met with "
                                f"probability {r3(0.5 * (1 + math.erf((math.log(1.10) / k['se_log_irr'] - 1.96) / math.sqrt(2))))}. The count of victims under 18 can detect only a ratio of "
                                f"{r3(SC['victims_under_18_half42']['mde_irr_80pct'])} or more (D for 1.25 is {r3(SC['victims_under_18_half42']['D_for_irr_1.25'])}), so the age results are reported and decide nothing.")},
    "already_seen": ("The citywide daily series of shootings and its temperature models; the hourly distribution by temperature band. I have not tabulated shootings by date relative to the school calendar, "
                     "and no script in the repository uses a school calendar with shootings. The victim age field has not been queried by this project."),
    "alternatives": [
        "Season: late June and July differ from May and early June in daylight and outdoor life beyond what temperature captures; the linear trends absorb only smooth change.",
        "Events tied to the calendar and not to school: the weekend of 4 July and the West Indian Day parade on Labor Day fall just after and just before the transitions; public holidays are dropped but the days around them are not.",
        "Summer programmes: the Summer Youth Employment Program starts in early July, about a week after the last day, and would offset a school effect inside the window.",
        "Most victims and shooters are over 18; an effect on school-age youth is diluted about tenfold in the total, which is why the age split is reported."],
    "prior": 0.12,
    "prior_note": "Probability of 'confirmed'. About 0.45 for refuted.",
    "registrant": "Claude (heat solutions agent)",
}
for rec in (rec_a, rec_b, rec_c):
    print(claims.register(rec))
print("yardsticks", YARD_SHOOT, YARD_CALLS, u_low, u_high)
