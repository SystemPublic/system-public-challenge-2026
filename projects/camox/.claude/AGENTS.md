# CAMOX: rules for coding agents

Read this file first, then the skill for your task (below). These rules apply to every agent and every teammate. Codex and Cursor users: this file is at `.claude/AGENTS.md`, so point your agent at it.

## Two halves: product and agent config

- `projects/camox/` is the product judges see. It must read like a clean, finished project.
- All agent config lives in `.claude/` and nowhere else: this file, `CLAUDE.md`, `skills/`, `launch.json`. Product code never imports from it, and the README never mentions it.
- Scratch scripts and one-off checks are not product. Keep them out of the repo (a gitignored `.claude/scratch/` is fine).

## Structure

- One module, one job. File and function names say what they do, so a newcomer can find anything in ten seconds.
- Split modules only when a file stops doing one job. Small and modular beats clever and layered.
- Split independent work into subagents, one writer per file. Review what they write before it counts.
- `docs/architecture.html` (made with the archify skill) is the high-level view of the agent flow and the project's look. Update it whenever the flow, the tools or the layout change.

## Scope and safety

- Work only inside `projects/camox/`. The challenge rules forbid changing files outside it.
- This fork is public. Everything pushed is visible. Never commit keys (`.env` is ignored) or data (`data/` and `*.duckdb` are ignored). Every file must be under 25 MB.
- Submission deadline: PR and Devpost by 15:00 on 14 Nov 2026. Stop adding features at 14:00.

## Write as little code as possible

- Write the smallest change that solves the task. Add no abstractions, config options, or generality for needs we don't have yet.
- Edit or delete existing code before you add new code. Add a file only when no existing one fits.
- Keep comments to a few lines; the long version goes in the commit message. Test the behaviour you changed and stop.
- Check what's already there before adding a dependency. Every line is a cost someone pays at 14:30.

## Layout (target; `docs/architecture.html` shows it)

| Path | What |
|---|---|
| `server/` | FastAPI app that deploys the agent loop: profiles, runs streamed over SSE, serves `web/`, mounts the MCP server |
| `agents/` | `contracts.py` (Pydantic models every agent reads and writes), the shared harness (retry, compaction, MCP tools), planner, specialists, formatter, prompts |
| `tools/` | Everything the MCP server exposes: graph client (live System Graph API or local DuckDB), literature search, outside-data connectors |
| `mcp_server.py` | The product's tool surface for the agent loop. Not a team collaboration tool |
| `web/` | Plain HTML/JS/CSS dashboard, cytoscape.js graph view. No build step |
| `eda/` | SQL that builds `data/graph.duckdb`, challenge keyword profiles, EDA notes |
| `docs/architecture.html` | Architecture diagram (archify) |

`agent/` holds the first single-agent prototype; its tools move to `tools/` and its loop is replaced by `agents/`.

## Decisions (14 Nov)

- **Scope: a general layer over the graph.** It makes the System Public Graph usable for any challenge: EDA, hypothesis checks, theory of change, policy evidence. Never hard-code one challenge into tools, prompts or schemas.
- **Users drive the context.** A profile picker (no passwords) says who the user is (for example a World Bank analyst) and which outside data they can reach. The agent adapts to that profile. Outside APIs are connectors per stakeholder, not one-off code for one challenge.
- **Demo:** one challenge, to be picked. Its questions and data are demo content on top of the general layer.
- **Stack:** FastAPI backend, plain HTML/JS frontend.
- **Product database:** SQLite holds profiles, runs, agent context and each user's project thread. The backend writes it; the MCP server can read it (project context as a tool).
- **Keys:** build only on keyless APIs. Users can add their own API keys in their profile to switch on more tools (for example an OpenAlex key or a DHS key).
- **Agents:** planner, then specialists in parallel (graph evidence, research with external search, EDA, policy / theory of change), then a formatter. Every hand-off is a Pydantic contract; a failed check retries with the validation errors. Long runs compact their context. All agents use `gpt-6-luna` (`OPENAI_MODEL` overrides).
- **Tools only through MCP.** The agent loop is an MCP client of our own server. A new tool is added once and every agent gets it.
- **Graph client:** live System Graph API when the key works, local DuckDB copy (cleaned Dataverse subset) otherwise, behind the same tools. Neo4j stays off.
- **External search:** OpenAlex and PubMed (no keys) plus OpenAI's hosted web search.
- **Stretch:** a per-project knowledge graph for graph RAG, after the core loop, dashboard and one connector work.
- **Team collaboration tooling is out of scope.** It is a separate system with its own database and MCP server, never part of the product, and is not documented here.

## Licences and disclosure

- Anything containing or derived from graph data is CC BY-NC 4.0.
- List every outside data source, with its licence, in `README.md` before using it.
- `README.md` must disclose the AI coding tools we used. Keep it current.

## Skills

| Task | Skill |
|---|---|
| Querying the graph, evidence cards, adding a tool | `.claude/skills/graph-evidence/SKILL.md` |
| Demo UI, graph visualizer, wording, screenshot audit | `.claude/skills/dashboard/SKILL.md` |

Paths are relative to `projects/camox/`. Claude Code loads them automatically when started in this folder. Other agents should read the file before starting the task.
