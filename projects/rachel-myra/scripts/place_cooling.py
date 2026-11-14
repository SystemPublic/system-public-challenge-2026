"""NYC cooling places -> data/processed/cooling_places_nyc.geojson (one Point per place, `source` field).

Sources (priority order; lower-priority records within 50 m of an already-kept place are dropped and their
source is appended to `also_in`):
  1. nycem_cool_options  NYC Emergency Management "Cool Options" finder layer (finder.nyc.gov/coolingcenters),
     ArcGIS FeatureServer services6.arcgis.com/yG5s3afENB5iO9fj/.../Cool_Options/FeatureServer/0.
     Indoor cooling centers (older adult centers, libraries, Petco, etc.) with hours + accessibility,
     plus outdoor spray showers / pools. Agency + facility type joined from Cooling_Centers_PROD_view
     (services5.arcgis.com/tMsas0Edz7Aih7fO) on NYCEM_ID. Seasonal: Finder_status reflects the 2026 season
     record at download; the app-level status flag was "Open" (last edit 2026-10-21).
  2. nyc_parks_rec_center  NYC Parks recreation centers feed (nycgovparks.org/bigapps/DPR_RecreationCenter_001.json)
     with building hours; coordinates from NYC Parks Structures (n8q6-i44s, recreation_center=true, footprint
     centroid by property) else NYC GeoSearch geocode of the address.
  3. facdb_public_library  NYC Facilities Database (ji82-xba5) PUBLIC LIBRARY rows (NYPL, BPL, QPL).
  4. queens_library  Queens Library Branches (kh3d-xhq7) - adds hours URL.
  5. osm  OpenStreetMap via Overpass (library, community_centre, social_centre, mall, department_store,
     senior outreach; plus anything else tagged air_conditioning=yes in those public categories).
Hours/accessibility fields are passed through where the source has them; they are blank otherwise.

python3 scripts/place_cooling.py
"""
import json, math, os, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "place")
OUT = os.path.join(ROOT, "data", "processed")
UA = {"User-Agent": "hackathon-data-script/1.0"}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def fetch(url):
    for a in range(5):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read())
        except Exception as e:
            print("retry", e)
            time.sleep(3 * (a + 1))
    return None


def dist_m(a, b):
    return math.hypot((a[0] - b[0]) * 111320 * math.cos(math.radians(a[1])), (a[1] - b[1]) * 110540)


def centroid(geom):
    pts = []

    def walk(c):
        if isinstance(c[0], (int, float)):
            pts.append(c)
        else:
            for x in c:
                walk(x)
    walk(geom["coordinates"])
    return [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]


places = []


def add(rec):
    if rec.get("coords") is None:
        return
    for p in places:
        if dist_m(p["coords"], rec["coords"]) <= 50 and (p["indoor"] == rec["indoor"]):
            if rec["source"] != p["source"] and rec["source"] not in p["also_in"]:
                p["also_in"].append(rec["source"])
                for k in ("opening_hours", "hours_url", "wheelchair", "accessible"):
                    if not p.get(k) and rec.get(k):
                        p[k] = rec[k]
            if rec["source"] != p["source"]:
                return
    rec.setdefault("also_in", [])
    places.append(rec)


# 1. NYC EM Cool Options ------------------------------------------------------
prod = {f["properties"]["NYCEM_ID"]: f["properties"]
        for f in json.load(open(os.path.join(RAW, "cooling", "cooling_centers_prod.geojson")))["features"]}
