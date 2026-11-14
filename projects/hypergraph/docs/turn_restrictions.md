# Left turns, turn restrictions and pedestrian injuries

Turn-restrictions agent, 13 November 2026. Claims: `turn-calming-ped`, `turn-calming-leftturn`, `turn-calming-displacement`. Code: `analyses/turn_restrictions/`. Data: `data/derived/turn_restrictions/` (crash extracts in `~/opt/nyc-concordance/turn_restrictions/`, outside the repo). Figures: `figures/turn_restrictions/`.

## Corrections after review

A referee rebuilt the three ratios with separate code and got the same values (`critique/turn-calming-ped.md`, `critique/turn-calming-leftturn.md`, `critique/turn-calming-displacement.md`). The verdicts stand under rules 1 and 4, but the two confirmations should be read beside the placebo and not counted as agreement with research.

1. Had the placebo been registered, rule 11 would make both confirmations unsettled: against the placebo, D is 0.39 for pedestrian injuries and −9.3 for left-turn crashes.
2. Against 4,713 untreated intersections with leading pedestrian intervals, the treated sites decline steadily, by about 3.5 to 5% a year from three years before installation, with no peak and no step at installation. Longer gaps before the comparison sites were treated increase the bias. This contradicts the explanation that comparison sites were approaching a peak. The likely reading is that DOT chooses sites on a long downward trend, for reasons the data do not show.
3. An empirical Bayes check failed its own placebo (1.30 to 1.36), because the open data hold no pedestrian or turning volumes.
4. The data do not "agree with DOT's −18%", and the true effect is not known to lie between the registered ratio and 1. The displacement result shows that injuries in the surrounding ring fell too; it does not show that injuries did not move.
5. The response is a successor claim decided on crashes after September 2026 for sites installed in 2025 and 2026, with a placebo registered as part of the test (rule 12).

## Question

Jeff asked whether left-turn restrictions on busy streets, such as those on 42nd Street in Manhattan, reduce crashes and especially pedestrian injuries, and what they do to throughput. This note does not repeat `docs/street_safety.md`, which covers red-light cameras, LPIs, road diets and daylighting, or `mob-speedcam-247`.

## What the research says

NYC DOT's *Don't Cut Corners* study (2016) found that 108 of the 859 pedestrians and bicyclists killed in 2010-2014 were struck by a left-turning vehicle. Left turns accounted for 19% of pedestrians and bicyclists killed or severely injured, against 6% for right turns. Seniors are over-represented: 53% of left-turn deaths were people aged 65 or older.

The same study compared 3 years before and 3 years after treatment at 478 intersections, with no comparison group. Left-turn pedestrian and bicyclist injuries changed as follows:

| Treatment | Sites | Before | After | Change |
|---|---|---|---|---|
| Left-turn restriction (ban) | 51 | 113 | 67 | -41% |
| Left-turn-only signal | 34 | 55 | 37 | -33% |
| Left-turn bay | 140 | 117 | 100 | -15% |
| Protected bicycle lane | 149 | 295 | 250 | -15% |
| LPI | 104 | 282 | 243 | -14% |

These are the largest effects in the literature for any left-turn treatment, and the weakest design. Sites are chosen after crash clusters, so some decline is expected without any treatment.

DOT's turn-calming page reports pedestrian injuries down 18%, severe pedestrian injuries down 33% and median left-turn speed down 54% at calmed intersections. It says injuries declined "faster than nearby comparable locations" but does not name those locations or the periods. An IIHS study of 10 hardened-centerline sites in Washington, DC, against 8 controls, found left-turn conflicts with pedestrians down 70.5% and mean turning speed down 9.8% (Hu and Cicchino 2020). Most of that conflict reduction came from two sites.

### The graph

Variable search over 16 terms (`graph_collect.py`) found no evaluation of turn bans, turn calming or hardened centerlines. "Turn restriction", "turn ban", "hardened centerline", "protected left" and "crash migration" returned nothing relevant. I read the abstracts of the four records this note mentions:

