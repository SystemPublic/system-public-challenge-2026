"""Resolve pass1/pass2 disagreements (after re-reading the quotes) and build the final matrix,
the source table and a coverage summary.
Run: python3 -I scripts/guidance_build_final.py
Outputs: data/processed/guidance_matrix.csv, data/processed/guidance_sources.csv,
         data/processed/guidance_kappa.json (adds resolution + coverage blocks)"""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guidance_common import PROC, CORE, SOURCES

FIELDS = ["mentioned", "mention_level", "action_type", "specificity", "evidence_cited"]

# Resolutions after re-reading each disputed quote in the full source text.
# value: (winner, field overrides applied on top of pass 2, reason)
RES = {
 ("ANSM", "adhd_stimulants"): ("pass1", dict(mentioned="yes", mention_level="specific", action_type="general_caution", all_actions="general_caution", specificity="generic"), "Codebook counts recreational amphetamine mention as specific; context is drug misuse ('usage de certaines drogues'), not ADHD prescribing."),
 ("ANSM", "ssri"): ("pass2", {}, "PDF p. 3 sentence listing 'antidépresseurs sérotoninergiques' ends with reference 10 (Sommet 2012): evidence cited."),
 ("CDC", "epinephrine_autoinjector"): ("pass2", {}, "EpiPen sentence states a hazard only; CDC's storage bullet names insulin and inhalers, not EpiPens: generic."),
 ("GER_HEID", "laxatives"): ("pass2", {}, "Laxanzien row carries reference 2 in the table."),
 ("HC", "acei_arb"): ("pass2", {}, "Table 4.2 row 'ACE-II inhibitors' explicitly says 'Monitor patient hydration' (labelled general; 'No specific recommendations')."),
 ("HC", "nitrates"): ("pass2", {}, "Table 4.2 row 'Nitrate vasodilators' explicitly says 'Monitor patient hydration'."),
 ("HC", "acetaminophen"): ("pass1", dict(mention_level="umbrella", quote="On antipyretics", location="Health Canada 2011, §3.2 'Factors Associated with Heat Morbidity'"), "'On antipyretics' is listed as a heat-morbidity risk factor: umbrella mention."),
 ("HC", "adhd_stimulants"): ("pass1", dict(mentioned="yes", mention_level="specific", action_type="general_caution", all_actions="general_caution", specificity="generic", evidence_cited="yes"), "Codebook counts amphetamines named in a case report; they are weight-loss amphetamines (phentermine, propylhexedrine), not ADHD drugs. Case report cites Reference 177, so evidence = yes (neither pass had this exactly)."),
 ("HC", "carbamazepine_oxcarbazepine"): ("pass1", dict(evidence_cited="no"), "The Table 4.2 recommendation has no citation; the cited hyponatraemia sentence (Reference 193) is about antiepileptics in general (umbrella)."),
 ("HC", "ccb"): ("pass1", dict(specificity="specific"), "'The side effects of calcium channel blockers should also be monitored during the summer months' attaches the action to the class itself."),
 ("HC", "insulin"): ("pass2", {}, "Ch. 3 'Diabetes' explicitly addresses insulin storage with potency data (Reference 134); pass 1 missed it."),
 ("HC", "lithium"): ("pass1", dict(action_type="general_caution", all_actions="general_caution"), "Lithium row gives drug-specific hydration advice (water, avoid electrolyte solutions) but no instruction to monitor levels: general_caution, specificity specific."),
 ("HC", "ssri"): ("pass1", dict(action_type="general_caution", all_actions="general_caution"), "'Especially in individuals taking SSRIs' points to the hydration/protect-from-heat advice; no explicit monitoring instruction."),
 ("HC", "snri"): ("pass2", {}, "'Antidepressants' row is an umbrella mention for SNRIs."),
 ("UKHSA", "carbamazepine_oxcarbazepine"): ("pass2", {}, "'antiepileptics' = umbrella."),
 ("UKHSA", "ccb"): ("pass2", {}, "'antihypertensives' = umbrella."),
 ("UKHSA", "nitrates"): ("pass1", dict(mentioned="yes", mention_level="specific", action_type="general_caution", all_actions="general_caution", specificity="generic"), "Row is 'Nitrates / antianginals'; UKHSA names 'antianginal drugs': specific."),
 ("UKHSA", "snri"): ("pass2", {}, "'serotoninergic agonists' = umbrella."),
 ("WHO_EUR", "adhd_stimulants"): ("pass2", {}, "'Sympathomimetics' (2011 table) = umbrella."),
 ("WHO_EUR", "anticholinergics_oxybutynin"): ("pass1", dict(evidence_cited="yes"), "2026 sentence naming anticholinergics ends with citations (19–22)."),
 ("WHO_EUR", "antihistamines_1stgen"): ("pass1", dict(mentioned="no", mention_level="umbrella", action_type="none", all_actions="", specificity="none"), "WHO says 'Antihistamines' without generation: umbrella for first-generation antihistamines."),
 ("WHO_EUR", "carbamazepine_oxcarbazepine"): ("pass2", {}, "'Antiepileptics' = umbrella."),
 ("WHO_EUR", "snri"): ("pass2", {}, "'Antidepressants' = umbrella."),
 ("WHO_EUR", "tca"): ("pass2", {}, "'Antidepressants' = umbrella."),
}

