"""Prescriber specialty shares per HeatRx drug class, from US Medicare Part D (CMS public data).

Source: Medicare Part D Prescribers - by Provider and Drug, data year 2024 (data.cms.gov, dataset
9552739e-3d05-4c1b-8eff-ecabf391e2e5). Claims (Tot_Clms) are summed by prescriber type (Prscrbr_Type).

Rows come ordered by prescriber NPI, which is unrelated to specialty, so for common drugs the first
MAX_PAGES x 5,000 prescribers are used as a sample; the output records how many rows were read.

Usage (from the repo root):
  python3 -I scripts/medicare_specialty.py data/medicare reference/medicare_specialty.json
"""
import collections
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

cache_dir, out_path = sys.argv[1:3]
os.makedirs(cache_dir, exist_ok=True)
DATASET = "9552739e-3d05-4c1b-8eff-ecabf391e2e5"
BASE = "https://data.cms.gov/data-api/v1/dataset/%s/data" % DATASET
PAGE, MAX_PAGES = 5000, 4
POOL = ThreadPoolExecutor(6)

# Commonly prescribed members per class, as CMS spells the generic name (Gnrc_Name).
DRUGS = {
    "diuretics": ["Furosemide", "Hydrochlorothiazide", "Chlorthalidone", "Spironolactone", "Bumetanide", "Torsemide"],
    "beta_blockers": ["Metoprolol Succinate", "Metoprolol Tartrate", "Carvedilol", "Atenolol", "Propranolol HCl"],
    "acei_arb": ["Lisinopril", "Losartan Potassium", "Valsartan", "Olmesartan Medoxomil", "Benazepril HCl"],
    "ccb": ["Amlodipine Besylate", "Diltiazem HCl", "Nifedipine", "Verapamil HCl"],
    "anticholinergics": ["Oxybutynin Chloride", "Tolterodine Tartrate", "Solifenacin Succinate", "Benztropine Mesylate", "Trospium Chloride"],
    "antipsychotics": ["Quetiapine Fumarate", "Olanzapine", "Risperidone", "Aripiprazole", "Haloperidol"],
    "antidepressants": ["Sertraline HCl", "Escitalopram Oxalate", "Citalopram Hydrobromide", "Fluoxetine HCl",
                        "Duloxetine HCl", "Mirtazapine", "Bupropion HCl", "Venlafaxine HCl", "Amitriptyline HCl"],
    "lithium": ["Lithium Carbonate"],
    "insulin": ["Insulin Glargine,hum.Rec.Anlog", "Insulin Lispro", "Insulin Aspart", "Insulin Degludec"],
    "sglt2": ["Empagliflozin", "Dapagliflozin Propanediol", "Canagliflozin"],
    "other_diabetes": ["Metformin HCl", "Glipizide", "Semaglutide", "Glimepiride", "Dulaglutide"],
    "anticonvulsants": ["Topiramate", "Divalproex Sodium", "Carbamazepine", "Oxcarbazepine"],
    "nsaids": ["Meloxicam", "Ibuprofen", "Naproxen", "Diclofenac Sodium", "Celecoxib"],
    "opioids_sedatives": ["Oxycodone HCl", "Hydrocodone/Acetaminophen", "Tramadol HCl", "Lorazepam", "Alprazolam", "Zolpidem Tartrate"],
    "stimulants": ["Methylphenidate HCl", "Dextroamphetamine/Amphetamine"],
    "antihistamines": ["Hydroxyzine HCl", "Promethazine HCl"],
}


def get(url):
    path = os.path.join(cache_dir, urllib.parse.quote(url, safe="")[-180:] + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    for attempt in range(4):
        try:
            data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "heatrx-hackathon/0.1"}), timeout=120))
            json.dump(data, open(path, "w"))
            return data
        except Exception as e:  # transient network or server error
            print("retry", attempt, e, flush=True)
            time.sleep(3 + 5 * attempt)
    raise RuntimeError("failed: " + url)


out = {"source": "CMS Medicare Part D Prescribers - by Provider and Drug, data year 2024; dataset " + DATASET,
       "measure": "share of Part D claims (Tot_Clms) by prescriber type",
       "sample": "first %d prescriber rows per drug (rows ordered by NPI)" % (PAGE * MAX_PAGES),
       "drugs": {}, "classes": {}}
for cls, names in DRUGS.items():
    agg = collections.Counter()
    for name in names:
        q = urllib.parse.quote(name)
        stats = get(BASE + "/stats?filter[Gnrc_Name]=" + q)
        found = stats.get("found_rows", 0)
        d = collections.Counter()
        read = 0
        urls = ["%s?size=%d&offset=%d&column=Prscrbr_Type,Tot_Clms&filter[Gnrc_Name]=%s" % (BASE, PAGE, p * PAGE, q)
                for p in range(min(MAX_PAGES, (found + PAGE - 1) // PAGE))]
        for rows in POOL.map(get, urls):
            read += len(rows)
            for r in rows:
                try:
                    d[r.get("Prscrbr_Type") or "Unknown"] += int(r.get("Tot_Clms") or 0)
                except ValueError:
                    pass
        out["drugs"][name] = {"class": cls, "prescribers": found, "rows_read": read, "claims_read": sum(d.values())}
        print(cls, name, "prescribers", found, "read", read, flush=True)
        agg.update(d)
    tot = sum(agg.values()) or 1
    out["classes"][cls] = {"claims_read": sum(agg.values()),
                           "by_type": [[k, round(v / tot, 4)] for k, v in agg.most_common(12)]}
json.dump(out, open(out_path, "w"), indent=1)
print("written", out_path)
