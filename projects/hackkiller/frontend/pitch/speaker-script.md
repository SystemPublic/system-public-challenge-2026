# Malaria Atlas · HackKiller

## Open and rehearse

Double-click **Open Presentation.command** in this folder. Keep its Terminal window open throughout the presentation. It starts a server on your own computer and opens `pitch.html` in the browser.

If you prefer the terminal, run the following command from this folder, then open `http://127.0.0.1:8787/pitch.html`.

```sh
python3 -m http.server 8787 --bind 127.0.0.1
```

Press **F** for full screen and **T** to start the rehearsal timer. Left and right arrows move between the three main slides. **D** opens the live product. **B** opens the saved demo screens. In backup, use **1** for evidence and **2** for budget. **Shift+T** resets the timer. These shortcuts work when the presentation has focus. During the live product, use the persistent buttons above it to return to findings or open backup.

If the browser limits the full-screen button, press **Control + Command + F** on Mac. The deck displays that fallback in a message. The main spoken text is approximately **291 words**, leaving room for clicks within the three-minute slot. Check the timing at your own speaking pace.

Opening `pitch.html` directly also displays all slides and embedded backup images. The live product uses the local server because its data loads through browser fetch requests.

Aim to finish at **2 minutes 50 seconds**, leaving ten seconds for a slow click or transition. The timing below reserves 90 seconds for the live demo. Read only the blockquotes aloud. The action instructions are rehearsal cues.

## 0:00–0:30 · Project and purpose

**Screen** — Project and purpose. **Action** — Start the timer, face the judges, then click **Open the atlas** as you finish.

> We’re HackKiller, and this is Malaria Atlas. Imagine you’re planning a malaria prevention programme in Benin. What did a bed net trial find, and how many people could your budget reach? We built this for programme teams to explore evidence by setting, comparison and follow-up, then examine their own budget assumptions.

## 0:30–1:20 · Map, country and source

**Actions**

1. On the map, click **Benin**. The country links below the map are larger click targets if needed.
2. Drag the year slider to **2024**. This also pauses the automatic timeline. The selected year controls which publications are available. It also selects the country background year.
3. Keep **Paper-verified anchors** selected. Select **ITNs** in the prevention filter.
4. Scroll to the first **chlorfenapyr-pyrethroid net** card, showing **0.54** and a **2023 publication** tag. Click **Inspect source & graph**.
5. Point to the comparator and follow-up in the open panel. Close the panel using its × button, then click **BUDGET** in the left rail.

> We start with the country context, then move to the evidence. The year slider shows what had been published by that year. Here in Benin, the same bed net trial has results for different follow-up periods. Opening a result shows the comparator, children studied, follow-up and source paper. That context matters when someone asks whether an estimate applies to their programme.

**Pacing** — Open the source panel by about 1:00. Point to its fields briefly. The online paper link can be opened during questions, so the timed demo can stay in the product.

## 1:20–2:00 · Change a budget input

**Actions**

1. In the Budget & Coverage Planner, select **Benin** again. The planner opens with its own default country.
2. Keep **10,000** target people, **ITNs only**, **$12** full programme cost per person, **80%** target coverage and **90%** sustained use. These are illustrative user inputs.
3. At **$100,000**, show the **8,000** funded enrolments in the output table. Scroll to the table and back to the input if necessary.
4. Change the total budget to **60000**, then scroll to the output. Show **5,000** funded enrolments and **4,500** expected used packages.
5. Click **Continue to findings →** in the persistent bar above the product.

> Now we can ask a planning question. Suppose we have ten thousand eligible people, an eighty percent coverage target, and an assumed twelve-dollar programme cost per person. A hundred thousand dollars funds all eight thousand target enrolments. Reducing the budget to sixty thousand funds five thousand. At ninety percent sustained use, that gives forty-five hundred expected used packages. The calculation follows the assumptions we enter.

**Optional live input** — If time allows, replace “Reducing the budget to sixty thousand” with “What budget would you like to try?” Use the judge’s answer, read the live output and continue. Keep $60,000 as the rehearsed fallback. An arbitrary budget may fund the full target, so describe the number the tool actually displays.

## 2:00–2:30 · What we found and where it stops

**Screen** — What we found. **Action** — Point to the two confidence intervals, then advance once.

> The follow-up period belongs with the result. In this Benin trial, the reported hazard ratio was point five four during the first two years. In year three, it was point eight zero, with a confidence interval crossing one. Evidence coverage and review depth remain selective. Budget outputs depend on the user’s cost and uptake assumptions.

## 2:30–3:00 · How we used the Graph

**Screen** — How we used the System Public Graph. **Action** — Follow the three columns from left to right. Finish by about 2:50.

> We combined Graph concept relationships with variable-name searches, then checked outcomes, comparators and follow-up against the papers. That produced four hundred eighty-one candidate associations and fifty-three reviewed comparisons. We kept uptake studies separate from malaria outcomes. WHO, MAP and Pf8 add background context. A Python pipeline packages this into the local frontend, where users can inspect each result’s source.

## If the live demo is interrupted

Click **Backup screens** above the product, or focus the presentation toolbar and press **B**. The backup images are embedded in the HTML. Use the **Evidence** and **Budget** tabs to follow the same sequence.

> I’ll continue with the saved product screens. This is the same source panel and budget calculation from our local snapshot.

