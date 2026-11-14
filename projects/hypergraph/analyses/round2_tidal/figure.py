import json
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageCms
ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "round2" / "tidal_trend"
r = json.load(open(D / "results.json"))
BL, OR, GR = "#1f5fa8", "#c4600c", "#6b6b6b"
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1.05, 1]})
a = ax[0]
labs = ["< 0.30", "0.30-0.35", "0.35-0.40", "0.40-0.45", ">= 0.45"]
x = np.arange(5)
for g, c, off, lab in (("tidal", BL, -0.12, "Coastal ZIP set (8 ZIPs)"), ("placebo", GR, 0.12, "All other ZIPs")):
    b = r[f"bands_{g}"]
    est = [1.0] + [b[f"band{i}"]["rr"] for i in range(1, 5)]
    lo = [1.0] + [b[f"band{i}"]["lo"] for i in range(1, 5)]; hi = [1.0] + [b[f"band{i}"]["hi"] for i in range(1, 5)]
    a.errorbar(x + off, est, yerr=[np.array(est) - lo, np.array(hi) - est], fmt="o", color=c, capsize=3, label=lab)
    a.plot(x + off, est, color=c, lw=1)
a.set_xticks(x); a.set_xticklabels(labs); a.axhline(1, color="k", lw=0.5)
a.set_yscale("log"); a.set_yticks([1, 1.5, 2, 3, 4]); a.set_yticklabels(["1", "1.5", "2", "3", "4"])
a.set_xlabel("Battery daily maximum, m above MHHW (dry days, 2010-2019)")
a.set_ylabel("Rate ratio vs. below 0.30 m")
n = r["days_by_band"]
a.set_title("Street-flooding and catch-basin complaints\nrise with the tide (days: " + ", ".join(str(n[k]) for k in ("0", "1", "2", "3", "4")) + ")", fontsize=10)
a.legend(frameon=False, fontsize=9, loc="upper left")
p = r["primary"]
a.text(0.03, 0.80, f"Hinge above 0.35 m, per 10 cm:\ncoastal {p['tidal']['rr']:.2f} ({p['tidal']['lo']:.2f} to {p['tidal']['hi']:.2f})\nother {p['placebo']['rr']:.2f} ({p['placebo']['lo']:.2f} to {p['placebo']['hi']:.2f})",
       transform=a.transAxes, ha="left", va="top", fontsize=8.5)
b = ax[1]
p2 = r["part2a"]; yrs = np.arange(2010, 2026); N = np.array([p2["N_by_year"][str(y)] for y in yrs])
b.bar(yrs, N, color="#9fbfe0", width=0.8, label="Dry days with maximum >= 0.35 m")
o = p2["ols"]; mean_y = N.mean(); fit = mean_y + o["slope"] * (yrs - yrs.mean())
b.plot(yrs, fit, color=BL, lw=2, label=f"OLS slope {o['slope']:.2f} (95% {o['lo']:.2f} to {o['hi']:.2f}) days/yr/yr")
b.plot(yrs, mean_y + p2["implied"] * (yrs - yrs.mean()), color=OR, lw=2, ls="--", label=f"Implied by 2.95 mm/yr: {p2['implied']:.2f}")
b.set_xlabel("Year"); b.set_ylabel("Days per year"); b.set_title("Tide days above the knot, 2010-2025", fontsize=10)
b.legend(frameon=False, fontsize=8, loc="upper left")
for s in ("top", "right"):
    a.spines[s].set_visible(False); b.spines[s].set_visible(False)
fig.tight_layout()
out = ROOT / "figures" / "round2" / "further-tidal-flooding-trend.png"; out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=200); plt.close(fig)
im = Image.open(out).convert("RGB")
im.save(out, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes(), dpi=(200, 200))
print(out)