for f in json.load(open(os.path.join(RAW, "cooling", "cool_options_all.geojson")))["features"]:
    p = f["properties"]
    if not f.get("geometry"):
        continue
    x = prod.get(p["NYCEM_ID"], {})
    hours = {d: p.get(d) for d in DAYS if p.get(d)}
    add({"name": p["Facility_name"], "category": (p["Space_type"] or "").lower(),
         "indoor": p["Location_type"] == "Indoor", "address": p.get("Address") or x.get("ADDRESS"),
         "borough": p.get("Borough_name"), "zip": p.get("ZIP_code"), "phone": p.get("Phone"),
         "operator": x.get("Operating_agency"), "facility_type": x.get("FACILITY_TYPE"),
         "official_cooling_center": p["Space_type"] in ("Cooling Center", "Other Indoor Cool Option"),
         "finder_status": p.get("Finder_status"), "accessible": p.get("Accessible"),
         "pet_friendly": p.get("Pet_friendly"), "age_restriction": p.get("Age_restriction"),
         "entrance_info": p.get("Entrance_information"), "hours": hours or None,
         "source_id": p["NYCEM_ID"], "source": "nycem_cool_options",
         "coords": f["geometry"]["coordinates"][:2]})
print("after Cool Options", len(places))

# 2. NYC Parks rec centers ----------------------------------------------------
struct = {}
for s in json.load(open(os.path.join(RAW, "cooling", "parks_structures_reccenter.json"))):
    if s.get("multipolygon"):
        struct.setdefault(s["gispropnum"], []).append(centroid(s["multipolygon"]))
geo_cache_path = os.path.join(RAW, "cooling", "geosearch_cache.json")
geo_cache = json.load(open(geo_cache_path)) if os.path.exists(geo_cache_path) else {}
for r in json.load(open(os.path.join(RAW, "cooling", "nycparks_reccenters.json"))):
    coords, how = None, ""
    if r["Prop_ID"] in struct:
        cs = struct[r["Prop_ID"]]
        coords, how = [sum(c[0] for c in cs) / len(cs), sum(c[1] for c in cs) / len(cs)], "parks_structures_centroid"
    else:
        q = f"{r['ADDRESS']}, {r['CITY']}, NY {r['ZIP']}"
        if q not in geo_cache:
            g = fetch("https://geosearch.planninglabs.nyc/v2/search?" + urllib.parse.urlencode({"text": q, "size": 1}))
            ft = (g or {}).get("features") or []
            geo_cache[q] = {"coords": ft[0]["geometry"]["coordinates"], "conf": ft[0]["properties"].get("confidence")} if ft else None
        if geo_cache[q]:
            coords, how = geo_cache[q]["coords"], f"geosearch (confidence {geo_cache[q]['conf']})"
    bh = r.get("Building_Hours") or {}
    hours = {d: f"{bh[d.upper()]['startTime'][:5]}-{bh[d.upper()]['endTime'][:5]}" for d in DAYS
             if bh.get(d.upper(), {}).get("startTime") and bh[d.upper()].get("endTime")}
    add({"name": r["NAME"], "category": "recreation center", "indoor": True,
         "address": r["ADDRESS"], "borough": r.get("CITY"), "zip": r.get("ZIP"), "phone": r.get("PHONE"),
         "operator": "NYC Parks", "facility_type": r.get("RecreationCenter_Type"), "official_cooling_center": False,
         "hours": hours or None, "membership_required": "NYC Parks rec center membership generally required",
         "source_id": r["Prop_ID"], "source": "nyc_parks_rec_center", "coord_method": how, "coords": coords})
json.dump(geo_cache, open(geo_cache_path, "w"))
print("after Parks", len(places))

# 3. FacDB public libraries -----------------------------------------------------
fac_path = os.path.join(RAW, "cooling", "facdb_public_libraries.json")
if not os.path.exists(fac_path):
    json.dump(fetch("https://data.cityofnewyork.us/resource/ji82-xba5.json?factype=PUBLIC%20LIBRARY&$limit=1000"), open(fac_path, "w"))
for r in json.load(open(fac_path)):
    if not r.get("latitude"):
        continue
    add({"name": r["facname"].title(), "category": "library", "indoor": True, "address": r.get("address"),
         "borough": (r.get("boro") or "").title(), "zip": r.get("zipcode"), "operator": r.get("overabbrev"),
         "facility_type": "Public library", "official_cooling_center": False,
         "source_id": r["uid"], "source": "facdb_public_library",
         "coords": [float(r["longitude"]), float(r["latitude"])]})
