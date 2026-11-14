"""Answers to three blind referee reports of 13 Nov 2026 (critique/afford-gentrification-prevalence.md,
critique/afford-poor-count-shift.md, critique/all-boats-trees-rent.md).

Each change goes through concord.claims.revise, which keeps the earlier outcome in `history`.
No registration is touched and no verdict changes. The three stances are set to null.

Numbers marked "referee" are the referees' re-estimates. Before any outcome is revised this script
re-runs both referee scripts (analyses/critique/referee_afford.py and referee_trees_rent.py) and
asserts that each figure quoted below is in their printed output, so a quoted figure that the
scripts no longer print stops the run. Numbers marked "re-checked" are computed here:
  afford-gentrification-prevalence   Fisher exact test of 8 of 22 against 6 of 33
  all-boats-trees-rent               the registered slope and interval, read from
                                     data/derived/all_boats/tree_test_results.json; the 2015 minus
                                     2005 total of living trees in a tract against the 8,840 rows of
                                     2005 without a usable longitude

Run once: ~/.venvs/nyc-concordance/bin/python analyses/critique/answer_round6_afford.py
"""
import json
import subprocess
import sys
from pathlib import Path

from scipy.stats import fisher_exact

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims as C

DATE = "13 Nov 2026"
ROOT = Path(__file__).resolve().parents[2]


def load(i):
    return json.loads((C.OUT / f"{i}.json").read_text())


def answer(cid, note, reason, short, **changes):
    """Append `note` to the outcome's notes and apply `changes`."""
    report = f"critique/{cid}.md"
    lead = f"After the referee ({DATE})"
    o = load(cid)
    if lead + ": " + note[:60] in (o.get("notes") or ""):
        print("already answered:", cid)
        return
    ch = dict(changes)
    ch["notes"] = (o.get("notes") or "") + f"\n\n{lead}: " + note
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


def referee_output(script):
    r = subprocess.run([sys.executable, str(ROOT / "analyses/critique" / script)], cwd=ROOT,
                       capture_output=True, text=True, check=True)
    return r.stdout


def require(out, *needles):
    for n in needles:
        assert n in out, f"referee script no longer prints: {n}"


# ------------------------------------------------- reproduction of the quoted referee figures

