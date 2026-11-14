# Cool-Aid

_Formerly "The Missing Label"; name may change._

**Heat-wave outreach for patients whose medicines make heat more dangerous.**
Built for **Visualize Challenge 3** of the System Public Challenge (NYC, 13–14 Nov 2026): *Which common medications make heat more dangerous, and what should prescribers and health systems do about it?*

> Prototype. Synthetic patients only. Considerations for clinicians, not medical instructions.

_Last updated: Sat 14 Nov 2026, 1:35 PM. Keep this file current whenever the plan, data or app changes._

---

## What it does
On the morning a heat wave is forecast, a clinic nurse sees which patients are **Low, Medium or High risk** because of their **medicines and their home**, texts each group a simple plan, and each patient sees on a **map** where it's cooler, where help is, how to get there, and the safest time to go.

**For the clinician**
- **Risk groups** (High / Medium / Low), with one plain sentence of why for each patient, a **"Text this group"** button, and **"Why?"** to see the evidence.
- **Heat + help map:** hottest and coolest neighborhoods, every patient as a colored dot, and the community resources near them.
- **Medicines:** the evidence map the challenge asks for, now with an **"In heat" column** (↑ stronger / ↓ weaker / ↕ depends, from the Heat Dose Compass), as a simple grouped list showing what to do, how strong the evidence is, who prescribes it, and whether the label and guidance warn about heat.
- **Messages:** one click from any patient opens the **conversation with that patient** (`/messages/[id]`): every alert and text sent, texts to their contact, their "I'm OK / unwell / No AC" replies, quick-reply templates, and a box to text them. The inbox (`/messages`) puts "Needs a call" first.
- **Outreach that escalates:** if a High-risk patient doesn't reply, their caregiver or emergency contact is alerted.

**For the patient** ("my heat plan," large type, 2D map by default with a 3D switch)
- Their risk today and why
- The safest hours to be outside
- The nearest cool place, the route, the walk time and "leave by"
- A delivery option if going out isn't safe
- What to watch for, plus "I'm OK" / "I feel unwell" buttons

**Designed to embed in the EHR:** SMART on FHIR launch and a CDS Hooks card. The prototype runs stand-alone.

## Design rules
1. **Outcome first, evidence on click:** screens show who's at risk, what to do and where to go; the evidence sits behind "Why?".
2. **Readable by anyone:** no codes or jargon on the main screens.
3. **Few visuals:** 6 instead of 21.
4. **No invented data:** every number traces to a file in `data/`.
5. **No dose advice** to patients.
6. **Colors:** the Okabe–Ito chip palette. Risk groups are **High = orange**, **Medium = yellow**, **Low = teal** (`#0e7c86`, which replaced the old blue everywhere). Logo and tab icon: a hot-and-cool pill (orange + teal), `web/src/app/icon.svg`. Font: Plus Jakarta Sans.

## How the System Public Graph is used
- **Patient cards show the graph directly:** click a patient (time-lapse, map) to see each of their medicines → body effect ← heat with System study counts, and which medicines stack on the same effect.
- **Medicine → body effect ← heat pathways** (dehydration, low sodium, kidney strain, impaired sweating) explain *why* a medicine matters and how two medicines **stack**.
- **Second extractor:** our extracted numbers are checked against System's findings for the same papers (verification badges).
- **Gap finder and audit:** links the graph implies but no study has tested, plus a fix list of mislabeled findings.
- **Evidence behind 9 product questions**, from "which medicines are risky?" to "is the medicine still good?" (`spec.md` §8.5c).
- **Live layer:** relationship counts fetched from the API.
- **Presentation write-up:** `docs/system-api-story.html` covers the data we had and the four jobs System did (find, check, spot gaps, feed the app), with charts and lines to say on stage. More pictures: `docs/data-pipeline.svg`, `docs/system-funnel.html`, `docs/system-cleaning-chart.html`, `docs/data-cleaning-charts.html`.

## What we built on (advisor's models), and how we go further
- **CDC CHILL'D-Out questionnaire** (Cooling, Housing, Isolation & mobility, eLectricity, Learning, Drugs, Outside): our intake questionnaire is modeled on it. We score the answers into risk groups, fill in **Drugs** from the medication list, and act on each answer.
- **NACHC, *Heat-Related Illness Management in EHR Systems*,** and **La Clínica's heat text alerts:** our messaging follows the "5 Rights of Clinical Communication" (right person, message, method, time, priority) and sends only on high-heat days. Messages are personal, not one per diagnosis group.
- Notes and a comparison table are in `research-notes/advisor-models.md`.

## Run it
Requirements: Node 24, Python 3 (`py -3` on Windows). Java 17 is needed only to regenerate Synthea patients.

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000. The dev server listens on the local network, so a phone on the same Wi-Fi can open `http://<laptop-ip>:3000/phone`.

Keys go in `.env` (see `.env.example`). Only `SYSTEM_API_KEY` is required; openFDA and OpenRouteService keys are optional. **Texts and push notifications are simulated** in the demo and labeled as such.

