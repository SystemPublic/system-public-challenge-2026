"""Dose map: how much each subway station complex's entries changed since 2019, by weekday and hour band.

Step 1 of docs/consequence_map.md. Exposure only: no crime, health, crash, taxi or restaurant data are read.

Entries come from the MTA Subway Hourly Ridership datasets on data.ny.gov (t69i-h2me for 2019, 5wq4-mkjj for
the recent period). The periods and the week-exclusion rule are those of analyses/transit/weekday_pattern.py:
calendar 2019, and 1 Nov 2025 to 31 Oct 2026, keeping only Monday-to-Sunday weeks that contain no federal
holiday (or day after one) and no day from 24 Dec to 1 Jan. Each retained week is queried separately, in two
pieces (Monday-Thursday, Friday-Sunday), because larger groupings time out on the portal.

Run:  ~/.venvs/nyc-concordance/bin/python -m analyses.transit.dose_map
Writes data/derived/transit/dose_map.csv, dose_map_long.csv, dose_map_sources.json, dose_map_summary.json
and figures/transit/dose_map.png.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

import concord.socrata as soc
from analyses.transit.weekday_pattern import retained_weeks, federal_holidays  # noqa: F401  (same exclusion rule)

soc.DOMAIN = "https://data.ny.gov"  # the MTA datasets are on the State portal
NYC = "https://data.cityofnewyork.us"
ROOT = Path(__file__).resolve().parents[2]
OUTD = ROOT / "data" / "derived" / "transit"
FIG = ROOT / "figures" / "transit" / "dose_map.png"
BCACHE = ROOT / "data" / "cache" / "boundaries"
DS = {2019: "t69i-h2me", 2025: "5wq4-mkjj", 2026: "5wq4-mkjj"}
PERIODS = {"y2019": (dt.date(2019, 1, 1), dt.date(2019, 12, 31)), "recent": (dt.date(2025, 11, 1), dt.date(2026, 10, 31))}
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
BANDS = {"night 00-06": range(0, 6), "AM peak 06-10": range(6, 10), "midday 10-16": range(10, 16),
         "PM peak 16-20": range(16, 20), "evening 20-24": range(20, 24)}
BOUNDARIES = {"nta": ("9nt8-h7nd", "2020 Neighborhood Tabulation Areas"), "cd": ("5crt-au7u", "Community Districts"),
              "taxi": ("8meu-9t5y", "NYC Taxi Zones")}
MIN_WEEKS = 20          # as in the S5 complex-level check of the weekday claim
MIN_MIDWEEK = 500       # mean Tue-Thu entries per day in both periods for the deficit to be reported
SOURCES: list[dict] = []


def _src(src):
    SOURCES.append({**src, "data_access": "open", "portal": "data.ny.gov"})


# ------------------------------------------------------------------ ridership
def fetch_period(key: str):
    """Return ids, array (complex, week, dow, hour) of entries for the retained weeks of one period."""
    a, b = PERIODS[key]
    weeks = retained_weeks(a, b)
    idx: dict[str, int] = {}
    chunks = []
    for wi, m in enumerate(weeks):
        ds = DS[m.year]
        for d0, d1 in ((0, 3), (4, 6)):
            lo, hi = m + dt.timedelta(d0), m + dt.timedelta(d1)
            w = f"transit_mode='subway' AND transit_timestamp between '{lo}T00:00:00' and '{hi}T23:59:59'"
            rows, src = soc.query(ds, select="date_trunc_ymd(transit_timestamp) as day, date_extract_hh(transit_timestamp) as hr, "
                                  "station_complex_id, sum(ridership) as n", where=w, group="day,hr,station_complex_id", limit=50000)
            if len(rows) >= 50000:
                raise RuntimeError(f"row limit reached for {lo}")
            _src(src)
            df = pd.DataFrame(rows)
            df["dow"] = (pd.to_datetime(df["day"]).dt.date.map(lambda d: (d - m).days)).astype(int)
            for c in df["station_complex_id"].unique():
                idx.setdefault(c, len(idx))
            chunks.append((wi, df))
    A = np.zeros((len(idx), len(weeks), 7, 24))
    for wi, df in chunks:
        ci = df["station_complex_id"].map(idx).to_numpy()
        A[ci, wi, df["dow"].to_numpy(), df["hr"].astype(int).to_numpy()] = df["n"].astype(float).to_numpy()
    return list(idx), A, weeks


def complex_table():
    """Position, borough and name of each complex from the ridership data; CBD flag from the MTA station table."""
    rows, src = soc.query("5wq4-mkjj", select="station_complex_id, station_complex, borough, avg(latitude) as lat, avg(longitude) as lon",
                          where="transit_mode='subway' AND transit_timestamp between '2026-03-02T00:00:00' and '2026-03-02T23:59:59'",
                          group="station_complex_id,station_complex,borough", limit=5000)
    _src(src)
    recent = pd.DataFrame(rows)
    rows, src = soc.query("t69i-h2me", select="station_complex_id, station_complex, borough, avg(latitude) as lat, avg(longitude) as lon",
                          where="transit_mode='subway' AND transit_timestamp between '2019-03-04T00:00:00' and '2019-03-04T23:59:59'",
                          group="station_complex_id,station_complex,borough", limit=5000)
    _src(src)
    old = pd.DataFrame(rows)
    both = pd.concat([recent, old[~old.station_complex_id.isin(recent.station_complex_id)]], ignore_index=True)
    for c in ("lat", "lon"):
        both[c] = both[c].astype(float)
    rows, src = soc.query("39hk-dx4f", select="complex_id,cbd", limit=5000)
    _src(src)
    cbd = defaultdict(bool)
    for r in rows:
        cbd[r["complex_id"]] |= r["cbd"] == "true"
    both["in_cbd"] = both.station_complex_id.map(lambda c: cbd.get(c, None))
    return both.drop_duplicates("station_complex_id").set_index("station_complex_id")


# ------------------------------------------------------------------ boundaries
def load_boundaries():
    BCACHE.mkdir(parents=True, exist_ok=True)
    out, recs = {}, []
    old = soc.DOMAIN
    for k, (ds, name) in BOUNDARIES.items():
        url = f"{NYC}/resource/{ds}.geojson?$limit=5000"
        f = BCACHE / f"{ds}.geojson"
        if not f.exists():
            r = requests.get(url, timeout=180)
            r.raise_for_status()
            f.write_bytes(r.content)
        soc.DOMAIN = NYC
        try:
            m = soc.metadata(ds)
        finally:
            soc.DOMAIN = old
        feats = json.loads(f.read_text())["features"]
        out[k] = [(shape(x["geometry"]), x["properties"]) for x in feats]
        recs.append({"kind": "nyc-open-data-boundary", "key": k, "dataset": ds, "name": m.get("name"), "url": m.get("url"),
                     "rows_updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(m["rowsUpdatedAt"])) if m.get("rowsUpdatedAt") else None,
                     "download": url, "n_features": len(feats), "sha256_of_download": hashlib.sha256(f.read_bytes()).hexdigest(),
                     "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(f.stat().st_mtime))})
    return out, recs


def locate(bounds, lon, lat, max_m=400.0):
    """Index of the polygon containing the point; if none, the nearest within max_m metres (method recorded)."""
    geoms = [g for g, _ in bounds]
    tree = STRtree(geoms)
    p = Point(lon, lat)
    for i in tree.query(p, predicate="within"):
        return int(i), "within"
    j = int(tree.nearest(p))
    km_lat, km_lon = 111.32, 111.32 * np.cos(np.radians(lat))
    near = geoms[j].exterior.distance(p) if geoms[j].geom_type == "Polygon" else geoms[j].boundary.distance(p)
    d = near * np.hypot(km_lat, km_lon) / np.sqrt(2) * 1000  # approximate metres from degrees
    return (j, "nearest") if d <= max_m else (None, "none")


# ------------------------------------------------------------------ metrics
def deficits(A: np.ndarray):
    """Per-complex mean over weeks of Mon and Fri entries relative to that week's Tue-Thu mean."""
    day = A.sum(axis=3)                           # complex, week, dow
    mid = day[:, :, 1:4].mean(axis=2)
    ok = mid > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        mon, fri = day[:, :, 0] / mid, day[:, :, 4] / mid
    mon[~ok], fri[~ok] = np.nan, np.nan
    return 1 - np.nanmean(np.where(ok, mon, np.nan), axis=1), 1 - np.nanmean(np.where(ok, fri, np.nan), axis=1), ok.sum(axis=1), mid.mean(axis=1)