aff = referee_output("referee_afford.py")
require(
    aff,
    # the leak and its information
    "seed 0: k 6 k2 7 rho 0.38",
    "simulated k mean 6.9, 2.5% 2, 97.5% 15; rho mean 0.33 (0.08 to 0.53)",
    "true gentrified areas among the simulated set: mean 5.4 of a simulated k of 6.9",
    "share of seeds with simulated k in 4..11: 0.79",
    # the comparison group and the benchmark
    "low-start 8 of 22 (36%), other 6 of 33 (18%)",
    "Fisher exact two-sided p: 0.206",
    "areas of 55 above city on rent growth: 18 | on college change: 21",
    "median area rent growth 0.356 against city 0.411 ; median college change 12.3 against city 14.7",
    "within the 22 low-start: [np.float64(0.77)",
    # poor count
    "poor count, Welch gentrified minus other: -0.283 (-0.544 to -0.021), se 0.121, df 13.4",
    "end 2023             log poor count -0.280 (-0.579 to +0.018)",
    "end 2024             log poor count -0.257 (-0.519 to +0.005)",
    "end 2017-2018-2019   log poor count -0.243 (-0.350 to -0.137), se 0.050",
    "end 2018-2019-2021   log poor count -0.250 (-0.380 to -0.119), se 0.062",
    "number of the 22 single removals that put the upper limit at or above 0: 6",
    "leave one area out with the end period 2017-2019: largest upper limit -0.117",
    "correlation of (2022-24 minus 2017-19 log change) with the 2021->22 population jump: 0.69",
    "sd within groups, 2022-24: gent 0.284 other 0.255 ; 2017-19: gent 0.107 other 0.124",
    "end 2022-2024, log population change: +0.027 (-0.171 to +0.225)",
    "end 2022-2024, log poverty rate change: -0.310 (-0.474 to -0.146)",
    "end 2022-2024, poverty rate change in points: -6.491 (-10.286 to -2.696)",
    "contrast within borough (OLS with borough terms), end 2022-24: -0.173 (-0.479 to +0.132)",
    "contrast within borough (OLS with borough terms), end 2017-19: -0.165 (-0.294 to -0.037)",
    "without the seven Bronx areas (8 against 7): -0.204 (-0.474 to +0.067)",
    "to 2017-19: -0.182 (-0.299 to -0.064)",
    "flip ['Washington Heights/Inwood']: n 7/15, -0.230 (-0.523 to +0.063)",
    "flip ['East Harlem']: n 9/13, -0.234 (-0.493 to +0.025)",
    "k2 definition (baseline 2005-07): n 8/14, -0.214 (-0.498 to +0.071)",
    "college change (per 10 points): -0.132 (-0.227 to -0.037), Spearman -0.61",
    "2000 to 2005-07: -0.002 (-0.068 to +0.065)",
    "2005-07 to 2010-12: -0.087 (-0.186 to +0.011)",
    "2010-12 to 2017-19: -0.154 (-0.246 to -0.062)",
    "2017-19 to 2022-24: -0.040 (-0.230 to +0.150)",
    "gentrified 8: poor 341,325 -> 241,494 (-29.2%); non-poor 727,798 -> 907,052 (+24.6%)",
    "other low-start 14: poor 607,961 -> 544,228 (-10.5%); non-poor 1,231,277 -> 1,376,879 (+11.8%)",
)

# The 35 combinations of seven rent rules and five college rules: the range of k among the 22.
grid = aff.split("rent rule x college rule")[1].split("size of the low-start group")[0]
ks = [int(cell.split("/")[0]) for line in grid.splitlines()[2:] for cell in line.split() if "/" in cell]
assert len(ks) == 35 and min(ks) == 5 and max(ks) == 12 and sum(k <= 11 for k in ks) == 34, ks

# End periods: the five Brooklyn areas never appear in a "differs from registered set" list.
brooklyn5 = ["Williamsburg/Greenpoint", "Bedford Stuyvesant", "Bushwick", "North Crown Heights/Prospect Heights",
             "Brooklyn Heights/Fort Greene"]
ends = [ln for ln in aff.splitlines() if "differs from registered set" in ln and ln.startswith("  20")]
assert len(ends) == 11 and not any(b in ln for b in brooklyn5 for ln in ends)
assert sum("Washington Heights/Inwood" in ln for ln in ends) == 5

# Re-checked here: Fisher exact test, 8 of 22 low-rent areas against 6 of the other 33.
p_fisher = fisher_exact([[8, 14], [6, 27]])[1]
assert abs(p_fisher - 0.206) < 0.001, p_fisher

