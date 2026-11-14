"""CMS Medicare Part D prescribing of the 15 heat-risk drug classes in NYC (data year 2024), aggregate only.

Steps (all via data.cms.gov data-api v1 filters; no full-file download):
  1. "Part D Prescribers - by Geography and Drug" 2024 (c8ea3f8e-...) national rows -> list of (generic, brand)
     pairs; classify into our drug classes (CLASSES below). Save national + New York state rows for matched pairs.
  2. "Part D Prescribers - by Provider" 2024 (14d8e8a9-...) filtered to Prscrbr_Zip5 IN <NYC ZCTAs>:
     NPI -> ZIP5, prescriber type, entity code (raw only; no names kept).
  3. "Part D Prescribers - by Provider and Drug" 2024 (9552739e-...) filtered to NY + matched generic names;
     keep only rows whose NPI is in step 2 and whose (generic, brand) pair is matched.
  4. Aggregate by ZIP x class and by specialty x class.

Raw NPI-level rows are kept in data/raw/place/partd/ (NPI + counts only, no prescriber names). Processed files
contain no NPIs or names.

Caveats: CMS suppresses Tot_Benes < 11 (blank) and omits prescriber-drug rows with < 11 claims entirely.
Summed beneficiaries double-count people seen by more than one prescriber; treat as "prescriber-patient pairs".
Prescriber ZIP is practice address, not patient residence.

python3 scripts/place_partd.py
"""
import csv, json, os, re, time, urllib.parse, urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "place", "partd")
OUT = os.path.join(ROOT, "data", "processed")
os.makedirs(RAW, exist_ok=True)
API = "https://data.cms.gov/data-api/v1/dataset/{}/data"
GEO_DRUG = "c8ea3f8e-3a09-4fea-86f2-8902fb4b0920"
PROV = "14d8e8a9-7e9b-4370-a044-bf97c46b4b44"
PROV_DRUG = "9552739e-3d05-4c1b-8eff-ecabf391e2e5"
YEAR = 2024

# class -> generic-name regex (matched against CMS Gnrc_Name, lower-case); brand exclusions handled below
CLASSES = {
    "lithium": r"^lithium",
    "loop diuretics": r"furosemide|bumetanide|torsemide|ethacrynic",
    "thiazides": r"hydrochlorothiazide|chlorthalidone|indapamide|metolazone|chlorothiazide",
    "ACE inhibitors/ARBs": r"(benazepril|captopril|enalapril|fosinopril|lisinopril|moexipril|perindopril|quinapril|ramipril|trandolapril|azilsartan|candesartan|eprosartan|irbesartan|losartan|olmesartan|telmisartan|valsartan)",
    "SGLT2 inhibitors": r"gliflozin",
    "insulin": r"^insulin(?! (admin|pen,|pmp|pump))|/insulin",  # excludes supplies/pump cartridges/reusable pens
    "metformin": r"metformin",
    "anticholinergics (bladder/antiparkinson)": r"oxybutynin|tolterodine|trospium|solifenacin|darifenacin|fesoterodine|benztropine|trihexyphenidyl",
    "antipsychotics": None,  # CMS Antpsyct_Drug_Flag == Y
    "SSRIs": r"^(sertraline|fluoxetine|citalopram|escitalopram|paroxetine|fluvoxamine)",
    "topiramate/zonisamide": r"topiramate|zonisamide",
    "ADHD stimulants": r"methylphenidate|amphetamine|lisdexamfetamine|methamphetamine",
    "beta blockers": r"(atenolol|metoprolol|propranolol|carvedilol|bisoprolol|nebivolol|labetalol|nadolol|sotalol|pindolol|acebutolol)",
    "fentanyl/opioid patches": r"^fentanyl$|^buprenorphine$",
    "epinephrine auto-injectors": r"^epinephrine$",
}
BRAND_EXCLUDE = {
    "fentanyl/opioid patches": {"sublocade", "brixadi"},  # buprenorphine injections, not patches
    "epinephrine auto-injectors": {"adrenalin", "neffy"},  # vial / nasal spray, not auto-injectors
}


def get(dataset, params, size=5000):
    rows, offset = [], 0
    while True:
        q = urllib.parse.urlencode(params + [("size", size), ("offset", offset)])
        url = API.format(dataset) + "?" + q
        for attempt in range(6):
            try:
                part = json.loads(urllib.request.urlopen(url, timeout=180).read())
                break
            except Exception as e:
                print("retry", e)
                time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(url)
        rows += part
        if len(part) < size:
            return rows
        offset += size


