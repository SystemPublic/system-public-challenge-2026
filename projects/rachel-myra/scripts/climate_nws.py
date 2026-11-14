"""Resolve NWS API gridpoints for the demo ZIP centroids and save a sample forecast + active alerts.

For each ZIP (Census 2024 ZCTA gazetteer internal point, data/raw/climate/nws/zcta_gazetteer_2024_demo_zips.tsv):
    GET https://api.weather.gov/points/{lat},{lon}
      -> forecast office (gridId), gridX/gridY, forecast / forecastHourly / forecastGridData URLs,
         forecast zone, county zone, fire weather zone, observation stations URL
    GET forecastHourly (sample, first 48 periods kept in processed JSON; full response cached in raw)
    GET forecast (7-day, 12-h periods)
Then GET https://api.weather.gov/alerts/active?zone=<zone> for every distinct forecast/county zone,
plus alerts/active?area=NY filtered to heat events.

api.weather.gov requires a User-Agent; a generic one is used.
Output: data/processed/nws_zip_gridpoints.json ; raw responses in data/raw/climate/nws/.

Usage:
    uv run python scripts/climate_nws.py
"""
import csv
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/climate/nws"
OUT = ROOT / "data/processed/nws_zip_gridpoints.json"
UA = "missing-label-hackathon (research prototype)"
HEAT_EVENTS = {"Heat Advisory", "Extreme Heat Warning", "Extreme Heat Watch",
               "Excessive Heat Warning", "Excessive Heat Watch"}


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/geo+json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # NWS API intermittently returns 500/503 for gridpoint forecasts
            err = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


def tail(url):
    return url.rstrip("/").split("/")[-1] if url else None


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    fetched = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = list(csv.DictReader(open(RAW / "zcta_gazetteer_2024_demo_zips.tsv"), delimiter="\t"))
    zips, zones = [], set()
    for r in rows:
        r = {k.strip(): v.strip() for k, v in r.items()}
        lat, lon = round(float(r["INTPTLAT"]), 4), round(float(r["INTPTLONG"]), 4)
        z = r["GEOID"]
        pts = get(f"https://api.weather.gov/points/{lat},{lon}")
        json.dump(pts, open(RAW / f"points_{z}.json", "w"), indent=1)
        p = pts["properties"]
        entry = {
            "zip": z, "centroid_lat": lat, "centroid_lon": lon,
            "centroid_source": "US Census 2024 Gazetteer ZCTA internal point",
            "office": p.get("gridId"), "cwa": p.get("cwa"), "grid_x": p.get("gridX"), "grid_y": p.get("gridY"),
            "forecast_url": p.get("forecast"), "forecast_hourly_url": p.get("forecastHourly"),
            "forecast_grid_data_url": p.get("forecastGridData"),
            "observation_stations_url": p.get("observationStations"),
            "forecast_zone": tail(p.get("forecastZone")), "county_zone": tail(p.get("county")),
            "fire_weather_zone": tail(p.get("fireWeatherZone")),
            "radar_station": p.get("radarStation"),
            "relative_location": (p.get("relativeLocation") or {}).get("properties"),
        }
        zones.update(x for x in (entry["forecast_zone"], entry["county_zone"]) if x)
        try:
            fh = get(entry["forecast_hourly_url"])
            json.dump(fh, open(RAW / f"forecast_hourly_{z}.json", "w"))
            per = fh["properties"]["periods"]
            entry["sample_forecast_hourly"] = {
                "generated_at": fh["properties"].get("generatedAt"),
                "update_time": fh["properties"].get("updateTime"),
                "periods_total": len(per),
                "periods_first_48": [{
                    "start": q["startTime"], "temp_f": q["temperature"],
                    "dewpoint_c": (q.get("dewpoint") or {}).get("value"),
                    "rh_pct": (q.get("relativeHumidity") or {}).get("value"),
                    "pop_pct": (q.get("probabilityOfPrecipitation") or {}).get("value"),
                    "wind": f'{q.get("windSpeed")} {q.get("windDirection")}', "short": q["shortForecast"],
                } for q in per[:48]],
            }
        except Exception as e:
            entry["sample_forecast_hourly"] = {"error": str(e)}
        try:
            fc = get(entry["forecast_url"])
            json.dump(fc, open(RAW / f"forecast_{z}.json", "w"))
            entry["sample_forecast_7day"] = {
                "generated_at": fc["properties"].get("generatedAt"),
                "periods": [{"name": q["name"], "start": q["startTime"], "is_daytime": q["isDaytime"],
                             "temp_f": q["temperature"], "short": q["shortForecast"]}
                            for q in fc["properties"]["periods"]],
            }
        except Exception as e:
            entry["sample_forecast_7day"] = {"error": str(e)}
        zips.append(entry)
        time.sleep(1)

    alerts = {}
    for zone in sorted(zones):
        a = get(f"https://api.weather.gov/alerts/active?zone={zone}")
        json.dump(a, open(RAW / f"alerts_active_{zone}.json", "w"), indent=1)
        alerts[zone] = [{"event": f["properties"]["event"], "headline": f["properties"].get("headline"),
                         "onset": f["properties"].get("onset"), "ends": f["properties"].get("ends"),
                         "severity": f["properties"].get("severity")} for f in a.get("features", [])]
    ny = get("https://api.weather.gov/alerts/active?area=NY")
    json.dump(ny, open(RAW / "alerts_active_area_NY.json", "w"))
    ny_heat = [f["properties"]["headline"] for f in ny.get("features", []) if f["properties"]["event"] in HEAT_EVENTS]

    out = {
        "fetched_utc": fetched,
        "source": "https://api.weather.gov (NWS API), User-Agent: " + UA,
        "zips": zips,
        "active_alerts_by_zone": alerts,
        "active_heat_alerts_area_NY": ny_heat,
        "active_alerts_area_NY_total": len(ny.get("features", [])),
        "how_to_use": {
            "hourly_forecast": "GET forecast_hourly_url (Accept: application/geo+json, User-Agent required); "
                               "periods[].temperature (F), dewpoint (degC), relativeHumidity (%)",
            "raw_grid": "GET forecast_grid_data_url -> properties.heatIndex / apparentTemperature / maxTemperature / "
                        "minTemperature / relativeHumidity time series (SI units, ISO8601 durations)",
            "alerts": "GET https://api.weather.gov/alerts/active?zone=<forecast_zone> ; heat events: " + ", ".join(sorted(HEAT_EVENTS)),
        },
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps({z["zip"]: [z["office"], z["grid_x"], z["grid_y"], z["forecast_zone"], z["county_zone"]] for z in zips}))
    print("alerts:", {k: len(v) for k, v in alerts.items()}, "NY heat:", ny_heat, "NY total", out["active_alerts_area_NY_total"])


if __name__ == "__main__":
    main()
