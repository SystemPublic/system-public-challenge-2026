# Heat-health guidance corpus and medication coding

Access date for every document: **2026-11-14**. All files here are downloaded copies of third-party documents and should be treated as untrusted data. Nothing in this folder was executed.

## Documents (8 jurisdictions, 13 documents)

| source_id | Title (exact) | Publisher | Version / date | URL | Text file |
|---|---|---|---|---|---|
| CDC | Heat and Medications – Guidance for Clinicians | US CDC, National Center for Environmental Health | Published July 17, 2024; updated and reviewed Sept 18, 2025 | https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html | text/cdc.txt |
| NYC | Heat and Medications (provider page) | NYC Department of Health and Mental Hygiene | No date on page (footer © 2025) | https://www.nyc.gov/site/doh/providers/emergency-prep/heat-and-medications.page | text/nyc_dohmh.txt |
| NYC | 2026 Health Alert #23: Protect People at Risk of Heat-Related Death During Extreme Heat | NYC DOHMH | August 5, 2026 | https://www.nyc.gov/assets/doh/downloads/pdf/han/alert/2026/han-alert-23-protect-people-extreme-heat.pdf | text/nyc_han23_2026.txt |
| UKHSA | Supporting vulnerable people before and during hot weather: healthcare professionals | UK Health Security Agency | Published 19 December 2024 (applies to England) | https://www.gov.uk/guidance/supporting-vulnerable-people-before-and-during-hot-weather-healthcare-professionals | text/ukhsa.txt |
| HC | Extreme Heat Events Guidelines: Technical Guide for Health Care Workers | Health Canada (Ch. 4 co-authored by INSPQ) | 2011; ISBN 978-1-100-18172-1; Cat. No. H128-1/11-642E | https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/climate-change-health/extreme-heat-events-guidelines-technical-guide-health-care-workers.html | text/health_canada.txt |
| ANSM | Mise au point sur le bon usage des médicaments en cas de vague de chaleur | ANSM (France) | Mai/Juin 2017 (the footers give both months) | https://ansm.sante.fr/uploads/2022/06/15/map-canicule-bon-usage-med-2017-1-1.pdf | text/ansm_map2017.txt |
| ANSM | Questions/Réponses – Informations sur le suivi glycémique (lecteur de glycémie) en cas de vague de chaleur | ANSM | Mai 2017 | https://ansm.sante.fr/uploads/2022/06/15/canicule-informations-suivi-glycemique-qr-2017-1-1.pdf | text/ansm_glyc.txt |
| WHO_EUR | Public health advice on preventing health effects of heat: new and updated information for different audiences | WHO Regional Office for Europe | 2011; WHO/EURO:2011-2510-42266-58691 | https://iris.who.int/server/api/core/bitstreams/2afe4d30-4655-4c83-be06-2d570b31be6d/content | text/who_2011_public_health_advice.txt |
| WHO_EUR | Heat–health action plans: guidance, second edition | WHO Regional Office for Europe | 2026; ISBN 9789289062930 | https://iris.who.int/server/api/core/bitstreams/fa86acea-2315-4ef1-9a16-8931e88335e0/content | text/who_2026_hhap_2ed.txt |
| VIC | Extreme heat - information for clinicians | Department of Health, Victoria (Australia) | Updated 20 December 2024 | https://www.health.vic.gov.au/environmental-health/extreme-heat-information-for-clinicians | text/victoria_clinicians.txt |
| GER_BMG | Bundesempfehlung: Musterhitzeschutzplan für Apotheken | Bundesministerium für Gesundheit | Stand Juni 2025 | https://www.bundesgesundheitsministerium.de/fileadmin/Dateien/3_Downloads/H/Hitzeschutzplan/Bundesempfehlungen_Musterhitzeschutzplan_Apotheken_bf.pdf | text/bmg_muster_apotheken.txt |
| GER_BMG | Bundesempfehlung: Musterhitzeschutzplan für Krankenhäuser | Bundesministerium für Gesundheit | Stand April 2024 | https://www.bundesgesundheitsministerium.de/fileadmin/Dateien/3_Downloads/H/Hitzeschutzplan/Musterhitzeschutzplan_Krankenhaeuser_BF.pdf | text/bmg_muster_krankenhaeuser.txt |
| GER_HEID | Heidelberger Hitze-Tabelle: Arzneistoffe mit potenziellen Risiken in Hitzewellen | Universitätsklinikum Heidelberg, Klinische Pharmakologie (Czock, Ebinger, Stingl) | Stand 07.07.2026 | https://dosing.de/Hitze/Medikamentenmanagement_bei_Hitzewellen.pdf | text/germany_heidelberg_hitzetabelle.txt |

