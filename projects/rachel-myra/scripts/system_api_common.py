"""Shared helpers for the scripts/system_api_*.py pipeline (System Public Graph API, 14 Nov 2026).

- paths for inputs/outputs
- citation ID normalisation (PMID / PMCID / DOI) via data/processed/literature_id_map.csv
- term-group matching re-exported from scripts/system_terms.py
- statistic-type helpers (ratio types, direction)
- Dataverse cross-check: stream data/raw/system/dataverse/associations.csv once and
  return rows whose association system_id or study_id is in a given set
"""
import csv, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
from system_terms import DRUGS15, COMPARATORS, MEDIATORS, HEAT, compile_groups, match_groups  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
API_DIR = P("data", "raw", "system", "api")
PROC = P("data", "processed")
DV_ASSOC = P("data", "raw", "system", "dataverse", "associations.csv")
DV_STUDIES = P("data", "raw", "system", "dataverse", "studies.csv")

DRUG_GROUPS = {**DRUGS15, **COMPARATORS}
DRUG_C = compile_groups(DRUG_GROUPS)
MED_C = compile_groups(MEDIATORS)
HEAT_C = compile_groups(HEAT)

csv.field_size_limit(10 ** 8)


def norm_doi(d):
    if not d:
        return ""
    d = str(d).strip()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", d, flags=re.I)
    return d.rstrip(".,;)").lower()


def norm_pmcid(x):
    if not x:
        return ""
    x = str(x).strip().upper()
    return x if x.startswith("PMC") else ("PMC" + x if x.isdigit() else x)


def norm_pmid(x):
    if x is None:
        return ""
    x = str(x).strip()
    if x.endswith(".0"):
        x = x[:-2]
    return x if x.isdigit() else ""


class IdMap:
    """Lookup any of pmid / pmcid / doi -> (pmid, pmcid, doi) from literature_id_map.csv."""

    def __init__(self, path=P("data", "processed", "literature_id_map.csv")):
        self.by = {}
        for r in csv.DictReader(open(path, encoding="utf-8")):
            rec = (norm_pmid(r["pmid"]), norm_pmcid(r["pmcid"]), norm_doi(r["doi"]))
            for k in ("pmid:" + rec[0] if rec[0] else None, "pmcid:" + rec[1] if rec[1] else None,
                      "doi:" + rec[2] if rec[2] else None):
                if k and k not in self.by:
                    self.by[k] = rec

    def resolve(self, pmid="", pmcid="", doi=""):
        pmid, pmcid, doi = norm_pmid(pmid), norm_pmcid(pmcid), norm_doi(doi)
        for k in (("pmid:" + pmid) if pmid else None, ("pmcid:" + pmcid) if pmcid else None,
                  ("doi:" + doi) if doi else None):
            if k and k in self.by:
                m = self.by[k]
                return (pmid or m[0], pmcid or m[1], doi or m[2])
        return (pmid, pmcid, doi)


def paper_key(pmid, pmcid, doi):
    return f"PMID:{pmid}" if pmid else (f"DOI:{doi}" if doi else f"PMCID:{pmcid}")


RATIO_RE = re.compile(r"odds|hazard|risk_ratio|relative_risk|rate_ratio|incidence|\bor\b|\bhr\b|\brr\b|\birr\b|ratio", re.I)


def is_ratio(stat_type, sys_type=""):
    s = f"{stat_type or ''} {sys_type or ''}"
    return bool(RATIO_RE.search(s)) and not re.search(r"difference|coefficient|correlation", s, re.I)


def direction(stat_value, stat_type, sys_type=""):
    """'up' (>1), 'down' (<1), 'null' (==1) for ratio types; '' otherwise."""
    try:
        v = float(stat_value)
    except (TypeError, ValueError):
        return ""
    if not is_ratio(stat_type, sys_type):
        return ""
    return "up" if v > 1 else ("down" if v < 1 else "null")


def groups_of(text):
    return {"drug": match_groups(text, DRUG_C), "mediator": match_groups(text, MED_C), "heat": match_groups(text, HEAT_C)}


def dataverse_lookup(assoc_ids=(), study_ids=(), cache=None):
    """Stream the Dataverse associations CSV; return rows whose system_id is in assoc_ids
    or whose study_id is in study_ids. Optionally cache the hits to `cache` (csv)."""
    assoc_ids, study_ids = set(assoc_ids), set(study_ids)
    if cache and os.path.exists(cache):
        rows = list(csv.DictReader(open(cache, encoding="utf-8")))
        have = {r["_query_key"] for r in rows if r.get("_query_key")}
        want = {"a:" + a for a in assoc_ids} | {"s:" + s for s in study_ids}
        if want <= have:
            return [r for r in rows if r["system_id"] in assoc_ids or r["study_id"] in study_ids]
    if not os.path.exists(DV_ASSOC):
        raise FileNotFoundError(DV_ASSOC)
    out = []
    with open(DV_ASSOC, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["system_id"] in assoc_ids or r["study_id"] in study_ids:
                out.append(r)
    if cache:
        fields = list(out[0].keys()) if out else ["system_id", "study_id"]
        with open(cache, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields + ["_query_key"])
            w.writeheader()
            for r in out:
                w.writerow({**r, "_query_key": ""})
            # record which keys were queried so a rerun with the same sets is free
            for a in sorted(assoc_ids):
                w.writerow({"system_id": "", "study_id": "", "_query_key": "a:" + a})
            for s in sorted(study_ids):
                w.writerow({"system_id": "", "study_id": "", "_query_key": "s:" + s})
    return out


def num(x):
    try:
        if x in (None, ""):
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def close(a, b, claimed_text=None):
    """True if b equals a at the precision a was written with (e.g. '6.0' vs 6.02 -> True, tol 0.051)."""
    if a is None or b is None:
        return False
    dec = 0
    if claimed_text and "." in claimed_text:
        dec = len(claimed_text.split(".")[1])
    tol = 0.5 * 10 ** (-dec) + 1e-9 if dec else 0.5
    tol = max(tol, 0.0051)
    return abs(a - b) <= tol


def write_csv(path, rows, fields=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if fields is None:
        fields = []
        for r in rows:
            for k in r:
                if k not in fields:
                    fields.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return path
