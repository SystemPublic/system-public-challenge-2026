# Build spec (14 Nov, 11:55): the contract between modules

Read `.claude/AGENTS.md` first. All paths are relative to `projects/camox/`. Python venv: `.venv/bin/python`. Secrets are in `.env` (never print values; read names with `sed 's/=.*//' .env`).

## Layout and owners

| Folder | Owner | Done when |
|---|---|---|
| `agents/contracts.py` | done | Pydantic models for every hand-off. Do not change without asking the lead |
| `agents/` (harness, roles, orchestrator) | lead | `orchestrator.run()` below works end to end |
| `tools/` + `mcp_server.py` | subagent A | tools auto-discovered and served over MCP; graph client with live/local fallback; literature; World Bank |
| `server/` + `Dockerfile` | subagent B | FastAPI app below runs locally against Neon and serves `web/` |
| `web/` | subagent C | dashboard below works against the API and the event stream |

## Orchestrator interface (agents/orchestrator.py)

```python
def list_agents() -> list[dict]:
    # [{"name": "evidence", "title": "Graph evidence", "description": "...", "section": "evidence"}, ...]

async def make_plan(query, profile, history, agents) -> Plan     # for the editable plan step

async def run(query: str, profile: dict, history: list[dict], agents: list[str] | None,
              emit: Callable[[dict], Awaitable[None]], plan: dict | None = None) -> Answer:
    # profile: {"id", "name", "role", "organisation", "about"}
    # history: earlier turns in this project, oldest first: [{"query": str, "summary": str}]
    # agents: None = planner chooses; a list = planner may only use these
```

## Events (emit() payloads, JSON-safe dicts; the server adds "t": ISO time and stores them in order)

| type | fields |
|---|---|
| `run_started` | `run_id` (added by the server) |
| `plan` | `plan`: Plan (question, tasks[{agent, instruction}]) |
| `agent_started` | `agent`, `instruction` |
| `tool_call` | `agent`, `tool`, `args` (dict), `summary` (one line, e.g. "12 concepts, top: malaria (1316 studies)"), `ms` |
| `retry` | `agent`, `error` (the validation error, shortened) |
| `agent_done` | `agent`, `section_type` |
| `agent_failed` | `agent`, `error` |
| `formatting` | (none) |
| `answer` | `answer`: Answer (see contracts.py; sections are typed by `type`: evidence, eda, policy, research) |
| `error` | `message` |
| `run_done` | `status`: done or failed (added by the server) |

## HTTP API (server/main.py, FastAPI; JSON in and out)

| Method and path | Body / query | Returns |
|---|---|---|
| `GET /api/agents` | | `list_agents()` |
| `GET /api/profiles` | | `[{id, name, role, organisation, about, key_names: [str]}]` |
| `POST /api/profiles` | `{name, role, organisation, about}` | the profile |
| `PUT /api/profiles/{id}/keys` | `{key_name: value}` (empty value deletes) | `{key_names}`; values are never returned |
| `GET /api/profiles/{id}/projects` | | `[{id, title, created_at, n_runs}]` |
| `POST /api/profiles/{id}/projects` | `{title}` | the project |
| `GET /api/projects/{id}` | | `{id, title, profile_id, runs: [{id, query, status, created_at, answer}]}` |
| `POST /api/projects/{id}/plan` | `{query, agents}` | a Plan to show and edit |
| `POST /api/projects/{id}/runs` | `{query, agents: [str] or null, plan: Plan or null}` | `{run_id}`; 429 with a plain message when over the run limit |
| `GET /api/runs/{id}` | | `{id, project_id, query, status, answer, events}` |
| `GET /api/runs/{id}/events` | | `text/event-stream`: replays stored events, then live ones, each `data: <json>\n\n`; ends after `run_done` |
| `GET /api/graph?ids=a,b,c` | concept ids | `{nodes: [{id, label, n_studies}], edges: [{source, target, n_studies}]}` from `tools.graph.subgraph` |
| `/mcp` | | the product MCP server (streamable HTTP, `Authorization: Bearer $MCP_TOKEN`) |
| `/` | | `web/` static files |

Run limit: 10 runs per profile per hour and 60 per hour overall, counted from the `runs` table.
Runs execute as background tasks; history for a run = the project's earlier done runs (query + answer.summary).

## Database (Postgres on Neon, `DATABASE_URL`; psycopg 3; create tables on startup if missing)

```sql
profiles(id serial primary key, name text not null, role text, organisation text, about text,
         keys bytea, created_at timestamptz default now())          -- keys: Fernet(KEY_SECRET) of a JSON dict
projects(id serial primary key, profile_id int references profiles on delete cascade,
         title text not null, created_at timestamptz default now())
runs(id serial primary key, project_id int references projects on delete cascade, query text not null,
     agents text[], status text not null default 'running', answer jsonb, events jsonb not null default '[]',
     created_at timestamptz default now(), finished_at timestamptz)
```
Seed three example profiles if `profiles` is empty, marked as examples in `about`: a World Bank jobs analyst, a PATH malaria researcher, a Nesta childhood-obesity policy lead.

## Tools (tools/)

- `tools/__init__.py` exposes `TOOLS`: every public function (no leading `_`) defined in the modules of the package, discovered automatically. Adding a tool = adding a function to a module.
- Tool rules: plain functions, type hints only `str|int|float|bool|list[str]` and `X | None`, docstring written for the model, small JSON results with row caps, read-only.
- `mcp_server.py` builds `server` (MCPServer with every tool) and `http_app()` (streamable HTTP app wrapped in the bearer-token check) so the backend can mount it. The agent harness connects in-process with `mcp.Client(mcp_server.server)`.

## Environment (.env)

`OPENAI_API_KEY`, `OPENAI_MODEL` (default gpt-6-luna), `SPG_APIKEY` (System Graph API; list endpoints currently return 500, get-by-id works), `OPENALEX_API_KEY`, `DATABASE_URL`, `MCP_TOKEN`, `KEY_SECRET` (Fernet key), `HF_TOKEN`, `GRAPH_DB` (default `data/graph.duckdb`), `GRAPH_DATASET` (`dams2005/camox-graph`, private HF dataset holding graph.duckdb for the hosted Space).

## Hosting

Hugging Face Space (Docker SDK, port 7860). On start, if `GRAPH_DB` is missing, download `graph.duckdb` from `GRAPH_DATASET` with `huggingface_hub` using `HF_TOKEN`. Secrets are Space secrets, never in the repo.
