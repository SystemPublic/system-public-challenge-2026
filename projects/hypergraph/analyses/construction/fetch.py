"""Fetch the city tables the construction claims need, as lean column sets, through concord.socrata
(cached in data/cache/socrata, with a source record per query). Writes parquet copies to data/big/construction/
(gitignored) and the source records to data/derived/construction/sources.json. Run from the repo root."""
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import socrata as so

ROOT = Path(__file__).resolve().parents[2]
BIG = ROOT / "data" / "big" / "construction"
BIG.mkdir(parents=True, exist_ok=True)
DER = ROOT / "data" / "derived" / "construction"
DER.mkdir(parents=True, exist_ok=True)
SRC = DER / "sources.json"

JOBS = {
 "permits_nb_legacy": ("ipu4-2q9a", dict(select="job__,job_doc___,permit_type,filing_status,permit_status,issuance_date,expiration_date,bbl,borough,residential,gis_latitude,gis_longitude",
                                          where="job_type='NB'")),
 "co_legacy_nb": ("bs8b-p36w", dict(select="job_number,job_type,c_o_issue_date,issue_type,bbl,pr_dwelling_unit,ex_dwelling_unit", where="job_type='NB'")),
 "co_dobnow": ("pkdm-hqz6", dict(select="job_filing_name,job_type,c_of_o_issuance_date,c_of_o_filing_type,c_of_o_status,number_of_dwelling_units,bbl")),
 "jobs_nb_dobnow": ("w9ak-ipjd", dict(select="job_filing_number,filing_status,job_type,bbl,filing_date,first_permit_date,approved_date,signoff_date,proposed_dwelling_units,latitude,longitude",
                                       where="job_type='New Building'")),
 "dobnow_permits_2022on": ("rbx6-tga4", dict(select="job_filing_number,work_permit,filing_reason,work_type,permit_status,issued_date,expired_date,bbl",
                                              where="expired_date >= '2022-01-01T00:00:00'")),
 "legacy_shed_permits": ("ipu4-2q9a", dict(select="job__,job_type,permit_type,permit_subtype,filing_status,permit_status,issuance_date,expiration_date,bbl",
                                           where="permit_subtype='SH'")),
 "hdb_nb": ("br6q-ssj3", dict(select="job_number,job_type,job_status,permityear,compltyear,datepermit,datecomplt,classaprop,units_co,bbl", where="job_type='New Building'")),
}


def run(name, ds, soql, order=":id"):
    f = BIG / f"{name}.parquet"
    srcs = json.loads(SRC.read_text()) if SRC.exists() else {}
    if f.exists() and name in srcs:
        print("have", name)
        return
    t = time.time()
    rows, src = so.query_all(ds, order=order, **soql)
    df = pd.DataFrame(rows)
    df.to_parquet(f)
    srcs = json.loads(SRC.read_text()) if SRC.exists() else {}
    srcs[name] = src
    SRC.write_text(json.dumps(srcs, indent=1))
    print(name, len(df), f"{time.time()-t:.0f}s", flush=True)


if __name__ == "__main__":
    which = sys.argv[1:] or list(JOBS)
    for n in which:
        ds, soql = JOBS[n]
        run(n, ds, soql)
