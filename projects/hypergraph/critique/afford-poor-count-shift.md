# Referee report: afford-poor-count-shift

Verdict recorded: confirmed. Recommendation: keep the verdict with its note, and change the notes as listed at the end. The registered condition is met by a margin smaller than the effect of removing one area. The direction is supported by end periods before the 2022 boundary change, which were not registered.

Referee code: `analyses/critique/referee_afford.py`. It reads `data/derived/affordability/furman_panel.csv`, rebuilds the area table with its own code without importing `analyses/affordability/gentrification_test.py`, and prints its results. I read the registration, the outcome, the scripts in `analyses/affordability/`, the derived data and the verdict rules. I did not read `docs/affordability.md` or any other write-up of this claim.

## (a) Does the verdict follow from the registered conditions?

Yes, by the letter. The support condition is an upper limit of the Welch interval below 0. My code gives a difference in mean log change of -0.283 (-0.544 to -0.021), with a standard error of 0.121 and 13.4 degrees of freedom, for 8 gentrified areas against 14 others. The two-sided p-value is 0.036. Rule 1 gives confirmed. The condition is written on an interval bound and the interval is computed without resampling, so rules 9 and 10 do not apply. The script in the working tree is identical to the one in commit f4d9839, and the groups are the ones the first claim's registered definition produces.

The order of events is the same as for afford-gentrification-prevalence. The registration file was written at 07:47:06 on 13 November 2026 and committed at 07:47:18 on the branch `prereg/afford-poor-count-shift`. The results file was written at 07:47:24, six seconds later. Git records the commit time and not the push time. The outcome is stamped 07:51:50.

The registration followed the faulty `--simulate` run, which revealed a noisy version of the group membership. Four of the six areas in the leaked set are among the true eight. The registration says that no poverty or population value was read, because the output was cut at 70 lines. I rebuilt the simulated run. It prints 116 lines, and the block for this claim starts at line 70, which is the line `"claim2": {`. A cut at 70 lines therefore ends on the header of this claim's block and shows none of its numbers, so the statement is consistent with the output to the line. The repository cannot confirm that the output was cut. The simulated run also wrote the whole block to `gentrification_results_SIMULATED.json`, and that file is no longer in `data/derived/affordability/`. The simulated contrast was -0.520 (-1.053 to +0.014), which the script labels unsettled.

Seeing that number would not have helped tune the condition. An upper limit below 0 is the conventional condition and has no free threshold. It could have informed the predicted range (-0.45 to -0.10) and the decision to register a negative direction. A negative direction is also what prior knowledge of these areas predicts.

No measure chosen after the data decides the verdict. The end period of 2017-2019 in the notes was chosen after the outcome and is labelled exploratory, as rule 4 requires.

## (b) Errors in code, units, joins, dates, geography or uncertainty

The numbers reproduce: the contrast and its interval, the totals (341,000 to 241,000 poor residents in the gentrified areas, a fall of 29.2%; a fall of 10.5% in the other 14; 3.1% in the other 33), and the exploratory contrast for 2017-2019 of -0.243 (-0.350 to -0.137). I found no error in the code. The script multiplies the mean poverty rate by the mean population for the three end years. The mean of the three annual products gives -0.282 (-0.544 to -0.020), so that choice does not matter.

The registered margin is fragile. I list the variants in which the upper limit reaches 0 or passes it.

| Variant | Difference (95% interval) |
|---|---|
| Registered | -0.283 (-0.544 to -0.021) |
| End year 2022 alone | -0.309 (-0.582 to -0.037) |
| End year 2023 alone | -0.280 (-0.579 to +0.018) |
| End year 2024 alone | -0.257 (-0.519 to +0.005) |
| Without Washington Heights/Inwood | -0.259 (upper limit +0.032) |
| Without Brooklyn Heights/Fort Greene | -0.265 (upper limit +0.030) |
| Without North Crown Heights/Prospect Heights | -0.265 (upper limit +0.030) |
| Without Bushwick | -0.215 (upper limit +0.020) |
| Without Throgs Neck/Co-op City | -0.229 (upper limit +0.017) |
| Without Morningside Heights/Hamilton Heights | -0.286 (upper limit +0.012) |
| Washington Heights/Inwood classed as not gentrified | -0.230 (-0.523 to +0.063) |
| East Harlem classed as gentrified | -0.234 (-0.493 to +0.025) |
| Groups by the k2 definition (baseline 2005-2007) | -0.214 (-0.498 to +0.071) |
| Groups by a rise of five rent ranks and the college condition | -0.280 (-0.597 to +0.037) |
| Borough terms added | -0.173 (-0.479 to +0.132) |
| Without the seven Bronx areas | -0.204 (-0.474 to +0.067) |

