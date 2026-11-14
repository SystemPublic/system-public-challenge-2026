# Heat: shootings, heat illness and street trees

This note reports three questions about heat in New York City. For each, the published evidence comes from the System Public Graph, a knowledge graph of findings extracted from papers (API v1.0, Dataverse v2.1), and from papers read in PubMed. The city side comes from NYC Open Data, the Health Department's Environment and Health Data Portal (EHDP) and NOAA. Each hypothesis, with its predicted direction and size, was written down and committed to the repository (registered) before the city data that test it were queried. A claim is confirmed when the city estimate has the predicted sign and its 95% interval excludes zero, contested when it has the opposite sign and its interval excludes zero, and unsettled when its interval includes zero. A bridge is a chain of links that no single source holds. The registrations are in `claims/registered/heat-*.json` and the outcomes in `claims/outcomes/heat-*.json`. The scripts in `analyses/heat/` rebuild every number here from a clean cache.

## What the graph holds on heat

The graph holds more on heat and mortality than on heat and violence or heat and trees. Thermodynamic temperature and mortality rate share 40 findings from 16 studies, and extreme heat and mortality rate share 25 findings from 14 studies. Extreme heat links to emergency visits for heat illness through two studies. The larger is Sun et al. (2021, BMJ, PMID 34819309), which found 66.3% (60.2 to 72.7) more ED visits for heat-related illness on days at the local 95th percentile of warm-season temperature than on reference days (34.4 C against 14.9 C at the national average).

The graph has no relationship between gun violence and any temperature concept. The concepts for violence, crime, aggression and violent crime have none either. The only heat-violence evidence is temperature and homicide (4 findings, 2 studies) and temperature and injury (4 findings, 3 studies). One of the injury studies is from New York: Girma et al. (2023, PMID 37448837) found that intentional-injury ED visits among 20 to 25 year olds had an odds ratio of 1.54 (1.28 to 1.85) on warm-season days with a minimum of 77 F compared with 48 F.

Three of the homicide findings are mis-extracted. Xu et al. (2020, PMID 32738768) reported an 8.8% increase in intentional homicide per 5 C in New York and 9.5% in Chicago; the graph stores these as odds ratios of 0.088 and 0.095, which reverses their meaning. The Xu rows are absent from the Dataverse CSV, so the graph's quality filter removes them. Rahman et al. (2023, PMID 36858215) reported 4.9% and 6.2% increases in homicide per 5 C; the graph stores them as odds ratios of 4.9 and 6.2, and these rows are present in the CSV, so they remain in filtered queries.

The tree concept has no relationships. Green space has 14, none of them with temperature, heat illness or emergency care. The only vegetation-temperature finding is a correlation stored as r = -1.0 between NDVI (a satellite measure of greenness) and land surface temperature, attributed to Hasan et al. (2022, PMID 35060045), a study of one city in Bangladesh. The abstract reports a strong negative correlation but gives no number, so the value -1.0 is not from the source, and the row is absent from the Dataverse CSV, so the claims below use it for direction only. No finding in the graph connects trees or green space to heat-related ED visits. The chain from trees to ED visits therefore has to be assembled from city data and from papers outside the graph.

## Heat and shootings (heat-shootings, confirmed)

The registered hypothesis was that daily shooting incidents rise with the daily maximum temperature in Central Park by 5 to 20 percent per 5 C, comparing days within the same month and year. The data were the NYPD shooting incidents in `5ucz-vwe8` (one row per incident, updated 5 November 2026), counted by day from 1 January 2006 to 31 August 2026: 24,429 incidents on 7,548 days. The archived file `833y-fsy8` agrees with it to within two incidents for 2006 to 2024. Temperature and rain came from GHCN-Daily station USW00094728. The model was a negative binomial regression with terms for day of week, month, year, holidays and rain.

The incidence rate ratio was 1.146 per 5 C (95% CI 1.130 to 1.163). Six pre-registered sensitivity analyses gave rate ratios between 1.11 and 1.17. They used a two-day mean of temperature, the daily minimum, the warm season only, the years 2006 to 2019, the years 2020 to 2026, and murder incidents alone (1.115, 1.079 to 1.151). Shootings rose after 2020 and then fell, but the estimate was about the same for 2006 to 2019 (1.144) as for 2020 to 2026 (1.148).

