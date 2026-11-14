"""NYC Hyperlocal Temperature Monitoring (NYC Open Data qdq3-9eqn): per-sensor summary via SoQL aggregation.

The table holds ~2.1M hourly rows (Jun 2018 - Oct 2019, ~423 sensors, Heat Vulnerability Index neighborhoods).
We never download it; we ask Socrata for per-sensor aggregates:
  - location, borough, NTA (2010 code), install type, hours of data, first/last day
  - mean / max / min air temperature (F), all hours
  - mean afternoon (13-17h) and night (0-5h) temperature, Jul-Aug only
  - hours >= 90F and >= 95F
Output: data/processed/hyperlocal_temp_sensors.csv (+ .geojson points), borough coverage table in
data/processed/hyperlocal_temp_borough_coverage.csv. Raw aggregate JSON in data/raw/place/hyperlocal/.

python3 scripts/place_hyperlocal_temp.py
"""
import csv, json, os, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "place", "hyperlocal")
OUT = os.path.join(ROOT, "data", "processed")
os.makedirs(RAW, exist_ok=True)
URL = "https://data.cityofnewyork.us/resource/qdq3-9eqn.json"
SBH_NTA2010 = {"BX36", "BX40", "BX41", "BX05", "BX17", "BX75", "BX01", "BX06", "BX30", "BX63"}  # informational only


def q(params, name):
    path = os.path.join(RAW, name)
    if os.path.exists(path):
        return json.load(open(path))
    url = URL + "?" + urllib.parse.urlencode(dict(params, **{"$limit": 50000}))
    for a in range(6):
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=300).read())
            json.dump(d, open(path, "w"))
            return d
        except Exception as e:
            print("retry", e)
            time.sleep(10 * (a + 1))
    raise RuntimeError(url)


G = "sensor_id,borough,ntacode,install_type"
base = q({"$select": G + ",avg(latitude) as lat,avg(longitude) as lon,count(*) as n_hours,min(day) as first_day,"
          "max(day) as last_day,avg(airtemp) as mean_f,max(airtemp) as max_f,min(airtemp) as min_f", "$group": G}, "agg_base.json")
summer = "date_extract_m(day) in (7,8)"
aft = q({"$select": "sensor_id,avg(airtemp) as jul_aug_afternoon_mean_f",
         "$where": summer + " AND hour in ('13','14','15','16','17')", "$group": "sensor_id"}, "agg_afternoon.json")
night = q({"$select": "sensor_id,avg(airtemp) as jul_aug_night_mean_f",
           "$where": summer + " AND hour in ('0','1','2','3','4','5')", "$group": "sensor_id"}, "agg_night.json")
h90 = q({"$select": "sensor_id,count(*) as hours_ge_90f", "$where": "airtemp >= 90", "$group": "sensor_id"}, "agg_ge90.json")
h95 = q({"$select": "sensor_id,count(*) as hours_ge_95f", "$where": "airtemp >= 95", "$group": "sensor_id"}, "agg_ge95.json")

extra = {}
for rows in (aft, night, h90, h95):
    for r in rows:
        extra.setdefault(r["sensor_id"], {}).update({k: v for k, v in r.items() if k != "sensor_id"})

# sensors can appear in >1 group row if metadata varies; merge on sensor_id keeping the largest n_hours row
sensors = {}
for r in base:
    s = sensors.get(r["sensor_id"])
    if s is None or int(r["n_hours"]) > int(s["n_hours"]):
        sensors[r["sensor_id"]] = r
fields = ["sensor_id", "borough", "ntacode_2010", "install_type", "lat", "lon", "n_hours", "first_day", "last_day",
          "mean_f", "max_f", "min_f", "jul_aug_afternoon_mean_f", "jul_aug_night_mean_f", "hours_ge_90f", "hours_ge_95f",
          "in_bronx"]
out, feats = [], []
for sid, r in sorted(sensors.items()):
    d = {"sensor_id": sid, "borough": r.get("borough", ""), "ntacode_2010": r.get("ntacode", ""),
         "install_type": r.get("install_type", ""), "n_hours": r["n_hours"],
         "first_day": r["first_day"][:10], "last_day": r["last_day"][:10]}
    for k in ["lat", "lon", "mean_f", "max_f", "min_f"]:
        d[k] = round(float(r[k]), 5 if k in ("lat", "lon") else 2) if r.get(k) else ""
    e = extra.get(sid, {})
    for k in ["jul_aug_afternoon_mean_f", "jul_aug_night_mean_f"]:
        d[k] = round(float(e[k]), 2) if e.get(k) else ""
    d["hours_ge_90f"] = e.get("hours_ge_90f", 0)
    d["hours_ge_95f"] = e.get("hours_ge_95f", 0)
    d["in_bronx"] = d["borough"] == "Bronx"
    out.append(d)
    if d["lat"] != "":
        feats.append({"type": "Feature", "properties": d, "geometry": {"type": "Point", "coordinates": [d["lon"], d["lat"]]}})
with open(os.path.join(OUT, "hyperlocal_temp_sensors.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(out)
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "hyperlocal_temp_sensors.geojson"), "w"),
          separators=(",", ":"))
cov = {}
for d in out:
    c = cov.setdefault(d["borough"] or "(blank)", {"borough": d["borough"] or "(blank)", "n_sensors": 0, "ntas": set()})
    c["n_sensors"] += 1
    c["ntas"].add(d["ntacode_2010"])
with open(os.path.join(OUT, "hyperlocal_temp_borough_coverage.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["borough", "n_sensors", "n_ntas_2010", "ntas_2010"])
    w.writeheader()
    for c in sorted(cov.values(), key=lambda x: x["borough"]):
        w.writerow({"borough": c["borough"], "n_sensors": c["n_sensors"], "n_ntas_2010": len(c["ntas"]),
                    "ntas_2010": " ".join(sorted(c["ntas"]))})
print(len(out), "sensors;", {k: v["n_sensors"] for k, v in cov.items()})
