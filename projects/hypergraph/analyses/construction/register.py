"""Registrations for the construction topic. Run once, before any city-data query for these claims.
Each id is written by concord.claims.register and committed at once (see notes/BRIEF.md)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims

REGISTRANT = "Claude (construction agent), for Jeff Vernon"

GRAPH_NOTE = [
    {"relationship_id": "B0QiEej1E1|COEFxSZVXO", "concepts": ["population growth", "construction"], "n_findings": 1, "n_studies": 1,
     "direction": "+", "summary": "Population growth rate and expansion rate of construction land, Chongqing over 20 years (coefficient 1.82; doi:10.1117/12.815931). The only construction-supply finding found in the graph.",
     "pubmed_ids": []},
    {"association_id": "aFGrNWb1i5", "concepts": ["housing (vacant housing demolitions)", "crime"], "n_findings": 1, "n_studies": 1, "direction": "-",
     "summary": "Vacant housing demolitions and change in crime, mean difference -0.068 (CI -0.119 to -0.018), PMID 36228876. Shows the graph treats land and buildings as exposures for health and crime, not as supply outcomes.",
     "pubmed_ids": [36228876]},
    {"association_id": "(search)", "concepts": ["construction", "permit", "completion", "vacant", "demolition", "renovation"], "n_findings": 0, "n_studies": 0, "direction": "0",
     "summary": "Variable and concept searches (13 terms, data/derived/construction/graph_search.json) found no finding on building permits, permit-to-completion ratios, lags or permit lapse. The construction concept (COEFxSZVXO) has 3 relationships in all (wage, population growth, natural disasters).",
     "pubmed_ids": []},
]

LIT_CENSUS = {"citation": "U.S. Census Bureau, New Residential Construction, methodology and 'Relationship between building permits, starts and completions'",
              "doi": None, "url": "https://www.census.gov/construction/nrc/pdf/summeas_nrc.pdf",
              "finding": "Construction is undertaken for all but a very small percentage of units authorized by permit; an older bridge table puts abandonment before start near 1.5% and after start near 0.5%. Counts are housing units, not permit rows."}
LIT_DCP = {"citation": "NYC Department of City Planning, 'New Housing Permits in the First Half of 2022' (information brief, 2022)",
           "doi": None, "url": "https://atlanticyardsreport.blogspot.com/2022/11/dcp-expiration-of-421-tax-break-drove.html (quotes the brief)",
           "finding": "'Typically, 80 to 90 percent of permitted projects are completed within four years.' DOB issued permits for about 58,600 homes in the first half of 2022, ahead of the 421-a expiry."}
LIT_FURMAN = {"citation": "NYU Furman Center, State of New York City's Housing and Neighborhoods / 2019 data on the housing stock",
              "doi": None, "url": "https://furmancenter.org/thestoop/entry/2019-data-on-new-york-citys-housing-stock",
              "finding": "Median time from new-building permit to certificate of occupancy was about 1.9 years for buildings permitted in 2009-2014."}
LIT_SHEDS = {"citation": "NYC Department of Buildings, 'Get Sheds Down' plan (July 2023) and press coverage",
             "doi": None, "url": "https://www.nyc.gov/site/buildings/dob/get-sheds-down.page",
             "finding": "About 9,000 sidewalk sheds, roughly 400 miles, stood in the city in 2023; many stand for years, often for facade work under Local Law 11 (FISP)."}

REGS = [
 {
  "id": "construction-permit-funnel",
  "kind": "confirmation",
  "statement": "In New York City, counts of new-building (NB) permit rows overstate new buildings: each NB job carries several permit rows, and fewer jobs reach a certificate of occupancy and a recorded year built than are permitted.",
  "graph_evidence": GRAPH_NOTE,
  "literature": [LIT_CENSUS, LIT_FURMAN],
  "prediction": {
   "direction": "+",
   "magnitude": "Legacy DOB Permit Issuance (ipu4-2q9a), job_type NB, issued 2010-2019: rows per unique NB job between 3 and 10, with renewals at least 20% of rows. Unique NB jobs with a permit, per year 2010-2019: 1,500 to 4,500. PLUTO lots with yearbuilt in 2012-2021 per year: 40% to 100% of NB jobs permitted two years before.",
   "support_if": "rows per job >= 3 in every year 2010-2019 AND jobs reaching any CO (bs8b-p36w or pkdm-hqz6) are fewer than jobs permitted, for cohorts 2010-2017",
   "refute_if": "rows per job < 2 in most years, or CO jobs roughly equal permitted jobs (ratio > 0.97) for cohorts 2010-2017"
  },
  "plan": "SoQL aggregation by year of issuance on ipu4-2q9a (job_type='NB'): count of rows, count distinct job__, rows by filing_status (INITIAL/RENEWAL) and permit_type. DOB NOW NB jobs from w9ak-ipjd/rbx6-tga4 for 2021-2025. Join unique NB job numbers (first NB permit year) to CO records in bs8b-p36w (job_number, job_type NB) and pkdm-hqz6 (job_filing_name prefix, job_type New Building) to get the year of first CO. Compare with DCP Housing Database (br6q-ssj3) new-building completions by compltyear and PLUTO (64uk-42ks) count of lots by yearbuilt. Unit: NB job; years 2010-2025. Figure: funnel of rows, jobs, jobs with CO, HDB completions, PLUTO yearbuilt.",
  "alternatives": ["Jobs that are superseded or refiled under a new job number (the building is built, under another job)",
                   "CO records missing from open data or issued under a different job number (temporary CO only, or PAA)",
                   "PLUTO yearbuilt is estimated and often recorded late or not updated after demolition and rebuild",
                   "Recent cohorts are right-censored (not yet finished)"],
  "prior": 0.75,
  "registrant": REGISTRANT,
 },
 {
  "id": "construction-four-year-completion",
  "kind": "confirmation",
  "statement": "The share of NYC new-building jobs that reach a certificate of occupancy within four years of first permit matches the Department of City Planning's statement that 80 to 90 percent of permitted projects are completed within four years.",
  "graph_evidence": GRAPH_NOTE,
  "literature": [LIT_DCP, LIT_FURMAN, LIT_CENSUS],
  "prediction": {
   "direction": "+",
   "magnitude": "Registrant's expectation: the job-level share with a first CO (temporary or final) within 4 years of first NB permit, cohorts 2010-2017, is about 0.70, range 0.55 to 0.85; median permit-to-CO time 1.8 to 3.0 years among jobs that reach a CO. Research value: 0.80-0.90 (DCP), median 1.9 years (Furman), near-complete eventual completion (Census).",
   "support_if": "pooled 2010-2017 four-year share between 0.75 and 0.95 (consistent with DCP's 0.80-0.90 given measurement differences)",
   "refute_if": "pooled 2010-2017 four-year share below 0.65 with a 95% interval excluding 0.75; then the NYC job-level data conflict with the DCP statement"
  },
  "plan": "Cohort = unique NB job numbers in ipu4-2q9a whose first NB permit (permit_type NB, filing_status INITIAL) was issued 2010-2017. Outcome = earliest CO issue date for the same job number in bs8b-p36w or pkdm-hqz6. Share with CO within 1461 days, by cohort year, with Wilson 95% intervals and pooled. Residential subset checked against DCP Housing Database (br6q-ssj3: datepermit, datecomplt, job_status) as a second measure of the same quantity. Eventual completion share for cohorts 2010-2014 (CO by Nov 2026) compared with the Census near-100% statement.",
  "alternatives": ["DCP counts projects or units, and units weight large projects that finish more reliably than small one- and two-family jobs",
                   "Job numbers change between filing systems (BIS to DOB NOW), so a real CO is not matched",
                   "Buildings occupied without a CO (illegal occupancy or only a letter of no objection)",
                   "Withdrawn or superseded jobs that never meant to build"],
  "prior": 0.35,
  "registrant": REGISTRANT,
 },
 {
  "id": "construction-sheds-outnumber-nb",
  "kind": "confirmation",
  "statement": "On a given day, the construction a person sees on NYC streets is mostly not new buildings: active sidewalk-shed permits outnumber active new-building jobs, and most sheds stand on lots without an active new-building job.",
  "graph_evidence": GRAPH_NOTE,
  "literature": [LIT_SHEDS],
  "prediction": {
   "direction": "+",
   "magnitude": "Reference date 2026-11-01. Active sidewalk-shed permits (DOB NOW Build approved permits with work type Sidewalk Shed, issued on or before the date and expiring after it, counted by distinct job filing): 6,000 to 11,000. Active NB jobs (an NB work permit issued and unexpired on the date, in either system): 1,500 to 5,000. Ratio sheds/NB between 1.5 and 6. Share of active sheds on a BBL with an active NB job: 5% to 25%.",
   "support_if": "ratio of active shed jobs to active NB jobs > 1.2 AND share of sheds on NB lots < 0.35",
   "refute_if": "ratio < 0.8 or share of sheds on NB lots > 0.5"
  },
  "plan": "SoQL on rbx6-tga4 (work_type for sidewalk sheds; NB work permits via job_filing_number joined to w9ak-ipjd job_type 'New Building') and on ipu4-2q9a (legacy NB permits still active, expiration_date after the date). Count distinct jobs active on 2026-11-01, plus a monthly series of active shed and NB jobs 2022-2026 if queries allow. Join on BBL for the overlap share. Also count active alteration and facade (FISP, xubg-57si) work for context. Figure: bar chart of active jobs by kind on the date.",
  "alternatives": ["Permit 'active' status overstates sheds actually standing (sheds removed before the permit expires) or understates them (sheds standing on expired permits)",
                   "Sheds per job differ (one job may carry several shed permits along a frontage)",
                   "Perception is driven by cranes and tall towers, not by count of sites"],
  "prior": 0.6,
  "registrant": REGISTRANT,
 },
 {
  "id": "construction-aerial-triangulation",
  "kind": "bridge",
  "statement": "Aerial photographs (USDA NAIP) give a third, independent record of whether permitted new buildings were built: for a random sample of NB jobs first permitted 2018-2020, visible change on the lot between a pre-permit and a recent NAIP year agrees with the CO record, and shows sites under construction that the CO record misses.",
  "graph_evidence": GRAPH_NOTE,
  "literature": [LIT_DCP, LIT_FURMAN],
  "prediction": {
   "direction": "+",
   "magnitude": "Random sample of 48 NB jobs (seed 20261112) first permitted 2018-2020. Visible change of the lot between the latest NAIP year <= 2017 and the latest year >= 2022: 65% to 90% of jobs. Agreement of visible change with 'has a CO by the later image date': Cohen's kappa 0.2 to 0.7. Jobs changed on the aerial but without a CO: 10% to 35%. Jobs with a CO but no visible change: under 10%.",
   "support_if": "visible-change share >= 0.6 AND kappa > 0.2 AND CO-but-no-change share < 0.15",
   "refute_if": "visible-change share < 0.45, or CO-but-no-change share >= 0.25 (the aerial and the CO disagree about what was built)"
  },
  "plan": "Sample NB jobs from ipu4-2q9a (first NB permit 2018-2020) and DOB NOW (w9ak-ipjd New Building with first_permit_date 2018-2020), stratified by nothing, seed fixed. Lot polygon from PLUTO (64uk-42ks geom) by BBL. NAIP tiles from the Planetary Computer STAC for the lot box plus a 15 m margin, earlier and later years. Primary measure: my visual judgement of each before/after pair (changed / unchanged / unclear), made on a label-free grid BEFORE the CO status is joined, saved as data/derived/construction/aerial_judgements.csv. Secondary measure: mean absolute difference of grey levels inside the lot polygon after per-image standardisation, with a threshold set by eye on 6 cases. Then join CO status and compute the 2x2 table and kappa. Figure: grid of before/after thumbnails.",
  "alternatives": ["Seasonal and sun-angle differences in NAIP make unchanged lots look changed",
                   "Tall neighbouring buildings lean over small lots in an orthophoto and hide them",
                   "Interior gut renovations under an NB filing (rare) or enlargements produce little roof change",
                   "Demolition alone (lot cleared, not rebuilt) counts as visible change but is not a completed building"],
  "prior": 0.45,
  "registrant": REGISTRANT,
  "chain": ["construction-permit-funnel", "construction-four-year-completion"],
 },
]

if __name__ == "__main__":
    for r in REGS:
        print(claims.register(r))
