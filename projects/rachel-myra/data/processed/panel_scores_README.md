# Panel scores (patient-side logic, build plan Step 4)

**Every patient here is SYNTHETIC** (data/processed/synthetic). Not clinical advice. No dose advice anywhere.

```bash
node --experimental-strip-types scripts/compute_panel.ts --today 2026-11-14   # writes the 3 files below
node --test --experimental-strip-types lib/patient/tests/*.test.ts            # 60 tests
```

Code: `lib/patient/` (dependency-free TypeScript; `index.ts` = pure modules the app imports; `load-node.ts` = Node file loaders), types in `lib/types/patient.ts` and `lib/types/health-system.ts`, config in `config/health-systems/sbh.json`. The script is deterministic for a given `--today` and picks up the knowledge base and routing files automatically each time it runs.

## Files

| File | What |
|---|---|
| `panel_scores_today.json` | As of 2026-11-14 with the live NWS HeatRisk (all 0). `summary`, `outlook` (probability-bar series), `scatter` (x, y, tier per patient), `call_list`, `drill_call_list_top25`, `story_patients`, `rules` (every rule table below), `patients` (full `PatientScore[]`) |
| `panel_scores_replay.json` | The same panel on the replay heat-wave day, **2025-06-24 (HeatRisk 4, magenta)**. Archived day-1 HeatRisk values stand in for the forecast. Ages are today's ages, because a replayed past heat wave hits today's patients |
| `panel_scores_summary.json` | Both summaries plus compact results for story patients S01–S10 |

## Headline results (run of 2026-11-14)

| | Today (Nov 14, HeatRisk 0) | Replay (Jun 24 2025, HeatRisk 4) |
|---|---|---|
| Call today | **0** (drill: 53 if HeatRisk were 3) | **59** |
| Call before heat wave | 0 | 0 (the wave is already under way) |
| Heat cards (non-urgent) | 266 | 207 |
| Routine | 34 | 34 |
| Auto safety alerts (push + SMS) | 0 | 116 |
| Morning cooling-place texts | 0 | 161 |
| Enrolled in escalation without a contact close enough | 120 of 208 | 157 of 208 (45-min budget) |
| Median worst-case time before anyone notices | 405 min | 405 min (longest gap between check-ins + T_max) |
| Probability bar, today | HeatRisk 0 (NWS), history 0% | HeatRisk 4 |
| Message guardrail failures | 0 | 0 |

Story patients on the replay day:

| ID | Rank | Tier | Readiness | x (exposure pts) | y (med level) |
|---|---|---|---|---|---|
| S01 | 1 | call today | very high | 12 | 4 |
| S08 | 3 | call today | very high | 9 | 4 |
| S04 | 4 | call today | very high | 9 | 4 |
| S06 | 10 | call today | very high | 7 | 4 |
| S10 | 14 | call today | very high | 6 | 4 |
| S03 | 115 | heat card + auto alert (her grandparent qualifies as a contact) | high | 7 | 2 |
| S07 | 139 | heat card (5 drugs, but a good home and a neighbor 7 min away) | medium | 2 | 3 |
| S05 | 161 | heat card (insulin storage) | medium | 5 | 2 |
| S02 | 184 | heat card | medium | 4 | 2 |
| S09 | 213 | heat card (epinephrine storage) + cooling text (no AC) | medium | 9 | 1 |

**Escalation finding.** Using real routed travel and assuming no car, a contact must arrive within 15 min on a 45-min budget. Most enrolled patients have no contact that close (157/208 on the replay day). That is the case for the buddy program and the priority call list. S01's only contact is a daughter 99 min away by car.

## Inputs used and fallbacks (from `meta.data_notes`)

