"""Intersection gazetteer from OpenStreetMap: nodes shared by named streets.
Input: ~/opt/nyc-concordance/osm/nyc_highways.json (Overpass, highway ways with names in the NYC bbox,
downloaded 13 Nov 2026 from overpass.private.coffee; OSM base timestamp in the file).
Output: data/derived/street_safety/osm_intersections.json (normalised name pair -> list of points),
with borough from NYC Borough Boundaries (gthc-hcne)."""
import json, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analyses/street_safety"))
from rlc_sites import norm  # noqa: E402

SRC = Path.home() / "opt/nyc-concordance/osm/nyc_highways.json"


def boroughs():
    import requests
    from shapely.geometry import shape
    f = ROOT / "data/derived/street_safety/borough_boundaries.geojson"
    if not f.exists():
        r = requests.get("https://data.cityofnewyork.us/resource/gthc-hcne.geojson", timeout=120)
        r.raise_for_status()
        f.write_text(r.text)
    gj = json.loads(f.read_text())
    return [(ft["properties"].get("boroname", "").upper(), shape(ft["geometry"])) for ft in gj["features"]]


def boro_of(lat, lon, polys):
    from shapely.geometry import Point
    p = Point(lon, lat)
    for name, g in polys:
        if g.contains(p):
            return name
    return None


def main():
    d = json.loads(SRC.read_text())
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in d["elements"] if e["type"] == "node"}
    names_at = defaultdict(set)
    for e in d["elements"]:
        if e["type"] == "way":
            nm = e.get("tags", {}).get("name")
            if not nm:
                continue
            n = norm(nm)
            alt = {norm(e["tags"][k]) for k in ("alt_name", "old_name", "official_name") if e["tags"].get(k)}
            for nd in e["nodes"]:
                names_at[nd].add(n)
                names_at[nd].update(alt)
    pairs = defaultdict(list)
    for nd, ns in names_at.items():
        if len(ns) < 2:
            continue
        ns = sorted(ns)
        for i in range(len(ns)):
            for j in range(i + 1, len(ns)):
                pairs[f"{ns[i]}|{ns[j]}"].append(nodes[nd])
    polys = boroughs()
    out = {}
    for k, pts in pairs.items():
        lat = sum(p[0] for p in pts) / len(pts); lon = sum(p[1] for p in pts) / len(pts)
        # split into clusters if the same pair meets far apart (e.g. two crossings); keep each cluster
        cl = []
        for p in pts:
            for c in cl:
                if abs(c[0][0] - p[0]) < 0.002 and abs(c[0][1] - p[1]) < 0.002:
                    c.append(p); break
            else:
                cl.append([p])
        out[k] = [{"lat": sum(p[0] for p in c) / len(c), "lon": sum(p[1] for p in c) / len(c)} for c in cl]
    for k, v in out.items():
        for c in v:
            c["boro"] = boro_of(c["lat"], c["lon"], polys)
    meta = {"source": "OpenStreetMap via Overpass API (overpass.private.coffee)", "osm_base": d.get("osm3s", {}).get("timestamp_osm_base"),
            "query": "way[highway~motorway_link|trunk|primary|secondary|tertiary(+_link)|residential|unclassified][name] in bbox 40.49,-74.27,40.92,-73.68",
            "licence": "ODbL 1.0"}
    (ROOT / "data/derived/street_safety/osm_intersections.json").write_text(json.dumps({"meta": meta, "pairs": out}))
    print("pairs", len(out))


if __name__ == "__main__":
    main()
