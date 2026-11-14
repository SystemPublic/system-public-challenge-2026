"""Power check for a pedestrian-injury test on the 14th Street busway (pre-October-2019 data only).
Counts crashes with a pedestrian injured or killed, by corridor and year, 2013 to September 2019, and
computes the smallest relative change on 14th Street (against the four comparison corridors) that a
before-after test with a given post window could detect (D >= 4, i.e. two standard errors).
Writes data/derived/street_space/peds_power.json."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from concord import socrata as s
from analyses.street_space.common import DER
from analyses.street_space.peds_common import assign, BBOX, TREATED


def fetch(a, b):
    w = (f"crash_date between '{a}' and '{b}' and (number_of_pedestrians_injured>0 or number_of_pedestrians_killed>0) "
         f"and latitude between {BBOX[0]} and {BBOX[1]} and longitude between {BBOX[2]} and {BBOX[3]}")
    rows, src = s.query_all('h9gi-nx95', select="collision_id, crash_date, latitude, longitude, on_street_name, "
                            "number_of_pedestrians_injured, number_of_pedestrians_killed", where=w)
    df = pd.DataFrame(rows)
    df["c"] = assign(df.latitude, df.longitude)
    df["inj"] = df.number_of_pedestrians_injured.astype(int) + df.number_of_pedestrians_killed.astype(int)
    return df[df.c.notna()], src


def main():
    df, src = fetch("2013-01-01", "2019-09-30")
    df["yr"] = df.crash_date.str[:4]
    tab = df.groupby(["c", "yr"]).inj.sum().unstack().fillna(0)
    print(tab)
    t_per_yr = tab.loc[TREATED, [str(y) for y in range(2014, 2019)]].mean()
    c_per_yr = tab.drop(TREATED)[[str(y) for y in range(2014, 2019)]].sum().mean()
    # Year-to-year sd of log ratio treated/controls (2013-2018), beyond Poisson.
    lr = np.log(tab.loc[TREATED, [str(y) for y in range(2013, 2019)]] / tab.drop(TREATED)[[str(y) for y in range(2013, 2019)]].sum())
    out = {"table": tab.to_dict(), "treated_per_year": t_per_yr, "controls_per_year": c_per_yr,
           "sd_log_ratio_yearly": float(lr.std(ddof=1)), "source": src, "mde": {}}
    for post_years, pre_years in ((5 / 12, 5 / 12), (5 / 12, 5), (3, 5)):
        se = np.sqrt(1 / (t_per_yr * post_years) + 1 / (t_per_yr * pre_years) + 1 / (c_per_yr * post_years) + 1 / (c_per_yr * pre_years))
        out["mde"][f"post{post_years:.2f}y_pre{pre_years}y"] = {"se_log_poisson": round(float(se), 3),
                                                                 "mde_pct_D4": round(float(100 * (1 - np.exp(-2 * se))), 1)}
    (DER / "peds_power.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: v for k, v in out.items() if k not in ("table", "source")}, indent=1))


if __name__ == "__main__":
    main()
