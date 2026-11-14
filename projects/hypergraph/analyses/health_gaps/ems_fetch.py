"""Daily citywide EMS aggregates from 76xm-jjuj (EMS Incident Dispatch Data), 2017 to latest.

Writes data/derived/health_gaps/ems_daily.csv with, per day:
  n_all       all incidents
  n_disp, disp_sum           incidents with valid dispatch time; sum of dispatch_response_seconds_qy
                             (incident creation to first unit assigned = wait for a free unit), by severity group
  n_trav, trav_sum           incidents with valid response time; sum of incident_travel_tm_seconds_qy
  n_hosp, hosp_sum           transported incidents (disposition 82) with hospital arrival and close in the
                             same calendar month and 0 < close - hospital arrival < 14,400 s; sum of that
                             interval (time at hospital until the unit is closed out = turnaround)
and data/derived/health_gaps/ems_daily_sources.json.
"""
from __future__ import annotations
import json
import pandas as pd
from concord import socrata
from analyses.health_gaps.common import DER

DS = "76xm-jjuj"
SEV = "case(initial_severity_level_code in ('1','2','3'), 'hi', true, 'lo')"


def hs(x):
    return f"(date_extract_hh({x})*3600+date_extract_mm({x})*60+date_extract_ss({x}))"


C, H = "incident_close_datetime", "first_hosp_arrival_datetime"
DIFF = f"((date_extract_d({C})-date_extract_d({H}))*86400+{hs(C)}-{hs(H)})"


def halves(y):
    return [(f"{y}-01-01T00:00:00", f"{y}-06-30T23:59:59"), (f"{y}-07-01T00:00:00", f"{y}-12-31T23:59:59")]


def main(years=range(2017, 2027)):
    frames, srcs = [], []
    for y in years:
        for a, b in halves(y):
            w = f"incident_datetime between '{a}' and '{b}'"
            r1, s1 = socrata.query_all(DS, select=f"date_trunc_ymd(incident_datetime) as d, {SEV} as sev, count(*) as n_all",
                                      where=w, group="d, sev", order="d, sev")
            r2, s2 = socrata.query_all(DS, select=(f"date_trunc_ymd(incident_datetime) as d, {SEV} as sev, count(*) as n_disp, "
                                                  "sum(dispatch_response_seconds_qy) as disp_sum"),
                                      where=w + " and valid_dispatch_rspns_time_indc='Y'", group="d, sev", order="d, sev")
            r3, s3 = socrata.query_all(DS, select=(f"date_trunc_ymd(incident_datetime) as d, {SEV} as sev, count(*) as n_trav, "
                                                  "sum(incident_travel_tm_seconds_qy) as trav_sum"),
                                      where=w + " and valid_incident_rspns_time_indc='Y'", group="d, sev", order="d, sev")
            r4, s4 = socrata.query_all(DS, select=f"date_trunc_ymd(incident_datetime) as d, {SEV} as sev, count(*) as n_hosp, sum({DIFF}) as hosp_sum",
                                      where=(w + f" and incident_disposition_code='82' and {H} IS NOT NULL and {C} IS NOT NULL"
                                             f" and date_extract_m({C})=date_extract_m({H}) and {DIFF} > 0 and {DIFF} < 14400"),
                                      group="d, sev", order="d, sev")
            parts = [pd.DataFrame(r) for r in (r1, r2, r3, r4)]
            if parts[0].empty:
                continue
            m = parts[0]
            for p in parts[1:]:
                if not p.empty:
                    m = m.merge(p, on=["d", "sev"], how="left")
            frames.append(m)
            srcs += [s1, s2, s3, s4]
    df = pd.concat(frames)
    df["d"] = df["d"].str[:10]
    for c in df.columns:
        if c not in ("d", "sev"):
            df[c] = pd.to_numeric(df[c])
    df.to_csv(DER / "ems_daily.csv", index=False)
    (DER / "ems_daily_sources.json").write_text(json.dumps(srcs[:4] + [{"note": f"{len(srcs)} queries, one per half-year and measure"}], indent=1))
    print(df.shape, df["d"].min(), df["d"].max())


if __name__ == "__main__":
    main()
