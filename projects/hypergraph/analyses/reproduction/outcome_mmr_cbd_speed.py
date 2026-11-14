"""Write the outcome of repro-mmr-cbd-speed from the derived files."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from concord import claims, socrata

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "reproduction"
STATED = {"FY24": 6.9, "FY25": 6.9, "FY26": 6.5}
TOL = 0.2


def main():
    fy = pd.read_csv(DER / "mmr_cbd_speed_fy.csv")
    tab = fy[fy.reading.str.match(r"R\d")].pivot(index="reading", columns="fy", values="mph")
    reproduces = {r: bool(abs(tab.loc[r, "FY25"] - 6.9) <= TOL and abs(tab.loc[r, "FY26"] - 6.5) <= TOL) for r in tab.index}
    r1 = tab.loc["R1"]
    assert reproduces["R1"]
    diffs26 = [tab.loc[r, "FY26"] - 6.5 for r in tab.index if reproduces[r]]
    per = pd.read_csv(DER / "mmr_cbd_speed_periods.csv").pivot(index="period", columns="area", values="mph")

    files = json.loads((DER / "mmr_cbd_speed_files.json").read_text())
    chk = json.loads((DER / "mmr_cbd_speed_check_sources.json").read_text())
    for s in chk["socrata"]:
        s["data_access"] = "open"
    chk["mta"]["data_access"] = "open"
    _, zsrc = socrata.query("8meu-9t5y", select="locationid,zone,borough", where="borough='Manhattan'", order="locationid")
    zsrc["data_access"] = "open"
    yrows_src = json.loads(next((ROOT / "data/cache/socrata").glob("yfdc-w5jh-*.json")).read_text())["source"]
    yrows_src.update({"url": "https://data.ny.gov/d/yfdc-w5jh", "data_access": "open"})
    sources = [
        {"kind": "tlc-trip-record-files", "name": "TLC Yellow Taxi Trip Records, monthly parquet, Jul 2023 - Jun 2026",
         "page": "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page", "data_access": "open", "files": files},
        *chk["socrata"], chk["mta"], zsrc, yrows_src,
        {"kind": "report", "name": "Mayor's Management Report Fiscal 2026, DOT chapter (p. 349) and indicator definitions (p. 256)",
         "url": "https://www.nyc.gov/assets/operations/downloads/pdf/mmr2026/dot.pdf", "data_access": "open"},
    ]

    rec = {
        "id": "repro-mmr-cbd-speed",
        "verdict": "confirmed",
        "city_effect": {
            "label": "R1 reproduced FY26 speed minus MMR stated FY26 speed (6.5 mph); lo and hi are the range of this difference over the readings that reproduce both years (R1, R3, R7, R8, R9)",
            "estimate": round(float(r1["FY26"] - 6.5), 3), "lo": round(min(diffs26), 3), "hi": round(max(diffs26), 3),
            "scale": "mph", "null": 0, "n": int(fy[(fy.reading == "R1") & (fy.fy.isin(["FY25", "FY26"]))].n_trips.sum()),
        },
        "reproduced": {
            "stated": STATED, "tolerance_mph": TOL,
            "by_reading": {r: {k: float(tab.loc[r, k]) for k in ("FY24", "FY25", "FY26")} | {"reproduces_FY25_and_FY26": reproduces[r]} for r in tab.index},
            "R1_change_FY25_FY26": round(float(r1["FY26"] - r1["FY25"]), 3),
            "stated_change_FY25_FY26": -0.4,
        },
        "periods_mph": {p: {a: float(per.loc[p, a]) for a in per.columns} for p in per.index},
        "sources": sources,
        "prediction_scored": ("hit: under the primary reading R1 the reproduced values are 6.95 mph for FY25 (stated 6.9) and 6.62 mph "
                              "for FY26 (stated 6.5), both within the registered 0.2 mph. Secondary checks also hit: FY24 6.94 "
                              "(stated 6.9) and an FY25-to-FY26 change of -0.33 mph (stated -0.4). Five of the nine readings "
                              "(R1, R3, R7, R8, R9) reproduce both years; the mean of trip speeds (R2), the two looser geographies "
                              "(R4, R5) and the minimal filter (R6) do not."),
        "settle": ("DOT's method note for the indicator (zone set, aggregation, trip filters, holiday list and whether trip records "
                   "or GPS are used) would settle the remaining 0.1 mph gap in FY26. The disagreement with mob-crz-traffic is one "
                   "of measure, not of data: see notes."),
        "research_needed": [
            {"question": "Why did yellow-taxi speeds fall citywide in January to June 2026 (rest of city -6.5% and Manhattan north of 60th St -5.9% against January to June 2025)?",
             "data": "TLC FHV high-volume trip records, DOT traffic speed sensors (i4gi-tjb9), MTA bus speeds",
             "design": "Compare taxi, FHV and bus speeds by area and month; check for changes in trip-record recording (both vendors show the fall)",
             "priority": "medium"},
            {"question": "Does the CBD's speed gain relative to Manhattan north of 60th St persist after the first six months of tolling?",
             "data": "TLC trip records 2023-2026, both comparison areas",
             "design": "Registered difference-in-differences by half-year with spillover-adjusted comparison areas",
             "priority": "high"},
        ],
        "figures": ["figures/reproduction/repro_mmr_cbd_speed.png"],
        "notes": (
            "The trip-record reproduction uses the 38 MTA CBD taxi zones for both pickup and drop-off, weekday pickups from 8AM to 6PM, "
            "federal holidays excluded, and total miles over total hours. It gives 6.94, 6.95 and 6.62 mph for FY24, FY25 and FY26 "
            "against the MMR's 6.9, 6.9 and 6.5. The parquet files match the NYC Open Data copies of 2024 and 2025 (rwwi-khbc, "
            "irx2-vgm4) exactly in trip count for most months of 2024 and within 0.31% for every month; the 2025 Open Data copy holds "
            "slightly fewer trips from April 2025 on, which suggests a later revision of one of the two copies. "
            "The MTA series 6p29-6xqn (all hours, taxi and FHV) ends in August 2025 and runs about 1.7 mph higher (8.57 and 8.66 mph "
            "in FY24 and FY25), so it is not the MMR's source. "
            "Reconciliation with mob-crz-traffic. The MMR number has no comparison area and uses fiscal years. FY25 holds six untolled "
            "months (July to December 2024, 6.66 mph under R1) and six tolled months (January to June 2025, 7.24 mph), so the toll's "
            "effect is averaged with the slow pre-toll autumn and FY25 equals FY24. FY26 holds the second half of 2025 (6.66 mph) and "
            "January to June 2026 (6.57 mph). In January to June 2026 taxi speeds fell everywhere in the city: by 9.2% in the CBD, 5.9% "
            "in Manhattan north of 60th Street and 6.5% in the rest of the city against January to June 2025, and the fall appears for "
            "both taxi vendors (exploratory check). The fall in the MMR number from 6.9 to 6.5 mph is therefore a citywide fall, not a "
            "fall in the CBD relative to elsewhere. Relative to the rest of the city the CBD gained: the ratio of CBD to rest-of-city "
            "speed rose 5.1% from calendar 2024 to calendar 2025, close to the +5.7% of mob-crz-traffic, and in January to June 2026 "
            "it was still 2.9% above January to June 2024. Relative to Manhattan north of 60th Street, the gain was 2.6% in January to "
            "June 2025 and had disappeared by the second half of 2025 (-0.5% against the second half of 2024) and January to June 2026 "
            "(-1.0% against January to June 2024). The two published results are both reproduced by the same trip records; they "
            "answer different questions, and the choice of comparison area changes the size and persistence of the effect. These "
            "comparison-area figures are descriptive outputs named in the registration's plan, not tests."
        ),
    }
    print(claims.outcome(rec))


if __name__ == "__main__":
    main()
