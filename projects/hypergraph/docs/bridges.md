# Bridges tested against an endpoint

The challenge defines a bridge as a link that no single dataset holds but several hold together. The project's first bridge, from street trees to surface temperature to heat ED visits (`docs/heat.md`), was a product of two estimates. Nothing outside the chain could check it, and it was contested at area level. This note reports two bridges built differently. Each one composes a prediction from registered links and then tests it against an endpoint dataset that was not used to build it.

The order of work was as follows. `analyses/bridges/compose.py` computed each composed prediction from the link estimates alone, by Monte Carlo with 200,000 draws, and wrote `data/derived/bridges/composed_predictions.json`. That file and four registrations were committed before the endpoint data were queried (commits `a4b6f1e` to `e783221`). The analyses in `analyses/bridges/` then queried the endpoints and wrote the outcomes in `claims/outcomes/bridge-*.json`.

| Claim | Role | Verdict | Estimate (95% interval) |
|---|---|---|---|
| bridge-crz-crash-link | research link: speed, volume and crashes | no_test | exponent 1.2 for injury crashes (Elvik 2009) |
| bridge-crz-injury-crashes | bridge, chain mob-crz-traffic and bridge-crz-crash-link | unsettled (first recorded as confirmed, revised under rule 8) | composed −0.4% (−8.2 to +8.7); observed +1.3% (−4.7 to +7.8) |
| bridge-crz-injury-crashes-v2 | re-analysis against Manhattan north of 60th St | unsettled | composed −2.2% (−9.2 to +5.5); observed +4.5% (−2.7 to +12.2); 2024 placebo +15.2% (+4.8 to +26.6) |
| bridge-shot-ems-link | link: EMS gunshot dispatches per shooting | confirmed | 1.25 (1.20 to 1.30) dispatches per incident |
| bridge-heat-shootings-ems | bridge, chain heat-shootings and bridge-shot-ems-link | confirmed | composed IRR 1.099 (1.049 to 1.148) per 5 C; observed 1.111 (1.100 to 1.121) |

## What an endpoint test can and cannot show

In both bridges, "confirmed" means that the endpoint agrees with the chain. It does not mean that each link has been shown to be right. The registered test computes the difference between the observed endpoint and the composed prediction on the log scale. It divides that difference by the combined uncertainty of the two. The bridge is confirmed when the ratio is below 1.96 in absolute value, and contested when it is not.

A match supports the chain as a whole. A mismatch shows that at least one link, or the way the links were joined, is wrong, but it does not say which. A match is also weaker evidence when the composed interval is wide, because a wide prediction is easy to meet. Different link values can compose to the same prediction. In the first bridge, for example, a larger speed exponent paired with a larger volume elasticity gives the same composed change, and the endpoint cannot tell such pairs apart. The endpoint test checks the composition against data the composition did not use, and the test can fail. The tree bridge had no such test. Its two links each had the sign opposite to the prediction, their product had the predicted sign by accident, and only the separate reading of each link showed this.

## Bridge 1: congestion pricing, speed and injury crashes

### The chain

Congestion pricing began on 5 January 2025 in Manhattan south of 60th Street. The first link is the city's own estimate, from mob-crz-traffic. In 2025, taxi and for-hire vehicle speeds in the zone rose 5.7% (2.9 to 8.6) relative to the rest of the city. Fewer vehicles entered the zone. TLC trips fell 9.8% relative to trips outside it, about half of which continued an earlier trend. The MTA's vehicle-miles series fell 3.8% to 11.0% against 2024, depending on the measurement method. The composition used a volume change of −7.6%, with a 95% range of −3% to −12%.

The second link comes from research. The System graph holds a few findings that tie speed to injury: child pedestrian collisions on higher-speed roads (IRR 1.27, Toronto, PMID 26759927), moped crashes above 20 mph (OR 2.02 for severe injury, PMID 21399547), and cyclist injury where motor traffic is slower than 30 km/h (OR 0.52, PMID 23411678). The graph holds no power-model findings and nothing that links traffic volume to crashes. The exponents therefore come from the literature. Nilsson's power model makes crashes proportional to a power of mean speed. Elvik's 2009 update gives an exponent of 1.2 for injury crashes on urban roads and 2.6 for fatal crashes, but the urban values rest on few studies. The composition drew the injury exponent from a normal distribution with mean 1.2 and standard deviation 0.5. The elasticity of injury crashes with respect to traffic volume was drawn from a normal distribution with mean 0.9 and standard deviation 0.2. That range is an assumption based on safety performance functions, not an estimate from the graph.

