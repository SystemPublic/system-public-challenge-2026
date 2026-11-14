# CAMOX Evidence Agent

**Team:** CAMOX
**Members:** Daniel Mora (daMS2005), catxu632, vishnuskulkarni, yilalalalala
**Challenge:** TODO
**Pitch slides:** TODO

## What it does

A research assistant that makes the System Public Graph usable for any question. You pick a profile (who you are, what you work on), open a project and ask in plain language: a hypothesis to check, a policy to map, a topic to explore. A planner splits the question into tasks, specialist agents work on them in parallel, and you watch every tool call as it happens. The answer comes back in typed sections:

- **Evidence cards**: one per sub-claim, with a verdict (supported, contested, mixed, thin, no evidence), a consensus meter (findings pointing up or down, and how many are significant), the key findings with effect sizes, CIs, populations and DOIs, and where the evidence runs out.
- **Theory of change**: the chain from a policy to its outcome, with each link marked backed, partial or unbacked by the graph.
- **Coverage (EDA)**: where evidence is dense or thin, with tables and charts.
- **Outside research**: recent papers from OpenAlex and PubMed, web sources and World Bank indicators for what the graph doesn't hold.
- **Skeptic**: the strongest evidence against the user's claim.

Follow-up questions in a project see the earlier answers. You can review and edit the plan before agents start.

## How we used the System Public Graph

- **Search:** concepts by label and alias, and the raw variable wording papers used, so terms without a concept ("mold") still resolve.
- **Graph walks:** neighbours and 1 to 3 hop paths between concepts (mediators for a theory of change), and the subgraph behind each answer, drawn in the dashboard.
- **Findings:** filtered by concept groups (synonyms pooled), population wording and effect family. Direction splits, CI counts and medians are computed in code by `summarise_evidence`, never by the model, and different effect families are never pooled.
- **Checks in code:** every DOI, concept id, effect size, CI and meter count in an answer must appear in that run's tool results. "Supported" needs 3 or more studies, "no evidence" needs at least three searches first, and causal verbs are rejected (the graph holds associations). An agent that fails a check retries with the error.
- **Data:** the cleaned Dataverse subset (2.0M findings, 845k studies) in DuckDB, with the live System Graph API tried first for concept lookups.

## How it is built

`agents/` (planner, specialists, formatter, shared harness, Pydantic contracts), `agents/roles/` (one file per specialist; drop a file in to add an agent), `tools/` (every function is a tool, served over MCP), `server/` (FastAPI, Postgres), `web/` (plain HTML/JS). Our agents call tools only through our own MCP server, which any MCP client can use too. Diagram: `docs/architecture.html`.

## How to run it

1. `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
2. Build the local graph (about 10 minutes, needs the `duckdb` CLI):
   ```bash
   mkdir -p data && cd data && B=https://dataverse.harvard.edu/api/access/datafile
   curl -sL $B/14061020 -o associations.csv
   curl -sL $B/14061025 -o relationships.csv
   curl -sL "$B/14061021?format=original" -o concepts.csv
   curl -sL "$B/14061022?format=original" -o studies.csv
   curl -sL "$B/14061023?format=original" -o variables.csv
   cd .. && duckdb data/graph.duckdb < eda/load.sql
   ```
3. Create `.env` in this folder:
   ```
   OPENAI_API_KEY=your-openai-key
   DATABASE_URL=postgresql://...        # any Postgres, e.g. a free Neon project
   KEY_SECRET=...                       # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   MCP_TOKEN=any-long-secret
   SPG_APIKEY=your-system-key           # optional: live System Graph API
   OPENALEX_API_KEY=...                 # optional: higher OpenAlex limits
   ```
4. `.venv/bin/uvicorn server.main:app --port 8000`, then open http://localhost:8000

The MCP server is at `http://localhost:8000/mcp/` (header `Authorization: Bearer <MCP_TOKEN>`), so Claude, Cursor or Codex can use the same tools.

## Data sources

- System Public Graph, July 1, 2026 release, cleaned subset from Harvard Dataverse, doi:10.7910/DVN/7V6JDO (CC BY-NC 4.0). Everything derived from it carries the same licence.
- System Public Graph API, public-api.system.com (CC BY-NC 4.0).
- OpenAlex API (CC0 data).
- PubMed E-utilities, NCBI (public; individual abstracts may carry publisher copyright).
- World Bank Indicators API and Data360 (CC BY 4.0).
- OpenAI web search, used by the research agent for reports and datasets; each source is linked in the answer.

## Limitations

- Findings are associations extracted from papers, not causal estimates, and extraction errors exist even in the cleaned subset.
- Variable wording often hides the reference group (which sex, which exposure level); agents flag it but can still misread it.
- Coverage is uneven: dense for common health outcomes, thin for policy instruments such as taxes, and populations skew to high-income countries.
- A run takes 1 to 2 minutes and calls OpenAI, so runs are rate-limited per profile.
- Sources the research agent finds on the web are not checked against our tool results the way graph findings are.

## AI coding tools

Yes. Claude Code (with subagents) wrote most of the code and docs. The product's agents run on OpenAI (`gpt-6-luna`).