- **Drug → heat defenses:** `data/kb/knowledge_base.json` where it covers the drug (231 patient-drug profiles, KB classes expanded to their ingredients). Elsewhere the **provisional** table in `lib/patient/provisional-drug-map.ts` is used, built from the synthetic generator's convenience tags. Every profile carries `source`. ACB scores come from `data/kb/anticholinergic_burden.csv` (ACB 2012); a drug that isn't on that scale counts as 0.
- **Contact travel:** `contacts_routed.csv` (routing agent, OSRM). We prefer `fastest_nocar_min` (walk or subway) and fall back to `fastest_min` (driving) only when no walk/subway route exists. If that file is missing, the naive `contacts.csv` placeholder is used and labeled `naive_placeholder`.
- **Cooling places:** `cooling_match.csv` (routed walking times; reference day Monday 2025-06-23). Hours are re-checked for the scored day against `cooling_places_nyc.geojson`. Places closed that day are dropped, and leave-by is recomputed. When nothing is left, the built-in fallback matcher picks the nearest open indoor place: step-free if needed, older-adult centers only for 60+, straight line × 1.3 at 0.8 m/s for 65+ or mobility needs (1.07 m/s otherwise), with a naive transit estimate above 25 min walking.
- **HeatRisk:** `heatrisk_zip_current.json` covers only 10453/57/58/60. Other ZIPs use the max of the forecast ZIPs that day, labeled `heatriskSource`.

## Rule tables (also in each JSON under `rules`)

### y-axis: medication heat-risk stack (`lib/patient/med-risk.ts`)
These are categories and reasons, not a black-box score. `level` (0–4) is the first matching rule. `plotY = level + min(body defenses, 9)/10` spreads dots within a band.

| Rule | Level | When |
|---|---|---|
| L4-combo | 4 | Danger combination: 2+ antipsychotics, lithium (narrow-margin, kidney-cleared) + diuretic/NSAID/ACEi-ARB/SGLT2, or thiazide + SSRI |
| L4-acb | 4 | Anticholinergic stack (2+ drugs, ACB total ≥3) and 3+ body defenses weakened |
| L4-stack | 4 | Another level-raising combination and 5+ body defenses weakened |
| L3-combo | 3 | ACEi/ARB + water pill, anticholinergic stack, SGLT2 + water pill, or 2+ sweat blockers |
| L3-defenses | 3 | 4+ body defenses weakened |
| L3-drug | 3 | Lithium or an antipsychotic |
| L2-defenses | 2 | 2–3 body defenses weakened |
| L2-core | 2 | One core defense: sweating, thermostat/heat production, fluid & salt, drug delivery (patch, insulin) |
| L1 | 1 | One other defense, or a medicine that is heat-sensitive to store |
| L0 | 0 | None |

Body defenses: sweating, skin blood flow, fluid & salt balance, blood pressure, kidneys, brain thermostat / heat production, alertness & thirst, blood sugar, drug delivery. Medicine storage is listed but not counted as a body defense. The triple whammy (Mangoni 2017, **null**) and 5+ medicines are shown but never raise the level. Evidence wording follows the KB's `combination_rules`. The unverified "~30% of hyponatremia admissions" figure is not shown.

### x-axis: personal heat exposure (`lib/patient/exposure.ts`), max 17 points
| Factor | Points | Factor | Points |
|---|---|---|---|
| No working AC | 3 | Can't reach a cool place / only with help | 2 / 1 |
| AC but cost limits use | 2 | Floor 7+ (assumption) | 1 |
| Outdoors / physical work all day | 2 | Floor 4+ walk-up (assumption) | 1 |
| Outdoor work or sports (if not above) | 1 | Home often gets hot | 1 |
| Home all day without reliable AC | 1 | Power-dependent equipment | 1 |
| Lives alone | 2 | Neighborhood HVI 5 / 4 | 2 / 1 |
| Lives alone and no one checks on them | 1 | Neighborhood ≥15% homes without AC (only if own AC answer missing) | 1 |

Bands: low 0–2, medium 3–5, high 6–8, very high 9+. The ZIP→sub-borough crosswalk for AC rates is approximate (flagged in the config).

### Personal readiness level (spec §9)
Matrix of medication level (rows 0–4) × exposure band (low / medium / high / very high):

| Med level | low | medium | high | very high |
|---|---|---|---|---|
| 0 | low | low | low | medium |
| 1 | low | low | medium | medium |
| 2 | low | medium | high | high |
| 3 | medium | high | high | very high |
| 4 | high | high | very high | very high |

