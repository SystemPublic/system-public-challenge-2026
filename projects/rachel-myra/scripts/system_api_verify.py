"""Task 2 (spec 8.5a role 2): System as an independent second extractor. The five checks of
docs/system-verification.md, run automatically on every citation claim, with badges.

Inputs
  data/processed/citation_verification.csv        claims (master list + report), abstract grounding
  data/Drug heat risk master list.csv              drug / outcome / evidence direction for master-list rows
  data/processed/system_api_master_list_findings.csv   System findings per cited paper (system_api_master_audit.py)
  data/processed/system_api_findings.csv           System findings classed drug x mediator / heat (system_api_evidence.py)
  data/processed/system_api_relationships.csv      concept edges (system_api_evidence.py)
  data/raw/system/dataverse/associations.csv       Dataverse bulk release (check 4)

Checks
  1 same number : each claimed number vs System statistic_value on the same paper (tolerance = the claim's
                  own precision, min 0.005); also CI-bound matches and derived differences of two claimed numbers
  2 same meaning: drug group named near the number vs drug group in System's variable names
                  (exact group / broader class label e.g. "psychotropic drugs" for antipsychotics / mislabel);
                  direction for ratio statistics (>1 harm) vs master-list "Evidence direction"
  3 corroboration: other System studies on the same drug group x outcome (variable-name findings + concept
                  edges): N studies, % ratio findings pointing the same way
  4 API vs Dataverse: is the matched System finding (by association id, else study+names+value) in the bulk CSV?
  5 reverse check: System findings on our papers that no claim uses; strong System edges for our drugs not
                  in the master list

Badges (per claim row and per claimed number)
  ✓✓ number in abstract AND same number + meaning in System (strict: and present in Dataverse)
  ✓  number in abstract, System has no matching extraction
  ⚠  System has our number but a different drug label (mislabel) or the opposite direction
  ?  no abstract match and no System match (hidden from public labels)
  –  no number claimed for this citation (qualitative claim; only existence/corroboration apply)
  ↗  appended when check 3 corroborates (>=2 other studies, >=50% of ratio findings in the claimed direction)

Outputs
  data/processed/system_api_verification.csv           one row per claim
  data/processed/system_api_verification_numbers.csv   one row per claimed number
  data/processed/system_api_reverse_check.csv          check 5
  data/processed/system_api_verification_summary.json  badge counts + master-list funnel
No API calls (reads the outputs of the other system_api_* scripts).
Run:  uv run python scripts/system_api_verify.py
"""
import csv, json, os, re, sys
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(__file__))
from system_api_common import (P, PROC, API_DIR, DRUG_C, MED_C, HEAT_C, DRUG_GROUPS, DRUGS15, MEDIATORS,  # noqa: E402
                               match_groups, direction, num, close, write_csv, dataverse_lookup, norm_pmid)

# Broader class words that legitimately cover a specific group (label is coarse but not wrong).
BROADER = {
    r"psychotropic|psychoactive|psychiatric medication|psychotropics": {"antipsychotics", "ssris", "lithium", "benzodiazepines", "adhd_stimulants"},
    r"antihypertensive|blood pressure[- ]lowering": {"acei_arb", "beta_blockers", "thiazides", "loop_diuretics", "diuretics_any"},
    r"diuretic": {"loop_diuretics", "thiazides", "diuretics_any"},
    r"antidiabetic|glucose[- ]lowering|hypoglyc[a]?emic agent|diabetes medication": {"insulin", "metformin", "sglt2", "sulfonylureas"},
    r"cardiovascular (drug|medication)": {"acei_arb", "beta_blockers", "thiazides", "loop_diuretics", "diuretics_any"},
    r"medication|drug use|polypharmacy": set(),
}


def groups(text, comp):
    return set(match_groups(text or "", comp))


def window(text, numtxt, w=90):
    i = (text or "").find(numtxt)
    if i < 0:
        return text or ""
    return text[max(0, i - w): i + len(numtxt) + 30]


def nearest_drug(text, numtxt, w=120):
    """Drug groups of the nearest drug mention before the number (same sentence), else just after it."""
    text = text or ""
    i = text.find(numtxt)
    if i < 0:
        return set()
    before = re.split(r"(?<=[.;])\s", text[max(0, i - w):i])[-1]
    best, pos = set(), -1
    for g, (inc, exc) in DRUG_C.items():
        for m in inc.finditer(before):
            seg = before[max(0, m.start() - 30): m.end() + 30]
            if exc and exc.search(seg):
                continue
            if m.start() > pos:
                best, pos = {g}, m.start()
            elif m.start() == pos:
                best.add(g)
    if best:
        return best
    after = text[i + len(numtxt): i + len(numtxt) + 40]
    return groups(after, DRUG_C)


