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
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from pydantic import BaseModel

import mcp_server
from agents import dashboard, orchestrator, report
from agents.harness import MODEL
from server import auth, db, kg
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
app.include_router(auth.router)
app.include_router(kg.router)


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
    thread_id: int | None = None


class ThreadIn(BaseModel):
    title: str


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
async def create_project(profile_id: int, p: ProjectIn):
    found(await run_in_threadpool(db.get_profile, profile_id))
    project = await run_in_threadpool(db.create_project, profile_id, p.title, p.goals)
    return {**project, "first_pass_run_id": await start_first_pass(project["id"]) if p.goals.strip() else None}


@app.put("/api/projects/{project_id}")
async def update_project(project_id: int, p: ProjectIn):
    before = found(await run_in_threadpool(db.get_project, project_id))
    project = await run_in_threadpool(db.update_project, project_id, p.title, p.goals)
    first = not before["goals"].strip() and p.goals.strip()
    return {**project, "first_pass_run_id": await start_first_pass(project_id) if first else None}


FIRST_PASS = "First pass: what data is available for this project, and where do sources disagree or run out?"


# Data runs (the first pass and "Data: topic") plan their own research with these agents.
DATA_AGENTS = ["availability", "indicator-map", "research", "evidence"]


async def start_first_pass(project_id):
    """A fixed-plan run started when a project gets goals; the project dashboard is built when it succeeds."""
    _, profile, history = await run_in_threadpool(context, project_id)
    run_id = await run_in_threadpool(db.create_run, project_id, FIRST_PASS, None)
    subscribers[run_id], events_sent[run_id] = [], 0

    async def then_dashboard():
        await execute(run_id, FIRST_PASS, profile, history, DATA_AGENTS, None, kind="first_pass")
        if (await run_in_threadpool(db.get_run, run_id))["status"] == "done":
            await start_dashboard(project_id)
    task = asyncio.create_task(then_dashboard())
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return run_id


@app.get("/api/projects/{project_id}")
def get_project(project_id: int):
    return found(db.get_project(project_id))


def context(project_id, thread_id=None):
    """(project, profile, history) for a query in this project; history comes from the given thread (None = Main)."""
    project = found(db.get_project(project_id))
    profile = {**db.get_profile(project["profile_id"]), "project": {"title": project["title"], "goals": project["goals"]}}
    return project, profile, db.history(project_id, thread_id)


@app.get("/api/projects/{project_id}/threads")
def list_threads(project_id: int):
    return db.list_threads(project_id)


@app.post("/api/projects/{project_id}/threads")
def create_thread(project_id: int, t: ThreadIn):
    found(db.get_project(project_id))
    return db.create_thread(project_id, t.title.strip() or "New thread")


@app.put("/api/threads/{thread_id}")
def rename_thread(thread_id: int, t: ThreadIn):
    return found(db.rename_thread(thread_id, t.title.strip() or "New thread"))


class FolderIn(BaseModel):
    folder: str | None = None


class MoveIn(BaseModel):
    project_id: int


def owned(request: Request, project_id: int):
    """Deleting or moving needs the logged-in owner, so example profiles' projects stay as they are."""
    owner = found(db.q("select pf.user_id from projects p join profiles pf on pf.id = p.profile_id where p.id = %s",
                       (project_id,), one=True))["user_id"]
    user = auth.current_user(request)
    if not owner or not user or user["id"] != owner:
        raise HTTPException(403, "Log in as the project's owner to do this. Example projects can't be changed.")


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: int, request: Request):
    owned(request, project_id)
    db.delete_project(project_id)


@app.put("/api/projects/{project_id}/folder")
def set_folder(project_id: int, f: FolderIn):
    """Folders are labels: setting a new name creates the folder, clearing it moves the project out."""
    return found(db.set_folder(project_id, (f.folder or "").strip() or None))


@app.put("/api/threads/{thread_id}/project")
def move_thread(thread_id: int, m: MoveIn, request: Request):
    owned(request, found(db.q("select project_id from threads where id = %s", (thread_id,), one=True))["project_id"])
    owned(request, m.project_id)
    return found(db.move_thread(thread_id, m.project_id))


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
            return
        if not project.get("reports"):  # the first dashboard also writes the first report, from the goals
            try:
                await start_report(project_id, ReportIn(auto=True))
            except Exception:
                pass

    await run_in_threadpool(db.set_dashboard, project_id, "building: planning panels")
    task = asyncio.create_task(build())
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return {"dashboard_status": "building: planning panels"}


class ReportIn(BaseModel):
    instruction: str | None = None
    auto: bool = False


