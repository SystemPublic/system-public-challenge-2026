# Build plan: The Missing Label

**Written 14 Nov 2026.** Covers everything in `spec.md` (the source of truth).
**Deadline:** Devpost submission **3:00 PM Saturday**. Pitches 3–4 PM.

The steps are in dependency order: each one needs the steps above it. Rachel and Myra divide the work.

**Parallel work:** once Step 1 fixes the knowledge-base format, Steps 5–7 can start on **mock data** while Steps 2–4 fill in the real data. Swap the real data in when it's ready.

---

## Priority focus (Rachel, Sat 14 Nov midday)
The 8-step structure stays. These goals get **more weight** in every step, marked **[FOCUS]** below.

**The goal:** turn the evidence into **actions for clinicians and patients**. Give the clinician a recommendation to pass on, make it easy for the clinician to see, and make it easy for the patient to see.

1. **Screen patients into Low / Medium / High risk buckets.** Inputs:
   - the **intake questionnaire**, which we write by adapting a baseline LA County paper (citation to add)
   - the patient's **heat habits and lifestyle**
   - the **risk of each medication**
   - **how medications stack:** different heat harms add up (e.g. one drug stops sweating and another causes fatigue → both count)
   - whether they're **warned** (label audit) and **what guidance says** (secondary)
2. **Send information by bucket, easily.** The clinician picks a bucket (or patients), and each patient gets a message tailored to their bucket, medicines and situation. **Delivery is by text** through an SMS-provider API (e.g. Twilio-style), not an app notification. The demo can stay simulated (open question in spec §12.3).
3. **Reach out to patients and their caregiver or emergency contact** when a patient is High risk during a heat wave (the escalation algorithm, spec §4.4a).
4. **Connect people to resources: where, what and how to get there.**
   - **Where/what:** cooling centers, libraries, senior centers, community-based organizations and nonprofits (scraped from their websites and directories), and **delivery options** (groceries, medicines) for people who shouldn't go out.
   - **How:** the **best way to get there given the heat**: walking with less heat exposure (shade, cooler blocks), transit with AC, or delivery instead. Show travel time and heat exposure on the way.
5. **The 3D NYC map is the main visual for both the clinician and the patient.**
   - **Heat first:** where it's hottest and where it's cooler.
   - Then **resources** on the map, then the **route** to them.
   - Patient map: "what's near me, what can I use, how do I get there."
   - Clinician map: their patients' risk buckets (aggregated, no individuals on a public view), the hottest areas and resource coverage.
