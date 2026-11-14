# The Missing Label: project spec

**Event:** System Public Challenge, NYC, 13–14 Nov 2026. Visualize Challenge 3.
**Team:** Rachel and Myra
**Status:** working spec, reorganized 14 Nov; Myra's notes merged 14 Nov. **This is the source of truth.** The build plan comes later.

**Related docs:**
- **`docs/build-plan.md`: the chronological build plan (8 steps, dependency order)**
- `docs/winning-plan.md`: the first strategy draft; partly superseded, see its header
- `docs/myra-strategy-notes.md`: Myra's session notes, merged here; conflicts are in §12.2
- `docs/graph-check-results.md`, `docs/schizophrenia-sbh-focus.md`, `docs/supply-chain.md`, `docs/system-api-guide.md`: focus notes

**Contents**
1. Problem
2. The challenge and how we meet it
3. Audiences and design principles
4. The product
5. Visuals catalogue
6. Supporting models and content
7. Scale-up ideas
8. Data
9. Evidence model
10. Guardrails: non-goals, success criteria, constraints, risks
11. Add later if time
12. Decision log and open questions

---

## 1. Problem

Many common prescriptions make heat more dangerous. They block sweating, deepen dehydration, push drug levels into toxic ranges, absorb faster, or degrade in storage. Yet:

- **Patients are almost never warned.** Drug labels warn about alcohol and sunlight, rarely about heat waves.
- **Guidance is uneven.** The 8 heat-health guidance sources we reviewed rely mostly on drug lists dating from the 2003 French heat wave. None grades its evidence. None mentions fentanyl patches or SGLT2 inhibitors.
- **The evidence is scattered,** and the System Public Graph holds almost none of it directly:
  - about 15 direct drug × heat findings
  - landmark papers are indexed but filed under vague labels, or have no findings extracted
- **Most heat deaths happen alone at home.** Knowing who is at risk isn't enough. Someone has to act.

## 2. The challenge and how we meet it

**What we're asked to produce** (Visualize Challenge 3, challenge owner Chethan Sarabu, MD, Cornell Tech):
> "A visual evidence map of heat-sensitive medications grouped by type of action, showing evidence strength, the prescribers involved and gaps in current guidance, which a clinician, pharmacist or public health official could use to plan heat-wave counseling and outreach."

**Category criterion (Visualize):** "Design and communication, turning relationships in the graph into compelling and accurate visual stories for a non-specialist audience."

**Our judge:** a pediatrician and clinical informatician who works with SBH Health System (Bronx). He frames this as **climate + health**, and suggested the dosing-direction and supply-chain angles.

### 2.1 Event facts (from Myra's notes, 13 Nov)
- **Deadline:** Sat 14 Nov 2026, **3:00 PM EST** (Devpost).
- **Saturday:** hacking 10 AM–3 PM, pitches 3–4 PM, winners 5 PM.
- **Prizes:** one $2,000 winner per category (Explore, Visualize, Build), plus three $500 honorable mentions across all categories.
- **Judging:** four criteria, **25% each**:
  - meaningful use of the Public Graph
  - insight or usefulness to the user/problem
  - technical execution
  - communication
- **Hosts favor** interdisciplinary problems at the intersection of climate, environment, food and health.
- **The category prize is shared across Visualize:** we're up against Visualize 1 (women's health, owner Verhulst) and Visualize 2 (malaria prevention, owner Amato/PATH). The same five judges score everyone.
- **Likely competition:** evidence dashboards with buckets, bar charts and a guidance table. Competent, but alike. **Our edge:** turn evidence into action, make it physical, and be honest about the graph.

### 2.2 The judges and what each wants (from Myra's notes)
| Judge | Background | What impresses them | What we give them |
|---|---|---|---|
| **Dr. Chethan Sarabu** (wrote our challenge) | Pediatrician, clinical informatics, Cornell Tech | Real clinical workflow; patients and **caregivers**; wearables | EHR alert (CDS Hooks); **child/caregiver case**; pediatrics lens |
| **Stefaan Verhulst** (GovLab, NYU) | Data for public good, responsible data reuse | Gaps turned into a research agenda; responsible data use | **"10 questions research must answer next"**; data-responsibility note |
| **Daniel Gil-Sanchez** (World Bank data) | Data quality, reuse across countries | Reproducible; scales beyond one city | City toggle; versioned sources in `data/SOURCES.md` |
| **Travis Rich** (Knowledge Futures) | Open infrastructure, provenance, versioned datasets | Every claim traceable; giving back | Sources on every line; **open, versioned label dataset**; missing-papers list for the graph |
| **Nalini Edwin** (System comms) | Storytelling about the graph | A story she'd retell; the graph looking valuable | The bottle moment and the headline line (§7.5) |

Only 1 of 5 judges is a clinician, so the main screen must make sense to non-clinicians too.

| Brief asks for | Our answer | Status |
|---|---|---|
| Use the System graph to map the drug-to-heat evidence | Paper-level receipts, two-hop pathways, gap constellation, graph audit (§4.1, 6.4, 7.3) | Planned |
| Action buckets (dose, hold/substitute, monitor, storage) | Master list tagged by bucket; periodic-table evidence map | Data done |
| Evidence strength per bucket | Evidence tiers + FLAG/CHANGE meters | Data done; meters planned |
| Prescribers involved | Prescriber column; prescriber filters and icons | Data done |
| What a prescriber might reasonably change | Drug Card: actions, Heat Dose Compass, substitutes, combination flags | Planned |
| Compare with guidance worldwide; show gaps and conflicts | 8 guidance sources coded; evidence-vs-guidance quadrant | Data done; visual planned |
| *Optional:* wearables, and where the evidence runs out | Wearables "evidence runs out" panel (§6.7) | Research done |
| *Optional:* NYC heat × prescriptions overlap | Heat-Wave Readiness: call-first scatter, simulator, 3D NYC map | Planned |
| Climate + health framing | Climate layer and NOAA forecasts (§6.5, 6.6) | Planned |
| **Our standout** | **The core loop:** see risk → act → someone shows up (§4.0) | Planned |

**Rule:** the evidence map is the core deliverable. Every other feature connects back to it. It must be readable **without a research background**: plain labels, visual encodings instead of statistics jargon, and a one-line "what this means" on every cell. That's how one deliverable satisfies both "non-specialist" and "clinician, pharmacist or public health official."

## 3. Audiences and design principles

### 3.1 Two sides, one knowledge base

| Side | Users | What it is |
|---|---|---|
| **Clinician tool** (primary, the judged deliverable) | Clinicians first (primary care, **pediatrics**, psychiatry, cardiology, endocrinology, nephrology, neurology). Pharmacists and public-health officials use the same views with their own filters. Researchers use the Evidence section. | Evidence map, Drug Cards, Heat-Wave Readiness, action items, Evidence/"nerd stats," EHR alert |
| **Patient app: "My Medicine Cabinet"** | Patients, especially **older adults**, plus caregivers and trusted contacts | Medicine cabinet visual, sign-up questionnaire, **mandatory safety alert**, cooling-place texts, check-ins |
| **System's team** (judges) | — | Proof the graph can power this, plus a precise audit of where it falls short |

**One knowledge base** (one row per drug) feeds both sides, so the clinician card, patient text and labels always agree, at different reading levels.

### 3.2 Clinician-first design
- **The core question is the clinician's own:** "I'm prescribing X, a heat wave is coming. What do I need to know?" Answer it in one card.
- **Readable in about 5 seconds.** Use familiar clinical chart types (risk lists, forest plots, heatmaps), action-bucket colors, plain labels, and no jargon without a tooltip. Less elementary than the patient side.
- **Informatics:** real standards (RxNorm, FHIR MedicationRequest, SMART-on-FHIR-style context, CDS Hooks).
- **Alert fatigue:** fire only when the drug is flagged **and** the forecast is high, never year-round.
- **Pediatrics slice:**
  - topiramate/zonisamide reduced sweating in children (all US zonisamide cases were age ≤18)
  - ADHD stimulants and teen athletes
  - epinephrine auto-injectors and inhalers in heat
  - asthma
  - Thin evidence is shown as a gap.
- **Credible wording:** "considerations for clinicians," never orders. Every claim has a receipt, with evidence tier and confounding labeled.

### 3.3 Visual style
- **Light mode** on both sides. No dark mode.
- **One heat color scale everywhere (Sat 14 Nov):** pale yellow → yellow → orange → vermillion → pink → deep purple (the "Feels like" 88°–116°+ legend). Source of truth: `HEAT_STOPS` in `web/src/components/replay/colors.ts`. The time-lapse, the hour-by-hour strip and the static map's neighborhood heat (HVI 1–5, sampled from the same ramp) all use it.
- **One color per action bucket,** used everywhere (grid, cards, map, cabinet, labels, props):
  - Adjust dose
  - Hold / substitute
  - Monitor
  - Store cool
- **Fill intensity = evidence strength:** solid = strong, pale = weak, outline = mechanism/no study.
- **Ring or "!" badge = guidance gap.**
- Colors are colorblind-safe and always paired with icons or letters.
- Older users on the patient side get large type, high contrast, simple words and big tap targets.

### 3.4 Plain language (from Myra's notes)
The plain version is what's on screen. The technical term sits one click or one tooltip away.

| Technical | Plain version |
|---|---|
| FLAG / CHANGE | "Check on this person" / "Rethink the medicine" *(see choice C7)* |
| Odds ratio 2.43 | "About 2½ times the risk" |
| Hyponatremia, acute kidney injury | "Low salt in the blood," "kidney strain" |
| Anticholinergic | "Medicines that reduce sweating" |
| Evidence tiers | 3-step meter: Strong / Some / Early signs *(see choice C8)* |
| Sankey drug → mediator → heat | Medicine → what it does to your body → why heat makes it worse |

- **Keep detail one click away:** sources, study numbers and the Evidence section stay. A non-specialist reads the plain line; a curious judge clicks through.

### 3.5 Who the client is
- **The client is any hospital or health system.** **SBH Health System (Bronx) is our example client,** the one we zoom in on for the demo. It isn't the only client (§3.7).
- A health system is the right client because it It holds the medication lists, prescribers and patient phone numbers, so it can act. A health department can warn about heat but can't see who takes lithium.
- **Day-to-day users:** psychiatry and primary care clinics, pharmacists, care coordinators.
- **Secondary user:** NYC DOHMH, seeing aggregate neighborhood views only.
- **Core insight:** for many patients, the right response isn't changing the drug but **a phone call and access to cooling** (Cincinnati 1999: working AC OR 0.03). FLAG says who to call; CHANGE says whose prescription to review.

### 3.7 Scalable to any hospital or health system (required, 14 Nov)
**Goal:** prove it isn't a one-off SBH demo, and that any health system could switch it on.

**Why it scales (architecture):**
- **Plugs into any EHR through standards:**
  - SMART on FHIR app (runs inside Epic, Oracle Health/Cerner, athena and others)
  - FHIR R4 to read the patient panel and medications
  - CDS Hooks for the prescribing alert
  - RxNorm for drug codes

  No custom integration per hospital.
- **One national knowledge base:** the drug rows (evidence, buckets, Compass, guidance) are the same everywhere. Local guidance can be added as extra columns.
- **National data sources, so any US location works:**

| Need | National source |
|---|---|
| Heat forecasts | NWS/CDC HeatRisk (by ZIP, nationwide); NOAA CPC outlooks |
| Neighborhood vulnerability | CDC/ATSDR Social Vulnerability Index and Heat & Health Tracker (tract/county, national); NYC Heat Vulnerability Index as the local upgrade where it exists |
| Health conditions by area | CDC PLACES (tract-level, national) |
| Prescribing patterns | CMS Part D (national) |
| Cooling places | OpenStreetMap (libraries, community centers, malls, nationwide) plus local cooling-center feeds where available |
| Routing | OpenRouteService / OSRM on OpenStreetMap; local transit via GTFS (most US agencies publish it) |

- **Per-health-system configuration, not code:** catchment ZIPs, clinics and prescribers, languages, local cooling-place list, escalation contacts, alert rules. A **multi-tenant** setup: each health system's data is kept separate.
- **The patient app is the same everywhere.** Only the health system's name and local resources change.

