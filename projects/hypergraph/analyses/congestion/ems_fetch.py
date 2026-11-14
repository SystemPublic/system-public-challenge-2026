"""Fetch EMS (76xm-jjuj) and fire (8m42-w767) dispatch aggregates by date, hour, area and
severity group, one year per call, through concord.socrata (cached, versioned).

Usage: python -m analyses.congestion.ems_fetch ems 2019 2020 ...   (or: fire, arrest, shot)
Writes data/derived/congestion/{kind}_{year}.csv and appends source records to
{kind}_sources.json. Only incidents with a valid response time are aggregated for ems/fire.
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from concord import socrata
from analyses.congestion.common import DER, area_case


def year_parts(y):
    return [(f"{y}-01-01T00:00:00", f"{y}-06-30T23:59:59"), (f"{y}-07-01T00:00:00", f"{y}-12-31T23:59:59")]


def fetch(kind: str, year: int):
    rows, srcs = [], []
    for a, b in year_parts(year):
        if kind == "ems":
            r, s = socrata.query_all(
                "76xm-jjuj",
                select=("date_trunc_ymd(incident_datetime) as d, date_extract_hh(incident_datetime) as hh, "
                        f"{area_case()} as area, "
                        "case(initial_severity_level_code in ('1','2','3'), 'hi', true, 'lo') as sev, "
                        "count(*) as n, sum(incident_travel_tm_seconds_qy) as travel, "
                        "sum(incident_response_seconds_qy) as response, sum(dispatch_response_seconds_qy) as dispatch"),
                where=f"incident_datetime between '{a}' and '{b}' and valid_incident_rspns_time_indc='Y'",
                group="d, hh, area, sev", order="d, hh, area, sev")
        elif kind == "fire":
            r, s = socrata.query_all(
                "8m42-w767",
                select=("date_trunc_ymd(incident_datetime) as d, date_extract_hh(incident_datetime) as hh, "
                        f"{area_case()} as area, incident_classification_group as cls, "
                        "count(*) as n, sum(incident_travel_tm_seconds_qy) as travel, "
                        "sum(incident_response_seconds_qy) as response"),
                where=f"incident_datetime between '{a}' and '{b}' and valid_incident_rspns_time_indc='Y'",
                group="d, hh, area, cls", order="d, hh, area, cls")
        elif kind in ("arrest", "shot"):
            ct = "final_call_type='ARREST'" if kind == "arrest" else "final_call_type in ('SHOT','STAB')"
            r, s = socrata.query_all(
                "76xm-jjuj",
                select=("date_trunc_ymd(incident_datetime) as d, date_extract_hh(incident_datetime) as hh, "
                        f"{area_case()} as area, final_call_type as ct, incident_disposition_code as disp, "
                        "valid_incident_rspns_time_indc as valid, "
                        "count(*) as n, sum(incident_travel_tm_seconds_qy) as travel, "
                        "sum(incident_response_seconds_qy) as response"),
                where=f"incident_datetime between '{a}' and '{b}' and {ct}",
                group="d, hh, area, ct, disp, valid", order="d, hh, area, ct, disp, valid")
        else:
            raise SystemExit(kind)
        rows += r
        srcs.append(s)
    df = pd.DataFrame(rows)
    df.to_csv(DER / f"{kind}_{year}.csv", index=False)
    f = DER / f"{kind}_sources.json"
    old = json.loads(f.read_text()) if f.exists() else {}
    old[str(year)] = srcs
    f.write_text(json.dumps(old, indent=1))
    print(kind, year, len(df), flush=True)


if __name__ == "__main__":
    for y in sys.argv[2:]:
        fetch(sys.argv[1], int(y))
