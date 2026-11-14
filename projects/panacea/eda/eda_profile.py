"""EDA profiler for the System Public Graph v1 dataset (dataverse_files/).

Reads the five CSVs, computes structural + domain stats relevant to
Challenge 4 (heat/ER/tree confirmations, conflicts, bridges), and renders
charts to eda/out/charts/. Run with: python3 -I eda/eda_profile.py
"""

import json
import os
import re
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "dataverse_files")
OUT = os.path.join(BASE, "eda", "out")
CHARTS = os.path.join(OUT, "charts")
os.makedirs(CHARTS, exist_ok=True)

# ---------------------------------------------------------------- style ----
# dataviz skill reference palette (light mode)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"  # slot 1 / sequential base
CAT = {  # categorical slots 1-4 (identity jobs only)
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
}
SEQ = [  # blue sequential ramp 100 -> 700
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
    "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "savefig.dpi": 150,
    "text.color": INK,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": INK2,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.titlecolor": INK,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "axes.titlesize": 13,
    "axes.titleweight": "semibold",
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
})

S = {}  # summary dict -> summary.json


def done(msg):
    print(msg, flush=True)


def style_ax(ax, xgrid=False, ygrid=False):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    if ygrid:
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
    if xgrid:
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)


def save(fig, name):
    path = os.path.join(CHARTS, name)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    done(f"  chart -> {name}")


# ---------------------------------------------------------------- load -----
done("loading concepts...")
concepts = pd.read_csv(
    os.path.join(DATA, "system-public-graph-v1-concepts-1.csv"), dtype=str
)
done(f"  concepts: {len(concepts):,}")

done("loading relationships...")
rel = pd.read_csv(
    os.path.join(DATA, "system-public-graph-v1-relationships.csv"),
    dtype=str,
    usecols=[
        "relationship_id", "num_findings", "num_studies",
        "last_published_date", "last_updated",
        "source_concept.system_id", "source_concept.wikidata_id",
        "source_concept.wikidata_label", "source_concept.wikidata_description",
        "target_concept.system_id", "target_concept.wikidata_id",
        "target_concept.wikidata_label", "target_concept.wikidata_description",
    ],
)
done(f"  relationships: {len(rel):,}")

done("loading associations...")
assoc = pd.read_csv(
    os.path.join(DATA, "system-public-graph-v1-associations.csv"),
    dtype=str,
    usecols=[
        "study_id", "pubmed_id", "statistic_type", "system_statistic_type",
        "statistic_value", "ci_lower", "ci_upper", "p_value",
        "variable_1_concept_id", "variable_2_concept_id",
        "variable_1_name", "variable_2_name",
    ],
)
done(f"  associations: {len(assoc):,}")

done("loading studies...")
studies = pd.read_csv(
    os.path.join(DATA, "system-public-graph-v1-studies-1.csv"), dtype=str
)
done(f"  studies: {len(studies):,}")

done("loading variables...")
variables = pd.read_csv(
    os.path.join(DATA, "system-public-graph-v1-variables-1.csv"), dtype=str
)
done(f"  variables: {len(variables):,}")

# ------------------------------------------------------- structural EDA ----
manifest = json.load(open(os.path.join(DATA, "MANIFEST.json")))
actual = {
    "concepts": len(concepts), "relationships": len(rel),
    "associations": len(assoc), "studies": len(studies),
    "variables": len(variables),
}
S["rows_actual"] = actual
S["rows_manifest"] = {f["filename"]: f["rows"] for f in manifest["files"]}

# concept coverage
S["concepts"] = {
    "total": len(concepts),
    "distinct_wikidata_ids": int(concepts["wikidata_id"].nunique()),
    "dup_wikidata_ids": int(len(concepts) - concepts["wikidata_id"].nunique()),
    "pct_with_description": round(
        100 * concepts["wikidata_description"].notna().mean(), 1),
    "pct_with_aliases": round(
        100 * (~concepts["wikidata_aliases"].fillna("").str.strip().isin(["", "[]"])).mean(), 1),
    "avg_aliases_when_present": round(float(
        concepts["wikidata_aliases"].fillna("[]")
        .map(lambda s: len(re.findall(r'",\s*"|,\s*(?=")', s)) + 1)
        .where(~concepts["wikidata_aliases"].fillna("[]").isin(["", "[]"]), 0).mean()), 2),
}

