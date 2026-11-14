#!/usr/bin/env python
"""Paths through the System Public Graph: neighbours, shared neighbours and consequences.

A literature search answers a question that has already been asked. These functions
ask the graph the open questions instead:

  neighbours(concept)        every concept with findings linked to this one
  between(a, b)              concepts linked to both a and b: candidate mediators
                             (a -> m -> b) and candidate confounders (a <- m -> b).
                             The graph does not say which; read the variable names.
  consequences(term)         outcomes linked to study variables whose NAME matches a
                             term. Many exposures (commuting, telework) have no concept
                             and exist only as variable names.

Every function returns plain dicts and writes nothing unless asked. Counts are of
findings (associations) and studies. Signs come from tools/graph_evidence.normalise:
"+" or "-" relative to the statistic's null. A sign is the sign between the two
variables as named, so "lack of X" reverses it; check names before relying on a sign.

CLI:
  graph_paths.py neighbours "heat wave"
  graph_paths.py between temperature violence [--min 2]
  graph_paths.py consequences "commute time" [--max-vars 150]
Each prints a table and writes JSON to data/derived/graph/paths/<slug>.json.

API cost: neighbours is one paged call per concept; between is two; consequences is
one call per matching variable plus one per distinct outcome concept (all cached).
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from concord import sysgraph as g  # noqa: E402
from graph_evidence import normalise  # noqa: E402

OUT = ROOT / "data" / "derived" / "graph" / "paths"
ID_RE = re.compile(r"^[A-Za-z0-9_-]{10}$")


def _label(c) -> str:
    return (c or {}).get("wikidata_label") or (c or {}).get("system_id") or "?"


def resolve(term: str, expand: bool = True) -> list[dict]:
    """Concepts for an id or a search term. Search matches whole words, so several
    concepts may come back ("temperature" gives air, surface, body temperature ...).
    With expand=False only exact label matches are kept when there are any."""
    if ID_RE.match(term):
        c = g.concept(term)
        return [{"system_id": c["system_id"], "label": _label(c)}] if c.get("system_id") else []
    rows = g.concepts(term, limit=50)
    exact = [r for r in rows if (r.get("wikidata_label") or "").lower() == term.lower()]
    pick = rows if expand else (exact or rows)
    return [{"system_id": r["system_id"], "label": _label(r)} for r in pick]


def neighbours(cid: str, max_items: int = 5000) -> dict[str, dict]:
    """other concept id -> {label, n_findings, n_studies, relationship_ids}."""
    out: dict[str, dict] = {}
    for r in g.concept_relationships(cid, max_items=max_items):
        s, t = r.get("source_concept") or {}, r.get("target_concept") or {}
        other = t if s.get("system_id") == cid else s
        oid = other.get("system_id")
        if not oid or oid == cid:
            continue
        d = out.setdefault(oid, {"label": _label(other), "n_findings": 0, "n_studies": 0, "relationship_ids": []})
        d["n_findings"] += int(r.get("num_findings") or 0)
        d["n_studies"] += int(r.get("num_studies") or 0)
        d["relationship_ids"].append(r.get("relationship_id"))
    return out


def _pool(terms_or_ids) -> tuple[list[dict], dict[str, dict]]:
    """Resolve one or more terms and pool their neighbours."""
    if isinstance(terms_or_ids, str):
        terms_or_ids = [terms_or_ids]
    concepts, pooled = [], {}
    for t in terms_or_ids:
        for c in resolve(t):
            concepts.append(c)
            for oid, d in neighbours(c["system_id"]).items():
                p = pooled.setdefault(oid, {"label": d["label"], "n_findings": 0, "n_studies": 0, "via": []})
                p["n_findings"] += d["n_findings"]
                p["n_studies"] += d["n_studies"]
                p["via"].append(c["label"])
    return concepts, pooled


def between(a, b, min_findings: int = 2) -> dict:
    """Concepts linked to both a and b, ranked by the weaker of the two links.
    a and b may be terms, ids, or lists of them (pooled)."""
    ca, na = _pool(a)
    cb, nb = _pool(b)
    ids_a, ids_b = {c["system_id"] for c in ca}, {c["system_id"] for c in cb}
    direct = sum(d["n_findings"] for oid, d in na.items() if oid in ids_b)
    shared = []
    for oid in set(na) & set(nb):
        if oid in ids_a or oid in ids_b:
            continue
        fa, fb = na[oid]["n_findings"], nb[oid]["n_findings"]
        if min(fa, fb) < min_findings:
            continue
        shared.append({"system_id": oid, "label": na[oid]["label"], "findings_with_a": fa, "findings_with_b": fb,
                       "studies_with_a": na[oid]["n_studies"], "studies_with_b": nb[oid]["n_studies"],
                       "weaker_link": min(fa, fb)})
    shared.sort(key=lambda x: (-x["weaker_link"], -(x["findings_with_a"] + x["findings_with_b"])))
    return {"a": ca, "b": cb, "direct_findings": direct, "neighbours_a": len(na), "neighbours_b": len(nb),
            "shared": shared, "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "api": g.API_VERSION, "dataset": g.DATASET_VERSION}


def consequences(term: str, max_vars: int = 150, min_findings: int = 1) -> dict:
    """Outcomes linked to study variables whose name matches `term`.
    Groups the other variable of each association by its concept (or by its name when
    ungrounded) and reports findings, studies and the split of signs."""
    vs = g.variables(term, limit=max_vars)
    groups: dict[str, dict] = {}
    n_assoc = 0
    for v in vs:
        vid = v["system_id"]
        for a in g.variable_associations(vid, max_items=500):
            n_assoc += 1
            side = "2" if a.get("variable_1_id") == vid else "1"
            cid = a.get(f"variable_{side}_concept_id")
            name = a.get(f"variable_{side}_name") or "?"
            key = cid or ("name:" + name.lower()[:60])
            d = groups.setdefault(key, {"concept_id": cid, "label": None, "n_findings": 0, "studies": set(),
                                        "plus": 0, "minus": 0, "unsigned": 0, "significant": 0, "examples": []})
            n = normalise(a)
            d["n_findings"] += 1
            d["studies"].add(a.get("study_id"))
            d["plus" if n["direction"] == "+" else "minus" if n["direction"] == "-" else "unsigned"] += 1
            d["significant"] += 1 if n["significant"] else 0
            if len(d["examples"]) < 4:
                d["examples"].append({"exposure": a.get(f"variable_{'1' if side == '2' else '2'}_name"), "outcome": name,
                                      "statistic": a.get("system_statistic_type"), "value": a.get("statistic_value"),
                                      "ci": [a.get("ci_lower"), a.get("ci_upper")], "p": a.get("p_value"),
                                      "pubmed_id": a.get("pubmed_id"), "flags": n["flags"]})
    rows = []
    for key, d in groups.items():
        if d["n_findings"] < min_findings:
            continue
        if d["concept_id"]:
            d["label"] = _label(g.concept(d["concept_id"]))
        else:
            d["label"] = key[5:] + " (ungrounded)"
        d["n_studies"] = len(d.pop("studies"))
        rows.append(d)
    rows.sort(key=lambda x: (-x["n_studies"], -x["n_findings"]))
    return {"term": term, "variables_matched": len(vs), "associations": n_assoc, "outcomes": rows,
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "api": g.API_VERSION, "dataset": g.DATASET_VERSION}


def _slug(*parts) -> str:
    return "__".join(re.sub(r"[^a-z0-9]+", "-", str(p).lower()).strip("-") for p in parts)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return
    cmd, args = argv[1], argv[2:]
    opt = {args[i]: args[i + 1] for i in range(len(args) - 1) if args[i].startswith("--")}
    pos = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or not args[i - 1].startswith("--"))]
    OUT.mkdir(parents=True, exist_ok=True)
    if cmd == "neighbours":
        cs = resolve(pos[0])
        res = {"concepts": cs, "neighbours": {c["label"]: sorted(neighbours(c["system_id"]).values(), key=lambda d: -d["n_findings"]) for c in cs}}
        for lab, ns in res["neighbours"].items():
            print(f"{lab}: {len(ns)} neighbours")
            for d in ns[:25]:
                print(f"   {d['n_findings']:5d} findings {d['n_studies']:4d} studies  {d['label']}")
        f = OUT / f"neighbours__{_slug(pos[0])}.json"
    elif cmd == "between":
        res = between(pos[0], pos[1], int(opt.get("--min", 2)))
        print(f"a: {[c['label'] for c in res['a']]}\nb: {[c['label'] for c in res['b']]}\ndirect findings: {res['direct_findings']}; shared neighbours: {len(res['shared'])}")
        for s in res["shared"][:40]:
            print(f"   a:{s['findings_with_a']:5d}  b:{s['findings_with_b']:5d}  {s['label']}")
        f = OUT / f"between__{_slug(pos[0], pos[1])}.json"
    elif cmd == "consequences":
        res = consequences(pos[0], int(opt.get("--max-vars", 150)))
        print(f"{res['variables_matched']} variables, {res['associations']} associations, {len(res['outcomes'])} outcomes")
        for d in res["outcomes"][:40]:
            print(f"   {d['n_studies']:3d} studies {d['n_findings']:4d} findings  +{d['plus']} -{d['minus']} ?{d['unsigned']}  {d['label']}")
        f = OUT / f"consequences__{_slug(pos[0])}.json"
    else:
        print(__doc__)
        return
    f.write_text(json.dumps(res, indent=1, default=str))
    print("wrote", f.relative_to(ROOT))


if __name__ == "__main__":
    main(sys.argv)