### The composed prediction

Faster speeds predict more crashes, and fewer vehicles predict fewer. On their own, the speed term gives +6.7% (+1.4 to +15.0) and the volume term gives −6.7% (−12.4 to −2.3). Together they give −0.4% (−8.2 to +8.7) in injury crashes in the zone relative to the rest of the city. For deaths, the larger exponent makes the speed term dominate, and the composed change is +7% (−4 to +23).

The registrant bet on a decline of 2 to 15 percent, for three reasons. First, the power model was fitted to speed changes on roads that are not congested, and Elvik (2013) finds smaller effects at low initial speeds. Second, London's charge reduced accidents in its zone by about 40 percent (Green, Heywood and Navarro 2016), which is much more than its fall in traffic alone would predict, and London's network speed before the charge, 8.6 mph, was close to New York's 8.5 mph in 2024. Third, the registrant recalled, without having checked them, statements from 2025 that traffic injuries in the zone had fallen. This bet was recorded apart from the endpoint test, and its prior of 0.45 was set lower because of it.

### The endpoint

The endpoint was the NYPD crash records (`h9gi-nx95`). The zone is the largest polygon of the MTA geofence (`srxy-5nxn`): the tolled streets, without the FDR Drive and West Side Highway strips. An injury crash is one with at least one person injured or killed. The model is the one used for speeds in mob-crz-traffic. It is an OLS regression of the log monthly count on area, calendar month, year, and a zone-by-2025 term, with HAC standard errors, fitted to 96 area-months from 2022 to 2025.

Injury crashes in the zone changed by +1.3% (−4.7 to +7.8) relative to the rest of the city. The zone recorded 2,581 to 2,763 injury crashes a year in 2022-2024 and 2,726 in 2025. A false start in January 2024 gives +3.8% (−5.4 to +14.0), so there was no clear earlier trend. The observed change lies well inside the composed interval (z = 0.32), so the bridge is confirmed under its registered rule. The directional bet failed: the point estimate is positive and its interval spans zero.

The secondary measures agree. Persons injured changed by −1.2% (−7.8 to +5.9), pedestrians and cyclists injured by +4.8% (−3.3 to +13.5), and all crashes by +0.2% (−6.6 to +7.4). Including the excluded highways gives +1.7%, and adding January to August 2026 gives +3.2% (−2.3 to +9.0). Deaths are too few to test: the zone recorded 11 to 18 a year, and the estimate is +11% (−47 to +130).

One unregistered check matters for the comparison. In 2022-2024, about 9 to 11 percent of injury crashes citywide lacked coordinates, compared with 2.6 percent in 2025. Among crashes coded as Manhattan, the share without coordinates rose from about 2 to 4.4 percent. Under the assumption that crashes without coordinates are distributed like the rest within each borough, this change biases the zone estimate downward by about 2 to 3 points. With that correction the estimate is about +4%, which is still compatible with the composed prediction.

### What the result means

The endpoint rules out large changes. It rules out a decline the size of London's and any rise above about 8 percent. It cannot say whether the speed and volume effects cancel, as the composition predicts, or whether both are small at speeds of 8 to 9 mph. The difference from London needs its own study. London's charge came with large changes in bus service and road space, and its design compared central London with 20 other British cities, not with the rest of London. Segment-level speeds, volumes and crashes inside the zone would separate the two terms.

Figure: `figures/bridges/bridge_crz_injury_crashes.png`. Panel (a) shows the two link terms, the composed prediction, the endpoint and the placebo on one axis. Panel (b) shows monthly injury crashes in the zone and in the rest of the city, each as a percentage of its 2022-2024 mean for the calendar month.

## Re-analysis of bridge 1 against Manhattan north of 60th Street

The bridge referee (`critique/bridge-crz-injury-crashes.md`) found three problems with the first endpoint test. The share of injury crashes without coordinates fell from about 9 to 11 percent in 2022-2024 to 2.6 percent in 2025, which could bias the comparison of the zone with the rest of the city by 7 to 10 points. The composed prediction (−0.4%) was so close to zero that the test could not tell the chain from no effect. Rule 7, which relabelled the verdict and changed the stance, was written 30 seconds after the outcome was committed. The verdict had already been changed to unsettled under rule 8. The re-analysis is a new claim, bridge-crz-injury-crashes-v2.

