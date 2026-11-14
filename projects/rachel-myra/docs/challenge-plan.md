# Visualize Challenge 3 plan: heat-sensitive medications

System Public Challenge, NYC, 13–14 Nov 2026. Challenge owner: Chethan Sarabu, MD (Cornell Tech).

## What the challenge asks

Build one visual evidence map that a clinician, pharmacist or public-health official could use to plan heat-wave counseling. For each medication, show:

1. **The action:** dose adjustment, hold or substitute, closer monitoring, or storage and stability
2. **Evidence strength**, taken from the System Public Graph
3. **Prescribers involved:** primary care, psychiatry, cardiology, endocrinology, nephrology, pediatrics and others
4. **Guidance gaps:** where global heat-health guidance is missing, or doesn't match the evidence

Optional extensions: wearables evidence, and NYC heat × prescriptions overlap.

## Why this track

- Visualize is judged on clarity and polish, which suits a two-person team better than Build does.
- The spec is concrete: the four buckets give a ready-made structure.
- The optional NYC extension gives the project a local hook.
- Risk: graph coverage of drug × heat findings may be thin. Check that in the first hour. If it is thin, present the thinness as a finding.

## Planned views

1. **Evidence map:** medications (rows) × action buckets (columns). Cells are shaded by evidence strength and tagged with prescriber specialties. Clicking a cell shows its source findings.
2. **Evidence vs. guidance quadrant (the key view):**
   - x-axis: evidence strength
   - y-axis: guidance coverage (how many of the 8 guidance sources address the harm)
   - marker size: severity
   - hollow markers: null findings
3. **Specialty checklists:** filter by specialty to get a one-screen checklist to work through before a heat wave.
4. **Optional NYC map:** CMS Medicare Part D Prescribers (drug claims by zip) overlaid on the NYC Heat Vulnerability Index. Note: Part D covers people aged 65 and over only.

## Data

- `data/Drug heat risk master list.csv` is the main input. It has 86 rows covering basic and rare risks, and a `Guidance coverage` column.
- System Public Graph: query drug names and classes × heat outcomes (heat illness, hyperthermia, hospitalization, AKI, mortality).
- Guidance documents reviewed: CDC, NYC DOHMH, UKHSA, Health Canada, ANSM, WHO Europe, Victoria, Germany. See the `Guidance` tab of the spreadsheet.

## Weekend schedule

| When | Data | Design |
|---|---|---|
| First 2 hours | Coverage check: query the graph for ~15 drugs × heat outcomes | Sketch views; choose a style |
| Saturday | Pull findings; score evidence; finalize guidance coding | Build views 1–2 with real data |
| Saturday night | Join Part D data with the Heat Vulnerability Index (if on track) | View 3; click-through to findings |
| Sunday morning | Accuracy pass: check every cell against its source | Polish; write the narrative |
| Before judging | Rehearse the demo twice | |

## Pitch (~3 min)

1. Open with a patient: a 78-year-old in the Bronx on furosemide and oxybutynin, with no AC, during a heat wave.
2. Evidence map: what the research says.
3. Quadrant: where guidance lags the evidence. Examples: fentanyl patches, SGLT2 inhibitors, topiramate in adults.
4. Specialty checklist: what her doctor could do on Monday.
5. NYC map: where outreach should go.
6. Close on the gaps: wearables were never validated in medicated patients, and controlled trials studied mostly young, healthy men.

## Pitfalls

- Frame recommendations as "considerations for prescribers," never as medical advice.
- Label study design. Most evidence is observational and confounded by indication.
- Cover about 15 drugs done accurately, not 40 done loosely.
- Don't put unverified citations on public slides. The spreadsheet has a `Citation status` column to filter on.
