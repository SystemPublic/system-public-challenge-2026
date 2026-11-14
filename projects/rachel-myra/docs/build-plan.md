# Build plan v2: The Missing Label (rewritten Sat 14 Nov, 11:50)

**Deadline:** Devpost **3:00 PM**, so we submit by **2:45 PM**. Pitches 3–4 PM.
**Time left:** about 3 hours. **Code freeze at 2:15 PM.**
The old 8-step plan is archived in `docs/build-plan-v1-archive.md`. `spec.md` is still the source of truth (§4.0a focus, §5.0 simplify).

---

## The product in one sentence
**On the morning a heat wave is forecast, a clinic nurse sees which patients are Low, Medium or High risk because of their medicines and their home, texts each group a simple plan, and each patient sees on a map where it's cooler, where help is, how to get there, and the safest time to go.**

## Design rules (decided)
1. **Outcome first, evidence on click.** Screens show who's at risk, what to do and where to go. The evidence sits behind a **"Why?"** button: the plain reason first, then sources, System graph, FDA reports and badges.
2. **Readable by anyone:** no codes or scores on main screens (no FLAG/CHANGE, ROR, T1–T8, "jurisdictions," "HeatRisk 4 Magenta"). Every chart title states the takeaway. Numbers in words.
3. **Few visuals:** 6 (below). Everything else is cut or moved into "Why?" / nerd stats.
4. **Pretty and clean:** keep the current palette (Okabe–Ito chips Rachel likes); risk groups **High = orange, Medium = yellow, Low = blue**; light mode, lots of white space, one main action per screen. At most 3 colors per chart.
5. **Patient map: 2D by default** (older patients), with a 3D switch.
6. **No invented data.** Missing pieces show a labeled placeholder naming the file they'll come from. Synthetic patients only.

