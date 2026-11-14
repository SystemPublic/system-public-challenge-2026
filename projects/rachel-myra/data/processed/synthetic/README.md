# Synthetic patient panel (SBH catchment, Bronx)

**Every record here is SYNTHETIC.** No real patient data. Names are Synthea-style (`Rosa412 Quintero877`), phone numbers come from the fictional 555-01xx block, and homes are random points inside a ZIP polygon, not addresses. The CSVs have a `synthetic=true` column. FHIR resources carry the `https://example.org/fhir/StructureDefinition/synthetic` extension (`valueBoolean: true`) and `meta.tag` HTEST.

Generator: `scripts/generate_synthetic_panel.py`. Its docstring lists every assumption (A1–A17). It is deterministic: seed `20261114` plus the cached files in `sources/` give byte-identical output.

```bash
~/.local/bin/uv run --with certifi python scripts/generate_synthetic_panel.py            # from cache
~/.local/bin/uv run --with certifi python scripts/generate_synthetic_panel.py --refresh  # re-download sources
```

**Why not Synthea (spec §6.8, build plan Step 2):** the build machine has no Java and very little free disk, so we wrote a small stdlib-only Python generator calibrated to the same public sources.

## Files

| File | Rows | What |
|---|---|---|
| `patients_fhir.json` | 1 Bundle (collection) | 300 Patient, 696 Condition (ICD-10-CM), 952 MedicationRequest (RxNorm), 327 RelatedPerson (trusted contacts), 300 QuestionnaireResponse (sign-up answers) |
| `patients.csv` | 300 | Demographics, ZIP, home lat/lon, language, conditions + ICD-10 codes, med counts, spec §8.7 heat classes, mechanism tags, ACB total, combination flags, mail-order, contact summary, `story_patient`, `coverage_topup` |
| `medications.csv` | 952 | One row per patient × drug: generic, RxCUI, TTY, RxNorm name, class, spec §8.7 heat class, mechanism tags, ACB score, dose form, route, indication, OTC-possible, temperature-sensitive, mail-order, delivery location |
| `questionnaire.csv` | 300 | Spec §4.5a core 5 + action-item fields + the optional "asked over time" fields |
| `contacts.csv` | 327 | 0–2 trusted contacts per patient: relationship, fictional phone, lat/lon, location type, straight-line km, naive travel estimate |
| `rxnorm_cache.json` | 83 drugs | RxNav lookups (RxCUI, TTY, name) |
| `summary.json` | — | All distribution summaries below, regenerated on each run |
| `sources/` | — | Cached raw source pulls (PLACES, TIGERweb ZCTA, SVI, NYC Parks, ICD-10-CM checks) |

**Doses are intentionally omitted.** Spec §10.1 says no dose numbers, so MedicationRequest carries only route and dose form.

## Story patients (`story_patient=true`, IDs S01–S10)

| ID | Story |
|---|---|
| S01 | 78F (Spanish), furosemide + oxybutynin + lisinopril + metoprolol; no AC, lives alone, 6th-floor walk-up, step-free need, fluid restricted, no smartphone; only contact is a daughter ~95 km away (no qualifying contact, so the buddy-match path applies) |
| S02 | 16M, mixed amphetamine salts + albuterol; plays outdoor summer soccer |
| S03 | 9F, topiramate for epilepsy; Spanish-speaking parent answers; outdoor day camp; AC cost-limited |
| S04 | 44M, schizophrenia on clozapine + haloperidol + benztropine (2 antipsychotics + anticholinergic stack); lives alone, no AC |
| S05 | 34F, type 1 diabetes on an insulin pump; insulin delivered by mail and left in the building lobby; works outdoors |
| S06 | 58F, bipolar disorder on lithium + hydrochlorothiazide + lisinopril + OTC ibuprofen (lithium × thiazide/ACEi/NSAID; also a triple whammy) |
| S07 | 72M, losartan + chlorthalidone + naproxen (triple whammy) + empagliflozin + metformin; CKD; neighbor in the same building |
| S08 | 66F, heart failure (fluid restricted) + fentanyl patch; lives alone, 9th floor; AC cost-limited |
| S09 | 29F, peanut allergy + asthma, bike delivery courier carrying an epinephrine auto-injector; no AC |
| S10 | 81M, sertraline + HCTZ (low-sodium risk), tolterodine + diphenhydramine (anticholinergic stack); walker, cannot reach a cool place alone |

