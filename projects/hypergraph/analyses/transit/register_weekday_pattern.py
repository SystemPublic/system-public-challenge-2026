"""Registration of transit-weekday-pattern. Run once, before any ridership value is queried.

    ~/.venvs/nyc-concordance/bin/python -m analyses.transit.register_weekday_pattern
"""
from concord import claims

REC = {
    "id": "transit-weekday-pattern",
    "kind": "confirmation",
    "statement": (
        "In the Manhattan central business district, weekday subway entries in the 12 months to October 2026 "
        "are about equal on Tuesday, Wednesday and Thursday and at least 8% lower on Monday and Friday, and "
        "this Monday/Friday deficit is at least 4 percentage points larger than it was in 2019."
    ),
    "edge": {
        "cause": "hybrid work (working from home concentrated on Mondays and Fridays since 2020)",
        "effect": "day-of-week pattern of subway entries in the Manhattan CBD (Monday and Friday below Tuesday-Thursday)",
    },
    "graph_evidence": [
        {
            "note": (
                "The System graph API key is not on this machine and the Dataverse deposit is not downloaded here, "
                "so no live lookup was made. A live lookup of the concept pairs (telework | public transport use), "
                "(telecommuting | commuting) and (day of the week | transit ridership) is pending. The repo's cache "
                "(data/cache/sysgraph, 947 responses, 136 distinct searches; data/derived/graph_audit/evidence, 4 "
                "pairs) holds no search on telework, remote work, working from home, hybrid work or transit "
                "ridership, and no cached response contains those phrases. The strings 'weekday' and 'day of the "
                "week' occur only as covariates in cached findings on asthma, air pollution, temperature and "
                "violence. The graph is built mainly from health and social-science abstracts, so the expected "
                "result of the live lookup is that it holds no finding on this edge."
            ),
            "cached_searches_checked": ["wikidata_label:commute", "wikidata_label:commuting", "name:active commuting",
                                        "name:traffic volume", "name:congestion"],
            "n_findings": 0,
            "live_lookup": "pending",
        }
    ],
    "literature": [
        {
            "citation": "Barrero JM, Bloom N, Davis SJ (2023). The Evolution of Work from Home. Journal of Economic Perspectives 37(4):23-50.",
            "doi": "10.1257/jep.37.4.23",
            "finding": "Full days worked at home were 28% of paid workdays among Americans aged 20-64 in mid-2023, about four times the 2019 share (abstract).",
            "data_used": "Survey of Working Arrangements and Attitudes (SWAA), monthly online survey of US residents, with ATUS and ACS for the pre-2020 series",
            "data_access": "open",
            "access_note": "SWAA microdata are downloadable from wfhresearch.com; ACS and ATUS are public.",
        },
        {
            "citation": "Barrero JM, Bloom N, Davis SJ (2021). Why Working from Home Will Stick. NBER Working Paper 28731.",
            "doi": "10.3386/w28731",
            "finding": "Predicts that working from home will persist after the pandemic at a multiple of its 2019 level. Later SWAA releases and Bloom's public summaries name Friday as the most common day worked from home, with Monday and Thursday next; these day-of-week shares were read from secondary reports and slides, not from a table in the paper, so no number is quoted.",
            "data_used": "SWAA",
            "data_access": "open",
        },
        {
            "citation": "Motte-Baumvol B, Schwanen T, Bonin O (2024). Telework and the day-to-day variability of travel behaviour: The specificities of Fridays. Transportation Research Part D 132:104245.",
            "doi": "10.1016/j.trd.2024.104245",
            "finding": "Teleworkers in England commute less on Fridays and make more non-work trips on that day. A search snippet gives a 20% reduction in Friday commuting for teleworkers; the full text was not read, so the number is unverified.",
            "data_used": "National Travel Survey for England, seven-day travel diaries",
            "data_access": "partly_open",
            "access_note": "NTS microdata are available from the UK Data Service after registration.",
        },
        {
            "citation": "Light R, Osorio J, Liu Y, Ouyang Y (2025). How COVID-19 impacted Chicago Metra's ridership loss and recovery: 2019-2022. Transportation Research Part D 146:104857.",
            "doi": "10.1016/j.trd.2025.104857",
            "finding": "Attributes most of the weekday commuter-rail ridership loss to reduced workplace occupancy from remote work (abstract, read through a search summary). It does not report a day-of-week breakdown that we could verify.",
            "data_used": "Metra station origin-destination ridership January 2019 to October 2022, workplace occupancy series",
            "data_access": "unknown",
        },
        {
            "citation": "MTA New York City Transit (December 2022). Subway service adjustments for 2023, as reported by amNewYork, 19 December 2022.",
            "doi": None,
            "finding": "System-wide average weekday subway ridership in fall 2022 was about 12.5% higher on Thursdays than on Mondays, and lower on Mondays and Fridays than on Tuesday to Thursday. This is an agency statement in a news report (the MTA press release returned HTTP 403), grey literature. It is system-wide, not the CBD, and gives no pre-2020 comparison.",
            "data_used": "MTA fare-collection ridership counts",
            "data_access": "open",
        },
        {
            "citation": "Kastle Systems. Back to Work Barometer (weekly, 2020-2026).",
            "doi": None,
            "finding": "Office card-swipe occupancy in the New York metro area peaks on Tuesday and is lowest on Friday. Grey literature; the buildings are Kastle's clients, not a sample of offices. No figure is quoted because dated New York day-of-week values could not be verified.",
            "data_used": "Kastle access-control swipes in client buildings",
            "data_access": "restricted",
        },
        {
            "citation": "NYC Comptroller (10 October 2021). Beyond Rush Hour: COVID-19 and the Future of Public Transit.",
            "doi": None,
            "finding": "In 2021 weekday subway ridership was at 51% of pre-pandemic levels and weekend ridership at 65%. It gives no Monday or Friday figures.",
            "data_used": "MTA day-by-day ridership and hourly ridership supplied by the MTA",
            "data_access": "partly_open",
        },
    ],
    "literature_gap": (
        "Two extended web searches found no peer-reviewed study that measures a Tuesday-Thursday plateau and a Monday/Friday "
        "deficit in fare-collection counts after 2020 and compares it with the same counts before 2020. The peer-reviewed "
        "evidence is on travel diaries (Motte-Baumvol et al.) and on total weekday loss (Light et al.). The day-of-week "
        "pattern in ridership is asserted in agency statements and trade reports."
    ),
    "prediction": {
        "direction": "+",
        "definitions": (
            "For each retained week w and weekday d, R[w,d] is the sum of `ridership` over the 65 CBD complexes. "
            "The index is I[w,d] = R[w,d] / mean(R[w,Tue], R[w,Wed], R[w,Thu]). "
            "Deficit(d) = 1 - mean over weeks of I[w,d]. "
            "MF deficit = (Deficit(Mon) + Deficit(Fri)) / 2. "
            "Midweek range = max minus min of the three mean indices for Tue, Wed and Thu. "
            "Delta = MF deficit in the recent period minus MF deficit in 2019, in percentage points. "
            "Intervals are 95% percentile intervals from 10,000 bootstrap resamples of weeks, drawn separately in each period (seed 20261112)."
        ),
        "magnitude": (
            "Recent CBD MF deficit 8% to 14% (Monday 7% to 13%, Friday 8% to 16%). Recent midweek range 1 to 4 points. "
            "2019 CBD MF deficit 2% to 6%, so the gap was smaller before 2020 but not absent. Delta +4 to +10 points."
        ),
        "support_if": (
            "All three hold in the primary analysis: (a) recent MF deficit >= 8%, with its interval's lower bound >= 5%, and "
            "Deficit(Mon) >= 5% and Deficit(Fri) >= 5% separately; (b) recent midweek range <= 3 points; "
            "(c) Delta >= 4 points with an interval that excludes 0."
        ),
        "refute_if": (
            "Any one holds: (a) recent MF deficit < 4% with its interval's upper bound < 8%; "
            "(b) Delta <= 1 point with its interval's upper bound < 4 points; (c) recent midweek range > 6 points."
        ),
        "otherwise": "Neither met gives unsettled (precedence rules 1 and 2). The outcome states which of (a), (b), (c) failed.",
        "sub_question_absent_before_2020": (
            "Scored separately and not part of the verdict: the gap counts as absent before 2020 if the 2019 MF deficit is "
            "below 3% and its interval includes values below 2%. The registrant predicts it was not absent (2% to 6%)."
        ),
        "city_effect_for_stance": "Delta, in percentage points, null 0.",
    },
    "plan": {
        "datasets": {
            "5wq4-mkjj": "MTA Subway Hourly Ridership: Beginning 2025 (data.ny.gov); recent period",
            "t69i-h2me": "MTA Subway Hourly Ridership: 2017-2019 (data.ny.gov); 2019 baseline and 2018 placebo year",
            "wujg-7c2s": "MTA Subway Hourly Ridership: 2020-2024 (data.ny.gov); descriptive trajectory 2022-2024 only",
            "39hk-dx4f": "MTA Subway Stations (data.ny.gov); CBD flag and coordinates",
        },
        "access": "concord/socrata.py with concord.socrata.DOMAIN set to https://data.ny.gov in the script. The source records therefore carry kind 'nyc-open-data' although the portal is New York State's; the url field shows data.ny.gov.",
        "measure": "Sum of the `ridership` column (entries by MetroCard or OMNY) with transit_mode = 'subway'. Entries are a proxy for people present, not a count of pedestrians; exits are not recorded, and fare evasion is not counted.",
        "area": (
            "Primary: the 65 station complexes that have a station flagged cbd = true in MTA Subway Stations (39hk-dx4f). "
            "In that table every complex is either wholly flagged or wholly unflagged. The flag is the MTA's own definition "
            "of the Manhattan central business district (60th Street and south). The join is station_complex_id = complex_id; "
            "all 65 matched in both the 2017-2019 and the 2025 datasets."
        ),
        "periods": "Recent: 1 November 2025 to 31 October 2026 (the data ran to 5 November 2026 when registered). Baseline: 1 January to 31 December 2019.",
        "unit_and_exclusions": (
            "Unit: weekday (Monday to Friday) within a calendar week (Monday to Sunday). A week is dropped if any of its seven "
            "days is an observed US federal holiday, if any of its days falls from 24 December to 1 January, or if its five "
            "weekdays are not all inside the period. Juneteenth counts as a holiday in 2025 and 2026 only. Every retained week "
            "therefore has all five weekdays. Days are calendar days of transit_timestamp. No other day is removed in the "
            "primary analysis (storms, school holidays and religious holidays stay in)."
        ),
        "model": "The ratios defined under prediction.definitions, with week-bootstrap intervals. No regression model.",
        "queries": "Server-side aggregation: sum(ridership) grouped by date_trunc_ymd(transit_timestamp) and date_extract_hh(transit_timestamp) for the CBD complex list and for each borough, and by day and station_complex_id for the ranking.",
        "sensitivity": [
            "S1 office core: CBD complexes whose mean station coordinates lie within 1.2 km of Grand Central-42 St (40.7527, -73.9772) or of Wall St at Broad St (40.7069, -74.0110).",
            "S2 median across weeks in place of the mean.",
            "S3 drop only the federal holidays themselves and 24 December to 1 January, keeping the rest of those weeks (unbalanced; day means divided by the Tue-Thu day mean).",
            "S4 recent period = calendar 2025 in place of November 2025 to October 2026.",
            "S5 complex-level: the MF deficit computed for each CBD complex, reported as the median and interquartile range across the 65 complexes, and an interval from resampling complexes.",
        ],
        "placebo": (
            "The same Delta computed for 2019 minus 2018 (both from t69i-h2me, the same exclusions). Hybrid work did not change "
            "between those years, so Delta should be near 0. The placebo passes if |Delta| < 1.5 points. If it fails, the "
            "primary Delta is reported with that year-to-year variation beside it, and a primary Delta smaller than three "
            "times the placebo's absolute value is treated as not met for condition (c)."
        ),
        "secondary": [
            "Hour bands, by hour of entry: AM peak 06:00-09:59, midday 10:00-15:59, PM peak 16:00-19:59, evening 20:00-23:59. The same deficits and Delta in each band for the CBD. Prediction: the largest Delta is in the PM peak, when office workers enter CBD stations to go home; the Friday evening deficit is under 3% or negative in both periods.",
            "Outer-borough residential contrast: all subway complexes in the Bronx, Brooklyn and Queens, AM peak entries only (residents leaving home). Prediction: Delta is positive but smaller than the CBD PM-peak Delta, between 2 and 6 points.",
            "Trajectory: CBD MF deficit for calendar 2022, 2023 and 2024 from wujg-7c2s (descriptive).",
            "Ranking: the 20 busiest complexes by mean entries per retained weekday in 2019 and in the recent period. Prediction: at least 16 complexes are in both lists, the Spearman correlation of mean weekday entries across all complexes is at least 0.95, and fewer of the top 20 are CBD complexes in the recent period than in 2019 or the same number.",
        ],
        "figure": "figures/transit/weekday_pattern.png: the day-of-week index for the CBD in 2019 and the recent period with intervals, and the MF deficit by hour band.",
    },
    "alternatives": [
        "A Monday/Friday deficit that existed before 2020 for reasons other than remote work (long weekends, compressed schedules, part-time work, school calendars); the 2019 baseline measures it.",
        "Leisure and tourist trips, which are a larger share of CBD entries than in 2019 and are spread differently over the week (more on Friday evenings), can hide or exaggerate the office pattern; the hour bands address this in part.",
        "Holiday-adjacent days and Friday early closing before long weekends remain in the retained weeks only when the holiday falls in another week; the week exclusion removes most of them.",
        "Service changes: from 2023 the MTA ran less service on some lines on Mondays and Fridays, which could lower entries on those days independently of demand.",
        "Congestion pricing since 5 January 2025 raised subway use into the CBD; it applies on every weekday, so it should change levels more than the day-of-week ratios.",
        "Fare evasion and the move from MetroCard to OMNY change what is counted, but there is no known reason for these to differ by weekday.",
        "Weather and one-off events (storms, strikes, the 2026 World Cup matches in June and July) fall on particular weekdays by chance; the week bootstrap and the median check reflect this.",
    ],
    "prior": 0.45,
    "prior_note": "All three conditions must hold. The registrant puts about 0.85 on (a), 0.9 on (c) and 0.6 on (b), since SWAA reports suggest Thursday is a common remote day.",
    "seen_before_registration": (
        "No ridership value from 5wq4-mkjj, wujg-7c2s or t69i-h2me had been queried by this project: data/cache/socrata held "
        "no file for them and no script in analyses/ names them. The project had queried the station table 39hk-dx4f once "
        "(commute-fhv-subway-distance, coordinates only). Before registering, this agent read (1) the metadata and column "
        "descriptions of the three ridership datasets, (2) the station table with its cbd column, (3) for one day in each of "
        "t69i-h2me (15 May 2019) and 5wq4-mkjj (13 May 2026) the distinct station_complex_id, station_complex, borough and "
        "transit_mode with a row count, to check the join, and (4) min and max of transit_timestamp in each of the three "
        "datasets. No sum or value of the ridership column was read. The registrant knew the MTA's fall 2022 statement cited "
        "under literature, and has a general recollection that system-wide Monday ridership was a few percent below midweek "
        "before 2020."
    ),
    "registrant": "Claude (agent), for Jeff Vernon",
}

if __name__ == "__main__":
    print(claims.register(REC))