## The 6 visuals we keep
| # | Visual | Where | Built from (already in the repo) |
|---|---|---|---|
| 1 | **Heat + help map** (2D/3D) | Clinician and patient | `hvi_nta2020.geojson` / `hyperlocal_temp_sensors.geojson` (heat), `cooling_places_nyc.geojson` (1,868 places), `synthetic/cooling_match.csv` (each patient's nearest place + walk minutes), `subway_stations_nyc.geojson` |
| 2 | **Risk groups: Low / Medium / High** + "Text this group" | Clinician | `panel_scores_replay.json` → `readiness.level` (low 65 / medium 104 / high 90 / very_high 41 → **very_high merges into High**), `readiness.drivers` for the plain "why" |
| 3 | **Medicine chart** (the simple evidence map the challenge requires) | Clinician | `data/kb/knowledge_base.json`: one row per medicine, grouped by what to do, evidence as Strong / Some / Early signs, who prescribes it, ✓/✗ "label warns," ✓/✗ "guidance says what to do" |
| 4 | **"How heat and medicine add up"** picture | Both (simple), "Why?" (detail) | `system_pathways.csv`, `system_drug_mediator_findings.csv`: medicine → body effect (dehydration, low salt, kidney strain, can't sweat, drowsy) ← heat. This is our visible System-graph use, and it explains stacking |
| 5 | **Safest time to go outside** (hourly strip) | Both | `replay_heatwave_hourly.csv` (heat index by hour) |
| 6 | **"My heat plan"** | Patient | the patient's group + why, nearest help, route + walk time, safe hours, what to do, delivery option, simulated text thread |

**Cut from the main screens:** call-first scatter, Compass, FLAG/CHANGE meters, forest plot, Sankeys, node graph, treemap, heatmaps, swimlanes, timelines, Medicine Cabinet, the 6-step journey bar, the Readiness placeholder page. (Evidence pieces can live behind "Why?" or in nerd stats if they already work.)

---

## What we should do, in order
Work in this order. If time runs out, everything above the line still makes a complete demo.

### P0. Simplify the shell (≈20 min), first
- Navigation down to **4 tabs:** **Patients** (risk groups), **Map**, **Medicines**, **Patient app**. Small "Methods" link in the footer for nerd stats.
- Remove the 6-step journey bar and the Readiness page from navigation.
- Rename the evidence map route `/map` → **`/medicines`**, so `/map` is the real map.
- Home page = the one-sentence product + two buttons ("I'm a clinician," "I'm a patient").
- Sweep the main screens for jargon (list in Design rules #2).

### P1. Heat + help map (≈60 min), the centerpiece
- deck.gl + MapLibre, light basemap (OpenFreeMap). **2D default, 3D toggle** (pitch + building extrusions).
- **Heat layer first:** hottest → coolest neighborhoods, with one simple legend ("hotter / cooler").
- **Help layer:** every community resource that can help in a heat wave, from **`data/processed/community_resources_nyc.geojson`** (being built now, see P1b; until it exists, use `cooling_places_nyc.geojson`). Icons by type with a type filter; **click → a small card**: name, type, address, hours, phone, website, services, languages, and "Directions."
- **Clinician mode: every patient as a colored dot at their home** (`synthetic/patients.csv` → `home_lat`/`home_lon`), colored by risk group (Low / Medium / High). Click a dot → name, group, plain why, "Text" and "Why?". Filter by group; lasso or click an area → "Text this group." (Synthetic patients, so individual dots are fine; a real deployment would show them only inside the clinic's login.)
- **Patient mode:** their home, nearest help, and the **route line** with walk minutes (from `cooling_match.csv`), plus the nearest subway station.
- "Best way there given the heat" (honest version for today): walk minutes × heat at that hour → **"leave by X"**; offer **delivery instead** when the walk is long, the patient can't reach a cool place alone (`q5_can_reach_cool_place`), or it's the hottest hours. Shade-aware routing goes in "Next steps."

### P1b. Community resources data (Claude) — DONE 11:55: `community_resources_nyc.geojson`, 4,484 places
Scrape and merge **all community-based organizations and nonprofits that could help in a heat wave** into one file: `data/processed/community_resources_nyc.geojson`, one point per place, with name, type, address, borough, ZIP, phone, website, hours, services, languages, source and access date.
- Types: cooling centers, libraries, senior / older adult centers, community centers, soup kitchens and food pantries, NYC Care community-based organizations, other nonprofits (health, housing, immigrant services), and rec centers.
- Sources: NYC Care CBO directory (https://www.nyccare.nyc/community-based-organization/), NYC Open Data (older adult centers, food programs, libraries, community centers), the existing `cooling_places_nyc.geojson`, and others as found. Each one is listed in `data/SOURCES.md`.
- Shown on the map (P1) with a click-for-details card; used to match patients to the nearest suitable help (P3).

### P2. Risk groups for the clinician (≈40 min)
- Rework `/board` into **three columns or tabs: High / Medium / Low** with counts.
- Each patient row: name (synthetic), age, ZIP, **one plain sentence of why** (from `readiness.drivers`, e.g. "No AC, lives alone, two medicines that both affect heat"), status.
- **"Text this group"** sends each patient their group's message (simulated SMS). High also notifies the caregiver/emergency contact when there's no reply (the existing escalation + fast-forward).
- **"Why?"** on a row opens the evidence: which medicines, what each does in heat, the System pathway, source links.
- Respect `alert_opt_in`: not opted in → "call instead" (open item in spec §12.3).

### P3. Patient "my heat plan" (≈40 min)
- Upgrade `/phone/[id]` (demo phone) into the patient app, with **large type** and **2D map by default**:
  1. "Your heat risk today: **High**" + why in one sentence
  2. **Safest time to go out** (hourly strip, green/red)
  3. **Where to go:** nearest cool place + map + route + walk time, "leave by X"
  4. **Or stay in:** delivery option
  5. **What to watch for** and "call your doctor or pharmacist" (no dose advice)
  6. The simulated text thread + "I'm OK" / "I feel unwell" / "No AC" buttons (already built)
- Message per group (Low: heads-up; Medium: + nearest help + safe hours; High: + route + check-ins + contact).

### P4. Medicine chart + medicine page, outcome first (≈30 min)
- `/medicines`: replace the tile wall with a **clean grouped list**: group header ("Check on these patients," "Dose may need a look," "Store cool," …), then a row per medicine with plain one-line risk, evidence in words, prescribers, ✓/✗ label, ✓/✗ guidance.
- `/drug/[id]`: top = the plain message + what to do. **Everything else behind "See the evidence."**

### P5. "How heat and medicine add up" (≈25 min)
- One simple 3-column picture: **medicines → body effect ← heat**. Thick line = more studies in System. Click a line → "Why?" with System study counts.
- A small version on the patient's plan: "Your two medicines both make it harder to stay cool."

### P5b. Heat-day time-lapse (`/replay`) — REBUILT 1:35 (radar-style HRRR heat blobs under streets; click a patient → why, medicines + System evidence, nearest cool place, one route, message; no lines or rings) (new files: `web/src/app/replay/`, `web/src/components/replay/`, `web/src/lib/replay.ts`); add a nav link after Myra's agent finishes the nav
- About 20 seconds of the replay heat day, hour by hour (`replay_heatwave_hourly.csv`): the map warms from blue to orange; patient dots in their risk-group colors pulse when their heat-risk hour hits; the clock, temperature and counters (texts sent, check-ins) tick. Play / pause / scrub. Pitch opener. Only real data; message and check-in timing comes from `panel_scores_replay.json`.
- Rejected ideas (Rachel, Sat 14 Nov): cooling deserts, 3D "walk in their shoes," QR code for judges.

### P5c. Clinician ↔ patient messages — BUILT 1:00 (Rachel's session; new files only)
- `/messages` inbox and `/messages/[id]` conversation: thread of alerts, texts, contact texts and the patient's taps; quick replies; "Send heat safety alert"; free-text box (simulated, also lands on the demo phone).
- **To do (Myra's agent, `docs/coding-agent-followup.md`):** a "Messages" button on every patient row, map card and Why? panel → `/messages/<id>`; Messages in the top nav; `/replay` in the footer.

### ─── line: above here = a complete demo ───

### P6. If time (each ≈20–30 min, in this order)
- **Intake questionnaire screen** (patient sign-up), modeled on **CDC's CHILL'D-Out questionnaire** (Cooling, Housing, Isolation & mobility, eLectricity, Learning, Drugs, Outside; from the NACHC EHR guide the advisor sent, see `research-notes/advisor-models.md`). Drugs is filled in from the medication list. Shows the resulting group and why.
- **"Embedded in the EHR" view:** the patient's plan rendered in a narrow side-panel layout + the existing CDS Hooks route (`/api/cds-hooks`) returning a card that links to it. Label: "Prototype, designed to embed via SMART on FHIR / CDS Hooks." Use the NACHC EHR page as the model.
- Spanish toggle for the patient plan.

### 2:15 PM: code freeze → test → submit
- Run the demo end to end on the replay heat day: Patients → Text High group → demo phone shows the text and plan → no reply → fast-forward → contact notified → board updates → map.
- Test the phone on the venue Wi-Fi (hotspot backup).
- Check that every number on screen traces to a file.
- Record the backup video. Devpost: description, screenshots, repo, data sources, limitations. **Submit by 2:45.**

---

## What the advisor's models give us (see `research-notes/advisor-models.md`)
- **CHILL'D-Out** → our questionnaire; **5 Rights of Clinical Communication** → pitch framing; **message-fatigue rules** → text only on high-heat days, specific to the person; **La Clínica** → proof that clinic texts work and are trusted (2,608 → 11,535 recipients). Our step up: scored groups, medicines explained and stacked, help + route + safe hours, contact escalation, any health system.

## Who does what (suggested; you two decide)
- **Track A (map person):** P1 (patient dots + resources layer), then the map parts of P3.
- **Claude (this session):** P1b, the community resources data file.
- **Track B (app person):** P0, P2, the rest of P3, P4, P5.
- Whoever finishes first: questionnaire screen, EHR view, pitch slides.
- Coding agents can run each track in parallel. Two agents must never edit the same file. Map files live in `web/src/components/map/`; everything else stays where it is.

## Challenge checklist (check before submitting)
- [ ] Visual evidence map grouped by action, with evidence strength, prescribers and guidance gaps → **Medicines** tab (P4)
- [ ] Meaningful System graph use → "How heat and medicine add up" (P5) + "Why?" panels + nerd stats (verification, audit)
- [ ] Usable for counseling and outreach → Patients tab + texting + map (P1–P3)
- [ ] Readable by a non-specialist → design rules
- [ ] Every number traces to a file; synthetic patients labeled
- [ ] Devpost submitted by 2:45

## Already built (don't rebuild)
- Next.js app in `web/` (runs with `npm run dev` on port 3000, LAN-visible)
- `/board` clinic board with send, multi-send, fast-forward and message log; `/phone/[id]` demo phone with simulated push + SMS and check-in buttons; SQLite loop in `web/src/lib/loop.ts`
- Evidence map, drug pages, nerd stats (`/evidence`), knowledge base API, System live layer API, CDS Hooks route
- All data in `data/processed/` and `data/kb/` (`data/SOURCES.md` doesn't exist yet; add it before Devpost so the data-sources section is easy to write)
