# Style guide for dashboards and charts

This guide sets out the visual and data-display rules taken from two working personal-finance dashboards Ida Benedetto built: a one-page reading of the current position (the "Glance") and an interactive retirement projection (the "projection page").
Both are hand-written HTML with inline SVG and no chart library.
The rules below record the decisions those pages make and the values they use, so another page can reproduce the same look and the same way of reading. Example figures in quotation marks are illustrative, not taken from the finance data.

Where this repository already fixes an encoding, that encoding stands.
The verdict colours and mark shapes in `docs/visual_language.md` (Okabe-Ito blue, vermillion and bluish green, with grey for "unsettled") are one such case; this guide covers everything around them.

Contents: [Principles](#principles) · [Page structure](#page-structure) · [Tokens](#tokens) · [Colour set options](#colour-set-options-for-the-verdicts) · [Colour rules](#colour-rules) · [Choosing a chart form](#choosing-a-chart-form) · [Mark specifications](#mark-specifications) · [Labels and annotation](#labels-and-annotation) · [Numbers](#numbers) · [Interaction](#interaction) · [Provenance and age of data](#provenance-and-age-of-data) · [Phone width](#phone-width) · [Accessibility](#accessibility) · [Forms the dashboards avoid](#forms-the-dashboards-avoid) · [Checklist before publishing](#checklist-before-publishing)

## Principles

1. **A question heads every section, and the figures under it answer that question.** The Glance has three: "Am I safe right now?", "Am I making progress?", "How am I doing this month?". Each question carries a one-line written answer computed from the data, followed by the cards that support it.
2. **The page shows numbers, never a blended score.** A composite 0–100 index hides its arithmetic. The dashboards show each measure separately, and every number can open its formula.
3. **Every figure sits against a named reference.** A bare number gives the reader nothing to compare it with. The Glance draws months of cash runway against a floor, an action line and a target, and a balance against a floor line and a comfortable band.
4. **Label the marks directly.** A value, threshold or band carries its own text beside it. A separate legend appears only where direct labels cannot fit.
5. **The page states how old each number is.** Age is computed when the page is viewed, from the `as_of` date, so a number from last spring cannot pass as current.
6. **A reading surface stays separate from a scenario tool.** The Glance reads a settled position. Changing assumptions belongs on the projection page. Where the Glance allows a what-if, nothing is saved, and the page says so.
7. **Keep the register calm.** No red-for-down, no flashing, no celebration. A fall is shown in amber.

## Page structure

### Order on the page

1. **Header:** a serif title, then a lede paragraph naming every source and the date each was read ("Figures from the budget ledger, reconciled Nov 3; the net-worth snapshot of Oct 1 …").
2. **Question sections:** each a collapsible `<details>` element that starts open. The summary row holds a faint serif number (1, 2, 3), the question as the heading, the written answer under it, and a small "Hide / Show the figures" toggle.
3. **Cards** inside each section. One card holds one measure.
4. **Notes** at the foot of the page in small faint text, covering what the model leaves out and how the figures relate across pages.

### Anatomy of a card

Top to bottom:

- **Name:** small capitals (12 px, weight 500, letter-spacing 0.06em, uppercase, muted colour). A pill beside it names the tool the figure comes from, or a state chip ("stale", "unsaved what-if").
- **Headline number:** 28 px, weight 300, with the unit in 14 px muted text after it ("14 months").
- **Count line:** one or two sentences in 14 px muted text saying what went into the number ("$50,000 of cash after the tax set-aside, at $3,500/mo of spending").
- **Graphic,** 28 px below the count line.
- **Figure tiles** where the card has several sub-figures: a grid of small boxes, each with a label above and a value below.
- **Meta line:** a thin rule, then the read date, the refresh cadence, the source name and a small italic ƒ button that opens the source, formula, cadence and `as_of` date.

### Layout

- Content column at most 960 px wide, centred, with a 16 px side gutter on phones and 28 px from 700 px up.
- Three equal cards in a row from 760 px up; one column below that.
- A card with assumptions uses a two-column split from 860 px up (chart and figures on the left at 2.2 parts, an "Assumed here" aside on the right of at least 220 px). Below 860 px the aside moves under the chart, divided by a top rule.
- Cards: white surface, 1 px border, 18 px corner radius, 28 px padding, and a soft two-layer shadow.

## Tokens

Define every colour, size and space as a CSS custom property on `:root`, and redefine the colours for dark mode. The values below are the ones both finance pages use.

### Colour, light mode

| Token | Value | Use |
|---|---|---|
| `--bg` | `#eef1f4` | page background |
| `--card` | `#ffffff` | card surface |
| `--card2` | `#f4f6f9` | inputs, inset panels |
| `--tile` | `#f7f9fb` | figure tiles |
| `--ink` | `#171d24` | primary text, threshold markers |
| `--muted` | `#5a6673` | secondary text, count lines |
| `--faint` | `#8a97a3` | axis labels, notes |
| `--line` | `#e1e6eb` | borders, gridlines |
| `--line2` | `#cbd3db` | stronger borders, minor ticks |
| `--track` | `#e4e9ee` | the empty part of a bar |
| `--teal` | `#0f9d8a` | the measured value; links |
| `--blue` | `#3a6ea5` | targets, bands, reference lines |
| `--amber` | `#b4752c` | down, behind, stale, what-if |
| `--green` | `#2c8d59` | up (direction pill only) |
| `--red` | `#b3413a` | one warning: a threshold crossed that calls for action |

Each accent also has a pale `-soft` background for chips (for example `--amber-soft: #f6ead8`).

### Colour, dark mode

Dark mode lightens each accent rather than inverting it: `--bg #13171b`, `--card #1a2026`, `--ink #e8ecef`, `--muted #a3aeb8`, `--faint #76838f`, `--line #2a323a`, `--teal #27a893`, `--blue #4f8ad6`, `--amber #d9a35f`, `--green #5fc08a`, `--red #e8837b`.
Declare the dark values twice: under `@media (prefers-color-scheme: dark)` guarded by `:root:not([data-theme="light"])`, and under `:root[data-theme="dark"]`, so a manual theme switch works.
In dark mode only, the value marks get a soft glow (`drop-shadow(0 0 5px)` in the accent at 50–55% opacity). In light mode the glow token is transparent.

### Type

- **Serif** (Spectral, falling back to Iowan Old Style and Georgia): page title, question headings, the asides' titles, and annotations on charts, in italic.
- **Sans** (Work Sans, falling back to the system UI font): everything else.
- Sizes: 12 px (labels, meta), 14 px (body, count lines), 17 px (lede, answers, tile values), 28 px (headline numbers), 34 px (question headings), 42 px (page title).
- Chart text: value labels 12 px weight 500 in ink; mark labels 11 px faint; axis labels 10.5 px faint; text inside a filled bar 11 px weight 600 in white.
- All figures use `font-variant-numeric: tabular-nums` (lining numerals of equal width) so columns of numbers line up.

### Space

An 8-based scale: 8, 16, 28, 48 and 88 px. Sections are 88 px apart; cards 16 px apart; a card's graphic sits 28 px below its text.

## Colour set options for the verdicts

Four candidate sets are under trial, alongside the current Okabe-Ito set. `docs/colour_sets.html` draws each one on the same 22 real claims (concordance strip, verdict counts, stance scale and priority scale) in light and dark, with the validator's result under each panel. Nothing changes in `viz/style.css` until one is chosen.

| Set | Confirmed | Contested | Bridged | Unsettled | Surface |
|---|---|---|---|---|---|
| A · blue, amber, teal | `#2e64a6` / `#4682cc` | `#c17924` / `#c87f2c` | `#0f9b89` / `#29a288` | `#b4bcc5` / `#59636e` | `#ffffff` / `#1a2026` |
| B · indigo, brick, ochre on warm paper | `#434d97` / `#6673c1` | `#b94834` / `#b2422e` | `#bd9625` / `#ae912c` | `#bdb5a6` / `#615b51` | `#fbf8f1` / `#211f1b` |
| C · blue, orange, magenta | `#194cb1` / `#2e62c9` | `#e8721c` / `#de7515` | `#cc4da9` / `#d050ad` | `#b3b5b8` / `#5c6066` | `#ffffff` / `#141618` |
| D · sea blue, red, olive | `#0074a5` / `#1292c0` | `#c74c3d` / `#b94739` | `#889a21` / `#89a01b` | `#b0bcc4` / `#55636e` | `#ffffff` / `#0f1419` |

Each cell gives the light value, then the dark value. The stance scale runs from contested through a neutral grey to confirmed, and the priority scale is steps of the confirmed hue. Validator results, run on all pairs of the three hues: A passes every check in both modes; B's ochre is under 3:1 contrast against the paper; C in dark and D in light have a worst colour-blind separation of ΔE 7.0, which the validator allows only with a second cue. The strip supplies that cue with fixed shapes (confirmed circle, contested square, unsettled diamond, bridged triangle, no test hollow circle) and a written verdict.

## Colour rules

- **One role per colour.** Teal is the measured value (what you have now). Blue is a target, threshold band or reference line (what you are measuring against). Ink marks a hard threshold. Amber means attention: down, behind, stale, or a figure the reader changed. A colour never switches roles between cards.
- **Down is amber, never red.** Red appears once on the Glance, when runway falls to the line that calls for cutting costs. Red-for-down on a short-horizon change is the trading-app pattern these pages were designed against.
- **Show grades of one thing as steps of one hue.** The unit chart shows three spending levels as blue at 100%, 62% and 34% opacity, with the empty track for the rest. A comfortable range is a translucent blue band (fill opacity 0.16–0.24) edged with 1.5 px blue lines.
- **Separate categories by hue only when the categories differ in kind.** Verdicts in this repository are an example, and `docs/visual_language.md` sets those colours.
- **Colour never carries meaning alone.** Every coloured mark also has a label, a shape, a position or written text.
- **Fills may use a gentle horizontal gradient** from 50% to 100% opacity of the accent, so a bar reads as growing toward its end. Areas under a line fade vertically from about 40% opacity to nothing.

## Choosing a chart form

Pick the form from the question the figure answers.

| Question | Form | Example on the finance pages |
|---|---|---|
| Where does one value stand against thresholds? | Track with markers (a horizontal bullet graph) | Months of runway against a floor, an action line and a target |
| Is a value ahead of or behind a target, and by how much? | Position bar with a marker, a band and a gap bracket | Retirement balance against the floor line and the comfortable band |
| Which named zone has the value reached? | Zone scale: adjacent segments with the value as a dot | Income this year against five named income levels |
| How did a value change between two readings? | Two-point slope | Net worth, previous snapshot to this one |
| How many out of 100? | Unit chart: a 10 × 10 grid of squares | Simulated markets in which the money lasts |
| How do two quantities move over time, and where do they cross? | Line chart with a band and end labels | Balance against a rising target line, year by year |
| What are the exact figures behind a chart? | Table under the chart | Year-by-year balance, floor line and band |

Make every chart answer one question, and say which in the card name or the heading.

## Mark specifications

### Track with markers

- A rounded track 14–16 px tall (4–5 px radius) in `--track`, with the value as a teal fill clipped to the track.
- Thresholds are vertical lines extending 5–6 px past the track: the ones that matter in 1.5 px ink, minor ticks in 1 px `--line2`.
- Each threshold is labelled under the track with its value (12 px ink) and its name on a second line (11 px faint): "12 mo" over "action line".
- The current value gets a 5 px dot at the end of the fill (with a 2 px ring in the card colour, so it separates from the fill) and an italic serif annotation above it: "14.2 months of runway".
- The scale maximum is labelled at the right end. A value past the maximum pins to the end; the headline number gives the true figure.

### Position bar

- As the track, plus a translucent blue band for a range and a 1.5 px ink line for the main target.
- The value's own label sits inside the fill in white when it fits with 16 px to spare, and outside the fill in ink when it does not.
- Labels above the track carry the target and the band: value on the first line, name on the second. When the two would overlap, the band label moves right of the target label; on narrow screens it is dropped if it still collides.
- The difference between value and target is a bracket under the track (a 6 px-deep open rectangle in muted grey) with an italic annotation: "$40K past the floor line" or "$10K to the floor line".

### Zone scale

- Adjacent segments with a 2 px gap between them, all blue: 16% fill opacity for ordinary zones, 42% with a blue outline for the goal zone.
- Each zone is labelled under its segment with its name and its upper value; the goal zone's label is in ink and reads "<name> · goal".
- The value is a teal dot with an annotation above. A pace marker (where the value should be by today to reach the goal) is a dashed faint line with a small label.
- Below 520 px wide, alternate zone labels drop to a second row so they do not collide.

### Two-point slope

- A 2 px teal line between two 4 px dots, over a teal area fading downward.
- The dates sit under the ends (11 px faint); the values sit next to the dots (12 px ink), above the higher dot and below the lower.
- Pair the slope with a direction pill: ▲ or ▼, the signed change and the comparison date ("▲ +$5,000 since Apr 1"). Up is green on a green-soft pill, down amber on amber-soft, no change grey.
- With no previous reading, show the value alone, with no pill and no flat placeholder.

### Unit chart

- 100 squares, 13 px each with 3 px gaps and 2.5 px corners, filled left to right and top to bottom.
- Graded fills of one hue, as in the colour rules. Each square has a tooltip naming its meaning ("market 72 of 100: lasts at the lowest spending level only").
- A key beside the grid reads as rows: swatch, count, sentence ("**60** of every 100 markets: the money lasts at every spending level").

### Line chart

- 320 px tall on desktop, 250 px on phones. Margins: 18 px top, 30 px bottom, 46 px left; the right margin widens to 178 px when end labels are drawn.
- Horizontal gridlines only, 1 px in `--line`, at round steps chosen from the data range (100K, 250K, 500K or 1M). No vertical gridlines and no chart border.
- Axis labels in 10.5 px faint. The x axis is labelled every 5 units, and the last tick names its unit ("age 65").
- The measured series is a 2 px teal line with round joins, over a fading teal area. A reference series is a 2 px blue line. A range is a blue band at 18% opacity edged with 1 px dashed blue lines.
- **End labels replace the legend:** each series is named at its right end with a short coloured stroke, its name and its last value ("floor target $1.5M"). Labels closer than 15 px are pushed apart.
- Events are marked in place: a dashed ink vertical line with an italic annotation ("saving can stop at 55"), an ink dot where two lines cross, and a bracket at the right edge showing the final gap.
- Observed data points (as opposed to projections) are teal dots with a ring in the card colour.

### Tables

- 12 px text, tabular numerals, right-aligned numbers with the first column left-aligned, 1 px row rules, headers in muted weight 500 with no rule above.
- Put the table under its chart (inside a disclosure if it is long), so every plotted point has its exact figure.

## Labels and annotation

- **Write labels as plain words naming the thing:** "floor line", "comfortable", "past the floor line". Avoid internal variable names and abbreviations the reader would have to decode.
- **Annotations are sentences in italic serif,** 13.5 px, with a 5 px stroke in the card colour behind the text so it stays readable over lines and fills.
- **Clamp labels to the drawing.** A label that would run off either edge switches its anchor to start or end at a 2 px inset.
- **Captions under charts say what the chart shows in one or two sentences, with the key figures in bold:** "From **$300,000** now, with no more saving, growing 5% after inflation. The balance crosses the floor line at **55**."
- **Every answer line names its comparison:** "14 months of runway at $3,500/mo, short of the 24-month target."

## Numbers

- Round money to whole dollars in text ($50,000). In chart labels use thousands ($50K) below a million and two decimals of millions ($1.25M) above.
- Use an en dash for ranges with no spaces ("$80,000–$100,000/yr"), and a true minus sign (−) for negatives.
- Give rates their unit and period: "/mo", "/yr", "% after inflation".
- Say what a percentage is a share of. "60% at the floor" is followed by "the money lasts in 60 of every 100 simulated markets at $5,000/mo".
- Compute derived figures in one shared script that every page loads, so two pages can never show two versions of the same number. The finance pages share one script for the formula and one for the drawing code.

## Interaction

- **Hover on line charts:** a faint vertical crosshair follows the pointer and snaps to the nearest data point. A dark tooltip (ink background, white 12 px text, 8 px radius, tabular numerals) shows the x value in bold and each series' value on its own line. The tooltip flips to the left of the crosshair near the right edge. Touch-move works the same way.
- **What-if inputs:** numeric fields format with thousands separators as the reader types. A changed field turns amber, a chip on the card reads "unsaved what-if", a note counts the changed fields ("2 figures changed from the stored values. Nothing is saved; reloading the page restores them."), and a dark button returns to the stored figures. A direction pill hides while any field holds a what-if.
- **Steppers and segment buttons** for bounded inputs: number fields keep their − and + buttons visible, and a choice among a few values uses a segmented control whose selected segment is filled in ink.
- **Disclosures** (`<details>`) hold secondary material: what-if inputs, long tables, extra rows. A disclosure's label says what it holds: "Try other figures for cash and monthly spending (nothing is saved)".
- Redraw charts on window resize, debounced by about 120 ms, since every chart sizes itself to its container.

## Provenance and age of data

- **Every card ends in a meta line:** "read Nov 3, 11 days ago · next refresh in 20 d · budget ledger · ƒ".
- **The ƒ button opens a panel** with the full source, the formula with the actual numbers substituted, the cadence, and the `as_of` date. A reader can check any figure without leaving the page.
- **Each figure has a cadence** (monthly, semiannual, annual, or "on re-run" for figures that hold until a model is run again). The age is compared with the cadence when the page is viewed.
- **A stale figure** shows its age in amber at the front of the meta line ("200 days old · past its semiannual refresh"), gets an amber "stale" chip by its name, and dims its number to 45% opacity. Staleness has one stage; the day count tells how stale.
- **A figure with no data yet** looks different from a stale one: a dashed border and no number, rather than a dimmed number.
- **A process that keeps data current shows a status lamp:** an 8 px dot, green when its last run is recent and amber when it is late, with one line of text.
- **The lede names each source and its date,** so the whole page's provenance can be read in one paragraph.

For this repository, the same rule maps onto dataset versions: show the `rows_updated_at`, `Last-Modified` or Dataverse version beside each figure, and put the exact query behind the ƒ panel.

## Phone width

- Every chart reads its width from its container (`clientWidth`) and lays itself out for that width; nothing is a fixed-size image.
- Below about 620 px, line charts drop the end labels, shorten bracket annotations ("$38K past") and reduce height to 250 px.
- Grids collapse: four tiles become two, three cards become one.
- No horizontal scrolling at 360 px.

## Accessibility

- Text contrast on white: ink 17:1 and muted 5.9:1 pass the 4.5:1 standard for small text. Faint (3.0:1), amber (3.8:1) and teal (3.4:1) do not, so the pages use them for chart labels, chips and links, and put anything the reader must read in ink or muted. In dark mode muted is 7.3:1 and faint 4.2:1 on the card.
- Colour is always paired with a label, shape or position (see [Colour rules](#colour-rules)).
- Interactive controls show a 2 px teal focus outline; inputs show a 3 px soft teal ring on focus.
- Unit-chart squares and other small marks carry `<title>` text, so a screen reader or hover can name them.
- The data behind every chart is available as a table or as written figures in tiles.

## Forms the dashboards avoid

- Gauges and dials: a bullet-graph track shows the same thing in less space with an exact reading.
- Pie and donut charts: a unit chart or a bar shows a share with less distortion.
- Legends separated from the data, when direct labels fit.
- 3D effects, heavy borders and vertical gridlines.
- A top-line status verdict that blends several measures. Each question's answer comes from its own figures.
- Countdown projections ("8 years to go") on a reading page. Time estimates import growth assumptions, so they belong on the projection page with their assumptions visible.
- Day-to-day change as the headline number.

## Checklist before publishing

1. Each section has a question heading and a written answer computed from the data.
2. Each figure has a named reference to compare with (a threshold, target, band or previous reading).
3. Each mark has its label beside it; a legend appears only where direct labels cannot fit.
4. Colours keep their roles; down and stale are amber; no meaning depends on colour alone.
5. Each card has a meta line with its age, cadence, source and an ƒ panel holding the formula.
6. Stale figures dim, and missing figures look different from stale ones.
7. The page works at 360 px and in dark mode.
8. Every plotted figure can be read exactly in a table, a tile or a tooltip.
9. Shared numbers come from one shared script.
