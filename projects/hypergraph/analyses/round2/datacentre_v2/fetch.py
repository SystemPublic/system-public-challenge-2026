"""Fetch UER Con Edison total consumption for all New York City ZIP codes, 2023-2024 (denominator D3 only)."""
import json
from pathlib import Path
import pandas as pd
from concord import socrata as s
OUT = Path(__file__).resolve().parents[3] / "data" / "derived" / "round2" / "datacentre_v2"
s.DOMAIN = "https://data.ny.gov"
where = ("data_class='electricity' AND data_field='3_nat_consumption' AND utility_display_name like 'Con%' AND year in (2023,2024) AND "
         "(zip_code like '100%' OR zip_code like '101%' OR zip_code like '102%' OR zip_code like '103%' OR zip_code like '104%' OR "
         "zip_code like '110%' OR zip_code like '111%' OR zip_code like '112%' OR zip_code like '113%' OR zip_code like '114%' OR zip_code like '115%' OR zip_code like '116%')")
rows, src = s.query_all("g2x3-izm4", select="year,month,zip_code,data_field,unit,value,number_of_accounts", where=where)
pd.DataFrame(rows).to_csv(OUT / "uer_nyc_total.csv", index=False)
(OUT / "sources_uer_nyc.json").write_text(json.dumps([src], indent=1))
print(src["n_rows"])
