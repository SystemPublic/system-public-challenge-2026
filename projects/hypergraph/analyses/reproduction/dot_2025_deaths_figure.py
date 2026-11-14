"""Figure for repro-dot-2025-deaths: stated DOT numbers against the open-data readings."""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
R = json.loads((ROOT / "data/derived/reproduction/dot_2025_deaths.json").read_text())
OUT = ROOT / "figures/reproduction/dot_2025_deaths.png"
S = R["stated"]
BOROS = ["BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"]
C = {"DOT": "#444444", "r1": "#2a6fbb", "r2": "#e08a2c"}

fig, ax = plt.subplots(1, 3, figsize=(15, 4.8), gridspec_kw={"width_ratios": [1.1, 2.4, 1.1]})

def bars(a, labels, series, title, ylab):
    n = len(series)
    w = 0.8 / n
    for i, (name, vals, col) in enumerate(series):
        xs = [j + (i - (n - 1) / 2) * w for j in range(len(labels))]
        a.bar(xs, vals, w, label=name, color=col)
    a.set_xticks(range(len(labels)))
    a.set_xticklabels(labels, fontsize=8)
    a.set_title(title, fontsize=10)
    a.set_ylabel(ylab)
    a.legend(fontsize=7, frameon=False)
    a.spines[["top", "right"]].set_visible(False)

labels = ["deaths 2024", "deaths 2025", "ped. 2024", "ped. 2025"]
bars(ax[0], labels, [
    ("DOT release", [S["deaths"]["2024"], S["deaths"]["2025"], S["ped"]["2024"], S["ped"]["2025"]], C["DOT"]),
    ("persons table (D1, P1)", [R["D1"]["2024"], R["D1"]["2025"], R["P1"]["2024"], R["P1"]["2025"]], C["r1"]),
    ("crash table (D2, P2)", [R["D2"]["2024"], R["D2"]["2025"], R["P2"]["2024"], R["P2"]["2025"]], C["r2"])],
    "Deaths, calendar year by crash date", "persons killed")

bl = [f"{b.title()[:9]} {y}" for y in ("2024", "2025") for b in BOROS]
bars(ax[1], bl, [
    ("DOT release", [S["boro"][y][b] for y in ("2024", "2025") for b in BOROS], C["DOT"]),
    ("borough field (B1)", [R["B1"][y].get(b, 0) for y in ("2024", "2025") for b in BOROS], C["r1"]),
    ("coordinates (B2)", [R["B2"][y].get(b, 0) for y in ("2024", "2025") for b in BOROS], C["r2"])],
    "Deaths by borough (crash table)", "persons killed")
for t in ax[1].get_xticklabels():
    t.set_rotation(45); t.set_ha("right")

inj = [("I1 crash table,\n1 Jan-15 Dec", "I1"), ("I2 persons table,\n1 Jan-15 Dec", "I2"),
       ("I3 2024 full year", "I3"), ("I4 1 Jan-14 Dec", "I4")]
for i, y in enumerate(("2024", "2025")):
    vals = [100 * (R[k][y] - S["inj"][y]) / S["inj"][y] for _, k in inj]
    ax[2].barh([j + (i - 0.5) * 0.38 for j in range(len(inj))], vals, 0.38, label=y,
               color=C["r1"] if y == "2025" else C["r2"])
ax[2].axvspan(-3, 3, color="#dddddd", zorder=0, label="registered tolerance")
ax[2].axvline(0, color=C["DOT"], lw=1)
ax[2].set_yticks(range(len(inj)))
ax[2].set_yticklabels([a for a, _ in inj], fontsize=8)
ax[2].invert_yaxis()
ax[2].set_xlabel("percent difference from DOT's injury count")
ax[2].set_title("Injuries against DOT\n(51,540 in 2024; 47,557 in 2025)", fontsize=10)
ax[2].legend(fontsize=7, frameon=False)
ax[2].spines[["top", "right"]].set_visible(False)
ax[0].set_xticklabels(["deaths\n2024", "deaths\n2025", "ped.\n2024", "ped.\n2025"], fontsize=8)

v = {s["dataset"]: s["rows_updated_at"] for s in R["sources"]}
fig.suptitle("NYC DOT release of 2 Jan 2026 against NYPD Motor Vehicle Collisions (h9gi-nx95 rows updated "
             f"{v.get('h9gi-nx95')}, f55k-p6yu {v.get('f55k-p6yu')})", fontsize=10)
fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=150)
subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(OUT)],
               check=True, capture_output=True)
print(OUT.relative_to(ROOT))
