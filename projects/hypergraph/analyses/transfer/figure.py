"""Figure: NYC and Chicago side by side for the heat-shootings and weekday-pattern results."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived"
OUT = ROOT / "figures" / "graph" / "transfer_chicago.png"
NYC_C, CHI_C, GREY = "#2a78d6", "#d9622b", "#8a8f98"
heat_n = json.loads((D / "heat" / "shootings_results.json").read_text())
heat_c = json.loads((D / "graph" / "transfer_chicago" / "heat_results.json").read_text())
wk_n = json.loads((D / "transit" / "weekday_pattern.json").read_text())
wk_c = json.loads((D / "graph" / "transfer_chicago" / "weekday_results.json").read_text())
expl = json.loads((D / "graph" / "transfer_chicago" / "weekday_exploratory_no_polar_vortex_week.json").read_text())
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

fig, ax = plt.subplots(2, 2, figsize=(11.5, 8.6))
# A: shootings by TMAX bin
a = ax[0, 0]
for f, col, lab, mean in ((D / "heat" / "shootings_by_tmax_bin.csv", NYC_C, "New York (Central Park)", None),
                          (D / "graph" / "transfer_chicago" / "heat_by_tmax_bin.csv", CHI_C, "Chicago (Midway)", None)):
    t = pd.read_csv(f)
    t["lo"] = t["bin"].str.extract(r"\((-?\d+\.?\d*),")[0].astype(float)
    t["mid"] = t["lo"] + 1.5
    t = t[t["count"] >= 20]
    base = (t["mean"] * t["count"]).sum() / t["count"].sum()
    a.plot(t["mid"], t["mean"] / base, color=col, marker="o", ms=4, lw=1.8, label=lab)
a.axhline(1, color="#c9ccd1", lw=1, zorder=0)
a.set_xlabel("Daily maximum temperature, C (3 C bins)")
a.set_ylabel("Mean daily shooting cases, relative to city mean")
a.set_title("A  Shootings by temperature (descriptive, bins with 20+ days)", fontsize=10, loc="left")
a.legend(frameon=False, fontsize=8)
# B: IRR forest
b = ax[0, 1]
rows = [("New York, 2006-2026", heat_n["primary"], NYC_C), ("Chicago, 2010-2026", heat_c["primary"], CHI_C),
        ("Chicago 2012-2016", heat_c["sensitivity"]["S6_2012_2016"], CHI_C),
        ("Chicago weekdays (exploratory)", heat_c["sensitivity"]["S9_exploratory_weekday"], CHI_C),
        ("Chicago weekend/holiday (expl.)", heat_c["sensitivity"]["S9_exploratory_weekend_holiday"], CHI_C),
        ("Reeping & Hemenway weekdays", {"estimate": 1.158, "lo": 1.132, "hi": 1.184}, GREY),
        ("Reeping & Hemenway weekends", {"estimate": 1.190, "lo": 1.160, "hi": 1.220}, GREY)]
yy = np.arange(len(rows))[::-1]
b.axvspan(1.110, 1.183, color="#e8f0fb", zorder=0)
b.axvline(1, color="#30343a", lw=0.8)
for y, (lab, r, col) in zip(yy, rows):
    b.errorbar(r["estimate"], y, xerr=[[r["estimate"] - r["lo"]], [r["hi"] - r["estimate"]]], fmt="o", color=col, capsize=3, ms=6, lw=1.8)
    b.text(1.232, y, f"{r['estimate']:.3f}", va="center", fontsize=8, color="#30343a")
b.set_yticks(yy, [r[0] for r in rows], fontsize=8)
b.set_xlim(0.99, 1.26)
b.set_xlabel("Rate ratio per 5 C of TMAX (95% interval)")
b.set_title("B  Same model; shaded = registered band", fontsize=10, loc="left")
# C: weekday index
c = ax[1, 0]
x = np.arange(5)
for src, key, col, ls, lab, off in ((wk_n["primary"], "y2019", NYC_C, "--", "New York CBD 2019", -0.08), (wk_n["primary"], "recent", NYC_C, "-", "New York CBD, Nov 2025-Oct 2026", -0.08),
                                    (wk_c["loop"], "y2019", CHI_C, "--", "Chicago Loop 2019", 0.08), (wk_c["loop"], "recent", CHI_C, "-", "Chicago Loop, Sep 2025-Aug 2026", 0.08)):
    s = src[key]
    y = np.array([s["index"][d] for d in DAYS]) * 100
    lo = np.array([s["index_ci"][d][0] for d in DAYS]) * 100
    hi = np.array([s["index_ci"][d][1] for d in DAYS]) * 100
    c.errorbar(x + off, y, yerr=[y - lo, hi - y], color=col, ls=ls, marker="o", ms=4, lw=1.6, capsize=2, label=lab, alpha=0.55 if key == "y2019" else 1)
c.axhline(100, color="#c9ccd1", lw=1, zorder=0)
c.set_xticks(x, DAYS)
c.set_ylabel("Entries, % of the week's Tue-Thu mean")
c.set_title("C  Entries by weekday: 2019 (dashed) and recent (solid)", fontsize=10, loc="left")
c.legend(frameon=False, fontsize=7, loc="lower center")
# D: delta forest
d = ax[1, 1]
nyc_rest = {"estimate": 4.21, "lo": 2.22, "hi": 6.58}
rows = [("New York CBD", wk_n["primary"]["delta"], NYC_C), ("Chicago Loop", wk_c["loop"]["delta"], CHI_C),
        ("Chicago Loop, no polar-vortex week (expl.)", expl["loop"]["delta"], CHI_C),
        ("New York, rest of system", nyc_rest, NYC_C), ("Chicago, rest of system", wk_c["rest"]["delta"], CHI_C),
        ("Chicago rest, no polar-vortex week (expl.)", expl["rest"]["delta"], CHI_C)]
yy = np.arange(len(rows))[::-1]
d.axvspan(6.5, 10.9, color="#e8f0fb", zorder=0)
d.axvline(0, color="#30343a", lw=0.8)
for y, (lab, r, col) in zip(yy, rows):
    d.errorbar(r["estimate"], y, xerr=[[r["estimate"] - r["lo"]], [r["hi"] - r["estimate"]]], fmt="o", color=col, capsize=3, ms=6, lw=1.8)
    d.text(24.2, y, f"{r['estimate']:.1f}", va="center", fontsize=8, color="#30343a")
d.set_yticks(yy, [r[0] for r in rows], fontsize=8)
d.set_xlim(-1, 26)
d.set_xlabel("Rise in Mon/Fri deficit since 2019, points (95% CI)")
d.set_title("D  Shaded = registered band (6.5 to 10.9)", fontsize=10, loc="left")
for q in ax.ravel():
    q.spines[["top", "right"]].set_visible(False)
fig.text(0.01, 0.005, "NYC: NYPD shooting incidents 5ucz-vwe8, Central Park GHCN-D; MTA hourly ridership (data.ny.gov). Chicago: Violence Reduction victims gumc-mgzr (distinct cases with gunshot injury), "
         "GHCN-D USW00014819; CTA 'L' entries 5neh-572f.\nMonday/Friday panels: weeks with federal holidays or 24 Dec-1 Jan dropped; week-bootstrap intervals. Intervals in B are model-based (robust SE).",
         fontsize=6.5, color="#555")
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(OUT, dpi=200)
plt.close(fig)
im = Image.open(OUT).convert("RGB")
im.save(OUT, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes(), dpi=(200, 200))
print(OUT)
