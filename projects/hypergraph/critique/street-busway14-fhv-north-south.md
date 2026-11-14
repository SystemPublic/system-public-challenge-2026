# Referee report: street-busway14-fhv-north-south

Verdict recorded: contested (refute_if met: the north upper bound, +6.49%, is below +7%). The referee rebuilt the deciding number from the TLC parquet files with separate code that does not import `analyses/street_space/`. The scratch code is in the session scratchpad folder `ref/` (`agg.py`, `fhv_ref.py`, `fhv_se.py`). The earlier referee's `ref/agg.py` was overwritten by mine; the yellow numbers in critique/street-busway14-crosstown-time.md do not depend on it. I read `docs/street_space.md` only after the re-estimates below were finished.

## Order of registration and data

The script `fhv.py` and the design file `fhv_design.json` were committed in 832efc5 at 13:18:18, in the same second as the registration 0f85b3a. The registration names 832efc5 as its script commit, so rule 9 is met. The design file holds FHV contrasts for February to September 2019 only, and no number from the outcome. The design aggregate `fhv_pairs_2019-02_2019-09.csv.gz` was written at 13:17:36. The FHV files for October 2019 to February 2020 were still downloading at registration (the October file finished at 13:17:29, the February file at 13:22:42). Their last-access times are 13:22:48 to 13:23:03, and the post-period aggregate was written at 13:23:12, after the registration. The outcome was decided at 13:24:50 and committed in c523b83 at 13:27:13. A last-access time records only the latest read, but the download times show that four of the five post-period files did not yet exist when the claim was registered.

The registrant had seen the yellow-taxi data to February 2020, including the yellow north swing of 2019-20, and says so. The hypothesis came from that split. That is the declared purpose of the held-out test and is acceptable.

## Re-estimate

