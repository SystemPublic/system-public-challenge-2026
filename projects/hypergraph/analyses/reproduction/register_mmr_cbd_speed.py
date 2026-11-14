"""Register repro-mmr-cbd-speed before any trip data are queried.

Run once: ~/.venvs/nyc-concordance/bin/python -m analyses.reproduction.register_mmr_cbd_speed
Only dataset metadata, the taxi zone reference tables (8meu-9t5y, yfdc-w5jh)
and the report PDFs had been read when this was written.
"""
from concord import claims

CBD_ZONES = [4, 12, 13, 45, 48, 50, 68, 79, 87, 88, 90, 100, 107, 113, 114, 125, 137, 144, 148, 158,
             161, 162, 163, 164, 170, 186, 209, 211, 224, 229, 230, 231, 232, 233, 234, 246, 249, 261]

FEDERAL_HOLIDAYS_OBSERVED = [
    # FY24
    "2023-07-04", "2023-09-04", "2023-10-09", "2023-11-10", "2023-11-23", "2023-12-25",
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-05-27", "2024-06-19",
    # FY25
    "2024-07-04", "2024-09-02", "2024-10-14", "2024-11-11", "2024-11-28", "2024-12-25",
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-05-26", "2025-06-19",
    # FY26
    "2025-07-04", "2025-09-01", "2025-10-13", "2025-11-11", "2025-11-27", "2025-12-25",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25", "2026-06-19",
]
MAJOR6 = ["2023-07-04", "2023-09-04", "2023-11-23", "2023-12-25", "2024-01-01", "2024-05-27",
          "2024-07-04", "2024-09-02", "2024-11-28", "2024-12-25", "2025-01-01", "2025-05-26",
          "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25", "2026-01-01", "2026-05-25"]

