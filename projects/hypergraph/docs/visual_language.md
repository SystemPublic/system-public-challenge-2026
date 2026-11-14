# Visual language of the dashboard and the explorer

This note explains how the evidence dashboard (`viz/index.html`) and the graph explorer (`viz/explorer.html`) encode the claims and the graph, and why.
The rules for claims, verdicts and the stance value are in `concord/claims.py`.

## Rebuilding

```bash
cd nyc-concordance
~/.venvs/nyc-concordance/bin/python tools/neighborhood.py --defaults   # graph subgraphs (cached; about 110 API calls from a cold cache)
~/.venvs/nyc-concordance/bin/python tools/build_site.py                # claims export, data wrappers, link check
```

`build_site.py` runs `python -m concord.claims export`, writes each data file a second time as a small `.js` file, and checks every relative `src` and `href` in the pages.
The `.js` copies exist because browsers refuse `fetch()` on pages opened from the file system but do load `<script src>`.
The pages therefore work when opened from the folder and when served as a static site.
The one external file is D3 7.8.5 from cdnjs.cloudflare.com, so the pages need a network connection.

## The middle is an interval, not a category

The register has five verdicts, but the verdict is a summary of a continuous result.
A claim called "unsettled" may have a central value close to agreement and an interval that only just reaches zero, or a central value at zero and an interval spread across the whole range.
Those two claims call for different next steps, and the single word "unsettled" does not distinguish them.
Most claims in a study like this one end in that middle, so a display with three categories would discard most of the information.

The concordance strip therefore puts every claim on one axis, the stance, which runs from −1 (the city data contradict the direction the research reports) through 0 (they cannot tell) to +1 (they agree).
`concord.claims.stance()` computes it from the city estimate and its 95% interval.
It divides the estimate by its standard error and passes the result through tanh(z/2), so that a precise effect approaches ±1 and an imprecise one stays near 0.
The interval is drawn as a bar.
A bar that crosses the centre line is a claim the data have not settled, and the length of the bar shows how far from settled it is.
The verdict still sets the colour and the shape of the mark, so the categorical reading is available alongside the continuous one.

The stance is computed against the registered direction.
For most claims that is the research direction.
A conflict claim may register the opposite direction, a bet that the city disagrees with the research.
For such claims the dashboard flips the sign, so that the axis always means agreement with the research and the shaded bet band moves to the left half.
The research direction is read from the outcome's `graph_effect`, or else from the majority `direction` in `graph_evidence`.

## Encodings in the concordance strip

| Element | Encodes |
|---|---|
| Horizontal position | stance, −1 to +1 |
| Bar | 95% interval of the stance |
| Mark colour and shape | verdict: confirmed (blue circle), bridged (green triangle), unsettled (grey diamond), contested (vermillion square), no test (hollow circle) |
| Dashed shaded band | the half of the axis the registrant bet on; a band around 0 for a predicted null |
| Right column | the registrant's prior that the outcome would be "confirmed", on a 0 to 1 track, and the scored prediction (hit, partial, miss) |
| Row without a bar | registered but not decided, or no test |

The bet band and the prior come from the registration, which precedes the outcome, so the viewer can compare what was bet with what happened.
A confirmed claim with a prior of 0.3 is a surprise, and one with a prior of 0.9 is not.

