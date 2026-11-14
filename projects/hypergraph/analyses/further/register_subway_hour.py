"""Registration of further-subway-crime-per-ride-by-hour and its reproduction companion.
Run once, before any complaint count, felony count or ridership total for these tests is queried.

    PYTHONPATH=. ~/.venvs/nyc-concordance/bin/python -m analyses.further.register_subway_hour
"""
from concord import claims

DEFS = (
    "Numerator N[b,p]: NYPD complaints (qgea-i56i for cmplnt_fr_dt through 2025-12-31, 5uac-w243 for 2026-01-01 to "
    "2026-09-30, the last complete quarter) with law_cat_cd = 'FELONY', ky_cd in {101 murder, 104 rape, 105 robbery, "
    "106 felony assault, 107 burglary, 109 grand larceny, 110 grand larceny of motor vehicle} (the seven MTA major "
    "felony types), prem_typ_desc = 'TRANSIT - NYC SUBWAY', assigned to the hour of cmplnt_fr_tm and the date of "
    "cmplnt_fr_dt. Complaints with a missing time or date are dropped and their share reported. Denominator E[b,p]: "
    "sum of `ridership` (estimated fare entries, in millions) over transit_mode = 'subway' for the same hours "
    "(t69i-h2me for 2019, 5wq4-mkjj for 2025-2026). Hour h of the ridership table covers h:00-h:59. Bands: 0-5 = "
    "hours 0-4, 5-10 = 5-9, 10-16 = 10-15, 16-20 = 16-19, 20-24 = 20-23. Periods: 2019 = 1 Jan-31 Dec 2019; L12 = "
    "1 Oct 2025-30 Sep 2026. Rate r[b,p] = N/E per million entries. Intervals: exact (Garwood) Poisson interval "
    "for a count, divided by the fixed exposure; for a ratio of two rates, the exact conditional binomial interval "
    "for N1/(N1+N2) given the exposures; for a ratio of ratios, a Wald interval on the log scale with variance "
    "equal to the sum of 1/N over the four counts. Ridership is treated as known; its estimation error is not "
    "propagated and is named as a limit. Quantities: A = r[0-5, L12] / r[10-16, L12]. G[b] = r[b, L12] / r[b, 2019]. "
    "G_all = the same ratio for all bands pooled. B = G[0-5] / G_all."
)

