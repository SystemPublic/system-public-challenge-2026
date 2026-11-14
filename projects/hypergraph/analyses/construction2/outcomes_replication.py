"""Write the outcomes of the two registered replications from data/derived/construction2/replication_summary.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims

S = json.loads((ROOT / "data/derived/construction2/replication_summary.json").read_text())
L, N = S["legacy"], S["dobnow"]
RN = [{"question": "How many permit rows does a typical NB job carry in each system, and are the systems' rows comparable (renewal practice, work types)?",
       "data": "DOB Permit Issuance ipu4-2q9a; DOB NOW Build Approved Permits rbx6-tga4", "design": "Match jobs that moved between systems and compare row counts per job", "priority": "low"}]

claims.outcome({
 "id": "construction2-rows-per-job-legacy-2000s",
 "verdict": "confirmed",
 "city_effect": {"label": "legacy NB permit rows per job over the table's life, jobs first permitted 2000-2009", "estimate": round(L["pooled_mean"], 2),
                 "lo": round(L["lo"], 2), "hi": round(L["hi"], 2), "scale": "rows per job (null: 1 row per building)", "null": 1, "n": L["jobs"]},
 "graph_effect": None,
 "sources": S["sources"][:1],
 "prediction_scored": ("hit on the decisive rule, partial on magnitude: the pooled mean was 5.89 rows per job (95% bootstrap interval 5.85 to 5.92; "
                       "49,959 jobs, 294,033 rows) and the lowest cohort mean was 4.37 (2000), so both support conditions were met. "
                       "The registered magnitude of 5 to 10 in every year missed for 2000 (4.37) and 2001 (4.55)."),
 "settle": "The replication settles the descriptive point for the legacy table. Whether rows per job grew over time because of renewals or because of more permit types per job is a separate question.",
 "research_needed": RN,
 "figures": ["figures/construction2/rows_per_job_replication.png"],
 "notes": ("Registered in commit 6159cf6 before any per-cohort value for cohorts before 2010 was computed. The registration disclosed that the first round's "
           "published aggregates implied about 5.1 rows per job for all jobs first permitted before 2010. Cohort means rose from 4.37 (2000) to 7.71 (2008); "
           "renewals were 42% of rows in 2000 and 66% in 2008. Medians were 4 to 6. "
           "The rise for 2007-2009 fits the registered alternative that jobs stalled by the 2008 crash renewed for years."),
})

claims.outcome({
 "id": "construction2-rows-per-job-dobnow",
 "verdict": "confirmed",
 "city_effect": {"label": "DOB NOW work-permit rows per NB job by Nov 2026, jobs first permitted 2021-2022", "estimate": round(N["pooled_mean"], 2),
                 "lo": round(N["lo"], 2), "hi": round(N["hi"], 2), "scale": "rows per job (null: 1 row per building)", "null": 1, "n": N["jobs"]},
 "graph_effect": None,
 "sources": S["sources"][1:],
 "prediction_scored": ("hit on the decisive rule, partial on magnitude: the pooled mean was 12.8 rows per job (95% bootstrap interval 12.2 to 13.3; 1,528 jobs), "
                       "above the support threshold of 3.0, but above the registered range of 4 to 12. The median was 10."),
 "settle": "The count will rise as the 2021-2022 jobs keep renewing; a re-count in 2028 would give a lifetime value.",
 "research_needed": RN,
 "figures": ["figures/construction2/rows_per_job_replication.png"],
 "notes": ("Registered in commit 6159cf6. Cohort means were 10.0 (2021, 253 jobs) and 13.3 (2022, 1,275 jobs); 19 jobs had no rows. "
           "Of 19,513 rows, 10,482 were initial permits and 9,031 renewals (46%). The largest work types were General Construction (4,121), "
           "Foundation (3,318), Structural (2,425), Earth Work (2,036), Plumbing (1,706) and Mechanical Systems (1,697). "
           "DOB NOW splits an NB job into more work types than the legacy system did, so its rows per job are higher; the registered "
           "alternative that DOB NOW updates rather than adds renewal rows is contradicted by the 9,031 renewal rows."),
})
print("ok")
