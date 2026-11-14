# What the advisor told us to model on, scale and improve (Sat 14 Nov)

Sources Rachel sent, read on Sat 14 Nov:
1. **NACHC, *Heat-Related Illness Management in EHR Systems*** (Sep 2024). PDF saved at `research-notes/sources/NACHC_EHR-Heat-Messaging-Guide.pdf`. It's a guide for community health centers on putting heat alerts into the EHR (Epic, athenahealth, NextGen, eClinicalWorks): registries from value sets, Best Practice Alerts for clinicians, and text/portal messages to patients.
2. **NACHC, La Clínica heat messaging highlight.** La Clínica (Bay Area, 81,000 patients) texted high-risk patients during extreme heat (2+ days over 95°F): 2,608 recipients in 2022; 5,871 + 5,664 in 2023. Patients trusted the clinic more than government; messages were by group (e.g. "CKD, age 65+, diabetes, heart failure…", "children < 5", "pregnant"), in the patient's language.
3. **LA County Public Health, Heat-Related Illness & Mortality Dashboard** (OEJCH). An interactive ArcGIS dashboard; the page has no readable text outside the map app, and **no questionnaire**. Useful as a model for the clinician's heat-illness map view.
4. **NYC Care community-based organizations.** Used as map data (`data/processed/community_resources_nyc.geojson`).

## The questionnaire to model on: CHILL'D-Out (CDC, 2024), from NACHC guide p. 12
Questions in **bold** are the main ones; the others are follow-ups.
- **C – Cooling:** **Working air conditioning?** Can they check and control indoor temperature? An electric fan? Do they know how to find a cooling center?
- **H – Housing:** **Stable housing?** Higher floor of a multi-story building? Indoor air pollutants (smoke, mold)? Air purifier / HVAC filter?
- **I – Isolation & mobility:** **A neighbor, friend or family member who can check on them on hot days?** Does mobility limit getting to cooling?
- **L – eLectricity:** **If heat causes a power outage, a plan for refrigerated medicines and/or electric medical devices?**
- **L – Learning:** **Do they check the daily and hourly forecast to know the hottest time of day? Can they access HeatRisk?** Where do they get heat-health information?
- **D – Drugs:** **Medications that increase heat risk?**
- **Out – Outside:** **Time outdoors on hot days for work, sports or recreation?** Outdoor air pollution exposure? Pollen allergies?

## Other useful pieces of the guide
- **5 Rights of Clinical Communication:** right person, right message, right method, right time, right priority. Good framing for the pitch.
- **Avoid message fatigue:** send only on high-heat days; be specific (name, their risk factors, clear actions); give context (today's heat, why them).
- **Clinician alert sample (BPA):** "Heat-Related Illness Risk Alert," with actions: acknowledge, view Heat Action Plan, order electrolytes / kidney labs, schedule follow-up, print education.
- **CDC heat action plan outline:** stay cool, stay hydrated, watch symptoms, check air quality, manage medicines (storage, power-outage plan).
- **Value sets** (ICD-10, SNOMED, RxNorm) for heat symptoms, clinical risk factors and **medication risk factors**, to build a "High Risk for Heat-Related Illness" registry.
- Third-party texting tools that plug into EHRs: CareMessage, Artera.

## How we scale it up and make it better
| Their approach | Ours |
|---|---|
| CHILL'D-Out is a checklist for staff; no scoring | Same 7 areas as a patient sign-up, scored into **Low / Medium / High** with the reason shown |
| "D – Drugs" is one yes/no question | Filled in automatically from the medication list: **which** medicines, **what each does in heat**, and how they **stack**, backed by the System graph and FDA reports |
| "Do they know how to locate a cooling center?" | We **show** the nearest help (4,484 places), the route, walk time, and "leave by" time |
| "Do they check the hourly forecast / hottest time?" | We **give** them the safest hours today |
| "Someone who can check on them?" | They name the contact, and we **alert that contact** automatically when there's no reply (escalation) |
| "eLectricity: plan for fridge medicines / devices" | Flags patients with fridge medicines or powered devices for a power-outage plan |
| La Clínica: one message per diagnosis group | Message per patient: their medicines, their home, their nearest help |
| Guide for one health center's EHR | One tool any health system can switch on; designed to embed via SMART on FHIR / CDS Hooks |
