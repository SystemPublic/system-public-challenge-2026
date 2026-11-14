"""Figures for docs/health_gaps.md. Run after the analyses."""
from __future__ import annotations
import json
import sys
import matplotlib
import matplotlib.ticker
import matplotlib.dates
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from analyses.heat.common import tag_srgb
from analyses.health_gaps.common import DER, FIG

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
INK, GREY, ACC, ACC2 = "#222222", "#9a9a9a", "#2a6f97", "#c0504d"


def save(fig, name):
    p = FIG / name
    fig.savefig(p, dpi=200, bbox_inches="tight")
    plt.close(fig)
    tag_srgb(p)


def asthma_power():
    o = json.load(open(DER / "crz_asthma_power.json"))
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    for lab, col in (("age 5-17", ACC), ("adults", INK), ("age 0-4", GREY)):
        g = o["groups"][lab]
        s = pd.Series(g["log_ratio_zone_rest"]); s.index = s.index.astype(int)
        ax[0].plot(s.index, 100 * (s - s.loc[2018:2019].mean()), marker="o", ms=3, color=col, label=lab)
    ax[0].axhline(0, color=GREY, lw=0.6)
    ax[0].set_title("Asthma ED visits, UHF 306-310 against the city outside Manhattan\n(log ratio, percent from 2018-19)", fontsize=9)
    ax[0].set_ylabel("percent"); ax[0].legend(frameon=False, fontsize=8)
    ax[0].xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    sc = o["discrimination"]["by_scenario"]
    keys = list(sc)
    vals = [sc[k]["pred_pct"] for k in keys]
    labels = [k.replace("|", "\n").replace("_", " ") for k in keys]
    y = np.arange(len(keys))
    mde = o["discrimination"]["mde80_pct"]
    ax[1].axvspan(-mde, mde, color="#eeeeee", label=f"not detectable (80% power): ±{mde:.0f}%")
    ax[1].scatter(vals, y, color=ACC2, zorder=3)
    ax[1].set_yticks(y); ax[1].set_yticklabels(labels, fontsize=6)
    ax[1].axvline(0, color=GREY, lw=0.6)
    ax[1].set_xlabel("predicted change in asthma ED visits, percent")
    ax[1].set_title("Predicted effect of the toll against the detectable effect", fontsize=9)
    ax[1].legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    fig.tight_layout()
    save(fig, "crz_asthma_power.png")


def food():
    d = pd.read_csv(DER / "food_zcta.csv", dtype={"zcta": str})
    fig, ax = plt.subplots(1, 3, figsize=(10, 3.3))
    sz = d["pop"] / 2500
    ax[0].scatter(d.xarea, d.y, s=sz, color=GREY, alpha=0.6)
    ax[0].set_xlabel("log2 supermarkets per km2"); ax[0].set_ylabel("log observed/expected diabetes admissions")
    ax[0].set_title("Per area", fontsize=9)
    ax[1].scatter(d.x, d.y, s=sz, color=GREY, alpha=0.6)
    ax[1].set_xlabel("log2 supermarkets per 10,000 residents"); ax[1].set_title("Per resident, unadjusted", fontsize=9)
    base = "ldens + poverty + linc + med_age"
    ry = smf.wls(f"y ~ {base}", data=d, weights=d["pop"]).fit().resid
    rx = smf.wls(f"x ~ {base}", data=d, weights=d["pop"]).fit().resid
    ax[2].scatter(rx, ry, s=sz, color=ACC, alpha=0.6)
    b = np.polyfit(rx, ry, 1, w=np.sqrt(d["pop"]))
    xs = np.linspace(rx.min(), rx.max(), 10)
    ax[2].plot(xs, np.polyval(b, xs), color=INK)
    ax[2].set_xlabel("supermarkets per resident, residual"); ax[2].set_ylabel("admissions, residual")
    ax[2].set_title("Per resident, holding density, poverty,\nincome and median age", fontsize=9)
    for a in (ax[0], ax[1]):
        for z, lab in (("11231", "Red Hook/Carroll Gdns"), ("10474", "Hunts Point")):
            r = d[d.zcta == z]
            if len(r):
                a.annotate(lab, (r[a is ax[0] and "xarea" or "x"].iloc[0], r.y.iloc[0]), fontsize=6, color=ACC2)
    fig.tight_layout()
    save(fig, "food_supermarket_diabetes.png")


