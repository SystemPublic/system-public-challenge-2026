# openFDA: FAERS heat-reaction signals + FDA label heat audit

**Accessed:** 2026-11-14 (openFDA `meta.last_updated` = 2026-10-28). No API key.
**Label everything from FAERS: "warning signal, not proof."**

## Files

| File | What |
|---|---|
| `scripts/openfda_common.py` | Cached GET helper (gzip cache here in `cache/`), ingredient list with roles |
| `scripts/faers_heat_signals.py` | FAERS disproportionality + seasonality |
| `scripts/fda_label_heat_audit.py` | Label text audit |
| `data/raw/openfda/cache/*.json.gz` | Every API response (key = sha1 of URL; each file stores the URL and fetch time). Reruns cost 0 calls |
| `data/raw/openfda/call_log.tsv` | Every network call: time, HTTP status, URL (about 560 calls in total) |
| `data/raw/openfda/hidden_candidate_terms.csv` | Hand mapping of the other agent's hidden-drug candidates to generic names (see Step 2) |
| `data/raw/openfda/label_audit_summary.txt` | Headline text for the label audit |
| `data/processed/faers_heat_signals.csv` | One row per drug (or pooled class) and event: n, 2x2 margins, ROR, 95% CI, signal flags |
| `data/processed/faers_heat_seasonality.csv` | Month-of-year counts of heat reports per drug, both composites, plus the all-drug background |
| `data/processed/fda_label_heat_audit.csv` | One row per label and hit category: set_id, effective_time, section, verbatim snippet |
| `data/processed/fda_label_heat_audit_summary.csv` | One row per ingredient: labels found and audited, counts per tier, best tier, 3-way class, example snippet |

Rerun: `~/.local/bin/uv run python scripts/faers_heat_signals.py --extra data/raw/openfda/hidden_candidate_terms.csv` and `~/.local/bin/uv run python scripts/fda_label_heat_audit.py`. Everything comes from the cache.

## 1. FAERS disproportionality (`https://api.fda.gov/drug/event.json`)

**Drug field:** `patient.drug.openfda.generic_name:"<ingredient>"`. This is a tokenised phrase match, so it also catches salts and combination products (e.g. `lisinopril` matches "LISINOPRIL AND HYDROCHLOROTHIAZIDE"). It counts the drug in **any role** (suspect, concomitant or interacting).
- *Why not primary suspect (`drugcharacterization:1`)?* openFDA search does not tie fields inside the same `patient.drug[]` element together. A query like `drugcharacterization:1 AND generic_name:X` matches any report where *some* drug is suspect and X is present *anywhere*. It cannot restrict to "X is the suspect", so we did not pretend to.
- Only reports that openFDA harmonised (the `openfda` block filled in) are counted. Reports that name the drug only in free-text `medicinalproduct` are missed.

**Reactions (MedDRA PTs, `patient.reaction.reactionmeddrapt.exact`):**
- Heat PTs: HEAT STROKE, HYPERTHERMIA, HEAT EXHAUSTION, HEAT ILLNESS, BODY TEMPERATURE INCREASED, ANHIDROSIS, HYPOHIDROSIS
- Fluid/kidney PTs: DEHYDRATION, HYPONATRAEMIA, ACUTE KIDNEY INJURY
- **HEAT COMPOSITE SPECIFIC (primary):** HEAT STROKE, HEAT EXHAUSTION, HEAT ILLNESS, ANHIDROSIS, HYPOHIDROSIS
- **HEAT COMPOSITE BROAD:** all 7 heat PTs. *Do not headline this one.* 20,423 of its 31,676 reports are BODY TEMPERATURE INCREASED (mostly fever) and 7,642 are HYPERTHERMIA (largely NMS, serotonin syndrome or malignant hyperthermia). On the broad composite all 3 negative controls came out "positive" (amoxicillin ROR 1.74, levothyroxine 1.52, atorvastatin 1.19). That is why we built the specific composite.

