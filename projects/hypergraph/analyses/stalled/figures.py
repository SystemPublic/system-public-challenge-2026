"""Figures for docs/case_334_van_brunt.md and docs/stalled.md.
figures/stalled/lot_334_timeline.png  dated record of block 545 lots 23-27 (events chosen from records.json and ecb_by_bin.json)
figures/stalled/vesting_cohorts.png   36-month no-CO rate by foundation-start window, registered and exploratory matching"""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "figures/stalled"
FIG.mkdir(parents=True, exist_ok=True)
D = ROOT / "data/derived/stalled"
C = {"Ownership and lending (ACRIS)": "#1f5f99", "DOB filings and permits": "#b35806",
     "DOB enforcement": "#6a3d9a", "Complaints (DOB, 311)": "#2e7d32"}
LANES = list(C)


def tag(p):
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(p)], capture_output=True)


# ---- timeline: events transcribed from the fetched records (dates as recorded) ----
E = [
    ("2014-03-24", 0, "Red Hook Anchor Realty buys lots 24-25"),
    ("2016-01-15", 0, "buys lots 26-27, $1.13M"),
    ("2016-03-23", 1, "Alt-1: enlarge 1-storey shop to 4-storey mixed use, 8 units"),
    ("2016-11-16", 1, "Alt-1 plans approved"),
    ("2018-03-08", 0, "$3.85M mortgage, ConnectOne Bank"),
    ("2018-09-21", 1, "foundation and alteration permits issued"),
    ("2019-01-22", 2, "Class 1: public not safeguarded, no work in progress"),
    ("2020-03-25", 2, "inactive site, fence and shed permits expired"),
    ("2020-06-19", 1, "NB job filed (4 storeys, 8 units)"),
    ("2020-06-24", 0, "ConnectOne mortgage satisfied"),
    ("2020-08-05", 2, "stop-work order: superintendent withdrew"),
    ("2020-09-22", 1, "NB plans approved; NB permit never issued"),
    ("2021-02-25", 2, "excavation and foundation concrete in progress"),
    ("2021-05-17", 2, "dewatering without permit; order to backfill to grade"),
    ("2022-06-15", 1, "421-a vesting deadline"),
    ("2022-11-22", 1, "last renewal of Alt-1 permit (to Jul 2023)"),
    ("2023-11-13", 2, "fence permit expired"),
    ("2024-02-05", 2, "barriers block walkway at a closed site"),
    ("2024-06-28", 0, "sold to NY 336 Van Brunt LLC, $2.80M; no mortgage recorded"),
    ("2024-10-28", 2, "'foundation phase', no activity, gates padlocked"),
    ("2024-12-03", 1, "new construction-fence permit"),
    ("2025-09-12", 0, "same buyer adds lot 23 (330 Van Brunt), $1.06M"),
    ("2026-04-24", 2, "fence permit expired, fence in disrepair"),
    ("2026-09-23", 2, "stop-work order: contractor withdrew"),
    ("2026-10-12", 1, "demolition filed for 330 Van Brunt buildings"),
]
ev = pd.DataFrame(E, columns=["date", "lane", "text"])
ev["date"] = pd.to_datetime(ev.date)
cmp = pd.read_csv if False else None
c311 = json.loads((D / "lot_334/records.json").read_text())
compl = []
for lot in ("23", "24", "25", "26", "27"):
    compl += [pd.to_datetime(c["created_date"]) for c in c311[lot]["complaints_311"]]
    compl += [pd.to_datetime(c["date_entered"], format="%m/%d/%Y") for c in c311[lot]["dob_complaints"]]
compl = pd.Series(compl)
compl = compl[compl >= "2014-01-01"]

fig, ax = plt.subplots(figsize=(11, 8.6))
ev = ev.sort_values("date").reset_index(drop=True)
n = len(ev)
for i, e in ev.iterrows():
    y = n - i
    col = C[LANES[e.lane]] if "deadline" not in e.text else "#777"
    ax.plot(e.date, y, "o", ms=7, color=col, mec="white", mew=1.2, zorder=3)
    ax.text(e.date + pd.Timedelta(days=60), y, f"{e.date:%b %Y}  {e.text}", va="center", fontsize=8, color="#222")
yc = 0
for d in compl:
    ax.plot(d, yc, "|", ms=10, color=C[LANES[3]], alpha=0.7)
