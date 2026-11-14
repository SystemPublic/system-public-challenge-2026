"""Hourly "feels like" temperature on a grid over NYC for the replay heat wave (June 22-26, 2025),
for the radar-style heat map in the time-lapse (/replay).

Source: NOAA HRRR 3 km model (archived forecasts), via the Open-Meteo Historical Forecast API
(https://open-meteo.com/en/docs/historical-forecast-api; no key; CC BY 4.0). Variable: apparent_temperature (°F).
Output: data/processed/replay_hrrr_grid.json  {lats, lons, times, apparent_f[t][i][j]}
Run: py -3 scripts/climate_hrrr_grid.py
"""
import json
import os
import time

import requests

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "data", "processed", "replay_hrrr_grid.json")
RAW = os.path.join(ROOT, "data", "raw", "climate", "hrrr_openmeteo")
os.makedirs(RAW, exist_ok=True)

LAT0, LAT1, LON0, LON1, STEP = 40.49, 40.93, -74.27, -73.69, 0.03
lats = [round(LAT0 + i * STEP, 3) for i in range(int((LAT1 - LAT0) / STEP) + 1)]
lons = [round(LON0 + j * STEP, 3) for j in range(int((LON1 - LON0) / STEP) + 1)]
pts = [(la, lo) for la in lats for lo in lons]
START, END = "2025-06-22", "2025-06-26"

results = {}
CHUNK = 50
for k in range(0, len(pts), CHUNK):
    chunk = pts[k:k + CHUNK]
    fn = os.path.join(RAW, f"chunk_{k:04d}.json")
    if os.path.exists(fn):
        data = json.load(open(fn, encoding="utf-8"))
    else:
        params = {
            "latitude": ",".join(str(p[0]) for p in chunk),
            "longitude": ",".join(str(p[1]) for p in chunk),
            "start_date": START, "end_date": END,
            "hourly": "apparent_temperature", "models": "gfs_hrrr",
            "temperature_unit": "fahrenheit", "timezone": "America/New_York",
        }
        for attempt in range(4):
            r = requests.get("https://historical-forecast-api.open-meteo.com/v1/forecast", params=params, timeout=120)
            if r.status_code == 200:
                break
            time.sleep(5 * (attempt + 1))
        r.raise_for_status()
        data = r.json()
        data = data if isinstance(data, list) else [data]
        json.dump(data, open(fn, "w", encoding="utf-8"))
        time.sleep(1)
    for p, d in zip(chunk, data):
        results[p] = d["hourly"]
    print(f"{min(k + CHUNK, len(pts))}/{len(pts)}")

times = results[pts[0]]["time"]
grid = [[[None for _ in lons] for _ in lats] for _ in times]
for i, la in enumerate(lats):
    for j, lo in enumerate(lons):
        vals = results[(la, lo)]["apparent_temperature"]
        for t, v in enumerate(vals):
            grid[t][i][j] = None if v is None else round(v, 1)

json.dump({
    "source": "NOAA HRRR 3 km (archived), via Open-Meteo Historical Forecast API, apparent_temperature (°F); CC BY 4.0",
    "accessed": time.strftime("%Y-%m-%d"),
    "lats": lats, "lons": lons, "times": times, "apparent_f": grid,
}, open(OUT, "w", encoding="utf-8"), separators=(",", ":"))
print("wrote", OUT, len(times), "hours,", len(lats), "x", len(lons))
