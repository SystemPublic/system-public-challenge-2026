"""Registrations for the mobility claims, written before any city data were queried.

Run once: python -m analyses.mobility.register_1
"""
import json
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[2]
EV = json.loads((ROOT / "data/derived/mobility/graph_evidence.json").read_text())
REGISTRANT = "mobility agent (Claude Opus 5.5), for J. Vernon"


def g(pair, rid):
    for r in EV["pairs"][pair]:
        if r["relationship_id"] == rid:
            sm = r["summary"]
            return {"relationship_id": rid, "concepts": [r["source"], r["target"]],
                    "n_findings": r["num_findings"], "n_studies": r["num_studies"], "direction": "+",
                    "summary": (f"{sm['n_ratio']} ratio findings; {sm['ratio_above_1']} above 1, "
                                f"{sm['ratio_below_1']} below; {sm['ratio_ci_excludes_1_above']} with CI above 1, "
                                f"{sm['ratio_ci_excludes_1_below']} with CI below 1; median ratio {sm['ratio_median']} "
                                "(mixed increments and designs)"),
                    "pubmed_ids": sm["pubmed_ids"][:25]}


CRZ_TRAFFIC = {
    "id": "mob-crz-traffic",
    "kind": "confirmation",
    "statement": ("Congestion pricing in Manhattan's Central Business District (from 5 January 2025) raised "
                  "taxi and for-hire vehicle speeds and reduced TLC trip counts in the CBD relative to the rest "
                  "of New York City."),
    "graph_evidence": [{"note": ("The System graph holds no findings on road pricing, congestion charging or "
                                 "cordon tolls (variable searches: congestion pricing, road pricing, congestion "
                                 "charging, low emission zone, cordon, toll). This claim rests on the literature "
                                 "below; the gap is itself a research_needed item."),
                        "searches": EV["road_pricing_search"]}],
    "literature": [
        {"citation": "Eliasson J (2009). A cost-benefit analysis of the Stockholm congestion charging system. Transp Res A 43:468-480.",
         "doi": "10.1016/j.tra.2008.11.014", "finding": "Traffic across the cordon fell about 20% and stayed lower."},
        {"citation": "Transport for London (2007). Central London Congestion Charging: Impacts monitoring, fifth annual report.",
         "doi": None, "finding": "Traffic entering the zone fell about 18-21%; congestion (delay) fell about 30% at first and returned toward baseline by 2006."},
        {"citation": "Cook C, Kreidieh A, Vasserman S, Allcott H, Arora N, van Sambeek F, Tomkins A, Turkel E (2025). Short-run traffic effects of New York's congestion pricing. NBER working paper.",
         "doi": None, "finding": "Reported faster travel in the CBD in early 2025 (cited from memory of the working paper; not verified here)."},
        {"citation": "NYC DOHMH (14 August 2026). Congestion pricing air quality report (Environment and Health Data Portal).",
         "doi": None, "finding": "States that traffic entering the zone fell about 10% in 2025 (secondary report, 6sqft, 17 Aug 2026)."},
    ],
    "prediction": {
        "direction": "+",
        "magnitude": ("Difference-in-differences of log monthly taxi/FHV speed, CBD minus rest of city, 2025 vs 2024: "
                      "+5% to +15%. Difference-in-differences of log monthly TLC trips (pickups plus drop-offs) in CBD "
                      "taxi zones minus non-CBD zones, 2025 vs 2024: -3% to -12%."),
        "support_if": "Speed DiD > 0 with a 95% interval above 0, and the trip-count DiD below 0.",
        "refute_if": "Speed DiD <= 0 with an interval that excludes +3%, or CBD trips rise relative to outside.",
    },
    "plan": ("Data: MTA 'CBD Taxi and For-Hire Vehicle Speeds: Beginning October 2019' (data.ny.gov 6p29-6xqn), zones "
             "CBD vs rest of city (and adjacent area as a second comparison); TLC 'Pickups and Drop-offs by Taxi Zone "
             "and Industry' (data.cityofnewyork.us c5iv-bn4s) with the CBD zone list from MTA yfdc-w5jh; MTA 'Vehicle "
             "Miles Traveled in the CBD' (jbxx-kxff) as a descriptive check; MTA CRZ entries (t6yz-b64h) descriptive only "
             "because it starts in 2025. Unit: month. Model: OLS of log value on area, calendar month, year and "
             "area x post (post = Jan 2025 on), pre-period Jan 2023 - Dec 2024, post Jan - latest 2025/2026 month; "
             "HAC (Newey-West, 3 lags) standard errors. Pre-trend check: the same model with a placebo post = Jan 2024 "
             "on 2023-2024 only. Figure: monthly CBD and comparison series with the start date marked."),
    "alternatives": [
        "Post-pandemic return-to-office trend that differs between the CBD and outer boroughs",
        "Seasonal and weather shocks (absorbed in part by calendar-month terms; common shocks by the comparison)",
        "Displacement: traffic avoiding the zone slows the comparison area, which inflates the DiD",
        "Change in TLC fleet composition or app-company pricing unrelated to the toll (the HVFHV $1.50 and taxi $0.75 per-trip CBD surcharges are part of the policy itself)",
    ],
    "prior": 0.8,
    "registrant": REGISTRANT,
}

