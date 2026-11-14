"""Build data/processed/community_resources_nyc.geojson: every community place that can help
someone in a heat wave (cool indoor places, libraries, senior centers, food pantries / soup kitchens,
community centers, community organizations and nonprofits, homeless drop-in services).

Sources (all public, no key):
  - NYC Facilities Database (DCP), NYC Open Data ji82-xba5 (selected sub-groups)
  - NYC Aging providers with sites open to the public, u7wp-np5k
  - NYCHA community facilities, crns-fw6u
  - DHS homeless drop-in centers, bmxf-3rd4
  - NYC Community Based Organizations (NYC Service), i4kb-6ab6
  - NYC Care community-based organizations page (scraped), geocoded with NYC Planning GeoSearch
  - existing data/processed/cooling_places_nyc.geojson (NYC EM Cool Options, OSM, libraries, rec centers)
Raw downloads are cached in data/raw/community/. Run:  py -3 scripts/community_resources.py
"""
import datetime as dt
import html
import json
import os
import re
import time

import requests

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data", "raw", "community")
OUT = os.path.join(ROOT, "data", "processed", "community_resources_nyc.geojson")
COOL = os.path.join(ROOT, "data", "processed", "cooling_places_nyc.geojson")
TODAY = dt.date.today().isoformat()
S = requests.Session()
S.headers["User-Agent"] = "heat-med-hackathon-data-script"
os.makedirs(RAW, exist_ok=True)

FACDB_TYPES = {
    "PUBLIC LIBRARIES": "Library",
    "SENIOR SERVICES": "Senior center",
    "SOUP KITCHENS AND FOOD PANTRIES": "Food pantry / soup kitchen",
    "COMMUNITY CENTERS AND COMMUNITY PROGRAMS": "Community center",
    "NON-RESIDENTIAL HOUSING AND HOMELESS SERVICES": "Homeless services",
    "IMMIGRANT SERVICES": "Community organization",
    "FINANCIAL ASSISTANCE AND SOCIAL SERVICES": "Community organization",
    "PROGRAMS FOR PEOPLE WITH DISABILITIES": "Community organization",
}
COOL_TYPES = {
    "cooling center": "Cooling center",
    "library": "Library",
    "community centre": "Community center",
    "social centre": "Community center",
    "recreation center": "Recreation center",
    "mall": "Cool indoor public place",
    "department store": "Cool indoor public place",
    "other indoor cool option": "Cool indoor public place",
    "spray shower": "Outdoor spray shower / pool",
    "pool": "Outdoor spray shower / pool",
}


def socrata(dsid, where=None):
    fn = os.path.join(RAW, f"{dsid}.json")
    if os.path.exists(fn):
        return json.load(open(fn, encoding="utf-8"))
    params = {"$limit": 50000}
    if where:
        params["$where"] = where
    r = S.get(f"https://data.cityofnewyork.us/resource/{dsid}.json", params=params, timeout=120)
    r.raise_for_status()
    rows = r.json()
    json.dump(rows, open(fn, "w", encoding="utf-8"))
    return rows


def fnum(x):
    try:
        v = float(x)
        return v if v == v and v != 0 else None
    except (TypeError, ValueError):
        return None


def clean(s):
    if s is None:
        return None
    s = html.unescape(re.sub(r"<[^>]+>", " ", str(s)))
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def titlecase(s):
    s = clean(s)
    if s and s.isupper():
        s = s.title()
    return s


features = []


def add(name, typ, lat, lon, source, **props):
    lat, lon = fnum(lat), fnum(lon)
    name = titlecase(name)
    if not name or lat is None or lon is None or not (40.4 < lat < 41.0 and -74.3 < lon < -73.6):
        return
    p = {"name": name, "type": typ}
    for k in ("address", "borough", "zip", "phone", "website", "hours", "services", "languages", "operator"):
        v = props.get(k)
        v = titlecase(v) if k in ("address", "borough", "operator") else clean(v)
        p[k] = v
    p["source"] = source
    p["accessed"] = TODAY
    features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                     "properties": p})


# 1. NYC Facilities Database
subs = ",".join("'" + s + "'" for s in FACDB_TYPES)
for r in socrata("ji82-xba5", where=f"facsubgrp in ({subs})"):
    add(r.get("facname"), FACDB_TYPES[r["facsubgrp"]], r.get("latitude"), r.get("longitude"),
        "NYC Facilities Database (ji82-xba5)",
        address=r.get("address"), borough=r.get("boro"), zip=r.get("zipcode"),
        services=(r.get("factype") or "").capitalize() or None, operator=r.get("opname"))

# 2. NYC Aging sites open to the public
for r in socrata("u7wp-np5k"):
    add(r.get("site_name"), "Senior center", r.get("latitude"), r.get("longitude"),
        "NYC Aging sites open to the public (u7wp-np5k)",
        address=r.get("site_address"), borough=r.get("borough"), zip=r.get("zip_code"),
        services=r.get("provider_type"), operator=r.get("sponsor_vendor"))

# 3. NYCHA community facilities (only ones in use)
for r in socrata("crns-fw6u"):
    if (r.get("status") or "").lower().startswith("vacant"):
        continue
    add(r.get("sponsor") or r.get("development"), "Community center", r.get("latitude"), r.get("longitude"),
        "NYCHA community facilities (crns-fw6u)",
        address=r.get("address"), borough=r.get("borough"), zip=r.get("postcode"),
        services=f"{r.get('program_type')} at {r.get('development')}", operator=r.get("sponsor"))

