"""Register repro-dcp-2025-completions before any data values of br6q-ssj3 are queried."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims

TARGET_NUM = 38682
rec = {
 "id": "repro-dcp-2025-completions",
 "kind": "reproduction",
 "target": {
  "report": "NYC Housing Production Snapshot 2025",
  "agency": "NYC Department of City Planning (DCP)",
  "date": "ArcGIS StoryMap, item modified March 2026",
  "url": "https://storymaps.arcgis.com/ (DCP Housing Production Snapshot 2025; the br6q-ssj3 description links the 21Q4 edition at https://storymaps.arcgis.com/stories/1c9138dc24064b2e8142ff156345a719)",
  "location": "Completed Units section; Permitted Units section; borough panel",
  "number": {"completed_units_new_buildings_2025": 38682, "new_building_permit_units_2025": 17673,
             "completed_by_borough": {"Brooklyn": 18048, "Queens": 9600, "Bronx": 5683, "Staten Island": 477,
                                      "Manhattan (by subtraction)": 38682 - 18048 - 9600 - 5683 - 477}},
  "definition": "'38,682 housing units were completed in new buildings in New York City in 2025'. Units, calendar year 2025, citywide, new-building jobs only. The snapshot does not state the completion rule or the unit field.",
  "data_used": "DCP Housing Database, release 25Q4 (the snapshot's release). Portal copy: Housing Database Project Level Files br6q-ssj3, rowsUpdatedAt 2026-09-30, 'Current version: 26q2.1' per its description. Aggregates dbdt-5s7j (by community district) and kyz5-72x5 (by NTA).",
  "data_access": "open"
 },
 "statement": "The DCP Housing Production Snapshot's count of 38,682 housing units completed in new buildings in 2025 is reproduced, within 4% (allowing for revision between the 25Q4 and 26Q2.1 releases), by summing proposed Class A units of new-building jobs whose first certificate of occupancy fell in 2025 in the portal copy of the Housing Database.",
 "graph_evidence": [],
 "literature": [
  {"citation": "NYC DCP, Housing Database data dictionary, column descriptions on br6q-ssj3", "doi": None,
   "finding": "compltyear is the year of the first certificate of occupancy for new buildings; classaprop counts proposed Class A units; units_co counts units on the latest temporary or final CO and may include Class B and hotel units.", "data_access": "open"},
  {"citation": "NYC DCP, Housing Production Snapshot 2024 and the 25Q4/25Q2 releases (as summarised in docs/reproduction_inventory.md)", "doi": None,
   "finding": "DCP's 2024 completion count moved from 33,974 to 33,859 (-0.34%) between releases, which sets the scale of revision the tolerance allows.", "data_access": "open"}
 ],
 "prediction": {
  "direction": "0",
  "magnitude": "Primary reading R1 within 37,135 to 40,229 (38,682 +/- 4%). Registrant's expectation: R1 between 37,500 and 39,500; R2 (units_co) higher than R1 by 0 to 5% because units_co can include Class B and hotel units, or lower if partial COs record fewer units than proposed.",
  "tolerance": {"exact_band": "|R - 38682| / 38682 <= 0.02 (37,908 to 39,456): reported as reproduced exactly",
                "revision_band": "|R - 38682| / 38682 <= 0.04 (37,135 to 40,229): reproduced allowing for release revision. A later release usually adds late-recorded COs for the latest year, and DCP edits unit counts; 0.04 is about ten times the 2024 revision of 0.34% and is set wide on purpose because 2025 was the newest year in 25Q4",
                "boroughs": "each borough within 4%, except Staten Island within 10% (small count)",
                "permits": "17,673 within 4% under P1"},
  "support_if": "R1 (primary) falls within the revision band (+/-4%) -> confirmed. Whether it also falls within the exact band (+/-2%) is reported.",
  "refute_if": "no registered completion reading (R1, R2, R3) falls within the revision band -> contested. If R1 is outside but R2 or R3 is inside, the verdict is unsettled (the report's unstated rule matters)."
 },
 "readings": {
  "R1 (primary)": "job_type = 'New Building', compltyear = 2025, sum of classaprop, all job_status values (jobs with a first CO in 2025 are status 4 'Partially Completed Construction' or 5 'Completed Construction'). For new buildings classaprop equals classanet, so net and gross agree; hotel and other Class B units are excluded.",
  "R2": "as R1 but sum of units_co (units on the latest CO, temporary or final; may include Class B and hotel units, and partial COs may list fewer units than proposed).",
  "R3": "as R1 but only job_status '5. Completed Construction' (final or complete CO), i.e. partial completions excluded.",
  "permits P1 (primary)": "job_type = 'New Building', permityear = 2025, sum of classaprop, excluding job_status '9. Withdrawn'.",
  "permits P2": "as P1, all job_status values including withdrawn.",
  "boroughs": "R1 grouped by boro.",
  "cross_check_not_a_reading": "sum of comp2025 over community districts in dbdt-5s7j. These aggregates count net units across all job types (new buildings, alterations, demolitions), apparently incrementally as COs are issued, so they are not expected to equal a new-building count; reported for context only."
 },
 "release_choice": "DCP archives earlier releases on BYTES of the BIG APPLE (https://www.nyc.gov/content/planning/pages/resources/datasets/housing-project-level). The 25Q4 project-level CSV exists at https://s-media.nyc.gov/agencies/dcp/assets/files/zip/data-tools/bytes/housing-database/housing-project-level/nychdb_25q4_csv.zip (HTTP HEAD on 12 Nov 2026: 200, 9,278,590 bytes, Last-Modified 4 Mar 2026). It is not used in this run, because downloading a file needs Jeff's approval and the run has none. The test uses the portal copy (26q2.1), and the revision band carries the difference. A follow-up test on 25Q4 is registered here in advance: R1 computed on nychdb_25q4_csv.zip (columns Job_Type, CompltYear, ClassAProp as in the data dictionary) is judged by the exact band (+/-2%) alone; it is reported as a secondary result and does not change this claim's verdict.",
 "plan": "Before any query: metadata only. Then SoQL aggregations on br6q-ssj3 through concord.socrata.query: (a) sum(classaprop), sum(units_co), count(*) where job_type='New Building' and compltyear='2025', grouped by job_status and boro; (b) same grouped by permityear (exploratory: which permit cohorts completed in 2025); (c) sum(classaprop) where job_type='New Building' and permityear='2025' grouped by job_status; (d) distinct version values; (e) sum(comp2025) on dbdt-5s7j. Also R1 for 2024 to compare with DCP's published 33,859 (25Q4) and 33,974 (earlier), as a check on the revision band. Unit: housing units. Figure: stated vs reproduced by reading and by borough, with the 2% and 4% bands. Outcome in claims/outcomes/, figure in figures/reproduction/, section in docs/reproduction.md.",
 "alternatives": [
  "Release revision: the 26q2.1 copy differs from 25Q4 by late-recorded COs and DCP edits, so a mismatch may be revision and not a different rule.",
  "The snapshot counts units incrementally as partial COs are issued (units on COs issued in 2025, including later COs of buildings first completed earlier) rather than all proposed units of buildings with a first CO in 2025.",
  "The snapshot counts units_co or includes non-Class A units.",
  "The snapshot's 2025 includes jobs DCP later reclassified or merged."
 ],
 "prior": 0.6,
 "disclosure": "Before registration the registrant read docs/construction.md and docs/reproduction_inventory.md, which give Housing Database figures for other years (completed residential new buildings 2012-2021: 14,756 jobs; unit-weighted four-year completion 0.67 for 2015 and 0.66 for 2022) but no 2025 completion count. The project's cache holds an earlier fetch of br6q-ssj3 (data/cache/socrata/br6q-ssj3-40f632f667d49f29e1b1d591.json, 12 Nov 2026 15:21, same rowsUpdatedAt 2026-09-30, all 35,188 new-building rows with compltyear, classaprop, units_co), and data/derived/construction/funnel_by_year.csv has columns hdb_completed_jobs and hdb_units by year. The registrant inspected only the query record and the column headers of these files, not their values.",
 "registrant": "reproduction agent (Claude Opus 5.5), session fe2cedf2",
}
print(claims.register(rec, overwrite=True))  # overwrite used once, before commit and before any data query, to correct release_choice
