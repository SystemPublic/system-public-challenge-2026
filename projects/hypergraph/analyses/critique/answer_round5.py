"""Answers to the two blind referee reports of 13 Nov 2026 on the round 5 claims
(critique/heat-night-minimum.md, critique/transfer-chicago-concordance-matrix.md).

Each change goes through concord.claims.revise, which keeps the earlier outcome in `history`.
No registration is touched and no verdict changes. Numbers marked "referee" are the referees'
re-estimates; both referee scripts (analyses/critique/referee_heat_night_minimum.py and
referee_chicago_matrix.py) were re-run by the answering agent and printed the values quoted.
Numbers marked "re-checked" were computed for this answer:
  heat-night-minimum   the 00:00 to 05:59 ratios per 5 C (the registered contrast is 6 C wide and
                       linear above 27 C, so the per 5 C value is the ratio to the power 5/6), from
                       data/derived/round5/heat_night/results.json; the two gaps in the Midway file
  heat-shootings, heat-mech-outdoors
                       night-of counts (06:00 to 05:59), analyses/critique/round5_night_of_check.py,
                       written to data/derived/round5/heat_night/night_of_check.json
  transfer-chicago-concordance-matrix
                       the prereg branch on the remote (git ls-remote), its commit and its content

Run once: ~/.venvs/nyc-concordance/bin/python analyses/critique/answer_round5.py
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims as C

DATE = "13 Nov 2026"
ROOT = Path(__file__).resolve().parents[2]


def load(i):
    return json.loads((C.OUT / f"{i}.json").read_text())


def answer(cid, note, reason, short, report=None, lead=None, **changes):
    """Append `note` to the outcome's notes and apply `changes`. The stance is kept as it
    stands unless `changes` sets it. `report` is the referee report that prompted the change
    (by default the claim's own)."""
    report = report or f"critique/{cid}.md"
    lead = lead or f"After the referee ({DATE})"
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


# ---------------------------------------------------------------- heat-night-minimum

res = json.loads((ROOT / "data/derived/round5/heat_night/results.json").read_text())
per5 = {}
for city in ("new_york", "chicago"):
    b = res[city]["part_b"]["block_00-06"]
    per5[city] = "{:.3f} ({:.3f} to {:.3f})".format(*(b[k] ** (5 / 6) for k in ("estimate", "lo", "hi")))
assert per5["new_york"].startswith("1.106") and per5["chicago"].startswith("1.107"), per5

answer(
    "heat-night-minimum",
    "the verdict is kept. The referee rebuilt both daily series with separate code and reproduced every reported "
    "number, and none of twelve further specifications of part (a) changes the verdict: the New York estimate lies "
    "between 0.997 (LaGuardia) and 1.060 (previous day's maximum and minimum added), every interval includes 1.00 and "
    "every New York upper limit is above 1.075, so 1.033 is not a measured effect. The corrections follow.\n"
    "Units. The ratios for 00:00 to 05:59, 1.128 (1.021 to 1.246) in New York and 1.129 (1.040 to 1.226) in "
    f"Chicago, are for 33 against 27 C of the daily maximum, which is 6 C. Per 5 C they are {per5['new_york']} and "
    f"{per5['chicago']} (re-checked), about 1.11 in each city, and not 1.13.\n"
    "Selection after the data. The six-hour blocks were registered as a table, with no prediction about which "
    "block would carry the excess, so singling out 00:00 to 05:59 is a choice made after the data and is "
    "exploratory under rule 4. Corrected for four blocks the p value is 0.07 in New York (0.018 uncorrected) and "
    "0.016 in Chicago (0.004 uncorrected). The inverse-variance mean of the two cities is 1.129 (1.059 to 1.203), "
    "z = 3.7, p about 0.0008 after the correction. The contrast with the evening block, from a binomial model of "
    "the 00:00 to 05:59 share of night shootings, is 1.177 (1.037 to 1.334) in New York and 1.132 (1.023 to 1.252) "
    "in Chicago (referee). The boundary at midnight is not sharp: 02:00 to 05:59 gives 1.201 and 1.133, 00:00 to "
    "02:59 gives 1.087 and 1.121, and 21:00 to 23:59 gives 1.006 and 0.998.\n"
    "The following night. This variant was in the registered plan with a stated expectation and is a registered "
    "secondary result. It is not robust to one control in New York: with the next day's maximum and a wet-day term "
    "for the next date in the model the ratio is 1.073 (0.989 to 1.164) in New York and 1.063 (1.006 to 1.122) in "
    "Chicago (referee). The next day's maximum and the following night's minimum correlate at 0.76 on hot days, so "
    "the daily record cannot separate a warm night from a hot spell that continues. Two placebo checks pass: the "
    "minimum two nights later adds nothing once the following night is in the model (0.984, 0.923 to 1.048; 0.991, "
    "0.953 to 1.031), and day shootings, which precede the following night, do not follow it (0.924, 0.813 to "
    "1.049; 1.039, 0.970 to 1.113). At other stations the following-night ratio is 1.112 (LaGuardia), 1.083 (JFK) "
    "and 1.041 (1.000 to 1.084, O'Hare).\n"
    "One observation. The after-midnight excess, the following-night ratio and the difference between calendar-day "
    "and shooting-day counts are the same observation stated three ways: shootings in the small hours follow the "
    "temperature of the night in which they occur. They are not three pieces of support. Shootings from 00:00 to "
    "05:59 of a date rise by 1.261 (1.140 to 1.396) in New York and 1.222 (1.125 to 1.328) in Chicago from 27 to "
    "33 C of that date's maximum, which comes later in the day (referee).\n"
    "Rivals not tested. Humidity was named in the registration and no variant addresses it; dew point is in the "
    "hourly airport files and not in GHCN-Daily, so the following-night result may be humid heat. A warm night "
    "also keeps people outdoors after midnight, and these data cannot separate that from a sleep path. On 36% of "
    "New York hot days and 38% of Chicago hot days the next date's minimum is more than 1 C lower, so the calendar "
    "minimum of date d was probably set in the evening; on those days the 'preceding' minimum partly measures the "
    "evening of the shooting day, which would raise its coefficient. Without those days part (a) is 1.063 (0.968 to "
    "1.168) and 1.031 (0.975 to 1.090), still unsettled.\n"
    "Threshold. The refutation threshold of 1.075 was derived from the calendar-day excess of 1.122. On the "
    "shooting days this claim uses, the excess is 1.051 (0.988 to 1.118) in New York and 1.035 (0.991 to 1.082) in "
    "Chicago, half of which is about 1.032 and 1.021 per 5 C of minimum. Both upper limits (1.109 and 1.054) are "
    "above those values as well. The threshold stays as registered.\n"
    "Code. run.py builds the following night's minimum and the previous day's maximum by shifting rows of the "
    "weather file and not calendar days. The Central Park file has no gap. The Midway file lacks 28 February 2012 "
    "and 16 August 2017 (re-checked), so on the four adjacent days the shifted value comes from two days away. With "
    "a calendar shift Chicago has 1,479 hot days and 13,503 shootings in place of 1,481 and 13,519, and the "
    "estimate is 1.009 (0.966 to 1.054) against 1.009 (0.967 to 1.054). The script is left as committed: it was "
    "fixed with the registration (rule 9), and the correction changes the registered count of days and one third "
    "decimal while changing no result.\n"
    "Order of events. The registration and script are on the remote branch prereg/heat-night-minimum (commit "
    "44edbc9, 01:24:38); the first query with a time of day was fetched at 01:24:57. Git records the commit time "
    "and not the push time, so the repository shows that the registration was committed 19 seconds before the "
    "fetch and cannot show that it was pushed before it.\n"
    "Stance. The stance is set to null. The value 0.416 was the z of the New York estimate against no effect, and "
    "on the strip it read as agreement with the research. The registration computed D = 0.13 and 0.37 and said the "
    "test is not an endpoint test of the chain; the realised z values are 0.88 against no effect, 0.53 against the "
    "composed 1.012 and -1.12 against the threshold, so the estimate does not favour any of the three.",
    "Referee: keep unsettled. After-midnight ratio restated per 5 C (1.11, not 1.13) and marked as selected after "
    "the data, with corrected p values; following-night control, placebos and untested humidity recorded; the "
    "three post hoc observations counted as one; row-shift error at the Midway gaps recorded; stance set to null.",
    "accepted; verdict kept, units and labels corrected, stance null",
    stance=None,
    stance_note="Null after the referee: the test cannot tell the graph-sized effect (1.012) from no effect "
                "(D = 0.13 and 0.37 as registered), and a stance computed against no effect showed an unsettled "
                "estimate as agreement with the research.",
    verdict_note="Unsettled: the preceding night's minimum is compatible with no effect, with the graph-sized 1.012 "
                 "and with half of the hot-day excess. The rise between 00:00 and 05:59 (about 1.11 per 5 C of "
                 "maximum in each city) was singled out after the data; it, the following-night ratio and the "
                 "calendar-day difference are one observation.",
)

# ---------------------------------------------------------------- earlier calendar-day heat claims

chk = json.loads((ROOT / "data/derived/round5/heat_night/night_of_check.json").read_text())
ny, chi, mo = chk["new_york"], chk["chicago"], chk["heat_mech_outdoors"]
cub = ny["rr_33_vs_27_cubic_spline"]
LEAD = f"After the referee of heat-night-minimum ({DATE})"
SRC = ("Exploratory, run after the outcomes, and deciding nothing under rule 4 "
       "(analyses/critique/round5_night_of_check.py; data/derived/round5/heat_night/night_of_check.json).")

# No registered condition of either claim changes side on night-of counts.
assert ny["irr_per_5c_night_of"]["lo"] > 1.0
assert mo["shootings_night_of"]["attenuation"] >= 0.25 and mo["shootings_night_of"]["attenuation_lo"] > 0.10
assert mo["shootings_night_of"]["mediator_coef_log1p"]["lo"] > 0
assert mo["shootings_night_of_year_by_month"]["attenuation"] >= 0.25


def att(k):
    a = mo[k]
    return f"{a['attenuation']:.2f} ({a['attenuation_lo']:.2f} to {a['attenuation_hi']:.2f})"


answer(
    "heat-shootings",
    "the registered count is by calendar date, and 35% of New York shooting incidents occur between 00:00 and "
    "05:59, before the maximum of the date they are counted on. The referee of heat-night-minimum raised this. "
    "With each shooting assigned to the day whose night it falls in (06:00 on date d to 05:59 on d+1), the "
    f"registered model gives {f3(ny['irr_per_5c_night_of'])} per 5 C against {f3(ny['irr_per_5c_calendar_day'])} "
    f"on calendar dates ({ny['n_days']:,} days, {ny['night_of_incidents']:,} incidents). The registered condition, "
    "a lower limit above 1.00, is met either way, and the estimate stays inside the registered 1.05 to 1.20. The "
    "average slope therefore does not depend on the assignment. The hot end does: with the piecewise-linear basis "
    f"of round 2 the ratio 33 against 27 C is {f3(ny['rr_33_vs_27_night_of'])} on night-of counts against "
    f"{f3(ny['rr_33_vs_27_calendar_day'])} on calendar dates, and with the 4-df cubic spline of this claim it is "
    f"{f3(cub['night_of'])} against {f3(cub['calendar_day'])}. A quarter to a half of the log rise above 27 C on "
    "calendar dates therefore comes from the assignment of small-hours shootings to the hot date. " + SRC,
    "Referee of heat-night-minimum: calendar-day counts include small-hours shootings that precede the day's "
    "maximum. Night-of re-estimate added to the notes; the registered condition is met either way.",
    "accepted; verdict kept, night-of re-estimate added",
    report="critique/heat-night-minimum.md",
    lead=LEAD,
)

answer(
    "heat-mech-outdoors",
    "the shootings series of this claim is counted by calendar date, so it includes shootings between 00:00 and "
    "05:59 that precede the day's maximum (35% of incidents). The referee of heat-night-minimum raised this. With "
    "shootings assigned to the night-of day (06:00 to 05:59) and the registered procedure otherwise unchanged (500 "
    f"week resamples, seed 1), the share removed by street-noise complaints is {att('shootings_night_of')} against "
    f"{att('as_registered')} as registered, and {att('shootings_night_of_year_by_month')} with year-by-month terms "
    f"(registered 0.32). The shootings slope is {f3(mo['shootings_night_of']['base_irr_per_5C'])} per 5 C and "
    f"{f3(mo['shootings_night_of']['adjusted_irr_per_5C'])} with the proxy. Complaints created between 00:00 and "
    f"05:59 are {100 * mo['early_noise_share']:.0f}% of the total; with complaints moved to the night-of day as "
    f"well the share is {att('both_night_of')}, and {att('both_night_of_year_by_month')} with year-by-month terms. "
    "Every registered condition is met under each assignment, so the calendar-day count did not produce the "
    "confirmation; the share is larger on night-of counts. The instability over time that the first referee found "
    "was not re-examined on night-of counts. The hot-end comparison is weaker than reported. The rise in shootings "
    f"from 27 to 33 C, scored above as 1.122 (1.072 to 1.173), is {f3(cub['night_of'])} on night-of counts with "
    f"the same 4-df spline and {f3(ny['rr_33_vs_27_night_of'])} with the piecewise-linear basis of round 2, whose "
    "interval includes 1. Complaints and bicycle counts still stop rising at 27 C; the excess in shootings that "
    "they do not explain is a quarter to a half smaller on the log scale than stated, and part of the stated excess "
    "is shootings after midnight on the hot date. " + SRC,
    "Referee of heat-night-minimum: calendar-day counts include small-hours shootings that precede the day's "
    "maximum. On night-of counts the share removed is 0.53 (0.41 to 0.66) and every registered condition is still "
    "met; the hot-day rise in shootings is smaller.",
    "accepted; verdict kept, night-of re-estimate added",
    report="critique/heat-night-minimum.md",
    lead=LEAD,
    prediction_scored=load("heat-mech-outdoors")["prediction_scored"] + " After the referee of heat-night-minimum: "
    "on night-of counts (06:00 to 05:59) A = 0.529 (0.406 to 0.665), and the rise in shootings from 27 to 33 C is "
    f"{f3(cub['night_of'])} with the same spline and {f3(ny['rr_33_vs_27_night_of'])} with the piecewise-linear "
    "basis.",
)

# ---------------------------------------------------------------- transfer-chicago-concordance-matrix

o = load("transfer-chicago-concordance-matrix")
notes = swap(
    o["notes"],
    "Three of the twelve agreeing pairs have a correlation below 0.1 in size (asthma with PM2.5 0.07, asthma with "
    "traffic 0.01, low birthweight with traffic 0.01); among",
    "Four of the twelve agreeing pairs have a correlation below 0.1 in size (asthma with PM2.5 0.07, depression "
    "with traffic 0.07, asthma with traffic 0.01, low birthweight with traffic 0.01; the count was given as three "
    "before the referee); among pairs with a deciding correlation of at least 0.1 in size Chicago agrees in 8 of 11 "
    "and New York in 4 of 13, and among")
# Stance against the referee's exposure-shuffle null (mean 7.53 pairs, SD 2.31), not against 0.370.
NULL_MEAN, NULL_SD = 7.5285, 2.3068
zs = [(k - NULL_MEAN) / NULL_SD for k in (12, 8, 13)]  # the count and the bootstrap limits 0.533 and 0.867 of 15
answer(
    "transfer-chicago-concordance-matrix",
    "the verdict is kept under rule 1 and its meaning is narrowed. The referee reproduced the counts, the interval "
    "(0.533 to 0.867 under another seed) and the correlations with separate code. Every registered support "
    "condition is met: 15 pairs, a share of 80%, a lower bootstrap limit of 0.533 against 0.370, and 12 against New "
    "York's 6 on the same pairs. verdict() in matrix.py did not check the last of these; it is met. What is "
    "confirmed is the count. The clause of the statement about the residential-sorting explanation is not tested by "
    "any registered condition, and the referee's results are evidence against reading the count as support for it.\n"
    "One exposure. The difference between the cities is PM2.5: 0 of 6 pairs in New York and 5 of 6 in Chicago. "
    "Without the PM2.5 pairs Chicago agrees in 7 of 9 and New York in 6 of 9. Six pairs that share one exposure are "
    "close to one observation.\n"
    "A regional gradient. Chicago's PM2.5 ranges from 8.63 to 9.33 micrograms per cubic metre (coefficient of "
    "variation 1.8%, against 10.7% in New York). A plane in the centroid coordinates explains 85% of its variance "
    "across community areas and 58% of ozone's; Moran's I is 0.83 for each. PM2.5 rises toward the southwest, and "
    "health is worse there. With the coordinates partialled out together with poverty, 1 of the 6 PM2.5 pairs "
    "agrees and Chicago agrees in 9 of 15 (New York 3 of 15). When PM2.5 is replaced by a plane tilted in each "
    "compass direction, 38% of directions give at least 5 of 6 positive pairs and 38% give at most 1 of 6. A "
    "contrast of 0.7 micrograms would not produce correlations of 0.35 to 0.55 with obesity, diabetes and early "
    "death through any causal path, so agreement with the literature's sign in Chicago says no more about the "
    "literature than disagreement did in New York.\n"
    "Dependence. With the Clifford and Richardson correction the effective number of areas is 12 to 31 for five of "
    "the six PM2.5 pairs (54 for asthma) and 16 to 45 for the ozone pairs, and at those sizes none of the fifteen "
    "correlations has p below 0.05 (smallest 0.08). The bootstrap resamples areas as independent, so its intervals "
    "are too narrow. The mean bootstrap share is 0.70, 3% of resamples fall below 60%, and leaving out one area "
    "gives 10 to 12 agreeing pairs.\n"
    "Chance and regression to the mean. When the three exposures are shuffled together across areas, the count has "
    "mean 7.5 and standard deviation 2.3; 12 or more occurs with probability 0.04, and a count as far from 7.5 in "
    "either direction with probability 0.08. Fisher's test of 12 of 15 against 6 of 15 gives 0.06 and assumes "
    "independent pairs. New York's 6 of 15 was known before registration and is low; on the other 60 pairs Chicago "
    "agrees in 43 and New York in 44, so a city with nothing particular about its pollution would be expected near "
    "70% on the fifteen pairs and would also have met the condition. The threshold 0.370 was registered as a "
    "constant although New York's 10 of 27 has its own sampling error.\n"
    "Controls. With foreign-born share, high-school completion or unemployment added to poverty, Chicago agrees in "
    "9 of 15, exactly the 60% threshold; with density added, in 12. Agreement is higher after partialling poverty "
    "(12) than before (10), so measured poverty does not carry the result. Racial segregation, which the "
    "registration named, is not measured in the indicator set.\n"
    "The two cities' PM2.5 measures differ in instrument (street-level survey against regional model) and in "
    "geography (highest in the dense core against highest in low-density areas), and with two cities the design "
    "cannot separate these from sorting.\n"
    "Not accepted. The report says there is no prereg branch for this claim. There is one: the remote holds "
    "refs/heads/prereg/transfer-chicago-concordance-matrix at commit 2805fb3, committed at 01:23:04 on 13 November "
    "2026 (git ls-remote, re-checked). It contains the registration and the three scripts, identical to those of "
    "commits 499547c and 0ba7f1a, and its commit time is four seconds before the first Chicago Health Atlas cache "
    "file (01:23:08). As for every claim, git records the commit time and not the push time, so the order of push "
    "and fetch cannot be shown from the repository. The referee's second option, unsettled, is not taken: rule 1 "
    "binds the verdict to the registered conditions, which are written on the count and are met under the "
    "registered seed, five others and the referee's; the sorting clause is in the statement and in no condition.",
    "Referee: keep confirmed under rule 1 for the count only. verdict_note added: the difference is PM2.5 alone, "
    "which in Chicago is a regional gradient, and the test does not test the sorting explanation; small "
    "correlations corrected to four; prediction (b) qualified; stance reduced. The referee's statement that no "
    "prereg branch exists is wrong and the note records the branch.",
    "mostly accepted; verdict kept under rule 1 for the count only, meaning narrowed, stance reduced; the "
    "statement about a missing prereg branch not accepted",
    notes=notes,
    verdict_note="Confirmed for the registered count only: 12 of 15 air and traffic pairs agree in Chicago against "
                 "6 of the same 15 in New York. The result does not test the residential-sorting explanation. The "
                 "difference is PM2.5 alone (5 of 6 against 0 of 6; without it 7 of 9 against 6 of 9), Chicago's "
                 "PM2.5 is 85% a regional plane with a range of 0.7 µg/m³, and with coordinates partialled out 1 of "
                 "6 PM2.5 pairs agrees. Effective n is 12 to 31, four agreeing pairs have |rho| below 0.1, and "
                 "against chance p is about 0.04 to 0.08.",
    prediction_scored=swap(
        o["prediction_scored"],
        "(b) hit: predicted +0.35 (0.10 to 0.60); the Spearman correlation of PM2.5 with poverty is +0.29 (+0.03 to "
        "+0.50) in Chicago and +0.11 (-0.23 to +0.43) in New York. The lower limit is close to zero (0.03 to 0.05 "
        "across seeds).",
        "(b) partial after the referee: predicted +0.35 (0.10 to 0.60); the Spearman correlation of PM2.5 with "
        "poverty is +0.29 (+0.03 to +0.50) in Chicago and +0.11 (-0.23 to +0.43) in New York. The registered "
        "scoring rule (a bootstrap interval that excludes zero) gives a hit, with a lower limit of 0.03 to 0.05 "
        "across seeds. The bootstrap treats areas as independent; with spatial dependence counted the effective "
        "number of areas is about 10 and p is 0.43, and the two cities' intervals overlap. The data therefore do "
        "not show that Chicago's high-PM2.5 areas are its poor areas.")
    + " After the referee: the hit on (a) is on the registered count. The count is 1.9 standard deviations above "
    "the mean of an exposure-shuffle null (p = 0.04 one-sided), and the difference from New York comes from the "
    "six PM2.5 pairs.",
    settle=o["settle"] + " After the referee: a test of the sorting explanation needs an exposure measure that is "
    "not a regional gradient (with centroid coordinates partialled out, 1 of 6 Chicago PM2.5 pairs agrees), a "
    "measure of segregation, and enough cities to relate agreement to the pollution-poverty correlation; two "
    "cities give one degree of freedom.",
    prereg={"branch": "prereg/transfer-chicago-concordance-matrix", "commit": "2805fb3",
            "committed_at": "2026-11-13T01:23:04-0500", "first_outcome_data_file": "2026-11-13T01:23:08-0500",
            "checked": "git ls-remote on 13 Nov 2026; content identical to commits 499547c and 0ba7f1a; the push "
                       "time is not recorded by git"},
    stance={"value": round(math.tanh(zs[0] / 2), 3), "lo": round(math.tanh(zs[1] / 2), 3),
            "hi": round(math.tanh(zs[2] / 2), 3), "z": round(zs[0], 2),
            "note": "Measured against the referee's exposure-shuffle null (mean 7.5 agreeing pairs of 15, SD 2.3), "
                    "which keeps the dependence among the fifteen pairs, and not against New York's 0.370 with a "
                    "bootstrap that treats areas and pairs as independent (the earlier z of 5.05). It is the "
                    "agreement of the count with the literature's sign, not support for the sorting explanation."},
)

print("done")
