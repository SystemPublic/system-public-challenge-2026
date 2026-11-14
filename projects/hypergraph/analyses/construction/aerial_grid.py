"""Draw before/after grids of the aerial sample. Mode 'judge' (default) writes label-free sheets (index only) for the
blind visual judgement; mode 'final' writes figures/construction/aerial_grid.png with each pair's judgement and CO status.
The lot outline is drawn in yellow."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageCms, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "construction"
A = D / "aerial"
F = ROOT / "figures" / "construction"
ICC = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
T = 170
try:
    FONT = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
except OSError:
    FONT = ImageFont.load_default()


def tile(i, y):
    im = Image.open(A / f"{i:02d}_{y}.png").convert("RGB")
    m = np.load(A / f"{i:02d}_mask.npy")
    edge = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES)
    e = np.array(edge) > 0
    a = np.array(im); a[e] = (255, 220, 0)
    im = Image.fromarray(a)
    s = T / max(im.size)
    return im.resize((max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s))), Image.LANCZOS)


def sheet(ids, labels, cols, out):
    rows = (len(ids) + cols - 1) // cols
    W, H = cols * (2 * T + 30), rows * (T + 40)
    S = Image.new("RGB", (W, H), (252, 252, 251))
    d = ImageDraw.Draw(S)
    for k, i in enumerate(ids):
        x0, y0 = (k % cols) * (2 * T + 30) + 10, (k // cols) * (T + 40) + 26
        for j, y in enumerate((2017, 2022)):
            t = tile(i, y)
            S.paste(t, (x0 + j * (T + 4), y0))
        d.text((x0, y0 - 20), labels[k], fill=(11, 11, 11), font=FONT)
    S.save(out, icc_profile=ICC, dpi=(150, 150))
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "judge"
    s = pd.read_csv(D / "aerial_sample.csv")
    if mode == "judge":
        ids = list(s.idx)
        for b in range(0, len(ids), 12):
            sheet(ids[b:b + 12], [f"#{i}   2017 | 2022" for i in ids[b:b + 12]], 3, A / f"judge_{b // 12}.png")
    else:
        j = pd.read_csv(D / "aerial_scored.csv")
        j = j.sort_values(["judgement", "has_co_by_2022", "idx"], ascending=[True, False, True])
        lab = [f"#{r.idx} {r.judgement}; CO by image: {'yes' if r.has_co_by_2022 else 'no'}; now: {'yes' if r.has_co_now else 'no'}" for r in j.itertuples()]
        sheet(list(j.idx), lab, 4, F / "aerial_grid.png")
