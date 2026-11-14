# Strategy notes from Myra's Claude session (13 Nov 2026, evening)

**For:** Rachel, to merge with your work
**From:** Myra
**Status:** strategy proposals, not decisions yet. The main open question for us both is in §10.

This is the full record of my evening session with Claude: what I asked, what came back, and the plan it ended up with. It builds on `spec.md` and `docs/schizophrenia-sbh-focus.md` and suggests changes to them.

**Contents**
1. Key facts from the hackathon and challenge brief
2. Session log: what I asked, in order
3. Hardware and supply-chain ideas, and why they got scaled back
4. How we compete
5. Who the client is, and the two views (clinician and patient)
6. Making it work for non-specialists
7. Wow factor and how we stand out
8. The judges and what each one wants
9. Backbone: heat across the medicine's whole journey
10. Proposed changes to `spec.md`, and open questions
11. Build priorities for tonight and tomorrow

---

## 1. Key facts from the hackathon and challenge brief

**Event:** System Public Challenge, System HQ, NYC
- **Deadline:** Sat 14 Nov 2026, 3:00 PM EST
- **Saturday:** hacking 10 AM–3 PM, pitches 3–4 PM, winners announced 5 PM
- **Prizes:** one $2,000 winner per category (Explore, Visualize, Build), plus three $500 honorable mentions across all categories
- **Judging:** four criteria, 25% each
  - meaningful use of the Public Graph
  - insight or usefulness to user/problem
  - technical execution
  - communication
- **Visualize category definition:** "Design and communication, turning relationships in the graph into compelling, accurate visual stories for a **non-specialist audience**."
- **Hosts' stated preference:** "deliberately favoring interdisciplinary problems at the intersection of fields such as climate, environment, food and health."

