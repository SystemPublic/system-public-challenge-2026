#!/usr/bin/env bash
# Round 2: datasets from Christina's shortlist that have open direct downloads.
# Run from the repo root:  ./external/fetch_external2.sh         (add BIG=1 to also fetch the 273 MB China purifier archive)
set -uo pipefail
cd "$(dirname "$0")/raw2"
get() { echo "-> $1"; curl -fsSL --retry 2 -o "$1" "$2" && echo "   ok ($(du -h "$1" | cut -f1))" || echo "   FAILED: $2"; }

# England: EHS 2023-24 health and housing annex tables (damp, keeping warm, household health, tenure, children)
get ehs_2023_24_health_housing_annex.ods "https://assets.publishing.service.gov.uk/media/6822103c53add7d476d81913/EHS_23_24_Health_and_Housing_Annex_Tables_v3.ods"
# England: pupil absence by characteristics, LA level, 2016/17-2024/25 (OGL)
get pupil_absence_by_characteristics.csv "https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/a5f750db-286a-4d63-a31b-d2a5c1d6d7e0/csv"
# England: seven occupied homes, indoor/outdoor PM, NO2, CO2, T, RH, window opening (Mendeley, CC BY 4.0)
get seven_homes_england.zip "https://data.mendeley.com/public-api/zip/47gjkbm29h/download/2"
# US (California): 70 homes with mechanical ventilation, indoor/outdoor PM2.5 + NO2, range hood use (Dryad, CC0)
get california_homes_ventilation.zip "https://datadryad.org/api/v2/datasets/doi%3A10.7941%2FD1ZS7X/download"
# Finland: controlled office room, ventilation/occupancy/CO2 (Zenodo, CC BY 4.0)
get finland_office_ventilation.zip "https://zenodo.org/api/records/18299691/files-archive"
# US: RECS 2020 household energy microdata + codebook (EIA, public domain)
get recs2020_public_v7.csv "https://www.eia.gov/consumption/residential/data/2020/csv/recs2020_public_v7.csv"
get recs2020_codebook_v7.xlsx "https://www.eia.gov/consumption/residential/data/2020/xls/RECS%202020%20Codebook%20for%20Public%20File%20-%20v7.xlsx"
# China: 100 homes, hourly air-purifier data, 2021-22 (figshare, CC BY 4.0) -- 273 MB .rar, optional
if [ "${BIG:-0}" = "1" ]; then get china_purifiers_100homes.rar "https://ndownloader.figshare.com/files/42612664"; else echo "-> skipped China purifier archive (273 MB). Re-run with BIG=1 to fetch."; fi
echo; ls -la
