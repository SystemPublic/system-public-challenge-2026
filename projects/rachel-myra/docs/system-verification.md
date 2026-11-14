# Using the System graph to check our data

Written 14 Nov 2026, with results from a live pilot against the System API. This feeds spec §8.2a.

## The idea in one line
Treat System as an **independent second extractor**. Systematic reviews have two people extract every number and compare. We have our AI extraction plus System's pipeline, and we compare the two at three levels: **the same paper, the same meaning, and across papers.**

---

## Pilot results (14 Nov, our 8 cited papers that have System findings)

| Paper | Our number(s) | System | Result |
|---|---|---|---|
| Martin-Latry 2007 (PMID 17513091) | OR 6.0, 4.6, 2.4 | OR 6.0, 4.6, 2.4 (with CIs) | **Values match**, but System labels all three "psychotropic drugs" → **mislabel** (6.0 is anticholinergics) |
| Mangoni 2017 (PMID 29116624) | OR 1.02 | OR 1.02 [0.21–2.97], plus OR 0.79 | **Match** |
| Voriconazole meta-analysis (PMID 30130598) | RR 1.72 | RR 1.72 [1.09–2.72] | **Match** |
| Dialysis heat study (PMID 31397862) | RR 1.27, 1.31 | RR 1.27 [1.13–1.43], 1.31 [1.01–1.70] (+5 more) | **Match** (my first script missed it because we cited the PMC ID, not the PMID) |
| Hurricane Irma nursing homes (PMID 35977265) | OR 1.25 | OR 1.25 [1.05–1.48] | **Match** (cited by DOI) |
| Insulin pens at 37°C (PMID 36585035) | 158.7 vs 157.0 mg/dL | mean difference 1.7, p=0.72 | **Match, derived** (158.7 − 157.0 = 1.7) |
| Army recruits, stimulants (PMID 29613996) | stimulants → mild heat illness | only BMI, tobacco and prior-illness findings | **Our claim not extracted** by System |
| Hydrochlorothiazide skin cancer (PMID 29217346) | no number cited | OR 1.29–7.38 | Nothing to compare; could add System's numbers |

**What this tells us:**
- **No number conflicts.** Wherever both of us extracted the same result, the numbers agreed.
- **System's weak spot is labels, not numbers:** the "psychotropic drugs" mislabel.
- **The coverage gap is real:** for the stimulants paper, System has the paper but not the drug finding.
- **ID joining matters:** we cite papers by PMID, PMCID or DOI, so we must normalize IDs first or we'll miss matches.

**Claim-level pilot (concept pairs):**

| Claim | System relationship | Direction across ratio-type findings |
|---|---|---|
| thiazide → hyponatremia | 5 findings / 5 studies | 2 raise risk, 1 lowers |
| furosemide → acute kidney injury | 18 / 18 | 9 raise, 3 lower |
| empagliflozin → diabetic ketoacidosis | 4 / 4 | 4 raise, 0 lower |
| lithium → AKI; topiramate → hypohidrosis; olanzapine → heat stroke; oxybutynin → hyperthermia | **none** | — (gap) |

---

## The method: five checks

### Check 1. Same paper, same number (value match)
1. **Normalize IDs:** convert every citation to PMID + PMCID + DOI (NCBI ID Converter API), then look up the paper in System (`/studies?filter=pubmed_id:…` or `doi:…`).
2. **Compare numbers:** match our value to System's `statistic_value` within rounding (e.g. ±0.01, or the precision the paper reports), and compare the CI bounds and statistic type.
   - Also allow **derived matches**, e.g. a difference of two means we quoted.
3. **Result:** Match / **Conflict** (same result, different number) / Paper in System but our finding not extracted / Paper not in System.

### Check 2. Same meaning (are the variables what we think they are?)
- Compare our drug and outcome to System's `variable_1_name` / `variable_2_name` and their concepts:
  - synonym lists from RxNorm and Wikidata aliases
  - an LLM judge for "does 'use of psychotropic drugs' mean 'anticholinergics'?"
- **Result:** Same meaning / **Mislabel** (numbers match, labels don't; goes on the audit fix list) / Unclear.
- **Direction check:** for odds/hazard/risk ratios, >1 = higher risk, and our claimed direction must agree. This catches swapped cause and effect.

### Check 3. Across papers (corroboration)
- Map each claim to a System concept pair (e.g. thiazide ↔ hyponatremia) and pull the relationship's findings.
- Report **number of independent studies**, **share pointing the same way** (ratio-type findings only, never mixing statistic types) and **newest year**.
- Shown on the claim as e.g. "**System: 18 studies, 75% agree it raises risk**."
- No relationship → "**not in System**" (feeds the gap constellation).

### Check 4. Is System's finding solid? (API vs Dataverse)
- System says about 20% of API associations are extracted inaccurately, and recommends keeping only those also in the Dataverse CSV.
- Keep API findings only if they also appear in the Dataverse CSV.

### Check 5. Reverse check: what does System have that we're missing?
- For each of our 15 drugs and each mediator/heat outcome, list System relationships with strong evidence (e.g. ≥5 studies) that **aren't in our master list**.
- This finds claims we should add, so it checks our completeness, not just our accuracy.

---

## Badges (replace the earlier draft in spec §8.2a)
- **✓✓ Double-verified:** our number matches System's for the same paper (Check 1 + 2) **and** appears in the abstract.
- **✓ Verified:** appears in the abstract; System has no extraction of it.
- **↗ Corroborated:** System has N other studies pointing the same way (Check 3). Shown alongside the badges above.
- **⚠ Conflict or mislabel:** numbers or meaning disagree; visible in nerd stats and on the audit fix list.
- **? Unverified:** no abstract match and no System support. **Hidden from public labels.**

## What goes in nerd stats
- Counts per badge.
- Pilot-style table of matches, conflicts and mislabels.
- "**System agreed with our extraction on X of Y shared results; 0 number conflicts; Z label errors**."
- Corroboration coverage: share of claims with any System relationship.

## Limits
- System only covers part of our evidence (8 of 51 cited papers had findings in the first check).
- It extracts text only, not tables.
- Its concept filing is incomplete, so "no relationship" can mean "filed under a different concept."
- Abstract matching can't see full-text-only numbers.
- No human review.
