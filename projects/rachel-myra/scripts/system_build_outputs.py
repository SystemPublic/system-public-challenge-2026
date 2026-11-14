"""Build app-ready System Public Graph outputs (spec 8.5a roles 1, 3, 4, 5) from the scan subsets.

Usage:
  uv run python scripts/system_build_outputs.py RAW_DIR PROCESSED_DIR

RAW_DIR (data/raw/system) must contain:
  assoc_relevant.csv, assoc_master_pmids.csv, master_pmids.csv   (system_dataverse_scan.py)
  relationships_filtered.csv                                    (system_relationships_filter.py)
  dataverse/studies.csv, dataverse/concepts.csv                 (Dataverse v2.1 originals)
  pubmed_dates.csv (optional; system_pubmed_dates.py)
and optionally ../master_list_graph_status.csv for the earlier API status.

Writes to PROCESSED_DIR:
  system_drug_mediator_findings.csv, system_heat_mediator_findings.csv,
  system_drug_heat_direct_findings.csv, system_pathways.csv,
  system_pathway_drug_summary.csv, system_hidden_drug_candidates.csv,
  system_master_list_study_findings.csv, system_relationships_subset.csv,
  system_untested_links.csv
Pass `--pmids-only OUT_TXT` instead of PROCESSED_DIR to just list the PMIDs that
need publication dates.
"""
import csv, math, os, re, sys
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import system_terms as T

csv.field_size_limit(10**8)
DRUGS = {**T.DRUGS15, **T.COMPARATORS}
KNOWN_HEAT = {"lithium", "loop_diuretics", "thiazides", "diuretics_any", "anticholinergics", "antipsychotics"}
ASSOC_COLS = ["system_id", "pubmed_id", "study_id", "statistic_type", "system_statistic_type", "statistic_value",
              "ci_level", "ci_lower", "ci_upper", "p_value", "p_value_equality"]
# graph_check.py core heat outcome terms (to reproduce its direct matches)
GC_CORE = re.compile("|".join(re.escape(t) for t in [
    "heat stroke", "heatstroke", "heat illness", "heat-related illness", "heat exhaustion", "exertional heat",
    "hyperthermia", "core temperature", "body temperature", "thermoregulation", "heat wave", "heatwave",
    "ambient temperature", "high temperature", "extreme heat", "hot weather", "heat exposure",
    "sweat", "anhidrosis", "hypohidrosis", "oligohidrosis"]), re.I)
DRUGLIKE_DESC = re.compile(r"medication|pharmaceutical|\bdrugs?\b|medicine used|used to treat|used for the treatment|"
                           r"used in the treatment|antibiotic|antipsychotic|antidepressant|anticonvulsant|antiepileptic|"
                           r"inhibitor|agonist|antagonist|blocker|diuretic|analgesic|vaccine|chemotherapy|"
                           r"anti-inflammatory|antihypertensive|anticoagulant|immunosuppress|monoclonal antibody|"
                           r"statin|class of (chemical )?compounds? used", re.I)
NOT_DRUG_LABEL = re.compile(r"^(sodium|potassium|water|glucose|creatinine|urea|oxygen|ethanol|alcohol|caffeine|"
                            r"cortisol|insulin|aldosterone|renin|angiotensin.*|vasopressin|norepinephrine|epinephrine|"
                            r"dopamine|serotonin|nitric oxide|chloride|calcium|magnesium|uric acid|albumin|"
                            r"hemoglobin|cholesterol|tobacco|nicotine|cigarette|salt|sodium chloride|carbon dioxide|"
                            r"lactic acid|bicarbonate|hydrogen|iron|zinc|vitamin d|lipid|protein|cytokine|body surface area|"
                            r"body mass index|contrast agent|contrast medium|radiocontrast agent)$", re.I)