# relationship strength
rel["num_findings_n"] = pd.to_numeric(rel["num_findings"], errors="coerce")
rel["num_studies_n"] = pd.to_numeric(rel["num_studies"], errors="coerce")
S["relationships"] = {
    "total": len(rel),
    "pct_single_finding": round(100 * (rel["num_findings_n"] == 1).mean(), 1),
    "pct_ge5_findings": round(100 * (rel["num_findings_n"] >= 5).mean(), 1),
    "max_findings": int(rel["num_findings_n"].max()),
    "pct_with_published_date": round(100 * rel["last_published_date"].notna().mean(), 1),
}

# degree: occurrences as source or target
src = rel["source_concept.system_id"]
tgt = rel["target_concept.system_id"]
degree = pd.concat([src, tgt]).value_counts()
label_of = {}
for c, l, d in zip(
    pd.concat([rel["source_concept.system_id"], rel["target_concept.system_id"]]),
    pd.concat([rel["source_concept.wikidata_label"], rel["target_concept.wikidata_label"]]),
    pd.concat([rel["source_concept.wikidata_description"], rel["target_concept.wikidata_description"]]),
):
    if c not in label_of:
        label_of[c] = (l, d)
S["degree"] = {
    "nodes_with_edges": len(degree),
    "max_degree": int(degree.max()),
    "median_degree": float(degree.median()),
    "top20": [
        {"system_id": k, "label": label_of.get(k, ("?",))[0], "degree": int(v)}
        for k, v in degree.head(20).items()
    ],
}

# associations: statistic types + field coverage
assoc["statistic_type_norm"] = assoc["statistic_type"].fillna("").str.strip()
assoc["system_statistic_type_norm"] = assoc["system_statistic_type"].fillna("").str.strip()
stat_counts = (
    assoc.loc[assoc["system_statistic_type_norm"] != "", "system_statistic_type_norm"]
    .value_counts()
)
S["associations"] = {
    "total": len(assoc),
    "pct_with_statistic_value": round(100 * assoc["statistic_value"].notna().mean(), 1),
    "pct_with_ci": round(100 * assoc["ci_lower"].notna().mean(), 1),
    "pct_with_pvalue": round(100 * assoc["p_value"].notna().mean(), 1),
    "pct_with_study": round(100 * assoc["study_id"].notna().mean(), 1),
    "n_system_stat_types": int(stat_counts.nunique()),
    "top_system_stat_types": {k: int(v) for k, v in stat_counts.head(15).items()},
}

# studies
S["studies"] = {
    "total": len(studies),
    "pct_with_doi": round(100 * studies["doi"].notna().mean(), 1),
    "pct_with_pubmed": round(100 * studies["pubmed_id"].notna().mean(), 1),
    "pct_with_population": round(100 * studies["population_string"].notna().mean(), 1),
    "study_type_counts": {
        (k if isinstance(k, str) else "null"): int(v)
        for k, v in studies["study_type"].fillna("null").value_counts().head(12).items()
    },
}

# referential integrity
concept_ids = set(concepts["system_id"])
S["integrity"] = {
    "rel_source_in_concepts_pct": round(100 * src.isin(concept_ids).mean(), 1),
    "rel_target_in_concepts_pct": round(100 * tgt.isin(concept_ids).mean(), 1),
    "assoc_var1_concept_in_concepts_pct": round(
        100 * assoc["variable_1_concept_id"].isin(concept_ids).mean(), 1),
    "assoc_var2_concept_in_concepts_pct": round(
        100 * assoc["variable_2_concept_id"].isin(concept_ids).mean(), 1),
    "assoc_study_in_studies_pct": round(
        100 * assoc["study_id"].isin(set(studies["study_id"])).mean(), 1),
    "variables_concept_in_concepts_pct": round(
        100 * variables["concept_id"].isin(concept_ids).mean(), 1),
}
done("structural stats done")