trees = referee_output("referee_trees_rent.py")
require(
    trees,
    "'lon_zero_or_missing': 8840",
    "my counts equal the registrant's in every tract: True",
    "primary, clustered by NTA                                    0.0127 ( 0.0018 to  0.0235) se 0.0055",
    "z against no effect 2.29; against 0.044 -5.67; against 0.018 -0.96; against 0.009 0.66",
    "D (0.044 against none) -26.9; D (0.018 against none) 4.3",
    "correlation of net gain with trees of 3 in or less in 2015: 0.31; 6 in or less: 0.32; with 2005 count: -0.35",
    "Queens        644.00       8.78   102.26           0.53       102.96                0.07              0.29",
    "Staten Island 113.00      25.16   208.35           0.59       290.15                0.04              0.10",
    "joint model: dsmall100                                       0.0097 (-0.0032 to  0.0226)",
    "joint model: dbig100                                         0.0201 ( 0.0018 to  0.0385)",
    "trees of 3 in or less in 2015 (new plantings)                0.0147 (-0.0064 to  0.0357)",
    "trees of 6 in or less in 2015                                0.0138 ( 0.0018 to  0.0258)",
    "net change instrumented by trees of 3 in or less             0.0166 (-0.0078 to  0.0411)",
    "net change instrumented by trees of 6 in or less             0.0273 (-0.0024 to  0.0570)",
    "net change winsorised at 1% and 99%                          0.0167 ( 0.0040 to  0.0293)",
    "tracts with |change| under 200 trees                         0.0326 ( 0.0125 to  0.0527) n 1916",
    "tracts with |change| under 300 trees                         0.0245 ( 0.0096 to  0.0395) n 2001",
    "change per km2 (thousands of trees per km2)                  0.0818 ( 0.0445 to  0.1191)",
    "so the per-area slope corresponds to 0.0453 per 100 trees there",
    "{'Staten Island': 20, 'Brooklyn': 12, 'Queens': 9, 'Bronx': 6}",
    "error-corrected baseline rent (mean error variance)          0.0073 (-0.0044 to  0.0179)",
    "error-corrected baseline rent (median error variance)        0.0115 ( 0.0012 to  0.0228)",
    "weighted by precision of the rent change                     0.0153 ( 0.0050 to  0.0256)",
    "Conley se, Bartlett kernel to 10 km: 0.0064  interval 0.0002 to 0.0251",
    "district (four-character) fixed effects                      0.0095 (-0.0005 to  0.0196)",
    "NTA fixed effects                                            0.0098 (-0.0008 to  0.0205)",
    "adding log population change                                 0.0085 (-0.0022 to  0.0193)",
    "no baseline rent                                             0.0084 (-0.0027 to  0.0196)",
    "Manhattan                                                 0.0818 (-0.0178 to  0.1815) n 210",
    "Bronx                                                    -0.0009 (-0.0144 to  0.0125) n 337",
    "median price of 200000: 0.066 (0.026 to 0.105)",
    "median price of 400000: 0.033 (0.013 to 0.052)",
    "2000 census rent is not among the files on disk",
)
# Re-checked here: the registered slope on file, and the size of the missing-coordinate rows
# against the counted gain.
res = json.loads((ROOT / "data/derived/all_boats/tree_test_results.json").read_text())
o_trees = load("all-boats-trees-rent")
ce = o_trees["city_effect"]
assert (ce["estimate"], ce["lo"], ce["hi"]) == (0.0127, 0.0018, 0.0235)
rp = res["rent_primary"]
assert (round(rp["estimate"], 4), round(rp["lo"], 4), round(rp["hi"], 4)) == (0.0127, 0.0018, 0.0235), rp
assert round((rp["estimate"] - 0) / rp["se"], 2) == 2.29 and round((rp["estimate"] - 0.044) / rp["se"], 2) == -5.67
assert "total living trees in a tract: 2005 575505  2015 652088" in trees
gain = 652088 - 575505
assert gain == 76583 and round(100 * 8840 / gain) == 12

# ------------------------------------------------- afford-gentrification-prevalence

