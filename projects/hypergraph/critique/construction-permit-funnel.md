# Referee report: construction-permit-funnel

Verdict recorded: confirmed. Recommendation: change to unsettled under the registered rule. The substantive point, that permit rows overstate buildings, is not in doubt.

## (a) Does the verdict follow from the registered conditions?

It does not. The support rule was "rows per job >= 3 in every year 2010-2019 AND jobs reaching any CO fewer than jobs permitted, cohorts 2010-2017". The plan defines the measure as a SoQL aggregation "by year of issuance ... count of rows, count distinct job__", which is rows per distinct job within each calendar year. I recomputed it from `funnel_by_year.csv`: 2.55 (2010), 2.64 (2011), 2.90 (2012), then 3.00-3.28 for 2013-2019. The rule fails in three of ten years.

The outcome replaces this with "lifetime rows per job by cohort" (7.0-10.3), a quantity chosen after the per-year figure was seen. The refutation rule (rows per job below 2 in most years, or a CO ratio above 0.97) is also not met. The registered result is therefore unsettled.

## (b) Errors in code, units, joins or dates

The counts are correct as computed: 173,976 rows for 25,339 jobs in 2010-2019, 54% renewals. Two quantities in the scoring do not match the registration. First, the predicted "unique NB jobs with a permit, per year" (1,500-4,500) is scored against first-permit cohorts (1,309-2,491); the plan's per-year distinct job count is 4,649-6,413, which lies above the predicted range. Second, the CO comparison is scored on cohorts 2012-2019 rather than the registered 2010-2017. Both changes are minor, but each one moves the reported result after the data were seen.

The CO-versus-permit comparison is weak as a test. For 2010-2011 it is driven by the missing pre-July-2012 CO records, and for recent cohorts by right-censoring. "Fewer COs than permits" would hold even if every permitted job were eventually built.

## (c) Is the research comparison fair?

The graph has no finding on permits, and the claim is a statement about the record, not about research. There is no research-side quantity to compare.

## (d) Alternative not addressed

Superseded and refiled jobs (named in the registration) are not measured. Without the job-relationship table, the gap between permitted jobs and completed jobs mixes jobs that were abandoned with jobs that were built under another number.

## (e) Is the settle condition right?

Yes. The job-relationship table (HDB or BIS related jobs) would settle the remaining question. It should also state that the "jobs fewer than permitted" criterion needs complete CO coverage (pre-2012 BIS COs) to be informative.

## Recommendation

Change to unsettled. If the project wants the lifetime-rows measure, it should be registered as a new claim.
