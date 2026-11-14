"""NOAA CPC temperature outlooks at NYC: 6-10 day, 8-14 day, week 3-4, monthly, seasonal (leads 1-13).

Machine-readable sources (verified 2026-11-14):
  ArcGIS MapServer layers (polygons with fields fcst_date, start_date/end_date or valid_seas, prob, cat):
    https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/cpc_6_10_day_outlk/MapServer/0
    https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/cpc_8_14_day_outlk/MapServer/0
    https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/cpc_mthly_temp_outlk/MapServer/0
    https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/cpc_sea_temp_outlk/MapServer/<0..12>  (Lead 1..13)
  Week 3-4 is not on the map service; it comes as a shapefile:
    https://ftp.cpc.ncep.noaa.gov/GIS/us_tempprcpfcst/wk34temp_latest.zip
  (6-10/8-14/monthly shapefiles + KMZ are also at https://ftp.cpc.ncep.noaa.gov/GIS/us_tempprcpfcst/)

A point query (spatialRel=esriSpatialRelIntersects) returns the polygon containing NYC. "prob" is the
probability (%) of the favored category "cat" (Above / Below / Normal). No polygon (or cat EC) = Equal Chances
(33/33/33). p_above_est follows the CPC convention that the non-favored tercile on the "near-normal" side
stays at 33.3%: Above favored -> p; Below favored -> 100 - p - 33.3; Normal favored -> (100 - p) / 2.

Output: data/processed/cpc_outlook_nyc.json ; raw responses in data/raw/climate/cpc/.

Usage:
    uv run --with pyshp --with shapely python scripts/climate_cpc.py
"""
import io
import json
import subprocess
import urllib.parse
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/climate/cpc"
UA = "missing-label-hackathon (research prototype)"
MS = "https://mapservices.weather.noaa.gov/vector/rest/services/outlooks"
WK34 = "https://ftp.cpc.ncep.noaa.gov/GIS/us_tempprcpfcst/wk34temp_latest.zip"
POINT = {"name": "Bronx (SBH area, ZIP 10457 centroid)", "lat": 40.8457, "lon": -73.8979}


def curl(url):
    return subprocess.run(["curl", "-sS", "-f", "-A", UA, url], check=True, capture_output=True).stdout


def ms_ts(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v / 1000, timezone.utc).strftime("%Y-%m-%d")
    return str(v)


def p_above(cat, prob):
    if prob is None or cat is None or str(cat).upper().startswith("EC"):
        return 33.3
    c = str(cat).lower()
    if c.startswith("above"):
        return float(prob)
    if c.startswith("below"):
        return round(100 - float(prob) - 33.3, 1)
    return round((100 - float(prob)) / 2, 1)


def query_layer(service, layer, label):
    geom = json.dumps({"x": POINT["lon"], "y": POINT["lat"], "spatialReference": {"wkid": 4326}})
    q = urllib.parse.urlencode({"geometry": geom, "geometryType": "esriGeometryPoint", "inSR": 4326,
                                "spatialRel": "esriSpatialRelIntersects", "outFields": "*",
                                "returnGeometry": "false", "f": "json"})
    url = f"{MS}/{service}/MapServer/{layer}/query?{q}"
    d = json.loads(curl(url))
    (RAW / f"{service}_layer{layer}.json").write_text(json.dumps(d, indent=1))
    feats = [f["attributes"] for f in d.get("features", [])]
    if not feats:
        # Equal chances: point is not in any probability polygon; get issue info from any feature
        q2 = urllib.parse.urlencode({"where": "1=1", "outFields": "*", "returnGeometry": "false",
                                     "resultRecordCount": 1, "f": "json"})
        anyf = json.loads(curl(f"{MS}/{service}/MapServer/{layer}/query?{q2}")).get("features", [])
        a = anyf[0]["attributes"] if anyf else {}
        cat, prob = "EC", None
    else:
        a = max(feats, key=lambda x: x.get("prob") or 0)  # innermost (highest-probability) contour
        cat, prob = a.get("cat"), a.get("prob")
    return {
        "outlook": label, "source": f"{MS}/{service}/MapServer/{layer}",
        "issued": ms_ts(a.get("fcst_date")),
        "valid_start": ms_ts(a.get("start_date")), "valid_end": ms_ts(a.get("end_date")),
        "valid_season": a.get("valid_seas"),
        "favored_category": cat, "prob_favored_pct": prob,
        "p_above_normal_est_pct": p_above(cat, prob),
        "service_file_date_utc": ms_ts(a.get("idp_filedate")),
    }


