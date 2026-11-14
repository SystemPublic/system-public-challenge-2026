"""Pharmacies in the SBH Health System catchment (11 primary-service-area ZIPs from SBH 2025-27 CSP).

Sources:
  1. CMS NPPES NPI Registry API (organization NPIs, taxonomy "pharmacy", location address in the ZIP).
     The NY taxonomy "license" field is the NYS Board of Pharmacy registration number (no bulk NYS
     registry is published as open data). Addresses geocoded with NYC Planning GeoSearch (Pelias, no key).
  2. OpenStreetMap amenity=pharmacy/healthcare=pharmacy within NYC (Overpass; raw file
     data/raw/place/osm/osm_pharmacy_nyc.json) clipped to the catchment ZIP polygons (MODZCTA).
NPPES and OSM records are matched when within 60 m; unmatched records from either source are kept.

Output: data/processed/pharmacies_sbh_catchment.geojson ; raw API responses in data/raw/place/pharmacies/.
python3 scripts/place_pharmacies.py
"""
import csv, json, math, os, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "place")
OUT = os.path.join(ROOT, "data", "processed")
os.makedirs(os.path.join(RAW, "pharmacies"), exist_ok=True)
ZIPS = [r["zip"] for r in csv.DictReader(open(os.path.join(OUT, "sbh_catchment_zips.csv")))]
UA = {"User-Agent": "hackathon-data-script/1.0"}


def fetch(url):
    for a in range(5):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except Exception as e:
            print("retry", e)
            time.sleep(3 * (a + 1))
    return None


def pip(pt, poly):  # point in polygon (ring list), ray casting
    x, y = pt
    inside = False
    for ring in poly:
        for i in range(len(ring)):
            (x1, y1), (x2, y2) = ring[i - 1][:2], ring[i][:2]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside


def zip_of(pt, shapes):
    for z, geom in shapes.items():
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        if any(pip(pt, p) for p in polys):
            return z
    return None


def dist_m(a, b):
    dx = (a[0] - b[0]) * 111320 * math.cos(math.radians(a[1]))
    dy = (a[1] - b[1]) * 110540
    return math.hypot(dx, dy)


# NPPES ----------------------------------------------------------------------
cache = os.path.join(RAW, "pharmacies", "nppes_pharmacy_catchment.json")
if os.path.exists(cache):
    nppes = json.load(open(cache))
else:
    nppes = []
    for z in ZIPS:
        skip = 0
        while True:
            d = fetch("https://npiregistry.cms.hhs.gov/api/?" + urllib.parse.urlencode(
                {"version": "2.1", "postal_code": z, "taxonomy_description": "pharmacy", "enumeration_type": "NPI-2",
                 "limit": 200, "skip": skip})) or {}
            res = d.get("results", [])
            nppes += res
            if len(res) < 200:
                break
            skip += 200
    json.dump(nppes, open(cache, "w"))
print("NPPES records", len(nppes))

geo_cache_path = os.path.join(RAW, "pharmacies", "geosearch_cache.json")
geo_cache = json.load(open(geo_cache_path)) if os.path.exists(geo_cache_path) else {}
recs = {}
for r in nppes:
    loc = next((a for a in r["addresses"] if a["address_purpose"] == "LOCATION"), None)
    if not loc or loc["postal_code"][:5] not in ZIPS:
        continue
    tax = [t for t in r["taxonomies"] if "harmacy" in (t.get("desc") or "")]
    prim = next((t for t in tax if t.get("primary")), tax[0] if tax else {})
    addr = f"{loc['address_1']}, {loc['city']}, NY {loc['postal_code'][:5]}"
    if addr not in geo_cache:
        g = fetch("https://geosearch.planninglabs.nyc/v2/search?" + urllib.parse.urlencode({"text": addr, "size": 1}))
        f = (g or {}).get("features") or []
        geo_cache[addr] = {"coords": f[0]["geometry"]["coordinates"], "confidence": f[0]["properties"].get("confidence"),
                           "label": f[0]["properties"].get("label")} if f else None
        time.sleep(0.1)
    g = geo_cache[addr]
    nys_reg = next((t.get("license") for t in tax if t.get("state") == "NY" and t.get("license")), "")
    recs["npi" + r["number"]] = {
        "name": r["basic"].get("organization_name"), "dba": (r["basic"].get("other_organization_name") or ""),
        "address": loc["address_1"] + (" " + loc["address_2"] if loc.get("address_2") else ""),
        "zip": loc["postal_code"][:5], "phone": loc.get("telephone_number", ""), "npi": r["number"],
        "taxonomy": prim.get("desc", ""), "nys_registration": nys_reg,
        "npi_status": r["basic"].get("status"), "last_updated": r["basic"].get("last_updated"),
        "coords": g["coords"] if g else None, "geocode_confidence": g["confidence"] if g else None,
        "source": "CMS NPPES NPI Registry API; geocoded NYC GeoSearch"}
