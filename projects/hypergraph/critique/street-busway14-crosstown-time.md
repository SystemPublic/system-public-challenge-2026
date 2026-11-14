# Referee report: street-busway14-crosstown-time

Verdict recorded: contested (a conflict-kind claim whose bet lost). The referee rebuilt the deciding number from the TLC parquet files with separate code that does not import `analyses/street_space/`. The scratch code is outside the repository, in the session scratchpad folder `ref/` (`agg.py`, `est.py`, `extra.py`, `nn.py`). I read `docs/street_space.md` only after the re-estimate below was finished.

## Order of registration and data

The scripts, the pre-period design run and `series_pre.csv` were committed in 8b0917f at 12:05:49. The registration was committed in d865ceb at 12:05:53, and the branch `origin/prereg/street-busway14-crosstown-time` points at d865ceb. The design files committed in 8b0917f stop at September 2019 (`series_pre.csv` ends at 2019-09-01). The post-period aggregate `~/opt/nyc-concordance/street_space/pairs_2019-10_2020-02.csv.gz` was written at 12:06:20, after the registration. The last-access times of `yellow_tripdata_2019-10.parquet` to `yellow_tripdata_2020-02.parquet` were 12:06:12 to 12:06:16 when I first checked them, which matches that extraction. A last-access time records only the latest read, so it cannot show that the files were never opened earlier. I found nothing that shows they were. The outcome was decided at 12:07:59 and committed in 5fda0d1 at 12:10:04.

The summer-netted estimator was chosen after the registrant saw drift in pre-busway data (the plain year-over-year DiD moved by +3.4% between the winters of 2017-18 and 2018-19). That choice used no post-period data, the registration states the reason, and the estimator, its standard error and its decision rule were fixed in `test.py` before registration. I consider that acceptable. The design run kept only one netted estimator; I cannot tell whether other baselines were tried on pre-period data and dropped.

## Re-estimate

Data: TLC yellow-taxi trip records `yellow_tripdata_2016-07.parquet` to `yellow_tripdata_2020-02.parquet` (44 monthly files, `https://d37ci6vzurychx.cloudfront.net/trip-data/`, local copy `~/opt/nyc-concordance/tlc_yellow_1720/`). I applied the registered trip filter, zone groups, weekday 07-18 sample, 20-trips-every-month pair rule and estimator E, with my own aggregation and code.

| Version | E, % (95% interval) | Placebo 2017 | Placebo 2018 |
|---|---|---|---|
| Registrant (outcome) | +0.931 (-2.350 to +4.323) | -0.723 | +1.254 |
| Referee, registrant's holiday list | +0.931 (-2.350 to +4.323) | -0.723 | +1.254 |
| Referee, all federal holidays removed | +0.868 (-2.402 to +4.248) | -0.660 | +1.043 |

The pair sets agree: 31 treated and 55 control directed pairs. The number reproduces exactly.

The registrant's holiday list (`estimate.py`, `HOLIDAYS`) covers only October to February of 2017-18 to 2019-20. The weekday sample therefore keeps Independence Day, Labor Day, Memorial Day and every holiday before October 2017, although the registration says "weekdays except federal holidays". Removing them moves E by -0.06 points and does not change the verdict.

## Does the verdict follow?

Yes. support_if requires E >= +2.0% and a lower bound above 0; E is +0.93% and the lower bound -2.35%, so it fails. refute_if requires the upper bound below +5.0%; the upper bound is +4.32%, so it is met. Under rule 1 a met refute_if gives `contested`, with the roles as registered for a conflict claim. The conditions are on interval bounds, so rule 10 does not apply. The outcome's phrase "met within sampling error (rule 10)" applies rule 10 language to a bound condition. That is harmless, but rule 10 is about point-estimate conditions. There is no resampling in the deciding number, so rule 9 does not apply.

## Problems

1. Exposure is diluted by the zone pairs. Many treated pairs join zones that are both south of 14th Street (West Village, Greenwich Village North, Meatpacking against East Village, Alphabet City); those trips can cross on 8th Street, St Marks Place or Houston Street without touching the busway. In an exploratory split, not registered and chosen by me after seeing the data, the 4 directed pairs between East Chelsea and Stuy Town or Gramercy (both north of 14th Street) give +7.4% (+2.8 to +12.1), and the 11 pairs between the southern zones give -1.5% (-5.5 to +2.7). The north-north pairs had placebo values of +0.7% (2017) and -3.1% (2018). Under rule 4 this decides nothing, and four pairs with a post-hoc choice is weak evidence. It does show that the registered pooled average can sit near zero while trips that most plausibly used 14th Street lengthened by several percent. This is the most important limit on what the verdict means: it says the corridor-area average did not rise by 5%. It does not say that displaced drivers lost little time.