def ems():
    o = json.load(open(DER / "ems_explore.json"))
    m = pd.DataFrame(o["month"])
    m["t"] = pd.to_datetime(dict(year=m.y.astype(int), month=m.m.astype(int), day=1))
    m = m.sort_values("t")
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.3))
    ax[0].stackplot(m.t, m.disp / 60, m.trav / 60, colors=[ACC2, ACC], labels=["wait for a unit (dispatch)", "travel"], alpha=0.8)
    ax[0].set_ylabel("minutes"); ax[0].set_title("Life-threatening incidents (severity 1-3),\ncitywide monthly means", fontsize=9)
    ax[0].legend(frameon=False, fontsize=7, loc="upper left")
    for k, col in (("hour_2019", GREY), ("hour_2025", INK)):
        h = pd.DataFrame(o[k]).sort_values("hh")
        ax[1].plot(h.hh, h.resp / 60, color=col, marker="o", ms=2, label=k[-4:])
    ax[1].set_xlabel("hour of day"); ax[1].set_ylabel("minutes"); ax[1].legend(frameon=False, fontsize=7)
    ax[1].set_title("Response time by hour", fontsize=9)
    yb = pd.DataFrame(o["year_borough"])
    yb = yb[yb.borough.notna() & (yb.borough != "UNKNOWN")]
    for b, g in yb.groupby("borough"):
        g = g.sort_values("y")
        ax[2].plot(g.y.astype(int), g.resp / 60, marker="o", ms=2, label=b.title())
    ax[2].legend(frameon=False, fontsize=6); ax[2].set_title("By borough, calendar year", fontsize=9)
    ax[2].set_ylabel("minutes")
    fig.tight_layout()
    save(fig, "ems_where_when.png")
    p = DER / "ems_daily.csv"
    if p.exists():
        from analyses.health_gaps.ems_model import daily, window
        d = window(daily())
        a = d.resample("MS").mean()
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.3))
        ax[0].plot(a.index, a.hosp / 60, color=ACC2, label="time at hospital (transported)")
        ax2 = ax[0].twinx(); ax2.plot(a.index, a.wait / 60, color=ACC, label="wait for a unit, all calls")
        ax[0].set_ylabel("hospital minutes", color=ACC2); ax2.set_ylabel("wait minutes", color=ACC)
        ax[0].set_title("Monthly means (excluding Mar-Jun 2020)", fontsize=9)
        ax[0].xaxis.set_major_locator(matplotlib.dates.YearLocator(2))
        ax[0].xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
        d2 = d.copy()
        d2["lwait"], d2["lhosp"], d2["ln"] = np.log(d2.wait), np.log(d2.hosp), np.log(d2.n)
        d2["dow"], d2["ym"] = d2.index.dayofweek, d2.index.to_period("M").astype(str)
        ry = smf.ols("lwait ~ ln + C(dow) + C(ym)", data=d2).fit().resid
        rx = smf.ols("lhosp ~ ln + C(dow) + C(ym)", data=d2).fit().resid
        ax[1].scatter(rx, ry, s=2, color=GREY, alpha=0.4)
        b = np.polyfit(rx, ry, 1); xs = np.linspace(rx.quantile(0.005), rx.quantile(0.995), 10)
        ax[1].plot(xs, np.polyval(b, xs), color=INK)
        ax[1].set_xlim(rx.quantile(0.002), rx.quantile(0.998)); ax[1].set_ylim(ry.quantile(0.002), ry.quantile(0.998))
        ax[1].set_xlabel("log time at hospital, within month and weekday"); ax[1].set_ylabel("log wait, residual")
        ax[1].set_title(f"Daily: slope {b[0]:.2f}", fontsize=9)
        fig.tight_layout()
        save(fig, "ems_turnaround_wait.png")


if __name__ == "__main__":
    for name in sys.argv[1:] or ["asthma_power", "food", "ems"]:
        globals()[name]()