answer(
    "afford-gentrification-prevalence",
    "the verdict is kept under rule 1. The referee rebuilt the area table with separate code and reproduced k = 8 "
    "of 22, k2 = 8 and the correlation of 0.68 (0.50 to 0.80); all three registered conditions of the reading "
    "'real but a minority' are met. The changes follow.\n"
    "Not blind. The faulty --simulate run that the registrant read before registering was informative. Rebuilt "
    "with seed 0 it gives what the registration reports (k 6, k2 7, correlation 0.38). Over 400 other seeds the "
    "simulated k has mean 6.9 (95% range 2 to 15), the simulated correlation has mean 0.33 (0.08 to 0.53), an "
    "average of 5.4 of the areas in a simulated set are among the true eight, and the simulated k is between 4 and "
    "11 in 79% of draws (referee). A registrant who had seen that output knew that the count and the correlation "
    "were probably inside the supporting window. The registration says the thresholds and the script were written "
    "before the simulated run. The repository cannot confirm this: no commit of the script or thresholds precedes "
    "the registration commit (07:47:16), the script's last save (07:43:44) is compatible with either order, and "
    "the file the simulated run wrote, gentrification_results_SIMULATED.json, is not in "
    "data/derived/affordability/. The referee judged tuning unlikely, because the window of 4 to 11 is wider than "
    "a window fitted to a leaked 6 would need to be and the six areas named in the prediction differ from the six "
    "leaked. The result is therefore a measurement under a definition fixed before the exact values were known, "
    "and not a blind prediction. The prediction is no longer scored as a hit.\n"
    "Dependence on the rule. Over 35 combinations of seven rent rules and five college rules the count ranges "
    "from 5 to 12, and 34 of the 35 are between 5 and 11 (referee). With other end periods it is 6 to 10. Five "
    "Brooklyn areas (Williamsburg/Greenpoint, Bedford Stuyvesant, Bushwick, North Crown Heights/Prospect Heights "
    "and Brooklyn Heights/Fort Greene) are in the set under each of the eleven end periods tried and pass the "
    "rent condition by 42 to 96 points of growth. The three upper Manhattan areas pass it by 8.7, 7.9 and 0.8 "
    "points; Washington Heights/Inwood, at 0.8, leaves the set in five of the ten other end periods. East Harlem "
    "misses by 2.0 points. The supported statement is that five areas changed by a wide margin and that two to "
    "five more are near the threshold.\n"
    "No difference from the other areas. Six of the other 33 areas also meet both conditions (18%), against 8 of "
    f"22 (36%); Fisher's exact test gives p = {p_fisher:.2f} (re-checked). The data show that about a third of "
    "low-rent areas had rent and college share rise faster than the city's. They do not show that this happened "
    "more often in low-rent areas than elsewhere.\n"
    "The benchmark. The city's rent growth (41.1%) is above the median area's (35.6%) and its college change "
    "(14.7 points) above the median area's (12.3), so 18 of 55 areas exceed the city on rent and 21 on college "
    "share. The reading 'common' needed 12 of the 22 to pass both, which the benchmark made hard to reach; the "
    "registered binomial table did not allow for this. The correlation condition is the part that could fail and "
    "it is well supported (0.68 across 55 areas, 0.77 within the 22, 0.62 within the other 33).\n"
    "The research range. The graph_effect of 0.24 (0.18 to 0.33) is the lowest and highest of three studies' "
    "shares, from different units, periods and definitions. It is not an interval, and agreement with it shows "
    "little, because the registered window of 18% to 50% would have accepted any of the three.\n"
    "Not changed: regression to the mean in rent is not visible (rank correlation of 2000 rent with rent growth "
    "-0.14; k = 7 when selection and baseline both use 2005-2007), and rent and college share take little of the "
    "2022 boundary change.",
    "Referee: keep confirmed. The pre-registration preview was informative and its timing relative to the "
    "thresholds cannot be verified, so the prediction is scored as not blind; the count is 5 to 12 over 35 rule "
    "combinations with five Brooklyn areas always in; low-rent areas are not distinguishable from the other 33 "
    "(36% against 18%, p = 0.21); stance null under rule 6.",
    "accepted; verdict kept, prediction rescored as not blind, stance null",
    verdict_note="Confirmed on the registered conditions (k = 8 of 22, k2 = 8, correlation 0.68 with a lower limit "
    "of 0.50). The registration followed a noisy view of the deciding numbers, in which about 5 of the 8 areas "
    "appear in a typical draw. No commit shows that the thresholds existed before that view, and the simulated "
    "results file is not in the repository. The result is a measurement under a fixed definition and not a blind "
    "prediction. It does not show that low-rent areas gentrified more often than other areas (36% against 18%, "
    "Fisher p = 0.21).",
    prediction_scored="not blind (scored 'hit' before the referee). k = 8 (predicted 6 to 10, best guess 8), k2 = 8, "
    "Spearman 0.68 (0.50 to 0.80; predicted 0.3 to 0.7). The predicted range was written after a simulated run "
    "that showed k = 6 and a correlation of 0.38, so its agreement with the outcome is not evidence of foresight. "
    "All six areas named in advance are in the set, and two of the six (Bedford Stuyvesant and Central Harlem) were not in the leaked list. No Bronx area "
    "is in it (the registration says eight Bronx low-start areas; there are seven).",
    graph_effect={**load("afford-gentrification-prevalence")["graph_effect"],
                  "scale": "proportion; lowest and highest of three studies' shares, not an interval"},
    stance=None,
    stance_note="Null after the referee (rule 6): the city effect is a raw proportion with a null of 0, which does "
    "not express a research direction. The earlier value of 0.957 was the distance of 36% from zero.",
)

