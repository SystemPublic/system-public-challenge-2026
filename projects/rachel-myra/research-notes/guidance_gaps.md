# Medication Content of Official Heat-Health Guidance, and the Drug-Heat Harms It Omits

Research date: 2026-11-13. About 20 tool calls. Several PDFs (ANSM 2017 mise au point, NYC HAN #23 2026, the ANSM "produits de santé en été" print page) came back as unreadable binary. No local PDF text extractor was available because Python is not installed. Where content came only from secondary reporting, this is flagged.

## What do the major guidance documents say about medications (drugs/classes, actions, evidence basis)?

### Takeaway
The US documents (CDC 2025 and NYC DOHMH) are the most drug-specific. They share near-identical class/mechanism tables, plus storage, power-outage and photosensitivity advice. UKHSA, Health Canada (2011) and Victoria give class lists plus generic "review/assess risk-benefit" advice. France's ANSM is unusual: it covers glucose-meter accuracy in heat and warns against paracetamol for heatstroke. WHO Europe's guidance is a planning framework, and no medication-specific clinical content was found in it.

### Cited Findings

**CDC, "Heat and Medications – Guidance for Clinicians" (US CDC Heat & Health; page dated Sept 18, 2025, an update of the 2024 version)**
- The page frames its guidance as expert opinion, with no formal evidence grading. It says actions should follow a careful risk-benefit review with each patient, and that the drug list is "not comprehensive." — [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)
- **Classes with mechanisms:**
  - Diuretics (furosemide, HCTZ, acetazolamide)
  - Beta blockers
  - CCBs
  - ACEi/ARBs/ARNI, flagged as higher risk when combined with a diuretic
  - Antiplatelets
  - Nitrates
  - Lithium: DI-like water loss and toxicity
  - Antipsychotics
  - SSRIs/SNRIs
  - TCAs
  - Antiseizure drugs: topiramate decreases sweating; oxcarbazepine; carbamazepine
  - Anticholinergic antihistamines
  - NSAIDs
  - Aspirin
  - Acetaminophen: heat-related liver injury
  - Sulfonamides
  - Indinavir
  - Levothyroxine
  - Stimulants
  - MDMA
  - Alcohol
  - Sedation from opioids and benzodiazepines

  Source: [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)
- **Internal inconsistency:** the table says SSRIs/SNRIs increase sweating, while the narrative lists SSRIs as impairing sweating. — [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)
- **Pediatric drugs named:** non-selective antihistamines, methylphenidate, TCAs, SSRIs and diuretics. — [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)
- **Actions:**
  - Medication review.
  - Consider dose or frequency adjustment in hot months, individualized by drug class.
  - Do not stop drugs abruptly without a plan. The page makes no blanket hold recommendation.
  - Consider relaxing fluid restrictions on hot days.
  - Make a medication plan for HeatRisk orange, red and magenta days.
  - Document the hot-day changes and when to resume, in the patient's "Health Action Plan".
  - Identify a check-in contact for high-risk patients.

  Source: [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)
- **Storage and devices:**
  - Refrigerate insulin; it may lose effectiveness after prolonged heat.
  - Do not leave medications in cars.
  - Inhalers can burst in hot places such as car trunks.
  - EpiPens may malfunction or deliver less epinephrine after heat exposure.
  - Plan for power outages: refrigerated drugs, nebulizers, ventilators and oxygen concentrators.

  Source: [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)
- **Photosensitivity:** flucytosine, griseofulvin, voriconazole, metronidazole, tetracyclines and fluoroquinolones. The page advises sun avoidance, protective clothing and SPF 30+ sunscreen. — [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)
- **Absent from the page:** fentanyl/transdermal patches, SGLT2 inhibitors and glucose meters. — [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)

**NYC DOHMH, "Heat and Medications" provider page (no date shown; footer reads © 2025) and Health Alert Network heat alerts (2026 HAN #11, #15, #17, #23; #23 dated Aug 5, 2026)**
- The mechanism groupings largely mirror CDC. NYC additionally names:
  - Apixaban, carbamazepine and lithium as narrow-therapeutic-index drugs with reduced clearance when dehydrated
  - Laxatives and antacids (electrolytes)
  - TMP-SMX (electrolytes)
  - Falls risk with antihypertensives

  Source: [NYC Health](https://www.nyc.gov/site/doh/providers/emergency-prep/heat-and-medications.page)
- The actions match CDC: review, no abrupt stopping, individualized dose or frequency changes, relaxed fluid restriction, documentation in a Health Action Plan, a check-in contact, and photosensitivity counselling. The page also covers AC access, setting AC to 78°F, and the HEAP Cooling Assistance program, which may need medical documentation. — [NYC Health](https://www.nyc.gov/site/doh/providers/emergency-prep/heat-and-medications.page)
- **Storage and devices:** inhalers, EpiPens, insulin, and a power-outage plan for refrigerated drugs and electricity-dependent equipment. The page cites no primary studies. Its listed resources are the University of Arizona heat and medications task force and an NYC "Using Drugs in Extreme Heat" palm card. — [NYC Health](https://www.nyc.gov/site/doh/providers/emergency-prep/heat-and-medications.page)
- **HAN alerts:** the alerts tell providers to review medications that affect temperature regulation and adjust regimens on hot days as needed. They name diuretics, anticholinergics and psychotropics. The 2026 HAN #23 reportedly advises more frequent blood-glucose checks for people with diabetes in high heat. This comes from a search summary; the PDF text could not be extracted. — [NYC HAN 2026 #23](https://www.nyc.gov/assets/doh/downloads/pdf/han/alert/2026/han-alert-23-protect-people-extreme-heat.pdf)

**UKHSA, "Supporting vulnerable people before and during hot weather: healthcare professionals" (GOV.UK; dated 19 December 2024; part of the Adverse Weather and Health Plan / Heat-Health Alert system)**
- **Classes with mechanisms:**
  - Diuretics, especially loop diuretics
  - Antihypertensives and antianginals
  - Anticholinergics and beta blockers (sweating)
  - Colchicine, antibiotics and opiates (diarrhoea or vomiting)
  - Antimicrobials, immunosuppressants, NSAIDs, anti-ulcer agents and chemotherapy (renal function)
  - Lithium, digoxin and antiepileptics (levels affected by dehydration)
  - Hypnotics, anxiolytics and analgesics (alertness)
  - Neuroleptics and serotonergic agonists (central thermoregulation)
  - Thyroxine

  The list is stated as not exhaustive. — [GOV.UK UKHSA](https://www.gov.uk/guidance/supporting-vulnerable-people-before-and-during-hot-weather-healthcare-professionals)
- **Actions:** no specific dose or stop instructions. The page says to assess the risks and benefits of any change, adapt care plans, and train staff to recognise risky medications. Monitoring covers fluid intake via body weight only. — [GOV.UK UKHSA](https://www.gov.uk/guidance/supporting-vulnerable-people-before-and-during-hot-weather-healthcare-professionals)
- **Storage:** most medicines should be kept below 25°C, in a cool dry place out of sunlight and away from windowsills. Refrigerate only if specified. The page defers to the NHS Specialist Pharmacy Service. It does not mention patches, photosensitivity, insulin, devices or power. — [GOV.UK UKHSA](https://www.gov.uk/guidance/supporting-vulnerable-people-before-and-during-hot-weather-healthcare-professionals)
- **Public Health Wales:** published a 2026 "Public health advice for healthcare professionals: hot weather" PDF. Its content was not reviewed. — [PHW](https://phw.nhs.wales/app/uploads/sites/2/2026/05/PHW-Public-health-advice-for-healthcare-professionals-hot-weather_FINAL2.pdf)

**Health Canada, "Extreme Heat Events Guidelines: Technical Guide for Health Care Workers" (2011; ISBN 978-1-100-18172-1; Cat. H128-1/11-642E). Chapter 4, "Heat Risk Factors Associated with Medications", was co-authored by INSPQ (Blachère and Gosselin).**
- **Mechanisms:** hypothalamic set-point change (antidopaminergic and anticholinergic), reduced sweating, altered heat perception, cardiac output and vasodilation, renal, hydration and electrolyte effects (including SSRI hyponatremia), and GI fluid loss. — [Health Canada](https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/climate-change-health/extreme-heat-events-guidelines-technical-guide-health-care-workers)
- **Table 4.2** covers antipsychotics, antidepressants (SSRIs), lithium, antiepileptics, cholinesterase inhibitors, anti-Parkinson agents, diuretics, antiarrhythmics/cardiotonics, nitrates, CCBs and ACE inhibitors. The actions are mostly "hydrate / protect from heat / monitor hydration." — [Health Canada](https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/climate-change-health/extreme-heat-events-guidelines-technical-guide-health-care-workers)
  - **Lithium:** drink water but avoid electrolyte solutions, because of hypernatremia risk.
  - **Water vs electrolyte solution:** the prescriber decides, and the guide warns that overdrinking causes hyponatremia.
  - **Cholinesterase inhibitors:** monitor closely if started in summer.
- **Topiramate (a tail-end harm addressed here and in few other documents):** the guide cites hypohidrosis in 11% of children, 69% in an experimental study, and severe hyperthermia in 19% in one study. It says the risk "should not be underestimated." — [Health Canada](https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/climate-change-health/extreme-heat-events-guidelines-technical-guide-health-care-workers)
- **Evidence basis, stated explicitly:**
  - Case reports of polypharmacy heat stroke, where attribution is difficult.
  - Odds ratios from the 2003 French heatwave: anticholinergics OR 6.0 (1.8–19.6), antipsychotics OR 4.6 (1.9–11.2), anxiolytics OR 2.4 (1.3–4.4). The anti-Parkinson estimate, OR 6.02 (0.72–50.37), is non-significant.
  - The guide notes that the French agency list is mechanism-based, not outcome-based, and that the Ontario list came from a coroner's investigation of two deaths.
  - It acknowledges that understudied drugs may be missing.

  Source: [Health Canada](https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/climate-change-health/extreme-heat-events-guidelines-technical-guide-health-care-workers)
- **Insulin storage:** covered in Chapter 3. Chapter 4 does not cover patches, photosensitivity, storage temperatures or power outages. No newer edition was found; catalogue records also show a c2014 entry (H128-1/11-642-1E). — [Health Canada](https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/climate-change-health/extreme-heat-events-guidelines-technical-guide-health-care-workers); [publications.gc.ca](https://publications.gc.ca/site/eng/9.696253/publication.html)

**France, ANSM "Canicule et produits de santé" dossier: "Mise au point – Bon usage des médicaments en cas de vague de chaleur" (2017 PDF, still hosted) plus a separate glucose-meter sheet (revised 30/07/2021)**
- **Approach:** treatment adaptation is case by case, with no systematic dose reduction or stopping. — [ANSM mise au point PDF 2017](https://ansm.sante.fr/uploads/2022/06/15/map-canicule-bon-usage-med-2017-1-1.pdf) (content via secondary sources: [Le Quotidien du Médecin](https://www.lequotidiendumedecin.fr/actu-medicale/la-liste-des-medicaments-qui-font-mauvais-menage-avec-la-canicule))
- **Recommended steps (as reported):**
  - Assess hydration.
  - Review all current treatments.
  - Check that diuretic users get appropriate water and salt intake.
  - Remind patients not to take any medicine, including OTC, without advice.
  - Classes: diuretics, nephrotoxic drugs, drugs altering thermoregulation (neuroleptics, serotonergics), antihypertensives, and psychotropics affecting alertness.

  Source: [Le Quotidien du Médecin](https://www.lequotidiendumedecin.fr/actu-medicale/la-liste-des-medicaments-qui-font-mauvais-menage-avec-la-canicule)
- **Paracetamol:** ANSM advises against it for heatstroke fever. It is ineffective there and may worsen the liver injury that often accompanies heatstroke. This is one of the few treatment-of-heat-illness drug cautions in any guidance. — [Le Quotidien du Médecin (cardiologie)](https://cardiologie.lequotidiendumedecin.fr/actus-medicales/recos-pratique/vague-de-chaleur-le-rappel-de-lansm-sur-le-bon-usage-des-medicaments)
- **Storage:** ANSM says brief heat exposure of 2–8°C products may not affect stability under some conditions. A separate storage mise au point exists. — [Le Quotidien du Médecin](https://cardiologie.lequotidiendumedecin.fr/actus-medicales/recos-pratique/vague-de-chaleur-le-rappel-de-lansm-sur-le-bon-usage-des-medicaments); [Ordre des pharmaciens](https://www.ordre.pharmacien.fr/les-communications/focus-sur/les-actualites/bon-usage-et-conservation-des-produits-de-sante-en-cas-de-vague-de-chaleur2)
- **Glucose meters (unique among the documents reviewed):**
  - High temperatures can impair test strips, sensors, electrodes and control solutions when kept above the recommended temperature for several hours. Meters themselves are less affected.
  - Do not refrigerate strips, because condensation distorts results.
  - Let the kit return to room temperature before testing.
  - Respect the operating temperature range.
  - Consult a professional before changing treatment because of abnormal readings.

  Source: [ANSM glucose-monitoring Q&A PDF](https://ansm.sante.fr/uploads/2022/06/15/canicule-informations-suivi-glycemique-qr-2017-1-1.pdf); [VIDAL](https://www.vidal.fr/actualites/38047-autosurveillance-glycemique-et-canicule-des-conseils-pour-limiter-la-surchauffe.html)
- **Device page:** ANSM also hosts "Fortes chaleurs et dispositifs médicaux : les bons réflexes". Its content was not readable. — [ANSM](https://ansm.sante.fr/dossiers-thematiques/fortes-chaleurs-et-dispositifs-medicaux-les-bons-reflexes/impression/577)

**WHO Regional Office for Europe**
- **"Heat–health action plans: guidance"** (2008; ISBN 9789289071918; 50 pp.). The landing page does not describe medication content; it is a planning framework covering early warning, medical advice, housing and health-system preparedness. — [WHO Europe](https://www.who.int/europe/publications/i/item/9789289071918)
- **"Heat and health in the WHO European Region: updated evidence for effective prevention"** (2021) updates the 2008 evidence. — [UNEP-CCC listing](https://unepccc.org/publications/heat-and-health-in-the-who-european-region-updated-evidence-for-effective-prevention/)
- **Second edition of the HHAP guidance:** search results indicate WHO issued it, structured around eight core elements, informed by systematic reviews from 2021, 2023 and 2024, and dated 2026. Not directly verified. — [PreventionWeb](https://www.preventionweb.net/quick/102825)
- **Media report on medicines:** a news report says WHO flagged medicine-storage challenges. It describes recommendations to stock IV fluids, ORS and cooling packs for emergency departments and to advise patients to keep medicines cool, and it lists diuretics, antihypertensives, antipsychotics and antidepressants. The report's year and document are unclear. — [Irish Examiner](https://www.irishexaminer.com/news/arid-+41935296.html)

**Australia, Victoria Department of Health**
- **Chief Health Officer advisory 260127 (27 Jan 2026), "Increased heat-related health risks":** says clinicians in general practice, EDs and pharmacies have key roles, and suggests a cool-box with ice or cool packs for medications. — [Health Vic advisory](https://health.vic.gov.au/health-advisories/increased-heat-related-health-risks)
- **"Extreme heat information for clinicians" page:** says certain medications affect sweating, dehydration and thermoregulation. — [Health Vic clinicians page](https://app.production.health-vic-gov-au.sdp3.sdp.vic.gov.au/environmental-health/extreme-heat-information-for-clinicians); [Heat health plan for Victoria (2021)](https://www.health.vic.gov.au/publications/heat-health-plan-for-victoria)
- **Council guidance:** Victorian council-level material says overheated medications can become less effective or occasionally toxic, and that most should be stored below 25°C. This is a local government source, not the Department. — [Murrindindi Shire](https://www.murrindindi.vic.gov.au/Community/Safety-and-Emergencies/Fire-and-Heat/Heatwaves)

**Germany**
- **Federal frame:** the Federal Ministry of Health (BMG) extended the "Hitzeschutzplan für Deutschland" (2023) with 2024 model plans, including for pharmacies and psychotherapy practices. They call for medication review and proper storage of heat-sensitive medicines. — [BMG press release 2024](https://www.bundesgesundheitsministerium.de/presse/pressemitteilungen/lauterbach-legt-hitzeschutzplaene-vor-pm-24-05-24); [BMG Muster-Hitzeschutzplan Krankenhäuser](https://www.bundesgesundheitsministerium.de/fileadmin/Dateien/3_Downloads/H/Hitzeschutzplan/Musterhitzeschutzplan_Krankenhaeuser_BF.pdf)
- **Practice-level material:** lists diuretics, ACE inhibitors, ARBs, antidepressants, anticonvulsants and antipsychotics as drugs to check. — [Labor Leipzig Hitzeschutzplan für Praxen](https://www.labor-leipzig.de/fileadmin/user_upload/Leipzig/06_Fuer_Aerzte/PI-120_Hitzeschutzplan_fuer_Praxen-Broschuere.pdf)
- No authoritative federal drug-by-drug list with dosing advice was found in search results. — [KBV Hitzeschutz](https://www.kbv.de/praxis/praxisfuehrung/hitzeschutz)

### Inferences
- **A shared lineage:** the lists share mechanism categories (sweating, thirst, renal/electrolyte, vasodilation, CNS thermoregulation, sedation). This suggests that the French 2003-era ANSM mechanism list, INSPQ, and later the University of Arizona/CDC tables are the common sources. CDC and NYC appear nearly identical.
- **Tiers of actionability:**
  - Most specific (CDC/NYC): drug-level storage and device harms, power outages, photosensitivity, fluid-restriction relaxation, documentation.
  - Middle tier (Health Canada 2011): per-class hydration actions; the only one with stated odds ratios and evidence caveats.
  - Middle tier (ANSM): stepwise assessment, the paracetamol caution, glucose meters.
  - Lowest (UKHSA, Victoria, Germany, WHO): class lists or "review medications / assess risk-benefit" only.

### Gaps
- Could not read the full text of the ANSM 2017 mise au point, the ANSM storage sheet, NYC HAN #23 2026, the Victoria clinician page or the PHW 2026 PDF; PDF extraction failed.
- Did not access: UKHSA "Beat the heat" public leaflets; NICE (I found no NICE heat-medication guideline); BfArM/BZgA specific material; Spain (Ministerio de Sanidad Plan Nacional de Actuaciones Preventivas); Italy (Ministero della Salute heat guidance); India (NDMA guidelines, Ahmedabad HAP); Japan (MHLW/MoE heatstroke guidance); NSW Health; ADA heat guidance; psychiatric associations; APhA; ACP. No claims about their medication content can be made from this research.
- Whether CDC's 2025 page differs materially from the original 2024 release was not checked.

## Which notable (especially rare or tail-end) drug-heat harms are omitted?

### Takeaway
None of the reviewed guidance mentions heat-accelerated absorption from fentanyl or other transdermal patches, or SGLT2-inhibitor volume depletion or euglycemic DKA. Glucose-meter heat errors appear only in ANSM. Topiramate anhidrosis in children appears substantively only in Health Canada 2011; CDC/NYC list topiramate's "decreased sweating" without pediatric emphasis. Power-outage device failure appears only in CDC/NYC. Degraded-drug toxicity appears only at council level in Victoria. Photosensitivity appears only in CDC/NYC.

### Cited Findings
- **CDC:** no mention of fentanyl patches, SGLT2 inhibitors or glucose meters. It does cover insulin potency loss, EpiPen under-delivery, inhaler bursting, power-outage planning for nebulizers, ventilators and oxygen concentrators, and photosensitizers. — [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)
- **NYC:** patches not mentioned; insulin covered for storage only, with no glucose monitoring or dosing advice on the provider page. — [NYC Health](https://www.nyc.gov/site/doh/providers/emergency-prep/heat-and-medications.page)
- **UKHSA healthcare-professional page:** no patches, photosensitivity, insulin, devices or power dependence. — [GOV.UK UKHSA](https://www.gov.uk/guidance/supporting-vulnerable-people-before-and-during-hot-weather-healthcare-professionals)
- **Health Canada Chapter 4:** no patches, photosensitivity, storage temperatures or power outages. It does give the topiramate pediatric hypohidrosis figure (11% of children). — [Health Canada](https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/climate-change-health/extreme-heat-events-guidelines-technical-guide-health-care-workers)
- **ANSM:** the only official source found that addresses glucose strip, sensor and electrode errors in heat and condensation errors from refrigerating strips. — [ANSM glycaemic Q&A](https://ansm.sante.fr/uploads/2022/06/15/canicule-informations-suivi-glycemique-qr-2017-1-1.pdf)
- **Patches in non-official material:** a 2026 Drug Topics pharmacist commentary notes heat can affect delivery from transdermal patches and inhalers. It does not name fentanyl. — [Drug Topics, May 2026](https://www.drugtopics.com/view/heat-and-medications-what-pharmacists-need-to-know)
- **SGLT2 in non-official material:** found only in a commercial patient blog (Pillo), which groups SGLT2 inhibitors with diuretics as fluid-loss drugs. This is not authoritative. — [Pillo](https://pillo.care/blog/medications-and-heat-risk)
- **Degraded-drug toxicity:** "less effective or occasionally toxic when overheated" appears in Victorian local council guidance, not in national or state clinical guidance reviewed here. — [Murrindindi Shire](https://www.murrindindi.vic.gov.au/Community/Safety-and-Emergencies/Fire-and-Heat/Heatwaves)

### Inferences
- **Degradation vs. potency loss:** omissions cluster in exposure-route and device harms, and in drug classes newer than the 2003-era lists, such as SGLT2 inhibitors. These lists rest on mechanism or epidemiology data from the 2003 French heatwave and coroner cases, so newer drugs and rare harms are structurally under-represented. Health Canada explicitly acknowledged this. Official documents describe degradation as loss of potency (insulin, EpiPen); they don't describe toxic degradation products.
- **Glucose monitoring:** the NYC HAN 2026 advice to check glucose more often (reported) combined with no guidance on meter heat errors in the US documents may create a gap where patients test more with potentially heat-compromised strips. This is an inference, not a documented harm.
- **Fentanyl patches:** the heat warning exists in product labelling (not verified in this research; see the adjacent research thread) but has not migrated into any heat-health guidance reviewed.

### Gaps
- Did not verify whether ADA, Diabetes UK or Diabetes Canada heat guidance covers SGLT2 inhibitors, euglycemic DKA or CGM/pump heat limits.
- Did not verify fentanyl label language or FDA communications in this thread.
- Japan and India guidance content is unknown here. Japan's MHLW/MoE heatstroke materials and India's NDMA guidelines may contain medication content, but they were not accessed.

## Are there published critiques or reviews comparing medication content of heat guidance?

### Takeaway
No peer-reviewed review dedicated to medication content across heat-health action plans was found. Existing content analyses look at other dimensions: triggers, outreach, mental health, maternal and child health, and pregnancy.

### Cited Findings
- **Randazza et al. 2023**, a content analysis of 21 US local heat action plans, coded triggers, messaging, cooling centers, surveillance and coordination (all 21 plans), plus outreach to at-risk groups (95%). Medication content was not a headline coded element in the search summary. — [Randazza et al. 2023 PDF](https://heathealth.info/wp-content/uploads/randazza-et-al-2023-planning-to-reduce-the-health-impacts-of-extreme-heat-a-content-analysis-of-heat-action-plans-in.pdf)
- **Mental health review:** of 83 plans from 24 countries, 75.9% mentioned mental health but only 31.3% acknowledged its specific impacts. — [search summary; JoGH PDF hosted by GHHIN](https://ghhin.org/wp-content/uploads/jogh-15-04157.pdf)
- **Maternal and child health:** a scoping review found that no heat-health action plan comprehensively addressed maternal, newborn and child health risks. — [Princeton listing](https://collaborate.princeton.edu/en/publications/how-is-maternal-newborn-and-child-health-addressed-in-heat-health/)
- **2025 meta-review:** "The Spectrum of Heat-Related Diseases" (Int J Public Health) found 13 studies, 6 of them policy documents on heat action plans. — [IJPH 2025](https://www.ssph-journal.org/journals/international-journal-of-public-health/articles/10.3389/ijph.2025.1608592/full)
- **Health Canada's own critique (2011):** existing lists are mechanism-based (France) or based on few cases (Ontario coroner, two deaths), and understudied drugs may be missing. — [Health Canada](https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/climate-change-health/extreme-heat-events-guidelines-technical-guide-health-care-workers)

### Inferences
- A cross-jurisdiction comparison of medication content appears to be an unfilled gap in the literature, at least in what general web search surfaces.

### Gaps
- PubMed or Scopus were not searched directly. Pharmacology-focused reviews may exist, for example Westaway et al. 2015 (Australia) or 2024–2025 reviews of heat and medication; their scope against guidance documents is unverified.

## Where does guidance conflict internally, with other guidance, or with evidence?

### Takeaway
The major documents converge on no blanket stopping of medications (CDC, NYC, ANSM, UKHSA). The main conflicts are on hydration and on sweating direction:
- Health Canada warns against overdrinking (hyponatremia) and electrolyte drinks with lithium, while US documents advise relaxing fluid restrictions.
- CDC's table and narrative disagree on whether SSRIs increase or impair sweating.

### Cited Findings
- **Stopping drugs:**
  - CDC: do not abruptly stop without a plan; adjustments individualized. — [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)
  - ANSM: no systematic reduction or stopping. — [ANSM PDF](https://ansm.sante.fr/uploads/2022/06/15/map-canicule-bon-usage-med-2017-1-1.pdf)
  - UKHSA: assess risk-benefit of any change. — [GOV.UK](https://www.gov.uk/guidance/supporting-vulnerable-people-before-and-during-hot-weather-healthcare-professionals)
- **Fluids:**
  - CDC/NYC: consider relaxing fluid restrictions on hot days. — [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)
  - Health Canada: overdrinking water causes hyponatremia (relevant to SSRIs, antipsychotics, diuretics, carbamazepine/oxcarbazepine); lithium patients should avoid electrolyte solutions. — [Health Canada](https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/climate-change-health/extreme-heat-events-guidelines-technical-guide-health-care-workers)
- **SSRI sweating:** the CDC table says increased sweating; the CDC narrative lists SSRIs among drugs impairing sweating. NYC says SSRIs/SNRIs increase sweating. — [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html); [NYC](https://www.nyc.gov/site/doh/providers/emergency-prep/heat-and-medications.page)
- **Diuretic effects, same class:** Health Canada's Table 4.2 lists "hyperhydration, hyponatremia" for diuretics. CDC/NYC/UKHSA list dehydration and volume depletion. — [Health Canada](https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/climate-change-health/extreme-heat-events-guidelines-technical-guide-health-care-workers); [GOV.UK](https://www.gov.uk/guidance/supporting-vulnerable-people-before-and-during-hot-weather-healthcare-professionals)
- **Cold-chain storage:**
  - ANSM: short heat exposure of 2–8°C products may not affect stability.
  - CDC: insulin may lose effectiveness after prolonged heat, with a general instruction to refrigerate.
  - UKHSA: below 25°C, refrigerate only if specified.

  These are compatible in substance but differ in emphasis. — [Le Quotidien du Médecin](https://cardiologie.lequotidiendumedecin.fr/actus-medicales/recos-pratique/vague-de-chaleur-le-rappel-de-lansm-sur-le-bon-usage-des-medicaments); [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html); [GOV.UK](https://www.gov.uk/guidance/supporting-vulnerable-people-before-and-during-hot-weather-healthcare-professionals)
- **Acetaminophen in heat illness:** ANSM says avoid it for heatstroke (ineffective, hepatotoxic). CDC lists heat-related liver injury risk with acetaminophen. These are consistent, but UKHSA does not address it. — [Le Quotidien du Médecin](https://cardiologie.lequotidiendumedecin.fr/actus-medicales/recos-pratique/vague-de-chaleur-le-rappel-de-lansm-sur-le-bon-usage-des-medicaments); [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html)
- **Evidence strength:** CDC and NYC rest on expert opinion with no grading. Health Canada is the only document reviewed that reports odds ratios and flags non-significant estimates (anti-Parkinson OR 6.02, CI 0.72–50.37). — [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html); [Health Canada](https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/climate-change-health/extreme-heat-events-guidelines-technical-guide-health-care-workers)

### Inferences
- **Diuretics:** no document found explicitly advises stopping them. The "stop diuretics vs decompensation" tension is therefore mostly implicit: generic "review/adjust" advice without heart-failure-specific guidance on weight-based diuretic titration leaves clinicians without direction. No source here addresses heart-failure decompensation risk from heat-driven dose reduction.
- **Fluids:** "relax fluid restriction" (US) versus "beware hyponatremia" (Canada) is a substantive unreconciled tension for heart failure and SSRI/antipsychotic users.

### Gaps
- Could not find guidance that explicitly recommends holding diuretics, so I could not test for a documented "stop diuretic" conflict. Primary peer-reviewed evidence on heat-season diuretic adjustment outcomes was not searched.