rec = {
    "id": "repro-mmr-cbd-speed",
    "kind": "reproduction",
    "target": {
        "report": "Mayor's Management Report, Fiscal 2026, Department of Transportation chapter",
        "agency": "NYC Mayor's Office of Operations (indicator owner: NYC DOT, Division of Planning and Sustainability, Congestion Mitigation)",
        "date": "September 2026",
        "url": "https://www.nyc.gov/assets/operations/downloads/pdf/mmr2026/dot.pdf",
        "url_definitions": "https://www.nyc.gov/assets/operations/downloads/pdf/mmr2026/dot_idf.pdf",
        "location": "DOT performance indicator table, p. 349; indicator definition, p. 256 of the definitions volume",
        "number": {"FY22": 8.4, "FY23": 7.8, "FY24": 6.9, "FY25": 6.9, "FY26": 6.5, "unit": "mph",
                   "registered_targets": "FY25 = 6.9 and FY26 = 6.5 (primary); FY24 = 6.9 (secondary)"},
        "definition": ("'The average speed of yellow taxis traveling with passengers between the hours of 8AM-6PM, "
                       "Monday-Friday, in Manhattan's Central Business District (CBD), excluding all major US holidays. "
                       "The CBD covers the entire area south of 60th Street.' City fiscal years run July to June "
                       "(FY25 = 1 Jul 2024 to 30 Jun 2025; FY26 = 1 Jul 2025 to 30 Jun 2026)."),
        "data_used": ("Not named in the report. Assumed: TLC yellow taxi trip records (NYC Open Data rwwi-khbc for 2024, "
                      "irx2-vgm4 for 2025; TLC monthly parquet files for July 2023 to June 2026, which include "
                      "January to June 2026), with TLC taxi zones (8meu-9t5y) and the MTA CBD taxi zone list (yfdc-w5jh). "
                      "DOT may instead use GPS traces or a vendor feed that is not public."),
        "data_access": "open",
    },
    "statement": ("The MMR Fiscal 2026 values of average yellow-taxi travel speed in the Manhattan CBD (6.9 mph in FY25 and "
                  "6.5 mph in FY26) can be recomputed from TLC yellow taxi trip records within 0.2 mph under the "
                  "primary reading of the unstated parts of the method."),
    "graph_evidence": [],
    "literature": [
        {"citation": "NYC DOT (2019). New York City Mobility Report.", "doi": None,
         "finding": "DOT has computed CBD travel speeds from taxi data in earlier reports; the trip-record method is not documented in the MMR.",
         "data_access": "open"},
        {"citation": "MTA. CBD Taxi and For-Hire Vehicle Speeds: Beginning October 2019 (data.ny.gov 6p29-6xqn).", "doi": None,
         "finding": "Monthly zonal speed for the CBD from TLC records; used here as a cross-check, not as the target.",
         "data_access": "open"},
    ],
    "prediction": {
        "direction": "0",
        "magnitude": ("Tolerance: the reproduced value is within 0.2 mph of the stated value for FY25 (6.9) and for FY26 (6.5). "
                      "The stated values are rounded to 0.1 mph, so 0.2 mph allows for rounding plus a small difference of method."),
        "support_if": "Under the primary reading R1, |FY25 - 6.9| <= 0.2 and |FY26 - 6.5| <= 0.2 (verdict confirmed).",
        "refute_if": ("No registered reading R1 to R9 gives both FY25 and FY26 within 0.2 mph (verdict contested). If some "
                      "readings other than R1 reproduce both and R1 does not, or R1 reproduces one year only, the verdict is unsettled."),
        "secondary": ("(a) The FY25 to FY26 change, stated as -0.4 mph (-5.8%), is reproduced within 0.2 mph under R1. "
                      "(b) FY24 (6.9) within 0.2 mph under R1. These are reported, and do not decide the verdict."),
    },
    "readings": {
        "primary": "R1",
        "R1": ("Trips with pickup AND drop-off in the 38 MTA CBD taxi zones (yfdc-w5jh: " + ", ".join(map(str, CBD_ZONES)) +
               "); pickup time 08:00:00 to 17:59:59 local, Monday to Friday; the 11 US federal holidays (observed dates) "
               "excluded; trip filter F1; speed = total trip_distance / total trip time (ratio of sums) over all qualifying "
               "trips in the fiscal year; no passenger_count filter (every trip record is a paid passenger trip)."),
        "R2": "As R1, but the arithmetic mean of per-trip speeds.",
        "R3": "As R1, but the median of per-trip speeds.",
        "R4": "As R1, but pickup in the CBD with drop-off anywhere.",
        "R5": "As R1, but pickup or drop-off in the CBD.",
        "R6": "As R1, but filter F0 (minimal) instead of F1.",
        "R7": "As R1, but filter F2 (strict) instead of F1.",
        "R8": "As R1, but only passenger_count >= 1 (records with 0 or null passengers dropped), and only the six major holidays excluded.",
        "R9": "As R1, but the fiscal-year value is the unweighted mean of the twelve monthly ratio-of-sums values.",
        "filters": {
            "F0": "trip_distance > 0, duration > 0, speed < 100 mph",
            "F1": "0 < trip_distance <= 50 miles, 60 s <= duration <= 3 h, 0.5 <= speed <= 50 mph",
            "F2": "0.2 <= trip_distance <= 20 miles, 120 s <= duration <= 90 min, 1 <= speed <= 35 mph",
        },
        "holidays_federal_observed": FEDERAL_HOLIDAYS_OBSERVED,
        "holidays_major6": MAJOR6,
        "fiscal_year_assignment": "by pickup date; trips whose pickup timestamp falls outside the file's month are dropped",
    },
    "plan": ("Data: TLC yellow taxi monthly parquet files for July 2023 to June 2026 (36 files from "
             "d37ci6vzurychx.cloudfront.net/trip-data/, cited by URL, Last-Modified and ETag), read with duckdb and kept in "
             "~/opt/nyc-concordance/ outside Dropbox. Socrata copies rwwi-khbc (2024) and irx2-vgm4 (2025) are queried through "
             "concord/socrata.py for a monthly check of trip count and summed trip_distance under the R1 zone, hour, weekday "
             "and holiday conditions, so that the parquet files are shown to match the open-data copies. Compute FY24, FY25 "
             "and FY26 under R1 to R9. Cross-check: the MTA monthly CBD zonal speed (6p29-6xqn, data.ny.gov) averaged over "
             "the same fiscal years, descriptive only. Reconciliation with mob-crz-traffic (zone speeds +5.7% against the rest "
             "of the city) and the MTA's +4%: monthly R1 series July 2023 to June 2026 for the CBD and for trips within "
             "Manhattan north of 60th Street, calendar 2024 against 2025, and the split of FY25 into its untolled (Jul-Dec 2024) "
             "and tolled (Jan-Jun 2025) halves. These are descriptive and do not decide the verdict. Figure: monthly CBD speed "
             "under R1 and R2 with the MMR fiscal-year values drawn as steps, in figures/reproduction/."),
    "alternatives": [
        "DOT uses GPS traces or a probe-vehicle feed (not trip records), so trip-record speeds differ in level",
        "DOT uses a different zone set or a different time rule (trip wholly within 8AM-6PM)",
        "DOT averages differently (mean of trip speeds, mean of monthly values, or a segment-weighted mean)",
        "TLC revisions to the trip files since DOT computed the figure",
    ],
    "prior": 0.35,
    "registrant": "reproduction agent (Claude Opus 5.5), for J. Vernon",
}

if __name__ == "__main__":
    print(claims.register(rec))
