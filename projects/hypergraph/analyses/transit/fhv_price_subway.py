"""transit-fhv-price-subway: did subway entries rise inside the area where for-hire and taxi trips
became more expensive (2 Feb 2019 surcharge, primary; 5 Jan 2025 zone toll, secondary)?

Usage: python -m analyses.transit.fhv_price_subway
Everything fixed in the registration is imported from analyses/transit/register_fhv_price_subway.py.
Writes data/derived/transit/fhv_price_subway_results.json and the weekly series used by the figure.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from pandas.tseries.holiday import USFederalHolidayCalendar

from analyses.mobility.common import nys
from analyses.transit.register_fhv_price_subway import BUFFER_M, COMPOSE, LINE_96, WINDOWS_2019, WINDOWS_2025
from concord import noaa, socrata

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "transit"
DER.mkdir(parents=True, exist_ok=True)
TLC = Path.home() / "opt" / "nyc-concordance" / "tlc_2019"
TLC_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/"
GOOD_FRIDAY = ["2017-04-14", "2018-03-30", "2019-04-19", "2022-04-15", "2023-04-07", "2024-03-29", "2025-04-18"]
SOURCES: list[dict] = []
M_LAT = 111_320.0
M_LON = 111_320.0 * math.cos(math.radians(40.75))


# ---------- days ----------
def excluded_days() -> set:
    hol = set(USFederalHolidayCalendar().holidays("2017-01-01", "2025-12-31"))
    tg = [d + pd.Timedelta(days=1) for d in hol if d.month == 11 and d.weekday() == 3]
    w, src = noaa.daily()
    SOURCES.append({**src, "data_access": "open", "use": "snow-day rule (SNOW >= 76 mm)"})
    snow = set(w.index[w["SNOW"] >= 76])
    return hol | set(tg) | set(pd.to_datetime(GOOD_FRIDAY)) | snow


# ---------- subway ----------
def dataset_for(day: pd.Timestamp) -> str:
    return "t69i-h2me" if day.year <= 2019 else ("wujg-7c2s" if day.year <= 2024 else "5wq4-mkjj")


SELECT = ("date_trunc_ymd(transit_timestamp) as d, station_complex_id, borough, transit_mode, "
          "case(date_extract_hh(transit_timestamp) >= 20 or date_extract_hh(transit_timestamp) < 4, 1, true, 0) as night, "
          "min(latitude) as lat, min(longitude) as lon, sum(ridership) as n")


def _one(ds: str, a: pd.Timestamp, b: pd.Timestamp):
    rows, src = socrata.query(  # the caller has set socrata.DOMAIN to data.ny.gov
        ds, select=SELECT,
        where=f"transit_timestamp >= '{a:%Y-%m-%dT00:00:00}' and transit_timestamp < '{b:%Y-%m-%dT00:00:00}'",
        group="d, station_complex_id, borough, transit_mode, night", limit=50000)
    if len(rows) >= 50000:
        raise RuntimeError("row limit reached; shorten the chunk")
    return rows, {**src, "url": f"https://data.ny.gov/d/{ds}"}


def _chunk(a: pd.Timestamp, b: pd.Timestamp):
    """One week in one query; if the server does not answer, the same week one day at a time."""
    ds = dataset_for(a)
    try:
        r, s = _one(ds, a, b)
        return [(r, s)]
    except RuntimeError:
        return [_one(ds, d, d + pd.Timedelta(days=1)) for d in pd.date_range(a, b - pd.Timedelta(days=1))]


def fetch_subway(start: str, end: str) -> pd.DataFrame:
    """Daily entries by complex, split into night (20:00-03:59) and other hours, start..end inclusive.
    One query per week (two-week queries took over a minute and sometimes timed out), three at a time."""
    from concurrent.futures import ThreadPoolExecutor
    chunks = []
    a = pd.Timestamp(start)
    stop = pd.Timestamp(end) + pd.Timedelta(days=1)
    while a < stop:
        b = min(a + pd.Timedelta(days=7), stop)
        if b.year != a.year:  # datasets split at year ends
            b = pd.Timestamp(year=b.year, month=1, day=1)
        chunks.append((a, b))
        a = b
    out = []
    import functools
    old, old_req = socrata.DOMAIN, socrata._req
    socrata.DOMAIN = "https://data.ny.gov"  # set once for all threads; the domain() helper is not thread-safe
    socrata._req = functools.partial(old_req, retries=2, timeout=75)  # fail fast, then fall back to daily queries
    try:
        with ThreadPoolExecutor(3) as ex:
            for parts in ex.map(lambda ab: _chunk(*ab), chunks):
                for rows, src in parts:
                    SOURCES.append({**src, "data_access": "open", "domain": "data.ny.gov (concord.socrata.DOMAIN set to https://data.ny.gov)"})
                    out.extend(rows)
    finally:
        socrata.DOMAIN, socrata._req = old, old_req
    df = pd.DataFrame(out)
    df = df[df.transit_mode == "subway"].copy()
    df["d"] = pd.to_datetime(df.d)
    for c in ("n", "lat", "lon"):
        df[c] = df[c].astype(float)
    df["night"] = df.night.astype(int)
    return df


def complexes(df: pd.DataFrame) -> pd.DataFrame:
    """One row per complex: coordinates, borough, signed distance (m) south of the 96th Street line, grid cell."""
    c = df.groupby("station_complex_id").agg(lat=("lat", "median"), lon=("lon", "median"), borough=("borough", "first"))
    (y1, x1), (y2, x2) = LINE_96
    dx, dy = (x2 - x1) * M_LON, (y2 - y1) * M_LAT
    px, py = (c.lon - x1) * M_LON, (c.lat - y1) * M_LAT
    cross = (dx * py - dy * px) / math.hypot(dx, dy)
    ref = dx * ((40.755 - y1) * M_LAT) - dy * ((-73.987 - x1) * M_LON)  # Times Square is south
    c["south_m"] = cross * np.sign(ref)
    c["cell"] = (np.floor(c.lon * M_LON / 1500).astype(int).astype(str) + "_" + np.floor(c.lat * M_LAT / 1500).astype(int).astype(str))
    return c


def window_means(df: pd.DataFrame, windows: dict, excl: set, weekend=False, night=None, min_cover=0.9) -> pd.DataFrame:
    """Mean daily entries per complex in each window; NaN where coverage is under 90% of included days."""
    d = df if night is None else df[df.night == night]
    daily = d.groupby(["station_complex_id", "d"]).n.sum().unstack("d")
    cols = {}
    for y, w in windows.items():
        for part in ("pre", "post"):
            days = pd.date_range(*w[part])
            days = [x for x in days if (x.weekday() >= 5) == weekend and (weekend or x not in excl)]
            sub = daily.reindex(columns=days)
            cover = (sub.fillna(0) > 0).mean(axis=1)
            m = sub.fillna(0).mean(axis=1)
            cols[f"{y}_{part}"] = m.where(cover >= min_cover)
            cols[f"{y}_{part}_ndays"] = len(days)
    return pd.DataFrame(cols)


def ddd(wm: pd.DataFrame, cx: pd.DataFrame, y1: str, y0: str, inside: pd.Series, keep: pd.Series,
        weighted=True, single=False) -> dict:
    """Coefficient on `inside` for D_c = y(y1) - y(y0), y = log(post/pre). `single` drops the y0 term."""
    need = [f"{y1}_pre", f"{y1}_post"] + ([] if single else [f"{y0}_pre", f"{y0}_post"])
    t = wm.join(cx).loc[keep.reindex(wm.index).fillna(False)]
    t = t.dropna(subset=need + ([f"{y0}_pre"] if weighted else []))
    D = np.log(t[f"{y1}_post"] / t[f"{y1}_pre"])
    if not single:
        D = D - np.log(t[f"{y0}_post"] / t[f"{y0}_pre"])
    ins = inside.reindex(t.index).astype(float)
    X = sm.add_constant(ins.rename("inside"))
    w = t[f"{y0}_pre"] if weighted else pd.Series(1.0, index=t.index)
    r = sm.WLS(D, X, weights=w).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(t.cell)[0]})
    b, se = float(r.params["inside"]), float(r.bse["inside"])
    pc = lambda x: round(100 * (math.exp(x) - 1), 3)
    return {"b_log": round(b, 5), "se_log": round(se, 5), "pct": pc(b), "lo": pc(b - 1.96 * se), "hi": pc(b + 1.96 * se),
            "n_inside": int(ins.sum()), "n_outside": int((1 - ins).sum()), "n_clusters": int(t.cell.nunique()),
            "entries_inside_y1_pre": round(float(t.loc[ins == 1, f"{y1}_pre"].sum())),
            "entries_outside_y1_pre": round(float(t.loc[ins == 0, f"{y1}_pre"].sum()))}


def weekly_ratio(df, cx, inside, keep, windows, excl) -> list[dict]:
    """Weekly log ratio of inside to outside weekday entries, relative to each year's pre-window mean."""
    out = []
    d = df.groupby(["station_complex_id", "d"]).n.sum().reset_index()
    d = d[d.station_complex_id.isin(keep.index[keep])]
    d["inside"] = d.station_complex_id.map(inside)
    for y, w in windows.items():
        days = [x for x in pd.date_range(w["pre"][0], w["post"][1]) if x.weekday() < 5 and x not in excl]
        s = d[d.d.isin(days)].groupby(["d", "inside"]).n.sum().unstack("inside")
        s["week"] = ((s.index - pd.Timestamp(w["post"][0])).days // 7)
        wk = s.groupby("week").mean()
        lr = np.log(wk[True] / wk[False])
        base = lr[lr.index < 0].mean()
        out += [{"year": y, "week": int(k), "log_ratio_rel_pre": round(float(v - base), 5)} for k, v in lr.items()]
    return out


# ---------- first stage (TLC monthly files) ----------
def taxi_zone_sides() -> pd.DataFrame:
    from shapely.geometry import shape
    rows, src = socrata.query("8meu-9t5y", select="locationid, zone, borough, the_geom", limit=500)
    SOURCES.append({**src, "data_access": "open"})
    rec = []
    (y1, x1), (y2, x2) = LINE_96
    dx, dy = (x2 - x1) * M_LON, (y2 - y1) * M_LAT
    ref = dx * ((40.755 - y1) * M_LAT) - dy * ((-73.987 - x1) * M_LON)
    for r in rows:
        c = shape(r["the_geom"]).centroid
        cross = dx * ((c.y - y1) * M_LAT) - dy * ((c.x - x1) * M_LON)
        rec.append({"zone_id": int(r["locationid"]), "zone": r["zone"], "borough": r["borough"],
                    "south": cross * np.sign(ref) > 0, "lat": c.y, "lon": c.x})
    z = pd.DataFrame(rec).drop_duplicates("zone_id").set_index("zone_id")
    islands = z.zone.str.contains("Roosevelt Island|Randalls Island|Governor|Ellis Island|Liberty Island", regex=True)
    z["inside"] = (z.borough == "Manhattan") & z.south & ~islands
    z["cell"] = (np.floor(z.lon * M_LON / 1500).astype(int).astype(str) + "_" + np.floor(z.lat * M_LAT / 1500).astype(int).astype(str))
    return z


def tlc_daily(zones: pd.DataFrame) -> pd.DataFrame:
    import duckdb
    con = duckdb.connect()
    ins = ",".join(str(i) for i in zones.index[zones.inside])
    parts = []
    spec = {"fhv": ("pickup_datetime", "PUlocationID", "DOlocationID"), "fhvhv": ("pickup_datetime", "PULocationID", "DOLocationID"),
            "yellow": ("tpep_pickup_datetime", "PULocationID", "DOLocationID"), "green": ("lpep_pickup_datetime", "PULocationID", "DOLocationID")}
    for f in sorted(TLC.glob("*.parquet")):
        kind, month = f.name.split("_tripdata_")[0], f.name.split("_tripdata_")[1][:7]
        t, pu, do = spec[kind]
        q = (f"select cast({t} as date) d, cast({pu} as integer) pu, count(*) n, "
             f"sum(case when cast({pu} as integer) in ({ins}) or cast({do} as integer) in ({ins}) then 1 else 0 end) touch "
             f"from read_parquet('{f}') where strftime({t}, '%Y-%m') = '{month}' group by 1, 2")
        p = con.execute(q).df()
        p["kind"] = "fhv" if kind in ("fhv", "fhvhv") else "taxi"
        parts.append(p)
        hdr = {}
        h = Path(str(f) + ".headers")
        if h.exists():
            for line in h.read_text().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    hdr[k.strip().lower()] = v.strip()
        SOURCES.append({"kind": "tlc-trip-record-file", "url": TLC_URL + f.name, "last_modified": hdr.get("last-modified"),
                        "etag": hdr.get("etag"), "bytes": f.stat().st_size, "data_access": "open",
                        "local_copy": "~/opt/nyc-concordance/tlc_2019/" + f.name})
    d = pd.concat(parts)
    d["d"] = pd.to_datetime(d.d)
    return d.groupby(["kind", "d", "pu"], dropna=False)[["n", "touch"]].sum().reset_index()


def first_stage(excl: set) -> dict:
    zones = taxi_zone_sides()
    t = tlc_daily(zones)
    t.to_csv(DER / "fhv_price_tlc_daily_by_zone.csv", index=False)
    W = {k: WINDOWS_2019[k] for k in ("2019", "2018")}
    res = {"inside_zone_ids": [int(i) for i in zones.index[zones.inside]]}
    days_of = {}
    for y, w in W.items():
        for part in ("pre", "post"):
            days_of[f"{y}_{part}"] = [x for x in pd.date_range(*w[part]) if x.weekday() < 5 and x not in excl]
    # share of trips without a usable pickup zone
    miss = {}
    for k, days in days_of.items():
        s = t[t.d.isin(days)]
        for kind in ("fhv", "taxi"):
            ss = s[s.kind == kind]
            bad = ss[ss.pu.isna() | ss.pu.isin([264, 265]) | ~ss.pu.isin(zones.index)].n.sum()
            miss[f"{kind}_{k}"] = round(float(bad / ss.n.sum()), 4)
    res["share_trips_without_pickup_zone"] = miss
    res["fhv_unreliable"] = bool(max(v for k, v in miss.items() if k.startswith("fhv")) > 0.10)
    cx = zones[["cell"]]
    for label, kinds in (("fhv_and_taxi", ("fhv", "taxi")), ("fhv", ("fhv",)), ("taxi", ("taxi",))):
        s = t[t.kind.isin(kinds) & t.pu.isin(zones.index)]
        cols = {}
        for k, days in days_of.items():
            g = s[s.d.isin(days)].groupby("pu").n.sum() / len(days)
            cols[k] = g
        wm = pd.DataFrame(cols).reindex(zones.index)
        wm = wm.where(wm >= 20)  # a zone needs at least 20 pickups a weekday in every window
        wm.index.name = "zone_id"
        r = ddd(wm, cx, "2019", "2018", zones.inside, pd.Series(True, index=zones.index))
        r["pickups_inside_2019_pre_per_weekday"] = r.pop("entries_inside_y1_pre")
        r["pickups_outside_2019_pre_per_weekday"] = r.pop("entries_outside_y1_pre")
        res[label] = r
    pre = t[t.d.isin(days_of["2019_pre"])]
    res["T0_trips_touching_zone_per_weekday_2019_pre"] = round(float(pre.touch.sum() / len(days_of["2019_pre"])))
    res["trips_all_per_weekday_2019_pre"] = round(float(pre.n.sum() / len(days_of["2019_pre"])))
    return res


def compose(fs_log: float, T0: float, E_in: float, E_out: float) -> dict:
    dT = T0 * (1 - math.exp(fs_log))
    out = {"dT_trips_lost_per_weekday": round(dT)}
    for i, name in enumerate(("p_lo", "p_c", "p_hi")):
        o, dv, s = COMPOSE["occupancy"][i], COMPOSE["diversion_to_subway"][i], COMPOSE["share_boarding_in_zone"][i]
        X = o * dv * dT
        p = 100 * (s * X / E_in - (1 - s) * X / E_out)
        out[name] = round(max(p, 0.0) if name == "p_lo" else p, 4)
        out[name + "_added_entries"] = round(X)
    return out


def main():
    excl = excluded_days()
    res = {"excluded_days_in_windows": sorted(f"{d:%Y-%m-%d}" for d in excl
                                             if any(pd.Timestamp(w[p][0]) <= d <= pd.Timestamp(w[p][1])
                                                    for W in (WINDOWS_2019, WINDOWS_2025) for w in W.values() for p in ("pre", "post")))}
    st, ssrc = nys("39hk-dx4f", select="complex_id, cbd, daytime_routes, stop_name, borough, gtfs_latitude, gtfs_longitude", limit=5000)
    SOURCES.append({**ssrc, "data_access": "open"})
    st = pd.DataFrame(st)
    cbd = st.groupby("complex_id").cbd.agg(lambda s: (s == "true").any())
    lroute = st.groupby("complex_id").daytime_routes.agg(lambda s: any("L" in str(x).split() for x in s))

    # ----- primary: 2019 -----
    W16 = {y: {"pre": w["pre"], "post": [w["post"][0], f"{pd.Timestamp(w['post'][1]) + pd.Timedelta(weeks=8):%Y-%m-%d}"]}
           for y, w in WINDOWS_2019.items() if y != "2017"}
    df = pd.concat([fetch_subway(WINDOWS_2019["2017"]["pre"][0], WINDOWS_2019["2017"]["post"][1]),
                    fetch_subway(W16["2018"]["pre"][0], W16["2018"]["post"][1]),
                    fetch_subway(W16["2019"]["pre"][0], W16["2019"]["post"][1])])
    cx = complexes(df)
    cx["cbd"] = cbd.reindex(cx.index)
    cx["L"] = lroute.reindex(cx.index).fillna(False)
    res["station_table_join_missing"] = int(cx.cbd.isna().sum())
    roosevelt = cx.index.isin(st[st.stop_name.str.contains("Roosevelt Island")].complex_id)
    mn = cx.borough == "Manhattan"
    band = cx.south_m.abs() <= BUFFER_M
    inside = mn & (cx.south_m > 0)
    base_keep = ~roosevelt & cx.borough.isin(["Manhattan", "Bronx", "Brooklyn", "Queens"])
    keep = base_keep & ~(mn & band)
    res["band_complexes"] = sorted(cx.index[mn & band & base_keep])
    wm = window_means(df, WINDOWS_2019, excl)
    P = {"primary": ddd(wm, cx, "2019", "2018", inside, keep),
         "placebo_2018_vs_2017": ddd(wm, cx, "2018", "2017", inside, keep),
         "S1_control_manhattan_north": ddd(wm, cx, "2019", "2018", inside, keep & mn),
         "S2_control_bronx_brooklyn_queens": ddd(wm, cx, "2019", "2018", inside, keep & (inside | ~mn)),
         "S3_unweighted": ddd(wm, cx, "2019", "2018", inside, keep, weighted=False),
         "S4_with_96_st_complexes": ddd(wm, cx, "2019", "2018", mn & (cx.south_m > -BUFFER_M), base_keep),
         "S5_without_L_complexes": ddd(wm, cx, "2019", "2018", inside, keep & ~cx.L),
         "S6_post_16_weeks": ddd(window_means(df, W16, excl), cx, "2019", "2018", inside, keep),
         "S7_night_20_to_04": ddd(window_means(df, WINDOWS_2019, excl, night=1), cx, "2019", "2018", inside, keep),
         "S7_placebo_night": ddd(window_means(df, WINDOWS_2019, excl, night=1), cx, "2018", "2017", inside, keep),
         "S8_weekends": ddd(window_means(df, WINDOWS_2019, excl, weekend=True), cx, "2019", "2018", inside, keep),
         "S9_2019_only": ddd(wm, cx, "2019", "2018", inside, keep, single=True),
         "S9_2018_only": ddd(wm, cx, "2018", "2017", inside, keep, single=True)}
    res["primary_2019"] = P
    res["weekly_2019"] = weekly_ratio(df, cx, inside, keep, WINDOWS_2019, excl)
    cx.assign(inside=inside, keep=keep).join(wm).to_csv(DER / "fhv_price_subway_complexes_2019.csv")

    # ----- first stage and composition -----
    fs = first_stage(excl)
    res["first_stage_2019"] = fs
    gate = fs["taxi"] if fs["fhv_unreliable"] else fs["fhv_and_taxi"]
    res["gate"] = {"series": "taxi" if fs["fhv_unreliable"] else "fhv_and_taxi", "pct": gate["pct"], "lo": gate["lo"], "hi": gate["hi"],
                   "passed": bool(gate["hi"] < 0)}
    comp = compose(gate["b_log"], fs["T0_trips_touching_zone_per_weekday_2019_pre"],
                   P["primary"]["entries_inside_y1_pre"], P["primary"]["entries_outside_y1_pre"])
    res["composed"] = comp
    b, se = P["primary"]["b_log"], P["primary"]["se_log"]
    pcl = math.log(1 + comp["p_c"] / 100)
    res["rule8"] = {"z_null": round(b / se, 2), "z_pred": round((b - pcl) / se, 2), "D": round((b / se) ** 2 - ((b - pcl) / se) ** 2, 2),
                    "min_detectable_effect_pct": round(100 * (math.exp(2.8 * se) - 1), 2),
                    "se_needed_for_D4_at_p_c_pct": round(comp["p_c"] / 2, 3), "se_pct": round(100 * se, 3)}

    # ----- secondary: 2025 -----
    d2 = pd.concat([fetch_subway(w["pre"][0], w["pre"][1]) for w in WINDOWS_2025.values()] +
                   [fetch_subway(w["post"][0], w["post"][1]) for w in WINDOWS_2025.values()])
    c2 = complexes(d2)
    c2["cbd"] = cbd.reindex(c2.index)
    keep2 = c2.borough.isin(["Manhattan", "Bronx", "Brooklyn", "Queens"]) & c2.cbd.notna()
    in2 = c2.cbd.fillna(False).astype(bool)
    wm2 = window_means(d2, WINDOWS_2025, excl)
    res["secondary_2025"] = {"estimate": ddd(wm2, c2, "2025", "2024", in2, keep2),
                             "placebo_2024_vs_2023": ddd(wm2, c2, "2024", "2023", in2, keep2),
                             "control_manhattan_north_of_60": ddd(wm2, c2, "2025", "2024", in2, keep2 & (c2.borough == "Manhattan")),
                             "placebo_control_manhattan_north_of_60": ddd(wm2, c2, "2024", "2023", in2, keep2 & (c2.borough == "Manhattan")),
                             "night": ddd(window_means(d2, WINDOWS_2025, excl, night=1), c2, "2025", "2024", in2, keep2),
                             "station_table_join_missing": int(c2.cbd.isna().sum())}
    res["sources"] = SOURCES
    (DER / "fhv_price_subway_results.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k not in ("sources", "weekly_2019")}, indent=1, default=str))


if __name__ == "__main__":
    main()


def exploratory_touch() -> dict:
    """EXPLORATORY, not registered: trips that touch the zone (pickup or drop-off inside) against trips that
    do not, by weekday, from the saved daily file. The registered first stage compares pickup zones, but a
    trip from an airport to Midtown also pays the surcharge. Day-level regression of log(touch / not touch)
    on post, 2019, and their product, HAC (5 lags)."""
    t = pd.read_csv(DER / "fhv_price_tlc_daily_by_zone.csv", parse_dates=["d"])
    excl = excluded_days()
    SOURCES.pop()
    out = {}
    for label, kinds in (("fhv_and_taxi", ("fhv", "taxi")), ("fhv", ("fhv",)), ("taxi", ("taxi",))):
        g = t[t.kind.isin(kinds)].groupby("d")[["n", "touch"]].sum()
        rows = []
        for y in ("2018", "2019"):
            for part in ("pre", "post"):
                for x in pd.date_range(*WINDOWS_2019[y][part]):
                    if x.weekday() < 5 and x not in excl and x in g.index:
                        rows.append({"y": math.log(g.touch[x] / (g.n[x] - g.touch[x])), "post": part == "post", "y19": y == "2019", "d": x})
        d = pd.DataFrame(rows).sort_values("d")
        X = sm.add_constant(pd.DataFrame({"post": d.post, "y19": d.y19, "did": d.post & d.y19}).astype(float))
        r = sm.OLS(d.y.values, X.values).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        b, se = float(r.params[3]), float(r.bse[3])
        pc = lambda v: round(100 * (math.exp(v) - 1), 2)
        out[label] = {"pct": pc(b), "lo": pc(b - 1.96 * se), "hi": pc(b + 1.96 * se), "n_days": len(d),
                      "touch_per_weekday_2019_pre": round(float(d[(d.y19) & (~d.post)].d.map(g.touch).mean())),
                      "touch_per_weekday_2019_post": round(float(d[(d.y19) & (d.post)].d.map(g.touch).mean())),
                      "touch_per_weekday_2018_pre": round(float(d[(~d.y19) & (~d.post)].d.map(g.touch).mean())),
                      "touch_per_weekday_2018_post": round(float(d[(~d.y19) & (d.post)].d.map(g.touch).mean()))}
    return out
