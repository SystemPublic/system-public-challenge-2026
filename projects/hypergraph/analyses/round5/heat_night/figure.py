"""Figure for heat-night-minimum: figures/round5/heat_night_minimum.png (sRGB profile embedded).
Left: rate ratio per 5 C of night minimum on days with TMAX >= 27 C (preceding and following night; all, day and night shootings).
Right: ratio 33 against 27 C of TMAX by six-hour block of the shooting day."""
import io
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[3]
r = json.loads((ROOT / "data/derived/round5/heat_night/results.json").read_text())
FIG = ROOT / "figures/round5"
FIG.mkdir(parents=True, exist_ok=True)
COL = {"new_york": "#1f5fa8", "chicago": "#c8501e"}
LAB = {"new_york": "New York, 2006-2026", "chicago": "Chicago, 2010-2026"}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 4.3), gridspec_kw={"width_ratios": [1.25, 1]})

rows = [("Preceding night, all shootings (registered)", lambda p: p["primary"]),
        ("Preceding night, 06:00-17:59", lambda p: p["secondary"]["n_day_preceding"]),
        ("Preceding night, 18:00-05:59", lambda p: p["secondary"]["n_night_preceding"]),
        ("Following night, all shootings", lambda p: p["secondary"]["following_only"]),
        ("Following night, 06:00-17:59", lambda p: p["secondary"]["n_day_following"]),
        ("Following night, 18:00-05:59", lambda p: p["secondary"]["n_night_following"])]
for i, (lab, get) in enumerate(rows):
    for j, c in enumerate(COL):
        v = get(r[c]["part_a"])
        y = -i + (0.16 if j == 0 else -0.16)
        a.plot([v["lo"], v["hi"]], [y, y], color=COL[c], lw=1.6)
        a.plot(v["estimate"], y, "o", color=COL[c], ms=5, label=LAB[c] if i == 0 else None)
a.axvline(1, color="0.4", lw=0.8)
a.axhline(-2.5, color="0.85", lw=0.8)
a.set_yticks([-i for i in range(len(rows))], [x[0] for x in rows])
a.set_xlabel("Rate ratio per 5 C of night minimum, at fixed daily maximum (95% interval)")
a.set_title("Days with a maximum of 27 C or more", loc="left", fontsize=10)

blocks = ["06-12", "12-18", "18-24", "00-06"]
for j, c in enumerate(COL):
    for i, k in enumerate(blocks):
        v = r[c]["part_b"][f"block_{k}"]
        x = i + (-0.12 if j == 0 else 0.12)
        b.plot([x, x], [v["lo"], v["hi"]], color=COL[c], lw=1.6)
        b.plot(x, v["estimate"], "o", color=COL[c], ms=5)
b.axhline(1, color="0.4", lw=0.8)
b.legend(*a.get_legend_handles_labels(), frameon=False, loc="upper center")
b.set_xticks(range(4), ["06:00-11:59", "12:00-17:59", "18:00-23:59", "00:00-05:59\n(next date)"])
b.set_ylabel("Shootings at 33 C against 27 C of daily maximum")
b.set_title("Hot-day excess by time of day", loc="left", fontsize=10)
fig.text(0.01, 0.005, "Negative binomial models with day of week, month, year, holiday and wet-day terms; HC0 intervals. A shooting day runs from 06:00 to 05:59. "
         "NYPD 5ucz-vwe8, Chicago gumc-mgzr, GHCN-Daily Central Park and Midway.", fontsize=6.5, color="0.35")
fig.tight_layout(rect=(0, 0.03, 1, 1))
buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=200)
buf.seek(0)
im = Image.open(buf).convert("RGB")
im.save(FIG / "heat_night_minimum.png", icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes(), dpi=(200, 200))
print(FIG / "heat_night_minimum.png")
