"""heat-trees-canopy-within-nta: vegetation share near NYC hyperlocal temperature sensors (NAIP 2022,
near infrared) and afternoon air temperature, compared within neighbourhood (NTA), flight date and day.

Registered plan: claims/registered/heat-trees-canopy-within-nta.json.
Data: Hyperlocal Temperature Monitoring (qdq3-9eqn); USDA NAIP 2022 New York flight through the Microsoft
Planetary Computer; NOAA GHCN-Daily Central Park (hot-day sensitivity only).

Run from the repo root:
  python -m analyses.heat.canopy_naip test       exposure code on two Staten Island points (no sensors there)
  python -m analyses.heat.canopy_naip exposure   NAIP vegetation measures at every sensor
  python -m analyses.heat.canopy_naip model      temperature queries, models, results json
  python -m analyses.heat.canopy_naip figure

Imagery (one small NDVI array per sensor) is kept outside Dropbox, in $NAIP_ROOT or ~/opt/nyc-concordance.
Outputs: data/derived/heat/canopy_naip_sensors.csv, canopy_naip_results.json, figures/heat/heat_canopy_naip.png
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

from analyses.heat import naip
from analyses.heat.common import DER, FIG, tag_srgb

YEAR = 2022
PRIMARY_DATE = "2022-07-19"
HALF = 310.0            # half-width of the box read around each sensor, metres
RES = 0.6
THRESH = 0.2
RING = (200.0, 300.0)   # placebo annulus, metres
NPZ = naip.ROOT / "naip_sensors"
LAT0 = np.deg2rad(40.7)


# ---------------------------------------------------------------- exposure

def ny_items(box):
    """2022 items of the New York State flight that touch the box, 19 July tiles first. New Jersey tiles of
    10 July 2022 overlap western Manhattan and the Bronx and are left out, so that only two dates occur."""
    its = [i for i in naip._items(box) if naip._year(i) == YEAR and i.properties.get("naip:state", "").lower() == "ny"]
    return sorted(its, key=lambda i: (i.datetime.date().isoformat() != PRIMARY_DATE, i.id))


def measure(lat: float, lon: float, items, name: str | None = None) -> dict:
    """Vegetation measures around one point from the items whose footprint touches its box."""
    dlat = HALF / 111320.0
    dlon = HALF / (111320.0 * np.cos(np.deg2rad(lat)))
    box = (lat - dlat, lon - dlon, lat + dlat, lon + dlon)
    crs, transform, width, height = naip._grid(box, RES)
    arr = np.zeros((4, height, width), np.uint8)
    date = np.zeros((height, width), np.uint8)       # index+1 of the acquisition date that filled the pixel
    dates, used = [], []
    for it in items:
        w, s, e, n = it.bbox
        if e < box[1] or w > box[3] or n < box[0] or s > box[2]:
            continue
        if arr.max(axis=0).min() > 0:
            break
        new = naip._read_into(it.assets["image"].href, arr, transform, crs)
        if new.any():
            d = it.datetime.date().isoformat()
            if d not in dates:
                dates.append(d)
            date[new] = dates.index(d) + 1
            used.append(it.id)
    v = naip.ndvi(arr)
    from pyproj import Transformer
    x, y = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform(lon, lat)
    col, row = ~transform * (x, y)
    rr, cc = np.mgrid[0:height, 0:width]
    dist = np.hypot((cc + 0.5 - col) * RES, (rr + 0.5 - row) * RES)
    out = {"items": ";".join(used)}
    ci, ri = int(np.clip(col, 0, width - 1)), int(np.clip(row, 0, height - 1))
    out["flight_date"] = dates[date[ri, ci] - 1] if date[ri, ci] else None
    for label, m in (("50", dist <= 50), ("100", dist <= 100), ("ring", (dist > RING[0]) & (dist <= RING[1]))):
        ok = m & ~np.isnan(v)
        out[f"valid{label}"] = float(ok.sum() / m.sum())
        out[f"veg{label}"] = float((v[ok] > THRESH).mean()) if ok.any() else None
        out[f"ndvi{label}"] = float(v[ok].mean()) if ok.any() else None
    d100 = np.unique(date[(dist <= 100) & (date > 0)])
    out["dates100"] = ";".join(dates[k - 1] for k in d100)
    p = np.percentile(v[~np.isnan(v)], [10, 50, 90]) if (~np.isnan(v)).any() else [np.nan] * 3
    out["box_ndvi_p10"], out["box_ndvi_p50"], out["box_ndvi_p90"] = (float(q) for q in p)
    if name:
        NPZ.mkdir(parents=True, exist_ok=True)
        q = np.where(np.isnan(v), -128, np.round(v * 100)).astype(np.int8)
        np.savez_compressed(NPZ / f"{name}.npz", ndvi100=q, date=date, dates=np.array(dates), col=col, row=row, res=RES)
    return out


def sensors() -> tuple[pd.DataFrame, dict]:
    from concord import socrata
    meta, src = socrata.query("qdq3-9eqn", select="sensor_id, latitude, longitude, ntacode, install_type, count(*) as n",
                              group="sensor_id, latitude, longitude, ntacode, install_type")
    meta = pd.DataFrame(meta)
    meta["n"] = meta["n"].astype(int)
    for c in ("latitude", "longitude"):
        meta[c] = meta[c].astype(float)
    # a sensor listed at two positions keeps the position with the most readings, as in hyperlocal.py
    meta = meta.sort_values("n").drop_duplicates("sensor_id", keep="last").set_index("sensor_id").sort_index()
    return meta, src


def exposure():
    meta, _ = sensors()
    box = (meta.latitude.min() - 0.01, meta.longitude.min() - 0.01, meta.latitude.max() + 0.01, meta.longitude.max() + 0.01)
    items = ny_items(box)

    def one(t):
        sid, r = t
        for k in range(4):
            try:
                return sid, measure(r.latitude, r.longitude, items, name=sid)
            except Exception as e:  # noqa: BLE001  network reads fail now and then
                err = e
                time.sleep(3 * (k + 1))
        return sid, {"error": str(err)}

    with ThreadPoolExecutor(8) as ex:
        res = dict(ex.map(one, list(meta.iterrows())))
    out = meta.join(pd.DataFrame.from_dict(res, orient="index"))
    out.to_csv(DER / "canopy_naip_sensors.csv")
    src = {"kind": "naip", "collection": naip.COLLECTION, "stac_url": naip.STAC_URL, "year": YEAR,
           "states": ["ny"], "items": sorted({i for s in out["items"].dropna() for i in s.split(";") if i}),
           "acquisition_dates": sorted({d for s in out["dates100"].dropna() for d in s.split(";") if d}),
           "gsd": [0.6], "resolution_m": RES, "threshold": THRESH, "license": "public domain (USDA)",
           "credit": naip.credit(YEAR), "data_access": "open", "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "file": "data/derived/heat/canopy_naip_sensors.csv"}
    (DER / "canopy_naip_source.json").write_text(json.dumps(src, indent=1))
    print(out[["veg50", "veg100", "vegring", "ndvi50", "valid50"]].describe().round(3))
    print(out["flight_date"].value_counts(dropna=False))


# ---------------------------------------------------------------- model

def temps(hours: tuple[int, int], min_hours: int):
    from concord import socrata
    rows, src = socrata.query_all("qdq3-9eqn", select="sensor_id, day, avg(airtemp) as t, count(*) as nh",
                                  where=f"hour >= {hours[0]} AND hour <= {hours[1]}", group="sensor_id, day",
                                  order="sensor_id, day")
    d = pd.DataFrame(rows)
    d["t_c"] = (d["t"].astype(float) - 32) * 5 / 9
    d["nh"] = d["nh"].astype(int)
    return d[d["nh"] >= min_hours], src


def within(d: pd.DataFrame, xs: list[str], y: str = "t_c") -> dict:
    """OLS of y on xs after removing cell means (cell = NTA x flight date x day), SE clustered by sensor."""
    import statsmodels.api as sm
    d = d.dropna(subset=xs + [y])
    d = d[d.groupby("cell")["sensor_id"].transform("nunique") >= 2]
    if d["sensor_id"].nunique() < 10:
        return {"n": int(len(d)), "sensors": int(d["sensor_id"].nunique()), "note": "too few sensors"}
    g = d.groupby("cell")
    X = pd.DataFrame({c: d[c] - g[c].transform("mean") for c in xs})
    X = X.loc[:, X.abs().max() > 1e-12]
    yy = d[y] - g[y].transform("mean")
    res = sm.OLS(yy, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["sensor_id"])[0]})
    out = {"n": int(res.nobs), "sensors": int(d["sensor_id"].nunique()), "cells": int(d["cell"].nunique()), "coef": {}}
    for c in X.columns:
        b, se = float(res.params[c]), float(res.bse[c])
        out["coef"][c] = {"estimate": b, "lo": b - 1.96 * se, "hi": b + 1.96 * se, "se": se, "p": float(res.pvalues[c])}
    return out


def model():
    from concord import noaa
    s = pd.read_csv(DER / "canopy_naip_sensors.csv", index_col=0)
    old = pd.read_csv(DER / "hyperlocal_sensors.csv", index_col=0)      # street trees within 50 m, earlier claim
    s = s.join(old[["trees50"]])
    s["lp"] = (s["install_type"] == "Light Pole").astype(float)
    for r in ("50", "100", "ring"):
        s[f"v{r}"] = s[f"veg{r}"] * 10          # per 10 percentage points
        s[f"n{r}"] = s[f"ndvi{r}"] * 10         # per 0.1 NDVI
    s["tr50"] = s["trees50"] / 10
    s["clean"] = (s["valid50"] >= 0.95) & (s["valid100"] >= 0.95) & ~s["dates100"].fillna("").str.contains(";")
    valid = s[(s["valid50"] >= 0.95) & s["flight_date"].notna()]
    aft, src_a = temps((12, 18), 5)
    ngt, src_n = temps((0, 5), 5)
    cols = ["ntacode", "flight_date", "lp", "v50", "v100", "vring", "n50", "n100", "tr50", "clean", "install_type"]

    def prep(t):
        d = t.join(valid[cols], on="sensor_id").dropna(subset=["ntacode", "v50"])
        d["date"] = d["day"].str[:10]
        d["cell"] = d["ntacode"] + "_" + d["flight_date"] + "_" + d["date"]
        return d

    a, n = prep(aft), prep(ngt)
    wx, src_w = noaa.daily("central_park")
    hot = set(wx.index[wx["TMAX"] >= 30].strftime("%Y-%m-%d"))
    out = {"sensors_with_exposure": int(len(valid)), "sensors_all": int(len(s)),
           "exposure": {"veg50_mean": float(valid.veg50.mean()), "veg50_sd": float(valid.veg50.std()),
                        "veg50_within_nta_sd": float((valid.veg50 - valid.groupby(["ntacode", "flight_date"]).veg50.transform("mean")).std()),
                        "veg50_min": float(valid.veg50.min()), "veg50_max": float(valid.veg50.max()),
                        "share_sensors_veg50_ge_40pct": float((valid.veg50 >= 0.4).mean()),
                        "veg100_mean": float(valid.veg100.mean()), "vegring_mean": float(valid.vegring.mean()),
                        "corr_veg50_trees50": float(valid[["veg50", "trees50"]].corr().iloc[0, 1]),
                        "corr_veg50_vegring": float(valid[["veg50", "vegring"]].corr().iloc[0, 1]),
                        "veg50_mean_street_tree": float(valid.loc[valid.lp == 0, "veg50"].mean()),
                        "veg50_mean_light_pole": float(valid.loc[valid.lp == 1, "veg50"].mean()),
                        "flight_dates": valid["flight_date"].value_counts().to_dict(),
                        "mixed_date_or_missing": int((~valid["clean"]).sum())}}
    m = {}
    m["primary_veg50"] = within(a, ["v50", "lp"])
    m["s1_veg100"] = within(a, ["v100", "lp"])
    m["s2_ndvi50"] = within(a, ["n50", "lp"])
    m["s2_ndvi100"] = within(a, ["n100", "lp"])
    m["s3_july19_only"] = within(a[a.flight_date == PRIMARY_DATE], ["v50", "lp"])
    m["s3_sept15_only"] = within(a[a.flight_date != PRIMARY_DATE], ["v50", "lp"])
    m["s4_clean_sensors"] = within(a[a.clean], ["v50", "lp"])
    m["s5_street_tree_mounts"] = within(a[a.lp == 0], ["v50"])
    m["s5_light_pole_mounts"] = within(a[a.lp == 1], ["v50"])
    m["s6_hot_days_tmax30"] = within(a[a.date.isin(hot)], ["v50", "lp"])
    m["s7_with_tree_count"] = within(a, ["v50", "tr50", "lp"])
    m["secondary_night_veg50"] = within(n, ["v50", "lp"])
    m["secondary_night_veg100"] = within(n, ["v100", "lp"])
    m["placebo_ring_alone"] = within(a, ["vring", "lp"])
    m["placebo_ring_joint"] = within(a, ["v50", "vring", "lp"])
    # descriptive: bins of the 50 m share, reference below 10%
    b = a.copy()
    edges = [(0.1, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 1.01)]
    for lo, hi in edges:
        b[f"b{int(lo * 100)}"] = ((b.v50 / 10 >= lo) & (b.v50 / 10 < hi)).astype(float)
    m["descriptive_bins"] = within(b, [f"b{int(lo * 100)}" for lo, _ in edges] + ["lp"])
    sv = valid.assign(bin=pd.cut(valid.veg50, [-0.01, 0.1, 0.2, 0.3, 0.4, 1.01], labels=["<10", "10-20", "20-30", "30-40", ">=40"]))
    out["sensors_per_bin"] = sv["bin"].value_counts().sort_index().to_dict()
    out["models"] = m
    out["scales"] = {"v50, v100, vring": "C per 10 percentage points of vegetation share (NDVI > 0.2)",
                     "n50, n100": "C per 0.1 of mean NDVI", "tr50": "C per 10 live street trees within 50 m",
                     "lp": "light pole against street-tree mount, C"}
    out["sources"] = [src_a, src_n, json.loads((DER / "canopy_naip_source.json").read_text()), src_w]
    (DER / "canopy_naip_results.json").write_text(json.dumps(out, indent=1, default=str))
    # sensor-level residuals for the figure
    a2 = a[a.groupby("cell")["sensor_id"].transform("nunique") >= 2].copy()
    for c in ("t_c", "v50", "lp"):
        a2[c + "_w"] = a2[c] - a2.groupby("cell")[c].transform("mean")
    a2["t_adj"] = a2["t_c_w"] - m["primary_veg50"]["coef"]["lp"]["estimate"] * a2["lp_w"]
    a2.groupby("sensor_id").agg(v50_w=("v50_w", "mean"), t_adj=("t_adj", "mean"), lp=("lp", "first"),
                                flight_date=("flight_date", "first"), days=("t_adj", "size")).to_csv(DER / "canopy_naip_sensor_resid.csv")
    print(json.dumps({k: (v.get("coef", {}) | {"n": v.get("n"), "sensors": v.get("sensors")}) for k, v in m.items()}, indent=1, default=str))
    print(json.dumps(out["exposure"], indent=1))


# ---------------------------------------------------------------- figure

def figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    r = json.loads((DER / "canopy_naip_results.json").read_text())
    m = r["models"]
    sr = pd.read_csv(DER / "canopy_naip_sensor_resid.csv")
    sr = sr[sr.days >= 20]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5.2), gridspec_kw={"width_ratios": [1, 1.15]})
    for lp, col, lab in ((0, "#2a7f62", "street-tree mount"), (1, "#b5651d", "light-pole mount")):
        q = sr[sr.lp == lp]
        ax1.scatter(q.v50_w * 10, q.t_adj, s=14, color=col, alpha=0.6, lw=0, label=lab)
    p = m["primary_veg50"]["coef"]["v50"]
    xx = np.array([sr.v50_w.min(), sr.v50_w.max()])
    ax1.plot(xx * 10, p["estimate"] * xx, color="black", lw=1.5)
    ax1.axhline(0, color="grey", lw=0.6)
    ax1.set_xlabel("Vegetation share within 50 m, difference from the\nneighbourhood-day mean (percentage points)")
    ax1.set_ylabel("Afternoon air temperature, difference from the\nneighbourhood-day mean, mount adjusted (C)")
    ax1.set_title(f"{len(sr)} sensors, mean over their days", fontsize=10)
    ax1.legend(frameon=False, fontsize=8)
    rows = [("Primary: share within 50 m", "primary_veg50", "v50"), ("Share within 100 m", "s1_veg100", "v100"),
            ("Mean NDVI within 50 m (per 0.1)", "s2_ndvi50", "n50"), ("19 July tiles only", "s3_july19_only", "v50"),
            ("15 September tiles only", "s3_sept15_only", "v50"), ("Single date, full imagery", "s4_clean_sensors", "v50"),
            ("Street-tree mounts", "s5_street_tree_mounts", "v50"), ("Light-pole mounts", "s5_light_pole_mounts", "v50"),
            ("Days with Central Park max >= 30 C", "s6_hot_days_tmax30", "v50"),
            ("Adjusted for street-tree count", "s7_with_tree_count", "v50"),
            ("Night (00-05 h), 50 m", "secondary_night_veg50", "v50"),
            ("Placebo: ring 200-300 m, alone", "placebo_ring_alone", "vring"),
            ("Ring, joint with 50 m share", "placebo_ring_joint", "vring"),
            ("50 m share, joint with ring", "placebo_ring_joint", "v50")]
    rows = [(lab, m[k]["coef"][c]) for lab, k, c in rows if c in m[k].get("coef", {})]
    for i, (lab, c) in enumerate(rows):
        y = len(rows) - i
        col = "black" if i == 0 else ("#7a7a7a" if "ring" in lab.lower() else "#2a5d8f")
        ax2.plot([c["lo"], c["hi"]], [y, y], color=col, lw=1.6)
        ax2.plot(c["estimate"], y, "o", color=col, ms=5)
    ax2.axvline(0, color="grey", lw=0.6)
    ax2.axvspan(-0.25, -0.02, color="#2a7f62", alpha=0.10, lw=0)
    ax2.set_yticks(range(len(rows), 0, -1))
    ax2.set_yticklabels([lab for lab, _ in rows], fontsize=8)
    ax2.set_xlabel("C per 10 percentage points of vegetation share (95% interval);\nshaded: registered range -0.02 to -0.25")
    ax2.set_title("Registered estimates", fontsize=10)
    fig.suptitle("Vegetation near temperature sensors and afternoon air temperature, within neighbourhood and day", fontsize=11)
    fig.text(0.01, 0.005, "Sources: Hyperlocal Temperature Monitoring qdq3-9eqn (summers 2018-2019), NYC Open Data. "
             + r["sources"][2]["credit"] + " Vegetation: NDVI > 0.2.", fontsize=7, color="#444")
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    f = FIG / "heat_canopy_naip.png"
    fig.savefig(f, dpi=160)
    tag_srgb(f)
    print(f.name)


def test():
    pts = {"SI Greenbelt woods": (40.5890, -74.1390), "SI St George streets": (40.6425, -74.0770)}
    box = (40.58, -74.15, 40.65, -74.07)
    items = ny_items(box)
    print([(i.id, i.datetime.date().isoformat()) for i in items])
    for k, (lat, lon) in pts.items():
        print(k, json.dumps(measure(lat, lon, items), indent=None))


if __name__ == "__main__":
    {"test": test, "exposure": exposure, "model": model, "figure": figure}[sys.argv[1]]()