**How we show it in the demo:**
- A **health-system switcher:** SBH (Bronx) is the default, then switch live to another health system in another city (e.g. a hospital in Phoenix or Houston). The map, heat forecast, cooling places, call list and languages all reconfigure from national data, with no code change.
- An **onboarding / configuration screen:** "Add your health system": pick catchment, connect FHIR, choose languages. It shows how fast a new hospital gets started.
- A **national view:** a US map of health systems or counties ranked by heat risk × heat-sensitive prescribing (Part D + HeatRisk), i.e. "where this matters most next summer."
- A one-slide **architecture diagram:** EHR (FHIR / CDS Hooks) → our knowledge base + national data → clinician tool + patient app.

### 3.6 Data responsibility note (for Verhulst)
- Synthetic patients only.
- Maps aggregated (hexagons / neighborhoods); no individual prescribers named.
- Opt-in consent for patient data and alerts.
- Open sources, versioned.

## 4. The product

### 4.0 The core loop (the standout): see risk → act → someone shows up
1. **See:** the call-first scatter shows who is at risk now. It combines medications, combinations, the questionnaire and neighborhood heat.
2. **Act:** the clinician selects patients and sends the **mandatory safety alert** (through do-not-disturb) with a personalized message and a cooling place.
3. **Someone shows up:** if the patient doesn't acknowledge in time, the **trusted contact** is sent to check on them, timed by the escalation algorithm. Morning texts route people to an air-conditioned public place where others are around.
4. **Close the loop:** the clinic board shows who acknowledged, who is at a cooling place, and who still needs a call. Post-heat-wave lab checks follow.

### 4.0a Priority focus (Rachel, Sat 14 Nov midday)
The structure stays; these goals get more weight. Full task list: `docs/build-plan.md` → "Priority focus."
- **Actionable items for clinicians and patients:** a recommendation the clinician gives the patient, easy for both to see.
- **Risk buckets Low / Medium / High** from:
  - the intake questionnaire (adapted from an LA County baseline)
  - heat habits and lifestyle
  - each medication's risk
  - **medication stacking:** different heat harms add up (e.g. one drug stops sweating, another causes fatigue)
  - whether the patient is warned, and what guidance says (secondary)
- **Send information by bucket**, easily, **by text** through an SMS-provider API (replaces the app notification as the main channel).
- **Outreach to the patient and their caregiver or emergency contact** when High risk during a heat wave.
- **Resources: where, what and how to get there:**
  - cooling centers, libraries, senior centers, community-based organizations and nonprofits (scraped), and grocery/medicine delivery
  - **best route given the heat:** travel time + heat exposure (shade, AC transit), or delivery instead
- **The 3D NYC map is the main visual for both clinician and patient:** heat first (hottest vs coolest), then resources, then routes.
- **Safest time of day to be outside** during a heat wave (hourly strip).
- **Clinician contacts the patient through the app.**
- **EHR-embeddable by design** (SMART on FHIR launch, CDS Hooks card, side-panel layout). The prototype is stand-alone.
- **One very specific use case** to build and pitch around (§12.3).
- **Pretty, clean, aesthetic.**
- **Medicine Cabinet scrapped as the main patient view;** optional side visual at most (§4.5).
- **Still required:** the challenge's visual evidence map (§4.1) and meaningful System use (§8.5a, §8.5c). The new focus is the "counseling and outreach" half of the challenge sentence.

- **Patients as colored dots on the clinician map** (Rachel, Sat 14 Nov): each synthetic patient at their home location, colored by Low / Medium / High.
- **All community resources on the map** (Rachel, Sat 14 Nov): scrape every community-based organization and nonprofit that could help in a heat wave (libraries, senior centers, soup kitchens and food pantries, community centers, NYC Care CBOs, other nonprofits) into `data/processed/community_resources_nyc.geojson`; click a place for details.

