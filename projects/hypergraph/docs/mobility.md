# Movement and air: mobility claims

This note reports six registered claims on traffic, air pollution, asthma, speed cameras and active commuting. Each claim was registered in `claims/registered/` and committed before the city data that test it were queried. The outcomes are in `claims/outcomes/`. The scripts in `analyses/mobility/` re-run every number below from a clean cache.

`figures/mobility/mobility_claims_summary.png` shows each city estimate and its 95% interval against the registered prediction.

| Claim | Kind | Verdict | City estimate (95% interval) | Prediction scored |
|---|---|---|---|---|
| mob-crz-traffic | confirmation | confirmed | CBD speed +5.7% (+2.9 to +8.6) relative to the rest of the city | hit |
| mob-crz-air | confirmation | unsettled | PM2.5 at PS 19 −5.2% (−9.5 to −0.9); NO2 not testable | partial |
| mob-crz-air-nyccas | confirmation (supersedes mob-crz-air for NO2) | unsettled | NYCCAS NO2 +0.9% (−2.2 to +4.2) | miss |
| mob-asthma-pollution | confirmation | unsettled | rate ratio 1.22 (0.81 to 1.85) per 10 ppb NO2, poverty-adjusted | miss on mechanism |
| mob-speedcam-247 | confirmation | unsettled | ratio of ratios 0.934 (0.860 to 1.014) | partial |
| mob-active-commute-obesity | confirmation | confirmed in sign | −6.0 (−7.8 to −4.1) obesity points per 10 points of walking or cycling to work | partial |

## The research side

The System Public Graph (API v1.0, Dataverse v2.1) holds many findings on the health outcomes of these exposures. It has 133 findings in 77 studies that link particulates to asthma, 97 findings in 62 studies that link nitrogen dioxide to asthma, and 51 findings in 29 studies that link traffic-related pollution to asthma. Most findings reported as ratios are above 1. The median ratio is 1.18 for particulates, 1.16 for NO2 and 1.51 for traffic-related pollution, but each median pools findings with different exposure increments and study designs, so the medians are not effect sizes. `analyses/mobility/graph_evidence.py` writes these summaries to `data/derived/mobility/graph_evidence.json`.

The graph holds little or no evidence on the transport links. Searches for congestion pricing, road pricing, congestion charging, low emission zones, cordon and toll found no relevant findings. The graph has no concept for cycling or commuting. It has one finding that links traffic-related pollution to NO2. Speed cameras are not a concept in the graph; searching variable names finds 7 associations in 6 studies. The road-pricing claims therefore rest on literature found on the web, cited in each registration.

I read the PubMed abstracts of the findings I relied on. The graph records one of them incorrectly. The graph records two associations from the Barcelona speed camera study (PMID 17666698): RR 0.73 (0.63 to 0.85) for collisions on the beltway with cameras, and RR 0.99 (0.90 to 1.10) labelled as people injured near the cameras. The abstract shows that the second value belongs to the comparison roads, which had no cameras.

## Congestion pricing and traffic (mob-crz-traffic): confirmed

Congestion pricing began in Manhattan south of 60th Street on 5 January 2025. The MTA publishes monthly average taxi and for-hire vehicle speeds for the CBD, the area next to it, and the rest of the city (data.ny.gov `6p29-6xqn`, from October 2019 to August 2025). I fitted a difference-in-differences model on log monthly speed, comparing 2025 with 2023-24, with area, calendar-month and year terms and Newey-West standard errors.

CBD speeds rose 5.7% (2.9 to 8.6) relative to the rest of the city and 4.2% (1.6 to 6.8) relative to the adjacent area. The same model with a false start in January 2024 gives −0.8% (−4.6 to +3.1), so speeds had no pre-existing upward trend. Average CBD speed was 8.5 mph in 2024 and 9.0 mph in January to August 2025.

TLC trip counts in the 38 CBD taxi zones (`c5iv-bn4s`, zones from `yfdc-w5jh`) fell 9.8% (6.6 to 12.8) relative to trips outside the CBD. The same model with a false start in January 2024 also shows a decline of 4.5%, so about half of the trip decline continues an earlier trend. High-volume app trips fell 14.3% and yellow taxi trips 4.7%. Passengers on these trips pay a CBD surcharge on each trip, so the counts measure exposure to the toll as well as traffic. The MTA vehicle-miles series for the zone (`jbxx-kxff`) has no comparison area. It shows 2025 daily vehicle-miles 3.8% to 11.0% below the same months of 2024, depending on the measurement method.

