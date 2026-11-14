"""Design check for retimed-ems-presence: the registered estimator applied to 2017 against 2018,
two years outside the test. It gives the sampling error to expect, and reveals nothing about 2019 or later."""
import datetime as dt, json, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib
from concord import socrata

def ems_panel(lo, hi):
    rows, src = socrata.query("76xm-jjuj", select="date_trunc_ymd(incident_datetime) as d, communitydistrict as cd, count(*) as n",
                              where=f"incident_datetime between '{lo}T00:00:00' and '{hi}T23:59:59' and date_extract_hh(incident_datetime) between 6 and 19",
                              group="d, cd", order="d, cd", limit=50000)
    assert len(rows) < 50000
    p = pd.DataFrame(rows).dropna(subset=["cd"])
    p["unit"] = p.cd.astype(int); p["n"] = p.n.astype(int); p["date"] = p.d.str[:10]
    return p[["unit", "date", "n"]], src

if __name__ == "__main__":
    ex = pd.read_csv(lib.OUT / "exposure_community_district.csv")
    ex = ex[ex.community_district % 100 <= 18]
    units = ex.community_district.tolist()
    P = {}
    for y in (2017, 2018):
        P[y], _ = ems_panel(f"{y}-01-01", f"{y}-12-31")
    A = {y: lib.week_arrays(P[y], units, lib.retained_weeks(dt.date(y, 1, 1), dt.date(y, 12, 31))) for y in P}
    cbd = (ex.cbd_share_entries > 0.5).values
    res = lib.estimate(A[2017], A[2018], ex.E_day.values, {"cbd": cbd, "rest": ~cbd})
    res["daily_mean_weekday_cbd_2018"] = float((A[2018][0][cbd].sum() + A[2018][1][cbd].sum()) / (5 * A[2018][0].shape[1]))
    res["daily_mean_weekday_rest_2018"] = float((A[2018][0][~cbd].sum() + A[2018][1][~cbd].sum()) / (5 * A[2018][0].shape[1]))
    json.dump(res, open(lib.OUT / "design_ems_placebo_2017_2018.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