def main():
    OUTD.mkdir(parents=True, exist_ok=True)
    FIG.parent.mkdir(parents=True, exist_ok=True)
    ids19, A19, w19 = fetch_period("y2019")
    idsR, AR, wR = fetch_period("recent")
    meta = complex_table()
    allids = sorted(c for c in set(ids19) | set(idsR) if c in meta.index)  # a complex with no station record (one id seen for a single week) is dropped
    def align(ids, A):
        out = np.zeros((len(allids),) + A.shape[1:])
        pos = {c: i for i, c in enumerate(ids)}
        for k, c in enumerate(allids):
            if c in pos:
                out[k] = A[pos[c]]
        return out
    A19, AR = align(ids19, A19), align(idsR, AR)
    present19 = np.array([c in set(ids19) for c in allids]); presentR = np.array([c in set(idsR) for c in allids])

    meta = meta.reindex(allids)
    bounds, brecs = load_boundaries()
    geo = {}
    for c in allids:
        r = meta.loc[c]
        if pd.isna(r["lat"]):
            geo[c] = {}
            continue
        g = {}
        for k in ("nta", "cd", "taxi"):
            i, how = locate(bounds[k], r["lon"], r["lat"])
            g[k] = (bounds[k][i][1] if i is not None else None, how)
        geo[c] = g

    # mean entries per day (over retained weeks) by dow and band
    def means(A):
        by = {"all day": A.sum(axis=3).mean(axis=1)}  # complex, dow
        for b, hrs in BANDS.items():
            by[b] = A[:, :, :, list(hrs)].sum(axis=3).mean(axis=1)
        return by
    M19, MR = means(A19), means(AR)

    long_rows = []
    for bi, band in enumerate(["all day"] + list(BANDS)):
        for di, d in enumerate(DOW):
            for k, c in enumerate(allids):
                e19, eR = M19[band][k, di], MR[band][k, di]
                long_rows.append((c, d, band, eR, e19, eR / e19 if e19 > 0 and present19[k] and presentR[k] else np.nan))
    L = pd.DataFrame(long_rows, columns=["complex_id", "weekday", "band", "entries_recent", "entries_2019", "ratio"])
    L.insert(1, "complex", [meta.loc[c, "station_complex"] for c in L.complex_id])
    L["entries_recent"] = L.entries_recent.round(1)
    L["entries_2019"] = L.entries_2019.round(1)
    L["ratio"] = L.ratio.round(4)
    L.to_csv(OUTD / "dose_map_long.csv", index=False)

    dm19, df19, n19, mid19 = deficits(A19)
    dmR, dfR, nR, midR = deficits(AR)
    rows = []
    for k, c in enumerate(allids):
        r = meta.loc[c]
        g = geo[c]
        wk19, wkR = M19["all day"][k], MR["all day"][k]
        both = present19[k] and presentR[k]
        reliable = both and n19[k] >= MIN_WEEKS and nR[k] >= MIN_WEEKS and mid19[k] >= MIN_MIDWEEK and midR[k] >= MIN_MIDWEEK
        row = {"complex_id": c, "complex": r["station_complex"], "latitude": r["lat"], "longitude": r["lon"], "borough": r["borough"],
               "in_cbd": r["in_cbd"],
               "taxi_zone_id": g.get("taxi", (None,))[0] and int(g["taxi"][0]["locationid"]),
               "taxi_zone": g.get("taxi", (None,))[0] and g["taxi"][0]["zone"],
               "nta2020": g.get("nta", (None,))[0] and g["nta"][0]["nta2020"], "nta2020_name": g.get("nta", (None,))[0] and g["nta"][0]["ntaname"],
               "community_district": g.get("cd", (None,))[0] and int(g["cd"][0]["boro_cd"]),
               "geo_join": "/".join(f"{k}:{g[k][1]}" for k in ("taxi", "nta", "cd")) if g else "none",
               "in_2019": bool(present19[k]), "in_recent": bool(presentR[k]),
               "weekday_mean_entries_2019": wk19[:5].mean(), "weekday_mean_entries_recent": wkR[:5].mean(),
               "weekly_entries_2019": wk19.sum(), "weekly_entries_recent": wkR.sum(),
               "n_weeks_2019": int(n19[k]), "n_weeks_recent": int(nR[k]), "deficit_reliable": bool(reliable)}
        for pre, dm, df_ in (("2019", dm19, df19), ("recent", dmR, dfR)):
            row[f"mon_deficit_{pre}_pct"] = 100 * dm[k]
            row[f"fri_deficit_{pre}_pct"] = 100 * df_[k]
            row[f"mf_deficit_{pre}_pct"] = 100 * (dm[k] + df_[k]) / 2
        row["mon_deficit_change_pts"] = row["mon_deficit_recent_pct"] - row["mon_deficit_2019_pct"]
        row["fri_deficit_change_pts"] = row["fri_deficit_recent_pct"] - row["fri_deficit_2019_pct"]
        row["mf_deficit_change_pts"] = row["mf_deficit_recent_pct"] - row["mf_deficit_2019_pct"]
        if not reliable:
            for kk in [x for x in row if "deficit" in x and x not in ("deficit_reliable",) and not x.startswith("n_")]:
                row[kk] = np.nan
        row["ratio_all_week"] = wkR.sum() / wk19.sum() if both and wk19.sum() > 0 else np.nan
        for name, days in (("weekday_all_day", range(5)),):
            row["ratio_" + name] = (MR["all day"][k, :5].sum() / M19["all day"][k, :5].sum()) if both and M19["all day"][k, :5].sum() > 0 else np.nan
        mid19b, midRb = M19["midday 10-16"][k, :5].sum(), MR["midday 10-16"][k, :5].sum()
        row["ratio_weekday_midday"] = midRb / mid19b if both and mid19b > 0 else np.nan
        sat19, satR = M19["all day"][k, 5:].sum(), MR["all day"][k, 5:].sum()
        row["ratio_weekend"] = satR / sat19 if both and sat19 > 0 else np.nan
        row["ratio_sat"] = MR["all day"][k, 5] / M19["all day"][k, 5] if both and M19["all day"][k, 5] > 0 else np.nan
        row["ratio_sun"] = MR["all day"][k, 6] / M19["all day"][k, 6] if both and M19["all day"][k, 6] > 0 else np.nan
        for b in BANDS:
            e19, eR = M19[b][k, :5].sum(), MR[b][k, :5].sum()
            row["ratio_weekday_" + b.split()[0] + ("_" + b.split()[1] if b.startswith(("AM", "PM")) else "")] = eR / e19 if both and e19 > 0 else np.nan
        rows.append(row)
    W = pd.DataFrame(rows)
    num = W.select_dtypes("number").columns
    W[num] = W[num].round(4)
    W.to_csv(OUTD / "dose_map.csv", index=False)

    summ = summarise(W, L)
    (OUTD / "dose_map_summary.json").write_text(json.dumps(summ, indent=1, default=str))
    (OUTD / "dose_map_sources.json").write_text(json.dumps(
        {"ridership_queries": SOURCES, "boundaries": brecs,
         "periods": {k: {"start": str(v[0]), "end": str(v[1]), "weeks_retained": len(retained_weeks(*v))} for k, v in PERIODS.items()},
         "rules": {"min_weeks": MIN_WEEKS, "min_midweek_entries": MIN_MIDWEEK,
                   "boundary_fallback": "a point outside every polygon is assigned to the nearest polygon within 400 m (recorded in geo_join)",
                   "missing_complex": "a complex absent from one period has ratios left empty"}}, indent=1))
    figure(W, bounds["cd"])
    return summ


