# Evidence Agent

**Team:** CAMOX
**Members:** TODO
**Challenge:** TODO
**Pitch slides:** TODO

## What it does

You ask a question or state a hypothesis in plain language. The agent splits it into testable sub-claims, searches the System Public Graph for each one, and returns an evidence card per sub-claim: supported, contested, mixed, thin or no evidence, with the counts, effect sizes, populations and DOIs behind the verdict, and where the evidence runs out.

## How we used the System Public Graph

TODO once the challenge is chosen. The agent's tools (`agent/tools.py`) search concepts and raw variable wording, walk concept links (neighbours, 1–3 hop paths), pull findings filtered by population and effect type, and compute direction and CI statistics in code, never in the model.

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
   SPG_APIKEY=your-system-key
   OPENAI_API_KEY=your-openai-key
   ```
4. `.venv/bin/python agent/agent.py "your question"`

## Data sources

- System Public Graph, July 1, 2026 release (CC BY-NC 4.0), cleaned subset from Harvard Dataverse, doi:10.7910/DVN/7V6JDO

## Limitations

TODO

## AI coding tools

Yes. Claude Code wrote most of the code. The agent itself runs on OpenAI (`gpt-6-luna`).
