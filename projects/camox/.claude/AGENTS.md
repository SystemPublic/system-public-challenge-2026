# CAMOX: rules for coding agents

Read this file first, then the skill for your task (below). These rules apply to every agent and every person working on the code. Codex and Cursor users: this file is at `.claude/AGENTS.md`, so point your agent at it.

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
| `agents/` | `contracts.py` (Pydantic models), `harness.py` (tool loop over MCP, strict output, code-side provenance check, retry), `orchestrator.py` (plan, parallel specialists, formatter), `rules.md`, `planner.md`, `formatter.md` |
| `agents/roles/*.md` | One file per specialist: frontmatter (name, title, description, section, optional tools, web_search) plus its prompt. Drop a file in to add an agent |
| `tools/` | Everything the MCP server exposes: graph client (live System Graph API or local DuckDB), literature search, outside-data connectors |
| `mcp_server.py` | The product's tool surface: the agent loop and any outside MCP client use it |
| `web/` | Plain HTML/JS/CSS dashboard, cytoscape.js graph view. No build step |
| `eda/` | SQL that builds `data/graph.duckdb`, challenge keyword profiles, EDA notes |
| `docs/architecture.html` | Architecture diagram (archify) |


## Decisions (14 Nov)

- **Scope: a general layer over the graph.** It makes the System Public Graph usable for any challenge: EDA, hypothesis checks, theory of change, policy evidence. Never hard-code one challenge into tools, prompts or schemas.
- **A scaffold, not a fixed feature list.** More agents and tools will be added. Adding one must be a small, local change; never assume today's set is complete.
- **Every user gets every feature.** All agents and tools are available to all users. A profile (picked, no passwords) adds context, such as who the user is and what they work on, and optional keys that switch on keyed APIs. It never hides agents or tools.
- **Adding tools and agents is drop-in.** A tool is one function in a `tools/` module; the MCP server serves it with no other change. An agent is one folder (prompt, output contract, allowed tools) that the planner discovers.
- **Routing:** the planner picks the agents for a query and shows its plan; the user can add or remove agents before or during the run.
- **Output is typed sections.** Each agent has its own output contract (evidence cards, EDA tables and Vega-Lite charts, theory-of-change chains, literature lists). The formatter writes a short overall answer and arranges the sections. The dashboard has one renderer per section type.
- **Projects with threads.** A user works in projects; each query is a turn in the project's thread, and follow-ups see earlier answers and context.
- **Live view:** the dashboard shows each agent's status and every tool call with a one-line result.
- **User keys** are encrypted in the product database with a server secret from `.env` and decrypted only when a tool needs them.
- **Hosted:** the product runs at a public URL, open to anyone, with a run limit per profile and per hour. On the host the graph client uses the live System Graph API.
- **Demo:** one challenge, to be picked. Its questions and data are demo content on top of the general layer.
- **Stack:** FastAPI backend, plain HTML/JS frontend, vega-embed for charts, Docker for deploy.
- **Product database:** Postgres on Neon (`DATABASE_URL` in `.env`), the same database locally and on the host. It holds profiles, runs, agent context and each user's project thread. The backend writes it; the MCP server can read it (project context as a tool).
- **Keys:** build only on keyless APIs. Users can add their own API keys in their profile to switch on more tools (for example an OpenAlex key or a DHS key).
- **Agents:** planner, then specialists in parallel (graph evidence, research with external search, EDA, policy / theory of change), then a formatter. Every hand-off is a Pydantic contract; a failed check retries with the validation errors. Long runs compact their context. All agents use `gpt-6-luna` (`OPENAI_MODEL` overrides).
- **Tools only through MCP.** The agent loop is an MCP client of our own server. A new tool is added once and every agent gets it.
- **Graph client:** live System Graph API when the key works, local DuckDB copy (cleaned Dataverse subset) otherwise, behind the same tools. Neo4j stays off.
- **External search:** OpenAlex and PubMed (no keys) plus OpenAI's hosted web search.
- **Stretch:** a per-project knowledge graph for graph RAG, after the core loop, dashboard and one connector work.

## Licences and disclosure

- Anything containing or derived from graph data is CC BY-NC 4.0.
- List every outside data source, with its licence, in `README.md` before using it.
- `README.md` must disclose the AI coding tools we used. Keep it current.

## Skills

| Task | Skill |
|---|---|
| Querying the graph, evidence cards, adding a tool | `.claude/skills/graph-evidence/SKILL.md` |
| Demo UI, graph visualizer, wording, screenshot audit | `.claude/skills/dashboard/SKILL.md` |
| Run flow in the UI: plan step, live progress, cards, chain, provenance | `.claude/skills/agent-ux/SKILL.md` |
| Planner, roles, formatter, prompt-vs-code checks, budgets, test questions | `.claude/skills/agent-workflow/SKILL.md` |

Paths are relative to `projects/camox/`. Claude Code loads them automatically when started in this folder. Other agents should read the file before starting the task.