The NYC estimate lies between the published homicide estimates and the published shooting estimate. Per 5 C, homicide rose by a factor of 1.088 (1.015 to 1.166) in New York in Xu et al. (2020) and 1.049 (1.016 to 1.081) in California in Rahman et al. (2023). Shootings in Chicago rose by 1.158 on weekdays and 1.190 on weekends in Reeping and Hemenway (2020, Injury Epidemiology), converted from their 34.0% and 41.6% per 10 C.

The rate ratio fell in the registered range, but the curve did not have the registered shape: the fitted curve keeps rising up to 35 C, where the registration predicted it would level off near the 85th to 95th percentile of temperature. At the 84th percentile of daily maximum (28.3 C) the rate ratio compared with the median day (18.3 C) is 1.42 (1.36 to 1.48). Lyons et al. (2022, JAMA Network Open) pooled 100 cities and found 1.17 (1.12 to 1.21) for the same contrast. The two numbers are not fully comparable, because the NYC model holds month fixed and Lyons et al. used a distributed-lag model, but the NYC slope is steeper than the 100-city average. Fitting the Lyons model to the NYPD series would show whether the difference is real.

Figure: `figures/heat/heat_shootings_curve.png`.

## Heat and emergency visits for heat illness (heat-ed-syndromic, confirmed)

The Health Department's syndromic surveillance covers every ED in the city, and the Department publishes daily counts of heat-syndrome ED visits from it in the `key-topics/heat-syndrome` folder of the `nychealth/EHDP-data` repository. This analysis used commit 547482b. The series covers May to September of 2017 to 2026: 7,620 visits on 1,522 days. No heat or syndromic dataset was found on NYC Open Data. Heat deaths are published only as yearly citywide counts (EHDP indicator 2074).

With the same model as for shootings, restricted to the warm season, the rate ratio was 4.09 per 5 C (3.76 to 4.45). The curve is nearly flat below 27 C and steep above it. At the warm-season 95th percentile (33.3 C) the rate ratio compared with the median (26.7 C) is 11.2 (10.0 to 12.5). The registered prediction (1.5 to 5 per 5 C, and above 3 at the 95th percentile) was met.

The national estimate of Sun et al., 1.66 for the local 95th percentile against a cooler reference day, is much smaller. The two are measured differently. The NYC series counts chief complaints that mention heat and is near zero on mild days, while Sun et al. counted diagnosis codes among insured adults in 2,939 counties with a national reference temperature. The size of the NYC excess therefore cannot be compared directly with the literature.

The registered yearly check found only a weak association. Yearly heat ED visits from hospital discharge data (EHDP indicator 2075, 2005 to 2022) had a Spearman correlation of 0.36 (p = 0.15) with the number of days at or above 90 F. With days at or above 95 F, an unregistered choice, the correlation was 0.84; for heat deaths it was 0.78. Years with many very hot days have many visits and deaths, but the number of 90 F days predicts them poorly. The syndromic counts rose in 2025 and 2026 although those summers had few 90 F days, which may reflect changes in how heat visits are detected or recorded rather than more illness.

Figure: `figures/heat/heat_ed_curve.png`.

## Street trees, temperature and heat illness (bridge)

The example chain posed by the hackathon challenge runs from more street trees, to lower neighbourhood temperature, to fewer heat-related ED visits. No single dataset holds it, and the graph holds none of its links. It was registered as two links and a composed chain across the 59 community districts (55 have every covariate; two more lack a published ED rate because counts are small), with a neighbourhood-level (NTA) replication, and with a street-level check from the hyperlocal temperature sensors.

The data were live trees in the 2015 Street Tree Census (`uvpi-gqnh`) per square kilometre of land; daytime summer surface temperature from a single Landsat satellite image taken on the afternoon of 17 July 2018 (EHDP indicator 2141); the five-year age-adjusted rate of heat-stress ED visits (EHDP indicator 2443, from SPARCS discharge data); and poverty, percent Black residents and household air conditioning from the Heat Vulnerability Index file. The Heat Vulnerability Index itself was not used as an outcome, because it is built from surface temperature and green space, so it would be correlated with trees by construction.

### Link a: street trees and surface temperature (heat-trees-surftemp, unsettled)

The prediction was that districts with more street trees per square kilometre have cooler surfaces. The adjusted slope went the other way: +0.50 F per standard deviation of log tree density (-0.03 to +1.04, 55 districts). Across 194 neighbourhoods it was +0.44 F (+0.15 to +0.73). Vegetative cover, which counts grass and all trees, had the predicted sign: -0.62 F per standard deviation (-1.17 to -0.07).

