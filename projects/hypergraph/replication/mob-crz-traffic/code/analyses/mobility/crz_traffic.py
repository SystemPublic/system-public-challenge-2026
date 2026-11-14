"""mob-crz-traffic: congestion pricing and CBD taxi/FHV speeds and trip counts.

Registered model: OLS of log monthly value on area, calendar month, year and
area x post (post = Jan 2025 on); pre-period Jan 2023 - Dec 2024; HAC (3 lags).
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from concord import socrata
from analyses.mobility.common import DER, nys, savefig

START = pd.Timestamp("2025-01-01")


def did(df: pd.DataFrame, treat: str, value: str) -> dict:
    d = df.copy()
    d["y"] = np.log(d[value])
    d["calm"] = d["month"].dt.month
    d["year"] = d["month"].dt.year
    d["treat"] = (d["area"] == treat).astype(int)
    d["post"] = (d["month"] >= START).astype(int)
    d = d.sort_values(["area", "month"])
    m = smf.ols("y ~ C(area) + C(calm) + C(year) + treat:post", data=d).fit(
        cov_type="HAC", cov_kwds={"maxlags": 3})
    b, se = m.params["treat:post"], m.bse["treat:post"]
    return {"estimate_log": b, "se": se, "pct": 100 * (np.exp(b) - 1),
            "lo_pct": 100 * (np.exp(b - 1.96 * se) - 1), "hi_pct": 100 * (np.exp(b + 1.96 * se) - 1),
            "n": int(m.nobs)}


def placebo(df, treat, value):
    d = df[(df["month"] >= "2023-01-01") & (df["month"] < "2025-01-01")].copy()
    global START
    keep = START
    START = pd.Timestamp("2024-01-01")
    try:
        return did(d, treat, value)
    finally:
        START = keep


def main():
    out, sources = {}, []
    # --- speeds
    rows, src = nys("6p29-6xqn", select="month, zone, zonal_speed", order="month")
    sources.append(src)
    sp = pd.DataFrame(rows)
    sp["month"] = pd.to_datetime(sp["month"])
    sp["speed"] = sp["zonal_speed"].astype(float)
    sp = sp.rename(columns={"zone": "area"})
    sp.to_csv(DER / "crz_speeds_monthly.csv", index=False)
    w = sp[sp["month"] >= "2023-01-01"]
    for comp in ("Greater NYC", "CBD Adjacent"):
        out[f"speed_CBD_vs_{comp}"] = did(w[w["area"].isin(["CBD", comp])], "CBD", "speed")
        out[f"speed_CBD_vs_{comp}_placebo2024"] = placebo(w[w["area"].isin(["CBD", comp])], "CBD", "speed")

    # --- TLC trips by zone
    zrows, zsrc = nys("yfdc-w5jh", select="taxi_zone")
    sources.append(zsrc)
    cbd = {int(r["taxi_zone"]) for r in zrows}
    rows, src = socrata.query("c5iv-bn4s", select="metric_month, industry, locationid, sum(trip_count) as n",
                              where="metric_month >= '2023-01-01'", group="metric_month, industry, locationid")
    sources.append(src)
    t = pd.DataFrame(rows)
    t["n"] = t["n"].astype(float)
    t["locationid"] = pd.to_numeric(t["locationid"], errors="coerce")
    t["month"] = pd.to_datetime(t["metric_month"])
    t["area"] = np.where(t["locationid"].isin(cbd), "CBD", "Outside CBD")
    tm = t.groupby(["month", "area"], as_index=False)["n"].sum()
    tind = t.groupby(["month", "industry", "area"], as_index=False)["n"].sum()
    tind.to_csv(DER / "crz_tlc_trips_monthly.csv", index=False)
    out["trips_CBD_vs_outside"] = did(tm, "CBD", "n")
    out["trips_CBD_vs_outside_placebo2024"] = placebo(tm, "CBD", "n")
    for ind in tind["industry"].unique():
        out[f"trips_{ind}"] = did(tind[tind["industry"] == ind], "CBD", "n")

    # --- VMT, descriptive
    rows, src = nys("jbxx-kxff", select="date, area, daily_vmt_agps, daily_vmt_cvd, indexed_average_vmt", order="date")
    sources.append(src)
    v = pd.DataFrame(rows)
    v["date"] = pd.to_datetime(v["date"])
    for c in ("daily_vmt_agps", "daily_vmt_cvd", "indexed_average_vmt"):
        v[c] = pd.to_numeric(v[c], errors="coerce")
    v.to_csv(DER / "crz_vmt_monthly.csv", index=False)
    vv = v[v["area"] == "CRZ"].set_index("date")
    m24 = vv.loc["2024-01-01":"2024-12-01"]
    m25 = vv.loc["2025-01-01":"2025-12-01"]
    j = m24.reset_index().assign(m=lambda x: x.date.dt.month).merge(
        m25.reset_index().assign(m=lambda x: x.date.dt.month), on="m", suffixes=("_24", "_25"))
    out["vmt_crz_2025_vs_2024_pct"] = {c: float(100 * (j[f"{c}_25"].sum() / j[f"{c}_24"].sum() - 1))
                                       for c in ("daily_vmt_agps", "daily_vmt_cvd") if j[f"{c}_24"].notna().all()}

    # --- CRZ entries, descriptive (2025 on)
    rows, src = nys("t6yz-b64h", select="date_trunc_ym(toll_date) as m, sum(crz_entries) as e, sum(excluded_roadway_entries) as x",
                    group="m", order="m")
    sources.append(src)
    e = pd.DataFrame(rows)
    e.to_csv(DER / "crz_entries_monthly.csv", index=False)

    (DER / "crz_traffic_results.json").write_text(json.dumps({"results": out, "sources": sources}, indent=1, default=float))
    for k, r in out.items():
        print(k, {a: round(b, 2) if isinstance(b, float) else b for a, b in r.items()} if isinstance(r, dict) else r)

    # --- figure
    import matplotlib.dates as mdates
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    ax = axes[0]
    for a, c in [("CBD", "#c0392b"), ("CBD Adjacent", "#7f8c8d"), ("Greater NYC", "#2c3e50")]:
        s = sp[(sp["area"] == a) & (sp["month"] >= "2022-01-01")]
        ax.plot(s["month"], s["speed"], label=a, color=c)
    ax.set_ylabel("Average taxi and FHV speed (mph)")
    ax.set_title("(a) Speeds by area, MTA 6p29-6xqn", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    ax = axes[1]
    ps = sp.pivot(index="month", columns="area", values="speed").loc["2022-01-01":]
    r = ps["CBD"] / ps["Greater NYC"]
    ax.plot(r.index, 100 * r / r.loc["2024-01-01":"2024-12-01"].mean(), color="#c0392b")
    ax.axhline(100, color="#999", lw=0.6)
    ax.set_ylabel("CBD speed / rest-of-city speed (2024 mean = 100)")
    ax.set_title("(b) CBD speed relative to Greater NYC", fontsize=10)
    ax = axes[2]
    piv = tm.pivot(index="month", columns="area", values="n")
    base = piv.loc["2024-01-01":"2024-12-01"].mean()
    for a, c in [("CBD", "#c0392b"), ("Outside CBD", "#2c3e50")]:
        ax.plot(piv.index, 100 * piv[a] / base[a], label=a, color=c)
    ax.set_ylabel("TLC trips, pickups + drop-offs (2024 mean = 100)")
    ax.set_title("(c) TLC trips by taxi zone, c5iv-bn4s", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    for ax in axes:
        ax.axvline(START, color="k", ls="--", lw=0.8)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.suptitle("Congestion pricing began 5 January 2025 (dashed line)", fontsize=10)
    fig.tight_layout()
    print(savefig(fig, "crz_traffic_before_after.png"))


if __name__ == "__main__":
    main()
