# Mappings: how to get from a drug to heat

The challenge (Visualize Challenge 3) asks for evidence linking medications to heat-related outcomes.
This file records the three vocabularies needed for that traversal and where each one lives.

## The traversal

```
DRUG CLASS ──(direct, almost empty)──────────────► HEAT EXPOSURE / HEAT ILLNESS
     │                                                   │
     └──► BRIDGE CONCEPT (physiological effect) ◄────────┘
```

- **Direct path:** a finding with a drug variable on one side and a heat variable on the other. About 6 genuine rows in the CSV; about a dozen with the live API (see F14–F19 in `FINDINGS.md`).
- **Bridge path (two hops):** drug class → concept X, and heat exposure → the same concept X. This is where the evidence is.
- The drug end and the heat end are detected by **variable name**. The bridge node is a **concept**. Reason: see quirk 1 in `DATA.md`.

## Vocabulary 1: heat (source of truth: `scripts/heat_meds_lib.py`)

| Tier | Meaning | Pattern object | Size |
|---|---|---|---|
| `direct` | heat exposure or heat illness: heat wave, heat stroke, heat stress, extreme heat, ambient/air/high temperature, hot weather, summer, hyperthermia, climate change | `HEAT_DIRECT` minus `HEAT_EXCLUDE` | 3,084 findings, 1,981 studies |
| `proxy` | physiology that stands in for heat vulnerability: dehydration, sweating, thermoregulation, core/body/skin temperature, hyponatremia, volume depletion | `HEAT_PROXY` | 2,915 findings, 1,809 studies |

`HEAT_EXCLUDE` removes heat-shock proteins, heat pain, heated tobacco, wheat, hyperthermia therapy, malignant hyperthermia, heating equipment.

Known weaknesses: "summer" and "season" pull in non-heat seasonality; "temperature" patterns catch fever studies;
cold-weather comparisons are included when the name mentions both.
Concepts these variables are grounded to: `reference/heat_concepts.csv`. Core concept IDs:

| Concept | system_id | Wikidata |
|---|---|---|
| extreme heat | `wpUeTjUbAc` | Q69044113 |
| heat stroke | `rYCo7LTyzN` | Q69032838 |
| heat illness | `PtQBvGm5CM` | Q1191065 |
| heat wave | `k9BAffdSqv` | Q215864 |
| heat exhaustion | `2M0TDlEdLk` | Q12643772 |
| hyperthermia | `FDJ4Gulj_Q` | Q242165 |
| urban heat island | `UbF0-c8zHb` | Q215712 |
| air temperature | `mUxSLRMwIy` | Q1160424 |
| temperature (generic, noisy) | `4FaXcuNJRt` | Q11466 |

## Vocabulary 2: medication classes (source of truth: `DRUGS` in `scripts/heat_meds_lib.py`)

24 classes matched on class words and individual drug names. Studies in the graph per class, and raw direct heat matches:

| Class | Studies anywhere | Direct heat studies (raw) | Named in challenge |
|---|---|---|---|
| Diuretics | 1,602 | 2 | yes |
| Beta blockers | 1,885 | 1 | yes |
| ACE inhibitors / ARBs | 2,760 | 2 (1 false) | |
| Calcium channel blockers | 1,336 | 0 | |
| Anticholinergics | 734 | 0 | yes |
| Antipsychotics | 2,257 | 0 | yes |
| Antidepressants | 2,525 | 0 | |
| Lithium | 339 | 1 | yes |
| Insulin (as therapy) | 4,198 | 2 (not therapy-related) | yes |
| SGLT2 inhibitors | 991 | 0 | yes |
| Other diabetes drugs | 2,251 | 0 | |
| Stimulants | 1,642 | 3 (illicit use / overdose) | |
| Antihistamines | 208 | 0 | |
| NSAIDs / analgesics | 3,970 | 5 (fever control) | |
| Opioids / sedatives | 7,188 | 3 (overdose) | |
| Anticonvulsants | 972 | 0 | |

