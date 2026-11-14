"""Outcomes for further-subway-crime-per-ride-by-hour and further-subway-crime-per-million-repro."""
import json
from pathlib import Path
from concord import claims
R = Path(__file__).resolve().parents[2]
D = R / "data/derived/further_subway"
o = json.loads((D / "results.json").read_text())
seen = {}
for s in json.loads((D / "sources.json").read_text()):
    s = dict(s); s["data_access"] = "open"
    seen[(s["dataset"], json.dumps(s["query"], sort_keys=True))] = s
sources = list(seen.values())
P = o["primary"]; G = P["G"]; rep = o["repro"]
fig = ["figures/further/subway_crime_per_ride_by_hour.png"]

main = {
    "id": "further-subway-crime-per-ride-by-hour",
    "verdict": "unsettled",
    "city_effect": {"label": "late-night (0-5) subway felony rate per million entries, Oct 2025-Sep 2026 against 2019", "estimate": G["0-5"][0],
                    "lo": G["0-5"][1], "hi": G["0-5"][2], "scale": "rate ratio", "null": 1, "n": P["rates"]["L12|0-5"]["n"] + P["rates"]["2019|0-5"]["n"]},
    "secondary_effects": {
        "A_night_vs_day_L12": {"estimate": P["A"][0], "lo": P["A"][1], "hi": P["A"][2], "note": "rate 0-5 over rate 10-16, registered threshold 3.0 with lower bound 2.0: met"},
        "A_night_vs_day_2019": {"estimate": P["A_2019"][0], "lo": P["A_2019"][1], "hi": P["A_2019"][2]},
        "ratio_20_24_vs_10_16_L12": {"estimate": P["A_2024"][0], "lo": P["A_2024"][1], "hi": P["A_2024"][2]},
        "G_all_bands": {"estimate": G["all"][0], "lo": G["all"][1], "hi": G["all"][2]},
        "B_night_G_over_all_G": {"estimate": P["B"][0], "lo": P["B"][1], "hi": P["B"][2], "note": "registered threshold 1.10: not met"},
        "G_by_band": {b: {"estimate": v[0], "lo": v[1], "hi": v[2]} for b, v in G.items()},
        "placebo_D_nonsubway": {"estimate": o["placebo"]["D"][0], "lo": o["placebo"]["D"][1], "hi": o["placebo"]["D"][2]},
        "sensitivity": {k: {"A": o[k]["A"], "G_0_5": o[k]["G"]["0-5"], "B": o[k]["B"]} for k in ("S1", "S2", "S3", "S4", "S5")} | {"S6": {"A": o["S6"]["A"], "G_22_4": o["S6"]["G"]}},
    },
    "graph_effect": None,
    "sources": sources,
    "prediction_scored": (
        "partial. The late-night against daytime ratio was predicted at 3 to 8 and is 15.0 (13.3 to 17.0), so the first "
        "support condition is met with a larger value than expected. The 0-5 rate against its 2019 level was predicted "
        "at 1.2 to 2.2 and is 0.97 (0.86 to 1.08), so the condition that its lower bound exceeds 1 is not met, and the ratio B of the night change to the all-day change "
        "was predicted 1.0 to 1.5 and is 0.90 (0.79 to 1.02). The upper bound of G[0-5] exceeds 1, so the refutation "
        "condition is not met either. The all-day rate per entry is above its 2019 level (1.08, 1.02 to 1.14), as predicted."
    ),
    "settle": (
        "Late-night per-person risk needs exposure measured in person-hours on platforms and trains (train-hour occupancy from "
        "MTA counts or automatic passenger counters) in place of fare entries, and a check on how the NYPD codes premise and "
        "time for crimes found on a sleeping or absent victim; a longer series with monthly 0-5 counts would narrow the 0-5 "
        "interval, which at 551 and 681 complaints leaves a rate ratio from 0.86 to 1.08."
    ),
    "research_needed": [
        {"question": "Per person-hour risk by hour band in the subway", "data": "MTA train occupancy or automatic passenger counts by hour, NYPD complaints", "design": "Poisson model with person-hours as offset by station complex, hour and month", "priority": "high"},
        {"question": "Whether 5-10 and 10-16 felony rates per entry rose because entries fell (fixed incident counts) or because incident counts rose", "data": "NYPD complaints by hour 2019-2026, ridership by hour", "design": "Decompose count and exposure changes by band; compare with non-subway placebo counts", "priority": "medium"},
        {"question": "Reporting and coding changes for the subway premise after 2020", "data": "NYPD complaint data dictionary versions, premise coding guidance; transit district assignment", "design": "Compare S1 and S2 numerators over time and with MTA Major Felonies counts", "priority": "medium"},
    ],
    "figures": fig,
    "notes": (
        "Primary numerator: NYPD felony complaints of the seven MTA major types with premise 'TRANSIT - NYC SUBWAY'; counts 2,501 in 2019 and 2,103 in the 12 months to 30 September 2026. "
        "Denominator: MTA estimated subway entries, 1,695 million in 2019 and 1,323 million in the 12 months, so the all-day rate per million entries was 1.48 (1.42 to 1.53) in 2019 and 1.59 (1.52 to 1.66) in the latest 12 months. "
        "Rates per million entries in the latest 12 months were 17.7 (16.2 to 19.2) at 0-5, 1.04 (0.93 to 1.15) at 5-10, 1.18 (1.07 to 1.29) at 10-16, 1.02 (0.93 to 1.13) at 16-20 and 2.11 (1.88 to 2.35) at 20-24. "
        "The 2019 rates were 18.3, 0.83, 1.14, 0.98 and 2.01. The 0-5 band holds 2.4% of entries and 26% of complaints. "
        "The 5-10 band has the clearest rise, 1.26 (1.08 to 1.46) times its 2019 rate; the other bands are near 1.0. The result therefore agrees with the first half of the hypothesis (a late-night rate many times the daytime rate) and does not agree with the second half: the late-night rate per entry is at its 2019 level, not above it, and the all-day rate is also above its 2019 level, so the premise that the all-day rate had returned was false. "
        "The State's all-day fall is a fall in counts and in entries together; per entry, the rate in every band except 5-10 is within the intervals of its 2019 value. "
        "Calendar 2025 in place of the latest 12 months gives A 17.3, G[0-5] 1.06 (0.95 to 1.19) and B 0.96 (0.84 to 1.09), and the 20-24 band at 1.27 (1.10 to 1.48) times 2019. None of the six sensitivity checks changes the verdict. "
        "Placebo: non-subway felonies of the same types rose in the 0-5 band relative to all hours by D = 1.05 (1.02 to 1.07), which excludes 1 but is under the registered 1.10, so a citywide shift toward the night is small. "
        "Limits: the denominator is fare entries, which understate people present on trains and platforms at night, so the per-entry night rate overstates per-person-hour risk if night riders stay longer; ridership is a modelled estimate and its error is not in the intervals; "
        "the interval on a ratio treats the denominators as fixed; complaint times are reported times and 1.9% (2019) and 3.8% (latest 12 months) of 0-5 complaints sit at exactly 00:00; no complaint was missing a time. "
        "The CBC survey of perceived safety was not read at the source. Registration was pushed to prereg/further-subway-crime-per-ride-by-hour before any complaint or ridership count was queried."
    ),
}
rep_ = rep["R1_primary"]
import math
from scipy import stats
c = rep_["2025_counts"]; lo, hi = stats.chi2.ppf(.025, 2 * c) / 2 / c, stats.chi2.ppf(.975, 2 * c + 2) / 2 / c
repro = {
    "id": "further-subway-crime-per-million-repro",
    "verdict": "contested",
    "city_effect": {"label": "MTA Major Felonies (yeek-jhmu, NYCT, Jan-Nov 2025) rate per million riders divided by the State's 1.65", "estimate": rep_["2025"] / 1.65,
                    "lo": rep_["2025"] * lo / 1.65, "hi": rep_["2025"] * hi / 1.65, "scale": "ratio to the published number", "null": 1, "n": c},
    "graph_effect": None,
    "sources": sources,
    "prediction_scored": (
        "miss. Under the primary reading R1 the 2025 rate is 1.11 per million (1,755 felonies over 1,578 million riders) against 1.65, and the fall since 2021 is 27.0% (1.52 in 2021 to 1.11 in 2025), at the lower edge of the 27 to 33 percent band. "
        "R2 to R6 as registered give 1.14, 1.11, 1.11, 6.12 and 1.83 for 2025; none meets both conditions."
    ),
    "settle": "The State's source and rider count. The release names no source. The NYPD complaint count over MTA subway entries gives 1.64 for January to November 2025 and a fall of 29.9% from 2021, which matches both published numbers; if the State's figure is that ratio, it should be stated as such.",
    "research_needed": [{"question": "Which dataset and denominator the State's 1.65 per million uses", "data": "request to the Governor's office or MTA; MTA Major Felonies metadata", "design": "Register the complaint-over-entries reading as a new claim and test it on 2024 and the 2025 full year", "priority": "high"}],
    "figures": [],
    "readings": {k: v for k, v in rep.items() if k.startswith("R")},
    "secondary_complaints_over_entries": rep["complaints_jan_nov"],
    "notes": (
        "Verdict follows the registration, which listed R1 to R6 and called the complaint-based ratio secondary. It is contested because no registered reading reproduces both numbers. "
        "The yeek-jhmu NYCT rows for January to November 2025 hold 1,755 felonies, all from NYPD, compared with 1,940 NYPD felony complaints with the subway premise in the same months, and the table's implied rider count is 1,578 million against 1,186 million subway entries in the ridership table. The table's rates are therefore on a larger denominator and a smaller count than the State's number implies. "
        "The secondary check, computed after the registered readings, gives 1,940 complaints over 1,186.3 million entries, 1.64 per million for January to November 2025 and 2.33 for the same months of 2021, a fall of 29.9%. That matches the published 1.65 and 30% within the registered tolerance, but it is a reading that the registration did not include among R1 to R6, so by the register's rules (PRECEDENCE 4) it decides nothing; it is a candidate for a new registration. "
        "R5 and R6 were registered with a riders formula that adds rates across agencies, which is not valid for more than one agency; a per-agency version gives 1.17 for all four agencies and 1.12 for NYCT and SIR, still far from 1.65. "
        "The table description says it counts arrests; the felony counts are below the complaint counts, which is consistent with that."
    ),
}
print(claims.outcome(main)); print(claims.outcome(repro))