CRZ_AIR = {
    "id": "mob-crz-air",
    "kind": "confirmation",
    "statement": ("After congestion pricing began on 5 January 2025, daily NO2 and PM2.5 at EPA regulatory monitors "
                  "inside the Congestion Relief Zone fell relative to monitors elsewhere in New York City."),
    "graph_evidence": [
        {"note": "No road-pricing findings in the graph (see mob-crz-traffic). The traffic-to-pollutant link is thin: "
                 "traffic-related pollution -> NO2 has 1 finding; traffic -> particulates and traffic -> NO2 return no "
                 "relationship. The downstream health link is dense:"},
        g("nitrogen dioxide -> asthma", "DC_F0GO0WQ|EAshH_Ko3h"),
        g("particulates -> asthma", "gX6h_gZWHH|EAshH_Ko3h"),
        g("traffic-related pollution -> asthma", "oG8Da1gCE9|EAshH_Ko3h"),
    ],
    "literature": [
        {"citation": "Johansson C, Burman L, Forsberg B (2009). The effects of congestions tax on air quality and health. Atmos Environ 43:4843-4854.",
         "doi": "10.1016/j.atmosenv.2008.09.015", "finding": "Modelled NOx emissions in inner Stockholm fell 8.5%, PM10 emissions about 13%; concentration changes were smaller."},
        {"citation": "Kelly F et al. (2011). The impact of the congestion charging scheme on air quality in London. HEI Research Report 155.",
         "doi": None, "finding": "Little detectable change in measured NOx, NO2 or PM10 attributable to the London charge."},
        {"citation": "Simeonova E, Currie J, Nilsson P, Walker R (2021). Congestion pricing, air pollution, and children's health. J Human Resources 56(4):971-996.",
         "doi": "10.3368/jhr.56.4.0218-9363R2", "finding": "Stockholm charge lowered ambient pollution 5-15% and acute asthma visits of young children."},
        {"citation": "Fraser T, Park YG, Lu D, Tayarani M, Deng H, Gao HO (2025). A first look into congestion pricing in the United States: PM2.5 impacts after six months of New York City cordon pricing. npj Clean Air 1:39.",
         "doi": "10.1038/s44407-025-00037-2", "finding": "Daily maximum PM2.5 in the CRZ fell 3.05 ug/m3 (22%) against a counterfactual, Jan-Jun 2025, 42 monitors (press coverage; paper not read in full)."},
        {"citation": "NYC DOHMH (14 August 2026). Congestion pricing air quality report.",
         "doi": None, "finding": "PM2.5, NO2, NO and black carbon in the CBD were not significantly different from the no-toll counterfactual in 2025 (secondary report)."},
    ],
    "prediction": {
        "direction": "-",
        "magnitude": ("Two-way fixed-effects DiD (site and date effects) of log daily NO2, in-zone vs other NYC monitors, "
                      "2025 vs 2022-2024: -3% to -10%. Same for PM2.5: 0% to -8%. The research disagrees on PM2.5, so "
                      "the PM2.5 prediction is weaker than the NO2 prediction."),
        "support_if": "NO2 DiD below 0 with a 95% interval below 0 (the primary test). PM2.5 is secondary.",
        "refute_if": "NO2 DiD at or above 0 with an interval that excludes -3%.",
    },
    "plan": ("Data: EPA AQS pre-generated daily files (aqs.epa.gov/aqsweb/airdata), NO2 parameter 42602 and PM2.5 "
             "parameter 88101, years 2022-2025, sites in the five NYC counties (FIPS 36005, 36047, 36061, 36081, 36085). "
             "In-zone: New York County sites south of 60th Street (by the site's latitude and the CRZ boundary). "
             "Adjacent: Manhattan north of 60th St, reported separately. Comparison: the other boroughs. Daily site mean "
             "of the primary monitor (POC averaged). Model: log(conc) ~ site FE + date FE + inzone x post, post = from "
             "5 Jan 2025. Date effects absorb weather and regional transport common to the city. Interval: block "
             "bootstrap by ISO week (1,000 draws). Placebo: post = 5 Jan 2024 on 2022-2024. A secondary check uses the "
             "DOHMH NYCCAS annual averages by UHF if a 2025 value is published. Figure: monthly in-zone minus comparison "
             "log difference with the start date marked. Design limits: few in-zone sites (likely one or two), so the "
             "result is a site-level comparison, not a zone average; regional PM2.5 dominates local traffic PM2.5."),
    "alternatives": [
        "Regional background change (wildfire smoke in 2023, transported sulfate) — absorbed by date effects only if it is spatially uniform",
        "Local construction or site-specific changes near a single in-zone monitor",
        "Long-run decline in vehicle emissions that is faster in Manhattan (fleet turnover, bus electrification)",
        "Traffic diverted to highways near comparison monitors (e.g. Cross Bronx) raises the comparison and inflates the DiD",
    ],
    "prior": 0.35,
    "registrant": REGISTRANT,
}

