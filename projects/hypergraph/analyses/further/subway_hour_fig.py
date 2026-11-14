import json, io
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageCms
R = Path(__file__).resolve().parents[2]
o = json.loads((R / "data/derived/further_subway/results.json").read_text())["primary"]
bands = ["0-5", "5-10", "10-16", "16-20", "20-24"]
fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=200)
for i, (p, lab, col, dx) in enumerate([("2019", "2019", "#7a7a7a", -0.09), ("L12", "Oct 2025 to Sep 2026", "#b3261e", 0.09)]):
    xs = [j + dx for j in range(5)]
    v = [o["rates"][f"{p}|{b}"] for b in bands]
    ax.errorbar(xs, [x["rate"] for x in v], yerr=[[x["rate"] - x["lo"] for x in v], [x["hi"] - x["rate"] for x in v]],
                fmt="o", color=col, capsize=3, label=lab, ms=6)
ax.set_yscale("log")
ax.set_xticks(range(5)); ax.set_xticklabels([f"{b.split('-')[0]}:00 to {b.split('-')[1]}:00" for b in bands])
ax.set_ylabel("Felony complaints per million entries (log)")
ax.set_xlabel("Hour of occurrence")
ax.set_title("Subway major felonies per million entries by hour band, 95% Poisson intervals", fontsize=10)
ax.grid(axis="y", alpha=.3); ax.legend(frameon=False)
fig.text(0.01, 0.005, "Source: NYPD complaints qgea-i56i, 5uac-w243 (subway premise, 7 felony types); MTA hourly ridership t69i-h2me, 5wq4-mkjj. Entries, not riders present.", fontsize=6)
fig.tight_layout(rect=(0, 0.02, 1, 1))
buf = io.BytesIO(); fig.savefig(buf, format="png"); buf.seek(0)
im = Image.open(buf).convert("RGB")
icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
im.save(R / "figures/further/subway_crime_per_ride_by_hour.png", icc_profile=icc, dpi=(200, 200))
