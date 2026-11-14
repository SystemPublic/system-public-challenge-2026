"""Outcomes for the neighbourhood claims. Numbers are read from the result files, not typed in.

python -m analyses.neighbourhood.outcomes <claim id>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "neighbourhood"


def r3(x):
    return round(float(x), 3)


def vacant():
    r = json.loads((D / "vacant_shootings_results.json").read_text())
    a, u = r["adjusted_per_quintile"], r["unadjusted_per_quintile"]
    sd, pr, ci = r["adjusted_per_sd"], r["adjusted_private_per_sd"], r["adjusted_city_owned_per_sd"]
    q = r["quintiles"]
    graph = json.loads((D / "graph_vacant.json").read_text())
    return {
        "id": "nbhd-vacant-shootings",
        "verdict": "confirmed",
        "city_effect": {"label": "NYC 2020 tracts: shootings 2019-2024 per resident, IRR per quintile step of vacant-land share, "
                                 "adjusted for poverty, log density, borough (negative binomial, HC1 SE)",
                        "estimate": r3(a["estimate"]), "lo": r3(a["lo"]), "hi": r3(a["hi"]),
                        "scale": "IRR per quintile step", "null": 1, "n": r["n_tracts"]},
        "graph_effect": {"label": "Philadelphia block groups 2002-2006: aggravated assault IRR per category shift of vacant properties "
                                  "(Branas, Rubin, Guo 2013, PMID 23814668; graph association 3rfxckzPtm)",
                         "estimate": 1.18, "lo": 1.12, "hi": 1.25, "scale": "IRR per category", "null": 1},
        "sources": r["sources"] + json.loads((D / "sources_base.json").read_text()) + [
            {"kind": "sysgraph", "api_version": "v1.0", "dataset_version": "Dataverse v2.1, doi:10.7910/DVN/7V6JDO",
             "file": "data/derived/neighbourhood/graph_vacant.json", "n_variables": len(graph)}],
        "prediction_scored": (
            f"partial. The direction was right and the registered support condition holds (adjusted IRR {a['estimate']:.2f}, "
            f"95% CI {a['lo']:.2f}-{a['hi']:.2f}). The magnitude was wrong: I predicted 1.00-1.10, weaker than Philadelphia, "
            f"and the NYC estimate equals the Philadelphia between-unit estimate (1.18). Adjustment for poverty did not attenuate it "
            f"(unadjusted {u['estimate']:.2f})."),
        "settle": (
            "The tract association is ecological and cannot show that vacant lots cause shootings in NYC. Three things would settle "
            "whether the Philadelphia causal result transfers: (1) a lot-level design in NYC, such as shootings within 100-200 m of "
            "vacant lots before and after they are built on, cleaned or fenced, using DOB new-building permits and DSNY lot-cleaning "
            "records for timing; (2) a split of vacant lots into those staged for construction (open DOB new-building job) and those "
            "vacant for 36 months or more, the exposure used in the Philadelphia and opioid studies; (3) the same model with "
            "pre-period shootings (2010-2014) to test reverse causation."),
        "research_needed": [
            {"question": "Do NYC vacant lots that are greened or cleaned see fewer nearby shootings, as in the Philadelphia trial?",
             "data": "MapPLUTO land use 11 by year (PLUTO archive), DSNY lot cleaning, GreenThumb gardens, NYPD shootings",
             "design": "difference-in-differences around treated versus matched untreated lots, 100-200 m buffers", "priority": "high"},
            {"question": "Is the association carried by long-vacant lots or by lots staged for construction?",
             "data": "PLUTO archive versions 2014-2026 (vacancy duration), DOB NOW and BIS job filings (new building)",
             "design": "tract or lot model with vacancy duration and permit status as separate exposures", "priority": "high"},
            {"question": "Why does private vacant land carry the association while City-owned vacant land does not?",
             "data": "PLUTO ownertype, HPD and DCAS land inventories, lot condition from aerial photographs",
             "design": "exploratory; describe lot condition by owner type, then register a test", "priority": "medium"},
            {"question": "Is the shape of the dose-response a threshold (any scattered vacant lots) rather than linear in vacant area?",
             "data": "this analysis, with counts of vacant lots under 0.25 acre", "design": "spline in vacant share; lot counts by size class",
             "priority": "medium"},
        ],
        "figures": ["figures/neighbourhood/vacant_shootings.png"],
        "notes": (
            f"Unit: {r['n_tracts']} 2020 census tracts with at least 500 residents and lot area in MapPLUTO 26v2. "
            f"Vacant land (land use 11) is {100 * r['citywide_vacant_share_of_lot_area']:.1f}% of NYC tax-lot area. "
            f"{r['n_shootings_in_tracts']} of {r['n_shootings_total']} shooting incidents 2019-2024 fell in the analysed tracts. "
            f"Shooting rates rose from {q[0]['rate_per_10k_per_year']:.2f} per 10,000 residents per year in the lowest vacant-share "
            f"quintile to {q[4]['rate_per_10k_per_year']:.2f} in the highest. The association held without Staten Island "
            f"(IRR {r['adjusted_per_quintile_no_staten_island']['estimate']:.2f}) and after adding the non-Hispanic white share "
            f"(IRR {r['adjusted_plus_race_per_quintile']['estimate']:.2f}). It was not linear in the share: per SD of the untransformed "
            f"share the IRR was {sd['estimate']:.2f} ({sd['lo']:.2f}-{sd['hi']:.2f}), because the top quintile runs from 2.8% to 94% "
            f"and the tracts with the most vacant land are industrial or waterfront tracts with few residents. "
            f"Exploratory, not registered: private vacant land IRR {pr['estimate']:.2f} per SD ({pr['lo']:.2f}-{pr['hi']:.2f}); "
            f"City-owned vacant land {ci['estimate']:.2f} ({ci['lo']:.2f}-{ci['hi']:.2f}). "
            "Data note: in Shootings (2006-Present), 5ucz-vwe8, the latitude column holds longitudes and the longitude column holds "
            "latitudes (checked 12 November 2026); the script detects and swaps them. Distinct incidents per year in 5ucz-vwe8 match "
            "the archived 833y-fsy8 table within one incident. The registration's literature note corrects the brief: the Branas et al. "
            "2018 greening trial was published in PNAS, not JAMA Network Open. The PNAS trial is not present as a variable in the graph; "
            "the graph holds the cross-sectional Philadelphia study, the abandoned-housing trial (South et al. 2023) and the Rochester "
            "demolition study."),
    }


def rodents():
    r = json.loads((D / "rodents_asthma_results.json").read_text())
    p, v = r["primary"], r["validity"]
    a, u = p["adjusted"], p["unadjusted"]
    insp, comp, chs = r["inspections_vs_latest"], r["complaints_vs_latest"], r["chs_inside"]
    base = json.loads((D / "sources_base.json").read_text())
    c311 = json.loads((D / "complaints311_sources.json").read_text())
    shrink = 1 - a["estimate"] / u["estimate"]
    return {
        "id": "nbhd-rodents-asthma",
        "verdict": "confirmed",
        "city_effect": {"label": "UHF42 (n=42): change in log asthma ED rate age 5-17 (2017) per SD of % homes with mice or rats in the "
                                 "building (NYCHVS 2017), adjusted for poverty % (2013-17) and renter housing problems % (2017); OLS, HC3",
                        "estimate": r3(a["estimate"]), "lo": r3(a["lo"]), "hi": r3(a["hi"]), "scale": "log rate per SD", "null": 0,
                        "n": p["n"]},
        "graph_effect": {"label": "Urban children with asthma, mouse-sensitised: odds of asthma-related health care use per tenfold bed "
                                  "mouse allergen (Torjusen et al. 2013, PMID 23067271; graph variable IET_Lwkf52)",
                         "estimate": 1.87, "lo": 1.21, "hi": 2.88, "scale": "OR per tenfold allergen", "null": 1},
        "sources": r["sources"] + [s for s in c311 if "Rodent" in json.dumps(s.get("query", {}))] + [
            {"kind": "sysgraph", "api_version": "v1.0", "dataset_version": "Dataverse v2.1, doi:10.7910/DVN/7V6JDO",
             "file": "data/derived/neighbourhood/graph_rodent.json"}],
        "prediction_scored": (
            f"partial. The direction and the unadjusted magnitude were right (Spearman rho {p['spearman_rho']:.2f}; predicted 0.5-0.8). "
            f"I expected adjustment to remove most of the association and leave an unsettled verdict. It did not: the coefficient fell by "
            f"{100 * shrink:.0f}%, from {u['estimate']:.2f} to {a['estimate']:.2f} (95% CI {a['lo']:.2f} to {a['hi']:.2f}), above the predicted "
            f"0.00-0.20, and the registered support condition holds."),
        "settle": (
            "The NYC estimate is ecological across 42 neighbourhoods, and the rodent measure is almost collinear with housing problems "
            f"(rho {v['rho_hvs_vs_housing_problems']:.2f}) and strongly related to poverty (rho {v['rho_hvs_vs_poverty']:.2f}). It cannot show "
            "that rodent allergen causes the excess ED visits. What would settle the bridge: (1) household-level data in NYC linking measured "
            "mouse allergen or reported rodents to child asthma ED use, for example the NYC KIDS survey microdata or a cohort such as "
            "the Columbia Center for Children's Environmental Health; (2) the same neighbourhood model with race and ethnicity, smoking, "
            "PM2.5 and primary-care access added; (3) a within-neighbourhood test, such as change in asthma ED rates after integrated pest "
            "management in NYCHA developments."),
        "research_needed": [
            {"question": "Does household rodent exposure explain part of the neighbourhood gradient in child asthma ED visits in NYC?",
             "data": "NYC KIDS survey microdata (rodents in home, asthma attack), SPARCS ED visits by ZIP, NYCHVS 2021/2023 microdata",
             "design": "multilevel model, household exposure nested in neighbourhood, adjusted for poverty, race, smoking", "priority": "high"},
            {"question": "Do the city's operational rodent measures (inspections, 311) measure household exposure at all?",
             "data": "DOHMH Rodent Inspection p937-wjvj, 311 rodent complaints, NYCHVS rodents in building by sub-borough",
             "design": "measurement-validity study against survey or allergen measurements; reporting propensity model", "priority": "high"},
            {"question": "Does rodent abatement (Rat Mitigation Zones, NYCHA pest management) change child asthma ED rates?",
             "data": "RMZ boundaries and dates, SPARCS ED rates by ZIP and quarter", "design": "difference-in-differences", "priority": "medium"},
        ],
        "figures": ["figures/neighbourhood/rodents_asthma.png"],
        "notes": (
            f"Primary model per registration: n = {p['n']} UHF neighbourhoods, 2017 data (latest year common to the NYCHVS rodent and "
            "housing measures and the SPARCS asthma ED rates on the EHDP portal). Adding the cockroach share left the rodent coefficient at "
            f"{r['primary_plus_cockroach']['adjusted']['estimate']:.2f}; the adult ED outcome gave {r['adult_outcome']['adjusted']['estimate']:.2f} "
            f"({r['adult_outcome']['adjusted']['lo']:.2f} to {r['adult_outcome']['adjusted']['hi']:.2f}). The CHS 2012 measure of adults "
            f"reporting mice or rats inside gave {chs['adjusted']['estimate']:.2f} ({chs['adjusted']['lo']:.2f} to {chs['adjusted']['hi']:.2f}). "
            "The city's operational rodent data behaved differently. The share of DOHMH initial inspections failed for rat activity, 2022-2024, "
            f"was barely related to the survey measure (rho {v['rho_hvs_vs_inspection_fail']:.2f}) and not to child asthma ED rates in 2023 "
            f"(adjusted {insp['adjusted']['estimate']:.2f}, {insp['adjusted']['lo']:.2f} to {insp['adjusted']['hi']:.2f}). 311 rodent complaints per "
            f"1,000 residents correlated with the survey measure at rho {v['rho_hvs_vs_311_rodent']:.2f} and with asthma at rho "
            f"{comp['spearman_rho']:.2f}, but not after adjustment ({comp['adjusted']['estimate']:.2f}, {comp['adjusted']['lo']:.2f} to "
            f"{comp['adjusted']['hi']:.2f}). Inspections and complaints mostly record rats outdoors and around buildings; the research concerns "
            "indoor mouse allergen among sensitised children. The survey measure joins mice and rats. The bridge is therefore graph "
            "(household mouse allergen to asthma morbidity) plus city survey data (neighbourhood rodents to child asthma ED rates), and it "
            "does not pass through the city's operational rodent datasets. Rodent inspections were aggregated by ZIP code; each ZIP's mean "
            "inspection coordinate was assigned to a UHF42 polygon (UHF neighbourhoods are unions of ZIP codes). Alternatives not handled: "
            "race and ethnicity, smoking, outdoor air pollution, primary-care access."),
    }


def noise():
    r = json.loads((D / "noise311_results.json").read_text())
    c, cs, cn = r["contrast_res"], r["contrast_street"], r["contrast_res_nhw"]
    o, rho = r["ols"], r["spearman"]
    nm = json.loads((D / "noise_map_source.json").read_text())
    c311 = json.loads((D / "complaints311_sources.json").read_text())
    base = json.loads((D / "sources_base.json").read_text())
    res, st = o["res"], o["street"]
    return {
        "id": "nbhd-noise311-exposure",
        "verdict": "unsettled",
        "city_effect": {"label": "2020 tracts: beta(rent change) - beta(modelled transport noise) in OLS of log(1 + residential noise "
                                 "complaints per 1,000 residents per year, 2022-2024), per SD, borough effects; tract bootstrap 95% CI",
                        "estimate": r3(c["estimate"]), "lo": r3(c["lo"]), "hi": r3(c["hi"]), "scale": "difference in log units per SD",
                        "null": 0, "n": r["n_tracts"]},
        "graph_effect": {"label": "Road traffic noise and prevalent hypertension, OR per 10 dB(A) (PMID 24952459; relationship "
                                  "cEPG6i4Yq1|fo-h4u_aJp, 12 findings in 8 studies). Shown for the research exposure scale; the graph holds "
                                  "no finding on noise complaints.",
                         "estimate": 1.11, "lo": 1.00, "hi": 1.23, "scale": "OR per 10 dB(A)", "null": 1},
        "sources": c311 + base + [
            {"kind": "map-service", "url": nm["service"], "layer": nm["layer"], "zoom": nm["zoom"], "fetched": nm["fetched"],
             "citation": nm["citation"]},
            r["liquor_source"],
            {"kind": "sysgraph", "api_version": "v1.0", "dataset_version": "Dataverse v2.1, doi:10.7910/DVN/7V6JDO",
             "files": ["data/derived/neighbourhood/graph_noise.json", "data/derived/neighbourhood/graph_noise_relationships.json"]}],
        "prediction_scored": (
            f"partial. Two of three parts hit: residential complaint rates were weakly related to modelled transport noise "
            f"(Spearman rho {rho['res_rate~noise_mean_db']['rho']:.2f}; predicted below 0.25), and street and vehicle complaints were "
            f"positively related to it (rho {rho['street_rate~noise_mean_db']['rho']:.2f}; predicted 0.15-0.45). The registered contrast "
            f"missed: rent change had no association with residential complaints ({res['z_d_logrent']['b']:.3f} per SD), so the contrast "
            f"was {c['estimate']:.2f} (95% CI {c['lo']:.2f} to {c['hi']:.2f}) against a predicted +0.05 to +0.30."),
        "settle": (
            "Neither the registered contrast nor its opposite is supported, and the deeper question, whether complaints measure exposure, "
            "cannot be answered with a transport noise model because residential complaints are mostly about neighbours. It would be "
            "settled by measured sound levels at a sample of addresses or blocks stratified by complaint rate and by demographic change: "
            "SONYC sensor Leq series (if released at block level), a DEP or DOHMH monitoring campaign, or smartphone dosimetry. With measured "
            "levels, complaints per resident can be modelled as level times reporting propensity, and propensity estimated from repeated "
            "reports of the same incident (the method of the 2025 Annals of Applied Statistics paper on 311 reporting bias)."),
        "research_needed": [
            {"question": "What is the relation between 311 noise complaints and measured sound levels at the same places and hours?",
             "data": "SONYC sensor levels (NYU), DEP inspection readings for noise complaints, 311 erm2-nwe9 with timestamps",
             "design": "matched hourly comparison by sensor site; complaints per resident against Leq and Lnight", "priority": "high"},
            {"question": "Does demographic change raise reporting propensity for the same noise?",
             "data": "311 duplicate reports per incident, ACS change 2008-12 to 2018-22, measured levels",
             "design": "reporting-propensity model (multiple reports of one incident) by tract change", "priority": "high"},
            {"question": "Can neighbour noise exposure be modelled at all from building data (party walls, building age, density)?",
             "data": "PLUTO building class and year, DOB complaints, HVS", "design": "exploratory model, then validation against measurements",
             "priority": "medium"},
            {"question": "Do health studies in NYC that use 311 complaints as exposure reach different conclusions from those using modelled dB?",
             "data": "literature search; SPARCS hypertension or sleep outcomes by tract", "design": "systematic comparison",
             "priority": "medium"},
        ],
        "figures": ["figures/neighbourhood/noise311.png"],
        "notes": (
            f"n = {r['n_tracts']} 2020 tracts with at least 500 residents and complete ACS change measures. 311 totals 2022-2024 in tracts: "
            f"residential {r['totals']['Noise - Residential']:,}, street/sidewalk {r['totals']['Noise - Street/Sidewalk']:,}, vehicle "
            f"{r['totals']['Noise - Vehicle']:,}, commercial {r['totals']['Noise - Commercial']:,}, DEP 'Noise' {r['totals']['Noise']:,}, "
            f"helicopter {r['totals']['Noise - Helicopter']:,}. In the joint model for residential complaints the largest coefficients were "
            f"poverty share ({res['z_poverty']['b']:.2f} per SD) and change in the non-Hispanic white share ({res['z_d_nhw']['b']:.2f}); modelled "
            f"noise was {res['z_noise_mean_db']['b']:.2f} ({res['z_noise_mean_db']['lo']:.2f} to {res['z_noise_mean_db']['hi']:.2f}). A secondary "
            f"contrast that the registered statement names but the support rule does not use, change in non-Hispanic white share minus "
            f"modelled noise, was {cn['estimate']:.2f} (95% CI {cn['lo']:.2f} to {cn['hi']:.2f}). This agrees with Legewie and Schaeffer (2016) "
            f"that complaints follow ethnoracial change, but it is reported as secondary, not as the test. For street and vehicle complaints, "
            f"modelled noise ({st['z_noise_mean_db']['b']:.2f}) and liquor licences ({st['z_log_bars']['b']:.2f}) both mattered, and the "
            f"rent-minus-noise contrast was negative ({cs['estimate']:.2f}, {cs['lo']:.2f} to {cs['hi']:.2f}): street complaints partly track "
            f"the sources the noise model contains. Commercial complaints followed liquor licences (rho "
            f"{rho['comm_rate~onprem_licences']['rho']:.2f}). Using the energy-mean Leq in place of the class mean gave a modelled-noise "
            f"coefficient of {r['sensitivity_leq_res']['z_noise_leq_db']:.2f}. The noise map was read from rendered tiles of the US DOT "
            "service by legend colour at zoom 12 (about 29 m pixels; deeper levels are not cached); areas below 45 dB are unpainted and were "
            "set to 40 dB. SONYC data were not used: no public block-level sound-level file was located in this session. The ACS change "
            "measures come from the Census Bureau summary files because the Census API now requires a key; 2008-2012 values on 2010 tracts "
            "were moved to 2020 tracts by land-area weights from the Census relationship file. Rents are nominal."),
    }


OUTCOMES = {"nbhd-vacant-shootings": vacant, "nbhd-rodents-asthma": rodents, "nbhd-noise311-exposure": noise}

if __name__ == "__main__":
    for cid in sys.argv[1:]:
        print(claims.outcome(OUTCOMES[cid]()))
