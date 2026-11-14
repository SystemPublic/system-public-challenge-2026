# Referee report: construction-aerial-triangulation

Verdict recorded: unsettled. Recommendation: keep the verdict, and fix the stance.

## (a) Does the verdict follow from the registered conditions?

Yes. Support required visible change of at least 0.6, kappa above 0.2 and a CO-but-no-change share below 0.15. Kappa is -0.07 (0.11 on decided pairs), so support fails. Refutation required visible change below 0.45 or CO-but-no-change of at least 0.25. With "unclear" counted as not changed, the second share is 0.229, just under the bound. The verdict follows the rule, but the margin is one job: 12 of 48 would have met the refutation bound. The rule also did not say how "unclear" should be counted. Dropping unclear pairs gives a CO-but-no-change share of 0.0, so the count convention decides whether that criterion passes or nearly refutes. It should have been fixed at registration.

## (b) Errors in code, units, joins or dates

`aerial_score.py` computes kappa, the shares and the AUC correctly. I confirmed the counts in `aerial_summary.json`: 33 changed, 14 unclear, 1 unchanged.

The blinding is weaker than described. The judgement sheets showed only an index number, but the same agent drew the sample (with job numbers) and had built `nb_jobs.csv.gz`, which holds CO dates, in the same session. The commit order (judgements at 15:39:17, construction analysis at 15:42:36) shows when files were committed, not when the CO join was first run. The design is still blind at the sheet level, but a second rater who never saw the job list would be needed for a credible blind judgement.

The stance is computed with null 0 for a proportion, so it is +1.0. That number means nothing, and it puts an unsettled claim at the far agreeing end of the dashboard.

## (c) Is the research comparison fair?

There is no research quantity. The claim is a measurement-validation exercise. That is fine, but it should not appear on the same agreement scale as claims tested against research.

## (d) Alternative not addressed

Fourteen of 48 pairs (29%) were unclear, mostly because the 2017 flight is 1.0 m. Unclear pairs are not missing at random: they are small lots and lots shaded by tall neighbours, where change is hardest to see. The visible-change share is therefore biased toward larger projects.

## (e) Is the settle condition right?

Yes. Stratifying on CO status and using finer imagery (NYC orthoimagery at 0.15 m) are the right next steps, and both are named.

## Recommendation

Keep "unsettled". Set the stance to null for this claim, and in any re-registration fix how unclear judgements are counted and use a second, independent rater.
