"""NYC Heat Vulnerability Index (HVI) + household air-conditioning access -> processed CSV/GeoJSON.

Inputs (already downloaded to data/raw/place/, see data/raw/place/README.md):
  ehdp/2411.json  HVI by NTA2020 (EHDP indicator 2411, measure 1288, 2023 release)
  ehdp/2191.json  HVI by CDTA2020 (indicator 2191)
  ehdp/hvi_zcta_4mhf-duep.csv  HVI by ZCTA 2020 (NYC Open Data 4mhf-duep)
  ehdp/2185.json  Household AC (NYCHVS) by PUMA2020/UHF42/Subboro/Borough
  boundaries/GeoLookup.csv, nta2020.geojson, modzcta.geojson, puma2020.geojson, puma_2020_names.csv

Outputs (data/processed/):
  hvi_nta2020.csv, hvi_nta2020.geojson
  hvi_zcta.csv, hvi_modzcta.geojson
  ac_households_nyc.csv  (all geographies, all years)
  ac_households_puma2020.geojson  (2023 HVS, finest available)

Stdlib only:  python3 scripts/place_hvi_ac.py
"""
import csv, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "place")
OUT = os.path.join(ROOT, "data", "processed")
os.makedirs(OUT, exist_ok=True)


def rnd(coords, n=5):
    if isinstance(coords, (int, float)):
        return round(coords, n)
    return [rnd(c, n) for c in coords]


def slim(geom):
    return {"type": geom["type"], "coordinates": rnd(geom["coordinates"])}


def load_ehdp(ind):
    d = json.load(open(os.path.join(RAW, "ehdp", f"{ind}.json")))
    keys = list(d.keys())
    return [dict(zip(keys, vals)) for vals in zip(*[d[k] for k in keys])]


def write_csv(path, rows, fields):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_geojson(path, feats):
    with open(path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f, separators=(",", ":"))


tp = {t["TimePeriodID"]: t["TimePeriod"] for t in json.load(open(os.path.join(RAW, "ehdp", "TimePeriods.json")))}
lookup = {}
for r in csv.DictReader(open(os.path.join(RAW, "boundaries", "GeoLookup.csv"))):
    lookup[(r["GeoType"], r["GeoID"])] = r

# ---- HVI by NTA2020 -------------------------------------------------------
nta = json.load(open(os.path.join(RAW, "boundaries", "nta2020.geojson")))
by_name = {f["properties"]["ntaname"].strip().lower(): f for f in nta["features"]}
rows, feats, unmatched = [], [], []
for r in load_ehdp(2411):
    lk = lookup.get(("NTA2020", str(r["GeoID"])), {})
    name = lk.get("Name", "")
    f = by_name.get(name.strip().lower())
    p = f["properties"] if f else {}
    row = {
        "nta2020": p.get("nta2020", ""), "ntaname": name, "borough": lk.get("Borough", ""),
        "cdta2020": p.get("cdta2020", ""), "ehdp_geoid": r["GeoID"], "hvi": r["Value"],
        "year": tp.get(r["TimePeriodID"], ""), "source": "NYC DOHMH EHDP indicator 2411 (HVI, NTA2020)",
    }
    rows.append(row)
    if f:
        feats.append({"type": "Feature", "properties": row, "geometry": slim(f["geometry"])})
    else:
        unmatched.append(name)
fields = ["nta2020", "ntaname", "borough", "cdta2020", "ehdp_geoid", "hvi", "year", "source"]
write_csv(os.path.join(OUT, "hvi_nta2020.csv"), rows, fields)
write_geojson(os.path.join(OUT, "hvi_nta2020.geojson"), feats)
print(f"HVI NTA: {len(rows)} rows, {len(feats)} with geometry; unmatched: {unmatched}")

