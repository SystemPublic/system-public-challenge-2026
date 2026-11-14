"""Claim construction-aerial-triangulation, step 1: sample NB jobs, fetch NAIP before/after crops of each lot,
compute a pixel-difference score, and draw a label-free grid for visual judgement.

Sample: 48 NB jobs whose first NB permit was issued 2018-2020 (data/derived/construction/nb_jobs.csv.gz), seed 20261112.
Lot polygon: DOF Digital Tax Map tax lots (i38t-6if2) by BBL; PLUTO's geom column is empty on Open Data, so the
registered source could not be used. Fallback: a 24 m square at the permit's coordinates.
Imagery: USDA NAIP via the Microsoft Planetary Computer STAC, New York flights of 2017 (1.0 m) and 2022 (0.6 m),
both resampled to a 0.5 m grid in UTM 18N. Outputs go to data/derived/construction/aerial/.
The CO status is NOT read here, so the judgements made from the grid are blind to it."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import socrata as so

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "construction"
A = D / "aerial"
A.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "figures" / "construction"
FIG.mkdir(parents=True, exist_ok=True)
SEED, N = 20261112, 48
YEARS = (2017, 2022)
RES = 0.5
MARGIN = 15.0


def sample():
    j = pd.read_csv(D / "nb_jobs.csv.gz", dtype={"job": str, "bbl": str})
    j = j[j.cohort.between(2018, 2020)]
    s = j.sample(N, random_state=SEED)[["job", "cohort", "system", "bbl", "first_permit"]].reset_index(drop=True)
    s.index.name = "idx"
    p = pd.read_parquet(ROOT / "data" / "big" / "construction" / "permits_nb_legacy.parquet")
    ll = p[p.job__.isin(s.job)].groupby("job__")[["gis_latitude", "gis_longitude"]].first()
    s = s.join(ll, on="job")
    return s


def lot_geoms(bbls):
    bbls = sorted({str(b).split(".")[0] for b in bbls if isinstance(b, str) and b[:1].isdigit()})
    q = ",".join(f"'{b}'" for b in bbls)
    rows, src = so.query("i38t-6if2", select="bbl,the_geom", where=f"bbl in ({q})")
    return {r["bbl"]: r["the_geom"] for r in rows if r.get("the_geom")}, src


def stac_items(lon, lat):
    import planetary_computer, pystac_client
    cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=planetary_computer.sign_inplace)
    items = list(cat.search(collections=["naip"], intersects={"type": "Point", "coordinates": [lon, lat]}).items())
    out = {}
    for y in YEARS:
        cand = [i for i in items if str(i.properties.get("naip:year")) == str(y)]
        cand.sort(key=lambda i: i.properties.get("naip:state") != "ny")
        out[y] = cand[0] if cand else None
    return out


def crop(item, poly_utm, dst_crs="EPSG:26918"):
    import rasterio
    from rasterio.warp import reproject, Resampling, transform_bounds
    from rasterio.windows import from_bounds
    from rasterio.transform import from_origin
    minx, miny, maxx, maxy = poly_utm.bounds
    minx, miny, maxx, maxy = minx - MARGIN, miny - MARGIN, maxx + MARGIN, maxy + MARGIN
    w, h = int(np.ceil((maxx - minx) / RES)), int(np.ceil((maxy - miny) / RES))
    dst_t = from_origin(minx, maxy, RES, RES)
    out = np.zeros((3, h, w), np.uint8)
    with rasterio.open(item.assets["image"].href) as src:
        b = transform_bounds(dst_crs, src.crs, minx - 5, miny - 5, maxx + 5, maxy + 5)
        win = from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
        arr = src.read([1, 2, 3], window=win, boundless=True, fill_value=0)
        wt = src.window_transform(win)
        for k in range(3):
            reproject(arr[k], out[k], src_transform=wt, src_crs=src.crs, dst_transform=dst_t, dst_crs=dst_crs,
                      resampling=Resampling.bilinear)
    return out, dst_t, item.properties.get("datetime") or str(item.datetime)


def main():
    from shapely.geometry import shape, box
    from shapely.ops import transform as stransform
    from pyproj import Transformer
    from rasterio.features import geometry_mask
    from PIL import Image, ImageCms
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    tf = Transformer.from_crs("EPSG:4326", "EPSG:26918", always_xy=True)
    s = sample()
    geoms, src = lot_geoms(s.bbl.dropna())
    recs = []
    for i, r in s.iterrows():
        bbl = str(r.bbl).split(".")[0] if isinstance(r.bbl, str) else None
        if bbl in geoms:
            g = stransform(tf.transform, shape(geoms[bbl])); gsrc = "tax lot"
        else:
            x, y = tf.transform(float(r.gis_longitude), float(r.gis_latitude)); g = box(x - 12, y - 12, x + 12, y + 12); gsrc = "permit point"
        if g.area > 20000:  # very large lots: crop to a 140 m box around the centroid
            c = g.centroid; g = g.intersection(box(c.x - 70, c.y - 70, c.x + 70, c.y + 70)); gsrc += " (clipped)"
        cen = stransform(Transformer.from_crs("EPSG:26918", "EPSG:4326", always_xy=True).transform, g.centroid)
        its = stac_items(cen.x, cen.y)
        rec = dict(idx=i, job=r.job, bbl=bbl, geom_source=gsrc, lot_m2=round(g.area, 1), lon=cen.x, lat=cen.y)
        imgs = {}
        for y in YEARS:
            arr, t, dt = crop(its[y], g)
            imgs[y] = arr
            rec[f"date_{y}"] = str(dt)[:10]
            rec[f"item_{y}"] = its[y].id
            Image.fromarray(np.transpose(arr, (1, 2, 0))).save(A / f"{i:02d}_{y}.png", icc_profile=icc)
        mask = ~geometry_mask([g.__geo_interface__], out_shape=imgs[YEARS[0]].shape[1:], transform=t)
        z = []
        for y in YEARS:
            gray = imgs[y].astype(float).mean(0)
            v = gray[mask]
            z.append((gray - v.mean()) / (v.std() + 1e-6))
        rec["mad_z"] = float(np.abs(z[1] - z[0])[mask].mean())
        rec["mean_change"] = float(imgs[YEARS[1]].astype(float).mean(0)[mask].mean() - imgs[YEARS[0]].astype(float).mean(0)[mask].mean())
        # lot outline file for the grid
        np.save(A / f"{i:02d}_mask.npy", mask)
        recs.append(rec)
        print(i, rec["job"], gsrc, rec["lot_m2"], round(rec["mad_z"], 3), flush=True)
    out = pd.DataFrame(recs)
    out.to_csv(D / "aerial_sample.csv", index=False)
    srcs = json.loads((D / "sources.json").read_text())
    srcs["tax_lots_aerial_sample"] = src
    srcs["naip"] = {"kind": "other", "name": "USDA NAIP via Microsoft Planetary Computer STAC (collection 'naip')",
                    "url": "https://planetarycomputer.microsoft.com/dataset/naip", "years": list(YEARS),
                    "items": sorted(set(out.item_2017) | set(out.item_2022))}
    (D / "sources.json").write_text(json.dumps(srcs, indent=1))


if __name__ == "__main__":
    main()