The registration was committed in `ce3586a` and pushed to GitHub at about 00:32 UTC on 13 November 2026, before any crash data were queried for it. It lists the crash data seen earlier: the citywide monthly totals and missing-coordinate counts from the first test, and a set of crash rows whose bounding box covers the zone and Manhattan up to about 80th Street, which had been assigned only to the zone. The v1 result was known. The primary comparison area is Manhattan north of 60th Street, built from the UHF neighbourhoods 301 to 310 and the avenue-axis line used in `analyses/mobility/crz_air.py`. The secondary area is the band from 60th to 96th Street, a stand-in for the MTA's CBD Adjacent area, whose boundary is not published. Because the comparison is now with upper Manhattan, the composed prediction uses the speed change of the CBD relative to the CBD Adjacent area (+4.2%) and comes to −2.2% (−9.2 to +5.5). The registration computed in advance that the rule 8 condition could be met only by an observed change of about −6% to −13%, with a probability of 3 to 16 percent if the chain is true. It also fixed four assumptions about where the missing records fall and decided the verdict at the primary estimate and at the two combined bounds.

Injury crashes in the zone changed by +4.5% (−2.7 to +12.2) relative to Manhattan north of 60th Street, 2025 against 2022-2024. The estimate is 1.25 standard errors from the composed prediction and 1.21 from no effect, so D is −0.11 and the endpoint favours neither. Under the bias bounds the estimate ranges from −2.0% (−8.8 to +5.2) to +11.6% (+3.9 to +19.8), and at the upper bound it is incompatible with the chain (z 2.50). The test cannot decide, for a different reason than expected. The false start in January 2024 gives +15.2% (+4.8 to +26.6), so the two areas had already diverged before pricing, and the registered rule makes the verdict unsettled. The 60th-96th Street band gives +5.0% with a placebo of +14.8%, and the Poisson model with area-by-month terms gives +4.6% (−3.6 to +13.4). The stance is 0.

Neither restriction to stable coordinate coverage could be run. No class of record (intersection, address, other) had coverage that varied by less than 2 points across the four years, and only two months before 2025 had coverage within 2 points of the 2025 level. The monthly series shows when the geocoding changed. Coverage was 82 to 95 percent from January 2022 to October 2024 and 96.5 to 98 percent in every month from November 2024 on. It dipped to 82 to 89 percent from July to October 2024. In the same months, injury crashes north of 60th Street fell to about 83 to 90 percent of their usual level while the zone did not (panel b of the figure). The observation is exploratory. It suggests that the 2024 placebo difference, like the 2025 bias, comes from how records were geocoded rather than from traffic.

The first verdict stays unsettled. Its outcome now records the re-analysis and marks the rule 7 stance as chosen after the data were seen (`stance_rule_note`), and the rule's text in `concord/claims.py` says so. Geocoding the 2022-2024 records that have street names but no coordinates would put every year on the same footing. Without that, neither the rest of the city nor upper Manhattan gives a comparison that can test a prediction this close to zero.

Figure: `figures/bridges/bridge_crz_injury_crashes_v2.png`. Panel (a) shows the composed prediction, the primary estimate, the two bias bounds, the secondary area and the placebo. Panel (b) shows monthly injury crashes in the zone and north of 60th Street, each as a percentage of its 2022-2024 mean for the calendar month. Code: `analyses/bridges/compose_v2.py`, `register_v2.py`, `crz_crashes_v2.py`, `figures_v2.py`, `outcomes_v2.py`.

## Bridge 2: heat, shootings and EMS dispatches for gunshot wounds

### Why the endpoint changed

The bridge first proposed ran from heat to shootings to assault ED visits in the Health Department's EHDP data. It could not be built. EHDP publishes violence-related and firearm ED visits only as annual counts and rates by area, for 2018 to 2023 (indicators 2400 and 2437, from SPARCS). It publishes no daily or monthly series, and a temperature gradient needs one. FDNY's EMS Incident Dispatch Data (`76xm-jjuj`) is a daily health-service record kept by a different agency from the NYPD. It records about 2,500 to 6,300 dispatches a year with the initial call type SHOT. Those dispatches became the endpoint. Before registration, only the 2023 total by call type had been looked at, to confirm that the call type exists.

### The chain

