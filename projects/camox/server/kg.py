"""The project knowledge graph API: read it, rebuild it (also after each done run), stored in kg_nodes and kg_edges."""
from collections import Counter

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from psycopg.types.json import Jsonb

from agents import kg
from server import db

router = APIRouter()


def rebuild(project_id: int) -> dict:
    """Delete and rebuild the graph of one project from its done answers; returns the stats."""
    runs = db.q("select id, query, answer from runs where project_id = %s and status = 'done' and answer is not null "
                "order by id", (project_id,))
    cache = {r["text"]: r["data"] for r in db.q("select text, data from kg_extract")}
    nodes, edges, new = kg.build(runs, cache)
    for text, data in new.items():
        db.q("insert into kg_extract(text, data) values (%s, %s) on conflict do nothing", (text, Jsonb(data)))
    db.q("delete from kg_edges where project_id = %s", (project_id,))
    db.q("delete from kg_nodes where project_id = %s", (project_id,))
    with db._conn.cursor() as cur:
        cur.executemany("insert into kg_nodes(project_id, id, kind, label, data) values (%s, %s, %s, %s, %s)",
                        [(project_id, n["id"], n["kind"], n["label"], Jsonb(n["data"])) for n in nodes])
        cur.executemany("insert into kg_edges(project_id, source, target, kind, data) values (%s, %s, %s, %s, %s)",
                        [(project_id, e["source"], e["target"], e["kind"], Jsonb(e["data"])) for e in edges])
    return stats(nodes, edges)


def stats(nodes, edges):
    return {"nodes": dict(Counter(n["kind"] for n in nodes)), "edges": dict(Counter(e["kind"] for e in edges))}


async def rebuild_after_run(run_id: int):
    """For the run-completion hook: a failed build never touches the run."""
    try:
        await run_in_threadpool(lambda: rebuild(db.get_run(run_id)["project_id"]))
    except Exception:
        pass


@router.get("/api/projects/{project_id}/kg")
def get_kg(project_id: int):
    nodes = db.q("select id, kind, label, data from kg_nodes where project_id = %s", (project_id,))
    edges = db.q("select source, target, kind, data from kg_edges where project_id = %s", (project_id,))
    return {"nodes": nodes, "edges": edges, "stats": stats(nodes, edges)}


@router.post("/api/projects/{project_id}/kg/rebuild")
async def post_rebuild(project_id: int):
    return await run_in_threadpool(rebuild, project_id)
