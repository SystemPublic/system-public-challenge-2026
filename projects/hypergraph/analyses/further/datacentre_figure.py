import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[2]
r = json.load(open(ROOT / "data/derived/further/datacentre_results.json"))
p, s, pl = r["primary"], r["sensitivity"], r["placebos"]
rows = [
 ("Data-centre floor area / reported floor area", p["area_share_pct"], None, p["boot95"]["A"]),
 ("Reported IT-equipment energy (lower bound)", p["L1_over_D1_pct"], p["L1_over_D2_pct"], p["boot95"]["L1"]),
 ("Data-centre area share of building electricity", p["L2_over_D1_pct"], p["L2_over_D2_pct"], None),
 ("Whole buildings, fixed list of 10 carrier hotels", s["list_only"]["U_over_D1_pct"], s["list_only"]["U_over_D2_pct"], None),
 ("Placebo: 10 size-matched offices (D1)", pl["P2_office_matched"]["draw_mean_pct"], None, [pl["P2_office_matched"]["draw_p2.5"], pl["P2_office_matched"]["draw_p97.5"]]),
 ("Whole buildings, list + 165 with any data-centre area\n(registered upper bound, decides verdict)", p["U_over_D1_pct"], p["U_over_D2_pct"], p["boot95"]["U"]),
]
fig, ax = plt.subplots(figsize=(9, 4.8), dpi=200)
ys = list(range(len(rows)))[::-1]
for y, (lab, d1, d2, ci) in zip(ys, rows):
    ax.barh(y + 0.18, d1, height=0.34, color="#2a6f97")
    if ci: ax.plot(ci, [y + 0.18] * 2, color="black", lw=1.2)
    if d2 is not None: ax.barh(y - 0.18, d2, height=0.34, color="#e09f3e")
    ax.text(max(d1, d2 or 0) + 0.3, y, f"{d1:.2f}" + (f" / {d2:.2f}" if d2 is not None else ""), va="center", fontsize=8)
ax.axvline(4.4, color="#9b2226", ls="--", lw=1.2)
ax.text(4.55, len(rows) - 0.45, "4.4% of US electricity, 2023 (LBNL)", color="#9b2226", fontsize=8, va="bottom")
ax.set_yticks(ys); ax.set_yticklabels([x[0] for x in rows], fontsize=8)
ax.set_xlabel("Share of Manhattan electricity, calendar year 2024 (percent)", fontsize=9)
ax.set_xlim(0, 21); ax.spines[["top", "right"]].set_visible(False)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#2a6f97", label="LL84 Manhattan grid electricity (D1)"), Patch(color="#e09f3e", label="Con Edison non-residential, Manhattan ZIPs (D2)")], fontsize=8, loc="upper right", bbox_to_anchor=(1.0, 0.82), frameon=False)
fig.tight_layout()
out = ROOT / "figures/further/datacentre_share_manhattan.png"
fig.savefig(out); plt.close(fig)
im = Image.open(out).convert("RGB")
prof = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
im.save(out, icc_profile=prof, dpi=(200, 200))
