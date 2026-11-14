# Referee report: construction-sheds-outnumber-nb

Verdict recorded: confirmed. Recommendation: keep the verdict for the counts, and remove the perception clause from the statement that was confirmed.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required a shed-to-NB ratio above 1.2 and a share of shed lots on NB lots below 0.35. The ratio is 2.30 (2.16 excluding signed-off permits), and the share is 0.10 (0.09). Both are well inside the bounds, and every magnitude prediction falls in its registered range.

## (b) Errors in code, units, joins or dates

I checked `sheds.py` against the parquet files. BBLs are 10-character strings in both systems, so the overlap join is valid. The "active NB job" count includes any active DOB NOW permit filed under an NB job number (plumbing, sprinklers, foundation, and so on), not only the NB work permit named in the registration. This widens the NB count and makes the ratio smaller, so it works against the claim. The shed count is by job filing, and one filing can cover several lots; the registration specified job counts, so this is consistent.

The "interval" (2.16-2.30) spans two definitions of "active" and is not a sampling interval. The outcome says so. The stance computed from it (+1.0) treats it as one.

## (c) Is the research comparison fair?

There is no research quantity, and the outcome states this. The statement's first clause, "the construction a person sees on NYC streets is mostly not new buildings", is a claim about perception that the data do not test. The confirmation applies to permit counts only.

## (d) Alternative not addressed

The outcome's own monthly series shows active shed jobs falling from about 10,000 to 7,600 in 2026. If this is delayed recording of renewals rather than removal, the count on 1 November 2026 is low. That would strengthen the claim, but the series is not stable, and the reference date matters more than the registration assumed.

## (e) Is the settle condition right?

Yes. A street survey or the DOB shed map on one day, and a perception survey, would settle the remaining parts.

## Recommendation

Keep "confirmed" for the permit counts. Restate the confirmed claim without the perception clause.
