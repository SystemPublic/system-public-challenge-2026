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

## Layout

| Path | What |
|---|---|
| `agent/tools.py` | Read-only graph tools. Plain functions; the docstring is what the model sees |
| `agent/agent.py` | OpenAI Responses tool loop. Default model `gpt-6-luna`; `OPENAI_MODEL` overrides it |
| `agent/system_prompt.md` | Agent rules and verdict criteria. The one source for both |
| `eda/` | SQL that builds `data/graph.duckdb`, challenge keyword profiles, EDA notes |
| `docs/architecture.html` | Architecture and agent-flow diagram (archify) |
| `app.py` | Streamlit demo (to be built) |
| `mcp_server.py` | The tools as an MCP server for teammates (to be built) |

## Decisions (14 Nov, morning)

- **Data:** DuckDB on the cleaned Dataverse subset (`data/graph.duckdb`). Neo4j stays off; bring it back only if we need graph algorithms. The live API returns 403 for now.
- **Agent:** OpenAI Responses API with our own tool loop. The final answer becomes JSON-schema output: evidence cards plus the concept ids used, so the UI can draw cards and the graph.
- **UI:** a single Streamlit file. The graph visualizer is our own HTML/JS component embedded in it.
- **Team access:** the tools are served as an MCP server through the cloudflared tunnel, behind one shared bearer token.
- **Challenge:** not chosen yet. Keep the agent challenge-agnostic until it is.

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
