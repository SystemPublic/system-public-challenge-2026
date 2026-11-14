"""Strip plot of the split relationships: one row each, findings as dots by stored sign,
significance and hand code, with the NYC estimate on the two rows that were tested."""
import json, subprocess
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/derived/graph/splits"
COL = {"c": "#0072B2", "a": "#D55E00", "x": "#9A9A9A"}

def main():
    coded = json.loads((OUT / "coded_findings.json").read_text())
    mod = pd.read_csv(OUT / "moderators.csv")
    a = json.loads((OUT / "city_asthma.json").read_text())["primary_cool"]["x"]
    c = json.loads((OUT / "city_covid.json").read_text())["primary"]
    nyc = {"4FaXcuNJRt|EAshH_Ko3h": f"NYC, 3,645 cool-season days: rate ratio {a['irr']:.3f}\n({a['lo']:.3f} to {a['hi']:.3f}) per +5 °C. No cold-day effect.",
           "4FaXcuNJRt|DZBybMvxDI": f"NYC, 291 weeks: growth {c['est']:+.3f} per +1 °C\n({c['lo']:+.3f} to {c['hi']:+.3f}). Neither side supported."}
    order = list(mod.relationship_id)
    fig, ax = plt.subplots(figsize=(14, 9.8))
    step = 0.82
    for i, rid in enumerate(order):
        y = len(order) - 1 - i
        fs = coded[rid]["findings"]
        for sign, d in (("-", -1), ("+", 1)):
            side = sorted([f for f in fs if f["direction"] == sign], key=lambda f: ("cax".index(f["code"]), not f["significant"]))
            for j, f in enumerate(side):
                x = d * (0.9 + j * step)
                ax.scatter(x, y, s=62, marker="o" if f["code"] != "x" else "X", linewidths=1.3,
                           facecolors=COL[f["code"]] if f["significant"] else "white", edgecolors=COL[f["code"]], zorder=3)
        m = mod[mod.relationship_id == rid].iloc[0]
        ax.text(-27.5, y, m.label.replace(" (tested in NYC)", ""), ha="right", va="center", fontsize=10.5,
                fontweight="bold" if rid in nyc else "normal")
        note = f"{m.diagnosis.replace('exposure polarity and three exposures in one', 'exposure polarity, three exposures')}: {int(m.consistent)} agree, {int(m.against)} against, {int(m.excluded)} set aside"
        ax.text(27.5, y + (0.2 if rid in nyc else 0), note, ha="left", va="center", fontsize=9.3, color="#333333")
        if rid in nyc:
            ax.text(27.5, y - 0.26, nyc[rid], ha="left", va="center", fontsize=9, color="#000000", fontweight="bold", linespacing=1.15)
    ax.axvline(0, color="#444444", lw=0.9, zorder=1)
    ax.axhline(1.5, color="#BBBBBB", lw=0.8, ls=(0, (4, 3)))
    ax.set_ylim(-0.9, len(order) - 0.3); ax.set_xlim(-27, 27)
    ax.set_yticks([]); ax.set_xticks([])
    for s in ("top", "right", "left", "bottom"): ax.spines[s].set_visible(False)
    ax.text(-0.9, len(order) - 0.45, "stored with a negative sign  ←", ha="right", va="bottom", fontsize=9.5, color="#444444")
    ax.text(0.9, len(order) - 0.45, "→  stored with a positive sign", ha="left", va="bottom", fontsize=9.5, color="#444444")
    h = [Line2D([], [], marker="o", ls="", ms=8, mfc=COL["c"], mec=COL["c"], label="agrees with the row's question once names are read"),
         Line2D([], [], marker="o", ls="", ms=8, mfc=COL["a"], mec=COL["a"], label="against it"),
         Line2D([], [], marker="X", ls="", ms=8, mfc=COL["x"], mec=COL["x"], label="another construct, or a graph error"),
         Line2D([], [], marker="o", ls="", ms=8, mfc="white", mec="#444444", label="open marker: not significant")]
    ax.legend(handles=h, loc="lower center", bbox_to_anchor=(0.5, -0.075), ncol=4, frameon=False, fontsize=9.3, handletextpad=0.3, columnspacing=1.6)
    fig.suptitle("Split literatures on urban exposures in the System Public Graph: stored sign against what each finding says",
                 x=0.012, ha="left", fontsize=13, fontweight="bold", y=0.985)
    fig.text(0.012, 0.93, "The 15 most balanced relationships (each dot is one finding; every row has equal numbers of positive and negative findings as stored)\nand, below the dashed line, the two relationships tested on New York City daily data.",
             fontsize=9.6, color="#333333")
    fig.subplots_adjust(left=0.235, right=0.625, top=0.905, bottom=0.07)
    f = ROOT / "figures/graph/split_literatures.png"
    fig.savefig(f, dpi=200)
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(f)], capture_output=True)
    print("wrote", f.relative_to(ROOT))

if __name__ == "__main__":
    main()
