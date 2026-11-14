"""Graph RAG over a project's own knowledge graph (kg_nodes, kg_edges in the product database)."""
import os

import psycopg
from psycopg.rows import dict_row


def project_graph(project_id: int, query: str, k: int = 20) -> dict:
    """Facts this project's earlier answers established: the entities (concepts, indicators, places, population
    groups, papers) whose label matches any word of `query`, each with its facts (linked to, measures, studied in,
    reported in) and their qualifiers (effect, value, CI, verdict, population, DOIs, run id). Empty query: top entities."""
    words = [w for w in query.lower().split() if len(w) > 2] or [""]
    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row) as conn:
        nodes = conn.execute("""
            select id, kind, label, data - 'runs' data, (select count(*) from unnest(%s::text[]) w
                                       where lower(label) like '%%' || w || '%%') hits
            from kg_nodes where project_id = %s order by hits desc, (data->>'n_papers')::int desc nulls last limit %s""",
                             (words, project_id, k)).fetchall()
        nodes = [n for n in nodes if n.pop("hits") or words == [""]]
        ids = [n["id"] for n in nodes]
        edges = conn.execute("""
            select e.source, s.label source_label, e.kind, e.target, t.label target_label, e.data
            from kg_edges e join kg_nodes s on s.project_id = e.project_id and s.id = e.source
            join kg_nodes t on t.project_id = e.project_id and t.id = e.target
            where e.project_id = %s and (e.source = any(%s) or e.target = any(%s))
            order by (e.data->>'n_studies')::int desc nulls last limit 60""", (project_id, ids, ids)).fetchall()
    return {"entities": nodes, "facts": edges}