# ----------------------------------------------------- domain tagging -----
# Matched on LABEL ONLY (descriptions caused noise: e.g. cardiac "vegetations").
DOMAINS = {
    "Heat & temperature": r"\bheat\b|heatwave|heat wave|\btemperature\b|hyperthermia|heatstroke|heat stroke|heat exhaustion|thermoregulation",
    "Air pollution": r"air pollution|air pollutant|air quality|particulate matter|pm2\.5|pm10|\bno2\b|nitrogen dioxide|ozone|\bsmog\b|black carbon|carbon monoxide|sulfur dioxide",
    "Green space": r"\btrees?\b(?! nut)|urban forest|urban greening|\bforestry\b|vegetation cover|green space|greenspace|tree canopy|greenness|\bparks?\b|\bndvi\b|\bforests?\b",
    "Emergency care": r"emergency department|emergency room|emergency visit|emergency admission|hospital admission|hospitalization|hospitalisation|urgent care|ambulance|length of stay",
    "Respiratory": r"\basthma\b|\bcopd\b|chronic obstructive pulmonary|respiratory disease|\blungs?\b|pulmonary\b",
    "Cardiovascular": r"cardiovascular|\bstrokes?\b|myocardial infarction|heart failure|hypertension|ischemic heart disease|cardiac|\bheart\b",
    "Mortality": r"\bmortality\b|\bdeaths?\b",
    "Mental health": r"mental health|depression|anxiety|psychological|psychiatric|\bmood\b",
    "Flooding & storms": r"\bflood|storm surge|precipitation|rainfall|hurricane",
    "Housing & energy": r"\bhousing\b|homeless|air conditioning|energy burden|\butilities?\b|\bheating\b|\bcooling\b",
    "Socioeconomic": r"\bpoverty\b|\bincome\b|socioeconomic|deprivation|inequality|racial|ethnic",
}

# homonym labels excluded from Green space (not urban-environment concepts)
GREEN_EXCLUDE = {"decision tree", "tea tree oil", "tree nut allergy",
                 "barmah forest virus disease"}

concept_text = concepts["wikidata_label"].fillna("").str.lower()

dom_of = {}          # system_id -> set of domains
domain_concept_rows = []
for dom, pat in DOMAINS.items():
    mask = concept_text.str.contains(pat, regex=True, na=False)
    if dom == "Green space":
        mask &= ~concepts["wikidata_label"].fillna("").str.lower().isin(GREEN_EXCLUDE)
    for sid, label, wd in zip(
        concepts.loc[mask, "system_id"],
        concepts.loc[mask, "wikidata_label"],
        concepts.loc[mask, "wikidata_id"],
    ):
        dom_of.setdefault(sid, set()).add(dom)
        domain_concept_rows.append(
            {"domain": dom, "system_id": sid, "wikidata_id": wd, "label": label})
    S.setdefault("domain_concept_counts", {})[dom] = int(mask.sum())
    done(f"  domain '{dom}': {int(mask.sum()):,} concepts")

domain_concepts = pd.DataFrame(domain_concept_rows)
domain_concepts.to_csv(os.path.join(OUT, "domain_concepts.csv"), index=False)

# cross-domain relationship matrix
sid2doms = dom_of
rows_ix = rel.index.to_numpy()
src_doms = [sid2doms.get(s, set()) for s in src]
tgt_doms = [sid2doms.get(t, set()) for t in tgt]
dom_names = list(DOMAINS.keys())
di = {d: i for i, d in enumerate(dom_names)}
M = np.zeros((len(dom_names), len(dom_names)), dtype=int)
bridge_rows = []
for i, sd in enumerate(src_doms):
    td = tgt_doms[i]
    if not sd or not td:
        continue
    for a in sd:
        for b in td:
            M[di[a], di[b]] += 1
            if a != b:
                bridge_rows.append((a, b, src.iloc[i], tgt.iloc[i],
                                    label_of.get(src.iloc[i], ("?",))[0],
                                    label_of.get(tgt.iloc[i], ("?",))[0]))
