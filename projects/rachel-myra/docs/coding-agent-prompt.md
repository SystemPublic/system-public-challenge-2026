You're working on our hackathon app, "The Missing Label," in this repo. The Next.js app is in `web/` (it runs on port 3000 with `npm run dev`). The Devpost deadline is 3:00 PM today and the code freeze is 2:15 PM, so work fast, in priority order, and keep the app running after every step.

Read these first (10 minutes max): `docs/build-plan.md` (v2, the plan you're executing), `spec.md` §4.0a and §5.0 (focus and simplification), and the existing code in `web/src/app/board`, `web/src/app/phone`, `web/src/lib/loop.ts`, `web/src/lib/panel.ts` and `web/src/lib/kb.ts`.

THE PRODUCT IN ONE SENTENCE
On the morning a heat wave is forecast, a clinic nurse sees which patients are Low, Medium or High risk because of their medicines and their home, texts each group a simple plan, and each patient sees on a map where it's cooler, where help is, how to get there, and the safest time to go.

DESIGN RULES (non-negotiable)
0. Colors: KEEP the current palette in `web/src/styles/tokens.css` (Okabe–Ito: solid chip + light tint + dark ink, rounded outlined pills like the bucket chips). Rachel likes it. Add risk-group tokens in the same style and use them everywhere (map dots, group tabs, chips, patient plan): **High = orange** (reuse the Hold vermillion: solid #d55e00, tint #fbe3d6, ink #a0410a); **Medium = yellow** (solid #f0c419, tint #fdf4d3, ink #7a5c00; give yellow map dots a thin dark outline so they show on a light map); **Low = blue** (reuse the Store-cool blue: solid #0072b2, tint #dcebf5, ink #005a8c). Other colors are fine if they stay in this palette and style. On the Medicines page, the medicine groups keep their existing colors.
1. Outcome first, evidence on click. Main screens show only who's at risk, what to do and where to go. All evidence (sources, System graph, FDA reports, badges, scores) goes behind a "Why?" / "See the evidence" button that opens a panel: a plain reason first, then the details.
2. Readable by anyone, including non-medical people. On main screens, no codes, scores or jargon: no FLAG/CHANGE, ROR, T1–T8, "jurisdictions," "negative-control band," "narrow therapeutic index," "HeatRisk 4 Magenta," and no raw scores like 0.605. Use plain words ("check on this person," "about 4 times as many heat reports"). Every chart title states the takeaway.
3. Few visuals, clean and pretty: light mode, calm colors, lots of white space, one main action per screen, at most 3 colors and one legend per chart. Large type on the patient side.
4. No invented data. Every number and sentence comes from a file in `data/`. If something isn't available, show a small labeled placeholder naming the file it would come from. Patients are synthetic; label them so.
5. No dose advice to patients. Patient messages end with "Talk to your doctor or pharmacist."

TASKS, IN ORDER (stop at the line if time runs out)

P0. Simplify the shell (~20 min)
- Top navigation becomes 4 tabs: Patients (`/board`), Map (`/map`), Medicines (`/medicines`), Patient app (`/phone`). Put a small "Methods" link to `/evidence` in the footer.
- Move the current evidence map from `/map` to `/medicines` (update links). Remove the 6-step journey bar and the Readiness page from navigation (keep the files).
- Home page: the one-sentence product plus two buttons, "I'm a clinician" → `/board` and "I'm a patient" → `/phone`.

P1. Heat + help map (~60 min), the centerpiece. Put the components in `web/src/components/map/`.
- deck.gl + MapLibre (already installed) with a light OpenFreeMap basemap. **2D by default, with a "3D" toggle** (pitch plus building extrusions).
- Heat layer first: neighborhoods shaded hotter → cooler from `data/processed/hvi_nta2020.geojson` (or the hyperlocal temperature sensors), with one legend: "Hotter / Cooler".
- Help layer: `data/processed/community_resources_nyc.geojson` (READY: 4,484 places). It has every community resource that helps in a heat wave (cooling centers, libraries, senior centers, community centers, soup kitchens/food pantries, NYC Care community organizations, other nonprofits). Properties: id, name, type, address, borough, zip, phone, website, hours, services, languages, operator, source, accessed (missing fields are null). Types: Cooling center, Library, Senior center, Community center, Food pantry / soup kitchen, Community organization, Homeless services, Recreation center, Cool indoor public place, Outdoor spray shower / pool. Default filter: everything except "Outdoor spray shower / pool" (outdoor, not for high-risk patients). Show "Hours and services can change. Call ahead." on the card. Don't edit the file. Simple icons by type, and a type filter (checkboxes). Click a place → a small clean card: name, type, address, hours, phone, website, services, languages, and a "Directions" button; show only the fields that exist.
- Clinician mode (`/map`): **every patient as a colored dot at their home**, using `home_lat` / `home_lon` from `data/processed/synthetic/patients.csv` (300 synthetic patients). Color by risk group (Low / Medium / High, same mapping as P2), with a legend and a group filter. Click a dot → a card with the synthetic name, age, group, one plain sentence of why, and "Text" and "Why?" buttons. Select an area (lasso or a click on a neighborhood) → its patients by group → "Text this group" (reuse the existing send API). Label the layer "Synthetic patients."
- Patient mode (a component reused in P3): home location, the nearest help place and a route line with walk minutes, from `data/processed/synthetic/cooling_match.csv`; nearest subway station from `subway_stations_nyc.geojson`. "Leave by X" uses the hourly heat in `replay_heatwave_hourly.csv`. Show "Ask for a delivery instead" when the walk is long, when the patient can't reach a cool place alone (`q5_can_reach_cool_place`), or during the hottest hours.

P2. Risk groups for the clinician (`/board`, ~40 min)
- Groups come from `data/processed/panel_scores_replay.json` → `patients[].readiness.level`: low → Low, medium → Medium, high + very_high → High.
- Layout: High / Medium / Low tabs or columns with counts. Each row shows the synthetic name, age, ZIP, ONE plain sentence of why (rewrite `readiness.drivers` into plain words), and status.
- A "Text this group" button sends each patient their group's message through the existing simulated SMS loop. Keep the escalation (contact notified when there's no reply) and the fast-forward buttons.
- "Why?" on a row opens a side panel: their medicines, what each one does in heat (from `data/kb/knowledge_base.json`), the System pathway, and source links.
- Patients with `alert_opt_in` false (in `data/processed/synthetic/questionnaire.csv`) get "Call instead," not a text.

P3. Patient "my heat plan" (`/phone/[id]`, ~40 min). Large type, simple, phone-sized.
Order on the screen:
1. "Your heat risk today: High," plus one sentence of why.
2. Safest time to go out: an hourly strip, green = OK and red = stay in, from `replay_heatwave_hourly.csv`.
3. Where to go: the nearest cool place on the 2D map (3D toggle), with the route, walk time and "leave by X."
4. Or stay in: the delivery option.
5. What to watch for, then "Talk to your doctor or pharmacist."
6. The existing simulated text thread and the "I'm OK" / "I feel unwell" / "No AC" buttons.
Messages differ by group: Low = heads-up; Medium = + nearest help + safe hours; High = + route + check-ins + contact.

P4. Medicines, outcome first (~30 min)
- `/medicines`: replace the tile wall with a clean grouped list. Group headers in plain words, from the knowledge-base buckets (e.g. "Check on these patients," "The dose may need a look," "Store it cool"). One row per medicine: a plain one-line risk, evidence as "Strong / Some / Early signs," who prescribes it, ✓/✗ "Label warns about heat," ✓/✗ "Guidance says what to do."
- `/drug/[id]`: the top shows only the plain message and what to do. Move everything else (FLAG/CHANGE, Compass, claims, guidance quotes, combinations) behind a "See the evidence" toggle. Translate any French or German guidance quotes to English.

P5. "How heat and medicine add up" (~25 min)
- A simple 3-column picture: medicines → body effect (dehydration, low salt, kidney strain, can't sweat, drowsy) ← heat, from `data/processed/system_api_pathways.csv` (the live-API rerun; columns drug_label, mediator, drug_leg_studies, heat_leg_studies; fall back to `system_pathways.csv`) and `system_api_findings.csv`. Line thickness = number of studies in the System graph. Clicking a line opens "Why?" with System study counts. Put it on `/medicines` and a one-line version on the patient plan ("Your two medicines both make it harder to stay cool").

──── Everything above this line = complete demo ────

P6. Only if time remains
- An intake questionnaire screen (`/phone/signup`) modeled on CDC's CHILL'D-Out questionnaire (the 7 areas and questions are listed in `research-notes/advisor-models.md`): one question per screen, big buttons, the Drugs section pre-filled from the medication list, and a caregiver/emergency contact. It ends with the resulting group and why. The answers that already exist in `data/processed/synthetic/questionnaire.csv` map onto these areas.
- An "EHR side panel" view (`/ehr/[id]`): the patient's plan in a narrow layout, plus have `/api/cds-hooks` return a card that links to it. Label it "Prototype, designed to embed via SMART on FHIR / CDS Hooks."

WORKING RULES
- Don't rebuild what works: the send/escalation loop, SQLite, the APIs and the data files.
- Keep `npm run dev` working after every task. Fix TypeScript and lint errors as you go.
- After each P-step, check it in the browser at desktop width and at phone width (375 px), then commit with a short message. Don't push.
- Don't edit or add anything in `data/`. Don't touch `.env`.
- If two agents are running, the map agent owns `web/src/components/map/` and `/map`; the other agent owns everything else. Never edit the same file.
- When you finish or stop, report: what's done, what's not, and anything shown as a placeholder.