Six of the 22 single removals move the upper limit to 0 or above. Washington Heights/Inwood passes the rent condition by 0.8 points of growth, and East Harlem misses it by 2.0 points, so the two reclassifications in the table are within the noise of the classification. The point estimate is negative in every variant, between -0.17 and -0.33.

Other tests on the registered groups and period agree with the registered one: a pooled-variance interval of -0.528 to -0.038, a Mann-Whitney p of 0.029, a permutation p of 0.022, and -0.290 (-0.529 to -0.050) after adjustment for the 2000 poverty rate. The 2000 poverty rates of the two groups are close (means of 32.1% and 32.8%), and the 2000 rate does not predict the change in the count (rank correlation 0.05), so regression to the mean in poverty is not an explanation.

The 2022 boundary change is the main source of the fragility. The standard error of the contrast is 0.050 with the end period 2017-2019, 0.062 with 2018, 2019 and 2021, and 0.121 with 2022-2024. The standard deviation of the log change within the groups rises from 0.11 and 0.12 to 0.28 and 0.26. Across the 22 areas, the difference between the log change to 2022-2024 and the log change to 2017-2019 has a correlation of 0.69 with the jump in population between 2021 and 2022. Bedford Stuyvesant gains 21% in population at the break, and its poor count moves from a fall of 16% (log change -0.175) to a rise of 2%. Bushwick loses 18%, and its fall goes from 33% to 57%. A count of poor residents is a rate multiplied by a population, so it takes the full boundary change, where the first claim's rent and college measures take little of it. The registered measure for 2022-2024 is therefore the count for a different territory in about half the areas. The error does not favour either group: the contrast in log population change is +0.027 (-0.171 to +0.225).

Measures less exposed to the boundary change give clearer results. The change in the poverty rate to 2022-2024 differs by -6.5 points (-10.3 to -2.7), and the log change of the rate by -0.310 (-0.474 to -0.146). With the end periods before the break the count contrast is -0.243 (-0.350 to -0.137) and -0.250 (-0.380 to -0.119), and no single removal of an area moves the 2017-2019 upper limit above -0.117. With borough terms the 2017-2019 contrast is -0.165 (-0.294 to -0.037), and without the Bronx areas it is -0.182 (-0.299 to -0.064). These variants were chosen after the data and decide nothing under rule 4. They are the reason I recommend keeping the verdict.

The Welch interval treats the 22 areas as independent. They are not. Five of the eight gentrified areas adjoin one another in northern and central Brooklyn, and the other three adjoin one another in upper Manhattan. Seven of the 14 comparison areas are in the Bronx, where no area gentrified. The effective number of independent units is smaller than 22, and the registered interval is too narrow by an amount I cannot estimate from these data.

## (c) Is the comparison with the research fair?

There is no comparison to judge. The registration says the graph holds no finding on counts of poor residents, and the outcome has no `graph_effect`. The studies cited (Freeman and Braconi 2004; Dragan, Ellen and Glied 2020) follow individuals and find that poor residents of gentrifying areas were no more likely to move. A count for an area cannot agree or disagree with them. The claim is filed as a confirmation, but there is no research estimate for it to confirm. The stance of 0.786 (z = 2.12) expresses agreement with a research direction that the graph does not supply. I suggest a null stance, or a note beside it that it measures the distance of the city contrast from zero and nothing else.

## (d) Which alternative explanation is not addressed?