def summarise(W, L):
    R = W[W.deficit_reliable]
    s = {"n_complexes": int(len(W)), "n_in_both_periods": int((W.in_2019 & W.in_recent).sum()), "n_deficit_reliable": int(len(R)),
         "only_2019": W[W.in_2019 & ~W.in_recent].complex.tolist(), "only_recent": W[~W.in_2019 & W.in_recent].complex.tolist()}
    for c in ("mf_deficit_change_pts", "mon_deficit_change_pts", "fri_deficit_change_pts"):
        s[c] = {"median": R[c].median(), "q25": R[c].quantile(.25), "q75": R[c].quantile(.75), "min": R[c].min(), "max": R[c].max(),
                "n_gt_10": int((R[c] > 10).sum()), "n_gt_0": int((R[c] > 0).sum())}
    s["n_both_mon_and_fri_gt_10"] = int(((R.mon_deficit_change_pts > 10) & (R.fri_deficit_change_pts > 10)).sum())
    s["n_either_mon_or_fri_gt_10"] = int(((R.mon_deficit_change_pts > 10) | (R.fri_deficit_change_pts > 10)).sum())
    s["by_borough_mf_change_median"] = R.groupby("borough").mf_deficit_change_pts.median().to_dict()
    s["by_borough_n_mf_gt_10"] = R.assign(g=R.mf_deficit_change_pts > 10).groupby("borough").g.agg(["sum", "count"]).to_dict("index")
    B = W[W.in_2019 & W.in_recent]
    for c in ("ratio_all_week", "ratio_weekday_midday", "ratio_weekend", "ratio_weekday_all_day"):
        v = B[c].dropna()
        s[c] = {"median": v.median(), "q25": v.quantile(.25), "q75": v.quantile(.75), "min": v.min(), "max": v.max(),
                "n_gt_1": int((v > 1).sum()), "n": int(len(v))}
    # citywide totals
    tot = B[["weekly_entries_2019", "weekly_entries_recent"]].sum()
    s["citywide_weekly_ratio"] = tot.weekly_entries_recent / tot.weekly_entries_2019
    # area-level sums over complexes in both periods (NTAs and CDs)
    mid = L[(L.band == "midday 10-16") & L.weekday.isin(DOW[:5])].merge(W[["complex_id", "nta2020", "nta2020_name", "community_district", "borough", "in_2019", "in_recent"]], on="complex_id")
    mid = mid[mid.in_2019 & mid.in_recent]
    we = L[(L.band == "all day") & L.weekday.isin(["Sat", "Sun"])].merge(W[["complex_id", "nta2020", "nta2020_name", "community_district", "borough", "in_2019", "in_recent"]], on="complex_id")
    we = we[we.in_2019 & we.in_recent]
    for lab, d in (("weekday_midday", mid), ("weekend", we)):
        for key in ("community_district", "nta2020"):
            g = d.groupby([key] + (["nta2020_name"] if key == "nta2020" else [])).agg(r=("entries_recent", "sum"), o=("entries_2019", "sum"))
            g = g[g.o >= 2000 * (5 if lab == "weekday_midday" else 2)]  # areas with at least ~2,000 entries a day in 2019
            g["ratio"] = g.r / g.o
            s[f"{lab}_by_{key}"] = {"n_areas": int(len(g)), "n_gt_1": int((g.ratio > 1).sum()),
                                    "top": {str(k): round(float(v), 3) for k, v in g.ratio.sort_values(ascending=False).head(12).items()},
                                    "bottom": {str(k): round(float(v), 3) for k, v in g.ratio.sort_values().head(5).items()}}
    top = B[(B.weekday_mean_entries_recent > 2000)]
    s["midday_gt_1_stations_over_2000"] = top[top.ratio_weekday_midday > 1][["complex", "borough", "community_district", "ratio_weekday_midday"]].sort_values("ratio_weekday_midday", ascending=False).head(25).to_dict("records")
    s["weekend_gt_1_stations_over_2000"] = B[(B.weekly_entries_recent / 7 > 2000) & (B.ratio_weekend > 1)][["complex", "borough", "community_district", "ratio_weekend"]].sort_values("ratio_weekend", ascending=False).head(25).to_dict("records")
    s["cbd_vs_other"] = R.groupby(R.in_cbd.astype(str)).mf_deficit_change_pts.agg(["median", "count"]).to_dict("index")
    return s