def meaning(claim_drugs, f, claim_drug_text=""):
    """Compare claim drug groups with System variable names. Returns (label, detail)."""
    names = f"{f.get('variable_1_name', '')} || {f.get('variable_2_name', '')}"
    sys_drugs = groups(names, DRUG_C)
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z-]{5,}", claim_drug_text or "")
             if w.lower() not in {"drugs", "medication", "medications", "inhibitors", "agents", "therapy"}]
    hit = [w for w in words if w.lower() in names.lower()]
    if hit:
        return "same_name", hit[0]
    if not claim_drugs:
        return "n/a_no_drug_in_claim", ",".join(sorted(sys_drugs))
    if claim_drugs & sys_drugs:
        return "same", ",".join(sorted(claim_drugs & sys_drugs))
    for pat, covers in BROADER.items():
        if re.search(pat, names, re.I):
            if claim_drugs & covers:
                return "broader_label", re.search(pat, names, re.I).group(0)
            return "mislabel", f"System says '{re.search(pat, names, re.I).group(0)}', claim is {','.join(sorted(claim_drugs))}"
    if sys_drugs:
        return "mislabel", f"System drug {','.join(sorted(sys_drugs))}, claim {','.join(sorted(claim_drugs))}"
    return "mislabel_or_unnamed", "System variables name no drug: " + names[:120]


def expected_dir(evdir):
    e = (evdir or "").lower()
    if "supports harm" in e:
        return "up"
    if "null" in e:
        return "null"
    return ""


