# Screening rules (fixed before screening)

Spec §8.4 step 4. Written 2026-11-14, **before** any record was screened, and not changed afterwards.
Screening is **automated**: a rule-based prefilter (`scripts/lit_prefilter.py`), then an LLM screener (Claude) reading title + abstract against the rules below. **No human screening or human review was done.**

Unit of screening: one record in `data/processed/literature_records.csv` (title + abstract + MeSH). Full texts were not read.

## Scope: the 15 drugs/classes (spec §8.7)
lithium; loop diuretics; thiazides; ACE inhibitors/ARBs; SGLT2 inhibitors; insulin (incl. pumps); metformin; anticholinergics (incl. oxybutynin, benztropine, tricyclics, first-generation antihistamines); antipsychotics (incl. clozapine); SSRIs; topiramate/zonisamide; ADHD stimulants (amphetamines, methylphenidate); beta blockers; fentanyl/opioid patches (incl. opioids generally); epinephrine auto-injectors.

Storage questions in the search (§8.4 step 1) also covered **inhalers** and **glucose test strips/meters**. Records about heat effects on these devices are included under the storage rule (I2) and tagged `storage_other`, because the search was designed for them; they are reported separately from the 15 drugs.

## Include (all of I1 or I2 must hold)
**I1. Drug × heat (clinical / physiological).**
- (a) Humans (any design: RCT, cohort, case-control, case-crossover, time-series, cross-sectional, case series, case report, pharmacovigilance, human lab/chamber study; systematic reviews/meta-analyses are included and tagged `review`; narrative reviews are included only as `review` if they are specifically about the drug × heat question), **and**
- (b) one of the 15 drugs/classes is an exposure, effect modifier, or the subject, **and**
- (c) a heat-related outcome or exposure is reported: heat illness / heat stroke / heat exhaustion; hyperthermia caused or worsened by environmental or exertional heat; heat waves / high ambient temperature / hot season (as exposure or effect modifier); impaired sweating or thermoregulation; dehydration, AKI, hyponatremia, lithium toxicity, hypoglycemia or other harm **explicitly linked to heat or hot weather**; drug pharmacokinetics or drug delivery (e.g. transdermal fentanyl absorption, insulin absorption) under heat.

**I2. Drug stability / storage under heat.** Lab or field studies (no humans required) reporting stability, potency, degradation, or device performance of one of the 15 drugs (in practice insulin, epinephrine auto-injectors, and others), or of inhalers / glucose test strips / meters, at elevated temperature (heat, hot climate, summer, car/mail transport, temperature excursions above label storage).

## Exclude (any one is enough)
- E1. No abstract (cannot be screened; counted, titles kept).
- E2. Animal-only or in-vitro biology with no human data (I2 lab stability studies of a medicine product are not E2).
- E3. Materials science / chemistry / engineering (e.g. lithium batteries, lithium salts in materials, crystals, ceramics, nanomaterials, synthesis) not about a human medicine.
- E4. Fever / infection / sepsis / inflammation, or drug-induced hyperthermia, **without** an environmental or exertional heat link.
- E5. Neuroleptic malignant syndrome, serotonin syndrome, malignant hyperthermia, anticholinergic toxidrome, or stimulant/overdose hyperthermia **unless** the record links it to environmental heat (heat wave, hot weather, high ambient temperature, exertion in heat).
- E6. None of the 15 drugs/classes (or, for storage, inhalers / glucose strips) is a studied exposure, effect modifier or product (e.g. drug only mentioned as a treatment for an unrelated condition, or anesthesia/hyperthermia therapy where the drug is incidental). Therapeutic hyperthermia (oncology), thermal ablation, cold-chain refrigeration only (no heat), sterilisation / heat-treatment of other materials are E6/E3.
- E7. Not about heat: "temperature" used only for cold storage, freezing, body temperature measurement unrelated to heat, or laboratory assay conditions.
- E8. Non-research items with no data (editorials, letters without a case, errata, protocols with no results) — unless a letter describes a case (then include as case report).

When in doubt between include and exclude on title/abstract alone, the screener **includes** and sets `reason` to start with `uncertain:` (standard SR practice: err toward inclusion at title/abstract stage).

## Recorded per record (`screen_results/chunk_NNN.csv`)
`record_id, decision (include|exclude), reason (rule code + short text), drug_class, outcome_type, design`
- `drug_class`: one of `lithium, loop_diuretics, thiazides, ace_arb, sglt2, insulin, metformin, anticholinergics, antipsychotics, ssris, topiramate_zonisamide, adhd_stimulants, beta_blockers, opioids_fentanyl, epinephrine, multiple, storage_other, none`
- `outcome_type`: `heat_illness, hyperthermia, mortality, hospitalization_ed, sweating_thermoregulation, renal_aki, electrolyte_hyponatremia, drug_toxicity_levels, hypoglycemia_glycemic, pharmacokinetics_absorption, stability_potency, device_performance, other, none`
- `design`: `rct, meta_analysis, systematic_review, review, cohort, case_control, case_crossover, time_series, cross_sectional, pharmacovigilance, human_lab_study, case_series, case_report, lab_bench, other`

## Mapping design → spec §9 evidence tier
| design | tier |
|---|---|
| rct, meta_analysis, systematic_review | 1 RCT / meta-analysis |
| cohort, case_control, case_crossover, time_series, cross_sectional, pharmacovigilance | 2 Population study |
| human_lab_study | 3 Small clinical study |
| case_series | 4 Case series |
| case_report | 5 Case report |
| lab_bench | 6 Lab / bench |
| review (narrative), other | 8 Mechanism / narrative only (not graded as primary evidence) |

## Extraction (included records, spec §8.4 step 5)
From the abstract only: drug, outcome, population, design/tier, heat definition, direction (`harm`, `null`, `protective`, `mixed`, `not_stated`), and effect statistic (type, value, CI). **A number is kept only if it appears verbatim in the abstract**; this is checked by script (`effect_verbatim_check`). Numbers that fail are blanked, never edited.
