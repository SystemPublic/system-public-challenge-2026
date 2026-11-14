"""Figure for repro-dcp-2025-completions: relative difference between DCP's stated numbers
and the numbers recomputed from br6q-ssj3 (26Q2.1), with the registered 2% and 4% bands."""
import json, subprocess
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
r = json.loads((ROOT / "data/derived/reproduction/dcp_2025_results.json").read_text())
b = r["boro_R1"]
stated_man = 38682 - 18048 - 9600 - 5683 - 477
rows = [  # label, stated, reproduced, registered role
 ("Citywide, R1 classaprop (primary)", 38682, r["readings"]["R1"]),
 ("Citywide, R3 final CO only", 38682, r["readings"]["R3"]),
 ("Citywide, R2 units_co", 38682, r["readings"]["R2"]),
 ("Brooklyn, R1", 18048, b["3"]),
 ("Queens, R1", 9600, b["4"]),
 ("Bronx, R1", 5683, b["2"]),
 ("Manhattan, R1 (stated by subtraction)", stated_man, b["1"]),
 ("Staten Island, R1", 477, b["5"]),
 ("Permit units 2025, P1 (excl. withdrawn)", 17673, r["P1"]),
]
fig, ax = plt.subplots(figsize=(8, 4.6), dpi=200)
fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")
ax.axvspan(-4, 4, color="#e6e5e0", zorder=0)
ax.axvspan(-2, 2, color="#d3d2cc", zorder=0)
ax.axvline(0, color="#52514e", lw=0.8, zorder=1)
for i, (lab, s, v) in enumerate(rows):
    d = 100 * (v - s) / s
    y = len(rows) - 1 - i
    ax.plot([0, d], [y, y], color="#86b6ef", lw=2, zorder=2)
    ax.scatter([d], [y], s=50, color="#2a78d6", edgecolor="#fcfcfb", linewidth=1.5, zorder=3)
    ax.text(d + (0.25 if d >= 0 else -0.25), y, f"{int(v):,} vs {s:,}", va="center",
            ha="left" if d >= 0 else "right", fontsize=7.5, color="#0b0b0b")
ax.set_yticks(range(len(rows))); ax.set_yticklabels([x[0] for x in rows][::-1], fontsize=8, color="#0b0b0b")
ax.set_xlim(-6, 9)
ax.set_xlabel("Reproduced minus stated, percent of stated (bands: registered 2% and 4%)", fontsize=8, color="#52514e")
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.tick_params(axis="x", labelsize=8, colors="#52514e"); ax.tick_params(axis="y", length=0)
ax.set_title("DCP Housing Production Snapshot 2025, units in new buildings,\nrecomputed from the Housing Database 26Q2.1 (br6q-ssj3)",
             fontsize=9.5, loc="left", color="#0b0b0b")
fig.text(0.01, 0.01, "Source: NYC Open Data br6q-ssj3, rowsUpdatedAt 2026-09-30, fetched 12 Nov 2026. Stated values: DCP snapshot (StoryMap, March 2026).",
         fontsize=6.5, color="#52514e")
fig.tight_layout(rect=(0, 0.03, 1, 1))
out = ROOT / "figures/reproduction/dcp_2025_completions.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, facecolor=fig.get_facecolor())
subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(out)], capture_output=True)
print(out)