S["cross_domain_relationships"] = int(sum(
    M[i, j] for i in range(len(dom_names)) for j in range(len(dom_names)) if i != j))

bridges = pd.DataFrame(
    bridge_rows,
    columns=["source_domain", "target_domain", "source_system_id",
             "target_system_id", "source_label", "target_label"],
)
bridge_pairs = (
    bridges.groupby(["source_domain", "target_domain"]).size()
    .sort_values(ascending=False)
)
bridge_pairs.to_csv(os.path.join(OUT, "domain_pair_relationship_counts.csv"))
done("domain tagging done")

# sample evidence: associations bridging challenge-critical domain pairs
DOM_SETS = {
    d: set(domain_concepts.loc[domain_concepts["domain"] == d, "system_id"])
    for d in DOMAINS
}
BRIDGE_PAIRS = [
    ("Heat & temperature", "Emergency care"),
    ("Green space", "Heat & temperature"),
    ("Green space", "Emergency care"),
    ("Green space", "Respiratory"),
    ("Air pollution", "Emergency care"),
    ("Air pollution", "Respiratory"),
    ("Air pollution", "Cardiovascular"),
    ("Heat & temperature", "Cardiovascular"),
    ("Heat & temperature", "Mortality"),
]
S["bridge_pairs"] = {}
for da, db in BRIDGE_PAIRS:
    ia, ib = DOM_SETS[da], DOM_SETS[db]
    sel = assoc[
        (assoc["variable_1_concept_id"].isin(ia) & assoc["variable_2_concept_id"].isin(ib))
        | (assoc["variable_1_concept_id"].isin(ib) & assoc["variable_2_concept_id"].isin(ia))
    ]
    key = f"{da} x {db}"
    S["bridge_pairs"][key] = len(sel)
    slug = key.lower().replace(" & ", "_").replace(" ", "_")
    sel.to_csv(os.path.join(OUT, f"associations_{slug}.csv"), index=False)
    done(f"  bridge {key}: {len(sel):,} associations")

heat_er = assoc[
    (assoc["variable_1_concept_id"].isin(DOM_SETS["Heat & temperature"]) & assoc["variable_2_concept_id"].isin(DOM_SETS["Emergency care"]))
    | (assoc["variable_1_concept_id"].isin(DOM_SETS["Emergency care"]) & assoc["variable_2_concept_id"].isin(DOM_SETS["Heat & temperature"]))
]

# how many studies reference New York City at all (population_string text)?
ny = studies["population_string"].fillna("").str.contains(
    r"new york|\bnyc\b|\bny\b|new york city", case=False, regex=True)
S["studies"]["n_population_mentions_new_york"] = int(ny.sum())
ny_assocs = assoc["study_id"].isin(set(studies.loc[ny, "study_id"]))
S["studies"]["n_associations_from_ny_studies"] = int(ny_assocs.sum())
done(f"NYC-mentioning studies: {int(ny.sum()):,}")

# ------------------------------------------------------------- charts -----
done("rendering charts...")

# 01 dataset overview: rows per table (log scale, one hue)
tables = list(actual.keys())
vals = [actual[t] for t in tables]
fig, ax = plt.subplots(figsize=(7.5, 3.2))
y = np.arange(len(tables))[::-1]
ax.barh(y, vals, height=0.55, color=BLUE)
ax.set_yticks(y, tables)
ax.set_xscale("log")
ax.set_xlim(1e4, 4e6)
for yi, v in zip(y, vals):
    ax.text(v * 1.15, yi, f"{v:,}", va="center", color=INK2, fontsize=9.5)
ax.set_xticks([1e4, 1e5, 1e6])
ax.set_xticklabels(["10k", "100k", "1M"])
style_ax(ax, xgrid=True)
ax.set_title("Rows per table (log scale)")
save(fig, "01_dataset_overview.png")