# 4. Homeless drop-in centers
for r in socrata("bmxf-3rd4"):
    add(r.get("center_name"), "Homeless services", r.get("latitude"), r.get("longitude"),
        "DHS drop-in centers (bmxf-3rd4)",
        address=r.get("address"), borough=r.get("borough"), zip=r.get("postcode"),
        hours=r.get("comments"), services="Drop-in center")

# 5. NYC Service community-based organizations
for r in socrata("i4kb-6ab6"):
    web = r.get("website")
    add(r.get("organization_name"), "Community organization", r.get("latitude"), r.get("longitude"),
        "NYC Community Based Organizations (i4kb-6ab6)",
        address=r.get("street_address"), borough=r.get("borough"), zip=r.get("postcode"),
        website=web.get("url") if isinstance(web, dict) else web,
        services=(clean(r.get("mission")) or "")[:280] or None)


# 6. NYC Care community-based organizations (scraped + geocoded)
def geosearch(text):
    try:
        r = S.get("https://geosearch.planninglabs.nyc/v2/search", params={"text": text, "size": 1}, timeout=30)
        f = r.json().get("features") or []
        if f:
            lon, lat = f[0]["geometry"]["coordinates"]
            return lat, lon
    except Exception:
        pass
    return None, None


nc_fn = os.path.join(RAW, "nyccare_cbo.html")
if not os.path.exists(nc_fn):
    page = S.get("https://www.nyccare.nyc/community-based-organization/", timeout=60).text
    open(nc_fn, "w", encoding="utf-8").write(page)
page = open(nc_fn, encoding="utf-8").read()
nyccare = []
for m in re.finditer(r'<h2 class="f24 ctitle">(.*?)</h2>(.*?)(?=<h2|$)', page, re.S):
    name, body = clean(m.group(1)), m.group(2)
    paras = re.findall(r"<p>(?!<div)(.*?)</p>", body, re.S)
    text = paras[0] if paras else ""
    lines = [clean(x) for x in re.split(r"<br\s*/?>", text) if clean(x)]
    phone = re.search(r'href="tel:([^"]+)"', body)
    web = re.search(r'class="cread"><a[^>]*href="([^"]+)"', body)
    addr_lines = [l for l in lines[1:] if re.search(r"\d", l)]
    nyccare.append({"name": name, "desc": lines[0] if lines else None, "address": ", ".join(addr_lines) or None,
                    "phone": phone.group(1) if phone else None, "website": web.group(1) if web else None})
geo_fn = os.path.join(RAW, "nyccare_geocoded.json")
geo = json.load(open(geo_fn, encoding="utf-8")) if os.path.exists(geo_fn) else {}
for o in nyccare:
    if not o["address"]:
        continue
    if o["address"] not in geo:
        geo[o["address"]] = geosearch(o["address"])
        time.sleep(0.2)
    lat, lon = geo[o["address"]]
    zm = re.search(r"\b(1\d{4})\b", o["address"])
    add(o["name"], "Community organization", lat, lon, "NYC Care community-based organizations (nyccare.nyc, scraped)",
        address=o["address"], zip=zm.group(1) if zm else None, phone=o["phone"], website=o["website"],
        services=(o["desc"] or "") + " NYC Care enrollment partner.")
json.dump(geo, open(geo_fn, "w", encoding="utf-8"))
import csv
with open(os.path.join(ROOT, "data", "processed", "nyccare_cbos.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["name", "desc", "address", "phone", "website", "on_map"])
    w.writeheader()
    for o in nyccare:
        w.writerow({**o, "on_map": bool(o["address"] and geo.get(o["address"], [None])[0])})

# 7. Existing cooling places
cool = json.load(open(COOL, encoding="utf-8"))
for f in cool["features"]:
    p = f["properties"]
    lon, lat = f["geometry"]["coordinates"][:2]
    typ = COOL_TYPES.get((p.get("category") or "").lower(), "Cool indoor public place")
    add(p.get("name"), typ, lat, lon, f"cooling_places_nyc.geojson ({p.get('source')})",
        borough=p.get("borough"),
        services="Official NYC cooling center" if p.get("official_cooling_center") in (True, "true", "True") else None)

# Dedupe: same name (normalized) within ~100 m; keep the record with the most filled fields.
def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("library", "lib"))


best = {}
for f in features:
    lon, lat = f["geometry"]["coordinates"]
    key = (norm(f["properties"]["name"]), round(lat, 3), round(lon, 3))
    score = sum(v is not None for v in f["properties"].values())
    if key not in best or score > best[key][0]:
        best[key] = (score, f)
out = [v[1] for v in best.values()]
for i, f in enumerate(out):
    f["properties"]["id"] = f"CR{i:05d}"

json.dump({"type": "FeatureCollection",
           "metadata": {"built": TODAY, "script": "scripts/community_resources.py", "count": len(out),
                        "note": "Public directories; hours and services can change. Call ahead."},
           "features": out}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)

from collections import Counter
print("NYC Care orgs parsed:", len(nyccare), "| geocoded:", sum(1 for o in nyccare if o["address"] and geo.get(o["address"], [None])[0]))
print("before dedupe:", len(features), "after:", len(out))
for t, n in Counter(f["properties"]["type"] for f in out).most_common():
    print(f"  {n:6d}  {t}")
