"""retimed-taxi-fhv-pickups: daytime pickups by taxi zone, Monday and Friday against midweek, Feb-Mar 2019 against Feb-Mar 2026."""
import datetime as dt, json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib, taxi_data

D = dt.date
M19, M26 = ["2019-02", "2019-03"], ["2026-02", "2026-03"]


def run(P0, P1, w0, w1, ex, col="E_day", weights=None, B=2000):
    units = ex.taxi_zone_id.tolist()
    A0, A1 = lib.week_arrays(P0, units, w0), lib.week_arrays(P1, units, w1)
    d0 = (A0[0].sum(1) + A0[1].sum(1)) / (5 * len(w0)); d1 = (A1[0].sum(1) + A1[1].sum(1)) / (5 * len(w1))
    keep = (d0 >= 200) & (d1 >= 200)
    A0 = tuple(a[keep] for a in A0); A1 = tuple(a[keep] for a in A1)
    E = ex[col].values[keep]
    q1, q2 = -0.06389333333333334, -0.0421
    Ed = ex.E_day.values[keep]
    r = lib.estimate(A0, A1, E, {"hi": Ed <= q1, "lo": Ed >= q2}, B=B)
    r["n_zones"] = int(keep.sum()); r["n_hi"] = int((Ed <= q1).sum()); r["n_lo"] = int((Ed >= q2).sum())
    r["daily_pickups"] = [float(d0[keep].sum()), float(d1[keep].sum())]
    Y = lib._r(*A1) - lib._r(*A0)
    if weights:
        r["slope_weighted_by_2019_pickups"] = float(np.polyfit(E, Y, 1, w=np.sqrt(d0[keep]))[0])
    return r, ex[keep].assign(Y=Y, pickups_2019=d0[keep], pickups_recent=d1[keep])


if __name__ == "__main__":
    ex = pd.read_csv(lib.OUT / "exposure_taxi_zone.csv")
    w19 = lib.retained_weeks(D(2019, 2, 1), D(2019, 3, 31)); w26 = lib.retained_weeks(D(2026, 2, 1), D(2026, 3, 31))
    src = []
    P = {}
    for name, kinds, months in (("y19", ["yellow"], M19), ("h19", ["fhvhv"], M19), ("y26", ["yellow"], M26), ("h26", ["fhvhv"], M26),
                                ("y18", ["yellow"], ["2018-02", "2018-03"])):
        P[name], s = taxi_data.panel(kinds, months); src += s
    both = lambda a, b: pd.concat([P[a], P[b]]).groupby(["date", "unit"], as_index=False).n.sum()
    out = {"weeks_2019": [str(w) for w in w19], "weeks_2026": [str(w) for w in w26]}
    out["primary"], zones = run(both("y19", "h19"), both("y26", "h26"), w19, w26, ex, weights=True)
    zones.round(5).to_csv(lib.OUT / "taxi_by_zone.csv", index=False)
    out["yellow_only"], _ = run(P["y19"], P["y26"], w19, w26, ex, B=1000)
    out["fhvhv_only"], _ = run(P["h19"], P["h26"], w19, w26, ex, B=1000)
    out["outside_cbd"], _ = run(both("y19", "h19"), both("y26", "h26"), w19, w26, ex[ex.cbd_share_entries < 0.5], B=1000)
    out["placebo_yellow_2018_vs_2019"], _ = run(P["y18"], P["y19"], lib.retained_weeks(D(2018, 2, 1), D(2018, 3, 31)), w19, ex, B=1000)
    # citywide weekday index, all zones
    def idx(Pn, weeks):
        p = Pn.copy(); p["date"] = pd.to_datetime(p.date).dt.date
        days = {w + dt.timedelta(i): i for w in weeks for i in range(5)}
        p = p[p.date.isin(days)]; t = p.groupby(p.date.map(days)).n.sum() / len(weeks)
        return (t / t[[1, 2, 3]].mean()).round(4).tolist(), float(t.mean())
    out["citywide_index"] = {"2019": idx(both("y19", "h19"), w19), "2026": idx(both("y26", "h26"), w26)}
    json.dump(out, open(lib.OUT / "taxi_results.json", "w"), indent=1)
    json.dump(src, open(lib.OUT / "taxi_sources.json", "w"), indent=1)
    print(json.dumps(out, indent=1)[:6000])