# 02 relationship strength: findings per relationship
nf = rel["num_findings_n"].dropna()
buckets = [(1, 1, "1"), (2, 2, "2"), (3, 3, "3"), (4, 5, "4-5"),
           (6, 10, "6-10"), (11, 50, "11-50"), (51, 10**9, "50+")]
counts = []
for lo, hi, _ in buckets:
    counts.append(int(((nf >= lo) & (nf <= hi)).sum()))
fig, ax = plt.subplots(figsize=(7.5, 3.4))
x = np.arange(len(buckets))
ax.bar(x, counts, width=0.62, color=BLUE)
ax.set_xticks(x, [b[2] for b in buckets])
ax.set_yscale("log")
ax.set_ylim(1, counts[0] * 8)
for xi, c in enumerate(counts):
    ax.text(xi, c * 1.35, f"{c:,}", ha="center", color=INK2, fontsize=9)
ax.set_ylabel("relationships (log)")
style_ax(ax, ygrid=True)
ax.set_title("Evidence strength: findings per concept pair")
save(fig, "02_relationship_strength.png")

# 03 hub concepts: top 20 by degree
top = degree.head(20)[::-1]
labels = [(label_of.get(k, ("?"))[0] or "?") for k in top.index]
labels = [l if len(l) <= 42 else l[:40] + "…" for l in labels]
fig, ax = plt.subplots(figsize=(8.5, 6.4))
ax.barh(np.arange(len(top)), top.values, height=0.6, color=BLUE)
ax.set_yticks(np.arange(len(top)), labels, fontsize=9)
for yi, v in enumerate(top.values):
    ax.text(v + top.max() * 0.012, yi, f"{v:,}", va="center", color=INK2, fontsize=8.5)
ax.set_xlim(0, top.max() * 1.12)
style_ax(ax, xgrid=True)
ax.set_title("Hub concepts: relationships per concept (top 20)")
save(fig, "03_hub_concepts.png")

# 04 statistic types (canonical), top 12
st = stat_counts.head(12)[::-1]
fig, ax = plt.subplots(figsize=(7.5, 4.6))
ax.barh(np.arange(len(st)), st.values, height=0.6, color=BLUE)
ax.set_yticks(np.arange(len(st)), st.index, fontsize=9)
for yi, v in enumerate(st.values):
    ax.text(v * 1.08 + 200, yi, f"{v:,}", va="center", color=INK2, fontsize=8.5)
ax.set_xscale("log")
ax.set_xlim(5e2, st.max() * 6)
ax.set_xticks([1e3, 1e4, 1e5, 1e6])
ax.set_xticklabels(["1k", "10k", "100k", "1M"])
style_ax(ax, xgrid=True)
ax.set_title("Associations by canonical statistic type (top 12)")
save(fig, "04_statistic_types.png")

# 05 concept completeness
cov = [
    ("Wikidata label", 100.0),
    ("Wikidata description", S["concepts"]["pct_with_description"]),
    ("Wikidata aliases", S["concepts"]["pct_with_aliases"]),
]
fig, ax = plt.subplots(figsize=(7.0, 2.6))
y = np.arange(len(cov))[::-1]
ax.barh(y, [c[1] for c in cov], height=0.5, color=BLUE)
ax.set_yticks(y, [c[0] for c in cov])
ax.set_xlim(0, 112)
ax.set_xticks([0, 25, 50, 75, 100])
for yi, (_, v) in zip(y, cov):
    ax.text(v + 1.5, yi, f"{v:.1f}%", va="center", color=INK2, fontsize=9.5)
style_ax(ax, xgrid=True)
ax.set_title("Concept record completeness (% of 45,721 concepts)")
save(fig, "05_concept_coverage.png")

