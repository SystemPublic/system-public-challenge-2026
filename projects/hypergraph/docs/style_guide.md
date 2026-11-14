# Style guide for the NYC Concordance interface

This guide sets out how the interface in `viz/` should be organised, and then how it should look.
The organisation sections come first because they decide what a reader meets and in what order, so a redesign starts with them and settles colour later.

Sources: the organisation sections come from a review of the twelve pages in `viz/` and `viz/data/claims.json` on Nov 14. The visual sections adapt the design of two working personal-finance dashboards by Ida Benedetto. `docs/visual_language.md` still explains how the strip, the paired estimates and the explorer encode the data, and this guide does not repeat it.

Sections marked **(before 3 PM)** are the changes that would most improve what judges see. The rest can follow.

**Organisation:** [Readers](#1-readers) · [Site map](#2-site-map-before-3-pm) · [First screen](#3-first-screen-of-every-page-before-3-pm) · [Vocabulary](#4-vocabulary-before-3-pm) · [Research map](#5-the-research-map-as-a-destination-before-3-pm) · [Claim view](#6-one-claim-view) · [Depth](#7-layers-of-depth-and-page-labels) · [Page templates](#8-page-templates) · [Entry points](#9-entry-points-for-researchers-and-city-analysts)
**Visual design:** [Tokens](#10-tokens) · [Colour sets](#11-colour-set-options) · [Colour rules](#12-colour-rules) · [Chart forms](#13-chart-forms-for-this-content) · [Marks](#14-mark-specifications) · [Labels and numbers](#15-labels-annotation-and-numbers) · [Interaction](#16-interaction) · [Sources and versions](#17-sources-and-versions) · [Long text](#18-long-text) · [Slides](#19-slides-and-the-site) · [Phone and accessibility](#20-phone-width-and-accessibility) · [Avoid](#21-forms-to-avoid) · [Checklist](#22-checklist)

---

## Part one: organisation

## 1. Readers

Three readers, in the order they arrive.

| Reader | Arrives with | Should leave able to say |
|---|---|---|
| **Judge** (about two minutes, then a three-minute pitch) | The challenge text: confirmations, conflicts, bridges, a dashboard with sources, a map of research needed | How many claims were tested, what share the city data confirm or contest, one striking example of each, and that every claim cites its dataset versions |
| **Researcher** | A topic or a finding from the literature | Which findings New York's data support or contradict, and which study would settle an open question |
| **City analyst** | An agency, a neighbourhood or a policy lever | What the research and the city's own records say about their area, and how sure the answer is |

Design every page for the judge's first screen first. The researcher and the analyst reach their material one click deeper.

## 2. Site map (before 3 PM)

The menu now lists nine links of equal weight, labelled by the form of the page ("Strips", "Edges as objects"). The home page is fourth. `compare.html` and `inspections.html` are not in it.

Group the pages by what they give the reader. The main path follows the challenge's three required outputs.

### Main path

| Order | Menu label | File | Answers |
|---|---|---|---|
| 1 | **Findings** | `index.html` | What the research and the city's data confirm, contest and connect |
| 2 | **Sources and tests** | `evidence.html` | What each claim rests on, from registration to verdict |
| 3 | **Research needed** | new page, or an anchor in `index.html` | Which kinds of study would settle the most open claims |

### Case studies

| Menu label | File | Answers |
|---|---|---|
| Restaurant inspections | `inspections.html` | What makes a restaurant unsafe? |
| Heat and medicines | `heat_drugs.html` | What the graph holds and lacks on heat, medicines and chronic illness |
| City levers | `levers.html` | What the city could do, ranked on five separate components |
| Congestion toll simulator | `simulate.html` | How a different toll schedule might change traffic |

### Tools and method

| Menu label | File | Answers |
|---|---|---|
| Graph explorer | `explorer.html` | What the System graph links to a concept |
| Neighbourhood explorer | `explore.html` | What the city's records show for one neighbourhood |
| Links as objects | `hypergraph.html` | Everything known about each link, and how links relate |
| How a link changes | `comics.html` | How a link's evidence changes as new data arrive |
| Compare versions | `compare.html` | What changed between two versions of the claims |
| How it was built | `architecture.html` | How the pieces of the system fit together |

### Menu rules

- One menu, identical on every page, in the order above. The current page is marked.
- The three groups are visible in the menu: the main path as the first links, then "Case studies" and "Tools and method" as labelled groups or dropdowns.
- A menu label names what the reader gets. It never names the chart form.
- A page's `<title>`, its menu label and its first heading use the same words. Today `index.html` is "NYC Concordance Evidence" in the title and "Evidence dashboard" in the menu.

## 3. First screen of every page (before 3 PM)

Every page opens with its question, answer, counts and next step, in this order, before any chart:

1. **The page's question** as the heading.
2. **A one-line answer computed from the data.**
3. **The counts behind the answer.**
4. **One link to the next step.**

How to read the chart goes in a disclosure under the chart. It does not go in the opening paragraph.

`inspections.html` already opens with its question ("What makes a restaurant unsafe?") and then the answer. Use it as the model.

For `index.html` the first screen is:

- **Heading:** "What research and New York City's data confirm, contest and connect".
- **Answer:** one sentence with the counts, computed from `claims.json` at build time.
- **A tally of verdicts:** one block per verdict with its count, its colour and shape, and a link that filters the strip to those claims.
- **One example of each verdict:** the claim in plain words, with its verdict, in a single line.

Today the page opens with a paragraph explaining the −1 to +1 axis.

## 4. Vocabulary (before 3 PM)

### Claim type and verdict

Each claim has a **type**, set when it is registered, and a **verdict**, set when it is scored. The two lists use overlapping words.

| Claim type | Claims | | Verdict | Claims |
|---|---|---|---|---|
| confirmation | 68 | | confirmed | 37 |
| bridge | 16 | | contested | 19 |
| conflict | 8 | | unsettled | 36 |
| reproduction | 6 | | bridged | 1 |
| | | | no test | 4 |

Of the 16 bridge claims, one has the verdict "bridged". Nine are unsettled, three confirmed, two contested and one has no test.

**The team needs to decide which list the headline counts use.** The challenge asks for "confirmations, conflicts and bridges", which reads like the types. The verdicts say how each test came out. Two workable options:

- **Headline by verdict,** with the type as a filter. The first screen reports how the tests came out.
- **Headline by type, split by verdict:** for example "16 bridges tested: 1 holds, 3 confirmed in part, 9 unsettled". The first screen uses the challenge's words.

Whichever is chosen, a type word and a verdict word never appear in the same position. Where both show, the type sits in small capitals before the claim and the verdict sits in its coloured mark.

### Fixed terms

Define each term once, in a glossary page or disclosure, and use it the same way on every page.

- **Claim:** a statement registered before the city data were looked at, with its predicted direction and what would refute it.
- **Stance:** where the city's estimate falls between contradicting the research (−1) and agreeing with it (+1). Computed by `concord.claims.stance()`.
- **Confirmed, contested, unsettled, bridged, no test:** the five verdicts, defined as in `concord/claims.py`.
- **Link:** a relationship in the System graph between two concepts. Use "link" everywhere; drop "edge" in reader-facing text.
- **Dataset version:** the exact version a figure rests on (see [Sources and versions](#17-sources-and-versions)).

## 5. The research map as a destination (before 3 PM)

The challenge requires "a map of what research is needed". Today it is the third section of `index.html`, below the strip and the single-claim detail.

- Give it its own menu entry, either a page or an anchor that the menu jumps to.
- Open it with its answer: which kinds of study would settle the most claims, by count. The kinds come from `RKINDS` in `viz/index.html`: individual-level data, sensor or monitoring data, imagery, an instrument or natural experiment, a longitudinal design, a within-unit design, finer resolution, and linking datasets.
- Under the answer, the claims-by-kinds matrix as it is now. Each cell links to the claim.
- 96 of the 98 claims carry a `research_needed` entry, so the page can say so.

## 6. One claim view

A claim's details are now spread over three pages: "One claim" in `index.html`, the test card and lineage in `evidence.html`, and the link contents in `hypergraph.html`.

Define one claim view, reachable by URL (`#claim=<id>`) from every page that mentions a claim, with this fixed order:

1. **Type and verdict,** with the verdict's colour and shape.
2. **The claim in plain words.**
3. **What the research says:** the graph's estimate and its interval, with the studies it comes from.
4. **What the city data say:** the city's estimate and its interval.
5. **The two side by side** as paired estimates (see [Chart forms](#13-chart-forms-for-this-content)).
6. **What would settle it:** the `settle` statement and the research-needed entries.
7. **Sources and versions:** every dataset with its version and query.
8. **How it was tested:** registration date and hash, the referee's review, any city data fetched before registration.

A worked example from the repo, claim `heat-ac-heat-calls`, verdict contested:

- **Claim:** ambulance calls for heat illness rise more steeply with temperature in community districts where fewer households have air conditioning.
- **Research says:** about +0.112 on the difference in log rate ratios, derived from case-control studies of heat death with a working air conditioner (Naughton 2002, Semenza 1996).
- **City says:** −0.032, with a 95% interval from −0.088 to +0.024 (EMS calls, May to September, 2006–2026).
- **Why contested:** the city's interval excludes the +0.112 the research implies.
- **What would settle it:** heat illness by place of residence, from the Health Department's ZIP-level emergency-department data or EMS records with a location type.

## 7. Layers of depth and page labels

Each page has three layers. A reader reaches each deeper layer from the one above it, and no page shows a deeper layer first.

1. **Verdict:** the answer and the counts.
2. **Evidence:** the estimates, the charts and the claim views.
3. **Method:** how claims were registered, tested and refereed, with lineage and code.

Every page carries a label under its heading saying what kind of result it shows:

- **Tested claims:** registered before the data were looked at, then scored.
- **Descriptive:** what the data show, not tested against a prediction.
- **Simulation:** a model's output, with its assumptions.

`explore.html` and `simulate.html` already say this in their prose. Make it a standard label in a fixed place.

## 8. Page templates

| Template | Pages | Order on the page |
|---|---|---|
| **Overview** | Findings, Research needed | Question, answer, counts, tally or matrix, the main chart, the table of all items, notes |
| **Case study** | inspections, heat and medicines, levers, toll simulator | Question, answer, result label, the main figure, the claims it rests on (each linking to its claim view), method, sources |
| **Tool** | the two explorers, links as objects, compare | One line on what the tool shows, the controls in one row above the canvas, the canvas, a panel for the selected item, how to read it |
| **Method** | sources and tests, how a link changes, how it was built | Question, a diagram of the process, the steps in order, worked example, rules |

Lettered sections (A–D on `evidence.html` and `hypergraph.html`) become headings that name their content.

## 9. Entry points for researchers and city analysts

After the judge's path works:

- **By topic,** for researchers: each topic the claims cover (for example heat, transport, food safety, construction) opens the strip filtered to that topic.
- **By agency or lever,** for city analysts: the levers page and the strip filtered by the agency whose data the claim uses.
- **By gap:** the research map, filtered to one kind of study.

---

## Part two: visual design

## 10. Tokens

Define every colour, size and space as a CSS custom property on `:root` in `viz/style.css`, and redefine the colours for dark mode. Pages do not override the tokens in their own `<style>` blocks. Today eleven of the twelve pages carry their own `<style>`, and `explore.html` and `architecture.html` do not load `style.css`.

### Neutral colours

The verdict colours come from the chosen colour set (section 11). The neutrals below are the finance dashboards' values and pair with set A. Sets B, C and D carry their own surfaces in `docs/colour_sets.html`.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#eef1f4` | `#13171b` | page background |
| `--card` | `#ffffff` | `#1a2026` | panels and chart surfaces |
| `--card2` | `#f4f6f9` | `#20272e` | inputs, inset panels |
| `--ink` | `#171d24` | `#e8ecef` | primary text |
| `--muted` | `#5a6673` | `#a3aeb8` | secondary text |
| `--faint` | `#8a97a3` | `#76838f` | axis labels, notes |
| `--line` | `#e1e6eb` | `#2a323a` | borders, gridlines |
| `--line2` | `#cbd3db` | `#39434d` | stronger borders, the zero line |
| `--track` | `#e4e9ee` | `#2a323a` | empty part of a bar |
| `--accent` | `#0f9d8a` | `#27a893` | links and focus rings |
| `--warn` | `#b3413a` | `#e8837b` | one use: a provenance problem, such as data fetched before registration |

Declare the dark values twice: under `@media (prefers-color-scheme: dark)` guarded by `:root:not([data-theme="light"])`, and under `:root[data-theme="dark"]`, so a manual theme switch works.

### Type

- **Serif** (Spectral, falling back to Iowan Old Style and Georgia) for page titles, question headings and italic annotations on charts.
- **Sans** (Work Sans, falling back to the system UI font) for everything else.
- **Sizes:** 12 px for labels, 14 px for body text, 17 px for answers and lede text, 28 px for headline counts, 34 px for section questions, 42 px for page titles.
- **Chart text:** values 12 px weight 500 in ink, mark labels 11 px faint, axis labels 10.5 px faint.
- **Figures:** all use `font-variant-numeric: tabular-nums` so columns line up.

### Space

An 8-based scale: 8, 16, 28, 48 and 88 px. Sections are 88 px apart, panels 16 px apart, and a chart sits 28 px below its text. Content column at most 1080 px wide, with a 16 px side gutter on phones.

## 11. Colour set options

Four candidate sets are under trial, alongside the current Okabe-Ito set. `docs/colour_sets.html` draws each one on the same 22 real claims (concordance strip, verdict counts, stance scale and priority scale) in light and dark, with the palette validator's result under each panel. Open it in a browser to compare. Nothing changes in `viz/style.css` until one is chosen.

| Set | Confirmed | Contested | Bridged | Unsettled | Surface |
|---|---|---|---|---|---|
| A · blue, amber, teal | `#2e64a6` / `#4682cc` | `#c17924` / `#c87f2c` | `#0f9b89` / `#29a288` | `#b4bcc5` / `#59636e` | `#ffffff` / `#1a2026` |
| B · indigo, brick, ochre on warm paper | `#434d97` / `#6673c1` | `#b94834` / `#b2422e` | `#bd9625` / `#ae912c` | `#bdb5a6` / `#615b51` | `#fbf8f1` / `#211f1b` |
| C · blue, orange, magenta | `#194cb1` / `#2e62c9` | `#e8721c` / `#de7515` | `#cc4da9` / `#d050ad` | `#b3b5b8` / `#5c6066` | `#ffffff` / `#141618` |
| D · sea blue, red, olive | `#0074a5` / `#1292c0` | `#c74c3d` / `#b94739` | `#889a21` / `#89a01b` | `#b0bcc4` / `#55636e` | `#ffffff` / `#0f1419` |

Each cell gives the light value, then the dark value.

- **Scales:** the stance scale runs from contested through a neutral grey to confirmed. The priority scale is steps of the confirmed hue.
- **Validator results,** run on all pairs of the three hues:
  - A passes every check in both modes.
  - B's ochre is under 3:1 contrast against the paper.
  - C in dark and D in light have a worst colour-blind separation of ΔE 7.0, which the validator allows only with a second cue.
- **The second cue:** the strip gives one with fixed shapes and a written verdict. Confirmed is a circle, contested a square, unsettled a diamond, bridged a triangle and no test a hollow circle.

## 12. Colour rules

- **One role per colour.** The verdict colours mean the verdicts and nothing else. Links, buttons and focus rings use `--accent`. A provenance problem uses `--warn`.
- **Verdicts always carry their shape and name.** Colour is never the only cue.
- **Diverging scales have a grey middle.** The middle of the stance axis means "cannot tell", so it carries no hue.
- **Magnitude is one hue, light to dark.** Priority, counts in a matrix and finding counts on a link all use steps of one hue.
- **Graph link signs** use the confirmed hue for positive, the contested hue for negative and grey for mixed. A dashed light grey line means a link that was not sampled. The sign follows the variables as each study named them, so it is a reading aid, not an effect estimate (see `docs/visual_language.md`).
- **Highlights for change** (a link added or withdrawn in a comic frame) use one highlight colour outside the verdict set, plus a label ("added", "withdrawn").

## 13. Chart forms for this content

Pick the form from the question the figure answers.

| Question | Form | Pages |
|---|---|---|
| How did all the tests come out? | Verdict tally: one block per verdict with count, colour and shape | Findings |
| Where does each claim fall between contradiction and agreement, and how sure is it? | Concordance strip: one row per claim on a −1 to +1 axis, an interval bar, the verdict mark, the registrant's bet as a shaded band | Findings |
| Do the research and the city agree on size, not just direction? | Paired estimates: two rows (research, city), each a point and a 95% interval, with a line at no effect; ratios on a log axis | Claim view |
| How do several studies combine? | Forest plot: one row per study, a pooled row at the bottom, studies ordered by weight | Links as objects |
| What does the graph link to a concept? | Network: the concept at the centre, neighbours placed by number of findings, line width by the square root of findings | Graph explorer |
| How do two groups of things relate through one centre? | Radial diagram with the centre in the middle and the two groups on either side | Heat and medicines |
| How does a link change as evidence arrives? | Comic sequence: small multiples in a fixed grid, with the same layout in every frame and only the changes highlighted | How a link changes, compare versions |
| Where is evidence dense, and where is it missing? | Matrix: rows and columns of fixed order, cells shaded by count, empty cells drawn as outlines so absence is visible | Research needed, links as objects |
| Where in the city? | Choropleth map with a fixed sequential scale and a selected area outlined; aerial images beside the map at the same scale | Neighbourhood explorer, levers |
| What would a policy change do? | Simulator output: each outcome as a point with its 95% interval against the current schedule, with the inputs above in one row | Toll simulator |
| How do options rank on separate criteria? | Ranking table with one column per criterion, sortable, with no total column | City levers |
| What are the exact figures? | Table under every chart | All |

## 14. Mark specifications

- **Points:** 5–6 px radius with a 2 px ring in the surface colour, so overlapping marks stay separate.
- **Intervals:** 3 px bars with round ends. An interval that crosses the zero line is the visual sign of "not settled", so the zero line is the one strong vertical line (1.2 px, `--line2`).
- **Lines:** 2 px with round joins. Reference lines 1 px dashed.
- **Bars and blocks:** 2 px gap of surface colour between adjacent fills, 3–4 px corner radius.
- **Gridlines:** horizontal or vertical only as the axis needs, 1 px in `--line`. No chart borders.
- **Network nodes:** size by one measure only (findings), labels on the centre and the largest neighbours, the rest on hover.
- **Comic frames:** identical size and node positions in every frame, a frame number and date above each, and at most two highlighted changes per frame.
- **Matrix cells:** square, with the count written in the cell when it is 1 or more.

## 15. Labels, annotation and numbers

- **Label marks directly.** A legend appears only where direct labels cannot fit, and then sits above the chart.
- **Write labels as plain words naming the thing:** "city data contradict the research", "agree". Not variable names such as `city_effect`.
- **Annotations are italic serif sentences,** 13.5 px, with a stroke in the surface colour behind them so they stay readable over marks.
- **Captions say what the chart shows in one or two sentences,** with the key figures in bold. They add what the chart cannot show; they do not narrate what the reader can see.
- **Numbers:**
  - Give an estimate with its interval: "−0.032 (95% interval −0.088 to +0.024)".
  - Use a true minus sign (−) and en dashes for ranges.
  - Say what a ratio or share is of.
  - Round to the precision the interval supports.
- **Counts that appear twice come from one source.** Verdict counts, claim totals and research-needed counts are computed from `claims.json` at build time and never typed into prose.

## 16. Interaction

- **Hover:** every chart mark has a tooltip naming the claim, its verdict and its estimate. On line charts a crosshair snaps to the nearest point.
- **Selection:** clicking a claim anywhere opens its claim view. The selected claim stays highlighted in every chart on the page.
- **Filters:** one row of controls above the charts they affect: verdict, type, topic, agency. A filter never repaints the remaining marks with new colours.
- **Disclosures** (`<details>`) hold how-to-read text, long tables and method detail. A disclosure's label says what it holds.
- **What-if inputs** belong only on the toll simulator. Changed inputs turn the field amber, a note says nothing is saved, and a button returns to the stored schedule.
- **Redraw on resize,** debounced by about 120 ms, since charts size themselves to their container.

## 17. Sources and versions

Here a source means the exact dataset version a figure rests on.

- **Every figure** has a short source line under it: dataset name and version.
- **Version fields:** `rows_updated_at` for NYC Open Data, `Last-Modified` for NOAA, the Dataverse version for the System graph.
- **An ƒ button** on the source line opens the full record: publisher, version, the exact query, the fetch time and the file hash.
- **Graph findings** link to PubMed or the DOI.
- **The registration hash** and whether the outcome cites it appear in the claim view's "How it was tested" section.
- **A provenance problem** (city data fetched before registration, a hash mismatch) shows in `--warn` with a written reason, in the claim view and as a marker on the claim's row in the strip.

## 18. Long text

- **Line length:** at most about 72 characters (`max-width: 72ch`) for any paragraph.
- **Headings:** name their content as a noun phrase or a question the section answers. No letters (A–D) or numbers alone.
- **Lists of claims:** one line per claim with its verdict mark first and the claim in plain words; the id in small grey monospace after it.
- **Write-ups:** an opening summary of three to five lines at the top of any page longer than two screens.

## 19. Slides and the site

The decks (`deck/`, `deck2/`) have their own stylesheet with Source Serif 4 and IBM Plex Sans. The site uses the fonts in section 10.

- **Shared parts:** the slides and the site use the same verdict colours, shapes, vocabulary and headline counts.
- **Charts on slides** are the site's charts at slide size, with larger labels (at least 18 px) and fewer rows. They are not redrawn in another style.
- **One idea per slide:** the claim, its verdict and the one figure that shows it.
- **Fonts:** either the site moves to the decks' fonts or the decks move to the site's. Pick one pair.

## 20. Phone width and accessibility

- Every chart reads its width from its container. No horizontal scrolling at 360 px.
- On phones the strip shows the claim's short name above its row instead of beside it, and the menu collapses to the three groups.
- Text contrast on white: ink 17:1 and muted 5.9:1 pass the 4.5:1 standard for small text. Faint (3.0:1) is for chart labels that repeat information available elsewhere.
- Controls show a 2 px focus outline in `--accent`.
- Small marks carry `<title>` text. Every chart has a table view.

## 21. Forms to avoid

- A blended score that combines verdicts into one number.
- Dual axes.
- Rainbow scales, or a hue at the middle of a diverging scale.
- Legends far from the data when direct labels fit.
- Node-link diagrams where a matrix would show the same relationships more legibly (more than about 30 nodes with labels).
- How-to-read paragraphs above the first chart.

## 22. Checklist

1. The page is in the site map, with the same name in its title, menu label and heading.
2. The first screen shows the question, a computed answer, the counts and one next step.
3. The page carries its result label: tested claims, descriptive or simulation.
4. Claim types and verdicts are never confused, and the headline uses the agreed list.
5. Every claim mention links to its claim view.
6. Each figure has a source line with the dataset version and an ƒ record.
7. Colours come from the chosen set, and every verdict also has its shape and name.
8. The page loads `style.css` and does not override its tokens.
9. The page works at 360 px and in dark mode.
10. Every chart has a table view.
