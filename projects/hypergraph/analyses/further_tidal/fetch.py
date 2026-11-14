"""Fetch inputs for further-tidal-flooding-311 (run after registration)."""
import json, time
from pathlib import Path
import requests
from concord import socrata, noaa

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "further_tidal"; D.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "research-client/1.0"}

def tide():
    out, recs = {}, []
    for y in range(2020, 2027):
        b, e = f"{y}0101", f"{y}1231" if y < 2026 else "20261031"
        url = ("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=hourly_height&application=research"
               f"&begin_date={b}&end_date={e}&datum=MLLW&station=8518750&time_zone=lst_ldt&units=metric&format=json")
        r = requests.get(url, headers=UA, timeout=120); r.raise_for_status()
        j = r.json()
        for x in j["data"]:
            if x["v"]:
                d = x["t"][:10]; out[d] = max(out.get(d, -9), float(x["v"]))
        recs.append({"kind": "noaa-co-ops", "station": "8518750 The Battery", "url": url, "product": "hourly_height, datum MLLW, metric, lst_ldt",
                     "n_rows": len(j["data"]), "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                     "last_modified": r.headers.get("Last-Modified", "(none sent; API returns current verified/preliminary data)")})
    (D / "battery_daily_max.json").write_text(json.dumps({"daily_max_m_mllw": out, "sources": recs}))

def complaints():
    pats = {
     "C1": "(upper(complaint_type) like '%STREET FLOOD%' or upper(descriptor) like '%STREET FLOOD%')",
     "C2": "(upper(complaint_type) like '%STREET FLOOD%' or upper(descriptor) like '%STREET FLOOD%' or upper(descriptor) like '%CATCH BASIN%' or upper(descriptor) like '%SEWER BACKUP%')",
    }
    res = {}
    for k, w in pats.items():
        rows, src = socrata.query_all("erm2-nwe9", select="date_trunc_ymd(created_date) as d, incident_zip as zip, count(*) as n",
            where=f"created_date between '2020-01-01T00:00:00' and '2026-10-31T23:59:59' and {w}", group="d, zip", order="d, zip")
        res[k] = {"rows": rows, "source": src}
    (D / "complaints_by_day_zip.json").write_text(json.dumps(res))
    # also the descriptor strings actually matched, for the record
    rows, src = socrata.query("erm2-nwe9", select="complaint_type, descriptor, count(*) as n",
        where=f"created_date between '2020-01-01T00:00:00' and '2026-10-31T23:59:59' and {pats['C2']}", group="complaint_type, descriptor", order="n desc")
    (D / "matched_descriptors.json").write_text(json.dumps({"rows": rows, "source": src}))

def weather():
    for s in ("central_park", "jfk"):
        df, src = noaa.daily(s, refresh=True)
        df[["PRCP"]].to_csv(D / f"prcp_{s}.csv"); (D / f"prcp_{s}.source.json").write_text(json.dumps(src))

def floodnet():
    ev, s1 = socrata.query_all("aq7i-eu5q", order="flood_start_time")
    se, s2 = socrata.query("kb2e-tjy3", limit=5000)
    (D / "floodnet.json").write_text(json.dumps({"events": ev, "sensors": se, "sources": [s1, s2]}))

if __name__ == "__main__":
    tide(); weather(); complaints(); floodnet()
