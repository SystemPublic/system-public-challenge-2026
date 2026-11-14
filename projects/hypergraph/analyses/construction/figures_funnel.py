"""Figures for construction-permit-funnel and construction-four-year-completion.
Reads data/derived/construction/{funnel_by_year.csv, cohort_completion.csv, funnel_summary.json}; writes figures/construction/*.png (sRGB tagged)."""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "construction"
F = ROOT / "figures" / "construction"
F.mkdir(parents=True, exist_ok=True)
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})


def save(fig, name):
    p = F / name
    fig.savefig(p, dpi=200, bbox_inches="tight")
    plt.close(fig)
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(p)], capture_output=True)
    print(p.relative_to(ROOT))


f = pd.read_csv(D / "funnel_by_year.csv", index_col=0)
cc = pd.read_csv(D / "cohort_completion.csv")
sm = json.loads((D / "funnel_summary.json").read_text())

# 1. funnel, permits issued 2010-2019 and their outcomes
c = f.loc[2010:2019]
stages = [
    ("NB permit rows issued 2010-2019\n(legacy DOB Permit Issuance)", sm["rows_2010_2019"]),
    ("Distinct NB jobs with any of those rows", sm["unique_jobs_2010_2019"]),
    ("NB jobs whose first NB permit\nwas issued 2010-2019", int(c.nb_jobs_first_permit.sum())),
    ("... of which reached a certificate\nof occupancy by Nov 2026", int(c.cohort_jobs_with_co_by_2026.sum())),
    ("Housing Database: new buildings\ncompleted 2012-2021 (residential)", int(f.loc[2012:2021].hdb_completed_jobs.sum())),
    ("PLUTO lots with year built 2012-2021", int(f.loc[2012:2021].pluto_lots_yearbuilt.sum())),
]
fig, ax = plt.subplots(figsize=(8, 3.8))
for i, (lab, v) in enumerate(stages):
    ax.barh(i, v, color=S1 if i < 2 else S3, height=0.62)
    ax.text(v + 2500, i, f"{v:,}", va="center", color=INK, fontsize=9)
ax.set_yticks(range(len(stages)), [s[0] for s in stages], fontsize=8.5)
ax.invert_yaxis()
ax.set_xlim(0, max(v for _, v in stages) * 1.15)
ax.xaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
ax.set_xlabel("count")
ax.set_title("From permit rows to buildings, New York City new-building (NB) jobs", loc="left", color=INK, fontsize=11)
fig.text(0, -0.04, "Sources: NYC Open Data ipu4-2q9a, bs8b-p36w, pkdm-hqz6, br6q-ssj3, 64uk-42ks (versions in data/derived/construction/sources.json).",
         fontsize=7, color=INK2)
save(fig, "funnel_2010_2019.png")

# 2. by year, two panels (rows; jobs and outcomes)
fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.6))
yy = f.loc[2010:2025]
a.plot(yy.index, yy.legacy_nb_permit_rows, color=S1, lw=2, label="NB permit rows issued (legacy)")
a.plot(yy.index, yy.renewal_rows, color=S2, lw=2, label="of which renewals")
a.set_title("Legacy NB permit rows by year issued", loc="left", fontsize=10, color=INK)
a.yaxis.grid(True, color=GRID, lw=0.6)
a.text(2020.3, 17000, "after 2020 NB jobs move\nto DOB NOW; legacy rows\nare mostly renewals", fontsize=7.5, color=INK2)
a.set_ylim(0, 23000)
for ax_ in (a, b):
    ax_.set_xticks(range(2010, 2026, 3))
b.plot(yy.index, yy.nb_jobs_first_permit, color=S1, lw=2, label="NB jobs, first NB permit (both systems)")
b.plot(yy.index, yy.nb_jobs_first_co_in_year, color=S2, lw=2, label="NB jobs, first certificate of occupancy")
b.plot(yy.index, yy.hdb_completed_jobs, color=S3, lw=2, label="Housing Database completions (residential)")
b.plot(yy.index, yy.pluto_lots_yearbuilt, color=S4, lw=2, ls="--", label="PLUTO lots by year built")
b.set_ylim(0, 2800); b.yaxis.grid(True, color=GRID, lw=0.6)
b.set_title("Jobs and completions by year", loc="left", fontsize=10, color=INK)
b.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
a.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=1)
save(fig, "funnel_by_year.png")

# 3. four-year completion by cohort, against DCP's 80-90 percent
h4 = sm["hdb_share_4y_by_cohort"]
fig, ax = plt.subplots(figsize=(7.5, 3.6))
ax.axhspan(0.8, 0.9, color="#d9d8d3", alpha=0.6, lw=0)
ax.text(2009.8, 0.905, "DCP: 'typically 80 to 90 percent ... within four years'", fontsize=7.5, color=INK2)
x = cc[cc.full_4y_window].cohort
s = cc[cc.full_4y_window]
ax.errorbar(x - 0.1, s.share_4y, yerr=[s.share_4y - s.lo_4y, s.hi_4y - s.share_4y], fmt="o", ms=5, color=S1, lw=1.5,
            label="DOB jobs: CO within 4 years of first NB permit")
hx = [int(k) for k in h4 if int(k) <= 2021]
ax.plot([k + 0.1 for k in hx], [h4[str(k)] for k in hx], "s", ms=5, color=S2, label="Housing Database (residential): completed within 4 years")
ax.axvspan(2009.5, 2011.5, color="#f3e2d9", alpha=0.6, lw=0)
ax.text(2009.6, 0.33, "DOB CO table begins\nJuly 2012: cohorts\n2010-11 understated", fontsize=7, color=INK2)
ax.set_ylim(0.2, 1.0); ax.set_xticks(range(2010, 2022))
ax.set_ylabel("share of permitted jobs"); ax.yaxis.grid(True, color=GRID, lw=0.6)
ax.legend(frameon=False, fontsize=7.5, loc="lower right")
ax.set_title("Share of NB jobs completed within four years, by year of first permit", loc="left", fontsize=10.5, color=INK)
save(fig, "four_year_completion.png")