MAIN = {
    "id": "further-subway-crime-per-ride-by-hour",
    "kind": "conflict",
    "statement": (
        "Per fare entry, major felonies reported in the NYC subway in the hours 0-5 are at least three times as "
        "frequent as in the hours 10-16 in the 12 months to September 2026, and the 0-5 rate has not fallen back "
        "to its 2019 level, so the State's all-day fall in crime per rider does not describe the late-night hours."
    ),
    "edge": {
        "cause": "hour of day (late night against daytime, with the post-2020 change in who rides at night)",
        "effect": "major felony complaints per million subway entries",
    },
    "graph_evidence": [
        {
            "note": (
                "The System graph API key is not on this machine, so no live lookup was made. A live lookup of the "
                "concept pairs (time of day | violent crime), (public transportation | crime) and (perceived safety "
                "| public transport) is pending. The repo's graph cache was not searched for these concepts before "
                "registration; the graph is built mainly from health and social-science abstracts, and the expected "
                "result of the live lookup is few or no findings on this edge."
            ),
            "n_findings": 0,
            "live_lookup": "pending",
        }
    ],
    "literature": [
        {
            "citation": "Office of the Governor of New York (18 December 2025). Safer Subways: Governor Hochul announces subway crime on track to reach lowest levels in a generation in 2025.",
            "url": "https://www.governor.ny.gov/news/safer-subways-governor-hochul-announces-subway-crime-track-reach-lowest-levels-generation-2025",
            "finding": "\"there have been 1.65 major crimes per million riders in 2025, down roughly 30 percent from 2021\"; overall major crime in transit \"down 5.2 percent from 2024 and 14.4 percent from 2019\". The release names no data source, does not define major crime, and gives no figures by hour (read in full on 12 November 2026).",
            "data_used": "not stated; presumably the MTA Major Felonies series (yeek-jhmu) and MTA ridership",
            "data_access": "open",
        },
        {
            "citation": "Citizens Budget Commission (June 2025). Resident survey on public safety, as reported by Gothamist and amNewYork.",
            "url": None,
            "finding": "51% of residents felt safe on the subway by day and 22% at night, the same night figure as in 2023 and below 46% in 2017 (from news summaries; the report itself returned HTTP 403 and sample size and wording were not read).",
            "data_used": "resident survey",
            "data_access": "unknown",
        },
        {
            "citation": "Smith MJ, Clarke RV (2000). Crime and public transport. Crime and Justice 27:169-217.",
            "doi": None,
            "finding": "Reviews transport crime as concentrated at stations and times with low guardianship, including late evening and night; cited from memory of the review's thesis, the page-level claim was not checked and no number is quoted.",
            "data_used": "review of police and survey studies",
            "data_access": "partly_open",
        },
    ],
    "prediction": {
        "direction": "+",
        "definitions": DEFS,
        "magnitude": (
            "A (0-5 against 10-16 rate, L12) 3 to 8, point guess 4.5. G[0-5] (L12 against 2019) 1.2 to 2.2. G_all 1.1 to "
            "1.6, that is, the all-day rate per entry is also expected to be above its 2019 level because entries are "
            "well below 2019 while complaint counts are at or somewhat below the 2019 count; the premise that the "
            "all-day rate per ride has returned to 2019 is expected to be false. B 1.0 to 1.5. The 20-24 band "
            "rate is expected at 1.3 to 2.5 times the 10-16 rate and is reported but does not decide the verdict."
        ),
        "support_if": (
            "A >= 3.0 with the lower 95% bound of A >= 2.0, AND the lower 95% bound of G[0-5] > 1, AND B >= 1.10."
        ),
        "refute_if": (
            "The upper 95% bound of A < 3.0, OR the upper 95% bound of G[0-5] < 1 (the 0-5 rate per entry is "
            "below its 2019 level). Anything else is unsettled."
        ),
        "placebo": (
            "Placebo (reported, not part of the verdict): the same seven felony types at non-subway premises "
            "(all prem_typ_desc except subway, transit facility other, tunnel and bridge), counted by the same bands "
            "and periods without a ridership denominator. D_placebo = [N(0-5,L12)/N(0-5,2019)] / [N(all,L12)/N(all,2019)]. "
            "If D_placebo >= 1.10 with its 95% interval excluding 1, a citywide shift of reported crime toward "
            "the night, not the subway, explains a B >= 1.10, and the outcome says so."
        ),
    },
    "plan": (
        "Question: is the State's fall in crime per rider true at every hour, or only on average? Part 1 (the "
        "reproduction of the State's number) is registered separately as further-subway-crime-per-million-repro. "
        "Part 2 (this claim) uses NYPD complaint data over MTA hourly ridership, with the definitions in "
        "prediction.definitions fixed here. Primary numerator premise: 'TRANSIT - NYC SUBWAY'. Datasets: "
        "qgea-i56i, 5uac-w243 (data.cityofnewyork.us), t69i-h2me, 5wq4-mkjj (data.ny.gov; "
        "wujg-7c2s for 2020-2024 descriptive years only). Aggregation on the server by date and hour; no row "
        "downloads. Unit: citywide subway system by hour band and period (no station crosswalk is attempted, "
        "because the complaint file's station_name is incomplete and the rate is a system rate). Model: the "
        "rates and ratios in the definitions; a descriptive year series 2019 to 2025 by band is plotted (2020 to "
        "2024 ridership from wujg-7c2s). Pre-specified sensitivity checks, each reported with A, G[0-5] and B: "
        "S1 numerator premise also includes 'TRANSIT FACILITY (OTHER)'; S2 numerator is every felony in the seven "
        "types with transit_district not null; S3 drop complaints whose time is exactly 00:00:00 or 12:00:00 "
        "(default or rounded entries); S4 violent types only (101, 104, 105, 106); S5 calendar 2025 in place of "
        "L12; S6 bands shifted to 22-4 against 10-16. Placebo as in prediction.placebo. Limits named in advance: "
        "the denominator counts fare entries, not riders present or train-hours, so a transfer within the "
        "system, a rider staying aboard overnight, or free exits are not counted and the per-ride rate is "
        "per entry; a complaint's time is the reported time of occurrence and many are estimates; hourly "
        "ridership after 2020 is a modelled estimate; the 0-5 band holds few entries, so intervals are wide; "
        "complaints are reports and reporting may differ by hour and year; the complaint tables record "
        "only crimes reported, and subway-premise assignment depends on officers' coding."
    ),
    "alternatives": [
        "Reporting and coding: a change in how subway crimes are coded (premise) or reported by hour produces the pattern without a change in risk (placebo and S1, S2).",
        "Composition of riders: the night rider mix changed after 2020, so a higher per-entry rate reflects who is present and exposure per entry, not unsafe conditions.",
        "Denominator: entries per hour understate the people present on platforms and trains late at night, who include people sheltering, so per-entry rates overstate risk per person-hour at night.",
        "Offense mix: a rise confined to grand larceny or robbery of sleepers differs from a rise in violent crime (S4).",
        "Citywide: crime at all premises shifted toward the night (placebo).",
    ],
    "prior": 0.35,
    "registrant": "Claude (agent), for Jeff Vernon",
    "disclosure_prior_looks": (
        "Before registration this session read only metadata, column lists, the distinct values of prem_typ_desc, "
        "juris_desc, jurisdiction_code, law_cat_cd, transit_district and ky_cd/ofns_desc, and the date coverage of "
        "qgea-i56i (to 2025-12-31) and 5uac-w243 (to 2026-09-30), and the distinct agency, police_force and "
        "felony_type values and the month range of yeek-jhmu. No complaint count, felony count or ridership total "
        "was read. The repo's cache already holds hourly ridership aggregates fetched by other agents: t69i-h2me "
        "subway entries by day and hour for 2018 (all complexes, CBD complexes, and by borough), by station and "
        "night/day split for the week of 14 January 2019, and the 2025-2026 station list; these were not opened "
        "for this claim and are not used. No NYPD complaint or yeek-jhmu query had been made in the repo. The "
        "prior comes from general knowledge that entries are well below 2019 and that the State reports "
        "complaint counts below 2019."
    ),
    "graph_evidence_pending": True,
}

