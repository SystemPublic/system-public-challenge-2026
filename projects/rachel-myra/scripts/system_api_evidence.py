"""Task 3 (spec 8.5a roles 1 and 3): evidence pull for the 15 drugs via the System API, two-hop pathways,
and the "are known heat drugs rediscovered?" validation, redone on the full API graph.

Steps (every response cached in data/raw/system/api/cache/; reruns are free):
 A. Concept search  GET /v1/concepts?search=wikidata_label:<term>&limit=25
    for every drug / comparator term in scripts/system_terms.py, plus mediator and heat terms.
    A returned concept is kept only if its wikidata_label matches that group's regex (system_terms).
 B. Concept edges   GET /v1/concepts/{id}/relationships?limit=1000&offset=..  (aliases dropped before caching)
    Each edge's other end is classed drug / mediator / heat by concept id (from A) or by label regex.
    -> data/processed/system_api_relationships.csv  (drug-mediator, mediator-heat, drug-heat edges)
 C. Findings behind edges  GET /v1/relationships/{A%7CB}/associations
    for drug-heat and mediator-heat edges (all), and drug-mediator edges (non-BP mediators all; BP edges
    only the top ones by num_studies, because BP edges are antihypertensive efficacy trials).
 D. Variable-name route (grounding is incomplete): GET /v1/variables?search=name:<term>
    for heat terms and non-BP mediator terms; variables whose name matches the regex are kept and their
    findings pulled with GET /v1/associations?filter=variable_1_id:a||b.. (and variable_2_id), falling back
    to /v1/variables/{id}/associations if OR filters are not honoured.
    Every finding from C and D is classed by its two variable NAMES (drug x mediator, mediator x heat, drug x heat).
    -> data/processed/system_api_findings.csv
 E. Pathways and validation (same method as system_build_outputs.py on Dataverse):
    -> data/processed/system_api_pathways.csv            drug group x mediator: studies per leg, concept totals
    -> data/processed/system_api_pathway_drug_summary.csv per drug: ranks (non-BP specificity share etc.)

Budget knobs (env): SYSTEM_API_BUDGET (default 6000 live calls/day),
  EVID_VAR_CAP (variables paged per search term, default 600), EVID_BP_EDGES (default 40).
Run:  uv run --with requests python scripts/system_api_evidence.py
"""
import json, math, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from system_api_client import Client, BudgetExceeded  # noqa: E402
from system_api_common import (DRUG_GROUPS, DRUGS15, MEDIATORS, HEAT, DRUG_C, MED_C, HEAT_C, PROC, API_DIR,  # noqa: E402
                               match_groups, direction, write_csv)

VAR_CAP = int(os.environ.get("EVID_VAR_CAP", "600"))
BP_EDGES = int(os.environ.get("EVID_BP_EDGES", "40"))
DROP = ("wikidata_aliases",)