json.dump(geo_cache, open(geo_cache_path, "w"))

# OSM ------------------------------------------------------------------------
shapes = {f["properties"]["modzcta"]: f["geometry"]
          for f in json.load(open(os.path.join(RAW, "boundaries", "modzcta.geojson")))["features"]
          if f["properties"]["modzcta"] in ZIPS}
osm = json.load(open(os.path.join(RAW, "osm", "osm_pharmacy_nyc.json")))
osm_recs = []
for e in osm["elements"]:
    if e["tags"].get("amenity") not in ("pharmacy", None) and e["tags"].get("healthcare") != "pharmacy":
        continue
    lon, lat = (e.get("lon"), e.get("lat")) if "lon" in e else (e["center"]["lon"], e["center"]["lat"])
    z = zip_of((lon, lat), shapes)
    if z:
        t = e["tags"]
        osm_recs.append({"osm_id": f"{e['type']}/{e['id']}", "name": t.get("name", ""), "brand": t.get("brand", ""),
                         "address": " ".join(x for x in [t.get("addr:housenumber", ""), t.get("addr:street", "")] if x),
                         "zip": z, "opening_hours": t.get("opening_hours", ""), "wheelchair": t.get("wheelchair", ""),
                         "dispensing": t.get("dispensing", ""), "coords": [lon, lat]})
print("OSM pharmacies in catchment", len(osm_recs))

# merge ----------------------------------------------------------------------
feats, used = [], set()
for k, r in recs.items():
    m = None
    if r["coords"]:
        best = min(((dist_m(r["coords"], o["coords"]), i) for i, o in enumerate(osm_recs) if i not in used), default=None)
        if best and best[0] <= 60:
            m = osm_recs[best[1]]
            used.add(best[1])
    p = {k2: v for k2, v in r.items() if k2 != "coords"}
    if m:
        p.update({"osm_id": m["osm_id"], "osm_name": m["name"], "opening_hours": m["opening_hours"],
                  "wheelchair": m["wheelchair"], "source": p["source"] + "; matched OSM"})
    feats.append({"type": "Feature", "properties": p,
                  "geometry": {"type": "Point", "coordinates": [round(c, 6) for c in r["coords"]]} if r["coords"] else None})
for i, o in enumerate(osm_recs):
    if i in used:
        continue
    p = {k: v for k, v in o.items() if k != "coords"}
    p["source"] = "OpenStreetMap (Overpass), not matched to NPPES"
    feats.append({"type": "Feature", "properties": p,
                  "geometry": {"type": "Point", "coordinates": [round(c, 6) for c in o["coords"]]}})
json.dump({"type": "FeatureCollection", "features": feats},
          open(os.path.join(OUT, "pharmacies_sbh_catchment.geojson"), "w"), separators=(",", ":"))
print("features", len(feats), "NPPES", len(recs), "matched OSM", len(used), "OSM-only", len(osm_recs) - len(used),
      "NPPES ungeocoded", sum(1 for r in recs.values() if not r["coords"]))
