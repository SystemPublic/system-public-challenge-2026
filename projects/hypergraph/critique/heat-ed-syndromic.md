# Referee report: heat-ed-syndromic

Verdict recorded: confirmed. Recommendation: keep the verdict.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required a lower limit above 1 and an estimate of at least 1.5 for the IRR per 5 C. The estimate is 4.09 (3.76-4.45) on 1,522 warm-season days. The RR at the 95th percentile against the median (11.2) exceeds the predicted 3. The registered yearly secondary was weak (Spearman 0.36, p = 0.15), and the outcome reports it. It also reports an unregistered 95 F threshold (rho 0.84) and labels it as unregistered.

## (b) Errors in code, units, joins or dates

I tabulated `ed_daily.csv` by year and source file. 2017-2025 come from `previous_years.csv` (revised definition); 2026 comes only from the live file, and two days in 2023 from the 2023 live file. Year effects absorb any level difference between files. 2025 is missing 8 days. Visits rose in 2025-2026 (about 1,100 a year against 500-850 before) on few hot days; year effects absorb this as well. The data are daily (END_DATE is a single day), so the join to daily TMAX is correct. The holiday list adds 1 January, which is already a federal holiday; this is harmless.

## (c) Is the research comparison fair?

No, and the outcome says so. Sun et al. (2021) used claims diagnoses and a contrast of the local 95th percentile against a cooler reference day. The city series counts chief-complaint matches and is near zero on mild days, so any ratio against the median is inflated. The direction agrees; the sizes are not comparable. The registration's assumption that Sun's reference was the median was a registrant error, and the outcome notes it.

## (d) Alternative not addressed

Awareness bias was named and not tested. Heat advisories are issued on the hottest days, and chief-complaint keyword matching may respond to them. Including an advisory-day indicator (NWS or NYC Emergency Management dates) would test it directly.

## (e) Is the settle condition right?

Yes for the comparison of size. The direction needs no further settling.

## Recommendation

Keep "confirmed". Add an advisory-day sensitivity when the dates are available.