Other classes in the library: antihypertensives (unspecified), psychotropics (unspecified), antiparkinson/dementia drugs,
statins, anticoagulants, inhalers/epinephrine, laxatives/PPIs/alcohol, and a generic "medication use" bucket.

Notes:
- `Insulin (as therapy)` excludes biomarker wording (insulin resistance, fasting insulin, HOMA) via `INSULIN_BIOMARKER`, but leaks remain.
- `Inhalers / epinephrine` is polluted by epinephrine/norepinephrine used as vasopressors or measured as hormones.
- Concepts each class is grounded to, with concept IDs: `reference/drug_concepts.csv`.

## Vocabulary 3: bridge concepts (the middle node)

Two versions exist.

**Hand-picked mechanisms** (`MECH` in `scripts/pathways.py`), matched by name. Studies linking heat exposure to each:

| Mechanism | Heat studies | Strongest drug classes (studies) |
|---|---|---|
| Sweating / body temperature | 61 | NSAIDs 8, antidepressants 4 |
| Acute kidney injury | 14 | Diuretics 76, ACEi/ARB 68, NSAIDs 51, SGLT2 39 |
| Low sodium (hyponatremia) | 5 | Diuretics 30, antidepressants 14, antipsychotics 6 |
| Dehydration / volume loss | 5 | SGLT2 3 |
| Low blood pressure / fainting | 5 | Opioids 29, ACEi/ARB 28, beta blockers 20 |
| Falls | 2 | Opioids 39, antidepressants 14, psychotropics 13 |
| Low blood sugar | 2 | Insulin 366, other diabetes drugs 133, SGLT2 32 |
| Potassium / electrolytes | 1 | Diuretics 45, ACEi/ARB 38, SGLT2 13 |

**Data-driven inventory** (`scripts/bridges.py` → `reference/bridge_concepts.csv`): every concept linked to both a drug
class and heat exposure with at least 2 studies on each arm. 131 distinct concepts for the nine focus classes. It needs
curation because many are confounders or generic nodes rather than mechanisms.

| Keep as candidate bridges | Why |
|---|---|
| acute kidney injury, chronic renal insufficiency, creatinine, potassium, urine | renal / fluid pathway |
| hypotension, arterial/systolic/diastolic blood pressure, cardiac output | haemodynamic pathway |
| cardiovascular disease, myocardial infarction, ischemic stroke, atrial fibrillation, heart arrhythmia | cardiovascular events that heat also raises |
| hypoglycemia, blood glucose | glycaemic pathway (insulin, SGLT2) |
| delirium, suicide, mental depression, schizophrenia | neuropsychiatric pathway (anticholinergics, antipsychotics, lithium) |
| emergency department, cause of death, hospital mortality | outcome nodes |

| Drop | Why |
|---|---|
| body mass index, human body weight, weight gain, woman, man, aged, African Americans, gender identity | covariates and populations, not mechanisms |
| survival rate, survival skill, time, prevalence, incidence, pressure | generic or mis-grounded |
| breast cancer, prostate carcinoma, calcifediol, leptin | co-occurrence, no heat mechanism |

## What a bridge does and does not prove

A bridge says: studies link the drug to X, and other studies link heat to X. The two arms come from **different
populations** (drug arm is mostly hospital cohorts; heat arm is mostly population time-series). It is a hypothesis about
a shared pathway, not evidence of an interaction in one person. Any visual must label it that way.

## Not covered by the graph

- Drug storage and stability in heat: 1 finding (refrigerated vs non-refrigerated insulin).
- Drug absorption changes in heat: none found.
- Wearables with medication and heat: not searched systematically; none seen in the direct matches.
- Prescriber specialty: not in the data. Must be assigned by us per drug class.
- Heat-health guidance documents: not in the data. Must be collected separately.

## Direct evidence by action bucket (as of 2026-11-14)