INPATIENT = re.compile(r"vancomycin|piperacillin|polymyxin|colistin|aprotinin|hydroxyethyl starch|propofol|anesthe|anaesthe|"
                       r"contrast|vasoconstrictor|vasopressor|norepinephrine|cisplatin|chemotherapy|cardioplegi|"
                       r"aminoglycoside|gentamicin|amikacin|amphotericin|mannitol|dexmedetomidine|sevoflurane|"
                       r"intravenous|cytotoxic|antineoplastic", re.I)
# Heuristic flags (automated, not human-reviewed) for likely-irrelevant matches
FLAG_PATTERNS = [
    (re.compile(r"sweat chloride|level in sweat|in sweat\b|sweat test", re.I), "sweat used as a lab specimen, not sweating"),
    (re.compile(r"night sweats", re.I), "night sweats (symptom), not thermoregulatory sweating"),
    (re.compile(r"circulating insulin|serum insulin|plasma insulin", re.I), "endogenous insulin level, not insulin therapy"),
    (re.compile(r"febrile|fever|antipyre", re.I), "fever/antipyresis, not environmental heat"),
    (re.compile(r"\bcold\b|cool season|cool ambient|cool room|decrease in ambient|drop in ambient|lower\)|\bwinter", re.I),
     "cold or cooler-temperature contrast"),
    (re.compile(r"\b(pigs?|dogs?|cows?|cattle|sheep|mice|mouse|rats?|broilers?|chickens?|goats?|horses?|calves|heifers|"
                r"piglets|ewes|rabbits?|animals?|bulls?|camels?|udder|scrotal)\b", re.I), "possibly non-human"),
]


def flags(*texts):
    t = " || ".join(x or "" for x in texts)
    return "; ".join(sorted({msg for rx, msg in FLAG_PATTERNS if rx.search(t)}))
USE_WORDS = re.compile(r"\buse\b|users?\b|therapy|treat|dose|dosing|administ|prescri|exposure|initiat|regimen|"
                       r"\bmg\b|medication|drug|infusion|intake of|taking", re.I)


def rd(path):
    with open(path, encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f)


def split(s):
    return [x for x in (s or "").split(";") if x]


def legs(row):
    """For each ordering (a, b) yield side info: (side_index_of_a, a_groups, b_groups)."""
    s1 = {k: split(row["v1_" + k]) for k in ("drug", "mediator", "heat")}
    s2 = {k: split(row["v2_" + k]) for k in ("drug", "mediator", "heat")}
    return [(1, s1, s2, row["variable_1_name"], row["variable_2_name"], row["variable_1_concept_id"], row["variable_2_concept_id"]),
            (2, s2, s1, row["variable_2_name"], row["variable_1_name"], row["variable_2_concept_id"], row["variable_1_concept_id"])]


def load_relevant(raw):
    return list(rd(os.path.join(raw, "assoc_relevant.csv")))


def collect_pairs(rows, a_kind, b_kind):
    """Return list of (row, a_group, b_group, a_side, a_name, b_name) where side a matches a_kind and side b b_kind."""
    out, seen = [], set()
    for row in rows:
        for side, sa, sb, na, nb, ca, cb in legs(row):
            for ga in sa[a_kind]:
                for gb in sb[b_kind]:
                    key = (row["system_id"], ga, gb)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append((row, ga, gb, side, na, nb, ca, cb))
    return out


