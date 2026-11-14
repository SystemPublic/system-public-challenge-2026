# OSS frameworks that fit the CAMOX architecture

Checked 2026-11-14. Agent and UI rows were confirmed by web search; library names in the last two sections are from prior knowledge, so check versions before installing.

## Adopt now (each one removes code from the plan)

| Need in AGENTS.md | Tool | Why |
|---|---|---|
| Planner, specialists, formatter, Pydantic hand-offs, MCP client, run history | **OpenAI Agents SDK** (`openai-agents`) | Agents, handoffs, `output_type=<Pydantic model>`, guardrails, built-in tracing, SQLite sessions. `MCPServerStreamableHttp` connects to our `mcp_server.py`. Hosted web search is a built-in tool. Replaces most of the planned `agents/` harness. |
| Agent-generated charts | **Vega-Lite + vega-embed** | The agent emits a Vega-Lite JSON spec as a contract field; the page renders it with one `<script>` tag. No build step. Evidence by country/year, forest plots. |
| Evidence graph view | **cytoscape.js** | Already chosen. |
| Streaming runs | **FastAPI + `sse-starlette`** | `EventSourceResponse` streams agent steps; the MCP ASGI app mounts on the same FastAPI app. |
| Quantitative "contested / mixed" | **statsmodels** `combine_effects` | Random-effects pooling of ratio findings with CIs, one effect type at a time, plus heterogeneity (I²). Deterministic: stats in code, not the model. |
| Paper year, title, journal (not in the graph) | **pyalex** (OpenAlex), **Biopython `Entrez`** (PubMed) | Thin keyless clients. Needed for anything over time. |

Alternative to the Agents SDK: **Pydantic AI** (validation errors go back to the model as a retry; has an MCP client). Pick one. The Agents SDK wins because we are on OpenAI and tracing is free to demo.

## Worth knowing, probably not today

| Tool | What | Why not now |
|---|---|---|
| **MCP Apps** (`@modelcontextprotocol/ext-apps`) | MCP extension: the server returns interactive HTML (`ui://`) that renders inside Claude, ChatGPT, VS Code | Good pitch line ("CAMOX works inside Claude"); stretch |
| **A2UI**, **json-render**, **CopilotKit/AG-UI** | Agent emits JSON over a registered component catalog; host renders it | React and a build step; conflicts with plain HTML |
| **PaperQA2** (`paper-qa`) | Agentic RAG over full-text papers with citations | Needs PDFs, embeddings, an index |
| **GLiNER** | Local zero-shot NER for country / age in `population` strings | An OpenAI structured-output batch is fewer moving parts |
| **wbgapi**, **sodapy** | World Bank and NYC Open Data clients | Only for World Bank (E2/B2) or NYC (B4) challenges |

## Skip

- LangChain / LangGraph, CrewAI: overlap the Agents SDK, more concepts.
- Microsoft GraphRAG, LightRAG: DuckDB already holds the graph.
- Streamlit: the stack is FastAPI + plain HTML.

## Gaps spotted in the project

- `.claude/skills/dashboard/SKILL.md` still describes a Streamlit `app.py`; AGENTS.md says FastAPI + plain HTML.
- `agent/tools.py` only reads DuckDB (the filtered Dataverse subset). No live API client yet, so "no evidence" may mean "not in the subset".
