# Referee report: mob-crz-air-nyccas

Verdict recorded: unsettled. Recommendation: change to contested under the registered refutation rule, or state a project-wide rule that the generic verdict definitions override registered conditions and apply it to every claim.

## (a) Does the verdict follow from the registered conditions?

It does not. The registered refutation was "NO2 DiD at or above 0, or within the central 80% of the placebo-in-space distribution". The estimate is +0.9% with a one-sided placebo p of 0.70. Both parts of the refutation are met, and the outcome says so ("the refutation condition registered ... is met"). The verdict was nonetheless set to unsettled.

The likely reason is the generic definition in concord/claims.py, under which contested requires an interval that excludes zero. But heat-trees-ed-chain was scored the other way: its registered refutation was applied and gave contested even though its interval includes zero. The two claims apply opposite rules. One of them is wrong, and the register needs a stated precedence.

There is also a timing question. This claim was registered (15:24:55) after the AQS analysis for mob-crz-air had shown that no Manhattan NO2 monitor exists, and the same EHDP indicator file (2025, NYCCAS NO2 by UHF, including 2025 values) was used for mob-asthma-pollution. Git order shows registration before the outcome, but cannot show that the 2025 UHF values were unseen at registration.

## (b) Errors in code, units, joins or dates

The DiD on the balanced panel is computed correctly, and the placebo-in-space interval (estimate minus placebo quantiles) is a reasonable construction. I found no join or unit errors. Two points need checking. The NYCCAS "annual" period may not be a calendar year; if it starts in December, one pre-policy month is in the 2025 value. And with one post year and 32 controls, the placebo distribution has little resolution.

## (c) Is the research comparison fair?

Partly. Stockholm and London estimates are for monitored concentrations near cordons. NYCCAS annual surfaces are land-use regression outputs whose spatial traffic covariates are held fixed across years. The outcome notes this, and it is the main reason the comparison is weak: the instrument may not be able to show a local change.

## (d) Alternative not addressed

Diversion of traffic to the FDR Drive and West Side Highway, which border UHF 306-310, would raise NO2 inside the in-zone UHFs. The registration named diversion only for comparison monitors.

## (e) Is the settle condition right?

Yes. Raw in-zone NYCCAS monitor values, a second post year, and near-road hourly NO2 are the right data.

## Recommendation

Score it as contested under the registered rule, with the caveat about model-based surfaces in the notes; or, if the generic rule takes precedence, record that the registered refutation was met and rescore heat-trees-ed-chain by the same rule.
