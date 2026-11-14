"""USDA NAIP aerial imagery for any box, with a source record for claims.

The National Agriculture Imagery Program flies each state in summer every two
or three years at 0.3-1 m per pixel, in four bands (red, green, blue, near
infrared). The images are public domain. The Microsoft Planetary Computer
serves them as cloud-optimised GeoTIFFs through a STAC catalogue that needs no
account; only the pixels inside the requested box are read.

    from kit import naip
    box = (40.6778, -74.0145, 40.6792, -74.0126)          # south, west, north, east
    naip.years(box)                                       # flights that cover the box, with dates and coverage
    a = naip.fetch("redhook-555", *box, year=2022)
    a.arr, a.transform, a.source                          # (4, H, W) uint8, affine, record for `sources`
    naip.vegetation(a.arr)                                # NDVI share above the threshold
    s = naip.series("redhook-555", box, polygons={"lot": [(lon, lat), ...]})

Each year's image is written to ROOT/data/raw/naip/<name>/ as naip<year>.tif
(four bands, georeferenced), naip<year>.png (sRGB, for viewing) and
naip<year>.json (the source record). The files are reused unless refresh=True.

Every year of one name is resampled onto the same grid (NAD83 UTM, `res`
metres per pixel, default 0.6), so arrays from different years line up pixel
for pixel and can be differenced.

For New York City the state flights in the catalogue run from 2011 to 2022
(2021 was flown on 5 November, after leaf fall in most of the city). New Jersey
flights of 2023 (0.3 m, 20 August) and 2025 (0.6 m, 4 July) reach across the
Hudson to about longitude -73.98, so they cover lower and west midtown
Manhattan but not the rest of the city. years() reports how much of a box each
flight covers.

Credit line: "Aerial imagery: USDA Farm Service Agency, National Agriculture
Imagery Program (NAIP), <year>."
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import os

# Copied from concordance-kit kit/naip.py on 12 November 2026 for claim heat-trees-canopy-within-nta; the only
# change is this block. Imagery is written outside Dropbox: $NAIP_ROOT, or ~/opt/nyc-concordance by default.
ROOT = Path(os.environ.get("NAIP_ROOT", Path.home() / "opt" / "nyc-concordance")).expanduser()

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "naip"
OUT = ROOT / "data" / "raw" / "naip"
RES = 0.6
# NDVI computed from NAIP 8-bit digital numbers is not calibrated to reflectance, and each flight has its own
# radiometry. VEG_THRESHOLD (0.2) is a convention: in the November 2026 test boxes (Red Hook, midtown around
# Bryant Park) it marked tree canopy and lawn and little else in the 2010, 2011, 2013, 2015, 2022 and 2023 flights,
# but in the 2017 and 2019 New York flights the near-infrared band is bright everywhere and 0.2 marked roofs and
# streets as vegetation (midtown share 0.53 and 0.41 against about 0.10). threshold="relative" uses the image's own
# median NDVI plus RELATIVE_DELTA instead; it is steadier across most flights but fails on 2019 and is wrong where
# vegetation is most of the box. vegetation() reports the NDVI percentiles so a shifted flight can be seen.
VEG_THRESHOLD = 0.2
RELATIVE_DELTA = 0.3


def credit(year) -> str:
    return f"Aerial imagery: USDA Farm Service Agency, National Agriculture Imagery Program (NAIP), {year}."


# ---------------------------------------------------------------- catalogue

def _client():
    import planetary_computer
    import pystac_client
    return pystac_client.Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)


def _year(item) -> int:
    return int(item.properties.get("naip:year") or item.datetime.year)


def _box(box) -> tuple[float, float, float, float]:
    s, w, n, e = (float(v) for v in box)
    if not (s < n and w < e):
        raise ValueError("box is (south, west, north, east)")
    return s, w, n, e


def _items(box) -> list:
    s, w, n, e = _box(box)
    return list(_client().search(collections=[COLLECTION], bbox=[w, s, e, n]).items())


def _coverage(items, box) -> float:
    """Share of the box (by area in degrees, fine for boxes of a few km) inside the items' footprints."""
    from shapely.geometry import box as sbox, shape
    from shapely.ops import unary_union
    s, w, n, e = box
    b = sbox(w, s, e, n)
    if not items:
        return 0.0
    u = unary_union([shape(i.geometry) for i in items])
    return float(u.intersection(b).area / b.area)


