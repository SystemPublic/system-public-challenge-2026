"""Figure: the three consequences on the consequence map's form. Change at the centre; each arrow labelled with
what the graph holds (nothing) and what the city data estimate."""
import json, math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data/derived/round2/retimed_consequences"
COL = {"confirmed": "#0072B2", "contested": "#D55E00", "unsettled": "#6e6e6e"}
pct = lambda x: 100 * (math.exp(x) - 1)


def main():
    t = json.load(open(D / "taxi_results.json")); te = json.load(open(D / "taxi_exploratory.json"))
    b = json.load(open(D / "burglary_results.json")); e = json.load(open(D / "ems_results.json"))
    V = {k: json.load(open(ROOT / f"claims/outcomes/{k}.json"))["verdict"] for k in
         ("retimed-taxi-fhv-pickups", "retimed-daytime-burglary", "retimed-ems-presence")}
    s, c = t["primary"]["slope"], t["primary"]["hi_minus_lo"]
    yb, hl = b["primary"]["Y_all"], b["primary"]["hi_minus_lo"]
    C, el = e["primary"]["cbd_minus_rest"], e["elasticity"]
    items = [
        (180, "taxi and for-hire pickups", V["retimed-taxi-fhv-pickups"],
         [("c", f"city: pickups follow entries across {t['primary']['n_zones']} zones,"),
          ("c", f"slope {s['estimate']:.2f} ({s['lo']:.2f} to {s['hi']:.2f});"),
          ("c", f"most-thinned third of zones against least-thinned:"),
          ("c", f"{pct(c['estimate']):+.1f}% ({pct(c['lo']):+.1f} to {pct(c['hi']):+.1f})"),
          ("n", f"not registered: business district {pct(te['Y_cbd']['estimate']):+.1f}% ({pct(te['Y_cbd']['lo']):+.1f} to {pct(te['Y_cbd']['hi']):+.1f})")]),
        (0, "daytime residential burglary", V["retimed-daytime-burglary"],
         [("c", f"city: {pct(yb['estimate']):+.1f}% ({pct(yb['lo']):+.1f} to {pct(yb['hi']):+.1f}) citywide;"),
          ("c", "a fall of 5% to 10% was registered"),
          ("n", "secondary: districts sending more commuters"),
          ("n", f"against fewer, {pct(hl['estimate']):+.1f}% ({pct(hl['lo']):+.1f} to {pct(hl['hi']):+.1f})")]),
        (270, "daytime EMS incidents", V["retimed-ems-presence"],
         [("c", f"city: business district against the rest of the city, {pct(C['estimate']):+.1f}% ({pct(C['lo']):+.1f} to {pct(C['hi']):+.1f});"),
          ("c", f"{el['estimate']:.2f} ({el['lo']:.2f} to {el['hi']:.2f}) of the thinning of subway entries")]),
    ]
    fig, ax = plt.subplots(figsize=(14, 9), dpi=150)
    ax.set_xlim(-8.4, 8.4); ax.set_ylim(-5.9, 4.9); ax.set_aspect("equal"); ax.axis("off")
    cy = 1.6
    ax.add_patch(plt.Circle((0, cy), 1.55, fc="#f1f1f1", ec="#222", lw=1.8))
    ax.text(0, cy, "Monday and Friday\ncommuting fell\n5.1% to 13.8% deficit", ha="center", va="center", fontsize=12.5)
    dy = 0.42
    for ang, title, verdict, lines in items:
        a = math.radians(ang); ux, uy = math.cos(a), math.sin(a)
        x0, y0, x1, y1 = 1.6 * ux, cy + 1.6 * uy, 3.0 * ux, cy + 3.0 * uy
        px, py = -uy * 0.11, ux * 0.11
        ax.annotate("", xy=(x1 + px, y1 + py), xytext=(x0 + px, y0 + py), arrowprops=dict(arrowstyle="-|>", ls=(0, (4, 3)), color="#9a9a9a", lw=1.4))
        ax.annotate("", xy=(x1 - px, y1 - py), xytext=(x0 - px, y0 - py), arrowprops=dict(arrowstyle="-|>", color=COL[verdict], lw=2.8))
        n = len(lines) + 3
        if ang == 270:
            tx, ty, ha = 0, y1 - 0.25, "center"
        else:
            tx, ty, ha = x1 + 0.3 * ux, cy + dy * n / 2, ("left" if ux > 0 else "right")
        ax.text(tx, ty, title, ha=ha, va="top", fontsize=13.5, fontweight="bold", color="#111")
        ax.text(tx, ty - dy * 1.1, "research: none in graph", ha=ha, va="top", fontsize=11, color="#8a8a8a")
        for i, (kind, ln) in enumerate(lines):
            ax.text(tx, ty - dy * (2.1 + i), ln, ha=ha, va="top", fontsize=11, color=COL[verdict] if kind == "c" else "#444")
        ax.text(tx, ty - dy * (2.1 + len(lines)), f"verdict: {verdict}", ha=ha, va="top", fontsize=11, color=COL[verdict], fontweight="bold")
    ax.text(-8.3, -5.85, "Each estimate is the change in the ratio of Monday and Friday to Tuesday-to-Thursday counts, recent period against 2019 or earlier, with a 95% interval.\n"
            "Dashed grey arrow: the System Public Graph holds no finding on this consequence. Solid arrow: the city's estimate,\n"
            "coloured by verdict (blue confirmed, grey unsettled, vermillion contested).\n"
            "Data: TLC trip records (Feb-Mar 2019 and 2026), NYPD complaints (qgea-i56i, 5uac-w243), EMS incidents (76xm-jjuj), MTA hourly entries for the exposure.",
            fontsize=8.8, color="#333", va="bottom")
    out = ROOT / "figures/round2/retimed_consequences.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.png")
    fig.savefig(tmp, facecolor="white", bbox_inches="tight", pad_inches=0.3); plt.close(fig)
    im = Image.open(tmp).convert("RGB")
    im.save(out, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes(), dpi=(150, 150))
    tmp.unlink()
    print(out)


if __name__ == "__main__":
    main()