**Query templates (spaces URL-encoded as %20):**
```
total reports:          /drug/event.json?limit=1                                   -> meta.results.total
drug total:             ?search=patient.drug.openfda.generic_name:"furosemide"&limit=1
per-PT among drug:      ?search=<drug> AND patient.reaction.reactionmeddrapt.exact:("HEAT STROKE" "HYPERTHERMIA" ... "ACUTE KIDNEY INJURY")
                         &count=patient.reaction.reactionmeddrapt.exact&limit=999
  (limit=1000 returns 403 API_KEY_MISSING without a key. If the 999-term list was full and a PT was missing,
   the script asked directly: ?search=<drug> AND ...exact:"<PT>"&limit=1)
composite + seasonality:?search=<drug> AND patient.reaction.reactionmeddrapt.exact:("HEAT STROKE" "HEAT EXHAUSTION" "HEAT ILLNESS" "ANHIDROSIS" "HYPOHIDROSIS")
                         &count=receivedate      (daily counts; their sum = distinct reports)
background:             the same queries without <drug>
pooled class:           <drug> = (generic_name:"a" generic_name:"b" ...)   (OR)
```

**Background counts (2026-11-14):** N_total = 21,054,159 reports. HEAT STROKE 1,524; HYPERTHERMIA 7,642; HEAT EXHAUSTION 806; HEAT ILLNESS 675; BODY TEMPERATURE INCREASED 20,423; ANHIDROSIS 408; HYPOHIDROSIS 501; DEHYDRATION 133,521; HYPONATRAEMIA 56,386; ACUTE KIDNEY INJURY 153,188. Specific composite 3,850; broad composite 31,676.

**Math:** a = drug & event; b = drug total − a; c = event total − a; d = N − a − b − c. ROR = (a/b)/(c/d); 95% CI = exp(ln ROR ± 1.96·√(1/a+1/b+1/c+1/d)).
- `signal = yes` if a ≥ 3 and the lower CI is above 1.
- `above_neg_control_band = yes` if the row is a signal **and** its lower CI is above the highest upper CI any negative control reached for that event. For the specific composite that cut-off is **1.734** (atorvastatin).

**Drugs:** 48 ingredients.
- Study: 33 ingredients across the 15 classes.
- Positive controls: 12 (anticholinergics, antipsychotics, topiramate/zonisamide).
- Negative controls: 3 (amoxicillin, levothyroxine, atorvastatin).
- Hidden candidates: 15 (Step 2).
- Plus 15 pooled-class rows. The full list is in `openfda_common.INGREDIENTS`.
- Specific products: epinephrine counts *all* epinephrine reports, not only auto-injectors. Fentanyl is all forms, not only patches. "amphetamine" catches the mixed amphetamine salts but not dextroamphetamine-only products. "insulin" pools all insulins.

### Results: specific heat composite (warning signal, not proof)

**Positive controls behaved.**
- 11 of 12 positive-control ingredients signal. Haloperidol is the exception: n = 7, ROR 1.45 [0.69–3.05].
- 8 of 12 clear the negative-control band.

| Drug | n | ROR [95% CI] |
|---|---|---|
| Topiramate | 174 | 17.4 [14.9–20.2] |
| Zonisamide | 12 | 6.1 [3.5–10.8] |
| Anticholinergics, pooled | 59 | 5.6 [4.3–7.2] |
| Antipsychotics, pooled | 292 | 2.9 [2.6–3.3] |

Topiramate is also the strongest single-PT result: HYPOHIDROSIS ROR 39.7 (n = 49) and HEAT STROKE ROR 27.2 (n = 105).

**Negative controls mostly behaved.**
- Amoxicillin: 0.87 [0.51–1.50], no signal.
- Levothyroxine: 1.10 [0.85–1.41], no signal.
- Atorvastatin: 1.35 [1.05–1.73], a weak "signal". This most likely reflects confounding by age and polypharmacy, and it shows the noise floor. Treat RORs below about 1.7 as indistinguishable from background.

**Study drugs.**
- 18 of 33 ingredients signal.
- 6 clear the negative-control band (n, ROR [95% CI]):
  - lithium: 34, 4.37 [3.12–6.13]
  - sertraline: 167, 4.26 [3.65–4.97]
  - citalopram: 89, 3.61 [2.92–4.45]
  - lisdexamfetamine: 25, 3.88 [2.62–5.76]
  - propranolol: 37, 2.79 [2.02–3.86]
  - valsartan: 102, 2.32 [1.91–2.83]
- Pooled classes:

| Class | ROR [95% CI] | Flag |
|---|---|---|
| SSRIs | 2.83 [2.53–3.18] | above band |
| SGLT2 inhibitors | 2.10 [1.64–2.69] | signal |
| Thiazides | 1.96 [1.58–2.44] | signal |
| ADHD stimulants | 1.82 [1.38–2.41] | signal |
| ACEi/ARBs | 1.49 [1.31–1.71] | signal |
| Beta blockers | 1.36 [1.16–1.58] | signal |
| Loop diuretics | 1.19 [0.97–1.45] | no signal |
| Fentanyl/buprenorphine | 0.46 [0.30–0.71] | no signal |
| Insulin | 0.61 [0.47–0.80] | no signal |

  Metformin is a single ingredient: 1.66 [1.39–1.97], signal. Epinephrine (single ingredient): 1.76 [1.28–2.44], signal.
- **No FAERS heat signal does not mean safe.**
  - The fentanyl patch risk is *dose dumping*, which is reported as overdose or respiratory depression, not heat stroke.
  - Insulin risk is reported as hypoglycaemia.
  - Loop diuretic risk shows up under DEHYDRATION (ROR 3.6), HYPONATRAEMIA (6.0) and ACUTE KIDNEY INJURY (7.8).

**Fluid/kidney PTs** (DEHYDRATION, HYPONATRAEMIA, ACUTE KIDNEY INJURY) signal for almost everything, including all 3 negative controls (amoxicillin AKI ROR 7.9). They are dominated by background reporting in older, sicker patients. Use them only to compare drugs with each other, never as "heat evidence".

**Seasonality** (`faers_heat_seasonality.csv`, month of FDA `receivedate`, *not* the event date): 38.9% (1,496 of 3,850) of all specific-composite heat reports arrive in June to August, against 25% if spread evenly. So the reaction set is seasonal. Per-drug June–August shares are noisy when n is small; for example lithium is 14 of 34 (41%).

## 2. Hidden-drug candidates (`data/processed/system_hidden_drug_candidates.csv`)

The file existed by the time Step 1 finished. It holds 263 concept rows, labelled "UNVALIDATED raw candidate". Many are not drugs (e.g. "body surface area", "endovascular aneurysm repair"). I hand-mapped the top-ranked outpatient drug concepts that are **not** in our 15 to generic names. The mapping is in `hidden_candidate_terms.csv`, together with each concept's source rank:
- NSAIDs (ibuprofen, naproxen)
- PPIs (omeprazole, pantoprazole)
- simvastatin
- aspirin
- calcineurin inhibitors (tacrolimus, cyclosporine)
- trimethoprim
- tramadol
- desmopressin
- allopurinol
- spironolactone
- benzodiazepines (lorazepam, alprazolam)

I skipped inpatient-only concepts (vancomycin, piperacillin/tazobactam, vasopressors, hydroxyethyl starch, aprotinin).

**Result on the specific composite:**
- 7 of 15 signal: ibuprofen 1.54, naproxen 1.52, omeprazole 1.22, simvastatin 1.29, allopurinol 1.42, lorazepam 1.58, alprazolam 1.41.
- **None clear the negative-control band** (all lower CIs are below 1.73).
- The NSAID and benzodiazepine pooled classes signal at about 1.5.
- So FAERS gives **no strong confirmation** of any hidden candidate. The pathways may still be real (NSAIDs and AKI, for example), but FAERS heat PTs don't add evidence beyond the background.

## 3. FDA label audit (`https://api.fda.gov/drug/label.json`)

**Query per ingredient (1 call each, 48 calls):**
`search=openfda.generic_name:"<ingredient>" AND openfda.product_type:"HUMAN PRESCRIPTION DRUG"&sort=effective_time:desc&limit=25`

Overrides:
- fentanyl and buprenorphine: `AND openfda.route:"TRANSDERMAL"`
- epinephrine: `openfda.generic_name.exact:"EPINEPHRINE" AND openfda.route:"INTRAMUSCULAR"`, to target auto-injectors

**Selection:**
- Combination labels (generic name containing " AND ") are dropped when a single-ingredient label exists.
- Near-duplicate texts (relabelers) are collapsed.
- Up to the 10 most recently updated distinct labels are audited per ingredient: 463 labels in total.

**Sections scanned:** boxed_warning, warnings_and_cautions, warnings, precautions, adverse_reactions, patient_counseling_information, information_for_patients, spl_patient_package_insert, spl_medguide, instructions_for_use, storage_and_handling, how_supplied.

