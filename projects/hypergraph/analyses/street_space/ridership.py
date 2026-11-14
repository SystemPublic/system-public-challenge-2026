"""M14 ridership by month (exploratory, descriptive): MTA Bus Hourly Ridership 2017-2019 (98u6-vmgs) and
2020-2024 (kv7t-n8in), routes beginning M14, summed by month, with weekday means.
Writes data/derived/street_space/m14_ridership.json."""
from __future__ import annotations

import json

import pandas as pd

from analyses.mobility.common import nys
from analyses.street_space.common import DER


def main():
    out, srcs = [], []
    for ds, a, b in (("98u6-vmgs", "2018-07-01", "2019-12-31T23:59:59"), ("kv7t-n8in", "2020-01-01", "2020-02-29T23:59:59")):
        rows, src = nys(ds, select="date_trunc_ymd(transit_timestamp) as d, bus_route, sum(ridership) as r",
                        where=f"bus_route like 'M14%' and transit_timestamp between '{a}' and '{b}'",
                        group="d, bus_route", order="d", limit=50000)
        out += rows
        srcs.append(src)
    df = pd.DataFrame(out)
    df["d"] = pd.to_datetime(df.d.str[:10])
    df["r"] = df.r.astype(float)
    day = df.groupby("d").r.sum()
    wk = day[day.index.dayofweek < 5]
    monthly = wk.groupby(wk.index.to_period("M")).mean().round(0)
    routes = sorted(df.bus_route.unique())
    res = {"routes": routes, "weekday_mean_by_month": {str(k): v for k, v in monthly.items()},
           "weekday_mean_oct18_feb19": float(wk["2018-10-03":"2019-02-28"].mean()),
           "weekday_mean_jul_sep19": float(wk["2019-07-01":"2019-09-30"].mean()),
           "weekday_mean_oct19_feb20": float(wk["2019-10-03":"2020-02-29"].mean()), "sources": srcs}
    (DER / "m14_ridership.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k != "sources"}, indent=1))


if __name__ == "__main__":
    main()
