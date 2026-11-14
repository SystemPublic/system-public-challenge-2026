# Referee report: mob-active-commute-obesity

Verdict recorded: confirmed. Recommendation: keep the verdict for the associational statement as registered, but drop the comparison with the research effect and lower the dashboard stance.

## (a) Does the verdict follow from the registered conditions?

Yes. The support rule was a poverty-adjusted slope below zero with an interval below zero. The estimate is -5.97 points per 10 points (-7.81 to -4.12), n = 42. The magnitude exceeds the registered range (-0.5 to -4), and the outcome scores the prediction as partial, which is correct.

## (b) Errors in code, units, joins or dates

`active_commute.py` is correct. Bicycle and walking shares are added, obesity is the mean of 2017-2019 CHS estimates, and poverty is ACS 2015-19. The years overlap adequately. The obesity outcome is a survey estimate with a few hundred respondents per UHF; unweighted OLS ignores the different precision of each UHF, which affects the interval, not the sign.

## (c) Is the research comparison fair?

No. Flint et al. (2014) estimate an individual-level BMI difference between active and car commuters. The city quantity is an area-level prevalence slope across 42 neighbourhoods. The outcome itself shows that the city slope is several times larger than any causal effect implied by Flint. The research quantity and the city quantity are different, and the stance of +0.996 on the dashboard presents a composition gradient as agreement with research.

## (d) Alternative not addressed

Poverty turned out to be nearly uncorrelated with active commuting (r = -0.08), so the one adjustment did little. The confounders that matter here are education, race and ethnicity, age structure, income above the poverty line, and residential density. All are available by UHF in EHDP or ACS and were not used, even as an unregistered sensitivity. The slope without Manhattan (-11.6) is steeper than the full-sample slope, which suggests the gradient runs through outer-borough composition rather than Manhattan alone.

## (e) Is the settle condition right?

Yes. Individual data with commute mode, or a change design around new bike lanes or Citi Bike stations, would settle the causal question.

## Recommendation

Keep "confirmed" for the area-level association. Set the graph_effect comparison to "not comparable" and add an education and race/ethnicity sensitivity to the notes.
