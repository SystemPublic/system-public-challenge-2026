# Referee report: transfer-chicago-hot-end

Verdict recorded: unsettled. Recommendation: keep the verdict.

Scratch code: `referee-transfer-chicago-hot-end/ref.py` in the session scratchpad. It imports `analyses/round2/hot_end/model.py` and reads `data/derived/round2/hot_end/chicago_daily.csv` and `data/derived/graph/transfer_chicago/chicago_heat_daily.csv`.

## (a) Does the verdict follow from the registered conditions?

Yes. Part (a) required the upper limit of the Divvy ratio for 33 against 27 C to be below 1.06 and the lower limit of the full-window shootings ratio to be above 1.00. The values are 0.949 (0.896 to 1.005) and 1.058 (1.014 to 1.105), so part (a) is met. Part (b) required the proxy to remove at least 0.20 of the 15 to 21 C rise with a lower limit above 0.10. It removes 0.104 (0.041 to 0.247), so part (b) is not met. Neither refutation condition holds. The registration says that (a) without (b) is unsettled.

Nothing was decided by a measure chosen after the data were seen. The casual-rider result (0.298 of the mild-day rise removed) would have passed part (b), and it is correctly kept as secondary, as registered.

The registration was committed at 23:46:43 and 23:46:44 on 12 November 2026 (c9f6e41 and 4e5e256), and `prereg/transfer-chicago-hot-end` exists on the remote at 4e5e256. The cache holds 82 Divvy files. The earliest are the catalog metadata and a yearly query for 2013, both at 23:57:45, eleven minutes after the registration; the yearly queries were replaced by the 79 monthly queries cited in the outcome, fetched from 00:00:57 to 00:44:23 on 13 November. The outcome was decided at 00:46:33. The power simulation and the New York recomputation were written at 23:43 and 23:46, before the registration. The Chicago shootings and weather were fetched at 22:33 for an earlier claim, and the registration states that the unadjusted shootings means by temperature bin had been read. The shootings half of part (a) was therefore not blind, as the registration says. The push time cannot be checked from the repository.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I found no error that changes a number. My refit reproduces every deciding value (shares with a different bootstrap seed: 0.104, 0.043 to 0.263). One point of method is worth recording. The outcome's intervals use HC0 errors, and daily bicycle trips are strongly correlated from day to day.

| Variant | Shootings 33 vs 27 C, 2010 to 2026 | Divvy 33 vs 27 C |
|---|---|---|
| Registered (HC0) | 1.058 (1.014 to 1.105) | 0.949 (0.896 to 1.005) |
| HAC errors, 7 lags | 1.058 (1.008 to 1.110) | 0.949 (0.876 to 1.027) |
| Upper knot at 26 C | 1.065 (1.025 to 1.105) | 0.979 (0.932 to 1.029) |
| Upper knot at 28 C | 1.064 (1.023 to 1.106) | 0.964 (0.913 to 1.018) |
| Extra knot at 30 C | 1.069 (1.023 to 1.116) | 0.958 (0.905 to 1.013) |
| Without 2020 and 2021 (HAC) | 1.069 (1.015 to 1.126) | |
| 2010 to 2019; 2020 to 2026 | 1.065 (1.009 to 1.124); 1.061 (0.990 to 1.137) | |
| Days outside the Divvy window | 1.056 (0.999 to 1.117) | |
| Days with fewer than 200 trips removed | | 0.951 (0.898 to 1.006) |

Part (a) passes in every variant: the Divvy upper limit never reaches 1.06 and the shootings lower limit stays above 1.00, though by 0.008 with HAC errors. The shootings condition is met only on the full window; on the Divvy window the ratio is 1.053 (0.987 to 1.123), which the outcome reports. The window has 73 days at or above 33 C.

Ten days in the window have fewer than 200 trips, including two with none during the January 2014 cold. On the log scale these are extreme values. Removing them gives a share of 0.116 (0.046 to 0.283). Restricting to days of 5 C or warmer gives 0.078 (0.004 to 0.217), and April to October gives 0.015 (-0.110 to 0.209). Part (b) fails in every variant.

The outcome's stance of 0.859 (z = 2.58) is computed from the shootings ratio alone, the half of part (a) that was not blind. It says nothing about part (b), which is the part that failed. A reader of the strip would take 0.859 as agreement of an unsettled claim.

## (c) Is the comparison with New York fair?

For part (a), mostly. The model, basis and calendar terms are the same in both cities, and the New York values were recomputed with the registered basis before registration. The windows differ: shootings are fitted on 2010 to 2026 and Divvy on mid-2013 to 2019. The proxies are not the same kind of measure. Part (b) was predicted from New York street-noise complaints (0.415 of the mild-day rise) and tested with bicycle trips, and New York's own bicycle counts removed 0.021. The registration says this and names part (b) as the part most likely to fail. The failure of (b) therefore agrees with New York's bicycle result and says little about New York's noise result. Reeping and Hemenway is cited for a linear slope and is not compared with any number here. The claim has no graph effect; the registration reports that Kim 2022 was read again, and I confirmed the abstract (odds ratio 0.95 rural, 0.98 urban per 1 C).

## (d) Alternative explanation not addressed

The registration names mode switching, system growth, shared causes, proxy error and lake breeze. It does not address composition. Subscribers make three quarters of trips and are commuters, and their trips fall on hot days (0.958) and remove 0.038 of the mild-day rise. Casual trips do not fall (0.992, 0.924 to 1.066) and remove 0.298. The all-trips proxy that decides the claim is therefore mostly a commuting measure, and the flattening in part (a) may be commuters avoiding heat, not fewer people on the street. The casual series, which is closer to leisure, has an upper limit of 1.066 and would not have met the 1.06 condition. The support for part (a) depends on the commuter majority.

## (e) Could the test have failed?

Part (b) could fail and did. The registered prior was 0.15, and the simulation gave part (b) a probability of 0.8 of passing when a New York-sized chain was present and 0 when it was absent.

For the shootings ratio, the log estimate is 0.057 with standard error 0.022 (0.025 with HAC errors). Against the New York value of 1.122 (standard error 0.035) z is -1.42, and against no rise z is 2.58 (2.30 with HAC errors). D is 4.6 with the registered errors and 3.4 with HAC errors, so by the standard of rule 8 the shootings half barely separates a New York-sized rise from none. For the Divvy ratio, z is 0.56 against the New York bicycle value (0.931) and -1.79 against no change (-1.29 with HAC errors), so a fall is not shown; what is shown is that trips stop rising, since the ratio is about 7 standard errors below the 1.32 rise from 21 to 27 C. For the mild-day share, z is about -3.5 against the New York noise value (0.415), 1.5 against the New York bicycle value (0.021) and about 2 against zero.

Recommendation: keep. Part (a) is met and part (b) is not under the registered rule, and both results stand in every variant I ran.
