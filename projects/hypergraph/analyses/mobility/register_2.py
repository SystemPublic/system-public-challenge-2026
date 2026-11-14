"""Second registration: NO2 and PM2.5 from NYCCAS annual averages by UHF42.

Supersedes mob-crz-air for the NO2 test, because no EPA AQS NO2 monitor operated in
Manhattan in 2022-2025 (found while running the registered plan). Written after
seeing only that the EHDP NYCCAS series has a 2025 period, not its values.
"""
from concord import claims
from analyses.mobility.register_1 import CRZ_AIR, REGISTRANT

REC = {
    "id": "mob-crz-air-nyccas",
    "supersedes": "mob-crz-air",
    "kind": "confirmation",
    "statement": ("NYCCAS annual average NO2 in the five UHF42 neighbourhoods south of 60th Street fell from 2024 "
                  "to 2025, after congestion pricing began, more than in neighbourhoods outside Manhattan."),
    "why_superseded": ("The registered primary test of mob-crz-air (daily NO2 at EPA AQS monitors inside the zone) "
                       "could not run: the AQS daily files for 2022-2025 contain no NO2 monitor in New York County. "
                       "The NYC Community Air Survey (NYCCAS) annual averages by UHF42 include 2025."),
    "graph_evidence": CRZ_AIR["graph_evidence"],
    "literature": CRZ_AIR["literature"],
    "prediction": {
        "direction": "-",
        "magnitude": ("DiD of log annual NO2, UHF 306-310 vs the 32 UHFs outside Manhattan, 2025 vs 2021-2024: "
                      "-3% to -10%. PM2.5 (secondary): 0% to -6%."),
        "support_if": "NO2 DiD below 0, and below the 5th percentile of the placebo-in-space distribution (one-sided p < 0.05).",
        "refute_if": "NO2 DiD at or above 0, or within the central 80% of the placebo-in-space distribution.",
    },
    "plan": ("Data: NYC DOHMH Environment and Health Data Portal, github.com/nychealth/EHDP-data at commit "
             "547482b9df589006543e13e8cdf6546e00ed9998, indicator 2025 (NO2, measure 1431 annual mean, ppb) and "
             "indicator 2023 (PM2.5, measure 1425 annual mean, ug/m3), GeoType UHF42, years 2021-2025. "
             "In-zone: UHF 306 Chelsea-Clinton, 307 Gramercy Park-Murray Hill, 308 Greenwich Village-SoHo, "
             "309 Union Square-Lower East Side, 310 Lower Manhattan. Adjacent (reported, excluded from the main "
             "comparison): 301-305. Comparison: UHFs in the Bronx, Brooklyn, Queens and Staten Island. Model: OLS of log "
             "value on UHF and year fixed effects and inzone x post (post = 2025). Inference: placebo-in-space, the "
             "same estimator for every set of 5 comparison UHFs drawn at random (5,000 draws), giving a one-sided p and "
             "the 2.5-97.5% band of placebo estimates around the estimate; placebo-in-time with post = 2024 on 2021-2024. "
             "Figure: annual NO2 by group, 2014-2025, with the in-zone minus comparison difference."),
    "alternatives": CRZ_AIR["alternatives"] + [
        "NYCCAS annual surfaces are model-based (land-use regression on street-level monitors); if the model uses traffic "
        "inputs that were updated for 2025, the result is partly circular. Its method notes must be read before the result is used.",
        "The 2023 Canadian wildfire smoke episode raised 2023 PM2.5 citywide (absorbed by year effects if uniform).",
    ],
    "prior": 0.3,
    "registrant": REGISTRANT,
}

if __name__ == "__main__":
    print(claims.register(REC))
