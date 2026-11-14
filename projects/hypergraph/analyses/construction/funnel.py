"""Claims construction-permit-funnel and construction-four-year-completion.
Inputs: data/big/construction/*.parquet from fetch.py, data/derived/construction/pluto_yearbuilt.csv.
Outputs: data/derived/construction/{funnel_by_year.csv, nb_jobs.csv.gz, cohort_completion.csv, funnel_summary.json}."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "data" / "big" / "construction"
D = ROOT / "data" / "derived" / "construction"
CUTOFF = pd.Timestamp("2026-11-11")  # last update of the CO tables


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, c - h, c + h)


# ---- legacy permit rows ----
p = pd.read_parquet(B / "permits_nb_legacy.parquet")
p["iss"] = pd.to_datetime(p.issuance_date, format="%m/%d/%Y", errors="coerce")
p["exp"] = pd.to_datetime(p.expiration_date, format="%m/%d/%Y", errors="coerce")
p["year"] = p.iss.dt.year
p["job"] = p["job__"].astype(str)

rows_year = p.groupby("year").agg(rows=("job", "size"), jobs_any_row=("job", "nunique"),
                                  renewal_rows=("filing_status", lambda s: (s == "RENEWAL").sum()),
                                  nb_type_rows=("permit_type", lambda s: (s == "NB").sum()))

# per-job first NB-type permit (the work permit for the building), else first permit of any type
nbp = p[p.permit_type == "NB"].groupby("job").iss.min().rename("first_nb_permit")
anyp = p.groupby("job").agg(first_any_permit=("iss", "min"), n_rows=("iss", "size"),
                            n_renewals=("filing_status", lambda s: (s == "RENEWAL").sum()),
                            last_exp=("exp", "max"), bbl=("bbl", "first"), residential=("residential", "first"))
jobs = anyp.join(nbp, how="left")
jobs["first_permit"] = jobs.first_nb_permit.fillna(jobs.first_any_permit)
jobs["cohort"] = jobs.first_permit.dt.year
jobs["system"] = "BIS"

# ---- DOB NOW NB jobs (job number = filing number before '-') ----
dn = pd.read_parquet(B / "jobs_nb_dobnow.parquet")
dn["job"] = dn.job_filing_number.str.split("-").str[0]
dn["fp"] = pd.to_datetime(dn.first_permit_date, errors="coerce")
dnj = dn.groupby("job").agg(first_permit=("fp", "min"), bbl=("bbl", "first"),
                             withdrawn=("filing_status", lambda s: (s == "Filing Withdrawn").all()))
dnj = dnj[dnj.first_permit.notna()].copy()
dnj["cohort"] = dnj.first_permit.dt.year
dnj["system"] = "DOB NOW"

# ---- certificates of occupancy, earliest per job, both systems ----
c1 = pd.read_parquet(B / "co_legacy_nb.parquet")
c1["d"] = pd.to_datetime(c1.c_o_issue_date, errors="coerce")
c1 = c1[c1.d <= CUTOFF]
c1g = c1.groupby(c1.job_number.astype(str)).agg(co1=("d", "min"),
                                              final1=("issue_type", lambda s: (s == "Final").any()))
c2 = pd.read_parquet(B / "co_dobnow.parquet")
c2["d"] = pd.to_datetime(c2.c_of_o_issuance_date, format="mixed", errors="coerce")
c2 = c2[(c2.c_of_o_status == "CO Issued") & (c2.d <= CUTOFF)]
c2g = c2.groupby(c2.job_filing_name.astype(str)).agg(co2=("d", "min"),
                                                   final2=("c_of_o_filing_type", lambda s: (s == "Final").any()))
co = c1g.join(c2g, how="outer")
co["first_co"] = co[["co1", "co2"]].min(axis=1)
co["final_co"] = co.final1.fillna(False).astype(bool) | co.final2.fillna(False).astype(bool)

alljobs = pd.concat([jobs[["first_permit", "cohort", "system", "bbl", "n_rows", "n_renewals"]],
                     dnj[["first_permit", "cohort", "system", "bbl"]]])
alljobs = alljobs.join(co[["first_co", "final_co"]], how="left")
alljobs["final_co"] = alljobs.final_co.fillna(False).astype(bool)
alljobs["years_to_co"] = (alljobs.first_co - alljobs.first_permit).dt.days / 365.25
alljobs.index.name = "job"
alljobs.reset_index().to_csv(D / "nb_jobs.csv.gz", index=False)

# ---- HDB completions (residential NB) ----
h = pd.read_parquet(B / "hdb_nb.parquet")
h["compltyear"] = pd.to_numeric(h.compltyear, errors="coerce")
h["units_co"] = pd.to_numeric(h.units_co, errors="coerce")
h["classaprop"] = pd.to_numeric(h.classaprop, errors="coerce")
hdb_y = h[h.job_status.str.startswith("5")].groupby("compltyear").agg(hdb_completed_jobs=("job_number", "size"),
                                                                      hdb_units=("classaprop", "sum"))
hdb_perm = h.assign(py=pd.to_numeric(h.permityear, errors="coerce")).groupby("py").agg(hdb_permitted_jobs=("job_number", "size"))

pl = pd.read_csv(D / "pluto_yearbuilt.csv").set_index("yearbuilt").rename(columns={"lots": "pluto_lots_yearbuilt", "units": "pluto_units_yearbuilt"})

# ---- funnel by year ----
yrs = range(2010, 2027)
f = pd.DataFrame(index=pd.Index(yrs, name="year"))
f = f.join(rows_year[["rows", "renewal_rows", "jobs_any_row"]].rename(columns={"rows": "legacy_nb_permit_rows"}))
f["nb_jobs_first_permit"] = alljobs.groupby("cohort").size()
f["nb_jobs_first_permit_bis"] = alljobs[alljobs.system == "BIS"].groupby("cohort").size()
f["nb_jobs_first_permit_dobnow"] = alljobs[alljobs.system == "DOB NOW"].groupby("cohort").size()
f["cohort_jobs_with_co_by_2026"] = alljobs[alljobs.first_co.notna()].groupby("cohort").size()
f["cohort_jobs_co_within_4y"] = alljobs[alljobs.years_to_co <= 4].groupby("cohort").size()
f["nb_jobs_first_co_in_year"] = alljobs[alljobs.first_co.notna()].groupby(alljobs.first_co.dt.year).size()
f["rows_per_job_lifetime_by_cohort"] = jobs.groupby("cohort").n_rows.mean()
f = f.join(hdb_y).join(hdb_perm.rename_axis("year")).join(pl[["pluto_lots_yearbuilt", "pluto_units_yearbuilt"]])
f["rows_per_job_active"] = f.legacy_nb_permit_rows / f.jobs_any_row
f.to_csv(D / "funnel_by_year.csv")
print(f.to_string())

# ---- cohort completion (four-year claim) ----
out = []
for y in range(2010, 2023):
    s = alljobs[alljobs.cohort == y]
    n = len(s)
    k4 = int((s.years_to_co <= 4).sum())
    kall = int(s.first_co.notna().sum())
    p4, lo4, hi4 = wilson(k4, n)
    pa, loa, hia = wilson(kall, n)
    med = float(s.years_to_co.median()) if kall else None
    out.append(dict(cohort=y, jobs=n, co_within_4y=k4, share_4y=p4, lo_4y=lo4, hi_4y=hi4,
                    co_by_nov2026=kall, share_ever=pa, lo_ever=loa, hi_ever=hia, median_years_to_co=med,
                    final_co=int(s.final_co.sum()),
                    full_4y_window=(pd.Timestamp(f"{y}-12-31") + pd.Timedelta(days=1461)) <= CUTOFF))
cc = pd.DataFrame(out)
cc.to_csv(D / "cohort_completion.csv", index=False)
print(cc.to_string())

pool = alljobs[alljobs.cohort.between(2013, 2017)]
pool_all = alljobs[alljobs.cohort.between(2010, 2017)]
summ = {}
for name, s in [("2010_2017", pool_all), ("2013_2017", pool)]:
    n = len(s); k = int((s.years_to_co <= 4).sum())
    summ[f"share_4y_{name}"] = dict(zip(["p", "lo", "hi"], wilson(k, n))) | {"k": k, "n": n}
    summ[f"median_years_to_co_{name}"] = float(s.years_to_co.median())
s = alljobs[alljobs.cohort.between(2010, 2014)]
summ["share_ever_2010_2014"] = dict(zip(["p", "lo", "hi"], wilson(int(s.first_co.notna().sum()), len(s)))) | {"n": len(s)}
r = rows_year.loc[2010:2019]
summ["rows_per_active_job_2010_2019"] = float(r.rows.sum() / r.jobs_any_row.sum())
rr = p[p.year.between(2010, 2019)]
summ["rows_per_unique_job_2010_2019"] = float(len(rr) / rr.job.nunique())
summ["rows_2010_2019"] = int(len(rr)); summ["unique_jobs_2010_2019"] = int(rr.job.nunique())
# HDB check of left truncation: residential NB jobs permitted 2010-2017, completion within 4 years (HDB dates)
hh = h.assign(dp=pd.to_datetime(h.datepermit, errors="coerce"), dc=pd.to_datetime(h.datecomplt, errors="coerce"))
hh = hh[hh.dp.notna()]
hh["cy"] = hh.dp.dt.year
hh["in4"] = (hh.dc - hh.dp).dt.days <= 1461
summ["hdb_share_4y_by_cohort"] = {int(y): round(float(g.in4.mean()), 3) for y, g in hh[hh.cy.between(2010, 2021)].groupby("cy")}
summ["hdb_n_by_cohort"] = {int(y): int(len(g)) for y, g in hh[hh.cy.between(2010, 2021)].groupby("cy")}
summ["legacy_rows_total"] = int(len(p))
summ["legacy_jobs_total"] = int(p.job.nunique())
summ["renewal_share_rows"] = float((p.filing_status == "RENEWAL").mean())
summ["rows_per_job_alltime"] = float(len(p) / p.job.nunique())
(D / "funnel_summary.json").write_text(json.dumps(summ, indent=1, default=str))
print(json.dumps(summ, indent=1, default=str))
