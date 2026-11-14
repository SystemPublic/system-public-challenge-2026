"""transit-weekday-pattern: day-of-week pattern of subway entries in the Manhattan CBD.

Registered in claims/registered/transit-weekday-pattern.json before any ridership value was read.
Run:  ~/.venvs/nyc-concordance/bin/python -m analyses.transit.weekday_pattern
Writes data/derived/transit/weekday_pattern.json, figures/transit/weekday_pattern.png and the outcome.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import concord.socrata as soc
from concord import claims

soc.DOMAIN = "https://data.ny.gov"  # the MTA datasets are on the State portal
ROOT = Path(__file__).resolve().parents[2]
OUTD = ROOT / "data" / "derived" / "transit"
FIG = ROOT / "figures" / "transit" / "weekday_pattern.png"
DS = {2018: "t69i-h2me", 2019: "t69i-h2me", 2022: "wujg-7c2s", 2023: "wujg-7c2s", 2024: "wujg-7c2s",
      2025: "5wq4-mkjj", 2026: "5wq4-mkjj"}
SEED, NBOOT = 20261112, 10000
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
BANDS = {"AM peak 06-09": range(6, 10), "midday 10-15": range(10, 16), "PM peak 16-19": range(16, 20),
         "evening 20-23": range(20, 24)}
BOROUGH_YEARS = (2019, 2025, 2026)
SOURCES: list[dict] = []


def _obs(d: dt.date) -> dt.date:
    return d - dt.timedelta(1) if d.weekday() == 5 else d + dt.timedelta(1) if d.weekday() == 6 else d


def _nth(y, m, wd, n):
    d = dt.date(y, m, 1)
    d += dt.timedelta((wd - d.weekday()) % 7)
    return d + dt.timedelta(7 * (n - 1))


def _last(y, m, wd):
    d = dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(1)
    return d - dt.timedelta((d.weekday() - wd) % 7)


def federal_holidays(y: int) -> set[dt.date]:
    h = {_obs(dt.date(y, 1, 1)), _nth(y, 1, 0, 3), _nth(y, 2, 0, 3), _last(y, 5, 0), _obs(dt.date(y, 7, 4)),
         _nth(y, 9, 0, 1), _nth(y, 10, 0, 2), _obs(dt.date(y, 11, 11)), _nth(y, 11, 3, 4), _obs(dt.date(y, 12, 25)),
         _obs(dt.date(y + 1, 1, 1))}
    if y >= 2021:
        h.add(_obs(dt.date(y, 6, 19)))
    return h


def excluded_day(d: dt.date) -> bool:
    return d in federal_holidays(d.year) or d in federal_holidays(d.year - 1) or (d.month == 12 and d.day >= 24) or (d.month == 1 and d.day == 1)


def retained_weeks(start: dt.date, end: dt.date) -> list[dt.date]:
    """Mondays of weeks whose seven days hold no excluded day and whose five weekdays lie in [start, end]."""
    out = []
    m = start + dt.timedelta((0 - start.weekday()) % 7)
    while m + dt.timedelta(4) <= end:
        if not any(excluded_day(m + dt.timedelta(i)) for i in range(7)):
            out.append(m)
        m += dt.timedelta(7)
    return out


def cbd_complexes():
    rows, src = soc.query("39hk-dx4f", select="complex_id,stop_name,borough,cbd,gtfs_latitude,gtfs_longitude,daytime_routes", limit=5000)
    SOURCES.append({**src, "data_access": "open", "portal": "data.ny.gov"})
    cx = defaultdict(list)
    for r in rows:
        cx[r["complex_id"]].append(r)
    cbd = sorted(c for c, v in cx.items() if any(x["cbd"] == "true" for x in v))
    pos = {c: (np.mean([float(x["gtfs_latitude"]) for x in v]), np.mean([float(x["gtfs_longitude"]) for x in v])) for c, v in cx.items()}
    names = {c: " / ".join(sorted({x["stop_name"] for x in v})) for c, v in cx.items()}
    return cbd, pos, names


def _km(a, b):
    la = math.radians((a[0] + b[0]) / 2)
    return 111.32 * math.hypot(a[0] - b[0], (a[1] - b[1]) * math.cos(la))


def hourly(year: int, cbd: list[str]) -> pd.DataFrame:
    """Entries by day, hour and area (CBD, or borough) for one calendar year, in half-year queries."""
    ds, parts = DS[year], []
    inlist = ",".join(f"'{c}'" for c in cbd)
    if ds == "5wq4-mkjj":  # half-year aggregations time out on this dataset; query by month
        ends = [(dt.date(year + (m == 12), m % 12 + 1, 1) - dt.timedelta(1)) for m in range(1, 13)]
        chunks = [(f"{year}-{m:02d}-01", str(e)) for m, e in zip(range(1, 13), ends) if dt.date(year, m, 1) <= dt.date(2026, 10, 31)]
    else:
        chunks = [(f"{year}-01-01", f"{year}-06-30"), (f"{year}-07-01", f"{year}-12-31")]
    for a, b in chunks:
        w = f"transit_mode='subway' AND transit_timestamp between '{a}T00:00:00' and '{b}T23:59:59'"
        sel = "date_trunc_ymd(transit_timestamp) as day, date_extract_hh(transit_timestamp) as hr, sum(ridership) as n"
        rows, src = soc.query(ds, select=sel, where=w + f" AND station_complex_id in ({inlist})", group="day,hr", limit=50000)
        SOURCES.append({**src, "data_access": "open", "portal": "data.ny.gov"})
        parts.append(pd.DataFrame(rows).assign(area="CBD"))
        if year in BOROUGH_YEARS:  # the outer-borough contrast needs only 2019 and the recent period
            rows, src = soc.query(ds, select="borough, " + sel, where=w, group="borough,day,hr", limit=50000)
            SOURCES.append({**src, "data_access": "open", "portal": "data.ny.gov"})
            parts.append(pd.DataFrame(rows).rename(columns={"borough": "area"}))
    df = pd.concat([p for p in parts if len(p)], ignore_index=True)
    df["day"] = pd.to_datetime(df["day"]).dt.date
    df["hr"] = df["hr"].astype(int)
    df["n"] = df["n"].astype(float)
    return df


def by_complex(weeks: list[dt.date]) -> pd.DataFrame:
    """Entries by day and complex for the Monday-Friday days of each retained week, one query per week
    (month-long queries of this grouping time out on the portal)."""
    parts = []
    for m in weeks:
        w = f"transit_mode='subway' AND transit_timestamp between '{m}T00:00:00' and '{m + dt.timedelta(4)}T23:59:59'"
        rows, src = soc.query(DS[m.year], select="date_trunc_ymd(transit_timestamp) as day, station_complex_id, sum(ridership) as n",
                              where=w, group="day,station_complex_id", limit=50000)
        SOURCES.append({**src, "data_access": "open", "portal": "data.ny.gov"})
        parts.append(pd.DataFrame(rows))
    df = pd.concat(parts, ignore_index=True)
    df["day"] = pd.to_datetime(df["day"]).dt.date
    df["n"] = df["n"].astype(float)
    return df


def week_matrix(daily: pd.Series, weeks: list[dt.date]) -> np.ndarray:
    """weeks x 5 matrix of entries; daily is indexed by date."""
    return np.array([[daily.get(m + dt.timedelta(i), np.nan) for i in range(5)] for m in weeks], dtype=float)


def stats(M: np.ndarray, agg=np.mean) -> dict:
    I = M / M[:, 1:4].mean(axis=1, keepdims=True)
    mi = agg(I, axis=0)
    return {"index": mi, "def_mon": 1 - mi[0], "def_fri": 1 - mi[4], "mf": 1 - (mi[0] + mi[4]) / 2,
            "range": mi[1:4].max() - mi[1:4].min()}


def boot(M: np.ndarray, rng, agg=np.mean) -> dict:
    idx = rng.integers(0, len(M), size=(NBOOT, len(M)))
    I = M / M[:, 1:4].mean(axis=1, keepdims=True)
    mi = agg(I[idx], axis=1)  # NBOOT x 5
    return {"index": mi, "def_mon": 1 - mi[:, 0], "def_fri": 1 - mi[:, 4], "mf": 1 - (mi[:, 0] + mi[:, 4]) / 2,
            "range": mi[:, 1:4].max(axis=1) - mi[:, 1:4].min(axis=1)}


def ci(x):
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]


def summarise(M, rng, agg=np.mean):
    s, b = stats(M, agg), boot(M, rng, agg)
    out = {"n_weeks": int(len(M)), "index": {d: float(v) for d, v in zip(DAYS, s["index"])},
           "index_ci": {d: ci(b["index"][:, i]) for i, d in enumerate(DAYS)}}
    for k in ("def_mon", "def_fri", "mf", "range"):
        out[k] = float(s[k]) * 100
        out[k + "_ci"] = [v * 100 for v in ci(b[k])]
    return out, b


def delta(Ma, Mb, rng, agg=np.mean):
    """MF deficit of a minus b, percentage points, with bootstrap interval."""
    sa, ba = summarise(Ma, rng, agg)
    sb, bb = summarise(Mb, rng, agg)
    d = (ba["mf"] - bb["mf"]) * 100
    return {"estimate": sa["mf"] - sb["mf"], "lo": ci(d)[0], "hi": ci(d)[1]}, sa, sb


def main():
    rng = np.random.default_rng(SEED)
    OUTD.mkdir(parents=True, exist_ok=True)
    FIG.parent.mkdir(parents=True, exist_ok=True)
    cbd, pos, names = cbd_complexes()
    H = {y: hourly(y, cbd) for y in (2018, 2019, 2022, 2023, 2024, 2025, 2026)}
    Hall = pd.concat(H.values(), ignore_index=True)
    periods = {"2018": (dt.date(2018, 1, 1), dt.date(2018, 12, 31)), "2019": (dt.date(2019, 1, 1), dt.date(2019, 12, 31)),
               "2022": (dt.date(2022, 1, 1), dt.date(2022, 12, 31)), "2023": (dt.date(2023, 1, 1), dt.date(2023, 12, 31)),
               "2024": (dt.date(2024, 1, 1), dt.date(2024, 12, 31)), "2025": (dt.date(2025, 1, 1), dt.date(2025, 12, 31)),
               "recent": (dt.date(2025, 11, 1), dt.date(2026, 10, 31))}
    W = {k: retained_weeks(*v) for k, v in periods.items()}

    def daily(area, hours=None):
        d = Hall[Hall.area.isin(area if isinstance(area, list) else [area])]
        if hours is not None:
            d = d[d.hr.isin(list(hours))]
        return d.groupby("day")["n"].sum()

    def mat(area, per, hours=None):
        M = week_matrix(daily(area, hours), W[per])
        if np.isnan(M).any():
            raise RuntimeError(f"missing days in {area} {per}")
        return M

    res = {"n_cbd_complexes": len(cbd), "weeks": {k: [str(m) for m in v] for k, v in W.items()}}
    # primary
    D, s_rec, s_19 = delta(mat("CBD", "recent"), mat("CBD", "2019"), rng)
    res["primary"] = {"recent": s_rec, "y2019": s_19, "delta": D}
    # placebo 2019 - 2018
    P, _, s_18 = delta(mat("CBD", "2019"), mat("CBD", "2018"), rng)
    res["placebo_2019_minus_2018"] = {"delta": P, "y2018": s_18}
    # trajectory
    res["trajectory"] = {k: summarise(mat("CBD", k), rng)[0] for k in ("2018", "2019", "2022", "2023", "2024", "2025", "recent")}
    # hour bands
    res["bands"] = {}
    for b, hrs in BANDS.items():
        d, a, c = delta(mat("CBD", "recent", hrs), mat("CBD", "2019", hrs), rng)
        res["bands"][b] = {"recent": a, "y2019": c, "delta": d}
    outer = ["Bronx", "Brooklyn", "Queens"]
    d, a, c = delta(mat(outer, "recent", BANDS["AM peak 06-09"]), mat(outer, "2019", BANDS["AM peak 06-09"]), rng)
    res["outer_am"] = {"recent": a, "y2019": c, "delta": d}
    d, a, c = delta(mat(outer, "recent"), mat(outer, "2019"), rng)
    res["outer_all_day"] = {"recent": a, "y2019": c, "delta": d}
    # sensitivity S2, S4
    d, a, c = delta(mat("CBD", "recent"), mat("CBD", "2019"), rng, agg=np.median)
    res["S2_median"] = {"recent": a, "y2019": c, "delta": d}
    d, a, c = delta(mat("CBD", "2025"), mat("CBD", "2019"), rng)
    res["S4_calendar_2025"] = {"recent": a, "y2019": c, "delta": d}
    # S3 unbalanced: drop only excluded days
    s3 = {}
    cd = daily("CBD")
    for k in ("recent", "2019"):
        a0, b0 = periods[k]
        days = [x for x in cd.index if a0 <= x <= b0 and x.weekday() < 5 and not excluded_day(x)]
        m = pd.Series({x: cd[x] for x in days}).groupby(lambda x: x.weekday()).mean()
        mid = m[[1, 2, 3]].mean()
        s3[k] = {"n_days": len(days), "index": {DAYS[i]: float(m[i] / mid) for i in range(5)},
                 "mf": float(100 * (1 - (m[0] + m[4]) / (2 * mid))), "range": float(100 * (m[[1, 2, 3]].max() - m[[1, 2, 3]].min()) / mid)}
    s3["delta"] = s3["recent"]["mf"] - s3["2019"]["mf"]
    res["S3_days_only"] = s3
    # complex-level: S1, S5, ranking
    C = {k: by_complex(W[k]) for k in ("2019", "recent")}
    core_pts = [(40.7527, -73.9772), (40.7069, -74.0110)]
    core = [c for c in cbd if min(_km(pos[c], p) for p in core_pts) <= 1.2]
    res["S1_core_complexes"] = [names[c] for c in core]
    cm, per_cx, wkmean = {}, {}, {}
    for k in ("2019", "recent"):
        piv = C[k].pivot_table(index="day", columns="station_complex_id", values="n", aggfunc="sum")
        wkdays = [m + dt.timedelta(i) for m in W[k] for i in range(5)]
        wkmean[k] = piv.reindex(wkdays).mean()
        cm[k] = week_matrix(piv[[c for c in core if c in piv]].sum(axis=1), W[k])
        chk = week_matrix(piv[[c for c in cbd if c in piv]].sum(axis=1), W[k])
        res.setdefault("crosscheck_cbd_sum", {})[k] = float(np.nanmax(np.abs(chk / mat("CBD", k) - 1)))
        per_cx[k] = {}
        for c in cbd:
            if c in piv:
                M = week_matrix(piv[c].fillna(0), W[k])
                ok = M[:, 1:4].mean(axis=1) > 0
                if ok.sum() >= 20:
                    per_cx[k][c] = stats(M[ok])["mf"] * 100
    d, a, c = delta(cm["recent"], cm["2019"], rng)
    res["S1_office_core"] = {"n_complexes": len(core), "recent": a, "y2019": c, "delta": d}
    both = sorted(set(per_cx["2019"]) & set(per_cx["recent"]))
    r = np.array([per_cx["recent"][c] for c in both]); b = np.array([per_cx["2019"][c] for c in both])
    bi = rng.integers(0, len(both), size=(NBOOT, len(both)))
    res["S5_complex_level"] = {"n": len(both), "recent_median": float(np.median(r)), "recent_iqr": [float(np.percentile(r, 25)), float(np.percentile(r, 75))],
                               "y2019_median": float(np.median(b)), "y2019_iqr": [float(np.percentile(b, 25)), float(np.percentile(b, 75))],
                               "delta_mean": float((r - b).mean()), "delta_ci": ci((r - b)[bi].mean(axis=1)),
                               "n_complexes_delta_positive": int(((r - b) > 0).sum()),
                               "by_complex": {names.get(c, c): {"y2019": round(per_cx["2019"][c], 2), "recent": round(per_cx["recent"][c], 2)} for c in both}}
    # ranking
    a19, arc = wkmean["2019"].dropna(), wkmean["recent"].dropna()
    common = sorted(set(a19.index) & set(arc.index))
    rho = float(pd.Series(a19[common]).rank().corr(pd.Series(arc[common]).rank()))
    t19, trc = list(a19.sort_values(ascending=False).index[:20]), list(arc.sort_values(ascending=False).index[:20])
    res["ranking"] = {"spearman_all": rho, "n_complexes": len(common), "top20_overlap": len(set(t19) & set(trc)),
                      "top20_cbd_2019": sum(c in cbd for c in t19), "top20_cbd_recent": sum(c in cbd for c in trc),
                      "top20_2019": [{"complex": names.get(c, c), "cbd": c in cbd, "mean_weekday_entries": round(float(a19[c]))} for c in t19],
                      "top20_recent": [{"complex": names.get(c, c), "cbd": c in cbd, "mean_weekday_entries": round(float(arc[c])),
                                        "ratio_to_2019": round(float(arc[c] / a19[c]), 3) if c in a19 else None} for c in trc]}
    res["levels"] = {k: float(np.mean(mat("CBD", k))) for k in W}
    (OUTD / "weekday_pattern.json").write_text(json.dumps(res, indent=1))
    (OUTD / "weekday_pattern_sources.json").write_text(json.dumps(SOURCES, indent=1))
    figure(res)
    return res


def figure(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    blue, grey = "#2a78d6", "#8a8f98"
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1.15, 1]})
    x = np.arange(5)
    for key, col, lab in (("y2019", grey, "2019"), ("recent", blue, "Nov 2025 to Oct 2026")):
        s = res["primary"][key]
        y = np.array([s["index"][d] for d in DAYS]) * 100
        lo = np.array([s["index_ci"][d][0] for d in DAYS]) * 100
        hi = np.array([s["index_ci"][d][1] for d in DAYS]) * 100
        ax[0].errorbar(x, y, yerr=[y - lo, hi - y], color=col, marker="o", ms=6, lw=2, capsize=3, label=f"{lab} ({s['n_weeks']} weeks)")
        for xi, yi in zip(x, y):
            ax[0].annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points", xytext=(-8, 3) if key == "y2019" else (8, -10),
                           ha="right" if key == "y2019" else "left", fontsize=8, color=col)
    ax[0].axhline(100, color="#c9ccd1", lw=1, zorder=0)
    ax[0].set_xticks(x, DAYS)
    ax[0].set_ylabel("Entries, % of the week's Tue-Thu mean")
    ax[0].set_title("Subway entries by weekday, 65 Manhattan CBD complexes", fontsize=10, loc="left")
    ax[0].legend(frameon=False, fontsize=8, loc="lower center")
    names = ["All day"] + list(BANDS)
    v19 = [res["primary"]["y2019"]["mf"]] + [res["bands"][b]["y2019"]["mf"] for b in BANDS]
    vrc = [res["primary"]["recent"]["mf"]] + [res["bands"][b]["recent"]["mf"] for b in BANDS]
    e19 = [res["primary"]["y2019"]["mf_ci"]] + [res["bands"][b]["y2019"]["mf_ci"] for b in BANDS]
    erc = [res["primary"]["recent"]["mf_ci"]] + [res["bands"][b]["recent"]["mf_ci"] for b in BANDS]
    yy = np.arange(len(names))[::-1]
    for vals, errs, col, off, lab in ((v19, e19, grey, 0.17, "2019"), (vrc, erc, blue, -0.17, "Nov 2025 to Oct 2026")):
        ax[1].barh(yy + off, vals, height=0.3, color=col, label=lab)
        ax[1].errorbar(vals, yy + off, xerr=[[v - e[0] for v, e in zip(vals, errs)], [e[1] - v for v, e in zip(vals, errs)]], fmt="none", ecolor="#30343a", lw=1, capsize=2)
        for v, e, y0 in zip(vals, errs, yy + off):
            ax[1].text(max(e[1], 0) + 0.3, y0, f"{v:.1f}", va="center", fontsize=8, color="#30343a")
    ax[1].axvline(0, color="#30343a", lw=0.8)
    ax[1].set_yticks(yy, names)
    ax[1].set_xlabel("Monday/Friday deficit, % below Tue-Thu mean")
    ax[1].set_title("Deficit by hour of entry", fontsize=10, loc="left")
    ax[1].legend(frameon=False, fontsize=8, loc="lower right")
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "MTA Subway Hourly Ridership (data.ny.gov t69i-h2me, 5wq4-mkjj). Weeks with a federal holiday or 24 Dec to 1 Jan dropped.\n"
             "Bars and points: mean over weeks; lines: 95% week-bootstrap intervals. Entries are fare-paid entries, not pedestrians.", fontsize=7, color="#555")
    ax[0].set_xlim(-0.45, 4.45)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(FIG, dpi=200)
    plt.close(fig)
    from PIL import Image, ImageCms
    im = Image.open(FIG).convert("RGB")
    im.save(FIG, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes(), dpi=(200, 200))


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: r[k] for k in ("primary", "placebo_2019_minus_2018", "trajectory", "bands", "outer_am", "outer_all_day", "S1_office_core",
                                        "S2_median", "S3_days_only", "S4_calendar_2025", "crosscheck_cbd_sum", "levels")}, indent=1, default=str))
    print(json.dumps({k: v for k, v in r["S5_complex_level"].items() if k != "by_complex"}, indent=1))
    print(json.dumps(r["ranking"], indent=1))
