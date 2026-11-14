"""Describe the System Public Graph (Dataverse v2.1) as an object, with numbers.

Reads the DuckDB copy built by build_dataverse.py and writes
  data/derived/graph_audit/describe.json        every number quoted in docs/graph.md
  data/derived/graph_audit/families.csv         topic-family coverage
  data/derived/graph_audit/sign_mixing.csv      per-relationship sign counts (>= 5 signed findings)
  data/derived/graph_audit/self_loops_top.csv   largest concept->same-concept relationships
  data/derived/graph_audit/grounding_samples.csv  variable names and the concepts they are grounded to
  figures/graph_audit/*.png                     figures, sRGB-tagged

No API calls are made.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import duckdb
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = Path.home() / "opt" / "nyc-concordance" / "dataverse" / "graph.duckdb"
OUT = ROOT / "data" / "derived" / "graph_audit"
FIG = ROOT / "figures" / "graph_audit"

BLUE, ORANGE, GREY, INK, INK2, SURF = "#2a78d6", "#eb6834", "#a3a29c", "#0b0b0b", "#52514e", "#fcfcfb"

RATIO = ("odds_ratio", "adjusted_odds_ratio", "hazard_ratio", "adjusted_hazard_ratio",
         "relative_risk_ratio", "incident_rate_ratio", "prevalence_ratio")
SIGNED = ("coefficient", "pearson_r", "spearman_correlation", "mean_difference_unstandardized",
          "mean_difference_standardized", "risk_difference", "elasticity", "t_test")
DIFF = ("mean_difference_unstandardized", "mean_difference_standardized", "risk_difference", "t_test")

# Whole-word regular expressions on lower-cased concept labels. Each family is a
# reading of "urban, environmental and social"; labels are matched, not curated,
# so a family can include stray hits (listed in families_members.csv).
FAMILIES = {
    "heat and climate": r"heat wave|heatwave|heat island|heat stroke|heat-related|extreme heat|ambient temperature|air temperature|climate change|global warming|flood",
    "air quality": r"air pollution|air pollutant|particulates?|pm2\.5|pm10|nitrogen dioxide|ozone|black carbon|smog|traffic-related pollution",
    "noise": r"noise pollution|traffic noise|environmental noise|aircraft noise|road traffic noise",
    "green space and trees": r"green space|greenspace|urban park|park|tree|greenness|urban forest|vegetation",
    "violence and crime": r"violence|gun|firearm|homicide|crime|assault|shooting|police",
    "housing and neighbourhood": r"housing|eviction|homelessness|homeless|vacancy|gentrification|neighbou?rhood|segregation|urban area|urbanization|built environment|residential",
    "transport": r"traffic|commuting|walking|cycling|bicycle|public transport|transit|pedestrian|road traffic|motor vehicle",
    "socioeconomic": r"poverty|income|unemployment|deprivation|socioeconomic|food insecurity|social class|education",
}
# Coarse classes of all concepts from their Wikidata description.
CLASSES = [
    ("gene or protein", r"protein|gene\b|genes\b|enzyme|receptor"),
    ("chemical or drug", r"chemical compound|medication|pharmaceutical|drug|chemical substance|group of"),
    ("disease or symptom", r"disease|disorder|syndrome|symptom|infection|cancer|neoplasm|carcinoma|injury"),
    ("anatomy, cell or organism", r"anatomical|cell|tissue|organ\b|species|strain|genus|family of|bacteri|virus"),
    ("procedure or measurement", r"procedure|surgery|surgical|therapy|treatment|test|measurement|assay|technique|imaging"),
]


# Labels the family patterns catch but which are not urban, environmental or social topics.
EXCLUDE = {"tree nut allergy", "tea tree oil", "decision tree", "tree ring", "chromosome segregation",
           "residential treatment", "weight cycling", "gastrointestinal transit", "sleep deprivation",
           "physical education", "patient education", "health education", "sex education", "prenatal education",
           "special education", "ozone layer", "ozone depletion", "six minute walking test",
           "preferred walking speed", "nordic walking", "forensic firearm examination", "psychosocial deprivation",
           "air pollution, radioactive"}


def wordre(alt: str) -> str:
    return r"(?:^|[^a-z0-9])(?:" + alt + r")(?:[^a-z0-9]|$)"


def tag_png(p: Path) -> None:
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(p)],
                   check=False, capture_output=True)


def style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GREY)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis="x", color="#e6e5e0", linewidth=0.6)
    ax.set_axisbelow(True)


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    p = FIG / name
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    tag_png(p)
    return str(p.relative_to(ROOT))


def main() -> None:
    con = duckdb.connect(str(DB), read_only=True)
    q = lambda s, *a: con.execute(s, *a).fetchall()  # noqa: E731
    qd = lambda s, *a: con.execute(s, *a).df()  # noqa: E731
    R: dict = {"source": "Dataverse doi:10.7910/DVN/7V6JDO v2.1, files verified against MANIFEST.json sha256"}
    figs = []

    # ---- counts
    R["counts"] = {t: q(f"SELECT count(*) FROM {t}")[0][0] for t in
                   ("concepts", "variables", "associations", "studies", "relationships")}
    R["counts"]["distinct_pubmed_ids_in_associations"] = q("SELECT count(DISTINCT pubmed_id) FROM associations")[0][0]
    R["counts"]["sum_num_findings"] = q("SELECT sum(num_findings) FROM relationships")[0][0]
    R["counts"]["findings_per_relationship"] = dict(q(
        "SELECT CASE WHEN num_findings=1 THEN '1' WHEN num_findings<=4 THEN '2-4' WHEN num_findings<=19 THEN '5-19' "
        "ELSE '20+' END b, count(*) FROM relationships GROUP BY 1 ORDER BY 1"))
    R["counts"]["relationships_single_study_share"] = q("SELECT avg((num_studies=1)::INT) FROM relationships")[0][0]
    R["counts"]["associations_per_study_median"] = q(
        "SELECT median(n) FROM (SELECT count(*) n FROM associations GROUP BY study_id)")[0][0]
    R["studies"] = {
        "study_type": dict((str(k), v) for k, v in q("SELECT study_type, count(*) FROM studies GROUP BY 1")),
        "doi_missing_share": q("SELECT avg((doi IS NULL)::INT) FROM studies")[0][0],
        "pubmed_missing_share": q("SELECT avg((pubmed_id IS NULL)::INT) FROM studies")[0][0],
        "population_missing_share": q("SELECT avg((population_string IS NULL)::INT) FROM studies")[0][0],
    }

    # ---- statistic types and precision
    st = qd("""SELECT system_statistic_type t, count(*) n,
                 avg((ci_lower IS NOT NULL AND ci_upper IS NOT NULL)::INT) ci,
                 avg((p_value IS NOT NULL)::INT) p,
                 avg((ci_lower IS NULL AND ci_upper IS NULL AND p_value IS NULL)::INT) neither
               FROM associations GROUP BY 1 ORDER BY 2 DESC""")
    st.to_csv(OUT / "statistic_types.csv", index=False)
    R["statistic_types"] = st.set_index("t")["n"].to_dict()
    R["raw_statistic_type_strings"] = q("SELECT count(DISTINCT statistic_type) FROM associations")[0][0]
    R["precision"] = dict(zip(["with_interval", "with_p", "with_either", "with_neither"], q(
        """SELECT avg((ci_lower IS NOT NULL AND ci_upper IS NOT NULL)::INT), avg((p_value IS NOT NULL)::INT),
                  avg(((ci_lower IS NOT NULL AND ci_upper IS NOT NULL) OR p_value IS NOT NULL)::INT),
                  avg((ci_lower IS NULL AND ci_upper IS NULL AND p_value IS NULL)::INT) FROM associations""")[0]))
    R["precision"]["p_value_equality"] = {str(k): v for k, v in q(
        "SELECT p_value_equality, count(*) FROM associations GROUP BY 1")}
    R["precision"]["ci_level"] = {str(k): v for k, v in q(
        "SELECT round(ci_level, 3), count(*) FROM associations GROUP BY 1 ORDER BY 2 DESC LIMIT 6")}
    fig, ax = plt.subplots(figsize=(7.5, 5))
    style(ax)
    s2 = st.iloc[::-1]
    y = range(len(s2))
    ax.barh(y, s2["n"] * s2["ci"], color=BLUE, height=0.7, label="with interval")
    ax.barh(y, s2["n"] * (1 - s2["ci"]), left=s2["n"] * s2["ci"], color=GREY, height=0.7, label="no interval")
    ax.set_yticks(list(y), s2["t"].str.replace("_", " "))
    ax.set_xlabel("associations in the CSV", color=INK2)
    ax.set_title("Statistic types (system_statistic_type) and the share reporting an interval", color=INK, fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    figs.append(save(fig, "statistic_types.png"))

    # ---- direction: signed associations
    con.execute(f"""CREATE TEMP TABLE dir AS SELECT system_id, variable_1_concept_id||'|'||variable_2_concept_id rid,
        system_statistic_type t,
        CASE WHEN system_statistic_type IN {RATIO} THEN sign(statistic_value - 1)
             WHEN system_statistic_type IN {SIGNED} THEN sign(statistic_value) END d,
        CASE WHEN ci_lower IS NOT NULL AND ci_upper IS NOT NULL THEN
               (CASE WHEN system_statistic_type IN {RATIO} THEN NOT (ci_lower <= 1 AND 1 <= ci_upper)
                     ELSE NOT (ci_lower <= 0 AND 0 <= ci_upper) END)
             WHEN p_value IS NOT NULL THEN p_value < 0.05 AND coalesce(p_value_equality, '=') IN ('=', '<', '<=') END sig,
        CASE WHEN system_statistic_type IN {RATIO} AND statistic_value <= 0 THEN 1 ELSE 0 END bad_ratio,
        CASE WHEN ci_lower IS NOT NULL AND ci_upper IS NOT NULL AND ci_lower <= ci_upper
              AND (statistic_value < ci_lower - 1e-9 OR statistic_value > ci_upper + 1e-9) THEN 1 ELSE 0 END outside,
        CASE WHEN ci_lower > ci_upper THEN 1 ELSE 0 END reversed
        FROM associations""")
    R["direction"] = {
        "share_positive": q("SELECT avg((d=1)::INT) FROM dir")[0][0],
        "share_negative": q("SELECT avg((d=-1)::INT) FROM dir")[0][0],
        "share_zero_or_unsigned": q("SELECT avg((d IS NULL OR d=0)::INT) FROM dir")[0][0],
        "share_significant_of_signed": q("SELECT avg(sig::INT) FROM dir WHERE d IN (1,-1) AND sig IS NOT NULL")[0][0],
        "ratio_nonpositive": q("SELECT sum(bad_ratio) FROM dir")[0][0],
        "estimate_outside_interval": q("SELECT sum(outside) FROM dir")[0][0],
        "interval_reversed": q("SELECT sum(reversed) FROM dir")[0][0],
    }
    rel = R["relationships"] = {}
    rel["reciprocal_pairs"] = q("""SELECT count(*)/2 FROM relationships r JOIN relationships s
        ON s."source_concept.system_id" = r."target_concept.system_id" AND s."target_concept.system_id" = r."source_concept.system_id"
        WHERE r."source_concept.system_id" <> r."target_concept.system_id" """)[0][0]
    rel["self_loops"], rel["self_loop_findings"] = q("""SELECT count(*), sum(num_findings) FROM relationships
        WHERE "source_concept.system_id" = "target_concept.system_id" """)[0]
    sl = qd("""SELECT relationship_id, "source_concept.wikidata_label" label, num_findings, num_studies FROM relationships
        WHERE "source_concept.system_id" = "target_concept.system_id" ORDER BY num_findings DESC LIMIT 25""")
    sl["example"] = [q("SELECT variable_1_name || '  ~  ' || variable_2_name FROM associations WHERE "
                       "variable_1_concept_id||'|'||variable_2_concept_id = ? LIMIT 1", [r])[0][0] for r in sl.relationship_id]
    sl.to_csv(OUT / "self_loops_top.csv", index=False)

    # ---- what the relationship aggregate hides: signs within a relationship
    mix = qd("""SELECT rid, count(*) n_signed, sum((d=1)::INT) pos, sum((d=-1)::INT) neg,
                    sum((d=1 AND sig)::INT) sig_pos, sum((d=-1 AND sig)::INT) sig_neg,
                    sum((t IN {diff})::INT) n_diff
                 FROM dir WHERE d IN (1,-1) GROUP BY rid HAVING count(*) >= 5""".format(diff=DIFF))
    lab = qd("""SELECT relationship_id rid, "source_concept.wikidata_label" src, "target_concept.wikidata_label" tgt,
                   num_findings FROM relationships""")
    mix = mix.merge(lab, on="rid", how="left")
    mix["share_pos"] = mix["pos"] / mix["n_signed"]
    mix.sort_values("n_signed", ascending=False).to_csv(OUT / "sign_mixing.csv", index=False)
    nd = qd(f"""SELECT rid, count(*) n, sum((d=1)::INT) pos, sum((d=1 AND sig)::INT) sp, sum((d=-1 AND sig)::INT) sn
               FROM dir WHERE d IN (1,-1) AND t NOT IN {DIFF} GROUP BY rid HAVING count(*) >= 5""")
    R["sign_mixing"] = {
        "relationships_with_5plus_signed": len(mix),
        "all_one_sign": int(((mix.pos == 0) | (mix.neg == 0)).sum()),
        "mixed": int(((mix.pos > 0) & (mix.neg > 0)).sum()),
        "significant_both_ways": int(((mix.sig_pos > 0) & (mix.sig_neg > 0)).sum()),
        "minority_sign_ge_25pct": int((mix[["pos", "neg"]].min(axis=1) / mix.n_signed >= 0.25).sum()),
        "excluding_differences": {
            "relationships": len(nd),
            "mixed": int(((nd.pos > 0) & (nd.pos < nd.n)).sum()),
            "significant_both_ways": int(((nd.sp > 0) & (nd.sn > 0)).sum()),
        },
    }
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    style(ax)
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.6)
    ax.grid(axis="x", visible=False)
    ax.hist(mix["share_pos"], bins=20, range=(0, 1), color=BLUE, rwidth=0.9)
    ax.set_xlabel("share of signed findings in the relationship that are positive", color=INK2)
    ax.set_ylabel("relationships", color=INK2)
    ax.set_title(f"Sign agreement within {len(mix):,} relationships with five or more signed findings",
                 color=INK, fontsize=11, loc="left")
    figs.append(save(fig, "sign_mixing.png"))

    # ---- coverage of topic families against coarse concept classes
    concepts = qd("SELECT system_id, lower(wikidata_label) label, lower(coalesce(wikidata_description, '')) descr FROM concepts")
    touch = qd("""SELECT cid, count(*) n_assoc, count(DISTINCT study_id) n_studies FROM (
                    SELECT variable_1_concept_id cid, system_id, study_id FROM associations
                    UNION ALL SELECT variable_2_concept_id, system_id, study_id FROM associations) GROUP BY cid""")
    concepts = concepts.merge(touch, left_on="system_id", right_on="cid", how="left").fillna({"n_assoc": 0, "n_studies": 0})
    fam_rows, members = [], []
    con.register("concepts_df", concepts[["system_id", "label"]])
    for fam, alt in FAMILIES.items():
        m = concepts[concepts["label"].str.contains(wordre(alt), regex=True) & ~concepts["label"].isin(EXCLUDE)]
        ids = list(m["system_id"])
        n_assoc, n_st = q("""SELECT count(*), count(DISTINCT study_id) FROM associations
                             WHERE variable_1_concept_id IN (SELECT unnest(?)) OR variable_2_concept_id IN (SELECT unnest(?))""",
                          [ids, ids])[0]
        fam_rows.append({"family": fam, "concepts": len(m), "associations": n_assoc, "studies": n_st})
        members += [{"family": fam, "system_id": r.system_id, "label": r.label, "n_assoc": int(r.n_assoc)}
                    for r in m.sort_values("n_assoc", ascending=False).itertuples()]
    allfam = [m["system_id"] for m in members]
    n_any, st_any = q("""SELECT count(*), count(DISTINCT study_id) FROM associations
                         WHERE variable_1_concept_id IN (SELECT unnest(?)) OR variable_2_concept_id IN (SELECT unnest(?))""",
                      [allfam, allfam])[0]
    fam = pd.DataFrame(fam_rows)
    fam.loc[len(fam)] = {"family": "any urban/social family", "concepts": len(set(allfam)), "associations": n_any, "studies": st_any}
    tot = R["counts"]
    fam["concept_share"] = fam["concepts"] / tot["concepts"]
    fam["association_share"] = fam["associations"] / tot["associations"]
    fam["study_share"] = fam["studies"] / tot["studies"]
    fam.to_csv(OUT / "families.csv", index=False)
    pd.DataFrame(members).to_csv(OUT / "families_members.csv", index=False)
    R["families"] = fam.set_index("family").to_dict(orient="index")

    def klass(d):
        for name, alt in CLASSES:
            if pd.Series([d]).str.contains(alt, regex=True).iloc[0]:
                return name
        return "other or no description"
    concepts["class"] = concepts["descr"].map(klass)
    cls = concepts.groupby("class").agg(concepts=("system_id", "size"), assoc_ends=("n_assoc", "sum"))
    cls["concept_share"] = cls["concepts"] / cls["concepts"].sum()
    cls["assoc_end_share"] = cls["assoc_ends"] / cls["assoc_ends"].sum()
    cls.to_csv(OUT / "concept_classes.csv")
    R["concept_classes"] = cls.to_dict(orient="index")
    top = concepts.sort_values("n_assoc", ascending=False).head(15)
    R["top_concepts_by_association_ends"] = [
        {"label": r.label, "n_assoc": int(r.n_assoc), "share_of_associations": r.n_assoc / tot["associations"]}
        for r in top.itertuples()]
    R["survival_skill"] = {"n_assoc": int(concepts.loc[concepts.label == "survival skill", "n_assoc"].sum()),
                           "examples": [x[0] for x in q("""SELECT DISTINCT v.name FROM variables v JOIN concepts c
                               ON c.system_id = v.concept_id WHERE c.wikidata_label = 'survival skill' LIMIT 8""")],
                           "n_variables": q("""SELECT count(*) FROM variables v JOIN concepts c ON c.system_id = v.concept_id
                               WHERE c.wikidata_label = 'survival skill'""")[0][0]}

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    style(ax)
    f2 = fam.iloc[::-1]
    yy = range(len(f2))
    ax.barh(yy, 100 * f2["association_share"], color=[ORANGE if x.startswith("any") else BLUE for x in f2["family"]], height=0.65)
    for i, r in zip(yy, f2.itertuples()):
        ax.text(100 * r.association_share + 0.05, i, f"{r.associations:,} findings, {r.concepts} concepts",
                va="center", fontsize=8, color=INK2)
    ax.set_yticks(list(yy), f2["family"])
    ax.set_xlabel("share of the 1,999,877 CSV associations touching a family concept (%)", color=INK2)
    ax.set_title("Urban, environmental and social topics in the graph", color=INK, fontsize=11, loc="left")
    ax.set_xlim(0, max(100 * f2["association_share"]) * 1.6)
    figs.append(save(fig, "topic_families.png"))

    # ---- grounding samples: urban-sounding variable names and their concepts
    probes = {"rat": r"rats?|rodents?", "heat": r"heat wave|heatwave|extreme heat", "noise": r"noise",
              "tree": r"trees?|tree canopy", "vacant": r"vacant|vacancy", "traffic": r"traffic",
              "park": r"parks?", "eviction": r"evict\w*", "homeless": r"homeless\w*", "construction": r"construction"}
    gs = []
    for k, alt in probes.items():
        d = qd(f"""SELECT '{k}' probe, c.wikidata_label concept, c.wikidata_description descr, count(*) n_variables,
                       any_value(v.name) example FROM variables v JOIN concepts c ON c.system_id = v.concept_id
                   WHERE regexp_matches(lower(v.name), ?) GROUP BY 1,2,3 ORDER BY 4 DESC LIMIT 12""", [wordre(alt)])
        gs.append(d)
    pd.concat(gs).to_csv(OUT / "grounding_samples.csv", index=False)

    # ---- dates
    yrs = qd("""SELECT year(last_published_date) y, count(*) n FROM relationships WHERE num_studies = 1 GROUP BY 1 ORDER BY 1""")
    sy = qd("""WITH s AS (SELECT DISTINCT a.study_id, r.last_published_date d FROM relationships r
                 JOIN associations a ON a.variable_1_concept_id||'|'||a.variable_2_concept_id = r.relationship_id
                 WHERE r.num_studies = 1)
               SELECT year(d) y, count(DISTINCT study_id) n FROM s GROUP BY 1 ORDER BY 1""")
    dated = int(sy.loc[sy.y.notna(), "n"].sum())
    R["dates"] = {
        "note": "Studies carry no date. A relationship with num_studies = 1 has the date of its one study in "
                "last_published_date, so those studies can be dated.",
        "studies_dated_via_single_study_relationships": dated,
        "studies_dated_share": dated / tot["studies"],
        "study_year_median": float(sy.loc[sy.y.notna()].assign(c=lambda d: d.n.cumsum()).query("c >= @dated/2").y.iloc[0]),
        "study_year_share_2020_on": float(sy.loc[sy.y >= 2020, "n"].sum() / dated),
        "study_year_share_before_2000": float(sy.loc[sy.y < 2000, "n"].sum() / dated),
        "relationships_without_last_published_date": q("SELECT count(*) FROM relationships WHERE last_published_date IS NULL")[0][0],
        "last_updated_distinct_values": q("SELECT count(DISTINCT last_updated) FROM relationships")[0][0],
        "last_updated_modal_value": str(q("SELECT last_updated, count(*) FROM relationships GROUP BY 1 ORDER BY 2 DESC LIMIT 1")[0]),
        "last_updated_by_month": {str(k): v for k, v in q(
            "SELECT strftime(last_updated, '%Y-%m'), count(*) FROM relationships GROUP BY 1 ORDER BY 1")},
        "last_updated_range": [str(x) for x in q("SELECT min(last_updated), max(last_updated) FROM relationships")[0]],
    }
    sy.to_csv(OUT / "study_years.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    style(ax)
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.6)
    ax.grid(axis="x", visible=False)
    s3 = sy[(sy.y >= 1970) & sy.y.notna()]
    ax.bar(s3.y, s3.n, color=BLUE, width=0.8)
    ax.set_xlabel("publication year", color=INK2)
    ax.set_ylabel("studies", color=INK2)
    ax.set_title(f"Publication years of the {dated:,} studies that can be dated ({100*dated/tot['studies']:.0f}% of all)",
                 color=INK, fontsize=11, loc="left")
    figs.append(save(fig, "study_years.png"))

    # ---- API vs CSV figure from api_vs_csv.py output, if present
    av = OUT / "api_vs_csv_rows.parquet"
    if av.exists():
        d = pd.read_parquet(av)
        d["group"] = d["sample"].where(~d["sample"].str.startswith("vacant:"), "vacant-property variables")
        d = d.drop_duplicates(["group", "system_id"])
        g = d.groupby("group").apply(lambda x: pd.Series({
            "n": len(x),
            "absent_grounded": ((~x.in_csv) & x.both_grounded).sum() / len(x),
            "absent_ungrounded": ((~x.in_csv) & ~x.both_grounded).sum() / len(x)}), include_groups=False)
        g = g[g.n >= 20].sort_values("n")
        fig, ax = plt.subplots(figsize=(7.5, 4.8))
        style(ax)
        yy = range(len(g))
        ax.barh(yy, 100 * g.absent_grounded, color=BLUE, height=0.65, label="absent, both variables grounded to concepts")
        ax.barh(yy, 100 * g.absent_ungrounded, left=100 * g.absent_grounded, color=GREY, height=0.65,
                label="absent, one variable has no concept (outside the public-graph scope)")
        ax.set_yticks(list(yy), [f"{i} ({int(n):,})" for i, n in zip(g.index, g.n)])
        ax.set_xlim(0, 100)
        ax.set_xlabel("share of API associations absent from the Dataverse CSV (%)", color=INK2)
        ax.set_title("API associations missing from the CSV, by sample concept", color=INK, fontsize=11, loc="left")
        ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0, -0.13), ncol=1)
        figs.append(save(fig, "api_vs_csv.png"))
    R["figures"] = figs
    (OUT / "describe.json").write_text(json.dumps(R, indent=1, default=str))
    print(json.dumps(R, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
