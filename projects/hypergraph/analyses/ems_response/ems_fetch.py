"""EMS incident dispatch (76xm-jjuj) aggregates through concord.socrata (cached, versioned).

kinds:
  hourly YEAR   date x hour x area x severity group, Manhattan areas only (crz, north, as in
                analyses.congestion.common), incidents with a valid response time.
                -> ems_hourly_{YEAR}.csv  (the same query as analyses.congestion.ems_fetch,
                restricted to Manhattan; used for 2017-2018, which that script did not fetch)
  ybh           year x borough x hour x severity group, valid response time, 2017 on -> ems_ybh.csv
  ytype         year x initial call type x severity group, valid response time -> ems_ytype.csv
  yarea         year x dispatch area x severity group x hour block -> ems_yarea.csv
  weekly        ISO week (date_trunc_ymd then grouped in pandas) x borough x hour x sev, 2024 on
                -> ems_daily_boro_{YEAR}.csv
  valid         year x borough x severity group x validity flag (share without a valid time)
Writes source records to ems_sources.json under the kind (and year).
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from concord import socrata
from analyses.congestion.common import area_case
from analyses.ems_response.common import DER, EMS

SEV = "case(initial_severity_level_code in ('1','2','3'), 'hi', true, 'lo')"
AGG = ("count(*) as n, sum(incident_travel_tm_seconds_qy) as travel, "
       "sum(dispatch_response_seconds_qy) as dispatch, sum(incident_response_seconds_qy) as response")
VALID = "valid_incident_rspns_time_indc='Y'"


def save_src(key, srcs):
    f = DER / "ems_sources.json"
    old = json.loads(f.read_text()) if f.exists() else {}
    old[key] = srcs
    f.write_text(json.dumps(old, indent=1))


def halves(y):
    return [(f"{y}-01-01T00:00:00", f"{y}-06-30T23:59:59"), (f"{y}-07-01T00:00:00", f"{y}-12-31T23:59:59")]


def run(kind, year=None):
    rows, srcs = [], []
    if kind == "hourly":
        for a, b in halves(year):
            r, s = socrata.query_all(EMS, select=(
                f"date_trunc_ymd(incident_datetime) as d, date_extract_hh(incident_datetime) as hh, "
                f"{area_case()} as area, {SEV} as sev, {AGG}"),
                where=f"incident_datetime between '{a}' and '{b}' and {VALID} and borough='MANHATTAN'",
                group="d, hh, area, sev", order="d, hh, area, sev")
            rows += r; srcs.append(s)
        out = f"ems_hourly_{year}.csv"
    elif kind == "daily_boro":
        for a, b in halves(year):
            r, s = socrata.query_all(EMS, select=(
                f"date_trunc_ymd(incident_datetime) as d, borough, "
                f"case(date_extract_hh(incident_datetime) between 1 and 5, 'night', "
                f"date_extract_hh(incident_datetime) between 7 and 19, 'day', true, 'shoulder') as blk, "
                f"{SEV} as sev, {AGG}"),
                where=f"incident_datetime between '{a}' and '{b}' and {VALID}",
                group="d, borough, blk, sev", order="d, borough, blk, sev")
            rows += r; srcs.append(s)
        out = f"ems_daily_boro_{year}.csv"
    elif kind == "ybh":
        r, s = socrata.query_all(EMS, select=(
            f"date_extract_y(incident_datetime) as y, borough, date_extract_hh(incident_datetime) as hh, "
            f"{SEV} as sev, {AGG}"),
            where=f"incident_datetime >= '2017-01-01' and {VALID}",
            group="y, borough, hh, sev", order="y, borough, hh, sev")
        rows, srcs, out = r, [s], "ems_ybh.csv"
    elif kind == "ytype":
        r, s = socrata.query_all(EMS, select=(
            f"date_extract_y(incident_datetime) as y, initial_call_type as ct, {SEV} as sev, {AGG}"),
            where=f"incident_datetime >= '2017-01-01' and {VALID}",
            group="y, ct, sev", order="y, ct, sev")
        rows, srcs, out = r, [s], "ems_ytype.csv"
    elif kind == "yarea":
        r, s = socrata.query_all(EMS, select=(
            f"date_extract_y(incident_datetime) as y, incident_dispatch_area as da, "
            f"date_extract_hh(incident_datetime) as hh, {SEV} as sev, {AGG}"),
            where=f"incident_datetime >= '2017-01-01' and {VALID}",
            group="y, da, hh, sev", order="y, da, hh, sev")
        rows, srcs, out = r, [s], "ems_yarea.csv"
    elif kind == "valid":
        r, s = socrata.query_all(EMS, select=(
            f"date_extract_y(incident_datetime) as y, borough, {SEV} as sev, "
            f"valid_incident_rspns_time_indc as v, count(*) as n"),
            where="incident_datetime >= '2017-01-01'",
            group="y, borough, sev, v", order="y, borough, sev, v")
        rows, srcs, out = r, [s], "ems_valid.csv"
    else:
        raise SystemExit(kind)
    pd.DataFrame(rows).to_csv(DER / out, index=False)
    save_src(f"{kind}_{year}" if year else kind, srcs)
    print(kind, year, len(rows), flush=True)


if __name__ == "__main__":
    k = sys.argv[1]
    ys = [int(y) for y in sys.argv[2:]] or [None]
    for y in ys:
        run(k, y)