# Extra concept-search terms (Wikidata labels) beyond the system_terms include lists.
EXTRA_DRUG_TERMS = {
    "sglt2": ["empagliflozin", "dapagliflozin", "canagliflozin", "ertugliflozin", "SGLT2 inhibitor"],
    "insulin": ["insulin glargine", "insulin lispro", "insulin aspart", "insulin detemir", "insulin degludec",
                "insulin pump", "regular insulin", "insulin therapy"],
    "acei_arb": ["ACE inhibitor", "angiotensin II receptor antagonist"],
    "thiazides": ["thiazide diuretic"],
    "loop_diuretics": ["loop diuretic"],
    "antipsychotics": ["atypical antipsychotic", "typical antipsychotic"],
    "anticholinergics": ["anticholinergic", "muscarinic antagonist"],
    "adhd_stimulants": ["lisdexamfetamine", "methylphenidate", "amphetamine", "dextroamphetamine", "mixed amphetamine salts"],
    "opioids_fentanyl": ["opioid", "fentanyl", "transdermal fentanyl"],
    "epinephrine_ai": ["epinephrine", "adrenaline"],
    "ssris": ["selective serotonin reuptake inhibitor", "antidepressant"],
    "beta_blockers": ["beta blocker"],
}
MED_TERMS = {
    "dehydration": ["dehydration", "hypovolemia", "volume depletion"],
    "hyponatremia": ["hyponatremia", "serum sodium", "syndrome of inappropriate antidiuretic hormone secretion"],
    "aki": ["acute kidney injury", "acute kidney failure", "acute renal failure"],
    "bp_hypotension": ["hypotension", "orthostatic hypotension", "blood pressure"],
    "sweating": ["sweating", "perspiration", "anhidrosis", "hypohidrosis", "hyperhidrosis"],
    "body_temp": ["hyperthermia", "body temperature", "thermoregulation", "core body temperature"],
}
HEAT_TERMS = {
    "heat_wave": ["heat wave", "heatwave"],
    "ambient_temp": ["ambient temperature", "high temperature", "hot weather", "heat exposure", "air temperature",
                     "heat index"],
    "extreme_heat": ["extreme heat", "extreme temperature"],
    "heat_illness": ["heat stroke", "heat illness", "heat exhaustion", "heat-related illness", "heat stress",
                     "exertional heat illness"],
}
# Variable-name searches (route D)
VAR_TERMS_HEAT = ["heat wave", "heatwave", "heat stroke", "heatstroke", "heat illness", "heat-related", "heat exposure",
                  "heat exhaustion", "heat stress", "ambient temperature", "high temperature", "hot weather",
                  "extreme heat", "outdoor temperature", "air temperature", "apparent temperature", "heat index",
                  "daily temperature", "maximum temperature", "temperature exposure"]
VAR_TERMS_MED = ["dehydration", "volume depletion", "hypovolemia", "hyponatremia", "hyponatraemia", "serum sodium",
                 "acute kidney injury", "acute renal failure", "hypotension", "orthostatic hypotension",
                 "sweating", "sweat rate", "anhidrosis", "hypohidrosis", "hyperthermia", "body temperature",
                 "core temperature", "thermoregulation"]


def cls_label(label):
    return {"drug": match_groups(label, DRUG_C), "mediator": match_groups(label, MED_C), "heat": match_groups(label, HEAT_C)}


def concept_search(c):
    """Return {concept_id: {label, wikidata_id, kind, groups:set, terms:set}}."""
    kept = {}
    plan = []
    for g, d in DRUG_GROUPS.items():
        for t in d["include"] + EXTRA_DRUG_TERMS.get(g, []):
            if len(t) > 4:
                plan.append(("drug", g, t))
    for g, ts in MED_TERMS.items():
        plan += [("mediator", g, t) for t in ts]
    for g, ts in HEAT_TERMS.items():
        plan += [("heat", g, t) for t in ts]
    seen = set()
    for kind, g, t in plan:
        if (kind, t.lower()) in seen:
            continue
        seen.add((kind, t.lower()))
        res = (c.get("/concepts", search=f"wikidata_label:{t}", limit=25) or {}).get("data", [])
        comp = {"drug": DRUG_C, "mediator": MED_C, "heat": HEAT_C}[kind]
        for x in res:
            lab = x.get("wikidata_label") or ""
            gs = match_groups(lab, comp)
            if not gs:
                continue
            rec = kept.setdefault(x["system_id"], {"label": lab, "wikidata_id": x.get("wikidata_id"),
                                                   "description": (x.get("wikidata_description") or "")[:200],
                                                   "kinds": set(), "groups": set(), "terms": set()})
            rec["kinds"].add(kind)
            rec["groups"].update(f"{kind}:{gg}" for gg in gs)
            rec["terms"].add(t)
    return kept


def other_end(rel, cid):
    s, t = rel["source_concept"], rel["target_concept"]
    return (t, "out") if s["system_id"] == cid else (s, "in")


