"""Figure for transfer-chicago-hot-end: the two cities' curves side by side, registered basis.
Reads data/derived/round2/hot_end/curves.csv (Chicago) and refits New York from
data/derived/graph/heat_mechanisms/mediators_daily.csv; writes ny_curves.csv and
figures/round2/hot_end_two_cities.png (sRGB profile embedded)."""
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import pandas as pd
from PIL import Image, ImageCms

from analyses.round2.hot_end import model as M

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data" / "derived" / "round2" / "hot_end"
FIG = ROOT / "figures" / "round2"
FIG.mkdir(parents=True, exist_ok=True)
M.SPLINE = "lin"

ny0 = pd.read_csv(ROOT / "data/derived/graph/heat_mechanisms/mediators_daily.csv", index_col=0, parse_dates=True).dropna(subset=["TMAX"])
rows = []
for y, sub in (("n", ny0), ("noise_street", ny0.dropna(subset=["noise_street"])), ("bike", ny0.dropna(subset=["bike"]))):
    _, c = M.curve_fit(sub, y, M.nb_alpha(y, sub, 0.1))
    rows.append(c.assign(series=y))
ny = pd.concat(rows)
ny.to_csv(D / "ny_curves.csv", index=False)
ch = pd.read_csv(D / "curves.csv")
ch = ch[ch.basis == "lin"]

RED, BLUE, TEAL = "#b3261e", "#1f5fa8", "#2a8f83"
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), sharey=True)
panels = (
    (axes[0], ny, "New York (exploratory)",
     (("n", "Shooting incidents, 2006 to 2026", RED, "-"), ("noise_street", "311 street-noise complaints, 2010 to 2026", BLUE, "-"), ("bike", "Bicycle counts, 2014 to 2026", TEAL, "--"))),
    (axes[1], ch, "Chicago (registered test)",
     (("shootings_full", "Gunshot-injury cases, 2010 to 2026", RED, "-"), ("customer", "Divvy casual trips, 2013 to 2019", BLUE, "-"),
      ("trips", "Divvy trips, all riders, 2013 to 2019", TEAL, "--"))),
)
for ax, df, title, series in panels:
    ax.axvspan(27, 33, color="#000000", alpha=0.06, lw=0)
    ax.axhline(1, color="#888888", lw=0.6)
    for key, lab, col, ls in series:
        s = df[(df.series == key) & (df.tmax_c >= 3) & (df.tmax_c <= 35)]
        ax.fill_between(s.tmax_c, s.lo, s.hi, color=col, alpha=0.15, lw=0)
        ax.plot(s.tmax_c, s.rr, color=col, lw=2, ls=ls, label=lab)
    ax.set_yscale("log")
    ax.set_yticks([0.25, 0.5, 1, 2, 4])
    ax.set_yticklabels(["0.25", "0.5", "1", "2", "4"])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_ylim(0.2, 4.5)
    ax.set_xlim(3, 35)
    ax.set_xticks([3, 9, 15, 21, 27, 33])
    ax.set_xlabel("Daily maximum temperature (C)")
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    ax.text(30, 0.215, "27 to 33 C", ha="center", va="bottom", fontsize=8.5, color="#444444")
axes[0].set_ylabel("Daily count relative to a 15 C day (log scale)")
fig.suptitle("Above 27 C the outdoor proxies stop rising and shootings do not", x=0.01, ha="left", fontsize=13)
fig.text(0.01, 0.005, "Negative binomial models with day of week, month, year, holiday and wet-day terms; temperature as a piecewise-linear spline with knots at 15, 21 and 27 C. Bands are 95% intervals.",
         fontsize=7.5, color="#444444")
fig.tight_layout(rect=(0, 0.03, 1, 0.95))
buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=200)
buf.seek(0)
im = Image.open(buf).convert("RGB")
im.save(FIG / "hot_end_two_cities.png", icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes(), dpi=(200, 200))