The verdict sets the colour, but colour is never the only cue. Each verdict has its own mark shape, and its name appears in the tooltip, the selection list and the table.
The palette is Okabe-Ito blue (#0072B2), vermillion (#D55E00) and bluish green (#009E73), with a neutral grey for "unsettled".
Grey was chosen for the middle because the middle of a diverging scale should carry no hue.
The three hues pass the dataviz validator's all-pairs colour-vision-deficiency check in light mode (worst pair ΔE 11.0 under deuteranopia).
The light grey has contrast below 3:1 against the page, so unsettled bars carry a darker outline and the verdict is always written out.
Dark mode uses lighter steps of the same hues, which `viz/style.css` defines as CSS variables.

## Paired estimates

For the selected claim, the research estimate (`graph_effect`) and the city estimate (`city_effect`) are drawn as a two-row forest plot.
Each row has a point, a 95% interval and a dashed line at no effect (0, or 1 for ratios).
Ratios are drawn on a log axis, so that 0.5 and 2 are the same distance from 1.
The two rows share an axis only when their `scale` and `null` are the same.
When the units differ, as with a correlation in the literature and a slope in the city data, each row has its own axis and a note says that only the directions and the crossing of no effect can be compared.
Putting two different units on one axis would let readers compare sizes that the numbers do not support.
When the outcome gives no `graph_effect`, the research row lists the cited graph evidence by count and direction.

## Bridge path

A bridge is drawn as a vertical path of concept nodes joined by its link claims, in chain order.
Each link is a line coloured by its verdict, labelled with its claim id, its city estimate and the datasets it used, and given a small stance strip.
The link with the lowest interval bound is labelled "weakest link".
The concepts at each end of a link come from the first two-concept entry in its `graph_evidence`.
When the end of one link and the start of the next are different concepts (for example "surface temperature" and "air temperature"), a dashed connector marks the joint and says that the bridge assumes they are the same.
That joint is often where a bridge is weakest, so the dashboard draws it.
A vertical layout was chosen because it keeps long labels readable at phone width.

## Provenance

A time line places the registration, each dataset fetch and the outcome in order.
A city dataset fetched before the registration is flagged in the warning colour.
The fetch time is the time the response was cached, so a flag can mean an exploratory look; the notes should say which.
The panel lists the registration hash, whether the registration still matches it, and whether the outcome cites the same hash.
It then lists every source with its version (`rows_updated_at` for NYC Open Data, `Last-Modified` for NOAA, the Dataverse version for the System graph) and its exact query, and every graph finding cited at registration with PubMed links.

## Research-needed map

Every `research_needed` entry and every `settle` statement is placed in a claims-by-kinds matrix.
The kinds are individual-level data, sensor or monitoring data, imagery, an instrument or natural experiment, a longitudinal design, a within-unit design, finer resolution, and linking datasets.
They are assigned by keyword rules in `viz/index.html` (`RKINDS`), so an entry can fall under more than one kind, and an entry that matches none is put under "Other".
A filled cell is a research-needed entry, shaded by its highest priority and labelled with the count of entries.
An outlined cell is a settle statement only.
A matrix was chosen over a node-link map because it stays legible as claims are added, and because reading down a column answers the practical question of which one kind of new data would help the most claims.
Registrants who want a precise placement can add a `kind` field to an entry; the keyword rule is a fallback.

## Graph explorer

The explorer draws one concept and its neighbours in the System Public Graph from `viz/data/graph/<slug>.json`, written by `tools/neighborhood.py`.
In the radial layout, neighbours with more findings sit closer to the centre, on a log scale of findings.
They are spread around the circle so that the largest neighbours are not crowded together.
The force layout is offered for dragging.
Line width is the square root of the number of findings, so that area grows with the count.

The graph's relationship totals (`num_findings`, `num_studies`) carry no sign.
For the relationships with the most findings (twelve by default), the tool reads the individual associations and classifies each by its statistic.
Ratios are compared with 1, and coefficients and differences with 0.
An interval that crosses the null, or a p value above 0.05, counts as null.
Statistics without a sign, such as R² or chi-square, count as unknown.
Line colour runs from vermillion (all signed findings negative) through grey (mixed) to blue (all positive).
A light dashed grey line is a relationship that was not sampled, so its sign is unknown.
The sign follows the variables as each study named them.
A study of "lack of green space" reverses the sign of a study of "green space", so the colour is a reading aid and not an effect estimate.
Selecting a line lists the sampled findings with their statistics and PubMed or DOI links.

The pre-built set shows two limits of the data.
The heat wave concept (k9BAffdSqv) has one relationship in the graph, so its neighbourhood is one line.
The asthma concept has more relationships than the 1,500 the tool reads, and the page states this.
The association endpoint can return more associations than a relationship's `num_findings`; the sign counts are of what it returns.