The likely reason is that street-tree density measures the density of the street grid as much as it measures shade. Dense street grids in Manhattan, Brooklyn and the Bronx have many street trees per square kilometre and also hot roofs and pavement. Staten Island has the fewest street trees per square kilometre (697, against about 1,000 elsewhere) and the coolest surfaces, because of its parks, yards and wetlands, which street-tree counts do not include. A test of whether street trees cool surfaces would need canopy measured from LiDAR at block level, with impervious cover and building height held fixed.

### Link a at street level: trees and air temperature at the sensors (heat-trees-airtemp-hyperlocal)

The prediction was that, within the same neighbourhood on the same day, sensors with more street trees nearby record lower afternoon air temperature. The Hyperlocal Temperature Monitoring data (`qdq3-9eqn`) cover 420 sensors in 23 neighbourhoods of Brooklyn, the Bronx, Manhattan and Queens in the summers of 2018 and 2019. The analysis compared sensors only with other sensors in the same neighbourhood on the same day (86,451 sensor-days), with the mounting type held fixed and standard errors clustered by sensor.

The slope was -0.05 C per 10 live street trees within 50 m (-0.16 to +0.07), and -0.01 C per 10 trees within 100 m (-0.05 to +0.03). The registered range was -0.05 to -0.5 C. The point estimate is at the weak end of that range and its interval includes zero, so the link is unsettled. One unregistered contrast is larger: sensors on light poles read 1.26 C warmer in the afternoon than sensors mounted in street trees in the same neighbourhood on the same day. This may show the shade of the tree the sensor hangs in, or a difference in mounting height and exposure; the data cannot separate the two.

### Link b: surface temperature and heat ED visits (heat-surftemp-ed, contested)

The prediction was that hotter districts have higher heat ED rates. The adjusted slope was negative: -10.3% per 1 F (-17.5% to -2.6%, 54 districts), adjusted for poverty, percent Black residents and air conditioning. Heat hospitalization rates across 194 neighbourhoods gave the same sign (-3.9%, -7.2% to -0.4%). The highest district rates are in Bedford-Stuyvesant (23.9 per 100,000 a year), East Harlem (23.2) and the Rockaways (21.8), and Staten Island has the highest borough average (15.0) with the coolest surfaces. Several central districts with hot surfaces have low rates. Without Staten Island (an exploratory check, not registered) the slope is -8% (-16% to +0.3%).

Percent Black residents was the strongest adjusted predictor of heat ED rates: +10.9% per 10 percentage points (+1.4% to +21.2%). Race here most likely marks conditions that were not measured, such as housing quality, access to care and exposure at work. Poverty, once race and air conditioning were in the model, was not distinguishable from zero. These associations describe districts, not individuals.

### The composed chain (heat-trees-ed-chain, contested)

The composed indirect effect, trees to surface temperature to ED rate, was -3.7% per standard deviation of tree density (bootstrap interval -10.3% to +1.3%). The negative sign matches the prediction only by accident: each link has the opposite sign to the one predicted, and two reversed signs multiply to a negative. The registered rule says the chain is contested if either link is contested, and link b is. Street-tree density does have a negative total association with the heat ED rate (-19.9% per standard deviation, -31.4% to -6.6%, adjusted), but it does not run through surface temperature.

Figure: `figures/heat/heat_bridge_chain.png` shows each link's estimate and interval.

### What the chain cannot separate, and what would

Income and race shape where trees were planted, how buildings are built, who has air conditioning, and who goes to an emergency department. Building density and impervious cover affect both street-tree counts and surface temperature. With 54 districts and these correlated traits, no adjustment can separate them, and an association between areas need not hold for the people in them.

Three designs would settle the chain. The first uses variation within a neighbourhood: canopy by block and heat illness by residence, from individual records held by the Health Department. The second uses the timing of MillionTreesNYC plantings (2007 to 2015) as a natural experiment. The Forestry Tree Points dataset (`hn5i-inap`) records a planting date for each tree, so blocks planted early can be compared with blocks planted late, with the caveat that the programme targeted vulnerable neighbourhoods. The third is a daily case-crossover of heat ED visits by ZIP code, with canopy as an effect modifier, which compares each area with itself on hot and cool days and removes fixed differences between areas.

