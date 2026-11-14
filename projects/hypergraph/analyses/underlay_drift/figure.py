"""Figure for the Underlay drift audit (descriptive). Reads data/derived/underlay_drift/,
writes figures/underlay_drift/underlay_drift.png with an embedded sRGB profile."""
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image, ImageCms  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "underlay_drift"
F = ROOT / "figures" / "underlay_drift"
BLUE, VERM, INK, MUTED, GRID = "#0072B2", "#D55E00", "#222222", "#666666", "#DDDDDD"


def main():
    F.mkdir(parents=True, exist_ok=True)
    bm = pd.read_csv(D / "by_month.csv")
    ex = pd.read_csv(D / "example_zip_share_A.csv", dtype={"zipcode": str}).sort_values("share_A_snapshot")
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                         "xtick.color": MUTED, "ytick.color": MUTED, "font.family": "Helvetica"})
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1.7, 1]})

    x = range(len(bm))
    gone = 100 * bm.snapshot_only / bm.snapshot_total
    chg = 100 * bm.changed / bm.snapshot_total
    a.bar(x, gone, width=0.8, color=VERM, edgecolor="white", linewidth=1, label="in snapshot, gone from live table")
    a.bar(x, chg, bottom=gone, width=0.8, color=BLUE, edgecolor="white", linewidth=1,
          label="in both, a field differs (score, grade, action, violations)")
    for i, r in bm.iterrows():
        if r.live_only >= 20:
            a.annotate(f"{r.month}: {r.live_only} inspections only in live", xy=(i, gone[i] + chg[i] + 0.2),
                       xytext=(i + 0.4, 15.6), ha="right", va="bottom", fontsize=8, color=INK,
                       arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.8})
    ticks = [i for i, m in enumerate(bm.month) if m.endswith(("-01", "-07"))]
    a.set_xticks(ticks, [bm.month[i] for i in ticks])
    a.set_ylabel("share of snapshot inspections in month (%)")
    a.set_title("Snapshot v1.0.0 (12 Jun 2026) against live 43nn-pn8j (rows updated 12 Nov 2026)",
                loc="left", fontsize=9.5, color=INK)
    a.yaxis.grid(True, color=GRID, linewidth=0.6); a.set_axisbelow(True)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.legend(frameon=False, loc="upper left", fontsize=8)
    a.set_ylim(0, 17)

    y = range(len(ex))
    for i, r in enumerate(ex.itertuples()):
        b.plot([100 * r.share_A_snapshot, 100 * r.share_A_live], [i, i], color=GRID, linewidth=2, zorder=1)
    b.scatter(100 * ex.share_A_snapshot, y, s=30, color=MUTED, label="snapshot v1.0.0", zorder=2, edgecolor="white", linewidth=1)
    b.scatter(100 * ex.share_A_live, y, s=30, color=BLUE, label="live, rows updated 12 Nov 2026", zorder=3,
              edgecolor="white", linewidth=1)
    b.set_yticks(list(y), ex.zipcode, fontsize=7)
    for lab in b.get_yticklabels():
        if lab.get_text() == "10018":
            lab.set_color(INK); lab.set_fontweight("bold")
    b.set_xlabel("grade A as % of A/B/C grades, inspections Jan 2025 to May 2026")
    b.set_title("The same figure by ZIP code, computed both ways", loc="left", fontsize=9.5, color=INK)
    b.xaxis.grid(True, color=GRID, linewidth=0.6); b.set_axisbelow(True)
    for s in ("top", "right"):
        b.spines[s].set_visible(False)
    b.legend(frameon=False, loc="lower right", fontsize=8)
    fig.text(0.01, 0.01, "Descriptive. Manhattan; inspections dated 2024-01-01 to 2026-06-11. "
             "Sources: Underlay nyc/restaurant-inspections v1.0.0 (ulv2:07a7f08a...), NYC Open Data 43nn-pn8j.",
             fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    buf = io.BytesIO()
    fig.savefig(buf, dpi=200, format="png")
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    Image.open(buf).convert("RGB").save(F / "underlay_drift.png", icc_profile=srgb, dpi=(200, 200))


if __name__ == "__main__":
    main()
