"""Answers to the four blind referee reports of 13 Nov 2026 on the heat-solutions and heat-extremes
claims (critique/heat-ac-shootings.md, heat-ac-heat-calls.md, heat-school-out.md,
heat-extremes-downturn.md).

Each change goes through concord.claims.revise, which keeps the earlier outcome in `history`.
No registration is touched and no verdict changes. Numbers marked "referee" are the referees'
re-estimates; the three referee scripts (analyses/critique/referee_heat_ac.py,
referee_heat_school_out.py, referee_heat_extremes.py) were re-run by the answering agent and
printed every value quoted. Numbers marked "re-checked" were computed for this answer:
  06:00 day    every estimate that docs/heat_solutions.md and docs/heat_extremes.md quote, refitted
               with events before 06:00 counted on the previous date:
               analyses/critique/round6_six_am_solutions.py -> data/derived/round6_heat/six_am_solutions.json
               analyses/critique/round6_six_am_extremes.py  -> data/derived/round6_heat/six_am_extremes.json
  home share   the share of HEAT calls from homes at which the registered yardstick formula equals
               the upper limit of heat-ac-heat-calls (solved below)

Run once, after the two round6 scripts: ~/.venvs/nyc-concordance/bin/python analyses/critique/answer_round6_heat.py
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims as C

DATE = "13 Nov 2026"
ROOT = Path(__file__).resolve().parents[2]
SOL = json.loads((ROOT / "data/derived/round6_heat/six_am_solutions.json").read_text())
EXT = json.loads((ROOT / "data/derived/round6_heat/six_am_extremes.json").read_text())
SRC_SOL = ("Exploratory, run after the outcomes, and deciding nothing under rule 4 (analyses/critique/round6_six_am_solutions.py; "
           "data/derived/round6_heat/six_am_solutions.json).")
SRC_EXT = ("Exploratory, run after the outcome, and deciding nothing under rule 4 (analyses/critique/round6_six_am_extremes.py; "
           "data/derived/round6_heat/six_am_extremes.json).")


def load(i):
    return json.loads((C.OUT / f"{i}.json").read_text())


def answer(cid, note, reason, short, **changes):
    """Append `note` to the outcome's notes and apply `changes`. The stance is kept as it
    stands unless `changes` sets it."""
    report = f"critique/{cid}.md"
    lead = f"After the referee ({DATE})"
    o = load(cid)
    if lead + ": " + note[:60] in (o.get("notes") or ""):
        print("already answered:", cid)
        return
    ch = dict(changes)
    base = ch.pop("notes", o.get("notes") or "")
    ch["notes"] = base + f"\n\n{lead}: " + note
    if "stance" not in ch:
        ch["stance"] = o.get("stance")
    crit = {"report": report, "answer": short}
    if o.get("critique"):
        crit["earlier"] = o["critique"]
    ch["critique"] = crit
    C.revise(cid, ch, reason, report)
    print("revised:", cid)


def swap(text, old, new):
    if new in text:  # already applied on an earlier run
        return text
    assert old in text, old[:60]
    return text.replace(old, new)


def f3(d):
    return f"{d['estimate']:.3f} ({d['lo']:.3f} to {d['hi']:.3f})"


def pair(claim, key):
    """'calendar against 06:00 day' for one estimate of the heat-solutions file."""
    return f"{f3(SOL['calendar'][claim][key])} on calendar dates and {f3(SOL['six_am'][claim][key])} on the 06:00 day"


def xpair(key, sub=None):
    a, b = EXT["calendar"][key], EXT["six_am"][key]
    if sub:
        a, b = a[sub], b[sub]
    return f"{f3(a)} on calendar dates and {f3(b)} on the 06:00 day"


OLD_LINE = ("One line of run.py was changed after registration and before any result existed: the hour of a shooting is now read "
            "as the text before the first colon, because some times in the file are not zero-padded and the registered line "
            "stopped with an error at that point. No model had run.")
NEW_LINE = ("Two lines of run.py (170 and 224) were changed after registration: each reads the hour of a shooting as the text "
            "before the first colon in place of the first two characters. The earlier wording of this note (one line; unpadded "
            "times in 'the file'; no model had run) was inaccurate and was corrected after the referee. The incident file "
            "5ucz-vwe8 has no unpadded time, and the two versions of line 170 give the same hour for all 24,429 incidents. The "
            "390 unpadded times (of 29,744) are in the archived victim file 833y-fsy8, which only heat-school-out uses, so the "
            "registered script stopped at line 224. That line comes after the air-conditioning models in main(), so in the "
            "failed run those models had been fitted in memory; the script prints and writes only at its end, so no result was "
            "displayed or saved before the change. The change alters no number of the three claims' deciding models, none of "
            "which uses the hour.")

# Would a registered condition change side on the 06:00 day? Reported, never applied (rule 4).
FLIPS = {}

# ---------------------------------------------------------------- heat-ac-shootings

sh_c, sh_s = SOL["calendar"]["heat_ac_shootings"], SOL["six_am"]["heat_ac_shootings"]
assert sh_c["primary"]["lo"] > 0 and f3(sh_c["primary"]) == "0.043 (0.007 to 0.080)"
assert f3(sh_s["primary"]) == "0.025 (-0.011 to 0.061)" and f3(sh_c["income_halves_pooled"]) == "0.034 (-0.007 to 0.076)"
assert f3(sh_c["days_27_or_more"]) == "-0.178 (-0.329 to -0.027)"
FLIPS["heat-ac-shootings"] = {
    "condition": "support: 95% lower limit of the difference above 0",
    "calendar_date": f3(sh_c["primary"]), "six_am_day": f3(sh_s["primary"]),
    "changes_side": bool(sh_s["primary"]["lo"] <= 0),
    "reading_on_six_am_day": "unsettled (lower limit below 0, upper limit above 0.042)" if sh_s["primary"]["hi"] >= 0.042 else "contested"}

o = load("heat-ac-shootings")
answer(
    "heat-ac-shootings",
    "the verdict is kept under rule 1 and narrowed. The referee rebuilt the district table, the district of each shooting "
    "and the daily series with separate code; the daily counts agree on all 7,548 days and the refit gives 0.043 (0.007 to "
    "0.080) on 6,932 days. The support condition, a lower limit above 0, is met by the registered model, so the label stays "
    "confirmed. What is confirmed is one linear slope over all days of the year, with shootings counted on calendar dates. "
    "It is not evidence about air conditioning, for four reasons.\n"
    "Temperature range (referee). The difference is 0.105 (-0.001 to 0.211) on days below 10 C, 0.161 (0.033 to 0.288) from "
    "10 to 20 C, -0.009 (-0.184 to 0.165) from 20 to 27 C and -0.178 (-0.329 to -0.027) at 27 C and above; 0.075 (0.031 to "
    "0.119) from October to April and -0.028 (-0.095 to 0.039) from May to September. It comes from days below about 20 C, "
    "when air conditioners are off, and the sign above the knot is negative for knots at 24, 27 and 30 C and at LaGuardia "
    "and JFK. The agreement of 0.043 with the half-carry value 0.042 is a coincidence of two numbers, and the sentence that "
    "compared them is removed from prediction_scored.\n"
    "The day. Shootings from 00:00 to 05:59 are 34.7% of incidents (8,480 of 24,429), and the maximum of their calendar "
    "date comes hours later. With the day running from 06:00 to 05:59 the registered model gives "
    f"{f3(sh_s['primary'])} on {sh_s['primary']['days']:,} days (referee; re-checked with the registered functions). The "
    "lower limit is below 0 and the upper limit is above 0.042, which the registered rule would read as unsettled. Under "
    "rule 4 a count chosen after the data decides nothing, so the verdict is not revised; the condition that changes side "
    "is reported here and to the coordinator. Shootings from 06:00 to 23:59 alone give 0.051 (0.006 to 0.096); shootings "
    "from 00:00 to 05:59 give 0.034 (-0.027 to 0.095) on the same date's maximum and -0.019 (-0.079 to 0.041) on the "
    "previous date's.\n"
    "Income. The Spearman correlation of air-conditioning share with median income is 0.699 and with the percentage of "
    "Black residents -0.72 (the registration does not mention the second). The income halves pooled by inverse variance "
    f"give {f3(sh_c['income_halves_pooled'])}, which includes 0; the income contrast with air conditioning ignored is 0.028 "
    "(-0.002 to 0.057). No model shows an air-conditioning difference that excludes 0 once income is in it. Within boroughs "
    "the estimate is 0.053 (-0.008 to 0.115) in Brooklyn, 0.044 (-0.028 to 0.117) in Queens and 0.000 (-0.086 to 0.086) in "
    "Manhattan; the Bronx has 169 incidents in high-AC districts.\n"
    "Period. 0.068 (0.025 to 0.112) for 2006 to 2019 and -0.023 (-0.088 to 0.042) for 2020 to 2026; the interaction is "
    "-0.040 (-0.077 to -0.003).\n"
    "Other specifications (referee), calendar date then 06:00 day: HAC errors with 7 lags 0.043 (0.008 to 0.078) and 0.025 "
    "(-0.010 to 0.060); year-by-month terms 0.051 (0.012 to 0.089) and 0.030 (-0.008 to 0.068); without 2020 and 2021 0.058 "
    "(0.020 to 0.097) and 0.037 (-0.002 to 0.076); LaGuardia 0.037 (0.001 to 0.074) and JFK 0.048 (0.007 to 0.088) on "
    "calendar dates. The Pearson statistic is 1.03 per degree of freedom, so the standard errors are sound.\n"
    "Every quoted estimate on the 06:00 day (re-checked), calendar date first: low half's own rate ratio "
    f"{pair('heat_ac_shootings', 'slope_low_half')}; high half {pair('heat_ac_shootings', 'slope_high_half')}; bottom "
    f"against top third {pair('heat_ac_shootings', 'terciles')}; low-income half {pair('heat_ac_shootings', 'low_income_half')}; "
    f"high-income half {pair('heat_ac_shootings', 'high_income_half')}; income halves pooled "
    f"{pair('heat_ac_shootings', 'income_halves_pooled')}; days of 27 C or more {pair('heat_ac_shootings', 'days_27_or_more')}; "
    f"May to September {pair('heat_ac_shootings', 'may_to_september')}; 2006 to 2019 {pair('heat_ac_shootings', '2006_2019')}; "
    f"2020 to 2026 {pair('heat_ac_shootings', '2020_2026')}; piecewise below 27 C "
    f"{pair('heat_ac_shootings', 'piecewise_below_27')} and above {pair('heat_ac_shootings', 'piecewise_above_27')}; Housing "
    f"Bureau jurisdiction against other incidents {pair('heat_ac_shootings', 'housing_jurisdiction_vs_other')}; public-housing "
    f"buildings against other apartment buildings {pair('heat_ac_shootings', 'public_housing_building_vs_apartment')}. On "
    "the 06:00 day the hot-day reversal no longer excludes 0. It is one of about ten registered secondary results (p = 0.02 "
    "uncorrected) and is reported as a result that contradicts the air-conditioning reading, not as a finding that high-AC "
    "districts are more sensitive to heat. " + SRC_SOL + "\n"
    "Rivals that fit the temperature pattern better than air conditioning (referee): outdoor life, which rises from cold to "
    "mild days and is complete by about 20 C; saturation, since the low-AC districts already hold 82% of incidents; and "
    "the poor fit of one linear term to both halves, so that a difference of slopes summarises a difference of shapes.\n"
    "Order of events. The registration is stamped 07:52:12 and the commit on prereg/heat-ac-shootings 07:53:07; the dated "
    "query was fetched at 07:53:21. Git records the commit time and not the push time, so the repository cannot show that "
    "the push preceded the fetch.\n"
    "Stance. The stance is set to null. The value 0.824 was the z of the estimate against no difference, and on the strip "
    "it read as agreement with research. The graph holds nothing on air conditioning and violence, graph_effect is null, "
    "and the one cited paper concerns poverty and housing age.\n"
    "Not done. The referee's fifth recommendation, a new registration of the contrast on days of 27 C or more with the "
    "06:00 day and income in the model, is recorded under research_needed and was not registered in this round.",
    "Referee: keep confirmed, narrowed. verdict_note limits the label to the whole-year slope on calendar dates and says it "
    "is not evidence of an air-conditioning effect; the 06:00-day estimate 0.025 (-0.011 to 0.061), under which the support "
    "condition is not met, is recorded and the verdict is not revised (rule 4); half-carry sentence removed; note on the "
    "changed lines corrected; stance set to null.",
    "accepted; verdict kept under rule 1 and narrowed, note on the changed lines corrected, stance null",
    notes=swap(o["notes"], OLD_LINE, NEW_LINE),
    verdict_note="Confirmed by the registered rule, for the whole-year linear slope on calendar dates only: 0.043 (0.007 "
                 "to 0.080). It is not evidence of an air-conditioning effect. The difference comes from days below about "
                 "20 C, when air conditioners are off, and is -0.178 (-0.329 to -0.027) at 27 C and above. It is 0.025 "
                 "(-0.011 to 0.061) when the day runs from 06:00 to 05:59, and 0.034 (-0.007 to 0.076) within income "
                 "strata pooled; neither interval excludes 0.",
    prediction_scored="partial. The difference is 0.043 (0.007 to 0.080); the predicted range was -0.02 to +0.05 with a "
                      "best guess of +0.01, and the registrant gave 'confirmed' a probability of 0.2. The lower limit is "
                      "above 0, so the support rule is met. After the referee: the sentence comparing the estimate with "
                      "the half-carry value 0.042 is withdrawn, because the difference arises on days below about 20 C, "
                      "when air conditioners are off. On a day from 06:00 to 05:59 the difference is 0.025 (-0.011 to "
                      "0.061) and the support rule is not met; that count was chosen after the data and does not decide "
                      "(rule 4).",
    stance=None,
    stance_note="Null after the referee: the graph has no finding on air conditioning and violence (graph_effect is null), "
                "so the z of the city estimate against no difference (2.34) does not measure agreement with research.",
    research_needed=o["research_needed"] + [{
        "question": "On days of 27 C or more, is the heat slope of shootings steeper in low-AC districts once income is in the model?",
        "data": "NYPD shootings by coordinates and time; Heat Vulnerability Index file",
        "design": "A new registration: the district contrast on days of 27 C or more, with the day from 06:00 to 05:59 and income as a term (the referee's fifth recommendation)",
        "priority": "medium"}],
)

# ---------------------------------------------------------------- heat-ac-heat-calls

hc_c, hc_s = SOL["calendar"]["heat_ac_heat_calls"], SOL["six_am"]["heat_ac_heat_calls"]
assert f3(hc_c["primary"]) == "-0.032 (-0.088 to 0.024)"
Y = 0.11246530985121782
FLIPS["heat-ac-heat-calls"] = {
    "condition": "refutation: 95% upper limit below 0.112 and lower limit at or below 0",
    "calendar_date": f3(hc_c["primary"]), "six_am_day": f3(hc_s["primary"]),
    "changes_side": not (hc_s["primary"]["hi"] < Y and hc_s["primary"]["lo"] <= 0)}


def yardstick(h, rr=1 / 0.23, ul=0.139, uh=0.05):
    """The registered yardstick formula when a share h of calls come from homes."""
    return 0.5 * math.log((1 + h * (rr - 1) * ul) / (1 + h * (rr - 1) * uh))


lo_h, hi_h = 0.0, 1.0
for _ in range(60):  # bisection: the home share at which the yardstick equals the upper limit
    mid = (lo_h + hi_h) / 2
    lo_h, hi_h = (mid, hi_h) if yardstick(mid) < hc_c["primary"]["hi"] else (lo_h, mid)
HOME = (lo_h + hi_h) / 2
assert 0.16 < HOME < 0.18, HOME

o = load("heat-ac-heat-calls")
answer(
    "heat-ac-heat-calls",
    "the verdict is kept. The referee rebuilt the series with separate code; the daily counts agree on all 3,183 days and "
    "the refit gives -0.032 (-0.088 to 0.024) on 1,920 days with at least one call. The refutation condition, an upper "
    "limit below 0.112 with a lower limit at or below 0, is met. Every full-sample variant the referee ran has a lower "
    "limit below 0 and an upper limit below 0.112: for example HAC errors with 7 lags -0.032 (-0.083 to 0.019), year-by-month "
    "terms -0.025 (-0.084 to 0.035), LaGuardia -0.020 (-0.070 to 0.030), JFK -0.012 (-0.065 to 0.041), days of 30 C or "
    "more -0.017 (-0.111 to 0.078), the night minimum in place of the maximum -0.063 (-0.129 to 0.002).\n"
    "What the refutation excludes. The yardstick 0.112 assumes that every call comes from a home, that the odds ratio "
    "for death (0.23) applies to ambulance calls, and that the hot-day contrast is spread evenly over 10 C. With a share h "
    "of calls from homes the same formula gives 0.114 at h = 1 (the registration's 0.112 used unrounded shares), 0.064 at "
    "one half, 0.035 at one quarter and 0.021 at 15% (referee). The upper limit 0.024 equals the yardstick at h = "
    f"{HOME:.2f} (re-checked by solving the formula). The result therefore excludes protection of households by air "
    "conditioning only if more than about 17% of HEAT calls come from homes. The data do not give that share, and 62% of "
    "calls fall between 12:00 and 17:59, which is consistent with many of them coming from outdoors. The comparison with "
    "the case-control studies is not like for like, and the outcome does not test them.\n"
    "Records left out. Of 17,688 HEAT calls, 583 have no community district and 281 carry a code that is not one of the "
    "59 districts (parks and airports), 864 in all. The share without a usable district is 5.8% on days below 30 C and "
    "4.4% on days of 30 C or more, so the loss is not concentrated on hot days. The registered period is May to September "
    "'to the last year in the file'; the calendar in common.py ends on 31 August 2026, so the 23 calls of September 2026 "
    "are left out. Neither changes the result.\n"
    "The negative binomial failure. The dispersion estimate for the high-AC half diverges (to a value near 10^224 in the "
    "referee's fit), and count_fit in run.py accepts any finite dispersion above 0.0001, so the diverged value was passed "
    "to the model and the slope came back as 2.335 with an interval of no width. The low-AC half fits normally (dispersion "
    "0.277, 6.675, 6.223 to 7.160). The deciding model is the binomial one and does not use count_fit. run.py is left as "
    "registered (rule 9); later scripts should bound the dispersion from above.\n"
    "Rivals (referee). Income: within the low-income half -0.121 (-0.229 to -0.012) on 1,065 calls in six high-AC "
    "districts, within the high-income half 0.057 (-0.038 to 0.153), pooled -0.020 (-0.091 to 0.052); the strata differ in "
    "sign and the low-income result is one of several secondary results. Manhattan has 37% of HEAT calls and eight of its "
    "twelve districts are in the high-AC half; without Manhattan the difference is -0.075 (-0.148 to -0.003), and without "
    "Brooklyn 0.010 (-0.054 to 0.074). Period: 0.006 (-0.062 to 0.075) for 2006 to 2019 and -0.112 (-0.207 to -0.017) for "
    "2020 to 2026, so the negative estimate comes from the recent years, when calls rose (1,483 in 2026 against 385 in "
    "2020). Not addressed by any variant: residents of poorer districts may go to an emergency department on foot or not "
    "call, and dispatch coding of HEAT may differ between areas.\n"
    f"The day. {100 * SOL['share_before_06']['heat_calls']:.0f}% of HEAT calls fall between 00:00 and 05:59 (472 of the "
    "15,754 in the model), so the definition of the day matters little here. Calendar date first (re-checked): primary "
    f"{pair('heat_ac_heat_calls', 'primary')}; bottom against top third {pair('heat_ac_heat_calls', 'terciles')}; "
    f"low-income half {pair('heat_ac_heat_calls', 'low_income_half')}; high-income half "
    f"{pair('heat_ac_heat_calls', 'high_income_half')}; days of 27 C or more {pair('heat_ac_heat_calls', 'days_27_or_more')}; "
    f"without Manhattan below 59th Street {pair('heat_ac_heat_calls', 'without_manhattan_below_59th_street')}; Poisson rate "
    f"ratios per 5 C, low half {pair('heat_ac_heat_calls', 'slope_low_half_poisson')} and high half "
    f"{pair('heat_ac_heat_calls', 'slope_high_half_poisson')}. The refutation condition is met under both definitions. "
    + SRC_SOL + "\n"
    "Stance. The stance is set to null. The value -0.505 read on the strip as city data disagreeing with the "
    "case-control studies, which this outcome does not test.",
    "Referee: keep contested. verdict_note adds that the upper limit excludes the yardstick only if more than about 17% "
    "of HEAT calls come from homes; 864 calls without a usable district and 23 calls of September 2026 reported; negative "
    "binomial failure explained; note on the changed lines corrected; 06:00-day estimates recorded; stance set to null.",
    "accepted; verdict kept, yardstick caveat added, stance null",
    notes=swap(o["notes"], OLD_LINE, NEW_LINE + " Neither changed line is used for heat calls."),
    verdict_note="Contested by the registered refutation rule: the heat slope of ambulance calls coded HEAT does not "
                 "differ between the halves, -0.032 (-0.088 to 0.024), and the interval excludes the difference expected "
                 "if all calls came from homes (0.112). Calls are located where the patient was found, so this does not "
                 "show that air conditioning fails to protect at home: the upper limit excludes household protection of "
                 "the size the case-control studies report only if more than about 17% of HEAT calls come from homes, and "
                 "the data do not give that share.",
    stance=None,
    stance_note="Null after the referee: the comparison with the case-control odds of heat death depends on the assumed "
                "share of calls from homes, and the outcome does not test those studies.",
)

# ---------------------------------------------------------------- heat-school-out

so_c, so_s = SOL["calendar"]["heat_school_out"], SOL["six_am"]["heat_school_out"]
assert f3(so_c["primary"]) == "1.105 (0.997 to 1.224)" and f3(so_s["primary"]) == "1.044 (0.951 to 1.146)"
assert f3(so_c["without_weekday_after_public_holiday"]) == "1.060 (0.957 to 1.173)"
assert f3(so_c["hour_block_00-05_without_weekday_after_holiday"]) == "1.182 (0.970 to 1.440)"


def school_rule(e):
    return "confirmed" if e["lo"] > 1.0 else "contested" if e["hi"] < 1.10 else "unsettled"


FLIPS["heat-school-out"] = {
    "condition": "support: lower limit above 1.00; refutation: upper limit below 1.10 with lower limit at or below 1.00",
    "calendar_date": f3(so_c["primary"]), "six_am_day": f3(so_s["primary"]),
    "changes_side": school_rule(so_c["primary"]) != school_rule(so_s["primary"])}
GONE_HOL = 100 * (1 - math.log(so_c["without_weekday_after_public_holiday"]["estimate"]) / math.log(so_c["primary"]["estimate"]))
GONE_SIX = 100 * (1 - math.log(so_s["primary"]["estimate"]) / math.log(so_c["primary"]["estimate"]))
u = so_c["under_18_per_100_weekdays"]
us = so_s["under_18_per_100_weekdays"]

o = load("heat-school-out")
answer(
    "heat-school-out",
    "the verdict is kept. The referee rebuilt the window with separate code: the same 2,260 weekdays, 1,125 days out and "
    "7,199 shootings, with identical counts on every row, and 1.105 (0.997 to 1.224). Neither registered condition is "
    "met, so the verdict is unsettled. The referee found four problems, all accepted.\n"
    "1. The morning after a public holiday. Shootings before 06:00 are counted on the calendar date. Public holidays are "
    "dropped from the window, and the weekday after one is kept and carries the holiday night's shootings after midnight. "
    "The twelve weekdays dated 5 July have a mean of 6.08 shootings before 06:00 against 0.89 on other days. These are the "
    "night of 4 July, counted as days out of school about a week after the last day of classes. The window has 74 "
    "weekdays that follow a public holiday, 29 of them out of school. Without those weekdays the ratio is "
    f"{f3(so_c['without_weekday_after_public_holiday'])}; with a term for them 1.078 (0.976 to 1.190); with only their "
    f"shootings before 06:00 removed 1.022 (0.924 to 1.130); on days from 06:00 to 05:59 {f3(so_s['primary'])} (referee; "
    "re-checked with the registered functions). The whole registered excess is in shootings before 06:00: from 06:00 to "
    f"23:59 on the calendar date the ratio is 0.999 (0.890 to 1.120). On the log scale {GONE_HOL:.0f}% of the excess goes "
    f"without the mornings after holidays and {GONE_SIX:.0f}% on the 06:00 day. Events tied to the calendar were a rival named in the registration, "
    "and the first outcome did not address it.\n"
    "2. The window. The ratio is 1.169 (0.992 to 1.379) at a half-width of 14 days, 1.217 (1.057 to 1.402) at 21, 1.167 "
    "(1.030 to 1.322) at 28, 1.126 (1.006 to 1.260) at 35, 1.105 at the registered 42, 1.079 (0.981 to 1.186) at 49, 1.071 "
    "(0.981 to 1.170) at 56, 1.052 (0.968 to 1.144) at 63 and 1.024 (0.945 to 1.109) at 70. A lasting effect of the recess "
    "would not shrink as the window grows. Without the days within 7 days of a transition the ratio is 1.055 (0.910 to "
    "1.224), and within 10 days 0.961 (0.820 to 1.125). The excess is a peak of about two weeks around the turn of June "
    "and July and is not a change of level that lasts through the recess. 'A 10% rise' is therefore replaced as the "
    "summary by the range across windows, 1.02 to 1.22.\n"
    "3. School-side days that are not school days. In the windows covered by the attendance file (September 2006 to June "
    "2019), 66 school-side weekdays outside the last 12 days of term have no attendance record (Anniversary Day, Clerical "
    "Day, Eid, Rosh Hashanah, Yom Kippur), about 8% of school-side days. Dropping them gives 1.139 (1.004 to 1.291) "
    "against 1.153 (1.019 to 1.305) for the same years as registered; counting them as out gives 1.083 (0.977 to 1.202). "
    "High schools hold Regents examinations and no regular classes from about the middle of June, so for students of "
    "high-school age classes end one to two weeks before the registered last day. Both facts bias the estimate towards 1, "
    "and the date of the transition is uncertain by more than a week for the age group the claim is about. Moving every "
    "transition one day earlier gives 1.143 (1.032 to 1.266) and one day later 1.083 (0.977 to 1.201).\n"
    "4. Dates counted twice. The end window runs to about 7 August and the start window begins about 28 July, so 184 "
    "dates are stacked in both as days out of school, and HC0 errors treat the copies as independent. With errors "
    "clustered by date the interval is 0.995 to 1.227; with each date kept once the ratio is 1.114 (1.002 to 1.238).\n"
    "The margin. The lower limit is 0.003 below 1.00, which is smaller than the effect of the window, the error estimator, "
    "the remote-schooling years or a one-day change in the dates: model-based errors give 1.105 (1.003 to 1.217), keeping "
    "the 2020 and 2021 transitions 1.102 (1.001 to 1.213), 2006 to 2019 alone 1.155 (1.025 to 1.300), 2022 to 2026 alone "
    "0.953 (0.765 to 1.187), and leaving out one year a lower limit between 0.973 and 1.019. The same data would have read "
    "confirmed under some of these. Without the mornings after holidays every one is unsettled again (1.060, 0.964 to "
    "1.166 with 2020 and 2021; 1.115, 0.991 to 1.254 for 2006 to 2019). The refutation rule is met under no variant; the "
    "smallest upper limit is 1.109. The realised standard error is 0.052 against the 0.045 expected at registration. The "
    "reference to rule 10 in the earlier verdict note is dropped: that rule concerns conditions on a point estimate, and "
    "this condition is on an interval bound.\n"
    "The exploratory hour blocks. The ratio 1.404 (1.144 to 1.723) for 00:00 to 05:59 is the largest of four blocks chosen "
    "after the data (p = 0.005 corrected for four), and its boundary differs from the registered table of victims by "
    "hour, which used 00:00 to 07:59. Without the mornings after holidays it is "
    f"{f3(so_c['hour_block_00-05_without_weekday_after_holiday'])}, and counted with the preceding day it is "
    f"{f3(so_s['hour_block_00-05'])}. A placebo transition 28 days inside the term gives 0.681 (0.499 to 0.927) for this "
    "block, so the linear trends do not describe how shootings after midnight grow through May and June and the nominal "
    "interval is too narrow. The figure 1.40 should not be quoted as a recess effect; 1.18 with an interval that includes "
    "1 is what the data support. The block also rises on weekend dates in the same windows, 1.100 (0.926 to 1.306), which "
    "answers the second research_needed question: the data do not show that the excess is specific to weekdays.\n"
    "Victims under 18 (exploratory, after the data). The registered table has 16 cells and no intervals: 51 victims under "
    "18 between 00:00 and 07:59 on school days and 108 on days out, and the other age groups move the same way (18 to 24: "
    "375 to 615; 25 or older: 632 to 837). In the referee's count models the ratio for victims shot before 06:00 is 3.56 "
    "(1.52 to 8.33) for under 18, 1.57 (1.13 to 2.18) for 18 to 24 and 1.35 (1.04 to 1.76) for 25 or older, and without the "
    "mornings after holidays 2.19 (0.88 to 5.41), 1.31 (0.94 to 1.83) and 1.14 (0.88 to 1.48). Without those mornings the "
    "share of under-18 victims shot before 06:00 is 8.5% on school days and 21.1% on days out, and the interaction of out "
    "with under 18 is 2.04 (1.25 to 3.33) on 118 victims. Victims under 18 do shift towards the hours after midnight more "
    "than adults do. The result was found after the data among at least 16 cells and 4 blocks, has no control for season "
    "beyond temperature and year, and needs its own registration.\n"
    "Season (referee). On Saturdays and Sundays in the same windows the ratio is 1.011 (0.895 to 1.142). Placebo "
    "transitions 22 to 35 days inside the term or the recess give 0.912 to 1.085 with 21-day windows. For 1 to 14 "
    "September, where the same day of the month is in and out of school in different years, the ratio is 1.253 (0.867 to "
    "1.810) on 171 weekdays. These are compatible with a school effect and with none.\n"
    "Every quoted estimate on the 06:00 day (re-checked), calendar date first: 21-day window "
    f"{pair('heat_school_out', 'window_21_days')}; victims under 18 {pair('heat_school_out', 'victims_u18')}; 18 to 24 "
    f"{pair('heat_school_out', 'victims_a1824')}; 25 or older {pair('heat_school_out', 'victims_a25')}; the heat-shootings "
    f"slope without the recess term {pair('heat_school_out', 'heat_slope_without_recess_term')} and with it "
    f"{pair('heat_school_out', 'heat_slope_with_recess_term')}; the recess term {pair('heat_school_out', 'recess_term')}, "
    f"which removes {100 * so_c['share_of_log_slope_removed']:.1f}% and {100 * so_s['share_of_log_slope_removed']:.1f}% of "
    "the log slope. Victims under 18 per 100 weekdays between 00:00 and 07:59 are "
    f"{u['00-07_school']:.1f} on school days and {u['00-07_out']:.1f} on days out on calendar dates, and "
    f"{us['00-07_school']:.1f} and {us['00-07_out']:.1f} when those shot before 06:00 are counted with the preceding day. "
    "No registered condition changes side on the 06:00 day: the verdict is unsettled under both. " + SRC_SOL + "\n"
    "Stance. The stance is set to null. The value 0.741 (z = 1.9) placed the claim well towards agreement on the strip. "
    "The graph holds no finding on school terms and shootings, graph_effect is null, and the one cited paper (Jacob and "
    "Lefgren 2003, cited from memory) reports more juvenile violent crime on days when school is in session, the opposite "
    "direction.\n"
    "Not accepted as a rule. The referee suggests a rule for all shootings claims that would count shootings before 06:00 "
    "on the previous date or drop the day after each excluded holiday. The criticism is accepted and the re-estimates are "
    "recorded here and in the other heat outcomes. No verdict rule is added, as in Round 5: under rule 4 a count chosen "
    "after the data cannot decide a verdict already given. New registrations on shootings by date should state the day.",
    "Referee: keep unsettled. Notes now say that the registered estimate counts the night of 4 July on 5 July (1.060 "
    "without weekdays after a public holiday; 1.044 on 06:00 days), that the excess is before 06:00 and falls from 1.217 "
    "at 21 days to 1.024 at 70, that two lines of run.py changed, that 184 dates are stacked twice, and that about 8% of "
    "school-side days are closures; the exploratory 1.40 is given with 1.18 (0.97 to 1.44); stance set to null. The "
    "proposed verdict rule for the 06:00 day is not adopted (rule 4).",
    "accepted except the proposed verdict rule; verdict kept, notes corrected, stance null",
    notes=swap(o["notes"], OLD_LINE, NEW_LINE),
    verdict_note="Unsettled: the rate ratio is 1.105 (0.997 to 1.224), with the lower limit 0.003 below the threshold 1.00 "
                 "and the upper limit above 1.10. About half of the excess is the night of 4 July and other holiday "
                 "nights counted on the following weekday: the ratio is 1.060 (0.957 to 1.173) without weekdays after a "
                 "public holiday and 1.044 (0.951 to 1.146) on days from 06:00 to 05:59. It falls from 1.217 at a 21-day "
                 "window to 1.024 at 70 days, so it is a peak around the turn of June and July and not a lasting change "
                 "of level, and it may be the season and not the school calendar.",
    prediction_scored=o["prediction_scored"] + " After the referee: without the weekdays that follow a public holiday the "
    "ratio is 1.060 (0.957 to 1.173), inside the predicted range, and on days from 06:00 to 05:59 it is 1.044 (0.951 to "
    "1.146). The registered measure is the calendar date, so the score stays a miss.",
    stance=None,
    stance_note="Null after the referee: the graph holds no finding on school terms and shootings (graph_effect is null) "
                "and the one cited paper points the other way, so the z against no effect (1.9) does not measure agreement "
                "with research.",
    research_needed=[o["research_needed"][0],
                     {**o["research_needed"][1],
                      "answered": "Partly, by the referee: on weekend dates in the same windows the 00:00 to 05:59 block is "
                                  "1.100 (0.926 to 1.306), so the data do not show that the excess is specific to weekdays."},
                     {"question": "Do victims under 18 shift towards the hours after midnight when school is out, more than adults do?",
                      "data": "NYPD shooting victims by age group and hour (archived file to 2024 and its successor)",
                      "design": "A new registration: the share of victims shot before 06:00, out by under-18 interaction "
                                "(exploratory value 2.04, 1.25 to 3.33, on 118 victims), with days from 06:00 to 05:59 and "
                                "day-of-year terms",
                      "priority": "medium"}],
)

# ---------------------------------------------------------------- heat-extremes-downturn

xc, xs = EXT["calendar"], EXT["six_am"]
assert f3(xc["pooled"]) == "1.035 (1.008 to 1.063)" and xs["pooled"]["lo"] < 1.0 and f"{xs['pooled']['lo']:.3f}" == "0.994"
assert f3(xc["heat_waves"]["chicago_shoot"]) == "0.983 (0.913 to 1.057)" and f3(xc["heat_waves"]["philadelphia_shoot"]) == "1.036 (0.912 to 1.177)"
FLIPS["heat-extremes-downturn"] = {
    "condition": "refutation: 95% lower limit of the pooled rate ratio above 1.00",
    "calendar_date": f3(xc["pooled"]), "six_am_day": f3(xs["pooled"]),
    "changes_side": xc["verdict_by_registered_rule"] != xs["verdict_by_registered_rule"],
    "reading_on_six_am_day": xs["verdict_by_registered_rule"]}
hw_c, hw_s = xc["heat_waves"], xs["heat_waves"]

o = load("heat-extremes-downturn")
answer(
    "heat-extremes-downturn",
    "the verdict is kept and reworded. The referee rebuilt the four daily series from the raw files with separate code; "
    "the counts agree on every day and the refit gives 1.035 (1.008 to 1.063), Q = 3.07. The registered refutation "
    "condition, a lower limit above 1.00, is met, and rule 1 gives contested. The two conditions were met with very "
    "different margins, and the notes now say so.\n"
    "The downturn. The support condition fails by a wide margin: z = 4.1 against the upper end of the predicted band "
    "(0.98), and no variant below has a lower limit under 0.98. The registered downturn at 38 C is excluded.\n"
    "The rise. The refutation condition is met by 0.008 (z = 2.56 against 1.00, p = 0.010; no single city excludes 1.00). "
    "It is not met, that is the lower limit is at or below 1.00, with a Hartung-Knapp interval, the usual correction for a "
    "pool of four estimates (0.992 to 1.081); with the daily minimum in the model, 1.019 (0.984 to 1.056); with rain "
    "amount and the previous day's maximum, 1.022 (0.987 to 1.059); with second weather stations in Phoenix, Dallas and "
    "Austin, 1.017 (0.987 to 1.049); with the day from 06:00 to 05:59, 1.030 (0.993 to 1.069) in the referee's fit and "
    f"{f3(xs['pooled'])} with the registered code; without 2020 and 2021, "
    "1.027 (0.997 to 1.057); with hot days in June to August only, 1.029 (0.997 to 1.061); with June to September and "
    "year-by-month terms, 1.034 (0.980 to 1.092); without 2018 (lower limit 0.998); and without Phoenix (0.989), Tucson "
    "(0.997) or Austin (0.989). The point estimate stays between 1.017 and 1.044 (referee). The earlier sentence that the "
    "condition was met 'by less than the sampling error (rule 10)' is withdrawn: rule 10 concerns conditions on a point "
    "estimate, and this one is on an interval bound.\n"
    "Wording. The result is: no downturn at 38 C; the rate is level or slightly higher. It is not 'assaults are more "
    "frequent at 38 C and above'. The registration assigned a plateau to the verdict unsettled and a linear rise to "
    "contested. The label contested comes from the literal condition, a lower limit above 1.00, which a small rise well "
    "short of the linear prediction (1.075; the published band starts at 1.06, z = -1.8) meets. The earlier sentence that "
    "the data 'fit a plateau better than either registered alternative' described the alternative that the registration "
    "tied to unsettled.\n"
    "Offence definitions. The four series are not the same offence. The Dallas file withholds family violence: 23,299 "
    "incidents are coded 'AGG ASSAULT - NFV' and 35 family violence. In Austin 47% of incidents carry the family-violence "
    "flag or a family or strangulation offence type (37% in 2003 to 2008, about 50% afterwards), and the category includes "
    "deadly conduct (7.5%). Phoenix and Tucson use a UCR summary category with no family-violence field. The difference "
    "does not explain the Dallas estimate: in Austin the ratio is 1.039 (0.976 to 1.106) for family violence and 1.038 "
    "(0.976 to 1.104) for the rest, and with Austin's non-family incidents the pool is 1.034 (1.005 to 1.064).\n"
    "Phoenix records. From 3 September 2025 the Phoenix file carries no time of day, September 2025 has 417 incidents "
    "against about 570 a year earlier, and the count of all offence rows rises by 40% in October 2025, which looks like a "
    "change of records system. The file runs to 31 December 2025 and build.py ends the series on 30 November 2025; "
    "neither the registration nor the script gives the reason. Ending Phoenix on 31 August 2025 gives 1.037 for the city "
    "and the same pool.\n"
    "Stations. Camp Mabry records 710 days at 38 C or more and Austin-Bergstrom 443; Sky Harbor 1,112 and Phoenix Deer "
    "Valley 854 on the same dates. A fixed threshold at a warm station is partly a comparison at a lower temperature "
    "across the city.\n"
    "Night and hour (referee, exploratory). In Phoenix incidents of the night that follows a hot day rise by 1.129 (1.019 "
    "to 1.251) and afternoon and evening incidents do not (1.011, 0.956 to 1.069), so the excess at 38 C and above may "
    "belong to the night. Incidents from 12:00 to 23:59 give 0.894 (0.811 to 0.984) in Dallas, in the direction of the "
    "daylight downturn that Rotton and Cohn reported for that city; it is one of twelve cells and not significant after "
    "correction.\n"
    "Degrees against percentiles. The statement that one curve in degrees fits better than one in percentiles is "
    "withdrawn as evidence on adaptation. The registrant's degree bins hold 2,700 to 6,400 days each and two percentile "
    "bins hold about 11,500 days each, so the comparison was unequal: 496 AIC units with those bins, 43 with ten "
    "equal-count bins on each scale, about 450 with splines of equal degrees of freedom. A scale of degrees from each "
    "city's own mean, which is a relative scale, fits as well as absolute degrees or better (3,053 against 2,822 units "
    "with ten bins; 3,227 against 3,217 with twenty). Among the hottest quarter of each city's days degrees are better by "
    "4 to 17 units, and in the four hot cities alone percentiles are better by 5. The comparison shows that the curve is "
    "close to linear in degrees and that ranks distort it. It does not show that cities share one absolute curve.\n"
    "New York heat waves (exploratory). The ratio for days two and later of a run at 32 C or more, 0.836 (0.739 to 0.946) "
    "for shootings, does not replicate with the same code in the two other cities with shooting series: Chicago 0.983 "
    "(0.913 to 1.057), Philadelphia 1.036 (0.912 to 1.177), the two together 0.996 (0.935 to 1.061). It depends on the "
    "threshold: 1.023 at 29 C, 0.966 at 30, 0.932 at 31, 0.836 at 32, 0.901 at 33 and 0.839 at 34, with only the 32 C "
    "interval excluding 1.00. Part of it comes from first days of a run being high (1.098 against isolated days). It is a "
    "New York shootings result that two other cities do not show, and not a property of heat waves.\n"
    f"The 06:00 day (re-checked with the registered test.py and describe.py on rebuilt daily files). Incidents from "
    f"00:01 to 05:59 are {100 * EXT['share_00_01_to_05_59_of_incident_file']['phoenix']:.0f}% of the Phoenix series, "
    f"{100 * EXT['share_00_01_to_05_59_of_incident_file']['dallas']:.0f}% of Dallas and "
    f"{100 * EXT['share_00_01_to_05_59_of_incident_file']['austin']:.0f}% of Austin; Tucson publishes no time and is "
    "unchanged, and Phoenix ends on 31 August 2025 because the file has no time after that. Calendar date first: pooled "
    f"{xpair('pooled')}; Phoenix {xpair('cities', 'phoenix')}; Dallas {xpair('cities', 'dallas')}; Austin "
    f"{xpair('cities', 'austin')}; year-by-month strata {xpair('S1_year_month_strata')}; May to September "
    f"{xpair('S2_may_sep_only')}; without 2020 and 2021 {xpair('S3_without_2020_2021')}; 35 to 38 C {xpair('S4_35_38_vs_32_35')}; "
    f"38 to 41 C {xpair('S5_38_41_vs_32_35')}; 41 C and above {xpair('S6_41_plus_vs_32_35')}; the linear prediction "
    f"{xpair('linear_prediction')} (z of the observed ratio below it {xc['z_observed_below_linear']:.1f} and "
    f"{xs['z_observed_below_linear']:.1f}); slope per 5 C from 20 to 35 C {xpair('slope_20_to_35_per_5C')} and above 35 C "
    f"{xpair('slope_above_35_per_5C')}; New York shootings on later days of a heat wave "
    f"{xpair('ny_heatwave_shootings', 'later_vs_first_or_isolated')}, New York felony assaults "
    f"{xpair('ny_heatwave_felony_assaults_later')}, Chicago shootings {f3(hw_c['chicago_shoot'])} and {f3(hw_s['chicago_shoot'])}, "
    f"Philadelphia shootings {f3(hw_c['philadelphia_shoot'])} and {f3(hw_s['philadelphia_shoot'])}, and those two cities "
    f"together {f3(hw_c['chicago_and_philadelphia_shootings_pooled'])} and {f3(hw_s['chicago_and_philadelphia_shootings_pooled'])}: "
    "on the 06:00 day the two other cities point the same way as New York and their intervals still include 1.00. The "
    f"degrees model is better than the percentile model by {xc['aic_degrees_better_by']:.0f} and "
    f"{xs['aic_degrees_better_by']:.0f} AIC units with the registrant's bins. On the 06:00 day the registered rule reads "
    f"{xs['verdict_by_registered_rule']}: the refutation condition changes side. Under rule 4 a count chosen after the "
    "data decides nothing, so the verdict is not revised; the condition that changes side is reported here and to the "
    "coordinator. The downturn band is excluded under both definitions. " + SRC_EXT,
    "Referee: keep contested, reworded as 'no downturn at 38 C; the rate is level or slightly higher'. The fragility of "
    "the lower limit (1.008) is listed, the reference to rule 10 removed, the family-violence difference between Dallas "
    "and Austin and the Phoenix records break of September 2025 recorded, the degrees-against-percentiles comparison "
    "withdrawn as evidence on adaptation, and the New York heat-wave ratio marked as not replicating in Chicago or "
    "Philadelphia. On the 06:00 day the refutation condition is not met; the verdict is not revised (rule 4).",
    "accepted; verdict kept under rule 1 and reworded, fragility of the lower limit listed, stance note added",
    notes=swap(swap(o["notes"],
                    "The rate at 38 C and above is 3.5% higher than at 32 to 35 C, so there is no downturn at 38 C.",
                    "The point estimate at 38 C and above is 3.5% above 32 to 35 C, so there is no downturn at 38 C; the rate "
                    "is level or slightly higher (reworded after the referee)."),
               "The verdict label 'contested' means that the downturn hypothesis is refuted at 38 C; the data fit a plateau "
               "above about 35 C better than either registered alternative.",
               "The verdict label 'contested' means that the downturn hypothesis is refuted at 38 C. It comes from the "
               "literal condition, a lower limit above 1.00; the registration assigned a plateau to unsettled, and the "
               "curve above about 35 C is close to a plateau (reworded after the referee)."),
    verdict_note="Contested means here that the registered downturn at 38 C is refuted: no downturn; the rate is level or "
                 "slightly higher, 1.035 (1.008 to 1.063). The downturn band (0.88 to 0.98) is excluded under every "
                 "variant (z = 4.1). The lower limit above 1.00 is fragile: it is at or below 1.00 with a Hartung-Knapp "
                 "interval (0.992), the daily minimum in the model (0.984), second weather stations (0.987), a day from "
                 "06:00 to 05:59 (0.994), without 2020 and 2021 (0.997), without 2018 (0.998), and without any one of "
                 "Phoenix, Tucson and Austin. The registration assigned a plateau to unsettled; the label follows the "
                 "literal condition.",
    prediction_scored="miss. The registered downturn (pooled ratio 0.88 to 0.98) was not found: the support condition "
                      "fails by a wide margin (z = 4.1 against 0.98, and every variant excludes the band). The refutation "
                      "condition is met by 0.008: the pooled lower limit is 1.008. It is not met with a Hartung-Knapp "
                      "interval (0.992 to 1.081), with the daily minimum in the model (0.984), with second stations "
                      "(0.987), with a day from 06:00 to 05:59 (0.994), without 2020 and 2021 (0.997), without 2018 "
                      "(0.998), or without any one of Phoenix, Tucson and Austin. The result is no downturn at 38 C, with "
                      "the rate level or slightly higher.",
    stance_note="The stance (-0.857, z = -2.56) measures disagreement of the city estimate with the registered downturn. "
                "It is not agreement with the graph's monotonic rise: the observed 1.035 is below the lower end of the "
                "published linear band (1.06, z = -1.8) and below the cities' own extrapolated slope (1.075, z = -2.6). On "
                "the variants listed in the verdict note the interval includes 1.00.",
    six_am_day={"pooled": xs["pooled"], "cities": xs["cities"], "reading_by_registered_rule": xs["verdict_by_registered_rule"],
                "note": "Exploratory (rule 4): incidents from 00:01 to 05:59 counted on the previous date in Phoenix, Dallas "
                        "and Austin; Tucson unchanged. Decides nothing."},
)

(ROOT / "data/derived/round6_heat/conditions_on_six_am_day.json").write_text(json.dumps(FLIPS, indent=1))
print(json.dumps(FLIPS, indent=1))
print("done")
