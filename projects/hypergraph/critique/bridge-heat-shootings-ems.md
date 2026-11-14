# Referee report: bridge-heat-shootings-ems

Verdict recorded: bridged (first recorded as confirmed, relabelled under rule 7). Recommendation: keep the verdict under the registered rule, but report the test as weak. Lower the stance, and add an exploratory analysis of the non-victim component. The endpoint partly re-measures the first link, and the composed range admits almost every plausible result.

## (a) Was the composed prediction fixed before the endpoint was queried?

Yes. `composed_predictions.json` was committed in `a4b6f1e` at 16:04:49 on 12 November, and the registration in `e783221` at 16:04:50. The daily EMS counts (`76xm-jjuj-2ccf…`) were fetched at 16:08:40. Before registration, only the 2023 total by call type (15:59:20) and the date range (15:59:25) had been fetched from this dataset. These fixed the range of w but contain no information about temperature. The heat-shootings link was estimated at 15:19-15:28, from NYPD data only.

As with the crash bridge, rule 7 and its stance formula were committed (`3d8ac0d`, 16:12:16) after this outcome was decided (16:10:34) and committed (16:11:46). The rule's text is dated 13 November.

## (b) Errors in composition, uncertainty, units or model

The mixture IRR = w·IRR_s + (1-w)·IRR_s^k is the correct form for a sum of two counts, provided w is the victim share at the reference temperature. Using an annual share is an approximation, and the error is small at these rate ratios. The units match: the endpoint uses the same Central Park TMAX/5, the same terms and the same negative binomial model as heat-shootings, on the same 7,548 days.

The variance of the difference is computed as if the link and the endpoint were independent. They share days, weather and, through the victim dispatches, events, so their sampling errors are positively correlated. The combined SE is therefore slightly too large. This is minor because the composed SD (0.025) comes almost entirely from the uniform prior on k, not from sampling error.

That prior is the main issue in the composition. The composed interval is not an estimate of uncertainty. It is the range of an unknown parameter, k, set by assumption to [0, 1]. The interval says only that non-victim dispatches follow heat somewhere between not at all and as much as shootings.

## (c) Is the endpoint independent of the links?

No, not fully. About 30 to 50 percent of SHOT dispatches are the shooting victims counted in heat-shootings. Those events appear in both the first link and the endpoint. On the same days, their heat gradient is by construction the gradient of the first link. With w = 0.37 and IRR_s = 1.146, the victim share alone puts the endpoint at 1.054 or above, whatever the other dispatches do. Part of the agreement is therefore guaranteed. The outcome's `settle` text notes the two extremes but does not say that the lower one is set by the shared events.

## (d) Is the test informative?

Weakly, as a test of the chain. The combined SE is 0.0256 on the log scale, so the test refutes only if the observed IRR is below 1.047 or above 1.155 per 5 C. With w = 0.37, this corresponds to k below -0.08 or above 1.09. The bridge would be contested only if shots-fired reports without a victim fell with heat, or rose faster than shootings. Neither was likely in advance.

Several hypotheses that do not involve the chain also pass. The stabbing contrast, 1.076, lies inside the acceptance region (z = -0.8). A hypothesis that all violence-related EMS calls rise with heat by a common amount would also have been confirmed. A null of no heat effect on EMS dispatches would have been refuted (z about -3.7), but a no-heat null was never plausible given the first link and the shared events.

The endpoint itself is precise (SE 0.0048) and does carry information: it puts k at about 0.64 and excludes k = 0 by a wide margin. That result is exploratory. It is the useful finding of this bridge, and it is not what the verdict scores.

## (e) Alternative explanation not addressed

The registration names fireworks, coding changes and outdoor presence. The alternative not addressed is a general rise in interpersonal-violence calls with heat that does not pass through shootings at all. The stabbing result shows such a rise exists. A test that separates the chain from this alternative would model the non-victim component directly: for example, the heat gradient of SHOT dispatches minus 1.25 times the day's NYPD incidents, compared with the STAB gradient.

## Recommendation

Keep bridged under the registered rule. Add to the outcome that roughly a third of the endpoint's events are the first link's events, and that the test refutes only for k outside about [-0.08, 1.09]. Reduce the stance, or report beside it the z of the STAB contrast against the composed prediction, so the dashboard does not read 0.835 as strong support. Report the k ≈ 0.64 estimate, and a direct model of the non-victim component, as exploratory analyses that could be registered as a new claim.