2. The result depends on the control corridor. With Midtown pairs alone E is -0.28% (-4.18 to +3.78). With downtown pairs alone it is +2.49% (-1.36 to +6.48), and refute_if would not be met. The registered pooling decides, but the downtown pairs (mean 10.9 minutes, 1.12 miles in October 2018 to February 2019) are closer in length to the treated pairs (11.5 minutes, 1.26 miles) than the Midtown pairs (15.1 minutes, 1.22 miles), which run through slower traffic.

3. The standard error is somewhat too small. The year-over-year monthly changes d_m are autocorrelated (lag-1 autocorrelation 0.20 from July 2017 to September 2019). With an AR(1) correction the standard error of E rises from 1.69% to 1.88% (log), and the interval becomes -2.7% to +4.7%. refute_if is still met, by 0.3 points. The empirical spread of the same estimator over 20 rolling false starts in the pre-period is 1.67%, close to the registered value. The registered standard error does not ignore day clustering: it is built from monthly values, and a day bootstrap of E (days resampled within months, 200 draws) gives a sampling component of only 1.09%. The secondary plain DiD bootstrap does understate uncertainty, because it ignores year-to-year drift. In the design run five of six false starts of that estimator had 95% intervals that excluded zero.

4. The choice of baseline matters. The monthly year-over-year changes after the busway were +4.3, +2.9, -2.8, -1.3 and -1.2% (October 2019 to February 2020). Netted against July to September 2019 (mean -0.5%) E is +0.9%. Netted against October 2018 to September 2019 (mean +1.7%) it would be about -1.3%. Every such variant stays below the 5% prediction, so the verdict is not sensitive to this choice, but the point estimate is.

5. Concurrent changes. The congestion surcharge of 2 February 2019 falls between the two years compared in both the summer months and four of the five winter months, so the netting removes most of any differential effect; only February 2020 against February 2019 differs. The M14 Select Bus Service (1 July 2019) is in both netted periods. The shift from yellow taxis to for-hire vehicles is large: weekday daytime yellow trips in the treated pairs fell from 128,579 (October 2018 to February 2019) to 102,600 (October 2019 to February 2020), and in the controls from 317,852 to 271,040. The treated share of trips fell by 1.3 points in winter and 1.1 points in summer, so the netting also absorbs most of the shift in share. A change in which riders still take yellow cabs could still move trip length within a pair, and the claim cannot test it. I did not check concurrent street changes in the Midtown or downtown control corridors.

## Does docs/street_space.md claim more than the numbers support?

In part. The tables and the Results section report the registered numbers correctly, state the control-group sensitivity, and say that both refutation conditions were met by less than one standard error. Three passages go further.

- "What this implies for the next closure" says the cost to drivers was "under half a minute on a typical crosstown taxi trip, with the most likely value a few seconds". The estimate is a zone-pair average that includes trips that never used 14th Street, as the Limits section says. It is not the cost to a displaced driver. The point estimate also ranges from about -1.3% to +2.5% across reasonable baselines and controls, so "a few seconds" is not a stable most-likely value.
- The "Conflict" section says the trips were lengthened "by no more than about 30 seconds (upper 95% bound)". That bound holds under the registered standard error and pooled control. With the AR(1) standard error it is about 33 seconds, and with downtown controls alone about 45 seconds.
- The note does not mention the 20% fall in yellow-taxi trips in these pairs between the two winters, or the 2019 congestion surcharge, which `common.py` names.

## Recommendation

Keep `contested`. The number reproduces, the verdict follows from the registered conditions under rule 1, and it survives the AR(1) standard error and the full holiday list. Add to the notes that the downtown-only control would leave refute_if unmet, that the registered sample keeps summer federal holidays, and that the exploratory north-north pairs show +7.4% (+2.8 to +12.1). Revise the "next closure" paragraph so that it describes a corridor-area average, not a per-driver cost. A registered follow-up restricted to pairs on the same side of 14th Street would test the exposed trips directly.
