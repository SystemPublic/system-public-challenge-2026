"""Register the three consequence tests. Run once, before any outcome data for the test periods are queried."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from concord import claims

WHO = "Claude (round 2, re-timed consequences agent), for Jeff Vernon"
DOSE = ("Exposure comes from the dose map only (data/derived/transit/dose_map_long.csv, built from MTA hourly entries before any "
        "outcome was queried). For a group of station complexes, E = ln(MF/TWT in Nov 2025-Oct 2026) - ln(MF/TWT in 2019), where MF is "
        "mean Monday and Friday entries and TWT mean Tuesday-to-Thursday entries, for 06:00-19:59 unless the AM peak (06:00-09:59) is named. "
        "E is negative where Mondays and Fridays thinned. Files: data/derived/round2/retimed_consequences/exposure_taxi_zone.csv, "
        "exposure_community_district.csv, exposure_groups.json; code analyses/round2/retimed_consequences/exposure.py.")
EST = ("Estimator (analyses/round2/retimed_consequences/lib.py, written before registration): for each unit and period, "
       "r = ln(mean Monday and Friday count / mean Tuesday-to-Thursday count) over retained weeks, and Y = r(recent) - r(baseline). "
       "Retained weeks have no federal holiday and no day from 24 December to 1 January, as in the dose map; the weeks of Monday 26 January "
       "and Monday 23 February 2026 are also dropped, because subway entries on those Mondays were 38% and 20% of the week's midweek level "
       "(docs/transit.md), which was known from entries before any outcome was seen. Intervals are the 2.5 and 97.5 percentiles of 2,000 "
       "bootstrap draws that resample weeks within each period and, for a slope across units, the units as well.")
GAP = ("System Public Graph, variable searches (data/derived/graph/retimed_week/gap_checks.json and "
       "data/derived/round2/retimed_consequences/graph_gap_check.json, graph_leads.json): no finding has this outcome with commuting, "
       "working at home, day of week or daytime population as the exposure.")
VERD = ("Verdict by concord.claims.PRECEDENCE rules 1 to 4: support_if met gives confirmed, refute_if met gives contested, otherwise unsettled; "
        "no_test if the registered data cannot be read. Secondary and placebo results decide nothing.")

taxi = {
 "id": "retimed-taxi-fhv-pickups", "kind": "confirmation",
 "statement": "Between February-March 2019 and February-March 2026, daytime taxi and high-volume for-hire pickups on Mondays and Fridays fell relative to Tuesday-to-Thursday pickups in the taxi zones whose subway entries thinned most on Mondays and Fridays, in proportion to between 0.3 and 1.0 of the thinning of entries.",
 "graph_evidence": [{"concepts": "taxi or ride-hail demand | commuting, working at home, weekday", "n_findings": 0, "direction": "none",
   "summary": GAP + " 82 variables match taxi, ride-hailing, ridesharing or uber. The nearest are rideshare trips per taxi zone-hour as an exposure for injury crashes (odds ratio 1.046, PMID 32253258) and an elasticity of 0.004 between ride-hailing use and transit ridership with no PubMed id. Neither is a finding on demand by day of week."}],
 "literature": [{"citation": "Barrero, Bloom and Davis 2023, The evolution of work from home, J Econ Perspectives", "doi": "10.1257/jep.37.4.23", "finding": "Days worked at home rose to about four times their 2019 share; no estimate for taxi demand."}],
 "prediction": {"direction": "+",
   "magnitude": "Primary: the slope b of Y (pickups) on E (entries) across taxi zones is between 0.3 and 1.0. Secondary measure that must agree in sign: Y pooled over the third of zones with the most thinning (E <= -0.0639; pooled E = -0.109) minus Y pooled over the third with the least (E >= -0.0421; pooled E = -0.032) is between -0.02 and -0.08.",
   "support_if": "The 95% interval of b lies above zero and the 95% interval of the top-third minus bottom-third contrast lies below zero.",
   "refute_if": "The 95% interval of b lies below zero, or its upper bound is below 0.3 (any effect is smaller than registered)."},
 "plan": DOSE + " " + EST + " Outcome: pickups with pickup hour 06 to 19 by pickup zone and date, yellow taxi plus high-volume for-hire (Uber, Lyft), from TLC trip records. This is a sample of months, not full years: February and March 2019 (7 retained weeks; high-volume for-hire records begin in February 2019; local parquet copies) against February and March 2026 (6 retained weeks; yellow from local parquet, high-volume for-hire by remote column scan of the TLC parquet files, which are not saved). Green taxis and other for-hire bases are left out. Units: the taxi zones that contain at least one reliable station complex (150) and have at least 200 pickups per weekday in the band in both periods. b is the unweighted OLS slope of Y on E. Sensitivity, reported and not deciding: slope weighted by 2019 pickups; yellow and for-hire separately; zones outside the CBD only; hours 06-09 against E for the AM peak. Placebo: yellow taxi February-March 2018 against 2019. Power, from data outside the test: random half-splits of the 10 retained weeks of January-March 2018 (yellow plus all for-hire, 147 zones) give a null standard deviation of 0.166 for b and 0.016 for the contrast; scaled to 7 and 6 weeks the expected standard errors are about 0.15 and 0.014 (design_taxi_placebo_2018.json). The smallest slope detectable with 80% power is about 0.41. At b = 0.5 the predicted contrast is -0.038, 2.7 standard errors from zero (D = 7.6, above the kit's threshold of 4). A true slope of zero would meet refute_if about half the time. The split-half error leaves out differences between zones that built up over seven years, so the real interval may be wider. " + VERD,
 "already_seen": "The project holds TLC pickups by zone and day for January-March 2018 and 2019 (transit-fhv-price-subway, used for totals near subway complexes, not by weekday), June-October 2023 and June-September 2024 (transit-gtrain-substitution, G-train zones), and zone totals for commute-fhv-subway-distance. None was tabulated by weekday against midweek. For this registration I read yellow and for-hire pickups for January-March 2018 only, to estimate sampling error. I have not tabulated 2019 or 2026 pickups by weekday.",
 "alternatives": ["Yellow taxis lost share to for-hire vehicles unevenly across zones, and the two services have different weekday patterns (separate estimates by service address this).",
   "Tourists and residents, who did not change their week, make most daytime trips in Manhattan, so pickups need not follow office attendance.",
   "Weather differed between the sampled weeks of 2019 and 2026; a storm on a Monday or Friday moves the citywide ratio, though less the difference between zones.",
   "The congestion charge from January 2025 lowered trips in the CBD on all weekdays; it biases the result only if its effect differs between Monday or Friday and midweek.",
   "MTA service changes on Mondays and Fridays alter entries without altering presence, which would weaken the slope."],
 "prior": 0.5, "registrant": WHO}

burg = {
 "id": "retimed-daytime-burglary", "kind": "confirmation",
 "statement": "Residential burglaries that began between 08:00 and 18:00 fell on Mondays and Fridays relative to Tuesday to Thursday between 2015-2019 and 2023-2026, by between half and all of the proportional fall in Monday and Friday morning-peak subway entries from residential districts (a ratio of 0.905 to 0.95).",
 "graph_evidence": [{"concepts": "burglary | home occupancy, working at home, commuting", "n_findings": 0, "direction": "none",
   "summary": GAP + " 43 variables match burglary, burglaries, guardianship or home occupancy; two findings have burglaries as the outcome: restaurant openings in Oakland (rate ratio 1.05, 1.04 to 1.06, PMID 35491751) and reporting victimisation to police (0.95, 0.84 to 1.07, PMID 27466811). Neither concerns whether homes are occupied in the daytime."}],
 "literature": [{"citation": "Cohen and Felson 1979, Social change and crime rate trends: a routine activity approach, American Sociological Review 44(4)", "doi": "10.2307/2094589", "finding": "Burglary rose as households emptied in the daytime; the reverse is expected when people work at home. Cited from memory of the argument, not for a number."}],
 "prediction": {"direction": "-",
   "magnitude": "Primary: the citywide ratio exp(Y) of the Monday-and-Friday to Tuesday-to-Thursday burglary ratio, recent over baseline, is between 0.905 and 0.95 (Y between -0.10 and -0.05). The proportional value comes from the dose map: pooled AM-peak E for community districts outside the CBD is -0.147 in the half that thinned more and -0.053 in the other half, about -0.10 overall. Secondary, not deciding: Y in the 24 higher-sending districts minus Y in the 24 lower-sending districts is negative (predicted about -0.05 to -0.09).",
   "support_if": "The 95% interval of the citywide ratio lies below 1.",
   "refute_if": "The 95% interval of the citywide ratio lies above 1, or its lower bound is above 0.95 (a fall of the registered size is excluded)."},
 "plan": DOSE + " " + EST + " Outcome: NYPD complaints with ky_cd 107 (burglary), prem_typ_desc in RESIDENCE - APT. HOUSE, RESIDENCE-HOUSE or RESIDENCE - PUBLIC HOUSING, cmplnt_fr_dt on a Monday to Friday of a retained week and cmplnt_fr_tm from 08:00:00 to 17:59:59, from qgea-i56i (to 2025) and 5uac-w243 (2026). The day and time are the start of the period in which the burglary could have happened, as reported by the victim. Baseline: 2015 to 2019. Recent: January 2023 to September 2026; the CBD Monday and Friday deficit in entries was 14.1% in 2023, 13.0% in 2024, 12.7% in 2025 and 13.8% in the latest 12 months, so the exposure has been in place since 2023. Primary: all complaints citywide, pooled. Sending areas, defined now from the dose map and listed in exposure_groups.json: community districts outside the CBD with a reliable station complex, split at the median AM-peak E (-0.0753) into 24 higher-sending and 24 lower-sending districts; complaints are assigned to districts by latitude and longitude (NYC Open Data 5crt-au7u). Sensitivity, not deciding: complaints whose end date equals the start date; baseline 2017-2019 only; Monday and Friday separately; attempted burglaries excluded. Placebo: 2015-2017 against 2018-2019. Power: a design query that pooled Monday to Friday, and so showed nothing about the outcome, counted 17,299 such complaints in 2015-2019 and 8,500 from 2023 to September 2026 (design_burglary_weekday_totals.json). With 40% of them on Mondays and Fridays the Poisson standard error of Y is 0.027; with 15% added for clustering it is 0.031. The central prediction Y = -0.075 is 2.4 standard errors from zero (D = 5.9); the lower end, -0.05, is 1.6 (D = 2.6), so the test can confirm only a fall of about 6% or more, and an estimate above +0.011 would refute. The district contrast has a standard error near 0.06 against a predicted -0.07 (D = 1.3); it cannot separate the hypothesis from no effect and is reported as secondary for that reason. " + VERD,
 "already_seen": "Earlier claims queried NYPD complaints for seven felony offences by month, hour and premises (further-subway-crime claims) and for shootings by day; none tabulated burglary by weekday. For this registration I queried counts of the outcome pooled over Monday to Friday by year, 2014 to 2026, which show the yearly level and not the weekday split.",
 "alternatives": ["Burglars' own schedules, and those of police, changed between the periods for reasons other than occupancy.",
   "Victims who are at home notice and report a burglary on the day; victims who are away report the day they left. A change in who is at home changes the recorded day as well as the true day.",
   "The mix of residential burglary changed (package and lobby theft recorded as burglary in apartment houses), with its own weekday pattern.",
   "Burglary fell by half between 2015 and 2019, so the baseline pools years with different offender populations (the 2017-2019 baseline checks this).",
   "Subway entries understate work at home among car commuters and overstate it where service was cut."],
 "prior": 0.25, "registrant": WHO}

ems = {
 "id": "retimed-ems-presence", "kind": "confirmation",
 "statement": "Daytime EMS incidents in the Manhattan business district (community districts 101 to 106) fell on Mondays and Fridays relative to Tuesday to Thursday between 2018-2019 and October 2024-September 2026, relative to the same change in the rest of the city, by between 0.2 and 1.0 of the difference in the thinning of subway entries.",
 "graph_evidence": [{"concepts": "EMS or ambulance call volume | daytime population, commuting, working at home, weekday", "n_findings": 0, "direction": "none",
   "summary": GAP + " 240 variables match ambulance, emergency medical services, EMS calls, daytime population or ambient population. Call volume appears as an outcome of a hurricane (PMID 30704948), the COVID-19 outbreak (PMID 33052824) and a smoke-free law (PMID 23918257); daytime population density appears only with physician supply (PMID 19226450). No finding relates call volume to the number of people present."}],
 "literature": [],
 "prediction": {"direction": "+",
   "magnitude": "Primary: the contrast C = Y(CBD districts pooled) - Y(other districts pooled) is between -0.013 and -0.064. As an elasticity, C / (E_cbd - E_rest) with E_cbd = -0.1174 and E_rest = -0.0535 (difference -0.0639), it is between 0.2 and 1.0. 'In proportion to entries' means an elasticity of 1; I expect less, about 0.4, because residents, visitors and people without offices generate most calls.",
   "support_if": "The 95% interval of C lies below zero (elasticity interval above zero).",
   "refute_if": "The 95% interval of C lies above zero, or its lower bound is above -0.013 (elasticity below 0.2 throughout the interval)."},
 "plan": DOSE + " " + EST + " Outcome: EMS incidents (76xm-jjuj) with incident hour 06 to 19, by communitydistrict and date. Baseline: 2018 and 2019. Recent: 1 October 2024 to 30 September 2026, the last two years in the dataset. Units: the community districts (codes ending 01 to 18) that hold a reliable station complex, 54 in all; the CBD group is the six districts whose complexes are all inside the MTA business district (101 to 106), and the rest are the other 48. The reported effect is the elasticity C / -0.0639 with its interval; whether the interval includes 1 is reported as the test of proportionality. Secondary, not deciding: the slope of Y on E across the 54 districts; Monday and Friday separately; hours 06-09 and 10-15; high-severity incidents (initial severity 1 to 3) only; baseline 2019 and recent 12 months only. Placebo: 2016-2017 against 2018-2019. Power, from years outside the test: the same estimator applied to 2017 against 2018 gave C = -0.013 (-0.038 to 0.012), standard error 0.0129, and a slope standard error of 0.27 (design_ems_placebo_2017_2018.json); weekday incidents in the band averaged 375 a day in the CBD districts and 2,305 in the rest. With two years on each side the standard error of C should be about 0.009, or 0.14 as an elasticity. The central prediction, elasticity 0.4 (C = -0.026), is 2.8 standard errors from zero (D = 8); elasticity 0.2 is 1.4. A true elasticity of zero would meet refute_if about a quarter of the time and support_if 2.5% of the time. The slope across districts can detect only an elasticity near 0.8 and is secondary for that reason. " + VERD,
 "already_seen": "Earlier claims queried EMS incidents by day for shootings and stabbings, drug and psychiatric calls, and asthma, citywide; none tabulated incidents by community district or by weekday against midweek. For this registration I queried all daytime incidents by district and date for 2017 and 2018 only, to estimate sampling error; 2018 is therefore in both the design check and the baseline, and I have seen the 2017-to-2018 change in its weekday ratio (C = -0.013), not its level against any later year.",
 "alternatives": ["Residents of the CBD districts, about 600,000 people, stay in the district when they work at home, which offsets the loss of commuters.",
   "Calls in Midtown come largely from visitors, shelters, hospitals and transit hubs, whose week did not change.",
   "EMS call triage and telemedicine changed after 2020 and may have changed call volume differently by district.",
   "The contrast is against the rest of the city, where people working at home add daytime presence on Mondays and Fridays; a negative C mixes a fall in the CBD with a rise elsewhere (the two pooled Y values are reported separately).",
   "The district recorded is where the incident was, and incidents without a district code are dropped."],
 "prior": 0.45, "registrant": WHO}

if __name__ == "__main__":
    for r in (taxi, burg, ems):
        if len(sys.argv) > 1 and r["id"] not in sys.argv[1:]:
            continue
        print(claims.register(r))