# 06 domain concept counts
dn = list(DOMAINS.keys())
dv = [S["domain_concept_counts"][d] for d in dn]
order = np.argsort(dv)
dn = [dn[i] for i in order]
dv = [dv[i] for i in order]
fig, ax = plt.subplots(figsize=(8.0, 4.8))
ax.barh(np.arange(len(dn)), dv, height=0.6, color=BLUE)
ax.set_yticks(np.arange(len(dn)), dn, fontsize=9)
for yi, v in enumerate(dv):
    ax.text(v + max(dv) * 0.012, yi, f"{v:,}", va="center", color=INK2, fontsize=8.5)
ax.set_xlim(0, max(dv) * 1.12)
style_ax(ax, xgrid=True)
ax.set_title("Challenge-relevant concepts by domain (keyword match on concept labels)")
save(fig, "06_domain_concepts.png")

# 07 cross-domain relationship heatmap (sequential ramp, log color)
SEQ_CMAP = LinearSegmentedColormap.from_list("spg_blue", SEQ)
Mshow = M.astype(float)
Mshow[Mshow == 0] = np.nan
fig, ax = plt.subplots(figsize=(9.4, 7.6))
im = ax.imshow(np.log10(Mshow), cmap=SEQ_CMAP, aspect="auto")
ax.set_xticks(range(len(dn)), dn, rotation=40, ha="right", fontsize=8.5)
ax.set_yticks(range(len(dn)), dn, fontsize=8.5)
vmax_log = np.log10(np.nanmax(Mshow))
for i in range(len(dn)):
    for j in range(len(dn)):
        v = M[i, j]
        if v == 0:
            continue
        dark = np.log10(v) / vmax_log > 0.55
        ax.text(j, i, f"{v:,}", ha="center", va="center",
                fontsize=7.2, color=("#ffffff" if dark else INK))
cbar = fig.colorbar(im, ax=ax, shrink=0.75, pad=0.02)
cbar.ax.set_ylabel("log10(relationships)", color=MUTED, fontsize=8.5)
cbar.outline.set_visible(False)
ax.set_title("Published relationships crossing domain pairs (diagonal = within domain)")
ax.tick_params(color=AXIS)
for spine in ax.spines.values():
    spine.set_visible(False)
save(fig, "07_domain_crosswalk_heatmap.png")

# 08 study types
stypes = studies["study_type"].fillna("null").value_counts().head(10)[::-1]
fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.barh(np.arange(len(stypes)), stypes.values, height=0.6, color=BLUE)
ax.set_yticks(np.arange(len(stypes)), [s if len(s) <= 44 else s[:42] + "…" for s in stypes.index], fontsize=9)
for yi, v in enumerate(stypes.values):
    ax.text(v + stypes.max() * 0.012, yi, f"{v:,}", va="center", color=INK2, fontsize=8.5)
ax.set_xlim(0, stypes.max() * 1.12)
style_ax(ax, xgrid=True)
ax.set_title("Studies by study_type (top 10)")
save(fig, "08_study_types.png")

