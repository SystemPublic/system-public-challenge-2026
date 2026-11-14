"""FAERS heat signals v2: robustness checks on the SPECIFIC heat composite.

WARNING SIGNAL, NOT PROOF. Same reaction composite, 2x2 table, ROR, signal rule and
negative-control cut-off as faers_heat_signals.py (v1). What is new:

  1. Every report in the specific composite (HEAT STROKE, HEAT EXHAUSTION, HEAT ILLNESS,
     ANHIDROSIS, HYPOHIDROSIS) is downloaded once (about 3,850 reports) and the numerators are
     counted locally, with the same phrase match on patient.drug[].openfda.generic_name that the
     API uses. Local counts are checked against v1's API counts.
  2. Strata (numerator AND denominator AND background all restricted the same way):
       all          all reports (v1 replication; drug totals come from the v1 cache)
       received_2015plus   receivedate >= 2015-01-01
       age_65plus   patient.patientonsetage >= 65 with unit = years (801)
       age_under18  onset age < 18 years (unit 801) or age given in months/weeks/days/hours (802-805)
       (an "all drugs suspect" stratum via NOT patient.drug.drugcharacterization:(2 3) was tested
        and dropped: openFDA ignores NOT, so the query returned all reports.)
     Plus one numerator-only variant that needs no extra calls:
       suspect_numerator_anyrole_denominator   a = composite reports where the index drug's own
                    drug entry has drugcharacterization = 1 (suspect) (exact, from the downloaded
                    reports); b = drug's any-role report total minus a. The denominator still counts
                    reports where the drug is only concomitant, so this ROR is biased toward 1
                    (conservative). openFDA cannot give a suspect-only denominator.
  3. Units: the 48 v1 ingredients, the 15 v1 pooled classes, and extra individual members of
     the 15 classes (EXTRA_INGREDIENTS) scored on their own (all strata where budget allows).
  4. Negative-control cut-off recomputed within each stratum (max upper 95% CI of amoxicillin,
     levothyroxine, atorvastatin in that stratum).

Usage: uv run python scripts/faers_heat_signals_v2.py [--api-key-from-env] [--max-calls N]
Output: data/processed/faers_heat_signals_v2.csv (long: one row per unit x stratum)
"""
import argparse, csv, math, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import openfda_common as oc  # noqa: E402
from openfda_common import INGREDIENTS, PROCESSED, get  # noqa: E402
from faers_heat_signals import EVENT, SPECIFIC_CLAUSE, SPECIFIC_PTS, drug_clause, ror, CAVEAT  # noqa: E402

EXTRA_INGREDIENTS = [
    ("loop diuretics", "ethacrynic acid"),
    ("thiazides", "metolazone"), ("thiazides", "chlorothiazide"),
    ("ACE inhibitors/ARBs", "benazepril"), ("ACE inhibitors/ARBs", "captopril"), ("ACE inhibitors/ARBs", "quinapril"),
    ("ACE inhibitors/ARBs", "fosinopril"), ("ACE inhibitors/ARBs", "perindopril"), ("ACE inhibitors/ARBs", "trandolapril"),
    ("ACE inhibitors/ARBs", "irbesartan"), ("ACE inhibitors/ARBs", "candesartan"), ("ACE inhibitors/ARBs", "telmisartan"),
    ("ACE inhibitors/ARBs", "azilsartan"), ("ACE inhibitors/ARBs", "sacubitril"),
    ("SGLT2 inhibitors", "ertugliflozin"), ("SGLT2 inhibitors", "sotagliflozin"), ("SGLT2 inhibitors", "bexagliflozin"),
    ("insulin (incl. pumps)", "insulin glargine"), ("insulin (incl. pumps)", "insulin lispro"), ("insulin (incl. pumps)", "insulin aspart"),
    ("insulin (incl. pumps)", "insulin detemir"), ("insulin (incl. pumps)", "insulin degludec"), ("insulin (incl. pumps)", "insulin glulisine"),
    ("insulin (incl. pumps)", "insulin human"),
    ("anticholinergics", "solifenacin"), ("anticholinergics", "darifenacin"), ("anticholinergics", "trospium"),
    ("anticholinergics", "fesoterodine"), ("anticholinergics", "glycopyrrolate"), ("anticholinergics", "scopolamine"),
    ("anticholinergics", "dicyclomine"), ("anticholinergics", "hyoscyamine"),
    ("antipsychotics", "ziprasidone"), ("antipsychotics", "lurasidone"), ("antipsychotics", "paliperidone"),
    ("antipsychotics", "chlorpromazine"), ("antipsychotics", "fluphenazine"), ("antipsychotics", "perphenazine"),
    ("antipsychotics", "asenapine"), ("antipsychotics", "brexpiprazole"), ("antipsychotics", "cariprazine"),
    ("antipsychotics", "loxapine"), ("antipsychotics", "thioridazine"),
    ("SSRIs", "fluvoxamine"), ("SSRIs", "vilazodone"),
    ("ADHD stimulants", "dextroamphetamine"), ("ADHD stimulants", "dexmethylphenidate"), ("ADHD stimulants", "methamphetamine"),
    ("beta blockers", "bisoprolol"), ("beta blockers", "nebivolol"), ("beta blockers", "nadolol"), ("beta blockers", "labetalol"),
    ("beta blockers", "sotalol"), ("beta blockers", "timolol"),
]
EXTRA_ROLE = {"anticholinergics": "positive_control", "antipsychotics": "positive_control"}

