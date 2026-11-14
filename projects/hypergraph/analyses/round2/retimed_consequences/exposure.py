"""Exposure for the three re-timed-week consequence tests, from the dose map only.

For each taxi zone and community district, sum subway entries over the station
complexes inside it, by weekday and hour band, in 2019 and in the recent period
(dose_map_long.csv). The exposure is
    E = ln(MF/TWT recent) - ln(MF/TWT 2019),
where MF is the mean of Monday and Friday entries and TWT the mean of Tuesday
to Thursday, for the bands 06:00-19:59 (AM peak, midday, PM peak). E_am is the
same for the AM peak alone. E is negative where Mondays and Fridays thinned.
No outcome data are read here.
"""
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data/derived/round2/retimed_consequences"
DAY = ["AM peak 06-10", "midday 10-16", "PM peak 16-20"]


def expo(long, keys, bands):
    d = long[long.band.isin(bands)].groupby(keys + ["weekday"])[["entries_recent", "entries_2019"]].sum().reset_index()
    d["grp"] = d.weekday.map({"Mon": "MF", "Fri": "MF", "Tue": "TWT", "Wed": "TWT", "Thu": "TWT"})
    g = d.dropna(subset=["grp"]).groupby(keys + ["grp"])[["entries_recent", "entries_2019"]].mean().unstack("grp")
    return np.log(g[("entries_recent", "MF")] / g[("entries_recent", "TWT")]) - np.log(g[("entries_2019", "MF")] / g[("entries_2019", "TWT")]), g


def main():
    dm = pd.read_csv(ROOT / "data/derived/transit/dose_map.csv")
    lg = pd.read_csv(ROOT / "data/derived/transit/dose_map_long.csv")
    dm = dm[dm.deficit_reliable]
    lg = lg.merge(dm[["complex_id", "taxi_zone_id", "taxi_zone", "community_district", "in_cbd", "borough"]], on="complex_id")
    res = {}
    for name, key in [("taxi_zone", "taxi_zone_id"), ("community_district", "community_district")]:
        e, g = expo(lg, [key], DAY)
        eam, _ = expo(lg, [key], ["AM peak 06-10"])
        t = pd.DataFrame({"E_day": e, "E_am": eam})
        t["twt_day_entries_2019"] = g[("entries_2019", "TWT")]
        t["twt_day_entries_recent"] = g[("entries_recent", "TWT")]
        w = dm.assign(w=dm.weekday_mean_entries_2019).groupby(key).apply(
            lambda x: pd.Series({"n_complexes": len(x), "cbd_share_entries": (x.w * x.in_cbd).sum() / x.w.sum(),
                                 "borough": x.borough.mode().iloc[0]}))
        t = t.join(w).reset_index()
        if name == "taxi_zone":
            t = t.merge(dm[["taxi_zone_id", "taxi_zone"]].drop_duplicates(), on="taxi_zone_id")
        t.round(5).to_csv(OUT / f"exposure_{name}.csv", index=False)
        res[name] = t
    return res


if __name__ == "__main__":
    r = main()
    for k, t in r.items():
        print(k, len(t)); print(t.describe().round(3).to_string())
    cd = r["community_district"].sort_values("E_day")
    print(cd.to_string())
