"""Read-only tools over the System Public Graph: the local DuckDB copy of the cleaned Dataverse subset
(GRAPH_DB, default data/graph.duckdb) for numbers, and the live System Graph API where it adds something."""
import functools
import os
import statistics
import time
from pathlib import Path
from urllib.parse import quote

import duckdb

from tools._http import get_json

API = "https://public-api.system.com/v1"
_live_down_until = 0.0
FAMILY = {
    **dict.fromkeys(["odds_ratio", "adjusted_odds_ratio", "hazard_ratio", "adjusted_hazard_ratio",
                     "relative_risk_ratio", "incident_rate_ratio", "prevalence_ratio"], "ratio"),
    **dict.fromkeys(["mean_difference_unstandardized", "mean_difference_standardized", "coefficient",
                     "risk_difference", "elasticity"], "difference"),
    **dict.fromkeys(["pearson_r", "spearman_correlation"], "correlation"),
}
NULL = {"ratio": 1.0, "difference": 0.0, "correlation": 0.0}


@functools.cache
def _db():
    return duckdb.connect(str(Path(__file__).resolve().parents[1] / os.environ.get("GRAPH_DB", "data/graph.duckdb")),
                          read_only=True, config={"memory_limit": os.environ.get("DUCKDB_MEMORY", "75%")})


def _rows(sql, params=()):
    cur = _db().cursor().execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def search_concepts(text: str, k: int = 10) -> list:
    """Find graph concepts (Wikidata-grounded) whose label or aliases contain `text`, most-studied first.
    Use short single terms ("malaria", "obesity"); try synonyms if results are thin."""
    return _rows("""
        WITH hits AS (SELECT system_id, wikidata_label, wikidata_id, wikidata_description FROM concepts
                      WHERE wikidata_label ILIKE '%' || $t || '%' OR wikidata_aliases ILIKE '%' || $t || '%'),
        counts AS (SELECT c, count(DISTINCT study_id) n FROM (
                     SELECT variable_1_concept_id c, study_id FROM associations UNION ALL
                     SELECT variable_2_concept_id, study_id FROM associations) WHERE c IN (SELECT system_id FROM hits) GROUP BY c)
        SELECT system_id concept_id, wikidata_label label, wikidata_id, wikidata_description description, n n_studies
        FROM hits JOIN counts ON c = system_id
        ORDER BY lower(wikidata_label) = lower($t) DESC, n DESC LIMIT $k""", {"t": text, "k": k})


def search_variables(text: str, k: int = 20) -> list:
    """Search the raw variable wording papers used (catches terms with no concept, e.g. "mold").
    Returns the concepts those variables are grounded to, with example wordings."""
    return _rows("""
        SELECT c.wikidata_label concept_label, v.concept_id, count(*) n_variables, list(v.name)[1:3] examples
        FROM variables v LEFT JOIN concepts c ON c.system_id = v.concept_id
        WHERE v.name ILIKE '%' || $t || '%' GROUP BY ALL ORDER BY n_variables DESC LIMIT $k""", {"t": text, "k": k})


def neighbours(concept_id: str, min_studies: int = 1, k: int = 25) -> list:
    """Concepts most strongly linked to `concept_id` (both directions merged), by number of studies."""
    return _rows("""
        WITH e AS (SELECT "target_concept.system_id" o, "target_concept.wikidata_label" label, num_studies, num_findings
                   FROM relationships WHERE "source_concept.system_id" = $c UNION ALL
                   SELECT "source_concept.system_id", "source_concept.wikidata_label", num_studies, num_findings
                   FROM relationships WHERE "target_concept.system_id" = $c)
        SELECT o concept_id, any_value(label) label, sum(num_studies) n_studies, sum(num_findings) n_findings
        FROM e WHERE o <> $c GROUP BY o HAVING sum(num_studies) >= $m ORDER BY n_studies DESC LIMIT $k""",
                 {"c": concept_id, "m": min_studies, "k": k})


