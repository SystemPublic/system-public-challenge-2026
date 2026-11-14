"""mob-crz-air: NO2 and PM2.5 at EPA AQS monitors inside vs outside the Congestion Relief Zone.

Registered model: log(daily conc) ~ site FE + date FE + inzone x post (post from 5 Jan 2025),
2022-2025, interval from a block bootstrap over ISO weeks (1,000 draws), placebo post = 5 Jan 2024.

Data: EPA AirData pre-generated daily files, downloaded to ~/opt/nyc-concordance/aqs/
(https://aqs.epa.gov/aqsweb/airdata/daily_<param>_<year>.zip, files 'As of 2026-06-25').
"""
from __future__ import annotations

import glob
import json
import math
import os
import subprocess
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analyses.mobility.common import DER, savefig

AQS = os.path.expanduser("~/opt/nyc-concordance/aqs")
URL = "https://aqs.epa.gov/aqsweb/airdata/daily_{p}_{y}.zip"
YEARS = (2022, 2023, 2024, 2025)
NYC = {5, 47, 61, 81, 85}
START = pd.Timestamp("2025-01-05")
RNG = np.random.default_rng(20261112)


def ensure(p):
    os.makedirs(AQS, exist_ok=True)
    for y in YEARS:
        f = f"{AQS}/daily_{p}_{y}.zip"
        if not os.path.exists(f):
            subprocess.run(["curl", "-s", "-f", "-o", f, URL.format(p=p, y=y)], check=True)


def south_of_60th(lat, lon):
    """Project onto the Manhattan avenue axis (29 degrees east of north) and compare with 60th St at 5th Ave."""
    k = math.radians(29)
    u = lambda la, lo: (lo + 73.97) * 84.2 * math.sin(k) + (la - 40.76) * 111.0 * math.cos(k)
    return u(lat, lon) < u(40.7648, -73.9727)


def load(p) -> pd.DataFrame:
    ensure(p)
    fs = []
    for z in sorted(glob.glob(f"{AQS}/daily_{p}_*.zip")):
        if int(z[-8:-4]) not in YEARS:
            continue
        zf = zipfile.ZipFile(z)
        d = pd.read_csv(zf.open(zf.namelist()[0]), low_memory=False,
                        usecols=["State Code", "County Code", "Site Num", "POC", "Latitude", "Longitude",
                                 "Local Site Name", "Date Local", "Sample Duration", "Event Type", "Arithmetic Mean"])
        fs.append(d[(d["State Code"] == 36) & d["County Code"].isin(NYC)])
    d = pd.concat(fs)
    d = d[d["Event Type"].fillna("None").isin(["None", "Included"])]
    d["site"] = d["County Code"].astype(str) + "-" + d["Site Num"].astype(str) + " " + d["Local Site Name"]
    d["date"] = pd.to_datetime(d["Date Local"])
    d = d[d["Arithmetic Mean"] > 0]
    g = d.groupby(["site", "date"], as_index=False).agg(conc=("Arithmetic Mean", "mean"), lat=("Latitude", "first"),
                                                        lon=("Longitude", "first"), county=("County Code", "first"))
    g["group"] = [("in-zone" if south_of_60th(a, o) else "Manhattan north of 60th") if c == 61 else "other boroughs"
                  for a, o, c in zip(g["lat"], g["lon"], g["county"])]
    return g


def twfe(d: pd.DataFrame, start, date_key="date", iters=50) -> float:
    y = np.log(d["conc"].to_numpy())
    x = ((d["group"] == "in-zone") & (d["date"] >= start)).astype(float).to_numpy()
    s = pd.factorize(d["site"])[0]
    t = pd.factorize(d[date_key])[0]
    ns, nt = s.max() + 1, t.max() + 1
    for _ in range(iters):  # alternating projections onto site and date means
        for idx, n in ((s, ns), (t, nt)):
            cnt = np.bincount(idx, minlength=n)
            y = y - (np.bincount(idx, y, n) / np.maximum(cnt, 1))[idx]
            x = x - (np.bincount(idx, x, n) / np.maximum(cnt, 1))[idx]
    return float((x @ y) / (x @ x))


def boot(d, start, n=1000):
    d = d.copy()
    d["week"] = d["date"].dt.strftime("%G-%V")
    weeks = d["week"].unique()
    groups = {w: g for w, g in d.groupby("week")}
    out = []
    for _ in range(n):
        pick = RNG.choice(weeks, size=len(weeks), replace=True)
        parts = []
        for i, w in enumerate(pick):
            g = groups[w].copy()
            g["dkey"] = g["date"].dt.strftime("%Y%m%d") + f"_{i}"
            parts.append(g)
        b = pd.concat(parts)
        if not (((b["group"] == "in-zone") & (b["date"] >= start)).any() and ((b["group"] == "in-zone") & (b["date"] < start)).any()):
            continue
        out.append(twfe(b, start, date_key="dkey", iters=30))
    return np.percentile(out, [2.5, 97.5]), len(out)


