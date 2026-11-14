import json, io
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageCms
ROOT = Path(__file__).resolve().parents[3]
r = json.load(open(ROOT / "data/derived/round2/datacentre_v2/results.json"))
P = r["primary"]
rows = [("D1  LL84 benchmarked\n(17.1 TWh)", P["S_lo_over_D1_pct"], P["S_hi_over_D1_pct"]),
        ("D2  Con Edison non-residential\n(16.0 TWh)", P["S_lo_over_D2_pct"], P["S_hi_over_D2_pct"]),
        ("D3  Zone J x Manhattan share\n(22.6 TWh)", P["S_lo_over_D3_pct"], P["S_hi_over_D3_pct"])]
col = "#1f5f8b"
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1, 1]})
for a, xmax, title in ((ax[0], 30, "Whole scale"), (ax[1], 5, "Zoom, 0 to 5 percent")):
    for i, (lab, lo, hi) in enumerate(rows):
        y = len(rows) - 1 - i
        a.barh(y, hi - lo, left=lo, height=0.45, color=col)
        if xmax == 5:
            a.text(hi + 0.08, y, f"{lo:.1f} to {hi:.1f}", va="center", fontsize=9)
    a.axvline(4.4, color="#b34a00", lw=1.5, ls="--")
    if xmax == 30:
        a.axvline(25, color="#6b3a8c", lw=1.5, ls="--")
        a.text(4.7, 2.62, "US 2023\n4.4", color="#b34a00", fontsize=8, va="top")
        a.text(24.6, 2.62, "Virginia 2023\n(about a quarter)", color="#6b3a8c", fontsize=8, ha="right", va="top")
    else:
        a.text(4.5, 2.62, "US 2023 4.4", color="#b34a00", fontsize=8, va="top")
    a.set_xlim(0, xmax); a.set_ylim(-0.6, 2.7); a.set_title(title, fontsize=10, loc="left")
    a.set_xlabel("Percent of denominator")
    a.set_yticks(range(len(rows))); a.set_yticklabels([x[0] for x in rows][::-1] if xmax == 30 else [""] * 3, fontsize=8)
    for s in ("top", "right"): a.spines[s].set_visible(False)
fig.suptitle("Allocated data-centre electricity in Manhattan: low figure (IT x PUE 1.4) to high figure (IT x 2.0 or carrier-hotel excess)", fontsize=10, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.94))
buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=200); buf.seek(0)
im = Image.open(buf).convert("RGB")
icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
out = ROOT / "figures/round2/datacentre_share_v2.png"
im.save(out, icc_profile=icc, dpi=(200, 200)); print(out)
