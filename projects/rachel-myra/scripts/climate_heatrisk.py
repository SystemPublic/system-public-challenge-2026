"""NWS/CDC HeatRisk (experimental) for the demo ZIP centroids.

Two machine-readable routes (both verified 2026-11-14):
 1. Current 7-day forecast: ArcGIS ImageServer identify at a point
    https://mapservices.weather.noaa.gov/experimental/rest/services/NWS_HeatRisk/ImageServer/identify
      ?geometry={"x":lon,"y":lat,"spatialReference":{"wkid":4326}}&geometryType=esriGeometryPoint
      &returnCatalogItems=true&returnGeometry=false&f=json
    -> properties.Values[i] is the HeatRisk category (0-4) of catalogItems.features[i]
       (name HeatRisk_<day>_Mercator, idp_validtime = epoch ms of the valid day).
    Also: latest GeoTIFF/KML per day at https://www.wpc.ncep.noaa.gov/heatrisk/data/HeatRisk_<d>_Mercator.tif
 2. Past days: daily archive of Day-1 forecasts (PNG/KML/GeoTIFF), back to 2024-ish
    https://www.wpc.ncep.noaa.gov/heatrisk/data/archive/HeatRisk_CONUS_YYYYMMDD.tif
    sampled here at the ZIP centroids for the replay window.

 3. CDC HeatRisk Dashboard backend (undocumented; county level only):
    https://ephtracking.cdc.gov/DataExplorer/HeatForecastData/<county FIPS>  -> [{date, day0..day6, countyFips}]

Outputs:
    data/raw/climate/heatrisk/identify_<zip>.json, archive/HeatRisk_CONUS_<date>.tif
    data/processed/heatrisk_zip_current.json     current 7-day HeatRisk per demo ZIP
    data/processed/heatrisk_zip_replay.csv       archived Day-1 HeatRisk per ZIP for the replay window

Usage:
    uv run --with rasterio --with pyproj python scripts/climate_heatrisk.py --start 2025-06-19 --end 2025-06-28
"""
import argparse
import csv
import json
import subprocess
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/climate/heatrisk"
UA = "missing-label-hackathon (research prototype)"
SVC = "https://mapservices.weather.noaa.gov/experimental/rest/services/NWS_HeatRisk/ImageServer"
ARCH = "https://www.wpc.ncep.noaa.gov/heatrisk/data/archive"
CDC_COUNTY = "https://ephtracking.cdc.gov/DataExplorer/HeatForecastData/{fips}"
LABELS = {0: "Green (little to no risk)", 1: "Yellow (minor)", 2: "Orange (moderate)", 3: "Red (major)", 4: "Magenta (extreme)"}


def zips():
    rows = csv.DictReader(open(ROOT / "data/raw/climate/nws/zcta_gazetteer_2024_demo_zips.tsv"), delimiter="\t")
    out = []
    for r in rows:
        r = {k.strip(): v.strip() for k, v in r.items()}
        out.append((r["GEOID"], float(r["INTPTLAT"]), float(r["INTPTLONG"])))
    return out


def get_json(url):
    # curl uses the system trust store (python's bundled CA store rejected the CDC chain)
    out = subprocess.run(["curl", "-sS", "-f", "-A", UA, url], check=True, capture_output=True).stdout
    return json.loads(out)


def current():
    res = {"fetched_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "service": SVC,
           "categories": LABELS, "zips": {}}
    for z, lat, lon in zips():
        geom = json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}})
        q = urllib.parse.urlencode({"geometry": geom, "geometryType": "esriGeometryPoint",
                                    "returnCatalogItems": "true", "returnGeometry": "false", "f": "json"})
        d = get_json(f"{SVC}/identify?{q}")
        json.dump(d, open(RAW / f"identify_{z}.json", "w"), indent=1)
        vals = d.get("properties", {}).get("Values", [])
        days = []
        for v, f in zip(vals, d.get("catalogItems", {}).get("features", [])):
            a = f["attributes"]
            days.append({"product": a["name"], "day": int(a["name"].split("_")[1]),
                         "valid_utc": datetime.fromtimestamp(a["idp_validtime"] / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
                         "issued_utc": datetime.fromtimestamp(a["idp_filedate"] / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
                         "heatrisk": int(float(v)) if v not in ("NoData", "") else None})
        days.sort(key=lambda x: x["day"])
        res["zips"][z] = {"lat": lat, "lon": lon, "days": days,
                          "max_next_7d": max([x["heatrisk"] for x in days if x["heatrisk"] is not None], default=None)}
    # CDC HeatRisk Dashboard backend (undocumented, county level; found in the dashboard's JS bundle).
    # date is epoch ms; day0..day6 are HeatRisk categories for the county (Bronx = 36005).
    try:
        cdc = get_json(CDC_COUNTY.format(fips="36005"))
        json.dump(cdc, open(RAW / "cdc_heatforecastdata_36005.json", "w"), indent=1)
        res["cdc_dashboard_county_36005"] = {"endpoint": CDC_COUNTY.format(fips="36005"), "response": cdc}
    except Exception as e:
        res["cdc_dashboard_county_36005"] = {"endpoint": CDC_COUNTY.format(fips="36005"), "error": str(e)}
    json.dump(res, open(ROOT / "data/processed/heatrisk_zip_current.json", "w"), indent=1)
    print({z: [x["heatrisk"] for x in v["days"]] for z, v in res["zips"].items()})


def replay(start, end):
    import rasterio
    from pyproj import Transformer
    (RAW / "archive").mkdir(parents=True, exist_ok=True)
    rows = []
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    zs = zips()
    while d0 <= d1:
        tag = d0.strftime("%Y%m%d")
        f = RAW / "archive" / f"HeatRisk_CONUS_{tag}.tif"
        if not f.exists():
            subprocess.run(["curl", "-sS", "-f", "-A", UA, "-o", str(f), f"{ARCH}/HeatRisk_CONUS_{tag}.tif"], check=False)
        if f.exists() and f.stat().st_size > 0:
            with rasterio.open(f) as src:
                tr = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
                pts = [tr.transform(lon, lat) for _, lat, lon in zs]
                for (z, lat, lon), v in zip(zs, src.sample(pts)):
                    val = int(v[0])
                    rows.append({"date": d0.isoformat(), "zip": z, "heatrisk_day1": val if 0 <= val <= 4 else "",
                                 "label": LABELS.get(val, "nodata"), "source": f"{ARCH}/HeatRisk_CONUS_{tag}.tif"})
        else:
            for z, _, _ in zs:
                rows.append({"date": d0.isoformat(), "zip": z, "heatrisk_day1": "", "label": "archive file missing", "source": ""})
        d0 += timedelta(days=1)
    with open(ROOT / "data/processed/heatrisk_zip_replay.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        if r["zip"] == "10457":
            print(r["date"], r["heatrisk_day1"], r["label"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-06-19")
    ap.add_argument("--end", default="2025-06-28")
    a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    current()
    replay(a.start, a.end)


if __name__ == "__main__":
    main()
