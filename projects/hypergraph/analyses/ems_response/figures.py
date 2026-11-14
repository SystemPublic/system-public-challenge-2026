"""Figures for docs/ems_response.md and the exploratory citywide traffic share.
Writes figures/ems_response/*.png (sRGB tagged) and data/derived/ems_response/citywide_share.json."""
import json
import subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analyses.ems_response.common import DER, FIG, SRGB

R = json.load(open(DER / "results.json"))
DEC = json.load(open(DER / "decomposition.json"))
ND = json.load(open(DER / "night_day.json"))
BOR = {"BRONX": "bx", "BROOKLYN": "bk", "MANHATTAN": "mn", "QUEENS": "qn", "RICHMOND / STATEN ISLAND": None}
NAME = {"BRONX": "Bronx", "BROOKLYN": "Brooklyn", "MANHATTAN": "Manhattan", "QUEENS": "Queens", "RICHMOND / STATEN ISLAND": "Staten Island"}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    f = FIG / name
    fig.savefig(f, dpi=200, bbox_inches="tight")
    plt.close(fig)
    subprocess.run(["sips", "--embedProfile", SRGB, str(f)], capture_output=True)


# exploratory citywide traffic share from yellow-taxi pace by borough and block
sp = pd.DataFrame(ND["taxi_mph"])
pace = sp[sp.y.isin([2019, 2026])].pivot_table(index=["area", "blk"], columns="y", values="mph")
dp = np.log(pace[2019] / pace[2026])  # change in log pace (hours per mile)
ybh = pd.read_csv(DER / "ems_ybh.csv")
ybh = ybh[(ybh.sev == "hi") & (ybh.borough != "UNKNOWN") & ybh.y.isin([2019, 2026])].copy()
ybh["blk"] = np.select([ybh.hh.between(1, 5), ybh.hh.between(7, 19)], ["night", "day"], "shoulder")
g = ybh.groupby(["y", "borough", "blk"])[["n", "travel"]].sum()
w26 = g.loc[2026].n / g.loc[2026].n.sum()
rows = []
for (b, k), w in w26.items():
    a = BOR[b]
    d = dp.get((a, k), np.nan) if a else np.nan
    rows.append({"borough": b, "blk": k, "w": w, "dpace": d})
cw = pd.DataFrame(rows)
cw["dpace_filled"] = cw.dpace.fillna(cw.groupby("blk").dpace.transform("mean"))
cy = ybh.groupby("y")[["n", "travel"]].sum()
D = float(np.log((cy.travel / cy.n)[2026] / (cy.travel / cy.n)[2019]))
P = float((cw.w * cw.dpace_filled).sum())
beta_hi = R["t1_hi"]["x_only"]["x"]["est"]
share = {"D_log_citywide_travel": D, "pace_term_log": P, "S1": P / D, "S_at_beta_hi": beta_hi * P / D, "beta_hi": beta_hi,
         "cells": cw.round(4).to_dict("records"),
         "note": "Exploratory. Taxi pace by borough from yellow trips with both ends in the borough (airports excluded); Staten Island has no taxi measure and takes the mean of the other boroughs. 2019 full year EMS against 2026 January-September; taxi January-September both years."}
(DER / "citywide_share.json").write_text(json.dumps(share, indent=1))
print({k: v for k, v in share.items() if k != "cells"})

# Figure 1: annual travel by borough and the wait
ab = pd.DataFrame(DEC["annual_borough_travel_min"]).T
ab.index = ab.index.astype(int)
ac = pd.DataFrame(DEC["annual_city"]).T
ac.index = ac.index.astype(int)
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
for b in ab.columns:
    ax[0].plot(ab.index, ab[b], marker="o", ms=3, label=NAME[b])
ax[0].set_title("Travel time, life-threatening calls (min)")
ax[0].legend(frameon=False, fontsize=7)
ax[1].bar(ac.index, ac.travel_min, color="#4a6fa5", label="travel")
ax[1].bar(ac.index, ac.dispatch_min, bottom=ac.travel_min, color="#d08c60", label="wait for a unit")
ax[1].set_title("Citywide dispatch + travel (min)")
ax[1].legend(frameon=False, fontsize=7)
for a in ax:
    a.set_xticks(range(2017, 2027, 1)); a.tick_params(axis="x", labelrotation=45)
