# Next features (14 Nov, 13:10): report, threads, proactive data, project knowledge graph

Read `.claude/AGENTS.md` and `build/spec.md` first. **Build on the existing infra. Replace nothing.** The current demo is getting good feedback, so every change below is additive: a new table or column, a new endpoint, a new agent prompt, a new section renderer. Existing routes, contracts, events and runs keep working unchanged.

Each feature copies a pattern that already exists:

| Feature | Copies |
|---|---|
| Report | The project dashboard: `POST /api/projects/{id}/dashboard`, a background task, a status column, polling, `agents/dashboard.py` |
| Threads | Projects and runs in `server/db.py`; `db.history()` |
| Proactive data | The automatic first pass and the planner; the eda role and `get_worldbank_data` |
| Knowledge graph | `Finding` in `contracts.py`, `GET /api/graph`, `web/graph.js` (cytoscape) |

## 1. Generate report (PDF), iterable

**User story:** a World Bank analyst preparing a funding case clicks "Generate report" on a project and gets a PDF: in-text citations, links to the papers, and a clear data-provenance appendix. Then they type "make section 2 shorter and add the regional data" and get version 2.

- **DB:** `alter table projects add column if not exists reports jsonb not null default '[]'` and `report_status text`. Versions are appended, never overwritten.
- **API:**
  - `POST /api/projects/{id}/report`, body `{instruction: str | null}`: builds in the background, like the dashboard.
  - `GET /api/projects/{id}` already returns the project, so the reports come with it.
- **Agent:** `agents/report.py` + `agents/report_writer.md`, run through `run_agent` with a `Report` contract.
  - **Input:** the project's goals, its stored answers (all threads), the dashboard if built, and on a revision the previous version plus the user's instruction.
  - **Contract:** `Report{title, purpose, executive_summary, sections[{heading, paragraphs[str]}], limitations[str], cited_dois[str]}`.
  - **Citations:** paragraphs carry markers like `[3]`. Each marker must map to a DOI already present in the stored answers. Check this in code with the existing verifier or provenance check, and retry on failure.
- **Built in code, not by the model:**
  - **References:** numbered, with title, year, venue (`GET /api/references` already does the OpenAlex lookup) and a `https://doi.org/` link for each.
  - **Data provenance appendix:** from the stored `runs.events`. Every `tool_call` has tool, args and time, so list each data source used: System Public Graph (Dataverse release, concept ids), World Bank (indicator id, dataset, retrieval time), OpenAlex or PubMed, each with its licence. No model writes this part.
- **PDF:** no new dependency. `web/report.html` renders the report with a print stylesheet (A4, page numbers, references at the end, links visible). "Download PDF" calls `window.print()`. Server-side PDF (WeasyPrint) is out: it needs system libraries in the Docker image.
- **UI:** a "Generate report" button on the project page, a version list ("v1 · 13:40"), a revise box under the latest version, and "Download PDF".

## 2. Multiple chat threads per project

**User story:** like Claude Code sessions. One project, several threads ("funding case", "regional data", "skeptic pass"). All threads share the project's goals, knowledge graph, dashboard and reports. Each thread has its own conversation history.

- **DB:**
  - `create table if not exists threads(id serial primary key, project_id int references projects on delete cascade, title text not null, created_at timestamptz default now())`
  - `alter table runs add column if not exists thread_id int references threads on delete cascade`
- **Back-compat:** runs with a null `thread_id` show as the project's "Main" thread. No migration of old runs.
- **API:**
  - `GET/POST /api/projects/{id}/threads`
  - `POST /api/projects/{id}/runs` accepts an optional `thread_id`
  - `db.history(project_id, thread_id)` filters by thread when given
- **Project-level context** (goals, dashboard, knowledge graph) stays project-wide, so every thread sees it.
- **UI:** threads listed under the selected project in the sidebar, a "New thread" button, and the thread title editable inline.

## 3. Proactive data: "air quality in Indonesia" shows air quality by region

**User story:** the user asks about a topic in a place. Without being asked, the answer includes the relevant measured data for that place, broken down by sub-region where it exists, as a chart with its source.

- **Planner rule** (one line in `planner.md`): when the query names a place and a measurable topic, add an `eda` task: "fetch the indicator values for {place}, by sub-region if available, and chart them".
- **Data, the open question:**
  - World Bank `get_worldbank_data` is country-level, e.g. PM2.5 `EN.ATM.PM25.MC.M3`.
  - Sub-national values need a source to be verified first: search Data360 for subnational series; OpenAQ needs a key, and the existing profile keys can switch it on.
  - Don't promise "by region" until one real call returns regional rows.
  - Country-level comparison with neighbours is the fallback.
- **Output:** the existing `EdaSection` with a Vega-Lite bar chart by region (no choropleth: it needs topojson), and the source and retrieval date under the chart.
- **Scaffold on project creation:** run the same first pass automatically when a project is created with goals. It produces a research overview (coverage), the proactive data and the initial knowledge graph. The automatic first pass already exists; extend it, don't add a second one.

## 4. Project knowledge graph: entities, facts, qualifiers

**User story:** each project builds a graph of the facts in its research: what is linked to what, in which population and place, with what effect, from which paper. The user can see it and the agents can query it.

- **Model** (Wikidata-style statements with qualifiers):
  - `Entity` nodes: graph concepts (existing ids), places (country, region), population groups, interventions, World Bank indicators.
  - `Fact` nodes: one per finding, holding subject → object ("linked to", never causal).
  - `Qualifier` values on the fact: effect type, value, CI, p-value, population, place, year, study design.
  - Every fact keeps its DOI and the run id it came from.
- **Built in code** from the `Finding` objects already in stored answers: variables, values, CIs, populations, DOIs. A cheap model call extracts only place and population entities from the `population` strings, cached per string. No model invents facts.
- **Storage:** `create table if not exists kg_nodes(project_id, id, kind, label, data jsonb)` and `kg_edges(project_id, source, target, kind, data jsonb)`. Upsert after each run and on project creation.
- **API and tool:**
  - `GET /api/projects/{id}/kg` for the UI.
  - A `project_graph(project_id, query)` tool on the MCP server, so agents get graph RAG over the project's own facts (AGENTS.md lists this as the stretch goal and says the MCP server may read project context).
- **UI:** the existing cytoscape view, with node shapes per kind. Clicking a fact shows its qualifiers and the DOI link.

## Order and time

The freeze in AGENTS.md is 14:00, with submission at 15:00. Daniel decides what goes in before the freeze.

1. Report, with PDF via print and the provenance appendix: about 45 min. Highest value for the World Bank story.
2. Threads: about 30 min.
3. Proactive data: the planner rule plus a country-level chart is about 15 min; by-region depends on the data source check.
4. Knowledge graph: about 60 min or more. After submission, or as a "next" slide.

Anything not merged by the freeze goes in the pitch as next steps, not into the demo.