def in_filter(name, path, values):
    p = [(f"filter[{name}][condition][path]", path), (f"filter[{name}][condition][operator]", "IN")]
    return p + [(f"filter[{name}][condition][value][]", v) for v in values]


def classify(gen, brand, antpsy):
    g, b, out = gen.lower(), brand.lower(), []
    for cls, rx in CLASSES.items():
        if cls == "antipsychotics":
            if antpsy == "Y":
                out.append(cls)
        elif re.search(rx, g) and b not in BRAND_EXCLUDE.get(cls, set()):
            if cls == "fentanyl/opioid patches" and g == "buprenorphine" and b not in {"butrans", "buprenorphine"}:
                continue
            out.append(cls)
    return out


def write_csv(path, rows, fields):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(os.path.relpath(path, ROOT), len(rows))


# 1. drug list ---------------------------------------------------------------
nat_path = os.path.join(RAW, "geo_drug_2024_national_all.json")
if os.path.exists(nat_path):
    nat = json.load(open(nat_path))
else:
    nat = get(GEO_DRUG, [("filter[Prscrbr_Geo_Lvl]", "National")])
    json.dump(nat, open(nat_path, "w"))
pairs = {}
for r in nat:
    cl = classify(r["Gnrc_Name"], r["Brnd_Name"], r.get("Antpsyct_Drug_Flag"))
    if cl:
        pairs[(r["Gnrc_Name"], r["Brnd_Name"])] = cl
generics = sorted({g for g, _ in pairs})
write_csv(os.path.join(RAW, "drug_class_map_2024.csv"),
          [{"gnrc_name": g, "brnd_name": b, "classes": "; ".join(c)} for (g, b), c in sorted(pairs.items())],
          ["gnrc_name", "brnd_name", "classes"])
geo_fields = ["Prscrbr_Geo_Lvl", "Prscrbr_Geo_Desc", "Gnrc_Name", "Brnd_Name", "Tot_Prscrbrs", "Tot_Clms",
              "Tot_30day_Fills", "Tot_Drug_Cst", "Tot_Benes", "GE65_Tot_Clms", "GE65_Tot_Benes", "Antpsyct_Drug_Flag"]
ny = get(GEO_DRUG, [("filter[Prscrbr_Geo_Desc]", "New York")])
geo_rows = []
for r in nat + ny:
    cl = pairs.get((r["Gnrc_Name"], r["Brnd_Name"]))
    if cl:
        r = dict(r, drug_classes="; ".join(cl), year=YEAR)
        geo_rows.append(r)
write_csv(os.path.join(OUT, "partd_geo_drug_national_ny.csv"), geo_rows, ["year"] + geo_fields + ["drug_classes"])

# 2. NYC prescribers -----------------------------------------------------------
mod = json.load(open(os.path.join(ROOT, "data", "raw", "place", "boundaries", "modzcta.geojson")))
zip_to_mod = {}
for f in mod["features"]:
    for z in (f["properties"].get("zcta") or "").split(","):
        if z.strip() and z.strip() != "99999":
            zip_to_mod[z.strip()] = f["properties"]["modzcta"]
prov_cols = "Prscrbr_NPI,Prscrbr_Zip5,Prscrbr_City,Prscrbr_State_Abrvtn,Prscrbr_Ent_Cd,Prscrbr_Type,Tot_Clms,Tot_Benes"
prov_path = os.path.join(RAW, "nyc_prescribers_2024_npi_zip.csv")
zips = sorted(zip_to_mod)
prov = list(csv.DictReader(open(prov_path))) if os.path.exists(prov_path) else []
for i in ([] if prov else range(0, len(zips), 40)):  # chunk: long IN lists exceed the API's URL limit
    prov += get(PROV, in_filter("z", "Prscrbr_Zip5", zips[i:i + 40]) + [("column", prov_cols)])
prov = [p for p in prov if p["Prscrbr_State_Abrvtn"] == "NY"]
write_csv(os.path.join(RAW, "nyc_prescribers_2024_npi_zip.csv"), prov, prov_cols.split(","))
npi = {p["Prscrbr_NPI"]: p for p in prov}

