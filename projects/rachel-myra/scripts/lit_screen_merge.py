"""Merge prefilter + LLM screening + LLM extraction; verbatim-check numbers; write the funnel report.

Spec §8.4 steps 4-7. Screening and extraction were done by an LLM (Claude subagents) against the fixed
rules in data/raw/literature/screening_rules.md. No human screening or review.

Inputs:  data/processed/literature_records.csv, data/raw/literature/screen_prefilter.csv,
         data/raw/literature/screen_results/{chunk,extract}_NNN.csv, data/processed/citation_chase.csv,
         data/Drug heat risk master list.csv
Outputs: data/processed/literature_screen.csv       (every record, one decision each)
         data/processed/literature_extraction.csv   (included records; numbers verbatim-checked)
         data/raw/literature/screening_report.md    (funnel)

Verbatim rule: effect_text must be a substring of the full abstract, and effect_value / ci_lower / ci_upper
must each appear in effect_text (digits/decimal exactly, after mapping "·"->"." and odd spaces->" ").
If any check fails, the numbers are blanked (never edited) and number_check = "failed_blanked".

Usage: ~/.local/bin/uv run --with pandas python -I scripts/lit_screen_merge.py
"""
import glob, os, re
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIT = os.path.join(ROOT, "data", "raw", "literature")
PROC = os.path.join(ROOT, "data", "processed")
TIER = {"rct": "1 RCT / meta-analysis", "meta_analysis": "1 RCT / meta-analysis",
        "systematic_review": "1 RCT / meta-analysis", "cohort": "2 Population study",
        "case_control": "2 Population study", "case_crossover": "2 Population study",
        "time_series": "2 Population study", "cross_sectional": "2 Population study",
        "pharmacovigilance": "2 Population study", "human_lab_study": "3 Small clinical study",
        "case_series": "4 Case series", "case_report": "5 Case report", "lab_bench": "6 Lab / bench",
        "review": "8 Narrative / mechanism only", "other": "8 Narrative / mechanism only"}
CLASSES = ["sglt2", "epinephrine", "topiramate_zonisamide", "opioids_fentanyl", "insulin", "loop_diuretics",
           "lithium", "thiazides", "metformin", "adhd_stimulants", "ace_arb", "beta_blockers",
           "anticholinergics", "ssris", "antipsychotics", "multiple", "storage_other"]


def rd(p):
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def norm(t):
    t = t.replace("·", ".").replace("−", "-").replace("–", "-")
    return re.sub(r"[    - ]", " ", t)


def num_in(v, text):
    v = norm(v).strip()
    if not v:
        return True
    return re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d])", norm(text)) is not None