- **Colors (Rachel, Sat 14 Nov):** keep the current Okabe–Ito chip palette. Risk groups: **High = orange** (#d55e00), **Medium = yellow** (#f0c419), **Low = blue** (#0072b2). More colors are allowed if they stay in this scheme.

**Sources Rachel sent (Sat 14 Nov): the advisor's models to copy, scale and improve.** Read; notes and the "how we do better" table are in `research-notes/advisor-models.md`.
- NYC Care community-based organizations: https://www.nyccare.nyc/community-based-organization/ (map data to scrape)
- LA County Public Health, Heat Illness & Mortality: https://ph-lacounty.hub.arcgis.com/pages/heat-illness-mortality (screening baseline)
- NACHC, heat-related messaging at La Clínica: https://www.nachc.org/about-nachc/our-work/air-water-and-chemical-exposures/heat-and-health-basics/heat-related-messaging-highlight-la-clinica/ (patient messaging model)
- NACHC, Heat-Related Illness Management in EHR Systems: https://www.nachc.org/resource/heat-related-illness-management-in-ehr-systems/ (EHR embedding model)

### 4.1 Screen 1: Evidence Map (the deliverable)
- **Main view: the "periodic table" of heat-sensitive medications.**
  - Each tile is one drug or class.
  - Tile color = bucket; fill = evidence strength; corner badge = evidence tier; small icons = prescribers; ring = guidance gap.
  - Sort or filter by bucket, prescriber (e.g. pediatrics), or guidance gap.
- **Toggle views:** evidence-vs-guidance quadrant; heat-risk pathways; node graph (§5).
- **Featured example:** schizophrenia / antipsychotics (§6.3).
- Clicking any tile opens the **Drug Card**.

### 4.2 Drug Card (opens from any drug)
Everything about one drug, in tabs or sections:
- **The Missing Label:** a redesigned label with the heat warning: bucket, plain-language line (e.g. "During a heat wave, check lithium levels: dehydration can push them into the toxic range"), prescribers, disclaimer "Prototype. Considerations for clinicians, not instructions."
- **Two meters:**
  - **FLAG:** how strongly this prescription identifies a person to contact
  - **CHANGE:** how strongly the evidence supports changing the drug itself
- **Heat Dose Compass:** does heat make this drug act stronger (↑) or weaker (↓), and through what mechanism? Plus trigger, what to monitor and evidence strength. **Arrows only. No temperature slider, no numbers** (§6.2).
- **Evidence:** the mini forest plot of System findings and the literature, with receipts. Each claim carries a chip: *in System graph* / *literature only* / *guidance only*.
- **Guidance:** which of the 8 sources mention it, and what they say.
- **Combinations:** common risky partners (§6.1).
- **Lower heat-risk alternatives to consider:** 2–3 examples confirmed with prescribing sources, as spring-review considerations, never automatic switches. Each shows mechanism, evidence tier, what's lost by switching, and "never stop abruptly." Candidates to verify:
  - oxybutynin → mirabegron
  - combination/high-risk antipsychotics → review (aripiprazole not elevated in one BC study)
  - topiramate → an anticonvulsant without carbonic-anhydrase activity, per neurology
- **Patient wording preview:** exactly what this drug's patient-app notification says.
- **EHR alert preview** (§4.6).

### 4.3 Screen 2: Heat-Wave Readiness (climate + place)
**Question it answers:** "Is heat coming, and what happens to our patients' medicines if it does?"

- **Heat-wave probability bar + heat context strip** (§6.6): NOAA forecasts and historical odds; 7-day HeatRisk, overnight low and humidity for the selected ZIP (default: SBH area).
- **Call-first scatter (core clinician visual):**
  - each dot is a (synthetic) patient
  - x = **personal** heat exposure (questionnaire home factors + neighborhood heat vulnerability)
  - y = medication heat-risk stack (mechanisms + combination flags)
  - color = main action bucket
  - **The highest-risk patients are unmistakable:**
    - a shaded, labeled top-right "call first" zone
    - the top dots enlarged, outlined and numbered by rank
    - a **ranked call list** beside the chart (rank, patient, drugs, why, action), linked both ways
    - tier bands (call today / this week / routine)
    - headline counts (e.g. "12 patients to call today")
  - **Lasso or select dots → "send alert"** (the core loop)
- **Heat-wave simulator:** "If a heat wave hit **now**, what happens to our current patients' medicines?"
  - Pick severity and length (e.g. 3 days at HeatRisk orange, nights not cooling below 80°F), or replay a real past NYC heat wave.
  - Outputs:
    - patients on flagged drugs, by bucket and FLAG/CHANGE
    - who to call first
    - Compass view (stronger / weaker drugs)
    - workload (calls, level checks)
    - before/after if the plan is followed
- **Playbook (72-hour plan),** in the SBH catchment:
  - **Where:** neighborhoods by Heat Vulnerability Index × CDC PLACES conditions, plus cooling centers and pharmacies.
  - **Who:** prescribers and areas with the most heat-risk prescriptions (CMS Part D, aggregate only).
  - **What:** messages split into "contact" (FLAG) and "consider changing" (CHANGE).
  - **Power-dependent equipment reminders.**
  - **Demo ZIPs:** 10453, 10457, 10458, 10460 and nearby (confirm against SBH's 2025–27 Community Service Plan).
- **3D NYC map** (built by Rachel and Myra; details to come). Layers:
  - heat × prescriptions (hexagon-aggregated, no individuals)
  - climate: street-level and surface heat, heat vulnerability, tree canopy, AC access, cooling centers, HeatRisk by ZIP
  - **supply chain (visual only):** heat-risk deliveries, routes and doorstep exposure as a map layer. Deeper supply-chain work is in §11.
  - bucket-colored toggles (e.g. "everyone on Hold/substitute drugs in high-heat blocks")
- **Talking point:** "Today, the odds of a heat wave are zero, which is exactly when you should run the drill."

### 4.4 Action items
**Principle:** after seeing who is at risk, the clinician acts in one click. The actions get people **cool, seen and connected**, against dying alone at home.

1. **Mandatory safety alert (required, a key part of the product).**
   - The notification **breaks through do-not-disturb and focus filters**, so the patient sees it whatever they're doing. It isn't a siren or a government broadcast.
   - **How:** iOS Critical Alerts (needs Apple's entitlement approval) or Time-Sensitive notifications; Android high-priority channel allowed to bypass DND.
   - **Sent as both an app push notification and an SMS** (decided 14 Nov), so it reaches people without the app or a smartphone too. A voice call stays an optional extra.
   - **Demo (decided Sat 14 Nov): both the push and the SMS are simulated** on the demo phone. The phone opens the patient app, which shows a mock lock-screen push banner and a mock text thread, both labeled "simulated." Production would use native push and an SMS provider.
   - Sent by the clinician, or automatically at high HeatRisk. Opt-in at sign-up. Used only on high-risk days.
   - Message from the knowledge base, e.g. "Heat danger today. Your lithium and water pill make heat riskier. Go somewhere cool by 11 AM. Reply OK."
2. **Trusted contact escalation.**
   - At sign-up, the patient names a trusted family member or friend who lives **close enough**. The distance is computed (§4.4a), not fixed.
   - No acknowledgement within the computed wait → the contact gets: "Please check on [name] in person or by phone," plus a **what to look for / what to do** checklist (confusion, hot dry skin → cool them, call 911).
   - Contact doesn't respond → clinic call list → a human decides on a wellness check.
3. **Morning cooling-place text (the most novel).**
   - Early on a heat-risk day, text the person **a specific air-conditioned public place near them**: library, community center, rec center, gym, mall or official cooling center in their ZIP.
   - Includes name, address, today's hours, walk/transit time, and **"get there before 11 AM, before it gets really hot."**
   - **Why public places:** cool air **and other people around.** If someone gets sick, others notice.
   - **Data:** NYC cooling centers (NYC Emergency Management / Open Data), NYPL / BPL / Queens Library branches and hours, NYC Parks rec centers. Check open that day and step-free if needed (questionnaire Q5).
4. **Scheduled "I'm OK" check-ins** during a heat wave (e.g. 10 AM and 4 PM; one tap or reply). Silence triggers escalation.
5. **Live "who hasn't checked in" board** for the clinic, ranked like the call-first scatter.
6. **Neighbor buddy match** for people with no qualifying trusted contact (NYC's "Be a Buddy" program, *verify*).
7. **Get AC before summer:** help apply for **NYS HEAP cooling assistance** (free or discounted AC), triggered by "no working AC."
8. **Indoor temperature check:** a thermometer card or home sensor; a hot room plus no check-in escalates.
9. **Post-heat-wave follow-up:** auto-schedule lithium level, sodium and kidney-function checks for flagged patients (clinician-approved).
10. **Tailored fluid advice:** "drink more water" for most, but not blanket advice for fluid-restricted heart-failure patients or thiazide/SSRI users at risk of low sodium. Clinician sets this per patient.
11. **Languages:** English and Spanish (SBH area).

**Safety rules for all actions:**
- Opt-in consent.
- Escalation stops at a **human** before any 911 or wellness-check request.
- No dose instructions to patients.
- Alerts only on high-risk days.
- Every action logged (audit trail and nerd stats).

#### 4.4a Escalation timing and contact distance: derived, not guessed
Both "how long to wait" and "how close the contact must be" come from a **time budget** set by medical evidence.

1. **Time budget T_max:** the maximum time from a missed acknowledgement to a person physically present.
   - Exertional heat stroke: cool to about 39°C within **30 min** of collapse.
   - Classic heat stroke: mortality **more than halves** if cooled below 38.9°C **within an hour** of presentation ([PMC10227888](https://pmc.ncbi.nlm.nih.gov/articles/PMC10227888/); [Bouchama et al., Crit Care 2007](https://link.springer.com/doi/10.1186/cc5910)).
   - Delayed treatment mortality up to about 80% vs about 10% with immediate cooling (illustrative, [Medscape](https://emedicine.medscape.com/article/166320-overview)).
   - One cohort averaged 8.3 h from onset to treatment ([PMC12208087](https://pmc.ncbi.nlm.nih.gov/articles/PMC12208087/)).
   - **Starting values** (refine from primary studies): very high risk / HeatRisk ≥3 / hot home **45 min**; high **60 min**; medium **90 min**. Leave time for cooling and EMS.
2. **Split:** T_max = T_wait (patient acknowledges) + T_contact (contact responds) + T_travel (contact arrives).
3. **T_travel = real travel time, not miles.**
   - Route by walking, transit (MTA GTFS) or driving at that time of day (OpenRouteService / OSRM).
   - Older walkers: about **0.77–0.9 m/s**, not 1.2 m/s ([Western et al., Age and Ageing 2025, PMC12682371](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12682371/)).
4. **T_wait and T_contact from response-time data:**
   - Start at the 90th percentile of published notification response times: Pielot et al. MobileHCI 2014 (DOI 10.1145/2628363.2628364), Pielot et al. 2018 (about 795k notifications), Mehrotra et al. CHI 2016. *Medians still to extract.*
   - Then learn each person's own p90 from check-ins.
   - Re-send the alert once at the halfway point.
5. **Contact eligibility:** T_travel ≤ T_max − p90(patient) − p90(contact).
   - It's computed per patient: tighter for higher risk and hotter days.
   - No one qualifies → ask for a closer contact, or offer a buddy, plus priority call list.
   - Several contacts are allowed; the fastest is alerted first.
6. **Check-in frequency:** the worst-case time before anyone notices = check-in interval + T_max. More check-ins at 2–6 PM for very high risk; an indoor sensor can trigger one early.
7. **Benchmarks:**
   - France's heat-wave registers: regular calls; no answer → alert → possible in-person check by police or firefighters; exact timings not found ([Connexion France](https://www.connexionfrance.com/practical/how-to-sign-up-for-frances-heatwave-welfare-check-register/797620); [Paris REFLEX](https://www.paris.fr/pages/en-ligne-avec-les-personnes-fragiles-pendant-la-canicule-8156)).
   - NYC EMS response times (NYC Open Data).
8. **Research to do:**
   - primary classic-heat-stroke time-to-cooling cohorts
   - notification-study medians
   - older-adult phone response times
   - medical-alert (PERS) escalation standards

### 4.5 Patient app: "My Medicine Cabinet"
> **Sat 14 Nov: scrapped as the main patient view** (Rachel). The patient app's main view is now the **map + "my heat plan."** The map **switches between 2D and 3D; 2D is the default** for older or less tech-comfortable patients (flat street map, big labels, big tap targets), and 3D is one tap away. The plan shows the bucket and why, nearby resources, the best route, the safest time outside, and what to do. The cabinet below may survive as a small side visual if time allows.

**Why this design (original):** a cabinet of familiar bottles is easy to understand, especially for **older adults, who are most likely to die in heat.**

- **The cabinet:** a shelf of the patient's own medicines, colored by bucket.
- **Medicines added two ways:** the patient adds them, or they're **added automatically** from the pharmacy or clinic record (FHIR MedicationRequest / dispense data; the synthetic panel in the demo).
- **When heat is forecast,** bottles glow by risk, and notifications follow a fixed plain-language template:
  > "⚠️ Heat warning for **[drug]**: in hot weather it can **[effect in plain words]** because **[why]**. Watch for **[symptoms]**, and **[safe action]**."
- **Combinations** show as one combined warning.
- **Personal flow:** *my medicines → what heat does to each → what to do* (a simplified Sankey).
- **Notification timing:** follows the probability bar and HeatRisk (about 3 days before orange, the day of, after), plus the mandatory safety alert, cooling-place texts and check-ins (§4.4).
- **Safety:** no dose changes, ever. Every message ends with "talk to your doctor or pharmacist." Text is pre-reviewed per drug and comes from the shared knowledge base.

#### 4.5b Customized patient messages (decided 14 Nov; method to be worked out)
Every message is **tailored to the patient's needs**, never generic (e.g. no blanket "drink more water").

**Inputs:**
- their medications and combinations
- diagnoses (e.g. heart-failure fluid limits, low-sodium risk)
- questionnaire answers (AC, floor, living alone, mobility, where they spend the day)
- age (child → parent/caregiver wording)
- language
- neighborhood heat and forecast
- clinician-set flags (e.g. "fluid restricted")

**Approach options:**
1. **Rules from the knowledge base** (starting point): message blocks per drug, mechanism and situation, assembled by documented rules. Safe and checkable.
2. **Learning from data** (later): learn which wording, timing and channel get acknowledged, per person or by group, from response and check-in history. This applies to **delivery** (when, how, which words), never to the medical content.
3. Clinician review of the medical rules. An LLM may draft wording variants, but every variant is pre-approved, never generated live.

**Safety:** no dose advice; fluid advice only within clinician-set limits; every message ends with "talk to your doctor or pharmacist."

#### 4.5a Sign-up questionnaire
**Why:** most heat deaths happen at home, and neighborhood data can't see inside a home.
- NYC heat mortality reports: most heat deaths are at home; lack of home cooling is key.
- BC 2021: most who died were alone at home.
- Cincinnati 1999: working AC OR 0.03.
- Chicago 1995 (Semenza et al., NEJM 1996, *verify*): living alone, not leaving home and being bedbound raised risk; AC protected.

**Sat 14 Nov update:** the questionnaire is modeled on **CDC's CHILL'D-Out questionnaire** (Cooling, Housing, Isolation & mobility, eLectricity, Learning, Drugs, Outside), found in the NACHC EHR guide the advisor sent (`research-notes/advisor-models.md`; the LA County link is a dashboard with no questionnaire). We add **heat habits** (time outside, outdoor work or exercise, fluids, fan-only cooling) and a **caregiver / emergency contact**, and output a **Low / Medium / High** bucket instead of four levels.

**Known from the pharmacy or clinic record (not asked):** age, medications, diagnoses (heart, kidney, diabetes, mental illness, dementia), pregnancy.

**Core 5 questions (team decision):**
1. Do you have working AC at home?
2. Where do you spend most of your day? (home / indoors with AC / outdoors or physical work)
3. What floor do you live on?
4. Do you live alone?
5. Could you get to a cool place if you needed to?

**Also needed for the action items:** ZIP / address; trusted contact(s) (name, phone, address or ZIP); opt-in to the safety alert; text / app / call preference; language.

**Optional, asked over time:**
- Does the AC work, and do you use it (cost)?
- Do windows open? How hot does your home get?
- Does someone check on you?
- Do you leave home most days?
- Do you use power-dependent equipment? Fridge medicines?
- Do you get mail-order medicines, and where are they left?
- Outdoor work or exercise?
- Stable housing?
- Do you know the signs of heat illness?

**How it's used (transparent):**
- Answers + medication risk + neighborhood heat → a **personal heat readiness level** (low / medium / high / very high).
- The patient sees which answers drove it, e.g. "no working AC + lives alone + on lithium and a diuretic."
- Fixed, documented points per factor, weighted by the evidence above. The formula is shown in nerd stats.
- **Feeds the call-first scatter's x-axis** (personal exposure).
- **Triggers help:** HEAP AC, nearest cooling place, buddy offer, delivery to an indoor drop.
- **Re-asked every spring.**

**Privacy:**
- Every question is optional, with its purpose shown.
- Shared with the care team only with consent.
- Collect the minimum; allow deletion.
- **The demo uses synthetic answers only.**

### 4.6 EHR alert (CDS Hooks): should-have
- A working alert in the public CDS Hooks sandbox.
- Fires when a flagged drug **or flagged combination** is ordered while the forecast is high (e.g. "adding a diuretic to a patient on lithium during a heat forecast").
- Uses RxNorm codes, FHIR MedicationRequest, and a "heat-risk patient list" for panel management.

### 4.8 Tech stack (picked 14 Nov)
Chosen for speed (5 hours, two people), open source, and one language per layer.

| Layer | Choice | Why |
|---|---|---|
| **Data pipeline** | **Python 3** + pandas + requests (scripts in `scripts/`) | Already used for the graph checks; best for APIs and CSVs |
| **LLM for screening, extraction, guidance coding, message wording** | **Default: Claude Code does these steps inside our session** (it reads the scraped abstracts and writes the JSON); **no API key needed.** Optional: the Claude API, only if we want the pipeline fully scripted and re-runnable without a Claude Code session | No extra account for the hackathon |
| **Knowledge base** | Versioned **JSON files** (`data/kb/`) generated by the pipeline | Simple, diffable, easy to publish as the open dataset |
| **Web app (clinician + patient)** | **Next.js (React, TypeScript) + Tailwind CSS**, light mode | One codebase for both sides; API routes built in |
| **Charts** | **Apache ECharts** (via `echarts-for-react`) | One library covers scatter, Sankey, treemap, heatmap, calendar, forest-style plots and graphs, so all 21 visuals can be prototyped quickly |
| **Node graph** | **react-force-graph** (2D; 3D optional) | A real interactive force-directed "CS" node graph |
| **3D NYC map** | **deck.gl + MapLibre GL JS** with OpenStreetMap / OpenFreeMap vector tiles (3D building extrusions) | Open source, no token, 3D buildings, hexagon and arc layers |
| **Database + live updates** | **Local SQLite (decided Sat 14 Nov; Supabase dropped)** behind the Next.js API routes, using **Node's built-in `node:sqlite`** (no better-sqlite3: it needs a native build on Windows; decided Sat 14 Nov). **The database holds live demo state only** (alerts, check-ins, simulated push/SMS log, live questionnaire sign-ups, fast-forward clock: `db/schema.sql`, `web/src/lib/db.ts`); patients, meds, questionnaire and contacts stay in `data/processed/synthetic/` and load through `lib/patient`. The clinic board and the patient app **poll every 2–3 seconds**, so a tap on the demo phone shows up on the clinician laptop almost instantly. The phone opens the app from the laptop's server, so both share one database. Production: a hosted Postgres per health system | Patients, questionnaire, contacts, check-ins, alerts. No account needed |
| **Scheduled escalation timers** | A small Node timer in the app server; **demo has a "fast-forward" control** so a 45-minute wait plays in seconds | Runs the T_wait → contact → clinic escalation |
| **SMS** | **Demo: simulated (decided 14 Nov).** The alert appears in a mock text thread on the demo phone and in the message log, labeled "simulated SMS." Production: an SMS provider (e.g. Twilio) | No account needed |
| **Push notifications** | **Demo: simulated (decided Sat 14 Nov).** The patient app on the demo phone shows a mock lock-screen push banner (styled like a real notification, labeled "simulated") when the clinician sends the alert. Production: native app with iOS **Critical Alerts / Time-Sensitive** and an Android DND-bypass channel | No Web Push, VAPID keys or HTTPS tunnel needed |
| **EHR alert** | **CDS Hooks** service as a Next.js API route; tested in the public CDS Hooks sandbox; FHIR R4 JSON | Real informatics standards |
| **Synthetic patients** | **Synthea** (Java CLI) → FHIR R4 bundles | Realistic multi-drug panels for SBH and a second city |
| **Routing** | **Default: no-key OSM routing** (routing.openstreetmap.de, walking and driving); OpenRouteService (free key) optional, for isochrones | Trusted-contact eligibility; cooling-place travel time |
| **Weather** | **api.weather.gov** (NWS); **WPC HeatRisk** data files; **NOAA CPC** outlooks; NOAA GHCN-Daily | All free; NOAA only |
| **FDA reports** | **openFDA** FAERS API (no key needed at our volume, about 300 requests) | Warning-signal counts |
| **Hosting** | **Run locally** on a laptop; the demo phone opens the app over the same Wi-Fi (phone hotspot as backup). GitHub repo + video for Devpost. No Vercel (Sat 14 Nov) | No extra accounts |
| **Required keys** | **System API only** | Everything else is optional |

**Caveat on "breaks through do-not-disturb":** a web app (PWA) **can't** bypass DND, and SMS only does if the sender is allowed through. True DND breakthrough needs a native app: iOS Critical Alerts require Apple's entitlement; Time-Sensitive notifications need the user's permission; Android needs a channel the user lets bypass DND.
- **For the demo:** push and SMS are both simulated on the demo phone (labeled), and the native DND-breakthrough path is shown on a slide or architecture diagram. An Expo build on an Android phone is §11, only if time allows.
- Be upfront about this in nerd stats.

**Repo layout (proposed):**
- `scripts/`: pipeline
- `data/raw/`, `data/kb/`: data
- `app/`: Next.js app: `/clinician/*` and `/patient/*` routes; `/api/cds-hooks`, `/api/alerts`, `/api/escalation`
- `db/`: SQLite schema and seed (synthetic panel)
- `docs/`: notes

### 4.7 Screen 3: Evidence / "nerd stats" (Methods & Receipts)
A clearly labeled section that shows our results are legit:
- **Evidence funnel:** records searched → screened → included.
- **Graph audit:** in System / findings extracted / correct / mislabeled, plus System extraction accuracy.
- **Data quality:** citations verified %, hand-check accuracy, guidance-coding agreement (Cohen's kappa).
- **The scoring formulas:** evidence score, FLAG/CHANGE, personal readiness level.
- **Per-drug forest plots and study lists.**
- **Data sources** with versions and access dates; live System API status and counts.
- **Escalation-timing assumptions** (§4.4a).
- **Known limitations and confounding.**

## 5. Visuals catalogue

### 5.0 Simplify: fewer visuals, plain words (Rachel's review, Sat 14 Nov ~11:45)
**Rachel's verdict on the first build:** the graphs aren't clear when you look and click; there are too many strange words and too many strange graphs. **It must be readable by everyone, not just clinicians. Cut the number of visuals** (which ones: to discuss).

**What the review found (app at localhost:3000, ~11:45):**
- **Words:** main screens show FLAG / CHANGE, "Score 0.605: association strength 0.26 × severity 1.0," "ROR 4.373," "negative-control band," "T1–T8 best evidence tier," "8/8 jurisdictions," "narrow therapeutic index," "HeatRisk 4 Magenta," and untranslated French and German guidance quotes.
- **Charts:** the evidence map tile packs five encodings (color, fill, corner badge, icons, ring) plus letters M/A/H; the "Medicines by action and evidence" bar chart is hard to read; the Readiness page is mostly "not built yet" boxes.
- **Navigation:** 7 top tabs plus a 6-step journey bar, so it's unclear where to start. "Evidence Map" lives at `/map`, which will clash with the real map.

**Outcome first, evidence on click (Rachel, Sat 14 Nov, decided):** a clear, simple visual matters more right now than showing how accurate it is.
- Every screen shows **only the outcome**: who's at risk, what to do, where to go.
- The evidence is **not shown up front**. It sits behind one click ("Why?" / "See the evidence") for the clinician who wants to know more.
- Behind the click: the plain-language reason first, then the details (sources, System graph, FDA reports, badges, scores). Nerd stats stays for the full methods.
- The evidence work isn't dropped. It's still there for judges who click, and for the System-use score, but it no longer crowds the main view.

**Plain-language rules (apply everywhere):**
- No abbreviations or codes on main screens. Say "check on this person" and "consider changing the medicine," not FLAG / CHANGE.
- Each chart gets a **title that states the takeaway**, one message per chart, at most one legend, and 3 colors or fewer.
- Numbers in words ("about 4 times as many heat reports as other medicines"), never raw scores.
- Scores, formulas, tiers and receipts go to nerd stats or behind "Show the evidence."
- Guidance quotes translated to English.
- Aim for about an 8th-grade reading level; the patient side simpler still.

**Proposed keep list (to discuss; about 6 visuals instead of 21):**

| Keep | For | Why |
|---|---|---|
| **1. Heat + resources map** (2D/3D switch) | Both | The main visual: where it's hot, what help is near, how to get there |
| **2. Risk buckets (Low / Medium / High)** with "text this group" | Clinician | Replaces the call-first scatter: easier to read, and it's the action |
| **3. Medicine chart** (simplified evidence map) | Clinician | Required by the challenge: one row per medicine, grouped by what to do, evidence as Strong / Some / Early in words, who prescribes it, ✓/✗ for "label warns" and "guidance says what to do" |
| **4. "How heat and medicine add up" picture** | Both | One simple System-graph picture: medicine → body effect (dehydration, low salt, no sweating) ← heat. Keeps the graph use visible and also explains stacking |
| **5. Safest time to go outside** (hourly strip) | Both | One glance: green hours, red hours |
| **6. Patient "my heat plan"** | Patient | Bucket and why, nearest help, route, safe time, what to do |

**Proposed cut or move to nerd stats:** call-first scatter, Heat Dose Compass, FLAG/CHANGE meters, forest plot, Sankeys, node graph (nerd stats only), treemap, neighborhood × drug heatmap, body diagram, heat ladder, prescriber swimlanes, calendar heatmap, evidence timeline, "who was studied," audit funnel (nerd stats), combination matrix, heat-day timeline, Medicine Cabinet, the 6-step journey bar.

### 5.1 Full catalogue (14 Nov; being cut down per §5.0)
**Decision (14 Nov): prototype all of these.** The team will look at each and cut the ones that aren't effective. The **node graph is required**, the **call-first scatter is chosen**, and the **medicine cabinet is the patient-side centerpiece**.

| # | Visual | Side | What it shows |
|---|---|---|---|
| 1 | **Periodic table** of heat-sensitive medications | Clinician | Main evidence map (§4.1) |
| 2 | **Call-first scatter** + ranked list | Clinician | Who to call, ranked (§4.3) |
| 3 | **Medicine cabinet / heat shelf** | Patient | My medicines glowing by risk (§4.5) |
| 4 | **Node graph (required):** one interactive explorer with modes: Evidence X-ray (drug → mediator → heat harm from System), risk constellation (neighborhoods ↔ drugs ↔ mechanisms, arranged by heat vulnerability), combination web (one patient), gap constellation (implied-but-untested links, dashed) | Clinician | The "graph as a graph" |
| 5 | **Evidence × guidance quadrant** | Clinician | Where guidance is missing or out of step; dots colored by bucket, sized by severity, hollow = null |
| 6 | **Pathway Sankey** | Clinician | Drug → mediators → heat harms |
| 7 | **Flow Sankey** | Both | Clinician: neighborhoods → drugs → mechanisms → actions. Patient: my medicines → heat effect → what to do |
| 8 | **Mini forest plot** | Clinician (Drug Card) | Findings for one link, grouped by statistic type, with receipts |
| 9 | **Neighborhood × drug heatmap** | Clinician | Where the lithium patients in the hottest blocks are, with no map needed |
| 10 | **Treemap** | Clinician | Patients at risk, nested neighborhood → drug |
| 11 | **Body diagram** | Both | Skin/sweat, kidneys, blood, brain, plus "outside the body" for storage; drugs pinned to where heat hits |
| 12 | **Heat ladder** | Clinician | Drugs on a temperature axis where a threshold is known (e.g. hyponatremia above about 15°C); most in an "unknown threshold" zone |
| 13 | **Prescriber swimlanes** | Clinician | "Which of these are mine?" by specialty |
| 14 | **Calendar heatmap** | Clinician | Next 3 months by week: heat-wave probability, overlaid with refill and delivery dates |
| 15 | **Evidence timeline** | Clinician | When each drug's heat evidence accumulated (System dates) |
| 16 | **"Who was studied" bars** | Clinician | Share of evidence that includes children, women, older adults, non-US |
| 17 | **Graph audit funnel** | Evidence section | Papers found → in System → extracted → correct / mislabeled |
| 18 | **Combination matrix** (15 × 15) | Clinician | Every drug pair: shared mechanism / known evidence / untested (§7.4) |
| 19 | **Heat-day timeline** | Clinician / demo | One heat day replayed: forecast → texts → check-ins → escalation → help arrives (§7.1) |
| 20 | **3D NYC map** | Both | Heat, prescriptions, cooling places, deliveries (§4.3) |
| 21 | **Heat-wave probability bar + context strip** | Both | Is heat coming (§6.6) |

**Directed-edge rules (node graph and Sankeys):**
- Arrows go from **drug or heat → harm.** We set the direction ourselves and don't trust the graph's source/target order: System warns about direction errors, and some links are stored backwards, e.g. "hyponatremia → hydrochlorothiazide."
- Solid = higher risk; dashed/hollow = no effect found; different color = lower risk; thickness = number of studies.
- Arrows mean "linked to," not "causes." Say this in the legend.
- The main evidence map stays a grid; the network lives in the node-graph view.

## 6. Supporting models and content

### 6.1 Multiple medications (systems thinking)
Risk is assessed **per patient across all their medications.**

**What the evidence says about combinations:**
- 2+ antipsychotics: OR 4.05 vs monotherapy 1.79 for heat-dome death (BC 2021)
- ACE inhibitor + diuretic started together: highest dehydration/heat-illness admission ratio, 2.79 (Kalisch Ellett 2016)
- Thiazide + SSRI: may cause about 30% of hyponatremia admissions (Swedish data)
- The "triple whammy" (diuretic + NSAID + ACEi/ARB): **null** for in-hospital AKI in heat (Mangoni 2017). Shown honestly.
- Polypharmacy / anticholinergic burden: linked to heat-wave admission, not death
- Most combinations are untested in heat, and that's shown as a gap.

**How we combine (no fake math):**
- Group drugs by mechanism: sweat blocked, fluid/salt loss, kidney-cleared buildup, faster absorption, sedation, blood-pressure drop, storage-sensitive.
- Flag **same-mechanism stacking** (sweat blockers summed with the Anticholinergic Burden scale).
- Flag **cross-mechanism danger combos** (fluid-losing drug + kidney-cleared narrow-margin drug like lithium, digoxin or dabigatran).
- Flag **known combos with direct evidence.**
- **No single multiplied risk score.**

**Where it appears:** call-first ranking, Drug Card "risky partners," patient combined warning, combination web and matrix, EHR alert. The synthetic panel (Synthea) generates realistic multi-drug lists.

### 6.2 Heat Dose Compass (from the judge's input)
- For each drug: ↑ stronger in heat (insulin absorption, patches, lithium/digoxin buildup, added blood-pressure drop), ↓ weaker (degraded epinephrine or insulin, patches peeling off, unreliable inhalers), or ↕ depends.
- Each also shows mechanism, trigger (forecast heat, fever, exertion, heat on a patch), what to monitor and evidence strength.
- **No numbers, and no temperature slider** (dropped 14 Nov). There isn't enough data: no validated calibration exists, and wearable core-temperature estimates aren't validated in medicated patients.
- **Evidence:** Vanakoski & Seppälä, *Clin Pharmacokinet* 1998 (PMID 9571303): heat changes oral-drug kinetics only a little but raises levels from transdermal and subcutaneous drugs. Human data are very limited.
- **Talking point:** "We show direction, not doses, because that's what the evidence supports."

### 6.3 Featured case: schizophrenia and SBH
- **Illness and medication both contribute,** plus poverty and isolation:
  - BC 2021 heat dome (Chen et al., *Sci Rep* 2025): any antipsychotic OR 2.43; 2+ OR 4.05; haloperidol 3.31; clozapine 2.63; aripiprazole not elevated; income assistance 2.45
  - Japan within-person study: no added drug effect
  - Cincinnati 1999: many who died weren't taking their psychotropics; AC was the strongest protection
  - Bark 1998, Bronx Psychiatric Center: psychiatric patients died at about twice the general population's rate in heat waves, and prevention after 1979 reduced it
- **Label:** FLAG high, CHANGE moderate. Review combination therapy in spring; check-ins and cooling access during heat; never stop abruptly.
- **SBH:**
  - Bronx safety-net system serving mostly Medicaid and uninsured patients
  - SBH Behavioral Health: 160,000+ visits a year; 49 adult psychiatric beds; psychiatric emergency care in an ED with about 100,000 visits a year
- Details in `docs/schizophrenia-sbh-focus.md`.

### 6.4 Heat-risk pathways and hidden heat drugs
- **Pathway:** drug → (dehydration / low sodium / kidney injury / blood pressure) ← heat, built from System findings on both sides.
- Validated against known heat-risk drugs ("rediscovers X of Y").
- Drugs with strong pathways on no guidance list are **flagged as hidden heat drugs**. They're confirmed against the literature before any claim is made.
- **Known blind spot:** anticholinergics act through sweating, and the graph has no anticholinergic × sweating findings. Say so.

### 6.5 Climate layer
**Purpose:** climate data exists so medicines are prescribed, taken, stored and delivered safely despite the heat. It's near-term operations, not climate prediction.

| Horizon | What's needed | Data | Action |
|---|---|---|---|
| This season / next few years | When heat season starts, expected heat days, recent trends | NOAA 1991–2020 normals; recent NYC summers (NOAA GHCN-Daily, Central Park / LaGuardia) | Spring medication review; summer delivery rules |
| Week | Is a heat wave coming, how bad, and do nights cool? | NWS/CDC **HeatRisk** 0–4 by ZIP ([WPC HeatRisk](https://www.wpc.ncep.noaa.gov/heatrisk/)); NWS API; advisories; heat index | Outreach list, safety alert, EHR alert (≥ orange) |
| Day / hour | Hourly temperature, humidity, overnight low | NWS hourly forecast | Cooling-place timing ("before 11 AM"); check-ins |
| After | Did the heat wave just end? | Same | Post-heat-wave labs |

**Where heat lands:**
- NYC Heat Vulnerability Index
- NYC Hyperlocal Temperature Monitoring: about 475 street-level sensors, hourly, dataset `qdq3-9eqn`; **thin Bronx coverage, shown as a gap** ([data.gov](https://catalog.data.gov/dataset/hyperlocal-temperature-monitoring))
- urban heat island data story and mobile sensor routes ([DOHMH](https://a816-dohbesp.nyc.gov/IndicatorPublic/data-stories/urban-heat-island/))
- Landsat surface temperature
- tree canopy
- NYC heat mortality reports (about 525 heat deaths a year citywide, mostly at home); heat-related ED visits

**Things that compound heat:** nights that don't cool, humidity, air quality (AirNow), power outages.

**In the product:** the heat context strip on every view; temperature thresholds shown where studies report one (most have none, shown as a gap); Compass and alerts tied to the HeatRisk level.

### 6.6 Heat-wave forecasting: NOAA only
- Day-by-day forecasts lose skill after about 10–14 days, so further out we give **odds, not dates.**

| Time ahead | Source | Gives |
|---|---|---|
| 0–7 days | NWS/CDC HeatRisk; NWS API | Heat-risk level by ZIP, daily |
| 6–14 days | NOAA CPC 6–10 / 8–14 day outlooks | Probability above / near / below normal |
| 3–4 weeks | CPC week 3–4 outlook | Same, coarser |
| 1–3 months | CPC monthly and seasonal outlooks | Same |
| Any date | NOAA history (about 30 years) | Historical odds of a heat wave around this date |

- **Probability bar:** the forecast where available, otherwise the CPC outlook shifting the historical odds. On 13 Nov it reads about 0%, so it's a drill; in July it's a live readiness check. Colors match HeatRisk; the source is labeled.
- Heat-wave definition: NWS NYC advisory criteria (*to confirm*).
- **No custom forecasting ML.**

### 6.7 Wearables: where the evidence runs out
- Heart-rate-based core-temperature estimators (e.g. ECTemp) are validated only in healthy soldiers, athletes and firefighters, and miss many readings above 39°C.
- They've never been validated in people on beta blockers, stimulants or anticholinergics, or in older, dialysis, MS or pregnant users.
- Shown as an "evidence runs out" panel linked from the Compass.

### 6.9 The medicine's whole journey (from Myra's notes): organizes the site
Covers supply chain, clinician and patient in one picture: the systems thinking the hackathon favors. **Decided (C5):** the site is organized by these 6 stages, and each stage can also be viewed as a **map view** (3D NYC), a **graph view** (node graph) and a **patient-facing view** (Medicine Cabinet).

| Stage | What heat does | Clinician / system action | Patient / caregiver action |
|---|---|---|---|
| **1. Prescribe** | Some drugs add heat risk | EHR alert during a heat forecast; review combinations before summer | — |
| **2. Dispense / ship** | Mail-order packages go out of range (every shipment in the Utah study) | Pharmacy holds heat-sensitive mail orders or ships insulated during heat alerts | "Bring the package in right away" |
| **3. Store at home** | Insulin and EpiPens degrade; outages spoil refrigerated drugs | Refill reminders before heat season; outage plan | Thermochromic bottle: "Too warm? Here's what to do" |
| **4. Take it** | Insulin absorbs faster; patches release more drug; lithium builds up | Heat Dose Compass | Plain label line |
| **5. Watch for warning signs** | Signs of heat illness differ by drug | Call list sorted by risk | "I feel dizzy" button that reaches the clinic |
| **6. After the heat wave** | Refill and ER surges after outages (Hurricane Beryl, Houston) | Follow-up list; post-heat-wave labs | Check levels if advised |

Sources: `research-notes/` and `report/Prescribed drug heat risks.md`. Verify before slides.

### 6.8 Synthetic patient panel
- **Demo:** Synthea (open-source synthetic FHIR patients), tuned to the SBH catchment's ages and conditions (CDC PLACES, Census), with multi-drug lists and synthetic questionnaire answers.
- **Population view:** CMS Part D aggregates.
- **Real deployment:** a clinic connects its own FHIR panel.
- No real patient data is used at the hackathon.

## 7. Scale-up ideas (the four strengths)

### 7.1 Core loop: see risk → act → someone shows up
- **Show the real software, not a staged scenario** (decided 14 Nov). No role-play with judges. Demo the working product: forecast → call-first scatter → send alert → simulated push banner + text appear on the demo phone → escalation logic → clinic board updating. The simulated messages are clearly labeled; the software around them is real. *(Test the demo phone on the venue Wi-Fi beforehand.)*
- **Heat-day timeline replay (visual 19):** one real past NYC heat day, minute by minute. 5 AM forecast → 6 AM cooling-place texts → 10 AM check-ins → 11:30 no reply → contact alerted → 11:52 contact arrives. Swimlanes for patient, system, contact and clinic.
- **Lasso-to-act:** select the top-right dots on the call-first scatter → preview the personalized messages → send to all.
- **Smart replies:** "OK" / "Need help" / "Can't get there." "Need help" or "can't get there" goes straight to the clinic call list.
- **Patient → clinic buttons** (from Myra): **"I feel unwell / dizzy"** and **"I have no AC"** move that patient to the top of the clinician's call list in real time. That's the loop judges can see live.
- **Child and caregiver case** (from Myra, aimed at Dr. Sarabu):
  - Topiramate, a common pediatric epilepsy and migraine drug, can stop children sweating. Its FDA label notes this mostly in children.
  - Children can't report symptoms, so the patient message goes to the **parent, and the school nurse or camp**: "Your child's medicine can make it hard to sweat. During hot days and sports, watch for…"
  - Contrast to show: the label *does* mention it, yet heat guidance mostly doesn't.
  - **Check that the citation is verified** before using it.
- **Trusted-contact view:** a simple page with the patient's address, what to look for, what to do, and one tap to call 911.
- **Cooling-place matching:** spread people across nearby places by distance and opening hours. Suggest neighbors go together ("cooling buddies").
- **Outcome funnel on the clinic board:** at risk → alerted → acknowledged → at a cooling place → checked on.
- **End-of-season report:** response times, places used, contacts triggered. It tunes each person's wait times (§4.4a).

### 7.2 Evidence map + Drug Card
- **Lenses** on the periodic table: by prescriber (a **pediatrics lens** for the judge), bucket, guidance gap, or "in the System graph."
- **Confidence chips** on every claim: *System graph ✓* / *literature only* / *guidance only*.
- **Compare mode:** two drugs side by side.
- **Printable one-page heat counseling sheet per drug,** for pharmacists and clinic handouts; it matches the printed bottle props.
- **Search any drug:** if it isn't in our 15, show what the System graph's two-hop pathways suggest, marked "not yet reviewed."
- **Drug Card tabs:** Label · Compass · Evidence · Guidance · Combinations · Alternatives · Patient wording.

### 7.3 Gap constellation + graph audit
- **Research agenda ranked by local impact:** rank the implied-but-untested drug-heat links by **how many SBH-area patients they affect.** That's novel: gaps weighted by real burden.
- **"Fix list" for System:** a CSV and one-page report of PMIDs that are indexed but have no findings, mislabeled findings (e.g. Martin-Latry "psychotropic drugs"), and direction errors. Hand it to System's judges.
- **Before / after:** how many drug-heat links the graph shows now vs after our corrections.
- **Coverage strip per drug:** share of its key papers with findings extracted in System.
- **Live counts** from the API.
- **"The 10 questions research must answer next"** (from Myra, for Verhulst): the top implied-but-untested links and evidence gaps, as one slide.
- **Validate hidden heat drugs first** (from Myra): run the chain on known heat drugs (diuretics, lithium). If they rank high, the hidden list is credible; if not, drop the claim and lead with the audit. Lithium has no direct graph links, so check whether it shows up through the chain at all.
- **Deliver the audit constructively:** three of five judges work on the graph or scholarly infrastructure. Every other team will praise the graph; we improve it.

### 7.4 Combination flags
- **15 × 15 combination matrix (visual 18):** each pair marked as shared mechanism / evidence-backed danger / untested. Untested cells feed the gap constellation.
- **Top risky combos in the panel:** "the 5 combinations to review this spring" for the SBH synthetic panel.
- **Anticholinergic Burden calculator** per patient.
- **Combination-aware alerts:** in the EHR alert and the patient app.

### 7.5 Headline line and pitch (from Myra's notes)
**The line judges should walk away with:**
> "Your medicine warns you about alcohol, not heat. We wrote the missing label, traced every word back to System's graph, and turned it into a call list a Bronx clinic could run on Thursday."

**The physical wow: the warning appears in their hand.**
1. A judge holds a plain pill bottle.
2. As their hand warms it, a heat warning appears (thermochromic ink, activating near skin temperature, ~31°C/88°F).
3. They scan the QR code, and the warning opens on their own phone (English or Spanish).
4. They tap "I feel dizzy," and on the big screen the Bronx clinic's call list moves that patient to the top.

**Backup if the stickers don't arrive:** a printed label with a QR code. The reveal is lost, but the phone moment stays.

*Note (14 Nov): no hardware and no staged scenario, so the bottle reveal and the judge role-play below aren't in the plan. Kept for reference. The pitch is a walkthrough of the real software, organized by the 6-stage journey, switching between map, graph and patient views, and ending with the health-system switcher (§3.7).*

**Myra's pitch run-of-show (3 minutes):**
1. **0:00** Bottle in a judge's hand; the warning appears. "Your medicine warns about alcohol, not heat."
2. **0:30** Journey map: heat affects the medicine from the pharmacy to the kitchen (§6.9).
3. **1:00** The graph: the medicine → dehydration ← heat chain, hidden heat drugs, "your graph has 15 findings; here are 60 studies to add."
4. **1:45** Live: heat forecast → EHR alert fires → clinician sends the label → judge's phone shows it (including the child version) → "I feel dizzy" → that patient tops the call list.
5. **2:40** "Works for any city, every claim is sourced, the dataset is open, and here are the 10 questions research must answer next."

*(Rachel's version adds the safety alert breaking through DND and the trusted-contact escalation as the live moment, §7.1. See choice C6.)*

## 8. Data

### 8.1 Source tiers
| Tier | Sources | Use |
|---|---|---|
| **A. Scholarly** | System Public Graph (API + Dataverse v2.1); our literature review; master list and report | Evidence, claims |
| **B. Official, verifiable** | Heat-health guidance (CDC, NYC DOHMH, UKHSA, Health Canada, ANSM, WHO Europe, Victoria, Germany); FDA label text; RxNorm; CMS Part D; CDC PLACES; NYC Heat Vulnerability Index; NYC Open Data (cooling centers, libraries, rec centers, pharmacies); NOAA/NWS; MTA GTFS | Guidance comparison, mapping, forecasts, routing, normalization |
| **C. Unverifiable** (news, forums, social media) | Context only | Pitch hook at most. Never evidence. Always labeled. |

**Rule:** a source earns its place only if it changes a label, a ranking or a headline number.

### 8.2 Data quality requirements
- Drug names normalized to RxNorm.
- Graph findings deduplicated to distinct papers; direction tagged.
- Keep API findings only if they also appear in the Dataverse CSV (System says about 20% are extracted inaccurately).
- About 40 graph findings hand-checked against abstracts.
- Guidance coded independently by both team members (kappa).
- Every public citation verified, or marked unverified.
- Versions and access dates in `data/SOURCES.md`.

### 8.2a Automated verification: no human checking (decided 14 Nov)
**Refined method and pilot results:** `docs/system-verification.md`. System is used as an independent second extractor, with five checks:
1. same paper, same number
2. same meaning (catches mislabels)
3. corroboration across papers
4. API vs Dataverse cross-check
5. reverse check for evidence we're missing

**Pilot (14 Nov):** wherever both we and System extracted the same result, **the numbers matched, with 0 conflicts** (Martin-Latry, Mangoni, voriconazole, dialysis, Hurricane Irma, insulin pens). There was **1 mislabel** (Martin-Latry "psychotropic drugs") and **1 paper where System missed our drug finding** (stimulants in Army recruits). IDs must be normalized (PMID / PMCID / DOI) before matching. **Badges updated:** ✓✓ double-verified, ✓ verified, ↗ corroborated (N System studies, % same direction), ⚠ conflict/mislabel, ? unverified (hidden). The list below is the earlier draft.

Every claim gets checked by machine, from several independent angles, and shows a **verification badge**.

1. **Does the citation exist?** Check each PMID/DOI against PubMed / Crossref, and check the title matches. (We already found 50 of 51 PMIDs indexed in System.)
2. **Is the number actually in the paper? (abstract grounding)** Fetch the abstract (PubMed / Europe PMC). Check that every number we show (e.g. "OR 2.43") **appears verbatim** in the abstract, along with the drug and outcome terms. It's simple string matching, cheap and very effective at catching made-up or mistyped numbers. An LLM reader is a second check for meaning (direction, population).
3. **Does System agree? (double extraction with the graph)** For papers System has extracted, compare our value, direction and variables with System's `statistic_value`, CI and variable names.
   - **Two independent extractions that agree** is the standard idea of "dual extraction" in systematic reviews, with System's pipeline as the second extractor.
   - Disagreements are flagged, not silently resolved.
4. **Is System's finding itself solid?** Keep API findings only if they also appear in the Dataverse CSV, as System recommends, since about 20% are extracted inaccurately.
5. **Is the link corroborated?** Check that a matching System relationship exists (e.g. thiazide → hyponatremia, 5 studies) and that the effect direction is consistent across its findings.
6. **Does the direction make sense?** OR/RR/HR > 1 = harm, and our claimed direction must match. Catches swapped cause and effect, a known System issue.

**Badges (shown on claims; counts in nerd stats):**
- **✓✓ Verified:** the number is in the abstract **and** System agrees.
- **✓ Abstract-verified:** the number is in the abstract; System has no extraction.
- **⚠ Conflict:** our value and System's disagree, or the direction doesn't match.
- **? Unverified:** no abstract found or no number match. **Not shown on public labels.**

**Limits, stated in nerd stats:**
- System has findings for only some of our papers (8 of 51 so far), so most claims can reach ✓ but not ✓✓.
- Abstract matching can't check numbers that only appear in full-text tables.
- No human review was done.

### 8.3 Current state of our data (13–14 Nov)
**A good map, not yet verified data.**
- The master list (86 rows) came from web searches and abstracts. Citations: 40 verified, 16 partly, 5 unverified, 25 with none.
- Severity ratings are the compiler's judgment; some figures are from secondary sources.
- **Checked against System** (`data/master_list_graph_status.csv`):
  - 51 distinct PMIDs; **50 are indexed**, **8 have findings**, 42 have none
  - PMID 42710533 isn't indexed (recheck the ID)
  - Martin-Latry 2007 is mislabeled
- **Graph coverage** (`docs/graph-check-results.md`): about 15 direct drug × heat findings; about 300 drug → mediator findings; heat → mortality / AKI / cardiovascular links present.

### 8.4 Getting better evidence: a mini systematic review with System built in
1. **Search** PubMed (E-utilities) and Europe PMC (including open-access full text) with fixed drug × heat queries (MeSH: *Hot Temperature*, *Heat Stress Disorders*, *Heat Stroke*, *Extreme Heat*, *Hyperthermia*, *Hypohidrosis*, "heat wave"). Save the queries and counts.
2. **Chase citations** from key reviews (Hospers 2024, Tews 2026, Kalisch Ellett 2016, Layton 2020, the 2025 schizophrenia review) via OpenAlex or Europe PMC.
3. **System discovery:** scan the Dataverse associations CSV for drug + heat/temperature/summer variable names; pull the drug → mediator links.
4. **Screen:** by LLM against fixed inclusion rules (**no human screening**, decided 14 Nov). Record counts.
5. **Extract with System pre-filling:** LLM extraction from abstracts, then automated verification (§8.2a). Track System right / wrong / missing (this feeds the audit).
6. **Grade** with the evidence tiers; tag direction and population.
7. **Report the funnel** in the Evidence section.

### 8.5 What the System API can do
| Capability | API | Use |
|---|---|---|
| Neighborhood around a concept | `/concepts/{id}/relationships` sorted by `num_studies` | Data-driven list of what links to heat harms |
| Multi-hop paths | chained relationships | Pathways, hidden heat drugs |
| Hypotheses (implied but untested) | drug → mediator + mediator → heat, without drug → heat | Gap constellation, research agenda |
| Evidence weighting | `num_findings`, `num_studies` | Edge thickness, node size |
| Evidence over time | `last_published_date`, study dates | Timeline, freshness badges |
| Agreement | `statistic_value`, CI, `p_value` | Forest plots |
| Who was studied | study `population` text | Coverage gaps (children, women…) |
| Study design | `study_type` (often null) | Design mix |
| Link to other data | Wikidata IDs | Drug classes, ATC, RxNorm |
| Compare drugs on one outcome | filter by target concept | Ranked bars |
| Stay current | live calls, `last_updated` | Live counts on Drug Cards |
| Audit | study lookup by PMID | Evidence section, fix list |

**Limits:** 10,000 requests/day; closed beta (fields may change); about 20% of extractions wrong; filing incomplete. Cache locally and verify claims.

**Note:** System's API returns data only (JSON). There's no public visual explorer, so we build all the visuals.

### 8.5a How we use System: the complete plan (14 Nov)
System is used in **six roles**, and each shows up visibly in the product (25% of judging is "meaningful use of the Public Graph"):

| # | Role | What we do | Where it shows | Build step |
|---|---|---|---|---|
| 1 | **Evidence source** | Pull findings (effect size, CI, p, paper) for our 15 drugs' heat-relevant links; Dataverse CSV scan for drug + heat/temperature variable names | Drug Card forest plots; claims; 3-step meter | 2–3 |
| 2 | **Second extractor (verification)** | The five checks in `docs/system-verification.md`: same number, same meaning, corroboration, API vs Dataverse, reverse check | Badges (✓✓ / ✓ / ↗ / ⚠ / ?); nerd stats | 3 |
| 3 | **Connector (two-hop pathways)** | Chain drug → mediator (kidney injury, low sodium, dehydration, blood pressure) ← heat; validate on known heat drugs | Pathway Sankey; node graph Evidence X-ray; Compass support | 3 |
| 4 | **Gap finder** | Implied-but-untested links; links with no relationship; weighted by local patient impact | Gap constellation; "10 questions research must answer next" | 3 |
| 5 | **Auditor (giving back)** | Papers indexed / extracted / correct / mislabeled; fix list (e.g. Martin-Latry mislabel, missing stimulant finding) | Graph audit funnel; fix-list handout for System's judges | 3 |
| 6 | **Live layer** | Drug Cards fetch live relationship counts and newest-evidence year from the API (cached; 10,000 requests/day) | "Live from System" badge on cards; API status in nerd stats | 5 |

**Per question:** §8.5c maps each of the 9 product questions to its System step.

**Data flow:** a Python pipeline pulls from the System API and the Dataverse CSV → caches in `data/raw/system/` → verification and pathway scripts → knowledge-base JSON → app. The live layer only refreshes counts. Claims come from the verified knowledge base.

**"How we used System creatively" write-up (Sat 14 Nov):** `docs/system-connections.html` (private artifact https://claude.ai/artifact/NUmLptbFd7bUuXSyVbrJXT; companion to `docs/system-api-story.html`). Six moves, each with a visual from the data files: (1) the bridge medicine → body effect ← heat, 38 pathways / 22 never tested directly; (2) coverage matrix + gaps; (3) validation: 13 of 15 known heat-risk groups reached, NSAIDs #1 of 19 on the non-BP score though not on our list; (4) per-patient bridge (S04 example; 118 of 300 synthetic patients have a stacked effect backed on both halves); (5) unvalidated leads past our list (PPIs, tolvaptan, simvastatin…; tolvaptan shows direction is unknown); (6) System as second reader and our audit back to it. States honestly that the live Drug Card refresh (`/api/system-live`) is still a stub.

**Headline numbers from System:**
- "Wherever System and we extracted the same result, the numbers agreed (X/Y, 0 conflicts)"
- "System holds about 15 direct drug × heat findings"
- "Pathways rediscovered X of Y known heat drugs"
- "N untested links implied by the graph"
- "Z label errors on the fix list"

### 8.5b Data check of Myra's overnight pipeline (commit 95fb864, 14 Nov)
- **Overall:** about 60 processed CSVs. All parse cleanly (no ragged rows, no unexpected empty columns). Every synthetic file is labelled synthetic. The knowledge base builds for all 15 drugs.
- **System status:** the overnight API pull got HTTP 403 (key rejected), so every `system_*` output comes from the **Dataverse v2.1 fallback** (about 2.0M findings vs. about 5.9M via the API). The key in `.env` **works as of 14 Nov late morning (HTTP 200)**. **Next step:** rerun the API pipeline in this order: `system_api_master_audit` → `system_api_evidence` → `system_api_graph_check` → `system_api_verify` → `system_api_live_layer`. That's about 2–4.5k of the 10k daily requests. Then rebuild the knowledge base.
- **Why the API rerun matters:** Dataverse holds only 7 of our 83 cited papers. The API had 50 indexed, 8 with findings. The **Martin-Latry mislabel** (our best audit story) is API-only, and so are the dialysis RR 1.27 and the insulin-pen finding.
- **API rerun done (14 Nov, 1,902 calls; 15,001 findings, complete):**
  - Of the 83 papers we cite, 80 are indexed and 15 have findings (50 findings).
  - 14 of our numbers are ✓✓, up from 5. There are 0 number or direction conflicts.
  - 3 papers carry System mislabels or drop the drug: Martin-Latry 2007, Layton 2020 (PMID 33301532) and Wong 2024.
  - Concept-level drug × heat edges: still 7.
  - The server takes about 10 s per batched call, so the variable route was fetched 8 at a time with `scripts/system_api_prefetch.py`, splitting batches that return 500. The evidence step then reran entirely from cache.
- **Decision:** a System mislabel never downgrades our claim. If our number is in the abstract, the claim keeps ✓, gets an audit note, and goes to `data/processed/system_audit_fix_list.csv`. ⚠ is reserved for real number or direction conflicts.
- **Fix list** (`system_audit_fix_list.csv`): 4 mislabels, 5 findings System didn't extract, and 17 candidate additions. Highlights:
  - an unused **outdoor temperature → drug-induced hyponatremia OR 2.21** on PMID 28737683, which we already cite
  - lithium PMID 25163443
  - SGLT2 → AKI (31 studies, mostly protective)
  - loop diuretics → AKI (30 studies, 27 of the ratio findings point up)
- **Visuals:** `docs/data-pipeline.svg` shows how the data was gathered, joined and filtered. `docs/data-cleaning-charts.html` shows the cleaning and System verification charts and the cleaning log. `docs/system-funnel.html` shows the find and check funnels; `docs/system-cleaning-chart.html` shows badges before and after the API check. `docs/system-api-story.html` is the presentation write-up: the data we had, the four jobs System did (find, check, spot gaps, feed the app), the ground rules and three lines for the slides.
- **Open decision:** System's rule "keep API findings only if they're also in Dataverse" would drop Martin-Latry. Proposal: apply the rule to evidence badges (✓✓), but still report API-only findings in the audit/fix list, labelled "API only."
- **Graph coverage file:** `data/graph_coverage.csv` was overwritten in Dataverse mode (13 core-heat findings). The 13 Nov API version (about 7 concept / 15 variable findings) is backed up in `data/raw/system/graph_coverage_api_2026-11-13_backup.csv`. Keep the headline numbers tied to their source.
- **Lithium under-scored:** lithium shows "Early signs" (0.156), because its only population-study claim (Wilting, Utrecht thesis, no PMID) is badged "?" and hidden.
  - Fix 1: find a PMID/DOI for the Wilting work.
  - Fix 2: add the System-surfaced McGill 2014 study (PMID 25163443: lithium dose-level ratio vs. mean daily temperature, β −0.17, p=0.08, n=63) to the master list.
  - This is a demo example of System **adding** evidence (role 5, reverse check).
- **SGLT2:** literature score 0, with graph-only (28 AKI studies) + FAERS + label support. Add DKA/volume-depletion-in-heat literature, or present it explicitly as a "graph-only / gap" drug.
- **Small cleanups:**
  - `fda_label_heat_claims_v2.csv` has 70 exact duplicate rows (mostly insulin storage lines repeated per label section). Dedupe them.
  - Name-matched System findings have unreviewed `auto_flags_heuristic`. Filter flagged rows and BP-efficacy rows out of public views.
  - `system_hidden_drug_candidates.csv` is unvalidated. Never show it as findings.
- **Rediscovery result (Dataverse):** diuretics rank 1–3 of 19, lithium 7, antipsychotics 11, anticholinergics 15. Thermoregulation (sweating / body temperature) is barely in the graph, and that's itself a gap finding.

### 8.5c The 9 product questions, and how System answers each (Sat 14 Nov)
The product is organized around 9 questions. **Every question gets a System step**, even where System is only a cross-check. Where the graph is thin, we say so on screen ("System has N studies on this"), and the thinness itself is a gap finding.

**Probe (Sat 14 Nov, live API, top 1,000 relationships of each heat concept, sorted by study count):**
- Heat evidence is mostly filed under **"thermodynamic temperature"** (201 relationships), with smaller sets under "hyperthermia" (95), "heat illness" (62) and "air temperature" (20).
- **"heat wave" has only 1 relationship.**
- So heat queries must cover all of these concepts, not just "heat wave."

| # | Question | Our main data | What System does | System coverage (probe) | Output / where it shows |
|---|---|---|---|---|---|
| 1 | **Which medicines are risky, and how sure are we?** | Literature review (5,995 searched, 333 included), 105 verified citations | **Roles 1–4:** drug → mediator (dehydration, kidney injury, low sodium) ← heat pathways; second extractor for our numbers; corroboration counts; reverse check | **Strong** (about 300 drug → mediator findings) | 3-step meter, badges, pathway Sankey, node graph, Drug Card forest plot |
| 2 | **Does real-world harm show up?** | FAERS signals (heat stroke, loss of sweating) vs comparison drugs | **Triangulation:** for each drug, does the FAERS signal line up with System findings for the same harm (e.g. drug → acute kidney injury, drug → hyponatremia)? Three-way agreement: literature + System + FAERS | **Some** (mediator outcomes yes; sweating/thermoregulation barely in graph) | "3 sources agree" marker on Drug Card; agreement matrix in nerd stats |
| 3 | **Are patients warned?** | FDA label audit (28 of 45 drugs: no heat warning on any label) | **Evidence vs label gap:** System's study count per drug next to "label mentions heat? Y/N." Headline: "N drugs with X+ studies in System still carry no heat warning" | **None directly** (no label concepts); System supplies the evidence side | Label-gap quadrant (evidence strength × label warning); Missing Label |
| 4 | **What does guidance say?** | 8 guidance sources coded per drug (mentioned vs specific action) | **Evidence vs guidance gap:** same idea, System evidence strength × guidance coverage. Drugs strong in System but missing from guidance = top gaps | **None directly**; System supplies the evidence side | Evidence-vs-guidance quadrant; gap badges |
| 5 | **When is heat coming?** | NOAA/NWS, HeatRisk, 35 yrs NYC weather, replay heat wave | **Heat → harm evidence:** temperature → mortality rate (16 studies), → emergency medical services, → out-of-hospital cardiac arrest, hyperthermia → hospital mortality. Used to justify **why a HeatRisk level triggers action** | **Some** | Forecast strip footnote: "why this threshold: System, N studies"; nerd stats |
| 6 | **Where is risk highest?** | HVI, AC access, CDC PLACES, SVI, Medicare prescribing by ZIP | **Place-factor evidence:** temperature ↔ urban area (5), air conditioning, income, vegetation (NDVI), housing. Each map layer gets a "System evidence" chip | **Thin** (mostly 1–5 studies each) | Map layer legend chips; thin coverage → gap constellation |
| 7 | **Who to call?** | 300 synthetic Bronx patients | **Patient-factor weights:** temperature/heat illness ↔ cardiovascular disease, kidney disease, age group, pregnancy outcomes. Each readiness-score factor cites its System support (or "not in System") | **Some** for conditions; thin for age, living alone, isolation | Call-first scatter tooltip "why this patient"; scoring formula in nerd stats |
| 8 | **Can help reach them?** | Real travel times to contacts and cooling places | **Time-to-help evidence:** temperature → EMS / cardiac arrest findings support the time budget (T_max). Response-time defaults stay from Pielot/Mehrotra (not in System) | **Thin** (1 study each) | Escalation assumptions panel: each number shows its source, System or not |
| 9 | **Is the medicine itself still good?** | Thermal simulation + drug storage evidence | **Storage evidence check:** Dataverse CSV variable-name scan for storage/stability terms (insulin, epinephrine, temperature, potency, degradation); API study lookup for every storage paper we cite (e.g. insulin pens at 37 °C, already matched) | **Very thin** (no storage concepts linked to heat in the probe; individual papers do have findings) | Storage card: "System has findings from N of our M storage papers"; gap finding |

**Rules:**
- Never inflate a thin row. Show the real study count, and show "not in System" when it's zero.
- Rows 3, 4 and 9 are where System is weakest, and that's a pitch point: the evidence exists for the drug risk, but labels, guidance and storage research haven't caught up.
- All counts come from cached API pulls with the date. The numbers in the table are from the Sat 14 Nov probe and must be re-pulled by the pipeline before they go on screen.
- Every new pull uses the existing client (`scripts/system_api_client.py`, cached, request log, daily budget).

### 8.6 Already in the repo
- `data/Drug heat risk master list.xlsx` / `.csv`: master list (86 rows) and guidance comparison
- `data/graph_coverage.csv`, `graph_heat_relationships.csv`, `graph_heat_variable_hits.csv`, `master_list_graph_status.csv`: graph checks
- `report/Prescribed drug heat risks.md`: research report
- `docs/graph-check-results.md`, `docs/schizophrenia-sbh-focus.md`, `docs/supply-chain.md`, `docs/system-api-guide.md`, `docs/winning-plan.md`
- `scripts/graph_check.py`, `scripts/build_master.py`

### 8.7 Starting scope: 15 medications (we may add more)
The knowledge base is one row per drug, and the views read from it, so adding drugs means adding rows, not code.

Suggested 15 (to confirm):
- lithium
- loop diuretics
- thiazides
- ACE inhibitors/ARBs
- SGLT2 inhibitors
- insulin (incl. pumps)
- metformin
- anticholinergics (oxybutynin)
- antipsychotics (incl. clozapine)
- SSRIs
- topiramate/zonisamide
- ADHD stimulants
- beta blockers
- fentanyl/opioid patches
- epinephrine auto-injectors

## 9. Evidence model
- **Tiers (strongest to weakest):** RCT/meta-analysis → population study → small clinical study → case series → case report → lab/bench → label/guidance only → mechanism only.
- **Evidence score:** design weight × independent studies × consistency × population match. Graph pathways are shown separately, never blended in.
- **FLAG vs CHANGE:** strong within-person studies showing no added drug effect → high FLAG, low CHANGE.
- **Personal readiness level:** documented points from the questionnaire + medication stack + neighborhood heat (§4.5a).
- **Null findings and conflicts are shown, not hidden.**

## 10. Guardrails

### 10.1 Non-goals
- No patient dosing advice or dose numbers
- No recreational or illicit drugs
- No naming individual prescribers or patients; no real patient data
- No brand names or pharmacy logos on props
- Not a replacement for clinical guidance

### 10.2 Success criteria
- **Judging:** every rubric area visibly covered; a clean, rehearsed 3-minute demo of the core loop, with a recorded backup.
- **Accuracy:** no unverified claim on a public label; every headline number traces to a repo file.
- **Headline numbers:**
  - graph coverage and audit
  - pathway validation (X of Y known heat drugs rediscovered)
  - hidden heat drugs flagged
  - number of patients to call in the simulated heat wave
  - escalation time-to-help
- **Usefulness:** the core loop runs end to end on a replayed NYC heat day.

### 10.3 Constraints
- **Time (corrected from Myra's notes):** hacking runs **Sat 10 AM–3 PM**, and the Devpost deadline is **3:00 PM**. That's about 5 hours on Saturday plus Friday night, not 24 hours. Two people.
- System API: closed beta, 10,000 requests/day; key in `.env` (gitignored).
- Licenses: System Public Graph is CC BY-NC 4.0 (non-commercial, credit required).
- November: no live heat, so replay mode.
- iOS Critical Alerts need Apple's entitlement, so the demo push is simulated (decided Sat 14 Nov).
- The demo phone must reach the laptop's server (same Wi-Fi; venue Wi-Fi may block device-to-device traffic, so have a phone hotspot as backup).

### 10.4 Risks
| Risk | Mitigation |
|---|---|
| Thin graph coverage hurts "meaningful graph use" | Pathways, gap constellation, receipts and audit put the graph at the center |
| Overclaiming | Evidence type labeled everywhere; confounding shown |
| Read as medical advice | Disclaimers; "considerations for clinicians"; no patient dose advice |
| Alert fatigue / false alarms | High-risk days only; computed waits; personal p90 |
| Live demo breaks | Recorded backup; replay mode |
| Scope creep | Core loop + evidence map first; §11 items only if time |

## 11. Add later if time
- **Supply chain, in depth** (beyond the 3D-map layer): pre-ship risk check (forecast + drug profile + shipping speed → ship / upgrade / insulate / reroute / hold), "bring it inside" delivery texts, doorstep exposure via mean kinetic temperature, pharmacy dashboard. Talking point: we quantify the drug in the box, not in the body. Details: `docs/supply-chain.md`.
- **Hardware:** package temperature logger (ESP32 + SHT31), or a home temperature sensor (§4.4, item 8). Myra's hardware concepts:
  - **"Heat odometer" for medicines:** a tag (ESP32 + SHT31/DS18B20 + battery + e-ink or LED, ~$25–35) that keeps a running mean kinetic temperature for a drug kit or shipment. Example: "Lorazepam kit: 41 days at MKT 31°C, beyond what studies tested, rotate." Demo: pre-heat it, and lorazepam is flagged while midazolam is fine, matching the published data. **Honesty rule:** show "exposure beyond what study X tested," never an invented "% potency left."
  - **Pharmacy fridge network for blackouts:** a live map of where insulin is still stored safely during an outage. Hard to demo with one device.
  - **Thermochromic shipping label:** already sold by vendors (e.g. SpotSee), so it's a prop only.
  - Myra's view: the storage sensor only if someone has done ESP32 work **and** the parts are in hand; 15 seconds of the pitch at most. No rubric criterion scores hardware, and the graph has no storage evidence.
- **Publish the label dataset** as an open, versioned set (for Travis Rich).
- **Thermochromic printed bottles** (props).
- **Standalone public story site** ("The Missing Label" scrolling story: a person, the four ways heat and medicine collide, the graph pathways, the guidance gap, the Bronx, the doorstep, the reveal). Its opening can be the pitch intro.
- **Heat Label API** (RxNorm code in → label JSON out).
- **City toggle** (e.g. Phoenix).
- **FDA label audit:** does each heat-risk drug's official label mention heat?
- **Escalation trade-off simulation:** false alarms vs time-to-help on the synthetic panel.
- **Long-range climate projections** (NPCC4; NPCC3 said 24–75 days ≥90°F/yr by the 2080s vs 10 in 1971–2000). At most one pitch line.

## 12. Decision log and open questions

### 12.1 Decisions
- **13 Nov:**
  - The evidence map is the primary deliverable, readable by non-specialists.
  - Clinician-first, with a pediatrics slice.
  - Light mode.
  - NOAA only for forecasting.
  - Heat Dose Compass instead of a dose algorithm.
  - Synthetic patients only.
  - Directed arrows set by us.
- **14 Nov:**
  - The core loop is the standout.
  - The **safety alert is mandatory**.
  - Medicine Cabinet is the patient app.
  - Prototype **all** visuals, then cut.
  - Node graph required.
  - Call-first scatter chosen.
  - 15 drugs to start.
  - Core 5 questions.
  - Escalation timing derived from a time budget.
- **Dropped (14 Nov):**
  - the Compass temperature slider (not enough data)
  - action items: cooling-place ride help, Con Edison life-sustaining-equipment enrollment, building door-knocks, NYC Advance Warning System
  - custom forecasting ML
  - FDA adverse-event (FAERS) disproportionality analysis (not something the team asked for). *Reversed later on 14 Nov: see C9.*
- **Sat 14 Nov (hack day):**
  - **Supabase dropped:** local SQLite + polling instead; no accounts beyond System.
  - **Push notifications simulated** on the demo phone (mock banner, labeled), like the SMS. No Web Push, Twilio or Vercel.
  - **Priority focus (midday, §4.0a):** actions and resources first; Low / Medium / High buckets; medication stacking; text by bucket; caregiver outreach; resources + best heat-aware route + safest time outside; 3D map as the main visual for both sides; EHR-embeddable by design; one specific use case.
  - **Medicine Cabinet scrapped** as the main patient view (side visual at most). This changes C1.
  - **Patient map: 2D/3D switch, 2D by default** (for older patients).
  - **Simplify (review ~11:45):** too complicated; plain words for everyone; cut the number of visuals. Proposal in §5.0, to discuss.
  - **Outcome first, evidence on click:** clear and simple beats showing accuracy up front; evidence sits behind a "Why?" / "See the evidence" click (§5.0).

### 12.2 Choices: Rachel's spec vs Myra's notes (merged 14 Nov)
**Rachel's decisions (14 Nov):**
- **C1:** ~~keep the **Medicine Cabinet app**~~. **Changed Sat 14 Nov midday:** the patient app's main view is the map + "my heat plan"; the cabinet is a side visual at most.
- **C2:** the safety alert is **mandatory**, sent as **both an app push notification (breaking through DND) and an SMS**. In the demo both are simulated on the demo phone (Sat 14 Nov).
- **C3:** we **are** building the **3D map**.
- **C4:** **build the node graph** to see it, and decide later whether to use it.
- **C5:** **both.** The site is organized by the **6-stage journey**, and it can also be viewed as a **map view, a graph view and a patient-facing view**.
- **C6:** **no staged or role-played scenario** (no "judge plays the patient"). The pitch shows off the real software working.
- **C7:** keep **FLAG / CHANGE**.
- **C8:** the **3-step meter (Strong / Some / Early signs)** is shown on the main screens. The **8-step tier detail** lives in **nerd stats**.
- **No human checking of the evidence (14 Nov):** it isn't realistic in the time. Verification is **automated** (§8.2a), and nerd stats states this plainly.
- **C9: YES, use the FDA adverse-event reports (FAERS via openFDA)** as a labeled **warning signal**, never as proof: anyone can report, there's no count of people taking each drug, and a report doesn't prove cause. It's used as a third evidence layer and to check "hidden heat drugs."
- **C10:** patient messages are **customized to each patient's needs** (see §4.5b). The method is to be worked out and may involve learning from data.
- **C11:** **no hardware**, so no thermochromic bottles. All hardware stays in §11.
- **C12:** **don't scale down.** Keep the full scope; a lot can be done in 5 hours.
- **SBH clarification:** SBH is an **example client to zoom in on**, not *the* client. The product must scale to **any hospital or health system** (§3.7).

**The original conflict list:**

| # | Topic | Spec (Rachel) | Myra's notes |
|---|---|---|---|
| C1 | **Patient side** | "My Medicine Cabinet" **app** (cabinet visual, questionnaire, notifications) | **Not an app:** one phone page the clinic sends, reached by QR code on the bottle or a text |
| C2 | **Safety alert / live messaging** | Mandatory alert through DND; trusted contact; live judge demo | **Cut "live SMS"**; the clinic sends one label page |
| C3 | **NYC map** | 3D NYC map (team builds) | **Cut "full NYC map"** |
| C4 | **Node graph** | Required interactive node graph; prototype all 21 visuals | **Graph as a simple picture, not a network diagram**; one example per bucket |
| C5 | **Site structure** | 3 screens (Evidence Map, Heat-Wave Readiness, Evidence) built around the core loop | The **6-stage medicine journey** organizes the site |
| C6 | **Pitch live moment** | Safety alert breaks through DND, then trusted-contact escalation | Thermochromic bottle → QR → "I feel dizzy" → call list moves |
| C7 | **FLAG / CHANGE names** | FLAG / CHANGE | "Check on this person" / "Rethink the medicine" |
| C8 | **Evidence display** | 8 evidence tiers | 3-step meter: Strong / Some / Early signs (tiers kept underneath?) |
| C9 | **FDA adverse-event evidence layer** | Dropped (FAERS removed 14 Nov) | Every claim tagged ① graph ② literature **③ FDA adverse-event reports** |
| C10 | **Patient message content** | Tailored fluid advice; no blanket "drink water" (heart-failure fluid limits, low-sodium risk) | Example message says "Drink water… keep taking it" for everyone |
| C11 | **Thermochromic bottles** | "Add later if time" | **Core: order tonight** |
| C12 | **Scope vs time** | Prototype all 21 visuals, core loop, escalation algorithm, questionnaire | Must-haves are ~8 labels, patient page, call list, props, sized for **5 hours on Saturday** |

### 12.3 Open questions
- **"FDA verification" from the team's idea list:** what exactly does it mean? (Possibly checking FDA labels; to discuss.)
- Confirm the 15 drugs, and which ~8 get polished labels.
- ~~Tech stack~~: decided 14 Nov, see §4.8.
- HeatRisk data access (API vs WPC data files); NYC heat-advisory criteria.
- Verify: Semenza 1996; Be a Buddy; HEAP details; substitute examples; notification-study medians.
- Do we use any tier C sources in the pitch?
- **System API key returned 403** on Myra's overnight run (Sat 14 Nov); System results so far are the Dataverse fallback. Get a working key and rerun the System scripts: roles 1–6 (§8.5a) and 25% of judging depend on it.
- **Work split from 10:45 Sat:** Rachel = SQLite + core loop (send alert → simulated push/SMS on the phone → escalation with fast-forward → clinic board). Myra = System key rerun, then the evidence-side visuals in `web/` (forest plot, pathway Sankey, node graph, live System layer, CDS Hooks cards). The 3D map and call-first scatter go to whoever finishes first.
- **Core loop built (Sat 14 Nov, 11:00):** `/board` (clinic board: replay-day call list, send / multi-send, live status, message log, +5/+15/+45 min fast-forward, reset) and `/phone/<id>` (demo phone: simulated push banner, simulated SMS thread, "I'm OK" / "I feel unwell" / "No AC"). All wording and timings come from `panel_scores_replay.json` (`safety_alert`, `contact_check`, `escalation.steps`); escalation steps fire when the board or phone polls, so fast-forward just shifts the demo clock. **Rule: no invented data; missing pieces show a labeled placeholder naming the file they'll come from.**
- **English reading view (Sat 14 Nov):** `/phone/<id>?lang=en` (or the "Read in English" link) shows a Spanish-speaking patient's screen in English for the team and judges. The message texts are the **same lib/patient rules run with language forced to English** (`scripts/compute_messages_en.ts` → `data/processed/panel_messages_en_replay.json`), not hand translations. Patients are still sent their own language. Rerun the script whenever `compute_panel.ts` is rerun.
- **The one specific use case (Rachel, Sat 14 Nov): to pick.** One suggestion: *a clinic nurse at a Bronx health center, the morning a heat wave is forecast, screens the panel into buckets, texts each bucket its plan, and the High-risk patients and their caregivers get a resource, a route and a safe time to go.* To discuss.
- **Clinician ↔ patient messages (Rachel, Sat 14 Nov, required):** the clinician clicks a patient anywhere (board, map, Why? panel) and lands in their conversation: every alert and text sent, texts to their contact, the patient's replies and check-ins, quick replies and a text box. Built at `/messages` and `/messages/[id]`.
- **Heat-day time-lapse (Rachel, Sat 14 Nov): YES**, at `/replay`, as the pitch opener. **Redesign (Rachel, 1:15 PM):** heat as radar-style blobs (like a precipitation map), no trip lines, no pulse rings; click a patient to see their plan and contact them; only ONE patient's optimal route at a time, shown when you click them. Built with NOAA HRRR hourly "feels like" data; the card shows the patient's medicines with System graph study counts. **Rejected:** cooling deserts, 3D "walk in their shoes" route, QR code for judges.
- **Rachel's UI feedback (Sat 14 Nov, ~1:45 PM), all decided:**
  - **Name:** rename "The Missing Label" to **"Cool-Aid"** (with a C) for now; may change later. Write the name in one of our palette colors (now teal `#0e7c86`, `--bucket-store-solid`).
  - **Medicines tab (clinician):** much less wordy and simpler. **More color on the indicators** (evidence strength, "label warns about heat," "guidance says what to do"), e.g. colored chips. **Dropdowns** to organize the medicine groups. The "how heat and medicine add up" diagram (medicines → body effect ← heat, hover to highlight) is the style we want: make it **the main thing on the page, prettier** (color per body effect, cleaner labels), and keep it **clinician-only**.
  - **Patient view:** far too many words; it has to be **visual, not text**. Replace the network-style diagram with the **medicine cabinet**: the patient's own medicine bottles on a shelf with **stems** running from each bottle to what it can do to their body in the heat. **Hover/tap a bottle** to see the bad things it can cause; **select several bottles** to see the combined effects (where they add up). Use dropdowns to tuck away the rest.
  - **Patient app:** too many words too; same rule (visual first, dropdowns for detail).
- **Logo / tab icon (Rachel, Sat 14 Nov):** option 2, the **hot-and-cool pill**: a capsule, half orange (`#d55e00`) and half teal (`#0e7c86`), tilted 45°. It's the browser tab icon (`web/src/app/icon.svg`) and sits next to "Cool-Aid" in the header.
- **Teal replaces blue everywhere (Rachel, Sat 14 Nov):** every place that used the Okabe–Ito medium blue `#0072b2` now uses teal `#0e7c86` (tint `#d9f0f1`, ink `#0a5f66`): Store-cool chips, **Low risk** dots and chips, buttons, the "Cool-Aid" name, message bubbles, and the low-blood-pressure line in the medicines diagram. Low salt moved to dark gold `#b08800` so it doesn't look like the teal. Risk groups are now **High = orange, Medium = yellow, Low = teal**.
- **Stronger or weaker in heat, on the clinician Medicines list (Rachel, Sat 14 Nov):** new **"In heat"** column from the knowledge base's Heat Dose Compass (`compass.arrow`, direction only, never a dose). Chips: **↑ Stronger** or **↑ Matters more** (orange; "matters more" when the compass says the *effect* matters more in heat, e.g. blocked sweating), **↓ Weaker** (teal), **↕ Depends** (purple). Hover shows the compass's one-line meaning. Current split: 10 up, 4 depends (insulin, antipsychotics, SSRIs, beta blockers), 1 down (epinephrine auto-injector).
- **Font (Rachel, Sat 14 Nov):** **Plus Jakarta Sans** for the whole app (replaces the system font). Self-hosted with `next/font/google` in `web/src/app/layout.tsx` (works offline); `--font-body` in `tokens.css` puts it first.
- **Project name:** now **"Cool-Aid"** (Sat 14 Nov, placeholder; may change). Was "The Missing Label." Rachel rejected the first brainstorm (CoolPath, Safe Hours, Heatline, etc.); to pick.
- **Texting:** real SMS-provider API in the demo, or keep it simulated (decided simulated earlier on 14 Nov)? The SMS module is built so either works.
- **Open:** the board can send to patients whose `why` says "not opted in to safety alerts: phone call is the only route" (e.g. P0149). Send should respect the questionnaire's `alert_opt_in` and route those patients straight to the call list.
