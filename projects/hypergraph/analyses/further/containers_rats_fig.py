import json
from pathlib import Path
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageCms
ROOT = Path(__file__).resolve().parents[2]; D = ROOT/"data/derived/further"
ev = pd.read_csv(D/"event_series.csv", index_col=0); ev.index = pd.PeriodIndex(ev.index, freq="M"); ev = ev[ev.index <= "2026-10"]
res = json.load(open(D/"results.json"))
base = ev.loc["2024-06":"2025-05"].mean()
ix = (ev[["cd9","cmp"]]/base*100).rolling(3, center=True).mean()
fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw=dict(width_ratios=[1.35, 1]))
x = ix.index.to_timestamp()
a.plot(x, ix.cd9, color="#b3402a", lw=2, label="Manhattan CD9")
a.plot(x, ix.cmp, color="#4a5f7a", lw=2, label="CD7, 10, 11, 12 pooled")
a.axvline(pd.Timestamp("2025-06-01"), color="k", ls="--", lw=1); a.text(pd.Timestamp("2025-06-15"), a.get_ylim()[1]*0.97, "full service\n2 Jun 2025", va="top", fontsize=8)
a.axvline(pd.Timestamp("2024-11-12"), color="grey", ls=":", lw=1); a.text(pd.Timestamp("2024-11-20"), a.get_ylim()[0]+4, "citywide 1-9 unit rule", fontsize=7, color="grey")
a.set_ylabel("311 rat sightings per month\n(3-month mean, Jun 2024-May 2025 mean = 100)"); a.legend(frameon=False, fontsize=8, loc="upper left"); a.set_title("311 'Rat Sighting' counts", fontsize=10)
rows = [("Primary (Jun25-May26)", "primary"), ("Placebo year", "placebo_year"), ("6 months", "w6"), ("17 months", "w17"), ("All other Manhattan", "all_manhattan"),
        ("Leave out CD7", "loo_07"), ("Leave out CD10", "loo_10"), ("Leave out CD11", "loo_11"), ("Leave out CD12", "loo_12"), ("Noise - Residential (placebo type)", "placebo_noise")]
for i, (lab, k) in enumerate(rows[::-1]):
    r = res[k]; b.plot([r["lo"], r["hi"]], [i, i], color="#b3402a" if k == "primary" else "#555", lw=2); b.plot(r["R"], i, "o", color="#b3402a" if k == "primary" else "#555")
b.set_yticks(range(len(rows))); b.set_yticklabels([r[0] for r in rows[::-1]], fontsize=8); b.axvline(1, color="k", lw=1)
b.set_xlabel("CD9 vs comparison, rate ratio (95% CI)"); b.set_title("Difference in differences", fontsize=10)
fig.tight_layout(); out = ROOT/"figures/further/containers_rats_cd9.png"; fig.savefig(out, dpi=200)
im = Image.open(out).convert("RGB"); im.save(out, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes(), dpi=(200, 200))
