#!/usr/bin/env python
"""Consequence table, compositions and figure for the re-timed week (docs/graph_experiments.md).

Reads data/derived/graph/retimed_week/associations.csv (written by retimed_week.py) and
gap_checks.json (retimed_week_concepts.py). Makes no API or city-data request.

1. Assigns each finding a channel from its exposure variable's name (commute time or distance,
   commute mode, telework) and a consequence from its outcome's name. First match wins.
2. Counts findings, studies and signs per consequence and channel -> consequence_counts.csv.
   A sign is the sign of the statistic against its null for the two variables as named; the
   reading of each row after the abstracts were checked is in READ below.
3. Composes a predicted size for three testable consequences with concordance-kit's
   kit/bridge.py (compose, discrimination) -> compositions.json.
4. Draws figures/graph/retimed_week_consequences.png (sRGB profile embedded).
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT.parent / "concordance-kit"))
from kit.bridge import compose, discrimination  # noqa: E402

D = ROOT / "data" / "derived" / "graph" / "retimed_week"
FIG = ROOT / "figures" / "graph"

TELE = (r"telework|telecommut|remote(ly)? work|work(ing|ed|s)? remotely|work(ing|ed|s)? (from|at) home|"
        r"home[- ]?work|home-based (tele)?work|\bWFH\b|hybrid|home office")
CHANNELS = [
    ("telework", TELE),
    ("commute mode", r"active|cycl|bicycl|bik|walk|on foot|commut\w* (mode|physical)|commute physical|public transport|"
                     r"light rail|private|car commut|mode of transport|patterns of travel"),
    ("commute time", r"commut\w* (time|distance|duration)|commute time|time .*commut|long\w*[- ]commut|\(distance\)"),
]
CONSEQ = [
    ("sleep", r"sleep|insomnia|somnolen"),
    ("musculoskeletal pain", r"pain|musculoskel|stiff shoulder"),
    ("alcohol and smoking", r"alcohol|drink|smok"),
    ("respiratory infection", r"covid|sars|influenza|infect"),
    ("road and commuting injury", r"crash|accident|injur|collision"),
    ("loneliness", r"lonel|isolat"),
    ("sitting and inactivity", r"physical (in)?activ|motor activity|sedentary|sitting|step|exercise"),
    ("weight and cardiometabolic", r"body mass|\bbmi\b|obes|overweight|weight|waist|diabet|hypertens|blood pressure|"
                                   r"metabolic|cardiovascular|body fat|mortal"),
    ("mental health", r"depress|anxi|distress|mental|well-?being|stress|burnout"),
    ("fatigue and work functioning", r"fatigue|productiv|efficien|work functioning|absence|presenteeism"),
]

# Reading after the abstracts. direction: sign of the consequence for a worker who replaces a
# commuting day with a day worked at home, as each channel's findings imply. PMIDs were read on PubMed.
READ = {
    "sleep": {"commute time": "-", "telework": "+", "commute mode": None},
    "mental health": {"commute time": "-", "telework": "+", "commute mode": None},
    "sitting and inactivity": {"commute time": "-", "telework": "+", "commute mode": "+"},
    "weight and cardiometabolic": {"commute time": "-", "telework": "+", "commute mode": "+"},
    "musculoskeletal pain": {"commute time": "-", "telework": "+", "commute mode": None},
    "loneliness": {"commute time": None, "telework": "0", "commute mode": None},
    "alcohol and smoking": {"commute time": None, "telework": "+", "commute mode": None},
    "respiratory infection": {"commute time": None, "telework": "-", "commute mode": None},
    "road and commuting injury": {"commute time": None, "telework": None, "commute mode": "-"},
    "fatigue and work functioning": {"commute time": "-", "telework": "+", "commute mode": None},
}
GAPS = ["taxi demand", "restaurant trade", "burglary", "crowd safety"]


def first(pats, text):
    for name, rx in pats:
        if re.search(rx, text, re.I):
            return name
    return None


def counts() -> pd.DataFrame:
    a = pd.read_csv(D / "associations.csv")
    a = a[a.family.isin(["commuting", "telework", "active commuting"])].drop_duplicates("association_id").copy()
    a["channel"] = [first(CHANNELS, str(x)) for x in a.exposure_variable]
    a["consequence"] = [first(CONSEQ, f"{o} | {c}") for o, c in zip(a.outcome_variable.fillna(""), a.outcome_concept.fillna(""))]
    a = a.dropna(subset=["channel", "consequence"])
    a.to_csv(D / "consequence_findings.csv", index=False)
    g = a.groupby(["consequence", "channel"]).agg(
        n_findings=("association_id", "count"), n_studies=("study_id", "nunique"),
        plus=("direction", lambda s: int((s == "+").sum())), minus=("direction", lambda s: int((s == "-").sum())),
        significant=("significant", lambda s: int((s == True).sum())),  # noqa: E712
        pubmed_ids=("pubmed_id", lambda s: sorted({int(x) for x in s.dropna()}))).reset_index()
    g["direction_after_reading"] = [READ.get(c, {}).get(ch) for c, ch in zip(g.consequence, g.channel)]
    g.to_csv(D / "consequence_counts.csv", index=False)
    return g


def compositions() -> dict:
    out = {}
    # A. Obesity by neighbourhood (Community Health Survey, UHF42, 2019 to 2022).
    # Link: public-transport commuters have BMI 1.10 (0.53 to 1.67) lower than car commuters (men, PMID 25139861).
    # One BMI unit is taken as a 0.233 log change in obesity prevalence (normal BMI, SD 6, prevalence 26%).
    # Exponent: commute days lost per commuter in high- against low-dose neighbourhoods (5 points of Monday/Friday
    # deficit = 2 percent of commute days) times the share of adults who commute by transit (0.30).
    k = 0.233
    a = compose([{"name": "obesity ratio, no transit commute vs full transit commute",
                  "estimate": math.exp(k * 1.10), "lo": math.exp(k * 0.53), "hi": math.exp(k * 1.67),
                  "exponent": {"mean": 0.006, "sd": 0.002}}])
    se_a = 0.167 * math.sqrt(2) * math.sqrt(4 / 42)
    out["A obesity by neighbourhood"] = {**a, "discrimination": discrimination(a["composed"]["mean_log"], a["composed"]["sd_log"], se_a),
        "endpoint": "change in log obesity prevalence 2019 to 2022, high- against low-dose half of 42 UHF neighbourhoods",
        "endpoint_se_basis": "median SE of log prevalence per neighbourhood-year 0.167 (EHDP indicator 2063, 2022 intervals); two years; 21 against 21"}
    # B. No recent exercise by neighbourhood. Link: inactivity OR 1.25 (1.03 to 1.51) for commuting more than 5 h/week
    # against 1 to 5 h/week, within person, among those working over 40 h/week (PMID 31836613). Exponent (negative: the
    # change removes commuting): share of adults who cross the threshold, 0.3 long-hours x 0.30 transit commuters x 0.05
    # more workers dropping both days in high-dose areas.
    b = compose([{"name": "inactivity OR, commuting >5 h/week vs 1-5 h/week", "estimate": 1.25, "lo": 1.03, "hi": 1.51,
                  "exponent": {"mean": -0.0045, "sd": 0.002, "allow_negative": True}}])
    se_b = 0.059 * math.sqrt(2) * math.sqrt(4 / 42)
    out["B inactivity by neighbourhood"] = {**b, "discrimination": discrimination(b["composed"]["mean_log"], b["composed"]["sd_log"], se_b),
        "endpoint": "change in log share with no recent exercise 2019 to 2022, high- against low-dose half of 42 UHF neighbourhoods",
        "endpoint_se_basis": "median SE of log prevalence 0.059 (EHDP indicator 2060, 2022 intervals); two years; 21 against 21"}
    # C. Persons injured in crashes, weekdays 06:00-09:59, Monday and Friday against Tuesday to Thursday, 2018-19 against
    # November 2024 to October 2026. Link: morning entries outside the business district on Monday/Friday relative to
    # midweek, now against 2019: (1-0.151)/(1-0.058), interval from the deficit change 9.4 (7.0 to 12.1) points.
    # Exponent: share of morning road exposure that is commuting re-timed like subway commuting (0.2 to 0.6) times the
    # volume elasticity of injuries (0.9, as in bridge-crz-injury-crashes-v2). The graph supplies neither number.
    c = compose([{"name": "Monday/Friday morning commuting relative to midweek, now vs 2019",
                  "estimate": (1 - 0.151) / (1 - 0.058), "lo": 1 - (12.1 / 94.2), "hi": 1 - (7.0 / 94.2),
                  "exponent": {"mean": 0.36, "sd": 0.15}}])
    t = json.loads((D / "design_crash_totals.json").read_text())["rows"]
    pre = sum(int(r["inj"]) for r in t if r["y"] in ("2018", "2019"))
    post = sum(int(r["inj"]) for r in t if r["y"] in ("2024", "2025", "2026"))
    pois = math.sqrt(1 / (0.4 * pre) + 1 / (0.6 * pre) + 1 / (0.4 * post) + 1 / (0.6 * post))
    se_c = 1.3 * pois
    dc = discrimination(c["composed"]["mean_log"], c["composed"]["sd_log"], se_c)
    out["C morning road injuries by day"] = {**c, "discrimination": dc,
        "endpoint": "log ratio of ratios of persons injured, weekdays 06:00-09:59, (Mon+Fri)/(Tue-Thu), Nov 2024-Oct 2026 against 2018-19",
        "endpoint_se_basis": f"pooled weekday totals {pre} and {post} persons injured (design query, no split by day), "
                             f"Poisson SE {pois:.4f} times 1.3 for overdispersion",
        "exponent_needed_for_D_4": 2 * se_c / abs(math.log((1 - 0.151) / (1 - 0.058)))}
    (D / "compositions.json").write_text(json.dumps(out, indent=1))
    return out


def figure(g: pd.DataFrame):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    gaps = json.loads((D / "gap_checks.json").read_text())
    order = ["sleep", "mental health", "sitting and inactivity", "weight and cardiometabolic", "musculoskeletal pain",
             "fatigue and work functioning", "loneliness", "alcohol and smoking", "respiratory infection",
             "road and commuting injury"] + GAPS
    n = len(order)
    fig, ax = plt.subplots(figsize=(13, 13))
    ax.set_xlim(-1.75, 1.75)
    ax.set_ylim(-1.95, 1.75)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(plt.Circle((0, 0), 0.33, fc="#f2f2f2", ec="#222", lw=1.5, zorder=3))
    ax.text(0, 0, "Monday and Friday\ncommuting fell\n5.1% to 13.8% deficit", ha="center", va="center", fontsize=10.5, zorder=4)
    COL = {"commute time": "#1f77b4", "telework": "#d62728", "commute mode": "#2ca02c"}
    SYM = {"+": "more", "-": "less", "0": "no change at 1-2 days", None: ""}
    for i, name in enumerate(order):
        th = math.pi / 2 - 2 * math.pi * (i + 0.5) / n
        x, y = 1.05 * math.cos(th), 1.22 * math.sin(th) * (1.18 if abs(math.sin(th)) > 0.9 else 1.0)
        rows = g[g.consequence == name]
        tot = int(rows.n_findings.sum()) if len(rows) else 0
        gap = name in GAPS
        ax.annotate("", xy=(0.86 * x, 0.86 * y), xytext=(0.36 * math.cos(th), 0.36 * math.sin(th)),
                    arrowprops=dict(arrowstyle="-|>", lw=1.0 + min(tot, 60) / 15, color="#999" if gap else "#333",
                                    ls=(0, (4, 4)) if gap else "-"), zorder=2)
        ha = "left" if x > 0 else "right"
        ax.text(x, y + 0.045, name, ha=ha, va="bottom", fontsize=11.5, fontweight="bold", color="#777" if gap else "#111")
        if gap:
            v = gaps[name]
            note = ("one finding: restaurant openings and burglaries\n(Oakland, PMID 35491751); none on daytime occupancy"
                    if name == "burglary" else
                    f"no finding on this consequence\n({v['variables_matching']} variables matched the words,\nnone about commuters or weekdays)")
            ax.text(x, y + 0.03, note,
                    ha=ha, va="top", fontsize=8.5, color="#777")
            continue
        yy = y + 0.03
        for _, r in rows.sort_values("channel").iterrows():
            d = r.direction_after_reading
            lab = f"{r.channel}: {r.n_findings} findings, {r.n_studies} studies, +{r.plus}/-{r.minus}"
            if d is not None and not (isinstance(d, float) and math.isnan(d)):
                lab += f"  -> {SYM[d]}"
            ax.text(x, yy, lab, ha=ha, va="top", fontsize=8.5, color=COL[r.channel])
            yy -= 0.062
    ax.text(-1.72, -1.93, "Arrows: consequences of replacing a commuting day with a day worked at home, from study-variable searches of the System Public Graph (API v1.0, 12 Nov 2026).\n"
            "Counts are findings, studies and raw sign split (+/-) for each channel of evidence. 'more'/'less' is the direction each channel implies for the re-timed week,\n"
            "after the abstracts were read. Blue and red disagree for sleep, mental health, sitting, weight, pain and fatigue. Dashed: the graph holds no finding.",
            fontsize=8.5, va="bottom", color="#333")
    FIG.mkdir(parents=True, exist_ok=True)
    p = FIG / "retimed_week_consequences.png"
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor="white")
    from PIL import Image, ImageCms
    im = Image.open(p).convert("RGB")
    im.save(p, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes(), dpi=(150, 150))


if __name__ == "__main__":
    g = counts()
    print(g.drop(columns="pubmed_ids").to_string(index=False))
    c = compositions()
    for k, v in c.items():
        print(k, [round(x, 4) for x in v["composed"]["ratio_lo_median_hi"]],
              {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v["discrimination"].items() if a != "advice"},
              v.get("exponent_needed_for_D_4"))
    figure(g)
