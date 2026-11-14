"""Step 5: the verified matrix, the breadth score and the figure.

Inputs: matrix_raw.csv (counts of studies per cell from the graph, signs unverified) and
verification.csv (one row per finding read against its PubMed abstract, coded by hand).
A cell is a verified benefit when at least one finding read in it is relevant to the urban
feature and its abstract reports a benefit (whatever the graph record says); a verified harm likewise.
Breadth = domains with a verified benefit minus domains with a verified harm.
"""
import subprocess, sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/derived/all_boats"
FIG = ROOT / "figures/all_boats"
sys.path.insert(0, str(Path(__file__).parent))
from interventions import INTERVENTIONS
DOMS = [("physical_health", "Physical\nhealth"), ("mental_health", "Mental\nhealth"), ("mortality", "Mortality"),
        ("crime_safety", "Crime and\nsafety"), ("education", "Education"), ("income_employment", "Income and\nemployment"),
        ("housing_cost", "Housing\ncost"), ("social_ties", "Social\nties")]
RANK = {"experimental": 3, "longitudinal": 2, "cross-sectional": 1}
LETTER = {"experimental": "E", "longitudinal": "L", "cross-sectional": "C"}
BLUE, VERM, GREY, INK = "#0072B2", "#D55E00", "#D9D9D9", "#222222"


def build():
    raw = pd.read_csv(OUT / "matrix_raw.csv")
    v = pd.read_csv(OUT / "verification.csv", keep_default_na=False)
    rows = []
    for iv in INTERVENTIONS:
        for d, _ in DOMS:
            r = raw[(raw.intervention == iv) & (raw.domain == d)]
            vv = v[(v.intervention == iv) & (v.domain == d)]
            ok = vv[vv.relevant == "yes"]
            ben, harm = ok[ok.verified_effect == "benefit"], ok[ok.verified_effect == "harm"]
            best = lambda x: max(x.design_class, key=lambda k: RANK.get(k, 0)) if len(x) else ""
            status = "empty" if not len(r) and not len(vv) else "mixed" if len(ben) and len(harm) else "benefit" if len(ben) else "harm" if len(harm) else "null" if (ok.verified_effect == "null").any() else "unverified"
            rows.append({"intervention": iv, "label": INTERVENTIONS[iv]["label"], "domain": d, "n_studies_graph": max(int(r.n_studies.iloc[0]) if len(r) else 0, vv.pubmed_id.nunique()),
                         "n_read": len(vv), "status": status, "benefit_design": best(ben), "harm_design": best(harm)})
    m = pd.DataFrame(rows)
    b = m.groupby("intervention").apply(lambda g: pd.Series({
        "benefit_domains": int(g.status.isin(["benefit", "mixed"]).sum()), "harm_domains": int(g.status.isin(["harm", "mixed"]).sum()),
        "experimental_benefit_domains": int(((g.benefit_design == "experimental")).sum()),
        "domains_with_any_study": int((g.n_studies_graph > 0).sum()), "studies_graph": int(g.n_studies_graph.sum())}))
    b["breadth"] = b.benefit_domains - b.harm_domains
    b = b.sort_values(["breadth", "experimental_benefit_domains", "studies_graph"], ascending=False)
    m.to_csv(OUT / "matrix_verified.csv", index=False)
    b.reset_index().to_csv(OUT / "breadth.csv", index=False)
    return m, b


def figure(m, b):
    order = list(b.index)
    fig, ax = plt.subplots(figsize=(12.5, 0.42 * len(order) + 2.2), dpi=200)
    for i, iv in enumerate(order):
        y = len(order) - 1 - i
        for j, (d, _) in enumerate(DOMS):
            c = m[(m.intervention == iv) & (m.domain == d)].iloc[0]
            if c.status == "empty":
                continue
            face = {"benefit": BLUE, "harm": VERM, "mixed": "white", "null": GREY, "unverified": "white"}[c.status]
            ax.add_patch(Rectangle((j + 0.04, y + 0.06), 0.92, 0.88, facecolor=face, edgecolor="#888888" if c.status in ("unverified", "null") else "white",
                                   linewidth=0.8, linestyle="--" if c.status == "unverified" else "-"))
            if c.status == "mixed":
                ax.add_patch(Rectangle((j + 0.04, y + 0.06), 0.46, 0.88, facecolor=BLUE, edgecolor="white", linewidth=0))
                ax.add_patch(Rectangle((j + 0.50, y + 0.06), 0.46, 0.88, facecolor=VERM, edgecolor="white", linewidth=0))
            sign = {"benefit": "+", "harm": "−", "mixed": "±", "null": "0", "unverified": "?"}[c.status]
            des = "/".join(x for x in (LETTER.get(c.benefit_design, ""), LETTER.get(c.harm_design, "")) if x)
            txt = f"{sign} {des}  n={c.n_studies_graph}" if des else f"{sign}  n={c.n_studies_graph}"
            ax.text(j + 0.5, y + 0.5, txt, ha="center", va="center", fontsize=6.6 if c.status == "mixed" else 7.5,
                    color="white" if c.status in ("benefit", "harm", "mixed") else INK, fontweight="bold" if c.status in ("benefit", "harm", "mixed") else "normal")
        ax.text(-0.1, y + 0.5, INTERVENTIONS[iv]["label"], ha="right", va="center", fontsize=8.5, color=INK)
        ax.text(len(DOMS) + 0.45, y + 0.5, f"{int(b.loc[iv, 'breadth']):+d}" if b.loc[iv, "domains_with_any_study"] else "no data", ha="center", va="center", fontsize=9, color=INK,
                fontweight="bold")
    for j, (_, lab) in enumerate(DOMS):
        ax.text(j + 0.5, len(order) + 0.15, lab, ha="center", va="bottom", fontsize=7.8, color=INK)
    ax.text(len(DOMS) + 0.45, len(order) + 0.15, "Breadth", ha="center", va="bottom", fontsize=8.5, color=INK, fontweight="bold")
    for k in range(len(order) + 1):
        ax.plot([0, len(DOMS)], [k, k], color="#EEEEEE", lw=0.5, zorder=0)
    for k in range(len(DOMS) + 1):
        ax.plot([k, k], [0, len(order)], color="#EEEEEE", lw=0.5, zorder=0)
    ax.set_xlim(-3.6, len(DOMS) + 1)
    ax.set_ylim(-1.9, len(order) + 1.9)
    ax.axis("off")
    ax.text(-3.6, len(order) + 1.45, "Urban features by outcome domain: what the graph's findings show after reading the abstracts", fontsize=11, color=INK, fontweight="bold")
    ax.text(-3.6, -0.55, "Blue +: a finding read against its abstract shows a benefit.  Vermillion −: a verified harm.  Split cell: both.  Grey 0: read, no association.\n"
                         "Dashed ?: the graph holds findings but none read was a usable finding on the feature.  Blank: the graph search returned nothing.\n"
                         "Letter: strongest design behind the verified finding (E randomised or quasi-experimental, L longitudinal, C cross-sectional or ecological).\n"
                         "n: studies the variable-name search returned for the cell, signs not verified.  Breadth: verified benefit domains minus verified harm domains.",
            fontsize=7.5, color="#444444", va="top", linespacing=1.5)
    FIG.mkdir(parents=True, exist_ok=True)
    f = FIG / "all_boats_matrix.png"
    fig.savefig(f, bbox_inches="tight", facecolor="white")
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(f)], capture_output=True)
    print("wrote", f.relative_to(ROOT))


if __name__ == "__main__":
    m, b = build()
    print(b.to_string())
    figure(m, b)