## Summary of claims

| Claim | Kind | Verdict | City estimate |
|---|---|---|---|
| heat-shootings | confirmation | confirmed | IRR 1.146 per 5 C (1.130 to 1.163) |
| heat-ed-syndromic | confirmation | confirmed | IRR 4.09 per 5 C (3.76 to 4.45) |
| heat-trees-surftemp | bridge link | unsettled | +0.50 F per SD trees (-0.03 to +1.04) |
| heat-trees-airtemp-hyperlocal | bridge link | unsettled | -0.05 C per 10 trees within 50 m (-0.16 to +0.07) |
| heat-surftemp-ed | bridge link | contested | -10.3% per 1 F (-17.5 to -2.6) |
| heat-trees-ed-chain | bridge | contested | -3.7% per SD trees (-10.3 to +1.3) |

## Research needed

- A daily series of heat-illness ED visits by ZIP code or neighbourhood (held by the Health Department) would allow a case-crossover design with canopy and air conditioning as effect modifiers.
- Block-level LiDAR canopy, impervious cover and building height would allow a test of whether street trees cool surfaces and air once the street grid is held fixed.
- The planting dates in Forestry Tree Points, linked to later heat ED visits, would allow a staggered difference-in-differences design for MillionTreesNYC.
- For shootings, hourly counts by location type and data on time spent outdoors would show whether temperature works through street activity.
- The graph lacks the urban-heat literature on trees and heat morbidity (for example Ziter et al. 2019, PNAS; Madrigano et al. 2015, EHP) and should flag its mis-extracted temperature-homicide rows.

## Sources

- NYPD Shooting Incident Data: `5ucz-vwe8` (2006 to present) and `833y-fsy8` (archived, to 2024), NYC Open Data.
- 2015 Street Tree Census `uvpi-gqnh`; Hyperlocal Temperature Monitoring `qdq3-9eqn`, NYC Open Data.
- NOAA GHCN-Daily, Central Park USW00094728, doi:10.7289/V5D21VHZ.
- NYC DOHMH, EHDP-data repository (github.com/nychealth/EHDP-data, commit 547482b9df589006543e13e8cdf6546e00ed9998): heat-syndrome daily files; indicators 2074, 2075, 2141, 2143, 2410, 2443; hvi-nta.csv; CD and NTA2010 geography.
- System Public Graph API v1.0 and Dataverse v2.1 (doi:10.7910/DVN/7V6JDO): `data/derived/heat/graph_evidence.json`, `data/derived/heat/graph_audit_heat.json`; abstracts in `data/derived/heat/abstracts_graph.txt`.
- Reeping PM, Hemenway D (2020), Injury Epidemiology 7:31, doi:10.1186/s40621-020-00260-3. Lyons VH et al. (2022), JAMA Network Open 5:e2247207, doi:10.1001/jamanetworkopen.2022.47207. Xu R et al. (2020), Environment International 143:105992. Rahman MM et al. (2023), Science of the Total Environment 874:162462. Sun S et al. (2021), BMJ 375:e065653. Madrigano J et al. (2015), EHP 123:672-678. Ziter CD et al. (2019), PNAS 116:7575-7580.

## Vegetation from aerial imagery at the sensors (heat-trees-canopy-within-nta, confirmed)

This section was added on 12 November 2026 and re-tests the street-level link with a different measure of exposure. The earlier test counted street trees within 50 m of each sensor and was unsettled. This test measures the share of ground within 50 m that is covered by green vegetation, from the 2022 flight of the USDA National Agriculture Imagery Program (NAIP), which records red and near-infrared light at 0.6 m per pixel. A pixel counts as vegetation when its NDVI, (near infrared - red) / (near infrared + red), is above 0.2.

The afternoon temperatures of these sensors had already been used by the earlier claim, and its result was known when this claim was registered. The vegetation values at the sensors had not been read. The registration (`claims/registered/heat-trees-canopy-within-nta.json`) states this, and was committed and pushed to the branch `prereg/heat-trees-canopy-within-nta` before any NAIP pixel at a sensor was fetched. The research side is Ziter et al. (2019), who measured air temperature from a bicycle in Madison, Wisconsin, and found more than 1.5 C of daytime cooling from no canopy to full canopy within 60 to 90 m, with most of it above 40% canopy. The System graph holds no finding on vegetation and air temperature; the cached evidence was used, because the API key was not on the machine, and a live lookup is pending. The registered prediction was a slope of -0.02 to -0.25 C per 10 percentage points of vegetation share.

