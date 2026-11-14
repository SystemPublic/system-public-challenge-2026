"""Register heat-night-minimum. Run once, after design.py and before run.py.
Usage: python -m analyses.round5.heat_night.register <commit of run.py>"""
import json
import sys
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[3]
D = json.loads((ROOT / "data/derived/round5/heat_night/prereg_design.json").read_text())
G = json.loads((ROOT / "data/derived/round5/heat_night/graph.json").read_text())
SCRIPT_COMMIT = sys.argv[1]
ny, ch, comp = D["new_york"], D["chicago"], D["composition"]["composed"]
r3 = lambda x: round(x, 3)


def rel(section, key):
    return [{"relationship_id": r["relationship_id"], "num_findings": r["num_findings"], "num_studies": r["num_studies"],
             "n_returned": r["n_returned"]} for r in G[section].get(key, [])]


graph_evidence = [
    {"relationship_id": "4FaXcuNJRt|nDIFXeS4Xr", "concepts": ["temperature", "sleep"], "n_findings": 2, "n_studies": 2, "direction": "-",
     "summary": ("Two findings, both on indoor temperature. Valham 2012 (randomised crossover, 40 untreated sleep apnoea patients, Sweden): sleep efficiency "
                 "6 points lower at 24 C room temperature than at 16 C (71 against 77%, P = 0.012); the abstract adds 30 minutes less total sleep, which the graph does not hold. "
                 "The other finding is on cold rooms (17 C or less, difficulty initiating sleep, OR 1.79). Neither uses outdoor night temperature."),
     "pubmed_ids": [22467989, 38821464]},
    {"association_id": "variable 0SZFkEwEQv", "concepts": ["bedroom temperature during sleep (variable, grounded to sleep quality)", "poorer sleep quality"],
     "n_findings": 1, "n_studies": 1, "direction": "-",
     "summary": "Lappharat 2018 (63 sleep apnoea patients, Bangkok): adjusted odds of poor sleep quality 1.46 (1.01 to 2.10) with higher measured bedroom temperature.",
     "pubmed_ids": [29609708]},
    {"relationship_id": ["4FaXcuNJRt|aeY3nW1sT_", "aeY3nW1sT_|4FaXcuNJRt", "aeY3nW1sT_|dINFs04idR"], "concepts": ["temperature, hot", "sleep quality"],
     "n_findings": 8, "n_associations_returned": 0, "n_studies": 5, "direction": "0",
     "summary": "The relationship records report 8 findings in 5 studies; the association endpoint returns none of them, as found on 12 November.", "pubmed_ids": []},
    {"association_id": "variable ygo-nXuMA0", "concepts": ["outdoor temperature", "indoor bedroom temperature"], "n_findings": 1, "n_studies": 1, "direction": "+",
     "summary": ("Zuurbier 2021 (113 homes of elderly people, two Dutch cities, warm episode): the graph stores r = 0.34; the abstract gives R2 = 0.34 for bedrooms, "
                 "so the correlation is about 0.58. No slope in degrees per degree is given."), "pubmed_ids": [33421789]},
    {"association_id": "variables searched by name", "concepts": ["night or minimum outdoor temperature (variable names)", "sleep, aggression, violence, crime"],
     "n_findings": 0, "n_studies": 0, "direction": "0",
     "summary": ("Variable-name searches for night temperature, nighttime temperature, nocturnal temperature, minimum temperature, hot nights, tropical night and bedroom temperature "
                 "and sleep temperature returned about 200 variables (the minimum temperature search is capped at 100). The 23 that name outdoor night heat or bedroom temperature link to preterm birth, mortality, heat hospitalisation, anthrax, eczema, "
                 "cholesterol, body mass and crop yield. None links to sleep duration, aggression, violence or injury. None of the first 100 sleep duration variables names temperature."),
     "pubmed_ids": [36623379, 36274245, 33195962, 37172196, 28074921]},
    {"relationship_id": "k4RCuWBkJ3|y83mBL5cYb", "concepts": ["sleep duration", "aggression"], "n_findings": 4, "n_studies": 3, "direction": "-",
     "summary": ("Street 2016 (1,878 Boston high school students): adjusted odds of moderate physical aggression against peers 0.90 (0.81 to 1.00) per hour of sleep. "
                 "Van Veen 2022 (meta-analysis, 76,761 participants): correlation -0.16 (-0.19 to -0.12) in observational studies; standardised difference after "
                 "experimental sleep restriction -0.37 (-0.80 to 0.05). One further finding (reactive aggression, aOR 3.13) is on short against adequate sleep."),
     "pubmed_ids": [28923255, 36064210, 25940021]},
    {"relationship_id": ["nDIFXeS4Xr|y83mBL5cYb", "y83mBL5cYb|nDIFXeS4Xr", "aeY3nW1sT_|y83mBL5cYb", "y83mBL5cYb|1f0aF1BXj-", "1f0aF1BXj-|2qLKgaxkm_", "2qLKgaxkm_|1f0aF1BXj-",
                         "2qLKgaxkm_|aeY3nW1sT_"], "concepts": ["sleep, sleep quality, insomnia", "aggression, violence"],
     "n_findings": 18, "n_studies": 13, "direction": "-",
     "summary": ("Every signed finding says worse sleep goes with more aggression (for example preschool children sleeping under 9.44 hours, aggression OR 1.81, 1.36 to 2.41, "
                 "Scharf 2013). Eight of the 18 run the other way in time: violence exposure as a cause of poor sleep."), "pubmed_ids": [23838583, 40817272, 34058519, 31883497]},
]

