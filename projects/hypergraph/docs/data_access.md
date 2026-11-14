# Data behind the cited literature

The registrations in `claims/registered/` cite 47 literature entries. After merging entries that name the same work (Reeping and Hemenway 2020, the Furman Center housing-stock note, the Census New Residential Construction methodology and the DOHMH congestion-pricing report each appear twice), there are 43 distinct items. For each one we looked up the paper or report, using the abstract, the methods section where it could be reached, and the publisher or agency page, and recorded what data it rests on, whether those data can be obtained today, and whether the headline number could be recomputed from open data. The full records, with notes on each access judgement, are in `data/derived/data_access/literature.json`. No registration was changed and no NYC data were queried.

Access is classed as open when anyone can download or query the data, partly open when aggregates are open but microdata are restricted or when free registration is required, restricted when the data are licensed, proprietary or held under a data use agreement, and unknown when the paper does not say or its methods could not be read. Where a source could not be confirmed, the item is marked unknown and the note says why. A meta-analysis is classed as open because its inputs are the published study estimates, which are tabulated in the paper; the primary studies' own data are not.

## Counts

Of the 43 items, 29 are peer-reviewed academic papers, 8 are government reports or data products, and 6 are grey literature (a TØI institute report, a doctoral thesis, an HEI research report, an NBER working paper, the Furman Center and Schaller Consulting). Eighteen items are about New York City and 25 are about other places: Chicago, California, Rhode Island, Texas, Philadelphia, Madison, London, Stockholm, the United Kingdom as a whole, the United States as a whole, or the international literature.

By data access, 19 items are open, 8 partly open, 9 restricted and 7 unknown. Ten of the 19 open items are about NYC, and five of the 19 are meta-analyses or systematic reviews whose openness consists of published estimates. Among the 29 academic papers, 10 rest on open data (5 of them meta-analyses), 5 on partly open data, 8 on restricted data and 6 are unknown. Code is reported as available for only 2 items (the DOHMH Heat Vulnerability Index repository and the SONYC project); for 24 it is not available and for 17 we could not tell.

A team could recompute the headline number from open data today for 9 items, could do so with substantial effort or with substitute open sources for 17, and could not for 17. Eight of the 9 recomputable items are about NYC, and all 8 are either agency figures (DCP, DOB, the HVI, the State Comptroller) or analyses of 311 and DOB records.

## Summary table