fig.text(0, -0.04, "Source: EMS Incident Dispatch Data (76xm-jjuj), initial severity 1-3, valid response time; 2026 is January-September.", fontsize=7)
save(fig, "annual.png")

# Figure 2: decomposition of the 2019 -> 2026 citywide rise (minutes)
wait = ac.dispatch_min[2026] - ac.dispatch_min[2019]
trav = ac.travel_min[2026] - ac.travel_min[2019]
mix = DEC["borough_hour_2019_2026"]["mix_s"] / 60
tr_b = share["S_at_beta_hi"] * trav
tr_1 = share["S1"] * trav
parts = [("wait for a unit", wait), ("call mix (borough x hour)", mix), ("traffic, at measured elasticity", tr_b),
         ("traffic, extra if one for one", tr_1 - tr_b), ("remainder: distance, supply", trav - mix - tr_1)]
fig, ax = plt.subplots(figsize=(7, 2.4))
left = 0
cols = ["#d08c60", "#999999", "#4a6fa5", "#a9bedc", "#6b8e4e"]
for (lab, v), c in zip(parts, cols):
    ax.barh(0, v, left=left, color=c, label=f"{lab}: {v:.2f}")
    left += v
ax.set_yticks([]); ax.set_xlabel("minutes added, 2019 to 2026 (January-September)")
ax.legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.45), ncol=2)
ax.set_title(f"Life-threatening dispatch + travel rose {ac.travel_min[2026] + ac.dispatch_min[2026] - ac.travel_min[2019] - ac.dispatch_min[2019]:.2f} min")
save(fig, "decomposition.png")

# Figure 3: weekly year-on-year changes, Manhattan
y = pd.read_csv(DER / "weekly_yoy.csv")
y = y[(y.yr * 100 + y.wk >= 202427)]
x = np.arange(len(y))
fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(x, 100 * y.e, label="ambulance travel time", color="#b0413e")
ax.plot(x, 100 * y.p, label="yellow-taxi time per mile", color="#4a6fa5")
ax.axhline(0, color="k", lw=0.5)
ticks = [i for i, (a, b) in enumerate(zip(y.yr, y.wk)) if b in (1, 27)]
ax.set_xticks(ticks, [f"{a}-W{b:02d}" for a, b in zip(y.yr.iloc[ticks], y.wk.iloc[ticks])])
ax.set_ylabel("% change on the same week a year earlier")
ax.legend(frameon=False)
ax.set_title("Manhattan below 110th Street, all hours")
save(fig, "weekly_yoy.png")

# Figure 4: night against day by borough
nd = DEC["night_day_pct_2019_2026"]
fig, ax = plt.subplots(1, 2, figsize=(9, 3.2), sharey=True)
bs = list(nd)
xx = np.arange(len(bs))
ax[0].bar(xx - 0.2, [nd[b]["night"] for b in bs], 0.4, label="01:00-05:59", color="#333366")
ax[0].bar(xx + 0.2, [nd[b]["day"] for b in bs], 0.4, label="07:00-19:59", color="#e0a040")
ax[0].set_xticks(xx, [NAME[b] for b in bs], rotation=30)
ax[0].set_title("Ambulance travel time, % change 2019 to 2026")
ax[0].legend(frameon=False, fontsize=7)
pv = lambda a, k: 100 * (np.exp(dp.get((a, k), np.nan)) - 1) if a else np.nan
ax[1].bar(xx - 0.2, [pv(BOR[b], "night") for b in bs], 0.4, color="#333366")
ax[1].bar(xx + 0.2, [pv(BOR[b], "day") for b in bs], 0.4, color="#e0a040")
ax[1].set_xticks(xx, [NAME[b] for b in bs], rotation=30)
ax[1].set_title("Yellow-taxi time per mile, % change")
ax[1].axhline(0, color="k", lw=0.5)
fig.text(0, -0.16, "EMS: 2019 full year against January-September 2026. Taxi: January-September both years, trips with both ends in the borough; Staten Island has none.", fontsize=7)
save(fig, "night_day.png")