rec = {
    "id": "heat-night-minimum",
    "kind": "confirmation",
    "statement": ("On days with a maximum of 27 C or more, shootings in New York rise with the preceding night's minimum temperature at a fixed daily maximum, "
                  "and the rise in shootings from 27 to 33 C falls in the hours from 18:00 to 05:59 more than in the hours from 06:00 to 17:59; the same holds in Chicago."),
    "graph_evidence": graph_evidence,
    "graph_evidence_note": ("Collected on 13 November 2026 by analyses/round5/heat_night/graph.py and variable-name searches, API only (the Dataverse copy is not on this machine), "
                            "124 uncached requests; data/derived/round5/heat_night/graph.json. Valham 2012, Lappharat 2018, Street 2016, Van Veen 2022, Zuurbier 2021 and Scharf 2013 "
                            "were read in PubMed on 13 November 2026. The graph's values match the abstracts except Zuurbier's, where an R2 is stored as r."),
    "literature": [
        {"citation": "Reeping PM, Hemenway D. The association between weather and the number of daily shootings in Chicago (2012-2016). Inj Epidemiol 2020;7:31.",
         "doi": "10.1186/s40621-020-00260-3", "finding": "+34.0% shootings per 10 C of daily high on weekdays; no separate estimate for the daily low."}],
    "composed_prediction": {
        "chain": ("outdoor night minimum -> bedroom temperature (slope assumed uniform 0.2 to 0.6 C per C; the graph gives only Zuurbier's correlation) -> sleep "
                  "(Valham 2012: 30 minutes per 8 C of room temperature, 3.75 minutes per C; the 30 minutes is from the abstract, the graph holds the sleep-efficiency contrast) "
                  "-> aggression (Street 2016: odds 0.90, 0.81 to 1.00, per hour of sleep; taken as a rate ratio 1.111 per hour lost)."),
        "rate_ratio_per_5c_night_minimum": [r3(x) for x in comp["ratio_lo_median_hi"]],
        "tool": "concordance-kit/kit/bridge.py compose, 20,000 draws, seed 1 (data/derived/round5/heat_night/prereg_design.json)",
        "discrimination": {"new_york": ny["discrimination_of_composed"], "chicago": ch["discrimination_of_composed"]},
        "reading": ("The graph-sized sleep path predicts a rate ratio of about 1.012 (1.000 to 1.031) per 5 C of night minimum. The expected standard error of the endpoint is "
                    f"{r3(ny['se_log_rr_per_5c_tmin'])} in New York and {r3(ch['se_log_rr_per_5c_tmin'])} in Chicago, so D is {r3(ny['discrimination_of_composed']['D_expected'])} and "
                    f"{r3(ch['discrimination_of_composed']['D_expected'])}, far below 4. The test cannot detect an effect of the composed size and is not registered as an endpoint test of "
                    "the chain (rule 8). It is registered as a test of whether the night minimum carries a large part of the hot-day excess."),
    },
    "prediction": {
        "direction": "+",
        "magnitude": ("(a) New York: rate ratio between 0.98 and 1.08 per 5 C of the preceding night's minimum at fixed maximum, on days with TMAX of 27 C or more; best guess 1.03. "
                      "Chicago: 0.98 to 1.06. (b) The ratio 33 against 27 C is 1.08 to 1.20 for night shootings and 0.98 to 1.12 for day shootings in New York, "
                      "and 1.03 to 1.12 and 0.97 to 1.08 in Chicago; the ratio of the night ratio to the day ratio is above 1 in both cities, with an interval that probably includes 1."),
        "support_if": ("(a) in New York: the 95% lower limit of the rate ratio per 5 C of the preceding night's minimum is above 1.00. This alone decides 'confirmed'."),
        "refute_if": (f"(a) in New York: the 95% upper limit is below {r3(ny['rr_carrying_half_the_excess'])} and the lower limit is at or below 1.00. "
                      f"{r3(ny['rr_carrying_half_the_excess'])} is the rate ratio per 5 C of minimum that would carry half of the New York hot-day excess (1.122 from 27 to 33 C), "
                      f"given that TMIN rises {r3(ny['tmin_per_c_tmax_hot_days'])} C per C of TMAX on hot days: exp(0.5 x ln 1.122 x 5 / (6 x {r3(ny['tmin_per_c_tmax_hot_days'])}))."),
        "otherwise": "Unsettled.",
        "secondary_registered": (
            "(b) For each city, the ratio 33 against 27 C for day shootings and for night shootings, and the ratio of the two from the binomial model. "
            "Part (b) is 'met' when the 95% lower limit of the night-over-day ratio of ratios is above 1.00, 'reversed' when its upper limit is below 1.00, otherwise 'not separated'. "
            f"(c) Chicago is scored on (a) by the same rule with its own threshold {r3(ch['rr_carrying_half_the_excess'])} (half of its excess of 1.058; TMIN rises "
            f"{r3(ch['tmin_per_c_tmax_hot_days'])} C per C of TMAX). The replication is 'replicated' when Chicago's (a) falls on the same side as New York's "
            "(both support, or both refute), 'not replicated' when they fall on opposite sides, otherwise 'inconclusive'. Parts (b) and (c) are reported and do not decide the verdict. "
            "The inverse-variance mean of the two cities' log rate ratios is reported."),
    },
    "plan": (
        f"Script: analyses/round5/heat_night/run.py at commit {SCRIPT_COMMIT}, run unchanged; model code analyses/round2/hot_end/model.py (SPLINE = 'lin', knots 15, 21, 27 C). "
        "No resampling and no random numbers: all intervals are Wald intervals from HC0 standard errors (PRECEDENCE rule 9).\n"
        "Data. New York: NYPD shooting incidents 5ucz-vwe8, one row per incident_key with occur_date and occur_time, 2006-01-01 to 2026-08-31; Central Park GHCN-Daily "
        "(USW00094728) TMAX, TMIN, PRCP through concord/noaa.py. Chicago: Violence Reduction victims gumc-mgzr, distinct case_number with gunshot injury, time from the date field, "
        "2010-01-01 to 2026-08-31, through concord/socrata.py with DOMAIN set to data.cityofchicago.org; Midway (USW00014819).\n"
        "Day. A shooting day d runs from 06:00 on date d to 05:59 on d+1 (last shooting day 2026-08-30). Day shootings fall from 06:00 to 17:59, night shootings from 18:00 to 05:59. "
        "TMAX is that of date d. The preceding night's minimum is TMIN of date d, which normally falls near dawn before the shooting day begins; the following night's minimum is "
        "TMIN of d+1. Calendar terms are those of date d: C(dow) + C(month) + C(year) + hol + wet, as in heat-shootings.\n"
        "(a) Shooting days with TMAX >= 27 C: negative binomial GLM, log link, of the count on TMAX/5 + TMIN/5 + calendar terms. On these days the registered piecewise-linear "
        "spline has a single free slope, so TMAX enters linearly. Dispersion by maximum likelihood from the model without TMIN.\n"
        "(b) All shooting days: the piecewise-linear TMAX spline and calendar terms, no TMIN, fitted to day and to night shootings; ratio 33 against 27 C for each; the ratio of the "
        "ratios from a binomial GLM of night shootings out of the shooting day's shootings on the same terms.\n"
        "Pre-specified secondary results, reported and not deciding: (a) for day and for night shootings; calendar-day counts; the following night's minimum alone and together "
        "with the preceding one (a sleep path predicts the preceding night, heat carried into the evening predicts the following night and night shootings); previous-day TMAX added; "
        "TMAX >= 30 C; June to August; the ratio 33 against 27 C by six-hour block; the all-day spline model with TMIN added, to show how much of the 33 against 27 C ratio remains; "
        "the hourly distribution of shootings by TMAX band (21-27, 27-30, 30 C and over) as a table.\n"
        "Figure: the night-minimum rate ratios and the day and night hot-day ratios for the two cities."),
    "can_it_fail": {
        "source": "data/derived/round5/heat_night/prereg_design.json (analyses/round5/heat_night/design.py; weather and calendar only, Fisher information at the published hot-day mean count)",
        "new_york": {k: ny[k] for k in ny if k != "discrimination_of_composed"},
        "chicago": {k: ch[k] for k in ch if k != "discrimination_of_composed"},
        "reading": (f"The smallest rate ratio per 5 C of minimum detectable with 80% power is {r3(ny['mde_rr_80pct'])} in New York and {r3(ch['mde_rr_80pct'])} in Chicago. "
                    f"If the night minimum has no effect, the refutation rule is met with probability {r3(ny['p_refute_if_no_effect'])} in New York and the support rule with 0.025. "
                    f"If the minimum carries half the excess, support is met with probability {r3(ny['p_support_if_half'])}. An unsettled verdict is therefore likely "
                    "(about one half) under either truth; the test can fail in both directions and cannot be passed by a null result."),
    },
    "already_seen": (
        "TMAX-only models of shootings are seen in both cities (linear, 4-df spline, piecewise-linear; New York 33 against 27 C 1.122, 1.048 to 1.202; Chicago 1.058, 1.014 to 1.105). "
        "Two earlier scripts fitted TMIN in place of TMAX, alone, on all days: heat-shootings (1.164 per 5 C of TMIN, 1.143 to 1.185) and transfer-chicago-heat-shootings "
        "(1.133, 1.119 to 1.147); I read both values. The referee of heat-mech-outdoors added TMIN, previous-day TMAX and rain amount together to an all-day linear model "
        "and reported only that the TMAX slope fell from 0.141 to 0.095 per 5 C (critique/heat-mech-outdoors.md); no TMIN coefficient was reported. That drop suggests TMIN or "
        "yesterday's TMAX carries about a third of the all-day linear slope, which is known before this test and is why the prediction is positive. No model with TMIN and TMAX "
        "together on hot days, and no model, table or query of shootings by hour of day, exists in the repository, the Socrata cache or the documents (searched for TMIN, occur_time, "
        "hour). I fitted none before registering. design.py read weather and calendar columns and the published tables of mean count by TMAX bin. run.py was tested before "
        "registration on simulated Poisson counts with the real Central Park weather; no shooting record was read."),
    "alternatives": [
        "TMIN at fixed TMAX measures humidity and cloud (humid days have warm nights), so a positive coefficient may be humid heat during the day and not the night.",
        "TMIN of date d correlates with TMAX of d-1; heat carried over from the previous day would appear as a night effect. The previous-day TMAX variant addresses it.",
        "The GHCN minimum is the minimum of the calendar day and sometimes falls late in the evening after a front, not at dawn; this adds error to the preceding-night measure.",
        "One station per city: Central Park is cooler at night than dense residential blocks, and Midway differs from the lakefront.",
        "A warmer night keeps people outdoors later, so a night effect on night shootings is also a routine-activity effect and does not by itself show a sleep path.",
        "Reported times of shootings are approximate, and the six-hour shift assigns early-morning shootings to the evening before, which is right for most and wrong for some."],
    "prior": 0.25,
    "prior_note": "Probability that New York's lower limit is above 1.00. About 0.25 for refuted and 0.5 for unsettled.",
    "registrant": "Claude (round 5 agent, night minimum)",
}
print(claims.register(rec))
