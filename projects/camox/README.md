# CAMOX Evidence Agent

**Team:** CAMOX
**Members:** Daniel Mora (daMS2005), catxu632, vishnuskulkarni, yilalalalala
**Challenge:** Build Challenge 2 (World Bank): Can the System Public Graph improve discovery across World Bank data and research, with an initial focus on the jobs agenda?
**Pitch slides:** TODO
**Live demo:** [jobs evidence map](https://camox.onrender.com/#profile=1&project=10) and [malaria and gender](https://camox.onrender.com/#profile=2&project=11) (free hosting: the first load takes about a minute)

## What it does

A research assistant that makes the System Public Graph usable for any question. You pick a profile (who you are, what you work on), open a project and ask in plain language: a hypothesis to check, a policy to map, a topic to explore. A planner splits the question into tasks, specialist agents work on them in parallel, and you watch every tool call as it happens. The answer comes back in typed sections:

- **Evidence cards**: one per sub-claim, with a verdict (supported, contested, mixed, thin, no evidence), a consensus meter (findings pointing up or down, and how many are significant), the key findings with effect sizes, CIs, populations and DOIs, and where the evidence runs out.
- **Theory of change**: the chain from a policy to its outcome, with each link marked backed, partial or unbacked by the graph.
- **Coverage (EDA)**: where evidence is dense or thin, with tables and charts.
- **Outside research**: recent papers from OpenAlex and PubMed, web sources and World Bank indicators for what the graph doesn't hold.
- **Skeptic**: the strongest evidence against the user's claim.

Each project has goals that every agent reads, and follow-up questions see the earlier answers. You can review and edit the plan before agents start. Answers cite DOIs inline, each checked in code against the run's tool results, with a numbered reference list (titles from OpenAlex).

## How we used the System Public Graph

- **Search:** concepts by label and alias, and the raw variable wording papers used, so terms without a concept ("mold") still resolve.
- **Graph walks:** neighbours and 1 to 3 hop paths between concepts (mediators for a theory of change), and the subgraph behind each answer, drawn in the dashboard.
- **Findings:** filtered by concept groups (synonyms pooled), population wording and effect family. Direction splits, CI counts and medians are computed in code by `summarise_evidence`, never by the model, and different effect families are never pooled.
- **Checks in code:** every DOI, concept id, effect size, CI and meter count in an answer must appear in that run's tool results. "Supported" needs 3 or more studies, "no evidence" needs at least three searches first, and causal verbs are rejected (the graph holds associations). An agent that fails a check retries with the error.
- **Data:** the cleaned Dataverse subset (2.0M findings, 845k studies) in DuckDB, with the live System Graph API tried first for concept lookups.

## Build Challenge 2: the jobs agenda

The jobs demo sits on top of the general layer: a World Bank jobs analyst profile and one agent, the indicator map. The agent works for any World Bank indicator, not only jobs.

**1. Can the tool surface connected indicators in other datasets?** Yes, though less often than we expected. The indicator-map agent finds the seed indicator in the World Bank Data360 catalogue, matches it to graph concepts, takes the concepts the evidence links to it most often, and searches the World Bank indicators again for each one. Code, not the model, marks a link "Different dataset" when its indicator sits in another database than the seed (for example WDI and Women, Business and the Law), and those links are listed first. A copy of the same series in another database does not count. The linked indicators, their datasets and the evidence behind them download as a CSV.

Across the three jobs demo runs, the evidence linked the seeds to 16 concepts. Code flagged 4 as crossing datasets, and 2 of those are clear. For the employment-to-population ratio (WDI), food insecurity (14 studies) leads to FAO's "Prevalence of moderate or severe food insecurity", and educational stage (9 studies) to "Mean years of schooling" in EdStats. Of the other two, one is the unemployment rate in Gender Statistics, close to the WDI series, and one is a weak match (job satisfaction to a teacher-satisfaction indicator). 8 of the 16 are data gaps: well-studied, but no World Bank indicator measures them. Examples are mental depression (79 studies), quality of life (28), return to work (9 to 14) and postpartum depression (6).

**2. How well do indicator definitions match graph concepts?** The agent labels every match exact, narrower, broader or proxy, with one sentence why. Matching on concept labels and aliases works for broad outcomes such as unemployment, income, life expectancy and internet use. It breaks for legal and firm-level indicators: the graph has no concept for maternity leave (the nearest is parental leave), labor law or access to finance. There the agent falls back to the wording papers used. In the three jobs demo runs, every seed matched one concept, and all three matches were broader than the indicator. The employment-to-population ratio matched "employment", and the length of paid maternity leave matched "parental leave". None was exact: the graph holds the idea an indicator measures, not the indicator's precise definition.

**3. What does the evidence cover well, and what poorly?** Job outcomes and Pillar 1 are well covered; Pillars 2 and 3 and public-sector pay are thin. Studies with at least one finding on the concept, in the cleaned Dataverse subset:

| Jobs agenda group | Graph concepts (studies) |
|---|---|
| Job outcomes | income 2,278; unemployment 1,279; household income 1,255; informal economy 25 |
| Pillar 1: foundations | Internet use 382; life expectancy 190 |
| Pillar 2: business environment | day care 142; child care 108; parental leave 54; employment protection legislation 1; minimum wage 1; no concept for maternity leave or labor law |
| Pillar 3: private capital | foreign direct investment 44; credit 15; no concept for access to finance |
| Public sector | public sector 37; government employee 36 |

The coverage run adds that job-focused interventions and job quality are thin even where the outcomes are dense: employment has 1,885 studies, but job training has 2, working conditions 1 and unemployment benefits 1.

**4. Can it show where to look next, and where the evidence runs out?** Every link shows its study count, so a link that rests on one or two studies is visible as such. A linked concept that no World Bank indicator measures is shown as a "Data gap", not dropped. For maternity leave and women's employment (seed: length of paid maternity leave), the answer says so plainly: the graph holds 54 parental-leave studies, linked most often to breastfeeding (15 studies), and no finding that pairs leave with employment. Each answer ends with its gaps and where to look next, and the research agent searches OpenAlex, PubMed, the web and World Bank data for what the graph doesn't hold.

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
- The studies are about individuals, while World Bank indicators are country-level, so a link between two concepts does not mean the two indicators move together across countries.
- Matching an indicator to a graph concept can be wrong; the match type and its reason are shown so a reader can judge it.
- "No matching indicator" means we didn't find one, not that the data doesn't exist.

## AI coding tools

Yes. Claude Code (with subagents) wrote most of the code and docs. The product's agents run on OpenAI (`gpt-6-luna`).
