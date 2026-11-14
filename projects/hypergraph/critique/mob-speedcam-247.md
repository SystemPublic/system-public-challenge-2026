# Referee report: mob-speedcam-247

Verdict recorded: unsettled. Recommendation: keep the verdict.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required a ratio of ratios below 1 with an interval below 1. The estimate is 0.934 (0.860-1.014). Refutation required a ratio at or above 1 with an interval excluding 0.97. Neither is met.

## (b) Errors in code, units, joins or dates

I checked the SoQL classification of hours, which compares `crash_time` as text. The field is zero-padded ("09:35"), so the string comparison with "06:00" and "22:00" is correct. `date_extract_dow` returns 0 for Sunday, as the code assumes. The cached query returned 1,512 rows (72 months x 7 days x 3 bands), so nothing was truncated. The model uses a fixed effect for each sample month, not calendar month as the registration wrote; this is the more flexible choice and does not bias the estimate. Weekday holidays are counted as old hours. In 2021-2023 there are about 10 such days a year, too few to matter.

## (c) Is the research comparison fair?

No, and the outcome says so. The graph effects (Barcelona RR 0.73, South Wales 0.49) are measured at camera sites. The city estimate is citywide, so a local effect is diluted by the large majority of crashes that occur away from cameras. The outcome's catch of a mis-extracted graph row (PMID 17666698, comparison roads stored as a camera effect) is useful.

## (d) Alternative not addressed

The outcome shows that the new-hours share returned to its 2019 level after the change, so post-pandemic recovery of daytime travel can explain the whole drop. One more alternative is not addressed: the growth of e-bike and moped delivery traffic, concentrated in evening hours. It was named but not measured.

## (e) Is the settle condition right?

Yes. Camera locations and crashes geocoded near them, with hourly traffic volumes, are the right data.

## Recommendation

Keep "unsettled".
