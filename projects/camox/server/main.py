"""The CAMOX web app: profiles, projects, agent runs streamed over SSE, the graph view API,
the product MCP server at /mcp and the web/ dashboard at /.

Run: .venv/bin/uvicorn server.main:app --port 8000
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import mcp_server
from agents import dashboard, orchestrator
from server import db
from tools import graph, literature  # importing tools loads .env

RUNS_PER_PROFILE, RUNS_TOTAL = 10**9, 10**9  # rate limit off for the demo
subscribers: dict[int, list[asyncio.Queue]] = {}   # run id -> live SSE queues, only while the run is going
events_sent: dict[int, int] = {}                    # run id -> events emitted so far
tasks = set()


@asynccontextmanager
async def lifespan(app):
    await run_in_threadpool(db.init)
    await run_in_threadpool(db.fail_stale_runs)
    async with mcp_server.server.session_manager.run():
        yield


app = FastAPI(title="CAMOX", lifespan=lifespan)


@app.exception_handler(Exception)
async def json_error(request, e):
    """Any unhandled error becomes a short JSON body, never an HTML page or a stack trace."""
    return JSONResponse({"detail": f"Server error ({type(e).__name__}). Please try again."}, 500)


class ProfileIn(BaseModel):
    name: str
    role: str | None = None
    organisation: str | None = None
    about: str | None = None


class ProjectIn(BaseModel):
    title: str
    goals: str = ""


class RunIn(BaseModel):
    query: str
    agents: list[str] | None = None
    plan: dict | None = None


def found(row):
    """The row, or a 404."""
    if not row:
        raise HTTPException(404, "Not found")
    return row


@app.get("/api/health")
def health():
    """For hosting checks: what the app depends on, each true or false. `ok` needs the database and the graph."""
    try:
        database = db.q("select 1 as ok", one=True)["ok"] == 1
    except Exception:
        database = False
    try:
        live = httpx.get(f"{graph.API}/concepts/bNXwlzaSaB", headers={"x-api-key": os.environ.get("SPG_APIKEY", "")},
                         timeout=5).status_code == 200
    except httpx.HTTPError:
        live = False
    checks = {"database": database, "graph_file": graph.GRAPH_FILE.exists(),
              "openai_key": bool(os.environ.get("OPENAI_API_KEY")), "live_graph_api": live}
    return JSONResponse({"ok": database and checks["graph_file"], **checks},
                        200 if database and checks["graph_file"] else 503)


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
    return db.create_project(profile_id, p.title, p.goals)


@app.put("/api/projects/{project_id}")
def update_project(project_id: int, p: ProjectIn):
    return found(db.update_project(project_id, p.title, p.goals))


@app.get("/api/projects/{project_id}")
def get_project(project_id: int):
    return found(db.get_project(project_id))


def context(project_id):
    """(project, profile, history) for a query in this project."""
    project = found(db.get_project(project_id))
    profile = {**db.get_profile(project["profile_id"]), "project": {"title": project["title"], "goals": project["goals"]}}
    return project, profile, db.history(project_id)


@app.post("/api/projects/{project_id}/dashboard")
async def start_dashboard(project_id: int):
    """Builds the project dashboard in the background; poll GET /api/projects/{id} for dashboard_status."""
    project, profile, _ = await run_in_threadpool(context, project_id)
    answers = [{"query": r["query"], **r["answer"]} for r in project["runs"] if r["status"] == "done" and r["answer"]]
    if not answers:
        raise HTTPException(400, "Ask at least one question in this project first; the dashboard is built from the answers.")

    async def emit(e):
        if e["type"] in ("agent_started", "tool_call"):
            await run_in_threadpool(db.set_dashboard, project_id, f"building: {e['agent']}" + (f", {e['tool']}" if "tool" in e else ""))

    async def build():
        try:
            d = await dashboard.build_dashboard(project, profile, answers, emit)
            await run_in_threadpool(db.set_dashboard, project_id, "done", d.model_dump())
        except Exception:
            await run_in_threadpool(db.set_dashboard, project_id, "failed")

    await run_in_threadpool(db.set_dashboard, project_id, "building: planning panels")
    task = asyncio.create_task(build())
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return {"dashboard_status": "building: planning panels"}


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
    """Run the agents in the background: store every event, push it to live SSE subscribers, then finish the run."""
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


@app.get("/api/references")
def get_references(dois: str):
    """Title, year and venue for each DOI an answer cites (OpenAlex), for the References list."""
    return literature.lookup_dois([d for d in dois.split(",") if d][:50])


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