**Judges**
- Dr. Chethan Sarabu: Director of Clinical Innovation, Health Tech Hub, Cornell Tech. Pediatrician and clinical informatician. **Wrote our challenge.**
- Dr. Stefaan Verhulst: Co-founder, The GovLab (NYU). Owns Visualize 1 (women's health).
- Daniel Gil-Sanchez: Data scientist, World Bank Development Data Group
- Travis Rich: Co-founder and Head of R&D, Knowledge Futures. Owns Build 4 (NYC data / Underlay).
- Nalini Edwin: Head of Communications, System

**Our challenge, Visualize 3** (brief text, lightly trimmed):
> Which common medications make heat more dangerous, and what should prescribers and health systems do about it?
>
> Use the System Public Graph to map the evidence linking medications to heat-related outcomes and organize it into actionable buckets: dose adjustment (e.g. insulin absorbing faster in heat); substitution or temporary holding (e.g. diuretics, anticholinergics); closer monitoring (e.g. lithium levels, hydration); storage and stability (e.g. insulin, inhalers, epinephrine). For each bucket, show how strong the evidence is, which prescribers are most involved (primary care, psychiatry, cardiology, endocrinology, nephrology, pediatrics) and what a prescriber might reasonably change ahead of or during a heat wave. Compare this against heat-health guidance from health systems and public health agencies globally to highlight where guidance is missing or out of step with the evidence. Teams can also explore what research exists on using wearable data (heart rate, skin temperature) to personalize heat guidance, and where that evidence runs out. Mapping where in NYC heat exposure and these prescriptions overlap is an optional extension.
>
> **What you'll produce:** a visual evidence map of heat-sensitive medications grouped by type of action, showing evidence strength, the prescribers involved and gaps in current guidance, which a clinician, pharmacist or public health official could use to plan heat-wave counseling and outreach.

**Other Visualize challenges we're up against for the category prize**
- Visualize 1: Where does the evidence sit on the women's health map? (owner: Verhulst)
- Visualize 2: How does the effect of malaria prevention vary by setting and over time? (owner: Amato, PATH)

---

## 2. Session log: what I asked, in order

1. **Clone the repo.** Done, into `~/system-hackathon`. It's a normal clone of `rachelchen24/system-hack-heat-med`.
2. **Can we make supply-chain solutions for medications with hardware?** I shared my brainstorm notes and an earlier Claude chat (summary below). → §3
3. **Pull the project spec.** Pulled the new `spec.md` and `docs/schizophrenia-sbh-focus.md`. Claude summarized them and showed where hardware could fit. → §3
4. **I shared the full challenge list and the Devpost page.** Claude re-checked the hardware idea against the rubric and time. → §3, §4
5. **If we made both a client-facing and a patient-facing version, who is the client?** It also had to max out the rubric and stand out. → §5
6. **The brief says non-specialist audience.** → §6
7. **What makes us stand out? What's our wow factor?** → §7
8. **We compete against other tracks too.** Maximize every part of the rubric; cover the whole process (supply chain, taking the medicine, patient and clinician sides); add something other teams won't think of; think like the judges (the challenge author is a pediatrician and clinical informatician). → §4, §8, §9

**My original brainstorm notes**
- Make it scalable. Approach it from an angle the judges haven't seen. Be so standout they can't forget us.
- Some medications need more or less dosing in heat → an algorithm for a safe range? *(Ruled out: see §3.4.)*
- Body temperature varies by patient (indoors all day vs. construction worker).
- Supply chain issues.
- Add a hardware solution?

**Earlier Claude chat I pasted in ("The Missing Label")**
- Five pieces: the Missing Label; evidence vs. guidance quadrant; hidden heat drugs; NYC heat-wave playbook; wearables frontier panel.
- Hardware options: a smart storage sensor (ESP32 + SHT31/DHT22 + RGB LED, ~$20–30), or thermochromic heat-reactive labels.
- Rule of thumb: build the software first and add hardware only once the core works.

Most of that is already in `spec.md`.

---

## 3. Hardware and supply-chain ideas, and why they got scaled back

### 3.1 First pass: three supply-chain hardware concepts
Grounded in `research-notes/storage_devices_supply.md`.

**A. "Heat odometer" for medicines** (was the top pick before we checked the rubric)
- **The idea:** a small tag that rides with a drug kit or shipment. It logs temperature and keeps a running **mean kinetic temperature (MKT)** on the device. MKT is a single number for the total heat a drug has absorbed; the stability studies in our notes use it (e.g., McMullan: lorazepam breakdown in ambulances tracked MKT).
- **What it shows, per drug:** e.g. "Lorazepam kit: 41 days at MKT 31°C. Above the exposure where studies saw it drop below 90%. Rotate." or "Insulin shipment: 9 hrs above 30°C. Check before use."
- **Where it would be used:**
  - ambulance drug boxes (lorazepam and succinylcholine degrade; South African ambulances lost about 25% of their adrenaline in 4 weeks)
  - mail-order prescriptions (in the Utah study, every shipment went outside 68–77°F)
  - home insulin and EpiPens
- **Parts:** ESP32 + SHT31 or DS18B20 + battery + e-ink screen or LED, about $25–35.
- **Demo:** pre-heat the tag to simulate "4 weeks in an ambulance." The dashboard flags lorazepam while midazolam is still fine, which matches the published data.
- **Honesty rule:** decay data exists for only a few drugs (lorazepam, dilute epinephrine, succinylcholine, insulin). Show "exposure beyond what study X tested," with the citation. Never invent a "% potency left."

**B. Pharmacy fridge network for blackouts**
- Sensors in pharmacy fridges feed a live NYC map of where insulin is still stored safely during an outage.
- Evidence: ER visits for refills spiked after Hurricane Beryl in Houston, and heat deaths roughly doubled in a blackout model.
- Plugs into the playbook, but hard to demo with one device.

**C. Thermochromic shipping label**
- Cheap and scales, but a vendor already sells this (SpotSee), so it isn't new to judges. Prop only.

### 3.2 What the spec already says about hardware
- `spec.md` §3.7 lists "printed pill bottles with thermochromic heat-warning labels" and an "optional evidence-calibrated storage sensor" as stretch outputs.
- §11 still asks "Are we including the optional sensor?" and "Can thermochromic labels arrive in time?"
- The spec's audience is clinicians and health systems, so ambulance and mail-order logistics are off-target as a standalone product.

### 3.3 After reading the full brief and Devpost page: scale it back
- **Time:** tonight plus 5 hours of hacking. Getting parts, flashing firmware and wiring a dashboard would eat most of it.
- **Rubric:** nothing scores hardware. Visualize is about design and communication, so a device only scores if it makes the evidence clearer.
- **The graph has no storage evidence.** The storage and stability findings in our notes come from outside the System graph, so a storage sensor adds almost nothing to "graph use," our weakest criterion.
- **Supply chain isn't in the brief.** Storage is one of four buckets; the question is what prescribers and health systems should do.

**Recommendation**
- **Do the thermochromic pill-bottle labels.** Cheap, unforgettable and no code. The warning appears as a judge's hand warms the bottle. Order tonight (Amazon same-day), with an activation temperature near skin temperature (~31°C/88°F).
- **Storage sensor only if** one of us has done ESP32 work before *and* the parts are already in hand. Present it as the **Store cool** label made physical, disclosed as "evidence: published literature, not in the graph." Keep it to 15 seconds of the pitch.
- **Skip** the ambulance fleet, mail-order and pharmacy-fridge products as builds. The supply-chain angle comes back as part of the journey map (§9).

### 3.4 The "safe dose at this temperature" algorithm is ruled out
Our own `docs/schizophrenia-sbh-focus.md` §3 already says why:
- there's no validated calibration data (the insulin evidence is one study of 8 people in a sauna)
- core-temperature estimates from wearables aren't validated in medicated patients
- a dose number would be unverified medical advice

The replacement is the **Heat Dose Compass** (spec §3.4): an arrow per drug showing whether heat makes it stronger, weaker or either, plus the mechanism, the trigger, what to monitor and the evidence strength. It never gives a dose. Dr. Sarabu is a clinician and will respect that line.

---

## 4. How we compete

- The main prize is per category, so we're competing with all Visualize teams (women's health, malaria, heat × meds). Honorable mentions are across all tracks.
- The same five judges score everyone, so we optimize for **these five people** and the **four equal criteria**.
- Likely competition: most teams will build an evidence dashboard with buckets, bar charts of evidence strength, maybe a guidance table and a heat map. Competent but alike.
- Our edge: **turn evidence into action, make it physical, and be honest about the graph.**