The model compared sensors only with other sensors in the same neighbourhood on the same day and under the same flight date, with the mount type held fixed and standard errors clustered by sensor. It used 420 sensors and 86,451 sensor-days. Of the 423 sensors with imagery, 354 lie under tiles flown on 19 July 2022 and 69 under tiles flown on 15 September 2022. The vegetation share within 50 m has a mean of 22.5% and a standard deviation of 12.7 points within a neighbourhood. Twelve percent of sensors have 40% or more.

The slope was -0.20 C per 10 percentage points (95% interval -0.25 to -0.15), inside the registered range. The three registered support conditions hold, so the verdict is confirmed. The 19 July tiles alone give -0.21 (-0.26 to -0.16) and the 15 September tiles -0.15 (-0.25 to -0.04). The share within 100 m gives -0.28 (-0.35 to -0.22). Mean NDVI within 50 m, in place of the thresholded share, gives -0.42 C per 0.1 of NDVI (-0.52 to -0.32). Sensors mounted in street trees and sensors on light poles give the same slope, -0.21, with intervals of -0.25 to -0.17 and -0.36 to -0.06. On days when Central Park reached 30 C the slope is -0.24 (-0.29 to -0.18). At night (00 to 05 h) it is -0.07 (-0.09 to -0.05), smaller than in the afternoon as predicted, and slightly larger in size than the registered night range of 0 to -0.06.

The slope is not linear. Against sensors with under 10% vegetation, sensors with 10 to 20% read 0.08 C cooler (interval -0.26 to +0.10), those with 20 to 30% read 0.22 C cooler, those with 30 to 40% read 0.36 C cooler, and those with 40% or more read 0.82 C cooler (-1.10 to -0.54). This description was planned but does not decide the verdict. It agrees with the threshold near 40% that Ziter et al. and Alonzo et al. (2021) reported.

The placebo was not null. The vegetation share of the ring 200 to 300 m from the sensor, which lies beyond the 90 m scale at which Ziter et al. found the largest effect, has a slope of -0.35 (-0.45 to -0.25) on its own. With both measures in the model, the ring has -0.24 (-0.34 to -0.15) and the 50 m share has -0.17 (-0.22 to -0.13). The local slope remains, which is what the registered condition required. The ring result means that greener parts of a neighbourhood are cooler over distances of several hundred metres. Vegetation may cool the air at that distance, for example downwind of a park, or greener blocks may differ in building height, street width and traffic. The data do not separate these, so the result is an association within neighbourhoods and is not an estimate of what planting within 50 m would do.

The count of street trees does not measure the same thing as the vegetation share. Across sensors the two have a correlation of -0.10 within 50 m. With both in the model the vegetation slope is unchanged at -0.20 and the tree count has -0.03 C per 10 trees (-0.13 to +0.07). This is the likely reason that the earlier test found little: a count gives a sapling and a mature tree the same weight and leaves out yards and parks.

Four limits were stated in the registration. The imagery is from 2022 and the temperatures from 2018 and 2019. NAIP values are not calibrated, so the 0.2 threshold is a convention and the two flight dates were never compared with each other. NDVI counts grass and shrubs with tree canopy. The sensors were placed in 23 neighbourhoods with high heat vulnerability, on trees and poles, and not at random. The city's 2017 LiDAR land cover would separate canopy from grass and is closer in time to the sensors. A model by distance rings with building height held fixed would show how far the association reaches.

Figure: `figures/heat/heat_canopy_naip.png`. Script: `analyses/heat/canopy_naip.py`. Sources: Hyperlocal Temperature Monitoring `qdq3-9eqn` (rows updated 20 August 2021), NYC Open Data; USDA Farm Service Agency, NAIP 2022, New York tiles of 19 July and 15 September 2022, read from the Microsoft Planetary Computer (tile ids in `data/derived/heat/canopy_naip_source.json`); NOAA GHCN-Daily, Central Park USW00094728; Ziter CD et al. (2019), PNAS 116:7575-7580, doi:10.1073/pnas.1817561116; Alonzo M et al. (2021), Environmental Research Letters 16:084028, doi:10.1088/1748-9326/ac12f2.