# 3. provider x drug (NY, our generics) ---------------------------------------
pd_cols = "Prscrbr_NPI,Prscrbr_City,Prscrbr_Type,Brnd_Name,Gnrc_Name,Tot_Clms,Tot_30day_Fills,Tot_Day_Suply,Tot_Benes,GE65_Tot_Clms,GE65_Tot_Benes"
# Cache = the NPI-level NYC output of a previous run (re-classified below). Delete it to re-fetch from the API,
# e.g. after widening CLASSES (a narrower re-run overwrites it with fewer rows).
pd_cache = os.path.join(RAW, "nyc_provider_drug_2024_npi_level.csv")
pd_rows = list(csv.DictReader(open(pd_cache))) if os.path.exists(pd_cache) else []
for i in ([] if pd_rows else range(0, len(generics), 25)):
    chunk = generics[i:i + 25]
    pd_rows += get(PROV_DRUG, [("filter[Prscrbr_State_Abrvtn]", "NY")] + in_filter("g", "Gnrc_Name", chunk) + [("column", pd_cols)])
    print("generics", i + len(chunk), "/", len(generics), "rows", len(pd_rows))
kept = []
for r in pd_rows:
    cl = pairs.get((r["Gnrc_Name"], r["Brnd_Name"]))
    p = npi.get(r["Prscrbr_NPI"])
    if cl and p:
        r = dict(r, Prscrbr_Zip5=p["Prscrbr_Zip5"], modzcta=zip_to_mod.get(p["Prscrbr_Zip5"], ""), drug_classes="; ".join(cl))
        kept.append(r)
write_csv(os.path.join(RAW, "nyc_provider_drug_2024_npi_level.csv"), kept,
          pd_cols.split(",") + ["Prscrbr_Zip5", "modzcta", "drug_classes"])


# 4. aggregates ------------------------------------------------------------------
def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def agg(keyfn, keynames, path):
    acc = defaultdict(lambda: {"tot_clms": 0.0, "tot_30day_fills": 0.0, "tot_day_suply": 0.0, "tot_benes_sum": 0.0,
                               "ge65_tot_clms": 0.0, "n_prescribers": set(), "n_rows_benes_suppressed": 0,
                               "generics": set()})
    for r in kept:
        for cl in r["drug_classes"].split("; "):
            a = acc[keyfn(r) + (cl,)]
            a["tot_clms"] += num(r["Tot_Clms"]) or 0
            a["tot_30day_fills"] += num(r["Tot_30day_Fills"]) or 0
            a["tot_day_suply"] += num(r["Tot_Day_Suply"]) or 0
            a["ge65_tot_clms"] += num(r["GE65_Tot_Clms"]) or 0
            b = num(r["Tot_Benes"])
            if b is None:
                a["n_rows_benes_suppressed"] += 1
            else:
                a["tot_benes_sum"] += b
            a["n_prescribers"].add(r["Prscrbr_NPI"])
            a["generics"].add(r["Gnrc_Name"])
    rows = []
    for k, a in sorted(acc.items()):
        d = dict(zip(keynames + ["drug_class"], k))
        d.update({x: round(a[x], 1) for x in ["tot_clms", "tot_30day_fills", "tot_day_suply", "tot_benes_sum", "ge65_tot_clms"]})
        d["n_prescribers"] = len(a["n_prescribers"])
        d["small_cell"] = d["n_prescribers"] < 3  # app should not display single-prescriber cells on their own
        d["n_rows_benes_suppressed"] = a["n_rows_benes_suppressed"]
        d["generics"] = "; ".join(sorted(a["generics"]))
        d["year"] = YEAR
        rows.append(d)
    write_csv(path, rows, ["year"] + keynames + ["drug_class", "n_prescribers", "tot_clms", "tot_30day_fills", "tot_day_suply",
                                                  "tot_benes_sum", "n_rows_benes_suppressed", "ge65_tot_clms", "small_cell", "generics"])


agg(lambda r: (r["Prscrbr_Zip5"], r["modzcta"]), ["prscrbr_zip5", "modzcta"], os.path.join(OUT, "partd_nyc_zip_drugclass.csv"))
agg(lambda r: (r["Prscrbr_Type"],), ["prscrbr_type"], os.path.join(OUT, "partd_nyc_specialty_drugclass.csv"))
print("NYC prescribers:", len(npi), " NYC provider-drug rows kept:", len(kept))
