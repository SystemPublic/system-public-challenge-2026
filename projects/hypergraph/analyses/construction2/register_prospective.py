"""Prospective registration: completion of the 2022 421-a rush cohort by mid-2027.

The report (docs/REPORT.md, section 5) notes that only a registration made before its data
exist is out of sample for the completion rate. This script registers such a test on
12 November 2026. The data it names (a Housing Database release covering 30 June 2027) do not
exist yet. Run once; registrations are not edited.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims

REGISTRANT = "Claude (prospective-registration agent), for Jeff Vernon"

GRAPH = [{"association_id": "(search)", "concepts": ["construction", "permit", "completion"], "n_findings": 0, "n_studies": 0,
          "direction": "0",
          "summary": "The graph holds no finding on building permits, permit-to-completion ratios, lags or permit lapse "
                     "(data/derived/construction/graph_search.json). The research side comes from the literature.",
          "pubmed_ids": []}]

LIT = [
 {"citation": "NYC Department of City Planning, 'New Housing Permits in the First Half of 2022' (information brief, 2022)",
  "doi": None,
  "url": "https://atlanticyardsreport.blogspot.com/2022/11/dcp-expiration-of-421-tax-break-drove.html (quotes the brief)",
  "finding": "'Typically, 80 to 90 percent of permitted projects are completed within four years.' DOB issued permits for "
             "about 58,600 homes in the first half of 2022, ahead of the 421-a expiry."},
 {"citation": "NYU Furman Center, 2019 data on New York City's housing stock",
  "doi": None,
  "url": "https://furmancenter.org/thestoop/entry/2019-data-on-new-york-citys-housing-stock",
  "finding": "Median time from new-building permit to certificate of occupancy was about 1.9 years for buildings permitted in 2009-2014."},
]

SEEN = ("Seen before this registration, all from the first round (12 Nov 2026): the unit-weighted Housing Database share for the "
        "2022 permit cohort with a completion date by July 2026, 0.66, as stated in the settle text of "
        "construction-four-year-completion (that outcome does not record whether its cohort was calendar 2022 or its first half; "
        "this registrant did not re-query to find out); the 2015 cohort's unit-weighted four-year share, 0.67; the job-level "
        "DOB measure for the calendar-2022 cohort, 1,599 of 1,974 jobs (0.810) with a CO by November 2026 "
        "(data/derived/construction/cohort_completion.csv); and the Housing Database job-level four-year shares for cohorts "
        "2010-2021, 0.756 to 0.881 (data/derived/construction/funnel_summary.json). "
        "Not seen, because they do not exist: any completion recorded after the Housing Database release current in "
        "November 2026. This registrant made no query to NYC Open Data; both machines used had no access to it.")

REG = {
 "id": "construction-2022-rush-units-2027",
 "kind": "confirmation",
 "supersedes": None,
 "follows": "construction-four-year-completion (settle condition 2 and its first research_needed entry)",
 "prospective": True,
 "statement": ("At least 80 percent of the housing units in new-building jobs permitted in the first half of 2022, ahead of the "
               "421-a expiry, will have a completion date on or before 30 June 2027, as DCP's statement that 80 to 90 percent "
               "of permitted projects are completed within four years implies when one extra year is allowed."),
 "graph_evidence": GRAPH,
 "literature": LIT,
 "prediction": {
  "direction": "+",
  "magnitude": ("Registrant's expectation: unit-weighted share 0.72 to 0.82, central 0.77. A rise from about 0.66 in July 2026 "
                "is expected because the median permit-to-CO time is about two years, but the 2031 extension of the 421-a "
                "completion deadline removes the pressure to finish soon. Research value: 0.80 to 0.90 within four years (DCP), "
                "so at least 0.80 within five."),
  "support_if": "unit-weighted share with a completion date on or before 30 June 2027 is >= 0.80",
  "refute_if": ("unit-weighted share < 0.75 AND the upper bound of its 95% bootstrap interval is < 0.80; then the rush cohort "
                "conflicts with DCP's typical completion rate even with a year's allowance"),
 },
 "plan": ("Data: the first DCP Housing Database release whose records run to at least 30 June 2027 (expected to be the 2027 Q2 "
          "release, on NYC Open Data as br6q-ssj3 or its successor, or on DCP's Bytes of the Big Apple). Record its version, "
          "release date and the dataset's rowsUpdatedAt. "
          "Cohort: records with job_type 'New Building' and datepermit from 2022-01-01 to 2022-06-30 inclusive, all job_status "
          "values, withdrawn jobs included, because DCP's statement is about permitted projects. "
          "Weight: proposed class A units (classaprop); records with missing or zero classaprop are excluded from the unit measure "
          "and counted in a note. "
          "Outcome: datecomplt (the first certificate of occupancy, temporary or final) on or before 2027-06-30. "
          "Statistic: units in completed jobs divided by units in the cohort, with a 95% interval from 2,000 bootstrap resamples "
          "of jobs (seed 20270630). "
          "If the field names have changed, map them by the release's data dictionary and record the mapping. "
          "Secondary, reported but not deciding: the job-level share; the share excluding withdrawn jobs; the share of units in "
          "jobs whose units_co has reached classaprop (complete rather than first CO); the same measure for the second half of "
          "2022; and the share at 15 June 2031, the extended 421-a completion deadline, when that release exists. "
          "Cross-check, not deciding: match cohort job numbers to DOB NOW certificates of occupancy (pkdm-hqz6). " + SEEN),
 "alternatives": [
  "Placeholder filings: some jobs were permitted only to vest 421-a eligibility and were not meant to start soon, lowering the share without any change in how ordinary projects finish",
  "The extension of the 421-a completion deadline to June 2031 removed the pressure to finish by 2026, so the cohort finishes later than DCP's typical projects",
  "Interest rates and construction costs after 2022 slowed financing of large multifamily projects, which carry most of the units",
  "The Housing Database records a completion only when DOB issues a CO, so buildings occupied without one, or with a CO entered late, count as incomplete",
  "DCP's statement may refer to projects or to units; a project-weighted figure would differ from the unit-weighted one",
 ],
 "prior": 0.25,
 "registrant": REGISTRANT,
}

if __name__ == "__main__":
    print(claims.register(REG))