def main():
    rec = rd(os.path.join(PROC, "literature_records.csv"))
    pre = rd(os.path.join(LIT, "screen_prefilter.csv"))
    chunks = pd.concat([rd(f) for f in sorted(glob.glob(os.path.join(LIT, "screen_results", "chunk_*.csv")))])
    ext = pd.concat([rd(f).assign(chunk=os.path.basename(f)[8:11])
                     for f in sorted(glob.glob(os.path.join(LIT, "screen_results", "extract_*.csv")))])
    to_screen = set(pre.loc[pre.prefilter_decision == "screen", "record_id"])
    assert set(chunks.record_id) == to_screen and chunks.record_id.is_unique, "screen results incomplete"

    # ---- master list IDs (novelty flag)
    ml = open(os.path.join(ROOT, "data", "Drug heat risk master list.csv"), encoding="utf-8-sig").read()
    ml_pmid = set(re.findall(r"PMID:?\s*(\d{5,9})", ml))
    ml_doi = {d.lower().rstrip(".);,") for d in re.findall(r"10\.\d{4,9}/[^\s,;\"]+", ml)}
    ml_pmc = set(re.findall(r"PMC\d+", ml))

    meta = rec[["record_id", "pmid", "pmcid", "doi", "year", "journal", "title", "abstract"]].copy()
    meta["pmid"] = meta.pmid.str.replace(r"\.0$", "", regex=True)

    def in_master(r):
        return (r.pmid and r.pmid in ml_pmid) or (r.doi and r.doi.lower() in ml_doi) or (r.pmcid and r.pmcid in ml_pmc)

    meta["in_master_list"] = ["yes" if in_master(r) else "no" for r in meta.itertuples()]

    # ---- literature_screen.csv
    s = pre.merge(chunks, on="record_id", how="left").merge(meta.drop(columns="abstract"), on="record_id")
    s["stage"] = s.prefilter_decision.map({"exclude": "prefilter_rule", "screen": "llm"})
    s["decision"] = s.decision.where(s.stage == "llm", "exclude")
    s["reason"] = s.reason.where(s.stage == "llm", s.prefilter_rule)
    s["drug_class"] = s.drug_class.where(s.stage == "llm", "")
    s["uncertain"] = s.reason.str.startswith("uncertain").map({True: "yes", False: "no"})
    s["evidence_tier"] = s.design.map(TIER).fillna("").where(s.decision == "include", "")
    s["screened_by"] = s.stage.map({"prefilter_rule": "rule (scripts/lit_prefilter.py)", "llm": "LLM (Claude), no human review"})
    cols = ["record_id", "pmid", "pmcid", "doi", "year", "journal", "title", "group", "query_classes", "stage",
            "decision", "reason", "uncertain", "drug_class", "outcome_type", "design", "evidence_tier",
            "in_master_list", "screened_by"]
    s = s[cols].sort_values(["decision", "record_id"], ascending=[False, True])
    s.to_csv(os.path.join(PROC, "literature_screen.csv"), index=False)

    # ---- literature_extraction.csv with verbatim check against the FULL abstract
    inc = set(s.loc[s.decision == "include", "record_id"])
    ext = ext[ext.record_id.isin(inc)].merge(meta, on="record_id", how="left")
    checks = []
    for i, r in ext.iterrows():
        nums = [r.effect_value, r.ci_lower, r.ci_upper]
        if not any(n.strip() for n in nums) and not r.effect_text.strip():
            checks.append("no_number")
            continue
        ok = norm(r.effect_text).strip() in norm(r.abstract) if r.effect_text.strip() else False
        ok = ok and all(num_in(n, r.effect_text) for n in nums) and all(num_in(n, r.abstract) for n in nums)
        if ok:
            checks.append("verbatim_ok" if any(n.strip() for n in nums) else "text_only_ok")
        else:
            checks.append("failed_blanked")
            for c in ["effect_value", "ci_lower", "ci_upper"]:
                ext.at[i, c] = ""
    ext["number_check"] = checks
    ext["evidence_tier"] = ext.design.map(TIER).fillna("")
    scr = s.set_index("record_id")
    ext["screen_reason"] = ext.record_id.map(scr.reason)
    ext["uncertain_include"] = ext.record_id.map(scr.uncertain)
    ext["extracted_by"] = "LLM (Claude) from abstract, numbers verbatim-checked by script; no human review"
    ecols = ["record_id", "pmid", "doi", "year", "title", "drug", "drug_class", "outcome", "population", "design",
             "evidence_tier", "heat_definition", "direction", "effect_type", "effect_value", "ci_lower", "ci_upper",
             "effect_text", "number_check", "notes", "uncertain_include", "screen_reason", "in_master_list", "extracted_by"]
    ext = ext[ecols]
    ext.to_csv(os.path.join(PROC, "literature_extraction.csv"), index=False)

    # ---- funnel report
    chase = rd(os.path.join(PROC, "citation_chase.csv"))
    ch_ids = set(chase.pmid[chase.pmid != ""]) | {d.lower() for d in chase.doi if d}
    rec_ids = set(meta.pmid[meta.pmid != ""]) | {d.lower() for d in meta.doi if d}
    chase = chase.assign(_key=[(r.doi.lower() or ("PMID:" + r.pmid if r.pmid else "") or r.openalex_id or r.title.lower())
                               for r in chase.itertuples()])
    chase_works = chase.drop_duplicates(subset=["_key"])
    chase_new = sum(1 for r in chase_works.itertuples() if not ((r.pmid and r.pmid in rec_ids) or (r.doi and r.doi.lower() in rec_ids)))

    def cls_of(row):
        return row.drug_class if row.stage == "llm" else row.query_classes.split("|")[0] if row.query_classes else "storage"

    # Funnel by query class (records can belong to several query classes; counted once per class)
    rows = []
    s2 = s.copy()
    s2["qc"] = s2.query_classes.replace("", "storage").str.split("|")
    s2 = s2.explode("qc")
    for qc, g in s2.groupby("qc"):
        rows.append(dict(query_class=qc, records=len(g), prefilter_excluded=(g.stage == "prefilter_rule").sum(),
                         llm_screened=(g.stage == "llm").sum(), included=(g.decision == "include").sum(),
                         uncertain=((g.decision == "include") & (g.uncertain == "yes")).sum()))
    fq = pd.DataFrame(rows).sort_values("records", ascending=False)

    incd = s[s.decision == "include"]
    byc = []
    for c in CLASSES:
        g = incd[incd.drug_class == c]
        e = ext[ext.drug_class == c]
        byc.append(dict(drug_class=c, included_records=len(g), uncertain=(g.uncertain == "yes").sum(),
                        new_vs_master=(g.in_master_list == "no").sum(), extraction_rows=len(e),
                        rows_with_verbatim_number=(e.number_check == "verbatim_ok").sum(),
                        tier1=(g.evidence_tier.str[0] == "1").sum(), tier2=(g.evidence_tier.str[0] == "2").sum(),
                        tier3=(g.evidence_tier.str[0] == "3").sum(), tier4_5=g.evidence_tier.str[0].isin(["4", "5"]).sum(),
                        tier6=(g.evidence_tier.str[0] == "6").sum(), tier8=(g.evidence_tier.str[0] == "8").sum()))
    fc = pd.DataFrame(byc)
    # extraction rows by class (multi-drug records split per drug)
    pre_counts = pre.prefilter_rule.replace("", "to LLM screening").value_counts()
    llm_ex = s[(s.stage == "llm") & (s.decision == "exclude")].reason.str.extract(r"^(E\d)")[0].value_counts()

    def md(df):
        h = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
        return h + "".join("| " + " | ".join(str(v) for v in r) + " |\n" for r in df.itertuples(index=False))

    # notable new population-level / tier 1-2 includes not in master list
    new_strong = incd[(incd.in_master_list == "no") & incd.evidence_tier.str[0].isin(["1", "2"])]
    new_tbl = new_strong[["record_id", "year", "drug_class", "design", "title"]].copy()
    new_tbl["title"] = new_tbl.title.str.slice(0, 110).str.replace("|", "/", regex=False)
    nc = ext.number_check.value_counts()

    # recall check: master-list papers that are in the search set
    mls = s[s.in_master_list == "yes"][["record_id", "stage", "decision", "reason", "title"]].copy()
    mls["title"] = mls.title.str.slice(0, 90).str.replace("|", "/", regex=False)
    mls["reason"] = mls.reason.str.slice(0, 70).str.replace("|", "/", regex=False)
    mls_ex = mls[mls.decision == "exclude"]

    # no-abstract records whose TITLE names one of the drugs and a heat-illness/heat-storage term
    import importlib.util
    spec = importlib.util.spec_from_file_location("pf", os.path.join(ROOT, "scripts", "lit_prefilter.py"))
    pf = importlib.util.module_from_spec(spec); spec.loader.exec_module(pf)
    strong = re.compile(r"heat|hot\b|hyperthermi|hidrosis|summer|sun|temperature|thermal|warm", re.I)
    p1 = s[(s.reason == "P1 no abstract")]
    noise = re.compile(r"\b(rats?|mice|mouse|rabbits?|pigs?|dogs?|cats?|animals?)\b|" + pf.NMS_TITLE + "|" + pf.MATERIALS
                       + r"|fluoride|thermoluminescen|tumou?r|cancer|retraction", re.I)
    cand = p1[[bool(strong.search(t)) and not noise.search(t)
               and (any(v.search(t) for v in pf.DRX.values()) or bool(pf.SORX.search(t))) for t in p1.title]][["record_id", "year", "title"]].copy()
    cand["title"] = cand.title.str.slice(0, 110).str.replace("|", "/", regex=False)

    n = len(s)
    txt = f"""# Literature screening and extraction: funnel report

Spec §8.4 steps 4–7. Generated by `scripts/lit_screen_merge.py` on the 2026-11-14 overnight run.

**Screening and extraction are fully automated. A rule-based prefilter removed obvious exclusions; an LLM (Claude, run as parallel subagents, each given the same fixed brief `screen_instructions.md`) screened every remaining title/abstract against the fixed rules in `screening_rules.md` and extracted data from included abstracts. No human screened, extracted or reviewed anything.** Numbers in the extraction were checked by script to appear verbatim in the abstract; any that failed were blanked, not corrected.

## Funnel
| Step | Records |
|---|---|
| Unique records from search (`literature_records.csv`) | {n} |
| Excluded by rule-based prefilter | {(s.stage == 'prefilter_rule').sum()} |
| Screened by LLM (title + abstract) | {(s.stage == 'llm').sum()} |
| Excluded by LLM | {((s.stage == 'llm') & (s.decision == 'exclude')).sum()} |
| **Included** | **{len(incd)}** (of which {(incd.uncertain == 'yes').sum()} flagged `uncertain:` = included on doubt) |
| Extraction rows (one per included record × drug) | {len(ext)} |
| Extraction rows with an effect number verbatim in the abstract | {nc.get('verbatim_ok', 0)} |
| Extraction rows where a number failed the verbatim check (blanked) | {nc.get('failed_blanked', 0)} |
| Included records new relative to the master list (no PMID/DOI/PMCID match) | {(incd.in_master_list == 'no').sum()} |

Included records by group: drug×heat query {(incd.group == 'drug_x_heat').sum()}, storage query {(incd.group == 'storage').sum()}.

### Prefilter exclusions (rules P1–P6, `scripts/lit_prefilter.py`)
{md(pre_counts.rename_axis('rule').reset_index(name='records'))}
### LLM exclusions by rule code
{md(llm_ex.rename_axis('rule').reset_index(name='records'))}
## Funnel by search query (a record found by several queries counts under each)
{md(fq)}
## Included records by drug class (LLM-assigned) and §9 evidence tier
`multiple` = record covers several of the 15 classes (extraction splits these per drug where results are separate). `storage_other` = inhalers / glucose strips / meters (outside the 15, from the storage questions).

{md(fc)}
Extraction rows by drug class (after splitting multi-drug records): {', '.join(f'{k} {v}' for k, v in ext.drug_class.value_counts().items())}.

Direction of extracted results: {', '.join(f'{k} {v}' for k, v in ext.direction.value_counts().items())}.

## New relative to `data/Drug heat risk master list.csv`
{(incd.in_master_list == 'no').sum()} of {len(incd)} included records are not cited in the master list (`in_master_list = no` in both CSVs). Those at tier 1–2 (RCT/meta-analysis/systematic review or population study), {len(new_tbl)} records:

{md(new_tbl)}
## Recall check against the master list
{len(mls)} master-list papers are in the search set; the pipeline included {(mls.decision == 'include').sum()} and excluded {len(mls_ex)}:

{md(mls_ex)}
(Most excluded ones are about drugs outside the 15 — benzodiazepines, ketamine, general emergency drugs — or have no abstract.)

## No-abstract records worth a title-only look
{len(cand)} of the {len(p1)} no-abstract records have a title naming one of the drugs (or inhaler/glucose strip) and a heat/temperature word, after dropping titles with animal, NMS/malignant-hyperthermia, materials or cancer words. Keyword match only; not screened. They were not screened (rule E1) and are listed here so they are not lost:

{md(cand)}
## Citation chase (§8.4 step 2)
`citation_chase.csv` has {len(chase)} rows / {len(chase_works)} distinct works; {len(chase_works) - chase_new} are already in the search set (and were screened above), {chase_new} are not. The chase file has titles but no abstracts, so those {chase_new} works were **not screened** in this pass; fetching their abstracts is the next step.

## Limits
- Title/abstract screening only; abstracts were truncated at 2,500 characters for the screener (number checks use the full abstract). {pre_counts.get('P1 no abstract', 0)} records with no abstract were excluded unseen (rule E1), which drops some case reports.
- The prefilter is keyword-based (P3 materials, P4 no drug named, P6 NMS/serotonin syndrome without environmental-heat words); it may drop a few relevant records.
- The 24 chunks were screened by 12 separate LLM subagents with the same brief. Judgement calls drift between them (e.g. whether narrative reviews or 25°C room-temperature storage count; "antidepressants" coded `ssris` vs `multiple`). `uncertain` includes are flagged so they can be filtered out.
- Self-controlled case series are coded `case_crossover` (tier 2); illicit methamphetamine is coded `adhd_stimulants`.
- Effect numbers are the single "main" drug × heat result chosen by the LLM; secondary results are in `notes`. Only numbers verbatim in the abstract are kept.
- No human review. Not yet cross-checked against System (§8.2a check 3).
"""
    open(os.path.join(LIT, "screening_report.md"), "w").write(txt)
    print(f"screen rows {len(s)}, included {len(incd)}, extraction rows {len(ext)}, number checks {nc.to_dict()}")


if __name__ == "__main__":
    main()
