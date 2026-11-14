"""Write the outcome of stalled-421a-vesting-footings from data/derived/stalled/vesting_result.json (registered run)
and vesting_exploratory.json (exploratory, decides nothing)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims

D = ROOT / "data/derived/stalled"
r = json.loads((D / "vesting_result.json").read_text())
x = json.loads((D / "vesting_exploratory.json").read_text())
d1, d2 = r["D1_rush_minus_2017_2019"], r["D2_rush_minus_2023"]
rt = r["rates"]
claims.outcome({
    "id": "stalled-421a-vesting-footings",
    "verdict": "contested",
    "city_effect": {"label": "D1: 36-month no-CO rate, foundation starts 15 Dec 2021-14 Jun 2022 minus same window 2017-2019 (registered BBL matching)",
                    "estimate": round(d1["est"], 3), "lo": round(d1["lo"], 3), "hi": round(d1["hi"], 3),
                    "scale": "difference in proportions", "null": 0, "n": rt["2022"]["n"] + rt["2017"]["n"] + rt["2018"]["n"] + rt["2019"]["n"]},
    "graph_effect": None,
    "sources": r["sources"],
    "prediction_scored": ("miss. refute_if was met: the upper 95%% bound of D1 is %.3f, below 0.03. D2 (rush minus 2023) was %.3f (%.3f to %.3f), "
                          "so its support condition was met, but support required both." % (d1["hi"], d2["est"], d2["lo"], d2["hi"])),
    "settle": ("A job-level link between permits and certificates that survives lot changes (DOB's own job-to-CO crosswalk), the HPD list of "
               "projects vested in 421-a with their commencement dates, and a completion horizon of six years for the 2022 cohort (2028) "
               "to see whether the 2031 extension lets vested projects wait."),
    "research_needed": [
        {"question": "Which of the 807 jobs that started foundations in the six months before 15 June 2022 were vested in 421-a, and which of those have no CO?",
         "data": "HPD 421-a(16) applications with commencement dates; DOB job numbers", "design": "match on BBL and job; compare vested and non-vested starts in the same window", "priority": "high"},
        {"question": "How often does the BBL on a permit differ from the BBL on the certificate of occupancy for the same job?",
         "data": "ipu4-2q9a, w9ak-ipjd, bs8b-p36w, pkdm-hqz6", "design": "job-number match, then compare BBLs by cohort year", "priority": "medium"}],
    "figures": ["figures/stalled/vesting_cohorts.png"],
    "notes": (
        "Registered run: rates of no CO within 1,096 days of the first initial foundation permit, BBL matching: "
        + ", ".join(f"{k} {v['rate']:.3f} (n {v['n']})" for k, v in rt.items())
        + ". The control windows 2017 and 2018 (0.68 and 0.63) were far above 2019 (0.45). A check after the result, by job number, "
        "showed that the registered BBL matching misses certificates for older jobs: for 2017 legacy jobs, 59% had a CO under the same job "
        "number within 36 months, against 32% found by BBL. The permit's lot and the certificate's lot differ for many older jobs, probably "
        "because lots were merged, split or converted to condominium billing lots after the permit. "
        "EXPLORATORY (analyses/stalled/vesting_exploratory.py, decides nothing): matching by job number or BBL, the 36-month no-CO rates are "
        + ", ".join(f"{k} {v['rate']:.3f}" for k, v in x["horizon_1096"].items())
        + f". D1 under this matching is {x['D1_union_36m'][0]} ({x['D1_union_36m'][1]} to {x['D1_union_36m'][2]}), so the refutation does not depend on "
        f"the matching defect; legacy jobs only, D1 is {x['D1_union_36m_legacy_only'][0]} ({x['D1_union_36m_legacy_only'][1]} to {x['D1_union_36m_legacy_only'][2]}). "
        f"Against the 2021 window D1 is {x['D1_union_36m_vs_2021'][0]} ({x['D1_union_36m_vs_2021'][1]} to {x['D1_union_36m_vs_2021'][2]}). "
        f"The rush window had 807 foundation starts against about 520 a year in 2017-2019. At 48 months its no-CO rate ({x['horizon_1461']['2022']['rate']}) "
        "is within the range of 2017-2019 (0.25 to 0.30). By November 2026, "
        f"{x['rush_no_co_by_nov2026']['n']} of the {x['rush_no_co_by_nov2026']['of']} rush-window jobs have no CO. "
        "The rush to pour footings before the deadline therefore added about 300 starts, most of which were completed at the usual rate; it did "
        "not produce a measurable excess of stalled foundations citywide. The 2023 window stalls less than 2022, which fits a composition "
        "change (jobs that could not vest are smaller or condominium projects) as well as the vesting account."),
})
print("outcome written")