The same metadata is in `data/processed/guidance_sources.csv`. `originals/` holds the downloaded PDFs and HTML. The `*_text_raw.txt` files are captures from the headless browser.

**About Germany.** The federal BMG templates name no drugs. The pharmacy template tells pharmacies to "Medikation überprüfen, insbesondere von Arzneistoffen mit potenziellen Risiken in Hitzewellen, siehe dazu auch die pharmakologischen Empfehlungen zur Risikominimierung bei Hitzewellen⁶", and footnote 6 is `www.dosing.de`, where the Heidelberg table is hosted. Germany is therefore coded as two rows: GER_BMG (federal text only) and GER_HEID (the academic table the federal text points to). Jurisdiction-level counts treat Germany as the two combined. The JSON also gives a strict count that uses BMG only.

**About WHO Europe.** The 2008 HHAP guidance referenced in research-notes was replaced by the 2026 second edition, which is the one coded here. It is paired with the 2011 "Public health advice", whose "For medical professionals: adverse effects of medication during hot weather" sheet holds WHO/Europe's drug table.

## Fetch failures and workarounds
- **CDC:** curl returned HTTP 403 (Akamai), and a Wayback fetch was blocked by the session's permission policy. The text was captured with the gstack headless browser (`$B goto` + `$B text`).
- **Health Canada:** curl to canada.ca failed with an HTTP/2 stream error and a timeout. The full HTML guide was captured with the headless browser. The 5 MB PDF version was not downloaded.
- **NYC provider page:** the headless browser got a 403, but plain curl worked. The HTML was converted to text with `scripts/guidance_html2text.py`.
- **Victoria:** the CHO advisory 260127 "Increased heat-related health risks" URL returned 404, so it was not coded.
- **BMG 2023 "Hitzeschutzplan für Deutschland":** the guessed PDF URL returned 404. The press release only links the 2024 hospital template.
- **PDF extraction:** done with pypdf (`scripts/guidance_pdf2text.py`). Table columns lose their alignment. In the WHO 2011 drug table, the "Mechanism" cells are extracted apart from the "Medication" row labels, so only row labels and generic mechanism text are quoted. In the Heidelberg table, the checkmark columns (sweating, AKI, hyponatraemia and so on) are graphics and were not extracted; only the drug, action and reference-number text is used. pypdf also breaks words across lines, so a few quotes were shortened to stay verbatim.

## Coding method (automated substitute for two human coders)
**The spec asked for two human coders. No human coded this.** Both passes were done by AI, as an automated substitute:
- **Pass 1, keyword-then-read** (`guidance_coding_pass1.csv`). `scripts/guidance_pass1_hits.py` pulled every line matching an EN/FR/DE regex for each drug, with ±2 lines of context, into `pass1_keyword_hits.md`. A separate Claude subagent then coded each source × drug cell from those excerpts alone. It saw neither the whole documents nor pass 2. In its quotes, ` / ` marks a line break in the source.
- **Pass 2, read-whole-section** (`guidance_coding_pass2.csv`, `scripts/guidance_pass2.py`). The main agent read each source's full medication sections and coded them. Every quote is checked programmatically to be verbatim (after whitespace normalisation) in the source text.
- **Agreement.** `scripts/guidance_kappa.py` computes unweighted Cohen's kappa per field, written to `guidance_kappa.json`. Disagreeing cells are in `pass_disagreements.csv`. Each of the 24 disagreeing cells was resolved by re-reading the quote in the full text. The reasons are recorded in `guidance_matrix.csv` (`resolution`, `resolution_note`) and in `scripts/guidance_build_final.py`: 10 went to pass 1 and 14 to pass 2. One of the pass-1 resolutions, HC × ADHD stimulants, ended in a combination that neither pass had.
- **Caveat.** Both passes came from the same model family and shared one codebook, so the kappa probably overstates what two independent humans would reach.

