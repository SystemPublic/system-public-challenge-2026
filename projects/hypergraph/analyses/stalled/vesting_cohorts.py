"""Claim stalled-421a-vesting-footings: did new-building jobs whose foundation work started in the six months
before the 421-a vesting deadline (15 June 2022) fail to reach a certificate of occupancy within 36 months more
often than jobs that started foundations in the same calendar window of 2017-2019, and of 2023?

Unit: a new-building (NB) job, legacy BIS or DOB NOW. Start date: the earliest INITIAL foundation permit of the job
(legacy ipu4-2q9a permit_type FO on job_type NB; DOB NOW rbx6-tga4 work_type Foundation, filing_reason Initial Permit,
on a job listed as New Building in w9ak-ipjd). Window for year y: 15 Dec (y-1) to 14 Jun y inclusive.
Outcome: 1 if no certificate of occupancy (temporary or final; legacy bs8b-p36w NB rows or DOB NOW pkdm-hqz6 rows) is
recorded on the job's BBL within 1,096 days after the start date, else 0. Matching is by BBL, not job number,
because job numbers change between BIS and DOB NOW. Jobs with a malformed BBL (not 10 digits, lot 0) are dropped.

Statistics: D1 = rate(2022) - rate(2017-2019 pooled); D2 = rate(2022) - rate(2023). Percentile bootstrap,
2,000 draws, seed 20261113, resampling jobs within each window.

Usage: python analyses/stalled/vesting_cohorts.py sizes   (window sizes only; no outcome is read)
       python analyses/stalled/vesting_cohorts.py run     (the registered test)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata as so

B = ROOT / "data" / "big" / "construction"
OUT = ROOT / "data" / "derived" / "stalled"
OUT.mkdir(parents=True, exist_ok=True)
SEED, DRAWS, HORIZON = 20261113, 2000, 1096
YEARS = [2017, 2018, 2019, 2020, 2021, 2022, 2023]


def okbbl(s):
    s = s.astype(str).str.replace(r"\.0+$", "", regex=True).str.strip()
    good = s.str.fullmatch(r"[1-5]\d{9}") & (s.str[-4:] != "0000")
    return s.where(good)


def starts():
    srcs = []
    p = pd.read_parquet(B / "permits_nb_legacy.parquet")
    p = p[(p.permit_type == "FO") & (p.filing_status == "INITIAL")].copy()
    p["d"] = pd.to_datetime(p.issuance_date, format="%m/%d/%Y", errors="coerce")
    p["bbl"] = okbbl(p.bbl)
    leg = p.dropna(subset=["d", "bbl"]).groupby("job__").agg(start=("d", "min"), bbl=("bbl", "first")).reset_index()
    leg["job"] = "L" + leg.job__.astype(str)
    leg["system"] = "legacy"
    srcs.append(json.loads((ROOT / "data/derived/construction/sources.json").read_text())["permits_nb_legacy"])

    rows, src = so.query_all("rbx6-tga4", select="job_filing_number,work_type,filing_reason,issued_date,bbl",
                             where="work_type='Foundation'", order="job_filing_number,issued_date")
    srcs.append(src)
    f = pd.DataFrame(rows)
    f = f[f.filing_reason == "Initial Permit"].copy()
    f["job"] = f.job_filing_number.str.split("-").str[0]
    nb = pd.read_parquet(B / "jobs_nb_dobnow.parquet")
    nbjobs = set(nb.job_filing_number.str.split("-").str[0])
    srcs.append(json.loads((ROOT / "data/derived/construction/sources.json").read_text())["jobs_nb_dobnow"])
    f = f[f.job.isin(nbjobs)]
    f["d"] = pd.to_datetime(f.issued_date, errors="coerce")
    f["bbl"] = okbbl(f.bbl)
    dn = f.dropna(subset=["d", "bbl"]).groupby("job").agg(start=("d", "min"), bbl=("bbl", "first")).reset_index()
    dn["job"] = "N" + dn.job
    dn["system"] = "dobnow"
    s = pd.concat([leg[["job", "start", "bbl", "system"]], dn[["job", "start", "bbl", "system"]]], ignore_index=True)
    s["window"] = np.nan
    for y in YEARS:
        m = (s.start >= pd.Timestamp(y - 1, 12, 15)) & (s.start < pd.Timestamp(y, 6, 15))
        s.loc[m, "window"] = y
    return s.dropna(subset=["window"]).assign(window=lambda d: d.window.astype(int)), srcs


def cos():
    c1 = pd.read_parquet(B / "co_legacy_nb.parquet")
    c1 = pd.DataFrame({"bbl": okbbl(c1.bbl), "d": pd.to_datetime(c1.c_o_issue_date, errors="coerce")})
    c2 = pd.read_parquet(B / "co_dobnow.parquet")
    c2 = pd.DataFrame({"bbl": okbbl(c2.bbl), "d": pd.to_datetime(c2.c_of_o_issuance_date, errors="coerce")})
    srcs = json.loads((ROOT / "data/derived/construction/sources.json").read_text())
    return pd.concat([c1, c2]).dropna(), [srcs["co_legacy_nb"], srcs["co_dobnow"]]


def outcome(s, c):
    m = s.merge(c, on="bbl", how="left", suffixes=("", "_co"))
    m["hit"] = (m.d > m.start) & (m.d <= m.start + pd.Timedelta(days=HORIZON))
    done = m.groupby("job").hit.any()
    s = s.set_index("job")
    s["stalled"] = (~done.reindex(s.index).fillna(False)).astype(int)
    return s.reset_index()


def boot_diff(a, b, rng):
    a, b = np.asarray(a, float), np.asarray(b, float)
    da = rng.choice(a, size=(DRAWS, len(a))).mean(1)
    db = rng.choice(b, size=(DRAWS, len(b))).mean(1)
    d = da - db
    return dict(est=float(a.mean() - b.mean()), lo=float(np.percentile(d, 2.5)), hi=float(np.percentile(d, 97.5)))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "sizes"
    s, srcs = starts()
    sizes = s.groupby(["window", "system"]).size().unstack(fill_value=0)
    print(sizes.to_string())
    if mode == "sizes":
        (OUT / "vesting_window_sizes.json").write_text(json.dumps({int(k): v for k, v in s.groupby("window").size().items()}, indent=1))
        sys.exit(0)
    c, csrc = cos()
    srcs += csrc
    s = outcome(s, c)
    s.to_csv(OUT / "vesting_jobs.csv", index=False)
    rng = np.random.default_rng(SEED)
    rate = s.groupby("window").stalled.agg(["mean", "size"])
    ctrl = s[s.window.isin([2017, 2018, 2019])].stalled
    rush = s[s.window == 2022].stalled
    post = s[s.window == 2023].stalled
    D1 = boot_diff(rush, ctrl, rng)
    D2 = boot_diff(rush, post, rng)
    res = dict(rates={int(k): dict(rate=float(v["mean"]), n=int(v["size"])) for k, v in rate.iterrows()},
               rates_by_system={f"{int(w)}-{sy}": dict(rate=float(g.stalled.mean()), n=int(len(g))) for (w, sy), g in s.groupby(["window", "system"])},
               D1_rush_minus_2017_2019=D1, D2_rush_minus_2023=D2, seed=SEED, draws=DRAWS, horizon_days=HORIZON, sources=srcs)
    print(json.dumps({k: v for k, v in res.items() if k != "sources"}, indent=1))
    (OUT / "vesting_result.json").write_text(json.dumps(res, indent=1, default=str))
