"""Write the outcomes of the two registered tests from the result files."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims
OUT = ROOT / "data/derived/graph/splits"
GRAPH_SRC = {"kind": "system-public-graph", "api": "v1.0", "fetched": "2026-11-12",
             "note": "API associations by relationship id; cached in data/cache/sysgraph; the API carries no version id"}

def ev(rid):
    c = json.loads((OUT / "coded_findings.json").read_text())[rid]
    return [{"association_id": f["id"], "relationship_id": rid, "variables": [f["v1"], f["v2"]], "statistic": f["stat"],
             "value": f["value"], "ci": [f["lo"], f["hi"]], "stored_direction": f["direction"], "significant": f["significant"],
             "pubmed_id": f["pmid"], "code": f["code"]} for f in c["findings"]]

def asthma():
    r = json.loads((OUT / "city_asthma.json").read_text())
    p, w, d = r["primary_cool"]["x"], r["warm"]["x"], r["all_interaction"]["warm_minus_cool_log"]
    bm = r["by_month_exploratory"]
    claims.outcome({
     "id": "split-temp-asthma-ems", "verdict": "unsettled",
     "city_effect": {"label": "Asthma EMS dispatches, October to March, per 5 C higher mean temperature over lags 0-3 days",
                     "estimate": round(p["irr"], 4), "lo": round(p["lo"], 4), "hi": round(p["hi"], 4),
                     "scale": "incidence rate ratio per +5 C", "null": 1, "n": r["primary_cool"]["n_days"]},
     "graph_effect": {"label": "Recoded graph findings: 16 of 17 short-term level findings say colder days bring more asthma; relative risks at the 5th temperature percentile against the median run from 1.10 to 2.16 over lags of up to 21 days",
                      "estimate": None, "lo": None, "hi": None, "scale": "relative risk, cold against median", "null": 1},
     "graph_evidence": ev("4FaXcuNJRt|EAshH_Ko3h"),
     "sources": r["sources"] + [GRAPH_SRC],
     "prediction_scored": (f"miss. Registered: cool half-year rate ratio 0.95 to 0.99 per +5 C. Found {p['irr']:.3f} ({p['lo']:.3f} to {p['hi']:.3f}); "
                           "the interval includes 1 and lies above the whole registered range. Secondary (moderator) prediction: warm-minus-cool "
                           f"difference of log rate ratios positive; found {d['est']:.4f} ({d['lo']:.4f} to {d['hi']:.4f}), right sign, interval includes 0: not met."),
     "settle": ("Asthma emergency visits by day and age group from the Health Department's syndromic system, which is not on NYC Open Data, "
                "with a distributed-lag model to 21 days as in the Hong Kong and Hefei studies, and daily pollen and ozone. The EMS series "
                "bounds the effect of a cold day within four days at under 1% per 5 C in either direction; it cannot see a three-week lag "
                "through month fixed effects."),
     "research_needed": [
       {"question": "Does the cold-day asthma effect found in East Asian cities exist in a centrally heated city at lags beyond four days?",
        "data": "daily asthma ED visits by age, NYC syndromic surveillance; Central Park temperature", "design": "distributed-lag non-linear model, lags 0-21, by season", "priority": "medium"},
       {"question": "Is the summer rise of asthma dispatches with temperature (June to August, exploratory) a heat effect or an ozone effect?",
        "data": "daily ozone and PM2.5 (state monitors), EMS asthma dispatches", "design": "two-exposure daily model within June to August", "priority": "medium"},
       {"question": "How much of any within-September temperature slope is the return to school?",
        "data": "DOE school calendar, EMS asthma dispatches", "design": "event study around the first school day, by year", "priority": "low"}],
     "figures": ["figures/graph/split_literatures.png"],
     "notes": ("Deviation from the registration: the asthma call types first appear on 2006-09-28, so the series starts 2006-10-01, not 2006-01-01. "
               f"{r['totals']['dispatches_initial']:,} dispatches on {r['totals']['days']:,} days. Warm half-year rate ratio {w['irr']:.3f} ({w['lo']:.3f} to {w['hi']:.3f}). "
               "Sensitivity analyses (final call type, lag 0, lags 0-7, minimum temperature, excluding March 2020 to June 2021) all give cool-season rate ratios between 1.001 and 1.006 with intervals including 1. "
               "Exploratory, by calendar month: June " + f"{bm['6']['irr']:.3f}, July {bm['7']['irr']:.3f} ({bm['7']['lo']:.3f} to {bm['7']['hi']:.3f}), August {bm['8']['irr']:.3f}, "
               f"September {bm['9']['irr']:.3f} ({bm['9']['lo']:.3f} to {bm['9']['hi']:.3f}), February {bm['2']['irr']:.3f} ({bm['2']['lo']:.3f} to {bm['2']['hi']:.3f}). "
               "The September slope is confounded with the date: asthma rises after schools open while days cool, and month fixed effects do not remove a trend inside a month. "
               "The half-year split chosen at registration averages a positive summer slope with this negative September one."),
    })

def covid():
    r = json.loads((OUT / "city_covid.json").read_text())
    p, q = r["primary"], r["quarterly_summary"]
    claims.outcome({
     "id": "split-temp-covid-growth", "verdict": "unsettled",
     "city_effect": {"label": "Weekly log growth of COVID-19 hospital admissions per 1 C temperature anomaly, days 7-20 before",
                     "estimate": round(p["est"], 4), "lo": round(p["lo"], 4), "hi": round(p["hi"], 4),
                     "scale": "change in weekly log growth per +1 C", "null": 0, "n": p["n_weeks"]},
     "graph_effect": {"label": "Graph: 26 positive and 17 negative findings; after recoding 20 say higher temperature, less transmission and 22 the opposite, 13 of the 22 being unadjusted correlations with case counts",
                      "estimate": None, "lo": None, "hi": None, "scale": "mixed", "null": 0},
     "graph_evidence": ev("4FaXcuNJRt|DZBybMvxDI"),
     "sources": r["sources"] + [GRAPH_SRC],
     "prediction_scored": (f"miss. Registered: -0.030 to -0.003 per C. Found {p['est']:+.4f} ({p['lo']:+.4f} to {p['hi']:+.4f}) over {p['n_weeks']} weeks; the interval "
                           "includes 0 and excludes effects more negative than -0.004. Secondary (moderator) prediction: at least a quarter of calendar quarters "
                           f"significantly positive and a quarter significantly negative in the raw correlation. Found {q['sig_pos']} of {q['quarters']} positive (23%) and "
                           f"{q['sig_neg']} of {q['quarters']} negative (59%): both signs occur, the positive share is just under the registered 25%."),
     "settle": ("A multi-city panel of weekly admission growth with city and week fixed effects, so that the same variant wave is compared across "
                "cities with different weather in the same week. One city gives 291 weeks and a standard error of 0.005 per C, about the size of the effect the "
                "transmission models in the graph report."),
     "research_needed": [
       {"question": "Does a temperature anomaly change COVID-19 growth once the variant wave is held fixed?",
        "data": "weekly admissions for 20 or more US cities (HHS Protect, city portals), GHCN-Daily", "design": "panel with city and calendar-week fixed effects", "priority": "medium"},
       {"question": "Which published temperature and COVID-19 correlations would reverse if the study window moved by one quarter?",
        "data": "the 13 raw-correlation findings in the graph with their study windows; public case series for each place", "design": "re-run each correlation over rolling windows", "priority": "low"}],
     "figures": ["figures/graph/split_literatures.png"],
     "notes": ("Sensitivity: anomaly over days 0-13, " + f"{r['sensitivity']['window_0_13']['est']:+.4f} ({r['sensitivity']['window_0_13']['lo']:+.4f} to {r['sensitivity']['window_0_13']['hi']:+.4f}); "
               f"days 14-27, {r['sensitivity']['window_14_27']['est']:+.4f}; cases instead of admissions, {r['sensitivity']['cases']['est']:+.4f}; dropping 2020, {r['sensitivity']['drop_2020']['est']:+.4f}; "
               f"dropping the Omicron weeks, {r['sensitivity']['drop_omicron']['est']:+.4f}. All intervals include 0; the days 0-13 window is the only negative one and too short for an infection to reach hospital. "
               "The raw quarterly Spearman correlations of daily temperature with daily cases range from -0.79 (2020 Q2) to +0.77 (2024 Q2). "
               "Exploratory: over the first 30, 45, 60 and 90 days from 1 March 2020 the raw correlation is +0.03, +0.17, +0.14 and -0.22."),
    })

if __name__ == "__main__":
    asthma(); covid()