---

## 5. Who the client is, and the two views

### 5.1 The client is a health system; the demo client is SBH Health System (Bronx)
- **It can act on this.** It holds the medication lists, the prescribers and the patient phone numbers. A health department can warn about heat but can't see who takes lithium.
- **It matches the brief:** "what should prescribers and **health systems** do."
- **It's a strong story.** SBH is a safety-net hospital and one of the Bronx's largest mental health providers (160,000+ behavioral health visits a year). The landmark study showing psychiatric patients' heat deaths are *preventable* (Bark 1998) came from Bronx Psychiatric Center. Our judge works with SBH.
- **Day-to-day users:** psychiatry and primary care clinics, pharmacists, care coordinators.
- **Secondary user:** NYC DOHMH, seeing the neighborhood view in aggregate only.

### 5.2 Clinician view: the "Heat Desk"
It switches on when a heat wave is forecast (we replay a real past NYC heat wave, since it's November).
1. **Who to call first:** ranked list of synthetic patients (never real) on heat-risk drugs, sorted by FLAG score.
2. **What to consider, per drug:** the label with action bucket, FLAG/CHANGE meters, Heat Dose Compass arrow and what to monitor. Every claim tagged ① graph, ② published literature, ③ FDA adverse-event reports.
3. **One button** sends the patient version.

### 5.3 Patient view: the Missing Label
- A phone page in English and Spanish, reached by a QR code on the pill bottle or a text from the clinic.
- One plain message, e.g. *"Heat waves can make this medicine riskier. Drink water, stay somewhere cool, and keep taking it. Call your clinic if you feel dizzy or confused."*
- **No dose numbers, never "stop taking it."** The clinic sends it, so it stays under clinical oversight.
- **Closes the loop:** the patient taps "I feel unwell" or "I have no AC," and that patient jumps to the top of the clinician's call list.

### 5.4 The core insight connecting both views
For many patients, the right response isn't changing the drug but **a phone call and access to cooling**. Our schizophrenia notes show this: in the Cincinnati 1999 heat wave, a working air conditioner was the strongest protection (OR 0.03). FLAG says who to call; CHANGE says whose prescription to review.

### 5.5 Change to the spec
`spec.md` §2 says "It isn't a patient app." It still isn't one: patients get a single page their clinic sends, not an app.

---

## 6. Making it work for non-specialists

**Two lines in the brief that seem to conflict**
- The Visualize category asks for stories for a "**non-specialist audience**."
- Our challenge's deliverable asks for something "a **clinician, pharmacist or public health official** could use."

**How they fit:** a clinician is a medical expert but not an expert in heat pharmacology or research evidence, so the product has to work for someone with no research background. Only 1 of 5 judges is a clinician. If the main screen only makes sense to a doctor, we lose four of five judges.

### 6.1 Open with a visual story, with the clinician tool underneath
1. *Your pill bottle warns you about alcohol. Not heat.*
2. *These common medicines make heat more dangerous*: the 4 action buckets as simple icons.
3. *Here's what the research shows, and where it's missing*: the graph pathway, drawn simply.
4. *Here's what a Bronx clinic could do on Thursday*: the Heat Desk.

The patient label sits inside step 1, so the patient-facing piece becomes the way in.

### 6.2 Plain-language swaps

| Current | Plain version |
|---|---|
| FLAG / CHANGE | "Check on this person" / "Rethink the medicine" |
| Odds ratio 2.43 | "About 2½ times the risk" |
| Hyponatremia, acute kidney injury | "Low salt in the blood," "kidney strain" |
| Anticholinergic | "Medicines that reduce sweating" |
| Evidence tiers | 3-step meter: Strong / Some / Early signs |
| Sankey of drug → mediator → heat | Medicine → what it does to your body → why heat makes it worse |

### 6.3 Other rules
- **Graph view as a picture, not a network diagram.** One example per bucket, e.g. lithium → *your body holds onto it when you're dehydrated* ← *heat dehydrates you*.
- **Keep the detail one click away.** Sources, study numbers and the Methods page stay. A non-specialist reads the plain line; a curious judge clicks through.

---

## 7. Wow factor and how we stand out

### 7.1 The wow: the warning appears in their hand
1. A judge holds a plain pill bottle.
2. As their hand warms it, a heat warning **appears on the label** (thermochromic ink).
3. They scan the QR code, and the warning opens **on their own phone** in English or Spanish.
4. They tap "I feel dizzy," and on the big screen the Bronx clinic's call list moves that patient to the top.

In about 30 seconds the judge *experiences* the whole problem: no warning exists, heat makes the medicine dangerous, and someone needs to call. It needs no explanation, which suits a non-specialist audience.

### 7.2 Two things that make the wow hold up under questions
**1. Hidden heat drugs: a new finding from the graph.**
- Chain the graph's links: drug → dehydration / kidney strain / low salt ← heat. Per `docs/graph-check-results.md`, there are about 300 drug → mediator findings: ACEi/ARB 74, diuretics 55, NSAIDs 44, antipsychotics 22, loop diuretics 21, SGLT2 19.
- Flag common drugs that score high but appear on no guidance list.
- **Validate first:** run it on drugs already known to be heat risks (diuretics, lithium). If they rank high, the hidden list is credible. If not, drop the claim and lead with the audit.
- Note: lithium has no direct graph links, so check whether it shows up through the chain at all.

**2. The graph audit: a gift to the host.**
- "Your graph holds about 15 findings on medications × heat. We found 60+ published studies that should be there, and here's the list."
- Three of five judges work on the graph or scholarly infrastructure. Every other team will praise the graph; we improve it. Deliver it constructively.

### 7.3 The line judges should walk away with
> **"Your medicine warns you about alcohol, not heat. We wrote the missing label, traced every word back to System's graph, and turned it into a call list a Bronx clinic could run on Thursday."**

### 7.4 Backup if the thermochromic stickers don't arrive
A printed label with a QR code. We lose the reveal but keep the phone moment.

---

## 8. The judges and what each one wants

| Judge | Background | What would impress them | What we give them |
|---|---|---|---|
| **Dr. Chethan Sarabu** (wrote our challenge) | Pediatrician, clinical informatics, Cornell Tech | Fits real clinical workflow; patients and **caregivers**; wearables | **EHR alert** on the CDS Hooks standard (what Epic/Cerner use); **child/caregiver case** |
| **Stefaan Verhulst** (GovLab, NYU) | Data for public good, responsible data reuse, "the questions that matter" | Gaps turned into a research agenda; responsible data use | **"The 10 questions research must answer next"**; short data-responsibility note (synthetic patients, aggregate-only maps, no individual prescribers) |
| **Daniel Gil-Sanchez** (World Bank data) | Data quality, reusing indicators across countries | Reproducible; scales beyond one city | **City/country toggle** (e.g. Phoenix); versioned sources in `data/SOURCES.md` |
| **Travis Rich** (Knowledge Futures) | Open infrastructure, provenance, versioned datasets | Every claim traceable; giving something back | Sources on every line; **label dataset published as an open, versioned set**; the missing-papers list for the graph |
| **Nalini Edwin** (System comms) | Storytelling about the graph | A story she'd retell; the graph looking valuable | **The bottle moment** and the headline line (§7.3) |

### 8.1 Two things other teams won't think of (both aimed at Dr. Sarabu)

**1. The alert that fires inside the clinician's normal software**
- When a clinician prescribes lithium during a heat forecast, a card appears: *"Heat wave forecast this week. Lithium: dehydration can push levels into the toxic range. [Send patient heat label] [See evidence]."*
- Uses CDS Hooks, the real standard EHRs use for these alerts. A clinical informatician will recognize it right away.
- It answers "could this actually be used?" A mock-up of one screen plus the card JSON is enough.

**2. The child and caregiver case**
- Topiramate, a common pediatric epilepsy and migraine drug, can stop children from sweating. Its FDA label notes this mostly in children.
- Children can't report symptoms themselves, so the patient view goes to the **parent and the school nurse or camp**: *"Your child's medicine can make it hard to sweat. During hot days and sports, watch for…"*
- Useful contrast: topiramate's label *does* mention the risk, yet heat guidance mostly doesn't, so the gap isn't only on labels.
- **Check before using it:** the claim must be in our master list with a verified citation.

---

## 9. Backbone: heat across the medicine's whole journey

This covers supply chain, the clinician side and the patient side in one picture, and it reflects the systems thinking the hackathon favors.

| Stage | What heat does | Clinician/system action | Patient/caregiver action |
|---|---|---|---|
| **1. Prescribe** | Some drugs add heat risk | EHR alert during a heat forecast; review combinations before summer | — |
| **2. Dispense / ship** | Mail-order packages go out of range (every shipment in the Utah study) | Pharmacy holds heat-sensitive mail orders or ships them insulated during heat alerts | "Bring the package in right away" |
| **3. Store at home** | Insulin and EpiPens degrade; outages spoil refrigerated drugs | Refill reminders before heat season; outage plan | Thermochromic bottle: "Too warm? Here's what to do" |
| **4. Take it** | Insulin absorbs faster; patches release more drug; lithium builds up | Heat Dose Compass | Plain label line: drink water, keep taking it |
| **5. Watch for warning signs** | Signs of heat illness show up differently on each drug | Call list sorted by risk | "I feel dizzy" button, which reaches the clinic |
| **6. After the heat wave** | Outages lead to surges in refills and ER visits (Hurricane Beryl, Houston) | Follow-up list; report adverse events | Check levels if advised |

Sources for each row are in `research-notes/` (storage/supply, pharmacokinetics, epidemiology) and `report/Prescribed drug heat risks.md`. Verify citations before putting them on a slide.

---

## 10. Proposed changes to `spec.md`, and open questions

**Proposed changes**
1. **§2 Audience:** keep it clinician- and health-system-facing. Add the patient/caregiver page, sent by the clinic, as the way into the story. Lead with plain language (§6).
2. **New backbone:** the six-stage medicine journey (§9) organizes the site.
3. **§3.7 Stretch → core:** the thermochromic bottles and the EHR alert card move up. The storage sensor stays optional.
4. **New:** child/caregiver label (topiramate), if the citation checks out.
5. **New:** "10 questions research must answer next" slide and data-responsibility note.
6. **§11 answers proposed:** sensor = no (unless parts are in hand and someone knows ESP32); thermochromic = yes, order tonight.

**Open questions for us both**
- Do we agree on SBH as the client and the two-view framing?
- Which ~8 drugs get polished labels? Current suggestion: lithium, loop diuretics, topiramate, oxybutynin, fentanyl patch, insulin/pump, SGLT2 inhibitors, an antipsychotic.
- Who orders the thermochromic stickers tonight?
- Tech stack for the site.
- Do we include tier C (unverifiable) sources anywhere? Current answer: pitch hook only, always labeled.

---

## 11. Build priorities for tonight and tomorrow

A half-working demo loses technical points (25%). Priorities:

1. **Must have**
   - label data for ~8 drugs, with sources
   - plain-language labels
   - patient phone page and clinician call list (both reading the same data)
   - bottle props
2. **High value, small effort**
   - journey map (mostly design; the evidence is already in our notes)
   - EHR alert card (one screen mock-up is enough)
   - "10 questions" slide
3. **Only if ahead**
   - child label
   - city toggle
   - publishing the dataset
   - Spanish
4. **Cut**
   - storage sensor
   - live SMS
   - full NYC map

**Suggested order**
- **Tonight:** run the hidden-heat-drug check (does the drug → mediator ← heat chain rank known heat drugs high?) and build the label data file. Order the stickers.
- **Sat 10 AM–1 PM:** clinician view, patient view, QR loop, journey map.
- **Sat 1–2:30 PM:** EHR card, polish, rehearse, record a backup video.
- **Sat 2:30–3 PM:** submit on Devpost (deadline 3:00 PM).

### Pitch run-of-show (3 minutes)
1. **0:00** Bottle in a judge's hand; the warning appears. "Your medicine warns about alcohol, not heat."
2. **0:30** Journey map: heat affects the medicine from the pharmacy to the kitchen.
3. **1:00** The graph: medicine → dehydration ← heat chain, hidden heat drugs, "your graph has 15 findings; here are 60 studies to add."
4. **1:45** Live: heat forecast → EHR alert fires → clinician sends the label → judge's phone shows it (including the child version) → "I feel dizzy" → that patient tops the call list.
5. **2:40** "Works for any city, every claim is sourced, the dataset is open, and here are the 10 questions research must answer next."
