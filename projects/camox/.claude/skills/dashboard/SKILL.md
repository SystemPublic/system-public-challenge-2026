---
name: dashboard
description: Use when building or changing the Streamlit demo (app.py) or the graph visualizer, when writing any text a user or judge will read, or when auditing the UI and the pipeline behind it.
---

# Dashboard: demo UI, graph view, wording, audit

The demo is what judges see in three minutes. It shows a question going in, the agent working, and evidence cards plus a graph coming out. Taste is left to the agent, so the agent checks its own work with screenshots before calling anything done.

## Stack

- One file: `app.py`, run with `.venv/bin/streamlit run app.py`.
- The graph visualizer is our own HTML/JS page, embedded with `st.components.v1.html`. Move to `components.declare_component` only if clicks in the graph have to reach Python.
- Use one graph library, from a CDN, at an exact pinned version. Use cytoscape.js (for example `https://cdn.jsdelivr.net/npm/cytoscape@3.30.2/dist/cytoscape.min.js`). Don't add a second library.
- Graph data:
  - **Nodes:** the concepts the agent touched, taken from the tool trace and the cards' `concept_ids`.
  - **Edges:** relationships between those concepts, from DuckDB (`relationships`). Edge width scales with `num_studies`.
  - **Verdicts:** show them as text and colour together, both on the cards and on the nodes they cover.
- Keep the HTML/JS as one template string or one file under `ui/`. Fill it with JSON from Python; don't build the page from string fragments.
- If Streamlit blocks something we need, stop and ask before switching stacks.

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

1. **Run.** In Claude Code, add an entry to `.claude/launch.json` (`runtimeExecutable` `.venv/bin/streamlit`, args `run app.py --server.headless true`, port 8501), then open it with the browser pane's `preview_start`. Elsewhere, run the command and open http://localhost:8501.
2. **Screenshot.** Take four: desktop light, desktop dark, 390 px light, 390 px dark. Capture the empty state, a running state and a finished answer.
3. **Check** each screenshot against Nonslop UI and Nonslop writing above. Write down every miss.
4. **Audit the pipeline** on the standing test question: "Validate: girls under 12 are more vulnerable to malaria because of sexism in malaria-endemic countries." Check that:
   - every DOI shown on a card appears in a tool result in the trace
   - every count on a card (studies, findings, direction split, CIs excluding the null) matches a `summarise_evidence` output
   - no causal language appears anywhere in the answer
   - run time and tool-call count are recorded, and neither has grown by much since the last run without a reason
5. **Fix** what failed, take the screenshots again and repeat until a full pass is clean. Then report what you checked and what you changed.