def years(box, items=None) -> list[dict]:
    """The NAIP flights that touch box (south, west, north, east): one dict per year with the acquisition dates,
    states, native ground sample distance, item ids and the share of the box covered, oldest first."""
    box = _box(box)
    items = _items(box) if items is None else items
    out = []
    for y in sorted({_year(i) for i in items}):
        its = [i for i in items if _year(i) == y]
        out.append({
            "year": y,
            "dates": sorted({i.datetime.date().isoformat() for i in its}),
            "states": sorted({i.properties.get("naip:state", "") for i in its}),
            "gsd": sorted({float(i.properties.get("gsd")) for i in its if i.properties.get("gsd")}),
            "items": sorted(i.id for i in its),
            "coverage": round(_coverage(its, box), 4),
        })
    return out


available = years      # alias used where a parameter named `years` hides the function


# ---------------------------------------------------------------- grid and reading

def _utm_epsg(lon: float) -> int:
    return 26900 + int((lon + 180) // 6) + 1        # NAD83 / UTM zone, as NAIP uses in the continental US


def _grid(box, res: float):
    from rasterio.transform import from_origin
    from rasterio.warp import transform_bounds
    s, w, n, e = box
    crs = f"EPSG:{_utm_epsg((w + e) / 2)}"
    left, bottom, right, top = transform_bounds("EPSG:4326", crs, w, s, e, n)
    left, top = np.floor(left / res) * res, np.ceil(top / res) * res      # snap so every year shares the grid
    width = int(np.ceil((right - left) / res))
    height = int(np.ceil((top - bottom) / res))
    return crs, from_origin(left, top, res, res), width, height


def _read_into(href, dst, dst_transform, dst_crs) -> np.ndarray:
    """Read the part of one COG under the target grid, resample it, and fill pixels of dst that are still empty.
    Returns the mask of pixels this item filled."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.warp import reproject, transform_bounds
    from rasterio.windows import from_bounds
    h, w = dst.shape[1:]
    a, e, c, f = dst_transform.a, dst_transform.e, dst_transform.c, dst_transform.f
    bounds = (c, f + e * h, c + a * w, f)
    with rasterio.open(href) as src:
        sb = transform_bounds(dst_crs, src.crs, *bounds)
        win = from_bounds(*sb, transform=src.transform).round_offsets().round_lengths()
        win = win.intersection(rasterio.windows.Window(0, 0, src.width, src.height)) if _overlaps(win, src) else None
        if win is None or win.width < 1 or win.height < 1:
            return np.zeros((h, w), bool)
        bands = list(range(1, min(src.count, 4) + 1))
        data = src.read(bands, window=win)
        tmp = np.zeros((len(bands), h, w), data.dtype)
        reproject(data, tmp, src_transform=src.window_transform(win), src_crs=src.crs, src_nodata=0,
                  dst_transform=dst_transform, dst_crs=dst_crs, dst_nodata=0, resampling=Resampling.bilinear)
    new = (tmp.max(axis=0) > 0) & (dst.max(axis=0) == 0)
    for k in range(len(bands)):
        dst[k][new] = tmp[k][new]
    return new


def _overlaps(win, src) -> bool:
    return win.col_off < src.width and win.row_off < src.height and \
        win.col_off + win.width > 0 and win.row_off + win.height > 0


# ---------------------------------------------------------------- fetch

@dataclass
class Naip:
    name: str
    year: int
    arr: np.ndarray          # (4, H, W) uint8: red, green, blue, near infrared; 0 where no imagery
    transform: object        # rasterio Affine, grid CRS below
    crs: str
    source: dict             # record for an outcome's `sources`
    folder: Path

    @property
    def png(self) -> Path:
        return self.folder / f"naip{self.year}.png"

    @property
    def tif(self) -> Path:
        return self.folder / f"naip{self.year}.tif"

    def to_px(self, lat: float, lon: float) -> tuple[float, float]:
        """(column, row) in the arrays and the PNG for a latitude and longitude."""
        from pyproj import Transformer
        x, y = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True).transform(lon, lat)
        col, row = ~self.transform * (x, y)
        return col, row


def _load(folder: Path, year: int, name: str) -> Naip | None:
    import rasterio
    j, t = folder / f"naip{year}.json", folder / f"naip{year}.tif"
    if not (j.exists() and t.exists()):
        return None
    with rasterio.open(t) as src:
        arr, tr, crs = src.read(), src.transform, src.crs.to_string()
    return Naip(name, year, arr, tr, crs, json.loads(j.read_text()), folder)


def fetch(name: str, south: float, west: float, north: float, east: float, year: int | None = None,
          res: float = RES, fill: bool = False, refresh: bool = False) -> Naip:
    """NAIP for one box and one flight year, cached under ROOT/data/raw/naip/<name>/.

    year=None takes the most recent year whose flights cover the whole box (by footprint), or failing that the
    year with the largest coverage. With fill=False pixels outside the year's flights stay 0 and the record's
    `coverage` says how much of the box has imagery; fill=True fills them from the nearest other years and lists
    those years in the record. A claim should usually rest on one date, so the default is no fill."""
    box = _box((south, west, north, east))
    folder = OUT / name
    items = None
    if year is None:
        items = _items(box)
        if not items:
            raise RuntimeError("no NAIP imagery covers this box")
        ys = years(box, items)
        full = [y for y in ys if y["coverage"] >= 0.999]
        year = (full[-1] if full else max(ys, key=lambda y: (y["coverage"], y["year"])))["year"]
    if not refresh:
        a = _load(folder, year, name)
        if a is not None and a.source.get("box") == dict(zip(("south", "west", "north", "east"), box)) \
                and a.source.get("resolution_m") == res:
            return a
    items = _items(box) if items is None else items
    its = [i for i in items if _year(i) == year]
    if not its:
        raise RuntimeError(f"no NAIP flight of {year} covers this box; available: {[y['year'] for y in years(box, items)]}")
    # Within a year, the latest acquisition first; with fill, other years follow by distance from the chosen year.
    order = sorted(its, key=lambda i: i.datetime, reverse=True)
    if fill:
        order += sorted([i for i in items if _year(i) != year], key=lambda i: (abs(_year(i) - year), -_year(i)))
    crs, transform, width, height = _grid(box, res)
    arr = np.zeros((4, height, width), np.uint8)
    used = []
    for it in order:
        if arr.max(axis=0).min() > 0:
            break
        new = _read_into(it.assets["image"].href, arr, transform, crs)
        if new.any():
            used.append((it, int(new.sum())))
    valid = arr.max(axis=0) > 0
    src = {
        "kind": "naip",
        "collection": COLLECTION,
        "stac_url": STAC_URL,
        "items": [i.id for i, _ in used],
        "item_urls": [f"{STAC_URL}/collections/{COLLECTION}/items/{i.id}" for i, _ in used],
        "year": year,
        "years": sorted({_year(i) for i, _ in used}),
        "acquisition_dates": sorted({i.datetime.date().isoformat() for i, _ in used}),
        "states": sorted({i.properties.get("naip:state", "") for i, _ in used}),
        "gsd": sorted({float(i.properties["gsd"]) for i, _ in used if i.properties.get("gsd")}),
        "resolution_m": res,
        "crs": crs,
        "box": dict(zip(("south", "west", "north", "east"), box)),
        "size": [width, height],
        "coverage": round(float(valid.mean()), 4),
        "filled_from_other_years": fill and len({_year(i) for i, _ in used}) > 1,
        "files": [f"naip{year}.tif", f"naip{year}.png"],
        "license": "public domain (USDA)",
        "credit": credit(year),
        "data_access": "open",
        "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    _write(folder, year, arr, transform, crs, src)
    return Naip(name, year, arr, transform, crs, src, folder)


def _write(folder: Path, year: int, arr, transform, crs, src):
    import rasterio
    from PIL import Image, ImageCms
    folder.mkdir(parents=True, exist_ok=True)
    with rasterio.open(folder / f"naip{year}.tif", "w", driver="GTiff", height=arr.shape[1], width=arr.shape[2],
                       count=4, dtype="uint8", crs=crs, transform=transform, nodata=0, compress="deflate") as dst:
        dst.write(arr)
        dst.descriptions = ("red", "green", "blue", "nir")
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    Image.fromarray(np.transpose(arr[:3], (1, 2, 0))).save(folder / f"naip{year}.png", icc_profile=icc)
    (folder / f"naip{year}.json").write_text(json.dumps(src, indent=1))


# ---------------------------------------------------------------- vegetation

def ndvi(arr: np.ndarray) -> np.ndarray:
    """NDVI = (NIR - red) / (NIR + red) from a (4, H, W) NAIP array; NaN where there is no imagery."""
    r = arr[0].astype(np.float32)
    nir = arr[3].astype(np.float32)
    valid = arr.max(axis=0) > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        v = (nir - r) / (nir + r)
    v[~valid | ((nir + r) == 0)] = np.nan
    return v


def vegetation(arr: np.ndarray, threshold: float | str = VEG_THRESHOLD, mask: np.ndarray | None = None) -> dict:
    """Share of imaged pixels (inside mask, if given) with NDVI above threshold, the mean NDVI and the 10th,
    50th and 90th NDVI percentiles of the whole image. threshold is a number or "relative" (the whole image's
    median NDVI plus RELATIVE_DELTA). Both are uncalibrated (see VEG_THRESHOLD): compare places within one flight
    more readily than one place across flights. A median NDVI above about 0 in a built-up box means the flight's
    near-infrared is shifted and a fixed threshold will overcount."""
    v = ndvi(arr)
    allv = v[~np.isnan(v)]
    pct = [float(x) for x in np.percentile(allv, [10, 50, 90])] if allv.size else [None] * 3
    t = (pct[1] + RELATIVE_DELTA if pct[1] is not None else None) if threshold == "relative" else float(threshold)
    ok = ~np.isnan(v) if mask is None else (~np.isnan(v) & mask)
    n = int(ok.sum())
    return {"veg_share": float((v[ok] > t).mean()) if n and t is not None else None,
            "mean_ndvi": float(np.nanmean(v[ok])) if n else None,
            "n_pixels": n, "threshold": t, "threshold_rule": "relative" if threshold == "relative" else "fixed",
            "image_ndvi_p10_p50_p90": pct}


def summarize(a: "Naip", polygons: dict, threshold: float | str = VEG_THRESHOLD, point_radius_m: float = 10.0) -> dict:
    """Vegetation share and mean NDVI inside each named polygon or point (see _masks for accepted forms)."""
    return {k: vegetation(a.arr, threshold, m) for k, m in _masks(a, polygons, point_radius_m).items()}


# ---------------------------------------------------------------- polygons and points

def _masks(a: Naip, polygons, point_radius_m: float = 10.0) -> dict:
    """Pixel masks for named geometries in lon/lat. polygons is a dict {id: geometry} where a geometry is a
    shapely geometry, a GeoJSON-like dict, a list of (lon, lat) vertices, or one (lon, lat) point (buffered by
    point_radius_m)."""
    from pyproj import Transformer
    from rasterio.features import geometry_mask
    from shapely.geometry import Point, Polygon, mapping, shape
    from shapely.ops import transform as stransform
    to = Transformer.from_crs("EPSG:4326", a.crs, always_xy=True).transform
    out = {}
    for k, g in polygons.items():
        if isinstance(g, dict):
            g = shape(g)
        elif isinstance(g, (list, tuple)) and len(g) == 2 and np.isscalar(g[0]):
            g = Point(g)
        elif isinstance(g, (list, tuple)):
            g = Polygon(g)
        p = stransform(to, g)
        if p.geom_type == "Point":
            p = p.buffer(point_radius_m)
        out[k] = geometry_mask([mapping(p)], out_shape=a.arr.shape[1:], transform=a.transform, invert=True,
                               all_touched=False)
    return out


# ---------------------------------------------------------------- series

def _mad(x: np.ndarray, y: np.ndarray, mask=None) -> float | None:
    """Mean absolute difference of the RGB digital numbers over pixels imaged in both years (0-255 scale)."""
    ok = (x.max(axis=0) > 0) & (y.max(axis=0) > 0)
    if mask is not None:
        ok &= mask
    if not ok.any():
        return None
    return float(np.abs(x[:3].astype(np.int16) - y[:3].astype(np.int16))[:, ok].mean())


def series(name: str, box, years: list[int] | None = None, polygons: dict | None = None, res: float = RES,
           min_coverage: float = 0.999, threshold: float | str = VEG_THRESHOLD, point_radius_m: float = 10.0) -> dict:
    """The same box in several flight years on one grid, for change detection.

    years=None takes every year whose flights cover at least min_coverage of the box. Returns per year the
    vegetation share, mean NDVI, coverage and dates; for each consecutive pair the mean absolute RGB difference;
    the same per polygon if polygons are given; and the list of source records. Raw differences include changes of
    sun angle, season and sensor between flights, so compare a lot's difference with the box's as a baseline."""
    box = _box(box)
    items = _items(box)
    avail = available(box, items)
    if years is None:
        years = [y["year"] for y in avail if y["coverage"] >= min_coverage]
    imgs = [fetch(name, *box, year=y, res=res) for y in years]
    masks = _masks(imgs[0], polygons, point_radius_m) if polygons else {}
    per_year, sources = [], []
    for a in imgs:
        row = {"year": a.year, "dates": a.source["acquisition_dates"], "coverage": a.source["coverage"],
               **vegetation(a.arr, threshold)}
        if masks:
            row["polygons"] = {k: vegetation(a.arr, threshold, m) for k, m in masks.items()}
        per_year.append(row)
        sources.append(a.source)
    changes = []
    for a, b in zip(imgs, imgs[1:]):
        c = {"from": a.year, "to": b.year, "mean_abs_diff": _mad(a.arr, b.arr)}
        if masks:
            c["polygons"] = {k: _mad(a.arr, b.arr, m) for k, m in masks.items()}
        changes.append(c)
    return {"name": name, "box": dict(zip(("south", "west", "north", "east"), box)), "available": avail,
            "per_year": per_year, "changes": changes, "sources": sources}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="NAIP years for a box (south west north east)")
    p.add_argument("box", nargs=4, type=float)
    for y in years(p.parse_args().box):
        print(y["year"], ",".join(y["dates"]), ",".join(y["states"]), y["gsd"], f"coverage {y['coverage']:.0%}")
