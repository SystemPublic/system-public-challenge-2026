#!/usr/bin/env python
"""Figure for the round-2 heat confounders study: slope by adjustment set, both claims."""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
R = json.loads((ROOT / "data/derived/round2/heat_confounders/results.json").read_text())
OUT = ROOT / "figures/round2/heat_confounders.png"

A = [("Analyst set: poverty, percent Black", R["A_cd"]["primary"]["original"], "#555555"),
     ("+ population density", R["A_cd"]["popdens_only"]["graph_set"], "#9a9a9a"),
     ("+ built-up share", R["A_cd"]["built_only"]["graph_set"], "#9a9a9a"),
     ("+ road share", R["A_cd"]["road_only"]["graph_set"], "#9a9a9a"),
     ("Graph set: all three (registered)", R["A_cd"]["primary"]["graph_set"], "#1f5fa8"),
     ("NTA, analyst set (n = 194)", R["A_nta"]["primary"]["original"], "#555555"),
     ("NTA, graph set", R["A_nta"]["primary"]["graph_set"], "#1f5fa8")]
B = [("Analyst set: poverty, percent Black, AC", R["B_cd"]["primary"]["original"], "#555555"),
     ("Graph set: + older adults living alone (registered)", R["B_cd"]["primary"]["graph_set"], "#1f5fa8"),
     ("+ density, built-up and road share only", R["B_cd"]["built_form_only"]["graph_set"], "#9a9a9a"),
     ("+ living alone and the three built-form measures", R["B_cd"]["plus_built_form"]["graph_set"], "#9a9a9a")]

fig, axes = plt.subplots(2, 1, figsize=(8.6, 6.6), gridspec_kw={"height_ratios": [7, 4]})
for ax, rows, title, xl in ((axes[0], A, "Street trees and surface temperature, 55 districts",
                             "F of surface temperature per SD of log street trees per km$^2$ (95% interval)"),
                            (axes[1], B, "Surface temperature and heat ED visits, 54 districts",
                             "Percent change in heat ED rate per 1 F of surface temperature (95% interval)")):
    for i, (lab, e, col) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.plot([e["lo"], e["hi"]], [y, y], color=col, lw=2.2, solid_capstyle="round")
        ax.plot(e["estimate"], y, "o", color=col, ms=7)
        ax.text(1.01, y, f"{e['estimate']:+.2f} ({e['lo']:+.2f} to {e['hi']:+.2f})" if ax is axes[0] else
                f"{e['estimate']:+.1f} ({e['lo']:+.1f} to {e['hi']:+.1f})", transform=ax.get_yaxis_transform(), va="center", fontsize=8.5)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=9)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel(xl, fontsize=9)
    ax.set_title(title, fontsize=10.5, loc="left")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#e6e6e6", lw=0.6)
    ax.set_axisbelow(True)
axes[0].axhline(1.5, color="#cccccc", lw=0.6, ls="--")
fig.text(0.01, 0.005, "Blue: registered graph-derived adjustment set. Dark grey: the analyst's original set. Light grey: secondary models, not deciding. "
         "Research direction is negative in the upper panel and positive in the lower.", fontsize=7.5, color="#444444", wrap=True)
fig.tight_layout(rect=(0, 0.03, 0.86, 1))
fig.savefig(OUT, dpi=200, facecolor="white")
subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(OUT)], check=False, capture_output=True)
print(OUT.relative_to(ROOT))