## Distribution summary (current run)

**Panel:** 300 patients (10 story, 3 coverage top-up).
- **Age:** 42 children, 70 aged 18–44, 102 aged 45–64, 86 aged 65+.
- **Sex:** 166 F, 134 M.
- **ZIP:** 10453 = 62, 10458 = 60, 10460 = 49, 10457 = 43 (demo ZIPs, 214 total); 10468 = 31, 10452 = 28, 10456 = 27 (nearby).
- **Language:** English 165, Spanish 125, Arabic 4, Bengali 4, French 2.

**Medicines:**
- 952 medication rows; mean 3.2 per patient (children 1.5; 18–44: 1.8; 45–64: 3.8; 65+: 4.3).
- 23% of all patients take 5 or more; 45% of those aged 65+ do.

**Patients per spec §8.7 heat class:**

| Heat class | Patients |
|---|---|
| ACEi/ARB | 123 |
| metformin | 64 |
| SSRIs | 44 |
| beta blockers | 43 |
| anticholinergics | 32 |
| thiazides | 27 |
| insulin | 24 |
| SGLT2 | 19 |
| loop diuretics | 18 |
| antipsychotics | 18 |
| epinephrine | 14 |
| ADHD stimulants | 13 |
| topiramate/zonisamide | 11 (6 of them children) |
| lithium | 5 |
| fentanyl patch | 5 |

Six teens (12–17) are on stimulants, and 2 patients use insulin pumps.

**Combination flags** (descriptive, not a score; spec §6.1):

| Flag | Patients |
|---|---|
| 5+ medicines | 69 |
| ACEi/ARB + diuretic | 32 |
| Anticholinergic stack (≥2 ACB drugs, total ACB ≥3) | 22 |
| Triple whammy | 6 |
| Thiazide + SSRI | 4 |
| Lithium + NSAID | 3 |
| Lithium + ACEi/ARB | 3 |
| Lithium + thiazide | 2 |
| Fluid-loss drug + lithium/digoxin | 3 |
| 2+ antipsychotics | 2 |

**Adult prevalence, panel vs CDC PLACES 2025** (crude, weighted by adult population across the 7 ZCTAs). The panel is enriched by design: it is a clinic panel of people on medicines.

| Condition | Panel | PLACES |
|---|---|---|
| Hypertension | 53.1% | 35.0% |
| Diabetes | 29.5% | 16.5% |
| Asthma | 8.5% | 12.1% |
| Depression | 21.7% | 17.0% |
| CKD | 7.0% | 3.5% (PLACES 2023) |
| Arthritis / chronic pain | 32.9% | 21.3% |

Asthma comes out below PLACES in this draw because of random variation (the target was about 12%).

**Questionnaire answers:**
- **Working AC:** yes 204, yes but cost limits use 47, no 49.
- **Where they spend the day:** home 130, indoors with AC 121, outdoors or physical work 49.
- **Lives alone:** 21% of adults.
- **Floor:** 23% live on floor 7 or higher; 37 live on floor 4+ of a walk-up.
- **Mobility:** 69 need step-free access.
- **Can reach a cool place:** yes 205, with help 69, no 26.
- **Fluid restricted:** 22.
- **Alerts:** 88% opted in. Channel: app + SMS 187, SMS only 78, voice call 35.
- **No AC and lives alone:** 8.

**Trusted contacts:**
- **Per patient:** 0 contacts for 50 patients, 1 for 173, 2 for 77.
- **Where contacts live:** same building 44, walkable 94, elsewhere in the Bronx 100, elsewhere in NYC 58, out of area 31.
- **No qualifying contact under the naive placeholder rule:** 154 patients at a 60-min budget, 92 at a 90-min budget (see A14).

