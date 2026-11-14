"""Figure for docs/heat_extremes.md: dose-response curves by city (small multiples).

Run: ~/.venvs/nyc-concordance/bin/python -m analyses.heat_extremes.figure
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from analyses.heat.common import tag_srgb
from analyses.heat_extremes import model as m

FIG = m.ROOT / "figures" / "heat_extremes"
ORDER = ["phoenix", "tucson", "austin", "dallas", "los_angeles", "philadelphia", "chicago", "new_york"]
INK, MUTED, BLUE, GREY = "#1f2328", "#6b7280", "#2563a8", "#9aa1ab"


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    cv = pd.read_csv(m.DER / "curves.csv")
    cv = cv[cv.mean_tmax >= 6]
    pooled = cv[cv.city == "pooled_hot4"].sort_values("mean_tmax")
    ref = pd.DataFrame({"mean_tmax": [21.5], "estimate": [1.0]})
    pooled = pd.concat([pooled, ref]).sort_values("mean_tmax")
    plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 9, "axes.edgecolor": "#c9ced6", "axes.linewidth": 0.8})
    fig, axes = plt.subplots(2, 4, figsize=(11, 5.6), sharex=True, sharey=True)
    for ax, c in zip(axes.ravel(), ORDER):
        g = cv[cv.city == c].sort_values("mean_tmax")
        ax.axhline(1, color="#c9ced6", lw=0.8, zorder=0)
        ax.axvspan(38, 49, color="#f1f3f5", zorder=0)
        ax.plot(pooled.mean_tmax, pooled.estimate, color=GREY, lw=1.2, ls=(0, (3, 2)), zorder=1)
        ax.fill_between(g.mean_tmax, g.lo, g.hi, color=BLUE, alpha=0.16, lw=0, zorder=2)
        ax.plot(g.mean_tmax, g.estimate, color=BLUE, lw=2, marker="o", ms=3.5, zorder=3)
        last = g.iloc[-1]
        ax.set_title(f"{m.LABEL[c]}", loc="left", color=INK, fontsize=10, fontweight="bold", pad=4)
        ax.text(0.03, 0.93, f"hottest bin: {last.estimate:.2f} ({last.lo:.2f} to {last.hi:.2f})\n{int(last.days)} days at {last.bin.strip('[)').replace(', inf', ' C and above').replace(', ', ' to ')}"
                + ("" if "inf" in last.bin else " C"), transform=ax.transAxes, va="top", fontsize=7.5, color=MUTED)
        ax.set_ylim(0.72, 1.36)
        ax.set_xlim(5, 48)
        ax.set_xticks([10, 20, 30, 38, 45])
        ax.tick_params(colors=MUTED, length=2)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    for ax in axes[1]:
        ax.set_xlabel("Daily maximum temperature (C)", color=MUTED)
    for ax in axes[:, 0]:
        ax.set_ylabel("Rate ratio against 20 to 23 C", color=MUTED)
    fig.suptitle("Aggravated assaults by daily maximum temperature: the rise stops near 35 C and does not reverse", x=0.012, ha="left", fontsize=11.5, color=INK, fontweight="bold")
    fig.text(0.012, 0.925, "Blue: the city's curve with 95% interval, adjusted for year, month, weekday, holidays, first of month and rain. Dashed grey: the four hot cities pooled. "
             "Shaded: 38 C and above. Bins with under 20 days are not drawn.", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    out = FIG / "dose_response_by_city.png"
    fig.savefig(out, dpi=200, facecolor="white")
    tag_srgb(out)
    print(out)


if __name__ == "__main__":
    main()