ASTHMA = {
    "id": "mob-asthma-pollution",
    "kind": "confirmation",
    "statement": ("Across New York City's 42 UHF neighbourhoods, asthma emergency department visit rates are higher "
                  "where NYCCAS annual average NO2 and PM2.5 are higher, and the association survives adjustment for "
                  "neighbourhood poverty."),
    "graph_evidence": [
        g("nitrogen dioxide -> asthma", "DC_F0GO0WQ|EAshH_Ko3h"),
        g("particulates -> asthma", "gX6h_gZWHH|EAshH_Ko3h"),
        g("air pollution -> asthma", "P6IzhScRdx|EAshH_Ko3h"),
        {"note": "Abstracts read on PubMed: 24858282 (NJ pediatric ED, PM2.5 RR per IQR 1.03, 1.02-1.04); "
                 "33254941 (California, NO2 per 5 ppb lag 0-30 OR 1.56, 1.43-1.70); 16984840 (Taichung, ecological "
                 "Pearson r = 0.72 NO2 vs child ED visits, one year)."},
    ],
    "literature": [
        {"citation": "Zheng X-y et al. (2015). Association between air pollutants and asthma emergency room visits and hospital admissions in time series studies: a systematic review and meta-analysis. PLoS ONE 10(9):e0138146.",
         "doi": "10.1371/journal.pone.0138146", "finding": "Pooled short-term RR: PM2.5 1.023 (1.015-1.031); NO2 1.018 (1.014-1.022) (increment as reported in the paper, read as per 10 ug/m3)."},
        {"citation": "Khreis H et al. (2017). Exposure to traffic-related air pollution and risk of development of childhood asthma. Environ Int 100:1-31.",
         "doi": "10.1016/j.envint.2016.11.012", "finding": "Asthma development: NO2 RR 1.05 (1.02-1.07) per 4 ug/m3; PM2.5 1.03 (1.01-1.05) per 1 ug/m3."},
    ],
    "prediction": {
        "direction": "+",
        "magnitude": ("Unadjusted: rate ratio of asthma ED visits per 10 ppb NO2 between 1.3 and 3 (far above the "
                      "long-term research value of about 1.05 per 4 ug/m3, i.e. about 1.25 per 10 ppb), because the "
                      "neighbourhood gradient carries poverty, housing and access to care. Poverty-adjusted: the NO2 "
                      "ratio shrinks by more than half and its interval may include 1. PM2.5: weaker than NO2 and "
                      "possibly null or negative, because PM2.5 is highest in midtown Manhattan."),
        "support_if": "Poverty-adjusted NO2 rate ratio > 1 with a 95% interval above 1.",
        "refute_if": "Poverty-adjusted NO2 rate ratio <= 1 with an interval that excludes the research value.",
    },
    "plan": ("Data: NYC DOHMH Environment and Health Data Portal (github.com/nychealth/EHDP-data, commit hash recorded) "
             "and NYC Open Data c3uy-2p5r (Air Quality, NYCCAS annual averages by UHF42). Outcome: asthma ED visit rate "
             "per 10,000 by UHF42, children 5-17 if available, else all ages; the most recent years available before "
             "2020 (average of up to three years) to avoid the COVID disruption, with the same years of NYCCAS annual NO2 "
             "and PM2.5. Covariate: percent of residents below the federal poverty level (EHDP, UHF42). Do NOT use the "
             "EHDP 'PM2.5-attributable asthma ED visits' indicator, which is derived from research concentration-response "
             "functions and would be circular. Model: OLS of log rate on pollutant (per 10 ppb NO2; per 1 ug/m3 PM2.5), "
             "then adding poverty; HC3 standard errors; sensitivity with borough fixed effects and with both pollutants. "
             "Figure: scatter of UHF neighbourhoods (log rate vs NO2) coloured by poverty, with the research slope drawn "
             "through the city mean."),
    "alternatives": [
        "Poverty and the conditions that travel with it (housing quality, pests, mould, smoking, access to primary care)",
        "Ecological fallacy: residence of ED patients vs where exposure occurs; UHF averages hide within-area variation",
        "Spatial autocorrelation: the Bronx cluster drives the fit (borough FE sensitivity)",
        "Diagnosis and ED-use practices that vary with insurance",
    ],
    "prior": 0.35,
    "registrant": REGISTRANT,
}

