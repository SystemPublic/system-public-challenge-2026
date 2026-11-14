#!/usr/bin/env bash
# Round 3: Christina's supplemental handoff (NHS costs, Bath overheating, UKHSA heat 2024).
# Run from the repo root:  ./external/fetch_external3.sh      (add BIG=1 for the ~67 MB NHS cost ZIPs)
set -uo pipefail
cd "$(dirname "$0")/raw3"
get() { echo "-> $1"; curl -fsSL --retry 2 -o "$1" "$2" && echo "   ok ($(du -h "$1" | cut -f1))" || echo "   FAILED: $2"; }

# UK (Bath): 43 homes with an occupant 65+, summer 2017-18 indoor temps + comfort (CC BY 4.0, DOI 10.15125/BATH-00562)
get bath_bedroom_temps.csv   "https://researchdata.bath.ac.uk/562/1/Phase%202%20and%204%20BR.csv"
get bath_livingroom_temps.csv "https://researchdata.bath.ac.uk/562/2/Phase%202%20and%204%20LR.csv"
get bath_external_weather.csv "https://researchdata.bath.ac.uk/562/3/ExternalWeatherSummer.csv"
get bath_tsv.csv              "https://researchdata.bath.ac.uk/562/4/TSV.csv"
get bath_readme_summer.pdf    "https://researchdata.bath.ac.uk/562/5/READ%20ME%20SUMMER.pdf"
# England: UKHSA heat mortality monitoring data 2024 (OGL v3)
get ukhsa_heat_mortality_2024.ods "https://assets.publishing.service.gov.uk/media/67ebd7ade9c76fa33048c592/heat-mortality-monitoring-data-2024.ods"
# England & Wales: Census 2021 overcrowding (TS052 occupancy rating for bedrooms; RM099 by tenure) - Nomis bulk files (OGL v3)
get census2021_ts052.zip "https://www.nomisweb.co.uk/output/census/2021/census2021-ts052.zip"
get census2021_rm099.zip "https://www.nomisweb.co.uk/output/census/2021/census2021-rm099.zip"
# England: NHS National Cost Collection 2023/24 organisation-level source data (OGL v3) -- ~67 MB total, optional
if [ "${BIG:-0}" = "1" ]; then
  get nhs_ncc_2324_part1.zip "https://www.england.nhs.uk/wp-content/uploads/2023/04/Organisation_level_source_data_1_2324-v2.zip"
  get nhs_ncc_2324_part2.zip "https://www.england.nhs.uk/wp-content/uploads/2023/04/Organisation_level_source_data_2_2324-v2.zip"
  get nhs_ncc_2324_part3.zip "https://www.england.nhs.uk/wp-content/uploads/2023/04/Organisation_level_source_data_3_2324-v2.zip"
else echo "-> skipped NHS cost ZIPs (~67 MB). Re-run with BIG=1 to fetch."; fi
echo; ls -la