def paths(concept_a: str, concept_b: str, min_studies: int = 2, k: int = 15) -> list:
    """Chains linking two concepts: direct, or via one or two intermediate concepts (mediators/bridges).
    Ranked by the study count of the weakest link. Use for mechanisms and theory-of-change links."""
    rows = _rows("""
        WITH u AS (SELECT least(s, t) a, greatest(s, t) b, sum(n) n FROM (
                     SELECT "source_concept.system_id" s, "target_concept.system_id" t, num_studies n FROM relationships)
                   WHERE s <> t GROUP BY 1, 2 HAVING sum(n) >= $m),
        e AS (SELECT a, b, n FROM u UNION ALL SELECT b, a, n FROM u)
        SELECT * FROM (
          SELECT [x.a, x.b] ids, x.n strength FROM e x WHERE x.a = $A AND x.b = $B
          UNION ALL SELECT [x.a, x.b, y.b], least(x.n, y.n) FROM e x JOIN e y ON x.b = y.a
            WHERE x.a = $A AND y.b = $B AND x.b <> $B
          UNION ALL SELECT [x.a, x.b, y.b, z.b], least(x.n, y.n, z.n) FROM e x JOIN e y ON x.b = y.a JOIN e z ON y.b = z.a
            WHERE x.a = $A AND z.b = $B AND x.b NOT IN ($A, $B) AND y.b NOT IN ($A, $B) AND x.b <> y.b)
        ORDER BY len(ids), strength DESC LIMIT $k""", {"A": concept_a, "B": concept_b, "m": min_studies, "k": k})
    ids = {i for r in rows for i in r["ids"]}
    label = {r["system_id"]: r["wikidata_label"] for r in
             _rows("SELECT system_id, wikidata_label FROM concepts WHERE list_contains($ids, system_id)", {"ids": list(ids)})}
    return [{"path": [label.get(i, i) for i in r["ids"]], "concept_ids": r["ids"], "weakest_link_studies": r["strength"]}
            for r in rows]


def _where(concepts_a, concepts_b, variable_text, population_text, stat_family):
    sql = "(list_contains($A, a.variable_1_concept_id) AND {b2} OR list_contains($A, a.variable_2_concept_id) AND {b1})"
    p = {"A": concepts_a}
    if concepts_b:
        sql = sql.format(b1="list_contains($B, a.variable_1_concept_id)", b2="list_contains($B, a.variable_2_concept_id)")
        p["B"] = concepts_b
    else:
        sql = sql.format(b1="true", b2="true")
    if variable_text:
        sql += " AND (a.variable_1_name ILIKE '%' || $v || '%' OR a.variable_2_name ILIKE '%' || $v || '%')"
        p["v"] = variable_text
    if population_text:
        sql += " AND s.population_string ILIKE '%' || $pop || '%'"
        p["pop"] = population_text
    if stat_family:
        sql += " AND list_contains($fam, a.system_statistic_type)"
        p["fam"] = [t for t, f in FAMILY.items() if f == stat_family]
    return sql, p


FINDINGS_SQL = """
    SELECT a.variable_1_name, a.variable_2_name, a.system_statistic_type stat_type, a.statistic_value value,
           a.ci_lower, a.ci_upper, a.p_value, a.study_id, s.doi, s.pubmed_id, s.population_string population
    FROM associations a JOIN studies s USING (study_id) WHERE {where}"""


def get_findings(concepts_a: list[str], concepts_b: list[str] | None = None, variable_text: str | None = None,
                 population_text: str | None = None, stat_family: str | None = None, limit: int = 40) -> dict:
    """Statistical findings between concept group A (list of concept_ids, synonyms grouped) and group B
    (or anything, if B is omitted). Optional filters: substring of either variable's wording, substring of the
    study population (e.g. "child", "Uganda"), stat_family "ratio" | "difference" | "correlation".
    Each row has variable wordings, effect type/value, CI, p-value, DOI and population. Findings with CIs first."""
    where, p = _where(concepts_a, concepts_b, variable_text, population_text, stat_family)
    rows = _rows(f"""SELECT *, count(*) OVER () total FROM ({FINDINGS_SQL.format(where=where)})
                     ORDER BY ci_lower IS NULL, study_id LIMIT $lim""", {**p, "lim": limit})
    return {"total": rows[0].pop("total") if rows else 0, "shown": len(rows),
            "findings": [{k: v for k, v in r.items() if k != "total"} for r in rows]}


