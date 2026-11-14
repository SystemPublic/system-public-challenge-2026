LEARN.md

Spec for the Learn tab. Owned by the technical/design lead. Science facts come from SCIENCE.md. Data shapes from CONTRACT.md.

What Learn is for

A judge or a non-specialist lands here first and must leave able to say: this mutation, in this parasite, affects this drug, and that matters because of this. One screen, under ninety seconds of reading.

It is not a textbook page. Everything that doesn't serve that sentence is cut.

Page structure

Five blocks, in order. Nothing else.

1. Identity strip

One line, scannable, no prose.

Plasmodium falciparum · {gene} · {alteration} · affects {drug}

Plus a classification chip only if the science lead has a sourced classification to put in it, with the source named on the chip. If there is no sourced classification, omit the chip entirely. Never invent a status.

2. The one-sentence answer

A single bolded sentence, large type, directly under identity. This is the thing a judge remembers.

Parasites carrying {alteration} in {gene} are associated with reduced efficacy of {drug}.

Written by the science lead, reviewed before it ships. Hedge word included — "associated with," not "cause."

3. The diagram

The original visual. See the diagram spec below.

4. Plain-language mechanism

Three short paragraphs maximum, roughly 150 words total.

What the gene normally does.
What the mutation changes.
Why that blunts the drug.

No jargon that isn't defined inline. If a term needs defining, define it in the same sentence rather than a glossary.

5. Limits and actions

Two short lists side by side.

What this doesn't tell you — three bullets, drawn from the "May not" list in SCIENCE.md. At minimum: presence of a marker is not treatment failure for an individual patient; absence of evidence is not evidence of absence; this is not clinical guidance.

Actions — two buttons, both carrying the shared selection:

See where it's been observed → Forecast tab (Benjamin's map)
Watch this marker → Alert tab (David's), with the marker pre-filled

These two buttons are the reason Learn exists in a three-tab product. They are the connective tissue the pitch depends on. Build them before the prose.

Diagram spec

One original SVG. Hand-authored geometry, not generated from data.

If the demo marker is dhfr or dhps, draw the accumulation ladder: rungs for each alteration in the order SCIENCE.md gives, each rung labelled with its effect on the drug. Earlier rungs sit lower. A short caption states that combinations are properties of individual parasites, not of regions.

If the demo marker is pfcrt, pfmdr1 or kelch13, draw a before/after pair: drug acting normally on the left, drug blunted by the alteration on the right, with the changed protein element highlighted in both.

Requirements either way:

Original work. No traced figures, no reused diagrams from papers.
Reviewed by the science lead before it ships. Nothing unreviewed goes on screen.
Readable at a glance from three metres — a judge will see this projected.
Labels are real text, not paths, so they're selectable and accessible.
Colour is never the only encoding. Pair it with position, shape or label.
Any animation respects prefers-reduced-motion and has a visible pause. A static version must be fully legible on its own.

Scroll-driven sequences are a stretch. A static diagram that is correct and clear beats an animated one that isn't finished.

States
State	Render
Content complete and reviewed	the full page
Marker exists, visual not ready	identity + one-sentence answer + "Visual explanation coming", plus the action buttons. Never a blank panel
Science lead has not reviewed	do not ship. Hold the section rather than showing unreviewed claims
Shared state

Learn reads and writes the same object as the other tabs:

json
{ "markerId": null, "timeRange": null, "selectedFindingId": null }

Learn sets markerId. It never sets selectedFindingId. Moving to Forecast or Alert must not require re-selecting anything.

Copy rules
"Associated with", never "causes".
"Partial resistance" for artemisinin. Not "resistance".
Name the drug every time the marker is named. A marker without its drug context is meaningless and the plan's boundaries require them kept distinct.
No WHO endorsement, integration or operational framing.
No prevalence figures on this page. The graph does not hold them.
No geographic claims on this page. Forecast owns the map, and its location data comes from a separate source, not the System graph. Learn links to Forecast rather than restating anything about where the marker has been seen.
Relationship to the other tabs

Learn is the entry point. Home funnels into it; it funnels into Forecast and Alert. Those two buttons are the connective tissue the pitch depends on — build them before any prose.

Forecast and Alert are owned by Benjamin and David. Create their routes as trivial placeholders that read useSelection() and nothing more. Never build their contents; they overwrite these pages wholesale.

Build order
Shell and tab navigation with shared state. This unblocks the other two.
Action buttons wired to Forecast and Alert.
Identity strip and one-sentence answer with placeholder text.
Limits list.
Mechanism paragraphs, once the science lead supplies them.
Diagram.
Animation, only if everything else is done.

Steps 1 and 2 are due by 10:30. Everything after is yours alone and blocks nobody, so it can absorb the day's delays.

Content to fill at kickoff
marker:            TBD
gene:              TBD
alteration:        TBD
drug:              TBD
one-sentence:      TBD   (science lead writes, you typeset)
mechanism para 1:  TBD
mechanism para 2:  TBD
mechanism para 3:  TBD
diagram type:      ladder | before-after