# ------------------------------------------------------------------ figure
def figure(W, cd_bounds):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath
    lat0 = 40.72
    aspect = 1 / np.cos(np.radians(lat0))

    def outline(ax):
        for g, _ in cd_bounds:
            for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
                x, y = p.exterior.xy
                ax.fill(x, y, facecolor="#f1f2f4", edgecolor="#d3d6db", lw=0.3, zorder=0)
        ax.set_aspect(aspect)
        ax.set_xlim(-74.27, -73.69)
        ax.set_ylim(40.49, 40.92)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)

    D = W.dropna(subset=["longitude", "latitude"])
    size = lambda v: np.clip(v, 0, None) ** 0.5 / 14
    fig = plt.figure(figsize=(12, 7.4))
    ax1 = fig.add_axes([0.0, 0.14, 0.5, 0.80])
    ax2 = fig.add_axes([0.5, 0.14, 0.5, 0.80])
    outline(ax1); outline(ax2)
    nr = D[~D.deficit_reliable]
    ax1.scatter(nr.longitude, nr.latitude, s=size(nr.weekday_mean_entries_recent), color="#9aa0a8", alpha=.6, lw=0, zorder=2)
    r = D[D.deficit_reliable].sort_values("weekday_mean_entries_recent", ascending=False)
    norm = TwoSlopeNorm(vmin=-10, vcenter=0, vmax=25)
    sc = ax1.scatter(r.longitude, r.latitude, s=size(r.weekday_mean_entries_recent), c=r.mf_deficit_change_pts.clip(-10, 25), cmap="RdBu_r",
                     norm=norm, edgecolor="#30343a", linewidth=0.25, alpha=.9, zorder=3)
    ax1.set_title("Change in the Monday/Friday deficit since 2019", fontsize=11, loc="left", x=0.04)
    cax = fig.add_axes([0.08, 0.095, 0.34, 0.016])
    cb = fig.colorbar(sc, cax=cax, orientation="horizontal")
    cb.set_label("percentage points (red: Mondays and Fridays thinned more)", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    for n in (1000, 10000, 50000):
        ax1.scatter([], [], s=size(n), color="#c9ccd1", edgecolor="#30343a", lw=.3, label=f"{n:,}")
    ax1.legend(title="Mean weekday entries,\nrecent period", frameon=False, fontsize=8, title_fontsize=8, loc="upper left", labelspacing=1.4)
    m = D.dropna(subset=["ratio_weekday_midday"]).sort_values("weekday_mean_entries_recent", ascending=False)
    norm2 = TwoSlopeNorm(vmin=0.4, vcenter=1.0, vmax=1.6)
    sc2 = ax2.scatter(m.longitude, m.latitude, s=size(m.weekday_mean_entries_recent) * 0.8, c=m.ratio_weekday_midday.clip(0.4, 1.6), cmap="PuOr", norm=norm2,
                      edgecolor="#30343a", linewidth=0.25, alpha=.9, zorder=3)
    ax2.set_title("Weekday midday (10-16) entries, recent / 2019", fontsize=11, loc="left", x=0.04)
    cax2 = fig.add_axes([0.58, 0.095, 0.34, 0.016])
    cb2 = fig.colorbar(sc2, cax=cax2, orientation="horizontal")
    cb2.set_label("ratio (orange: below 2019; purple: above 2019)", fontsize=8)
    cb2.ax.tick_params(labelsize=8)
    ax3 = ax2.inset_axes([0.03, 0.66, 0.26, 0.26])
    ax3.hist(m.ratio_weekday_midday.clip(0.2, 1.6), bins=np.linspace(0.2, 1.6, 22), color="#8a8f98")
    ax3.axvline(1, color="#30343a", lw=.8)
    ax3.set_yticks([]); ax3.tick_params(labelsize=7); ax3.set_xlabel("ratio, all complexes", fontsize=7)
    ax3.spines[["top", "right", "left"]].set_visible(False); ax3.patch.set_alpha(0)
    fig.text(0.01, 0.015, "MTA Subway Hourly Ridership (data.ny.gov t69i-h2me for 2019, 5wq4-mkjj for Nov 2025 to Oct 2026); weeks with a federal holiday or 24 Dec to 1 Jan dropped.\n"
             "Entries are fare-paid subway entries, not pedestrians. Background: Community Districts (NYC Open Data 5crt-au7u). Dot size: mean weekday entries, recent period.",
             fontsize=7, color="#555")
    fig.savefig(FIG, dpi=200)
    plt.close(fig)
    from PIL import Image, ImageCms
    im = Image.open(FIG).convert("RGB")
    im.save(FIG, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes(), dpi=(200, 200))


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, default=str))