def edge_groups(cid, concepts):
    """groups for a concept id via search results, else via its label."""
    return concepts[cid]["groups"] if cid in concepts else set()


def main():
    c = Client()
    log = {"started": True}
    concepts = concept_search(c)
    print(f"A. kept {len(concepts)} concepts ({c.stats()})")
    json.dump({k: {**v, "kinds": sorted(v["kinds"]), "groups": sorted(v["groups"]), "terms": sorted(v["terms"])}
               for k, v in concepts.items()}, open(os.path.join(API_DIR, "concepts_kept.json"), "w"), indent=1)

    # B. relationships for every kept concept
    edges = {}
    nrels = {}
    for cid, rec in sorted(concepts.items(), key=lambda kv: kv[1]["label"]):
        try:
            rels = c.paged(f"/concepts/{cid}/relationships", page=1000, cap=20000, drop_keys=DROP)
        except BudgetExceeded:
            print("budget reached during relationships"); break
        nrels[cid] = len(rels)
        for r in rels:
            o, _ = other_end(r, cid)
            og = edge_groups(o["system_id"], concepts)
            if not og:
                cl = cls_label(o.get("wikidata_label") or "")
                og = {f"{k}:{g}" for k, gs in cl.items() for g in gs}
            if not og:
                continue
            rid = r["relationship_id"]
            e = edges.setdefault(rid, {"relationship_id": rid,
                                       "source_label": r["source_concept"].get("wikidata_label"),
                                       "source_id": r["source_concept"]["system_id"],
                                       "target_label": r["target_concept"].get("wikidata_label"),
                                       "target_id": r["target_concept"]["system_id"],
                                       "num_findings": r.get("num_findings"), "num_studies": r.get("num_studies"),
                                       "last_published_date": r.get("last_published_date"),
                                       "last_updated": r.get("last_updated"), "groups": set()})
            e["groups"] |= {f"{x}" for x in rec["groups"]} | og
    rel_rows = []
    for e in edges.values():
        kinds = {g.split(":")[0] for g in e["groups"]}
        # an edge is relevant if its two ends are of two kinds among drug/mediator/heat
        sg = edge_groups(e["source_id"], concepts) or {f"{k}:{g}" for k, gs in cls_label(e["source_label"] or "").items() for g in gs}
        tg = edge_groups(e["target_id"], concepts) or {f"{k}:{g}" for k, gs in cls_label(e["target_label"] or "").items() for g in gs}
        sk, tk = {g.split(":")[0] for g in sg}, {g.split(":")[0] for g in tg}
        etype = set()
        for a in sk:
            for b in tk:
                if a != b:
                    etype.add("-".join(sorted([a, b])))
        if not etype:
            continue
        rel_rows.append({**{k: v for k, v in e.items() if k != "groups"}, "edge_type": " | ".join(sorted(etype)),
                         "source_groups": " | ".join(sorted(sg)), "target_groups": " | ".join(sorted(tg))})
    rel_rows.sort(key=lambda r: (r["edge_type"], -(r["num_studies"] or 0)))
    write_csv(os.path.join(PROC, "system_api_relationships.csv"), rel_rows)
    print(f"B. {len(rel_rows)} drug/mediator/heat edges ({c.stats()})")

    # C. associations behind edges
    def want(r):
        if "drug-heat" in r["edge_type"] or "heat-mediator" in r["edge_type"]:
            return True
        return "drug-mediator" in r["edge_type"]
    bp_only = lambda r: all(("bp_hypotension" in g) or not g.startswith("mediator") for g in  # noqa: E731
                            (r["source_groups"] + " | " + r["target_groups"]).split(" | "))
    todo = [r for r in rel_rows if want(r) and not (("drug-mediator" == r["edge_type"]) and bp_only(r))]
    bp = [r for r in rel_rows if r["edge_type"] == "drug-mediator" and bp_only(r)]
    # keep hypotension-labelled BP edges first, then by studies
    bp.sort(key=lambda r: (0 if re.search("hypotens", f"{r['source_label']} {r['target_label']}", re.I) else 1, -(r["num_studies"] or 0)))
    todo += bp[:BP_EDGES]
    findings = {}
    for r in todo:
        rid = r["relationship_id"].replace("|", "%7C")
        try:
            assocs = c.paged(f"/relationships/{rid}/associations", page=100, cap=1000)
        except BudgetExceeded:
            print("budget reached during edge associations"); break
        for a in assocs:
            findings.setdefault(a["system_id"], {**a, "routes": set()})["routes"].add("edge:" + r["relationship_id"])
    print(f"C. {len(findings)} findings behind {len(todo)} edges ({c.stats()})")

    # D. variable-name route
    var_hits = {}
    batch_ok = None
    for kind, terms in (("heat", VAR_TERMS_HEAT), ("mediator", VAR_TERMS_MED)):
        comp = HEAT_C if kind == "heat" else MED_C
        for t in terms:
            try:
                vs = c.paged("/variables", page=100, cap=VAR_CAP, search=f"name:{t}")
            except BudgetExceeded:
                print("budget reached during variable search"); break
            for v in vs:
                if match_groups(v.get("name") or "", comp):
                    var_hits.setdefault(v["system_id"], {"name": v.get("name"), "concept_id": v.get("concept_id"),
                                                         "terms": set(), "kind": kind})["terms"].add(t)
    print(f"D. {len(var_hits)} matching variables ({c.stats()})")
    ids = sorted(var_hits)
    skipped_d = []
    skipped_batches = []

    def batch_assoc(side, chunk):
        """OR-batched lookup; on a server error, split the batch in half (down to one-variable calls)."""
        c.max_attempts = 2  # a 500 here is the query being too heavy, not a blip: split instead of waiting
        if os.environ.get("EVID_D_CACHED_ONLY"):
            # Fast finish: use only batches already fetched; skip the rest (the server takes ~10 s per batch).
            from system_api_client import _cache_name
            flt = f"{side}:" + "||".join(chunk)
            if not os.path.exists(_cache_name("/associations", {"filter": flt, "offset": 0, "limit": 100})[1]):
                skipped_d.append(len(chunk))
                skipped_batches.append([side, chunk])
                return []
        try:
            return c.paged("/associations", page=100, cap=3000, filter=f"{side}:" + "||".join(chunk))
        except RuntimeError as e:
            if isinstance(e, BudgetExceeded):
                raise
            if len(chunk) == 1:
                if side == "variable_1_id":  # the per-variable route returns both sides at once
                    try:
                        return c.paged(f"/variables/{chunk[0]}/associations", page=100, cap=1000)
                    except RuntimeError as e2:
                        if isinstance(e2, BudgetExceeded):
                            raise
                        print(f"  skipped variable {chunk[0]}: {str(e2)[-60:]}")
                return []
            mid = len(chunk) // 2
            return batch_assoc(side, chunk[:mid]) + batch_assoc(side, chunk[mid:])

    try:
        for i in range(0, len(ids), 40):
            chunk = ids[i:i + 40]
            got = []
            if batch_ok is not False:
                for side in ("variable_1_id", "variable_2_id"):
                    got += batch_assoc(side, chunk)
                if batch_ok is None:
                    # verify OR semantics once against a single-variable call
                    single = c.paged(f"/variables/{chunk[0]}/associations", page=100, cap=1000)
                    gotids = {a["system_id"] for a in got}
                    batch_ok = all(a["system_id"] in gotids for a in single)
                    print("OR filter on variable ids honoured:", batch_ok)
                    if not batch_ok:
                        got = []
            if batch_ok is False:
                for vid in chunk:
                    got += c.paged(f"/variables/{vid}/associations", page=100, cap=1000)
            for a in got:
                findings.setdefault(a["system_id"], {**a, "routes": set()})["routes"].add("variable_name")
    except BudgetExceeded:
        print("budget reached during variable associations")
    if skipped_batches and os.environ.get("EVID_DUMP_SKIPPED"):
        json.dump(skipped_batches, open(os.environ["EVID_DUMP_SKIPPED"], "w"))  # for scripts/system_api_prefetch.py
    if skipped_d:
        print(f"D. fast finish: skipped {len(skipped_d)} uncached batches ({sum(skipped_d)} variable-side lookups)")
    print(f"D. total findings now {len(findings)} ({c.stats()})")

    # classify findings by variable names (both orders)
    frows = []
    for a in findings.values():
        n1, n2 = a.get("variable_1_name") or "", a.get("variable_2_name") or ""
        g1, g2 = cls_label(n1), cls_label(n2)
        pairs = set()
        for x, y in ((g1, g2), (g2, g1)):
            for d in x["drug"]:
                for m in y["mediator"]:
                    pairs.add(("drug_mediator", d, m))
                for h in y["heat"]:
                    pairs.add(("drug_heat", d, h))
            for h in x["heat"]:
                for m in y["mediator"]:
                    pairs.add(("heat_mediator", h, m))
        base = {k: a.get(k) for k in ("system_id", "study_id", "pubmed_id", "variable_1_name", "variable_2_name",
                                       "statistic_type", "system_statistic_type", "statistic_value", "ci_lower",
                                       "ci_upper", "ci_level", "p_value", "p_value_equality", "variable_1_concept_id",
                                       "variable_2_concept_id")}
        base["routes"] = " | ".join(sorted(a["routes"]))[:300]
        base["direction_if_ratio"] = direction(a.get("statistic_value"), a.get("statistic_type"), a.get("system_statistic_type"))
        if not pairs:
            frows.append({**base, "leg": "", "group_a": "", "group_b": ""})
        for leg, x, y in sorted(pairs):
            frows.append({**base, "leg": leg, "group_a": x, "group_b": y})
    write_csv(os.path.join(PROC, "system_api_findings.csv"), frows)
    print(f"wrote system_api_findings.csv: {len(frows)} rows")

    # E. pathways
    leg = defaultdict(set)  # (leg, a, b) -> study ids
    legf = defaultdict(set)
    for r in frows:
        if r["leg"]:
            leg[(r["leg"], r["group_a"], r["group_b"])].add(r["study_id"])
            legf[(r["leg"], r["group_a"], r["group_b"])].add(r["system_id"])
    heat_leg = defaultdict(set)
    for (lg, h, m), s in leg.items():
        if lg == "heat_mediator":
            heat_leg[m] |= s
    concept_tot = defaultdict(lambda: [0, 0, 0, ""])  # (kind, d, m) -> rels, findings, studies, newest
    for r in rel_rows:
        groups = (r["source_groups"] + " | " + r["target_groups"]).split(" | ")
        ds = {g.split(":")[1] for g in groups if g.startswith("drug:")}
        ms = {g.split(":")[1] for g in groups if g.startswith("mediator:")}
        hs = {g.split(":")[1] for g in groups if g.startswith("heat:")}
        for d in ds:
            for m in ms:
                t = concept_tot[("dm", d, m)]
                t[0] += 1; t[1] += r["num_findings"] or 0; t[2] += r["num_studies"] or 0
                t[3] = max(t[3], r["last_published_date"] or "")
            for h in hs:
                t = concept_tot[("dh", d, h)]
                t[0] += 1; t[1] += r["num_findings"] or 0; t[2] += r["num_studies"] or 0
                t[3] = max(t[3], r["last_published_date"] or "")
        for m in ms:
            for h in hs:
                t = concept_tot[("hm", h, m)]
                t[0] += 1; t[1] += r["num_findings"] or 0; t[2] += r["num_studies"] or 0
                t[3] = max(t[3], r["last_published_date"] or "")
    prow = []
    for d in DRUG_GROUPS:
        direct = set().union(*[s for (lg, a, b), s in leg.items() if lg == "drug_heat" and a == d] or [set()])
        for m in MEDIATORS:
            ds = leg.get(("drug_mediator", d, m), set())
            hs = heat_leg.get(m, set())
            ct = concept_tot[("dm", d, m)]
            hct = [concept_tot[("hm", h, m)] for h in HEAT]
            prow.append({"drug_group": d, "drug_label": DRUG_GROUPS[d]["label"], "in_15": d in DRUGS15, "mediator": m,
                         "drug_leg_findings": len(legf.get(("drug_mediator", d, m), set())), "drug_leg_studies": len(ds),
                         "heat_leg_studies": len(hs), "direct_drug_heat_studies": len(direct),
                         "concept_drug_leg_relationships": ct[0], "concept_drug_leg_findings": ct[1],
                         "concept_drug_leg_studies_summed": ct[2], "concept_drug_leg_newest": (ct[3] or "")[:10],
                         "concept_heat_leg_relationships": sum(x[0] for x in hct),
                         "concept_heat_leg_studies_summed": sum(x[2] for x in hct),
                         "score_sqrt_studies": round(math.sqrt(len(ds) * len(hs)), 3),
                         "untested": bool(ds and hs and not direct)})
    write_csv(os.path.join(PROC, "system_api_pathways.csv"), prow)

    # validation summary
    srow = []
    for d in DRUG_GROUPS:
        allst = set().union(*[s for (lg, a, b), s in leg.items() if lg == "drug_mediator" and a == d] or [set()])
        nonbp = set().union(*[s for (lg, a, b), s in leg.items() if lg == "drug_mediator" and a == d and b != "bp_hypotension"] or [set()])
        rows = [r for r in prow if r["drug_group"] == d]
        srow.append({"drug_group": d, "drug_label": DRUG_GROUPS[d]["label"], "in_15": d in DRUGS15,
                     "drug_mediator_studies_all": len(allst), "drug_mediator_studies_nonbp": len(nonbp),
                     "nonbp_share": round(len(nonbp) / len(allst), 3) if allst else 0.0,
                     "score_total": round(sum(r["score_sqrt_studies"] for r in rows), 3),
                     "score_nonbp": round(sum(r["score_sqrt_studies"] for r in rows if r["mediator"] != "bp_hypotension"), 3),
                     "concept_drug_mediator_studies_summed": sum(r["concept_drug_leg_studies_summed"] for r in rows),
                     "concept_drug_mediator_studies_nonbp": sum(r["concept_drug_leg_studies_summed"] for r in rows if r["mediator"] != "bp_hypotension"),
                     "direct_drug_heat_studies": rows[0]["direct_drug_heat_studies"] if rows else 0})
    for key in ("nonbp_share", "score_total", "score_nonbp", "concept_drug_mediator_studies_nonbp"):
        order = sorted(srow, key=lambda r: -r[key])
        for i, r in enumerate(order, 1):
            r["rank_" + key] = i
    write_csv(os.path.join(PROC, "system_api_pathway_drug_summary.csv"), sorted(srow, key=lambda r: r["rank_nonbp_share"]))
    print("validation (rank by non-BP share):")
    for r in sorted(srow, key=lambda r: r["rank_nonbp_share"]):
        print(f"  {r['rank_nonbp_share']:2d} {r['drug_group']:22s} share={r['nonbp_share']:.3f} nonbp={r['drug_mediator_studies_nonbp']} all={r['drug_mediator_studies_all']} rank_score_nonbp={r['rank_score_nonbp']}")
    json.dump({"n_concepts": len(concepts), "n_concepts_with_relationships": sum(1 for v in nrels.values() if v),
               "n_edges": len(rel_rows), "n_findings": len(findings), "n_matching_variables": len(var_hits),
               "or_filter_on_variable_ids": batch_ok, "client": c.stats()},
              open(os.path.join(API_DIR, "evidence_run_summary.json"), "w"), indent=1)
    print(c.stats())


if __name__ == "__main__":
    main()