**Mail order:** 48 patients; 16 mail-order rows are temperature-sensitive (insulin, semaglutide, epinephrine).

## Sources (accessed 2026-11-14)

1. **CDC PLACES: ZCTA Data (GIS Friendly Format), 2025 release.** data.cdc.gov dataset `kee5-23sr` (BRFSS 2023 model-based estimates). Used for ZIP population weights and as the prevalence reference. https://data.cdc.gov/resource/kee5-23sr.json
   - It matches `data/processed/places_nyc_zcta.csv`, which the place agent wrote.
2. **CDC PLACES ZCTA, 2023 release, `c7b2-4ecy`.** Chronic kidney disease, which is missing from the 2025 GIS release.
3. **US Census TIGERweb, 2020 ZCTA polygons.** `TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/7`. Homes are sampled inside these polygons.
4. **CDC/ATSDR Social Vulnerability Index 2022, Bronx County.** ACS 2018–2022 values: 13.3% aged 65+, 24.7% aged ≤17, 14.5% with limited English, 67.5% of housing in 10+ unit structures. https://onemap.cdc.gov/OneMapServices/rest/services/SVI/CDC_ATSDR_Social_Vulnerability_Index_2022_USA/FeatureServer/1
   - We used SVI because the Census Data API now requires a key.
5. **NYC Parks Properties** (NYC Open Data `enfh-gkve`). Bronx parks over 2 acres are excluded as home locations. The Jerome Park Reservoir is excluded with a hand-drawn approximate box.
6. **NYC Housing & Vacancy Survey via NYC DOHMH Environment & Health Data Portal, indicator 2185** (household AC). Read from `data/processed/ac_households_nyc.csv`. Also used: NYC Council heat data (https://council.nyc.gov/data/heat) and the NYS Comptroller's "Air Conditioning Availability in New York" (https://www.osc.ny.gov/reports/air-conditioning-availability-new-york).
7. **NIH NLM RxNav** for RxCUIs. https://rxnav.nlm.nih.gov/REST/rxcui.json?name=…
   - Most are IN level.
   - Combination products are MIN: sacubitril/valsartan 1656339, budesonide/formoterol 389132, mixed amphetamine salts 822929.
   - Divalproex is PIN 266856.
8. **NLM Clinical Tables ICD-10-CM API.** Every condition code is checked to exist; results are in `sources/icd10cm_cache.json`.
9. **Rate anchors from the literature** (used for weights, not reproduced exactly):
   - Gallego et al. 2012: antipsychotic polypharmacy, international median about 20%.
   - Western et al. 2025 (PMC12682371): older adults walk at about 0.8 m/s.
   - Boustani et al. 2008: the Anticholinergic Burden scale.
   - Guideline first-line drug choices: ACC/AHA 2017 (hypertension), ADA Standards (diabetes), APA (psychiatric conditions).

## Assumptions to know before using this

These are the most important ones; the script docstring has the full A1–A17 list.
- **Not representative.** The panel is older and sicker than the ZIP population by design (A1, A4). Schizophrenia and bipolar disorder are enriched about 3× because of SBH's behavioral-health focus.
- **Coverage top-up.** Each of the 15 drug classes is guaranteed at least 5 patients (A17); these rows are marked `coverage_topup=true`. Drop them if you need "natural" rates.
- **Placeholder contact rule.** `naive_travel_min` and `naive_qualifies_60min` / `naive_qualifies_90min` in contacts.csv are placeholders (A14). The real §4.4a rule must use routed travel time (OpenRouteService / MTA GTFS) and published p90 response times.
- **Contact locations are approximate.** They are bearing-plus-distance offsets, so a few may fall in water or parks. Patient homes do not.
- **Provisional drug fields.** `mechanism_tags` and `acb_score` are convenience fields (A15). The Step-3 knowledge base is authoritative. ACB scores were recalled from the scale and should be checked against the current list.
- **Assumed rates.** Language mix (A11), lives-alone rates (A8), mail-order rates (A13) and contact distances (A12) are stated assumptions, not measured values.