| Item | Kind | NYC | Main data | Access | Recompute | Claims |
|---|---|---|---|---|---|---|
| Elvik 2009 | grey | no | meta-analysis of speed-change studies | open | with effort | bridge-crz-crash-link, bridge-crz-injury-crashes, bridge-crz-injury-crashes-v2 |
| Nilsson 2004 | grey | no | Swedish before-after studies of speed-limit changes and national accident statistics | unknown | no | bridge-crz-crash-link, bridge-crz-injury-crashes, bridge-crz-injury-crashes-v2 |
| Elvik 2013 | academic | no | Re-analysis of the study estimates assembled for the 2009 Power Model meta-analysis | open | with effort | bridge-crz-crash-link, bridge-crz-injury-crashes, bridge-crz-injury-crashes-v2 |
| Green 2016 | academic | no | STATS19 police-reported road accident records | open | with effort | bridge-crz-crash-link, bridge-crz-injury-crashes, bridge-crz-injury-crashes-v2 |
| Reeping 2020 | academic | no | Daily counts of shooting victims from the Chicago Tribune crime-tracking website | unknown | with effort | bridge-heat-shootings-ems, heat-shootings |
| Lyons 2022 | academic | no | Gun Violence Archive incident records | partly open | with effort | heat-shootings |
| Xu 2020 | academic | yes | Daily intentional homicide counts from city crime records and daily weather | unknown | with effort | heat-shootings |
| Rahman 2023 | academic | no | California death certificates with residential address | restricted | no | heat-shootings |
| Barajas 2021 | academic | no | City of Chicago Transportation Network Providers trip records | open | with effort | commute-fhv-subway-distance |
| Schaller / TLC fact books | grey | yes | NYC TLC trip records and TLC fact books, summarised by Schaller Consulting | open | yes | commute-fhv-subway-distance |
| Hoehner 2012 | academic | no | Cooper Center Longitudinal Study geocoded to work and home addresses | restricted | no | commute-time-depression |
| Christian 2012 | academic | no | American Time Use Survey respondent diaries | open | yes | commute-time-depression |
| NYC DCP 2022 brief | government | yes | DOB new-building permit filings and DCP Housing Database | open | yes | construction-2022-rush-units-2027, construction-aerial-triangulation, construction-four-year-completion |
| NYU Furman Center 2019 | grey | yes | DOB new-building permits and certificates of occupancy, via Furman Center CoreData | open | yes | construction-2022-rush-units-2027, construction-aerial-triangulation, construction-four-year-completion, construction-permit-funnel |
| Census NRC methodology | government | no | Building Permits Survey and Survey of Construction | partly open | no | construction-four-year-completion, construction-permit-funnel, construction2-rows-per-job-dobnow, construction2-rows-per-job-legacy-2000s |
| NYC DOB Get Sheds Down 2023 | government | yes | DOB sidewalk shed permits | open | yes | construction-sheds-outnumber-nb |
| Sun 2021 | academic | no | OptumLabs Data Warehouse claims | restricted | no | heat-ed-syndromic, heat-surftemp-ed, heat-trees-ed-chain |
| Kingsley 2016 | academic | no | Rhode Island Department of Health hospital ED visit and death records | restricted | no | heat-ed-syndromic |
| Madrigano 2000 | academic | yes | NYC DOHMH vital-statistics death records | restricted | no | heat-surftemp-ed, heat-trees-ed-chain, heat-trees-surftemp |
| NYC DOHMH Heat Vulnerability Index | government | yes | Surface temperature, green space, household air conditioning, ACS poverty/income and race | open | yes | heat-surftemp-ed, heat-trees-ed-chain |
| Ziter 2019 | academic | no | Own bicycle-mounted air-temperature transects | unknown | no | heat-trees-airtemp-hyperlocal, heat-trees-ed-chain, heat-trees-surftemp |
| Flint 2014 | academic | no | Understanding Society with nurse-measured BMI and body fat | partly open | with effort | mob-active-commute-obesity |
| Celis-Morales 2017 | academic | no | UK Biobank cohort linked to hospital and death records | restricted | no | mob-active-commute-obesity |
| Zheng 2015 | academic | no | Meta-analysis of 87 published time-series studies of asthma ED visits and admissions | open | with effort | mob-asthma-pollution |
| Khreis 2017 | academic | no | Systematic review and meta-analysis of 41 studies of traffic-related pollution and childhood asthma incidence | open | with effort | mob-asthma-pollution |
| Johansson 2009 | academic | no | Emission and dispersion modelling with SLB-analys monitoring and Stockholm traffic counts | unknown | no | mob-crz-air, mob-crz-air-nyccas |
| Kelly 2011 | grey | no | London Air Quality Network monitoring and modelled emissions | open | with effort | mob-crz-air, mob-crz-air-nyccas |
| Simeonova 2021 | academic | no | Swedish national patient registers linked to population registers | restricted | no | mob-crz-air, mob-crz-air-nyccas |
| Fraser 2025 | academic | yes | Daily PM2.5 from 42 regulatory and other monitors, traffic, meteorology and neighbourhood demographics | unknown | with effort | mob-crz-air, mob-crz-air-nyccas |
| NYC DOHMH 2026 CRZ air report | government | yes | NYCCAS integrated and real-time monitors, EPA AQS sites, periodic highway traffic counts | partly open | with effort | mob-crz-air, mob-crz-air-nyccas, mob-crz-traffic |
| Eliasson 2009 | academic | no | City of Stockholm cordon traffic counts and travel-time measurements | unknown | no | mob-crz-traffic |
| TfL 2007 monitoring report | government | no | TfL traffic counts, journey-time surveys and congestion monitoring | partly open | no | mob-crz-traffic |
| Cook 2025 | grey | yes | Google Maps Traffic Trends road-segment speeds, generalized synthetic control | restricted | no | mob-crz-traffic |
| Wilson 2010 | academic | no | Cochrane systematic review of 35 published camera evaluations | open | with effort | mob-speedcam-247 |
| NYC DOT speed camera reports | government | yes | DOT speed-camera locations and violations | open | with effort | mob-speedcam-247 |
| Legewie 2016 | academic | yes | NYC 311 service requests | open | yes | nbhd-noise311-exposure |
| Kontokosta 2021 | academic | yes | NYC 311 service requests | open | yes | nbhd-noise311-exposure |
| Boxer et al. 2025 (AoAS) | academic | yes | NYC 311 heat/hot water complaints | open | with effort | nbhd-noise311-exposure |
| Zheng 2014 | academic | yes | NYC 311 noise complaints | partly open | with effort | nbhd-noise311-exposure |
| Bello 2019 | academic | yes | Own SONYC acoustic sensor network | partly open | no | nbhd-noise311-exposure |
| NYS Comptroller 2018 | government | yes | NYC 311 noise complaints | open | yes | nbhd-noise311-exposure |
| Olmedo 2011 | academic | yes | NYC Neighborhood Asthma and Allergy Study: home dust allergen samples and child IgE sensitisation | restricted | no | nbhd-rodents-asthma |
| Branas 2018 | academic | no | Philadelphia Police Department crime reports around 541 randomised vacant lots | partly open | no | nbhd-vacant-shootings |

