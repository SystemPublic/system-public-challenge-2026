"""Figure: lifetime NB permit rows per job by first-permit cohort; seen cohorts (2010-2019) against the two replications."""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
F = ROOT / "figures/construction2"; F.mkdir(parents=True, exist_ok=True)
seen = pd.read_csv(ROOT / "data/derived/construction/funnel_by_year.csv").set_index("year").loc[2010:2019, "rows_per_job_lifetime_by_cohort"]
new = pd.read_csv(ROOT / "data/derived/construction2/legacy_rows_per_job_2000_2009.csv").set_index("cohort").mean_rows
dn = json.loads((ROOT / "data/derived/construction2/replication_summary.json").read_text())["dobnow"]["by_cohort"]

fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
ax.plot(seen.index, seen.values, "o-", color="#9a9a9a", label="legacy, cohorts 2010-2019 (seen by the first round)")
ax.plot(new.index, new.values, "o-", color="#1f5f99", label="legacy, cohorts 2000-2009 (replication, registered first)")
ax.plot([int(k) for k in dn], [v["mean"] for v in dn.values()], "s", color="#c0392b", ms=7,
        label="DOB NOW, cohorts 2021-2022, rows to Nov 2026 (replication)")
ax.axhline(5, color="#1f5f99", lw=0.8, ls=":")
ax.text(2010.2, 5.15, "support threshold, legacy pooled mean (5.0)", fontsize=7, color="#1f5f99")
ax.axhline(3, color="#c0392b", lw=0.8, ls=":")
ax.text(2010.2, 3.15, "support threshold, DOB NOW pooled mean (3.0)", fontsize=7, color="#c0392b")
ax.set_ylim(0, 15); ax.set_xlim(1999, 2023)
ax.set_xlabel("year of the job's first new-building permit"); ax.set_ylabel("mean permit rows per job")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(fontsize=7.5, frameon=False, loc="upper left")
ax.set_title("Permit rows per new-building job, by cohort", fontsize=10, loc="left")
fig.text(0.01, 0.01, "Sources: DOB Permit Issuance (ipu4-2q9a); DOB NOW Build Job Filings (w9ak-ipjd) and Approved Permits (rbx6-tga4); fetched 12-13 Nov 2026.", fontsize=6.5, color="#555")
fig.tight_layout(rect=(0, 0.03, 1, 1))
out = F / "rows_per_job_replication.png"
fig.savefig(out)
subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(out)], capture_output=True)
print(out)
