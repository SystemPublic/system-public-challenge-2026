"""Answers to three blind referee reports of 13 Nov 2026 on the congestion-toll claims
(critique/bridge-crz-ems-travel.md, critique/crz-storefront-vacancy.md, critique/sim-crz-holdout-2026.md).

Each change goes through concord.claims.revise, which keeps the earlier outcome in `history`.
No registration is touched. One verdict changes: bridge-crz-ems-travel, confirmed to unsettled,
under rule 8. The other two verdicts are kept under rule 1 with a verdict_note.

Every referee number written into an outcome was reproduced by the answering agent, by re-running
  python -m analyses.critique.referee_crz ems
  python -m analyses.critique.referee_crz vacancy
  python -m analyses.critique.referee_sim_holdout
on 13 Nov 2026. The three scripts printed the values quoted below. Numbers computed for this
answer are derived in the code: z of the trend-adjusted estimate against the proportional fall,
the interval of S1 with the calibration error carried, the stance of the held-out claim, and the
number of ordinary days a day-level successor test would need.

Run once: ~/.venvs/nyc-concordance/bin/python analyses/critique/answer_round6_crz.py
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims as C

DATE = "13 Nov 2026"


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
    if new in text:
        return text
    assert old in text, old[:60]
    return text.replace(old, new)


# ---------------------------------------------------------------- bridge-crz-ems-travel

o = load("bridge-crz-ems-travel")
et = o["endpoint_test"]
D_null = et["D_vs_null"]
assert round(D_null, 2) == 0.14 and D_null < 4
# trend-adjusted variant (referee E3): log estimate -0.0317, se 0.0234; proportional fall log -0.0559
z_prop_trend = (-0.0317 + 0.0559) / 0.0234
assert round(z_prop_trend, 2) == 1.03

notes = swap(
    o["notes"],
    "Lives (composition, not a test): with 1331 attended cardiac arrests a year in the zone at peak hours, the "
    "measured change implies 0.3 lives a year (-0.7 to 2.0).",
    "Lives (composition, not a test and not a result): the number of lives a year among cardiac arrests in the zone "
    "at peak hours depends on which measured change is used, and its sign is not determined. The registered peak "
    "estimate gives +0.3 (-0.7 to +2.0), the difference of peak and overnight hours gives -1.4 (-4.1 to -0.2), total "
    "response time gives -0.3 (-4.6 to +2.9), and no effect gives 0.0 (-1.4 to +1.3).")

answer(
    "bridge-crz-ems-travel",
    "the verdict is changed from confirmed to unsettled under rule 8. The claim is a bridge with an endpoint test. "
    "Rule 8 measures discrimination against no effect: D = z_null^2 - z_chain^2 = 0.76^2 - 0.66^2 = 0.14, below 4. "
    "The registration computed D against a fall in proportion to speed (-5.4%), which gave 17.0, and named rules 1, "
    "2 and 8 for the verdict. A registration cannot replace the D that rule 8 defines, so rule 8 applies as written "
    "and the endpoint's agreement with the composed prediction does not decide. The registration said in advance "
    "that the test could not tell the chain from no effect. Round 4 changed graph-triad-cold-asthma-absence in the "
    "same way (D = 3.0). The referee simulated the registered rule at the observed standard error: it returns "
    "confirmed with probability 0.80 if the toll had no effect, 0.87 if the chain is true, 0.50 if travel time rose "
    "by 1% and 0.01 if it fell in proportion to speed. Any estimate from -3.04% to +0.99% met the support condition. "
    "What the registered estimate shows is narrower than the first label: with calendar-month terms it excludes a "
    "fall in proportion to speed (z = 4.18). That exclusion does not survive a linear trend in the pre-period: the "
    f"estimate is then -3.13% (-7.47 to +1.42) and z against the proportional fall is {z_prop_trend:.2f}. The trend "
    "term was chosen after the data and decides nothing under rule 4. The registered estimator run at 17 false start "
    "dates in 2023-24 gives estimates from -0.2% to +4.9% with a standard deviation of 0.016 on the log scale, "
    "against the HAC standard error of 0.011, so the registered interval is too narrow. No improvement is shown: the "
    "interval includes zero and a rise of 1.4%. The overnight control argues against the toll as the cause of the "
    "peak estimate. In overnight hours, when the toll is a quarter of the peak toll, the zone's relative travel time "
    "fell by 4.0% (1.7 to 6.3), and peak minus overnight is +3.3% (+1.4 to +5.2), which is 4.0 combined standard "
    "errors from the composed prediction and 3.5 from zero. The overnight series is not stable before the toll "
    "either (false starts in 2023-24 give +4.4% to +12.1%), so it is not a clean control. Incidents in the zone fell "
    "by 3.0% relative to the rest of the city at peak (-4.3 to -1.7) and overnight (-5.4 to -0.5), which would free "
    "units at all hours. Link 2 is not stable: the registered exponent 0.317 is fitted mostly on the pandemic "
    "months; without March 2020 to June 2021 the slope is -0.62 (se 0.10), for 2022-24 it is -0.49 (se 0.12) and for "
    "2023-24 it is -1.13 (se 0.40), which is a proportional response. The overnight ratio has nearly the same slope "
    "on taxi speed (-0.29, se 0.06) as the peak ratio, so the monthly co-movement is not specific to congested "
    "hours. The composed prediction is quoted as -1.68%, the median of the draws; the notes above give -1.8%, the "
    "mean of the log (-0.0178), and the z values use the mean. ZIP 10044 (Roosevelt Island) is in the zone list in "
    "analyses/congestion/common.py and is outside the toll zone; with the zone defined by dispatch areas M1 to M3, "
    "which exclude it, the peak estimate is -0.79% (-3.10 to +1.59). The script was fixed with the registration and "
    "is not corrected. Citywide, mean travel time rose from 559 s in 2023 to 607 s in 2024, 651 s in 2025 and 724 s "
    "in January to September 2026, and the share of incidents with no valid response time, which the analysis "
    "drops, rose from 4.4% to 6.3% in 2025 and 9.5% in 2026. The closure of Mount Sinai Beth Israel was registered "
    "as an alternative and has not been examined.",
    "Referee: rule 8 defines discrimination against no effect (D = 0.14), the registered rule confirms a no-effect "
    "world with probability 0.80, a trend term removes the exclusion of a proportional fall, the overnight control "
    "fell 4.0%, and the lives figure has no determined sign.",
    "accepted; verdict changed from confirmed to unsettled under rule 8; the lives figure is no longer reported as "
    "a result; the script is not corrected (rule 9)",
    verdict="unsettled",
    notes=notes,
    verdict_note="Unsettled under rule 8: the endpoint test cannot tell the composed chain from no effect (D = 0.14 "
                 "against no effect; the registered rule returns confirmed with probability 0.80 if the toll did "
                 "nothing). Peak ambulance travel time in the zone changed by -0.9% (-3.0 to +1.4) relative to the "
                 "rest of the city, so no improvement is shown. A fall in proportion to the 5.7% rise in taxi speed "
                 "is excluded by the registered estimate and not when a trend term is added. Overnight, when the "
                 "toll is a quarter as large, the zone's relative travel time fell by 4.0%, which argues against "
                 "the toll as the cause. The number of lives is not a result: between about -1.5 and +2 a year, "
                 "sign not determined, depending on the comparison used.",
    prediction_scored="not scored as a hit after the referee. The registered support condition is met (z_chain 0.66, "
                      "D against a proportional fall 17.0), but rule 8 measures discrimination against no effect, "
                      "where D is 0.14, so the endpoint does not decide. The interval includes zero, the exclusion "
                      "of a proportional fall does not survive a trend term (z 1.03), and the overnight control "
                      "moved further than the peak.",
    settle=o["settle"] + " After the referee: a design whose pre-toll false starts have a spread no larger than its "
    "standard error (the 17 false starts of 2023-24 run from -0.2% to +4.9%); travel times for life-threatening "
    "calls separately, which rose by 5.2% at peak with a 2024 placebo of +6.0%; and the dates and volumes of the "
    "Mount Sinai Beth Israel closure.",
    lives_note="Not a result. Lives a year among cardiac arrests in the zone at peak hours, by the measured change "
               "used: registered peak estimate +0.3 (-0.7 to +2.0); peak minus overnight -1.4 (-4.1 to -0.2); total "
               "response time -0.3 (-4.6 to +2.9); composed prediction +0.7 (0.0 to +2.5). The count of 1,331 "
               "attended arrests includes the 43% pronounced dead on scene, the all-incident estimate is applied to "
               "calls whose own travel time rose by 5.2%, and odds ratios per minute are applied to about 3 seconds.",
)

# ---------------------------------------------------------------- crz-storefront-vacancy

o = load("crz-storefront-vacancy")
notes = swap(
    o["notes"],
    "The same difference was -0.74, -1.40 and -0.45 in the three earlier years, mean -0.86, so the 2025 value is "
    "+0.39 points above that mean and equal to the 2024 value: the zone's faster recovery continued at its 2024 pace "
    "and slower than in 2022-23.",
    "The same difference was -0.45 in 2024, the one earlier year under the present filing structure, so the 2025 "
    "value equals the 2024 value. The values for 2022 and 2023 (-0.74 and -1.40) are not used as a trend, for the "
    "reason given in the referee note below.")
notes = swap(
    notes,
    "The test excludes a rise of 1.2 points (about 180 storefronts) in the zone's relative vacancy.",
    "The test excludes a rise of 1.2 points (about 180 storefronts) in the zone's vacancy relative to the whole "
    "rest of the city, counting sampling error only.")

answer(
    "crz-storefront-vacancy",
    "the verdict stays confirmed under rule 1. Both registered support conditions are met on the registered "
    "comparison, and they remain met in the referee's four variants: with the February filing added, -0.76 (-1.70 "
    "to +0.16); on tax lots present in both years, -0.36 (-0.95 to +0.25); with a bootstrap over ZIP codes, -0.47 "
    "(-1.19 to +0.24); without ZIP 10044 (Roosevelt Island, which is in the zone list and outside the toll zone), "
    "-0.46. The label covers less than its wording suggests, and the verdict_note now says what it covers. The "
    "negative difference comes from a rise elsewhere: zone vacancy rose by 0.18 points and vacancy outside rose by "
    "0.65. Against downtown Brooklyn and Long Island City, where vacancy fell by 0.91 points, the zone did worse by "
    "1.09 points (-0.60 to +2.85), an interval that includes zero and twice the threshold; that area has four ZIPs "
    "and about 2,100 storefronts. The registered interval covers the sampling of tax lots only. With the "
    "year-to-year standard deviation of the difference (0.48, from three values) added, the upper bound against "
    "zero is +0.67, and against the mean of 2022-24 the 2025 value is +0.39 with a standard error of 0.64 and an "
    "upper bound of +1.66, which does not exclude 1.2. The registry was restructured between reporting years '2022 "
    "and 2023' and 2023: one filing due in August became a main filing due in June and a separate February filing "
    "in which every row is vacant, and the coding of business activity changed. The 2023 difference of -1.40 "
    "compares a filing under the old structure with one under the new; with the February rows added it is +1.14. "
    "Only 2024 (-0.45) is a clean pre-toll year, so the registration's expectation of about -0.5 without a toll "
    "rests on one year, and the mean of three earlier years (-0.86) is withdrawn from the notes. Between the "
    "filings for 31 December 2020 and 2021 the registry lost 18% of its rows outside the zone and 9% inside. The "
    "threshold of 1.2 points is the resolution of the test: the plan chose it as the effect at which the design "
    "reaches a discrimination of about 4, before the 2025 values were seen. It is not an effect size from the "
    "retail literature. The two papers in the registration (London and Stockholm) concern retail sales, were cited "
    "from memory, have not been checked against their texts, and supply no number to the test. Within the zone the "
    "change runs from -4.0 points (ZIP 10038) to +2.1 (10036) among ZIPs with 300 or more storefronts. Commercial "
    "leases commonly run five to ten years, so one filing after the toll cannot tell no effect from a delayed one.",
    "Referee: keep confirmed; the label overstates. The exclusion of 1.2 points holds against the whole rest of the "
    "city with sampling error only, and not against the zone's earlier trend or downtown Brooklyn and Long Island "
    "City; the 2023 pre-trend value spans a change in the filing structure; the threshold is the test's resolution.",
    "accepted; verdict kept under rule 1 with a verdict_note; the mean of three earlier years withdrawn; the two "
    "citations marked unverified",
    notes=notes,
    verdict_note="Confirmed on the registered comparison only. Zone vacancy itself rose by 0.2 points in the first "
                 "year, and vacancy in the rest of the city rose by 0.65. A rise of 1.2 points relative to the whole "
                 "rest of the city is ruled out, with sampling error only, and nothing smaller is. It is not "
                 "excluded against the zone's earlier trend (upper bound +1.66) or against downtown Brooklyn and "
                 "Long Island City (upper bound +2.85). The 2023 pre-trend value spans a change in the registry's "
                 "filing, so 2024 is the only clean pre-toll year. The 1.2 threshold is the resolution of the test, "
                 "and the two cited papers are unverified. Sales, rents and effects that take more than one lease "
                 "cycle are not tested.",
    prediction_scored=o["prediction_scored"] + ". After the referee: the hit is on the comparison with all other "
    "city ZIPs and on sampling error alone; with the year-to-year movement of the difference added the upper bound "
    "against zero is +0.67.",
    literature_note="The two citations in the registration (Quddus, Carmel and Bell 2007; Daunfeldt, Rudholm and "
                    "Ramme 2009) were written from memory and have not been checked against the papers. Nothing in "
                    "the test depends on them.",
)

# ---------------------------------------------------------------- sim-crz-holdout-2026

o = load("sim-crz-holdout-2026")
ce = dict(o["city_effect"])
s1 = ce["estimate"]
se_cal = 0.088                        # referee section 1: delta method, calibration se carried
lo_c, hi_c = s1 - 1.96 * se_cal, s1 + 1.96 * se_cal
assert (round(lo_c, 2), round(hi_c, 2)) == (0.11, 0.46)
thr = 0.5                             # the registered refutation threshold
zs = [(x - thr) / se_cal for x in (s1, lo_c, hi_c)]
# a successor on ordinary days: se of S1 without the four low days is 0.539 / 0.409 on 119 days;
# D = (1 / se)^2 >= 4 needs se <= 0.5
se_ord = 0.539 / 0.409
days_needed = 119 * (se_ord / 0.5) ** 2
assert round(se_ord, 2) == 1.32 and 800 < days_needed < 850
ce["label"] = ("S1: held-out elasticity of zone taxi speed to vehicle entries as a ratio of the elasticity fitted on "
               "2025 (-0.409); non-holiday weekdays 5 January to 30 June 2026, by band of hours. The estimate is "
               "fixed by two storm days (23 February and 26 January 2026), which carry 84% of the identifying "
               "variation; without them S1 is -0.23 with a standard error of 1.05")
ce["interval_with_calibration_error"] = {"lo": round(lo_c, 2), "hi": round(hi_c, 2), "se": se_cal}

ps = swap(o["prediction_scored"],
          "because entries fell (-8.3% in the morning band, -6.7% at midday) while speed also fell",
          "because entries fell (-8.3% in the morning band and -6.7% at midday as differences of mean logs, which "
          "the two storm days enlarge; -6.1% and -5.5% as ratios of means) while speed also fell")

answer(
    "sim-crz-holdout-2026",
    "the verdict stays contested under rule 1. The registered refutation condition is met, it remains met when the "
    "error of the fitted elasticity is carried into the ratio (standard error 0.088, interval 0.11 to 0.46), and no "
    "rule allows a day to be excluded after the data. The verdict means that the fitted link did not predict the "
    "held-out days as registered. It does not measure the elasticity on ordinary days. After the registered fixed "
    "effects, 23 February carries 74% and 26 January 10% of the variation in log entries of the held-out period. On "
    "23 February entries were 78% to 95% below normal by band and taxi speed was 18% to 71% above normal; a constant "
    "elasticity of -0.41 predicts a rise of about 150% for a 90% fall in entries, so those days show that the "
    "log-linear form fails at large changes. Without 23 February alone the upper bound of S1 is 0.51 and the "
    "refutation condition is not met. On the remaining days the held-out elasticity runs from +0.10 (se 0.43) "
    "without the two storm days to -0.47 (se 0.36) without the eight days under 0.90 of median entries, -0.93 (se "
    "0.16) without the 22 days under 0.95 and -1.14 (se 0.16) on dry days. Day-level data cannot identify the "
    "relation in either year. In 2025 the residual standard deviation of log entries is 0.032, 65% of band-days lie "
    "within 2% of their expected entries and 93% within 5%, and the day after Thanksgiving alone carries 31% of the "
    "variation. The 2025 coefficient falls from -0.41 to -0.09 (se 0.11) when the number of taxi trips inside the "
    "zone is added and returns to -0.37 when mean trip distance is also added; it differs from zero only in the last "
    "quarter. Taxi and for-hire entries, which do not respond to the entry toll, have the same coefficient as other "
    "entries (-0.22 each). The level miss of the speed link cannot be assigned to the link. From January 2026 taxi "
    "speed fell across the city: trips under three miles that neither start nor end in the zone slowed by 10.1%, "
    "13.1%, 5.4%, 4.0%, 4.3% and 2.6% in January to June against a year earlier, and trips inside the zone by 8.5%, "
    "13.2%, 6.0%, 5.9%, 5.4% and 9.4%. In December 2025 both were within about 2% of the year before. Within 1,344 "
    "pairs of origin and destination zones speed fell 8.9%, with recorded miles per trip down 1.1% and minutes up "
    "8.6%. Both vendors show the fall. Bus speeds do not: in the zone they fell 3.9% over the half-year, mostly in "
    "January to March, and outside it 0.6%. Weather explains a small part (the 2026 effect on log speed is -0.066, "
    "se 0.009, with weather controls). The cause was not found. Until it is, the taxi speed series should not be "
    "compared across the two years. The ambulance link does not depend on the low days: S2 is 1.22 (0.76 to 1.69) "
    "without the two storm days and 1.12 (0.60 to 1.64) without the eight days under 0.90, and its D against no "
    "relation is 32. Its size falls from about -0.6 to about -0.4 within weeks (-0.39, se 0.09) or on dry days "
    "(-0.38, se 0.12), so part of the registered slope is weather that slows taxis and ambulances together. The "
    "holiday list holds federal holidays only, and the night band joins the end of one night with the start of the "
    "next; neither changes a number that decides the verdict. The stance was +0.994, computed against no relation, "
    "which placed a contested claim at the agreeing end. It is now measured against the registered threshold. No "
    "successor was registered. On ordinary days the standard error of S1 is 1.32 on 119 days; a discrimination of 4 "
    f"between S1 = 1 and S1 = 0 needs a standard error of 0.5, which is about {days_needed:.0f} ordinary weekdays, "
    "more than three years, so a day-level test with the data to autumn 2026 could not fail (rule 8).",
    "Referee: keep contested; two storm days fix S1; entries vary about 3% within the fixed effects, so day-level "
    "data cannot identify the relation; taxi speed fell citywide from January 2026 and bus speed did not; the stance "
    "is at the wrong end; ten defects in the simulator.",
    "accepted; verdict kept under rule 1; verdict_note and effect label rewritten; stance measured against the "
    "registered threshold; no successor registered because a day-level test could not fail; simulator revised "
    "separately (docs/policy_simulation.md)",
    city_effect=ce,
    prediction_scored=ps,
    verdict_note="Contested as registered: the link fitted on 2025 did not predict the held-out days. The held-out "
                 "slope rests on two storm days (23 February and 26 January 2026), which carry 84% of the "
                 "identifying variation; without 23 February alone the verdict would be unsettled, and on the "
                 "remaining days the held-out elasticity is between +0.1 and -1.1 depending on how 22 winter days "
                 "are treated. Vehicle entries vary by about 3% within the fixed effects, so day-level data cannot "
                 "identify the relation in either year. Taxi speeds fell across the city from January 2026 (trips "
                 "wholly outside the zone slowed equally and bus speeds did not; the cause was not found), so the "
                 "level miss cannot be assigned to the link. The ambulance link transferred in slope (S2 = 1.10, "
                 "0.72 to 1.48) and does not depend on the storm days.",
    settle=o["settle"] + " After the referee: the cause of the citywide fall in taxi speed from January 2026, which "
    "bus speeds do not show. A day-level successor test was not registered, because about 830 ordinary weekdays "
    "would be needed for it to discriminate.",
    stance={"value": round(math.tanh(zs[0] / 2), 3), "lo": round(math.tanh(zs[1] / 2), 3),
            "hi": round(math.tanh(zs[2] / 2), 3), "z": round(zs[0], 2),
            "note": "Measured against the registered refutation threshold, S1 = 0.5 (half the fitted elasticity), "
                    "with the error of the fitted elasticity carried (se 0.088). The earlier value, +0.994, was "
                    "measured against no relation and placed a contested claim at the agreeing end. The value "
                    "rests on two storm days; without them S1 is -0.23 (se 1.05) and the stance is not "
                    "determined."},
)

print("done")
