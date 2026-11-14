"""EXPLORATORY (written after the registered result of stalled-421a-vesting-footings was seen; decides nothing).
The registered outcome matched certificates of occupancy to jobs by BBL only. A check by job number showed that BBL
matching misses many certificates for the older cohorts (the lot recorded on the permit is not the lot recorded on the
certificate). This script matches a certificate to a job if either the job number or the BBL agrees, using both CO
tables (the DOB NOW table also carries BIS job numbers), and reports the 36-month and 48-month non-completion rates."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "data" / "big" / "construction"
D = ROOT / "data" / "derived" / "stalled"
rng = np.random.default_rng(20261113)

s = pd.read_csv(D / "vesting_jobs.csv", dtype=str)
s["start"] = pd.to_datetime(s.start)
s["jobno"] = s.job.str[1:]
c1 = pd.read_parquet(B / "co_legacy_nb.parquet")
c2 = pd.read_parquet(B / "co_dobnow.parquet")
co = pd.concat([pd.DataFrame({"jobno": c1.job_number.astype(str), "d": pd.to_datetime(c1.c_o_issue_date, errors="coerce")}),
                pd.DataFrame({"jobno": c2.job_filing_name.astype(str).str.split("-").str[0],
                              "d": pd.to_datetime(c2.c_of_o_issuance_date, errors="coerce", format="mixed")})]).dropna()
first_job = co[co.d.notna()].groupby("jobno").d.min()
s["co_job"] = s.jobno.map(first_job)
# BBL-matched first CO after start, from the registered run's logic
from vesting_cohorts import cos, okbbl  # noqa: E402
cb = cos()[0]
m = s[["job", "bbl", "start"]].merge(cb, on="bbl", how="left")
m = m[m.d > m.start]
s["co_bbl"] = s.job.map(m.groupby("job").d.min())
s["co_any"] = s[["co_job", "co_bbl"]].min(axis=1)
age = (s.co_any - s.start).dt.days
for h in (1096, 1461):
    s[f"stalled_{h}"] = (~age.between(-60, h)).astype(int)
asof = pd.Timestamp("2026-11-01")
res = {}
for h in (1096, 1461):
    col = f"stalled_{h}"
    r = {}
    for w, g in s.groupby("window"):
        full = (pd.Timestamp(int(w), 6, 15) + pd.Timedelta(days=h)) <= asof
        r[int(w)] = dict(rate=round(float(g[col].mean()), 3), n=int(len(g)), full_followup=bool(full),
                         legacy=round(float(g[g.system == "legacy"][col].mean()), 3) if (g.system == "legacy").any() else None,
                         dobnow=round(float(g[g.system == "dobnow"][col].mean()), 3) if (g.system == "dobnow").any() else None)
    res[f"horizon_{h}"] = r


def bd(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = rng.choice(a, (2000, len(a))).mean(1) - rng.choice(b, (2000, len(b))).mean(1)
    return [round(float(a.mean() - b.mean()), 3), round(float(np.percentile(d, 2.5)), 3), round(float(np.percentile(d, 97.5)), 3)]


x = s.stalled_1096
res["D1_union_36m"] = bd(x[s.window == "2022"], x[s.window.isin(["2017", "2018", "2019"])])
res["D2_union_36m"] = bd(x[s.window == "2022"], x[s.window == "2023"])
leg = s.system == "legacy"
res["D1_union_36m_legacy_only"] = bd(x[(s.window == "2022") & leg], x[s.window.isin(["2017", "2018", "2019"]) & leg])
res["D1_union_36m_vs_2021"] = bd(x[s.window == "2022"], x[s.window == "2021"])
# Jobs in the rush window with no CO at all by Nov 2026
rush = s[s.window == "2022"]
res["rush_no_co_by_nov2026"] = dict(n=int(rush.co_any.isna().sum()), of=int(len(rush)))
print(json.dumps(res, indent=1))
(D / "vesting_exploratory.json").write_text(json.dumps(res, indent=1))
s.to_csv(D / "vesting_jobs_union.csv", index=False)
