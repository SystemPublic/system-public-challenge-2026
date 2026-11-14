UI feedback from Rachel (Sat 14 Nov, ~1:45 PM). Full notes are in `spec.md` under "Rachel's UI feedback". Pull first. Some of this is already in the code, so finish what's left and make it look good, and don't rebuild what works. Check each page in the browser at desktop and phone width (375 px) after each step.

ALREADY DONE (keep, polish if needed)
- Name is "Cool-Aid" in the header, in our blue. Check that no "The Missing Label" text is left anywhere a user sees it (page titles, home page, CDS Hooks card labels, Disclaimer).
- Medicines page: the diagram is on top; the list is below; Sources are in a dropdown at the bottom. "Label warns?" and "Guidance says what to do?" show as colored chips.
- The diagram (`HeatMedicinePicture.tsx`) has a color per body effect and medicine names in pill chips.
- The patient medicine cabinet (`web/src/components/cabinet/MedicineCabinet.tsx`) exists and is on `/phone/[id]`.

1. MEDICINES TAB (clinician): simpler, fewer words, more color
   - Make the "how heat and medicine add up" diagram the hero: full width, clean, pretty, and easy to hover. Keep it clinician-only. At most one short line of help text; move the rest into the "Why?" panel or a dropdown.
   - Turn each medicine group in the list into a **dropdown** (`<details>`, first one open) with a colored group header. `MedicineList.tsx` lost its dropdowns in the merge, so add them back.
   - Give the evidence indicator color: show Strong / Some / Early signs as 3 dots filled in orange (`hold` colors), not a gray chip.
   - Cut wording everywhere on the page: short titles, short column headers, no paragraphs.

2. PATIENT APP (`/phone/[id]` and the patient side): visual, not words
   - The medicine cabinet is the main visual for "what can my medicines do in the heat."
     - Bottles sit on a shelf, with colored stems from each bottle to the body effects.
     - Hovering or tapping a bottle shows the bad things it can cause.
     - Several bottles can be selected at once, to see the combined effects ("Adds up ×N" where they overlap).
     - Make sure it looks good and works on a phone: bottles, stems and effect boxes are readable and the stems line up.
   - Cut words on the patient page hard: one-line headings, a short risk line, and everything else in **dropdowns** (`<details>`). Keep visible: risk today, the safest-hours strip, where to go (map), the cabinet, and "Talk to your doctor or pharmacist."
   - Make sure no network/graph diagram appears anywhere on the patient side.

RULES: no invented data (every label comes from the data files); no dose advice; keep the palette (Okabe–Ito: High = orange #d55e00, Medium = yellow #f0c419, Low = blue #0072b2; the chip style in `web/src/styles/tokens.css`); light mode. Commit after each step; don't push. When done, report what changed and anything left undone.