Data: TLC High Volume FHV trip records `fhvhv_tripdata_2019-02.parquet` to `fhvhv_tripdata_2020-02.parquet` (13 files, `https://d37ci6vzurychx.cloudfront.net/trip-data/`, local copy `~/opt/nyc-concordance/fhvhv_1920/`; byte sizes match the outcome's `file_bytes`), and yellow-taxi records `yellow_tripdata_2016-07.parquet` to `yellow_tripdata_2020-02.parquet` (44 files, `~/opt/nyc-concordance/tlc_yellow_1720/`). I applied the registered trip filter, the shared-ride exclusion, the weekday 07-18 sample, the 20-trips-every-month pair rule, estimator E_fhv and its standard error.

| Version | North E, % (95% interval) | South E, % (95% interval) |
|---|---|---|
| Registrant (outcome) | +1.559 (-3.140 to +6.487) | +0.301 (-3.911 to +4.698) |
| Referee, registrant's holiday list | +1.559 (-3.141 to +6.487) | +0.301 (-3.911 to +4.698) |
| Referee, all federal holidays removed | +1.17 (-3.21 to +5.75) | +0.29 (-3.87 to +4.62) |
| Referee, AR(1) standard error | +1.56 (-3.68 to +7.08) | +0.30 (-4.98 to +5.88) |
| Referee, Midtown controls only | +0.66 (-4.35 to +5.93) | -0.59 (-5.68 to +4.78) |
| Referee, downtown controls only | +2.70 (-2.78 to +8.49) | +1.43 (-2.79 to +5.84) |

The number reproduces exactly. There are 4 north pairs in both fleets, 12 south pairs in FHV and 11 in yellow. Restricting the yellow input to months before October 2019 leaves the estimate unchanged, so the post-period yellow data do not enter E through the pair rule. Only the first two rows after the registrant's are the registered test; the others are sensitivity checks chosen by me.

## Is the borrowed seasonal baseline biased toward zero?

The outcome's notes say that if FHV trips swing less from summer to winter than taxi trips, the estimate is biased down. The pre-busway data do not support that direction. From February to September 2019 the FHV north contrast tracks the yellow one with a slope of 1.00 (south 0.94). From February 2019 to the summer of 2019 the north contrast fell by 7.8% for FHV and by 6.6% for yellow. If FHV's seasonal amplitude differs, it is if anything larger than yellow's, which would bias E upward. I find no evidence of a bias toward zero from this source.

A different feature of the data matters more. In the busway winter the two fleets diverged. The yellow north swing was 10.61% and the FHV swing 6.58%, a difference of 3.7 log points. Before the busway the monthly fleet difference had a standard deviation of 1.30 points, so a difference this large in a 5-month minus 3-month contrast is about 3.9 standard deviations. The two fleets agreed in the south pairs (difference 0.5 points, 1.0 standard deviation). Either the busway changed yellow and FHV trips differently in the north pairs, for example because app routing moved FHV drivers off 14th Street sooner, or the yellow north result was noise. The FHV estimate cannot tell these apart. The claim therefore fails to replicate the yellow split, but it does not show that the yellow split was wrong.

The baseline itself is uncertain. The three yellow north swings were 5.54%, 6.31% and 3.03%. Leaving one season out gives placebo values of +0.84%, +1.95% and -2.73%, a spread consistent with the registered standard error of 2.42%.

## Is the contested verdict fair?

Under rule 1 the verdict follows. refute_if is a condition on an interval bound, so rule 10 does not apply, and there is no resampling, so rule 9 does not apply.

The margin is small and depends on choices the registration fixed but which are not the only defensible ones. The upper bound sits 0.51 points below 7%, about 0.2 standard errors. The registered standard error treats the monthly values as independent. The yellow year-over-year changes for the north pairs have a lag-1 autocorrelation of 0.16; with an AR(1) correction the standard error rises from 2.42% to 2.70% and the upper bound becomes 7.08%, so refute_if would not be met. With downtown controls alone the upper bound is 8.49%, also not met. Removing all federal holidays moves the bound to 5.75%, met more firmly. Every version excludes neither zero nor +3%, the low end of the predicted range.

The refutation threshold was set at the predicted central value. A test whose refute region begins at the centre of the prediction refutes a prediction that it could not support at its low end. The registration's design note said so (D = 1.5 at +3%). A verdict of contested here means only that +7% was excluded under the registered standard error.

## Problems

1. The verdict turns on the independence assumption in the standard error. A plausible AR(1) correction turns the result into unsettled. This is the most important problem, and it is analogous to the seed and draw sensitivity that rule 9 addresses for resampled bounds.
2. The yellow and FHV north contrasts diverged by 3.9 pre-period standard deviations in the busway winter. The outcome reports both swings but does not say that the divergence is far outside the pre-period fleet difference. The registered alternative ("the FHV seasonal swing may differ from the yellow swing") cannot be checked for the winter-summer swing, since FHV has no earlier winter, but February 2019 shows no smaller FHV seasonality.
3. The south distance rise of +1.90% (+0.48 to +3.35) reproduces. It is unregistered and correctly labelled exploratory.
4. The registered holiday list omits Independence Day and Labor Day, which fall in the summer windows, and every holiday before October 2017, which affects the 2016 and 2017 yellow seasons. Using the full list lowers the north estimate by 0.4 points.

## Does docs/street_space.md claim more than the numbers support?

The "Drivers" paragraph reports the registered numbers and the 0.5-point margin correctly. Two sentences need revision. "The verdict rests on a borrowed seasonal baseline: if for-hire trips swing less from summer to winter than taxi trips, the estimate is too low" names a bias that the pre-period data do not show. The verdict rests more on the standard error, since an AR(1) correction or the downtown-only control leaves refute_if unmet. "The held-out data do not reproduce the referee's +7.4%" is correct, but the paragraph should add that the yellow and FHV north contrasts diverged in the busway winter by far more than before it, so the two fleets give different answers rather than one fleet confirming the other's null. The break-even figures that use this claim's numbers (90,000 and 21,000 occupant-trips) are checked in critique/street-busway14-m14-speed.md.

## Recommendation

Change the verdict to `unsettled` if the authors extend rule 9's principle to bound conditions that depend on an unregistered independence assumption; otherwise keep `contested` and state beside it that the AR(1) standard error and the downtown-only control both leave refute_if unmet. In the notes, replace the sentence about a downward bias with the pre-period evidence (slope 1.00, February-to-summer change 7.8% against 6.6%), and add the 3.9-standard-deviation fleet divergence in the north pairs. A second FHV winter after the busway (October 2020 onward) is confounded by the pandemic, so the most useful follow-up is route-level data, as the outcome's `settle` field says.