Then one step up (at most) for age 75+, a child under 5, or dementia/schizophrenia in the record.

### Priority tiers (config `alert_rules`; gated on the forecast)
- **Call today:** very-high readiness at HeatRisk ≥2. Also high readiness at HeatRisk ≥3 when automation can't reach anyone in time: no contact close enough **and** (lives alone **or** not opted in).
- **Call before the heat wave:** the wave hasn't started (today below 2), HeatRisk ≥2 is forecast within 7 days, and readiness is high or very high.
- **Send heat card:** med level ≥2 or a storage-sensitive medicine. This is non-urgent education and not gated on the forecast.
- **Routine:** everyone else.
- **Auto safety alert:** HeatRisk ≥3, readiness high or very high, opted in.
- **Morning cooling text:** HeatRisk ≥2 and (no reliable AC or readiness high or very high).
- **Drill column** (`drillTier`): the tier the patient would get if today's HeatRisk were 3.

### Escalation (spec §4.4a; config `escalation`)
- T_max by readiness: very high 45, high 60, medium 90 (spec starting values), low 120 (assumption). It tightens to 45 at HeatRisk ≥3 or for a hot home with no AC.
- p90 response times are **assumptions pending extraction** from Pielot 2014/2018 and Mehrotra 2016: patient app/SMS 15 min, voice 20 min, contact 15 min (matches the routing agent), older-adult extra 0 (a knob).
- A contact is eligible when travel ≤ T_max − T_wait − T_contact. The fastest eligible contact is asked first.
- Steps: the alert is re-sent at T_wait/2. At T_wait the contact is asked, with a checklist. At T_wait + T_contact the next contact and the clinic list are alerted. At T_max **a human decides**; the system never calls 911 itself.
- Check-ins come from the questionnaire. Very-high readiness adds 14:00, 16:00 and 18:00 at HeatRisk ≥3. Worst case = longest waking gap (08:00–21:00) + T_max.

### Messages (`lib/patient/messages.ts`)
- **Blocks:** the KB `patient_messages` (`heat_forecast`) are used when the KB has the drug and the text doesn't name a different ingredient. Otherwise the provisional per-defense blocks follow the spec §4.5 template. KB Spanish is tagged "machine-translated, needs review".
- **Fluid rules, in order:**
  1. Clinician-set restriction: stay within your limit.
  2. Thiazide + SSRI: don't force down plain water.
  3. Heart failure, CKD or a loop diuretic: follow your fluid plan and ask.
  4. Everyone else: drink water regularly.
- **Audience:** a child gets parent wording; an adult whose answers came from a caregiver gets "the person you care for". English and Spanish only (config). Other languages fall back to English with `needsTranslation`.
- **Guardrail** (`checkMessageSafety`): every patient message must avoid "stop taking", dose numbers and dose talk, and must end with "Talk to your doctor or pharmacist." All 2,609 generated messages pass.

### Heat-wave probability (`lib/patient/forecast.ts`, NOAA only)
| Lead | Source |
|---|---|
| 0–7 days | HeatRisk level (not a probability); bar = level/4 |
| 6–14 days | CPC 6–10 / 8–14 day outlooks |
| Weeks 3–4 | CPC week 3–4 outlook |
| Up to 13 months | CPC monthly / seasonal outlooks |
| Otherwise | History only |

For the CPC rows, p = historical p(in heat wave) × CPC p(above normal) ÷ 33.3%, capped at 1. Outlooks issued after the as-of date are ignored. History is `cp_p_in_heatwave_smoothed15d`; a heat wave means ≥3 days at ≥90 °F at Central Park.

## Known limitations
- The provisional drug table is still used for drugs the KB doesn't cover yet. Re-running the script picks up KB updates.
- Response-time p90s and the floor and walk-up points are assumptions (marked as such in the config and code).
- Contact driving times are free-flow (optimistic), which is why we prefer the no-car times.
- Generic drug names appear in English inside Spanish messages unless a KB block supplies the Spanish name.
- HeatRisk is sampled for only 4 ZIPs; the other catchment ZIPs use a labeled proxy.
