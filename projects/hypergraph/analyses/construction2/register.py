"""Out-of-sample replications of the two construction measures that the first critique round
downgraded because they were chosen after the data were seen. Run once, before any query or
computation of the new cohorts. See docs/construction_replication.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims

REGISTRANT = "Claude (construction replication agent), for Jeff Vernon"
GRAPH = [{"association_id": "(search)", "concepts": ["construction", "permit", "completion"], "n_findings": 0, "n_studies": 0,
          "direction": "0", "summary": "The graph holds no finding on building permits or permit rows (data/derived/construction/graph_search.json). The claim is about the city record.",
          "pubmed_ids": []}]
LIT = [{"citation": "U.S. Census Bureau, New Residential Construction methodology", "doi": None,
        "url": "https://www.census.gov/construction/nrc/pdf/summeas_nrc.pdf",
        "finding": "Census counts permitted housing units, one count per authorisation, not permit rows."}]

SEEN = ("Seen by the first round (12-13 Nov 2026): legacy ipu4-2q9a lifetime rows per job by first-permit cohort for 2010-2026 "
        "(funnel_by_year.csv: 7.0 to 10.3 for 2010-2019, 8.13 for the 699 legacy jobs of 2022), rows per job within each calendar year "
        "2010-2019 (2.55 to 3.28), the all-time figure of 5.97 rows per job over 95,784 jobs, and 6.87 rows per job for rows issued 2010-2019. "
        "From these seen aggregates one can derive that jobs first permitted before 2010 (about 72,900 jobs, back to the table's start) "
        "average about 5.1 rows each; this registrant derived that number from the published tables before registering. "
        "Not seen: any per-cohort value for cohorts before 2010. For DOB NOW, the first round counted jobs holding active permits by work type "
        "on given dates (sheds.py) and did not count permit rows per NB job.")

REGS = [
 {
  "id": "construction2-rows-per-job-legacy-2000s",
  "kind": "confirmation",
  "supersedes": None,
  "replicates": "construction-permit-funnel (exploratory lifetime rows per job by cohort, 7.0-10.3 for 2010-2019)",
  "statement": "In the legacy DOB permit table, each new-building job first permitted in 2000-2009 carries several permit rows over its life, so counts of NB permit rows overstate jobs, as they did for cohorts 2010-2019.",
  "graph_evidence": GRAPH,
  "literature": LIT,
  "prediction": {
   "direction": "+",
   "magnitude": "Mean lifetime rows per job between 5 and 10 in each cohort year 2000-2009; pooled 2000-2009 between 5 and 9.",
   "support_if": "pooled mean lifetime rows per job, cohorts 2000-2009, >= 5.0 AND the mean is >= 4.0 in every one of the ten cohort years",
   "refute_if": "pooled mean < 3.0 OR the mean is < 3.0 in three or more of the ten cohort years",
  },
  "plan": ("Data: DOB Permit Issuance (ipu4-2q9a), job_type='NB', all permit types and filing statuses, as fetched by "
           "analyses/construction/fetch.py on 12 Nov 2026 (data/big/construction/permits_nb_legacy.parquet; version in "
           "data/derived/construction/sources.json). Unit: job (job__). Cohort: year of the job's first permit of permit_type NB, else its first "
           "permit of any type (the definition in analyses/construction/funnel.py). Measure: number of rows for the job over the whole table "
           "(lifetime rows), mean by cohort year 2000-2009 and pooled, with a bootstrap 95% interval for the pooled mean (2,000 resamples of jobs, seed 20261113). "
           "Secondary, reported but not deciding: median rows per job and renewal share of rows by cohort. " + SEEN),
  "alternatives": [
   "Jobs from the 2000s may have had fewer permit types (equipment and plumbing permits were split out differently), lowering rows without any change in buildings per job",
   "The table may hold incomplete records for the early 2000s (missing renewals), lowering the count",
   "Long-lived stalled jobs from the 2008 crash renewed for years, raising the count for 2007-2009",
  ],
  "prior": 0.6,
  "registrant": REGISTRANT,
 },
 {
  "id": "construction2-rows-per-job-dobnow",
  "kind": "confirmation",
  "supersedes": None,
  "replicates": "construction-permit-funnel (exploratory lifetime rows per job by cohort, 7.0-10.3 for 2010-2019)",
  "statement": "In DOB NOW, each new-building job first permitted in 2021-2022 carries several work-permit rows by November 2026, so counts of permit rows overstate jobs in the current system as in the legacy one.",
  "graph_evidence": GRAPH,
  "literature": LIT,
  "prediction": {
   "direction": "+",
   "magnitude": "Mean rows per job between 4 and 12; median at least 3.",
   "support_if": "pooled mean rows per job, DOB NOW NB cohorts 2021-2022, >= 3.0 with the lower bound of its bootstrap 95% interval >= 2.5",
   "refute_if": "pooled mean rows per job < 2.0",
  },
  "plan": ("Data: DOB NOW: Build Job Application Filings (w9ak-ipjd), job_type='New Building', as fetched on 12 Nov 2026 "
           "(data/big/construction/jobs_nb_dobnow.parquet); and a new SoQL aggregation of DOB NOW: Build Approved Permits (rbx6-tga4): "
           "select job_filing_number, count(*) where issued_date >= '2020-01-01' group by job_filing_number. Unit: job, the filing number "
           "before '-'. Cohort: the earliest first_permit_date among the job's filings falls in 2021 or 2022. Measure: rows in rbx6-tga4 for all "
           "filings of the job, all work types and filing reasons, issued by the table version fetched; jobs with no rows count as 0 and are "
           "reported. Pooled mean with a bootstrap 95% interval (2,000 resamples of jobs, seed 20261113), and by cohort year. The window is "
           "incomplete (jobs still renewing), which biases the count down, against the prediction. Secondary: rows by work type and filing reason. " + SEEN),
  "alternatives": [
   "DOB NOW records renewals by updating a permit row rather than adding one, lowering the count",
   "DOB NOW may issue one permit covering several work types, lowering the count",
   "Right-censoring: cohorts 2021-2022 are still renewing",
  ],
  "prior": 0.7,
  "registrant": REGISTRANT,
 },
]

if __name__ == "__main__":
    for r in REGS:
        print(claims.register(r))
