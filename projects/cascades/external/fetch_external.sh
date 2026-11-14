#!/usr/bin/env bash
# Downloads external UK context datasets for the Retrofit Evidence Explorer.
# Run from the repo root:  ./external/fetch_external.sh
set -uo pipefail
cd "$(dirname "$0")/raw"
get() { echo "-> $1"; curl -fsSL --retry 2 -o "$1" "$2" && echo "   ok ($(du -h "$1" | cut -f1))" || echo "   FAILED: $2"; }

# Deprivation: IoD 2025 File 7, all ranks/scores/deciles by LSOA (incl. Living Environment domain)
get iod2025_file7_lsoa.csv "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
# Fuel poverty: DESNZ sub-regional 2026 (2024 data), LA + LSOA
get fuel_poverty_subregional_2026.xlsx "https://assets.publishing.service.gov.uk/media/6a02febf81a251700a20b42a/fuel-poverty-sub-regional-2026-2024-data-tables.xlsx"
# Damp, Category 1 hazards, non-decent homes: EHS local authority stock condition modelling 2023
get ehs_la_stock_condition_2023.ods "https://assets.publishing.service.gov.uk/media/6827049d8999f671f3c24378/Tables_-_Local_Authority_Stock_Condition_Modelling_2023.ods"
# Energy/carbon/bills: MHCLG EPC live table EB3 (existing dwellings: energy use, CO2, fuel costs)
get epc_eb3_existing_dwellings.ods "https://assets.publishing.service.gov.uk/media/6ae0b9d2779378370fd80a25/EB3-_Existing_Domestic_Properties.ods"
# EPC live table EB1 (existing dwellings by energy efficiency band)
get epc_eb1_existing_dwellings.ods "https://assets.publishing.service.gov.uk/media/6ae0ba657b7111c482d80a39/EB1-_Existing_Domestic_Properties.ods"
# Health outcomes by local authority: OHID Fingertips
get fingertips_90810_asthma_admissions_u19.csv "https://fingertips.phe.org.uk/api/all_data/csv/by_indicator_id?indicator_ids=90810"
get fingertips_93759_fuel_poverty.csv          "https://fingertips.phe.org.uk/api/all_data/csv/by_indicator_id?indicator_ids=93759"
get fingertips_90360_excess_winter_deaths.csv  "https://fingertips.phe.org.uk/api/all_data/csv/by_indicator_id?indicator_ids=90360"
echo; ls -la