def result(d, start, label, nboot=1000):
    est = twfe(d, start)
    (lo, hi), nb = boot(d, start, nboot)
    pct = lambda v: 100 * (math.exp(v) - 1)
    r = {"label": label, "estimate_log": est, "pct": pct(est), "lo_pct": pct(lo), "hi_pct": pct(hi),
         "n_site_days": int(len(d)), "n_sites": int(d["site"].nunique()),
         "in_zone_sites": sorted(d.loc[d["group"] == "in-zone", "site"].unique().tolist()), "n_boot": nb}
    print(label, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
    return r


def main():
    out = {"sources": [{"kind": "epa-aqs-airdata", "url": URL.format(p=p, y=y), "version": "pre-generated file as of 2026-06-25",
                        "parameter": {"42602": "NO2 (ppb)", "88101": "PM2.5 FRM/FEM (ug/m3)"}[p]}
                       for p in ("42602", "88101") for y in YEARS]}
    sites = {}
    for p, name in (("42602", "NO2"), ("88101", "PM25")):
        d = load(p)
        d.to_csv(DER / f"crz_aqs_{name}_daily.csv", index=False)
        sites[name] = (d.groupby(["site", "group"]).agg(first=("date", "min"), last=("date", "max"), days=("date", "size"))
                       .reset_index().astype(str).to_dict("records"))
        if (d["group"] == "in-zone").any():
            out[name] = result(d[d["group"] != "Manhattan north of 60th"], START, f"{name} in-zone vs other boroughs")
            out[name + "_vs_manhattan_north"] = result(d[d["group"] != "other boroughs"], START,
                                                       f"{name} in-zone vs Manhattan north of 60th", nboot=300)
            # sensitivity (not registered): sites observed both before and after the start, >= 50 days each
            cnt = d.assign(post=d["date"] >= START).groupby(["site", "post"]).size().unstack(fill_value=0)
            keep = cnt[(cnt.get(False, 0) >= 50) & (cnt.get(True, 0) >= 50)].index
            out[name + "_balanced_sites"] = result(d[d["site"].isin(keep) & (d["group"] != "Manhattan north of 60th")],
                                                   START, f"{name} sites observed before and after (sensitivity)", nboot=300)
            pre = d[d["date"] < START]
            out[name + "_placebo2024"] = result(pre[pre["group"] != "Manhattan north of 60th"], pd.Timestamp("2024-01-05"),
                                                f"{name} placebo (post = 5 Jan 2024)", nboot=300)
        else:
            out[name] = {"label": f"{name}: no AQS monitor inside the zone in {YEARS[0]}-{YEARS[-1]}", "estimate_log": None}
            print(out[name]["label"])
    out["sites"] = sites
    (DER / "crz_air_results.json").write_text(json.dumps(out, indent=1, default=str))

    # figure: PS 19 against the two comparison monitors that ran in every year, on the same days
    import matplotlib.dates as mdates
    d = pd.read_csv(DER / "crz_aqs_PM25_daily.csv", parse_dates=["date"])
    w = d.pivot_table(index="date", columns="site", values="conc")
    ref_sites = ["5-110 IS 52", "81-124 QUEENS COLLEGE 2"]
    w = w[["61-128 PS 19"] + ref_sites].dropna()
    w["ref"] = w[ref_sites].mean(axis=1)
    w["diff"] = np.log(w["61-128 PS 19"]) - np.log(w["ref"])
    m = w.resample("QS").mean()
    yr = w["diff"].groupby(w.index.year).mean()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    ax = axes[0]
    ax.plot(m.index, m["61-128 PS 19"], color="#c0392b", marker="o", ms=3, label="PS 19, East Village (in zone)")
    ax.plot(m.index, m["ref"], color="#2c3e50", marker="o", ms=3, label="IS 52 (Bronx) and Queens College 2, same days")
    ax.set_ylabel("PM2.5, quarterly mean of daily values (ug/m3)")
    ax.set_title("(a) PM2.5 on days PS 19 sampled", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    ax = axes[1]
    ax.bar(m.index, 100 * (np.exp(m["diff"]) - 1), width=60, color=np.where(m.index >= pd.Timestamp("2025-01-01"), "#c0392b", "#95a5a6"))
    for y, v in yr.items():
        ax.hlines(100 * (np.exp(v) - 1), pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31"), color="k", lw=1.5)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_ylabel("PS 19 above comparison, same days (%)")
    ax.set_title("(b) Quarterly bars; black lines are annual means", fontsize=10)
    for ax in axes:
        ax.axvline(START, color="k", ls="--", lw=0.8)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.suptitle("PM2.5 inside the congestion zone vs other boroughs. No NO2 monitor operated in Manhattan in 2022-2025.",
                 fontsize=9)
    fig.tight_layout()
    print(savefig(fig, "crz_air_pm25_before_after.png"))
    out["ps19_annual_log_excess"] = {int(k): float(v) for k, v in yr.items()}
    (DER / "crz_air_results.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