REPRO = {
    "id": "further-subway-crime-per-million-repro",
    "kind": "reproduction",
    "target": {
        "report": "Safer Subways: Governor Hochul announces subway crime on track to reach lowest levels in a generation in 2025 (press release)",
        "agency": "Office of the Governor of New York",
        "date": "2025-12-18",
        "url": "https://www.governor.ny.gov/news/safer-subways-governor-hochul-announces-subway-crime-track-reach-lowest-levels-generation-2025",
        "location": "paragraph on crime per rider",
        "number": {"major_crimes_per_million_riders_2025": 1.65, "fall_since_2021_percent": 30,
                   "transit_major_crime_change_vs_2024_percent": -5.2, "transit_major_crime_change_vs_2019_percent": -14.4},
        "definition": (
            "\"1.65 major crimes per million riders in 2025, down roughly 30 percent from 2021.\" The release names no "
            "source, does not define major crime, and was issued on 18 December 2025, so 2025 means a partial year."
        ),
        "data_used": ["MTA Major Felonies yeek-jhmu (data.ny.gov), column crimes_per_million_riders"],
        "data_access": "open",
        "tolerance": "1.65 within +-0.05 (about 3%); fall since 2021 within 27 to 33 percent",
    },
    "statement": (
        "The MTA Major Felonies table (yeek-jhmu) reproduces the Governor's figures: about 1.65 major felonies per "
        "million riders in 2025 and a fall of about 30% from 2021."
    ),
    "graph_evidence": [{"note": "Not applicable to a reproduction; no live graph lookup is pending for it.", "n_findings": 0}],
    "literature": [],
    "prediction": {
        "direction": "0",
        "definitions": (
            "Rate for a period = (sum of felony_count over the months and rows) / (sum over months of riders in "
            "millions), with the riders of a month taken as the monthly total felony_count divided by the monthly "
            "sum of crimes_per_million_riders over felony types, for the same rows. Fall since 2021 = 1 - rate(2025)/rate(2021) "
            "for the same months."
        ),
        "magnitude": "Primary reading R1 gives 1.60 to 1.70 for 2025 and a fall of 27 to 33 percent. Other readings may differ by more than the tolerance.",
        "support_if": (
            "Under the primary reading R1 both hold: rate(2025) within 1.65 +- 0.05 and the fall within 27 to 33 percent."
        ),
        "refute_if": "Under no registered reading R1 to R6 are both conditions met. Primary reading misses but another reading meets both: unsettled.",
        "readings": {
            "R1_primary": "agency = 'NYCT', both police forces, all seven felony types, months January to November 2025 against January to November 2021 (the release was issued 18 December 2025)",
            "R2": "as R1 with January to December 2025 against January to December 2021",
            "R3": "as R1 but the unweighted mean of the monthly total rates",
            "R4": "agency = 'NYCT' and police_force = 'NYPD' only, January to November",
            "R5": "all four agencies (NYCT, SIR, LIRR, MNR) pooled, January to November",
            "R6": "agency in ('NYCT','SIR'), January to November",
        },
    },
    "plan": (
        "Query yeek-jhmu (data.ny.gov) with server-side aggregation by month, agency, police_force and felony_type. "
        "Compute the readings in prediction.readings. Method sensitivity is the share of readings R1 to R6 that "
        "reproduce both numbers. As an independent check, also report the ratio of NYPD complaint counts (subway "
        "premise, seven felony types) to MTA subway entries for January to November 2025 and 2021, labelled "
        "secondary; it does not decide the verdict. The table description says it counts arrests while the column "
        "is named felony_count; the outcome states which the counts resemble by comparing with the complaint counts."
    ),
    "alternatives": ["The State's figure uses different months, agencies, a different rider count (ridership by trips rather than entries) or a different release of the table."],
    "prior": 0.6,
    "registrant": "Claude (agent), for Jeff Vernon",
    "disclosure_prior_looks": (
        "Only the distinct agency, police_force and felony_type values and the month range (2019-01 to 2026-09, "
        "table updated 2026-10-23) of yeek-jhmu were read before registration. No count or rate was read."
    ),
}

if __name__ == "__main__":
    for r in (MAIN, REPRO):
        print(claims.register(r))