## App pages (`web/src/app`)
| Page | What it is |
|---|---|
| `/` | Home: "I'm a clinician" / "I'm a patient" |
| `/board` | **Patients:** risk groups, texting, escalation, fast-forward clock |
| `/map` | **Heat + help map** (being rebuilt; the old evidence map is moving to `/medicines`) |
| `/medicines`, `/drug/[id]` | **Medicines:** grouped list and one page per medicine (evidence behind "See the evidence") |
| `/phone`, `/phone/[id]` | **Patient app:** "my heat plan" and the simulated text thread |
| `/messages`, `/messages/[id]` | **Messages:** clinician inbox and the conversation with one patient (simulated texts) |
| `/replay` | **Heat-day time-lapse** (pitch opener) |
| `/evidence` | **Methods** (nerd stats): verification, audit, formulas, sources |
| `/api/*` | Knowledge base, System live layer, CDS Hooks, alert loop |

## Repo layout
| Path | What's in it |
|---|---|
| `spec.md` | **Source of truth:** product, decisions, open questions |
| `docs/build-plan.md` | Current build plan (v2), task order and challenge checklist |
| `docs/coding-agent-prompt.md` | The prompt the coding agent is running |
| `docs/` (other) | Verification method, System API guide, setup, earlier plans and notes |
| `research-notes/` | Research notes and the advisor's models (`advisor-models.md`); `sources/` holds the NACHC guide PDF |
| `data/kb/` | **Knowledge base** (`knowledge_base.json`): 15 medicines, claims, badges, guidance, label and FDA signals |
| `data/processed/` | Cleaned data: patients (synthetic), risk scores, climate, place, System outputs, **community resources** |
| `data/raw/` | Raw downloads and API caches |
| `data/SOURCES.md` | Where each dataset came from |
| `scripts/` | Python pipeline: literature, System API, openFDA, guidance, climate, place, routing, community resources |
| `lib/` | Shared TypeScript logic (patient scoring, thermal model, types) |
| `db/` | SQLite database for the alert loop |
| `config/health-systems/` | Per-health-system settings (`sbh.json`) |
| `schemas/` | JSON schema for the knowledge base |
| `web/` | The Next.js app |
| `report/` | Research report on prescribed drugs and heat |

## Key data
| File | What |
|---|---|
| `data/kb/knowledge_base.json` | 15 medicines: what to do, evidence strength, mechanisms, prescribers, guidance, label, FDA reports |
| `data/processed/panel_scores_replay.json` | 300 synthetic Bronx patients scored for the replay heat day (risk level + reasons) |
| `data/processed/synthetic/` | Synthetic patients, medicines, questionnaire answers, contacts, cooling-place matches |
| `data/processed/community_resources_nyc.geojson` | **4,484 places that help in a heat wave:** cooling centers, libraries, senior centers, food pantries / soup kitchens, community centers, community organizations, homeless services (built by `scripts/community_resources.py`) |
| `data/processed/replay_heatwave_hourly.csv` | Hourly heat for the replay heat wave (LaGuardia, Central Park) |
| `data/processed/replay_hrrr_grid.json` | Hourly "feels like" °F on a 0.03° grid over NYC, June 22–26, 2025 (NOAA HRRR via Open-Meteo; `scripts/climate_hrrr_grid.py`) |
| `data/processed/hvi_nta2020.geojson` | NYC Heat Vulnerability Index by neighborhood |
| `data/processed/system_api_pathways.csv` | Medicine → body effect ← heat pathways from the System API |

## Status (Sat 14 Nov, 12:15 PM)
- **Done:** data pipeline, knowledge base, synthetic panel and scores, System API rerun, alert loop (board + demo phone), community resources data.
- **In progress (coding agent):** simplified navigation, heat + help map, risk groups, patient plan, simplified medicines page, "how heat and medicine add up."
- **Built:** **heat-day time-lapse** at `/replay` (pitch opener). Radar-style heat blobs from real hourly "feels like" temperatures (NOAA HRRR 3 km model via Open-Meteo, `data/processed/replay_hrrr_grid.json`), June 22–26, 2025, drawn under the streets and labels. The 300 synthetic patients are dots in their risk colors. **Click a patient** to see why they're at risk, **their medicines and how each adds to heat risk, with study counts from the System graph** (and which medicines stack), their nearest cool place with leave-by time, **"Show the way"** (one walking route at a time, OSRM), and **"Message"**. Not linked in the nav yet.
- **Built:** **clinician messages** at `/messages` and `/messages/[id]`. Myra's agent adds the "Messages" buttons on the board, map and Why? panel (`docs/coding-agent-followup.md`).
- **Open:** project name; the one specific use case for the pitch.
- **Deadline:** Devpost by 2:45 PM (hard deadline 3:00 PM).

## Caveats
- Research prototype, not clinical advice. All patients are synthetic.
- Directory data (hours, services) changes; the map says "call ahead."
- About 20% of System's extractions may be inaccurate (per System), so findings are cross-checked. Verification is automated; no human review.
- FDA adverse-event reports are a warning signal, not proof.
- The System Public Graph is licensed CC BY-NC 4.0.

## Team
Rachel and Myra.