The brief's four buckets, with the best grounded direct finding we hold for each. Abstract-checked unless marked.

| Bucket | Best direct finding | Source |
|---|---|---|
| Substitution / temporary holding | Anticholinergics OR 6.0, antipsychotics OR 4.6, anxiolytics OR 2.4 for heat-related admission (France 2003) | PMID 17513091, API |
| Substitution / holding | Long-term antihypertensives, HR 2.17 for death in heatstroke (Lyon 2003) | PMID 17698677, CSV |
| Closer monitoring | Drug-induced hyponatremia reports rise with temperature, OR 2.21 | PMID 28737683, API |
| Closer monitoring | Lithium dose-to-level ratio vs daily temperature, coef −0.17, p=0.08 (unchecked) | DOI 10.1002/hup.2413, CSV |
| Closer monitoring | Serum potassium peaks in winter and troughs in summer, and potassium/ACE-inhibitor prescribing shifts with it (the extracted RRs are not heat effects, see C16) | PMID 37280056, API |
| Dose adjustment | Insulin absorbed 50–60% faster at 35 °C than 20 °C | PMID 7010077, API |
| Dose adjustment | Insulin users aged 65+: serious hypoglycemia OR 1.38 on days above the 99th heat-index percentile, about 2M US users | PMID 38060348, CSV |
| Substitution / holding | "Persons under medication" aOR 3.09 for heat illness (Odisha, India) | PMID 31842287, CSV |
| Storage / stability | Refrigerated vs non-refrigerated insulin mixture: earlier and higher peak when refrigerated, 7 patients | PMID 3069528, CSV |

Everything else for these buckets comes from the bridge path.

## Third route: drug in the study population (added 2026-11-14)

Some heat findings have no drug in either variable name but study a population defined by a medication
("adults aged 65 and older who use insulin"). Find them by applying `drug_classes()` to `studies.population_string`
for rows with a direct-tier heat variable. This is direct evidence, not a bridge. Two usable studies so far (F21, F22).

## Direction of the drug arm (added 2026-11-14)

A drug → effect arm is only a hazard pathway if the findings point the harmful way. Check the share of ratio rows
whose CI sits above 1 before drawing it (F24, C18). SGLT2 inhibitors → AKI is mostly protective; use ketoacidosis and
volume depletion for that class.

## HeatRx evidence base (added 2026-11-14, phase 1)

Source of truth: `scripts/heat_meds_lib.py` (`FOCUS`, `MEMBERS`, `HUBS`, `EFFECTS`, `env_heat()`, `direction()`) and
`scripts/evidence.py`. Output: `bundle/evidence.json`, row-level CSVs in `data/derived/evidence/`.

### 16 drug classes
`FOCUS` maps each app id to a `DRUGS` key: diuretics, beta_blockers, acei_arb, ccb, anticholinergics, antipsychotics,
antidepressants, lithium, insulin, sglt2, other_diabetes, anticonvulsants, nsaids (includes acetaminophen and
aspirin), opioids_sedatives (includes benzodiazepines and hypnotics), stimulants (includes cocaine, amphetamine,
MDMA), antihistamines. `MEMBERS` lists generic drug names per class for search and the medication review.

### Body systems (hubs) and effects

| Hub | Effects (ribbon-map nodes) |
|---|---|
| Heat illness | heat_illness: heat stroke, heat illness/exhaustion, hyperthermia, neuroleptic malignant syndrome, serotonin syndrome |
| Brain | confusion: delirium, confusion, cognitive impairment, altered mental status (hepatic encephalopathy excluded) |
| Heart and blood pressure | low_bp: hypotension, syncope, orthostatic; heart_rhythm: arrhythmia, QT, torsade, AF, VF/VT, cardiac arrest, sudden death |
| Kidney | kidney: acute kidney injury, acute renal failure, nephrotoxicity |
| Sodium and potassium | sodium: hyponatremia; potassium: hyper/hypokalemia, serum potassium |
| Blood sugar | low_sugar: hypoglycemia; ketoacidosis: DKA, hyperglycemic emergencies, hyperosmolar state |
| Fluid loss | fluid_loss: dehydration, hypovolemia, volume depletion |
| Falls | falls: falls, hip fracture |

