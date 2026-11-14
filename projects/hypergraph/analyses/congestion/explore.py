"""Exploratory results for docs/congestion_tradeoffs.md (no registered test). Writes
data/derived/congestion/explore_results.json. Every number from this file is exploratory.

Sections: business proxies (restaurant openings among surviving restaurants, licence
applications, subway entries at evenings and weekends, taxi drop-offs), traffic by weekday
and hour (CRZ entries, taxi and bus speeds), and hot nights (overnight EMS travel time).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from concord import noaa
from analyses.congestion.common import DER, ROOT, area_of_zip, is_peak
from analyses.congestion import ems_lib as L, speed_lib as S

R = {}
f3 = lambda r: {"pct": round(r["pct"], 2), "lo": round(r["lo"], 2), "hi": round(r["hi"], 2), "n_months": r["n_months"]}


def rr(a1, a0, b1, b0):
    """Ratio of ratios (a1/a0)/(b1/b0) with a Poisson log-scale interval."""
    e = np.log(a1 / a0) - np.log(b1 / b0)
    se = np.sqrt(1 / a1 + 1 / a0 + 1 / b1 + 1 / b0)
    return {"ratio": float(np.exp(e)), "lo": float(np.exp(e - 1.96 * se)), "hi": float(np.exp(e + 1.96 * se))}


# ---------------- business proxies
r = pd.read_csv(DER / "restaurants_prepermit.csv", dtype={"zipcode": str})
r["y"] = pd.to_datetime(r.first_prepermit).dt.year
r["zone"] = r.zipcode.map(area_of_zip) == "crz"
c = r[r.y >= 2023].groupby(["y", "zone"]).size().unstack()
R["restaurant_openings_surviving"] = {
    "counts_zone": {int(k): int(v) for k, v in c[True].items()}, "counts_outside": {int(k): int(v) for k, v in c[False].items()},
    "zone_share_pct": {int(k): round(100 * c.loc[k, True] / c.loc[k].sum(), 1) for k in c.index},
    "post_2025_26_vs_2023_24": rr(c.loc[[2025, 2026], True].sum(), c.loc[[2023, 2024], True].sum(), c.loc[[2025, 2026], False].sum(), c.loc[[2023, 2024], False].sum()),
    "pre_trend_2024_vs_2023": rr(c.loc[2024, True], c.loc[2023, True], c.loc[2024, False], c.loc[2023, False]),
    "y2025_vs_2024": rr(c.loc[2025, True], c.loc[2024, True], c.loc[2025, False], c.loc[2024, False]),
    "y2026_vs_2025": rr(c.loc[2026, True], c.loc[2025, True], c.loc[2026, False], c.loc[2025, False])}
d = pd.read_csv(DER / "dcwp_premises_new.csv")
d["y"] = d.y.str[:4].astype(int)
d["zone"] = d.area == "crz"
c = d.groupby(["y", "zone"]).n.sum().unstack()
R["dcwp_premises_new_applications"] = {"zone": {int(k): int(v) for k, v in c[True].items()},
                                       "zone_share_pct": {int(k): round(100 * c.loc[k, True] / c.loc[k].sum(), 1) for k in c.index},
                                       "y2025_vs_2024": rr(c.loc[2025, True], c.loc[2024, True], c.loc[2025, False], c.loc[2024, False])}

t = pd.read_csv(DER / "taxi_dropoffs.csv")
t["d"] = pd.to_datetime(t.d)
t = t[(t.d >= "2023-07-01") & (t.d < "2026-07-01") & ~((t.d >= "2025-01-01") & (t.d < "2025-01-05"))]
t["dow"] = t.d.dt.dayofweek
t["month"] = t.d.dt.to_period("M").dt.to_timestamp()
parts = {"weekday_evening_19_23": (t.dow < 5) & (t.hh >= 19), "weekend": t.dow >= 5, "weekday_day_6_18": (t.dow < 5) & (t.hh >= 6) & (t.hh < 19)}
R["taxi_dropoffs"] = {}
for nm, m in parts.items():
    g = t[m].groupby(["month", "area"]).n.sum().unstack()
    for comp in ("north", "other"):
        R["taxi_dropoffs"][f"{nm}_cbd_vs_{comp}"] = f3(L.did(np.log(g["cbd"] / g[comp]), "2025-01-01", "2023-07-01"))
        R["taxi_dropoffs"][f"{nm}_cbd_vs_{comp}_placebo_2024"] = f3(L.did(np.log(g["cbd"] / g[comp]), "2024-04-01", "2023-07-01", "2024-12-01"))

sf = DER / "subway_entries_parts.csv"
if sf.exists():
    s = pd.read_csv(sf)
    s["m"] = pd.to_datetime(s.m)
    dm = pd.read_csv(ROOT / "data/derived/transit/dose_map.csv")[["complex_id", "in_cbd", "borough", "latitude", "community_district"]]
    s["complex_id"] = pd.to_numeric(s.station_complex_id, errors="coerce")
    s = s.merge(dm, on="complex_id")
    s["grp"] = np.where(s.in_cbd, "cbd", np.where((s.borough == "Manhattan") & (s.latitude < 40.80), "north",
                        np.where(s.community_district.isin([302, 401, 402]), "bklic", "rest")))
    R["subway_entries"] = {"months": [str(s.m.min())[:7], str(s.m.max())[:7]]}
    last = s.m.max()
    s = s[s.m < last] if last >= pd.Timestamp("2026-11-01") else s
    for part in ("wk_evening", "weekend", "wk_day"):
        g = s[s.part == part].groupby(["m", "grp"]).n.sum().unstack()
        for comp in ("north", "bklic", "rest"):
            dd = np.log(g["cbd"] / g[comp])
            R["subway_entries"][f"{part}_cbd_vs_{comp}"] = f3(L.did(dd, "2025-01-01", "2023-01-01"))
            R["subway_entries"][f"{part}_cbd_vs_{comp}_placebo_2024"] = f3(L.did(dd, "2024-01-01", "2023-01-01", "2024-12-01"))
        own = np.log(g["cbd"])
        R["subway_entries"][f"{part}_cbd_own"] = f3(L.did(own, "2025-01-01", "2023-01-01"))
        g.to_csv(DER / f"subway_{part}_monthly.csv")

# ---------------- traffic by weekday and hour
e = pd.read_csv(DER / "crz_entries_month_dow_hour.csv")
e["m"] = pd.to_datetime(e.m)
e = e[e.m < "2026-11-01"]
days = e.groupby(["m", "dow"]).days.max().groupby("dow").sum()
names = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}
per_day = (e.groupby("dow").entries.sum() / days)
mid = per_day[[3, 4, 5]].mean()
grid = (e.groupby(["dow", "hh"]).entries.sum().unstack("dow") / days)
grid.rename(columns=names).to_csv(DER / "crz_entries_dow_hour.csv")
car = e[e.vehicle_class.str.startswith("1")]
R["crz_entries"] = {"per_day": {names[k]: round(float(v)) for k, v in per_day.items()},
                    "vs_midweek_pct": {names[k]: round(100 * (float(v) / mid - 1), 1) for k, v in per_day.items()},
                    "share_peak_pct": round(100 * e[e.time_period == "Peak"].entries.sum() / e.entries.sum(), 1),
                    "share_taxi_fhv_pct": round(100 * e[e.vehicle_class.str.contains("TLC")].entries.sum() / e.entries.sum(), 1),
                    "share_cars_pct": round(100 * car.entries.sum() / e.entries.sum(), 1),
                    "weekday_am_peak_6_9_vs_midweek_pct": {names[k]: round(100 * (grid.loc[6:9, k].sum() / grid.loc[6:9, [3, 4, 5]].sum().mean() - 1), 1) for k in (2, 6)},
                    "evening_19_23_vs_midweek_pct": {names[k]: round(100 * (grid.loc[19:23, k].sum() / grid.loc[19:23, [3, 4, 5]].sum().mean() - 1), 1) for k in (2, 6, 7, 1)},
                    "per_day_2025": round(float(e[e.m.dt.year == 2025].entries.sum() / e[e.m.dt.year == 2025].groupby(["m", "dow"]).days.max().sum())),
                    "per_day_2026_jan_oct": round(float(e[e.m.dt.year == 2026].entries.sum() / e[e.m.dt.year == 2026].groupby(["m", "dow"]).days.max().sum())),
                    "jan_oct_2026_vs_jan_oct_2025_pct": None}
a = e[(e.m.dt.year == 2025) & (e.m.dt.month <= 10)]
b = e[(e.m.dt.year == 2026) & (e.m.dt.month <= 10)]
R["crz_entries"]["jan_oct_2026_vs_jan_oct_2025_pct"] = round(100 * ((b.entries.sum() / b.groupby(["m", "dow"]).days.max().sum()) / (a.entries.sum() / a.groupby(["m", "dow"]).days.max().sum()) - 1), 1)

df = S.load()
R["taxi_speed_cbd_vs_north"] = {}
for g in S.GROUPS:
    tt = S.series(df, g)
    R["taxi_speed_cbd_vs_north"][g] = {"post_to_jun_2026": f3(L.did(tt, "2025-01-01", "2023-07-01")),
                                       "y2025": f3(L.did(tt, "2025-01-01", "2023-07-01", "2025-12-01")),
                                       "own_cbd": f3(L.did(S.series(df, g, ("cbd", None)), "2025-01-01", "2023-07-01")),
                                       "level_2024_mph": round(float(np.exp(S.series(df, g, ("cbd", None))["2024-01-01":"2024-12-01"]).mean()), 2)}
rows = []
for nm, days_ in [("Mon", [0]), ("Tue-Thu", [1, 2, 3]), ("Fri", [4]), ("Sat", [5]), ("Sun", [6])]:
    for blk, hrs in [("05-09", range(5, 10)), ("10-15", range(10, 16)), ("16-20", range(16, 21)), ("21-04", [21, 22, 23, 0, 1, 2, 3, 4])]:
        S.GROUPS["_x"] = lambda x, days_=days_, hrs=list(hrs): x.dow.isin(days_) & x.hh.isin(hrs)
        r_ = L.did(S.series(df, "_x"), "2025-01-01", "2023-07-01")
        o_ = L.did(S.series(df, "_x", ("cbd", None)), "2025-01-01", "2023-07-01")
        rows.append({"day": nm, "hours": blk, "did_vs_north_pct": r_["pct"], "lo": r_["lo"], "hi": r_["hi"], "own_cbd_pct": o_["pct"],
                     "level_2024_mph": float(np.exp(S.series(df, "_x", ("cbd", None))["2024-01-01":"2024-12-01"]).mean())})
del S.GROUPS["_x"]
pd.DataFrame(rows).to_csv(DER / "taxi_speed_did_day_block.csv", index=False)
R["taxi_speed_day_block"] = [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in x.items()} for x in rows]

b = pd.read_csv(DER / "bus_speed_cbd.csv")
b["month"] = pd.to_datetime(b.month)
b = b[b.route_type.isin(["Local", "SBS", "Limited"])]


def bser(day, hours):
    x = b[(b.day_type == day) & (b.hour_of_day.isin(list(hours)))].groupby(["month", "cbd_relation"])[["miles", "hours"]].sum()
    return np.log(x.miles / x.hours).unstack()


R["bus_speed_cbd_vs_noncbd_routes"] = {}
for lab, day, hrs in [("weekday_05_09", "Weekday", range(5, 10)), ("weekday_10_15", "Weekday", range(10, 16)), ("weekday_16_20", "Weekday", range(16, 21)),
                      ("weekday_overnight_21_04", "Weekday", [21, 22, 23, 0, 1, 2, 3, 4]), ("weekend_peak_09_20", "Weekend", range(9, 21)),
                      ("weekend_overnight_21_08", "Weekend", [21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8])]:
    s_ = bser(day, hrs)
    dd = s_["CBD"] - s_["Non-CBD"]
    R["bus_speed_cbd_vs_noncbd_routes"][lab] = {"post_to_sep_2026": f3(L.did(dd, "2025-01-01", "2023-01-01")),
                                                 "placebo_2024": f3(L.did(dd, "2024-01-01", "2023-01-01", "2024-12-01")),
                                                 "level_2024_mph": round(float(np.exp(s_["CBD"]["2024-01-01":"2024-12-01"]).mean()), 2)}

# ---------------- hot nights (exploratory, raised half in jest)
w, wsrc = noaa.daily("central_park")
w = w.reset_index().rename(columns={"DATE": "d"})[["d", "TMAX", "TMIN"]]
ems = pd.concat([pd.read_csv(DER / f"ems_{y}.csv") for y in range(2019, 2027)])
ems["d"] = pd.to_datetime(ems.d)
# a night = 21:00 to 04:59; hours 0-4 belong to the previous calendar day's night
ems["night"] = np.where(ems.hh >= 21, ems.d, np.where(ems.hh < 5, ems.d - pd.Timedelta(days=1), pd.NaT))
ems["night"] = pd.to_datetime(ems["night"])
nt = ems.dropna(subset=["night"])
nt = nt[nt.night.dt.month.isin([6, 7, 8]) & (nt.night.dt.year != 2020)]
nt["zone"] = nt.area == "crz"
g = nt.groupby(["night", "zone"])[["travel", "response", "n"]].sum().reset_index().merge(w, left_on="night", right_on="d")
g["hot"] = g.TMAX >= 32.2   # 90 F
g["tt"], g["rt"] = g.travel / g.n, g.response / g.n
g["year"] = g.night.dt.year
import statsmodels.formula.api as smf
hot = {"definition": "nights (21:00-04:59) from June to August, 2019 and 2021-2026, after a day with a maximum of at least 32.2 C (90 F) at Central Park",
       "n_nights": int(g.night.nunique()), "n_hot_nights": int(g[g.hot].night.nunique())}
for z, nm in [(True, "zone"), (False, "outside")]:
    x = g[g.zone == z]
    for v, lab in [("tt", "travel"), ("rt", "response"), ("n", "incidents")]:
        m = smf.ols(f"np.log({v}) ~ hot + C(year) + C(night.dt.dayofweek)", data=x.assign(hot=x.hot.astype(int))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        bb, se = m.params["hot"], m.bse["hot"]
        hot[f"{nm}_{lab}_hot_vs_other_pct"] = {"pct": round(100 * (np.exp(bb) - 1), 2), "lo": round(100 * (np.exp(bb - 1.96 * se) - 1), 2), "hi": round(100 * (np.exp(bb + 1.96 * se) - 1), 2)}
    hot[f"{nm}_mean_travel_s_hot"] = round(float(x[x.hot].travel.sum() / x[x.hot].n.sum()), 1)
    hot[f"{nm}_mean_travel_s_other"] = round(float(x[~x.hot].travel.sum() / x[~x.hot].n.sum()), 1)
# gunshot calls at night
sh = pd.concat([pd.read_csv(DER / f"shot_{y}.csv", dtype={"disp": str}) for y in range(2019, 2027)])
sh = sh[sh.ct == "SHOT"]
sh["d"] = pd.to_datetime(sh.d)
sh["night"] = pd.to_datetime(np.where(sh.hh >= 21, sh.d, np.where(sh.hh < 5, sh.d - pd.Timedelta(days=1), pd.NaT)))
sn = sh.dropna(subset=["night"])
sn = sn[sn.night.dt.month.isin([6, 7, 8]) & (sn.night.dt.year != 2020)]
sv = sn[sn.valid == "Y"]
k = sv.groupby("night")[["n", "travel", "response"]].sum().reset_index().merge(w, left_on="night", right_on="d", how="right")
k = k[k.d.dt.month.isin([6, 7, 8]) & (k.d.dt.year >= 2019) & (k.d.dt.year != 2020) & (k.d <= "2026-08-31")].fillna({"n": 0, "travel": 0, "response": 0})
k["hot"] = k.TMAX >= 32.2
hot["gunshot_calls_per_night_hot"] = round(float(k[k.hot].n.mean()), 2)
hot["gunshot_calls_per_night_other"] = round(float(k[~k.hot].n.mean()), 2)
hot["gunshot_travel_s_hot"] = round(float(k[k.hot].travel.sum() / k[k.hot].n.sum()), 1)
hot["gunshot_travel_s_other"] = round(float(k[~k.hot].travel.sum() / k[~k.hot].n.sum()), 1)
hot["gunshot_calls_in_zone_share_pct"] = round(100 * float(sn[sn.area == "crz"].n.sum() / sn.n.sum()), 1)
hot["gunshot_calls_in_zone_per_summer_night"] = round(float(sn[sn.area == "crz"].n.sum() / k.d.nunique()), 3)
# how congested is the night: zone travel time by hour, recent summers
hh = ems[(ems.area == "crz") & (ems.d >= "2023-01-01") & (ems.d < "2025-01-01")].groupby("hh")[["travel", "n"]].sum()
hot["zone_travel_s_by_hour_2023_24"] = {int(i): round(float(v), 0) for i, v in (hh.travel / hh.n).items()}
v = hh.travel / hh.n
hot["zone_travel_s_min_hour"] = float(v.min())
hot["zone_travel_s_21_04"] = float(hh.loc[[21, 22, 23, 0, 1, 2, 3, 4]].travel.sum() / hh.loc[[21, 22, 23, 0, 1, 2, 3, 4]].n.sum())
hot["zone_travel_s_10_18"] = float(hh.loc[10:18].travel.sum() / hh.loc[10:18].n.sum())
hot["night_excess_over_quietest_hour_pct"] = round(100 * (hot["zone_travel_s_21_04"] / hot["zone_travel_s_min_hour"] - 1), 1)
hot["weather_source"] = wsrc
R["hot_nights"] = hot

(DER / "explore_results.json").write_text(json.dumps(R, indent=1, default=float))
print(json.dumps({k: v for k, v in R.items() if k not in ("taxi_speed_day_block",)}, indent=1, default=float)[:9000])
