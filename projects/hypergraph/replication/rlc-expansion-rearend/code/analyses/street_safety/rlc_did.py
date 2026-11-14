"""Red-light camera expansion of 2026: stacked before-after test with matched control intersections.

Registered as rlc-expansion-rearend and rlc-expansion-injuries (claims/registered/). The procedure
below is fixed before any crash data are read; see the registrations for the predictions.

Inputs
  data/derived/street_safety/rlc_sites_geo.json   camera intersections with first-ticket date and
                                                    coordinates (rlc_sites.py, geocode_sites.py)
  data/derived/street_safety/lpi_gazetteer.json     signalized intersections with LPIs (control pool)
  NYC Open Data h9gi-nx95 (Motor Vehicle Collisions - Crashes), queried here by SoQL.

Design
  Treated: intersections whose first red-light ticket (violation code 7) is dated 2026-01-01 to
    2026-08-31 and that had no ticket before 2026 (the 2026 expansion). Activation month a = the month
    of the first ticket. Post window: calendar months a+1 .. min(a+9, 2026-10); the activation month
    is dropped. October 2026 may be incompletely reported; proportional under-reporting
    cancels in the ratio of ratios because treated and control windows share calendar months. Pre window: the same calendar months in 2024 and in 2025 (two years, averaged).
    Sites with no full post month are dropped.
  Control pool: LPI intersections (xc4v-ntf4) with LPI installed before 2024-01-01, more than 300 m
    from every camera site that ever had a ticket (2023-2026), in the same borough.
  Matching: for each treated site, the K=3 pool intersections in the same borough with the nearest
    count of all crashes within R in the pre windows of that site (2024 and 2025 calendar months),
    without replacement within a borough where possible. Controls inherit the treated site's windows.
  Crash assignment: crashes with coordinates within R=50 m of the intersection point. A crash near
    two sites counts for each (rare at 300 m separation; reported).
  Outcomes (counts in a window):
    rear_end   rear-end proxy: crashes with any contributing factor 'Following Too Closely', or
               with a vehicle (bm4k-52h4, Motor Vehicle Collisions - Vehicles) whose point of
               impact is 'Center Back End' and whose pre-crash action is 'Going Straight Ahead',
               'Stopped in Traffic', 'Slowing or Stopping' or 'Starting in Traffic' (a moving or
               queued vehicle struck from behind; parked vehicles are excluded)
    injured    persons injured + killed
    ped        pedestrians injured + killed
    tcd        crashes with any contributing factor 'Traffic Control Disregarded' (red-running proxy)
    all        all crashes
  Estimator: ratio of ratios RR = (T_post / T_pre) / (C_post / C_pre), with T_pre and C_pre the
    mean of the 2024 and 2025 windows, summed over sites. Controls are weighted 1/K.
  Interval: cluster bootstrap over matched sets (treated site with its K controls), B=2000 draws,
    seed 20261113, percentile 95% interval. Rule-8 discrimination: z_null and z_chain from the
    bootstrap SE of log RR.
  Check of rule 9: rerun with B=20000 and seeds 1..10 (--robust).

Usage
  python analyses/street_safety/rlc_did.py            # run on live data
  python analyses/street_safety/rlc_did.py --synthetic   # test the code on simulated crashes (no city data)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DER = ROOT / "data/derived/street_safety"

R_M = 50.0
SEP_M = 300.0
K = 3
B = 2000
SEED = 20261113
LAST_MONTH = (2026, 10)
MAX_POST = 9
OUTCOMES = ["rear_end", "injured", "ped", "tcd", "all"]
PRIMARY = {"rlc-expansion-rearend": ("rear_end", 1.10, 1.60), "rlc-expansion-injuries": ("injured", 0.70, 0.95)}


def xy(lat, lon):
    """Local equirectangular projection in metres (adequate at city scale)."""
    lat0 = 40.70
    return (np.asarray(lon) + 74.0) * 111320.0 * math.cos(math.radians(lat0)), (np.asarray(lat) - lat0) * 110540.0


def months_after(y, m, k):
    m2 = m + k
    return y + (m2 - 1) // 12, (m2 - 1) % 12 + 1


def windows(first_date: str):
    y, m = int(first_date[:4]), int(first_date[5:7])
    post = []
    for k in range(1, MAX_POST + 1):
        ym = months_after(y, m, k)
        if ym > LAST_MONTH:
            break
        post.append(ym)
    return post


def load_sites():
    d = json.loads((DER / "rlc_sites_geo.json").read_text())
    raw = sorted([s for s in d["sites"] if s.get("lat") is not None], key=lambda s: s["first"])
    # Merge sites within 60 m (approaches of one intersection under different names); the merged
    # intersection takes the earliest first-ticket date, so an intersection with an older camera
    # on another approach is not counted as new.
    sites = []
    for s in raw:
        sx, sy = xy(s["lat"], s["lon"])
        for m in sites:
            mx, my = xy(m["lat"], m["lon"])
            if (sx - mx) ** 2 + (sy - my) ** 2 <= 60.0 ** 2:
                m.setdefault("merged", []).append(f"{s['a']} @ {s['b']}")
                break
        else:
            sites.append(dict(s))
    allsites = sites
    treated = []
    for s in sites:
        if "2026-01" <= s["first"][:7] <= "2026-08":
            post = windows(s["first"])
            if post:
                treated.append({**s, "post": post})
    return treated, [s for s in allsites if s.get("lat") is not None], d


def control_pool(all_cam):
    g = json.loads((DER / "lpi_gazetteer.json").read_text())["rows"]
    g = [r for r in g if r.get("lpi_installed") and r["lpi_installed"] < "2024-01-01" and r.get("boro")]
    cx, cy = xy([s["lat"] for s in all_cam], [s["lon"] for s in all_cam])
    gx, gy = xy([r["lat"] for r in g], [r["lon"] for r in g])
    keep = []
    for i, r in enumerate(g):
        d2 = (cx - gx[i]) ** 2 + (cy - gy[i]) ** 2
        if d2.min() > SEP_M ** 2:
            keep.append(r)
    # drop duplicate points (same intersection listed twice)
    seen, out = set(), []
    for r in keep:
        k = (round(r["lat"], 4), round(r["lon"], 4))
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def fetch_crashes():
    from concord import socrata as s
    sel = ("collision_id, crash_date, latitude, longitude, number_of_persons_injured, number_of_persons_killed, "
           "number_of_pedestrians_injured, number_of_pedestrians_killed, contributing_factor_vehicle_1, "
           "contributing_factor_vehicle_2, contributing_factor_vehicle_3, contributing_factor_vehicle_4, "
           "contributing_factor_vehicle_5")
    where = ("crash_date >= '2023-01-01T00:00:00' and crash_date < '2026-11-01T00:00:00' "
             "and latitude > 40.4 and longitude < -73.6")
    rows, src = s.query_all("h9gi-nx95", select=sel, where=where, order="collision_id")
    vwhere = ("crash_date >= '2023-01-01T00:00:00' and crash_date < '2026-11-01T00:00:00' "
              "and point_of_impact = 'Center Back End' and pre_crash in ('Going Straight Ahead', "
              "'Stopped in Traffic', 'Slowing or Stopping', 'Starting in Traffic')")
    vrows, vsrc = s.query_all("bm4k-52h4", select="collision_id", where=vwhere, order="collision_id")
    struck = {r["collision_id"] for r in vrows}
    for r in rows:
        r["_struck_rear"] = r["collision_id"] in struck
    return rows, [src, vsrc]


def crash_arrays(rows):
    def f(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0.0
    lat = np.array([f(r.get("latitude")) for r in rows])
    lon = np.array([f(r.get("longitude")) for r in rows])
    ym = np.array([int(r["crash_date"][:4]) * 100 + int(r["crash_date"][5:7]) for r in rows])
    cf = [{(r.get(f"contributing_factor_vehicle_{i}") or "").strip().lower() for i in range(1, 6)} for r in rows]
    out = {
        "rear_end": np.array([1.0 if ("following too closely" in c or r.get("_struck_rear")) else 0.0
                              for c, r in zip(cf, rows)]),
        "tcd": np.array([1.0 if "traffic control disregarded" in c else 0.0 for c in cf]),
        "injured": np.array([f(r.get("number_of_persons_injured")) + f(r.get("number_of_persons_killed")) for r in rows]),
        "ped": np.array([f(r.get("number_of_pedestrians_injured")) + f(r.get("number_of_pedestrians_killed")) for r in rows]),
        "all": np.ones(len(rows)),
    }
    x, y = xy(lat, lon)
    return x, y, ym, out


def counts_near(px, py, cx, cy, cym, vals, yms):
    """Sum each outcome over crashes within R of (px,py) in the set of yyyymm values `yms`."""
    d2 = (cx - px) ** 2 + (cy - py) ** 2
    m = (d2 <= R_M ** 2) & np.isin(cym, list(yms))
    return {k: float(v[m].sum()) for k, v in vals.items()}


def build(treated, pool, cx, cy, cym, vals):
    from scipy.spatial import cKDTree
    tree = cKDTree(np.c_[cx, cy])
    pool_xy = {}
    for r in pool:
        px, py = xy(r["lat"], r["lon"])
        pool_xy[id(r)] = (float(px), float(py))

    def near_idx(px, py):
        return tree.query_ball_point([px, py], R_M)

    pool_near = {id(r): np.array(near_idx(*pool_xy[id(r)]), dtype=int) for r in pool}
    sets = []
    used = defaultdict(set)
    for t in sorted(treated, key=lambda s: s["first"]):
        tx, ty = xy(t["lat"], t["lon"])
        idx = np.array(near_idx(float(tx), float(ty)), dtype=int)
        post = {y * 100 + m for y, m in t["post"]}
        pre24 = {(y - 2) * 100 + m for y, m in t["post"]}
        pre25 = {(y - 1) * 100 + m for y, m in t["post"]}

        def summ(ix):
            cym_i = cym[ix]
            res = {}
            for nm, ms in (("post", post), ("pre24", pre24), ("pre25", pre25)):
                mm = np.isin(cym_i, list(ms))
                res[nm] = {k: float(v[ix][mm].sum()) for k, v in vals.items()}
            return res

        ts = summ(idx)
        tpre_all = ts["pre24"]["all"] + ts["pre25"]["all"]
        cands = [r for r in pool if r["boro"] == t["boro"] and id(r) not in used[t["boro"]]]
        if len(cands) < K:
            cands = [r for r in pool if r["boro"] == t["boro"]]
        sc = []
        for r in cands:
            ix = pool_near[id(r)]
            cym_i = cym[ix]
            n = float(np.isin(cym_i, list(pre24 | pre25)).sum())
            sc.append((abs(n - tpre_all), r["lat"], id(r), r))
        sc.sort(key=lambda z: (z[0], z[1]))
        ctr = [z[3] for z in sc[:K]]
        for r in ctr:
            used[t["boro"]].add(id(r))
        cs = [summ(pool_near[id(r)]) for r in ctr]
        sets.append({"site": f"{t['a']} @ {t['b']} ({t['boro']})", "first": t["first"], "n_post_months": len(post),
                     "treated": ts, "controls": cs,
                     "control_names": [f"{r['a']} @ {r['b']}" for r in ctr]})
    return sets


def rr_from(sets, outcome, w=None):
    w = np.ones(len(sets)) if w is None else w
    Tpo = Tpr = Cpo = Cpr = 0.0
    for wi, s in zip(w, sets):
        t = s["treated"]
        Tpo += wi * t["post"][outcome]
        Tpr += wi * (t["pre24"][outcome] + t["pre25"][outcome]) / 2
        for c in s["controls"]:
            Cpo += wi * c["post"][outcome] / K
            Cpr += wi * (c["pre24"][outcome] + c["pre25"][outcome]) / 2 / K
    if min(Tpr, Cpo, Cpr) <= 0:
        return float("nan"), (Tpo, Tpr, Cpo, Cpr)
    return (Tpo / Tpr) / (Cpo / Cpr), (Tpo, Tpr, Cpo, Cpr)


def boot(sets, outcome, b=B, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(sets)
    est = []
    for _ in range(b):
        w = np.bincount(rng.integers(0, n, n), minlength=n).astype(float)
        r, _ = rr_from(sets, outcome, w)
        if np.isfinite(r) and r > 0:
            est.append(r)
    est = np.array(est)
    return float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5)), float(np.log(est).std())


def discrimination(rr, se, lo_band, hi_band):
    pred = math.log(math.sqrt(lo_band * hi_band))     # centre of the registered band (geometric)
    z_null = math.log(rr) / se
    z_chain = (math.log(rr) - pred) / se
    return {"z_null": round(z_null, 2), "z_pred": round(z_chain, 2), "D": round(z_null ** 2 - z_chain ** 2, 2),
            "expected_D_at_prediction": round((pred / se) ** 2, 2)}


def analyse(sets, robust=False):
    res = {}
    for o in OUTCOMES:
        rr, parts = rr_from(sets, o)
        lo, hi, se = boot(sets, o)
        res[o] = {"rr": round(rr, 4), "lo": round(lo, 4), "hi": round(hi, 4), "se_log": round(se, 4),
                  "T_post": parts[0], "T_pre_mean": parts[1], "C_post_per_set": parts[2], "C_pre_mean_per_set": parts[3]}
        for cid, (oo, a, b_) in PRIMARY.items():
            if oo == o:
                res[o]["rule8"] = discrimination(rr, se, a, b_)
        if robust:
            alt = []
            for sd in range(1, 11):
                l2, h2, _ = boot(sets, o, b=20000, seed=sd)
                alt.append((round(l2, 4), round(h2, 4)))
            res[o]["robust_bounds_B20000_seeds1to10"] = alt
    return res


def placebo(treated, pool, cx, cy, cym, vals):
    """Fake activation one year earlier: post = 2025 months, pre = 2023 and 2024 months. Needs 2023 data,
    which are loaded."""
    fake = []
    for t in treated:
        y = int(t["first"][:4]) - 1
        fake.append({**t, "first": f"{y}{t['first'][4:]}", "post": [(yy - 1, mm) for yy, mm in t["post"]]})
    return build(fake, pool, cx, cy, cym, vals)


def sip_points():
    from concord import socrata as s
    rows, _ = s.query("shr7-eqdc", select="pjct_name, end_date, lat, long",
                      where="end_date >= '2024-01-01T00:00:00' and end_date < '2026-11-01T00:00:00'", limit=50000)
    pts = []
    for r in rows:
        try:
            pts.append(tuple(float(v) for v in xy(float(r["lat"]), float(r["long"]))))
        except (KeyError, TypeError, ValueError):
            pass
    return pts


def synthetic(treated, pool, effect=1.3):
    """Simulated crashes for testing the code: Poisson counts around each site, with a known effect."""
    rng = np.random.default_rng(1)
    rows_lat, rows_lon, rows_ym, flags = [], [], [], []
    months = [(y, m) for y in (2024, 2025, 2026) for m in range(1, 13) if (y, m) <= LAST_MONTH]
    tpost = {}
    for t in treated:
        for ym in t["post"]:
            tpost.setdefault((t["lat"], t["lon"]), set()).add(ym)
    for s in [*treated, *pool[:1500]]:
        base = rng.gamma(2.0, 0.4)
        for (y, m) in months:
            mult = effect if ((y, m) in tpost.get((s["lat"], s["lon"]), set())) else 1.0
            n = rng.poisson(base * mult)
            for _ in range(n):
                rows_lat.append(s["lat"] + rng.normal(0, 0.0001))
                rows_lon.append(s["lon"] + rng.normal(0, 0.0001))
                rows_ym.append(y * 100 + m)
                flags.append(1.0)
    x, y = xy(np.array(rows_lat), np.array(rows_lon))
    f = np.array(flags)
    vals = {o: f.copy() for o in OUTCOMES}
    return x, y, np.array(rows_ym), vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--robust", action="store_true")
    a = ap.parse_args()
    treated, all_cam, sd = load_sites()
    pool = control_pool(all_cam)
    print(f"treated sites {len(treated)}; control pool {len(pool)}")
    if a.synthetic:
        cx, cy, cym, vals = synthetic(treated, pool)
        sets = build(treated, pool, cx, cy, cym, vals)
        res = analyse(sets)
        print(json.dumps(res["all"], indent=1))
        return
    rows, src = fetch_crashes()
    cx, cy, cym, vals = crash_arrays(rows)
    ok = (cx != 0) & np.isfinite(cx)
    sets = build(treated, pool, cx, cy, cym, vals)
    res = analyse(sets, robust=a.robust)
    # Secondary checks fixed with the design:
    # (1) placebo: the same sites and windows moved one year earlier (post 2025, pre 2023 and 2024);
    pl = analyse(placebo(treated, pool, cx, cy, cym, vals))
    # (2) treated sites with a Vision Zero street improvement project (shr7-eqdc intersections, end date
    #     2024-01 to 2026-10) within 100 m dropped, with their matched controls.
    sip = sip_points()
    keep = []
    for st, t in zip(sets, sorted(treated, key=lambda s: s["first"])):
        tx, ty = xy(t["lat"], t["lon"])
        if not any((tx - px) ** 2 + (ty - py) ** 2 <= 100.0 ** 2 for px, py in sip):
            keep.append(st)
    nosip = analyse(keep) if len(keep) > 20 else None
    out = {"placebo_one_year_earlier": pl, "excluding_sip_sites": {"n": len(keep), "results": nosip},"design": {"R_m": R_M, "sep_m": SEP_M, "K": K, "B": B, "seed": SEED, "last_month": LAST_MONTH},
           "n_treated": len(sets), "n_pool": len(pool), "n_crashes": int(ok.sum()), "crash_sources": src,
           "site_sources": sd.get("sources"), "results": res, "sets": sets}
    (DER / "rlc_did_results.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
