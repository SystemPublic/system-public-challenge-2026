"""Extract NYC subway stations (GTFS parent stations, location_type=1) from the MTA static subway GTFS.

Input: data/raw/place/gtfs/gtfs_subway.zip  (https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip)
Output: data/processed/subway_stations_nyc.geojson  (stop_id, stop_name, routes serving the station)
python3 scripts/place_gtfs_stations.py
"""
import csv, io, json, os, zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
z = zipfile.ZipFile(os.path.join(ROOT, "data", "raw", "place", "gtfs", "gtfs_subway.zip"))
rd = lambda n: csv.DictReader(io.TextIOWrapper(z.open(n), encoding="utf-8-sig"))
stops = list(rd("stops.txt"))
parent = {s["stop_id"]: (s.get("parent_station") or s["stop_id"]) for s in stops}
trip_route = {t["trip_id"]: t["route_id"] for t in rd("trips.txt")}
routes = defaultdict(set)
for st in rd("stop_times.txt"):
    routes[parent.get(st["stop_id"], st["stop_id"])].add(trip_route.get(st["trip_id"], ""))
feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(s["stop_lon"]), float(s["stop_lat"])]},
          "properties": {"stop_id": s["stop_id"], "stop_name": s["stop_name"], "routes": " ".join(sorted(routes[s["stop_id"]])),
                         "source": "MTA subway GTFS static"}}
         for s in stops if s.get("location_type") == "1"]
json.dump({"type": "FeatureCollection", "features": feats},
          open(os.path.join(ROOT, "data", "processed", "subway_stations_nyc.geojson"), "w"), separators=(",", ":"))
print(len(feats), "stations")