ax.text(pd.Timestamp("2014-01-01"), -0.9, f"each tick: one DOB or 311 complaint on the five lots ({len(compl)} since 2014)", fontsize=7.5, color="#444")
ax.axvspan(pd.Timestamp("2021-12-15"), pd.Timestamp("2022-06-15"), color="#ddd", zorder=0)
ax.axvspan(pd.Timestamp("2022-11-22"), pd.Timestamp("2024-06-28"), color="#f2e6d9", zorder=0)
ax.text(pd.Timestamp("2022-12-15"), n + 0.9, "no valid work permit\nafter Jul 2023", fontsize=7.5, color="#555", va="bottom")
ax.text(pd.Timestamp("2021-12-20"), n + 0.9, "421-a\nrush", fontsize=7.5, color="#555", va="bottom")
ax.set_ylim(-1.5, n + 2.4)
ax.set_xlim(pd.Timestamp("2013-10-01"), pd.Timestamp("2031-06-01"))
ax.set_yticks([])
for s in ("left", "right", "top"):
    ax.spines[s].set_visible(False)
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(axis="x", colors="#444", labelsize=8)
hs = [plt.Line2D([], [], marker="o", ls="", color=v, label=k) for k, v in C.items()]
ax.legend(handles=hs, loc="upper left", fontsize=8, frameon=False, ncol=4, bbox_to_anchor=(0, 1.04))
ax.set_title("Van Brunt and King Streets, Red Hook (Brooklyn block 545, lots 23-27): the record, 2014-2026", fontsize=10.5, loc="left", pad=22)
fig.text(0.01, 0.005, "Sources: ACRIS (bnx9-e6tj, 8h5j-fqxa, 636b-3b5g), DOB BIS jobs and permits (ic3t-wcy2, ipu4-2q9a), DOB NOW (w9ak-ipjd, rbx6-tga4), "
         "DOB and ECB violations (3h2n-5cm9, 6bgk-3dad), DOB complaints\n(eabe-havv), 311 (erm2-nwe9); fetched 13 Nov 2026. Grey marker: a statutory date, not a record of the lots.", fontsize=6.5, color="#444")
fig.tight_layout(rect=(0, 0.035, 1, 1))
p = FIG / "lot_334_timeline.png"
fig.savefig(p, dpi=170)
tag(p)
plt.close(fig)

# ---- vesting cohorts ----
reg = json.loads((D / "vesting_result.json").read_text())["rates"]
exp = json.loads((D / "vesting_exploratory.json").read_text())["horizon_1096"]
yrs = sorted(int(k) for k in reg)
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(yrs, [reg[str(y)]["rate"] for y in yrs], "-o", color="#b35806", lw=2, ms=7, label="registered: CO matched by lot (BBL)")
ax.plot(yrs, [exp[str(y)]["rate"] for y in yrs], "-o", color="#1f5f99", lw=2, ms=7, label="exploratory: CO matched by job number or lot")
for y in yrs:
    ax.text(y, 0.04, f"n={reg[str(y)]['n']}", ha="center", fontsize=7.5, color="#444")
ax.axvspan(2021.6, 2022.4, color="#ddd", zorder=0)
ax.text(2022, 0.74, "six months before the\n421-a deadline", ha="center", fontsize=7.5, color="#444")
ax.set_ylim(0, 0.8)
ax.set_ylabel("share with no CO within 36 months", fontsize=8.5)
ax.set_xlabel("foundation starts, 15 Dec of the previous year to 14 Jun", fontsize=8.5)
ax.grid(axis="y", color="#eee")
for s in ("right", "top"):
    ax.spines[s].set_visible(False)
ax.legend(fontsize=8, frameon=False, loc="lower left", bbox_to_anchor=(0.0, 0.1))
ax.set_title("New-building jobs that had not reached a certificate of occupancy 36 months after their first foundation permit",
             fontsize=9, loc="left")
fig.text(0.01, 0.005, "Sources: ipu4-2q9a, rbx6-tga4, w9ak-ipjd, bs8b-p36w, pkdm-hqz6 (NYC Open Data, Nov 2026). Claim stalled-421a-vesting-footings.",
         fontsize=6.5, color="#444")
fig.tight_layout(rect=(0, 0.03, 1, 1))
p = FIG / "vesting_cohorts.png"
fig.savefig(p, dpi=170)
tag(p)