- PMID 37288501 (Montreal, 2012-2019). Traffic-calming measures and collisions, IRR 0.31 (0.12-0.86). The figure is correct, but it is a subgroup result for intersections on local roads. Overall the authors found weak evidence, and they note that most collisions are on arterials, where New York puts its turn calming.
- PMID 30962130 (Changsha). Signals that let left turns and pedestrians go together raised risky conflicts (IRR 3.13 for vehicles, 4.02 for pedestrians). The graph labels the 3.13 as a "proportion of intersections", which is wrong. The abstract also reports no difference in transport efficiency between the two signal designs. It is the only graph evidence on throughput.
- PMID 26680430 (Montreal, 512 intersections). A fourth intersection leg (IRR 2.40) and parking within 5 m (IRR 2.40) are associated with more injured pedestrians. The figures are correct, but the study is cross-sectional.
- PMID 31033340 (Ghana). The street-safety agent had already found this record reversed, and I did not use it.

## Which intersections were treated, and when

Left-turn bans have no dated public list. NYC Open Data holds no dataset of turn prohibitions. The Vision Zero street improvement project layers (`shr7-eqdc`, `if4c-w48d`) give project names and years but not the features installed.

On 42nd Street, DOT's 2019 transit project mostly extended existing bans rather than adding new ones (presentation to Community Board 6, 4 September 2019). The changes were:

- 6th Avenue (eastbound to northbound): from 7am-7pm except Sunday to all times.
- Lexington Avenue (westbound to southbound): from 7am-7pm except Sunday to all times except buses.
- 7th Avenue (westbound to southbound): from all times except buses to all vehicles.

Implementation was planned for summer 2019, and I could not find the exact dates. Three intersections with uncertain dates, followed by the 2020 pandemic, cannot support a test, so I did not register one.

Left-turn calming does have dated data. The VZV Turn Traffic Calming layer (`sm2x-35i7`) lists 1,601 records with completion dates. After dropping right-turn and bike-island records and merging records within 40 m, it gives 1,207 intersections treated from 2016 to 2026. Figure: `figures/turn_restrictions/sites_map.png`. These treatments slow the turn; they do not ban it. The registered test is therefore a test of calming. It is not a test of bans.

## Registered test

Before reading any site-level crash data, I fixed the analysis script (commit `bd2a8d9`) and registered three claims (commit `85b40af`, pushed to `prereg/turn-calming-*`).

The design stacks cohorts by installation quarter, 2016Q3 to 2023Q2. Each treated site is compared over the 24 months before and the 24 months after its installation month. The comparison group is calming sites that DOT treated more than 24 months after the cohort, observed over the same calendar months.

The outcomes are:

- `ped`: pedestrians injured or killed within 40 m of the site.
- `lt`: crashes within 40 m in which a vehicle's pre-crash manoeuvre was "Making Left Turn".
- `ped_ring`: pedestrians injured or killed 50-200 m away, excluding crashes within 40 m of any other calming site.

