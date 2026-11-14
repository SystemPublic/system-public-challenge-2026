"""Real NYC heat-wave scenarios for the HeatRx heat-level replay.

Inputs (fetched from the Iowa Environmental Mesonet, which archives NWS data):
  data/weather/nyc_2026_MM.json     daily summaries for Central Park (station NYC, network NY_ASOS):
                                    https://mesonet.agron.iastate.edu/api/1/daily.json?station=NYC&network=NY_ASOS&year=2026&month=MM
  data/weather/nyz072_vtec_2026.json NWS watch/warning/advisory events for zone NYZ072 (New York, Manhattan):
                                    https://mesonet.agron.iastate.edu/json/vtec_events_byugc.py?ugc=NYZ072&sdate=2026-06-01&edate=2026-09-30
Usage (from the repo root):
  python3 -I scripts/nyc_scenario.py data/weather reference/nyc_heat_scenarios.json
"""
import datetime
import json
import os
import sys

wdir, out = sys.argv[1:3]
days = {}
for m in ("06", "07", "08"):
    for r in json.load(open(os.path.join(wdir, "nyc_2026_%s.json" % m)))["data"]:
        days[r["date"]] = r
ev = json.load(open(os.path.join(wdir, "nyz072_vtec_2026.json")))
ev = ev.get("events", ev)
LEVEL = {("HT", "Y"): ("heat_advisory", 1, "Heat Advisory"), ("XH", "W"): ("extreme_heat_warning", 2, "Extreme Heat Warning"),
         ("EH", "W"): ("extreme_heat_warning", 2, "Excessive Heat Warning")}
EDT = datetime.timedelta(hours=-4)
alert_by_day = {}
for e in ev:
    lv = LEVEL.get((e.get("phenomena"), e.get("significance")))
    if not lv:
        continue
    t0 = datetime.datetime.strptime(e["issue"][:16], "%Y-%m-%dT%H:%M") + EDT
    t1 = datetime.datetime.strptime(e["expire"][:16], "%Y-%m-%dT%H:%M") + EDT
    d = t0.date()
    while d <= t1.date():
        k = d.isoformat()
        if k not in alert_by_day or alert_by_day[k][1] < lv[1]:
            alert_by_day[k] = lv
        d += datetime.timedelta(days=1)


def scenario(sid, title, start, end, note):
    out_days = []
    d = datetime.date.fromisoformat(start)
    while d <= datetime.date.fromisoformat(end):
        k = d.isoformat()
        r = days.get(k, {})
        lv = alert_by_day.get(k, ("normal", 0, "No heat alert"))
        out_days.append({"date": k, "max_temp_f": r.get("max_tmpf"), "min_temp_f": r.get("min_tmpf"),
                         "max_heat_index_f": round(r["max_feel"], 1) if r.get("max_feel") else None,
                         "level": lv[0], "level_rank": lv[1], "nws_product": lv[2]})
        d += datetime.timedelta(days=1)
    return {"id": sid, "title": title, "place": "New York City (Central Park station; NWS zone NYZ072, Manhattan)",
            "note": note, "days": out_days}


res = {"source": "NWS alerts and Central Park daily observations via the Iowa Environmental Mesonet (mesonet.agron.iastate.edu)",
       "levels": [{"id": "normal", "rank": 0, "label": "Normal"}, {"id": "heat_advisory", "rank": 1, "label": "Heat advisory"},
                  {"id": "extreme_heat_warning", "rank": 2, "label": "Extreme heat warning"}],
       "scenarios": [
           scenario("nyc_2026_07", "New York City, 28 June to 7 July 2026", "2026-06-28", "2026-07-07",
                    "NWS Extreme Heat Warning 1-4 July 2026; Central Park reached 100 °F on 2 July."),
           scenario("nyc_2026_08", "New York City, 3 to 12 August 2026", "2026-08-03", "2026-08-12",
                    "NWS Heat Advisories 6-8 and 9-10 August 2026; NYC Health Alert #23 was issued on 5 August for this event."),
       ]}
json.dump(res, open(out, "w"), indent=1)
for s in res["scenarios"]:
    print(s["id"], [(x["date"][5:], x["max_temp_f"], x["max_heat_index_f"], x["level_rank"]) for x in s["days"]])