def summarise_evidence(concepts_a: list[str], concepts_b: list[str] | None = None, variable_text: str | None = None,
                       population_text: str | None = None) -> dict:
    """Deterministic statistics over ALL findings matching the same filters as get_findings (never compute these
    yourself). Per effect family: count, how many point above/below the null, how many have a CI excluding the
    null on each side, median value; plus distinct studies and sample populations."""
    where, p = _where(concepts_a, concepts_b, variable_text, population_text, None)
    rows = _rows(FINDINGS_SQL.format(where=where), p)
    out = {"n_findings": len(rows), "n_studies": len({r["study_id"] for r in rows}), "by_family": {}}
    for fam, null in NULL.items():
        fr = [r for r in rows if FAMILY.get(r["stat_type"]) == fam and r["value"] is not None]
        if not fr:
            continue
        ci = [r for r in fr if r["ci_lower"] is not None and r["ci_upper"] is not None]
        out["by_family"][fam] = {
            "n": len(fr), "n_studies": len({r["study_id"] for r in fr}),
            "above_null": sum(r["value"] > null for r in fr), "below_null": sum(r["value"] < null for r in fr),
            "with_ci": len(ci), "ci_excludes_null_above": sum(r["ci_lower"] > null for r in ci),
            "ci_excludes_null_below": sum(r["ci_upper"] < null for r in ci),
            "median_value": statistics.median(r["value"] for r in fr)}
    out["sample_populations"] = list(dict.fromkeys(r["population"] for r in rows if r["population"]))[:10]
    return out


def sql(query: str) -> list:
    """Escape hatch: run a read-only DuckDB SQL query (max 50 rows). Tables: associations, relationships,
    studies, variables, concepts. Relationship columns are quoted, e.g. "source_concept.system_id"."""
    return _rows(f"SELECT * FROM ({query.rstrip('; ')}) LIMIT 50")



def _live(path):
    """GET from the live System Graph API, or None. After a failure it is skipped for a minute, so fallback stays fast."""
    global _live_down_until
    if not os.environ.get("SPG_APIKEY") or time.time() < _live_down_until:
        return None
    try:
        return get_json(API + path, headers={"x-api-key": os.environ["SPG_APIKEY"]}, timeout=5)
    except RuntimeError:
        _live_down_until = time.time() + 60
        return None


def get_concept(concept_id: str) -> dict:
    """One concept's Wikidata label, id, description and aliases. Works for concepts outside the local copy too
    (asks the live System Graph API first). `source` says "live" or "local"."""
    live = _live(f"/concepts/{quote(concept_id, safe='')}")
    if live:
        return {**live, "source": "live"}
    rows = _rows("""SELECT system_id, wikidata_label, wikidata_id, wikidata_description, wikidata_aliases
                    FROM concepts WHERE system_id = $c""", {"c": concept_id})
    return {**rows[0], "source": "local"} if rows else {"error": f"unknown concept {concept_id}"}


def subgraph(concept_ids: list[str], max_extra: int = 0) -> dict:
    """The graph among the given concepts: nodes with study counts and edges with study counts (both directions
    merged). max_extra adds up to that many of the concepts most linked to the set (max 30). For drawing a map."""
    extra = [] if max_extra <= 0 else [r["o"] for r in _rows("""
        SELECT o FROM (SELECT "target_concept.system_id" o, num_studies n FROM relationships
                       WHERE list_contains($ids, "source_concept.system_id") UNION ALL
                       SELECT "source_concept.system_id", num_studies FROM relationships
                       WHERE list_contains($ids, "target_concept.system_id"))
        WHERE NOT list_contains($ids, o) GROUP BY o ORDER BY sum(n) DESC LIMIT $k""",
                                                             {"ids": concept_ids, "k": min(max_extra, 30)})]
    ids = list(dict.fromkeys(concept_ids + extra))
    nodes = _rows("""
        WITH counts AS (SELECT c, count(DISTINCT study_id) n FROM (
                          SELECT variable_1_concept_id c, study_id FROM associations UNION ALL
                          SELECT variable_2_concept_id, study_id FROM associations) WHERE list_contains($ids, c) GROUP BY c)
        SELECT system_id id, wikidata_label label, coalesce(n, 0) n_studies
        FROM concepts LEFT JOIN counts ON c = system_id WHERE list_contains($ids, system_id)""", {"ids": ids})
    edges = _rows("""
        SELECT least(s, t) source, greatest(s, t) target, sum(n) n_studies FROM (
          SELECT "source_concept.system_id" s, "target_concept.system_id" t, num_studies n FROM relationships
          WHERE list_contains($ids, "source_concept.system_id") AND list_contains($ids, "target_concept.system_id"))
        WHERE s <> t GROUP BY 1, 2 ORDER BY n_studies DESC LIMIT 300""", {"ids": ids})
    return {"nodes": nodes, "edges": edges, "source": "local"}
