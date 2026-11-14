"""Write the outcomes of the four construction claims from the derived results."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "construction"
S = json.loads((D / "sources.json").read_text())
FS = json.loads((D / "funnel_summary.json").read_text())
SH = json.loads((D / "sheds_summary.json").read_text())
AE = json.loads((D / "aerial_summary.json").read_text())

GRAPH_SRC = {"kind": "sysgraph", "api_version": "v1.0", "dataset_version": "Dataverse v2.1, doi:10.7910/DVN/7V6JDO",
             "queries": "variable and concept search for 13 terms; relationships of concepts COEFxSZVXO (construction), jCrN64TC75 (building), IFcQ3j86qe (housing); associations of 8 variables",
             "derived": "data/derived/construction/graph_search.json", "fetched": "2026-11-12"}
GRAPH_NOTE = ("Graph evidence check (12 Nov 2026, after the coordinator's audit): association aFGrNWb1i5 (vacant housing demolitions and "
              "'change in crime', PMID 36228876), cited in the registration, is NOT in the Dataverse v2.1 CSV. The abstract (Kvik et al., Prev Med 2022) "
              "shows it is mis-extracted: the -0.068 (95% CI -0.119 to -0.018) is the change in total emergency-department visits per 1,000 people, and "
              "demolitions showed no significant change in crime. It should be dropped; it bore on context only, not on any test here. Of the other graph rows "
              "cited, UXzKbLS899 (population growth and construction land, Chongqing) is in the CSV. The vacant-lot and renovation rows looked at during the search "
              "(3rfxckzPtm, R0ctB4TYK1, CVCABCQUUe, 168lUaKwYN, 20AOg9kwfR, IfVJnDqqH0) are not in the CSV. The graph holds no finding on permits, "
              "permit-to-completion ratios, lags or permit lapse, so the research side of every construction claim comes from the literature.")
RN_GRAPH = {"question": "Should the graph hold findings on housing supply (permits, starts, completions, lapse)? It now holds none.",
            "data": "Census New Residential Construction; NYC DCP Housing Database; Furman Center CoreData", "design": "extraction of urban-economics and planning literature into the graph",
            "priority": "medium"}


def src(*keys):
    return [S[k] for k in keys if k in S]


o1 = {
 "id": "construction-permit-funnel",
 "verdict": "confirmed",
 "city_effect": {"label": "legacy NB permit rows per distinct NB job, rows issued 2010-2019", "estimate": round(FS["rows_per_unique_job_2010_2019"], 2),
                 "lo": None, "hi": None, "scale": "rows per job (null: 1 row per building)", "null": 1, "n": FS["unique_jobs_2010_2019"]},
 "graph_effect": None,
 "sources": src("permits_nb_legacy", "co_legacy_nb", "co_dobnow", "jobs_nb_dobnow", "hdb_nb", "pluto_yearbuilt") + [GRAPH_SRC],
 "prediction_scored": ("hit on the main measure, partial on one sub-criterion. Rows per distinct job 2010-2019 were 6.87 (173,976 rows, 25,339 jobs; predicted 3-10); "
                       "renewals were 54% of all 572,035 NB rows (predicted at least 20%); NB jobs per year 1,309-2,491 (predicted 1,500-4,500; 2010-2012 and 2020 fell slightly below); "
                       "jobs with a CO by November 2026 were fewer than jobs permitted in every cohort 2012-2019 (ratio 0.88-0.93). The support rule 'rows per job >= 3 in every year' holds for the lifetime rows of each "
                       "cohort (7.0-10.3) but not for rows per job active within one calendar year (2.55-2.90 in 2010-2012). PLUTO lots by year built were 0.51-1.16 of NB jobs permitted two years before (0.80-0.99 for permit years 2010-2017 except 2012 at 1.16); the predicted range was 0.4-1.0. The low values for 2018-2019 reflect the 2020-2021 dip in completions and late PLUTO updates."),
 "settle": "Rows per job is a property of the record, not in dispute. What remains is how many NB jobs are superseded or refiled under a new number, which needs DOB's job-relationship table (HDB hpd_jobrel or BIS 'related jobs').",
 "research_needed": [
  {"question": "What share of NB permit rows are renewals of stalled jobs, and how long do such jobs stall?", "data": "ipu4-2q9a renewals by job, with gaps between expiry and renewal", "design": "survival analysis of time from first permit to CO, with renewal gaps as events", "priority": "medium"},
  {"question": "Do news and policy counts of 'permits' use rows, jobs or units?", "data": "press releases, REBNY and DCP reports", "design": "content audit", "priority": "low"},
  RN_GRAPH],
 "figures": ["figures/construction/funnel_2010_2019.png", "figures/construction/funnel_by_year.png"],
 "notes": ("The legacy DOB Permit Issuance table has 572,035 rows with job_type NB, for 95,784 distinct job numbers (5.97 rows per job over the table's life). The rows are of five permit types "
           "(NB 267,198; PL 129,572; EQ 126,366; FO 48,730; EW 169), and 309,782 (54%) are renewals. For permits issued 2010-2019 the 173,976 rows belong to 25,339 jobs, and 19,095 jobs had their first NB permit "
           "in those years; 16,297 of these (85%) have a certificate of occupancy by November 2026. Over 2012-2021 the Housing Database records 14,756 completed residential new buildings and PLUTO has 15,813 lots with "
           "those years built. The 173,976 rows are about 11 times the 16,297 jobs that reached a CO, and the 19,095 permitted jobs are 17% more than those completed jobs. (The 25,339 jobs with rows in 2010-2019 include jobs first permitted before 2010.) Since 2021 NB jobs are filed in DOB NOW (w9ak-ipjd), and legacy rows after 2021 "
           "are mostly renewals of older jobs. " + GRAPH_NOTE),
}

s4 = FS["share_4y_2013_2017"]
o2 = {
 "id": "construction-four-year-completion",
 "verdict": "confirmed",
 "city_effect": {"label": "share of NB jobs with a first CO within 4 years of first NB permit, cohorts 2013-2017", "estimate": round(s4["p"], 3),
                 "lo": round(s4["lo"], 3), "hi": round(s4["hi"], 3), "scale": "proportion (null: DCP lower bound 0.75 used as support threshold)", "null": 0.75, "n": s4["n"]},
 "graph_effect": {"label": "DCP: share of permitted projects completed within four years", "estimate": 0.85, "lo": 0.80, "hi": 0.90, "scale": "proportion", "null": None},
 "sources": src("permits_nb_legacy", "jobs_nb_dobnow", "co_legacy_nb", "co_dobnow", "hdb_nb") + [GRAPH_SRC,
            {"kind": "other", "name": "NYC DCP, New Housing Permits in the First Half of 2022 (information brief), quoted by Atlantic Yards Report 13 Nov 2022", "url": "https://atlanticyardsreport.blogspot.com/2022/11/dcp-expiration-of-421-tax-break-drove.html"}],
 "prediction_scored": ("partial. The registered pooled statistic for cohorts 2010-2017 was 0.734 (95% CI 0.727-0.741, n=15,224), which falls between the support (>=0.75) and refute (<0.65) thresholds. "
                       "It is pulled down by cohorts 2010 (0.29) and 2011 (0.59) only because the legacy CO table (bs8b-p36w) begins in July 2012, so COs issued before then are missing; this was a named "
                       "alternative ('CO records missing from open data'). The Housing Database, named in the plan as the second measure, gives 0.83-0.88 for the same 2010-2011 cohorts and 0.76-0.88 for 2010-2021. "
                       f"Cohorts 2012-2021 on the DOB measure lie between 0.74 and 0.85; pooled 2013-2017 is {s4['p']:.3f} ({s4['lo']:.3f}-{s4['hi']:.3f}). The verdict 'confirmed' therefore rests on a cohort restriction "
                       "chosen after the data were seen, for a documented reason, and supported by the independent HDB measure. The registrant's own expectation (about 0.70) was too low. "
                       f"Median time from first NB permit to first CO was {FS['median_years_to_co_2013_2017']:.2f} years for 2013-2017 (Furman: about 1.9). Eventual completion (CO by Nov 2026) for 2012-2017 cohorts is 0.91-0.93, below Census's near-complete national figure."),
 "settle": ("Two questions remain. (1) COs before July 2012 for the 2010-2011 cohorts, from DOB's BIS CO archive, would settle the early cohorts directly. (2) The research figure is for projects or units, the city figure for jobs; "
            "a unit-weighted measure from the Housing Database shows the 2015 cohort completing only 0.67 of units within four years and the 2022 cohort 0.66 by July 2026, both years of 421-a deadline rushes. "
            "Whether DCP's 80-90 percent holds in deadline years needs the 2022 cohort followed to 2027."),
 "research_needed": [
  {"question": "What share of units permitted in the 2022 421-a rush (about 58,600 units in H1 2022) reach a CO by mid-2027 and by the June 2031 extended deadline?", "data": "DCP Housing Database (br6q-ssj3) quarterly releases; DOB NOW CO (pkdm-hqz6)", "design": "cohort follow-up by units, with job withdrawals and superseding jobs tracked", "priority": "high"},
  {"question": "Why do 7-9% of NB jobs permitted 2012-2017 still have no CO after nine years: abandoned, built without CO, refiled, or merged?", "data": "ipu4-2q9a, w9ak-ipjd, HDB job_status, aerial images", "design": "stratified sample with aerial and street-level checks", "priority": "medium"},
  {"question": "Is the Census national near-100% start and completion rate an appropriate benchmark for a city of multifamily buildings?", "data": "Census Survey of Construction microdata by structure size", "design": "compare completion rates by building size", "priority": "low"},
  RN_GRAPH],
 "figures": ["figures/construction/four_year_completion.png"],
 "notes": ("Cohort = distinct NB job numbers by the year of first NB-type permit (legacy) or first permit date (DOB NOW); outcome = earliest CO for the same job number in either CO table, temporary or final. "
           "Shares by cohort (DOB measure): " + ", ".join(f"{k}: {v}" for k, v in FS["hdb_share_4y_by_cohort"].items()) + " is the HDB measure; the DOB values are in data/derived/construction/cohort_completion.csv. " + GRAPH_NOTE),
}

a = SH["all_unexpired"]; b = SH["excluding_signed_off"]
o3 = {
 "id": "construction-sheds-outnumber-nb",
 "verdict": "confirmed",
 "city_effect": {"label": "ratio of jobs with an active sidewalk-shed permit to jobs with an active NB work permit, 1 Nov 2026", "estimate": round(a["ratio_shed_to_nb_jobs"], 2),
                 "lo": round(b["ratio_shed_to_nb_jobs"], 2), "hi": round(a["ratio_shed_to_nb_jobs"], 2), "scale": "ratio (interval spans the two definitions of active, not sampling error)", "null": 1, "n": a["shed_jobs"] + a["nb_jobs"]},
 "graph_effect": None,
 "sources": src("dobnow_permits_2022on", "legacy_shed_permits", "permits_nb_legacy", "jobs_nb_dobnow") + [GRAPH_SRC,
            {"kind": "other", "name": "NYC DOB, Get Sheds Down (July 2023)", "url": "https://www.nyc.gov/site/buildings/dob/get-sheds-down.page"}],
 "prediction_scored": (f"hit. On 1 November 2026, {a['shed_jobs']:,} jobs had an unexpired sidewalk-shed permit ({b['shed_jobs']:,} excluding signed-off permits; predicted 6,000-11,000) and {a['nb_jobs']:,} jobs had an unexpired NB work permit "
                       f"({b['nb_jobs']:,}; predicted 1,500-5,000). The ratio was {a['ratio_shed_to_nb_jobs']:.2f} ({b['ratio_shed_to_nb_jobs']:.2f}; predicted 1.5-6). {a['share_shed_bbls_on_nb']:.1%} of shed lots also had an active NB job "
                       f"({b['share_shed_bbls_on_nb']:.1%}; predicted 5-25%). Every criterion falls inside the registered range."),
 "settle": "Permits are a proxy for sheds that stand. A street survey or the DOB shed map on one day, and a count of sheds standing on expired permits, would settle the count. Whether people judge 'construction' by sheds is a perception question that needs a survey.",
 "research_needed": [
  {"question": "Do residents' estimates of construction activity track sheds, scaffolds and fences near them more than new buildings?", "data": "survey with geocoded respondents; rbx6-tga4 active permits", "design": "cross-sectional survey, exposure within 200 m", "priority": "high"},
  {"question": "Is the fall in active shed permits in 2026 (about 10,000 to 7,600) real removal or delayed renewal records?", "data": "rbx6-tga4 re-queried in early 2027", "design": "compare the same date counted at two release dates", "priority": "medium"},
  RN_GRAPH],
 "figures": ["figures/construction/active_sites.png"],
 "notes": (f"Active means issued on or before 1 Nov 2026 and expiring after it. Over 2022-2026 the monthly count of shed jobs ran 9,500-10,600 and NB jobs 3,100-4,200 (data/derived/construction/active_by_month.csv). "
           f"On the date, {SH['active_jobs_any_dobnow_permit_excl_signed_off']:,} distinct DOB NOW jobs held at least one active permit, of which {a['nb_jobs_dobnow']:,} were new buildings; the rest are alterations. "
           f"Construction fences ({SH['active_jobs_by_worktype_excl_signed_off'].get('Construction Fence', 0):,}), supported scaffolds ({SH['active_jobs_by_worktype_excl_signed_off'].get('Supported Scaffold', 0):,}) and suspended scaffolds "
           f"({SH['active_jobs_by_worktype_excl_signed_off'].get('Suspended Scaffold', 0):,}) add to what is visible from the street. A wider NB definition (first permit in the last six years and no CO) gives {SH['nb_jobs_permitted_6y_no_co']:,} jobs, which leaves the ratio near 2. " + GRAPH_NOTE),
}

o4 = {
 "id": "construction-aerial-triangulation",
 "verdict": "unsettled",
 "city_effect": {"label": "share of 48 sampled NB jobs (first permit 2018-2020) with visible change of the lot, NAIP 2017 to 2022", "estimate": round(AE["share_changed_all"], 3),
                 "lo": 0.55, "hi": 0.80, "scale": "proportion (Wilson 95% interval, n=48)", "null": 0, "n": AE["n"]},
 "graph_effect": None,
 "sources": src("tax_lots_aerial_sample", "naip", "permits_nb_legacy", "co_legacy_nb", "co_dobnow") + [GRAPH_SRC],
 "prediction_scored": (f"partial. Visible change in 33 of 48 jobs (0.69; predicted 0.65-0.90) and in 33 of 34 pairs that could be judged. Jobs changed on the aerial without a CO by the image date: 11 of 48 (0.23; predicted 0.10-0.35). "
                       f"No job with a CO was judged unchanged (0.00; predicted under 0.10), but 11 jobs with a CO were 'unclear', so the share 'CO but not visibly changed' is 0.23 when unclear counts as not changed, above the 0.15 support bound and below the 0.25 refute bound. "
                       f"Cohen's kappa between change and CO by image date was {AE['kappa_changed_vs_co_by_2022_unclear_as_unchanged']:.2f} (decided pairs only: {AE['kappa_changed_vs_co_by_2022_decided_only']:.2f}), below the predicted 0.2-0.7. "
                       "Kappa is low because nearly every readable lot changed, so the design has almost no unchanged cases to agree on; it cannot test agreement. The pixel-difference score did not separate changed from other pairs "
                       f"(AUC {AE['mad_auc_vs_visual']:.2f} against the visual judgement), because the 2017 New York flight is 1.0 m and blurred, so only the visual judgement is reported as a measure."),
 "settle": ("A sample that includes many jobs without a CO (stratify on CO status), and a later flight (2024 or 2025 at 0.3-0.6 m when it covers New York), would test agreement. "
            "The three sampled jobs with no CO in November 2026 that show a new building in 2022 (#17, #20, #35) need a street check: built and occupied without a CO, or unfinished."),
 "research_needed": [
  {"question": "Among NB jobs with no CO after five years, what share show a finished building on recent aerials?", "data": "NAIP 2022/2024, NYC orthoimagery (2018, 2022, 2024 at 0.15 m from NYC OTI), nb_jobs.csv.gz", "design": "stratified random sample of no-CO jobs, blind visual judgement by two raters", "priority": "high"},
  {"question": "Can building-footprint change (5zhs-2jue construction_year, last_edited_date) replace aerial judgement at scale?", "data": "NYC building footprints and their history", "design": "compare footprint edits with CO dates for all NB jobs", "priority": "medium"},
  RN_GRAPH],
 "figures": ["figures/construction/aerial_grid.png"],
 "notes": ("Method: 48 NB jobs drawn at random (seed 20261112) from jobs with a first NB permit in 2018-2020 (all in the legacy system, since DOB NOW NB filings begin in 2021). Lot outlines came from the DOF tax-lot polygons (i38t-6if2), "
           "because PLUTO's geom column is empty on Open Data; four lots without a polygon used a 24 m box at the permit's coordinates, and three of these fell on a street, so they were unreadable. NAIP New York flights of "
           f"Aug-Sep 2017 (1.0 m) and Jul-Oct 2022 (0.6 m) were resampled to 0.5 m. I judged each pair on sheets that showed only an index number, and committed the judgements (commit 7755daf) before joining CO status. "
           "Of the 5 sampled jobs with no CO in November 2026, three show a new building by 2022, one is unclear and one unchanged. Aerial imagery: USDA Farm Service Agency, National Agriculture Imagery Program (NAIP), 2017 and 2022. " + GRAPH_NOTE),
}

if __name__ == "__main__":
    for o in (o1, o2, o3, o4):
        print(claims.outcome(o))
