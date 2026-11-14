#!/usr/bin/env python
"""Research evidence in the System Public Graph for a pair of concepts.

Given two concepts, by System id or by search term, this tool collects every
association (finding) that links them in either order, from two sources:

  CSV   the Dataverse deposit doi:10.7910/DVN/7V6JDO (v2.1), loaded into DuckDB
        at ~/opt/nyc-concordance/dataverse/graph.duckdb by
        analyses/graph_audit/build_dataverse.py. This is the quality-filtered set.
  API   the System Public Graph API v1.0, GET /v1/relationships/{a|b}/associations
        (cached by concord/sysgraph.py). The API also serves associations that
        were removed from the CSV as mis-extracted; the documentation says to
        drop API associations absent from the CSV. Each row says `in_csv`.

For each association it reports the statistic type and value, the interval,
the p-value, the study DOI and PubMed id, and a normalised direction:

  direction   "+" or "-" relative to the null of the statistic: 1 for ratio
              statistics (odds, hazard, risk, rate and prevalence ratios), 0 for
              coefficients, correlations, differences and elasticities. None
              for statistics with no sign (R^2, Gini) or a missing value.
  significant True if the interval excludes the null, else (no interval) if
              p < 0.05; None if neither is reported.
  flags       data checks: ratio_nonpositive, estimate_outside_ci,
              ci_reversed, sign_depends_on_group_order (mean and risk
              differences, whose sign depends on which group is subtracted;
              read the variable names, which often say "[vs ...]").

The direction is the sign of the association between the two variables as
named. It is not yet the direction between the concepts: a variable named
"lack of green space" is grounded to "green space", so read the names.

Usage:
  graph_evidence.py A B [options]

  A and B are System concept ids (e.g. k9BAffdSqv) or search terms ("heat wave").
  A term is matched against concept labels, then aliases, case-insensitively;
  exact matches win. With --expand, every concept whose label contains the
  term as a whole word is included (e.g. "asthma" adds "childhood asthma").

Options:
  --expand            include every concept whose label contains the term
  --offline           CSV only; no API calls
  --api-only          skip the CSV (in_csv is then null)
  --csv-only-rows     drop API rows absent from the CSV from the output
  --json PATH         where to write JSON ("-" for stdout). Default:
                      data/derived/graph_audit/evidence/<a>__<b>.json
  --max-pairs N       cap on concept pairs queried through the API (default 12)
  --rows N            rows to print in the summary table (default 15)
  --quiet             write JSON, print one line

Examples:
  ~/.venvs/nyc-concordance/bin/python tools/graph_evidence.py "air pollution" asthma
  ~/.venvs/nyc-concordance/bin/python tools/graph_evidence.py X7hfhwez9f "temperature" --expand
  ~/.venvs/nyc-concordance/bin/python tools/graph_evidence.py "green space" "heat stroke" --offline --json -

From Python:
  import sys; sys.path.insert(0, "tools"); from graph_evidence import evidence
  ev = evidence("air pollution", "asthma")   # dict, same shape as the JSON

API cost: one call per concept pair and order (two per pair) when uncached,
plus one call per term that is resolved through the API because the DuckDB
file is missing.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB = Path.home() / "opt" / "nyc-concordance" / "dataverse" / "graph.duckdb"
DEFAULT_OUT = ROOT / "data" / "derived" / "graph_audit" / "evidence"
DATAVERSE = {"doi": "doi:10.7910/DVN/7V6JDO", "url": "https://doi.org/10.7910/DVN/7V6JDO"}

RATIO = {"odds_ratio", "adjusted_odds_ratio", "hazard_ratio", "adjusted_hazard_ratio",
         "relative_risk_ratio", "incident_rate_ratio", "prevalence_ratio"}
SIGNED = {"coefficient", "pearson_r", "spearman_correlation", "mean_difference_unstandardized",
          "mean_difference_standardized", "risk_difference", "elasticity", "t_test"}
UNSIGNED = {"coefficient_of_determination", "gini_coefficient"}
GROUP_ORDER = {"mean_difference_unstandardized", "mean_difference_standardized", "risk_difference", "t_test"}
ID_RE = re.compile(r"^[A-Za-z0-9_-]{10}$")


# --------------------------------------------------------------------------- data access

def _db():
    if not DB.exists():
        return None
    import duckdb
    return duckdb.connect(str(DB), read_only=True)


def _db_provenance(con) -> dict:
    if con is None:
        return {}
    kv = dict(con.execute("SELECT key, value FROM provenance").fetchall())
    files = {f["filename"]: f for f in json.loads(kv.get("files", "[]"))}
    a = files.get("system-public-graph-v1-associations.csv", {})
    return {**DATAVERSE, "version": kv.get("version"), "release_time": kv.get("release_time"),
            "license": kv.get("license"), "associations_sha256": a.get("sha256"),
            "associations_md5": a.get("md5"), "loaded_at": kv.get("loaded_at")}


def resolve(term: str, con, expand: bool = False) -> list[dict]:
    """Resolve an id or a search term to a list of concepts {system_id, label, wikidata_id}."""
    if con is not None:
        if ID_RE.match(term):
            r = con.execute("SELECT system_id, wikidata_label, wikidata_id FROM concepts WHERE system_id = ?",
                            [term]).fetchall()
            if r:
                return [{"system_id": x[0], "label": x[1], "wikidata_id": x[2], "match": "id"} for x in r]
        t = term.lower().strip()
        exact = con.execute("SELECT system_id, wikidata_label, wikidata_id FROM concepts WHERE lower(wikidata_label) = ?",
                            [t]).fetchall()
        out = [{"system_id": x[0], "label": x[1], "wikidata_id": x[2], "match": "label"} for x in exact]
        if not out:
            # aliases are stored as a JSON-like list string
            al = con.execute("SELECT system_id, wikidata_label, wikidata_id, wikidata_aliases FROM concepts "
                             "WHERE lower(wikidata_aliases) LIKE ?", [f"%{t}%"]).fetchall()
            for x in al:
                try:
                    aliases = [s.lower() for s in json.loads(x[3])]
                except (TypeError, ValueError):
                    aliases = []
                if t in aliases:
                    out.append({"system_id": x[0], "label": x[1], "wikidata_id": x[2], "match": "alias"})
        if expand or not out:
            pat = r"(^|[^a-z0-9])" + re.escape(t) + r"([^a-z0-9]|$)"
            word = con.execute("SELECT system_id, wikidata_label, wikidata_id FROM concepts "
                               "WHERE regexp_matches(lower(wikidata_label), ?) ORDER BY length(wikidata_label)",
                               [pat]).fetchall()
            have = {o["system_id"] for o in out}
            extra = [{"system_id": x[0], "label": x[1], "wikidata_id": x[2], "match": "word"}
                     for x in word if x[0] not in have]
            out += extra if expand else extra[:1]
        return out
    # no local copy: use the API
    from concord import sysgraph
    if ID_RE.match(term):
        d = sysgraph.concept(term)
        if d.get("system_id"):
            return [{"system_id": d["system_id"], "label": d.get("wikidata_label"),
                     "wikidata_id": d.get("wikidata_id"), "match": "id"}]
    rows = sysgraph.concepts(term, limit=50)
    exact = [r for r in rows if (r.get("wikidata_label") or "").lower() == term.lower()]
    pick = rows if expand else (exact or rows[:1])
    return [{"system_id": r["system_id"], "label": r.get("wikidata_label"), "wikidata_id": r.get("wikidata_id"),
             "match": "api"} for r in pick]


# --------------------------------------------------------------------------- normalisation

def _f(x):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


def normalise(a: dict) -> dict:
    st = a.get("system_statistic_type")
    v, lo, hi, p = _f(a.get("statistic_value")), _f(a.get("ci_lower")), _f(a.get("ci_upper")), _f(a.get("p_value"))
    null = 1.0 if st in RATIO else 0.0 if st in SIGNED else None
    flags = []
    direction = None
    if null is not None and v is not None:
        if st in RATIO and v <= 0:
            flags.append("ratio_nonpositive")
        elif v > null:
            direction = "+"
        elif v < null:
            direction = "-"
    if lo is not None and hi is not None:
        if lo > hi:
            flags.append("ci_reversed")
        elif v is not None and not (lo - 1e-9 <= v <= hi + 1e-9):
            flags.append("estimate_outside_ci")
    if st in GROUP_ORDER:
        flags.append("sign_depends_on_group_order")
    significant = None
    if null is not None and lo is not None and hi is not None and lo <= hi:
        significant = not (lo <= null <= hi)
    elif p is not None:
        eq = (a.get("p_value_equality") or "=").strip()
        significant = p < 0.05 if eq in ("=", "<", "<=", "") else (False if eq in (">", ">=") else None)
    return {"null": null, "direction": direction, "significant": significant, "flags": flags,
            "ci_level": _f(a.get("ci_level")), "ci_lower": lo, "ci_upper": hi, "p_value": p,
            "statistic_value": v}


# --------------------------------------------------------------------------- collection

ASSOC_COLS = ["system_id", "pubmed_id", "study_id", "statistic_type", "system_statistic_type", "statistic_value",
              "ci_level", "ci_lower", "ci_upper", "p_value", "p_value_equality", "variable_1_id", "variable_2_id",
              "variable_1_concept_id", "variable_2_concept_id", "variable_1_name", "variable_2_name"]


def _csv_assocs(con, A: list[str], B: list[str]) -> list[dict]:
    q = (f"SELECT {', '.join('a.' + c for c in ASSOC_COLS)}, s.doi, s.population_string, s.study_type "
         "FROM associations a LEFT JOIN studies s ON s.study_id = a.study_id "
         "WHERE (a.variable_1_concept_id IN (SELECT unnest(?)) AND a.variable_2_concept_id IN (SELECT unnest(?))) "
         "   OR (a.variable_1_concept_id IN (SELECT unnest(?)) AND a.variable_2_concept_id IN (SELECT unnest(?)))")
    cur = con.execute(q, [A, B, B, A])
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def _csv_relationships(con, A, B) -> list[dict]:
    q = ("SELECT relationship_id, num_findings, num_studies, CAST(last_published_date AS VARCHAR), "
         "CAST(last_updated AS VARCHAR), \"source_concept.wikidata_label\", \"target_concept.wikidata_label\" "
         "FROM relationships WHERE (\"source_concept.system_id\" IN (SELECT unnest(?)) AND \"target_concept.system_id\" IN (SELECT unnest(?))) "
         "OR (\"source_concept.system_id\" IN (SELECT unnest(?)) AND \"target_concept.system_id\" IN (SELECT unnest(?)))")
    rows = con.execute(q, [A, B, B, A]).fetchall()
    return [{"relationship_id": r[0], "num_findings": r[1], "num_studies": r[2], "last_published_date": r[3],
             "last_updated": r[4], "source": r[5], "target": r[6], "from": "csv"} for r in rows]


def _study_lookup(con, ids: list[str]) -> dict:
    if con is None or not ids:
        return {}
    cur = con.execute("SELECT study_id, doi, population_string, study_type FROM studies WHERE study_id IN (SELECT unnest(?))", [ids])
    return {r[0]: {"doi": r[1], "population_string": r[2], "study_type": r[3]} for r in cur.fetchall()}


def evidence(a: str, b: str, *, expand: bool = False, offline: bool = False, api_only: bool = False,
             csv_only_rows: bool = False, max_pairs: int = 12) -> dict:
    """Collect the evidence for concepts a and b (ids or search terms). Returns a dict."""
    con = None if api_only else _db()
    CA, CB = resolve(a, con, expand), resolve(b, con, expand)
    if not CA or not CB:
        return {"query": {"a": a, "b": b}, "error": f"no concept found for {'a' if not CA else 'b'}",
                "concepts_a": CA, "concepts_b": CB}
    A, B = [c["system_id"] for c in CA], [c["system_id"] for c in CB]
    rows: dict[str, dict] = {}
    rels: list[dict] = []
    api_calls = 0
    if con is not None:
        for r in _csv_assocs(con, A, B):
            r["in_csv"], r["in_api"] = True, None
            rows[r["system_id"]] = r
        rels += _csv_relationships(con, A, B)
    api_meta = None
    if not offline:
        from concord import sysgraph
        pairs = [(x, y) for x in A for y in B][:max_pairs]
        csv_ids = set(rows)
        for x, y in pairs:
            for rid in (f"{x}|{y}", f"{y}|{x}"):
                rel = sysgraph.relationship(rid)
                api_calls += 1
                if not rel or rel.get("error") or not rel.get("relationship_id"):
                    continue
                rels.append({"relationship_id": rid, "num_findings": rel.get("num_findings"),
                             "num_studies": rel.get("num_studies"), "last_published_date": rel.get("last_published_date"),
                             "last_updated": rel.get("last_updated"),
                             "source": rel.get("source_concept", {}).get("wikidata_label"),
                             "target": rel.get("target_concept", {}).get("wikidata_label"), "from": "api"})
                assoc = sysgraph.relationship_associations(rid)
                api_calls += 1 + len(assoc) // 100  # pages of 100
                for r in assoc:
                    if r["system_id"] in rows:
                        rows[r["system_id"]]["in_api"] = True
                    else:
                        r = {k: r.get(k) for k in ASSOC_COLS}
                        r["in_api"] = True
                        r["in_csv"] = (r["system_id"] in csv_ids) if con is not None else None
                        rows[r["system_id"]] = r
        for r in rows.values():
            if r.get("in_api") is None:
                r["in_api"] = False
        missing = [r["study_id"] for r in rows.values() if r.get("study_id") and "doi" not in r]
        info = _study_lookup(con, missing)
        for r in rows.values():
            if "doi" not in r:
                r.update(info.get(r.get("study_id"), {"doi": None, "population_string": None, "study_type": None}))
        api_meta = {"base": sysgraph.BASE, "api_version": sysgraph.API_VERSION, "pairs_queried": len(pairs),
                    "pairs_total": len(A) * len(B), "requests_including_cached": api_calls}
    out_rows = []
    setA = set(A)
    for r in rows.values():
        if csv_only_rows and r.get("in_csv") is False:
            continue
        n = normalise(r)
        out_rows.append({
            "association_id": r["system_id"],
            "orientation": "a->b" if r.get("variable_1_concept_id") in setA else "b->a",
            "variable_1": r.get("variable_1_name"), "variable_2": r.get("variable_2_name"),
            "variable_1_concept_id": r.get("variable_1_concept_id"), "variable_2_concept_id": r.get("variable_2_concept_id"),
            "statistic_type": (r.get("statistic_type") or "").strip() or None,
            "system_statistic_type": r.get("system_statistic_type"),
            **n,
            "p_value_equality": r.get("p_value_equality"),
            "in_csv": r.get("in_csv"), "in_api": r.get("in_api"),
            "study_id": r.get("study_id"), "pubmed_id": r.get("pubmed_id"), "doi": r.get("doi"),
            "population": r.get("population_string"), "study_type": r.get("study_type"),
        })
    out_rows.sort(key=lambda x: (x["in_csv"] is False, str(x["system_statistic_type"]), str(x["association_id"])))
    return {
        "query": {"a": a, "b": b, "expand": expand, "offline": offline},
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "concepts_a": CA, "concepts_b": CB,
        "sources": {"dataverse": _db_provenance(con) or None, "api": api_meta},
        "relationships": rels,
        "summary": summarise(out_rows),
        "associations": out_rows,
        "notes": ("direction is the sign of the statistic against its null (1 for ratios, 0 otherwise) for the "
                  "variables as named; check names for negations and comparators. The API documentation advises "
                  "dropping API associations absent from the Dataverse CSV (in_csv false)."),
    }


def summarise(rows: list[dict]) -> dict:
    def tally(rs):
        d = {"n": len(rs), "+": 0, "-": 0, "none": 0, "sig+": 0, "sig-": 0,
             "studies": len({r["study_id"] for r in rs if r.get("study_id")})}
        for r in rs:
            k = r["direction"] or "none"
            d[k] += 1
            if r["significant"] and r["direction"]:
                d["sig" + r["direction"]] += 1
        return d
    csv = [r for r in rows if r["in_csv"] is not False]
    api_only = [r for r in rows if r["in_csv"] is False]
    types = {}
    for r in csv:
        types[r["system_statistic_type"]] = types.get(r["system_statistic_type"], 0) + 1
    return {"csv": tally(csv), "api_only_dropped": tally(api_only), "statistic_types_csv": types,
            "with_interval_csv": sum(r["ci_lower"] is not None and r["ci_upper"] is not None for r in csv),
            "with_p_csv": sum(r["p_value"] is not None for r in csv),
            "flagged_csv": sum(bool([f for f in r["flags"] if f != "sign_depends_on_group_order"]) for r in csv)}


# --------------------------------------------------------------------------- CLI

def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "x"


def _fmt(x, nd=3):
    return "" if x is None else (f"{x:.{nd}g}" if isinstance(x, float) else str(x))


def print_summary(ev: dict, nrows: int = 15) -> None:
    if ev.get("error"):
        print("error:", ev["error"])
        return
    la = ", ".join(f"{c['label']} ({c['system_id']})" for c in ev["concepts_a"])
    lb = ", ".join(f"{c['label']} ({c['system_id']})" for c in ev["concepts_b"])
    print(f"A: {la}\nB: {lb}")
    dv = ev["sources"]["dataverse"]
    print(f"sources: Dataverse {dv['doi']} v{dv['version']}" if dv else "sources: no local Dataverse copy",
          "+ API v1.0" if ev["sources"]["api"] else "(offline)")
    for r in ev["relationships"]:
        print(f"  relationship {r['relationship_id']} [{r['from']}] {r['source']} -> {r['target']}: "
              f"{r['num_findings']} findings, {r['num_studies']} studies, last published {str(r['last_published_date'])[:10]}")
    s = ev["summary"]
    c, d = s["csv"], s["api_only_dropped"]
    print(f"findings kept (in CSV): {c['n']} from {c['studies']} studies; direction + {c['+']} (significant {c['sig+']}), "
          f"- {c['-']} (significant {c['sig-']}), no sign {c['none']}")
    print(f"  with interval {s['with_interval_csv']}, with p-value {s['with_p_csv']}, flagged {s['flagged_csv']}")
    if ev["sources"]["api"]:
        print(f"API-only findings (absent from CSV, advised to drop): {d['n']}")
    print(f"{'csv':4s} {'dir':3s} {'sig':4s} {'type':24s} {'value':>8s} {'interval':>17s} {'p':>8s}  {'pmid':>9s}  variables")
    for r in ev["associations"][:nrows]:
        iv = f"[{_fmt(r['ci_lower'])}, {_fmt(r['ci_upper'])}]" if r["ci_lower"] is not None else ""
        print(f"{'yes' if r['in_csv'] else 'no' if r['in_csv'] is False else '?':4s} {r['direction'] or '.':3s} "
              f"{'*' if r['significant'] else '':4s} {str(r['system_statistic_type'])[:24]:24s} {_fmt(r['statistic_value']):>8s} "
              f"{iv:>17s} {_fmt(r['p_value']):>8s}  {_fmt(r['pubmed_id']):>9s}  {str(r['variable_1'])[:40]} ~ {str(r['variable_2'])[:40]}")
    if len(ev["associations"]) > nrows:
        print(f"... {len(ev['associations']) - nrows} more rows in the JSON")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="graph_evidence.py", description=__doc__.split("\n\n")[0],
                                 epilog="See the module docstring for field definitions.")
    ap.add_argument("a", help="concept id or search term")
    ap.add_argument("b", help="concept id or search term")
    ap.add_argument("--expand", action="store_true", help="include every concept whose label contains the term")
    ap.add_argument("--offline", action="store_true", help="CSV only, no API calls")
    ap.add_argument("--api-only", action="store_true", help="skip the local CSV copy")
    ap.add_argument("--csv-only-rows", action="store_true", help="drop API rows absent from the CSV")
    ap.add_argument("--json", default=None, help="output path, or - for stdout")
    ap.add_argument("--max-pairs", type=int, default=12)
    ap.add_argument("--rows", type=int, default=15)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    ev = evidence(a.a, a.b, expand=a.expand, offline=a.offline, api_only=a.api_only,
                  csv_only_rows=a.csv_only_rows, max_pairs=a.max_pairs)
    text = json.dumps(ev, indent=1, ensure_ascii=False, default=str)
    if a.json == "-":
        print(text)
        return 0
    path = Path(a.json) if a.json else DEFAULT_OUT / f"{_slug(a.a)}__{_slug(a.b)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    try:
        shown = path.resolve().relative_to(ROOT)
    except ValueError:
        shown = path
    if a.quiet:
        s = ev.get("summary", {}).get("csv", {})
        print(f"{shown}: {s.get('n', 0)} findings in CSV")
    else:
        print_summary(ev, a.rows)
        print(f"JSON: {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