NOTES = {
 ("UKHSA", "acetaminophen"): "Heatstroke first-aid advice, not chronic-medication guidance.",
 ("WHO_EUR", "acetaminophen"): "Heatstroke treatment advice, not chronic-medication guidance.",
 ("ANSM", "acetaminophen"): "Advice for fever during a heat wave (heatstroke); not chronic medication.",
 ("ANSM", "opioid_patches_fentanyl"): "ANSM warns that transdermal systems' pharmacokinetics change in heat (vasodilation, detachment from sweating) but names no opioid/fentanyl.",
 ("ANSM", "insulin"): "ANSM also publishes a glucose-meter heat Q&A (strips, sensors, control solutions); it does not name insulin.",
 ("NYC", "insulin"): "Monitoring advice is from HAN 2026 #23; storage advice from the provider page.",
 ("CDC", "ssri"): "Internal inconsistency: SSRIs listed under impaired sweating but table says 'Increased sweating'.",
 ("VIC", "metformin"): "Only source listing metformin as a narrow-therapeutic-index drug whose toxicity increases in dehydration.",
 ("GER_HEID", "opioid_patches_fentanyl"): "Only source that names opioid patches; action: close ADR monitoring and dose adjustment if needed.",
 ("GER_HEID", "topiramate_zonisamide"): "Only source naming zonisamide.",
 ("WHO_EUR", "antipsychotics_clozapine"): "Storage action concerns supply-chain temperature control of antipsychotics (2026 HHAP), not patient dosing.",
 ("VIC", "antipsychotics_clozapine"): "Clozapine named explicitly.",
 ("GER_HEID", "antipsychotics_clozapine"): "Clozapine named explicitly.",
}

DOC_EVIDENCE = {  # document-level evidence basis (verbatim support in README)
 "CDC": ("no", "no", "States 'This guidance reflects expert opinion'; no references."),
 "NYC": ("no", "no", "No references; links University of Arizona heat & medications resource."),
 "UKHSA": ("no", "no", "List 'not exhaustive'; no references in medication section."),
 "HC": ("yes", "no", "Reports odds ratios with 95% CIs from 2003 French heatwave studies and case series; no formal grading."),
 "ANSM": ("yes", "no", "Cites epidemiological and pharmacovigilance studies (refs 1-11); states the list is theory/mechanism-based; no grading."),
 "WHO_EUR": ("yes", "no", "2011 table 'adapted from Health Canada (2011b)'; 2026 HHAP cites references; no drug-level grading."),
 "VIC": ("no", "no", "No references in medication table."),
 "GER_BMG": ("no", "no", "No drug content; defers to 'pharmakologische Empfehlungen zur Risikominimierung bei Hitzewellen' (www.dosing.de)."),
 "GER_HEID": ("yes", "no", "Numbered literature references per drug row; '?' marks unclear/disputed effects; no formal grade."),
}