**Sentence classification** (regexes are in the script):
- **heat warning:** explicit heat, hot weather, heat stroke or exhaustion, external heat sources, body-temperature regulation, or reduced sweating, in a clinical (non-storage) sentence.
- **incidental:** heat terms that appear only as a sign or differential. Examples: "hyperthermia" in serotonin-syndrome or NMS lists, "heat stroke" in the NMS differential diagnosis, heat terms only inside adverse_reactions listings, "heat intolerance" as a symptom.
- **sweating/dehydration only:** indirect, e.g. "volume depletion".
- **storage temperature only:** includes product-protection lines such as "keep away from heat", "do not expose to extreme heat", and a pump "exposed to sunlight or direct heat".
- **nothing.**

An ingredient's tier is the **best tier found on any** audited label. This is generous to FDA, so it makes the "no warning" claim conservative.

### Headline

**29 of 45 heat-risk ingredients (64%) carry no explicit heat warning on any of their current audited labels. By class, 8 of 15 classes have no ingredient with one.**

Three-way split (45 heat-risk ingredients):

| Split | Count | Ingredients |
|---|---|---|
| Heat warning | 16 | lithium, hydrochlorothiazide, chlorthalidone, empagliflozin, oxybutynin, benztropine, trihexyphenidyl, olanzapine, haloperidol, risperidone, quetiapine, aripiprazole, topiramate, zonisamide, fentanyl (patch), buprenorphine (patch) |
| Storage temperature only (no clinical heat warning) | 29 | all the rest. Every audited label has storage text, so this 3-way "nothing" bin is empty |
| Nothing | 0 | – |

Detail for the 29 without a heat warning:

| Tier | Count | Ingredients |
|---|---|---|
| Heat or hyperthermia mentioned only incidentally | 8 | clozapine, sertraline, fluoxetine, citalopram, escitalopram, paroxetine, amphetamine, lisdexamfetamine |
| Sweating/dehydration only | 18 | furosemide, bumetanide, torsemide, indapamide, lisinopril, enalapril, ramipril, losartan, valsartan, olmesartan, dapagliflozin, canagliflozin, insulin, metformin, methylphenidate, metoprolol, carvedilol, epinephrine |
| Storage only | 3 | tolterodine, propranolol, atenolol |

Classes with no ingredient carrying a heat warning: loop diuretics, ACEi/ARBs, insulin, metformin, SSRIs, ADHD stimulants, beta blockers, epinephrine auto-injectors.

Negative controls: 0 of 3 carry a heat warning. Levothyroxine lists "heat intolerance" as an overdose symptom (incidental).

### Notes for using the audit

- **Some "heat warnings" are weak or technical.** The hydrochlorothiazide and chlorthalidone hit is "Dilutional hyponatremia may occur in edematous patients in hot weather". The empagliflozin hit appears only on 1 of 9 labels ("fluid losses (such as … excessive heat exposure)"). Haloperidol: "Hyperpyrexia and heat stroke … have also been reported".
- **Strong, patient-relevant warnings:**
  - fentanyl and buprenorphine patches: boxed or W&P warnings on external heat
  - the antipsychotic "Body Temperature Regulation" section
  - oxybutynin: "heat prostration (fever and heat stroke due to decreased sweating)"
  - topiramate and zonisamide: oligohidrosis and hyperthermia
  - trihexyphenidyl: "in hot weather"
  - lithium Medication Guide: "Avoid becoming overheated or dehydrated during exercise and in hot weather"
- **Insulin and epinephrine** labels mention heat only to protect the *product* ("Keep away from heat", "Do not expose to extreme heat"). They don't warn that heat changes the patient's risk.
- **Clozapine**: none of the 10 audited labels has the "Body Temperature Regulation" section that other antipsychotic labels carry. Heat stroke appears only in its NMS differential.
- **Tolterodine** (an anticholinergic): no heat or sweating language was found on any of its 10 audited labels.

## Caveats (say these out loud)

**FAERS:**
- Spontaneous reports, with no exposure denominator.
- Duplicates, stimulated reporting, and confounding by indication, age and polypharmacy.
- Any-role drug matching.
- receivedate is not the onset date.
- A ROR measures reporting disproportionality, not risk. Warning signal, not proof.

**Label audit:**
- Regex text matching on openFDA SPL JSON, with a sample of up to 10 recent labels per ingredient (not every label).
- Section boundaries are as openFDA parses them.
- Generic-manufacturer labels can differ from the reference listed drug label.
- This is a text check, not a regulatory review.
- Snippets are verbatim from openFDA but should be spot-checked against DailyMed (by set_id) before being quoted publicly.