The figure is `figures/mobility/crz_traffic_before_after.png`.

## Congestion pricing and air quality (mob-crz-air, mob-crz-air-nyccas): unsettled

Published studies of this question disagree. Stockholm's charge lowered ambient pollution by 5% to 15% (Simeonova et al. 2021). London's charge produced little measurable change (Kelly et al. 2011). For New York, Fraser et al. (2025, npj Clean Air) report that daily maximum PM2.5 in the zone was 22% below a modelled counterfactual in January to June 2025. The NYC Health Department's report of August 2026 found no significant difference in PM2.5, NO2, NO or black carbon in 2025.

The registered test used EPA AQS daily data (pre-generated files dated 25 June 2026). The primary NO2 test could not be run, because no AQS NO2 monitor operated in Manhattan in 2022-2025. The only in-zone PM2.5 monitor with data before 2025 is PS 19 in the East Village, which samples one day in three. A model with site and date effects gives −5.2% (−9.5 to −0.9) for PM2.5 at PS 19 relative to monitors in other boroughs. The result depends on the choice of comparison monitors. Against only the two comparison monitors that ran in every year (IS 52 in the Bronx and Queens College 2), on the same days, the difference between PS 19 and those monitors changed by −0.3%. The −5.2% estimate depends on five comparison monitors that began in mid-2023 or 2025.

The NO2 test was then re-registered on the NYC Community Air Survey (NYCCAS) annual averages by UHF42 neighbourhood. The new registration was committed before the 2025 values were read. NO2 in the five UHF neighbourhoods south of 60th Street changed by +0.9% relative to the 32 neighbourhoods outside Manhattan, comparing 2025 with 2021-24. To judge this, I drew 5,000 random sets of five neighbourhoods from the 32 comparison neighbourhoods, treated each set as if it were the zone, and computed the same estimate. The spread of those estimates gives a 95% interval of −2.2% to +4.2%, and 70% of them are lower than the zone's estimate. PM2.5 changed by +1.7%. The NYCCAS result agrees with the Health Department report, which used the same survey. The NYCCAS result rules out a fall in NO2 of the size seen in Stockholm but does not rule out a small one.

NYCCAS annual values are model outputs. A land-use regression with fixed traffic and building covariates spreads street-level measurements across the city, and this may pull a local change toward zero. Raw in-zone NYCCAS site measurements and a second year after the toll would settle the question. The city data show an effect of the toll on traffic but no detectable effect on annual air quality.

The figures are `figures/mobility/crz_air_pm25_before_after.png` and `figures/mobility/crz_air_nyccas_uhf42.png`.

## Air pollution and asthma (mob-asthma-pollution): unsettled

The graph holds many findings that link PM2.5 and NO2 to asthma emergency visits. Two meta-analyses give the size of the effect. Zheng et al. (2015) give short-term relative risks of 1.023 for PM2.5 and 1.018 for NO2. Khreis et al. (2017) give 1.05 per 4 µg/m³ NO2 for developing asthma, which is about 1.26 per 10 ppb.

The city test used 42 UHF neighbourhoods, with asthma ED visit rates for children aged 5 to 17 (SPARCS), NYCCAS annual NO2 and PM2.5, all averaged over 2017-19, and the percentage of residents below the poverty line in 2015-19. All four come from the EHDP repository at commit `547482b`. I did not use the EHDP indicator of asthma visits attributable to PM2.5, because it is computed from research concentration-response functions and would make the test circular.

The unadjusted rate ratio is 1.32 (0.65 to 2.65) per 10 ppb NO2. Adjusted for poverty it is 1.22 (0.81 to 1.85), close to the research value but with an interval that includes 1. Poverty alone gives 1.91 (1.62 to 2.25) per 10 percentage points and explains half the variation in log rates; NO2 alone explains 2%. The registered prediction was wrong about the mechanism: it expected poverty to carry most of the NO2 association, so that adjustment would halve it. NO2 and poverty are almost uncorrelated across UHF neighbourhoods (r = 0.05), so poverty does not confound the NO2 association here. NO2 and PM2.5 are highest in midtown and lower Manhattan, where child asthma visits are rare. Asthma visits are highest in the South Bronx and Harlem, where pollution is middling and poverty is high.

A cross-section of 42 neighbourhoods cannot detect an effect of the size the research reports, because the variation in asthma rates that tracks poverty is much larger. A case-crossover analysis of daily asthma visits by neighbourhood against daily concentrations would settle it, because each neighbourhood would serve as its own control.

