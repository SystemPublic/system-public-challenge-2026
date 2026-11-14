"""Outcomes for mob-crz-air (AQS, as registered) and mob-crz-air-nyccas (its NO2 successor)."""
import json
import math

from concord import claims
from analyses.mobility.common import DER

A = json.loads((DER / "crz_air_results.json").read_text())
N = json.loads((DER / "crz_air_nyccas_results.json").read_text())
pm, bal, pl, nth = A["PM25"], A["PM25_balanced_sites"], A["PM25_placebo2024"], A["PM25_vs_manhattan_north"]
ex = A["ps19_annual_log_excess"]
same_day = 100 * (math.exp(ex["2025"] - (ex["2023"] + ex["2024"]) / 2) - 1)
f = lambda r: f"{r['pct']:+.1f}% ({r['lo_pct']:+.1f} to {r['hi_pct']:+.1f})"

LIT_CONFLICT = ("The research on this exact question disagrees. Fraser et al. (2025, npj Clean Air) report daily maximum "
                "PM2.5 in the zone 22% below a counterfactual in January-June 2025; the NYC Health Department (August "
                "2026) reports no significant difference for PM2.5, NO2, NO or black carbon in 2025.")

air = {
    "id": "mob-crz-air",
    "verdict": "unsettled",
    "city_effect": {"label": "PM2.5 at PS 19 (only in-zone AQS monitor with a pre-period) vs other-borough monitors, 2025 vs 2023-24, TWFE DiD",
                    "estimate": round(pm["pct"], 2), "lo": round(pm["lo_pct"], 2), "hi": round(pm["hi_pct"], 2),
                    "scale": "percent change in daily PM2.5", "null": 0, "n": pm["n_site_days"]},
    "graph_effect": {"label": "No road-pricing findings in the graph. Literature range for NO2: Stockholm -5% to -15% ambient (Simeonova et al. 2021)",
                     "estimate": None, "lo": None, "hi": None, "scale": "percent", "null": 0},
    "sources": A["sources"],
    "prediction_scored": ("partial. The primary NO2 test could not be run: the EPA AQS daily NO2 files for 2022-2025 contain "
                          "no monitor in Manhattan (sites: IS 52 and Pfizer Lab in the Bronx, Queens College 2 and Queens "
                          f"College Near Road). The secondary PM2.5 estimate, {f(pm)}, falls in the registered range "
                          "(0% to -8%), but it rests on one monitor that samples one day in three and is not robust: on the "
                          "same days, against the two comparison monitors that ran in every year (IS 52, Queens College 2), "
                          f"PS 19's excess changed by {same_day:+.1f}%. The 2024 placebo is {f(pl)}."),
    "settle": ("An in-zone NO2 record with a pre-period. Candidates: the NYCCAS street-level two-week samples at in-zone sites "
               "(not published as a time series), the DEC Division Street site (PM2.5 began 2025; no pre-period), "
               "satellite NO2 (TROPOMI, about 5 km pixels, too coarse for a 23 km2 zone but usable for a Manhattan vs "
               "outer-borough contrast) and the low-cost sensor networks used by Fraser et al."),
    "research_needed": [
        {"question": "Publish the NYCCAS biweekly site-level measurements inside the CRZ for 2022-2025.",
         "data": "NYCCAS raw monitoring data", "design": "site-level DiD with reference-site adjustment", "priority": "high"},
        {"question": "Reconcile Fraser et al. (2025) with the DOHMH 2026 report: daily maximum vs daily mean, monitor sets, counterfactual model.",
         "data": "both studies' monitor lists and code", "design": "re-analysis on common data", "priority": "high"},
    ],
    "figures": ["figures/mobility/crz_air_pm25_before_after.png"],
    "notes": (f"Against Manhattan monitors north of 60th Street the PM2.5 estimate is {f(nth)}. Restricting to sites observed "
              f"before and after gives {f(bal)}. The two-way fixed-effects estimate depends on which comparison monitors "
              "enter, because three Brooklyn and Bronx monitors started in mid-2023 and two more in 2025. " + LIT_CONFLICT +
              " The NO2 test was re-registered as mob-crz-air-nyccas."),
}

