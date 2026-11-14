---
name: agent-ux
description: Use when designing how a user drives and reads an agent run in web/: the plan step, live progress, stopping, evidence cards, the theory-of-change chain, citations and the graph view. Covers interaction and information design; the dashboard skill covers look, wording and the screenshot audit.
---

# Agent UX: how a run feels and how evidence reads

Read `.claude/skills/dashboard/SKILL.md` first. This skill decides *what* the screen shows and *when*. That skill decides how it looks.

Sources: Microsoft's 18 Guidelines for Human-AI Interaction (HAX), Shneiderman's "overview first, zoom and filter, details on demand", GRADE and Cochrane summary-of-findings tables, and the agent patterns in Deep Research, NotebookLM, Consensus and Elicit.

## 1. Before the run: set expectations (HAX 1–2)

- Under the input, one line on what the tool does and does not do: "Answers from about 2M published findings. Shows associations, not causes. Says when the evidence runs out."
- Show 3 example questions for the selected profile. Clicking one fills the input and does not run it.
- Agent chips (from `GET /api/agents`) sit under the input. The user can switch any of them off before running.

## 2. The plan step (Deep Research's "plan and propose")

- On the `plan` event, show the restated question and one row per task: the agent's title and its instruction.
- The user can remove a task or add an agent before the specialists start, and during the run (decision in AGENTS.md). Keep it to remove and add. Don't build a full instruction editor.
- For policy questions the plan *is* the theory of change. Show the proposed chain (policy → mediators → outcome) as text in the plan, so the user checks the chain before evidence is gathered.

## 3. During the run: a taskboard, not a chat (HAX 3, 11)

- **Rows:** one row per agent with a status (`agent_started`, `retry`, `agent_done` or `agent_failed`) and its elapsed time.
- **Tool calls:** each `tool_call` event adds a line under its agent: tool name, the main argument and the `summary` ("search_concepts: malaria → 12 concepts, top: malaria (1316 studies)"). Collapse to the last 3 lines, with an expand control.
- **Retries:** show them as a small "Fixing output (1 retry)" line, not as an error.
- **Stop:** keep a Stop button visible at all times. Its tooltip says what stopping does: "Keeps the sections already finished."
- **Partial results:** show each section as soon as its agent is done. Don't wait for the formatter.
- **Failures:** a failed agent becomes a card that says what failed and offers "Run again". The other sections still render.

## 4. The answer: overview first, details on demand

Each card is built in layers. Each layer must make sense without the next one.

1. **Overview** (always visible): the formatter's short overall answer, then a strip of claims with their verdicts. The user should get the gist in 5 seconds.
2. **Card head:** the claim, then the verdict as text plus colour, then the meter.
3. **Card body:** the `basis` sentence, then `populations` and `gaps`.
4. **Details:** the `findings` table, in Elicit style:
   - columns: variable 1 → variable 2, effect type, value, CI, population, DOI
   - effects with a CI that excludes the null are marked
   - numbers use tabular figures and are right-aligned

Rules for the card:
- **Meter** (Consensus style): one horizontal bar from the `Meter` fields. It shows significant up, non-significant up, non-significant down and significant down, with counts labelled. Under it, label the family and the null, for example "ratio, null = 1", plus "N studies". Never show a meter without its counts.
- **Explain the verdict** (GRADE's lesson: say why certainty is what it is). Clicking or hovering the verdict shows the rule that produced it, from `agents/rules.md`, e.g. "Supported: 3+ studies and at least two thirds of significant findings point the same way."
- **Population mismatch:** when `populations` says the evidence doesn't match the user's population, show a visible "Different population" tag next to the verdict.
- **Single-study** links get a "1 study" tag. Don't leave it to the prose.
- **Gaps:** give them their own labelled block ("Where the evidence runs out"), not a footnote. This is part of the product.

## 5. The theory-of-change chain (PolicySection)

- **Layout:** boxes in a row for cause → via → effect. It wraps to a vertical list under 600 px.
- **Links:** each arrow carries its `support` value as a label (backed / partial / unbacked) plus line style. Use solid, dashed and dotted, so the chain reads without colour.
- **Weakest link:** flag the link with the least support and fewest studies as "Weakest link". That one line is the policy insight.
- **Drill-down:** clicking a link opens its note, studies and DOIs, and any evidence card on the same concepts.

## 6. Provenance: every number goes back to the graph (NotebookLM's grounded citations)

- **DOIs:** every DOI is a link to `https://doi.org/<doi>`.
- **Linked views:**
  - Hovering a card highlights its `concept_ids` in the graph view.
  - Clicking a graph node filters the cards to those that use it.
  - Clicking a card's "Show source calls" highlights the `tool_call` lines in the trace whose args mention its concept ids.
- **Trace:** keep the full trace one click away on every finished run. Judges score "real use of the graph", and the trace is the proof.

## 7. After the answer (HAX 15–18)

- **Follow-ups:** offer 2–3 next questions taken from the cards' `gaps`. Clicking one asks it in the same project thread.
- **Run history:** earlier turns in the project stay visible and collapsed above the new one.
- **Skip today:** per-card thumbs feedback, settings pages, onboarding tours.

## 8. Demo safety

- `GET /api/runs/{id}/events` replays stored events. A finished run can be replayed as if live, so keep one finished run per demo question and use the replay if the network is slow.
- The first screen a judge sees should have a finished example answer one click away, not an empty page.

## Checklist (add to the dashboard audit loop)

- [ ] The plan shows and can be edited before the specialists start.
- [ ] Every agent row shows a live status. Every tool call shows a one-line result.
- [ ] Stop works and keeps the finished sections.
- [ ] The overview is readable in 5 seconds. Every card works with only the head visible.
- [ ] Every verdict has a text label, a meter with counts and a "why" explanation.
- [ ] Population mismatch and single-study tags appear where they apply.
- [ ] The chain has a weakest-link flag and reads in greyscale.
- [ ] Every DOI links out, and every card can show the tool calls behind it.
