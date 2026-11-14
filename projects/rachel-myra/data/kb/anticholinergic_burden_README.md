# anticholinergic_burden.csv

## Source
Anticholinergic Cognitive Burden (ACB) Scale, 2012 update. Aging Brain Care, Indiana University Center for Aging Research. Copyright 2008, 2012 Regenstrief Institute, Inc.
Original scale: Boustani M, Campbell N, Munger S, Maidment I, Fox C. Impact of anticholinergics on the aging brain: a review and practical application. *Aging Health* 2008;4(3):311-320.

URL: https://www.hii.iu.edu/resources/anticholinergic-cognitive-burden-scale.pdf (2-page PDF; created 2013-01-25, modified 2020-07-12)
Raw copy: `sources/acb_scale_2012_hii_iu.pdf` (317 KB)
Accessed: 2026-11-14

## How it was retrieved
The PDF was downloaded with curl. The original agingbraincare.org link no longer resolves. The page-1 tables were read with pypdf, and each drug was assigned to a column ("Drugs with ACB Score of 1/2/3") from the x-coordinate of its text. Brand names were matched by y-coordinate. No scores were typed in by hand or filled in from memory. Every row maps to a name printed in the PDF. The layout parse was clean, so no score was ambiguous and none is left blank.

## Counts (99 drugs)
| ACB score | Drugs |
|---|---|
| 1 (possible anticholinergic) | 44 |
| 2 (definite) | 12 |
| 3 (definite; may cause delirium) | 43 |

## Caveats
- `drug_generic` uses the name as printed, in lowercase. A few names are USAN rather than INN, and the INN is given in `note`: methotrimeprazine (INN levomepromazine), meperidine (pethidine), chlorpheniramine (chlorphenamine), scopolamine (hyoscine). The source lists alimemazine under its INN; its USAN is trimeprazine.
- `belladonna` is a botanical, not a single INN. `isosorbide` is listed without a salt (the brands shown are Isordil and Ismo).
- On page 2, the source lists drugs it reviewed in 2012 but did NOT add to the scale: fexofenadine, gabapentin, topiramate, levetiracetam, tamoxifen, nizatidine and duloxetine. They are not in the CSV.
- 16 drugs were added in the 2012 update, and their `note` says so.
- Other scales score some drugs differently. For example, other scales score some SSRIs, and some secondary copies of the ACB list differ from this one. The CSV reflects this one source only.
- Use of the scale is subject to the Regenstrief/Aging Brain Care Terms of Use, which the PDF cites.
- A drug that is absent from the scale is "not listed". That is not the same as a score of 0.

## Project drug check
Not listed in the source (and so not in the CSV): sertraline, citalopram, escitalopram, fluoxetine, carvedilol, lithium, mirabegron.

The other 34 checked drugs are present:
- **Score 3:** oxybutynin, tolterodine, solifenacin, trospium, darifenacin, fesoterodine, benztropine, trihexyphenidyl, amitriptyline, nortriptyline, imipramine, doxepin, diphenhydramine, hydroxyzine, chlorpheniramine, promethazine, clozapine, olanzapine, quetiapine, paroxetine, meclizine
- **Score 2:** cyclobenzaprine, carbamazepine
- **Score 1:** haloperidol, risperidone, aripiprazole, furosemide, metoprolol, atenolol, ranitidine, warfarin, digoxin, prednisone, alprazolam