The model is a conditional Poisson (binomial) regression with cohort fixed effects and standard errors clustered by site. The data are 1,798,418 geocoded crashes (`h9gi-nx95`) and 207,891 left-turn collision ids (`bm4k-52h4`; the brief's `bk4m-6pyy` is a typo for this id), through September 2026.

The power check (`power.py`, assumed rates) expected a standard error of 0.077 on the log ratio for pedestrians, which risked an unsettled result. The realised standard error was 0.044.

| Claim | Ratio of ratios (95% CI) | Predicted | Verdict |
|---|---|---|---|
| `turn-calming-ped` | 0.848 (0.779-0.924) | 0.80-0.97 | confirmed |
| `turn-calming-leftturn` | 0.904 (0.847-0.965) | 0.70-0.95 | confirmed |
| `turn-calming-displacement` | 0.923 (0.876-0.973) | 0.93-1.07, CI within 0.88-1.12 | unsettled |
| Secondary: left-turn crashes in the ring | 0.945 (0.899-0.994) | not registered | |

At treated sites, pedestrians injured or killed fell from 1,966 to 1,706, and left-turn crashes fell from 3,242 to 2,683. The checks fixed in `did.py` agree. With a 30 m radius the ratios are 0.844 for pedestrians and 0.895 for left-turn crashes. Restricted to cohorts whose windows avoid March-June 2020, they are 0.827 and 0.900. The figures are `event_time.png` and `forest.png`.

The ring 50-200 m away fell as well (0.92), so the test cannot say whether injuries moved there, which is why the displacement claim is unsettled rather than confirmed: its lower bound missed the registered band by 0.004.

## Why the confirmations do not show that calming works

The event-time figure shows that treated sites were already falling towards the comparison sites before installation. A placebo that moves installation 12 months earlier gives ratios of 0.912 (0.825-1.008) for pedestrians, 0.934 (0.861-1.013) for left-turn crashes and 0.935 (0.877-0.996) for the ring. If that pre-installation trend had continued, the trend-adjusted ratios would be 1.03 (0.82-1.29) for pedestrians and 1.04 (0.87-1.25) for left-turn crashes. These checks are exploratory (`did_explore.py`), written after the registered result was seen.

The likely cause is the comparison group. DOT chooses sites after crash clusters. Treated sites are therefore past their peak, while later-treated sites observed in the same months are still approaching theirs. Regression to the mean runs in opposite directions in the two groups and produces a ratio below 1 with no treatment at all.

The registered verdicts stand under rule 1. They do not separate an effect of calming from site selection, and with the earlier trend allowed for the ratios are about 1.03 to 1.04. The size of any effect of calming is not known from these data (see the corrections above).

## Throughput

Turn bans and turn calming have no throughput measure in the city's open data. DOT's traffic speeds (`i4gi-tjb9`) cover only highways, bridges and 11th/12th Avenue, with no link on 42nd Street or at any calmed intersection. Taxi trip records carry zones rather than coordinates, so a single intersection cannot be isolated.

As an exploratory proxy for the 42nd Street project, I used MTA weekday bus speeds (`data.ny.gov` `cudb-vcni`). The M42 rose from 4.46 mph in January-February 2019 to 4.70 mph in January-February 2020. The mean of six other crosstown routes (M31, M50, M57, M66, M72, M96) changed by +0.1% (range -1.5% to +3.2%). The M42 therefore gained about 5% relative to those routes (`bus_speeds.png`).

That project also added offset bus lanes and queue-jump signals. The turn changes cannot be separated from the other changes, and the comparison rests on one pair of months, so this is not evidence about turn bans. The only research on throughput in the graph (Changsha) found no loss of efficiency from separating left turns from pedestrians.

## What would settle it

For calming, the question would be settled by a registered empirical Bayes before-after study with a safety performance function fitted on untreated signalized intersections, or by a comparison group matched on the crash history DOT used to select sites. DOT's selection windows would let those years be excluded.

For bans, it needs a dated list of turn prohibitions, from DOT sign orders or the street centreline turn-restriction layer by date, tested with a displacement ring along the detour routes.

Throughput needs turning-movement counts at treated and comparison intersections.

## Sources

NYC DOT, *Don't Cut Corners: Left Turn Pedestrian & Bicyclist Crash Study* (2016), nyc.gov/html/dot/downloads/pdf/left-turn-pedestrian-and-bicycle-crash-study.pdf. NYC DOT Turn Calming Program page (accessed 13 November 2026). NYC DOT, 42nd Street Transit Improvements, Community Board 6, 4 September 2019. Hu W, Cicchino JB, J Safety Res (December 2020), IIHS. NYC Open Data `sm2x-35i7`, `h9gi-nx95`, `bm4k-52h4`, `i4gi-tjb9`; NY Open Data `cudb-vcni`. The dataset versions are in the outcome files.