@app.post("/api/projects/{project_id}/report")
async def start_report(project_id: int, r: ReportIn):
    """Builds a new report version in the background; poll GET /api/projects/{id} for report_status."""
    project, profile, _ = await run_in_threadpool(context, project_id)
    answers = [{"query": x["query"], **x["answer"]} for x in project["runs"] if x["status"] == "done" and x["answer"]]
    if not answers:
        raise HTTPException(400, "Ask at least one question in this project first; the report is built from the answers.")
    if (project["report_status"] or "").startswith("building"):
        raise HTTPException(409, "A report is already being built.")

    async def emit(e):
        if e["type"] in ("agent_started", "retry", "verifying"):
            await run_in_threadpool(db.set_report_status, project_id, "building: " + {"retry": "checking citations", "verifying": "verifying claims"}.get(e["type"], "writing"))

    async def build():
        try:
            calls = await run_in_threadpool(db.tool_calls, project_id)
            version = await report.build_report(project, profile, answers, r.instruction, calls, emit) | {"auto": r.auto}
            await run_in_threadpool(db.add_report, project_id, version)
        except Exception:
            await run_in_threadpool(db.set_report_status, project_id, "failed")

    await run_in_threadpool(db.set_report_status, project_id, "building: reading the answers")
    task = asyncio.create_task(build())
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return {"report_status": "building: reading the answers"}


@app.post("/api/projects/{project_id}/plan")
async def make_plan(project_id: int, r: RunIn):
    _, profile, history = await run_in_threadpool(context, project_id, r.thread_id)
    return (await orchestrator.make_plan(r.query, profile, history, r.agents)).model_dump()


@app.post("/api/projects/{project_id}/runs")
async def start_run(project_id: int, r: RunIn):
    _, profile, history = await run_in_threadpool(context, project_id, r.thread_id)
    mine, total = await run_in_threadpool(db.runs_last_hour, profile["id"])
    if mine >= RUNS_PER_PROFILE or total >= RUNS_TOTAL:
        return PlainTextResponse("Run limit reached: please try again in an hour.", 429)
    agents = DATA_AGENTS if r.query.lower().startswith("data:") and not r.plan else r.agents
    run_id = await run_in_threadpool(db.create_run, project_id, r.query, r.agents, r.thread_id)
    subscribers[run_id], events_sent[run_id] = [], 0
    task = asyncio.create_task(execute(run_id, r.query, profile, history, agents, r.plan))
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return {"run_id": run_id}


async def execute(run_id, query, profile, history, agents, plan, kind="question"):
    """Run the agents in the background: store every event, push it to live SSE subscribers, then finish the run."""
    async def emit(event):
        event = {**event, "t": datetime.now(timezone.utc).isoformat()}
        await run_in_threadpool(db.append_event, run_id, event)
        for queue in subscribers[run_id]:
            queue.put_nowait((events_sent[run_id], event))
        events_sent[run_id] += 1

    status, answer = "failed", None
    try:
        await emit({"type": "run_started", "run_id": run_id, "kind": kind})
        answer = (await orchestrator.run(query, profile, history, agents, emit, plan=plan)).model_dump()
        status = "done"
    except Exception as e:
        await emit({"type": "error", "message": f"{type(e).__name__}: {e}"[:500]})
    finally:
        await run_in_threadpool(db.finish_run, run_id, status, answer)
        if status == "done":
            for job in (kg.rebuild_after_run(run_id), name_thread(run_id)):
                tasks.add(t := asyncio.create_task(job))
                t.add_done_callback(tasks.discard)
        await emit({"type": "run_done", "status": status})
        del subscribers[run_id], events_sent[run_id]


async def name_thread(run_id):
    """Give a thread still called "New thread" a 3-6 word topic title after a finished run; failures are ignored."""
    try:
        run = await run_in_threadpool(db.q, "select r.thread_id, r.query, r.answer->>'summary' as summary from runs r "
                                      "join threads t on t.id = r.thread_id where r.id = %s and t.title in ('', 'New thread')",
                                      (run_id,), True)
        if run:
            r = await AsyncOpenAI().responses.create(
                model=MODEL, reasoning={"effort": "low"},
                instructions="Name this research thread in 3 to 6 words. Reply with the title only, no quotes or full stop.",
                input=f"Question: {run['query']}\nAnswer: {(run['summary'] or '').split('. ')[0]}")
            title = r.output_text.strip().strip('"').rstrip(".")[:80]
            if title:
                await run_in_threadpool(db.q, "update threads set title = %s where id = %s and title in ('', 'New thread')",
                                        (title, run["thread_id"]))
    except Exception:
        pass


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
