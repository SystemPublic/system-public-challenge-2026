"""Tract sets for further-chinatown-shift, built from geometry and lookup tables only
(DCP NTA equivalency 8ius-dhrr, Census Gazetteer internal points, DCP/DoITT centerline inkn-q76z).
No population counts are read here. Output: data/derived/further/chinatown_sets.json"""
import json, math, csv, sys
from pathlib import Path
from concord import socrata as s
ROOT = Path(__file__).resolve().parents[2]
EXT = Path.home() / "opt/nyc-concordance/chinatown"
OUT = ROOT / "data/derived/further"; OUT.mkdir(parents=True, exist_ok=True)

def hav(lat1, lon1, lat2, lon2):
    R = 6371000; p = math.pi / 180
    a = math.sin((lat2-lat1)*p/2)**2 + math.cos(lat1*p)*math.cos(lat2*p)*math.sin((lon2-lon1)*p/2)**2
    return 2*R*math.asin(math.sqrt(a))

def pt_seg(lat, lon, a, b):
    # local planar approximation; a,b = (lon,lat)
    k = math.cos(lat*math.pi/180)
    ax, ay, bx, by = a[0]*k, a[1], b[0]*k, b[1]
    px, py = lon*k, lat
    dx, dy = bx-ax, by-ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
    return hav(lat, lon, ay+t*dy, (ax+t*dx)/k)

def gaz(fn, vintage):
    out = {}
    with open(EXT / fn, encoding="utf-8-sig") as f:
        hdr = [h.strip() for h in f.readline().split("\t")]
        for line in f:
            r = dict(zip(hdr, [x.strip() for x in line.split("\t")]))
            g = r["GEOID"]
            if g[:5] in ("36061", "36047", "36081"):
                out[g] = (float(r["INTPTLAT"]), float(r["INTPTLONG"]))
    return out

g10 = gaz("Gaz_tracts_national.txt", 2010); g20 = gaz("2020_Gaz_tracts_national.txt", 2020)
rows, src = s.query("8ius-dhrr", limit=3000)
fips = {"Manhattan": "36061", "Brooklyn": "36047", "Queens": "36081"}
nta = {}
for r in rows:
    if r["borough"] in fips:
        nta[fips[r["borough"]] + r["_2010_census_tract"].zfill(6)] = (r["neighborhood_tabulation_area_nta_code"], r["neighborhood_tabulation_area_nta_name"])
sets = {"source_nta_equivalency": src}
sets["chinatown_B1"] = sorted(g for g, v in nta.items() if v[0] in ("MN27", "MN28"))
sets["chinatown_B2"] = sorted(g for g, v in nta.items() if v[0] == "MN27")
sets["chinatown_B3"] = sorted(g for g, v in nta.items() if v[0] in ("MN27", "MN28", "MN22"))
st = json.load(open(EXT / "lion_streets.json"))
def segs(name, boro, bbox):
    out = []
    for r in st:
        if r["full_street_name"] == name and r["boroughcode"] == boro:
            for line in r["the_geom"]["coordinates"]:
                for a, b in zip(line, line[1:]):
                    if bbox[0] <= a[1] <= bbox[1] and bbox[2] <= a[0] <= bbox[3] and bbox[0] <= b[1] <= bbox[1]:
                        out.append((a, b))
    return out
# 8th Avenue, Brooklyn, 40th St to 65th St (about lat 40.620 to 40.647)
s8 = segs("8 AVE", "3", (40.620, 40.648, -74.02, -73.99))
sp = [g for g, v in nta.items() if v[0] in ("BK32", "BK34")]
sets["sunset_park_all"] = sorted(sp)
sets["sunset_park_core"] = sorted(g for g in sp if min(pt_seg(*g10[g], a, b) for a, b in s8) <= 400)
sets["sunset_park_periphery"] = sorted(set(sp) - set(sets["sunset_park_core"]))
sets["sunset_park_8th_ave_segments"] = len(s8)
# Flushing: centre = intersection of Main St and Roosevelt Ave (Queens); use Roosevelt Ave segment endpoint nearest Main St
ms = segs("MAIN ST", "4", (40.74, 40.77, -73.85, -73.81)); ra = segs("ROOSEVELT AVE", "4", (40.74, 40.77, -73.85, -73.81))
best = min(((hav(a[1], a[0], c[1], c[0]), a) for seg1 in ms for a in seg1 for seg2 in ra for c in seg2))
cen = (best[1][1], best[1][0]); sets["flushing_centre_latlon"] = cen; sets["flushing_centre_gap_m"] = round(best[0], 1)
fl = [g for g, v in nta.items() if v[0] in ("QN22", "QN51", "QN52")]
sets["flushing_all"] = sorted(fl)
sets["flushing_core"] = sorted(g for g in fl if hav(*g10[g], *cen) <= 700)
sets["flushing_periphery"] = sorted(set(fl) - set(sets["flushing_core"]))
sets["rule"] = {"sunset_core": "2010 tracts of NTAs BK32+BK34 whose Gazetteer internal point is within 400 m of a centreline segment of 8 AVE (Brooklyn) between 40.620 and 40.648 N",
                "flushing_core": "2010 tracts of NTAs QN22+QN51+QN52 whose internal point is within 700 m of the Main St / Roosevelt Av intersection"}
json.dump(sets, open(OUT / "chinatown_sets.json", "w"), indent=1)
for k, v in sets.items():
    if isinstance(v, list): print(k, len(v))
print(cen, sets["flushing_centre_gap_m"], len(s8))
