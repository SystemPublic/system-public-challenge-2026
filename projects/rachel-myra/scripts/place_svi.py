"""CDC/ATSDR Social Vulnerability Index 2022 (latest available; New York state, tract level) -> NYC tracts.

Raw: data/raw/place/svi/NewYork_2022_tract.csv  from https://svi.cdc.gov/Documents/Data/2022/csv/states/NewYork.csv
Boundaries: data/raw/place/boundaries/tracts2020.geojson (NYC Open Data 63ge-mke6, 2020 tracts)
RPL_* percentiles are ranked WITHIN New York State (state file), not nationally.
-999 (missing) -> blank.

Outputs: data/processed/svi2022_nyc_tract.csv, data/processed/svi2022_nyc_tract.geojson
python3 scripts/place_svi.py
"""
import csv, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "place")
OUT = os.path.join(ROOT, "data", "processed")
NYC = {"36005", "36047", "36061", "36081", "36085"}
KEEP = ["FIPS", "COUNTY", "LOCATION", "E_TOTPOP", "RPL_THEMES", "RPL_THEME1", "RPL_THEME2", "RPL_THEME3", "RPL_THEME4",
        "F_TOTAL", "EP_POV150", "EP_UNEMP", "EP_HBURD", "EP_NOHSDP", "EP_UNINSUR", "EP_AGE65", "EP_AGE17",
        "EP_DISABL", "EP_SNGPNT", "EP_LIMENG", "EP_MINRTY", "EP_MUNIT", "EP_CROWD", "EP_NOVEH", "EP_GROUPQ",
        "EP_NOINT", "EP_AFAM", "EP_HISP"]


def rnd(c):
    return round(c, 5) if isinstance(c, (int, float)) else [rnd(x) for x in c]


rows = []
with open(os.path.join(RAW, "svi", "NewYork_2022_tract.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["STCNTY"] in NYC:
            rows.append({k: ("" if r[k] in ("-999", "-999.0", "-999.0000") else r[k]) for k in KEEP})
fields = [k.lower() for k in KEEP] + ["nta2020", "source"]
tracts = {f["properties"]["geoid"]: f for f in json.load(open(os.path.join(RAW, "boundaries", "tracts2020.geojson")))["features"]}
feats = []
with open(os.path.join(OUT, "svi2022_nyc_tract.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in rows:
        t = tracts.get(r["FIPS"])
        d = {k.lower(): v for k, v in r.items()}
        d["nta2020"] = t["properties"]["nta2020"] if t else ""
        d["source"] = "CDC/ATSDR SVI 2022, New York state file (state-ranked)"
        w.writerow(d)
        if t:
            feats.append({"type": "Feature", "properties": d,
                          "geometry": {"type": t["geometry"]["type"], "coordinates": rnd(t["geometry"]["coordinates"])}})
with open(os.path.join(OUT, "svi2022_nyc_tract.geojson"), "w") as f:
    json.dump({"type": "FeatureCollection", "features": feats}, f, separators=(",", ":"))
print(f"SVI NYC tracts: {len(rows)}; joined to 2020 tract boundaries: {len(feats)}")
