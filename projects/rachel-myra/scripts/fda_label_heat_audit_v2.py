"""FDA label audit v2: EVERY current prescription label per ingredient (not a 10-label sample).

Same sentence classifier as v1 (imported from fda_label_heat_audit.py), but:
  - pages through all openFDA drug/label.json results for each ingredient query
    (same queries and route overrides as v1), so generics and relabelers are included;
  - single-moiety labels are the primary denominator. A label counts as a combination only
    if its generic name names another active moiety (so mixed amphetamine salts and
    premixed insulins count as single-moiety, unlike v1);
  - reports, per ingredient, the share of labels whose best tier is "heat warning", and
    puts each ingredient in: heat warning on most (>50%) labels / on some labels / on none;
  - verifies three pitch claims across the WHOLE label text (all openFDA text fields):
    (a) insulin and epinephrine labels mention heat only for product storage,
    (b) no clozapine label has the "Body Temperature Regulation" section other antipsychotics carry,
    (c) no tolterodine label mentions heat or sweating.

Cache: label pages are large, so each page is compacted before caching (see compact_page):
the 12 audited sections are kept in full; every other text field keeps only sentences that
match a broad heat/temperature/sweat pattern. Cache key = key-free URL + '#label-compact-v2'.

Usage:
  uv run python scripts/fda_label_heat_audit_v2.py [--api-key-from-env] [--page-size 300]
Outputs:
  data/processed/fda_label_heat_audit_v2.csv          one row per label (all labels)
  data/processed/fda_label_heat_audit_summary_v2.csv  one row per ingredient
  data/processed/fda_label_heat_claims_v2.csv         every heat/sweat sentence behind claims (a)-(c)
  data/raw/openfda/label_audit_summary_v2.txt          headline text
"""
import argparse, csv, os, re, sys, time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import openfda_common as oc  # noqa: E402
import fda_label_heat_audit as v1  # noqa: E402
from openfda_common import INGREDIENTS, PROCESSED, RAW, get  # noqa: E402
from fda_label_heat_audit import (LABEL, SECTIONS, SEARCH_OVERRIDE, TIER_ORDER, TIER_LABEL, SENT_SPLIT,  # noqa: E402
                                  ENV_HEAT, STORAGE_SENT, PRODUCT_PROTECT, classify_label)

TAG = "#label-compact-v2"

# v2 fix: "dehydrated alcohol" is an excipient (ethanol), not dehydration. v1's SWEAT_FLUID matched it
# (e.g. tolterodine capsules). Patch the shared regex so classify_label() ignores it.
v1.SWEAT_FLUID = re.compile(v1.SWEAT_FLUID.pattern.replace(r"dehydrat\w*", r"dehydrat(?!ed alcohol)\w*"), re.I)
SWEAT_FLUID = v1.SWEAT_FLUID
BROAD = re.compile(r"heat|\bhot\b|warm|temperat|sweat|perspir|hidrosis|hyperthermi|hyperpyrexi|dehydrat|sauna|"
                   r"thermoregulat|overheat", re.I)
OF_KEEP = ["generic_name", "brand_name", "manufacturer_name", "product_type", "route", "application_number", "spl_set_id"]
SKIP_FIELDS = {"openfda", "id", "set_id", "version", "effective_time"}


def compact_label(l):
    out = {k: l.get(k) for k in ("id", "set_id", "version", "effective_time")}
    out["openfda"] = {k: l.get("openfda", {}).get(k) for k in OF_KEEP if l.get("openfda", {}).get(k)}
    for s in SECTIONS:
        if l.get(s):
            out[s] = l[s]
    other = {}
    for k, v in l.items():
        if k in SKIP_FIELDS or k in SECTIONS or k.endswith("_table"):
            continue
        texts = v if isinstance(v, list) else [v]
        hits = []
        for t in texts:
            if not isinstance(t, str):
                continue
            for sent in SENT_SPLIT.split(t):
                s = " ".join(sent.split())
                if BROAD.search(s):
                    hits.append(s)
        if hits:
            other[k] = hits
    out["_other_field_sentences"] = other
    out["_fields"] = sorted(k for k in l.keys())
    return out


def compact_page(d):
    if d.get("not_found"):
        return d
    return {"meta": d.get("meta", {}), "results": [compact_label(l) for l in d.get("results", [])]}


def fetch_all(q, page_size):
    labs, skip, total = [], 0, None
    while True:
        d = get(LABEL, {"search": q, "limit": page_size, "skip": skip}, compact=compact_page, compact_tag=TAG)
        if d.get("not_found"):
            return [], 0
        total = d["meta"]["results"]["total"]
        res = d.get("results", [])
        labs += res
        skip += page_size
        if not res or skip >= total:
            break
    return labs, total


