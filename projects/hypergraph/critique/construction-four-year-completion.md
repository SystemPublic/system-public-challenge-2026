# Referee report: construction-four-year-completion

Verdict recorded: confirmed. Recommendation: change to unsettled, and register the restricted cohorts as a new claim that supersedes this one.

## (a) Does the verdict follow from the registered conditions?

It does not. The registration fixed the test statistic as the pooled four-year share for cohorts 2010-2017, with support at 0.75-0.95 and refutation below 0.65 with an interval excluding 0.75. I re-read `funnel_summary.json`: the registered statistic is 0.734 (0.727-0.741, n = 15,224). That value is in neither region, so the registered rule gives unsettled.

The outcome reaches "confirmed" by switching to cohorts 2013-2017 (0.807) after seeing the cohort table. The outcome says so openly, and the reason is real: the legacy CO table (bs8b-p36w) starts on 12 July 2012, which I confirmed in the parquet (earliest c_o_issue_date 2012-07-12). The 2010 and 2011 cohorts are therefore truncated (0.29 and 0.59). But a documented reason does not turn a post hoc restriction into a registered test. The register's own rule (concord/claims.py) is that a changed plan is a new registration with `supersedes`.

## (b) Errors in code, units, joins or dates

The join of jobs to COs is sound. DOB NOW CO records carry BIS job numbers for BIS jobs and DOB NOW numbers without suffix for DOB NOW jobs, and `funnel.py` matches both. The four-year window (1,461 days) and the Wilson intervals are correct.

The outcome notes contain a labelling error. They say "Shares by cohort (DOB measure): 2010: 0.835, 2011: 0.825, 2012: 0.841 ...". Those are the Housing Database shares (`hdb_share_4y_by_cohort`). The DOB measure in `cohort_completion.csv` is 0.288, 0.585, 0.825, 0.849, 0.847, 0.770, 0.792, 0.787 for 2010-2017. A reader of the notes will take the HDB numbers as DOB numbers.

The Housing Database is described as "independent" support. It is not independent of the DOB record: HDB completion dates are derived from DOB certificates of occupancy, with access to pre-2012 BIS COs. HDB shows that the truncation explanation is plausible; it does not supply a second measurement of completion.

## (c) Is the research comparison fair?

Only partly. The DCP statement concerns permitted projects, and DCP's own pipeline work is residential and often unit-weighted. The city measure counts all NB jobs, including non-residential jobs, each with weight one. The outcome's own unit-weighted HDB figure for the 2015 cohort is 0.67, below DCP's range. The comparison should be restricted to residential jobs (or reported both ways) before it is called a confirmation.

## (d) Alternative not addressed

The 2015 cohort is the 421-a deadline rush: many jobs were permitted ahead of the January 2016 lapse, and their four-year share (0.77) is lower. Whether the pooled figure rests on policy timing rather than a stable completion rate is not examined. Superseded or refiled job numbers (a named alternative) would bias the share downward and are not measured.

## (e) Is the settle condition right?

Yes in part. Pre-2012 COs from the BIS archive would settle the early cohorts directly. A residential, unit-weighted comparison with DCP's definition should be added to the settle condition, because that is the quantity DCP reports.

## Recommendation

Change the verdict to unsettled under the registered rule. Register "four-year completion, cohorts 2012/2013-2017, residential and all-job versions" as a new claim that supersedes this one, and score it there. Correct the notes so that HDB and DOB shares are labelled separately.
