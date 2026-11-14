"""Fetch the aggregates for the exploratory sections (no registered test uses them).
Each block is cached by concord.socrata. Writes CSVs to data/derived/congestion/ and the
source records to explore_sources.json.
  python -m analyses.congestion.explore_fetch [entries] [bus] [dcwp] [subway] [rest]
"""
import json
import sys

import pandas as pd

from concord import socrata
from analyses.congestion.common import DER, nys, area_case

SRC = DER / "explore_sources.json"
src = json.loads(SRC.read_text()) if SRC.exists() else {}
what = sys.argv[1:] or ["entries", "bus", "dcwp", "subway", "rest"]

if "entries" in what:
    rows, s = nys("t6yz-b64h", all_pages=True,
                  select="date_trunc_ym(toll_date) as m, day_of_week_int as dow, hour_of_day as hh, vehicle_class, time_period, sum(crz_entries) as entries, count(distinct toll_date) as days",
                  group="m, dow, hh, vehicle_class, time_period", order="m, dow, hh, vehicle_class, time_period")
    pd.DataFrame(rows).to_csv(DER / "crz_entries_month_dow_hour.csv", index=False)
    src["entries"] = s
    rows, s = nys("t6yz-b64h", all_pages=True, select="toll_date as d, time_period, sum(crz_entries) as entries",
                  group="d, time_period", order="d, time_period")
    pd.DataFrame(rows).to_csv(DER / "crz_entries_daily.csv", index=False)
    src["entries_daily"] = s
    print("entries", flush=True)

if "bus" in what:
    rows, s = nys("r6db-kkzj", all_pages=True,
                  select="month, day_type, hour_of_day, time_period, cbd_relation, route_type, sum(sum_mileage) as miles, sum(sum_time) as hours",
                  group="month, day_type, hour_of_day, time_period, cbd_relation, route_type",
                  order="month, day_type, hour_of_day, time_period, cbd_relation, route_type")
    pd.DataFrame(rows).to_csv(DER / "bus_speed_cbd.csv", index=False)
    src["bus"] = s
    print("bus", flush=True)

if "dcwp" in what:
    rows, s = socrata.query_all("ptev-4hud", select=f"date_trunc_ym(submission_date) as m, {area_case('zip')} as area, business_category, application_type, count(*) as n",
                                where="address_type='Business' or address_type is null", group="m, area, business_category, application_type",
                                order="m, area, business_category, application_type")
    pd.DataFrame(rows).to_csv(DER / "dcwp_applications.csv", index=False)
    src["dcwp"] = s
    print("dcwp", flush=True)

if "rest" in what:
    # restaurants now active, by the month of their earliest inspection on record (a proxy for opening)
    rows, s = socrata.query_all("43nn-pn8j", select="camis, zipcode, min(inspection_date) as first_insp, max(inspection_date) as last_insp",
                                where="inspection_date > '1901-01-01'", group="camis, zipcode", order="camis")
    pd.DataFrame(rows).to_csv(DER / "restaurants_first_inspection.csv", index=False)
    src["restaurants"] = s
    print("rest", flush=True)

if "subway" in what:
    out = []
    for ds, years in (("wujg-7c2s", (2023, 2024)), ("5wq4-mkjj", (2025, 2026))):
        for y in years:
            for a, b in ((f"{y}-01-01T00:00:00", f"{y}-03-31T23:59:59"), (f"{y}-04-01T00:00:00", f"{y}-06-30T23:59:59"),
                         (f"{y}-07-01T00:00:00", f"{y}-09-30T23:59:59"), (f"{y}-10-01T00:00:00", f"{y}-12-31T23:59:59")):
                rows, s = nys(ds, all_pages=True,
                              select=("date_trunc_ym(transit_timestamp) as m, station_complex_id, "
                                      "case(date_extract_dow(transit_timestamp) in (0,6), 'weekend', date_extract_hh(transit_timestamp) >= 19, 'wk_evening', "
                                      "date_extract_hh(transit_timestamp) between 6 and 18, 'wk_day', true, 'wk_night') as part, sum(ridership) as n"),
                              where=f"transit_timestamp between '{a}' and '{b}' and transit_mode='subway'",
                              group="m, station_complex_id, part", order="m, station_complex_id, part")
                out += rows
                src[f"subway_{a[:7]}"] = s
                print("subway", a[:7], len(rows), flush=True)
                pd.DataFrame(out).to_csv(DER / "subway_entries_parts.csv", index=False)

SRC.write_text(json.dumps(src, indent=1))