no2, pmn = N["NO2"], N["PM25"]
import pandas as pd
_w = pd.read_csv(DER / "nyccas_NO2_uhf42_annual.csv", index_col="uhf42").loc[[306, 307, 308, 309, 310]].mean()
LONG_RUN = f"{_w['2014'] - _w['2020']:.1f} ppb ({_w['2014']:.1f} to {_w['2020']:.1f})"
nyccas = {
    "id": "mob-crz-air-nyccas",
    "verdict": "unsettled",
    "city_effect": {"label": "NYCCAS annual NO2, UHF 306-310 vs 32 UHFs outside Manhattan, 2025 vs 2021-24 (DiD); interval from placebo-in-space",
                    "estimate": round(no2["pct"], 2), "lo": round(no2["lo_pct"], 2), "hi": round(no2["hi_pct"], 2),
                    "scale": "percent change in annual NO2", "null": 0, "n": no2["n_uhf"]},
    "graph_effect": {"label": "Registered expectation from Stockholm and London: NO2 -3% to -10%",
                     "estimate": -6.5, "lo": -10, "hi": -3, "scale": "percent change in annual NO2", "null": 0},
    "sources": N["sources"],
    "prediction_scored": (f"miss. The NO2 DiD is {f(no2)}, in the wrong direction and well inside the placebo distribution "
                          f"(one-sided p = {no2['p_one_sided_placebo_space']:.2f}); the refutation condition registered "
                          "(estimate at or above 0) is met. The interval excludes the registered range below -2.2%, so the "
                          "city data rule out an NO2 decline of the size seen in Stockholm, while allowing a small one. "
                          f"PM2.5: {f(pmn)}, also not a decline."),
    "settle": ("The design compares model-based annual surfaces. NYCCAS is a land-use regression whose spatial covariates "
               "include traffic indicators held fixed across years and whose year-to-year change comes from street-level "
               "monitors adjusted to reference sites, so it may smooth a local change toward zero. Raw in-zone NYCCAS "
               "monitor values, a second post-year (2026), and hourly NO2 near the zone's main entry points would settle it."),
    "research_needed": [
        {"question": "Did NO2 at street level inside the CRZ change in 2025-26, measured at fixed monitors rather than modelled?",
         "data": "NYCCAS site data, new DEC Division Street NO2 if added, sensor networks", "design": "site-level DiD with a second post-year", "priority": "high"},
        {"question": "Did pollution rise near the diversion routes (Bronx expressways, FDR) as the Columbia sensor study reported?",
         "data": "NYCCAS UHF 105-107 and site data; MTA excluded-roadway entries (t6yz-b64h)", "design": "corridor DiD", "priority": "medium"},
        {"question": "What share of NO2 in the CBD comes from vehicles entering the zone vs buildings and through-traffic on excluded roads?",
         "data": "NYC emissions inventory, MTA entries by vehicle class", "design": "source apportionment", "priority": "medium"},
    ],
    "figures": ["figures/mobility/crz_air_nyccas_uhf42.png"],
    "notes": (f"Group means, NO2 ppb: in zone {no2['group_means']['in-zone']}; outside Manhattan "
              f"{no2['group_means']['outside Manhattan']}. In-zone NO2 fell by " + LONG_RUN + " between 2014 and 2020, so the "
              "long-run decline is much larger than any 2025 change. The placebo-in-time (post = 2024) is "
              f"{no2['placebo_time_2024_pct']:+.1f}% for NO2 and {pmn['placebo_time_2024_pct']:+.1f}% for PM2.5; the PM2.5 "
              "series has a 2024 rise in the zone that the design cannot explain. Manhattan north of 60th St moved "
              f"{no2['adjacent_301_305_pct']:+.1f}% in NO2 relative to outside Manhattan. This agrees with the DOHMH 2026 "
              "report, which used the same survey, and disagrees with Fraser et al. (2025) on PM2.5. Traffic speeds rose "
              "(mob-crz-traffic), so the policy changed traffic; the air-quality step of the chain is not visible in annual "
              "neighbourhood averages."),
}

if __name__ == "__main__":
    print(claims.outcome(air))
    print(claims.outcome(nyccas))