def main():
    p1 = {(r["source_id"], r["drug_id"]): r for r in csv.DictReader(open(os.path.join(PROC, "guidance_coding_pass1.csv"), encoding="utf-8"))}
    p2 = {(r["source_id"], r["drug_id"]): r for r in csv.DictReader(open(os.path.join(PROC, "guidance_coding_pass2.csv"), encoding="utf-8"))}
    rows = []
    for k, r2 in p2.items():
        r1 = p1[k]
        agree = all((r1[f] or "none") == (r2[f] or "none") for f in FIELDS)
        out = dict(r2)
        out.pop("coder", None)
        if agree:
            res, why = "agreed", ""
        else:
            win, ov, why = RES[k]
            out.update(ov)
            res = f"resolved_{win}"
        out["pass1_agreed_all_fields"] = "yes" if agree else "no"
        out["resolution"] = res
        out["resolution_note"] = why
        out["note"] = NOTES.get(k, "")
        out["source_evidence_basis_cited"], out["source_evidence_graded"], _ = DOC_EVIDENCE[k[0]]
        out["specific_action"] = "yes" if (out["mentioned"] == "yes" and out["specificity"] == "specific") else "no"
        rows.append(out)
    cols = ["source_id", "drug_id", "drug_label", "drug_group", "mentioned", "mention_level", "action_type", "all_actions",
            "specificity", "specific_action", "evidence_cited", "source_evidence_basis_cited", "source_evidence_graded",
            "quote", "location", "note", "pass1_agreed_all_fields", "resolution", "resolution_note"]
    with open(os.path.join(PROC, "guidance_matrix.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows([{c: r.get(c, "") for c in cols} for r in rows])
    # coverage per core drug
    eight = ["CDC", "NYC", "UKHSA", "HC", "ANSM", "WHO_EUR", "VIC", "GER"]
    cov = {}
    for d in CORE:
        g = {s: next(r for r in rows if r["source_id"] == s and r["drug_id"] == d) for s in SOURCES}
        def jur(s, key):
            if s == "GER":
                return any(g[x][key] == "yes" for x in ("GER_BMG", "GER_HEID"))
            return g[s][key] == "yes"
        cov[d] = {
            "mentioned_of_8": sum(jur(s, "mentioned") for s in eight),
            "specific_action_of_8": sum(jur(s, "specific_action") for s in eight),
            "specific_action_of_8_strict_germany_BMG_only": sum(jur(s, "specific_action") for s in eight[:-1]) + (g["GER_BMG"]["specific_action"] == "yes"),
            "sources_with_specific_action": [s for s in SOURCES if g[s]["specific_action"] == "yes"],
            "sources_mentioning": [s for s in SOURCES if g[s]["mentioned"] == "yes"],
            "umbrella_only": [s for s in SOURCES if g[s]["mention_level"] == "umbrella"],
        }
    kj = json.load(open(os.path.join(PROC, "guidance_kappa.json")))
    kj["resolution"] = {"n_disagreeing_cells": len(RES), "resolved_to_pass1": sum(v[0] == "pass1" for v in RES.values()),
                        "resolved_to_pass2": sum(v[0] == "pass2" for v in RES.values())}
    kj["coverage_core_drugs"] = cov
    kj["note"] = ("Both passes were done by AI (pass 1: a separate Claude subagent coding keyword-hit excerpts blind to pass 2; "
                  "pass 2: Claude reading whole medication sections). This is an automated substitute for two human coders, "
                  "not independent human double-coding. Germany counted as one jurisdiction = BMG federal plans + the Heidelberger "
                  "Hitze-Tabelle they reference.")
    json.dump(kj, open(os.path.join(PROC, "guidance_kappa.json"), "w"), indent=2, ensure_ascii=False)
    for d, c in cov.items():
        print(f"{d:30s} mentioned {c['mentioned_of_8']}/8  specific action {c['specific_action_of_8']}/8  {c['sources_with_specific_action']}")

if __name__ == "__main__":
    main()