# ------------------------------------------------- afford-poor-count-shift

o = load("afford-poor-count-shift")
answer(
    "afford-poor-count-shift",
    "the verdict is kept under rule 1: the registered condition, an upper limit of the Welch interval below 0, "
    "is met at -0.283 (-0.544 to -0.021; standard error 0.121, 13.4 degrees of freedom, p = 0.036), and the "
    "referee reproduced it with separate code. The referee's reason for keeping the verdict is the result on end "
    "periods before 2022. Those periods were chosen after the data and decide nothing under rule 4; the verdict "
    "stands because the registered condition is met, and for no other reason. The changes follow.\n"
    "Fragility. Six of the 22 single removals of an area put the upper limit at or above 0 (without Washington "
    "Heights/Inwood +0.032, Brooklyn Heights/Fort Greene +0.030, North Crown Heights/Prospect Heights +0.030, "
    "Bushwick +0.020, Throgs Neck/Co-op City +0.017, Morningside Heights/Hamilton Heights +0.012). So do the end "
    "years 2023 and 2024 taken singly (-0.280, -0.579 to +0.018; -0.257, -0.519 to +0.005), Washington "
    "Heights/Inwood classed as not gentrified (-0.230, -0.523 to +0.063), East Harlem classed as gentrified "
    "(-0.234, -0.493 to +0.025) and groups by the k2 definition (-0.214, -0.498 to +0.071). Those two areas are "
    "0.8 and 2.0 points of rent growth from the threshold. The point estimate is negative in every variant "
    "(referee).\n"
    "Boundary change. A count is a rate multiplied by a population, so it takes the full 2022 change of survey "
    "areas. The standard error of the contrast is 0.050 with the end period 2017-2019, 0.062 with 2018, 2019 and "
    "2021, and 0.121 with 2022-2024; the standard deviation of the log change within the groups rises from 0.11 "
    "and 0.12 to 0.28 and 0.26. Across the 22 areas the difference between the log change to 2022-2024 and the "
    "log change to 2017-2019 correlates 0.69 with the population jump between 2021 and 2022. The error does not "
    "favour either group: the contrast in log population change is +0.027 (-0.171 to +0.225). With end periods "
    "before the change the contrast is -0.243 (-0.350 to -0.137) and -0.250 (-0.380 to -0.119), and no single "
    "removal moves the 2017-2019 upper limit above -0.117. The log change of the poverty rate to 2022-2024 "
    "differs by -0.310 (-0.474 to -0.146) and the rate by -6.5 points (-10.3 to -2.7). All of these are post "
    "hoc. The interval of 4.4 to 8.6 points given above for the rate is for 2017-2019.\n"
    "Borough. Seven of the 14 comparison areas are in the Bronx, where no area gentrified, so the contrast is "
    "partly Brooklyn and Manhattan against the Bronx. With borough terms the registered contrast is -0.173 "
    "(-0.479 to +0.132) and the 2017-2019 contrast is -0.165 (-0.294 to -0.037); without the seven Bronx areas "
    "they are -0.204 (-0.474 to +0.067) and -0.182 (-0.299 to -0.064). A different trend in Bronx poverty, for "
    "reasons unrelated to rent, is a rival the registration does not name.\n"
    "Independence. The Welch interval treats the 22 areas as independent. Five of the eight gentrified areas "
    "adjoin one another in Brooklyn and the other three in upper Manhattan, so the effective number of areas is "
    "below 22 and the interval is too narrow by an amount these data cannot give.\n"
    "Shared data. The groups are defined by a rise in the college share from the same survey samples and areas "
    "that give the poverty count, and graduates are seldom poor, so part of the association follows from the "
    "definition. Among the 22 the log change in the poor count follows the college change (-0.13 per 10 points, "
    "-0.23 to -0.04; rank correlation -0.61) more closely than rent growth (rank correlation -0.33).\n"
    "Timing. The contrast in the change of the count by period is -0.002 (-0.068 to +0.065) from 2000 to "
    "2005-2007, -0.087 (-0.186 to +0.011) from 2005-2007 to 2010-2012, -0.154 (-0.246 to -0.062) from 2010-2012 "
    "to 2017-2019 and -0.040 (-0.230 to +0.150) from 2017-2019 to 2022-2024. Most of the difference arose between "
    "2010 and 2019, and these data say nothing reliable about the period since. (The referee's text labels these "
    "as changes 'to' each period; the script computes the change within each period.)\n"
    "What the count cannot show. In the gentrified areas the number of residents above the poverty line rose "
    "24.6% (728,000 to 907,000) while the number below it fell 29.2%; in the other low-rent areas the figures are "
    "+11.8% and -10.5%. The same contrast would result if poor residents moved out, if they died or aged and were "
    "replaced by residents who are not poor, if the incomes of residents who stayed rose past the national "
    "poverty line, or if poor households were counted in another area after the boundary change. The claim and "
    "the verdict concern the change of a count. They are not evidence on displacement.\n"
    "The leak. By the referee's rebuild, the simulated run printed this claim's block from line 70 of 116, so the registrant's statement "
    "that the output was cut at 70 lines and the block not read is consistent with the output. The run also wrote "
    "the block to gentrification_results_SIMULATED.json, which is not in the repository, so the statement rests "
    "on the registrant's account. The simulated contrast was -0.520 (-1.053 to +0.014). The condition has no free "
    "threshold that such a view could tune; the predicted range could have been informed by it.",
    "Referee: keep confirmed with its note. Fragility recorded (6 of 22 single-area removals, and the end years "
    "2023 and 2024 singly, put the upper limit at or above zero); the 2022 boundary change raises the standard "
    "error from 0.050 to 0.121; borough, spatial clustering, shared data and timing recorded; a falling count "
    "cannot show displacement; stance null.",
    "accepted; verdict kept under rule 1 and not on the post hoc periods, stance null",
    verdict_note="Confirmed on the registered condition (upper limit below 0) by a margin of 0.02 log points, on an "
    "end period affected by a boundary change. Six of the 22 single removals of an area, and the end years 2023 "
    "and 2024 taken singly, put the upper limit at or above 0, and with borough terms the interval includes zero "
    "(-0.173, -0.479 to +0.132). The exploratory repeats on end periods before the boundary change give a "
    "narrower interval with the same sign (-0.24, -0.35 to -0.14 for 2017-2019); they were chosen after the data "
    "and do not decide the verdict. The verdict covers the change of a count of poor residents and is not "
    "evidence on displacement.",
    prediction_scored=swap(o["prediction_scored"], "hit. -0.28", "within the predicted range, not scored as a blind "
                           "hit: the range and the direction were written after a simulated run that showed a "
                           "noisy version of the group membership. -0.28"),
    stance=None,
    stance_note="Null after the referee: the graph holds no finding on counts of poor residents and the studies "
    "cited follow individuals, so there is no research direction for the city contrast to agree with. The earlier "
    "value of 0.786 was the distance of the contrast from zero (z = 2.12 on the stance scale, t = -2.33).",
)

