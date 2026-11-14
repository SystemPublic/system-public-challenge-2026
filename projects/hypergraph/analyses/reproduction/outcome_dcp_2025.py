"""Write the outcome of repro-dcp-2025-completions from data/derived/reproduction/."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims

r = json.loads((ROOT / "data/derived/reproduction/dcp_2025_results.json").read_text())
src = json.loads((ROOT / "data/derived/reproduction/dcp_2025_sources.json").read_text())
for s in src:
    s["data_access"] = "open"
R1, R2 = r["readings"]["R1"], r["readings"]["R2"]
rel = (R1 - 38682) / 38682
rev = 0.0034  # scale of DCP's own 2024 revision between releases
by_py = {x.get("permityear"): float(x["units"]) for x in r["completions_2025_by_permityear"]}
share22 = by_py["2022"] / R1

rec = {
 "id": "repro-dcp-2025-completions",
 "verdict": "confirmed",
 "city_effect": {"label": "relative difference, R1 (sum of classaprop, New Building, compltyear 2025, 26Q2.1) minus DCP's 38,682, as a share of 38,682; interval is +/- the 0.34% revision DCP made to 2024 between releases, not a sampling interval",
                 "estimate": round(rel, 5), "lo": round(rel - rev, 5), "hi": round(rel + rev, 5), "scale": "proportion", "null": 0, "n": r["readings"]["jobs"]},
 "graph_effect": None,
 "reproduced": {
  "R1_primary_classaprop": R1, "R2_units_co": R2, "R3_final_co_only": r["readings"]["R3"],
  "stated": 38682, "R1_rel_diff": round(rel, 5), "R2_rel_diff": round((R2 - 38682) / 38682, 4),
  "boroughs_R1": {"Manhattan": r["boro_R1"]["1"], "Bronx": r["boro_R1"]["2"], "Brooklyn": r["boro_R1"]["3"], "Queens": r["boro_R1"]["4"], "Staten Island": r["boro_R1"]["5"]},
  "boroughs_stated": {"Manhattan (by subtraction)": 4874, "Bronx": 5683, "Brooklyn": 18048, "Queens": 9600, "Staten Island": 477},
  "permits_P1": r["P1"], "permits_P2": r["P2"], "permits_stated": 17673, "P1_rel_diff": round((r["P1"] - 17673) / 17673, 4),
  "R1_2024": 33859, "dcp_2024_stated": {"earlier release": 33974, "25Q4": 33859},
  "aggregate_dbdt_5s7j_comp2025_all_job_types": 43654.0,
  "completed_2025_units_by_permit_year": by_py,
  "jobs_completed_2025": r["readings"]["jobs"], "version": "26Q2.1"
 },
 "sources": src + [{"kind": "report", "name": "NYC DCP, Housing Production Snapshot 2025 (ArcGIS StoryMap, modified March 2026)", "data_access": "open",
                    "note": "stated numbers as transcribed in docs/reproduction_inventory.md"}],
 "prediction_scored": "hit. R1 is 38,689 against the stated 38,682 (+7 units, +0.02%), inside the exact band of 2%, and the boroughs agree within 8 units each. R2 (units_co, 40,567, +4.9%) lies outside the revision band, so the snapshot counts proposed Class A units, not units on the certificate. R3 equals R1 because every new-building job with a first CO in 2025 has status 5 in this release. The registrant expected R2 to exceed R1 by 0 to 5%; it exceeds it by 4.9%. The secondary permit count was not reproduced: P1 is 18,539 against 17,673 (+4.9%), outside the 4% band.",
 "settle": "The permit difference (866 units) would be settled by computing P1 on the archived 25Q4 file (nychdb_25q4_csv.zip on DCP's BYTES page, 9.3 MB), which shows whether the extra units are permits recorded after the 25Q4 cut-off or a different permit rule in the snapshot. The same file gives the exact-band follow-up test for completions registered in advance.",
 "research_needed": [
  {"question": "Are the 866 extra 2025 new-building permit units in 26Q2.1 late-recorded permits, or does the snapshot count permits differently (for example excluding jobs later superseded)?", "data": "DCP Housing Database 25Q4 and 26Q2.1 project-level files (BYTES archive); DOB NOW approved permits rbx6-tga4", "design": "job-level diff between releases for permityear 2025", "priority": "medium"},
  {"question": "How much of a year's completions belong to the 421-a deadline cohort, and when does that cohort's contribution end?", "data": "br6q-ssj3 releases through 2027", "design": "completed units by compltyear x permityear, tracked across releases", "priority": "high"}
 ],
 "figures": ["figures/reproduction/dcp_2025_completions.png"],
 "notes": (
  "The DCP headline count is reproduced to within 7 units from the public portal copy, using the rule that the Housing Database data dictionary implies: new-building jobs whose first certificate of occupancy fell in 2025 (compltyear), counted by proposed Class A units (classaprop, which equals classanet for new buildings). The release used is 26Q2.1, later than the 25Q4 release the snapshot used. The completion counts barely moved between releases: R1 for 2024 is 33,859, the same as DCP's 25Q4 figure. The 25Q4 archive was found after the first draft of the registration and before commit; it was not downloaded, because a file download needs Jeff's approval. "
  f"Exploratory, not a test: of the 38,689 units completed in 2025, {by_py['2022']:,.0f} ({share22:.0%}) were in jobs first permitted in 2022, the year of the 421-a deadline rush, and 6,875 in jobs permitted in 2023. Units completed in new buildings rose from 33,859 in 2024 to 38,689 in 2025, while units in new-building permits issued in 2025 were 18,539 (P1). The high 2025 completion count is therefore the 2022 permit surge reaching certificates of occupancy, not a rise in new starts. "
  "The aggregate table dbdt-5s7j gives 43,654 net units for 2025 across all job types (alterations and demolitions included, counted incrementally), so the aggregate tables do not equal the new-building figure and should not be quoted as it. "
  "R2 shows that units_co, the field a reader might choose for 'units completed', overstates the snapshot by 4.9%, because certificates can include Class B and hotel units."
 ),
}
print(claims.outcome(rec))