6. **Safest time of day to be outside** during a heat wave: an hourly strip from the forecast (or the replay heat wave), feeding the route timing ("leave before 11 AM").
7. **Clinician can contact the patient through the app** (by text), from the map, the bucket list or the call-first scatter.
8. **EHR-embeddable by design:** built to be launched inside an EHR (SMART on FHIR app launch, CDS Hooks card that opens it, a layout that works in an EHR side panel). For the prototype it's a stand-alone app labeled "designed to embed in the EHR."
9. **One very specific use case** to build and pitch around (to pick; spec §12.3).
10. **Pretty, clean and aesthetic:** light mode, calm colors, lots of white space, one clear action per screen.
11. **Patient map switches between 2D and 3D** (Rachel, Sat 14 Nov). **2D is the default** for older or less tech-comfortable patients: a flat, simple street map with big labels and big tap targets. 3D is one tap away. Same data and route in both.
12. **Simpler for everyone (Rachel's review of the app, Sat 14 Nov ~11:45):** it's too complicated, with too many strange words and graphs. Everything must be readable by non-medical people, and we cut the number of visuals (which ones: to discuss; proposal in spec §5.0).
    - Plain words, no abbreviations or codes on main screens (no FLAG/CHANGE, ROR, "negative-control band," "T1–T8," "jurisdictions," "narrow therapeutic index").
    - Every chart has a title that **says the takeaway** ("Lithium: strong reason to check on patients in a heat wave"), and one message per chart.
    - At most one legend per chart, with 3 colors or fewer.
    - Numbers in words ("about 4 times as many reports as other drugs"), not scores like 0.605.
    - **Outcome first, evidence on click (decided):** main screens show only the outcome (who's at risk, what to do, where to go). The evidence sits behind one click ("Why?" / "See the evidence"): plain reason first, then sources, System graph, FDA reports, badges and scores. Nerd stats keeps the full methods.
    - Guidance quotes in English only (translate the French and German ones).
    - Simpler navigation: a few tabs, not 7 tabs plus a 6-step journey bar.
13. **Medicine Cabinet is scrapped as the main patient view.** It may survive as a small side visual. The patient app's main view is the map plus "my heat plan."

**Sources Rachel sent (Sat 14 Nov), not read in full yet:**
- **Community-based organizations to put on the map:** NYC Care CBO directory, https://www.nyccare.nyc/community-based-organization/ (scrape in Step 2).
- **Baseline for the risk screening / questionnaire:** LA County Public Health, Heat Illness & Mortality, https://ph-lacounty.hub.arcgis.com/pages/heat-illness-mortality
- **Patient heat messaging model:** NACHC, heat-related messaging highlight at La Clínica, https://www.nachc.org/about-nachc/our-work/air-water-and-chemical-exposures/heat-and-health-basics/heat-related-messaging-highlight-la-clinica/
- **EHR embedding model:** NACHC, Heat-Related Illness Management in EHR Systems, https://www.nachc.org/resource/heat-related-illness-management-in-ehr-systems/

**Still required by the challenge (don't drop):**
- [ ] The **visual evidence map** grouped by action bucket, showing evidence strength, prescribers and guidance gaps (Step 5). The new focus is the "counseling and outreach" half of the same challenge sentence.
- [ ] **Meaningful use of the System graph** (25%): medication risk and stacking come from System pathways, plus the 9-question System steps (spec §8.5c).
- [ ] Readable by a **non-specialist**.
- [ ] Accurate: every number traces to a file; no invented data.
- [ ] Devpost submitted by 3:00 PM.

---

## Step 1. Foundations: decisions, keys, data format (first, ~45 min)
Everything else depends on this. **The manual steps (accounts, keys, installs) are in `docs/manual-setup.md`.**
- **Tech stack (decided, spec §4.8):**
  - Python data pipeline
  - Claude Code (in-session) for extraction and coding; no API key
  - JSON knowledge base
  - Next.js + TypeScript + Tailwind (light mode)
  - Apache ECharts
  - react-force-graph (node graph)
  - deck.gl + MapLibre (3D NYC map)
  - Local SQLite database; clinic board and patient app poll every 2–3 s (Supabase dropped Sat 14 Nov)
  - **Simulated push + simulated SMS** on the demo phone (no Twilio, no Web Push)
  - CDS Hooks API route
  - Synthea
  - OpenRouteService
  - NWS / NOAA / openFDA
  - Runs locally on a laptop; the demo phone opens it over the same Wi-Fi (no Vercel)
- **Scaffold:**
  - `npx create-next-app` with TypeScript and Tailwind
  - install echarts, echarts-for-react, react-force-graph, deck.gl, maplibre-gl and better-sqlite3
  - create the SQLite tables (patients, medications, questionnaire, contacts, alerts, check-ins) in `db/`
  - start the dev server on the local network (`next dev -H 0.0.0.0`) and open it on the demo phone
- **Keys (all done):**
  - System API (required, have)
  - openFDA and OpenRouteService (optional, have)
  - Nothing else: no Anthropic, Twilio, Supabase, Vercel or VAPID keys.
  - All in `.env` (gitignored).
- **Install Java** for Synthea.
- **Define the knowledge-base format:** one row per drug. Fields: buckets, 3-step meter + 8-step tier, FLAG/CHANGE, Compass arrow, mechanisms, prescribers, guidance coverage (8 sources), evidence claims with badges, FAERS signal, substitutes, combination partners, patient message blocks.
- **Define the patient record format:** synthetic FHIR patient + medications + questionnaire answers + trusted contacts.
- **Define the health-system config format** (for scalability): catchment ZIPs, clinics, languages, cooling-place source, alert rules.
- **Design tokens:** light mode, 4 bucket colors (colorblind-safe), badge styles, type scale (large for the patient app).
- **Confirm the 15 drugs** (spec §8.7).
- **Output:** schemas in the repo, keys working, a mock knowledge base with 2–3 drugs so UI work can start.

## Step 2. Data collection: scrapers, all in parallel (~1–2 hrs of scripting; can run overnight)
Needs: Step 1 formats and keys.
- **Literature:** PubMed + Europe PMC searches (15 drugs × heat terms); citation chasing from the key reviews (OpenAlex); abstracts saved.
- **System graph** (roles 1, 3 and 4 in spec §8.5a), cached in `data/raw/system/`:
  - drug → mediator and heat → mediator relationships with all their findings, for the 15 drugs
  - **ID normalization** (PMID / PMCID / DOI via the NCBI ID Converter), then System study lookups for every paper we cite
  - full scan of the **Dataverse associations CSV** (drug + heat/temperature variable names) and the list used for the API-vs-Dataverse cross-check
  - neighborhoods around the heat concepts
  - implied-but-untested links
  - **Pulls for the 9 product questions (spec §8.5c).** Query all heat concepts: thermodynamic temperature, hyperthermia, heat illness, air temperature and heat wave. "Heat wave" alone has only 1 relationship.
    - Q5, heat → harm: mortality, EMS, cardiac arrest, hospital mortality
    - Q6, place factors: urban area, air conditioning, income, vegetation, housing
    - Q7, patient factors: cardiovascular disease, kidney disease, age, pregnancy
    - Q8, time-to-help: EMS, cardiac arrest
    - Q9, storage: Dataverse variable-name scan for storage/stability terms, plus a study lookup for every storage paper we cite
    - Q2: drug → same-harm findings to triangulate with FAERS
    - Output: `data/processed/system_question_evidence.csv` with columns question, factor, concept, num_studies, num_findings, newest year, and "not in System" rows.
- **FDA reports (openFDA FAERS):** report counts for each drug × heat reactions (heat stroke, hyperthermia, heat exhaustion, dehydration, hyponatremia, anhidrosis/hypohidrosis) and background counts for the signal math.
- **Guidance:** text of the 8 guidance documents, for automated coding.
- **Climate:**
  - NWS/HeatRisk access
  - NOAA CPC outlooks
  - NOAA GHCN-Daily history (Central Park, LaGuardia; about 30 years)
  - one past NYC heat wave chosen for the replay
- **Place data:**
  - NYC Heat Vulnerability Index
  - NYC Hyperlocal Temperature Monitoring
  - CDC PLACES
  - CDC/ATSDR Social Vulnerability Index (national)
  - CMS Part D (NY and the second demo city)
  - cooling centers
  - NYPL/BPL/Queens libraries and hours
  - NYC Parks rec centers
  - OpenStreetMap cooling places (national)
  - MTA GTFS
  - **[FOCUS] Resources for the map:**
    - NYC Care community-based organizations (scrape https://www.nyccare.nyc/community-based-organization/: name, address, services, languages, hours, phone; geocode)
    - senior centers (NYC Aging older adult centers)
    - other nonprofits and CBO directories as found
    - grocery and medicine delivery options (programs and pharmacies that deliver in each ZIP)
  - **[FOCUS] Heat along the route:** tree canopy / shade, hyperlocal street temperatures, and which subway stations and buses have AC or step-free access.
  - **[FOCUS] Hourly forecast** (NWS hourly gridpoint data) for the safest-time-of-day strip, plus the hourly replay heat wave.
- **[FOCUS] Screening and messaging sources:** read the LA County heat illness page (questionnaire baseline) and the two NACHC pages (patient messaging; heat illness in EHR systems), and save notes to `research-notes/`.
- **Synthetic patients:** Synthea panel tuned to the SBH catchment, plus a second city for the switcher.
- **Output:** raw data files in `data/raw/` with sources and access dates in `data/SOURCES.md`.

## Step 3. Verification and the knowledge base (~1.5–2 hrs)
Needs: Step 2 data.
- **LLM screening and extraction** of the literature (no human review), with counts recorded for the funnel.
- **Automated verification with System as the second extractor** (spec §8.2a, `docs/system-verification.md`):
  1. same paper, same number
  2. same meaning (mislabels, direction)
  3. corroboration across papers (N studies, % same direction)
  4. API vs Dataverse
  5. reverse check for evidence we're missing
  - plus citation-exists and abstract-grounding checks
  - → badges ✓✓ / ✓ / ↗ / ⚠ / ?
- **Scoring:**
  - 8-step tiers → 3-step meter
  - FLAG / CHANGE
  - Compass arrows
  - mechanisms
  - combination rules (stacking, danger pairs, the anticholinergic burden scale)
- **Guidance coding** (LLM, 8 sources × 15 drugs) → guidance coverage and gap badges.
- **Pathways and hidden heat drugs:** chain System links, **validate on known heat drugs first**, flag candidates, check against FAERS signals.
- **FAERS signal:** reporting ratios per drug × reaction, labeled "warning signal, not proof."
- **System answers for the 9 questions (spec §8.5c):**
  - Q2 triangulation: literature + System + FAERS agreement per drug
  - Q3 label gap: System study count × "label mentions heat"
  - Q4 guidance gap: System evidence strength × guidance coverage
  - Q5–Q8: a System-support citation for every threshold, map layer, readiness-score factor and escalation number, or "not in System"
  - Q9 storage coverage: "System has findings from N of our M storage papers"
  - Thin and zero rows go into the gap constellation.
- **Graph audit:** papers in System / extracted / correct / mislabeled; fix list; "10 questions research must answer next."
- **Substitutes:** 2–3 per drug where prescribing sources support them.
- **Output:** the real knowledge base, the audit outputs, and the numbers for nerd stats.

## Step 4. Patient-side logic (~1–1.5 hrs; can run alongside Step 3)
Needs: Step 1 formats, Step 2 place, climate and Synthea data.
- **[FOCUS] Write the intake questionnaire:** adapt the LA County baseline, keep the core 5 (AC, where you spend the day, floor, lives alone, can get to a cool place), and add **heat habits** (time outside, outdoor work or exercise, fluids, fan-only cooling) and **caregiver / emergency contact**. Synthetic answers for the panel.
- **[FOCUS] Risk buckets: Low / Medium / High.**
  - Inputs: questionnaire + habits + medication risk (knowledge base) + **medication stacking** + neighborhood heat.
  - **Stacking:** tag each drug with its heat harms (stops sweating, dehydration/volume loss, low sodium, kidney strain, fatigue/sedation/confusion, low blood pressure). Different harms add up; two drugs with the same harm add up too. Use the System pathways for the drug → harm links.
  - Documented points and cut-offs, shown in nerd stats; the patient sees what put them in their bucket.
- **[FOCUS] Bucket → message and action rules:** what Low, Medium and High patients get (e.g. Low: heads-up text; Medium: text + nearest resource + safe hours; High: text + resource + route + check-ins + caregiver/contact outreach).
- **[FOCUS] Resource matching and best route:** for each patient, the nearest suitable resources (open now, step-free if needed, language), and the best way to get there, scored by **travel time + heat exposure on the way** (walk with shade, transit with AC, or delivery when going out is too risky).
- **[FOCUS] Safest time outside:** hourly heat → "safe window" per day; routes and suggested leave times use it.
- **Escalation algorithm** (spec §4.4a): time budget by risk/HeatRisk; travel time by routing; response-time defaults; contact eligibility; check-in schedule.
- **Cooling-place matching:** nearest open, step-free if needed, "arrive before 11 AM."
- **Message customization rules:** knowledge-base blocks + patient needs (fluid limits, child/caregiver, language).
- **Heat-wave probability:** HeatRisk → CPC outlook → historical odds blend.
- **Output:** functions or APIs the apps call; scores computed for the synthetic panel.

## Step 5. Clinician app, evidence side: journey structure, evidence map, Drug Card, nerd stats (~1.5–2 hrs)
Needs: Step 1 (start on mock data), then Step 3's knowledge base.
- Site shell organized by the **6-stage journey**, with **map / graph / patient view** switches.
- **Periodic table** evidence map (3-step meter, bucket colors, prescriber icons, gap rings, lenses incl. pediatrics).
- **Drug Card (outcome first):** top shows only the plain message and what to do; everything below sits behind "See the evidence": label, FLAG/CHANGE, Compass (arrows only), forest plot, badges, guidance, combinations, substitutes, patient-wording preview, EHR alert preview.
- **Evidence-vs-guidance quadrant** and **evidence-vs-label quadrant** (System study count on one axis).
- **"3 sources agree" marker** on the Drug Card (literature + System + FAERS).
- **"System evidence" chips** on every screen that answers one of the 9 questions (forecast threshold, map layers, scatter tooltip, escalation assumptions, storage card), each showing the study count or "not in System."
- **Nerd stats:** 8-step tiers, evidence funnel, verification badge counts, graph audit and fix list, formulas, sources, limitations, escalation assumptions, and the DND-breakthrough caveat.
- **Live System layer** (role 6): the Drug Card fetches live relationship counts and newest-evidence year from the System API through a cached Next.js API route; API status in nerd stats.

## Step 6. Clinician app, heat and place side + all other visuals (~2 hrs)
Needs: Step 4 logic, Step 2 data (start on mock data).
- **Heat-wave probability bar + context strip.**
- **Call-first scatter** + ranked list + tiers + lasso-to-send.
- **Simulator** and **playbook** (replayed NYC heat wave).
- **[FOCUS] 3D NYC map, the main visual for the clinician:** heat first (hottest to coolest), then patient risk buckets (hexagon-aggregated), resources (cooling centers, libraries, senior centers, CBOs, delivery coverage), and routes. Click an area → its patients by bucket → "text this group." Prescriptions and deliveries stay as extra layers.
- **[FOCUS] Bucket panel:** Low / Medium / High counts, with one-click "send to this bucket" using the bucket's message template.
- **[FOCUS] Safest-time-of-day strip** above the map.
- **Node graph** (evidence X-ray / risk constellation / combination web / gap constellation).
- Remaining catalogue visuals (spec §5): Sankeys, neighborhood × drug heatmap, treemap, body diagram, heat ladder, prescriber swimlanes, calendar heatmap, evidence timeline, "who was studied," audit funnel, combination matrix, heat-day timeline.
- **Team review:** cut visuals that aren't working.

## Step 7. Patient app, alerts and scalability (~1.5–2 hrs)
Needs: Step 4 logic, Step 5/6 shell.
- **[FOCUS] Patient app = map + "my heat plan"** (replaces the Medicine Cabinet as the main view):
  - the patient's bucket and why ("no AC + lives alone + two medicines that both affect heat")
  - the 3D map around them: heat, nearby resources, and the best route with travel time and heat exposure
  - today's safest time to go out
  - what to do, in plain words, plus the delivery option if they shouldn't go out
  - questionnaire, large-type light UI, English + Spanish
  - Medicine Cabinet only as an optional side visual, if time.
- **[FOCUS] Texting:** clinician → patient (and caregiver/contact) by text through an SMS-provider API module. Simulated in the demo unless we decide to wire a real provider.
- **[FOCUS] EHR-embeddable:** SMART on FHIR launch route, CDS Hooks card linking to the patient's plan, and a layout that fits an EHR side panel. Labeled "prototype, designed to embed in the EHR."
- **Mandatory safety alert:** push + SMS. **Both are simulated for the demo:** when the clinician sends the alert, the patient app on the demo phone shows a mock lock-screen push banner and a mock text thread, both labeled "simulated," and the message log records them. Production would use native push (iOS Critical Alerts / Android DND channel) and an SMS provider.
- **Fast-forward control** for the escalation timers, so a 45-minute wait plays in seconds.
- **Trusted-contact escalation** with the computed wait; contact page with the "what to look for / what to do" checklist.
- **Morning cooling-place text; "I'm OK" check-ins; "I feel unwell / no AC" buttons** → clinic call list.
- **Clinic board:** who hasn't checked in; outcome funnel.
- **EHR alert:** CDS Hooks card in the public sandbox (drug and combination triggers).
- **Scalability:** health-system switcher (SBH → second city), "add your health system" setup screen, national view, architecture slide.

## Step 8. Integrate, test, pitch, submit (last ~1 hr; finish by 2:45 PM)
Needs: everything above.
- **End-to-end run** on the replayed heat day: forecast → scatter → send alert → simulated push banner + text appear on the demo phone → escalation → board updates → post-heat-wave follow-up list.
- **Test:** the demo phone reaching the laptop on the venue Wi-Fi (phone hotspot as backup), the simulated push and SMS views, and the second-city switch.
- **Check every headline number** traces to a file; unverified claims are hidden from labels.
- **[FOCUS] Check against the challenge requirements** (the checklist at the top): evidence map present, System use visible, non-specialist readable.
- **Pitch:** 3-minute walkthrough of the real software (no staged scenario), organized by the journey and built around the **one specific use case**. Graph audit + "10 questions" slides. Headline line.
- **Record a backup video.**
- **Devpost:** description, screenshots, repo link, data sources, limitations. **Submit before 3:00 PM.**