def main(master_findings=None, evidence_findings=None, relationships=None, suffix="", findings_source="api"):
    """Paths default to the API outputs. The Dataverse fallback (system_api_dataverse_fallback.py) passes
    Dataverse-derived inputs and suffix='_dataverse_fallback'."""
    master_findings = master_findings or os.path.join(PROC, "system_api_master_list_findings.csv")
    evidence_findings = evidence_findings or os.path.join(PROC, "system_api_findings.csv")
    relationships = relationships or os.path.join(PROC, "system_api_relationships.csv")
    cv = list(csv.DictReader(open(P("data", "processed", "citation_verification.csv"), encoding="utf-8")))
    ml = {r["ID"]: r for r in csv.DictReader(open(P("data", "Drug heat risk master list.csv"), encoding="utf-8-sig"))}
    mlf = list(csv.DictReader(open(master_findings, encoding="utf-8")))
    papers = {}
    by_pmid, by_doi = {}, {}
    for r in mlf:
        p = papers.setdefault(r["paper_key"], {"meta": r, "findings": []})
        if r.get("system_id"):
            p["findings"].append(r)
        if r["pmid"]:
            by_pmid[r["pmid"]] = r["paper_key"]
        if r["doi"]:
            by_doi[r["doi"].lower()] = r["paper_key"]

    # check 4 set-up: Dataverse presence of every System finding on our papers
    all_ids = {f["system_id"] for p in papers.values() for f in p["findings"]}
    all_st = {f["study_id"] for p in papers.values() for f in p["findings"]}
    dv_rows = dataverse_lookup(all_ids, all_st, cache=os.path.join(API_DIR, f"dataverse_crosscheck_master{suffix}.csv")) if all_ids else []
    dv_ids = {r["system_id"] for r in dv_rows}
    dv_sig = {(r["study_id"], (r["variable_1_name"] or "").lower(), (r["variable_2_name"] or "").lower(),
               round(num(r["statistic_value"]) or 0, 3)) for r in dv_rows}
    dv_pmids = {norm_pmid(r["pubmed_id"]) for r in dv_rows}

    def in_dv(f):
        if f["system_id"] in dv_ids:
            return "yes_same_id"
        sig = (f["study_id"], (f["variable_1_name"] or "").lower(), (f["variable_2_name"] or "").lower(), round(num(f["statistic_value"]) or 0, 3))
        return "yes_same_content" if sig in dv_sig else "no"

    # check 3 set-up: corroboration index from evidence findings
    corr = defaultdict(lambda: {"studies": set(), "up": 0, "down": 0, "null": 0})
    fpath = evidence_findings
    if os.path.exists(fpath):
        for r in csv.DictReader(open(fpath, encoding="utf-8")):
            if r["leg"] in ("drug_mediator", "drug_heat"):
                k = (r["group_a"], r["group_b"])
                corr[k]["studies"].add(r["study_id"])
                if r["direction_if_ratio"]:
                    corr[k][r["direction_if_ratio"]] += 1
    rel_tot = defaultdict(lambda: [0, 0])
    rpath = relationships
    if os.path.exists(rpath):
        for r in csv.DictReader(open(rpath, encoding="utf-8")):
            gs = (r["source_groups"] + " | " + r["target_groups"]).split(" | ")
            ds = {g.split(":")[1] for g in gs if g.startswith("drug:")}
            os_ = {g.split(":")[1] for g in gs if g.startswith("mediator:") or g.startswith("heat:")}
            for d in ds:
                for o in os_:
                    rel_tot[(d, o)][0] += 1
                    rel_tot[(d, o)][1] += int(r["num_studies"] or 0)

    claim_rows, num_rows = [], []
    used = set()
    for i, c in enumerate(cv):
        pk = by_pmid.get(norm_pmid(c["pmid"])) or by_doi.get((c["doi"] or "").lower())
        p = papers.get(pk) if pk else None
        fin = p["findings"] if p else []
        mrow = ml.get(c["location"]) if c["source"] == "master_list" else None
        drug_text = (mrow["Drug or class"] + " ; " + mrow["Example drugs"]) if mrow else ""
        outcome_text = (mrow["What can go wrong"] + " ; " + mrow["Mechanism category"]) if mrow else c["claim_text"]
        exp = expected_dir(mrow["Evidence direction"]) if mrow else ""
        nums = [x.strip() for x in (c["numbers_claimed"] or "").split("|") if x.strip()]
        found_abs = {x.strip() for x in (c["numbers_found"] or "").split("|") if x.strip()}
        per = []
        for nt in nums:
            v = num(nt)
            if v is None or (v.is_integer() and 1900 <= v <= 2100):
                continue  # years are not results
            ctx = window(c["claim_text"], nt)
            # master-list rows: the row's drug class; report rows: nearest drug named before the number
            cd = groups(mrow["Drug or class"], DRUG_C) if mrow else nearest_drug(c["claim_text"], nt)
            if "." not in nt:
                # integers are counts / sample sizes / percents: abstract check only, never matched to System values
                val_m, ci_m, der = [], [], []
                fin_for_num = []
            else:
                fin_for_num = fin
            val_m = [f for f in fin_for_num if close(v, num(f["statistic_value"]), nt)]
            ci_m = [f for f in fin_for_num if f not in val_m and (close(v, num(f["ci_lower"]), nt) or close(v, num(f["ci_upper"]), nt))]
            der = []
            if not val_m:
                for o in nums:
                    ov = num(o)
                    if ov is None or o == nt:
                        continue
                    for f in fin_for_num:
                        if "differ" not in f"{f['statistic_type']} {f['system_statistic_type']}".lower():
                            continue
                        sv = num(f["statistic_value"])
                        if sv is not None and sv != 0 and abs(abs(v - ov) - abs(sv)) <= 0.051 and abs(v - ov) > 0:
                            der.append(f)
            match = val_m or der
            mean = [meaning(cd, f, mrow["Drug or class"] if mrow else "") for f in match]
            dirs = [direction(f["statistic_value"], f["statistic_type"], f["system_statistic_type"]) for f in match]
            dir_bad = bool(exp == "up" and dirs and all(d == "down" for d in dirs if d) and any(dirs))
            dvs = [in_dv(f) for f in match]
            for f in match:
                used.add(f["system_id"])
            if match:
                labs = {m[0] for m in mean}
                if dir_bad:
                    sysres = "direction_conflict"
                elif labs & {"same", "same_name", "broader_label", "n/a_no_drug_in_claim"}:
                    sysres = "match_derived" if der and not val_m else "match"
                else:
                    sysres = "mislabel"
            elif fin and "." not in nt:
                sysres = "integer_not_compared"
            elif fin:
                sysres = "paper_in_system_number_not_extracted"
            elif p and p["meta"]["indexed"] == "True":
                sysres = "paper_indexed_no_findings"
            elif p:
                sysres = "paper_not_in_system"
            else:
                sysres = "paper_not_looked_up"
            in_abs = nt in found_abs
            if sysres in ("mislabel", "direction_conflict"):
                badge = "⚠"
            elif sysres.startswith("match") and in_abs:
                badge = "✓✓"
            elif in_abs:
                badge = "✓"
            elif sysres.startswith("match"):
                badge = "✓ (System only, not in abstract)"
            else:
                badge = "?"
            strict = badge
            if badge == "✓✓" and not any(d.startswith("yes") for d in dvs):
                strict = "✓ (System match is API-only, absent from Dataverse)"
            num_rows.append({"claim_row": i, "source": c["source"], "location": c["location"], "paper_key": pk or "",
                             "cited_label": c["cited_label"], "number": nt, "context": ctx[:200],
                             "claim_drug_groups": ",".join(sorted(cd)), "in_abstract": in_abs,
                             "system_result": sysres,
                             "system_matches": " || ".join(f"{f['variable_1_name']} -> {f['variable_2_name']}: {f['statistic_type']} {f['statistic_value']} [{f['ci_lower']}, {f['ci_upper']}] p={f['p_value']}" for f in match)[:600],
                             "system_ci_bound_matches": len(ci_m),
                             "meaning": " | ".join(f"{a}:{b}" for a, b in mean)[:300],
                             "system_direction": ",".join(d for d in dirs if d), "expected_direction": exp,
                             "in_dataverse": ",".join(dvs), "badge": badge, "badge_strict_dataverse": strict})
            per.append(num_rows[-1])
        # check 3 corroboration
        cd_all = groups(drug_text or c["claim_text"], DRUG_C)
        oc = groups(outcome_text, MED_C) | groups(outcome_text, HEAT_C)
        own = set(p["meta"]["study_ids"].split(" | ")) if p and p["meta"]["study_ids"] else set()
        n_st, up, down, rels, relst = 0, 0, 0, 0, 0
        for d in cd_all:
            for o in oc:
                k = corr.get((d, o))
                if k:
                    n_st += len(k["studies"] - own); up += k["up"]; down += k["down"]
                rels += rel_tot[(d, o)][0]; relst += rel_tot[(d, o)][1]
        tot = up + down
        same_share = (up / tot) if tot and exp == "up" else ((down / tot) if tot and exp == "down" else None)
        corroborated = bool(exp == "up" and n_st >= 2 and same_share is not None and same_share >= 0.5)
        # claim-level badge
        bs = [r["badge"] for r in per]
        if any(b == "⚠" for b in bs):
            badge = "⚠"
        elif any(b == "✓✓" for b in bs) and all(b.startswith("✓") for b in bs):
            badge = "✓✓"
        elif any(b == "✓✓" for b in bs):
            badge = "✓✓ (partial)"
        elif bs and all(b.startswith("✓") for b in bs):
            badge = "✓"
        elif any(b.startswith("✓") for b in bs):
            badge = "✓ (partial)"
        elif not per:
            badge = "–"  # no number claimed in this citation: nothing to verify at number level
        else:
            badge = "?"
        sbs = [r["badge_strict_dataverse"] for r in per]
        strict = badge if not (badge.startswith("✓✓") and not any(b == "✓✓" for b in sbs)) else "✓ (System match API-only)"
        claim_rows.append({"claim_row": i, "source": c["source"], "location": c["location"], "id_type": c["id_type"],
                           "id_value": c["id_value"], "paper_key": pk or "", "cited_label": c["cited_label"],
                           "claim_text": c["claim_text"][:400], "drug_or_class": mrow["Drug or class"] if mrow else "",
                           "claim_drug_groups": ",".join(sorted(cd_all)), "claim_outcome_groups": ",".join(sorted(oc)),
                           "expected_direction": exp, "abstract_verdict": c["verdict"],
                           "system_indexed": p["meta"]["indexed"] if p else "", "system_findings_on_paper": len(fin),
                           "numbers_checked": len(per),
                           "numbers_system_match": sum(r["system_result"].startswith("match") for r in per),
                           "numbers_mislabel": sum(r["system_result"] == "mislabel" for r in per),
                           "numbers_direction_conflict": sum(r["system_result"] == "direction_conflict" for r in per),
                           "corroboration_other_studies": n_st, "corroboration_ratio_up": up, "corroboration_ratio_down": down,
                           "corroboration_same_direction_share": round(same_share, 3) if same_share is not None else "",
                           "concept_relationships": rels, "concept_relationship_studies_summed": relst,
                           "corroborated": corroborated,
                           "badge": badge + (" ↗" if corroborated else ""),
                           "badge_strict_dataverse": strict + (" ↗" if corroborated else "")})
    write_csv(os.path.join(PROC, f"system_api_verification{suffix}.csv"), claim_rows)
    write_csv(os.path.join(PROC, f"system_api_verification_numbers{suffix}.csv"), num_rows)

    # check 5 reverse
    rev = []
    for pk, p in sorted(papers.items()):
        for f in p["findings"]:
            if f["system_id"] not in used:
                rev.append({"kind": "unused_finding_on_cited_paper", "paper_key": pk, "cited_in": p["meta"]["cited_in"][:200],
                            "system_id": f["system_id"], "variable_1_name": f["variable_1_name"], "variable_2_name": f["variable_2_name"],
                            "statistic_type": f["statistic_type"], "statistic_value": f["statistic_value"],
                            "ci_lower": f["ci_lower"], "ci_upper": f["ci_upper"], "p_value": f["p_value"],
                            "in_dataverse": in_dv(f)})
    ml_pairs = set()
    for r in ml.values():
        ds = groups(r["Drug or class"] + " " + r["Example drugs"], DRUG_C)
        os_ = groups(r["What can go wrong"] + " " + r["Mechanism category"] + " " + r["Notes"], MED_C) | groups(r["What can go wrong"] + " " + r["Mechanism category"], HEAT_C)
        ml_pairs |= {(d, o) for d in ds for o in os_}
    for (d, o), k in sorted(corr.items(), key=lambda kv: -len(kv[1]["studies"])):
        if d in DRUGS15 and len(k["studies"]) >= 5 and (d, o) not in ml_pairs:
            rev.append({"kind": "system_link_not_in_master_list", "paper_key": "", "cited_in": "",
                        "variable_1_name": DRUG_GROUPS[d]["label"], "variable_2_name": o,
                        "statistic_type": f"{len(k['studies'])} studies; ratio up {k['up']} / down {k['down']}",
                        "statistic_value": "", "in_dataverse": ""})
    write_csv(os.path.join(PROC, f"system_api_reverse_check{suffix}.csv"), rev)

    # summary + funnel
    plist = list(papers.values())
    matched_papers = {r["paper_key"] for r in num_rows if r["system_result"].startswith("match")}
    mislab_papers = {r["paper_key"] for r in num_rows if r["system_result"] == "mislabel"}
    shared = [r for r in num_rows if r["system_result"] in ("match", "match_derived", "mislabel", "direction_conflict")]
    summ = {
        "access_date": "2026-11-14",
        "system_findings_source": findings_source,
        "funnel_papers": {
            "cited_distinct_papers": len(plist),
            "indexed_in_system": sum(p["meta"]["indexed"] == "True" for p in plist),
            "with_findings": sum(bool(p["findings"]) for p in plist),
            "with_findings_in_dataverse": sum(1 for p in plist if p["meta"]["pmid"] in dv_pmids),
            "finding_matches_our_claim_number": len(matched_papers),
            "mislabeled": len(mislab_papers),
        },
        "number_level": {
            "claimed_numbers_checked": len(num_rows),
            "shared_results_number_found_in_system": len(shared),
            "same_number_same_meaning": sum(r["system_result"] in ("match", "match_derived") for r in num_rows),
            "mislabels": sum(r["system_result"] == "mislabel" for r in num_rows),
            "direction_conflicts": sum(r["system_result"] == "direction_conflict" for r in num_rows),
            "system_matches_present_in_dataverse": sum(1 for r in shared if "yes" in r["in_dataverse"]),
        },
        "badges_claims": dict(Counter(r["badge"] for r in claim_rows)),
        "badges_claims_strict_dataverse": dict(Counter(r["badge_strict_dataverse"] for r in claim_rows)),
        "badges_numbers": dict(Counter(r["badge"] for r in num_rows)),
        "claims_corroborated": sum(r["corroborated"] for r in claim_rows),
        "claims_with_any_system_relationship": sum(1 for r in claim_rows if r["concept_relationships"]),
        "reverse_unused_findings_on_cited_papers": sum(r["kind"] == "unused_finding_on_cited_paper" for r in rev),
        "reverse_system_links_not_in_master_list": sum(r["kind"] == "system_link_not_in_master_list" for r in rev),
        "note_number_conflicts": "Check 1 cannot tell 'same result, different number' from 'different result' automatically; "
                                 "numbers not found in System are recorded as paper_in_system_number_not_extracted, never as conflicts.",
    }
    json.dump(summ, open(os.path.join(PROC, f"system_api_verification_summary{suffix}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(summ, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
