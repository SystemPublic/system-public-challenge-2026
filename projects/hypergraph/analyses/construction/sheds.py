"""Claim construction-sheds-outnumber-nb: active sidewalk-shed jobs against active new-building jobs on 2026-11-01,
with a monthly series from 2022. Inputs: data/big/construction/{dobnow_permits_2022on, legacy_shed_permits,
permits_nb_legacy, jobs_nb_dobnow}.parquet and data/derived/construction/nb_jobs.csv.gz.
Outputs: data/derived/construction/{sheds_summary.json, active_by_month.csv, active_by_worktype.csv}, figures/construction/active_sites.png."""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "data" / "big" / "construction"
D = ROOT / "data" / "derived" / "construction"
F = ROOT / "figures" / "construction"
DATE = pd.Timestamp("2026-11-01")

r = pd.read_parquet(B / "dobnow_permits_2022on.parquet")
r["iss"] = pd.to_datetime(r.issued_date, errors="coerce")
r["exp"] = pd.to_datetime(r.expired_date, errors="coerce")
r["job"] = r.job_filing_number.str.split("-").str[0]
dn = pd.read_parquet(B / "jobs_nb_dobnow.parquet")
nb_dobnow_jobs = set(dn.job_filing_number.str.split("-").str[0])
r["is_nb_job"] = r.job.isin(nb_dobnow_jobs)

lp = pd.read_parquet(B / "permits_nb_legacy.parquet")
lp["iss"] = pd.to_datetime(lp.issuance_date, format="%m/%d/%Y", errors="coerce")
lp["exp"] = pd.to_datetime(lp.expiration_date, format="%m/%d/%Y", errors="coerce")
ls = pd.read_parquet(B / "legacy_shed_permits.parquet")
ls["iss"] = pd.to_datetime(ls.issuance_date, format="%m/%d/%Y", errors="coerce")
ls["exp"] = pd.to_datetime(ls.expiration_date, format="%m/%d/%Y", errors="coerce")

CLOSED = {"Signed-off", "Revoked", "Withdrawn", "Expired"}


def active(df, d, exclude_closed=False):
    m = (df.iss <= d) & (df.exp > d)
    if exclude_closed and "permit_status" in df:
        m &= ~df.permit_status.isin(CLOSED)
    return df[m]


def counts(d, exclude_closed=False):
    sh = active(r[r.work_type == "Sidewalk Shed"], d, exclude_closed)
    lsh = active(ls, d)
    nbn = active(r[r.is_nb_job], d, exclude_closed)
    nbl = active(lp[lp.permit_type == "NB"], d)
    return dict(
        shed_jobs=sh.job.nunique() + lsh.job__.nunique(),
        shed_jobs_dobnow=sh.job.nunique(), shed_jobs_legacy=lsh.job__.nunique(),
        shed_bbls=len(set(sh.bbl.dropna()) | set(lsh.bbl.dropna().astype(str))),
        nb_jobs=nbn.job.nunique() + nbl.job__.nunique(),
        nb_jobs_dobnow=nbn.job.nunique(), nb_jobs_legacy=nbl.job__.nunique(),
        nb_bbls=len(set(nbn.bbl.dropna()) | set(nbl.bbl.dropna().astype(str))),
        _shed_bbls=set(sh.bbl.dropna()) | set(lsh.bbl.dropna().astype(str)),
        _nb_bbls=set(nbn.bbl.dropna()) | set(nbl.bbl.dropna().astype(str)),
    )


summ = {}
for var, ex in [("all_unexpired", False), ("excluding_signed_off", True)]:
    c = counts(DATE, ex)
    ov = len(c["_shed_bbls"] & c["_nb_bbls"])
    c["shed_bbls_on_active_nb_bbl"] = ov
    c["share_shed_bbls_on_nb"] = ov / max(c["shed_bbls"], 1)
    c["ratio_shed_to_nb_jobs"] = c["shed_jobs"] / max(c["nb_jobs"], 1)
    summ[var] = {k: v for k, v in c.items() if not k.startswith("_")}

# all NB jobs that are permitted and have no CO yet, first permit in the last six years (a wider definition)
nj = pd.read_csv(D / "nb_jobs.csv.gz", dtype={"job": str})
for c_ in ("first_permit", "first_co"):
    nj[c_] = pd.to_datetime(nj[c_], format="mixed", errors="coerce")
open_nb = nj[(nj.first_permit <= DATE) & (nj.first_permit > DATE - pd.DateOffset(years=6)) & (nj.first_co.isna() | (nj.first_co > DATE))]
summ["nb_jobs_permitted_6y_no_co"] = int(len(open_nb))

# active DOB NOW permits by work type (distinct jobs), for context
wt = active(r, DATE, True).groupby("work_type").job.nunique().sort_values(ascending=False)
wt.to_csv(D / "active_by_worktype.csv")
summ["active_jobs_by_worktype_excl_signed_off"] = wt.to_dict()
summ["active_jobs_any_dobnow_permit_excl_signed_off"] = int(active(r, DATE, True).job.nunique())
summ["date"] = str(DATE.date())

months = pd.date_range("2022-07-01", "2026-11-01", freq="MS")
ser = pd.DataFrame([{k: v for k, v in counts(m).items() if not k.startswith("_")} | {"month": m.date()} for m in months]).set_index("month")
ser.to_csv(D / "active_by_month.csv")
(D / "sheds_summary.json").write_text(json.dumps(summ, indent=1, default=int))
print(json.dumps(summ, indent=1, default=int))
print(ser[["shed_jobs", "nb_jobs"]].iloc[::6].to_string())

# figure
S1, S2, INK, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRID, "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF})
fig, (a, b) = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1.1, 1], "wspace": 0.55})
x = pd.to_datetime(ser.index)
a.plot(x, ser.shed_jobs, color=S1, lw=2, label="jobs with an unexpired sidewalk-shed permit")
a.plot(x, ser.nb_jobs, color=S2, lw=2, label="jobs with an unexpired new-building work permit")
a.set_ylim(0, None); import matplotlib.dates as mdates; a.xaxis.set_major_locator(mdates.YearLocator()); a.xaxis.set_major_formatter(mdates.DateFormatter("%Y")); a.yaxis.grid(True, color=GRID, lw=0.6)
a.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1))
a.set_title("Active sites by month, 2022-2026", loc="left", fontsize=10, color=INK)
top = wt.head(10)[::-1]
b.barh(range(len(top)), top.values, color=S1, height=0.62)
for i, v in enumerate(top.values):
    b.text(v + 100, i, f"{v:,}", va="center", fontsize=8, color=INK)
b.set_yticks(range(len(top)), top.index, fontsize=8)
b.xaxis.grid(True, color=GRID, lw=0.6); b.set_axisbelow(True)
b.set_title(f"Jobs with an active DOB NOW permit\non {DATE.date()}, by work type (10 largest)", loc="left", fontsize=10, color=INK)
fig.text(0, -0.12, "Sources: NYC Open Data rbx6-tga4 (DOB NOW Build approved permits), w9ak-ipjd, ipu4-2q9a. 'Active' = issued on or before the date and expiring after it.",
         fontsize=7, color=INK2)
p = F / "active_sites.png"
fig.savefig(p, dpi=200, bbox_inches="tight")
subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(p)], capture_output=True)
