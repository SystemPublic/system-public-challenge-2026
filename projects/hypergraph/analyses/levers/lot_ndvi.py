"""NDVI inside each sampled vacant lot from NAIP 2022 (New York flight, four bands, 0.6 m), read by window from the
Planetary Computer. Usage: lot_ndvi.py <input csv with bbl column> <output csv> [chips_dir n_chips]

For each lot the MapPLUTO polygon (lot_polygons.py) is the mask; pixels whose centre lies inside it are used.
Output per lot: n pixels, median NDVI, share of pixels with NDVI >= 0.2 (vegetated share), mean brightness of RGB.
"""
from __future__ import annotations

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
POLY = Path.home() / "opt" / "nyc-concordance" / "levers" / "lu11_polygons.geojson"
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
YEAR = 2022
_local = threading.local()


def items():
    import planetary_computer
    import pystac_client
    cat = pystac_client.Client.open(STAC, modifier=planetary_computer.sign_inplace)
    its = list(cat.search(collections=["naip"], bbox=[-74.26, 40.49, -73.69, 40.92],
                          query={"naip:year": {"eq": str(YEAR)}}).items())
    its = [i for i in its if i.properties.get("naip:state") == "ny"]
    return its


def open_ds(href):
    import rasterio
    cache = getattr(_local, "ds", None)
    if cache is None:
        cache = _local.ds = {}
    if href not in cache:
        cache[href] = rasterio.open(href)
    return cache[href]


def measure(geom, its, chip_path=None):
    import rasterio.features
    from rasterio.windows import from_bounds
    from shapely.geometry import shape, mapping
    from shapely.ops import transform as stransform
    from pyproj import Transformer
    g = shape(geom)
    c = g.centroid
    for it in its:
        b = it.bbox
        if not (b[0] <= c.x <= b[2] and b[1] <= c.y <= b[3]):
            continue
        ds = open_ds(it.assets["image"].href)
        tf = Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)
        gp = stransform(tf.transform, g)
        minx, miny, maxx, maxy = gp.bounds
        pad = 3
        win = from_bounds(minx - pad, miny - pad, maxx + pad, maxy + pad, ds.transform).round_offsets().round_lengths()
        if win.width < 1 or win.height < 1:
            continue
        arr = ds.read(window=win, boundless=True, fill_value=0).astype(float)
        wt = ds.window_transform(win)
        mask = rasterio.features.geometry_mask([mapping(gp)], out_shape=arr.shape[1:], transform=wt, invert=True)
        if mask.sum() == 0 or (arr[:, mask] == 0).all():
            continue
        r, gch, bl, nir = arr[0][mask], arr[1][mask], arr[2][mask], arr[3][mask]
        ndvi = (nir - r) / np.maximum(nir + r, 1)
        if chip_path is not None:
            from PIL import Image, ImageCms
            rgb = np.transpose(arr[:3], (1, 2, 0)).clip(0, 255).astype(np.uint8).copy()
            edge = mask ^ np.pad(mask, 1)[2:, 1:-1] | mask ^ np.pad(mask, 1)[:-2, 1:-1]
            rgb[edge] = [255, 255, 0]
            im = Image.fromarray(rgb).resize((max(1, win.width * 4), max(1, win.height * 4)), Image.NEAREST)
            icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
            im.save(chip_path, icc_profile=icc)
        return {"n_px": int(mask.sum()), "ndvi_median": float(np.median(ndvi)), "veg_share": float((ndvi >= 0.2).mean()),
                "brightness": float(((r + gch + bl) / 3).mean()), "naip_item": it.id}
    return {"n_px": 0, "ndvi_median": np.nan, "veg_share": np.nan, "brightness": np.nan, "naip_item": None}


def main(inp, outp, chips=None, n_chips=0):
    df = pd.read_csv(inp, dtype={"bbl": str})
    polys = {}
    for f in json.loads(POLY.read_text())["features"]:
        polys[str(int(f["properties"]["BBL"]))] = f["geometry"]
    its = items()
    print("NAIP items", len(its), file=sys.stderr)
    if chips:
        Path(chips).mkdir(parents=True, exist_ok=True)

    def one(k):
        bbl = df.bbl.iloc[k]
        g = polys.get(bbl)
        if g is None:
            return {"bbl": bbl, "n_px": 0, "poly": False}
        cp = (Path(chips) / f"{bbl}.png") if chips and k < n_chips else None
        for attempt in range(3):
            try:
                return {"bbl": bbl, "poly": True, **measure(g, its, cp)}
            except Exception as e:  # signed URLs expire; reopen
                _local.ds = {}
                err = str(e)
        return {"bbl": bbl, "poly": True, "n_px": 0, "error": err[:200]}

    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, range(len(df))))
    out = df.merge(pd.DataFrame(res), on="bbl", how="left")
    out.to_csv(outp, index=False)
    print(out[["n_px", "ndvi_median", "veg_share"]].describe().to_string(), file=sys.stderr)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], a[2] if len(a) > 2 else None, int(a[3]) if len(a) > 3 else 0)
