# Referee report: afford-gentrification-prevalence

Verdict recorded: confirmed. Recommendation: keep the verdict, record that the registration was not blind, set the stance to null and change the notes as listed at the end.

Referee code: `analyses/critique/referee_afford.py`. It reads `data/derived/affordability/furman_panel.csv`, rebuilds the area table with its own code without importing `analyses/affordability/gentrification_test.py`, and prints its results. I read the registration, the outcome, the scripts in `analyses/affordability/`, the derived data and the verdict rules. I did not read `docs/affordability.md` or any other write-up of this claim. I did not have the Furman workbook's documentation, so I could not check how the publisher maps census areas to sub-borough areas.

## (a) Does the verdict follow from the registered conditions?

Yes. The registered reading "real but a minority" needs k from 4 to 11, k2 of at least 3 and a lower limit of the Spearman correlation above 0. My code gives k = 8 of 22 (Wilson 0.20 to 0.57), k2 = 8 and a correlation of 0.68 (0.50 to 0.80). The eight areas are the ones the outcome lists. The city's rent growth is 41.1% and its college share rose 14.7 points. The test uses no resampling, so rule 9 raises no seed question. The script in the working tree is identical to the one in the registration commit f4d9839.

The order of events is as follows. The workbook was fetched at 07:37:28 on 13 November 2026. The panel was built at 07:42:50. The test script was last saved at 07:43:44. The registration file was written at 07:47:06 and committed at 07:47:16 on the branch `prereg/afford-gentrification-prevalence`, which holds that one commit for this claim. The results file was written at 07:47:24, eight seconds after the commit. Git records the commit time and not the push time, so the repository cannot show that the push preceded the run. The outcome is stamped 07:51:50.

The registration was not blind, and it says so. The `--simulate` mode of the script multiplies the real later-year values by lognormal noise, and the registrant read its output before registering. I rebuilt that run with seed 0 and obtained what the registration reports: k = 6, k2 = 7, a correlation of 0.38 and the same six areas. The noise is large but it is not uninformative. Over 400 other seeds the simulated k has a mean of 6.9 with a 95% range of 2 to 15, the simulated correlation has a mean of 0.33 (0.08 to 0.53), and 5.4 of the areas in a simulated set are, on average, among the true eight. A registrant who had seen k = 6 and a correlation of 0.38 (its interval by the registered formula is 0.12 to 0.59) knew that the true values were probably inside the supporting window.

The registration states that the thresholds and the script were written before the simulated run and were not changed after it. The repository cannot confirm this. There is no commit of the script or of the thresholds before 07:47:16. The simulated run must have happened between 07:42:50, when the panel was built, and 07:47:06. The script was last saved at 07:43:44, inside that interval, so its file time is compatible with either order. The file that the simulated run writes, `gentrification_results_SIMULATED.json`, is no longer in `data/derived/affordability/`, so its time cannot be read. The registration script `register.py` was last saved at 07:47:06, after the leak, since it describes the leak.

I judge that the thresholds were probably not tuned to the leak, for three reasons. The window of 4 to 11 is wide and follows from the stated Wilson reasoning (12 or more puts the lower limit above one third; 1 or fewer puts the upper limit at 0.22). A window fitted to a leaked value of 6 would not need to extend to 11. The script still contains the faulty simulation code and a docstring that describes it wrongly, so the last save did not follow a repair of the fault. The six areas named in the prediction differ from the six leaked areas: Coney Island and the Lower East Side were dropped, Bedford Stuyvesant and Central Harlem were added, and all six are in the true set, which is more consistent with prior knowledge of the city than with copying. These reasons make tuning unlikely. They do not show the order of events.

The consequence is for the prediction score and for the claim that the test could fail, not for the verdict. Rule 1 gives confirmed. The outcome's `prediction_scored` says "hit" and adds that the prediction followed a noisy view of the outcome. I would score the prediction as not blind and not as a hit, since the predicted range of 6 to 10 was written after a leaked value of 6.

One error in the registration is already recorded in the outcome. The registration counts eight Bronx areas among the low-start group, and there are seven.

## (b) Errors in code, units, joins, dates, geography or uncertainty

Every number I checked reproduced: k, k2, the correlation and its interval, the Wilson interval, the secondary counts (6 of the other 33, 8 with the income definition, 9 on rent alone, 12 on college share alone) and the rank correlation of 2000 rent with 2022-2024 rent (0.71). I found no error in the code. The 2020 values are absent for the college share and present for rent, and the registered end period does not use 2020.

The count of 8 does not depend on the registered thresholds. I varied the rent rule (above the city, above the median area, the city plus 5 or 10 points, the city minus 5 points, a dollar rise above the city's, a rise of five or more rank places) and the college rule (above the city, above the median area, the city plus or minus 3 points, relative growth above the city's). Over the 35 combinations k ranges from 5 to 12, and 34 of the 35 fall between 5 and 11. The exception is 12, with rent growth above the median area and relative growth of the college share. With the low-start group set at 11, 14, 16, 18, 20, 24, 27 or 28 areas the share is between 29% and 43%. With other end periods k is 9 (2015-2017), 9 (2017-2019), 8 (2018, 2019 and 2021), 7 (2019, 2021 and 2022), and 10, 9 and 6 for the single years 2022, 2023 and 2024. The correlation is between 0.49 and 0.68 in every end period, and its lower limit is at least 0.25.