def week34():
    import shapefile
    from shapely.geometry import Point, shape
    raw = curl(WK34)
    (RAW / "wk34temp_latest.zip").write_bytes(raw)
    z = zipfile.ZipFile(io.BytesIO(raw))
    names = z.namelist()
    base = [n[:-4] for n in names if n.lower().endswith(".shp")][0]
    r = shapefile.Reader(shp=io.BytesIO(z.read(base + ".shp")), dbf=io.BytesIO(z.read(base + ".dbf")),
                         shx=io.BytesIO(z.read(base + ".shx")))
    fields = [f[0] for f in r.fields[1:]]
    pt = Point(POINT["lon"], POINT["lat"])
    hits, sample = [], None
    for sr in r.iterShapeRecords():
        rec = dict(zip(fields, sr.record))
        sample = sample or rec
        if shape(sr.shape.__geo_interface__).contains(pt):
            hits.append(rec)
    probkey = next((k for k in fields if k.lower().startswith("prob")), None)
    catkey = next((k for k in fields if k.lower().startswith("cat")), None)
    if hits:
        a = max(hits, key=lambda x: float(x.get(probkey) or 0))
        cat, prob = a.get(catkey), a.get(probkey)
    else:
        a, cat, prob = sample or {}, "EC", None
    return {"outlook": "Week 3-4 temperature", "source": WK34, "shapefile_member": base, "fields": fields,
            "record_at_point": {k: str(v) for k, v in a.items()} if hits else None,
            "issued": str(a.get("Fcst_Date") or a.get("FCST_DATE") or a.get("fcst_date") or ""),
            "valid_start": str(a.get("Start_Date") or a.get("START_DATE") or ""),
            "valid_end": str(a.get("End_Date") or a.get("END_DATE") or ""),
            "favored_category": cat, "prob_favored_pct": prob, "p_above_normal_est_pct": p_above(cat, prob)}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    out = {"fetched_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "point": POINT,
           "note": "prob = probability (%) of favored tercile vs 1991-2020 normals; EC = equal chances 33/33/33. "
                   "p_above_normal_est_pct is derived (see script docstring), not published by CPC.",
           "outlooks": []}
    out["outlooks"].append(query_layer("cpc_6_10_day_outlk", 0, "6-10 day temperature"))
    out["outlooks"].append(query_layer("cpc_8_14_day_outlk", 0, "8-14 day temperature"))
    try:
        out["outlooks"].append(week34())
    except Exception as e:
        out["outlooks"].append({"outlook": "Week 3-4 temperature", "source": WK34, "error": str(e)})
    out["outlooks"].append(query_layer("cpc_mthly_temp_outlk", 0, "Monthly temperature"))
    for lead in range(13):
        out["outlooks"].append(query_layer("cpc_sea_temp_outlk", lead, f"Seasonal temperature lead {lead + 1}"))
    (ROOT / "data/processed/cpc_outlook_nyc.json").write_text(json.dumps(out, indent=1))
    for o in out["outlooks"]:
        print(o["outlook"], o.get("issued"), o.get("valid_start"), o.get("valid_end"), o.get("valid_season"),
              o.get("favored_category"), o.get("prob_favored_pct"), o.get("p_above_normal_est_pct"), o.get("error", ""))


if __name__ == "__main__":
    main()