For the evidence screen, explain the comparator and follow-up. For the budget screen, say “With these inputs, sixty thousand dollars funds five thousand enrolments.” Click **Continue to findings →** to resume the main sequence. Keep the original timing and shorten the explanation if the interruption took time.

## Numbers to keep straight

| Item | Meaning |
|---|---|
| Five countries | Benin, Burkina Faso, Mali, Nigeria and Tanzania are the showcase countries. |
| 481 associations / 273 papers | Candidate evidence in the supplied project snapshot. |
| 53 reviewed comparisons | 20 paper anchors plus 33 abstract-reviewed records, with 52 displayable comparisons. Review levels differ. |
| 11 full-text checks | Targeted checks recorded in the bundle. |
| 721 country-year records | Indicator records from WHO and MAP, across multiple indicators. |
| 2023 and 2024 | Publication years of the two Benin analyses. The follow-up labels describe time since net distribution. |
| $12 per person | An illustrative full programme cost entered in the planner. |
| $96,000 | 8,000 target enrolments multiplied by $12. |
| $60,000 / 5,000 | Budget and funded enrolments in the rehearsed scenario. |
| 4,500 | Expected used packages under the 90% sustained-use assumption. |


## Supporting vaccine and SMC results

On the findings slide, click **Vaccine & SMC results**, or press **V** while the presentation has focus. The panel contains the three comparisons supplied for the final presentation. Close it with × or Escape. It is available for questions and a longer demonstration.

| Intervention and setting | Reported effect and 95% confidence interval |
|---|---|
| R21/Matrix-M, seasonal trial sites | 12-month adjusted vaccine efficacy 75% (71%–79%). |
| R21/Matrix-M, standard vaccination trial sites | 12-month adjusted vaccine efficacy 68% (61%–74%). |
| RTS,S + SMC versus SMC alone | Three-year additional reduction in clinical malaria 62.8% (58.4%–66.8%). |

The R21 comparisons use a rabies control vaccine and concern first clinical malaria episodes over 12 months after dose 3. The combination trial compares RTS,S + SMC with SMC alone over three years. Each row retains its own comparator, population, outcome and follow-up. [R21 trial](https://pubmed.ncbi.nlm.nih.gov/38310910/) · [RTS,S + SMC trial](https://pubmed.ncbi.nlm.nih.gov/34432975/)

## Questions judges may ask

**How did you select evidence?**

The project scanned a fixed snapshot of 1,999,877 Graph associations. It used malaria-related concept relationships and variable-name searches for nets, SMC and vaccines. Source joins and review then added the context needed to interpret the selected comparisons. The full pipeline and selection rules are in the repository.

**How much was verified?**

The bundle distinguishes 20 paper anchors and 33 abstract-reviewed records. Eleven targeted full-text checks are recorded. The source panel displays the relevant review level and any available verification notes for each comparison.

**What do the Benin results tell us?**

The papers report a clinical-malaria hazard ratio of 0.54, with 95% CI 0.42–0.70, for the first two years, and 0.80, with 95% CI 0.56–1.17, for the third year. Both compare chlorfenapyr–pyrethroid nets with standard pyrethroid nets in the same trial. The third-year interval includes 1, and each estimate retains its own follow-up label. A direct statistical comparison between the follow-up periods would require further analysis. [First analysis](https://pubmed.ncbi.nlm.nih.gov/36706778/) · [Third-year analysis](https://pubmed.ncbi.nlm.nih.gov/38401551/)

**What does the budget planner calculate?**

It funds enrolments using the entered full programme cost, coverage target and available budget, then applies the entered completion or use rate. If multiple programmes are selected and funding is insufficient, it scales their target enrolments proportionally. Its range of people reached accounts for unknown overlap between programmes. The slide demonstrates a single programme so that its assumptions and arithmetic are easy to inspect.

**Where did the extra data enter?**

WHO supplies country indicators, MAP supplies modelled malaria trends, and Pf8 supplies sampled molecular-marker context. Their units, sampling and time coverage belong with the displayed data. The national setting labels are coarse navigation groupings. A trial’s own site description gives the setting for that comparison.

**How does this use the API?**

The project used the System Public Graph API during research to inspect concept relationships and association records. The stage presentation reads the supplied processed data locally. Its interactions require a local server, while paper and repository links open online sources.

**What did AI contribute?**

The project documentation records Claude Code assistance with the data pipeline and documentation. Codex assisted with research, source checking, and this presentation and script. Describe each team member’s own contribution from their actual work.

## Package provenance

This presentation uses the `frontend/` directory and its schema **1.0.1** data from the supplied `Hackiller_V2PATH-main.zip`. The separate pipeline site bundle is schema 1.0.0. The presentation copy loads local DM Sans and Manrope fonts and uses a saved-snapshot information button in place of remote refresh. The supplied ZIP remains the reference copy.

The three formal pages cover every required template section. The hidden backup page has two product captures. The deck embeds its fonts, map image, scientific figure and backup screenshots so those pages can be displayed independently. Live product files remain alongside it in `product/`.

The figure uses the two paper-reported Benin estimates. Product screenshots were captured from the supplied frontend. The Graph counts come from the supplied frontend bundle. Graph-derived data carry CC BY-NC 4.0 terms. Local fonts carry their bundled SIL Open Font License notices, and D3 retains its bundled license. [Project repository](https://github.com/DAzyyyyy/Hackiller_V2PATH)
