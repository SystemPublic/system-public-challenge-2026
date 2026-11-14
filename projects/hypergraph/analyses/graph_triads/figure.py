"""Figure: open triads as a three-column network, and the verification table it is drawn from."""
import csv, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageCms
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "graph" / "triads"
# (exposure, intermediate, outcome, studies A-B, studies B-C, direct findings, class, note)
V = [
 ("air pollution", "preterm birth", "cervical length", 90, 88, 0, "collider", "cervical length predicts preterm birth"),
 ("air pollution", "stroke", "carotid artery stenosis", 69, 131, 0, "collider", "stenosis causes stroke"),
 ("air pollution", "arterial hypertension", "left ventricular hypertrophy", 54, 51, 0, "chain", "composes +; cardiology literature outside the graph"),
 ("walking", "physical activity", "body fat percentage", 79, 85, 1, "chain", "walking is physical activity; composes -"),
 ("air pollution", "dementia", "delirium", 46, 92, 0, "chain", "composes +; community cohorts then inpatients"),
 ("air pollution", "asthma", "immunoglobulin E", 314, 46, 1, "collider", "IgE is a cause or marker of asthma"),
 ("walking", "physical activity", "mental health", 79, 80, 1, "chain", "composes +; signs mixed by coding of poor mental health"),
 ("air pollution", "stroke", "warfarin", 69, 70, 0, "treatment or test", "drug given for stroke prevention"),
 ("air pollution", "stroke", "bleeding", 69, 43, 1, "treatment or test", "complication among stroke patients"),
 ("air pollution", "myocardial infarction", "troponin", 47, 68, 1, "treatment or test", "diagnostic marker"),
 ("urban form", "depression", "mindfulness", 55, 67, 0, "treatment or test", "treatment for depression"),
 ("air pollution", "stroke", "alcohol consumption", 69, 65, 1, "collider", "alcohol is a cause of stroke"),
 ("urban form", "arterial hypertension", "acute kidney injury", 60, 51, 0, "populations differ", "surgical inpatients; exposure concept mixes deprivation, safety, density"),
 ("urban form", "arterial hypertension", "left ventricular hypertrophy", 60, 51, 1, "populations differ", "exposure concept mixes deprivation, safety, density"),
 ("urban form", "arterial hypertension", "arterial blood pressure", 60, 50, 1, "same construct", "hypertension is blood pressure"),
 ("urban form", "asthma", "rhinitis", 63, 48, 0, "same construct", "comorbid atopic conditions"),
 ("urban form", "arterial hypertension", "obstructive sleep apnea", 60, 49, 1, "collider", "apnea causes hypertension"),
 ("urban form", "depression", "migraine", 55, 51, 0, "same construct", "comorbidity in both directions"),
 ("urban form", "asthma", "immunoglobulin E", 63, 46, 1, "collider", "IgE is a cause or marker of asthma"),
 ("air pollution", "preterm birth", "HIV", 90, 37, 1, "collider", "maternal HIV causes preterm birth"),
]
EXTRA = [
 ("heat", "preterm birth", "ADHD", 14, 20, 0, "chain", "composes +; pregnancy cohorts on both links"),
 ("shift work", "metabolic syndrome", "stroke", 32, 76, 0, "chain", "composes +"),
 ("green space", "physical activity", "depression", 18, 39, 1, "chain", "composes -"),
 ("indoor pests", "asthma", "school attendance", 22, 31, 0, "chain", "composes +; too small to detect by neighbourhood"),
 ("cold days", "asthma", "school absence (NYC)", 24, 31, 0, "tested: direction confirmed", "ratio 1.10 (1.05-1.15); asthma path about 8% of it"),
 ("hot days", "asthma", "school absence (NYC)", 24, 31, 0, "tested: unsettled", "ratio 1.01 (0.97-1.05)"),
 ("air pollution", "depression", "violence", 29, 39, 0, "collider", "violence victimisation causes depression"),
 ("flood", "PTSD", "intimate partner violence", 16, 34, 0, "populations differ", "veterans on B-C; 9 of 21 A-B rows are exposure therapy"),
 ("noise", "arterial hypertension", "low birth weight", 34, 11, 0, "collider", "low birth weight causes adult hypertension"),
 ("fast food", "obesity", "sleep duration", 20, 30, 1, "collider", "short sleep causes obesity"),
]
COLS = ["exposure", "intermediate", "outcome", "studies_AB", "studies_BC", "direct_AC_findings", "class", "note"]
with open(OUT / "verification.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["set", "rank"] + COLS)
    for i, r in enumerate(V): w.writerow(["top20", i + 1, *r])
    for r in EXTRA: w.writerow(["candidate", "", *r])

BLUE, AQUA, YEL, GREY, INK, INK2 = "#2a78d6", "#1baf7a", "#eda100", "#b9b8b2", "#0b0b0b", "#52514e"
def style(cls):
    if cls == "chain": return BLUE, "-", 3
    if cls.startswith("tested: direction"): return AQUA, "-", 4
    if cls.startswith("tested: unsettled"): return YEL, "-", 4
    return GREY, (0, (3, 3)), 1
draw = [V[2], V[4], V[6], V[3]] + EXTRA[:6] + [V[0], V[1], V[11], V[5], V[10], V[12]] + EXTRA[6:]
A = list(dict.fromkeys(r[0] for r in draw)); B = list(dict.fromkeys(r[1] for r in draw))
C = [(r[0], r[1], r[2]) for r in draw]
def ys(n, top=0.95, bot=0.03): return [top - i * (top - bot) / max(n - 1, 1) for i in range(n)]
ya = dict(zip(A, ys(len(A), 0.9, 0.08))); yb = dict(zip(B, ys(len(B), 0.92, 0.06))); yc = dict(zip(C, ys(len(C))))
fig, ax = plt.subplots(figsize=(13, 10.5), dpi=200); fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")
XA, XB, XC = 0.13, 0.42, 0.66
for r in sorted(draw, key=lambda r: style(r[6])[2]):
    col, ls, z = style(r[6]); lw = 1.0 if col == GREY else 2.0
    ax.plot([XA, XB], [ya[r[0]], yb[r[1]]], color=col, ls=ls, lw=lw, zorder=z, solid_capstyle="round")
    ax.plot([XB, XC], [yb[r[1]], yc[(r[0], r[1], r[2])]], color=col, ls=ls, lw=lw, zorder=z, solid_capstyle="round")
for k, y in ya.items():
    ax.plot(XA, y, "o", ms=9, color=INK2, mec="#fcfcfb", mew=2, zorder=6); ax.text(XA - 0.012, y, k, ha="right", va="center", fontsize=10.5, color=INK)
for k, y in yb.items():
    ax.plot(XB, y, "o", ms=9, color=INK2, mec="#fcfcfb", mew=2, zorder=6); ax.text(XB, y + 0.014, k, ha="center", va="bottom", fontsize=9.5, color=INK)
for r in draw:
    y = yc[(r[0], r[1], r[2])]; col, ls, z = style(r[6])
    ax.plot(XC, y, "o", ms=10, color=col, mec="#fcfcfb", mew=2, zorder=6)
    ax.text(XC + 0.012, y + 0.006, r[2], ha="left", va="center", fontsize=10.5, color=INK, fontweight="bold" if r[6].startswith("tested") else "normal")
    ax.text(XC + 0.012, y - 0.012, f"{r[6]}: {r[7]}  [{r[3]}/{r[4]} studies, {r[5]} direct]", ha="left", va="center", fontsize=7.6, color=INK2)
for x, t in ((XA, "Exposure a city measures"), (XB, "Intermediate"), (XC + 0.1, "Outcome with 0 or 1 direct finding in the graph")):
    ax.text(x, 0.995, t, ha="center", va="bottom", fontsize=11.5, color=INK, fontweight="bold")
h = [plt.Line2D([], [], color=AQUA, lw=2.5, marker="o", label="tested in NYC data: direction confirmed"),
     plt.Line2D([], [], color=YEL, lw=2.5, marker="o", label="tested in NYC data: unsettled"),
     plt.Line2D([], [], color=BLUE, lw=2.5, marker="o", label="open chain that composes after reading abstracts, not tested"),
     plt.Line2D([], [], color=GREY, lw=1.2, ls=(0, (3, 3)), marker="o", label="open in the graph but does not compose (reason under the label)")]
ax.legend(handles=h, loc="lower left", bbox_to_anchor=(0.0, -0.075), ncol=2, frameon=False, fontsize=9.5)
ax.set_title("Open triads in the System Public Graph: exposure and outcome each linked to an intermediate, never studied together",
             loc="left", fontsize=12.5, color=INK, pad=24)
ax.set_xlim(0, 1.02); ax.set_ylim(-0.01, 1.03); ax.axis("off")
p = ROOT / "figures" / "graph" / "triads_network.png"
fig.savefig(p, bbox_inches="tight", facecolor=fig.get_facecolor()); plt.close(fig)
im = Image.open(p).convert("RGB"); im.save(p, dpi=(200, 200), icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
print("wrote", p.relative_to(ROOT))