# ---- HVI by ZCTA / MODZCTA ------------------------------------------------
zhvi = {r["zcta20"]: r["hvi"] for r in csv.DictReader(open(os.path.join(RAW, "ehdp", "hvi_zcta_4mhf-duep.csv")))}
mod = json.load(open(os.path.join(RAW, "boundaries", "modzcta.geojson")))
zrows, zfeats = [], []
zip_to_mod = {}
for f in mod["features"]:
    p = f["properties"]
    for z in [x.strip() for x in (p.get("zcta") or "").split(",") if x.strip()]:
        zip_to_mod[z] = p["modzcta"]
for z, h in sorted(zhvi.items()):
    zrows.append({"zcta20": z, "modzcta": zip_to_mod.get(z, ""), "hvi": h,
                  "source": "NYC Open Data 4mhf-duep (DOHMH HVI by ZCTA 2020)"})
write_csv(os.path.join(OUT, "hvi_zcta.csv"), zrows, ["zcta20", "modzcta", "hvi", "source"])
nomatch = 0
for f in mod["features"]:
    p = f["properties"]
    h = zhvi.get(p["modzcta"])
    if h is None:
        nomatch += 1
    zfeats.append({"type": "Feature", "geometry": slim(f["geometry"]), "properties": {
        "modzcta": p["modzcta"], "zctas": p.get("zcta"), "label": p.get("label"),
        "pop_est": p.get("pop_est"), "hvi": int(h) if h else None,
        "source": "HVI: NYC Open Data 4mhf-duep; boundary: MODZCTA pri4-ifjk"}})
write_geojson(os.path.join(OUT, "hvi_modzcta.geojson"), zfeats)
print(f"HVI ZCTA: {len(zrows)} ZCTAs; MODZCTA features {len(zfeats)}, without HVI: {nomatch}")

# ---- Household AC ---------------------------------------------------------
meas = {781: "pct_households_with_ac", 782: "n_households_with_ac", 1045: "pct_households_without_ac"}
acrows = []
for r in load_ehdp(2185):
    lk = lookup.get((r["GeoType"], str(r["GeoID"])), {})
    acrows.append({
        "geotype": r["GeoType"], "geoid": r["GeoID"], "name": lk.get("Name", ""), "borough": lk.get("Borough", ""),
        "year": tp.get(r["TimePeriodID"], ""), "measure": meas.get(r["MeasureID"], r["MeasureID"]),
        "value": r["Value"], "ci": r["CI"], "note": r["Note"],
        "source": "NYC DOHMH EHDP indicator 2185 (NYC Housing and Vacancy Survey)"})
acrows.sort(key=lambda x: (x["geotype"], str(x["geoid"]), x["year"], x["measure"]))
write_csv(os.path.join(OUT, "ac_households_nyc.csv"), acrows,
          ["geotype", "geoid", "name", "borough", "year", "measure", "value", "ci", "note", "source"])
pnames = {r["PUMA2020"]: r["GEONAME"] for r in csv.DictReader(open(os.path.join(RAW, "boundaries", "puma_2020_names.csv")))}
puma = {}
for r in acrows:
    if r["geotype"] == "PUMA2020" and r["year"] == "2023":
        d = puma.setdefault(str(r["geoid"]), {"puma2020": str(r["geoid"]), "name": pnames.get(str(r["geoid"]), r["name"]),
                                               "year": "2023", "source": "EHDP 2185 / NYCHVS 2023"})
        d[r["measure"]] = r["value"]
        d[r["measure"] + "_ci"] = r["ci"]
        if r["note"]:
            d["caution"] = "large CV, interpret with caution"
pfeats = []
for f in json.load(open(os.path.join(RAW, "boundaries", "puma2020.geojson")))["features"]:
    code = f["properties"]["puma"]
    props = puma.get(code, {"puma2020": code})
    pfeats.append({"type": "Feature", "properties": props, "geometry": slim(f["geometry"])})
write_geojson(os.path.join(OUT, "ac_households_puma2020.geojson"), pfeats)
print(f"AC: {len(acrows)} rows; PUMA2020 features {len(pfeats)}, with data {sum(1 for f in pfeats if 'pct_households_with_ac' in f['properties'])}")
