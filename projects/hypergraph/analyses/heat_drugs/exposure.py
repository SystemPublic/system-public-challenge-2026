"""Exposure for the New York design: Medicare Part D prescribing by prescriber ZIP code, 2023.

Sources (CMS data API, data year 2023):
  Medicare Part D Prescribers - by Provider            dataset 42888afe-3b85-4a61-a4ee-091f00bd62bc
  Medicare Part D Prescribers - by Provider and Drug   dataset e54db557-cd82-4e91-a0fe-61aad5865d69
Rows are filtered to prescribers in New York State. The raw pages are cached in
~/Library/Caches/nyc-concordance-big/cms/ (outside Dropbox). Writes
data/derived/heat_drugs/zip_exposure.csv: by NYC ZIP code, all Part D claims, antipsychotic claims (all ages,
from the drug file), insulin and sulfonylurea claims, and the antipsychotic and diabetes-drug shares of claims.

As run on 13 November 2026 (default, no --drugs): the drug-file queries take about two minutes each on the CMS API,
so only the provider file is used. The exposure is then ap_share = antipsychotic claims for patients aged 65 or
over (Antpsyct_GE65_Tot_Clms) / all claims for patients aged 65 or over (GE65_Tot_Clms), by prescriber ZIP.

The ZIP is the prescriber's practice address, not the patient's home. That is the main weakness of the measure.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data/derived/heat_drugs"
CACHE = Path.home() / "Library/Caches/nyc-concordance-big/cms"
API = "https://data.cms.gov/data-api/v1/dataset/{}/data"
PROV = "42888afe-3b85-4a61-a4ee-091f00bd62bc"
DRUG = "e54db557-cd82-4e91-a0fe-61aad5865d69"
ANTIPSYCHOTICS = ["Quetiapine Fumarate", "Olanzapine", "Risperidone", "Aripiprazole", "Haloperidol", "Haloperidol Decanoate",
                  "Haloperidol Lactate", "Clozapine", "Ziprasidone Hcl", "Paliperidone", "Paliperidone Palmitate",
                  "Lurasidone Hcl", "Chlorpromazine Hcl", "Fluphenazine Hcl", "Fluphenazine Decanoate", "Perphenazine",
                  "Asenapine Maleate", "Brexpiprazole", "Cariprazine Hcl", "Iloperidone", "Loxapine Succinate",
                  "Thiothixene", "Trifluoperazine Hcl", "Aripiprazole Lauroxil", "Pimavanserin Tartrate", "Lumateperone Tosylate"]
DIABETES = ["Insulin Glargine,Hum.Rec.Anlog", "Insulin Lispro", "Insulin Aspart", "Insulin Detemir", "Insulin Degludec",
            "Insulin Nph Hum/Reg Insulin Hm", "Insulin Regular, Human", "Insulin Nph Human Isophane",
            "Glipizide", "Glimepiride", "Glyburide"]
NYC_ZIP_PREFIX = ("100", "101", "102", "103", "104", "110", "111", "112", "113", "114", "116")


def pages(ds: str, filt: dict, size: int = 5000) -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    out, off = [], 0
    while True:
        q = {f"filter[{k}]": v for k, v in filt.items()}
        q.update({"size": size, "offset": off})
        key = ds[:8] + "_" + "_".join(f"{k}-{v}" for k, v in sorted(filt.items())).replace(" ", "").replace("/", "")[:120] + f"_{off}.json"
        f = CACHE / key
        if f.exists():
            rows = json.loads(f.read_text())
        else:
            r = requests.get(API.format(ds) + "?" + urllib.parse.urlencode(q), timeout=180)
            r.raise_for_status()
            rows = r.json()
            f.write_text(json.dumps(rows))
            time.sleep(0.3)
        out += rows
        if len(rows) < size:
            return out
        off += size


def num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)


def main():
    prov = pd.DataFrame(pages(PROV, {"Prscrbr_State_Abrvtn": "NY"}))
    prov["zip"] = prov["Prscrbr_Zip5"].astype(str).str[:5]
    prov = prov[prov["zip"].str.startswith(NYC_ZIP_PREFIX)]
    prov["Tot_Clms"] = num(prov["Tot_Clms"])
    prov["Antpsyct_GE65_Tot_Clms"] = num(prov["Antpsyct_GE65_Tot_Clms"])
    prov["GE65_Tot_Clms"] = num(prov["GE65_Tot_Clms"])
    if "--drugs" not in sys.argv:
        z = prov.groupby("zip").agg(all_clms=("Tot_Clms", "sum"), ge65_clms=("GE65_Tot_Clms", "sum"),
                                    ap65_clms=("Antpsyct_GE65_Tot_Clms", "sum"), n_prescribers=("Prscrbr_NPI", "size"))
        z["ap_share"] = z["ap65_clms"] / z["ge65_clms"].where(z["ge65_clms"] > 0)
        z = z.reset_index()
        DER.mkdir(parents=True, exist_ok=True)
        z.to_csv(DER / "zip_exposure.csv", index=False)
        print(len(z), "ZIPs"); print(z.describe().T[["mean", "50%", "max"]])
        return
    npi_zip = prov.set_index("Prscrbr_NPI")["zip"]
    drows = []
    for cls, names in (("antipsychotic", ANTIPSYCHOTICS), ("diabetes", DIABETES)):
        for gname in names:
            for r in pages(DRUG, {"Prscrbr_State_Abrvtn": "NY", "Gnrc_Name": gname}):
                drows.append({"npi": r["Prscrbr_NPI"], "cls": cls, "drug": gname, "clms": r["Tot_Clms"]})
    d = pd.DataFrame(drows)
    d["clms"] = num(d["clms"])
    d["zip"] = d["npi"].map(npi_zip)
    d = d.dropna(subset=["zip"])
    by = d.pivot_table(index="zip", columns="cls", values="clms", aggfunc="sum").fillna(0)
    z = prov.groupby("zip").agg(all_clms=("Tot_Clms", "sum"), ap65_clms=("Antpsyct_GE65_Tot_Clms", "sum"),
                                n_prescribers=("Prscrbr_NPI", "size")).join(by).fillna(0)
    z["ap_share"] = z["antipsychotic"] / z["all_clms"].where(z["all_clms"] > 0)
    z["dm_share"] = z["diabetes"] / z["all_clms"].where(z["all_clms"] > 0)
    z = z.reset_index()
    DER.mkdir(parents=True, exist_ok=True)
    z.to_csv(DER / "zip_exposure.csv", index=False)
    print(len(z), "ZIPs; drug rows", len(d), "; per class", d.groupby("cls")["clms"].sum().to_dict())
    print(z.describe().T[["mean", "50%", "max"]])


if __name__ == "__main__":
    main()