print("after FacDB", len(places))

# 4. Queens Library -------------------------------------------------------------
ql_path = os.path.join(RAW, "cooling", "queens_library_branches.json")
if not os.path.exists(ql_path):
    json.dump(fetch("https://data.cityofnewyork.us/resource/kh3d-xhq7.json?$limit=500"), open(ql_path, "w"))
# Queens Library coordinates are rounded to 0.01 deg (~1 km), so only attach phone/hours URL by name to the
# FacDB QPL record; branches with no FacDB match are added with coord_precision="~1 km".
by_name = {}
for p in places:
    if p.get("operator") == "QPL":
        by_name.setdefault(p["name"].lower().replace(" library", "").replace("-", " ").strip(), p)
for r in json.load(open(ql_path)):
    url = (r.get("hours_can_be_viewed_via_branch_url_") or {}).get("url")
    m = by_name.get(r["name"].lower().replace("-", " ").strip())
    if m:
        m["hours_url"], m["phone"] = url, r.get("phone")
        m["also_in"].append("queens_library")
    elif r.get("point"):
        add({"name": r["name"] + " (Queens Public Library)", "category": "library", "indoor": True,
             "address": r.get("address"), "borough": "Queens", "zip": r.get("postcode"), "phone": r.get("phone"),
             "operator": "QPL", "facility_type": "Public library", "official_cooling_center": False,
             "hours_url": url, "coord_precision": "~1 km (source rounds to 0.01 deg)",
             "source_id": r["name"], "source": "queens_library", "coords": r["point"]["coordinates"]})
print("after Queens Library", len(places))

# 5. OSM ----------------------------------------------------------------------
KEEP = {("amenity", "library"): "library", ("amenity", "community_centre"): "community centre",
        ("amenity", "social_centre"): "social centre", ("shop", "mall"): "mall",
        ("shop", "department_store"): "department store", ("social_facility", "outreach"): "senior centre"}
osm = json.load(open(os.path.join(RAW, "osm", "osm_cooling_nyc.json")))
for e in osm["elements"]:
    t = e.get("tags", {})
    cat = next((v for (k, val), v in KEEP.items() if t.get(k) == val), None)
    if not cat:
        continue  # air_conditioning=yes restaurants/shops/etc. are not public cooling places
    c = [e["lon"], e["lat"]] if "lon" in e else ([e["center"]["lon"], e["center"]["lat"]] if "center" in e else None)
    add({"name": t.get("name") or f"(unnamed {cat})", "category": cat, "indoor": True,
         "address": " ".join(x for x in [t.get("addr:housenumber", ""), t.get("addr:street", "")] if x) or None,
         "zip": t.get("addr:postcode"), "operator": t.get("operator") or t.get("brand"),
         "official_cooling_center": False, "opening_hours": t.get("opening_hours"),
         "wheelchair": t.get("wheelchair"), "air_conditioning": t.get("air_conditioning"),
         "source_id": f"{e['type']}/{e['id']}", "source": "osm", "coords": c})
print("after OSM", len(places))

feats = []
for p in places:
    c = p.pop("coords")
    p["also_in"] = "; ".join(p["also_in"])
    feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(c[0], 6), round(c[1], 6)]},
                  "properties": {k: v for k, v in p.items() if v not in (None, "", [])}})
json.dump({"type": "FeatureCollection", "features": feats,
           "metadata": {"accessed": "2026-11-14", "osm_base": osm.get("osm3s", {}).get("timestamp_osm_base")}},
          open(os.path.join(OUT, "cooling_places_nyc.geojson"), "w"), separators=(",", ":"))
from collections import Counter
print(len(feats), Counter(f["properties"]["source"] for f in feats), Counter(f["properties"]["category"] for f in feats))