1. Borough. The contrast between gentrified and other areas is partly a contrast between Brooklyn and Manhattan on one side and the Bronx on the other. Within Brooklyn the mean log changes are -0.410 for five gentrified areas and -0.265 for four others. Within Manhattan they are -0.321 for three and -0.097 for two. In the Bronx the seven areas average -0.014. With borough terms the registered contrast falls to -0.173 and its interval includes zero. With the end period 2017-2019 the contrast within borough is -0.165 and its interval excludes zero. The Bronx's different trend in poverty, for reasons unrelated to rent, is a rival that the registration does not name.

2. The classification and the outcome share their data. The gentrified group is defined by a rise in the college share from the same survey samples and the same redrawn areas that give the poverty count. An area whose 2022-2024 sample or territory holds more graduates will show both a larger college change and fewer poor residents. Graduates are seldom below the poverty line, so part of the association is built into the definition. The count is less exposed to this than the rate, which is why the registration chose it, but it is not free of it. Among the 22 areas the log change in the poor count follows the college change (slope -0.13 per 10 points, -0.23 to -0.04; rank correlation -0.61) more closely than it follows rent growth (rank correlation -0.33, with an interval for the slope that includes zero).

3. Timing. The contrast by period is -0.002 (-0.068 to +0.065) from 2000 to 2005-2007, -0.087 (-0.186 to +0.011) to 2010-2012, -0.154 (-0.246 to -0.062) to 2017-2019, and -0.040 (-0.230 to +0.150) to 2022-2024. Most of the difference arose between 2010 and 2019. Nothing can be said about the period since 2019 from these data.

4. What the count cannot show. The registration and the outcome both state that a fall in the count is not displacement, and the outcome's notes repeat it. I agree and add the composition. In the gentrified areas the number of residents above the poverty line rose by 24.6% (728,000 to 907,000) while the number below it fell by 29.2%. In the other low-rent areas the numbers are +11.8% and -10.5%. The same contrast would result if poor residents moved out, if they died or aged out of the area and were replaced by residents who are not poor, if the incomes of residents who stayed rose past the national poverty line, or if poor households were counted elsewhere after the boundary change. The data hold no information on which occurred. The claim as registered is about the count only, and the verdict should be read as covering only that.

5. Students. Morningside Heights/Hamilton Heights holds a university. Students living off campus are counted in the poverty universe, and changes in their number move the count without any change among long-term residents. The area's contribution is small (removing it changes the estimate from -0.283 to -0.286).

## (e) Could the test have failed?

Yes. The registration computed a probability of support between 0.34 and 0.90 for a true difference of -0.30, depending on the spread, and 0.025 with no true difference. The realised standard error is 0.121, inside the registered range of 0.09 to 0.18. Against no difference z is -2.33. Against the registered best guess of -0.25 it is -0.27. D is 5.4, so the result is closer to the prediction than to no effect by more than the threshold rule 8 uses for endpoint tests. The predicted range was written after the leak described in section (a), and I would not score it as a blind hit.

## Requested changes to the outcome

1. Keep the verdict and keep the `verdict_note`. Add to the note that six of the 22 single removals of an area, and the end years 2023 and 2024 taken singly, put the upper limit at or above 0.
2. Say that the count takes the full 2022 boundary change, give the correlation of 0.69 between the shift in the log change and the population jump, and give the standard errors before and after the break (0.050 and 0.121).
3. Add the borough result: seven of the 14 comparison areas are in the Bronx, and with borough terms the registered contrast is -0.173 (-0.479 to +0.132) and the 2017-2019 contrast is -0.165 (-0.294 to -0.037).
4. Say that the 22 areas are spatially clustered and that the interval assumes independence.
5. Add the timing: most of the difference arose between 2010-2012 and 2017-2019.
6. Record that the simulated run wrote this claim's block to a file that is no longer in the repository, and that the statement that the block was not read rests on the registrant's account.
7. Set the stance to null, or note that the graph supplies no direction for it.
8. In any summary, describe the result as a difference in the change of a count, and do not use it as evidence on displacement.

Recommendation: keep.
