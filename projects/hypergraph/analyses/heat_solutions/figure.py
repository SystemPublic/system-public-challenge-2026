"""Figure for docs/heat_solutions.md: figures/heat_solutions/heat_solutions.png.
Panels a and b are descriptive (binned daily means, no adjustment). Panel c shows model estimates."""
import json
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analyses.heat_solutions.common import DER, FIG

LOW, HIGH = "#b2182b", "#2166ac"
R = json.loads((DER / "results.json").read_text())
X = json.loads((DER / "exploratory.json").read_text())
fig, ax = plt.subplots(1, 3, figsize=(15, 4.6), dpi=200)

d = pd.read_csv(DER / "shootings_daily_by_ac_half.csv", index_col=0, parse_dates=True)
d["bin"] = pd.cut(d["TMAX"], np.arange(-3, 40, 3))
g = d.groupby("bin", observed=True).agg(low=("low", "mean"), high=("high", "mean"), n=("low", "size"), t=("TMAX", "mean"))
g = g[g.n >= 40]
ref = g[(g.t >= 12) & (g.t < 18)]
for c, col, lab in (("low", LOW, "29 districts with fewer households with air conditioning"), ("high", HIGH, "30 districts with more")):
    ax[0].plot(g.t, g[c] / ref[c].mean(), "o-", color=col, label=lab, lw=1.8, ms=4)
ax[0].axvline(27, color="0.6", lw=0.8, ls=":")
ax[0].set_xlabel("Daily maximum temperature, Central Park (°C)")
ax[0].set_ylabel("Shootings per day, relative to days of 12 to 18 °C")
ax[0].set_title("a. Shootings, 2006 to 2026", loc="left", fontsize=11)
ax[0].legend(frameon=False, fontsize=8, loc="upper left")

e = pd.read_csv(DER / "heat_calls_daily_by_ac_half.csv", index_col=0, parse_dates=True)
e["bin"] = pd.cut(e["TMAX"], np.arange(12, 40, 2))
g = e.groupby("bin", observed=True).agg(low=("low", "mean"), high=("high", "mean"), n=("low", "size"), t=("TMAX", "mean"))
g = g[g.n >= 20]
for c, col in (("low", LOW), ("high", HIGH)):
    ax[1].plot(g.t, g[c], "o-", color=col, lw=1.8, ms=4)
ax[1].set_yscale("log")
ax[1].axvline(27, color="0.6", lw=0.8, ls=":")
ax[1].set_xlabel("Daily maximum temperature, Central Park (°C)")
ax[1].set_ylabel("Ambulance calls coded HEAT per day (log scale)")
ax[1].set_title("b. Ambulance calls for heat illness, May to September", loc="left", fontsize=11)

S = R["heat_school_out"]
rows = [("All hours\n(registered)", S["primary_out_of_school_irr"])] + [(k.replace("-", " to ") + " h", v) for k, v in X["school_by_hour_block"].items()]
for i, (lab, v) in enumerate(rows):
    ax[2].plot([v["lo"], v["hi"]], [i, i], color="0.25", lw=1.6)
    ax[2].plot(v["estimate"], i, "o", color="0.1" if i == 0 else "0.45", ms=6)
ax[2].axvline(1, color="0.6", lw=0.8)
ax[2].set_yticks(range(len(rows)))
ax[2].set_yticklabels([r[0] for r in rows], fontsize=9)
ax[2].invert_yaxis()
ax[2].set_xlabel("Rate ratio of shootings, weekdays out of school\nagainst school weekdays at the same temperature", fontsize=9)
ax[2].set_title("c. School out of session", loc="left", fontsize=11)
for a in ax:
    a.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
out = FIG / "heat_solutions.png"
fig.savefig(out)
subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(out)], capture_output=True)
print(out)
