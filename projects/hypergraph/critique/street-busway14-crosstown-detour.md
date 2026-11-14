# Referee report: street-busway14-crosstown-detour

Verdict recorded: contested. The referee rebuilt the deciding number from the TLC parquet files with separate code that does not import `analyses/street_space/`. The scratch code is outside the repository, in the session scratchpad folder `ref/` (`agg.py`, `est.py`, `extra.py`, `nn.py`). I read `docs/street_space.md` only after the re-estimate below was finished.

## Order of registration and data

The scripts and the pre-period design run were committed in 8b0917f at 12:05:49, and the registration in 18e3f4b at 12:05:53; the branch `origin/prereg/street-busway14-crosstown-detour` exists. The committed design files stop at September 2019. The post-period aggregate `pairs_2019-10_2020-02.csv.gz` was written at 12:06:20, after the registration, and the last-access times of the October 2019 to February 2020 parquet files (12:06:12 to 12:06:16) match that extraction. A last-access time cannot prove the files were not opened earlier, and I found nothing that shows they were. The outcome was decided at 12:07:59 and committed in 5fda0d1.

The summer-netted estimator was chosen after the registrant saw drift in the pre-busway contrast, using pre-period data only, and was fixed in `test.py` before registration. I consider that acceptable. For distance, though, the drift is not a nuisance that the summer removes cleanly; see problem 1.

## Re-estimate

Data: TLC yellow-taxi trip records `yellow_tripdata_2016-07.parquet` to `yellow_tripdata_2020-02.parquet` (44 monthly files, `https://d37ci6vzurychx.cloudfront.net/trip-data/`, local copy `~/opt/nyc-concordance/tlc_yellow_1720/`). Registered filter, zones, weekday 07-18 sample, pair rule and estimator, with my own aggregation and code. Outcome: log metered trip distance.

| Version | E, % (95% interval) | Placebo 2017 | Placebo 2018 |
|---|---|---|---|
| Registrant (outcome) | +0.182 (-0.785 to +1.159) | +0.282 | +0.052 |
| Referee, registrant's holiday list | +0.182 (-0.785 to +1.159) | +0.282 | +0.052 |
| Referee, all federal holidays removed | +0.174 (-0.782 to +1.139) | +0.290 | +0.012 |

The pair sets agree (31 treated, 55 control directed pairs) and the number reproduces exactly. The registrant's holiday list covers only October to February, so the weekday sample keeps summer federal holidays, against the registered text. The effect is 0.01 points.

## Does the verdict follow?

Yes. support_if (E >= +0.5% and lower bound above 0) fails: E is +0.18%, the lower bound -0.79%. refute_if (upper bound below +1.5%) is met: the upper bound is +1.16%. Rule 1 gives `contested`. The conditions are on interval bounds, so rule 10 does not apply, although the outcome invokes it; rule 9 does not apply because the deciding number has no resampling.

## Problems

1. The summer baseline was already raised. The monthly year-over-year change in the distance contrast was -0.66, -0.23 and +0.34% in April to June 2019, then +1.25, +0.80 and +0.58% in July to September 2019, then +0.77, +0.95, +1.05, +1.15 and +1.38% in October 2019 to February 2020. Every month from July 2019 on is positive and the post-busway months rise steadily. The registered estimator subtracts the high summer, which gives +0.18%. Against April to September 2019 as the baseline E would be about +0.7%; against the twelve months October 2018 to September 2019 about +0.5%. The summer rise coincides with the start of the M14 Select Bus Service (1 July 2019), and the busway itself was announced for 1 July and then for 12 August 2019 and was delayed both times by court orders. If drivers changed routes that summer, the netting removes part of the effect. The registration names the M14 SBS as an alternative present in both periods, which is true of its direct effect but not of route learning that began in July. All of these variants remain below the predicted +1.5%, so the refutation of the central prediction is robust to the baseline. The estimate of the detour itself is not, and lies between about +0.2% and +1.2% depending on the baseline and the estimator.

2. The standard error is somewhat too small. The year-over-year monthly changes are autocorrelated (lag-1 autocorrelation 0.36). With an AR(1) correction the standard error of E rises from 0.50% to 0.59% (log), and the interval becomes -0.98% to +1.35%. The empirical spread of the estimator over 20 rolling false starts before the busway is 0.57%. refute_if is still met under both, by about 0.15 to 0.2 points. A day bootstrap (days resampled within months, 200 draws) gives a sampling component of 0.49%, about equal to the registered standard error. So the registered value covers day-level sampling but leaves almost nothing for month-level drift; the deciding number does not ignore day clustering, but its margin is thin. The secondary plain DiD has a day-bootstrap interval (+0.75 to +1.74%) that ignores year-to-year drift, as the outcome notes.

3. The result depends on the control corridor. Against Midtown pairs alone E is -0.10% (-1.26 to +1.08); against downtown pairs alone it is +0.56% (-0.79 to +1.92), and refute_if would not be met. The registered pooling decides.

4. Exposure is diluted. Many treated pairs join zones both south of 14th Street, whose trips need not use the busway. In an exploratory split chosen after the data, the 4 directed pairs between East Chelsea and Stuy Town or Gramercy give +1.9% (+0.2 to +3.6), and the 11 pairs between the southern zones -0.6% (-1.7 to +0.6). This decides nothing under rule 4, but the pooled average is not the detour of a driver who used to take 14th Street.

5. Composition and concurrent changes. Weekday daytime yellow trips in the treated pairs fell from 128,579 (October 2018 to February 2019) to 102,600 (October 2019 to February 2020) as riders moved to for-hire vehicles, and mean distance rose from 1.257 to 1.289 miles. A shift in which trips remain with yellow cabs moves metered distance directly, without any detour; the registration names this alternative and nothing in the design separates it. The congestion surcharge of 2 February 2019 lies between the compared years in both the summer months and four of five winter months, so the netting removes most of any differential effect.

## Does docs/street_space.md claim more than the numbers support?

For this claim the note mostly stays within the numbers. It reports the registered estimate, says that refute_if was met by less than one standard error, and describes the summer rise and the drift. Two points go further than the numbers.

- It says the test "estimates the detour ... the added distance", and that "the upper 95% bound of the detour is 1.2% of a crosstown trip". The 1.2% is the upper bound for the zone-pair average under the registered baseline and pooled controls. With the AR(1) standard error it is 1.35%, with downtown controls 1.9%, and the per-driver detour of trips that used 14th Street is not estimated at all.
- It calls the unadjusted series "consistent with a detour of 0.5% to 1%" and then says this "cannot be separated from drift". That sentence is accurate. The note should add that the same series is also consistent with a change in the mix of yellow-taxi trips, which fell by 20% in these pairs over the year.

## Recommendation

Keep `contested`: the number reproduces, the verdict follows from rule 1, and the refutation of +1.5% survives the AR(1) standard error, the full holiday list and other baselines. Add to the notes that the downtown-only control leaves refute_if unmet, that the summer-2019 rise makes the registered estimate a lower value among plausible baselines, and that the registered sample keeps summer federal holidays. Describe the 1.2% upper bound as a bound on the corridor-area average, not on the detour of displaced drivers.
