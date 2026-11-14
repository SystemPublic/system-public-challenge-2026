"""Exposure-only inputs for further-tidal-flooding-trend: Battery hourly heights 2010-2025 (MHHW datum) and
GHCN-Daily precipitation. No 311 data are read here."""
import json, time
from pathlib import Path
import requests
from concord import noaa

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "round2" / "tidal_trend"; D.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "research-client/1.0"}

def tide(y0=2010, y1=2025):
    out, recs, nhours = {}, [], {}
    for y in range(y0, y1 + 1):
        url = ("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=hourly_height&application=research"
               f"&begin_date={y}0101&end_date={y}1231&datum=MHHW&station=8518750&time_zone=lst_ldt&units=metric&format=json")
        r = requests.get(url, headers=UA, timeout=120); r.raise_for_status()
        j = r.json()
        for x in j["data"]:
            if x["v"]:
                d = x["t"][:10]; out[d] = max(out.get(d, -9), float(x["v"])); nhours[d] = nhours.get(d, 0) + 1
        recs.append({"kind": "noaa-co-ops", "station": "8518750 The Battery", "url": url, "product": "hourly_height, datum MHHW, metric, lst_ldt",
                     "n_rows": len(j["data"]), "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    (D / "battery_daily_max_mhhw.json").write_text(json.dumps({"daily_max_m_mhhw": out, "hours": nhours, "sources": recs}))

def weather():
    for s in ("central_park", "jfk"):
        df, src = noaa.daily(s)
        df[["PRCP"]].to_csv(D / f"prcp_{s}.csv"); (D / f"prcp_{s}.source.json").write_text(json.dumps(src))

if __name__ == "__main__":
    tide(); weather()
