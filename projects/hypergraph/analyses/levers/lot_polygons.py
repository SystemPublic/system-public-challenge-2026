"""MapPLUTO lot polygons for land use 11, from the Department of City Planning's ArcGIS feature service.

Writes ~/opt/nyc-concordance/levers/lu11_polygons.geojson (outside Dropbox) and a source record in
data/derived/levers/lot_polygons_source.json.
"""
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
URL = "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/MAPPLUTO/FeatureServer/0/query"
OUTD = Path.home() / "opt" / "nyc-concordance" / "levers"


def main():
    OUTD.mkdir(parents=True, exist_ok=True)
    feats, off = [], 0
    while True:
        for attempt in range(6):
            try:
                r = requests.get(URL, params={"where": "LandUse='11'", "outFields": "BBL,LotArea,Version", "outSR": 4326,
                                              "f": "geojson", "resultOffset": off, "resultRecordCount": 2000,
                                              "orderByFields": "OBJECTID"}, timeout=60)
                r.raise_for_status()
                break
            except requests.RequestException:
                time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(f"MapPLUTO service failed at offset {off}")
        fs = r.json().get("features", [])
        feats += fs
        if len(fs) < 2000:
            break
        off += len(fs)
        time.sleep(0.3)
    (OUTD / "lu11_polygons.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    vers = sorted({str(f["properties"].get("Version")) for f in feats})
    (ROOT / "data/derived/levers/lot_polygons_source.json").write_text(json.dumps(
        {"url": URL, "where": "LandUse='11'", "n": len(feats), "versions": vers,
         "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "path": "~/opt/nyc-concordance/levers/lu11_polygons.geojson"}, indent=1))
    print(len(feats), vers)


if __name__ == "__main__":
    main()
