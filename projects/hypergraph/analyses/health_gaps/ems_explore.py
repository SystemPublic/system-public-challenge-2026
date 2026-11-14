"""Exploratory (not registered): where and when EMS response to life-threatening incidents is slowest.
76xm-jjuj, severity 1-3, valid response time. Writes data/derived/health_gaps/ems_explore.json."""
from __future__ import annotations
import json
import pandas as pd
from concord import socrata
from analyses.health_gaps.common import DER

DS = "76xm-jjuj"
HI = "initial_severity_level_code in ('1','2','3') and valid_incident_rspns_time_indc='Y'"
SEL = ("count(*) as n, avg(incident_response_seconds_qy) as resp, avg(dispatch_response_seconds_qy) as disp, "
       "avg(incident_travel_tm_seconds_qy) as trav")


def q(select, where, group):
    r, s = socrata.query_all(DS, select=select, where=where, group=group, order=group)
    d = pd.DataFrame(r)
    for c in d.columns:
        if c not in ("borough", "area", "y"):
            d[c] = pd.to_numeric(d[c], errors="coerce")
    return d, s


def main():
    out, srcs = {}, []
    d, s = q(f"date_extract_y(incident_datetime) as y, borough, {SEL}", HI + " and incident_datetime >= '2015-01-01'", "y, borough")
    out["year_borough"] = d.round(1).to_dict("records"); srcs.append(s)
    d, s = q(f"date_extract_hh(incident_datetime) as hh, {SEL}", HI + " and incident_datetime between '2025-01-01' and '2025-12-31T23:59:59'", "hh")
    out["hour_2025"] = d.round(1).to_dict("records"); srcs.append(s)
    d, s = q(f"date_extract_hh(incident_datetime) as hh, {SEL}", HI + " and incident_datetime between '2019-01-01' and '2019-12-31T23:59:59'", "hh")
    out["hour_2019"] = d.round(1).to_dict("records"); srcs.append(s)
    d, s = q(f"incident_dispatch_area as area, {SEL}", HI + " and incident_datetime between '2025-01-01' and '2025-12-31T23:59:59'", "area")
    out["area_2025"] = d.round(1).to_dict("records"); srcs.append(s)
    d, s = q(f"incident_dispatch_area as area, {SEL}", HI + " and incident_datetime between '2019-01-01' and '2019-12-31T23:59:59'", "area")
    out["area_2019"] = d.round(1).to_dict("records"); srcs.append(s)
    d, s = q(f"date_extract_y(incident_datetime) as y, date_extract_m(incident_datetime) as m, {SEL}", HI + " and incident_datetime >= '2015-01-01'", "y, m")
    out["month"] = d.round(1).to_dict("records"); srcs.append(s)
    out["sources"] = srcs
    (DER / "ems_explore.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