def main(raw, proc, pmids_only=None):
    rows = load_relevant(raw)
    dm = collect_pairs(rows, "drug", "mediator")
    hm = collect_pairs(rows, "heat", "mediator")
    dh = collect_pairs(rows, "drug", "heat")
    # graph_check-style direct matches (drug term vs graph_check core heat terms) not caught by our HEAT groups
    dh_keys = {(r["system_id"], g) for r, g, *_ in dh}
    gc_extra = []
    for row in rows:
        for side, sa, sb, na, nb, ca, cb in legs(row):
            if GC_CORE.search(nb):
                for ga in sa["drug"]:
                    if (row["system_id"], ga) not in dh_keys:
                        dh_keys.add((row["system_id"], ga))
                        gc_extra.append((row, ga, "graph_check_core_term", side, na, nb, ca, cb))
    master = list(rd(os.path.join(raw, "assoc_master_pmids.csv")))

    if pmids_only:
        p = {r["pubmed_id"] for r, *_ in dm + hm + dh + gc_extra} | {r["pubmed_id"] for r in master}
        p |= {r["id"] for r in rd(os.path.join(raw, "master_pmids.csv")) if r["id_type"] == "pmid"}
        with open(pmids_only, "w") as f:
            f.write("\n".join(sorted(x for x in p if x)))
        print(f"{len(p)} PMIDs -> {pmids_only}")
        return

    os.makedirs(proc, exist_ok=True)
    need = {r["study_id"] for r, *_ in dm + hm + dh + gc_extra} | {r["study_id"] for r in master}
    master_ids = list(rd(os.path.join(raw, "master_pmids.csv")))
    m_pmids = {r["id"] for r in master_ids if r["id_type"] == "pmid"}
    m_dois = {r["id"] for r in master_ids if r["id_type"] == "doi"}
    studies, by_pmid, by_doi = {}, defaultdict(list), defaultdict(list)
    for s in rd(os.path.join(raw, "dataverse", "studies.csv")):
        doi = (s["doi"] or "").lower()
        if s["study_id"] in need or s["pubmed_id"] in m_pmids or doi in m_dois:
            studies[s["study_id"]] = s
            if s["pubmed_id"] in m_pmids:
                by_pmid[s["pubmed_id"]].append(s["study_id"])
            if doi in m_dois:
                by_doi[doi].append(s["study_id"])
    dates = {}
    dp = os.path.join(raw, "pubmed_dates.csv")
    if os.path.exists(dp):
        dates = {r["pmid"]: r for r in rd(dp)}
    concepts = {c["system_id"]: c for c in rd(os.path.join(raw, "dataverse", "concepts.csv"))}

    def study_cols(row):
        s = studies.get(row["study_id"], {})
        d = dates.get(row["pubmed_id"], {})
        return [s.get("doi", ""), d.get("sortpubdate", "")[:10].replace("/", "-"), d.get("pub_year", ""),
                d.get("title", ""), s.get("population_string", ""), s.get("study_type", "")]

    STUDY_HDR = ["doi", "published_date_pubmed", "pub_year", "title_pubmed", "population_string", "study_type"]

    def write_pairs(path, pairs, a_lab, b_lab, a_dict, b_dict, extra_flag=None):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["association_id", f"{a_lab}_group", f"{a_lab}_group_label"] +
                       (["in_scope_15"] if a_dict is DRUGS else []) +
                       [f"{b_lab}_group", f"{b_lab}_group_label", f"{a_lab}_variable_side", f"{a_lab}_variable", f"{b_lab}_variable",
                        f"{a_lab}_concept_id", f"{a_lab}_concept_label", f"{b_lab}_concept_id", f"{b_lab}_concept_label"] +
                       ASSOC_COLS[1:] + STUDY_HDR + ["auto_flags_heuristic"] + (["matched_by"] if extra_flag else []))
            for row, ga, gb, side, na, nb, ca, cb in pairs:
                b_label = b_dict[gb]["label"] if gb in b_dict else gb
                w.writerow([row["system_id"], ga, a_dict[ga]["label"]] +
                           ([ga in T.DRUGS15] if a_dict is DRUGS else []) +
                           [gb, b_label, side, na, nb, ca, concepts.get(ca, {}).get("wikidata_label", ""),
                            cb, concepts.get(cb, {}).get("wikidata_label", "")] +
                           [row[c] for c in ASSOC_COLS[1:]] + study_cols(row) +
                           [flags(na, nb, studies.get(row["study_id"], {}).get("population_string", ""))] +
                           ([("system_terms.HEAT" if gb != "graph_check_core_term" else "graph_check.py core-heat terms only")]
                            if extra_flag else []))
        print(f"wrote {path}: {len(pairs)} rows")

    write_pairs(os.path.join(proc, "system_drug_mediator_findings.csv"), dm, "drug", "mediator", DRUGS, T.MEDIATORS)
    write_pairs(os.path.join(proc, "system_heat_mediator_findings.csv"), hm, "heat", "mediator", T.HEAT, T.MEDIATORS)
    write_pairs(os.path.join(proc, "system_drug_heat_direct_findings.csv"), dh + gc_extra, "drug", "heat", DRUGS,
                {**T.HEAT, "graph_check_core_term": {"label": "graph_check core heat term (body temp/sweating etc.)"}},
                extra_flag=True)

    # ---------- pathways ----------
    def agg(pairs):
        f, s = defaultdict(set), defaultdict(set)
        for row, ga, gb, *_ in pairs:
            f[(ga, gb)].add(row["system_id"]); s[(ga, gb)].add(row["study_id"])
        return f, s
    dmf, dms = agg(dm)
    hmf, hms = agg(hm)
    hm_f_by_med, hm_s_by_med = defaultdict(set), defaultdict(set)
    hm_break = defaultdict(Counter)
    for (h, m), v in hmf.items():
        hm_f_by_med[m] |= v; hm_s_by_med[m] |= hms[(h, m)]; hm_break[m][h] = len(hms[(h, m)])
    dhf, dhs = defaultdict(set), defaultdict(set)
    for row, ga, gb, *_ in dh + gc_extra:
        dhf[ga].add(row["system_id"]); dhs[ga].add(row["study_id"])

    # concept-level relationship edges
    rels = list(rd(os.path.join(raw, "relationships_filtered.csv")))
    rel_dm, rel_hm, rel_dh = defaultdict(lambda: [0, 0, 0]), defaultdict(lambda: [0, 0, 0]), defaultdict(lambda: [0, 0, 0])
    def bump(d, k, r):
        d[k][0] += 1; d[k][1] += int(r["num_findings"] or 0); d[k][2] += int(r["num_studies"] or 0)
    for r in rels:
        sd, sm, sh = split(r["src_drug"]), split(r["src_mediator"]), split(r["src_heat"])
        td, tm, th = split(r["tgt_drug"]), split(r["tgt_mediator"]), split(r["tgt_heat"])
        for a_d, b_m in ((sd, tm), (td, sm)):
            for d in a_d:
                for m in b_m: bump(rel_dm, (d, m), r)
        for a_h, b_m in ((sh, tm), (th, sm)):
            for h in a_h:
                for m in b_m: bump(rel_hm, m, r)
        for a_d, b_h in ((sd, th), (td, sh)):
            for d in a_d:
                for h in b_h: bump(rel_dh, d, r)

    path_rows = []
    for d in DRUGS:
        for m in T.MEDIATORS:
            nf, ns = len(dmf[(d, m)]), len(dms[(d, m)])
            hf, hs = len(hm_f_by_med[m]), len(hm_s_by_med[m])
            score = math.sqrt(ns * hs)  # geometric mean of distinct studies per leg
            path_rows.append({
                "drug_group": d, "drug_group_label": DRUGS[d]["label"], "in_scope_15": d in T.DRUGS15,
                "known_heat_drug": d in KNOWN_HEAT, "mediator": m, "mediator_label": T.MEDIATORS[m]["label"],
                "drug_leg_findings": nf, "drug_leg_studies": ns, "heat_leg_findings": hf, "heat_leg_studies": hs,
                "heat_leg_breakdown_studies": "; ".join(f"{k}:{v}" for k, v in hm_break[m].most_common()),
                "direct_drug_heat_findings": len(dhf[d]), "direct_drug_heat_studies": len(dhs[d]),
                "rel_drug_mediator_edges": rel_dm[(d, m)][0], "rel_drug_mediator_findings": rel_dm[(d, m)][1],
                "rel_drug_mediator_studies_summed": rel_dm[(d, m)][2],
                "rel_heat_mediator_edges": rel_hm[m][0], "rel_heat_mediator_findings": rel_hm[m][1],
                "rel_heat_mediator_studies_summed": rel_hm[m][2],
                "pathway_score_sqrt_studies": round(score, 2),
                "pathway_present": ns > 0 and hs > 0,
            })
    write_dicts(os.path.join(proc, "system_pathways.csv"), path_rows)

    # total findings/studies naming each drug group (any partner variable), for a specificity measure
    tot_f, tot_s = defaultdict(set), defaultdict(set)
    for row in rows:
        for g in set(split(row["v1_drug"]) + split(row["v2_drug"])):
            tot_f[g].add(row["system_id"]); tot_s[g].add(row["study_id"])
    summ = []
    for d in DRUGS:
        pr = [p for p in path_rows if p["drug_group"] == d]
        meds = [p for p in pr if p["drug_leg_studies"] >= 2 and p["heat_leg_studies"] >= 2]
        summ.append({"drug_group": d, "drug_group_label": DRUGS[d]["label"], "in_scope_15": d in T.DRUGS15,
                     "known_heat_drug": d in KNOWN_HEAT,
                     "drug_mediator_findings_total": len(set().union(*[dmf[(d, m)] for m in T.MEDIATORS])),
                     "drug_mediator_studies_total": len(set().union(*[dms[(d, m)] for m in T.MEDIATORS])),
                     "mediators_with_pathway": len(meds),
                     "mediators_list": "; ".join(f"{p['mediator']}({p['drug_leg_studies']})" for p in sorted(meds, key=lambda x: -x["drug_leg_studies"])),
                     "pathway_score_total": round(sum(p["pathway_score_sqrt_studies"] for p in pr), 2),
                     "pathway_score_excl_bp": round(sum(p["pathway_score_sqrt_studies"] for p in pr if p["mediator"] != "bp_hypotension"), 2),
                     "direct_drug_heat_findings": len(dhf[d]), "direct_drug_heat_studies": len(dhs[d]),
                     "all_findings_naming_drug": len(tot_f[d]), "all_studies_naming_drug": len(tot_s[d])})
        nb = set().union(*[dms[(d, m)] for m in T.MEDIATORS if m != "bp_hypotension"])
        summ[-1]["nonbp_mediator_studies"] = len(nb)
        summ[-1]["share_studies_on_nonbp_mediators"] = round(len(nb) / len(tot_s[d]), 4) if tot_s[d] else 0
    for i, s in enumerate(sorted(summ, key=lambda x: -x["share_studies_on_nonbp_mediators"]), 1):
        s["rank_share_nonbp"] = i
    for key in ("pathway_score_total", "pathway_score_excl_bp"):
        for i, s in enumerate(sorted(summ, key=lambda x: -x[key]), 1):
            s["rank_" + key.replace("pathway_score_", "")] = i
    write_dicts(os.path.join(proc, "system_pathway_drug_summary.csv"), sorted(summ, key=lambda x: x["rank_excl_bp"]))

    # ---------- hidden heat-drug candidates (concept-level, from association rows) ----------
    in15 = T.compile_groups(DRUGS)
    cand = defaultdict(lambda: {"f": set(), "s": set(), "med": defaultdict(set), "names": Counter(), "use": 0, "n": 0,
                                "heat_f": set(), "heat_s": set()})
    for row in rows:
        for side, sa, sb, na, nb, ca, cb in legs(row):
            if not ca or not (sb["mediator"] or sb["heat"]) or sa["mediator"] or sa["heat"]:
                continue
            c = concepts.get(ca)
            if not c:
                continue
            lab, desc = c["wikidata_label"], c["wikidata_description"]
            if NOT_DRUG_LABEL.match(lab or "") or not DRUGLIKE_DESC.search(desc or ""):
                continue
            k = cand[ca]
            k["n"] += 1; k["names"][na] += 1; k["use"] += bool(USE_WORDS.search(na))
            if sb["mediator"]:
                k["f"].add(row["system_id"]); k["s"].add(row["study_id"])
                for m in sb["mediator"]:
                    k["med"][m].add(row["study_id"])
            if sb["heat"]:
                k["heat_f"].add(row["system_id"]); k["heat_s"].add(row["study_id"])
    crow = []
    for cid, k in cand.items():
        if not k["s"]:
            continue
        c = concepts[cid]
        lab = c["wikidata_label"]
        grp = T.match_groups(lab, in15)
        name_grp = T.match_groups(" ".join(k["names"]), in15)
        nonbp = {m: s for m, s in k["med"].items() if m != "bp_hypotension"}
        crow.append({
            "status": "UNVALIDATED raw candidate (name/description heuristics; not checked by a human)",
            "concept_id": cid, "concept_label": lab, "wikidata_id": c["wikidata_id"], "wikidata_description": c["wikidata_description"],
            "overlaps_existing_group": ";".join(grp), "in_our_15": any(g in T.DRUGS15 for g in grp),
            "variable_names_mention_group": ";".join(name_grp),
            "mediator_findings": len(k["f"]), "mediator_studies": len(k["s"]),
            "mediators_reached": len(k["med"]), "mediators_reached_excl_bp": len(nonbp),
            "studies_by_mediator": "; ".join(f"{m}:{len(s)}" for m, s in sorted(k["med"].items(), key=lambda x: -len(x[1]))),
            "nonbp_mediator_studies": len(set().union(*nonbp.values())) if nonbp else 0,
            "direct_heat_findings": len(k["heat_f"]), "direct_heat_studies": len(k["heat_s"]),
            "inpatient_or_procedural_heuristic": bool(INPATIENT.search(lab + " " + (c["wikidata_description"] or ""))),
            "share_variable_names_with_use_words": round(k["use"] / k["n"], 2),
            "example_variable_names": " | ".join(n for n, _ in k["names"].most_common(4)),
        })
    crow.sort(key=lambda x: (-x["nonbp_mediator_studies"], -x["mediator_studies"]))
    for i, r in enumerate(crow, 1):
        r["rank_by_nonbp_studies"] = i
    write_dicts(os.path.join(proc, "system_hidden_drug_candidates.csv"), crow)

    # ---------- master-list study lookups ----------
    gs = {}
    gpath = os.path.join(raw, "..", "..", "master_list_graph_status.csv")
    if os.path.exists(gpath):
        for r in rd(gpath):
            gs[r["pmid"]] = (r["graph_status"], r["n_findings"])
    m_by_study = defaultdict(list)
    for r in master:
        m_by_study[r["study_id"]].append(r)
    out = []
    for r in master_ids:
        ids = by_pmid.get(r["id"], []) if r["id_type"] == "pmid" else by_doi.get(r["id"], [])
        base = {"id_type": r["id_type"], "id": r["id"], "master_rows": r["master_rows"],
                "api_status_2026_11_13": gs.get(r["id"], ("", ""))[0], "api_n_findings_2026_11_13": gs.get(r["id"], ("", ""))[1],
                "in_dataverse_studies": bool(ids), "dataverse_study_ids": ";".join(ids)}
        fr = [a for sid in ids for a in m_by_study.get(sid, [])]
        if r["id_type"] == "doi":  # DOI-matched studies: pull findings from the relevant subset is not enough; use master scan by pmid
            pm = {studies[s]["pubmed_id"] for s in ids if studies[s].get("pubmed_id")}
            fr = [a for a in master if a["pubmed_id"] in pm] or fr
        base["dataverse_n_findings"] = len(fr)
        d = dates.get(r["id"], {}) if r["id_type"] == "pmid" else {}
        base["title_pubmed"] = d.get("title", "")
        base["pub_year"] = d.get("pub_year", "")
        if not fr:
            out.append({**base, **{c: "" for c in ["association_id", "variable_1_name", "variable_2_name"] + ASSOC_COLS[3:]},
                        "population_string": studies[ids[0]]["population_string"] if ids else ""})
        for a in fr:
            out.append({**base, "association_id": a["system_id"], "variable_1_name": a["variable_1_name"],
                        "variable_2_name": a["variable_2_name"], **{c: a[c] for c in ASSOC_COLS[3:]},
                        "population_string": studies.get(a["study_id"], {}).get("population_string", "")})
    write_dicts(os.path.join(proc, "system_master_list_study_findings.csv"), out)

    # ---------- relationship subset ----------
    rsub = []
    for r in rels:
        s_any = r["src_drug"] or r["src_mediator"] or r["src_heat"]
        t_any = r["tgt_drug"] or r["tgt_mediator"] or r["tgt_heat"]
        if not (s_any and t_any):
            continue
        def kind(d, m, h):
            return "+".join(x for x, v in (("drug", d), ("mediator", m), ("heat", h)) if v)
        rsub.append({"relationship_id": r["relationship_id"],
                     "source_concept_id": r["source_concept.system_id"], "source_label": r["source_concept.wikidata_label"],
                     "source_wikidata_id": r["source_concept.wikidata_id"],
                     "target_concept_id": r["target_concept.system_id"], "target_label": r["target_concept.wikidata_label"],
                     "target_wikidata_id": r["target_concept.wikidata_id"],
                     "num_findings": r["num_findings"], "num_studies": r["num_studies"],
                     "last_published_date": r["last_published_date"], "last_updated": r["last_updated"],
                     "source_kind": kind(r["src_drug"], r["src_mediator"], r["src_heat"]),
                     "target_kind": kind(r["tgt_drug"], r["tgt_mediator"], r["tgt_heat"]),
                     "source_groups": ";".join(filter(None, [r["src_drug"], r["src_mediator"], r["src_heat"]])),
                     "target_groups": ";".join(filter(None, [r["tgt_drug"], r["tgt_mediator"], r["tgt_heat"]]))})
    rsub.sort(key=lambda x: -int(x["num_studies"] or 0))
    write_dicts(os.path.join(proc, "system_relationships_subset.csv"), rsub)

    # ---------- implied-but-untested ----------
    ut = []
    for p in path_rows:
        if p["drug_leg_findings"] and p["heat_leg_findings"]:
            ut.append({"source": "drug_group", "entity": p["drug_group"], "entity_label": p["drug_group_label"],
                       "in_scope_15": p["in_scope_15"], "mediator": p["mediator"],
                       "drug_leg_findings": p["drug_leg_findings"], "drug_leg_studies": p["drug_leg_studies"],
                       "heat_leg_findings": p["heat_leg_findings"], "heat_leg_studies": p["heat_leg_studies"],
                       "direct_drug_heat_findings": p["direct_drug_heat_findings"],
                       "untested": p["direct_drug_heat_findings"] == 0,
                       "note": "direct findings exist (see system_drug_heat_direct_findings.csv); check whether they cover this mediator's mechanism"
                       if p["direct_drug_heat_findings"] else "implied by graph, no direct drug x heat finding"})
    for c in crow[:200]:
        if c["in_our_15"]:
            continue
        for m, n in [x.split(":") for x in c["studies_by_mediator"].split("; ") if x]:
            if hm_f_by_med[m]:
                ut.append({"source": "hidden_candidate (unvalidated)", "entity": c["concept_id"], "entity_label": c["concept_label"],
                           "in_scope_15": False, "mediator": m, "drug_leg_findings": "", "drug_leg_studies": int(n),
                           "heat_leg_findings": len(hm_f_by_med[m]), "heat_leg_studies": len(hm_s_by_med[m]),
                           "direct_drug_heat_findings": c["direct_heat_findings"], "untested": c["direct_heat_findings"] == 0,
                           "note": "candidate concept from broad scan"})
    write_dicts(os.path.join(proc, "system_untested_links.csv"), ut)


def write_dicts(path, rows):
    if not rows:
        print(f"WARNING: no rows for {path}")
        open(path, "w").close(); return
    keys = list(rows[0].keys())
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader(); w.writerows(rows)
    print(f"wrote {path}: {len(rows)} rows")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[2] == "--pmids-only":
        main(sys.argv[1], None, pmids_only=sys.argv[3])
    elif len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