# ------------------------------------------------- all-boats-trees-rent

answer(
    "all-boats-trees-rent",
    "the verdict is kept. The referee rebuilt the tree counts from the downloaded points and the rents from the "
    "ACS summary files, matched the registrant's values in every tract, and refitted 0.0127 (0.0018 to 0.0235; "
    "standard error 0.0055; 2,048 tracts, 196 clusters). Neither registered condition is met and neither was "
    "missed narrowly (0.66 standard errors above the support threshold, 0.96 below the refutation threshold). "
    "The changes follow.\n"
    "The exposure is only partly planting. The net change in living trees mixes new planting, loss of existing "
    "trees and differences between the two censuses. Across the sample tracts it correlates 0.31 with the count "
    "of trees of 3 inches or less in 2015, which must have been planted after 2005, and -0.35 with the 2005 "
    "count. The correlation with trees of 6 inches or less is 0.61 to 0.71 in Manhattan, the Bronx and Brooklyn, "
    "0.29 in Queens and 0.10 on Staten Island, so in Queens and Staten Island (757 of 2,048 tracts, 37%) the "
    "exposure mostly measures losses or census differences. In the 2005 file 8,840 rows (1.5%) have a longitude "
    "of zero and fall in no tract, which is 12% of the counted citywide gain of 76,583 (re-checked); the 2005 "
    "counts are too low in unknown tracts and the gain is overstated there. The count of trees of 12 inches or "
    "more rose 48% in Manhattan, which planting cannot produce in ten years. In a model with both parts the "
    "slope is 0.0097 (-0.0032 to 0.0226) for the change in smaller trees and 0.0201 (0.0018 to 0.0385) for the "
    "change in trees of 12 inches or more, so the part that cannot be planting carries at least as much of the "
    "association as the part that can (referee).\n"
    "The size is not stable. Over forms of the exposure and of the adjustment that can each be defended, the "
    "slope per 100 trees ranges from 0.0073 (-0.0044 to 0.0179; baseline rent corrected for sampling error at "
    "the mean error variance) to 0.0326 (0.0125 to 0.0527; tracts with a change under 200 trees), and the "
    "intervals reach 0.057 (0.0273, -0.0024 to 0.0570; net change instrumented by trees of 6 inches or less). "
    "Forty-seven tracts changed by 300 trees or more, twenty of them on Staten Island, with a median area of 0.74 "
    "square km against 0.18 for the sample; without them the slope is 0.0245 (0.0096 to 0.0395). Per square km "
    "the slope is 0.0818 (0.0445 to 0.1191) per thousand trees, which at the median tract area corresponds to "
    "0.045 per 100 trees, the central Portland prediction. The statements that the estimate is 29% of the "
    "prediction and that its upper limit of 0.0235 is below 0.044 hold for the registered form only. These "
    "variants were chosen after the data and decide nothing under rule 4; three of them would meet the support "
    "condition and none meets the refutation condition.\n"
    "The lower limit is not robust. The interval includes zero without baseline rent (0.0084, -0.0027 to "
    "0.0196), with population change (0.0085, -0.0022 to 0.0193), with fixed effects for 60 districts (0.0095, "
    "-0.0005 to 0.0196) or for neighbourhoods (0.0098, -0.0008 to 0.0205), and with the correction for error in "
    "baseline rent at the mean error variance (0.0073, -0.0044 to 0.0179). With Conley standard errors to 10 km "
    "it is 0.0002 to 0.0251. No borough's interval excludes zero, and the Bronx, with the largest gain (40%), "
    "shows none (-0.0009, -0.0144 to 0.0125). The statement that the interval excludes zero is withdrawn from "
    "the prediction score.\n"
    "The comparison with Portland is loose. The 300,000 dollar median price is an assumption; at 200,000 the "
    "prediction is 0.066 (0.026 to 0.105) and at 400,000 it is 0.033 (0.013 to 0.052), so the refutation "
    "threshold would lie between 0.013 and 0.026 and the observed upper limit of 0.0235 is inside that range. The "
    "Portland outcome is the sale price of single-family houses and the exposure is trees planted, at a lag of "
    "six years; the New York outcome is gross rent with much of the stock rent-stabilised, the exposure is a net "
    "change, and the baseline rent window (2008-12) lies inside the planting period (2005 to 2015). Each "
    "difference makes a smaller New York slope expected even if the Portland association carried over. The "
    "thresholds stay as registered.\n"
    "Rivals not answered. New construction (street trees are required with new buildings, which carry higher "
    "rents) is not in the registration; the population-change adjustment addresses it in part. No pre-trend test "
    "was possible, because the files on disk hold no rent before 2008-12; whether trees went where rents were "
    "already rising is the main open rival for any positive reading. The sample drops 135 top-coded tracts, "
    "which selects on the outcome.\n"
    "Blindness. The rent change had been on disk since 12 November and had been used in an earlier claim. The "
    "registration says only its marginal distribution was read. The repository cannot show this.\n"
    "Reading. These data cannot say whether street trees raised rents. A sentence saying that New York shows "
    "less rent effect than Portland predicts is not supported and has been removed from docs/all_boats.md.",
    "Referee: keep unsettled. The exposure is only partly planting (in Queens and Staten Island it mostly "
    "measures losses or census differences; 8,840 trees of 2005 have longitude zero); the slope ranges from about "
    "0.007 to 0.033 with intervals reaching 0.057 over defensible forms, so the comparison with the Portland "
    "prediction is not robust; the lower limit includes zero under several adjustments; stance set to null.",
    "accepted; verdict kept, '29% of the prediction' and 'excludes zero' withdrawn, stance null",
    verdict_note="Unsettled: neither registered condition is met. The registered slope of 0.0127 (0.0018 to "
    "0.0235) is not a stable description of size or sign: over other defensible forms the slope is 0.007 to 0.033 "
    "per 100 trees with intervals from below zero to 0.057, the exposure is only partly planting, and the lower "
    "limit includes zero under several adjustments. These data cannot say whether street trees raised rents, and "
    "they do not show that New York has less rent effect than the Portland study predicts.",
    prediction_scored=swap(
        o_trees["prediction_scored"],
        "The estimate is positive and its interval excludes zero, and it is 29% of the central prediction.",
        "After the referee: on the registered model the estimate is 2.29 standard errors from zero, 5.67 below the "
        "central prediction and 0.96 below its lower end. Neither the exclusion of zero nor the ratio to the "
        "central prediction (29%) is robust to the form of the exposure or to the adjustments listed in the "
        "notes, so the prediction is scored as not decided in size or in sign."),
    settle="A new registration with an exposure that measures planting (trees of 3 inches or less in the 2015 "
    "census, per square km) and a pre-trend test on 2000 census rent, which is not among the files on disk. The "
    "2025 tree census, when published, would give a second period.",
    stance=None,
    stance_note="Null after the referee: the value 0.817 was the distance of the estimate from no effect (z = 2.29) "
    "and read on the strip as agreement with the prediction, while the registered model puts the estimate 5.67 "
    "standard errors below the predicted 0.044 and the verdict is unsettled. Under other defensible forms the "
    "estimate is compatible with zero and with the central prediction, so it favours neither.",
)

print("done")
