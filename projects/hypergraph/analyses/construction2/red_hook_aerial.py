"""NAIP aerial crops of Brooklyn block 555 for every available year, with the DOF tax-lot outlines of lot 124
(348 Van Brunt St, the inferred lot) and lot 27 (100 Sullivan St, the alternative). Uses the aerial-imagery skill's
dtk.aerial.fetch (cached under diagrams/aerial/). Writes figures/construction2/red_hook_aerial_grid.png and
data/derived/construction2/red_hook/aerial_meta.json."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "diagrams"))
from concord import socrata as so
from dtk import aerial

CROP = dict(south=40.67788, west=-74.01295, north=40.67880, east=-74.01175)  # both lots with about 25 m around
BOX = dict(south=40.6771, west=-74.0143, north=40.6797, east=-74.0107)
OUT = ROOT / "data/derived/construction2/red_hook"
FIG = ROOT / "figures/construction2"


def years():
    import planetary_computer, pystac_client
    cat = pystac_client.Client.open(aerial.STAC_URL, modifier=planetary_computer.sign_inplace)
    it = list(cat.search(collections=["naip"], bbox=[BOX["west"], BOX["south"], BOX["east"], BOX["north"]]).items())
    return sorted({int(i.properties.get("naip:year") or i.datetime.year) for i in it})


rows, src = so.query("i38t-6if2", select="bbl,the_geom", where="bbl in ('3005550124','3005550027')")
geoms = {r["bbl"]: r["the_geom"] for r in rows}
meta = {"lot_polygons_source": src, "years": {}}
tiles = []
for y in years():
    a = aerial.fetch(f"nyc-redhook-block555-{y}", **BOX, year=y)
    m = a.meta
    meta["years"][y] = {k: m[k] for k in ("years_used", "dates", "items", "credit")} | {"m_per_px": a.m_per_px()}
    if m["years_used"] != [y]:
        print("skip", y, m["years_used"]); continue
    im = Image.open(a.png).convert("RGB")
    x0, y0 = a.to_px(CROP["north"], CROP["west"]); x1, y1 = a.to_px(CROP["south"], CROP["east"])
    off = np.array([x0, y0])
    im = im.crop((round(x0), round(y0), round(x1), round(y1)))
    W = 360
    sc = W / im.width
    im = im.resize((W, round(im.height * sc)), Image.BICUBIC)
    dr = ImageDraw.Draw(im)
    for bbl, col, dash in (("3005550124", (255, 215, 0), False), ("3005550027", (0, 220, 255), False)):
        g = geoms.get(bbl)
        if not g:
            continue
        rings = g["coordinates"] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
        for ring in rings[:1] if g["type"] == "Polygon" else rings:
            pts = [tuple((np.array(a.to_px(lat, lon)) - off) * sc) for lon, lat in ring]
            if dash:
                for i in range(0, len(pts) - 1):
                    dr.line([pts[i], pts[i + 1]], fill=col, width=2)
            else:
                dr.line(pts, fill=col, width=2)
    tiles.append((y, im, m["dates"]))
    print(y, m["dates"], round(a.m_per_px(), 2))

# grid
cols = 4
H = max(t[1].height for t in tiles)
lab = 30
rows_n = (len(tiles) + cols - 1) // cols
grid = Image.new("RGB", (cols * 370 + 10, rows_n * (H + lab + 10) + 50), "white")
d = ImageDraw.Draw(grid)
try:
    f = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
    fs = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 11)
except OSError:
    f = fs = ImageFont.load_default()
for k, (y, im, dates) in enumerate(tiles):
    x0, y0 = 10 + (k % cols) * 370, 10 + (k // cols) * (H + lab + 10)
    d.text((x0, y0), f"{y}  ({dates[0] if dates else ''})", fill="black", font=f)
    grid.paste(im, (x0, y0 + lab - 6))
d.text((10, grid.height - 38), "Yellow: lot 124 (348 Van Brunt St, inferred site of the photograph). Cyan: lot 27 (100 Sullivan St, the alternative). "
       "Lot outlines: DOF tax-lot polygons (i38t-6if2). Each crop is about 100 m across.", fill="black", font=fs)
d.text((10, grid.height - 22), "Aerial imagery: USDA Farm Service Agency, National Agriculture Imagery Program (NAIP), "
       + ", ".join(str(t[0]) for t in tiles) + ". North is up.", fill="black", font=fs)
icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
grid.save(FIG / "red_hook_aerial_grid.png", icc_profile=icc)
for y, im, _ in tiles:
    im.save(OUT / f"aerial_{y}.png", icc_profile=icc)
(OUT / "aerial_meta.json").write_text(json.dumps(meta, indent=1, default=str))
print("ok")