STRATA = [
    ("all", None),
    # ("all_drugs_suspect", "NOT patient.drug.drugcharacterization:(2 3)") was tried and DROPPED: openFDA
    # silently ignores NOT (stratum N = 21,054,159 and composite total = 3,850, identical to all reports;
    # sertraline total 222,021 with or without the NOT clause). There is no supported negation, so no
    # search pattern restricts the denominator to reports where the index drug is suspect.
    ("received_2015plus", "receivedate:[20150101 TO 20261231]"),
    ("age_65plus", "patient.patientonsetageunit:801 AND patient.patientonsetage:[65 TO 200]"),
    ("age_under18", "(patient.patientonsetageunit:(802 803 804 805) OR (patient.patientonsetageunit:801 AND patient.patientonsetage:[0 TO 17]))"),
]
TAG = "#faers-compact-v2"


def compact_reports(d):
    if d.get("not_found"):
        return d
    out = []
    for r in d.get("results", []):
        p = r.get("patient", {}) or {}
        out.append({
            "safetyreportid": r.get("safetyreportid"), "receivedate": r.get("receivedate"),
            "occurcountry": r.get("occurcountry"), "serious": r.get("serious"),
            "age": p.get("patientonsetage"), "age_unit": p.get("patientonsetageunit"), "sex": p.get("patientsex"),
            "pts": [x.get("reactionmeddrapt") for x in p.get("reaction", []) or []],
            "drugs": [{"char": x.get("drugcharacterization"), "product": x.get("medicinalproduct"),
                       "generic": (x.get("openfda") or {}).get("generic_name", [])} for x in p.get("drug", []) or []],
        })
    return {"meta": d.get("meta", {}), "results": out}


def download_composite(page):
    reps, skip = {}, 0
    while True:
        d = get(EVENT, {"search": SPECIFIC_CLAUSE, "limit": page, "skip": skip}, compact=compact_reports, compact_tag=TAG)
        total = d["meta"]["results"]["total"]
        for r in d["results"]:
            reps[r["safetyreportid"]] = r
        skip += page
        if not d["results"] or skip >= total:
            return list(reps.values()), total


def toks(s):
    return re.findall(r"[a-z0-9]+", (s or "").lower())


def phrase_in(term_toks, name):
    t = toks(name)
    n = len(term_toks)
    return any(t[i:i + n] == term_toks for i in range(len(t) - n + 1))


def in_stratum(r, stratum):
    if stratum == "all":
        return True
    if stratum == "received_2015plus":
        return (r.get("receivedate") or "") >= "20150101"
    try:
        age = int(float(r.get("age"))) if r.get("age") not in (None, "") else None
    except ValueError:
        age = None
    unit = str(r.get("age_unit") or "")
    if stratum == "age_65plus":
        return unit == "801" and age is not None and age >= 65
    if stratum == "age_under18":
        return unit in ("802", "803", "804", "805") or (unit == "801" and age is not None and 0 <= age <= 17)
    if stratum == "all_drugs_suspect":
        return not any(str(x.get("char")) in ("2", "3") for x in r["drugs"])
    raise ValueError(stratum)


def drug_match(r, terms, suspect_only=False):
    tt = [toks(t) for t in terms]
    for x in r["drugs"]:
        if suspect_only and str(x.get("char")) != "1":
            continue
        if any(phrase_in(t, g) for t in tt for g in x.get("generic") or []):
            return True
    return False


