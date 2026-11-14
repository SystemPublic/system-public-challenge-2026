"""Registrations for the neighbourhood claims (written before any city query for them).

Run once per id: python -m analyses.neighbourhood.register <id>
Registrations are never edited; a changed plan gets a new id with "supersedes".
"""
import sys

from concord import claims

REGISTRANT = "claude-code agent (neighbourhood), for Jeff Vernon"

CLAIMS = {
    "nbhd-vacant-shootings": {
        "id": "nbhd-vacant-shootings",
        "kind": "confirmation",
        "statement": (
            "Across New York City census tracts, a larger share of lot area in vacant land (MapPLUTO land use 11) "
            "is associated with more NYPD-recorded shootings per resident, after adjustment for poverty, "
            "population density and borough, but the association is weaker than the Philadelphia estimates."
        ),
        "graph_evidence": [
            {"association_id": "3rfxckzPtm", "study_id": "VViyzL1JcL", "concepts": ["vacant properties", "assaultive violence"],
             "n_findings": 1, "n_studies": 1, "direction": "+",
             "summary": "Philadelphia, 1,816 block groups 2002-2006, mixed negative binomial: IRR 1.18 (95% CI 1.12-1.25) "
                        "for aggravated assault per category shift of vacant properties, between block groups (Branas, Rubin, Guo 2013).",
             "pubmed_ids": [23814668]},
            {"association_id": "Q5b4AdFgrV", "study_id": "cuHN_rYwtF", "concepts": ["maintained vacant lots", "adolescent homicide"],
             "n_findings": 1, "n_studies": 1, "direction": "-",
             "summary": "Philadelphia case-control (143 cases): maintained vacant lots at the location OR 0.17 (0.03-0.81) for adolescent homicide (Culyba et al. 2016).",
             "pubmed_ids": [26954939]},
            {"association_id": "G6ohTa-WnC", "study_id": "TBKYMeK3EY", "concepts": ["abandoned housing remediation", "shootings"],
             "n_findings": 1, "n_studies": 1, "direction": "-",
             "summary": "Philadelphia cluster RCT of abandoned-house remediation: shootings -6.96% (95% CI -15.32% to +3.03%), gun assaults -13.1% (South et al. 2023).",
             "pubmed_ids": [36469329]},
            {"variable": "Demolishing abandoned buildings", "concepts": ["demolition", "firearm violence"], "direction": "-",
             "summary": "Rochester NY grid cells: one demolition IRR 0.86 (0.83-0.90) for shootings the next year (Jay et al. 2022).",
             "pubmed_ids": [34876475]},
            {"variable": "abandoned property count", "concepts": ["abandoned property", "aggravated assault"], "direction": "+",
             "summary": "Northeastern US city: abandoned property count IRR 1.28 (1.01-2.01) for aggravated assault (Lardier et al. 2021).",
             "pubmed_ids": [34210249]},
        ],
        "literature": [
            {"citation": "Branas CC, South E, Kondo MC, et al. Citywide cluster randomized trial to restore blighted vacant land and its effects on violence, crime, and fear. PNAS 2018;115(12):2946-51.",
             "doi": "10.1073/pnas.1718503115",
             "finding": "541 Philadelphia vacant lots randomised; greening reduced gun violence by 29.1% (P<0.001) in neighbourhoods below the poverty line. "
                        "Not found as a variable in the System graph. (The task brief cites this trial as JAMA Netw Open 2018; that journal carried the related mental-health trial, South et al. 2018.)"},
        ],
        "prediction": {
            "direction": "+",
            "magnitude": "Adjusted IRR per quintile step of tract vacant-land share between 1.00 and 1.10 (Philadelphia between-unit estimate 1.18 per category). "
                         "Unadjusted IRR larger, 1.10-1.30.",
            "support_if": "Adjusted IRR per quintile step has a 95% CI with lower bound above 1.00.",
            "refute_if": "Adjusted IRR per quintile step has a 95% CI with upper bound below 1.00 (contested). A CI spanning 1.00 is unsettled.",
        },
        "plan": (
            "Unit: 2020 census tracts (DCP 63ge-mke6 geometry) with at least 500 residents. Exposure: share of tax-lot area with landuse '11' "
            "in MapPLUTO (64uk-42ks, aggregated by bct2020 with SoQL; version recorded), entered as quintiles (per-step IRR) and, secondarily, per SD. "
            "Secondary exposures: vacant lots per 1,000 lots; vacant land owned by the City (ownertype 'C') versus private. "
            "Outcome: shooting incidents 2019-2024 from Shootings (2006-Present) 5ucz-vwe8, located by latitude/longitude into tracts; "
            "833y-fsy8 (historic archive) used as a cross-check of counts for overlapping years. "
            "Covariates: ACS 2018-2022 5-year total population (offset), percent below poverty, log population density, borough fixed effects. "
            "Model: negative binomial GLM (statsmodels), robust SE. Report unadjusted and adjusted IRR. "
            "Figure: binned scatter of shootings per 10,000 by vacant-share quintile within poverty terciles, with the Philadelphia IRR drawn beside the NYC estimate."
        ),
        "alternatives": [
            "Poverty and disinvestment cause both vacancy and violence (confounding); adjustment is coarse.",
            "NYC vacant lots are often staged for construction in rising-rent areas, which have falling violence; this dilutes or reverses the association.",
            "Large undeveloped natural or industrial lots (Staten Island, waterfront) add vacant area with few residents and few shootings.",
            "Reverse causation: violence depresses land values and delays building.",
            "Ecological inference: a tract association says nothing about risk next to a lot; the RCT evidence is place-level and causal.",
        ],
        "prior": 0.4,
        "registrant": REGISTRANT,
    },
    "nbhd-noise311-exposure": {
        "id": "nbhd-noise311-exposure",
        "kind": "conflict",
        "statement": (
            "311 noise complaint rates by census tract are a poor measure of noise exposure: they align weakly with modelled "
            "transportation noise and more strongly with neighbourhood change (rent increase and growth of the non-Hispanic white share)."
        ),
        "graph_evidence": [
            {"relationship_id": "cEPG6i4Yq1|fo-h4u_aJp", "concepts": ["traffic noise", "arterial hypertension"], "n_findings": 12, "n_studies": 8,
             "direction": "+", "summary": "Road traffic noise and hypertension; e.g. OR 1.11 per 10 dB(A) (1.00-1.23) (PMID 24952459); incident hypertension RR 1.13 (1.02-1.24) in ESCAPE cohorts (PMID 28417138).",
             "pubmed_ids": [24952459, 28417138, 33733673, 18335099, 21183206]},
            {"relationship_id": "cEPG6i4Yq1|XW9F7OPopQ", "concepts": ["traffic noise", "stroke"], "n_findings": 14, "n_studies": 8, "direction": "+",
             "summary": "Traffic noise and stroke (count from the relationship record).", "pubmed_ids": []},
            {"relationship_id": "cEPG6i4Yq1|nDIFXeS4Xr", "concepts": ["traffic noise", "sleep"], "n_findings": 3, "n_studies": 2, "direction": "+",
             "summary": "High road traffic noise and poorer sleep health OR 1.13 (1.06-1.20) (PMID 35513113).", "pubmed_ids": [35513113, 29078795]},
            {"variable_id": "pMSKrA677f", "concepts": ["aircraft and road noise", "hypertension"], "direction": "+",
             "summary": "Aircraft plus road noise >=45 dB: incident hypertension HR 1.39 (1.14-1.70) (PMID 30078646).", "pubmed_ids": [30078646]},
            {"note": "The graph holds no finding on noise complaints as a measure. The research evidence is on measured or modelled dB, so the conflict is about whether the city's common proxy measures the research exposure."},
        ],
        "literature": [
            {"citation": "Legewie J, Schaeffer M. Contested boundaries: explaining where ethnoracial diversity provokes neighborhood conflict. Am J Sociol 2016;122(1):125-61.",
             "doi": "10.1086/686942", "finding": "NYC 311 neighbour complaints (loud music, parties) are about 26% higher at fuzzy ethnoracial boundaries than in homogeneous areas or at sharp boundaries."},
            {"citation": "Kontokosta CE, Hong B. Bias in smart city governance: how socio-spatial disparities in 311 complaint behavior impact the fairness of data-driven decisions. Sustain Cities Soc 2021;64:102503.",
             "doi": "10.1016/j.scs.2020.102503", "finding": "311 reporting propensity differs by income, race and tenure in NYC."},
            {"citation": "Estimating reporting bias in 311 complaint data. Ann Appl Stat 2025.", "doi": "10.1214/24-aoas2003",
             "finding": "Reporting rates for the same underlying incident vary across NYC neighbourhoods."},
            {"citation": "Zheng Y, Liu T, Wang Y, et al. Diagnosing New York City's noises with ubiquitous data. UbiComp 2014.", "doi": "10.1145/2632048.2632102",
             "finding": "Uses 311 noise complaints as the target for inferring noise, i.e. treats complaints as a measure."},
            {"citation": "Bello JP, Silva C, Nov O, et al. SONYC: a system for monitoring, analyzing, and mitigating urban noise pollution. Commun ACM 2019;62(2):68-77.",
             "doi": "10.1145/3224204", "finding": "Sensor network in NYC; argues complaints are an incomplete signal of noise."},
            {"citation": "NY State Comptroller. Silencing excessive NYC noise (2018).", "doi": None,
             "finding": "311 noise complaints rose from about 200,000 (2010) to 384,000 (2015); few complaints are measured."},
        ],
        "prediction": {
            "direction": "+",
            "magnitude": "In a joint OLS of log(1 + residential noise complaints per 1,000 residents, 2022-2024) on standardised predictors with borough fixed effects, "
                         "the coefficient on rent change (ACS 2008-12 to 2018-22) exceeds the coefficient on modelled transportation noise by 0.05-0.30 log units per SD. "
                         "Spearman rho between residential complaint rate and modelled noise below 0.25. Street/vehicle complaints show a positive association with modelled noise (rho 0.15-0.45).",
            "support_if": "The difference (rent-change coefficient minus modelled-noise coefficient) has a bootstrap 95% CI above 0.",
            "refute_if": "The difference has a 95% CI below 0 (complaints track modelled noise more than change): contested. Spanning 0: unsettled.",
        },
        "plan": (
            "Unit: 2020 census tracts with at least 500 residents. Complaints: 311 Service Requests 2020-present (erm2-nwe9), created 2022-01-01 to 2024-12-31, "
            "complaint_type 'Noise - Residential' (primary), also 'Noise - Street/Sidewalk' + 'Noise - Vehicle', 'Noise - Commercial', and all types beginning 'Noise'; "
            "aggregated with SoQL group by latitude, longitude and complaint_type, then joined to tracts locally. "
            "Modelled noise: US DOT/BTS National Transportation Noise Map 2020, road+aviation+rail LAeq 24h, read from the geo.dot.gov tile service "
            "(classes 45-50, 50-55, 55-60, 60-70, 70-80, 80-90, >90 dB) and summarised as tract-mean class midpoint (below 45 dB set to 40) and share of area >=60 dB. "
            "Nightlife: active on-premises liquor licences per tract (NY State Liquor Authority data, data.ny.gov). "
            "Neighbourhood change: change in median gross rent (B25064, inflation not adjusted, in log) and in non-Hispanic white share (B03002) from ACS 2008-2012 (2010 tracts, "
            "area-weighted to 2020 tracts with the Census relationship file) to ACS 2018-2022. Controls: log population density, poverty share, borough fixed effects. "
            "Bootstrap tracts (1,000 draws) for the coefficient difference. SONYC sensor data used only if a public levels file is found; otherwise noted as unavailable. "
            "Figure: tract maps of complaint rate and modelled noise; coefficient plot with the research dose-response (per 10 dB) noted beside it."
        ),
        "alternatives": [
            "Residential complaints concern neighbour noise, which the transport noise map does not model; a weak link to modelled noise is then expected even if complaints measure exposure to their own source.",
            "Rent change and nightlife are collinear (new bars follow rising rents); the rent coefficient may carry real noise from new venues.",
            "Population density drives both complaints and actual neighbour noise.",
            "The noise map is coarse (classes, no values under 45 dB) and models traffic volume, not observed levels.",
            "Reporting propensity differs by language, trust in government and tenure, independent of change.",
        ],
        "prior": 0.45,
        "registrant": REGISTRANT,
    },
    "nbhd-rodents-asthma": {
        "id": "nbhd-rodents-asthma",
        "kind": "confirmation",
        "statement": (
            "Across NYC's 42 UHF neighbourhoods, a higher share of homes with mice or rats in the building is associated with higher "
            "asthma emergency department visit rates in children aged 5-17, and the association remains after adjustment for poverty and housing problems."
        ),
        "graph_evidence": [
            {"variable_id": "IET_Lwkf52", "concepts": ["mouse allergen exposure", "asthma morbidity"], "direction": "+",
             "summary": "Baltimore inner-city preschool children, mouse-sensitised and highly exposed: ED visit OR 2.1 (1.1-4.1), hospitalisation OR 36.6 (4.1-327) (Matsui et al. 2006).",
             "pubmed_ids": [17069107]},
            {"variable_id": "IET_Lwkf52", "concepts": ["mouse allergen", "asthma-related health care use"], "direction": "+",
             "summary": "150 urban children: each tenfold increase in bed mouse allergen OR 1.87 (1.21-2.88) for asthma-related health care use among mouse-sensitised children only (Torjusen et al. 2013).",
             "pubmed_ids": [23067271]},
            {"variable_id": "u5QsWFrJ4v", "concepts": ["school mouse allergen", "asthma symptom days"], "direction": "+",
             "summary": "School mouse allergen exposure OR 1.27 (1.05-1.54) for an asthma symptom day.", "pubmed_ids": [27893060]},
            {"variable_id": "OrMVbVvbil", "concepts": ["mouse allergen reduction", "symptoms"], "direction": "-",
             "summary": "Mouse allergen reduction IRR 0.94 (0.92-0.96) for symptoms in low-income children with asthma.", "pubmed_ids": [31520838]},
            {"variable_id": "KuPyJdVJcZ", "concepts": ["rodent or insect infestation", "asthma"], "direction": "+",
             "summary": "Residence with rodent or insect infestation OR 2.1 (1.1-3.8) for asthma (case-control, PMID 31103883).", "pubmed_ids": [31103883]},
        ],
        "literature": [
            {"citation": "Olmedo O, Goldstein IF, Acosta L, et al. Neighborhood differences in exposure and sensitization to cockroach, mouse, dust mite, cat, and dog allergens in New York City. J Allergy Clin Immunol 2011;128(2):284-92.",
             "doi": "10.1016/j.jaci.2011.02.044", "finding": "Homes in NYC neighbourhoods with high asthma prevalence had higher mouse and cockroach allergen levels than homes in low-prevalence neighbourhoods."},
        ],
        "prediction": {
            "direction": "+",
            "magnitude": "Unadjusted Spearman rho between percent of homes with mice or rats in the building (NYCHVS) and child (5-17) asthma ED rate: 0.5-0.8. "
                         "Adjusted standardised coefficient (per SD of rodent share, outcome in log rate) 0.00-0.20, shrinking by more than half from the unadjusted value.",
            "support_if": "Adjusted coefficient for rodent share has a 95% CI above 0.",
            "refute_if": "Adjusted coefficient has a 95% CI below 0 (contested). A CI spanning 0 is unsettled, which is the expected verdict.",
        },
        "plan": (
            "Unit: UHF42 neighbourhoods. Data from the NYC Environment and Health Data Portal repository (github.com/nychealth/EHDP-data, production branch, commit recorded): "
            "measure 94 (mice or rats in the building, percent, NYCHVS), measure 634 (adults reporting mice or rats inside, CHS) as an alternative exposure, "
            "measure 1196 (asthma ED visits age 5-17, rate per 10,000) as outcome, measure 1198 (adult asthma ED rate) as a secondary outcome, "
            "measures 221 (poverty percent) and 1248 or 86 (housing problems percent) as confounders. Latest period common to all. "
            "City operational data: DOHMH Rodent Inspection (p937-wjvj) share of initial inspections with active rat signs, and 311 rodent complaints per 1,000 residents "
            "(erm2-nwe9, complaint_type 'Rodent', 2022-2024), by ZIP code mapped to UHF42, as alternative exposures. "
            "Model: OLS of log asthma ED rate on standardised exposure, poverty, housing problems; n=42, HC3 SE. Report unadjusted rho and adjusted coefficient. "
            "Figure: binned scatter and coefficient plot with the household-level research OR beside the NYC estimate."
        ),
        "alternatives": [
            "Poverty, housing quality, cockroach allergen, smoking and outdoor air pollution all vary with rodent infestation across neighbourhoods.",
            "The research concerns indoor mouse allergen among sensitised children; NYC rodent measures mix rats and mice and indoor and outdoor signs.",
            "Health care access: ED use for asthma reflects lack of primary care as well as morbidity.",
            "n=42 gives little power to separate correlated neighbourhood measures.",
        ],
        "prior": 0.3,
        "registrant": REGISTRANT,
    },
}

if __name__ == "__main__":
    for cid in sys.argv[1:]:
        print(claims.register(CLAIMS[cid]))
