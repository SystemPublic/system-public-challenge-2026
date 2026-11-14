# What Works Where: malaria prevention across settings and time

**Team:** HackKiller
**Members:** ZiyaoDai, Chloe Wang, Kevin Qian, Yuqing Ji, Xinyi Zhao
**Challenge:** Visualize 2: How does the effect of malaria prevention vary by setting and over time? (PATH)
**Pitch slides:** _link_

## What it does

A dashboard for malaria programme staff and researchers. It compares the reported effects of bed nets, seasonal malaria chemoprevention (SMC) and malaria vaccines by country, study setting and follow-up time, and shows what each number actually compares.

## How we used the System Public Graph

- **Search.**
  - Scanned all 1,999,877 associations in the fixed Harvard Dataverse v2.1 snapshot of the graph.
  - Kept rows whose variables name a net (generic or by product: Interceptor G2, Olyset Plus, PermaNet, Royal Guard…), SMC (or SP+AQ, IPTc) or a malaria vaccine (RTS,S, R21).
  - Restricted to papers whose variables mention malaria, Plasmodium, Anopheles or mosquitoes.
  - Union with the teammate's lexical rule (`scripts/clean_data.py`) so nothing they found is lost.
  - Result: 481 associations from 273 papers.
- **Concepts.** Used the API to pull the `malaria` concept's relationships ranked by `num_studies`, and the `mosquito net` and `malaria vaccine` neighbourhoods. SMC has no grounded concept, so string search was essential.
- **Context.** Joined each association to its System study record (population, study type) and to PubMed (title, journal, year, DOI).
- **What counted as evidence.**
  - Associations where the intervention is the exposure and a malaria outcome is the result.
  - Uptake and acceptance studies (for example, education → net ownership) were kept separate.
  - Rows with no CI, a non-positive ratio or a percentage stored as a ratio are flagged and not plotted.
- **Verification.**
  - Pre-checked 142 priority rows against Europe PMC abstracts.
  - Reviewed 33 rows by hand. 19 of those needed their comparator, time point or label restored.
  - Entered 20 anchor results from 7 landmark trials directly from the papers.
  - The graph's original label is always kept next to the correction.
- **Other data.** WHO Global Health Observatory country indicators (ITN use and access, modelled; estimated incidence).

## How to run it

1. Install requirements: `pip install -r requirements.txt`
2. Create a file called `.env` in this folder containing:
   `SYSTEM_API_KEY=your-key-here`
3. From the repository root run `python3 scripts/restore_system.py` (restores the System tables, SHA-256 checked). Then run `bash what-works-where/pipeline/run_all.sh`. It works offline except PubMed/Europe PMC metadata and the two graph-level API queries, and ends with `validate.py`.
4. Serve the site: `python3 -m http.server -d site 8000`, then open http://localhost:8000

## Data sources

- System Public Graph, Harvard Dataverse v2.1 snapshot (CC BY-NC 4.0): doi:10.7910/DVN/7V6JDO, file 14061020, SHA-256 `a9c8ba3d…daddf9`, plus the Public Graph v1 API.
- PubMed E-utilities (metadata) and Europe PMC (abstracts).
- WHO Global Health Observatory (MALARIA_ITN_USE, MALARIA_ITN_COVERAGE, MALARIA_EST_INCIDENCE).
- Original trial reports, listed in `data/verified/evidence_verified.csv`.

## Limitations

- The graph covers open-access papers only, and keyword discovery can miss studies.
- Most graph rows are shown as extracted. Only the rows marked "checked" were compared with a paper or abstract, and abstract checks confirm the number, not the risk of bias.
- Tanzania measured infection and Benin clinical cases, so they are shown side by side, never pooled.
- We do not compute pooled effects or vote by statistical significance.
- Before–after, modelled and observational results are labelled as such.

## AI coding tools

Yes. Claude Code (Anthropic) helped write the data pipeline and documentation. The team reviewed the outputs, and verified the evidence values against the papers.

## Screenshot

_to add_

---
Code: MIT (see LICENSE). Data in `data/` and `site/data/` derived from the System Public Graph: CC BY-NC 4.0.