# 09 bipartite bridge diagram: focus-domain concepts vs their shared hubs
try:
    focus = ["Heat & temperature", "Air pollution", "Green space", "Emergency care"]
    focus_color = dict(zip(focus, [CAT["blue"], CAT["orange"], CAT["aqua"], CAT["yellow"]]))

    no_self = rel[rel["source_concept.system_id"] != rel["target_concept.system_id"]]
    focus_nodes = set().union(*[DOM_SETS[d] for d in focus])
    edges_focus = no_self[
        no_self["source_concept.system_id"].isin(focus_nodes)
        | no_self["target_concept.system_id"].isin(focus_nodes)
    ]

    # left column: grouped by domain, by global degree within group
    left = []
    for d in focus:
        members = [n for n in degree.index if n in DOM_SETS[d]]
        left.extend(members[:8])
    # right column: hub concepts (outside focus domains) most connected to the left
    L = set(left)
    conn = edges_focus[
        edges_focus["source_concept.system_id"].isin(L)
        | edges_focus["target_concept.system_id"].isin(L)
    ]
    partner_counts = {}
    for s, t in zip(conn["source_concept.system_id"], conn["target_concept.system_id"]):
        a, b = (s, t) if s in L else (t, s)
        if a in L and b not in L and b not in focus_nodes:
            partner_counts[b] = partner_counts.get(b, 0) + 1
    right = [n for n, _ in sorted(partner_counts.items(), key=lambda kv: (-kv[1], kv[0]))][:20]
    R = set(right)

    # aggregate edges between shown columns
    ag = {}
    for s, t, f in zip(edges_focus["source_concept.system_id"],
                       edges_focus["target_concept.system_id"], edges_focus["num_findings_n"]):
        a, b = (s, t) if s in L else (t, s)
        if a in L and b in R:
            ag[(a, b)] = ag.get((a, b), 0) + float(f or 1)

    def col_of(n):
        for d in focus:
            if n in DOM_SETS[d]:
                return focus_color[d]
        return "#b9b8b0"

    def wrap(lbl, width=24):
        words, lines, cur = (lbl or "?").split(), [], ""
        for w in words:
            if len(cur) + len(w) + 1 > width and cur:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        lines.append(cur)
        return "\n".join(lines)

    fig, ax = plt.subplots(figsize=(13.5, 9.8))
    nL, nR = len(left), len(right)
    ysL = np.linspace(0.97, 0.03, nL)
    ysR = np.linspace(0.95, 0.05, nR)
    posL = {n: (0.30, y) for n, y in zip(left, ysL)}
    posR = {n: (0.78, y) for n, y in zip(right, ysR)}

    wmax = max(ag.values())
    for (a, b), f in ag.items():
        (x0, y0), (x1, y1) = posL[a], posR[b]
        ax.plot([x0, x1], [y0, y1], color="#c9c8c0",
                linewidth=0.4 + 1.6 * np.log1p(f) / np.log1p(wmax),
                alpha=0.28 + 0.4 * (f / wmax), zorder=1)

    dmax_log = np.log10(degree.max())
    def sz(n, base, span):
        return base + span * (np.log10(degree.get(n, 1)) / dmax_log)
    ax.scatter(*zip(*posL.values()), s=[sz(n, 70, 330) for n in left],
               c=[col_of(n) for n in left], zorder=3, edgecolors=SURFACE, linewidths=1.2)
    ax.scatter(*zip(*posR.values()), s=[sz(n, 45, 185) for n in right],
               c=[col_of(n) for n in right], zorder=3, edgecolors=SURFACE, linewidths=1.2)
    for n, (x, y) in posL.items():
        ax.text(x - 0.015, y, wrap(label_of.get(n, ("?",))[0]), ha="right", va="center",
                fontsize=7.6, color=INK)
    for n, (x, y) in posR.items():
        ax.text(x + 0.015, y, f"{wrap(label_of.get(n, ('?',))[0])}  ({partner_counts[n]})",
                ha="left", va="center", fontsize=7.6, color=INK)

    # domain group labels on the left
    for d in focus:
        members = [n for n in left if n in DOM_SETS[d]]
        if not members:
            continue
        ys = [posL[m][1] for m in members]
        ax.text(0.035, (max(ys) + min(ys)) / 2 + 0.018, d, fontsize=9,
                color=focus_color[d], fontweight="bold", va="center")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    handles = [plt.Line2D([0], [0], marker="o", linestyle="", markersize=8,
                          color=focus_color[d], label=d) for d in focus]
    handles.append(plt.Line2D([0], [0], marker="o", linestyle="", markersize=8,
                              color="#b9b8b0", label="hub concept (partner count)"))
    ax.legend(handles=handles, loc="lower center", frameon=False, fontsize=9,
              labelcolor=INK2, ncol=5, bbox_to_anchor=(0.5, -0.04))
    ax.set_title(f"Challenge concepts (left) and the hub concepts they co-publish with (right)"
                 f"  - line = published relationship, {len(ag):,} edges shown")
    save(fig, "09_hub_network.png")
except Exception as e:
    done(f"  network chart skipped: {e}")

json.dump(S, open(os.path.join(OUT, "summary.json"), "w"), indent=2)
done("summary.json written")
done("ALL DONE")