## Items that differ from what the citation suggests

Reeping and Hemenway (2020), the anchor for both heat-and-shootings claims, did not use Chicago Police Department data. Their daily shooting counts came from the Chicago Tribune's crime-tracking website and their weather from Weather Underground, neither of which is a deposited dataset. Chicago's open shooting-victim data and NOAA station records could stand in for them, but the original counts cannot be retrieved as published.

Sun et al. (2021), cited by three heat and emergency-department claims, rests on the OptumLabs Data Warehouse, a proprietary claims database, and the paper states that no additional data are available. The NYC syndromic surveillance series the project uses is therefore a different kind of measurement, not a replication of the same data.

Cook et al. (NBER working paper 33584), cited for congestion-pricing traffic effects, uses Google Maps Traffic Trends speeds obtained through Google co-authors. Its headline speed gain cannot be recomputed from any open source. The registration's citation lacks the title and number; the NBER page gives two titles for the same paper ("The Short-Run Effects of Congestion Pricing in New York City" and "The Network-Wide Effects of Congestion Pricing: Evidence from New York City").

The DOHMH congestion-pricing air-quality report (August 2026) is a city report about NYC, but its monitor series are not on the open portal; the report says the air-quality data are available by contacting NYCCAS. The roughly 10 percent fall in traffic it mentions is given without a source on the report page.

The Annals of Applied Statistics paper cited without authors as "Estimating reporting bias in 311 complaint data" is by Boxer, Hong, Kontokosta and Neill (2025). It models under-reporting of heat and hot-water complaints, not noise complaints, so it supports the general point about 311 reporting bias rather than the noise claim directly.

The Branas et al. (2018) vacant-lot trial uses Philadelphia police data, which the city publishes, but the list of 541 randomised lots and their assignments is not public, so the trial effect cannot be recomputed from open data.

## What this means for the challenge

Most of the external benchmarks against which the NYC claims are compared cannot themselves be recomputed. Of the 25 items about other places, one (Christian 2012, from the American Time Use Survey) could be recomputed directly from open data, 11 could be recomputed with effort or substitute sources, and 13 could not be recomputed at all because they rest on health records, insurance claims, cohort studies or proprietary traffic data. The effect sizes the registrations take from this literature, such as the heat-to-ED elasticities, the heat-to-shootings rate ratios and the congestion-charge traffic reductions, therefore have to be accepted as published. A disagreement between a NYC result and one of them cannot be traced to a difference in data handling, because the comparison data are not available to inspect. Of the 18 NYC items, 14 can be recomputed, 8 of them directly, because they rest on 311, DOB, DCP, TLC and DOHMH portal data. This suggests that the more checkable claims are those that compare one NYC source with another, and that claims anchored on a restricted outside study should state that the anchor is taken on trust.