---

## v2 (keyed) run — 2026-11-14, actually run WITHOUT a key

**The key could not be used.** `OPENFDA_API_KEY` in `.env.local` is malformed (inline text and whitespace on the line); openFDA answered `403 API_KEY_INVALID`. Everything below ran keyless (1,000 calls/day). About 360 new network calls were made (call_log.tsv now has 924 rows for the day). `openfda_common.use_api_key_from_env()` and the `--api-key-from-env` flag on both v2 scripts are in place for when a valid 40-character key is saved. The key is only appended to the outgoing request: cache keys, cache files, call_log.tsv and error messages always use the key-free URL (checked: no `api_key` anywhere on disk). A keyed rerun reuses this cache and costs 0 calls.

New files (v1 outputs untouched):

| File | What |
|---|---|
| `scripts/fda_label_heat_audit_v2.py` | Audits **every** current Rx label per ingredient; verifies claims (a)–(c) |
| `scripts/faers_heat_signals_v2.py` | Specific-composite robustness: strata, suspect-role numerator, extra class members |
| `data/processed/fda_label_heat_audit_v2.csv` | One row per label (5,938 labels incl. negative controls): set_id, version, effective_time, manufacturer, combination flag, tier, verbatim snippet per category |
| `data/processed/fda_label_heat_audit_summary_v2.csv` | One row per ingredient: n labels, n/% with heat warning, distinct texts, coverage class, combination-label results |
| `data/processed/fda_label_heat_claims_v2.csv` | Every sentence behind claims (a)–(c), with set_id and field |
| `data/raw/openfda/label_audit_summary_v2.txt` | Headline text |
| `data/processed/faers_heat_signals_v2.csv` | One row per unit × stratum (specific composite) |

### Label audit v2: all labels

**Method:**
- Same queries, route overrides and sentence classifier as v1, but paged through all results (limit=300). That is 4,942 labels for the 45 heat-risk ingredients and 996 for the negative controls, de-duplicated by set_id.
- openFDA keeps one current version per set_id. Labels without an `openfda` block (not harmonised) cannot be found by `openfda.generic_name` and are missed.
- Large label pages are compacted before caching: the 12 audited sections are kept in full, and every other field keeps only its heat, temperature or sweat sentences (cache key suffix `#label-compact-v2`).

**Changes from v1:**
- The primary denominator is single-moiety labels. A label counts as a combination only if its generic name names another moiety; separators are `,`, `/`, ` AND ` and ` WITH `. So mixed amphetamine salts and premixed insulins now count as single-moiety. "LISINOPRIL/HCTZ" counts as a combination.
- Fix: "dehydrated alcohol" (an excipient) no longer counts as dehydration. v1 did not hit this, but v2 did on one tolterodine label.

**Headline: 28 of 45 heat-risk ingredients (62%) carry no explicit heat warning on *any* of their current single-moiety labels.** v1 said 29 of 45 from a ≤10-label sample. The one change is **methylphenidate**: 3 of its 82 labels carry a warning. All 3 are the transdermal patch (Daytrana and its generics), with the warning "avoid exposing the … application site to direct external heat sources". Oral methylphenidate labels have none.

By class, **7 of 15 classes have no ingredient with a heat warning on any label**: loop diuretics, ACEi/ARBs, insulin, metformin, SSRIs, beta blockers and epinephrine auto-injectors. ADHD stimulants dropped off this list because of the patch.

| Coverage (single-moiety labels) | n | Ingredients (labels with warning / labels) |
|---|---|---|
| Warning on most labels (>50%) | 14 | lithium 30/59 (51%, just over half), hydrochlorothiazide 146/155, chlorthalidone 77/81, oxybutynin 83/86, benztropine 35/35, olanzapine 105/105, haloperidol 98/111, risperidone 72/73, quetiapine 156/156, aripiprazole 124/125, topiramate 157/161, zonisamide 32/33, fentanyl patch 5/5, buprenorphine patch 7/7 |
| Warning on some labels (≤50%) | 3 | empagliflozin 1/8, trihexyphenidyl 4/12, methylphenidate 3/82 (patch only) |
| Warning on no label | 28 | furosemide 0/152, bumetanide 0/74, torsemide 0/34, indapamide 0/13, lisinopril 0/159, enalapril 0/69, ramipril 0/38, losartan 0/143, valsartan 0/69, olmesartan 0/81, dapagliflozin 0/30, canagliflozin 0/5, insulin 0/55, metformin 0/327, tolterodine 0/18, clozapine 0/16, sertraline 0/167, fluoxetine 0/168, citalopram 0/89, escitalopram 0/115, paroxetine 0/94, amphetamine 0/78, lisdexamfetamine 0/32, metoprolol 0/349, propranolol 0/143, atenolol 0/99, carvedilol 0/125, epinephrine (IM) 0/55 |

