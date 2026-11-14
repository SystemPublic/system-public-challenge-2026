"""Registration of moon-full-emergencies. Run before analyses/moon/test.py is first run.

Usage: python -m analyses.moon.register
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims

REC = {
    "id": "moon-full-emergencies",
    "kind": "confirmation",
    "statement": "On the day of a full moon and the days either side of it, New York City has no more and no fewer "
                 "shootings, ambulance incidents or injury crashes than on other days, within stated equivalence bounds.",
    "graph_evidence": [
        {"association_id": "variable search 'full moon', 'lunar cycle', 'moon phase', 'lunar phase' (14 November 2026)",
         "concepts": ["full moon", "road traffic crash emergency transport"], "n_findings": 1, "n_studies": 1, "direction": "+",
         "summary": "Relative risk 1.042 (1.021 to 1.063) of emergency transport for road traffic crashes on full-moon nights.",
         "pubmed_ids": [29990928]},
        {"association_id": "same search", "concepts": ["full moon", "motorcycle deaths"], "n_findings": 2, "n_studies": 1,
         "direction": "+", "summary": "Relative risk 1.05 (1.02 to 1.09) of motorcycle deaths on full-moon nights; a second record gives an odds ratio 1.26.",
         "pubmed_ids": [29229755]},
        {"association_id": "same search", "concepts": ["moon phase", "homicide"], "n_findings": 2, "n_studies": 1, "direction": "-",
         "summary": "Homicides in Finland: relative risk 0.85 (0.77 to 0.94) at full moon.", "pubmed_ids": [30647032]},
        {"association_id": "same search", "concepts": ["full moon", "out-of-hospital cardiac arrest"], "n_findings": 3, "n_studies": 1,
         "direction": "0", "summary": "Relative risk 1.007 (0.993 to 1.021).", "pubmed_ids": [33693140]},
    ],
    "graph_evidence_note": "The variable search returned 60 findings from 36 studies on lunar variables. The values above are the "
                           "graph's records as returned by the API; the abstracts were not read before registration.",
    "literature": [{"citation": "Rotton J, Kelly IW. Much ado about the full moon: a meta-analysis of lunar-lunacy research. "
                                "Psychol Bull 1985;97(2):286-306.", "doi": "10.1037/0033-2909.97.2.286",
                    "finding": "Phases of the moon accounted for no more than about 1% of the variance in the behaviours studied (cited from memory; to be verified)."}],
    "prediction": {
        "direction": "0",
        "magnitude": "Rate ratio for the 3-day full-moon window: shootings 0.96 to 1.04, ambulance incidents 0.995 to 1.005, "
                     "injury crashes 0.98 to 1.02. Best guess 1.00 for each.",
        "support_if": "All three 95% intervals lie inside their equivalence bounds: shootings 0.93 to 1.07, ambulance incidents "
                      "0.98 to 1.02, injury crashes 0.97 to 1.03.",
        "refute_if": "For at least one outcome the 98.3% interval excludes 1.00 while the 95% interval of the 23-day placebo "
                     "for that outcome includes 1.00.",
    },
    "plan": "analyses/moon/test.py, committed with this registration and not yet run. Poisson regression of daily counts on a "
            "3-day full-moon window (PyEphem instants, New York dates), with day of week, year-by-month fixed effects, holiday, "
            "daily maximum temperature and its square, and a wet-day indicator; Newey-West errors, 7 lags. Outcomes: shooting "
            "incidents 2006-2025 (data/derived/heat/shootings_daily.csv), all EMS incidents 2017-01-01 to 2026-08-31 "
            "(data/derived/health_gaps/ems_daily.csv), crashes with an injured person 2014-2025 (Motor Vehicle Collisions, "
            "h9gi-nx95, the copy fetched for the turn-restriction claims). Placebo (rule 12): the same model with a 3-day window "
            "that recurs every 23 days. Secondary, deciding nothing: the full-moon day alone.",
    "can_it_fail": "Yes. The graph's crash finding (1.042) lies outside the crash bound, so a New York effect of that size would "
                   "miss support_if, and its interval would probably exclude 1.00. Expected standard errors: about 0.025 for "
                   "shootings, 0.004 for ambulance incidents and 0.008 for injury crashes.",
    "already_seen": "The three daily series were built for earlier claims. None has been tabulated or plotted against lunar "
                    "phase by this registrant. The equivalence bounds were set from expected standard errors, not from results.",
    "alternatives": ["Moonlight changes visibility and night-time activity (a real but non-lunacy path)",
                     "Cloud cover hides the moon and dilutes any effect",
                     "Chance among many lunar studies (publication of positive results)"],
    "prior": 0.6,
    "prior_note": "The ambulance bound is narrow; a small real difference or residual seasonality could miss it.",
    "registrant": "Claude (coordinator), for Jeff Vernon",
}

if __name__ == "__main__":
    print(claims.register(REC))