The figure `figures/mobility/asthma_pollution_uhf42.png` plots each neighbourhood against NO2 and PM2.5, coloured by poverty, with the research slope drawn through the city mean.

## Speed cameras around the clock (mob-speedcam-247): unsettled

From 1 August 2022, NYC's school-zone speed cameras ran 24 hours a day, 7 days a week. Before that they ran on weekdays from 6 am to 10 pm. The design compares crashes in the newly enforced hours (weekday nights and weekends) with crashes in the hours that were already enforced. The comparison covers August 2021 to July 2023 and uses NYPD crash records (`h9gi-nx95`) aggregated by month and hour group.

The camera tickets confirm that the policy took effect. In July 2022 no school-zone speed tickets were issued between 10 pm and 6 am; in September 2022, 24% of the 646,589 tickets were issued in those hours (`nc67-uf89`). Injury crashes in the new hours fell relative to the old hours by a ratio of 0.934 (0.860 to 1.014). The count of persons injured gives 0.920 (0.846 to 1.001). A false start a year earlier gives 0.981. The estimate lies in the registered range, but its interval includes no change.

The share of injury crashes in the new hours was 37.7% in 2019, about 40% during the pandemic years, and 38.3% in the year after the change. The decline after August 2022 therefore looks like a return to the 2019 pattern, and the design cannot separate it from a camera effect. Cameras cover a small share of the city's streets, so a local effect of the size NYC DOT reports (7.6% fewer injuries in the new hours at camera sites) would be too small to resolve citywide. Camera locations and hourly traffic volumes would settle it, and neither is published as open data.

The figure is `figures/mobility/speedcam_247_new_vs_old_hours.png`.

## Active commuting and obesity (mob-active-commute-obesity): confirmed in sign, unsettled as a cause

Across the 42 UHF neighbourhoods, a 10-point higher share of workers who walk or cycle to work (ACS 2015-19) goes with 6.0 (4.1 to 7.8) points less adult obesity (Community Health Survey 2017-19), after adjusting for poverty. The verdict rule gives "confirmed", because the interval excludes zero in the predicted direction. The size is not plausible as an effect of commuting. Flint et al. (2014) found that active commuters have a BMI about 1 kg/m² lower than car commuters. On that basis, shifting 10% of workers to walking or cycling would lower neighbourhood obesity by well under one percentage point. The neighbourhood slope mostly reflects who lives where walking to work is possible. Residents of these neighbourhoods differ in income among people above the poverty line, in education, in age and in other characteristics that the poverty rate does not capture. Outside Manhattan the slope is steeper still, −11.6 points per 10.

The challenge defines a bridge as a link that no single dataset holds but several do together. This claim meets that definition only for the direction of the association, not its size. The research links physical activity to obesity, and the city data link commute mode to obesity across neighbourhoods. Neither source alone, nor the two together, shows that changing how people commute changes their weight. A before-and-after design would settle it, comparing obesity in neighbourhoods before and after the bicycle network or Citi Bike reached them.

The figure is `figures/mobility/active_commute_obesity_uhf42.png`.

## Research needed

The outcome files list the items in full. The main ones are these:

- The graph lacks the road-pricing literature (Stockholm, London, Milan, Singapore and now New York). It has no concept for cycling or active commuting, and its speed camera evidence comes from six studies.
- In-zone NO2 measured at fixed sites, with a period before the toll, is not public. The NYCCAS site data would answer the congestion pricing air question more directly than modelled annual averages.
- The two published New York studies (Fraser et al. 2025; NYC DOHMH 2026) reach different conclusions about PM2.5. A re-analysis on common data, comparing daily maximum with daily mean and the two monitor sets, would reconcile them.
- Daily asthma ED visits by neighbourhood would allow a within-neighbourhood test of the pollution and asthma link.
- Speed camera locations and activation dates as open data would allow a site-level test.

## Data versions

Every outcome file lists its sources with versions. NYC Open Data and data.ny.gov records carry the dataset id, its `rowsUpdatedAt` time, the exact SoQL and the fetch time. EPA AQS files are the pre-generated daily files dated 25 June 2026, downloaded to `~/opt/nyc-concordance/aqs/` and cited by URL. EHDP files come from github.com/nychealth/EHDP-data at commit `547482b9df589006543e13e8cdf6546e00ed9998`.