Negative controls: 0 of 774 single-moiety labels carry a heat warning.

**Combination labels inherit thiazide text.** Lisinopril/HCTZ (70 labels) and atenolol/chlorthalidone (9) carry the thiazide line "Dilutional hyponatremia may occur in edematous patients in hot weather". That line is about the thiazide, not the ACEi or beta blocker.

**Pitch claims, checked across the whole label text (every openFDA field):**
- **(a) Insulin and epinephrine mention heat only for product storage. CONFIRMED.**
  - Insulin: 61 labels, 58 mention heat. Epinephrine (IM): 55 labels, 23 mention heat. Every one of those sentences is product protection, for example:
    - "Keep away from heat and light." (insulin, e.g. set_id 2be14cbb-197a-4da8-82c8-2443594e7f6f)
    - "Keep NovoLog away from heat or light." (13891e5a-e57a-46e8-911c-2f680352b52b)
    - "Do not expose to extreme cold or heat." (epinephrine, 04f07f15-55e2-411b-abb8-07eab37f5664)
    - "If the device has been in extreme cold or heat, the EpiPen should be replaced." (311af6d9-20c0-4b87-b236-4185bfa49988)
  - The closest any label comes to more is the insulin pump line "The temperature of the insulin may exceed ambient temperature when the pump housing, cover, tubing or sport case is exposed to sunlight or radiant heat" (2be14cbb-…). It is still about the insulin degrading, not about the patient's heat risk.
- **(b) No clozapine label has the "Body Temperature Regulation" section. CONFIRMED: 0 of 16 labels.**
  - The atypical comparators carry it on nearly every label: olanzapine 109/109, quetiapine 156/156, risperidone 72/73, aripiprazole 124/125. Example: olanzapine 002dd00f-7946-ea4f-e063-6294a90a5916, "5.13 Body Temperature Regulation Disruption of the body's ability to reduce core body temperature has been attributed to antipsychotic agents."
  - Haloperidol (0/111) does not have the section either; it uses "Hyperpyrexia and heat stroke … have also been reported" instead.
  - Clozapine's only heat language is NMS-related, on all 16 labels: "Clinical manifestations of NMS include hyperpyrexia…" and "…other serious medical conditions (e.g., severe neutropenia, infection, heat stroke, …)" (e.g. 09231d80-6343-4a34-bd5b-100c547fd3c9, and Clozaril 90876802-0e3a-44c9-9ff7-1754dfbe736a).
- **(c) No tolterodine label mentions heat or sweating. CONFIRMED: 0 of 18 labels**, including Detrol 41eb00d2-64e3-4ec9-8732-4bfc81b04180. Their only temperature text is storage.

The full set_id list is in `fda_label_heat_claims_v2.csv` and `fda_label_heat_audit_v2.csv`. Spot-check on DailyMed with `https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=<set_id>`.

### FAERS v2: robustness of the specific heat composite (warning signal, not proof)

**Method:**
- All 3,850 specific-composite reports were downloaded (4 calls). Numerators are counted locally with the same phrase match on `patient.drug[].openfda.generic_name` that the API uses.
- **Validation:** local counts match v1's API counts for all 63 v1 units, and the local stratum totals match the API stratum totals (2,839 / 754 / 204).
- Denominators and the background come from API totals restricted the same way. The negative-control cut-off is recomputed within each stratum.

**(a) Suspect-only.**
- **The denominator cannot be restricted to suspect-only.** openFDA does not tie `drugcharacterization` to a particular drug, and it silently ignores `NOT`. With `NOT patient.drug.drugcharacterization:(2 3)`, N stayed at 21,054,159 and sertraline stayed at 222,021, so that stratum was dropped.
- What is possible from the downloaded reports:
  1. The share of each drug's heat reports in which *that drug's own entry* is suspect (`pct_cases_drug_suspect`).
  2. A conservative ROR. The numerator counts suspect-role reports only, but the denominator still counts any role, which biases the ROR toward and below 1. The negative controls fall to 0.20–0.27 under this definition, so a lower CI > 1 here is a strong result.