def moieties(generic):
    return [p.strip() for p in re.split(r",|/| AND | WITH ", generic.upper()) if p.strip()]


def is_combination(lab, term):
    names = lab.get("openfda", {}).get("generic_name") or [""]
    t = term.upper()
    return any(any(t not in p for p in moieties(g)) for g in names)


def all_sentences(lab):
    """(field, sentence) for every sentence in the compacted label: full audited sections + other-field hits."""
    for s in SECTIONS:
        for block in lab.get(s, []) or []:
            for sent in SENT_SPLIT.split(block):
                yield s, " ".join(sent.split())
    for f, sents in (lab.get("_other_field_sentences") or {}).items():
        for s in sents:
            yield f, s


HEAT_ANY = re.compile(r"\bheat|\bhot\b|warm weather|sauna|overheat|thermoregulat|body temperature|"
                      r"hidrosis|hyperthermi|hyperpyrexi", re.I)
BTR = re.compile(r"body temperature regulation|regulat\w* (?:of )?(?:core )?body temperature|core body temperature", re.I)
STORAGE_FIELDS = {"storage_and_handling", "how_supplied", "package_label_principal_display_panel",
                  "spl_unclassified_section", "instructions_for_use"}


def storage_like(field, s):
    return bool(PRODUCT_PROTECT.search(s) or STORAGE_SENT.search(s)) or field in ("storage_and_handling", "how_supplied",
                                                                                  "package_label_principal_display_panel")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-key-from-env", action="store_true", help="send OPENFDA_API_KEY (env or .env.local)")
    ap.add_argument("--page-size", type=int, default=300)
    args = ap.parse_args()
    if args.api_key_from_env:
        print("api key:", "loaded" if oc.use_api_key_from_env() else "NOT FOUND, running keyless", file=sys.stderr)

    rows, summary, claims = [], [], []
    labels_by_term = {}
    for cls, term, role in INGREDIENTS:
        q = SEARCH_OVERRIDE.get(term, f'openfda.generic_name:"{term}"') + ' AND openfda.product_type:"HUMAN PRESCRIPTION DRUG"'
        try:
            labs, total = fetch_all(q, args.page_size)
        except RuntimeError as e:
            print("stopping:", e, file=sys.stderr)
            break
        # de-duplicate by set_id (keep latest effective_time)
        by_set = {}
        for l in labs:
            k = l.get("set_id") or l.get("id")
            if k not in by_set or (l.get("effective_time") or "") > (by_set[k].get("effective_time") or ""):
                by_set[k] = l
        labs = list(by_set.values())
        labels_by_term[term] = labs
        stats = {"single": Counter(), "combo": Counter()}
        distinct = {"single": {}, "combo": {}}
        best = {"single": ("none", None), "combo": ("none", None)}
        for l in labs:
            of = l.get("openfda", {})
            combo = is_combination(l, term)
            grp = "combo" if combo else "single"
            hits = classify_label(l)
            tier = next((t for t in TIER_ORDER if t in hits), "none")
            stats[grp][tier] += 1
            dkey = tuple((l.get(s) or [""])[0][:400] for s in ("warnings_and_cautions", "warnings", "how_supplied"))
            if TIER_ORDER.index(tier) < TIER_ORDER.index(distinct[grp].get(dkey, "none")) or dkey not in distinct[grp]:
                distinct[grp][dkey] = tier
            if best[grp][1] is None or TIER_ORDER.index(tier) < TIER_ORDER.index(best[grp][0]):
                best[grp] = (tier, (l.get("set_id", ""), hits.get(tier, ("", ""))))
            row = {"drug_class": cls, "ingredient": term, "role": role, "set_id": l.get("set_id", ""), "spl_id": l.get("id", ""),
                   "version": l.get("version", ""), "effective_time": l.get("effective_time", ""),
                   "generic_name": "; ".join(of.get("generic_name", []) or []), "brand_name": "; ".join(of.get("brand_name", []) or []),
                   "manufacturer": "; ".join(of.get("manufacturer_name", []) or []),
                   "application_number": "; ".join(of.get("application_number", []) or []),
                   "combination_product": "yes" if combo else "no", "label_tier": TIER_LABEL[tier],
                   "heat_warning": "yes" if tier == "env_heat" else "no"}
            for cat, col in (("env_heat", "heat_warning"), ("hyperthermia", "incidental"), ("sweat_fluid", "sweat_fluid"), ("storage", "storage")):
                row[col + "_section"] = hits[cat][0] if cat in hits else ""
                row[col + "_snippet"] = hits[cat][1] if cat in hits else ""
            rows.append(row)

        def grp_stats(g):
            n = sum(stats[g].values())
            nh = stats[g]["env_heat"]
            nd = len(distinct[g])
            ndh = sum(1 for t in distinct[g].values() if t == "env_heat")
            share = nh / n if n else None
            three = ("no labels" if not n else "heat warning on most labels (>50%)" if share > 0.5 else
                     "heat warning on some labels (<=50%)" if nh else "heat warning on no label")
            return n, nh, share, nd, ndh, three

        n_s, nh_s, sh_s, nd_s, ndh_s, three_s = grp_stats("single")
        n_c, nh_c, sh_c, _, _, three_c = grp_stats("combo")
        primary = "single" if n_s else "combo"
        n_p, nh_p, sh_p, _, _, three_p = grp_stats(primary)
        bt, bex = best[primary]
        summary.append({
            "drug_class": cls, "ingredient": term, "role": role, "label_query": q, "n_labels_api_total": total,
            "n_labels_audited": len(labs), "n_single_moiety": n_s, "n_combination": n_c,
            "primary_denominator": "single-moiety" if primary == "single" else "combination (no single-moiety label)",
            "n_heat_warning": nh_p, "pct_heat_warning": f"{100 * sh_p:.1f}" if sh_p is not None else "",
            "n_incidental_only": stats[primary]["hyperthermia"], "n_sweat_fluid_only": stats[primary]["sweat_fluid"],
            "n_storage_only": stats[primary]["storage"], "n_nothing": stats[primary]["none"],
            "n_distinct_texts": nd_s if primary == "single" else len(distinct["combo"]),
            "n_distinct_texts_heat_warning": ndh_s if primary == "single" else sum(1 for t in distinct["combo"].values() if t == "env_heat"),
            "coverage_class": three_p,
            "best_tier": TIER_LABEL[bt] if n_p else "no label found",
            "example_set_id": bex[0] if bex else "", "example_section": bex[1][0] if bex else "", "example_snippet": bex[1][1] if bex else "",
            "combo_n_heat_warning": nh_c, "combo_pct_heat_warning": f"{100 * sh_c:.1f}" if sh_c is not None else "",
            "v1_sample_note": "v1 audited <=10 most recent distinct labels",
        })
        print(f"{term:20s} total={total:4d} audited={len(labs):4d} single={n_s:4d} heat={nh_s:4d} combo={n_c:4d} heat_c={nh_c:3d} calls={oc.net_calls[0]}",
              file=sys.stderr)

    # ---- Claims across the whole label text ----
    claim_lines = []
    # (a) insulin and epinephrine: every heat sentence anywhere; is it storage/product protection?
    for term in ("insulin", "epinephrine"):
        labs = labels_by_term.get(term, [])
        n_lab_heat, n_clin = 0, 0
        for l in labs:
            any_heat = False
            for f, s in all_sentences(l):
                if not ENV_HEAT.search(s):
                    continue
                any_heat = True
                kind = "storage/product protection" if storage_like(f, s) else "NOT storage (check)"
                if kind != "storage/product protection":
                    n_clin += 1
                claims.append({"claim": f"(a) {term}: heat mentioned only for product storage", "ingredient": term,
                               "set_id": l.get("set_id"), "effective_time": l.get("effective_time"),
                               "generic_name": "; ".join(l.get("openfda", {}).get("generic_name", []) or []),
                               "brand_name": "; ".join(l.get("openfda", {}).get("brand_name", []) or []),
                               "manufacturer": "; ".join(l.get("openfda", {}).get("manufacturer_name", []) or []),
                               "field": f, "classification": kind, "sentence": s[:600]})
            n_lab_heat += any_heat
        claim_lines.append(f"(a) {term}: {len(labs)} labels; {n_lab_heat} mention heat somewhere; "
                           f"{n_clin} heat sentences not recognised as storage/product protection (see claims CSV).")
    # (b) clozapine vs other antipsychotics: body temperature regulation language
    for term in ("clozapine", "olanzapine", "haloperidol", "risperidone", "quetiapine", "aripiprazole"):
        labs = labels_by_term.get(term, [])
        n_btr = 0
        for l in labs:
            hit = [(f, s) for f, s in all_sentences(l) if BTR.search(s)]
            if hit:
                n_btr += 1
            if term == "clozapine":
                heat = [(f, s) for f, s in all_sentences(l) if HEAT_ANY.search(s)]
                for f, s in (hit or heat):
                    claims.append({"claim": "(b) clozapine: no Body Temperature Regulation section", "ingredient": term,
                                   "set_id": l.get("set_id"), "effective_time": l.get("effective_time"),
                                   "generic_name": "; ".join(l.get("openfda", {}).get("generic_name", []) or []),
                                   "brand_name": "; ".join(l.get("openfda", {}).get("brand_name", []) or []),
                                   "manufacturer": "; ".join(l.get("openfda", {}).get("manufacturer_name", []) or []),
                                   "field": f, "classification": "BODY TEMPERATURE REGULATION TEXT" if hit else "other heat/temperature sentence",
                                   "sentence": s[:600]})
                if not hit and not heat:
                    claims.append({"claim": "(b) clozapine: no Body Temperature Regulation section", "ingredient": term,
                                   "set_id": l.get("set_id"), "effective_time": l.get("effective_time"),
                                   "generic_name": "; ".join(l.get("openfda", {}).get("generic_name", []) or []),
                                   "brand_name": "", "manufacturer": "; ".join(l.get("openfda", {}).get("manufacturer_name", []) or []),
                                   "field": "", "classification": "no heat/temperature sentence", "sentence": ""})
        claim_lines.append(f"(b) {term}: {n_btr} of {len(labs)} labels contain body-temperature-regulation language.")
    # (c) tolterodine: any heat or sweating sentence anywhere
    labs = labels_by_term.get("tolterodine", [])
    n_hit = 0
    for l in labs:
        hit = [(f, s) for f, s in all_sentences(l) if HEAT_ANY.search(s) or SWEAT_FLUID.search(s)
               or (BROAD.search(s) and not re.search(r"dehydrated alcohol", s, re.I))]
        n_hit += any(HEAT_ANY.search(s) and not storage_like(f, s) or SWEAT_FLUID.search(s) for f, s in hit)
        for f, s in hit:
            claims.append({"claim": "(c) tolterodine: no heat or sweating language", "ingredient": "tolterodine",
                           "set_id": l.get("set_id"), "effective_time": l.get("effective_time"),
                           "generic_name": "; ".join(l.get("openfda", {}).get("generic_name", []) or []),
                           "brand_name": "; ".join(l.get("openfda", {}).get("brand_name", []) or []),
                           "manufacturer": "; ".join(l.get("openfda", {}).get("manufacturer_name", []) or []),
                           "field": f, "classification": ("storage" if storage_like(f, s) else
                                                          "HEAT/SWEAT (clinical)" if (HEAT_ANY.search(s) or SWEAT_FLUID.search(s)) else "other temperature/warm"),
                           "sentence": s[:600]})
    claim_lines.append(f"(c) tolterodine: {n_hit} of {len(labs)} labels have a non-storage heat or sweating sentence.")

    # The same sentence can recur within one label field (e.g. insulin storage lines); keep one copy.
    claims = list({tuple(c.values()): c for c in claims}.values())

    os.makedirs(PROCESSED, exist_ok=True)
    for name, data in [("fda_label_heat_audit_v2.csv", rows), ("fda_label_heat_audit_summary_v2.csv", summary),
                       ("fda_label_heat_claims_v2.csv", claims)]:
        if not data:
            continue
        with open(os.path.join(PROCESSED, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)

    lines = []
    for scope, keep in [("heat-risk ingredients (study + positive controls)", ("study", "positive_control")),
                        ("negative-control ingredients", ("negative_control",))]:
        s = [r for r in summary if r["role"] in keep and r["n_labels_audited"]]
        nw = [r for r in s if r["n_heat_warning"] == 0]
        lines.append(f"{len(nw)} of {len(s)} {scope} carry no explicit heat warning on ANY of their current labels "
                     f"({sum(r['n_labels_audited'] for r in s)} labels audited).")
        for t in ("heat warning on most labels (>50%)", "heat warning on some labels (<=50%)", "heat warning on no label"):
            names = [f"{r['ingredient']} ({r['n_heat_warning']}/{r['n_single_moiety'] or r['n_combination']})" for r in s if r["coverage_class"] == t]
            lines.append(f"  {t}: {len(names)}  {', '.join(names)}")
        lines.append("  [best tier on any label]")
        for t in TIER_ORDER:
            names = [r["ingredient"] for r in s if r["best_tier"] == TIER_LABEL[t]]
            lines.append(f"  {TIER_LABEL[t]}: {len(names)}  {', '.join(names)}")
    classes = {}
    for r in summary:
        if r["role"] in ("study", "positive_control") and r["n_labels_audited"]:
            classes.setdefault(r["drug_class"], []).append(r["n_heat_warning"] > 0)
    lines.append(f"By class: {sum(1 for v in classes.values() if not any(v))} of {len(classes)} classes have no ingredient with a heat warning on any label: "
                 + ", ".join(c for c, v in classes.items() if not any(v)))
    lines.append("Claims (whole label text, all openFDA fields):")
    lines += ["  " + c for c in claim_lines]
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(RAW, "label_audit_summary_v2.txt"), "w") as f:
        f.write(f"openFDA drug/label.json audit v2 (all current labels), run {time.strftime('%Y-%m-%d')}. "
                "Label text check, not a legal review.\n" + txt + "\n")


if __name__ == "__main__":
    main()