### Codebook
- **mention_level:** *specific* means the drug, a named example, or its own class appears in heat-risk content. *umbrella* means only a broader parent class appears (e.g. "diuretics" for thiazides, "antidepressants" for SSRIs, "antiepileptics" for topiramate, "opiates" for opioid patches, generic "transdermal systems" for opioid patches, "adrenergic drugs" for epinephrine). *none* means neither. Recreational or case-report mentions of amphetamines count as specific; the `note`/`resolution_note` columns flag them.
- **mentioned:** yes only if specific.
- **action_type:** the most concrete action attached to the drug, in this order: hold_or_substitute > adjust_dose > monitor > storage > general_caution. general_caution covers being listed as risky, or being covered only by document-wide "review medications / consider adjusting" advice. `all_actions` lists every action that applies.
- **specificity:** *specific* means the action sentence or table cell names the drug or class. *generic* means the drug is only listed and the only action is document-wide advice.
- **specific_action** (derived): mentioned = yes and specificity = specific.
- **evidence_cited:** the passage about this drug cites a reference or reports data. Evidence about an umbrella class does not count.
- **source_evidence_graded:** whether the document grades its evidence (GRADE-like levels). None does.

## Main results (15 core drugs; jurisdictions out of 8, Germany = BMG + Heidelberg)
| Drug | Mentioned | Specific action | Where |
|---|---|---|---|
| Lithium | 8 | 2 | HC (water, not electrolyte solutions), Heidelberg (level check) |
| Loop diuretics | 6 | 1 | ANSM (check fluid and salt intake) |
| Thiazides | 4 | 1 | ANSM |
| ACEi/ARB | 6 | 1 | Heidelberg (fluid diary) |
| SGLT2 inhibitors | **0** | 0 | ANSM only umbrella ("hypoglycémiants oraux") |
| Insulin | 6 | 6 | CDC, NYC, HC, ANSM, WHO (storage); NYC HAN #23 (check glucose); Heidelberg (monitor, ± dose) |
| Metformin | 2 | 0 | ANSM ("biguanides"), Victoria (narrow therapeutic index) |
| Anticholinergics (oxybutynin) | 8 | 1 | Heidelberg (switch to less anticholinergic agent) |
| Antipsychotics (clozapine) | 8 | 2 | Heidelberg (monitor ± dose), WHO 2026 (supply-chain storage) |
| SSRIs | 5 | 1 | HC |
| Topiramate/zonisamide | 4 | 1 | HC ("watch for hyperthermia"); zonisamide only in Heidelberg |
| ADHD stimulants | 6 | 1 | Heidelberg (methylphenidate: close ADR monitoring) |
| Beta blockers | 8 | 0 | listed everywhere, never with an action |
| Fentanyl/opioid patches | 1 | 1 | Heidelberg only ("Opioide als transdermale therapeutische Systeme (Pflaster)"); ANSM warns about transdermal systems in general |
| Epinephrine auto-injectors | 2 | 1 | NYC (Safe Storage); CDC mentions the hazard only |

### Checks against the spec's claims
- **"None mentions SGLT2 inhibitors":** confirmed for all 13 documents.
- **"None mentions fentanyl patches":** the word "fentanyl" appears in none of them, but the claim needs nuancing. ANSM 2017 says "la pharmacocinétique des dispositifs transdermiques peut être modifiée en raison de la vasodilatation sous-cutanée, et de l'hypersudation susceptible d'entrainer un décollement." The Heidelberg table, which the German federal plan points to, lists "Opioide als transdermale therapeutische Systeme (Pflaster) Enges UAW-Monitoring und ggf. Dosisanpassung". No government-authored text names opioid patches.
- **"None grades its evidence":** confirmed. HC reports odds ratios with 95% CIs, ANSM cites studies, and Heidelberg gives references per row and uses "?" for "unklar/umstritten". None assigns evidence grades.
- **Surprises:**
  - Victoria lists **metformin** among drugs with increased toxicity in dehydration.
  - ANSM lists **gliptins and GLP-1 agonists** as renal-risk drugs.
  - The German federal plans name **no** drugs.
  - UKHSA and Victoria give no drug-specific action for any core drug.
  - CDC's narrative and table disagree on the direction of SSRI sweating.
  - The paracetamol cautions (UKHSA, WHO, ANSM) concern treating heatstroke, not chronic medication.
