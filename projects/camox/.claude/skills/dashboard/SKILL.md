---
name: dashboard
description: Use when building or changing the web dashboard (web/) or the graph visualizer, when writing any text a user or judge will read, or when auditing the UI and the pipeline behind it.
---

# Dashboard: demo UI, graph view, wording, audit

The demo is what judges see in three minutes. It shows a question going in, the agent working, and evidence cards plus a graph coming out. Taste is left to the agent, so the agent checks its own work with screenshots before calling anything done.

## Stack

- Plain HTML/CSS/JS ES modules in `web/`, served by the FastAPI app at `/`. No build step, no framework.
  - `index.html` layout, `style.css` tokens and layout, `app.js` state, API calls and the SSE stream (`/api/runs/{id}/events`), `sections.js` one renderer per section type (unknown types render as readable JSON), `graph.js` the cytoscape view.
  - A new section type needs one renderer in `sections.js` and nothing else.
- Libraries from jsDelivr at exact pinned versions: cytoscape@3.30.2, vega@5.30.0, vega-lite@5.21.0, vega-embed@6.26.0. Don't add another.
- Graph data comes from `GET /api/graph?ids=...`, where ids are the union of `concept_ids` across the answer's sections.
  - **Nodes:** size scales with `n_studies`.
  - **Edges:** width scales with `n_studies`.
  - **Verdicts:** show them as text and colour together, on the cards and anywhere else they appear.
- Colours are CSS tokens on `:root`, redefined under `prefers-color-scheme: dark`. JS reads them from the tokens, never hard-codes them.

## Nonslop UI

Distilled from the unslop and VectorLab anti-slop principles.

Never:
- gradients, glassmorphism, glow, drop-shadow stacks
- emoji as icons, hero banners, rows of icon cards, stock illustrations
- decorative charts, or a chart where a number would do
- colour as the only signal (verdicts carry a text label)
- spinners that say "Loading…" and nothing else

Always:
- **Colour:** a neutral palette and one accent. Verdict colours are the only other colours, used the same way everywhere.
- **Hierarchy:** use size and weight, not colour. At most three text sizes per screen.
- **Numbers:** use tabular figures and align them right in tables. Label every unit, such as "studies", "findings" or "OR".
- **Spacing:** use one scale (4/8/16/24/32 px). Fit dense data in a small space, without padding for its own sake.
- **States:**
  - loading names the tool running right now ("Searching concepts: malaria")
  - empty says what to try
  - an error says what failed and what to do next
- **Layout:** it works at 390 px wide with no sideways scroll, and in dark mode. That includes the graph, which must stay readable and pannable on a phone.
- **Screenshots:** nothing ships that hasn't been seen in a screenshot.

## Nonslop writing

This covers every piece of text a user reads: labels, cards, errors, README and slides.

- Use plain words. Banned:
  - "delve", "robust", "seamless", "leverage", "unlock", "empower", "comprehensive", "cutting-edge"
  - "it's not X, it's Y"
  - rhetorical questions
  - lists of three by habit
  - chains of em dashes
  - exclamation marks
- Lead with the finding, then the basis. Write "12 of 22 studies point the same way", not "a substantial body of evidence".
- Write "associated with". Never "causes", "leads to", "drives" or "results in".
- Labels use sentence case. Buttons are verbs ("Run", "Show findings").
- Errors say what happened and what to do next: "The graph file is missing. Run the build step in README.md."
- Cut any sentence that would still be true for a different project.

## Audit loop

Run this after every UI change and before any push that touches the demo.

1. **Run.** Start the backend (`.venv/bin/uvicorn server.main:app --port 8000`) and open http://localhost:8000. For UI-only work without the backend, `python3 .claude/scratch/mock_server.py` serves `web/` with a fake API and event stream on port 8766.
2. **Screenshot.** Take four: desktop light, desktop dark, 390 px light, 390 px dark. Capture the empty state, a running state and a finished answer.
3. **Check** each screenshot against Nonslop UI and Nonslop writing above. Write down every miss.
4. **Audit the pipeline** on the standing test question: "Validate: girls under 12 are more vulnerable to malaria because of sexism in malaria-endemic countries." Check that:
   - every DOI shown on a card appears in a tool result in the trace
   - every count on a card (studies, findings, direction split, CIs excluding the null) matches a `summarise_evidence` output
   - no causal language appears anywhere in the answer
   - run time and tool-call count are recorded, and neither has grown by much since the last run without a reason
5. **Fix** what failed, take the screenshots again and repeat until a full pass is clean. Then report what you checked and what you changed.
