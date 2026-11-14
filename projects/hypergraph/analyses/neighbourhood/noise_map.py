"""Read the US DOT/BTS National Transportation Noise Map 2020 (road + aviation + rail, LAeq 24 h) for NYC
from the public tile service and summarise it by 2020 census tract.

Service: https://geo.dot.gov/server/rest/services/Hosted/NTAD_Noise_2020_CONUS_Aviation_Road_Rail/MapServer
The service publishes rendered tiles only (no pixel values), so each tile pixel is mapped back to the legend class
by its colour. Classes: 45-50, 50-55, 55-60, 60-70, 70-80, 80-90, >90 dB(A). Unpainted pixels are below 45 dB
(set to 40 dB for the tract mean). Zoom 12 (38.2 m Web Mercator pixels, about 29 m on the ground at 40.7 N; the service caches no deeper level);
the source raster is 30 m.

Writes data/derived/neighbourhood/noise_map_tracts.csv and data/raw/noise/nyc_noise_z12.npz (class grid).
"""
from __future__ import annotations

import io
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SERVICE = "https://geo.dot.gov/server/rest/services/Hosted/NTAD_Noise_2020_CONUS_Aviation_Road_Rail/MapServer"
RAW = ROOT / "data" / "raw" / "noise"
OUT = ROOT / "data" / "derived" / "neighbourhood"
Z = 12
BBOX = (-74.2600, 40.4950, -73.6990, 40.9160)  # lon/lat
LEGEND = [((255, 193, 7), 47.5), ((255, 128, 0), 52.5), ((255, 0, 0), 57.5), ((255, 51, 153), 65.0),
          ((163, 0, 204), 75.0), ((82, 0, 204), 85.0), ((0, 0, 255), 92.5)]


def tile_xy(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def get_tile(z, y, x):
    RAW.mkdir(parents=True, exist_ok=True)
    f = RAW / f"t{z}_{y}_{x}.png"
    if not f.exists():
        for i in range(4):
            r = requests.get(f"{SERVICE}/tile/{z}/{y}/{x}", timeout=60)
            if r.status_code == 200:
                f.write_bytes(r.content)
                break
            if r.status_code == 404:
                f.write_bytes(b"")
                break
            time.sleep(2 * (i + 1))
    b = f.read_bytes()
    if not b:
        return np.zeros((256, 256, 4), dtype=np.uint8)
    return np.array(Image.open(io.BytesIO(b)).convert("RGBA"))


def classify(rgba):
    """Return dB midpoint per pixel (NaN where transparent) by nearest legend colour."""
    rgb = rgba[..., :3].astype(float)
    alpha = rgba[..., 3]
    cols = np.array([c for c, _ in LEGEND], dtype=float)
    vals = np.array([v for _, v in LEGEND])
    d = ((rgb[..., None, :] - cols[None, None, :, :]) ** 2).sum(-1)
    k = d.argmin(-1)
    out = vals[k].astype(float)
    out[alpha < 128] = np.nan
    out[np.sqrt(d.min(-1)) > 60] = np.nan  # pixels that match no class (e.g. edges)
    return out


def build_grid():
    x0, y0 = tile_xy(BBOX[0], BBOX[3], Z)
    x1, y1 = tile_xy(BBOX[2], BBOX[1], Z)
    xs, ys = range(int(x0), int(x1) + 1), range(int(y0), int(y1) + 1)
    rows = []
    for ty in ys:
        rows.append(np.concatenate([classify(get_tile(Z, ty, tx)) for tx in xs], axis=1))
    grid = np.concatenate(rows, axis=0)
    # pixel-centre lon/lat
    n = 2 ** Z * 256
    px = (np.arange(grid.shape[1]) + int(x0) * 256 + 0.5)
    py = (np.arange(grid.shape[0]) + int(y0) * 256 + 0.5)
    lon = px / n * 360 - 180
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * py / n))))
    np.savez_compressed(RAW / "nyc_noise_z12.npz", grid=grid, lon=lon, lat=lat)
    return grid, lon, lat


def by_tract(grid, lon, lat):
    import geopandas as gpd
    from analyses.neighbourhood.geo import tracts
    LON, LAT = np.meshgrid(lon, lat)
    keep = (LON >= BBOX[0]) & (LON <= BBOX[2]) & (LAT >= BBOX[1]) & (LAT <= BBOX[3])
    v = grid[keep]
    pts = gpd.GeoDataFrame({"db": v}, geometry=gpd.points_from_xy(LON[keep], LAT[keep]), crs=4326)
    j = gpd.sjoin(pts, tracts()[["geoid", "geometry"]], how="inner", predicate="within")
    j["db40"] = j["db"].fillna(40.0)
    j["ge60"] = (j["db"] >= 60).astype(float)
    j["ge55"] = (j["db"] >= 55).astype(float)
    # energy mean of class midpoints
    j["energy"] = 10 ** (j["db40"] / 10)
    g = j.groupby("geoid").agg(noise_mean_db=("db40", "mean"), noise_energy=("energy", "mean"),
                               share_ge60=("ge60", "mean"), share_ge55=("ge55", "mean"), n_px=("db40", "size"))
    g["noise_leq_db"] = 10 * np.log10(g["noise_energy"])
    g = g.drop(columns="noise_energy").reset_index().rename(columns={"geoid": "GEOID"})
    return g


def main():
    grid, lon, lat = build_grid()
    print("grid", grid.shape, "painted share", np.isfinite(grid).mean())
    g = by_tract(grid, lon, lat)
    g.to_csv(OUT / "noise_map_tracts.csv", index=False)
    meta = {"service": SERVICE, "layer": "CONUS_rail_road_and_aviation_noise_2020", "zoom": Z, "legend": LEGEND,
            "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "n_tracts": int(len(g)),
            "citation": "US DOT Bureau of Transportation Statistics, National Transportation Noise Map, 2020 data release (NTAD)."}
    (OUT / "noise_map_source.json").write_text(json.dumps(meta, indent=1))
    print(g.describe())


if __name__ == "__main__":
    main()