SPEEDCAM = {
    "id": "mob-speedcam-247",
    "kind": "confirmation",
    "statement": ("Extending New York City's school-zone speed cameras to 24-hour, 7-day operation on 1 August 2022 "
                  "reduced injury crashes in the newly enforced hours (weekday 10 pm-6 am and weekends) relative to "
                  "the weekday 6 am-10 pm hours that were already enforced."),
    "graph_evidence": [
        {"note": "No speed-camera concept in the graph; variable search found 7 associations in 6 studies.",
         "findings": EV["speed_camera_variables"]},
        {"note": "Abstract check: PMID 17666698 (Barcelona) reports RR 0.73 (0.63-0.85) for collisions on the beltway "
                 "with cameras; the graph's second association from that paper (RR 0.99, 0.90-1.10, labelled 'people "
                 "injured among the population affected by the speed cameras') is the comparison arterial roads without "
                 "cameras, so it is mis-extracted. PMID 14693888 (South Wales, mobile cameras) reports injurious crash "
                 "rate ratio 0.49 (0.42-0.57) within 500 m routes, with decreases in day and night."},
    ],
    "literature": [
        {"citation": "Wilson C, Willis C, Hendrikz JK, Le Brocque R, Bellamy N (2010). Speed cameras for the prevention of road traffic injuries and deaths. Cochrane Database Syst Rev (10):CD004607.",
         "doi": "10.1002/14651858.CD004607.pub4", "finding": "Reductions in injury crashes near camera sites of roughly 8-49%, fatal and serious 11-44%."},
        {"citation": "NYC DOT (2023, 2025). Speed camera program reports and press releases.",
         "doi": None, "finding": "About 7.6% fewer injuries in the new overnight and weekend hours at camera locations in the first year (agency figure)."},
    ],
    "prediction": {
        "direction": "-",
        "magnitude": ("Citywide, because cameras cover a small share of street length, the ratio of ratios (injury "
                      "crashes in new hours / old hours, Aug 2022-Jul 2023 vs Aug 2021-Jul 2022) between 0.92 and 1.00. "
                      "Persons injured and pedestrians injured are secondary outcomes."),
        "support_if": "Ratio of ratios below 1 with a 95% interval below 1.",
        "refute_if": "Ratio of ratios at or above 1 with an interval that excludes 0.97.",
    },
    "plan": ("Data: NYPD Motor Vehicle Collisions - Crashes (data.cityofnewyork.us h9gi-nx95), aggregated by SoQL to "
             "counts by month, day of week and hour. Exposure groups: new hours = Mon-Fri 22:00-05:59 and all Sat-Sun; "
             "old hours = Mon-Fri 06:00-21:59. Outcomes: crashes with >= 1 person injured or killed (primary), persons "
             "injured, pedestrians injured, persons killed. Model: Poisson GLM of monthly counts on group x month fixed "
             "effects ... specifically log E[count] = group + month(calendar) + group x post, on a 24-month window Aug "
             "2021-Jul 2023, with Pearson-scaled (quasi-Poisson) standard errors. Event-study figure of the new/old ratio by "
             "month, Jan 2020 - Dec 2024, to show pre-trends. Placebo: fake start 1 Aug 2021 on Aug 2020-Jul 2022. "
             "Mechanism check: camera tickets ('PHTO SCHOOL ZN SPEED VIOLATION') by issue hour in Open Parking and Camera "
             "Violations (nc67-uf89) should appear in the new hours from Aug 2022. Design limits: citywide counts dilute a "
             "local effect; night and weekend travel recovered from the pandemic at a different pace from weekday daytime "
             "travel, which can bias the DiD in either direction; no exposure (vehicle-miles) by hour."),
    "alternatives": [
        "Differential post-pandemic recovery of night and weekend traffic (nightlife) relative to weekday daytime",
        "Changes in NYPD crash reporting or in the share of crashes with location and time recorded",
        "E-bike and moped growth, concentrated in evening delivery hours",
        "Regression to the mean if 2021-22 night crash levels were unusually high",
    ],
    "prior": 0.3,
    "registrant": REGISTRANT,
}

if __name__ == "__main__":
    for rec in (CRZ_TRAFFIC, CRZ_AIR, ASTHMA, SPEEDCAM):
        print(claims.register(rec))