The membership is less stable than the count. Five Brooklyn areas (Williamsburg/Greenpoint, Bedford Stuyvesant, Bushwick, North Crown Heights/Prospect Heights and Brooklyn Heights/Fort Greene) are in the set under every end period I tried, and they pass the rent condition by 42 to 96 points. The three upper Manhattan areas pass it by 8.7, 7.9 and 0.8 points. Washington Heights/Inwood, at 0.8 points, leaves the set in five of the ten other end periods. East Harlem misses by 2.0 points and South Crown Heights by 6.4. A rule based on rank (five or more places) gives 6. The supported statement is that five areas changed by a wide margin and that two to five more are near the threshold.

The 2022 boundary change affects this claim less than it affects population counts. The population of 28 of 55 areas changes by more than 8% between 2021 and 2022, against 7 to 16 in other years. For rent relative to the city, the standard deviation of the one-year change is 0.070 in 2021-2022 against 0.056 and 0.058 in two earlier years. For the college share it is 3.1 points against 2.7 and 3.1. The end periods before the break give k of 8 or 9. The outcome reports the 2017-2019 check and labels it exploratory, which is correct.

Regression to the mean in rent is not visible. Across the 55 areas the rank correlation of 2000 rent with rent growth is -0.14, and within the 22 it is -0.13. With the baseline moved to 2005-2007, 10 of the 22 exceed the city's rent growth, against 9 from 2000. With both the selection and the baseline taken from 2005-2007, so that no 2000 value is used, k is 7. With a baseline of 2008-2010 it is 6. Among the 22, the change in rent rank from 2000 to 2005-2007 does not predict a reversal afterwards (rank correlation 0.11). Nine of the 22 rose in rank and ten fell. A group selected for a low rank can only rise or stay, so the falls are evidence against a large selection artefact. The k and k2 sets differ in two areas: East Harlem enters under k2 and Morningside Heights/Hamilton Heights leaves.

## (c) Is the comparison with the research fair?

The comparison is loose, and the registration says the graph supplies no effect size. The outcome's `graph_effect` of 0.24 (0.18 to 0.33) is the range of three shares from studies with different units (block groups in Durham, urban tracts nationally, 42 New York neighbourhoods), different periods and one-condition or other definitions. The range is not an interval. The city figure of 36% is on a two-condition definition at the scale of 100,000 to 250,000 residents. Agreement between 36% and a range of 18% to 33% shows little, because the registered window of 18% to 50% would have accepted almost any of those studies' values.

The stance of 0.957 (z = 3.82) should be null. Rule 6 says the stance is null when the city effect has no null value that expresses the research direction, and gives a raw proportion with a null of 0 as its example. The city effect here is a raw proportion with a null of 0.

## (d) Which alternative explanation is not addressed?

1. The definition does not separate the low-rent group from the rest. Among the other 33 areas, 6 meet both conditions (18%), against 8 of 22 (36%). A Fisher exact test of the two shares gives p = 0.21. The registration listed the count among the other 33 as a secondary result, and the outcome reports it without the comparison. The data support "about a third of low-rent areas had rent and college share rise faster than the city's". They do not show that this happened more often in low-rent areas than elsewhere.

2. The city benchmark makes a minority likely in any group. The city's rent growth (41.1%) is above the median area's (35.6%), and its college change (14.7 points) is above the median area's (12.3). Only 18 of the 55 areas exceed the city on rent and 21 on college share. The "common" reading needed 12 of the 22 to pass both conditions, which would require two thirds of all the areas that pass the rent condition to be low-start areas. Nine of the 18 are. The registered binomial table treats the probability of passing as free between 0.15 and 0.80, and the benchmark restricts it more than that.

3. The count condition alone would have been met by chance. With 9 of 22 passing the rent condition and 12 of 22 passing the college condition, independence predicts 4.9 areas passing both, which is inside the window. The registration recognises this and adds the correlation condition. The correlation is strong and stable (0.68 across the 55 areas, 0.77 within the 22, 0.62 within the other 33), so this part of the reading is well supported.

4. Change within areas. The registration names it, and the outcome's `settle` and `research_needed` entries propose tract data on fixed boundaries. Nothing in the present data addresses it.

5. Regulated and public housing. The registration names it for the Lower East Side and Harlem. The Lower East Side passes the college condition and misses the rent condition by 6.5 points, and East Harlem misses by 2.0 points, so the direction of this bias would raise k by one or two. It would not change the reading.

## (e) Could the test have failed?

It could have failed in principle, in the direction of "myth" through the correlation and in the direction of "common" through the count. Two things reduce the risk the registration states. The benchmark made "common" hard to reach, as point 2 above describes. The leak told the registrant that the count and the correlation were probably inside the supporting window: in my 400 noise draws around the true values, the simulated k is between 4 and 11 in 79% of draws, at most 1 in 2% and at least 12 in 9%. The registration gives a prior of 0.6 and says the leak raises it. I would put the probability of the supporting reading, given what had been seen, near 0.8.

The claim is not an endpoint test against a composed prediction, so z against the prediction does not apply. For the correlation, z against no association is 5.8 by the registered Fisher formula.

## Requested changes to the outcome

1. Keep the verdict.
2. Add a `verdict_note` saying that the registration followed a noisy view of the deciding numbers, that no commit shows the thresholds existed before that view, and that the simulated results file is not in the repository.
3. Score the prediction as not blind in place of "hit".
4. Set the stance to null under rule 6.
5. Report the comparison with the other 33 areas (18% against 36%, p = 0.21) and say that the definition does not distinguish low-rent areas from the rest at this sample size.
6. Say that five Brooklyn areas are in the set under every variant, that the three upper Manhattan areas are near the rent threshold, and that Washington Heights/Inwood passes by 0.8 points.
7. Describe the `graph_effect` range as a range of three studies' shares and not as an interval.

Recommendation: keep.
