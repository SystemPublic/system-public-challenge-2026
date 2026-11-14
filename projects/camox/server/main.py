"""The CAMOX web app: profiles, projects, agent runs streamed over SSE, the graph view API,
the product MCP server at /mcp and the web/ dashboard at /.

Run: .venv/bin/uvicorn server.main:app --port 8000
"""
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import mcp_server
from agents import orchestrator
from server import db
from tools import graph  # importing tools loads .env

RUNS_PER_PROFILE, RUNS_TOTAL = 10, 60       # per hour
subscribers: dict[int, list[asyncio.Queue]] = {}   # run id -> live SSE queues, only while the run is going
events_sent: dict[int, int] = {}                    # run id -> events emitted so far
tasks = set()


@asynccontextmanager
async def lifespan(app):
    await run_in_threadpool(db.init)
    async with mcp_server.server.session_manager.run():
        yield


app = FastAPI(title="CAMOX", lifespan=lifespan)


class ProfileIn(BaseModel):
    name: str
    role: str | None = None
    organisation: str | None = None
    about: str | None = None


class ProjectIn(BaseModel):
    title: str


class RunIn(BaseModel):
    query: str
    agents: list[str] | None = None
    plan: dict | None = None


def found(row):
    if not row:
        raise HTTPException(404, "Not found")
    return row


@app.get("/api/agents")
def list_agents():
    return orchestrator.list_agents()


@app.get("/api/profiles")
def list_profiles():
    return db.list_profiles()


@app.post("/api/profiles")
def create_profile(p: ProfileIn):
    return db.create_profile(p.name, p.role, p.organisation, p.about)


@app.put("/api/profiles/{profile_id}/keys")
def set_keys(profile_id: int, keys: dict[str, str]):
    found(db.get_profile(profile_id))
    return {"key_names": db.set_keys(profile_id, keys)}


@app.get("/api/profiles/{profile_id}/projects")
def list_projects(profile_id: int):
    return db.list_projects(profile_id)


@app.post("/api/profiles/{profile_id}/projects")
def create_project(profile_id: int, p: ProjectIn):
    found(db.get_profile(profile_id))
    return db.create_project(profile_id, p.title)


@app.get("/api/projects/{project_id}")
def get_project(project_id: int):
    return found(db.get_project(project_id))


def context(project_id):
    """(project, profile, history) for a query in this project."""
    project = found(db.get_project(project_id))
    return project, db.get_profile(project["profile_id"]), db.history(project_id)


@app.post("/api/projects/{project_id}/plan")
async def make_plan(project_id: int, r: RunIn):
    _, profile, history = await run_in_threadpool(context, project_id)
    return (await orchestrator.make_plan(r.query, profile, history, r.agents)).model_dump()


@app.post("/api/projects/{project_id}/runs")
async def start_run(project_id: int, r: RunIn):
    _, profile, history = await run_in_threadpool(context, project_id)
    mine, total = await run_in_threadpool(db.runs_last_hour, profile["id"])
    if mine >= RUNS_PER_PROFILE or total >= RUNS_TOTAL:
        return PlainTextResponse("Run limit reached: please try again in an hour.", 429)
    run_id = await run_in_threadpool(db.create_run, project_id, r.query, r.agents)
    subscribers[run_id], events_sent[run_id] = [], 0
    task = asyncio.create_task(execute(run_id, r.query, profile, history, r.agents, r.plan))
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return {"run_id": run_id}


async def execute(run_id, query, profile, history, agents, plan):
    async def emit(event):
        event = {**event, "t": datetime.now(timezone.utc).isoformat()}
        await run_in_threadpool(db.append_event, run_id, event)
        for queue in subscribers[run_id]:
            queue.put_nowait((events_sent[run_id], event))
        events_sent[run_id] += 1

    status, answer = "failed", None
    try:
        await emit({"type": "run_started", "run_id": run_id})
        answer = (await orchestrator.run(query, profile, history, agents, emit, plan=plan)).model_dump()
        status = "done"
    except Exception as e:
        await emit({"type": "error", "message": f"{type(e).__name__}: {e}"[:500]})
    finally:
        await run_in_threadpool(db.finish_run, run_id, status, answer)
        await emit({"type": "run_done", "status": status})
        del subscribers[run_id], events_sent[run_id]


@app.get("/api/runs/{run_id}")
def get_run(run_id: int):
    return found(db.get_run(run_id))


@app.get("/api/runs/{run_id}/events")
async def run_events(run_id: int):
    queue = asyncio.Queue()
    live = run_id in subscribers
    if live:
        subscribers[run_id].append(queue)     # subscribe before reading, so no event falls in between
    stored = found(await run_in_threadpool(db.get_run, run_id))["events"]

    async def stream():
        try:
            for event in stored:
                yield f"data: {json.dumps(event)}\n\n"
            if not live or any(e["type"] == "run_done" for e in stored):
                return
            while True:
                i, event = await queue.get()
                if i < len(stored):
                    continue
                yield f"data: {json.dumps(event)}\n\n"
                if event["type"] == "run_done":
                    return
        finally:
            if run_id in subscribers and queue in subscribers[run_id]:
                subscribers[run_id].remove(queue)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.get("/api/graph")
def get_graph(ids: str):
    return graph.subgraph([i for i in ids.split(",") if i])


@app.middleware("http")
async def no_cache_web(request, call_next):
    """Browsers revalidate the dashboard files, so a redeploy shows up on reload."""
    response = await call_next(request)
    if not request.url.path.startswith(("/api", "/mcp")):
        response.headers["Cache-Control"] = "no-cache"
    return response


app.mount("/mcp", mcp_server.http_app())
app.mount("/", StaticFiles(directory=Path(__file__).parents[1] / "web", html=True, check_dir=False))