The first link is heat-shootings. Daily NYPD shooting incidents rise by a factor of 1.146 (1.130 to 1.163) per 5 C of daily maximum temperature in Central Park. The second link connects shootings to dispatches. Only part of the SHOT dispatches follow from a recorded shooting: in 2023 the NYPD recorded 974 shooting incidents, against 3,164 SHOT dispatches. The rest are reports of shots fired with no victim, duplicate calls, and calls that turn out to be unfounded. The composition took the share of victim dispatches to be between 0.25 and 0.5. It assumed that the other dispatches follow temperature with some fraction, k, of the shootings gradient, where k lies between 0 and 1. The composed rate ratio is 1.099 (1.049 to 1.148) per 5 C. The graph contributes little to this bridge. It has no finding that links gun violence to temperature, as `docs/heat.md` reports. Its one New York finding on heat and intentional injury ED visits (Girma et al. 2023) was used for direction only.

The second link was tested on its own, using the daily levels of the endpoint data but not their relation to temperature. Each NYPD shooting incident adds 1.25 (1.20 to 1.30) SHOT dispatches on the same day, after allowing for calendar effects. This lies within the registered range of 0.6 to 1.6.

### The endpoint

The endpoint used the same negative binomial model as heat-shootings, with terms for day of week, month, year, holidays and rain, fitted to 7,548 days from 2006 to August 2026. SHOT dispatches rose by a factor of 1.111 (1.100 to 1.121) per 5 C. The value lies inside the composed interval (z = 0.41), so the bridge is confirmed. The warm-season estimate is 1.095 (1.077 to 1.114), and the estimate for 2006-2019 is 1.114 (1.102 to 1.126). Stabbing dispatches lie outside the chain and serve as a contrast. They rise less, by 1.076 (1.068 to 1.084).

The endpoint is far more precise than the prediction, so the test mainly rules out the two ends of the composed range. If only the victim dispatches followed heat, the rate ratio would be about 1.055. If every dispatch followed heat as shootings do, it would be 1.146. The observed value lies between these and implies, in an exploratory calculation, that dispatches with no recorded victim rise with heat at about two thirds of the rate of shootings. The bridge carries the heat gradient from police records to an EMS record. It does not reach ED visits for assault, which would need the Health Department's daily syndromic data.

Figure: `figures/bridges/bridge_heat_shootings_ems.png`. Panel (a) shows the shootings link, the composed prediction, the endpoint, two sensitivity analyses and the stabbing contrast. Panel (b) shows the two annual series and the second link's estimate.

## Stance

The precedence rule gives a bridge the stance of its weakest link. For the crash bridge, that is mob-crz-traffic, whose stance is 0.96, because the research link has no city test. The endpoint itself is near zero, and its stance against the registered negative direction is −0.21. That value is kept in the outcome as `endpoint_stance`. The rule was written for bridges that are products of link estimates. For bridges with an endpoint, the dashboard may need to show the endpoint stance as well.

## Research needed

- The System graph lacks the speed-and-crash literature (Nilsson 2004; Elvik 2009 and 2013; Cameron and Elvik 2010) and the London congestion charge accident study. With these, the first bridge's research link could be built from the graph.
- Segment-level speeds, volumes and crashes inside the zone would separate the speed term from the volume term.
- Crash records without coordinates could be geocoded from their street names. This would remove the coverage change between 2024 and 2025 from the comparison.
- Daily assault and firearm ED visits by neighbourhood, which the Health Department holds but does not publish, would carry the heat bridge to a health outcome.
- Linked EMS and NYPD records would show how many gunshot dispatches have a recorded shooting behind them.

## Sources

- NYPD Motor Vehicle Collisions - Crashes, `h9gi-nx95`. FDNY EMS Incident Dispatch Data, `76xm-jjuj`. NYPD Shooting Incident Data, `5ucz-vwe8` and `833y-fsy8`. All from NYC Open Data. The outcome files record `rowsUpdatedAt`, the SoQL and the fetch time.
- MTA Central Business District Geofence, `srxy-5nxn`, data.ny.gov. The MTA speed, trip and vehicle-miles series are cited in mob-crz-traffic.
- NOAA GHCN-Daily, Central Park USW00094728.
- Elvik R (2009), TØI Report 1034/2009. Elvik R (2013), Accident Analysis and Prevention 50:854-860, doi:10.1016/j.aap.2012.07.012. Nilsson G (2004), Lund Bulletin 221. Green CP, Heywood JS, Navarro M (2016), Journal of Public Economics 133:11-22, doi:10.1016/j.jpubeco.2015.10.005.
- System Public Graph API v1.0 and Dataverse v2.1 (doi:10.7910/DVN/7V6JDO). Abstracts read: `data/derived/bridges/abstracts_graph.txt`.
