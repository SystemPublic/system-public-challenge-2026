"""Fetch LL84 (Manhattan and Bronx, 2022-2024) and UER (Manhattan ZIPs) for further-datacentre-share-manhattan."""
import json
from pathlib import Path
import pandas as pd
from concord import socrata as s

OUT = Path(__file__).resolve().parents[2] / "data" / "derived" / "further"
COLS = ("report_year,property_id,property_name,parent_property_id,address_1,nyc_borough_block_and_lot,borough,postal_code,"
        "largest_property_use_type,electricity_use_grid_purchase_1,electricity_use_grid_purchase_2,property_gfa_calculated,property_gfa_self_reported,"
        "data_center_gross_floor_area,data_center_it_site_energy,data_center_pue,laboratory_gross_floor_area,office_gross_floor_area_ft,"
        "alert_data_center_issue_with,estimated_values_energy,estimated_data_flag,year_ending")

def main():
    srcs = []
    s.DOMAIN = "https://data.cityofnewyork.us"
    rows, src = s.query_all("5zyy-y8am", select=COLS, where="upper(borough) in ('MANHATTAN','BRONX') AND report_year in (2022,2023,2024)")
    srcs.append(src)
    pd.DataFrame(rows).to_csv(OUT / "ll84_mn_bx.csv", index=False)
    s.DOMAIN = "https://data.ny.gov"
    rows, src = s.query_all("g2x3-izm4", select="year,month,zip_code,data_field,unit,value,number_of_accounts",
        where="data_class='electricity' AND data_field in ('2_nat_consumption','3_nat_consumption','1_nat_consumption') AND utility_display_name like 'Con%' AND (zip_code like '100%' OR zip_code like '101%' OR zip_code like '102%') AND year in (2022,2023,2024)")
    srcs.append(src)
    pd.DataFrame(rows).to_csv(OUT / "uer_mn.csv", index=False)
    s.DOMAIN = "https://data.cityofnewyork.us"
    (OUT / "datacentre_sources.json").write_text(json.dumps(srcs, indent=1))
    print([x["n_rows"] for x in srcs])

if __name__ == "__main__":
    main()
