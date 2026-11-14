import json
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageCms
ROOT = Path(__file__).resolve().parents[2]; D = ROOT / "data/derived/further_tidal"
r = json.load(open(D / "results.json")); d = pd.read_csv(D / "daily_panel.csv", index_col=0, parse_dates=True)
rf = d[d.rf1 & d.E1.notna()]
fig, ax = plt.subplots(1, 2, figsize=(11, 5.2), gridspec_kw={"width_ratios": [1, 1.25]})
a = ax[0]
below = rf[rf.E1 == 0]; above = rf[rf.E1 == 1]
a.scatter(below.H, below.C1_t + np.random.default_rng(1).uniform(-.12, .12, len(below)), s=8, color="#9aa7b4", alpha=.5, label="rain-free days below the minor-flood level")
a.scatter(above.H, above.C1_t + np.random.default_rng(2).uniform(-.12, .12, len(above)), s=26, color="#b3261e", label="rain-free days at or above it (20)")
a.axvline(2.104, color="#444", lw=.8, ls="--")
a.set_xlabel("Daily maximum water level at the Battery (m above MLLW)"); a.set_ylabel("Street-flooding complaints that day, tidal ZIP set")
a.set_title("A. Complaints against tide, rain-free days 2020 to Oct 2026", fontsize=10, loc="left"); a.legend(fontsize=7.5, frameon=False, loc="upper left")
b = ax[1]
rows = [("Tide, tidal ZIPs (primary)", "primary_E1", "tidal", "#b3261e"), ("Tide, other ZIPs (placebo set)", "primary_E1", "placebo", "#5b6770"),
        ("Tidal / other ZIPs", "primary_E1", "ratio", "#222"),
        ("Tide shifted +7 d, tidal ZIPs", "placebo_shift7", "tidal", "#8a8f94"), ("Tide shifted +100 d, tidal ZIPs", "placebo_shift100", "tidal", "#8a8f94"),
        ("Continuous, per 10 cm, tidal ZIPs", "check_E2_continuous_per10cm", "tidal", "#b3261e"), ("Lagged one day, tidal ZIPs", "check_E1_lag1", "tidal", "#b3261e"),
        ("Adding catch basin and sewer backup, tidal", "check_other_complaint_set_C2", "tidal", "#b3261e"), ("Broader tidal ZIP set", "check_broad_zip_set", "tidal", "#b3261e"),
        ("Rain under 0.1 mm", "check_rain_under_0.1mm", "tidal", "#b3261e"), ("Poisson", "check_poisson", "tidal", "#b3261e"),
        ("Rainy days (10 mm or more), tide, tidal", "check_rainy_days_E1", "tidal", "#8a8f94")]
for i, (lab, k, g, c) in enumerate(rows[::-1]):
    v = r[k][g]; b.errorbar(v["rr"], i, xerr=[[v["rr"] - max(v["lo"], 1e-2)], [v["hi"] - v["rr"]]], fmt="o", color=c, capsize=2, ms=5)
b.set_yticks(range(len(rows))); b.set_yticklabels([x[0] for x in rows[::-1]], fontsize=8); b.set_xscale("log"); b.axvline(1, color="#444", lw=.8)
b.set_xlabel("Rate ratio and 95% block-bootstrap interval (log scale)")
b.set_title("B. Rate ratios (20 flood days; registered minimum 30)", fontsize=10, loc="left")
for s in ("top", "right"): a.spines[s].set_visible(False); b.spines[s].set_visible(False)
fig.tight_layout()
out = ROOT / "figures/further/further-tidal-flooding-311.png"
fig.savefig(out, dpi=200); plt.close(fig)
im = Image.open(out).convert("RGB"); icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
im.save(out, icc_profile=icc, dpi=(200, 200)); print(out)
