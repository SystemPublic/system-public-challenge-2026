"""CDC PLACES (2025 release; CKD from 2023 release) for NYC ZCTAs and census tracts.

Uses SoQL filters on data.cdc.gov (no full download):
  ZCTA 2025:  qnzd-25i4      tract 2025:  cwsq-ngmh
  ZCTA 2023:  9umn-c3jf      tract 2023:  em5e-5hvn   (only for KIDNEY = chronic kidney disease,
                                                       which the 2024 and 2025 releases no longer carry)
NYC ZCTAs = every ZCTA listed in the NYC MODZCTA file (data/raw/place/boundaries/modzcta.geojson).
NYC tracts = countyfips in 36005, 36047, 36061, 36081, 36085.

Raw (long) -> data/raw/place/places/*.csv ; wide -> data/processed/places_nyc_zcta.csv, places_nyc_tract.csv
Values are model-based crude prevalence (%) among adults (BRFSS 2023 small-area estimates).

python3 scripts/place_cdc_places.py
"""
import csv, io, json, os, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "place", "places")
OUT = os.path.join(ROOT, "data", "processed")
os.makedirs(RAW, exist_ok=True)

MEASURES_2025 = ["DIABETES", "BPHIGH", "BPMED", "CHD", "STROKE", "COPD", "DEPRESSION", "MHLTH", "OBESITY", "CASTHMA",
                 "DISABILITY", "MOBILITY", "COGNITION", "SELFCARE", "INDEPLIVE", "HEARING", "VISION",
                 "GHLTH", "LONELINESS", "EMOTIONSPT", "SHUTUTILITY", "LACKTRPT", "HOUSINSECU", "ACCESS2"]
MEASURES_2024 = ["KIDNEY"]
NYC_COUNTIES = ["36005", "36047", "36061", "36081", "36085"]


def soql(dataset, where, select, limit=50000):
    rows, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"$where": where, "$select": select, "$limit": limit, "$offset": offset,
                                    "$order": ":id"})
        url = f"https://data.cdc.gov/resource/{dataset}.csv?{q}"
        for attempt in range(5):
            try:
                txt = urllib.request.urlopen(url, timeout=120).read().decode()
                break
            except Exception as e:  # transient 5xx
                print("retry", dataset, e)
                time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(url)
        part = list(csv.DictReader(io.StringIO(txt)))
        rows += part
        if len(part) < limit:
            return rows
        offset += limit


def inlist(xs):
    return "(" + ",".join(f"'{x}'" for x in xs) + ")"


def save(name, rows):
    if not rows:
        return
    with open(os.path.join(RAW, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(name, len(rows))


mod = json.load(open(os.path.join(ROOT, "data", "raw", "place", "boundaries", "modzcta.geojson")))
zctas, zmod = [], {}
for f in mod["features"]:
    for z in (f["properties"].get("zcta") or "").split(","):
        z = z.strip()
        if z:
            zctas.append(z)
            zmod[z] = f["properties"]["modzcta"]

sel = "year,locationid,measureid,measure,data_value,low_confidence_limit,high_confidence_limit,totalpopulation,totalpop18plus,datavaluetypeid"
z25 = soql("qnzd-25i4", f"locationid in {inlist(zctas)} AND measureid in {inlist(MEASURES_2025)}", sel)
sel23 = sel.replace(",totalpop18plus", "")
z24 = soql("9umn-c3jf", f"locationid in {inlist(zctas)} AND measureid in {inlist(MEASURES_2024)}", sel23)
tsel = sel + ",countyname,countyfips"
t25 = soql("cwsq-ngmh", f"countyfips in {inlist(NYC_COUNTIES)} AND measureid in {inlist(MEASURES_2025)}", tsel)
t24 = soql("em5e-5hvn", f"countyfips in {inlist(NYC_COUNTIES)} AND measureid in {inlist(MEASURES_2024)}", tsel.replace(",totalpop18plus", ""))
save("places2025_zcta_nyc_long.csv", z25)
save("places2023_zcta_nyc_kidney_long.csv", z24)
save("places2025_tract_nyc_long.csv", t25)
save("places2023_tract_nyc_kidney_long.csv", t24)


def wide(rows_list, key_fields, out, extra):
    data, order = {}, MEASURES_2025 + MEASURES_2024
    for rows, tag in rows_list:
        for r in rows:
            d = data.setdefault(r["locationid"], {"locationid": r["locationid"], **{k: r.get(k, "") for k in key_fields}})
            if tag == "2025" or not d.get("totalpopulation"):
                d["totalpopulation"] = r["totalpopulation"]
                d["totalpop18plus"] = r.get("totalpop18plus", "")
            m = r["measureid"].lower()
            d[m] = r["data_value"]
            d[m + "_ci"] = f"{r['low_confidence_limit']}-{r['high_confidence_limit']}"
            d.setdefault("data_years", set()).add(f"{r['measureid']}:{r['year']}")
    fields = ["locationid"] + key_fields + extra + ["totalpopulation", "totalpop18plus"]
    for m in order:
        fields += [m.lower(), m.lower() + "_ci"]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields + ["release"], extrasaction="ignore")
        w.writeheader()
        for k in sorted(data):
            d = data[k]
            d["release"] = "PLACES 2025 (BRFSS 2023); kidney (CKD) from PLACES 2023 (BRFSS 2021)"
            for e in extra:
                d[e] = zmod.get(k, "") if e == "modzcta" else d.get(e, "")
            w.writerow(d)
    print(out, len(data))


wide([(z25, "2025"), (z24, "2024")], [], os.path.join(OUT, "places_nyc_zcta.csv"), ["modzcta"])
wide([(t25, "2025"), (t24, "2024")], ["countyname", "countyfips"], os.path.join(OUT, "places_nyc_tract.csv"), [])