Curated-only effects: drug_level (hub kidney; lithium), storage (no hub), overdose (no hub; drug use, not prescribing).
Effects are matched after removing qualifiers in brackets and text after "among / in patients with / patients with",
so "mortality (among patients with atrial fibrillation)" is not counted as a heart-rhythm outcome.
Not included as effects: myocardial infarction and stroke, psychiatric admissions, chronic kidney disease.

### Rules
- **Drug arm:** a focus-class variable on one side; an effect on the other side, which must not itself name a drug or a
  heat variable; the drug-side name must not itself name an effect ("thiazide-induced hyponatremia" → fracture is skipped).
- **Heat arm:** an environmental-heat variable (`env_heat()`: heat-tier, not cold, not clinical hyperthermia or patient
  body temperature, and matching explicit weather/heat wording) on one side, an effect on the other, no drug on either side.
  Includes API-only rows from `data/api/heat_associations.csv`, tagged.
- **Animal studies** (names or population) are dropped from both arms.
- **Direction** (`direction()`): ratio statistics with a CI only; raised if the lower bound > 1, lowered if the upper
  bound < 1, else unclear; other statistics are `not_ratio`. A study counts as raised if any of its rows is raised.
- **Tiers** per class × effect: `direct` (a curated direct finding, prescribed use; `direct_scope` says if it was a
  class, a group such as "antihypertensives", or medication in general); `shared` (drug arm ≥ 3 raised studies and more
  raised than lowered; heat arm ≥ 2 studies with ≥ 1 explicitly-high-heat study not pointing the protective way);
  `direct_misuse` (drug use or overdose); `weak` (everything else, kept in the bundle but not drawn by default).
- **Direct evidence** (routes 1 and 3) is hand-curated in `reference/direct_evidence.csv` from the candidate lists in
  `data/derived/evidence/direct_candidates.csv`; excluded candidates stay in the file with the reason.
  Heat-level bands for a finding go in `reference/direct_levels.json`.
- **Corrections** to graph labels found by abstract checks are in `reference/corrections.csv` and attached to every
  bundled finding with that PMID.

## Guidance coding (added 2026-11-14, phase 2)

- `reference/guidance/documents.csv`: one row per document (publisher, year, URL, audience, how much was read,
  what it says about its own evidence, timing).
- `reference/guidance/class_mentions.csv`: one row per document × class × effect. `named_as` and `mechanism` keep the
  document's wording (short, paraphrased where long); `effect` is our mapping onto the HeatRx effects. Group names are
  expanded: "all antihypertensives" → diuretics, beta blockers, ACEi/ARBs, CCBs; "psychotropics" → antipsychotics and
  antidepressants (plus opioids/sedatives where the document says anxiolytics or hypnotics); TCAs and SSRIs/SNRIs →
  antidepressants; anti-Parkinson and bladder antimuscarinics → anticholinergics; gliptins, GLP-1 agonists, biguanides,
  sulfonylureas, metformin → other diabetes drugs; topiramate, oxcarbazepine, carbamazepine → anticonvulsants.
  A blank effect means the document lists the class without a mechanism.
- `reference/guidance/actions.csv`: one row per recommended action, with bucket (`hold_swap`, `adjust_dose`,
  `monitor`, `storage`, `counsel`), scope (`class` or `general`), the classes named, timing and section.
- `reference/effect_actions.csv`: for each body effect, the bucket(s) guidance points to and which documents support
  it. Rows with no documents are our inference and are labelled as such. Heart rhythm has no action.
- A class's action buckets = its class-specific actions plus the effect-derived actions of its drawn links.