def total(search=None):
    p = {"limit": 1}
    if search:
        p["search"] = search
    d = get(EVENT, p)
    return 0 if d.get("not_found") else d["meta"]["results"]["total"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-key-from-env", action="store_true")
    ap.add_argument("--max-calls", type=int, default=100000)
    ap.add_argument("--page", type=int, default=999)  # keyless: limit=1000 returns 403
    ap.add_argument("--extras-all-strata", action="store_true",
                    help="also score EXTRA_INGREDIENTS in the restricted strata (costs 1 call per extra per stratum)")
    args = ap.parse_args()
    if args.api_key_from_env:
        print("api key:", "loaded" if oc.use_api_key_from_env() else "NOT FOUND, running keyless", file=sys.stderr)

    reps, comp_total = download_composite(args.page)
    print(f"downloaded {len(reps)} composite reports (API total {comp_total}) calls={oc.net_calls[0]}", file=sys.stderr)

    # units
    units = [(c, t, role, "ingredient", [t]) for c, t, role in INGREDIENTS]
    by_class, roles = defaultdict(list), {}
    for c, t, role in INGREDIENTS:
        by_class[c].append(t)
        roles[c] = role
    units += [(c, "ALL: " + "+".join(ts), roles[c], "class", ts) for c, ts in by_class.items()
              if len(ts) > 1 and roles[c] != "negative_control"]
    units += [(c, t, EXTRA_ROLE.get(c, "study"), "ingredient (v2 extra class member)", [t]) for c, t in EXTRA_INGREDIENTS]

    # v1 reference numerators (any role, all reports) for validation
    v1 = {}
    v1_path = os.path.join(PROCESSED, "faers_heat_signals.csv")
    if os.path.exists(v1_path):
        for r in csv.DictReader(open(v1_path)):
            if r["event"].startswith("HEAT COMPOSITE SPECIFIC"):
                v1[r["ingredient"]] = (int(r["n_cases"]), int(r["n_reports_drug"]))

    rows, budget_hit = [], False
    for sname, sclause in STRATA:
        try:
            n_total = total(sclause)
            n_event_api = total(SPECIFIC_CLAUSE + (" AND " + sclause if sclause else ""))
        except RuntimeError as e:
            print("stopping:", e, file=sys.stderr)
            break
        srep = [r for r in reps if in_stratum(r, sname)]
        print(f"[{sname}] N={n_total} composite API={n_event_api} local={len(srep)} calls={oc.net_calls[0]}", file=sys.stderr)
        variants = [(sname, False)] + ([("suspect_numerator_anyrole_denominator", True)] if sname == "all" else [])
        for cls, label, role, level, terms in units:
            if "extra" in level and sname != "all" and not args.extras_all_strata:
                continue
            dc = drug_clause(terms)
            n_drug = None
            if not budget_hit:
                try:
                    if oc.net_calls[0] >= args.max_calls:
                        raise RuntimeError("call budget exhausted")
                    n_drug = total(dc + (" AND " + sclause if sclause else ""))
                except RuntimeError as e:
                    print("stopping drug totals:", e, file=sys.stderr)
                    budget_hit = True
            for vname, susp in variants:
                a = sum(1 for r in srep if drug_match(r, terms, suspect_only=susp))
                a_any = a if not susp else None
                r_, lo, hi = ror(a, n_drug, n_event_api, n_total) if n_drug else (None, None, None)
                row = {"stratum": vname, "drug_class": cls, "ingredient": label, "level": level, "role": role,
                       "n_cases": a, "n_reports_drug": n_drug if n_drug is not None else "",
                       "n_reports_event": n_event_api, "n_reports_total": n_total,
                       "ror": f"{r_:.3f}" if r_ else "", "ror_ci_low": f"{lo:.3f}" if lo else "", "ror_ci_high": f"{hi:.3f}" if hi else "",
                       "signal": "yes" if (r_ and a >= 3 and lo > 1) else "no"}
                if vname == "all" and label in v1:
                    row["v1_n_cases"], row["v1_n_reports_drug"] = v1[label]
                else:
                    row["v1_n_cases"], row["v1_n_reports_drug"] = "", ""
                if vname == "all":
                    a_s = sum(1 for r in srep if drug_match(r, terms, suspect_only=True))
                    row["n_cases_drug_suspect"] = a_s
                    row["pct_cases_drug_suspect"] = f"{100 * a_s / a:.1f}" if a else ""
                else:
                    row["n_cases_drug_suspect"], row["pct_cases_drug_suspect"] = "", ""
                rows.append(row)
        print(f"  done {sname} calls={oc.net_calls[0]}", file=sys.stderr)

    band = {}
    for r in rows:
        if r["role"] == "negative_control" and r["ror_ci_high"]:
            band[r["stratum"]] = max(band.get(r["stratum"], 0), float(r["ror_ci_high"]))
    for r in rows:
        b = band.get(r["stratum"])
        r["neg_control_band_max"] = f"{b:.3f}" if b else ""
        r["above_neg_control_band"] = "yes" if (r["signal"] == "yes" and b and float(r["ror_ci_low"]) > b) else "no"
        r["event"] = "HEAT COMPOSITE SPECIFIC (" + ", ".join(SPECIFIC_PTS) + ")"
        r["caveat"] = CAVEAT

    with open(os.path.join(PROCESSED, "faers_heat_signals_v2.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    mism = [(r["ingredient"], r["n_cases"], r["v1_n_cases"]) for r in rows if r["stratum"] == "all" and r["v1_n_cases"] != "" and r["n_cases"] != r["v1_n_cases"]]
    print(f"validation: local vs v1 API numerator mismatches: {mism}", file=sys.stderr)
    print(f"neg-control bands: {band}  network_calls={oc.net_calls[0]}", file=sys.stderr)


if __name__ == "__main__":
    main()
