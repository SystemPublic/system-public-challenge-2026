"""Figure: agreement with the literature's sign by kind of pair, New York and Chicago side by side."""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
R = json.loads((ROOT / "data" / "derived" / "round5" / "chicago_matrix" / "results.json").read_text())
GROUPS = [("air, traffic or noise with anything", "Air pollution or traffic\nwith a health outcome"),
          ("behaviour with anything else", "A behaviour\nwith anything else"),
          ("health outcome with health outcome", "Two health\noutcomes"),
          ("social or housing condition with anything else", "A social or housing\ncondition with anything else"),
          ("all", "All qualifying\npairs")]
SERIES = [("new_york_same_pairs", "New York, 42 UHF neighbourhoods (the same pairs)", "#8a8a8a"),
          ("chicago", "Chicago, 77 community areas", "#2f6fb0")]
fig, ax = plt.subplots(figsize=(10.5, 5.2))
w = 0.36
for i, (key, lab, col) in enumerate(SERIES):
    for j, (g, _) in enumerate(GROUPS):
        v = R[key]["groups"][g]
        x = j + (i - 0.5) * w
        lo, hi = v["agreement_ci95"]
        ax.bar(x, v["agreement"], w * 0.92, color=col, label=lab if j == 0 else None, zorder=2)
        ax.plot([x, x], [lo, hi], color="#222222", lw=1.1, zorder=3)
        ax.text(x, 1.03, f"{v['agree']} of {v['n']}", ha="center", va="bottom", fontsize=8.5, color="#222222")
ax.axhline(0.5, color="#555555", lw=0.8, ls=(0, (4, 3)), zorder=1)
ax.text(-0.48, 0.505, "chance", fontsize=8, color="#555555", va="bottom", ha="left")
ax.set_xticks(range(len(GROUPS)))
ax.set_xticklabels([l for _, l in GROUPS], fontsize=9)
ax.set_ylim(0, 1.12)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=9)
ax.set_ylabel("Pairs whose correlation across areas has the\nliterature's sign (poverty partialled out)", fontsize=9)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.tick_params(axis="x", length=0)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, frameon=False, fontsize=9)
ax.set_title("Agreement between neighbourhood correlations and the System Public Graph, by kind of pair\n"
             "75 indicator pairs that qualify in both cities; lines are 95% bootstrap intervals over areas", fontsize=10.5, loc="left")
out = ROOT / "figures" / "round5" / "chicago_matrix_by_kind.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(out)], check=True, capture_output=True)
print(out)