- **Still signal (lower CI > 1):**

  | Drug | n | ROR [95% CI] | Suspect share |
  |---|---|---|---|
  | lithium | 15 | 1.92 [1.16–] | 44% |
  | sertraline | 95 | 2.37 [1.94–] | 57% |
  | citalopram | 44 | 1.76 [1.31–] | 49% |
  | lisdexamfetamine | 19 | 2.95 [1.88–] | 76% |
  | valsartan | 69 | 1.56 [1.23–] | 68% |
  | dapagliflozin | 20 | 1.72 [1.11–] | 80% |

  Also still signal: the SSRI and SGLT2 classes, and every positive control except haloperidol and quetiapine.
- **Collapses:** propranolol (only 5 of 37 reports, 14%, name it as suspect; 0.37) and metformin (29%; 0.47). Their v1 signals look like bystander/confounding signals.

**(b) Reports received 2015 or later** (N = 16.06M, 2,839 heat reports, cut-off 1.86).
- All 6 v1 study drugs above the band stay above it:

  | Drug | ROR [lower CI] |
  |---|---|
  | lithium | 4.55 [2.99] |
  | sertraline | 5.50 [4.67] |
  | citalopram | 3.85 [2.99] |
  | lisdexamfetamine | 4.01 [2.61] |
  | propranolol | 3.10 [2.17] |
  | valsartan | 2.37 [1.90] |

- **Hydrochlorothiazide joins them:** 2.46 [1.89].

**(c) Age subgroups.**
- **65+** (N = 4.29M, 754 heat reports, cut-off 1.87). Above the band:

  | Drug | n | ROR [lower CI] |
  |---|---|---|
  | sertraline | 24 | 3.11 [2.07] |
  | paroxetine | 8 | 4.00 [1.99] |
  | valsartan | 33 | 2.66 [1.87], borderline |

  - Also above it: oxybutynin 8.38, risperidone 9.13, topiramate, and the anticholinergic pool.
  - Signal but below the band: dapagliflozin 3.08 [1.65], the SGLT2 class 2.50 [1.62], ramipril, atenolol, the ACEi/ARB pool, and the SSRI pool 1.78 [1.30].
  - **Lithium (n = 1) and citalopram (n = 3) lose their signal in 65+.**
- **Under 18** (N = 0.81M, 204 heat reports).
  - Uninformative. The cut-off is 8.6 because the controls have n ≤ 1.
  - Only topiramate (30 reports, 29.8), benztropine and the anticholinergic pool clear it.
  - Citalopram 9.51 [5.03] (n = 10) and valsartan (n = 3) are nominal signals.

**(d) Extra individual members of the 15 classes**, all reports only (54 more ingredients; restricted strata not run, to save calls).
- **Above band:**

  | Drug | n | ROR [lower CI] |
  |---|---|---|
  | sacubitril | 50 | 2.37 [1.79] |
  | glycopyrrolate | 18 | 13.0 [8.2] |
  | solifenacin | 5 | 14.3 [6.0] |
  | fesoterodine | 11 | 5.6 [3.1] |
  | chlorpromazine | 11 | 8.4 [4.6] |
  | lurasidone | 15 | 3.9 [2.4] |
  | paliperidone | 28 | 2.9 [2.0] |
  | fluvoxamine | 3 | 6.7 [2.2] |
  | insulin glulisine | 7 | 3.8 [1.8], small and odd |

- **Caution on valsartan:** sacubitril/valsartan (Entresto) accounts for 50 of valsartan's 102 heat reports. The valsartan signal is substantially an Entresto (heart-failure population) signal.
- No signal: other ARBs/ACEis, other insulins, dextroamphetamine, bisoprolol and the other beta blockers.
- 16 extras have 0 heat reports. "insulin detemir" returned 0 drug reports, so the query term is likely mismatched.

**Updated FAERS take-away.** The SSRI signal (especially sertraline) is the most robust study-drug result: it holds after 2015, in 65+, and with a suspect-only numerator. Lithium, citalopram and lisdexamfetamine are robust overall but thin in 65+. The propranolol and metformin signals don't survive the suspect check. Warning signal, not proof.
