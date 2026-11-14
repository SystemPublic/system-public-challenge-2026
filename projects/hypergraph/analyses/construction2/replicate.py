"""Run the two registered replications (claims construction2-rows-per-job-*). Inputs: parquet files from
analyses/construction/fetch.py and one new SoQL aggregation of rbx6-tga4. Outputs in data/derived/construction2/."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata as so

B = ROOT / "data" / "big" / "construction"
D = ROOT / "data" / "derived" / "construction2"
D.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261113)


def boot(x, n=2000):
    x = np.asarray(x, float)
    m = rng.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


out = {}
# ---- legacy cohorts 2000-2009 ----
p = pd.read_parquet(B / "permits_nb_legacy.parquet")
p["iss"] = pd.to_datetime(p.issuance_date, format="%m/%d/%Y", errors="coerce")
p["job"] = p["job__"].astype(str)
nbp = p[p.permit_type == "NB"].groupby("job").iss.min()
g = p.groupby("job").agg(first_any=("iss", "min"), n_rows=("iss", "size"),
                         n_ren=("filing_status", lambda s: (s == "RENEWAL").sum()))
g["first"] = nbp.reindex(g.index).fillna(g.first_any)
g["cohort"] = g["first"].dt.year
L = g[g.cohort.between(2000, 2009)]
by = L.groupby("cohort").agg(jobs=("n_rows", "size"), mean_rows=("n_rows", "mean"), median_rows=("n_rows", "median"),
                             rows=("n_rows", "sum"), renewals=("n_ren", "sum"))
by["renewal_share"] = by.renewals / by.rows
by.to_csv(D / "legacy_rows_per_job_2000_2009.csv")
m, lo, hi = boot(L.n_rows)
out["legacy"] = dict(pooled_mean=m, lo=lo, hi=hi, jobs=int(len(L)), rows=int(L.n_rows.sum()),
                     min_cohort_mean=float(by.mean_rows.min()), cohorts_below_4=int((by.mean_rows < 4).sum()),
                     cohorts_below_3=int((by.mean_rows < 3).sum()))
print(by.to_string()); print(out["legacy"])

# ---- DOB NOW cohorts 2021-2022 ----
dn = pd.read_parquet(B / "jobs_nb_dobnow.parquet")
dn["job"] = dn.job_filing_number.str.split("-").str[0]
dn["fp"] = pd.to_datetime(dn.first_permit_date, errors="coerce")
jj = dn.groupby("job").fp.min().dropna()
jj = jj[jj.dt.year.isin([2021, 2022])]
soql = dict(select="job_filing_number, work_type, filing_reason, count(*) as n", where="issued_date >= '2020-01-01T00:00:00'",
            group="job_filing_number, work_type, filing_reason")
rows, src = so.query_all("rbx6-tga4", order="job_filing_number, work_type, filing_reason", **soql)
r = pd.DataFrame(rows)
r["n"] = r.n.astype(int)
r["job"] = r.job_filing_number.str.split("-").str[0]
r = r[r.job.isin(jj.index)]
per = r.groupby("job").n.sum().reindex(jj.index, fill_value=0)
coh = jj.dt.year
dd = pd.DataFrame({"rows": per, "cohort": coh})
dd.to_csv(D / "dobnow_rows_per_job.csv")
m, lo, hi = boot(dd.rows)
out["dobnow"] = dict(pooled_mean=m, lo=lo, hi=hi, median=float(dd.rows.median()), jobs=int(len(dd)), zero_rows=int((dd.rows == 0).sum()),
                     by_cohort={int(k): dict(jobs=int(len(v)), mean=float(v.rows.mean()), median=float(v.rows.median())) for k, v in dd.groupby("cohort")},
                     by_work_type=r.groupby("work_type").n.sum().sort_values(ascending=False).astype(int).to_dict(),
                     by_filing_reason=r.groupby("filing_reason").n.sum().sort_values(ascending=False).astype(int).to_dict())
mn = dd[dd.rows > 0]
out["dobnow"]["mean_excluding_zero"] = float(mn.rows.mean())
print(json.dumps(out["dobnow"], indent=1))
srcs = json.loads((ROOT / "data/derived/construction/sources.json").read_text())
out["sources"] = [srcs["permits_nb_legacy"], srcs["jobs_nb_dobnow"], src]
(D / "replication_summary.json").write_text(json.dumps(out, indent=1, default=str))
